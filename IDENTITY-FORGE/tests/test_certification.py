from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from audit.models import AuditLog
from certification.models import Campaign, CampaignItem
from certification.services import apply_decisions, create_campaign, decide_item
from tests.factories import assign_role, create_organization, create_role, create_user


class CertificationServiceTests(TestCase):
    def setUp(self):
        self.organization = create_organization()
        self.admin = create_user(
            self.organization,
            "cert.admin@example.invalid",
            platform_role=User.PlatformRole.ADMIN,
        )
        self.analyst = create_user(
            self.organization,
            "cert.analyst@example.invalid",
            platform_role=User.PlatformRole.SECURITY_ANALYST,
        )
        self.reviewer = create_user(
            self.organization,
            "cert.reviewer@example.invalid",
            platform_role=User.PlatformRole.REVIEWER,
        )
        self.target = create_user(self.organization, "cert.target@example.invalid")
        self.role = create_role(self.organization)
        self.active_assignment = assign_role(self.target, self.role)
        self.inactive_assignment = assign_role(self.target, self.role, active=False)

    def create_campaign(self):
        return create_campaign(
            self.organization,
            self.admin,
            "Quarterly access certification",
            date(2026, 12, 31),
            [self.reviewer],
        )

    def test_campaign_snapshots_only_active_assignments(self):
        campaign = self.create_campaign()
        self.assertEqual(campaign.items.count(), 1)
        item = campaign.items.first()
        self.assertEqual(item.assignment, self.active_assignment)
        self.assertEqual(item.decision, CampaignItem.Decision.PENDING)
        self.assertTrue(AuditLog.objects.filter(action="Created certification campaign").exists())

    def test_apply_requires_all_decisions(self):
        second_role = create_role(self.organization, code="second", name="Second")
        assign_role(self.target, second_role)
        campaign = self.create_campaign()
        item = campaign.items.order_by("id").first()
        decide_item(item, self.reviewer, CampaignItem.Decision.APPROVED)
        self.assertEqual(campaign.pending_count, 1)
        self.active_assignment.refresh_from_db()
        self.assertTrue(self.active_assignment.active)
        with self.assertRaises(ValueError):
            apply_decisions(campaign, self.analyst)
        self.active_assignment.refresh_from_db()
        self.assertTrue(self.active_assignment.active)

    def test_apply_revokes_explicit_decisions(self):
        campaign = self.create_campaign()
        item = campaign.items.first()
        decide_item(item, self.reviewer, CampaignItem.Decision.REVOKED, "No longer required")
        revoked = apply_decisions(campaign, self.analyst)
        self.assertEqual(revoked, 1)
        self.active_assignment.refresh_from_db()
        self.assertFalse(self.active_assignment.active)
        campaign.refresh_from_db()
        self.assertEqual(campaign.status, Campaign.Status.COMPLETED)
        self.assertTrue(AuditLog.objects.filter(action="Revoked certified access").exists())
        self.assertTrue(AuditLog.objects.filter(action="Applied certification decisions").exists())


class CertificationAPITests(TestCase):
    def setUp(self):
        self.organization = create_organization()
        self.admin = create_user(
            self.organization,
            "api.cert.admin@example.invalid",
            platform_role=User.PlatformRole.ADMIN,
        )
        self.reviewer = create_user(
            self.organization,
            "api.cert.reviewer@example.invalid",
            platform_role=User.PlatformRole.REVIEWER,
        )
        self.viewer = create_user(self.organization, "api.cert.viewer@example.invalid")
        self.target = create_user(self.organization, "api.cert.target@example.invalid")
        self.role = create_role(self.organization)
        assign_role(self.target, self.role)
        self.client = APIClient()

    def test_admin_creates_campaign_and_reviewer_decides(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/certification-campaigns/",
            {
                "organization": self.organization.id,
                "name": "API certification",
                "due_date": "2026-12-31",
                "reviewers": [self.reviewer.id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        campaign = Campaign.objects.get(name="API certification")
        self.assertEqual(campaign.items.count(), 1)
        item = campaign.items.first()

        self.client.force_authenticate(self.reviewer)
        decision = self.client.post(
            f"/api/certification-items/{item.id}/decide/",
            {"decision": CampaignItem.Decision.APPROVED, "note": "Still required"},
            format="json",
        )
        self.assertEqual(decision.status_code, 200, decision.data)
        item.refresh_from_db()
        self.assertEqual(item.decision, CampaignItem.Decision.APPROVED)

    def test_viewer_cannot_create_or_decide(self):
        self.client.force_authenticate(self.viewer)
        create_response = self.client.post(
            "/api/certification-campaigns/",
            {"name": "Forbidden", "due_date": "2026-12-31"},
            format="json",
        )
        self.assertEqual(create_response.status_code, 403)
        campaign = create_campaign(
            self.organization,
            self.admin,
            "Read only campaign",
            date(2026, 12, 31),
            [self.reviewer],
        )
        item = campaign.items.first()
        decision = self.client.post(
            f"/api/certification-items/{item.id}/decide/",
            {"decision": CampaignItem.Decision.APPROVED},
            format="json",
        )
        self.assertEqual(decision.status_code, 403)


class CertificationUITests(TestCase):
    def setUp(self):
        self.organization = create_organization()
        self.admin = create_user(
            self.organization,
            "ui.cert.admin@example.invalid",
            platform_role=User.PlatformRole.ADMIN,
        )
        self.reviewer = create_user(
            self.organization,
            "ui.cert.reviewer@example.invalid",
            platform_role=User.PlatformRole.REVIEWER,
        )
        self.target = create_user(self.organization, "ui.cert.target@example.invalid")
        self.role = create_role(self.organization)
        assign_role(self.target, self.role)

    def test_campaign_ui_workflow(self):
        self.client.login(username=self.admin.username, password="SyntheticPass!123")
        response = self.client.post(
            "/certifications/create/",
            {
                "name": "UI certification",
                "due_date": "2026-12-31",
                "reviewers": [self.reviewer.id],
            },
        )
        campaign = Campaign.objects.get(name="UI certification")
        self.assertRedirects(response, f"/certifications/{campaign.id}/")
        detail = self.client.get(f"/certifications/{campaign.id}/")
        self.assertContains(detail, "UI certification")
        self.assertContains(detail, "ui.cert.target@example.invalid")

        self.client.logout()
        self.client.login(username=self.reviewer.username, password="SyntheticPass!123")
        item = campaign.items.first()
        decision = self.client.post(
            f"/certifications/items/{item.id}/decide/",
            {"decision": CampaignItem.Decision.EXCEPTION, "note": "Temporary grant"},
        )
        self.assertRedirects(decision, f"/certifications/{campaign.id}/")
        item.refresh_from_db()
        self.assertEqual(item.decision, CampaignItem.Decision.EXCEPTION)
