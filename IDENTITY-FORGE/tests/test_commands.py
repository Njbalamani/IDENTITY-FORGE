import shutil
import tempfile

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from reports.models import Report
from tests.factories import create_organization, create_user

MEDIA_ROOT = tempfile.mkdtemp(prefix="identityforge-command-tests-")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ReportCommandTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.organization = create_organization()
        self.user = create_user(self.organization, "command@example.invalid")

    def test_report_command_generates_pdf(self):
        call_command(
            "identityforge_report",
            "--organization",
            self.organization.slug,
            "--type",
            "ZERO_TRUST",
            "--username",
            self.user.username,
            verbosity=0,
        )
        report = Report.objects.get(organization=self.organization)
        self.assertEqual(report.report_type, Report.ReportType.ZERO_TRUST)
        self.assertEqual(report.generated_by, self.user)
        self.assertTrue(report.file.storage.exists(report.file.name))

    def test_report_command_rejects_unknown_organization(self):
        with self.assertRaises(CommandError):
            call_command(
                "identityforge_report",
                "--organization",
                "missing-org",
                verbosity=0,
            )
