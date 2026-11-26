from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from access.models import (
    AccessEvent,
    AccessResource,
    AccessReview,
    Permission,
    Role,
    RoleAssignment,
)
from access.serializers import (
    AccessEventSerializer,
    AccessResourceSerializer,
    AccessReviewSerializer,
    PermissionSerializer,
    RoleAssignmentSerializer,
    RoleSerializer,
)
from analysis.imports import import_access_events
from audit.services import log_action
from config.permissions import CanManageAccess, HasOrganizationAccess
from config.viewsets import OrganizationScopedViewSet


class PermissionViewSet(OrganizationScopedViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [CanManageAccess]


class RoleViewSet(OrganizationScopedViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [CanManageAccess]


class RoleAssignmentViewSet(OrganizationScopedViewSet):
    queryset = RoleAssignment.objects.all()
    serializer_class = RoleAssignmentSerializer
    permission_classes = [CanManageAccess]

    def perform_create(self, serializer):
        serializer.save(granted_by=self.request.user)


class AccessResourceViewSet(OrganizationScopedViewSet):
    queryset = AccessResource.objects.all()
    serializer_class = AccessResourceSerializer
    permission_classes = [CanManageAccess]


class AccessEventViewSet(OrganizationScopedViewSet):
    queryset = AccessEvent.objects.all()
    serializer_class = AccessEventSerializer
    permission_classes = [IsAuthenticated, HasOrganizationAccess]

    @action(detail=False, methods=["post"], parser_classes=[MultiPartParser])
    def import_events(self, request):
        if not request.user.can_review and not request.user.is_platform_admin:
            return Response(
                {"detail": "Import requires reviewer or administrator access."}, status=403
            )
        uploaded = request.FILES.get("file")
        if not uploaded:
            return Response({"detail": "A CSV file is required."}, status=400)
        try:
            count = import_access_events(request.user.organization, uploaded)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        log_action(
            request.user.organization,
            request.user,
            "Imported access events",
            "AccessEvent",
            None,
            {"count": count},
            request.META.get("REMOTE_ADDR"),
        )
        return Response({"imported": count}, status=201)


class AccessReviewViewSet(OrganizationScopedViewSet):
    queryset = AccessReview.objects.all()
    serializer_class = AccessReviewSerializer
    permission_classes = [CanManageAccess]

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        from django.utils import timezone

        review = self.get_object()
        if review.status in {AccessReview.Status.APPROVED, AccessReview.Status.REJECTED}:
            return Response({"detail": "Review is already completed."}, status=400)
        decision = request.data.get("status")
        if decision not in {AccessReview.Status.APPROVED, AccessReview.Status.REJECTED}:
            return Response({"detail": "status must be APPROVED or REJECTED."}, status=400)
        review.status = decision
        review.reviewer = request.user
        review.completed_at = timezone.now()
        review.notes = request.data.get("notes", review.notes)
        review.save()
        log_action(
            review.organization,
            request.user,
            f"Completed access review {review.id}",
            "AccessReview",
            review.id,
            {"status": decision},
            request.META.get("REMOTE_ADDR"),
        )
        return Response(AccessReviewSerializer(review).data)
