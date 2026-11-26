from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from analysis.engines.graph import AccessGraphEngine
from analysis.forms import FindingReviewForm
from analysis.models import AnalysisRun, AnomalyResult, RiskFinding, ZeroTrustAssessment
from analysis.services import review_finding, run_all_analyses
from audit.services import log_action
from config.ui import active_organization


@login_required
def findings(request):
    organization = active_organization(request)
    queryset = (
        RiskFinding.objects.filter(organization=organization)
        if organization
        else RiskFinding.objects.none()
    )
    category = request.GET.get("category")
    status = request.GET.get("status")
    if category:
        queryset = queryset.filter(category=category)
    if status:
        queryset = queryset.filter(status=status)
    return render(
        request,
        "analysis/findings.html",
        {
            "findings": queryset,
            "categories": RiskFinding.Category.choices,
            "statuses": RiskFinding.Status.choices,
            "selected_category": category,
            "selected_status": status,
            "review_form": FindingReviewForm(),
            "organization": organization,
        },
    )


@login_required
@require_POST
def finding_review(request, pk):
    if not request.user.can_review and not request.user.is_platform_admin:
        messages.error(request, "Reviewer access is required.")
        return redirect("findings")
    organization = active_organization(request)
    finding = RiskFinding.objects.filter(id=pk, organization=organization).first()
    if not finding:
        messages.error(request, "Finding not found.")
        return redirect("findings")
    form = FindingReviewForm(request.POST, instance=finding)
    if form.is_valid():
        review_finding(
            finding,
            request.user,
            form.cleaned_data["status"],
            request.POST.get("note", ""),
            request.META.get("REMOTE_ADDR"),
        )
        messages.success(request, "Finding review saved.")
    else:
        messages.error(request, "Invalid review decision.")
    return redirect("findings")


@login_required
def anomalies(request):
    organization = active_organization(request)
    results = (
        AnomalyResult.objects.filter(organization=organization).select_related("user")
        if organization
        else AnomalyResult.objects.none()
    )
    return render(
        request, "analysis/anomalies.html", {"results": results, "organization": organization}
    )


@login_required
def zero_trust(request):
    organization = active_organization(request)
    assessment = (
        ZeroTrustAssessment.objects.filter(organization=organization).first()
        if organization
        else None
    )
    category_scores = []
    if assessment:
        for key, value in assessment.category_scores.items():
            category_scores.append(
                {"key": key, "label": key.replace("_", " ").title(), "value": value}
            )
    return render(
        request,
        "analysis/zero_trust.html",
        {
            "assessment": assessment,
            "category_scores": category_scores,
            "organization": organization,
        },
    )


@login_required
def graph(request):
    organization = active_organization(request)
    payload = (
        AccessGraphEngine(organization).to_payload()
        if organization
        else {"nodes": [], "links": [], "summary": {}}
    )
    return render(
        request, "analysis/graph.html", {"graph_payload": payload, "organization": organization}
    )


@login_required
@require_POST
def run_analysis(request):
    if not request.user.can_review and not request.user.is_platform_admin:
        messages.error(request, "Analyst access is required to run assessments.")
        return redirect("findings")
    organization = active_organization(request)
    if not organization:
        messages.error(request, "No organization assigned.")
        return redirect("findings")
    result = run_all_analyses(organization, request.user, request.META.get("REMOTE_ADDR"))
    log_action(
        organization,
        request.user,
        "Ran full assessment from dashboard",
        "AnalysisRun",
        None,
        {"open_findings": result["permissions"]["new_findings"]},
        request.META.get("REMOTE_ADDR"),
    )
    messages.success(request, "Full identity risk assessment completed.")
    return redirect(request.POST.get("next", "findings"))


@login_required
def analysis_runs(request):
    organization = active_organization(request)
    runs = (
        AnalysisRun.objects.filter(organization=organization)
        if organization
        else AnalysisRun.objects.none()
    )
    return render(request, "analysis/runs.html", {"runs": runs, "organization": organization})
