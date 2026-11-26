from django.conf import settings
from django.db import models


class Team(models.Model):
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="teams"
    )
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["organization", "name"], name="uniq_team_org_name")
        ]

    def __str__(self):
        return self.name


class IdentityProfile(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        SUSPENDED = "SUSPENDED", "Suspended"
        TERMINATED = "TERMINATED", "Terminated"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="identity_profiles"
    )
    team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True, related_name="members"
    )
    employee_id = models.CharField(max_length=64, blank=True)
    department = models.CharField(max_length=120, blank=True)
    title = models.CharField(max_length=160, blank=True)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    mfa_enabled = models.BooleanField(default=False)
    session_timeout_minutes = models.PositiveIntegerField(default=30)
    last_activity_at = models.DateTimeField(null=True, blank=True)
    risk_score = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return f"{self.user.username} profile"

    @property
    def is_active_account(self):
        return self.status == self.Status.ACTIVE and self.user.is_active
