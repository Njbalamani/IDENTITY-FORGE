from django.conf import settings
from django.db import models


class Report(models.Model):
    class ReportType(models.TextChoices):
        EXECUTIVE = "EXECUTIVE", "Executive"
        IDENTITY = "IDENTITY", "Identity"
        PERMISSIONS = "PERMISSIONS", "Permissions"
        ANOMALY = "ANOMALY", "Anomaly"
        ZERO_TRUST = "ZERO_TRUST", "Zero Trust"

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="reports"
    )
    title = models.CharField(max_length=220)
    report_type = models.CharField(
        max_length=24, choices=ReportType.choices, default=ReportType.EXECUTIVE
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_reports",
    )
    file = models.FileField(upload_to="reports/generated/", blank=True)
    summary = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
