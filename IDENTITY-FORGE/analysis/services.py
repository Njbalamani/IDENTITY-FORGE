from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from analysis.engines.anomaly import AnomalyEngine
from analysis.engines.escalation import EscalationEngine
from analysis.engines.graph import AccessGraphEngine
from analysis.engines.permissions import PermissionEngine
from analysis.engines.zero_trust import ZeroTrustEngine
from analysis.models import AnalysisRun, AnomalyResult, RiskFinding, ZeroTrustAssessment
from audit.services import log_action


def upsert_finding(organization, payload):
    lookup = {
        "organization": organization,
        "category": payload["category"],
        "title": payload["title"],
    }
    if payload.get("user_id") is not None:
        lookup["user_id"] = payload["user_id"]
    defaults = {
        key: value for key, value in payload.items() if key not in {"category", "title", "user_id"}
    }
    finding, created = RiskFinding.objects.update_or_create(defaults=defaults, **lookup)
    return finding, created


def review_finding(finding, actor, status, note="", ip_address=None):
    if status not in RiskFinding.Status.values:
        raise ValueError("Unsupported finding status")
    finding.status = status
    finding.reviewed_by = actor
    finding.reviewed_at = timezone.now()
    if note:
        finding.evidence = {**finding.evidence, "review_note": note}
    finding.save(update_fields=["status", "reviewed_by", "reviewed_at", "evidence", "updated_at"])
    log_action(
        finding.organization,
        actor,
        f"Reviewed finding {finding.id}",
        "RiskFinding",
        finding.id,
        {"status": status, "title": finding.title},
        ip_address,
    )
    return finding


def run_permission_analysis(organization, actor=None, ip_address=None):
    engine = PermissionEngine(organization)
    created_count = 0
    evaluated_count = 0
    with transaction.atomic():
        for result in engine.evaluate_all():
            evaluated_count += 1
            user = result["user"]
            for permission in result["excessive_permissions"]:
                _, created = upsert_finding(
                    organization,
                    {
                        "category": RiskFinding.Category.EXCESSIVE_PRIVILEGE,
                        "severity": "HIGH" if permission.risk_weight >= 8 else "MEDIUM",
                        "title": f"Excessive permission {permission.code} for {user.username}",
                        "description": f"{permission.code} is reachable through role inheritance or exceeds the configured high-risk limit.",
                        "evidence": {
                            "permission": permission.code,
                            "risk_weight": permission.risk_weight,
                            "direct_roles": [role.name for role in result["direct_roles"]],
                            "effective_roles": [role.name for role in result["effective_roles"]],
                        },
                        "recommendation": "Remove the inherited grant or document a compensating control and access review.",
                        "score": min(100, permission.risk_weight * 10),
                        "user_id": user.id,
                    },
                )
                created_count += int(created)
            for conflict in result["conflicts"]:
                title = f"Conflicting roles for {user.username}: {' + '.join(conflict['roles'])}"
                _, created = upsert_finding(
                    organization,
                    {
                        "category": RiskFinding.Category.CONFLICTING_ROLE,
                        "severity": "HIGH",
                        "title": title,
                        "description": "Mutually exclusive roles are assigned to the same identity.",
                        "evidence": {"roles": conflict["roles"], "role_ids": conflict["role_ids"]},
                        "recommendation": "Enforce separation of duties by removing one role.",
                        "score": 85,
                        "user_id": user.id,
                    },
                )
                created_count += int(created)
            if result["inactive_access"]:
                _, created = upsert_finding(
                    organization,
                    {
                        "category": RiskFinding.Category.INACTIVE_ACCESS,
                        "severity": "HIGH",
                        "title": f"Inactive identity {user.username} retains active access",
                        "description": "The identity profile is not active but direct role assignments remain enabled.",
                        "evidence": {
                            "status": result["profile"].status if result["profile"] else "UNKNOWN",
                            "roles": [role.name for role in result["direct_roles"]],
                        },
                        "recommendation": "Disable role assignments and apply the account lifecycle process.",
                        "score": 80,
                        "user_id": user.id,
                    },
                )
                created_count += int(created)
            for permission in result["high_risk_permissions"]:
                if permission.risk_weight < 8:
                    continue
                _, created = upsert_finding(
                    organization,
                    {
                        "category": RiskFinding.Category.HIGH_RISK_PERMISSION,
                        "severity": "MEDIUM",
                        "title": f"High-risk permission {permission.code} held by {user.username}",
                        "description": f"{permission.code} has risk weight {permission.risk_weight} and requires explicit justification.",
                        "evidence": {
                            "permission": permission.code,
                            "category": permission.get_category_display(),
                        },
                        "recommendation": "Confirm the permission is required and schedule an access review.",
                        "score": permission.risk_weight * 8,
                        "user_id": user.id,
                    },
                )
                created_count += int(created)
        AnalysisRun.objects.create(
            organization=organization,
            analysis_type=AnalysisRun.AnalysisType.PERMISSIONS,
            details={"evaluated": evaluated_count, "new_findings": created_count},
            completed_at=timezone.now(),
        )
        log_action(
            organization,
            actor,
            "Ran permission analysis",
            "AnalysisRun",
            None,
            {"evaluated": evaluated_count, "new_findings": created_count},
            ip_address,
        )
    return {"evaluated": evaluated_count, "new_findings": created_count}


def run_escalation_analysis(organization, actor=None, ip_address=None):
    findings = EscalationEngine(organization).analyze()
    created_count = 0
    with transaction.atomic():
        for item in findings:
            _, created = upsert_finding(organization, item)
            created_count += int(created)
        AnalysisRun.objects.create(
            organization=organization,
            analysis_type=AnalysisRun.AnalysisType.ESCALATION,
            details={"paths": len(findings), "new_findings": created_count},
            completed_at=timezone.now(),
        )
        log_action(
            organization,
            actor,
            "Ran privilege escalation analysis",
            "AnalysisRun",
            None,
            {"paths": len(findings)},
            ip_address,
        )
    return {"paths": len(findings), "new_findings": created_count}


def run_graph_analysis(organization, actor=None, ip_address=None):
    payload = AccessGraphEngine(organization).to_payload()
    with transaction.atomic():
        AnalysisRun.objects.create(
            organization=organization,
            analysis_type=AnalysisRun.AnalysisType.GRAPH,
            details=payload["summary"],
            completed_at=timezone.now(),
        )
        log_action(
            organization,
            actor,
            "Generated access graph",
            "AnalysisRun",
            None,
            payload["summary"],
            ip_address,
        )
    return payload


def run_anomaly_analysis(organization, events=None, actor=None, ip_address=None):
    rows = AnomalyEngine(organization).analyze(events)
    created_count = 0
    anomaly_count = 0
    users = {user.id: user for user in get_user_model().objects.filter(organization=organization)}
    with transaction.atomic():
        for row in rows:
            user = users.get(row["user_id"])
            if not user:
                continue
            AnomalyResult.objects.update_or_create(
                organization=organization,
                user=user,
                event_date=row["event_date"],
                model_name=row["model_name"],
                defaults={
                    "anomaly_score": row["anomaly_score"],
                    "is_anomaly": row["is_anomaly"],
                    "reasons": row["reasons"],
                    "features": AnomalyEngine.features_for(row),
                },
            )
            if not row["is_anomaly"]:
                continue
            anomaly_count += 1
            severity = "CRITICAL" if row["anomaly_score"] >= 1.0 else "HIGH"
            _, created = upsert_finding(
                organization,
                {
                    "category": RiskFinding.Category.ANOMALY_DETECTION,
                    "severity": severity,
                    "title": f"Anomalous access pattern for {user.username} on {row['event_date']}",
                    "description": "Observed activity differs from the computed identity activity baseline.",
                    "evidence": {
                        "score": row["anomaly_score"],
                        "reasons": row["reasons"],
                        "features": AnomalyEngine.features_for(row),
                        "model": row["model_name"],
                    },
                    "recommendation": "Review the source events with the identity owner before taking action.",
                    "score": min(100, int(50 + row["anomaly_score"] * 20)),
                    "user_id": user.id,
                },
            )
            created_count += int(created)
        AnalysisRun.objects.create(
            organization=organization,
            analysis_type=AnalysisRun.AnalysisType.ANOMALY,
            details={
                "profiles": len(rows),
                "anomalies": anomaly_count,
                "new_findings": created_count,
            },
            completed_at=timezone.now(),
        )
        log_action(
            organization,
            actor,
            "Ran anomaly analysis",
            "AnalysisRun",
            None,
            {"profiles": len(rows), "anomalies": anomaly_count},
            ip_address,
        )
    return {"profiles": len(rows), "anomalies": anomaly_count, "new_findings": created_count}


def run_zero_trust_assessment(organization, actor=None, ip_address=None):
    result = ZeroTrustEngine(organization).evaluate()
    created_count = 0
    with transaction.atomic():
        ZeroTrustAssessment.objects.create(
            organization=organization,
            score=result["score"],
            category_scores=result["category_scores"],
            findings=result["findings"],
            recommendations=result["recommendations"],
        )
        for index, finding in enumerate(result["findings"]):
            _, created = upsert_finding(
                organization,
                {
                    "category": RiskFinding.Category.ZERO_TRUST,
                    "severity": "MEDIUM",
                    "title": f"Zero Trust gap {index + 1}: {finding}",
                    "description": finding,
                    "evidence": result["category_scores"],
                    "recommendation": result["recommendations"][index],
                    "score": max(
                        10, 100 - result["category_scores"][list(result["category_scores"])[index]]
                    ),
                },
            )
            created_count += int(created)
        AnalysisRun.objects.create(
            organization=organization,
            analysis_type=AnalysisRun.AnalysisType.ZERO_TRUST,
            details={"score": result["score"], "new_findings": created_count},
            completed_at=timezone.now(),
        )
        log_action(
            organization,
            actor,
            "Ran Zero Trust assessment",
            "AnalysisRun",
            None,
            {"score": result["score"]},
            ip_address,
        )
    return {**result, "new_findings": created_count}


def run_all_analyses(organization, actor=None, ip_address=None):
    permissions = run_permission_analysis(organization, actor, ip_address)
    escalation = run_escalation_analysis(organization, actor, ip_address)
    graph = run_graph_analysis(organization, actor, ip_address)
    anomaly = run_anomaly_analysis(organization, actor=actor, ip_address=ip_address)
    zero_trust = run_zero_trust_assessment(organization, actor, ip_address)
    with transaction.atomic():
        AnalysisRun.objects.create(
            organization=organization,
            analysis_type=AnalysisRun.AnalysisType.ALL,
            details={
                "permissions": permissions,
                "escalation": escalation,
                "graph": graph["summary"],
                "anomaly": anomaly,
                "zero_trust_score": zero_trust["score"],
            },
            completed_at=timezone.now(),
        )
    return {
        "permissions": permissions,
        "escalation": escalation,
        "graph": graph["summary"],
        "anomaly": anomaly,
        "zero_trust": zero_trust,
    }
