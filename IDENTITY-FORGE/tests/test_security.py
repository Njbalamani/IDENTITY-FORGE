from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from audit.models import AuditLog
from tests.factories import create_organization, create_user


class SecurityBoundaryTests(TestCase):
    def setUp(self):
        self.organization = create_organization()
        self.client = APIClient()

    def test_jwt_authentication_returns_access_token(self):
        user = create_user(self.organization, "jwt@example.invalid")
        response = self.client.post(
            "/api/auth/token/",
            {"username": user.username, "password": "SyntheticPass!123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["access"])
        self.assertTrue(response.data["refresh"])

    def test_protected_api_requires_authentication(self):
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_registration_rejects_non_synthetic_username(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "real.person@example.com",
                "email": "real.person@example.com",
                "password": "SyntheticPass!123",
                "organization_slug": self.organization.slug,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_registration_accepts_synthetic_username_and_writes_audit_log(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "registered@example.invalid",
                "email": "registered@example.invalid",
                "password": "SyntheticPass!123",
                "organization_slug": self.organization.slug,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="registered@example.invalid")
        self.assertEqual(user.platform_role, User.PlatformRole.VIEWER)
        self.assertNotIn("password", response.data)
        audit_log = AuditLog.objects.get(
            organization=self.organization, actor=user, action="Registered account"
        )
        self.assertNotIn("SyntheticPass!123", str(audit_log.metadata))

    def test_admin_user_creation_rejects_non_synthetic_username(self):
        admin = create_user(
            self.organization,
            "admin@example.invalid",
            platform_role=User.PlatformRole.ADMIN,
        )
        self.client.force_authenticate(admin)
        response = self.client.post(
            "/api/users/",
            {
                "username": "production.user@example.com",
                "email": "production.user@example.com",
                "display_name": "Production User",
                "organization": self.organization.id,
                "platform_role": User.PlatformRole.VIEWER,
                "password": "SyntheticPass!123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="production.user@example.com").exists())

    def test_authenticated_mutation_is_audited(self):
        analyst = create_user(
            self.organization,
            "audited@example.invalid",
            platform_role=User.PlatformRole.SECURITY_ANALYST,
        )
        self.client.force_authenticate(analyst)
        response = self.client.post(
            "/api/roles/",
            {"code": "audited-role", "name": "Audited Role"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            AuditLog.objects.filter(
                organization=self.organization,
                actor=analyst,
                action="POST /api/roles/",
            ).exists()
        )
