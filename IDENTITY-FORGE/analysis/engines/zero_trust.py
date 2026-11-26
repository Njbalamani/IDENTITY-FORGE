from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from access.models import AccessEvent, AccessReview
from identities.models import IdentityProfile


class ZeroTrustEngine:
    def __init__(self, organization):
        self.organization = organization

    @staticmethod
    def safe_ratio(numerator, denominator):
        return float(numerator) / float(denominator) if denominator else 0.0

    def evaluate(self):
        from django.contrib.auth import get_user_model

        from analysis.models import RiskFinding

        users = list(
            get_user_model().objects.filter(organization=self.organization, is_active=True)
        )
        total = len(users)
        now = timezone.now()
        profiles = {
            profile.user_id: profile
            for profile in IdentityProfile.objects.filter(organization=self.organization)
        }
        excessive_users = set(
            RiskFinding.objects.filter(
                organization=self.organization,
                category=RiskFinding.Category.EXCESSIVE_PRIVILEGE,
                status=RiskFinding.Status.OPEN,
                user__isnull=False,
            ).values_list("user_id", flat=True)
        )
        conflict_users = set(
            RiskFinding.objects.filter(
                organization=self.organization,
                category=RiskFinding.Category.CONFLICTING_ROLE,
                status=RiskFinding.Status.OPEN,
                user__isnull=False,
            ).values_list("user_id", flat=True)
        )
        mfa_users = [
            user.id for user in users if profiles.get(user.id) and profiles[user.id].mfa_enabled
        ]
        long_sessions = [
            user.id
            for user in users
            if profiles.get(user.id)
            and profiles[user.id].session_timeout_minutes > settings.SESSION_TIMEOUT_LIMIT_MINUTES
        ]
        inactive_with_access = set(
            RiskFinding.objects.filter(
                organization=self.organization,
                category=RiskFinding.Category.INACTIVE_ACCESS,
                status=RiskFinding.Status.OPEN,
                user__isnull=False,
            ).values_list("user_id", flat=True)
        )
        reviews = AccessReview.objects.filter(organization=self.organization)
        overdue_reviews = reviews.filter(
            status__in=["PENDING", "IN_PROGRESS"], due_date__lt=now
        ).count()
        recent_events = AccessEvent.objects.filter(
            organization=self.organization,
            occurred_at__gte=now - timedelta(days=30),
        ).count()

        category_scores = {
            "least_privilege": int(round(100 * (1 - self.safe_ratio(len(excessive_users), total)))),
            "authentication": int(round(100 * self.safe_ratio(len(mfa_users), total))),
            "role_separation": int(round(100 * (1 - self.safe_ratio(len(conflict_users), total)))),
            "session_controls": int(round(100 * (1 - self.safe_ratio(len(long_sessions), total)))),
            "access_reviews": int(
                round(100 * (1 - self.safe_ratio(overdue_reviews, max(1, reviews.count()))))
            ),
            "account_lifecycle": int(
                round(100 * (1 - self.safe_ratio(len(inactive_with_access), total)))
            ),
        }
        findings = [
            f"{len(excessive_users)} identities carry findings for excessive permissions.",
            f"{total - len(mfa_users)} identities do not have MFA recorded.",
            f"{len(conflict_users)} identities have mutually exclusive roles.",
            f"{len(long_sessions)} identities exceed the {settings.SESSION_TIMEOUT_LIMIT_MINUTES}-minute session limit.",
            f"{overdue_reviews} access reviews are overdue.",
            f"{len(inactive_with_access)} inactive identities still have active assignments.",
        ]
        recommendations = [
            "Require MFA for every privileged role and verify the control through access reviews.",
            "Remove inherited high-risk permissions that are not explicitly justified.",
            "Enforce mutually exclusive role pairs in the assignment workflow.",
            f"Reduce session timeouts to {settings.SESSION_TIMEOUT_LIMIT_MINUTES} minutes or less.",
            "Complete overdue access reviews and evidence reviewer decisions in the audit trail.",
            "Disable or revoke access for inactive and terminated identities immediately.",
        ]
        weights = settings.ZERO_TRUST_RULES
        weighted_total = sum(
            category_scores[key] * weights[key]["weight"] for key in category_scores
        )
        weight_sum = sum(weights[key]["weight"] for key in category_scores)
        overall = int(round(weighted_total / weight_sum)) if weight_sum else 0
        return {
            "score": overall,
            "category_scores": category_scores,
            "findings": findings,
            "recommendations": recommendations,
            "evidence": {
                "identity_count": total,
                "recent_event_count": recent_events,
                "mfa_count": len(mfa_users),
                "overdue_review_count": overdue_reviews,
            },
        }
