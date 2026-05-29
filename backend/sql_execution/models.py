from django.conf import settings
from django.db import models


class ProjectDatabaseInstance(models.Model):
    project = models.OneToOneField(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="database_instance",
    )
    engine_type = models.CharField(max_length=20, default="sqlite")
    file_path = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    last_reset_at = models.DateTimeField(null=True, blank=True)
    is_read_only = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.engine_type} database for project {self.project_id}"


class QueryLog(models.Model):
    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"
    STATUS_TIMEOUT = "timeout"

    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Success"),
        (STATUS_ERROR, "Error"),
        (STATUS_TIMEOUT, "Timeout"),
    ]

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="query_logs",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    query_text = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True)
    row_count = models.IntegerField(null=True, blank=True)
    execution_time_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.status} query for project {self.project_id}"
