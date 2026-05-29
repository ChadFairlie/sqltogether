# Workflow: SQL MVP Planning

Use this workflow when planning the SQLite MVP implementation (Phase 4 of SQLTogether development).

This workflow ensures the SQL execution layer is designed correctly before any code is written.

---

## Prerequisites

- [ ] Phase 0 (Stabilize) is complete
- [ ] Phase 1 (Rebrand) is complete
- [ ] Phase 2 (Audit) is complete
- [ ] Phase 3 (SQL Editor) is complete
- [ ] You have read `docs/SQL_SANDBOX_STRATEGY.md`
- [ ] You have read `docs/SQLTOGETHER_ARCHITECTURE.md`
- [ ] You have read `.agent/rules/sql-safety-rules.md`

---

## Step 1: Confirm Application DB vs Learning DB Separation

Before writing any code, explicitly confirm:

- [ ] The Django app database (PostgreSQL) is accessed ONLY via Django ORM
- [ ] Student SQL will execute against separate SQLite files
- [ ] No Django `DATABASES` entry will be used for student queries
- [ ] The execution service opens SQLite connections directly (not via Django ORM)

Document the separation in your implementation plan.

---

## Step 2: Propose Models

Design the Django models for the new `sql_execution` app:

### ProjectDatabaseInstance

```
Fields to define:
- project (OneToOne to projects.Project)
- template (FK to DatabaseTemplate, nullable for Phase 4 — templates come in Phase 5)
- engine_type (CharField, default='sqlite')
- file_path (CharField — internal, never exposed to API)
- created_at (DateTimeField)
- last_reset_at (DateTimeField, nullable)
- is_read_only (BooleanField, default=False)
```

### QueryLog

```
Fields to define:
- project (FK to projects.Project)
- user (FK to users.User)
- query_text (TextField)
- status (CharField: 'success', 'error', 'timeout')
- error_message (TextField, blank)
- row_count (IntegerField, nullable)
- execution_time_ms (IntegerField, nullable)
- created_at (DateTimeField)
```

### DatabaseTemplate (Placeholder for Phase 5)

Do NOT implement templates in Phase 4. But design the ProjectDatabaseInstance model to support a template FK that will be added later.

---

## Step 3: Propose Endpoints

### Run Query

```
POST /api/query/run/

Request:
{
  "project_id": 42,
  "sql": "SELECT * FROM students WHERE grade > 80"
}

Response (success):
{
  "status": "success",
  "columns": ["id", "name", "grade"],
  "rows": [[1, "Alice", 95], [2, "Bob", 88]],
  "row_count": 2,
  "execution_time_ms": 12,
  "truncated": false
}

Response (error):
{
  "status": "error",
  "error_type": "syntax_error",
  "error_message": "near \"SELEC\": syntax error",
  "execution_time_ms": 1
}

Response (timeout):
{
  "status": "error",
  "error_type": "timeout",
  "error_message": "Query exceeded the 5 second time limit.",
  "execution_time_ms": 5000
}
```

### Query History

```
GET /api/projects/{pid}/query-history/?limit=50

Response:
{
  "queries": [
    {
      "id": 1,
      "query_text": "SELECT * FROM students",
      "status": "success",
      "row_count": 10,
      "execution_time_ms": 5,
      "created_at": "2026-05-29T12:00:00Z"
    }
  ]
}
```

---

## Step 4: Project Database File Layout

Define where project SQLite files will be stored:

```
Proposed layout:
  {SQLTOGETHER_DATA_DIR}/projects/{project_id}.db

Default SQLTOGETHER_DATA_DIR:
  Development: ./data/  (inside backend directory)
  Docker: /data/  (Docker volume)

Configuration:
  Add SQLTOGETHER_DATA_DIR to Django settings
  Add SQLTOGETHER_QUERY_TIMEOUT_SECONDS = 5
  Add SQLTOGETHER_MAX_RESULT_ROWS = 1000
  Add SQLTOGETHER_MAX_QUERY_LENGTH = 10000
  Add SQLTOGETHER_MAX_DB_SIZE_MB = 50
```

- [ ] Confirm the data directory will NOT be inside the Django project source tree in production
- [ ] Confirm the data directory is added to `.gitignore`
- [ ] Confirm the Docker volume mapping for the data directory

---

## Step 5: Query Execution Service Design

Design the `SQLiteExecutionService`:

```python
class SQLiteExecutionService:
    """Executes SQL queries against isolated SQLite project databases."""

    def execute(self, db_path: str, sql: str, read_only: bool = True) -> QueryResult:
        """
        1. Validate query length
        2. Open SQLite connection to db_path
        3. Set PRAGMA query_only if read_only
        4. Set timeout handler
        5. Execute SQL
        6. Fetch up to MAX_RESULT_ROWS + 1 rows
        7. Determine if truncated
        8. Return QueryResult
        9. Close connection in finally block
        """

    def create_project_database(self, project_id: int) -> str:
        """
        1. Determine file path: {DATA_DIR}/projects/{project_id}.db
        2. Create empty SQLite database at that path
        3. Return the file path
        """

    def reset_project_database(self, project_id: int, template_path: str = None) -> None:
        """
        1. Determine file path: {DATA_DIR}/projects/{project_id}.db
        2. Delete existing file
        3. If template_path provided: copy template to project path
        4. Else: create empty database
        """
```

Key design decisions to document:
- [ ] How is the timeout implemented? (progress handler, separate thread, signal?)
- [ ] How are dangerous commands blocked? (SQL parsing, PRAGMA, or both?)
- [ ] How is the connection managed? (open/close per request, no pooling)
- [ ] How are errors sanitized? (strip file paths from SQLite error messages)

---

## Step 6: Result Response Shape

Define the exact response format for the frontend:

### Success Response

```json
{
  "status": "success",
  "columns": ["column_name_1", "column_name_2"],
  "rows": [
    ["value_1a", "value_1b"],
    ["value_2a", "value_2b"]
  ],
  "row_count": 2,
  "execution_time_ms": 12,
  "truncated": false,
  "query_id": 42
}
```

### Error Response

```json
{
  "status": "error",
  "error_type": "syntax_error | timeout | permission_denied | file_error | query_too_long",
  "error_message": "Human-readable error message (sanitized)",
  "execution_time_ms": 1,
  "query_id": 43
}
```

### Data Types

- [ ] How are SQLite types mapped to JSON? (INTEGER → number, TEXT → string, REAL → number, BLOB → base64 or null, NULL → null)
- [ ] How are dates handled? (as strings)
- [ ] How are very long text values handled? (truncate individual cells?)

---

## Step 7: Error Response Shape

Define error types and messages:

| Error Type | When | Example Message |
|-----------|------|-----------------|
| `syntax_error` | SQL syntax is invalid | `near "SELEC": syntax error` |
| `timeout` | Query exceeds time limit | `Query exceeded the 5 second time limit.` |
| `permission_denied` | Write query in read-only mode | `This project is in read-only mode. Only SELECT queries are allowed.` |
| `query_too_long` | Query exceeds length limit | `Query exceeds the maximum length of 10,000 characters.` |
| `blocked_command` | ATTACH, LOAD_EXTENSION, etc. | `This SQL command is not allowed.` |
| `database_error` | File corruption, missing DB | `Database error. Try resetting the project database.` |
| `unknown_error` | Unexpected failure | `An unexpected error occurred. Please try again.` |

- [ ] Error messages must NEVER contain filesystem paths
- [ ] Error messages must be helpful for SQL learners

---

## Step 8: Reset Flow

Design the database reset mechanism:

```
1. User clicks "Reset Database" in the UI
2. Frontend sends POST /api/projects/{pid}/reset-database/
3. Backend validates:
   - User is authenticated
   - User is a member of the project's group
   - Project has a ProjectDatabaseInstance
4. Backend calls SQLiteExecutionService.reset_project_database()
5. Service deletes the project .db file
6. Service copies template .db (or creates empty DB if no template)
7. Updates ProjectDatabaseInstance.last_reset_at
8. Returns success
9. Frontend notifies user and optionally refreshes query history
```

---

## Step 9: Safety Checklist

Before implementation begins, confirm all safety measures are planned:

- [ ] Student SQL never touches the app database (PostgreSQL)
- [ ] Each project has its own isolated SQLite file
- [ ] Query timeout is enforced (default 5 seconds)
- [ ] Row limit is enforced (default 1000 rows)
- [ ] Query length limit is enforced (default 10,000 characters)
- [ ] `ATTACH DATABASE` is blocked
- [ ] `LOAD_EXTENSION` is blocked
- [ ] `PRAGMA query_only = ON` used for read-only mode
- [ ] Filesystem paths never in API responses or error messages
- [ ] SQLite error messages are sanitized
- [ ] Connections are closed after each query
- [ ] Auth and group membership verified before execution
- [ ] Query text is logged to QueryLog
- [ ] Database file size limits are checked

---

## Output

After completing this workflow, you should have:

1. Confirmed app DB / learning DB separation
2. Model definitions for ProjectDatabaseInstance and QueryLog
3. Endpoint specifications with request/response shapes
4. File layout for project databases
5. SQLiteExecutionService design
6. Error handling strategy
7. Reset flow design
8. Complete safety checklist confirmed

**Do not start coding until all steps are complete and reviewed.**
