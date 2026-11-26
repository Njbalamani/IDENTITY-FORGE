from django.test import TestCase

from accounts.models import User
from analysis.engines.escalation import EscalationEngine
from analysis.engines.zero_trust import ZeroTrustEngine
from analysis.models import RiskFinding
from analysis.services import run_escalation_analysis, run_zero_trust_assessment
from identities.models import IdentityProfile
from tests.factories import (
    assign_role,
    create_organization,
    create_permission,
    create_review,
    create_role,
    create_user,
)


class RiskAnalysisTests(TestCase):
    def setUp(self):
        self.organization = create_organization()
        self.high_permission = create_permission(
            self.organization,
            "CLOUD_DEPLOY",
            risk_weight=9,
            is_high_risk=True,
        )
        self.privileged = create_role(
            self.organization,
            "cloud_operator",
            "Cloud Operator",
            permissions=[self.high_permission],
            is_privileged=True,
            risk_weight=9,
        )
        self.power_user = create_user(
            self.organization,
            "power@example.invalid",
            platform_role=User.PlatformRole.ADMIN,
        )
        assign_role(self.power_user, self.privileged)

    def test_escalation_engine_reports_inheritance_path(self):
        create_role(
            self.organization,
            "engineer",
            "Platform Engineer",
            inherits=[self.privileged],
        )
        findings = EscalationEngine(self.organization).analyze()
        self.assertTrue(any(item["category"] == "ESCALATION_PATH" for item in findings))
        self.assertTrue(
            any(item["evidence"]["path"][0] == "Platform Engineer" for item in findings)
        )

    def test_escalation_service_persists_findings(self):
        create_role(self.organization, "engineer", "Platform Engineer", inherits=[self.privileged])
        result = run_escalation_analysis(self.organization)
        self.assertGreaterEqual(result["paths"], 1)
        self.assertTrue(
            RiskFinding.objects.filter(
                organization=self.organization,
                category=RiskFinding.Category.ESCALATION_PATH,
            ).exists()
        )

    def test_zero_trust_scores_actual_control_gaps(self):
        profile = IdentityProfile.objects.get(user=self.power_user)
        profile.mfa_enabled = False
        profile.session_timeout_minutes = 120
        profile.save(update_fields=["mfa_enabled", "session_timeout_minutes"])
        create_review(self.power_user)
        result = ZeroTrustEngine(self.organization).evaluate()
        self.assertLess(result["score"], 100)
        self.assertIn("authentication", result["category_scores"])
        self.assertFalse(result["category_scores"]["authentication"] == 100)
        self.assertTrue(
            any("MFA" in recommendation for recommendation in result["recommendations"])
        )

    def test_zero_trust_assessment_is_persisted(self):
        result = run_zero_trust_assessment(self.organization)
        self.assertIn("score", result)
        self.assertTrue(
            RiskFinding.objects.filter(
                organization=self.organization,
                category=RiskFinding.Category.ZERO_TRUST,
            ).exists()
        )
