from django.contrib import admin

from analysis.models import AnalysisRun, AnomalyResult, RiskFinding, ZeroTrustAssessment

for model in (RiskFinding, AnomalyResult, ZeroTrustAssessment, AnalysisRun):
    admin.site.register(model)
