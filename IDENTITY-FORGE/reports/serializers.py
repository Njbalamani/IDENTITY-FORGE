from rest_framework import serializers

from reports.models import Report


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["id", "title", "report_type", "file", "summary", "generated_by", "created_at"]
        read_only_fields = ["id", "created_at"]
