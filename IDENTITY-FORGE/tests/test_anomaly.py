from datetime import timedelta
from io import BytesIO

from django.test import TestCase, override_settings
from django.utils import timezone

from analysis.engines.anomaly import FEATURE_NAMES, AnomalyEngine
from analysis.imports import import_access_events, validate_access_event_csv
from analysis.models import AnomalyResult, RiskFinding
from analysis.services import run_anomaly_analysis
from tests.factories import create_organization, create_resource, create_user


@override_settings(ANOMALY_MIN_SAMPLES=99)
class AnomalyAnalysisTests(TestCase):
    def setUp(self):
        self.organization = create_organization()
        self.user = create_user(self.organization, "anomaly@example.invalid")
        self.spike_user = create_user(self.organization, "spike@example.invalid")
        self.resource = create_resource(self.organization, "claims-warehouse")

    def build_events(self):
        base = timezone.now().replace(hour=12, minute=0, second=0, microsecond=0)
        events = []
        for day in range(6):
            for _ in range(1):
                events.append(self.make_event(self.user, base - timedelta(days=day + 1)))
        for _ in range(40):
            events.append(self.make_event(self.spike_user, base - timedelta(days=8), hour=3))
        return events

    def make_event(self, user, occurred_at, hour=None):
        from tests.factories import create_event

        timestamp = occurred_at.replace(hour=hour) if hour is not None else occurred_at
        return create_event(user, occurred_at=timestamp, resource=self.resource)

    def test_feature_engineering_uses_observed_events(self):
        rows = AnomalyEngine.build_rows(self.build_events())
        self.assertEqual(len(rows), 7)
        spike = next(row for row in rows if row["user_id"] == self.spike_user.id)
        self.assertEqual(spike["event_count"], 40)
        self.assertEqual(spike["off_hours_count"], 40)
        for name in FEATURE_NAMES:
            self.assertIn(name, spike)

    def test_anomaly_engine_explains_flagged_profile(self):
        rows = AnomalyEngine(self.organization).analyze(self.build_events())
        flagged = [row for row in rows if row["is_anomaly"]]
        self.assertTrue(flagged)
        self.assertTrue(flagged[0]["reasons"])
        self.assertEqual(flagged[0]["model_name"], "statistical-baseline")

    def test_anomaly_service_persists_results_and_findings(self):
        result = run_anomaly_analysis(self.organization, self.build_events())
        self.assertGreaterEqual(result["anomalies"], 1)
        self.assertTrue(
            AnomalyResult.objects.filter(organization=self.organization, is_anomaly=True).exists()
        )
        self.assertTrue(
            RiskFinding.objects.filter(
                organization=self.organization,
                category=RiskFinding.Category.ANOMALY_DETECTION,
            ).exists()
        )

    def test_valid_csv_import_creates_events(self):
        csv_content = (
            "username,event_type,occurred_at,success,resource,source,ip_address,user_agent\n"
            f"{self.user.username},LOGIN,2026-11-20T10:00:00Z,true,claims-warehouse,IMPORTED,203.0.113.10,agent\n"
        )
        uploaded = BytesIO(csv_content.encode("utf-8"))
        uploaded.name = "events.csv"
        count = import_access_events(self.organization, uploaded)
        self.assertEqual(count, 1)
        from access.models import AccessEvent

        self.assertTrue(
            AccessEvent.objects.filter(
                organization=self.organization,
                source=AccessEvent.Source.IMPORTED,
            ).exists()
        )

    def test_csv_import_rejects_unknown_users(self):
        csv_content = (
            "username,event_type,occurred_at,success,resource,source\n"
            "ghost@example.invalid,LOGIN,2026-11-20T10:00:00Z,true,claims-warehouse,IMPORTED\n"
        )
        uploaded = BytesIO(csv_content.encode("utf-8"))
        uploaded.name = "events.csv"
        with self.assertRaises(ValueError) as context:
            validate_access_event_csv(uploaded, self.organization)
        self.assertIn("Unknown usernames", str(context.exception))

    def test_csv_import_rejects_non_synthetic_identity(self):
        non_synthetic = create_user(self.organization, "real.person@example.com")
        csv_content = (
            "username,event_type,occurred_at,success,resource,source\n"
            f"{non_synthetic.username},LOGIN,2026-11-20T10:00:00Z,true,claims-warehouse,IMPORTED\n"
        )
        uploaded = BytesIO(csv_content.encode("utf-8"))
        uploaded.name = "events.csv"
        with self.assertRaises(ValueError) as context:
            validate_access_event_csv(uploaded, self.organization)
        self.assertIn("Synthetic-only mode", str(context.exception))
