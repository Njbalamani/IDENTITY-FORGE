from celery import shared_task

from analysis.services import (
    run_all_analyses,
    run_anomaly_analysis,
    run_escalation_analysis,
    run_graph_analysis,
    run_permission_analysis,
    run_zero_trust_assessment,
)
from organizations.models import Organization


@shared_task(name="identityforge.run_permission_analysis")
def permission_analysis_task(organization_id):
    return run_permission_analysis(Organization.objects.get(id=organization_id))


@shared_task(name="identityforge.run_escalation_analysis")
def escalation_analysis_task(organization_id):
    return run_escalation_analysis(Organization.objects.get(id=organization_id))


@shared_task(name="identityforge.run_graph_analysis")
def graph_analysis_task(organization_id):
    return run_graph_analysis(Organization.objects.get(id=organization_id))


@shared_task(name="identityforge.run_anomaly_analysis")
def anomaly_analysis_task(organization_id):
    return run_anomaly_analysis(Organization.objects.get(id=organization_id))


@shared_task(name="identityforge.run_zero_trust_assessment")
def zero_trust_task(organization_id):
    return run_zero_trust_assessment(Organization.objects.get(id=organization_id))


@shared_task(name="identityforge.run_all_analyses")
def full_assessment_task(organization_id):
    return run_all_analyses(Organization.objects.get(id=organization_id))
