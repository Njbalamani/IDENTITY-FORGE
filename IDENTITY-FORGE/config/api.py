from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from access.api import (
    AccessEventViewSet,
    AccessResourceViewSet,
    AccessReviewViewSet,
    PermissionViewSet,
    RoleAssignmentViewSet,
    RoleViewSet,
)
from accounts.api import CurrentUserAPIView, RegisterAPIView, UserViewSet
from analysis.api import (
    AccessGraphAPIView,
    AIStatusAPIView,
    AnalysisRunViewSet,
    AnomalyResultViewSet,
    RiskFindingViewSet,
    RunAnalysisAPIView,
    ZeroTrustAssessmentViewSet,
)
from audit.api import AuditLogViewSet
from certification.api import CampaignItemViewSet, CampaignViewSet
from dashboard.api import DashboardMetricsAPIView
from identities.api import IdentityProfileViewSet, TeamViewSet
from organizations.api import OrganizationViewSet
from reports.api import GenerateReportAPIView, ReportViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("organizations", OrganizationViewSet, basename="organization")
router.register("teams", TeamViewSet, basename="team")
router.register("profiles", IdentityProfileViewSet, basename="profile")
router.register("permissions", PermissionViewSet, basename="permission")
router.register("roles", RoleViewSet, basename="role")
router.register("assignments", RoleAssignmentViewSet, basename="assignment")
router.register("resources", AccessResourceViewSet, basename="resource")
router.register("events", AccessEventViewSet, basename="event")
router.register("reviews", AccessReviewViewSet, basename="review")
router.register("findings", RiskFindingViewSet, basename="finding")
router.register("anomalies", AnomalyResultViewSet, basename="anomaly")
router.register("assessments", ZeroTrustAssessmentViewSet, basename="assessment")
router.register("analysis-runs", AnalysisRunViewSet, basename="analysis-run")
router.register("reports", ReportViewSet, basename="report")
router.register("audit-logs", AuditLogViewSet, basename="audit-log")
router.register("certification-campaigns", CampaignViewSet, basename="certification-campaign")
router.register("certification-items", CampaignItemViewSet, basename="certification-item")

urlpatterns = [
    path("auth/register/", RegisterAPIView.as_view(), name="api-register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/me/", CurrentUserAPIView.as_view(), name="api-me"),
    path("graph/", AccessGraphAPIView.as_view(), name="api-graph"),
    path("dashboard/metrics/", DashboardMetricsAPIView.as_view(), name="api-dashboard-metrics"),
    path("analysis/run/", RunAnalysisAPIView.as_view(), name="api-analysis-run"),
    path("ai/status/", AIStatusAPIView.as_view(), name="api-ai-status"),
    path("reports/generate/", GenerateReportAPIView.as_view(), name="api-report-generate"),
    path("", include(router.urls)),
]
