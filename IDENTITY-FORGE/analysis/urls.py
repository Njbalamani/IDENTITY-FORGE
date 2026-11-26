from django.urls import path

from analysis.views import (
    analysis_runs,
    anomalies,
    finding_review,
    findings,
    graph,
    run_analysis,
    zero_trust,
)

urlpatterns = [
    path("findings/", findings, name="findings"),
    path("findings/<int:pk>/review/", finding_review, name="finding-review"),
    path("anomalies/", anomalies, name="anomalies"),
    path("zero-trust/", zero_trust, name="zero-trust"),
    path("graph/", graph, name="graph"),
    path("runs/", analysis_runs, name="analysis-runs"),
    path("run/", run_analysis, name="run-analysis"),
]
