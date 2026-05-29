from rest_framework import serializers

from .models import QueryLog


class RunQuerySerializer(serializers.Serializer):
    project_id = serializers.IntegerField()
    sql = serializers.CharField(allow_blank=False, trim_whitespace=False)


class QueryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryLog
        fields = [
            "id",
            "query_text",
            "status",
            "error_message",
            "row_count",
            "execution_time_ms",
            "created_at",
        ]
