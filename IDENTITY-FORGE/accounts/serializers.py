from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from organizations.models import Organization

User = get_user_model()


class SyntheticUsernameValidationMixin:
    def validate_username(self, value):
        if settings.SYNTHETIC_DATA_ONLY and not value.endswith(".invalid"):
            raise serializers.ValidationError(
                "Synthetic-only mode requires usernames ending in '.invalid'."
            )
        return value


class UserSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "display_name",
            "platform_role",
            "organization",
            "organization_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "is_superuser"]


class UserCreateSerializer(SyntheticUsernameValidationMixin, serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "display_name",
            "platform_role",
            "organization",
            "password",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class RegisterSerializer(SyntheticUsernameValidationMixin, serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    organization_slug = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "display_name", "organization_slug", "password"]

    def create(self, validated_data):
        slug = validated_data.pop("organization_slug", "")
        password = validated_data.pop("password")
        organization = Organization.objects.filter(slug=slug).first() if slug else None
        user = User(
            organization=organization,
            platform_role=User.PlatformRole.VIEWER,
            **validated_data,
        )
        user.set_password(password)
        user.save()
        return user
