from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.permissions import CanManageAccess, HasOrganizationAccess
from config.viewsets import OrganizationScopedViewSet
from reports.models import Report
from reports.serializers import ReportSerializer
from reports.services import generate_report


class ReportViewSet(OrganizationScopedViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, HasOrganizationAccess]
    http_method_names = ["get", "head", "options"]


class GenerateReportAPIView(APIView):
    permission_classes = [IsAuthenticated, CanManageAccess]

    def post(self, request):
        organization = request.user.organization
        if not organization:
            return Response({"detail": "No organization assigned."}, status=400)
        report_type = request.data.get("report_type", "EXECUTIVE").upper()
        valid_types = {choice[0] for choice in Report.ReportType.choices}
        if report_type not in valid_types:
            return Response({"detail": "Unsupported report type."}, status=400)
        report = generate_report(
            organization, report_type, request.user, request.META.get("REMOTE_ADDR")
        )
        return Response(ReportSerializer(report).data, status=201)
