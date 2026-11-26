from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from config.permissions import IsPlatformAdmin
from organizations.models import Organization
from organizations.serializers import OrganizationSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsPlatformAdmin]
