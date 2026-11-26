from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response

from certification.models import Campaign, CampaignItem
from certification.serializers import CampaignItemSerializer, CampaignSerializer
from certification.services import (
    apply_decisions,
    cancel_campaign,
    create_campaign,
    decide_item,
)
from config.permissions import CanManageAccess, HasOrganizationAccess
from config.viewsets import OrganizationScopedViewSet


class CampaignViewSet(OrganizationScopedViewSet):
    queryset = Campaign.objects.prefetch_related("reviewers", "items").all()
    serializer_class = CampaignSerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated(), HasOrganizationAccess()]
        return [CanManageAccess(), HasOrganizationAccess()]

    def perform_create(self, serializer):
        user = self.request.user
        organization = (
            serializer.validated_data.get("organization") if user.is_platform_admin else None
        ) or user.organization
        if not organization:
            raise PermissionDenied("Assign the account to an organization before creating records.")
        campaign = create_campaign(
            organization,
            user,
            serializer.validated_data["name"],
            serializer.validated_data["due_date"],
            serializer.validated_data.get("reviewers", []),
            self.request.META.get("REMOTE_ADDR"),
        )
        serializer.instance = campaign

    @action(detail=True, methods=["post"])
    def apply(self, request, pk=None):
        campaign = self.get_object()
        try:
            revoked = apply_decisions(campaign, request.user, request.META.get("REMOTE_ADDR"))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response({"revoked": revoked, "status": campaign.status})

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        campaign = self.get_object()
        try:
            cancel_campaign(campaign, request.user, request.META.get("REMOTE_ADDR"))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response({"status": campaign.status})


class CampaignItemViewSet(OrganizationScopedViewSet):
    queryset = CampaignItem.objects.select_related("campaign", "user", "role", "assignment").all()
    serializer_class = CampaignItemSerializer
    organization_field = "campaign__organization"

    def get_permissions(self):
        return [IsAuthenticated(), HasOrganizationAccess()]

    @action(detail=True, methods=["post"])
    def decide(self, request, pk=None):
        item = self.get_object()
        user = request.user
        if not user.is_platform_admin and not item.campaign.reviewers.filter(id=user.id).exists():
            raise PermissionDenied("You are not assigned to this certification campaign.")
        try:
            decide_item(
                item,
                user,
                request.data.get("decision"),
                request.data.get("note", ""),
                request.META.get("REMOTE_ADDR"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(CampaignItemSerializer(item).data)
