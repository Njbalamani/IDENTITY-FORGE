from rest_framework.permissions import IsAuthenticated

from audit.models import AuditLog
from audit.serializers import AuditLogSerializer
from config.permissions import HasOrganizationAccess
from config.viewsets import OrganizationScopedViewSet


class AuditLogViewSet(OrganizationScopedViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, HasOrganizationAccess]
    http_method_names = ["get", "head", "options"]
