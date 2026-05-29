import os
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings


class SQLExecutionError(Exception):
    error_type = "database_error"

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class SQLTimeoutError(SQLExecutionError):
    error_type = "timeout"


class SQLValidationError(SQLExecutionError):
    error_type = "blocked_command"


class SQLTooLongError(SQLExecutionError):
    error_type = "query_too_long"


@dataclass
class QueryResult:
    status: str
    columns: list
    rows: list
    row_count: int
    affected_rows: int
    execution_time_ms: int
    truncated: bool


class SQLiteExecutionService:
    BLOCKED_PATTERNS = [
        (re.compile(r"\battach\b", re.IGNORECASE), "ATTACH is not allowed."),
        (re.compile(r"\bdetach\b", re.IGNORECASE), "DETACH is not allowed."),
        (re.compile(r"\bload_extension\s*\(", re.IGNORECASE), "Loading extensions is not allowed."),
        (re.compile(r"\bsqlite_db_filename\s*\(", re.IGNORECASE), "Filesystem path functions are not allowed."),
        (re.compile(r"\bpragma_database_list\b", re.IGNORECASE), "Filesystem path metadata is not allowed."),
        (re.compile(r"\breadfile\s*\(", re.IGNORECASE), "Filesystem read functions are not allowed."),
        (re.compile(r"\bwritefile\s*\(", re.IGNORECASE), "Filesystem write functions are not allowed."),
    ]
    SAFE_PRAGMAS = {
        "table_info",
        "table_xinfo",
        "table_list",
        "foreign_key_list",
        "index_list",
        "index_info",
        "index_xinfo",
    }
    ABSOLUTE_PATH_RE = re.compile(r"(/[A-Za-z0-9._~:@%+=,;/-]+)+")

    def __init__(self):
        self.data_dir = Path(settings.SQLTOGETHER_DATA_DIR)
        self.projects_dir = self.data_dir / "projects"
        self.timeout_seconds = settings.SQLTOGETHER_QUERY_TIMEOUT_SECONDS
        self.max_result_rows = settings.SQLTOGETHER_MAX_RESULT_ROWS
        self.max_query_length = settings.SQLTOGETHER_MAX_QUERY_LENGTH
        self.max_db_size_bytes = settings.SQLTOGETHER_MAX_DB_SIZE_MB * 1024 * 1024

    def project_db_path(self, project_id):
        return self.projects_dir / f"{project_id}.db"

    def create_project_database(self, project_id):
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        db_path = self.project_db_path(project_id)
        if db_path.exists():
            db_path.unlink()

        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.commit()
        finally:
            conn.close()
        return str(db_path)

    def delete_project_database(self, db_path):
        try:
            Path(db_path).unlink(missing_ok=True)
        except OSError:
            pass

    def execute(self, db_path, sql, read_only=False):
        start = time.monotonic()
        self._validate_length(sql)
        statements = self._split_statements(sql)
        if not statements:
            raise SQLValidationError("Enter a SQL statement to run.")
        for statement in statements:
            self._validate_statement(statement, read_only=read_only)

        db_path = str(db_path)
        self._validate_db_path(db_path)
        self._validate_db_size(db_path)

        conn = sqlite3.connect(db_path, timeout=self.timeout_seconds)
        deadline = start + self.timeout_seconds

        def timeout_handler():
            if time.monotonic() > deadline:
                return 1
            return 0

        conn.set_progress_handler(timeout_handler, 1000)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            if read_only:
                conn.execute("PRAGMA query_only = ON")
            conn.execute("BEGIN")

            final_columns = []
            final_rows = []
            final_row_count = 0
            affected_rows = 0
            truncated = False

            for statement in statements:
                cursor = conn.execute(statement)
                if cursor.description:
                    final_columns = [column[0] for column in cursor.description]
                    fetched = cursor.fetchmany(self.max_result_rows + 1)
                    truncated = len(fetched) > self.max_result_rows
                    final_rows = [
                        [self._to_json_value(value) for value in row]
                        for row in fetched[: self.max_result_rows]
                    ]
                    final_row_count = len(final_rows)
                else:
                    if cursor.rowcount and cursor.rowcount > 0:
                        affected_rows += cursor.rowcount
                    final_columns = []
                    final_rows = []
                    final_row_count = 0
                    truncated = False

            self._validate_db_size(db_path)
            conn.commit()
            return QueryResult(
                status="success",
                columns=final_columns,
                rows=final_rows,
                row_count=final_row_count,
                affected_rows=affected_rows,
                execution_time_ms=self._elapsed_ms(start),
                truncated=truncated,
            )
        except sqlite3.OperationalError as exc:
            conn.rollback()
            message = self.sanitize_error(str(exc))
            if "interrupted" in message.lower():
                raise SQLTimeoutError(f"Query exceeded the {self.timeout_seconds} second time limit.") from exc
            raise SQLExecutionError(message) from exc
        except sqlite3.DatabaseError as exc:
            conn.rollback()
            raise SQLExecutionError(self.sanitize_error(str(exc))) from exc
        finally:
            conn.set_progress_handler(None, 0)
            conn.close()

    def _split_statements(self, sql):
        statements = []
        buffer = ""
        for char in sql:
            buffer += char
            if sqlite3.complete_statement(buffer):
                statement = buffer.strip()
                if statement:
                    statements.append(statement)
                buffer = ""
        if buffer.strip():
            statements.append(buffer.strip())
        return statements

    def _validate_length(self, sql):
        if len(sql or "") > self.max_query_length:
            raise SQLTooLongError(
                f"Query exceeds the maximum length of {self.max_query_length} characters."
            )

    def _validate_statement(self, statement, read_only=False):
        normalized = self._strip_leading_comments(statement).strip()
        for pattern, message in self.BLOCKED_PATTERNS:
            if pattern.search(normalized):
                raise SQLValidationError(message)

        if re.match(r"^pragma\b", normalized, re.IGNORECASE):
            self._validate_pragma(normalized)

        if read_only and not re.match(r"^(select|with|explain)\b", normalized, re.IGNORECASE):
            raise SQLValidationError("This project is in read-only mode. Only SELECT queries are allowed.")

    def _validate_pragma(self, statement):
        match = re.match(r"^pragma\s+(?:\w+\.)?([A-Za-z_][A-Za-z0-9_]*)", statement, re.IGNORECASE)
        pragma_name = match.group(1).lower() if match else ""
        if pragma_name not in self.SAFE_PRAGMAS:
            raise SQLValidationError("This PRAGMA is not allowed.")

    def _strip_leading_comments(self, statement):
        value = statement.lstrip()
        while True:
            if value.startswith("--"):
                _, _, value = value.partition("\n")
                value = value.lstrip()
            elif value.startswith("/*"):
                end = value.find("*/")
                if end == -1:
                    return value
                value = value[end + 2 :].lstrip()
            else:
                return value

    def _validate_db_path(self, db_path):
        resolved = Path(db_path).resolve()
        projects = self.projects_dir.resolve()
        if not str(resolved).startswith(str(projects) + os.sep):
            raise SQLExecutionError("Database error. Try resetting the project database.")
        if not resolved.exists():
            raise SQLExecutionError("Project database is missing.")

    def _validate_db_size(self, db_path):
        if Path(db_path).exists() and Path(db_path).stat().st_size > self.max_db_size_bytes:
            raise SQLExecutionError("Project database exceeded the allowed size limit.")

    def sanitize_error(self, message):
        sanitized = message or "Database error. Please check your SQL and try again."
        sanitized = sanitized.replace(str(self.data_dir), "[data]")
        sanitized = self.ABSOLUTE_PATH_RE.sub("[path]", sanitized)
        sanitized = sanitized.replace("\n", " ").replace("\r", " ")
        return sanitized[:500]

    def _elapsed_ms(self, start):
        return max(0, int((time.monotonic() - start) * 1000))

    def _to_json_value(self, value):
        if isinstance(value, bytes):
            return "[BLOB]"
        return value
