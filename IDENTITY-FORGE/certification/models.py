from django.conf import settings
from django.db import models


class Campaign(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="certification_campaigns",
    )
    name = models.CharField(max_length=180)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    due_date = models.DateField()
    reviewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="certification_reviews", blank=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_certifications",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def item_count(self):
        return self.items.count()

    @property
    def decided_count(self):
        return self.items.exclude(decision=CampaignItem.Decision.PENDING).count()

    @property
    def pending_count(self):
        return self.items.filter(decision=CampaignItem.Decision.PENDING).count()


class CampaignItem(models.Model):
    class Decision(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REVOKED = "REVOKED", "Revoked"
        EXCEPTION = "EXCEPTION", "Exception"

    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="items")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certification_items"
    )
    role = models.ForeignKey(
        "access.Role", on_delete=models.CASCADE, related_name="certification_items"
    )
    assignment = models.ForeignKey(
        "access.RoleAssignment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certification_items",
    )
    decision = models.CharField(max_length=16, choices=Decision.choices, default=Decision.PENDING)
    note = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decided_certifications",
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user__username", "role__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "user", "role"], name="uniq_campaign_user_role"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"

    @property
    def organization(self):
        return self.campaign.organization
