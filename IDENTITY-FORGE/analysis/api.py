import csv
import io

from django.conf import settings
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from analysis.engines.graph import AccessGraphEngine
from analysis.models import AnalysisRun, AnomalyResult, RiskFinding, ZeroTrustAssessment
from analysis.serializers import (
    AnalysisRunSerializer,
    AnomalyResultSerializer,
    RiskFindingSerializer,
    ZeroTrustAssessmentSerializer,
)
from analysis.services import (
    review_finding,
    run_all_analyses,
    run_anomaly_analysis,
    run_escalation_analysis,
    run_graph_analysis,
    run_permission_analysis,
    run_zero_trust_assessment,
)
from audit.services import log_action
from config.permissions import CanReviewFindings
from config.viewsets import OrganizationScopedViewSet


class RiskFindingViewSet(OrganizationScopedViewSet):
    queryset = RiskFinding.objects.all()
    serializer_class = RiskFindingSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        if not request.user.can_review and not request.user.is_platform_admin:
            return Response({"detail": "Reviewer access is required."}, status=403)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not request.user.can_review and not request.user.is_platform_admin:
            return Response({"detail": "Reviewer access is required."}, status=403)
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, CanReviewFindings])
    def review(self, request, pk=None):
        finding = self.get_object()
        try:
            review_finding(
                finding,
                request.user,
                request.data.get("status"),
                request.data.get("note", ""),
                request.META.get("REMOTE_ADDR"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(RiskFindingSerializer(finding).data)

    @action(detail=False, methods=["get"])
    def export(self, request):
        findings = (
            self.get_queryset()
            .select_related("user", "resource", "reviewed_by")
            .order_by("-score", "-created_at")
        )
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "id",
                "category",
                "severity",
                "title",
                "nist_csf",
                "cis_controls",
                "score",
                "status",
                "username",
                "resource",
                "reviewed_by",
                "created_at",
            ]
        )
        for finding in findings:
            writer.writerow(
                [
                    finding.id,
                    finding.category,
                    finding.severity,
                    finding.title,
                    " ".join(finding.nist_controls),
                    " ".join(finding.cis_controls),
                    finding.score,
                    finding.status,
                    finding.user.username if finding.user else "",
                    finding.resource.name if finding.resource else "",
                    finding.reviewed_by.username if finding.reviewed_by else "",
                    finding.created_at.isoformat(),
                ]
            )
        log_action(
            request.user.organization,
            request.user,
            "Exported risk findings",
            "RiskFinding",
            None,
            {"count": findings.count()},
            request.META.get("REMOTE_ADDR"),
        )
        response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="identityforge-findings.csv"'
        return response


class AnomalyResultViewSet(OrganizationScopedViewSet):
    queryset = AnomalyResult.objects.all()
    serializer_class = AnomalyResultSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]


class ZeroTrustAssessmentViewSet(OrganizationScopedViewSet):
    queryset = ZeroTrustAssessment.objects.all()
    serializer_class = ZeroTrustAssessmentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]


class AnalysisRunViewSet(OrganizationScopedViewSet):
    queryset = AnalysisRun.objects.all()
    serializer_class = AnalysisRunSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]


class AccessGraphAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = request.user.organization
        if not organization and not request.user.is_platform_admin:
            return Response({"detail": "No organization assigned."}, status=400)
        if not organization:
            organization_id = request.query_params.get("organization")
            if not organization_id:
                return Response({"detail": "organization query parameter is required."}, status=400)
            from organizations.models import Organization

            organization = Organization.objects.filter(id=organization_id).first()
            if not organization:
                return Response({"detail": "Organization not found."}, status=404)
        engine = AccessGraphEngine(organization)
        graph = engine.build_graph()
        payload = engine.to_payload(graph)
        user_id = request.query_params.get("user_id")
        if user_id:
            payload["indirect_paths"] = engine.indirect_paths(graph, user_id)
        else:
            payload["indirect_paths"] = []
        return Response(payload)


class RunAnalysisAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.can_review and not request.user.is_platform_admin:
            return Response({"detail": "Analyst or administrator access is required."}, status=403)
        organization = request.user.organization
        if not organization:
            return Response({"detail": "No organization assigned."}, status=400)
        analysis_type = request.data.get("analysis", "ALL").upper()
        actor = request.user
        ip_address = request.META.get("REMOTE_ADDR")
        runners = {
            "PERMISSIONS": lambda: run_permission_analysis(organization, actor, ip_address),
            "ESCALATION": lambda: run_escalation_analysis(organization, actor, ip_address),
            "GRAPH": lambda: run_graph_analysis(organization, actor, ip_address),
            "ANOMALY": lambda: run_anomaly_analysis(
                organization, actor=actor, ip_address=ip_address
            ),
            "ZERO_TRUST": lambda: run_zero_trust_assessment(organization, actor, ip_address),
            "ALL": lambda: run_all_analyses(organization, actor, ip_address),
        }
        runner = runners.get(analysis_type)
        if not runner:
            return Response({"detail": "Unsupported analysis type."}, status=400)
        result = runner()
        log_action(
            organization,
            actor,
            f"Triggered {analysis_type} analysis",
            "AnalysisRun",
            None,
            {"analysis": analysis_type},
            ip_address,
        )
        return Response({"analysis": analysis_type, "result": result}, status=202)


class AIStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "synthetic_data_only": settings.SYNTHETIC_DATA_ONLY,
                "disclaimer": settings.AI_MODEL_DISCLAIMER,
                "models": ["isolation-forest", "statistical-baseline", "networkx-graph-analysis"],
                "unauthorized_escalation": "disabled",
                "requires_human_review": True,
            }
        )
