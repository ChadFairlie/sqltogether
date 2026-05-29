# SQLTogether — Architecture

## 1. Inherited PyTogether Architecture

SQLTogether is adapted from [PyTogether](https://github.com/SJRiz/pytogether). The inherited architecture is:

```
┌──────────────────────────────────────────────────────┐
│  Frontend (React + Vite)                             │
│  - CodeMirror editor (Python mode)                   │
│  - Y.js CRDT for real-time collaboration             │
│  - Pyodide Web Worker for browser-side Python exec   │
│  - Chat, voice (WebRTC), drawing (shared canvas)     │
│  - Tailwind CSS                                      │
└────────────────────┬─────────────────────────────────┘
                     │ HTTP (REST) + WebSocket
┌────────────────────▼─────────────────────────────────┐
│  Backend (Django + Django REST Framework)             │
│  - Django Channels (WebSocket consumers)             │
│  - Celery + Celery Beat (async tasks)                │
│  - Y.js doc sync via Redis                           │
│  - JWT auth                                          │
│  - Django apps: users, usergroups, projects, codes   │
└────────┬───────────┬─────────────────────────────────┘
         │           │
    ┌────▼──┐   ┌────▼──┐
    │ Postgres│   │ Redis │
    │ (app DB)│   │(cache,│
    │         │   │broker,│
    │         │   │channel│
    │         │   │layer) │
    └─────────┘   └───────┘
```

### Observed Backend Structure

```
backend/
├── backend/          # Django project config (settings, urls, asgi, celery, jwt middleware)
│   └── settings/     # Split settings (dev, prod, etc.)
├── users/            # Custom User model (email-based), auth views, JWT tokens
├── usergroups/       # Group model (owner, members, access_code), group CRUD
├── projects/         # Project model (belongs to group), project CRUD
├── codes/            # Code model (text per project), YjsCodeConsumer (WebSocket),
│                     #   Celery tasks (snapshot_dirty_projects, cleanup_ghost_projects)
├── utils/            # Redis helpers (ydoc persistence, key helpers)
├── manage.py
├── requirements.txt
└── .env.dev
```

### Observed Frontend Structure

```
frontend/reactapp/
├── src/
│   ├── App.jsx                  # Router: /, /home, /login, /register, /groups/:gid/projects/:pid
│   ├── pages/
│   │   ├── PyIDE.jsx            # Main editor page (CodeMirror + Y.js + Pyodide + WS)
│   │   ├── GroupsProjects.jsx   # Group/project management UI
│   │   ├── OfflinePlayground.jsx # Standalone Pyodide playground
│   │   ├── EmbedPlayground.jsx  # Embeddable playground
│   │   ├── Login.jsx / Register.jsx / About.jsx
│   │   └── TermsOfService.jsx / PrivacyPolicy.jsx
│   ├── components/
│   │   ├── CodeLayout.jsx       # Editor + console + chat layout shell
│   │   ├── PyodideNotice.jsx    # Pyodide migration notice modal
│   │   ├── GroupsList.jsx       # Group list UI
│   │   ├── ProjectsList.jsx     # Project list UI
│   │   └── Modals/, auth.js, ProtectedRoute, PublicRoute, SharedProjectHandler
│   ├── hooks/
│   │   ├── usePyRunner.js       # Pyodide execution hook (init, run, stop, input)
│   │   ├── useVoiceChat.js      # WebRTC voice chat
│   │   ├── useSharedCanvas.js   # Collaborative drawing
│   │   └── useLocalCanvas.js, useVersionCheck.js, useUmamiHeartbeat.js
│   ├── pyrunner/
│   │   ├── Worker.js            # Web Worker: loads Pyodide, installs packages, runs Python
│   │   └── TaskClient.js        # Comlink bridge to Worker
│   └── main.jsx, index.css, sw.js
├── package.json                 # Dependencies incl. pyodide-worker-runner, codemirror, y.js
├── vite.config.js
└── axiosConfig.jsx              # Axios instance with JWT interceptors
```

---

## 2. Target SQLTogether Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Frontend (React + Vite)                                 │
│  - CodeMirror editor (SQL mode — replaces Python mode)   │
│  - Y.js CRDT collaboration (preserved)                   │
│  - NO Pyodide / NO Web Worker execution                  │
│  - New: "Run Query" button → HTTP POST to backend        │
│  - New: Result table UI, error display, query history    │
│  - Chat, voice, drawing (preserved)                      │
└────────────────────┬─────────────────────────────────────┘
                     │ HTTP (REST) + WebSocket
┌────────────────────▼─────────────────────────────────────┐
│  Backend (Django + DRF)                                  │
│  - Existing: Django Channels, Celery, JWT auth           │
│  - Existing apps: users, usergroups, projects, codes     │
│  - NEW app: sql_execution (or similar)                   │
│    ├── DatabaseTemplate model                            │
│    ├── ProjectDatabaseInstance model                     │
│    ├── QueryLog model                                    │
│    ├── SQL execution service (isolated per-project DB)   │
│    ├── run-query endpoint                                │
│    └── reset-database endpoint                           │
└────────┬───────────┬──────────────┬──────────────────────┘
         │           │              │
    ┌────▼──┐   ┌────▼──┐    ┌─────▼────────────┐
    │Postgres│   │ Redis │    │ Project SQLite    │
    │(app DB)│   │       │    │ files (isolated)  │
    │        │   │       │    │ /data/projects/   │
    │        │   │       │    │   {pid}.db        │
    └────────┘   └───────┘    └──────────────────┘
```

### Key Architectural Change

Python execution happened **in the browser** (Pyodide Web Worker).  
SQL execution happens **on the server** (Django backend connects to isolated SQLite files).

This is a fundamental shift. The entire `pyrunner/` directory, the `usePyRunner` hook, and the `PyodideNotice` component become obsolete and will be replaced by:
- A backend SQL execution service
- A frontend hook like `useSqlRunner` that sends queries via HTTP/WS
- A result table component

---

## 3. Application Database vs Learning Database

This separation is the single most important architectural rule.

| | Application Database | Learning Database(s) |
|---|---|---|
| **Engine** | PostgreSQL (inherited) | SQLite (MVP), DuckDB/PG later |
| **Purpose** | Users, groups, projects, permissions, metadata, query logs | Student SQL practice |
| **Who queries it** | Django ORM only | Students via SQL execution service |
| **Connection** | Django `DATABASES['default']` | Separate connection per execution request |
| **Location** | Docker volume (postgres_data) | Server filesystem or Docker volume |

> **RULE: Student SQL must NEVER run against `DATABASES['default']` or any connection used by Django ORM.**

---

## 4. Recommended Initial SQLite Approach

### Template Storage

```
/data/templates/
  {template_id}.db         # Master SQLite file (read-only to students)
```

- Teachers upload or create templates via admin or API.
- Templates are SQLite database files.
- Templates are never opened in write mode by student queries.

### Project Database Instances

```
/data/projects/
  {project_id}.db          # Copy of template, writable by project's students
```

- Created by copying the template file when a project is created.
- All student queries execute against this file.
- Reset = delete project `.db` and re-copy from template.

### File Location

The exact filesystem path should be configurable via Django settings (e.g., `SQLTOGETHER_DATA_DIR`). Default in development: `./data/` inside the backend directory or a Docker volume.

---

## 5. Suggested Backend Domain Models

### New Django App: `sql_execution` (or `databases`)

```python
class DatabaseTemplate(models.Model):
    group = models.ForeignKey('usergroups.Group', on_delete=models.CASCADE, related_name='templates')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    engine_type = models.CharField(max_length=20, default='sqlite')  # Future: 'duckdb', 'postgres'
    file_path = models.CharField(max_length=500)  # Internal path, never exposed to users
    file_size_bytes = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)

class ProjectDatabaseInstance(models.Model):
    project = models.OneToOneField('projects.Project', on_delete=models.CASCADE, related_name='database_instance')
    template = models.ForeignKey(DatabaseTemplate, on_delete=models.SET_NULL, null=True)
    engine_type = models.CharField(max_length=20, default='sqlite')
    file_path = models.CharField(max_length=500)  # Internal path, never exposed
    created_at = models.DateTimeField(auto_now_add=True)
    last_reset_at = models.DateTimeField(null=True, blank=True)
    is_read_only = models.BooleanField(default=False)

class QueryLog(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='query_logs')
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    query_text = models.TextField()
    status = models.CharField(max_length=20)  # 'success', 'error', 'timeout'
    error_message = models.TextField(blank=True)
    row_count = models.IntegerField(null=True)
    execution_time_ms = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Existing Models (Unchanged or Minimal Changes)

- `User` — unchanged
- `Group` — may add a `role` field or separate model for teacher/student distinction
- `Project` — may add a `template` FK or keep it on `ProjectDatabaseInstance`
- `Code` — the collaborative editor text (SQL instead of Python). Model itself unchanged.

---

## 6. Query Execution Flow

```
┌──────────┐     POST /api/query/run/      ┌──────────────────┐
│ Frontend │ ──────────────────────────────▶│ Django View      │
│ (editor) │     { project_id, sql }       │                  │
└──────────┘                                │ 1. Auth check    │
                                            │ 2. Membership    │
                                            │ 3. Validate SQL  │
                                            │ 4. Get instance  │
                                            │ 5. Execute       │
                                            │ 6. Log query     │
                                            │ 7. Return result │
                                            └────────┬─────────┘
                                                     │
                                            ┌────────▼─────────┐
                                            │ SQLExecutionSvc  │
                                            │                  │
                                            │ - Opens project  │
                                            │   .db file       │
                                            │ - Sets timeout   │
                                            │ - Sets row limit │
                                            │ - Executes SQL   │
                                            │ - Returns rows   │
                                            │   or error       │
                                            └──────────────────┘
```

### Response Shape (Success)

```json
{
  "status": "success",
  "columns": ["id", "name", "email"],
  "rows": [[1, "Alice", "alice@example.com"], [2, "Bob", "bob@example.com"]],
  "row_count": 2,
  "execution_time_ms": 12,
  "truncated": false
}
```

### Response Shape (Error)

```json
{
  "status": "error",
  "error_type": "syntax_error",
  "error_message": "near \"SELEC\": syntax error",
  "execution_time_ms": 1
}
```

---

## 7. Database Reset Flow

```
POST /api/projects/{pid}/reset-database/

1. Validate user is project member (or teacher/admin)
2. Close any open connections to the project .db
3. Delete the project .db file
4. Copy the template .db to the project .db path
5. Update ProjectDatabaseInstance.last_reset_at
6. Return success
```

---

## 8. Security Boundaries

| Boundary | Rule |
|----------|------|
| App DB isolation | Student SQL never touches PostgreSQL |
| Project isolation | Each project has its own SQLite file; no cross-project access |
| Template protection | Templates are read-only; students never write to them |
| Filesystem hiding | Internal paths never sent to frontend |
| Query limits | Timeout (5s default), row limit (1000), query length limit (10KB) |
| Auth required | All query endpoints require JWT authentication |
| Group membership | Users can only query projects they belong to |
| Write control | MVP may restrict to SELECT/WITH only; writes allowed only with explicit opt-in |

---

## 9. Future Multi-Engine Strategy

The architecture should support multiple SQL engines without rewriting the core:

```python
class SQLExecutionService:
    """Abstract base for SQL execution."""
    def execute(self, instance: ProjectDatabaseInstance, sql: str) -> QueryResult: ...
    def reset(self, instance: ProjectDatabaseInstance) -> None: ...
    def create_instance(self, template: DatabaseTemplate, project: Project) -> ProjectDatabaseInstance: ...

class SQLiteExecutionService(SQLExecutionService): ...   # Phase 4 (MVP)
class DuckDBExecutionService(SQLExecutionService): ...   # Phase 7
class PostgresExecutionService(SQLExecutionService): ... # Phase 7
```

Key design decisions for multi-engine:
- `engine_type` field on both `DatabaseTemplate` and `ProjectDatabaseInstance`
- Factory pattern: `get_execution_service(engine_type)` returns the right service
- Each engine implements: execute, reset, create_instance, validate_connection
- PostgreSQL sandbox may use per-schema isolation or disposable containers
- DuckDB may use file-based isolation similar to SQLite

Do not implement multi-engine until Phase 7. Keep the abstraction in mind but build SQLite-only first.
