import os
import shutil
import tempfile
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from codes.models import Code
from projects.models import Project
from sql_execution.models import ProjectDatabaseInstance, QueryLog
from sql_execution.services import SQLiteExecutionService
from usergroups.models import Group
from users.models import User


TEST_DATA_DIR = tempfile.mkdtemp(prefix="sqltogether-test-")


@override_settings(
    SQLTOGETHER_DATA_DIR=TEST_DATA_DIR,
    SQLTOGETHER_QUERY_TIMEOUT_SECONDS=1,
    SQLTOGETHER_MAX_RESULT_ROWS=3,
    SQLTOGETHER_MAX_QUERY_LENGTH=200,
    SQLTOGETHER_MAX_DB_SIZE_MB=50,
)
class SQLExecutionAPITests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user("student@example.com", "testpass")
        self.other_user = User.objects.create_user("other@example.com", "testpass")
        self.group = Group.objects.create(owner=self.user, group_name="Class")
        self.group.group_members.add(self.user)
        self.project = Project.objects.create(project_name="Sandbox", group=self.group)
        Code.objects.create(project=self.project, content="SELECT 1;")
        db_path = SQLiteExecutionService().create_project_database(self.project.id)
        self.db_instance = ProjectDatabaseInstance.objects.create(project=self.project, file_path=db_path)

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    def test_project_creation_creates_database_instance_and_file(self):
        self.authenticate()
        response = self.client.post(
            f"/groups/{self.group.id}/projects/create/",
            {"project_name": "Created from API", "template": "none"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        project = Project.objects.get(id=response.data["id"])
        self.assertTrue(hasattr(project, "database_instance"))
        self.assertTrue(os.path.exists(project.database_instance.file_path))

    def test_run_query_requires_authentication(self):
        response = self.client.post(
            "/api/query/run/",
            {"project_id": self.project.id, "sql": "SELECT 1;"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_run_query_rejects_non_member(self):
        self.authenticate(self.other_user)
        response = self.client.post(
            "/api/query/run/",
            {"project_id": self.project.id, "sql": "SELECT 1;"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_member_can_run_write_statements_and_final_select(self):
        self.authenticate()
        sql = """
        CREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT);
        INSERT INTO students (name) VALUES ('Ada'), ('Grace');
        SELECT id, name FROM students ORDER BY id;
        """
        response = self.client.post(
            "/api/query/run/",
            {"project_id": self.project.id, "sql": sql},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["columns"], ["id", "name"])
        self.assertEqual(response.data["rows"], [[1, "Ada"], [2, "Grace"]])
        self.assertIsNotNone(response.data["query_id"])
        self.assertEqual(QueryLog.objects.filter(project=self.project).count(), 1)

    def test_projects_use_isolated_sqlite_files(self):
        other_project = Project.objects.create(project_name="Other", group=self.group)
        other_path = SQLiteExecutionService().create_project_database(other_project.id)
        ProjectDatabaseInstance.objects.create(project=other_project, file_path=other_path)

        self.authenticate()
        self.client.post(
            "/api/query/run/",
            {"project_id": self.project.id, "sql": "CREATE TABLE private_data (value TEXT); INSERT INTO private_data VALUES ('secret');"},
            format="json",
        )
        response = self.client.post(
            "/api/query/run/",
            {"project_id": other_project.id, "sql": "SELECT * FROM private_data;"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "error")
        self.assertNotIn(self.db_instance.file_path, response.data["error_message"])

    def test_dangerous_commands_and_overlong_sql_are_controlled_errors(self):
        self.authenticate()
        cases = [
            ("ATTACH DATABASE '/tmp/other.db' AS other;", "blocked_command"),
            ("DETACH DATABASE other;", "blocked_command"),
            ("SELECT load_extension('x');", "blocked_command"),
            ("PRAGMA database_list;", "blocked_command"),
            ("SELECT " + ",".join(["1"] * 300) + ";", "query_too_long"),
        ]

        for sql, error_type in cases:
            response = self.client.post(
                "/api/query/run/",
                {"project_id": self.project.id, "sql": sql},
                format="json",
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["status"], "error")
            self.assertEqual(response.data["error_type"], error_type)
            self.assertNotIn("/", response.data["error_message"])

    def test_row_limit_truncation_blob_and_null_conversion(self):
        self.authenticate()
        response = self.client.post(
            "/api/query/run/",
            {
                "project_id": self.project.id,
                "sql": """
                CREATE TABLE values_table (id INTEGER, payload BLOB, note TEXT);
                INSERT INTO values_table VALUES (1, x'0011', NULL), (2, x'0011', 'b'), (3, x'0011', 'c'), (4, x'0011', 'd');
                SELECT id, payload, note FROM values_table ORDER BY id;
                """,
            },
            format="json",
        )

        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["row_count"], 3)
        self.assertTrue(response.data["truncated"])
        self.assertEqual(response.data["rows"][0], [1, "[BLOB]", None])

    def test_query_history_requires_membership_and_hides_paths(self):
        self.authenticate()
        self.client.post(
            "/api/query/run/",
            {"project_id": self.project.id, "sql": "SELECT * FROM missing_table;"},
            format="json",
        )

        response = self.client.get(f"/api/projects/{self.project.id}/query-history/?limit=5")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["queries"]), 1)
        self.assertNotIn("file_path", response.data["queries"][0])
        self.assertNotIn("/", response.data["queries"][0]["error_message"])

        self.authenticate(self.other_user)
        forbidden = self.client.get(f"/api/projects/{self.project.id}/query-history/?limit=5")
        self.assertEqual(forbidden.status_code, 403)

    def test_execution_service_does_not_use_django_default_cursor_for_student_sql(self):
        with mock.patch("django.db.connection.cursor") as cursor:
            result = SQLiteExecutionService().execute(self.db_instance.file_path, "SELECT 1;")

        cursor.assert_not_called()
        self.assertEqual(result.rows, [[1]])
