from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from access.models import AccessEvent, AccessReview
from analysis.engines.graph import AccessGraphEngine
from analysis.models import AnomalyResult, RiskFinding, ZeroTrustAssessment
from certification.models import Campaign, CampaignItem
from identities.models import IdentityProfile


def dashboard_metrics(organization):
    if not organization:
        return {
            "total_identities": 0,
            "active_identities": 0,
            "privileged_accounts": 0,
            "excessive_permissions": 0,
            "suspicious_events": 0,
            "inactive_accounts": 0,
            "high_risk_relationships": 0,
            "open_findings": 0,
            "active_campaigns": 0,
            "pending_certifications": 0,
            "role_distribution": [],
            "event_trend": [],
            "zero_trust_trend": [],
            "risk_by_category": [],
            "graph_summary": {"node_count": 0, "edge_count": 0, "risky_edge_count": 0},
        }

    users = get_user_model().objects.filter(organization=organization)
    total_identities = users.count()
    active_identities = users.filter(is_active=True).count()
    privileged_accounts = (
        users.filter(
            is_active=True,
            role_assignments__active=True,
            role_assignments__role__is_privileged=True,
        )
        .distinct()
        .count()
    )
    open_status = RiskFinding.Status.OPEN
    excessive_permissions = RiskFinding.objects.filter(
        organization=organization,
        category=RiskFinding.Category.EXCESSIVE_PRIVILEGE,
        status=open_status,
    ).count()
    suspicious_events = AnomalyResult.objects.filter(
        organization=organization, is_anomaly=True
    ).count()
    inactive_accounts = (
        IdentityProfile.objects.filter(organization=organization)
        .exclude(status=IdentityProfile.Status.ACTIVE)
        .count()
    )
    high_risk_relationships = RiskFinding.objects.filter(
        organization=organization,
        category=RiskFinding.Category.ESCALATION_PATH,
        status=open_status,
    ).count()
    open_findings = RiskFinding.objects.filter(
        organization=organization, status=open_status
    ).count()
    active_campaigns = Campaign.objects.filter(
        organization=organization, status=Campaign.Status.ACTIVE
    ).count()
    pending_certifications = CampaignItem.objects.filter(
        campaign__organization=organization,
        campaign__status=Campaign.Status.ACTIVE,
        decision=CampaignItem.Decision.PENDING,
    ).count()

    role_rows = list(
        users.values("platform_role").annotate(count=Count("id")).order_by("platform_role")
    )
    role_distribution = [
        {"label": row["platform_role"].replace("_", " ").title(), "value": row["count"]}
        for row in role_rows
    ]

    start_date = timezone.now().date() - timedelta(days=6)
    event_rows = (
        AccessEvent.objects.filter(organization=organization, occurred_at__date__gte=start_date)
        .annotate(day=TruncDate("occurred_at"))
        .values("day")
        .annotate(count=Count("id"))
    )
    event_map = {str(row["day"]): row["count"] for row in event_rows}
    event_trend = [
        {
            "date": (start_date + timedelta(days=offset)).isoformat(),
            "count": event_map.get((start_date + timedelta(days=offset)).isoformat(), 0),
        }
        for offset in range(7)
    ]

    category_rows = list(
        RiskFinding.objects.filter(organization=organization)
        .values("category")
        .annotate(count=Count("id"))
    )
    risk_by_category = [
        {"label": row["category"].replace("_", " ").title(), "value": row["count"]}
        for row in category_rows
    ]

    trend_rows = (
        ZeroTrustAssessment.objects.filter(organization=organization)
        .order_by("created_at")
        .values("created_at", "score")[:12]
    )
    zero_trust_trend = [
        {"date": row["created_at"].date().isoformat(), "score": row["score"]} for row in trend_rows
    ]

    latest = ZeroTrustAssessment.objects.filter(organization=organization).first()
    return {
        "total_identities": total_identities,
        "active_identities": active_identities,
        "privileged_accounts": privileged_accounts,
        "excessive_permissions": excessive_permissions,
        "suspicious_events": suspicious_events,
        "inactive_accounts": inactive_accounts,
        "high_risk_relationships": high_risk_relationships,
        "open_findings": open_findings,
        "active_campaigns": active_campaigns,
        "pending_certifications": pending_certifications,
        "pending_reviews": AccessReview.objects.filter(
            organization=organization,
            status__in=[AccessReview.Status.PENDING, AccessReview.Status.IN_PROGRESS],
        ).count(),
        "zero_trust_score": latest.score if latest else None,
        "role_distribution": role_distribution,
        "event_trend": event_trend,
        "zero_trust_trend": zero_trust_trend,
        "risk_by_category": risk_by_category,
        "graph_summary": AccessGraphEngine(organization).to_payload()["summary"],
    }
