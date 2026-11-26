from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from analysis.models import RiskFinding, ZeroTrustAssessment
from tests.factories import create_organization, create_user


class UIFlowTests(TestCase):
    def setUp(self):
        self.organization = create_organization()
        self.admin = create_user(
            self.organization,
            "ui.admin@example.invalid",
            platform_role=User.PlatformRole.ADMIN,
        )
        self.reviewer = create_user(
            self.organization,
            "ui.reviewer@example.invalid",
            platform_role=User.PlatformRole.REVIEWER,
        )
        self.admin.set_password("SyntheticPass!123")
        self.admin.save(update_fields=["password"])
        self.reviewer.set_password("SyntheticPass!123")
        self.reviewer.save(update_fields=["password"])

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_dashboard_renders_database_metrics(self):
        self.client.login(username=self.admin.username, password="SyntheticPass!123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Command center")
        self.assertContains(response, "dashboard-metrics")
        self.assertContains(response, "graph-data")
        self.assertEqual(response.context["metrics"]["total_identities"], 2)

    def test_dashboard_includes_zero_trust_trend(self):
        earlier = ZeroTrustAssessment.objects.create(organization=self.organization, score=62)
        ZeroTrustAssessment.objects.filter(pk=earlier.pk).update(
            created_at=timezone.now() - timezone.timedelta(days=1)
        )
        ZeroTrustAssessment.objects.create(organization=self.organization, score=78)
        self.client.login(username=self.admin.username, password="SyntheticPass!123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "zero-trust-trend-chart")
        trend = response.context["metrics"]["zero_trust_trend"]
        self.assertEqual([item["score"] for item in trend], [62, 78])
        api_response = self.client.get("/api/dashboard/metrics/")
        self.assertEqual(api_response.status_code, 200)
        self.assertEqual(
            [item["score"] for item in api_response.json()["zero_trust_trend"]], [62, 78]
        )

    def test_graph_page_renders_graph_payload(self):
        self.client.login(username=self.admin.username, password="SyntheticPass!123")
        response = self.client.get(reverse("graph"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Access Relationship Graph")
        self.assertContains(response, "graph-data")

    def test_finding_review_ui_updates_status(self):
        finding = RiskFinding.objects.create(
            organization=self.organization,
            category=RiskFinding.Category.ZERO_TRUST,
            severity=RiskFinding.Severity.MEDIUM,
            title="UI review finding",
            description="UI test",
            recommendation="Review",
        )
        self.client.login(username=self.reviewer.username, password="SyntheticPass!123")
        response = self.client.post(
            reverse("finding-review", args=[finding.id]),
            {"status": RiskFinding.Status.ACCEPTED, "note": "Reviewed in UI"},
        )
        self.assertEqual(response.status_code, 302)
        finding.refresh_from_db()
        self.assertEqual(finding.status, RiskFinding.Status.ACCEPTED)
        self.assertEqual(finding.reviewed_by, self.reviewer)
