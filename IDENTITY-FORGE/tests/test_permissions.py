from django.test import TestCase

from analysis.engines.permissions import PermissionEngine
from analysis.models import RiskFinding
from analysis.services import run_permission_analysis
from identities.models import IdentityProfile
from tests.factories import (
    assign_role,
    create_organization,
    create_permission,
    create_role,
    create_user,
)


class PermissionEngineTests(TestCase):
    def setUp(self):
        self.organization = create_organization()
        self.low = create_permission(self.organization, "DATA_READ", risk_weight=1)
        self.high = create_permission(
            self.organization,
            "ROLE_ASSIGN",
            risk_weight=9,
            is_high_risk=True,
        )
        self.viewer = create_role(self.organization, "viewer", "Viewer", permissions=[self.low])
        self.privileged = create_role(
            self.organization,
            "admin",
            "Administrator",
            permissions=[self.high],
            is_privileged=True,
            risk_weight=10,
        )
        self.conflicting = create_role(
            self.organization,
            "auditor",
            "Auditor",
            permissions=[self.low],
            conflicts=[self.privileged],
        )

    def test_direct_roles_do_not_include_inherited_permissions(self):
        user = create_user(self.organization, "direct@example.invalid")
        assign_role(user, self.viewer)
        result = PermissionEngine(self.organization).evaluate_user(user)
        self.assertEqual([role.code for role in result["direct_roles"]], ["viewer"])
        self.assertEqual(
            [permission.code for permission in result["effective_permissions"]], ["DATA_READ"]
        )
        self.assertEqual(result["excessive_permissions"], [])

    def test_inherited_high_risk_permission_is_excessive(self):
        inheriting = create_role(
            self.organization,
            "operator",
            "Operator",
            permissions=[self.low],
            inherits=[self.privileged],
        )
        user = create_user(self.organization, "operator@example.invalid")
        assign_role(user, inheriting)
        result = PermissionEngine(self.organization).evaluate_user(user)
        self.assertIn(self.high, result["effective_permissions"])
        self.assertIn(self.high, result["excessive_permissions"])
        self.assertEqual(result["privilege_score"], 10)

    def test_conflicting_roles_are_detected(self):
        user = create_user(self.organization, "conflict@example.invalid")
        assign_role(user, self.privileged)
        assign_role(user, self.conflicting)
        result = PermissionEngine(self.organization).evaluate_user(user)
        self.assertEqual(len(result["conflicts"]), 1)
        self.assertCountEqual(result["conflicts"][0]["roles"], ["Administrator", "Auditor"])

    def test_inactive_account_with_access_is_detected(self):
        user = create_user(self.organization, "stale@example.invalid")
        profile = IdentityProfile.objects.get(user=user)
        profile.status = IdentityProfile.Status.INACTIVE
        profile.save(update_fields=["status"])
        assign_role(user, self.viewer)
        result = PermissionEngine(self.organization).evaluate_user(user)
        self.assertTrue(result["inactive_access"])

    def test_permission_analysis_persists_findings(self):
        inheriting = create_role(
            self.organization,
            "operator",
            "Operator",
            permissions=[self.low],
            inherits=[self.privileged],
        )
        user = create_user(self.organization, "risk@example.invalid")
        assign_role(user, inheriting)
        result = run_permission_analysis(self.organization)
        self.assertGreater(result["new_findings"], 0)
        self.assertTrue(
            RiskFinding.objects.filter(
                organization=self.organization,
                category=RiskFinding.Category.EXCESSIVE_PRIVILEGE,
                user=user,
            ).exists()
        )
