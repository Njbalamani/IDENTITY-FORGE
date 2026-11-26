from collections import defaultdict

import pandas as pd
from django.conf import settings
from sklearn.ensemble import IsolationForest

from access.models import AccessEvent

FEATURE_NAMES = [
    "event_count",
    "failed_ratio",
    "unique_resources",
    "privileged_action_ratio",
    "off_hours_count",
    "mfa_challenge_ratio",
]
PRIVILEGED_TYPES = {"PERMISSION_CHANGE", "ROLE_ASSIGNED", "ADMIN_ACTION"}


class AnomalyEngine:
    def __init__(self, organization):
        self.organization = organization

    @staticmethod
    def build_rows(events):
        grouped = defaultdict(list)
        for event in events:
            grouped[(event.user_id, event.occurred_at.date())].append(event)
        rows = []
        for (user_id, event_date), group in grouped.items():
            count = len(group)
            failed = sum(
                1 for event in group if event.event_type == "LOGIN_FAILED" or not event.success
            )
            privileged = sum(1 for event in group if event.event_type in PRIVILEGED_TYPES)
            off_hours = sum(
                1 for event in group if event.occurred_at.hour < 7 or event.occurred_at.hour >= 19
            )
            mfa = sum(1 for event in group if event.event_type == "MFA_CHALLENGE")
            rows.append(
                {
                    "user_id": user_id,
                    "event_date": event_date,
                    "event_count": count,
                    "failed_ratio": round(failed / count, 4),
                    "unique_resources": len(
                        {event.resource_id for event in group if event.resource_id}
                    ),
                    "privileged_action_ratio": round(privileged / count, 4),
                    "off_hours_count": off_hours,
                    "mfa_challenge_ratio": round(mfa / count, 4),
                }
            )
        return sorted(rows, key=lambda row: (row["user_id"], row["event_date"]))

    @staticmethod
    def build_reasons(row, means, stds, top_count=3):
        contributors = []
        for name in FEATURE_NAMES:
            deviation = stds[name]
            if deviation <= 0:
                continue
            z_score = (row[name] - means[name]) / deviation
            if z_score > 0.5:
                contributors.append((z_score, name, row[name], means[name]))
        contributors.sort(reverse=True)
        reasons = [
            f"{name.replace('_', ' ')} is {value} versus baseline {mean:.2f}"
            for _, name, value, mean in contributors[:top_count]
        ]
        if not reasons:
            reasons.append("Event pattern is isolated in the multivariate feature space")
        return reasons

    def analyze(self, events=None):
        if events is None:
            events = list(
                AccessEvent.objects.filter(organization=self.organization).select_related(
                    "user", "resource"
                )
            )
        rows = self.build_rows(events)
        if not rows:
            return []
        frame = pd.DataFrame(rows)[FEATURE_NAMES]
        means = {name: float(frame[name].mean()) for name in FEATURE_NAMES}
        stds = {name: float(frame[name].std(ddof=0)) for name in FEATURE_NAMES}
        matrix = frame.to_numpy(dtype=float)
        results = []

        if len(rows) >= settings.ANOMALY_MIN_SAMPLES:
            model = IsolationForest(
                n_estimators=120,
                contamination=settings.ANOMALY_CONTAMINATION,
                random_state=42,
            )
            predictions = model.fit_predict(matrix)
            raw_scores = -model.score_samples(matrix)
            for index, row in enumerate(rows):
                is_anomaly = bool(predictions[index] == -1)
                results.append(
                    {
                        **row,
                        "anomaly_score": round(float(raw_scores[index]), 4),
                        "is_anomaly": is_anomaly,
                        "reasons": self.build_reasons(row, means, stds) if is_anomaly else [],
                        "model_name": "isolation-forest",
                    }
                )
            return results

        for row in rows:
            deviations = [
                (row[name] - means[name]) / stds[name] for name in FEATURE_NAMES if stds[name] > 0
            ]
            score = round(float(max(deviations, default=0.0)), 4)
            is_anomaly = bool(score >= 2.0 and row["event_count"] > means["event_count"])
            results.append(
                {
                    **row,
                    "anomaly_score": score,
                    "is_anomaly": is_anomaly,
                    "reasons": self.build_reasons(row, means, stds) if is_anomaly else [],
                    "model_name": "statistical-baseline",
                }
            )
        return results

    @staticmethod
    def features_for(result):
        return {name: result[name] for name in FEATURE_NAMES}
