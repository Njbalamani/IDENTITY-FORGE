from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied


class OrganizationScopedViewSet(viewsets.ModelViewSet):
    organization_field = "organization"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_platform_admin:
            return queryset
        if user.organization_id:
            return queryset.filter(**{f"{self.organization_field}__id": user.organization_id})
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_platform_admin:
            serializer.save()
            return
        if not user.organization_id:
            raise PermissionDenied("Assign the account to an organization before creating records.")
        serializer.save(**{self.organization_field: user.organization})
