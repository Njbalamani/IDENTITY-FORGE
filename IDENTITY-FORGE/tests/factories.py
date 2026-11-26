from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from access.models import (
    AccessEvent,
    AccessResource,
    AccessReview,
    Permission,
    Role,
    RoleAssignment,
)
from identities.models import IdentityProfile, Team
from organizations.models import Organization


def create_organization(name="Northstar Health", slug="northstar-health"):
    return Organization.objects.create(name=name, slug=slug, synthetic=True)


def create_user(
    organization,
    username="analyst@example.invalid",
    platform_role=None,
    password="SyntheticPass!123",
    **extra,
):
    defaults = {
        "email": username,
        "display_name": username.split("@")[0],
        "organization": organization,
        "platform_role": platform_role or get_user_model().PlatformRole.VIEWER,
    }
    defaults.update(extra)
    user = get_user_model().objects.create_user(username=username, password=password, **defaults)
    IdentityProfile.objects.create(
        user=user,
        organization=organization,
        status=IdentityProfile.Status.ACTIVE,
        mfa_enabled=True,
        session_timeout_minutes=30,
    )
    return user


def create_permission(organization, code="DATA_READ", risk_weight=2, is_high_risk=False, **extra):
    defaults = {
        "name": code.replace("_", " ").title(),
        "category": Permission.Category.DATA,
        "risk_weight": risk_weight,
        "is_high_risk": is_high_risk,
    }
    defaults.update(extra)
    return Permission.objects.create(organization=organization, code=code, **defaults)


def create_role(
    organization, code="viewer", name="Viewer", permissions=(), inherits=(), conflicts=(), **extra
):
    defaults = {"name": name, "risk_weight": 1, "is_privileged": False}
    defaults.update(extra)
    role = Role.objects.create(organization=organization, code=code, **defaults)
    role.permissions.set(permissions)
    role.inherits.set(inherits)
    role.conflicts.set(conflicts)
    return role


def assign_role(user, role, active=True, team=None, source=RoleAssignment.Source.DIRECT):
    return RoleAssignment.objects.create(
        user=user, role=role, team=team, active=active, source=source
    )


def create_team(organization, name="Security Operations"):
    return Team.objects.create(organization=organization, name=name)


def create_resource(
    organization,
    name="claims-warehouse",
    sensitivity=AccessResource.Sensitivity.RESTRICTED,
    permissions=(),
):
    resource = AccessResource.objects.create(
        organization=organization, name=name, sensitivity=sensitivity
    )
    resource.permissions.set(permissions)
    return resource


def create_event(
    user,
    event_type=AccessEvent.EventType.LOGIN,
    occurred_at=None,
    resource=None,
    success=True,
    **extra,
):
    return AccessEvent.objects.create(
        organization=user.organization,
        user=user,
        event_type=event_type,
        occurred_at=occurred_at or timezone.now(),
        resource=resource,
        success=success,
        **extra,
    )


def create_review(user, due_date=None, status=AccessReview.Status.PENDING):
    return AccessReview.objects.create(
        organization=user.organization,
        user=user,
        due_date=due_date or timezone.now() + timedelta(days=3),
        status=status,
    )
