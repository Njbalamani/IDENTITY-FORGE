from rest_framework import serializers

from access.models import (
    AccessEvent,
    AccessResource,
    AccessReview,
    Permission,
    Role,
    RoleAssignment,
)


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = [
            "id",
            "code",
            "name",
            "category",
            "description",
            "risk_weight",
            "is_high_risk",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "code",
            "description",
            "permissions",
            "inherits",
            "conflicts",
            "is_privileged",
            "risk_weight",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class RoleAssignmentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = RoleAssignment
        fields = [
            "id",
            "user",
            "username",
            "role",
            "role_name",
            "team",
            "source",
            "granted_by",
            "justification",
            "active",
            "granted_at",
            "expires_at",
        ]
        read_only_fields = ["id", "granted_at", "username", "role_name"]


class AccessResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessResource
        fields = [
            "id",
            "name",
            "resource_type",
            "sensitivity",
            "owner",
            "permissions",
            "description",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AccessEventSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    resource_name = serializers.CharField(source="resource.name", read_only=True)

    class Meta:
        model = AccessEvent
        fields = [
            "id",
            "user",
            "username",
            "event_type",
            "resource",
            "resource_name",
            "ip_address",
            "user_agent",
            "success",
            "occurred_at",
            "source",
            "metadata",
            "risk_score",
        ]
        read_only_fields = ["id", "username", "resource_name"]


class AccessReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessReview
        fields = [
            "id",
            "user",
            "reviewer",
            "status",
            "due_date",
            "completed_at",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
