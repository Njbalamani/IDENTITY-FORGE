from django.test import TestCase
from rest_framework.test import APIClient

from analysis.compliance import control_mapping
from analysis.models import RiskFinding
from tests.factories import create_organization, create_user


class ComplianceMappingTests(TestCase):
    def setUp(self):
        self.organization = create_organization()
        self.user = create_user(self.organization, "compliance@example.invalid")
        self.finding = RiskFinding.objects.create(
            organization=self.organization,
            category=RiskFinding.Category.EXCESSIVE_PRIVILEGE,
            severity=RiskFinding.Severity.HIGH,
            title="Mapped finding",
            description="Compliance mapping test",
            recommendation="Review",
            score=80,
        )
        self.client = APIClient()

    def test_all_finding_categories_have_control_mappings(self):
        for category in RiskFinding.Category.values:
            mapping = control_mapping(category)
            self.assertTrue(mapping["nist_csf"])
            self.assertTrue(mapping["zero_trust_principles"])

    def test_api_exposes_control_mappings(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/findings/{self.finding.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("PR.AA-05", response.data["nist_controls"])
        self.assertIn("5.4", response.data["cis_controls"])

    def test_export_includes_control_columns(self):
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/findings/export/")
        content = response.content.decode("utf-8")
        self.assertIn("nist_csf", content)
        self.assertIn("PR.AA-05", content)

    def test_findings_page_displays_control_mapping(self):
        self.client.login(username=self.user.username, password="SyntheticPass!123")
        response = self.client.get("/analysis/findings/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PR.AA-05")
