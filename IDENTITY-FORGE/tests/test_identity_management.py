from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from tests.factories import create_organization, create_user


class IdentityManagementTests(TestCase):
    def setUp(self):
        self.organization = create_organization()
        self.admin = create_user(
            self.organization,
            "admin@example.invalid",
            platform_role=User.PlatformRole.ADMIN,
        )
        self.viewer = create_user(
            self.organization,
            "viewer@example.invalid",
            platform_role=User.PlatformRole.VIEWER,
        )
        self.client = APIClient()

    def test_custom_user_model_created_with_profile(self):
        self.assertEqual(get_user_model(), User)
        self.assertTrue(self.viewer.profile.organization == self.organization)
        self.assertTrue(self.viewer.check_password("SyntheticPass!123"))

    def test_user_email_is_normalized(self):
        user = User.objects.create_user(
            username="mixed@example.invalid",
            email="Mixed@Example.INVALID",
            password="SyntheticPass!123",
            organization=self.organization,
        )
        self.assertEqual(user.email, "mixed@example.invalid")

    def test_registration_creates_viewer(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "new.user@example.invalid",
                "email": "new.user@example.invalid",
                "password": "StrongSyntheticPass!123",
                "organization_slug": self.organization.slug,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="new.user@example.invalid")
        self.assertEqual(user.platform_role, User.PlatformRole.VIEWER)
        self.assertNotIn("password", response.data)

    def test_admin_can_list_users_and_viewer_cannot(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(self.viewer)
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_jwt_token_issued_for_valid_credentials(self):
        response = self.client.post(
            "/api/auth/token/",
            {"username": self.admin.username, "password": "SyntheticPass!123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
