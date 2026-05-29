import time

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from projects.models import Project

from .models import ProjectDatabaseInstance, QueryLog
from .serializers import QueryLogSerializer, RunQuerySerializer
from .services import SQLExecutionError, SQLiteExecutionService


def user_can_access_project(user, project):
    return project.group.group_members.filter(id=user.id).exists()


def get_accessible_project(user, project_id):
    try:
        project = Project.objects.select_related("group").get(id=project_id)
    except Project.DoesNotExist:
        return None, Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_access_project(user, project):
        return None, Response({"error": "Not authorized"}, status=status.HTTP_403_FORBIDDEN)

    return project, None


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def run_query(request):
    serializer = RunQuerySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    project, error_response = get_accessible_project(request.user, serializer.validated_data["project_id"])
    if error_response:
        return error_response

    try:
        db_instance = project.database_instance
    except ProjectDatabaseInstance.DoesNotExist:
        return Response(
            {"status": "error", "error_type": "database_error", "error_message": "Project database is missing."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    sql = serializer.validated_data["sql"]
    service = SQLiteExecutionService()
    start = time.monotonic()

    try:
        result = service.execute(db_instance.file_path, sql, read_only=db_instance.is_read_only)
        query_log = QueryLog.objects.create(
            project=project,
            user=request.user,
            query_text=sql,
            status=QueryLog.STATUS_SUCCESS,
            row_count=result.row_count,
            execution_time_ms=result.execution_time_ms,
        )
        return Response(
            {
                "status": "success",
                "columns": result.columns,
                "rows": result.rows,
                "row_count": result.row_count,
                "affected_rows": result.affected_rows,
                "execution_time_ms": result.execution_time_ms,
                "truncated": result.truncated,
                "query_id": query_log.id,
            },
            status=status.HTTP_200_OK,
        )
    except SQLExecutionError as exc:
        elapsed_ms = max(0, int((time.monotonic() - start) * 1000))
        log_status = QueryLog.STATUS_TIMEOUT if exc.error_type == "timeout" else QueryLog.STATUS_ERROR
        query_log = QueryLog.objects.create(
            project=project,
            user=request.user,
            query_text=sql,
            status=log_status,
            error_message=service.sanitize_error(exc.message),
            execution_time_ms=elapsed_ms,
        )
        return Response(
            {
                "status": "error",
                "error_type": exc.error_type,
                "error_message": service.sanitize_error(exc.message),
                "execution_time_ms": elapsed_ms,
                "query_id": query_log.id,
            },
            status=status.HTTP_200_OK,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def query_history(request, project_id):
    project, error_response = get_accessible_project(request.user, project_id)
    if error_response:
        return error_response

    try:
        limit = int(request.query_params.get("limit", 50))
    except (TypeError, ValueError):
        limit = 50
    limit = min(max(limit, 1), 100)

    queries = QueryLog.objects.filter(project=project).order_by("-created_at")[:limit]
    return Response({"queries": QueryLogSerializer(queries, many=True).data}, status=status.HTTP_200_OK)
