from organizations.models import Organization


def active_organization(request):
    user = request.user
    if user.is_platform_admin and request.GET.get("organization"):
        organization = Organization.objects.filter(id=request.GET.get("organization")).first()
        if organization:
            return organization
    if user.organization_id:
        return user.organization
    if user.is_platform_admin:
        return Organization.objects.order_by("name").first()
    return None
