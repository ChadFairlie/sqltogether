# SQL Sandbox Strategy

## 1. Core Rule

> **Student SQL queries must NEVER execute against the SQLTogether application database.**

The application database (PostgreSQL) stores users, groups, projects, permissions, metadata, and query logs. It is managed exclusively by Django ORM.

Student SQL runs against **isolated project databases** that are completely separate from the application database.

---

## 2. SQLite Template and Project-Copy Model

### How It Works

```
┌─────────────────────┐       file copy       ┌─────────────────────┐
│ DatabaseTemplate    │ ──────────────────────▶│ ProjectDatabase     │
│ /data/templates/    │                        │ /data/projects/     │
│   {template_id}.db  │                        │   {project_id}.db   │
│                     │                        │                     │
│ Read-only master    │                        │ Student sandbox     │
│ Never modified by   │                        │ Writable (if mode   │
│ student queries     │                        │   allows)           │
└─────────────────────┘                        └─────────────────────┘
```

### Template Lifecycle

1. Teacher creates a SQLite database with tables, data, and schema.
2. Teacher uploads the `.db` file to the group via API.
3. The backend stores it at a managed path (e.g., `/data/templates/{template_id}.db`).
4. Template metadata is saved in the app database (`DatabaseTemplate` model).
5. The template file is **never opened in write mode** by the application during student use.

### Project Database Lifecycle

1. Student creates a project and selects a template.
2. Backend copies the template `.db` file to a project path (e.g., `/data/projects/{project_id}.db`).
3. A `ProjectDatabaseInstance` record is created in the app database.
4. All student queries execute against the project `.db` file.
5. The project database can be **reset** by deleting the file and re-copying from the template.

---

## 3. Execution Modes

### Read-Only Mode

- Students can only run `SELECT` and `WITH` (CTE) queries.
- This is the safest default for the MVP.
- `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`, `ALTER` are rejected.
- Enforcement: SQL statement parsing before execution + SQLite `PRAGMA query_only = ON`.

### Sandbox Write Mode

- Students can run any DML/DDL within their isolated project database.
- This mode is useful for exercises that require creating tables or modifying data.
- Still isolated: writes only affect the project's `.db` file.
- Still resettable: teacher or student can reset to the template state.
- Enforcement: no `PRAGMA query_only`, but other limits still apply.

### Mode Configuration

- Mode should be configurable per project or per template.
- Default: read-only for safety.
- Teacher can enable write mode for specific projects or templates.

---

## 4. Teacher/Admin Reset Permissions

### Who Can Reset

- **Group owner (teacher/admin):** Can reset any project in their group.
- **Project member (student):** Can reset their own project (configurable — may want teacher approval).

### Reset Process

1. Close any active connections to the project `.db` file.
2. Delete the project `.db` file.
3. Copy the template `.db` file to the project path.
4. Update `ProjectDatabaseInstance.last_reset_at`.
5. Notify connected users via WebSocket (optional but recommended).
6. Clear or mark query history as "pre-reset" (optional).

### Reset Safety

- Reset is destructive: all student modifications to the database are lost.
- Consider adding a confirmation step in the UI.
- Consider keeping a brief backup before reset (optional, may add complexity).

---

## 5. Query Safety Controls

### 5.1 Query Timeout

| Setting | Default | Notes |
|---------|---------|-------|
| `SQLTOGETHER_QUERY_TIMEOUT_SECONDS` | 5 | Cancel query execution after this duration |

**Implementation for SQLite:**
```python
import sqlite3

conn = sqlite3.connect(db_path)
conn.set_progress_handler(timeout_handler, INSTRUCTION_COUNT_INTERVAL)
# OR: use a separate thread with conn.interrupt() after timeout
```

### 5.2 Row Limit

| Setting | Default | Notes |
|---------|---------|-------|
| `SQLTOGETHER_MAX_RESULT_ROWS` | 1000 | Return at most this many rows |

**Implementation:** Use `LIMIT` injection or fetch only N rows from cursor.

If the query naturally returns more rows, include `"truncated": true` in the response.

### 5.3 Query Length Limit

| Setting | Default | Notes |
|---------|---------|-------|
| `SQLTOGETHER_MAX_QUERY_LENGTH` | 10000 | Reject queries longer than this (characters) |

**Implementation:** Check `len(query_text)` before execution. Return error if exceeded.

### 5.4 Database File Size Limit

| Setting | Default | Notes |
|---------|---------|-------|
| `SQLTOGETHER_MAX_DB_SIZE_MB` | 50 | Max size for a project database file |

**Implementation:** Check file size before and after write operations. Reject operations that would exceed the limit.

### 5.5 Concurrent Query Limit

| Setting | Default | Notes |
|---------|---------|-------|
| `SQLTOGETHER_MAX_CONCURRENT_QUERIES` | 10 | Max concurrent query executions per server |

**Implementation:** Use a semaphore or queue to limit concurrent SQLite connections.

### 5.6 Statement Restrictions (Read-Only Mode)

In read-only mode, only these statement types should be allowed:
- `SELECT`
- `WITH ... SELECT` (CTEs)
- `EXPLAIN` (optional, useful for learning)

Blocked in read-only mode:
- `INSERT`, `UPDATE`, `DELETE`
- `CREATE`, `DROP`, `ALTER`
- `ATTACH`, `DETACH` (critical: prevents accessing other database files)
- `PRAGMA` (except safe read-only ones like `PRAGMA table_info()`)
- `LOAD_EXTENSION`

**Implementation:** Parse the SQL statement before execution. Use a simple prefix check or a proper SQL parser. Additionally, use `PRAGMA query_only = ON` as a defense-in-depth measure.

### 5.7 Dangerous SQLite PRAGMAs to Block

Always block these, regardless of mode:

```
PRAGMA database_list        -- exposes filesystem paths
PRAGMA journal_mode = OFF   -- can corrupt the database
PRAGMA key = ...            -- encryption-related
PRAGMA integrity_check      -- can be slow on large databases
```

Always block:
```
ATTACH DATABASE ...         -- can open arbitrary files on the server
DETACH DATABASE ...
```

---

## 6. Filesystem Path Protection

- **Never expose** the actual filesystem path of template or project database files to users.
- Users see: "Template: Chinook Database" and "Project: My SQL Project"
- Backend sees: `/data/templates/42.db` and `/data/projects/107.db`
- API responses must never include `file_path` fields.
- Error messages from SQLite should be sanitized to remove any path references.

---

## 7. Connection Management

### SQLite Connection Per Request

For the SQLite MVP, use short-lived connections:

```python
def execute_query(db_path: str, sql: str) -> QueryResult:
    conn = sqlite3.connect(db_path, timeout=5)
    try:
        conn.execute("PRAGMA query_only = ON")  # If read-only mode
        cursor = conn.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchmany(MAX_RESULT_ROWS + 1)
        truncated = len(rows) > MAX_RESULT_ROWS
        if truncated:
            rows = rows[:MAX_RESULT_ROWS]
        return QueryResult(columns=columns, rows=rows, truncated=truncated)
    finally:
        conn.close()
```

### Connection Isolation

- Each query execution opens a new connection.
- No connection pooling for project databases (unnecessary for SQLite files).
- Connections are closed immediately after query completion.
- This prevents file locking issues and ensures isolation.

---

## 8. Future PostgreSQL Sandbox Notes

When PostgreSQL is added as an engine (Phase 7+), the sandbox strategy changes:

### Option A: Per-Schema Isolation

- Each project gets its own PostgreSQL schema within a shared database.
- Use `SET search_path = project_{pid}` before queries.
- Create a restricted PostgreSQL role per project with access only to its schema.
- Pros: Lightweight, no extra containers.
- Cons: Harder to fully isolate, shared database server.

### Option B: Per-Container Isolation

- Each project (or group) gets its own PostgreSQL container or pod.
- Maximum isolation but higher resource cost.
- Pros: True isolation, easy reset (destroy and recreate container).
- Cons: Slow to provision, resource-heavy.

### Option C: Per-User Role with Restricted Permissions

- Shared PostgreSQL database with restricted roles.
- Each project's tables are owned by a project-specific role.
- `REVOKE ALL` on all other schemas.
- Pros: Moderate isolation, moderate resource usage.
- Cons: Complex permission management.

**Recommendation:** Start with Option A (per-schema) as it's simplest. Evaluate Option B if security requirements demand stronger isolation.

**Important:** PostgreSQL sandbox is significantly more complex than SQLite. Do not attempt it until SQLite MVP is fully working and tested.

---

## 9. Checklist for SQL Execution Safety

Use this checklist when implementing or reviewing SQL execution:

- [ ] Student SQL never touches the app database (PostgreSQL)
- [ ] Each project has its own isolated database file/instance
- [ ] Templates are never modified by student queries
- [ ] Query timeout is enforced
- [ ] Row limit is enforced
- [ ] Query length limit is enforced
- [ ] `ATTACH DATABASE` is blocked
- [ ] `LOAD_EXTENSION` is blocked
- [ ] Filesystem paths are never exposed in API responses or error messages
- [ ] Connections are closed after each query
- [ ] File size limits are checked
- [ ] Read-only mode uses `PRAGMA query_only = ON` as defense-in-depth
- [ ] Error messages are sanitized (no server paths, no internal details)
- [ ] Auth and group membership are verified before query execution
- [ ] Query text is logged for audit/history purposes
