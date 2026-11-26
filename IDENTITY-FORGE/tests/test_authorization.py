from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from analysis.models import RiskFinding
from analysis.services import review_finding
from tests.factories import create_organization, create_user


class AuthorizationBoundaryTests(TestCase):
    def setUp(self):
        self.organization = create_organization()
        self.other_organization = create_organization("Other Org", "other-org")
        self.viewer = create_user(self.organization, "viewer@example.invalid")
        self.analyst = create_user(
            self.organization,
            "analyst@example.invalid",
            platform_role=User.PlatformRole.SECURITY_ANALYST,
        )
        self.reviewer = create_user(
            self.organization,
            "reviewer@example.invalid",
            platform_role=User.PlatformRole.REVIEWER,
        )
        self.other_user = create_user(
            self.other_organization,
            "other@example.invalid",
            platform_role=User.PlatformRole.SECURITY_ANALYST,
        )
        self.client = APIClient()

    def test_viewer_cannot_create_role(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.post(
            "/api/roles/", {"code": "viewer2", "name": "Viewer Two"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_analyst_can_create_scoped_role(self):
        self.client.force_authenticate(self.analyst)
        response = self.client.post(
            "/api/roles/", {"code": "analyst2", "name": "Analyst Two"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        from access.models import Role

        role = Role.objects.get(code="analyst2")
        self.assertEqual(role.organization, self.organization)

    def test_role_list_is_organization_scoped(self):
        from access.models import Role

        Role.objects.create(organization=self.organization, code="scope-a", name="Scope A")
        Role.objects.create(organization=self.other_organization, code="scope-b", name="Scope B")
        self.client.force_authenticate(self.analyst)
        response = self.client.get("/api/roles/")
        codes = [item["code"] for item in response.data["results"]]
        self.assertIn("scope-a", codes)
        self.assertNotIn("scope-b", codes)

    def test_reviewer_can_review_finding_through_api(self):
        finding = RiskFinding.objects.create(
            organization=self.organization,
            category=RiskFinding.Category.EXCESSIVE_PRIVILEGE,
            severity=RiskFinding.Severity.HIGH,
            title="Review boundary finding",
            description="Boundary test",
            recommendation="Review and close",
        )
        self.client.force_authenticate(self.reviewer)
        response = self.client.post(
            f"/api/findings/{finding.id}/review/",
            {"status": RiskFinding.Status.REMEDIATED, "note": "Verified"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        finding.refresh_from_db()
        self.assertEqual(finding.status, RiskFinding.Status.REMEDIATED)
        self.assertEqual(finding.reviewed_by, self.reviewer)

    def test_review_finding_rejects_invalid_status(self):
        finding = RiskFinding.objects.create(
            organization=self.organization,
            category=RiskFinding.Category.ZERO_TRUST,
            severity=RiskFinding.Severity.MEDIUM,
            title="Invalid status finding",
            description="Boundary test",
            recommendation="Review",
        )
        with self.assertRaises(ValueError):
            review_finding(finding, self.reviewer, "NOT_A_STATUS")

    def test_viewer_cannot_generate_report_through_api(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.post(
            "/api/reports/generate/", {"report_type": "EXECUTIVE"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
