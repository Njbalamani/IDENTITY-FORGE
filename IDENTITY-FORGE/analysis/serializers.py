from rest_framework import serializers

from analysis.models import AnalysisRun, AnomalyResult, RiskFinding, ZeroTrustAssessment


class RiskFindingSerializer(serializers.ModelSerializer):
    nist_controls = serializers.ReadOnlyField()
    cis_controls = serializers.ReadOnlyField()
    zero_trust_principles = serializers.ReadOnlyField()

    class Meta:
        model = RiskFinding
        fields = [
            "id",
            "category",
            "severity",
            "title",
            "description",
            "evidence",
            "recommendation",
            "nist_controls",
            "cis_controls",
            "zero_trust_principles",
            "user",
            "resource",
            "score",
            "status",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "reviewed_by", "reviewed_at"]


class AnomalyResultSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = AnomalyResult
        fields = [
            "id",
            "user",
            "username",
            "event_date",
            "anomaly_score",
            "is_anomaly",
            "reasons",
            "features",
            "model_name",
            "detected_at",
        ]
        read_only_fields = fields


class ZeroTrustAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZeroTrustAssessment
        fields = ["id", "score", "category_scores", "findings", "recommendations", "created_at"]
        read_only_fields = fields


class AnalysisRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisRun
        fields = ["id", "analysis_type", "status", "details", "started_at", "completed_at"]
        read_only_fields = fields
