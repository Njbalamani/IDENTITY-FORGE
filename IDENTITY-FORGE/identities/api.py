from config.permissions import CanManageAccess
from config.viewsets import OrganizationScopedViewSet
from identities.models import IdentityProfile, Team
from identities.serializers import IdentityProfileSerializer, TeamSerializer


class TeamViewSet(OrganizationScopedViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [CanManageAccess]


class IdentityProfileViewSet(OrganizationScopedViewSet):
    queryset = IdentityProfile.objects.all()
    serializer_class = IdentityProfileSerializer
    permission_classes = [CanManageAccess]
