from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from config.ui import active_organization
from reports.models import Report
from reports.services import generate_report


@login_required
def report_list(request):
    organization = active_organization(request)
    reports = (
        Report.objects.filter(organization=organization) if organization else Report.objects.none()
    )
    return render(
        request,
        "reports/report_list.html",
        {
            "reports": reports,
            "organization": organization,
            "report_types": Report.ReportType.choices,
        },
    )


@login_required
@require_POST
def report_generate(request):
    if not request.user.can_review and not request.user.is_platform_admin:
        messages.error(request, "Reviewer access is required to generate reports.")
        return redirect("reports")
    organization = active_organization(request)
    if not organization:
        messages.error(request, "No organization assigned.")
        return redirect("reports")
    report_type = request.POST.get("report_type", "EXECUTIVE").upper()
    valid_types = {choice[0] for choice in Report.ReportType.choices}
    if report_type not in valid_types:
        messages.error(request, "Unsupported report type.")
        return redirect("reports")
    report = generate_report(
        organization, report_type, request.user, request.META.get("REMOTE_ADDR")
    )
    messages.success(request, f"Generated {report.title}.")
    return redirect("reports")
