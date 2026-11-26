from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsPlatformAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_platform_admin)


class CanReviewFindings(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.can_review)


class CanManageAccess(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.is_platform_admin or user.platform_role == user.PlatformRole.SECURITY_ANALYST


class HasOrganizationAccess(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_platform_admin:
            return True
        organization = getattr(obj, "organization", None)
        return bool(organization and organization.id == user.organization_id)
