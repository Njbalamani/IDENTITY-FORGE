from rest_framework import serializers

from identities.models import IdentityProfile, Team


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "name", "description", "parent", "created_at"]
        read_only_fields = ["id", "created_at"]


class IdentityProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = IdentityProfile
        fields = [
            "id",
            "user",
            "username",
            "team",
            "employee_id",
            "department",
            "title",
            "status",
            "mfa_enabled",
            "session_timeout_minutes",
            "last_activity_at",
            "risk_score",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]
