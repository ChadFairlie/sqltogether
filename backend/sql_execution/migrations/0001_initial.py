# Generated manually for SQLTogether Phase 4.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectDatabaseInstance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("engine_type", models.CharField(default="sqlite", max_length=20)),
                ("file_path", models.CharField(max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_reset_at", models.DateTimeField(blank=True, null=True)),
                ("is_read_only", models.BooleanField(default=False)),
                (
                    "project",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="database_instance",
                        to="projects.project",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="QueryLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("query_text", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[("success", "Success"), ("error", "Error"), ("timeout", "Timeout")],
                        max_length=20,
                    ),
                ),
                ("error_message", models.TextField(blank=True)),
                ("row_count", models.IntegerField(blank=True, null=True)),
                ("execution_time_ms", models.IntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="query_logs",
                        to="projects.project",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
