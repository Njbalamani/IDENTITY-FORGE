from rest_framework import serializers

from certification.models import Campaign, CampaignItem
from organizations.models import Organization


class CampaignItemSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = CampaignItem
        fields = [
            "id",
            "campaign",
            "user",
            "username",
            "role",
            "role_name",
            "assignment",
            "decision",
            "note",
            "decided_by",
            "decided_at",
            "created_at",
        ]
        read_only_fields = fields


class CampaignSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(), required=False
    )
    item_count = serializers.ReadOnlyField()
    decided_count = serializers.ReadOnlyField()
    pending_count = serializers.ReadOnlyField()
    items = CampaignItemSerializer(many=True, read_only=True)

    class Meta:
        model = Campaign
        fields = [
            "id",
            "organization",
            "name",
            "status",
            "due_date",
            "reviewers",
            "created_by",
            "item_count",
            "decided_count",
            "pending_count",
            "items",
            "created_at",
            "completed_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_by",
            "item_count",
            "decided_count",
            "pending_count",
            "items",
            "created_at",
            "completed_at",
        ]
