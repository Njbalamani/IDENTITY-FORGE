from django.conf import settings
from django.db import models


class Permission(models.Model):
    class Category(models.TextChoices):
        IDENTITY = "IDENTITY", "Identity"
        DATA = "DATA", "Data"
        ADMIN = "ADMIN", "Administration"
        FINANCE = "FINANCE", "Finance"
        OPERATIONS = "OPERATIONS", "Operations"

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="permissions"
    )
    code = models.CharField(max_length=120)
    name = models.CharField(max_length=180)
    category = models.CharField(max_length=24, choices=Category.choices, default=Category.IDENTITY)
    description = models.TextField(blank=True)
    risk_weight = models.PositiveSmallIntegerField(default=1)
    is_high_risk = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"], name="uniq_permission_org_code"
            )
        ]

    def __str__(self):
        return self.code


class Role(models.Model):
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="roles"
    )
    name = models.CharField(max_length=160)
    code = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, related_name="roles", blank=True)
    inherits = models.ManyToManyField(
        "self", symmetrical=False, related_name="inherited_by", blank=True
    )
    conflicts = models.ManyToManyField("self", symmetrical=True, blank=True)
    is_privileged = models.BooleanField(default=False)
    risk_weight = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["organization", "code"], name="uniq_role_org_code")
        ]

    def __str__(self):
        return self.name


class RoleAssignment(models.Model):
    class Source(models.TextChoices):
        DIRECT = "DIRECT", "Direct"
        TEAM = "TEAM", "Team"
        EXTERNAL = "EXTERNAL", "External"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="role_assignments"
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="assignments")
    team = models.ForeignKey(
        "identities.Team",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="role_assignments",
    )
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.DIRECT)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_assignments",
    )
    justification = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-granted_at"]

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"


class AccessResource(models.Model):
    class ResourceType(models.TextChoices):
        APPLICATION = "APPLICATION", "Application"
        DATABASE = "DATABASE", "Database"
        FILE_SYSTEM = "FILE_SYSTEM", "File System"
        CLOUD = "CLOUD", "Cloud"
        ENDPOINT = "ENDPOINT", "Endpoint"
        FINANCIAL = "FINANCIAL", "Financial"

    class Sensitivity(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        INTERNAL = "INTERNAL", "Internal"
        CONFIDENTIAL = "CONFIDENTIAL", "Confidential"
        RESTRICTED = "RESTRICTED", "Restricted"

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="resources"
    )
    name = models.CharField(max_length=180)
    resource_type = models.CharField(
        max_length=24, choices=ResourceType.choices, default=ResourceType.APPLICATION
    )
    sensitivity = models.CharField(
        max_length=20, choices=Sensitivity.choices, default=Sensitivity.INTERNAL
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_resources",
    )
    permissions = models.ManyToManyField(Permission, related_name="resources", blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["organization", "name"], name="uniq_resource_org_name")
        ]

    def __str__(self):
        return self.name

    @property
    def high_risk(self):
        return (
            self.sensitivity == self.Sensitivity.RESTRICTED
            or self.permissions.filter(is_high_risk=True).exists()
        )


class AccessEvent(models.Model):
    class EventType(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        LOGIN_FAILED = "LOGIN_FAILED", "Failed Login"
        LOGOUT = "LOGOUT", "Logout"
        PERMISSION_CHANGE = "PERMISSION_CHANGE", "Permission Change"
        ROLE_ASSIGNED = "ROLE_ASSIGNED", "Role Assigned"
        RESOURCE_ACCESS = "RESOURCE_ACCESS", "Resource Access"
        MFA_CHALLENGE = "MFA_CHALLENGE", "MFA Challenge"
        ADMIN_ACTION = "ADMIN_ACTION", "Administrative Action"

    class Source(models.TextChoices):
        SYNTHETIC = "SYNTHETIC", "Synthetic"
        IMPORTED = "IMPORTED", "Imported"
        LIVE = "LIVE", "Live"

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="access_events"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_events",
    )
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    resource = models.ForeignKey(
        AccessResource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_events",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    success = models.BooleanField(default=True)
    occurred_at = models.DateTimeField()
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.SYNTHETIC)
    metadata = models.JSONField(default=dict, blank=True)
    risk_score = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["organization", "-occurred_at"]),
            models.Index(fields=["user", "-occurred_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} {self.user_id or 'unknown'}"


class AccessReview(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="access_reviews"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="access_reviews"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="performed_reviews",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    due_date = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date"]

    def __str__(self):
        return f"Review {self.user.username}"
