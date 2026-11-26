from itertools import combinations

from django.conf import settings

from access.models import Permission, Role
from identities.models import IdentityProfile


class PermissionEngine:
    def __init__(self, organization):
        self.organization = organization

    def assigned_roles(self, user):
        return list(
            Role.objects.filter(
                organization=self.organization,
                assignments__user=user,
                assignments__active=True,
            ).distinct()
        )

    def reachable_roles(self, roles):
        result = []
        queue = list(roles)
        seen = set()
        while queue:
            role = queue.pop(0)
            if role.id in seen:
                continue
            seen.add(role.id)
            result.append(role)
            for parent in role.inherits.exclude(id__in=seen):
                queue.append(parent)
        return result

    def evaluate_user(self, user):
        direct_roles = self.assigned_roles(user)
        effective_roles = self.reachable_roles(direct_roles)
        direct_permissions = list(Permission.objects.filter(roles__in=direct_roles).distinct())
        effective_permissions = list(
            Permission.objects.filter(roles__in=effective_roles).distinct()
        )
        direct_ids = {permission.id for permission in direct_permissions}
        high_risk = [permission for permission in effective_permissions if permission.is_high_risk]
        inherited_high_risk = [
            permission for permission in high_risk if permission.id not in direct_ids
        ]
        excessive = list(inherited_high_risk)
        limit = settings.HIGH_RISK_PERMISSION_LIMIT
        if len(high_risk) > limit:
            direct_high_risk = {
                permission.code: permission
                for permission in high_risk
                if permission.id in direct_ids
            }
            overflow = [permission for permission in high_risk if permission.id not in direct_ids]
            if len(overflow) + len(direct_high_risk) > limit:
                excessive = (
                    overflow + list(direct_high_risk.values())[: max(0, limit - len(overflow))]
                )

        conflicts = []
        for first, second in combinations(direct_roles, 2):
            if second in first.conflicts.all():
                conflicts.append(
                    {"roles": [first.name, second.name], "role_ids": [first.id, second.id]}
                )

        profile = IdentityProfile.objects.filter(user=user, organization=self.organization).first()
        inactive_access = bool(
            profile and profile.status != IdentityProfile.Status.ACTIVE and direct_roles
        )
        privilege_score = sum(permission.risk_weight for permission in effective_permissions)

        return {
            "user": user,
            "direct_roles": direct_roles,
            "effective_roles": effective_roles,
            "direct_permissions": direct_permissions,
            "effective_permissions": effective_permissions,
            "high_risk_permissions": high_risk,
            "excessive_permissions": list(
                {permission.id: permission for permission in excessive}.values()
            ),
            "conflicts": conflicts,
            "inactive_access": inactive_access,
            "privilege_score": privilege_score,
            "profile": profile,
        }

    def evaluate_all(self):
        from django.contrib.auth import get_user_model

        users = get_user_model().objects.filter(organization=self.organization, is_active=True)
        return [self.evaluate_user(user) for user in users]
