from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from analysis.models import RiskFinding
from audit.models import AuditLog
from tests.factories import create_organization, create_user


class FindingExportTests(TestCase):
    def setUp(self):
        self.organization = create_organization()
        self.other_organization = create_organization("Other Org", "other-org")
        self.analyst = create_user(
            self.organization,
            "exporter@example.invalid",
            platform_role=User.PlatformRole.SECURITY_ANALYST,
        )
        self.other_analyst = create_user(
            self.other_organization,
            "other-exporter@example.invalid",
            platform_role=User.PlatformRole.SECURITY_ANALYST,
        )
        self.finding = RiskFinding.objects.create(
            organization=self.organization,
            category=RiskFinding.Category.EXCESSIVE_PRIVILEGE,
            severity=RiskFinding.Severity.HIGH,
            title="Exportable finding",
            description="Export test",
            recommendation="Review",
            score=90,
        )
        self.client = APIClient()

    def test_export_returns_csv_with_scoped_findings(self):
        self.client.force_authenticate(self.analyst)
        response = self.client.get("/api/findings/export/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("Exportable finding", response.content.decode("utf-8"))
        self.assertTrue(
            AuditLog.objects.filter(
                organization=self.organization, action="Exported risk findings"
            ).exists()
        )

    def test_export_does_not_cross_organization_boundary(self):
        self.client.force_authenticate(self.other_analyst)
        response = self.client.get("/api/findings/export/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("Exportable finding", response.content.decode("utf-8"))
