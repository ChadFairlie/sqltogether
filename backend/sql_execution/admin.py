from django.contrib import admin

from .models import ProjectDatabaseInstance, QueryLog


@admin.register(ProjectDatabaseInstance)
class ProjectDatabaseInstanceAdmin(admin.ModelAdmin):
    list_display = ("project", "engine_type", "created_at", "is_read_only")
    readonly_fields = ("created_at", "last_reset_at")


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ("project", "user", "status", "row_count", "execution_time_ms", "created_at")
    readonly_fields = ("created_at",)
