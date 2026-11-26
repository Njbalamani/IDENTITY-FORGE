from django.conf import settings
from django.db import models

from analysis.compliance import control_mapping


class RiskFinding(models.Model):
    class Category(models.TextChoices):
        EXCESSIVE_PRIVILEGE = "EXCESSIVE_PRIVILEGE", "Excessive Privilege"
        CONFLICTING_ROLE = "CONFLICTING_ROLE", "Conflicting Role"
        INACTIVE_ACCESS = "INACTIVE_ACCESS", "Inactive Access"
        HIGH_RISK_PERMISSION = "HIGH_RISK_PERMISSION", "High Risk Permission"
        ESCALATION_PATH = "ESCALATION_PATH", "Escalation Path"
        ANOMALY_DETECTION = "ANOMALY_DETECTION", "Anomaly Detection"
        ZERO_TRUST = "ZERO_TRUST", "Zero Trust Gap"

    class Severity(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        REMEDIATED = "REMEDIATED", "Remediated"
        ACCEPTED = "ACCEPTED", "Accepted"
        FALSE_POSITIVE = "FALSE_POSITIVE", "False Positive"

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="risk_findings"
    )
    category = models.CharField(max_length=32, choices=Category.choices)
    severity = models.CharField(max_length=16, choices=Severity.choices)
    title = models.CharField(max_length=220)
    description = models.TextField()
    evidence = models.JSONField(default=dict, blank=True)
    recommendation = models.TextField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="risk_findings",
    )
    resource = models.ForeignKey(
        "access.AccessResource",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="risk_findings",
    )
    score = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_findings",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-score", "-created_at"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["category", "severity"]),
        ]

    def __str__(self):
        return self.title

    @property
    def nist_controls(self):
        return control_mapping(self.category)["nist_csf"]

    @property
    def cis_controls(self):
        return control_mapping(self.category)["cis_controls"]

    @property
    def zero_trust_principles(self):
        return control_mapping(self.category)["zero_trust_principles"]


class AnomalyResult(models.Model):
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="anomaly_results"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="anomaly_results"
    )
    event_date = models.DateField()
    anomaly_score = models.FloatField()
    is_anomaly = models.BooleanField(default=False)
    reasons = models.JSONField(default=list, blank=True)
    features = models.JSONField(default=dict, blank=True)
    model_name = models.CharField(max_length=80, default="isolation-forest")
    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-anomaly_score"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user", "event_date", "model_name"],
                name="uniq_anomaly_result",
            )
        ]

    def __str__(self):
        return f"{self.user.username} {self.event_date}"


class ZeroTrustAssessment(models.Model):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="zero_trust_assessments",
    )
    score = models.PositiveSmallIntegerField()
    category_scores = models.JSONField(default=dict, blank=True)
    findings = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Zero Trust {self.score}"


class AnalysisRun(models.Model):
    class AnalysisType(models.TextChoices):
        PERMISSIONS = "PERMISSIONS", "Permissions"
        GRAPH = "GRAPH", "Access Graph"
        ESCALATION = "ESCALATION", "Privilege Escalation"
        ANOMALY = "ANOMALY", "Anomaly Detection"
        ZERO_TRUST = "ZERO_TRUST", "Zero Trust"
        ALL = "ALL", "Full Assessment"

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="analysis_runs"
    )
    analysis_type = models.CharField(max_length=24, choices=AnalysisType.choices)
    status = models.CharField(max_length=20, default="COMPLETED")
    details = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
