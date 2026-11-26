from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from audit.models import AuditLog
from config.ui import active_organization


@login_required
def audit_list(request):
    organization = active_organization(request)
    logs = (
        AuditLog.objects.filter(organization=organization).select_related("actor")
        if organization
        else AuditLog.objects.none()
    )
    return render(request, "audit/audit_list.html", {"logs": logs, "organization": organization})
