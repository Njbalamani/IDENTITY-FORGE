from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from access.models import AccessEvent
from analysis.engines.graph import AccessGraphEngine
from analysis.models import AnomalyResult, RiskFinding, ZeroTrustAssessment
from config.ui import active_organization
from dashboard.metrics import dashboard_metrics


@login_required
def home(request):
    organization = active_organization(request)
    metrics = dashboard_metrics(organization)
    if organization:
        findings = RiskFinding.objects.filter(organization=organization).order_by("-score")[:8]
        anomalies = AnomalyResult.objects.filter(organization=organization, is_anomaly=True)[:6]
        assessment = ZeroTrustAssessment.objects.filter(organization=organization).first()
        recent_events = AccessEvent.objects.filter(organization=organization).select_related(
            "user"
        )[:8]
    else:
        findings = []
        anomalies = []
        assessment = None
        recent_events = []
    graph_payload = (
        AccessGraphEngine(organization).to_payload()
        if organization
        else {"nodes": [], "links": [], "summary": {}}
    )
    return render(
        request,
        "dashboard/home.html",
        {
            "organization": organization,
            "metrics": metrics,
            "findings": findings,
            "anomalies": anomalies,
            "assessment": assessment,
            "recent_events": recent_events,
            "graph_payload": graph_payload,
        },
    )
