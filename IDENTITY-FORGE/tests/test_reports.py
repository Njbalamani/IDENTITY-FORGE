import shutil
import tempfile

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from analysis.models import AnomalyResult, RiskFinding
from reports.services import generate_report
from tests.factories import create_organization, create_user

MEDIA_ROOT = tempfile.mkdtemp(prefix="identityforge-tests-")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ReportTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.organization = create_organization()
        self.user = create_user(
            self.organization,
            "reports@example.invalid",
            platform_role=User.PlatformRole.SECURITY_ANALYST,
        )
        RiskFinding.objects.create(
            organization=self.organization,
            category=RiskFinding.Category.EXCESSIVE_PRIVILEGE,
            severity=RiskFinding.Severity.HIGH,
            title="Report evidence finding",
            description="Report test",
            recommendation="Remove excess grant",
            score=80,
        )
        AnomalyResult.objects.create(
            organization=self.organization,
            user=self.user,
            event_date="2026-11-20",
            anomaly_score=1.5,
            is_anomaly=True,
            reasons=["event count is 40 versus baseline 2.00"],
            model_name="statistical-baseline",
        )

    def test_generate_report_creates_pdf_and_summary(self):
        report = generate_report(self.organization, "EXECUTIVE", self.user)
        self.assertTrue(report.file)
        self.assertTrue(report.file.storage.exists(report.file.name))
        with report.file.open("rb") as handle:
            self.assertTrue(handle.read(5).startswith(b"%PDF-"))
        self.assertEqual(report.summary["finding_count"], 1)
        self.assertEqual(report.summary["anomaly_count"], 1)
        self.assertEqual(report.summary["metrics"]["total_identities"], 1)

    def test_report_api_generation_requires_manage_access(self):
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.post(
            "/api/reports/generate/", {"report_type": "ZERO_TRUST"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["file"])
