from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class PlatformRole(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        SECURITY_ANALYST = "SECURITY_ANALYST", "Security Analyst"
        REVIEWER = "REVIEWER", "Reviewer"
        VIEWER = "VIEWER", "Viewer"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
    )
    platform_role = models.CharField(
        max_length=32, choices=PlatformRole.choices, default=PlatformRole.VIEWER
    )
    display_name = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["username"]

    @property
    def is_platform_admin(self):
        return self.is_superuser or self.platform_role == self.PlatformRole.ADMIN

    @property
    def can_review(self):
        return self.is_platform_admin or self.platform_role in {
            self.PlatformRole.SECURITY_ANALYST,
            self.PlatformRole.REVIEWER,
        }

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        if not self.display_name:
            self.display_name = self.get_full_name() or self.username
        super().save(*args, **kwargs)
