# SQL Safety Rules

These rules are **non-negotiable** and apply to all phases of SQLTogether development.

## Rule 1: Never Run Student SQL Against the Application Database

The application database (PostgreSQL, `DATABASES['default']`) stores:
- Users
- Groups
- Projects
- Permissions
- Metadata
- Query logs

**Student SQL queries must NEVER execute against this database.** All student queries run against isolated project databases.

If you are writing code that executes SQL from user input, verify it connects to a **project database instance**, not the Django ORM database.

## Rule 2: Use Isolated Project Databases

Every project gets its own database instance:
- **SQLite MVP:** One `.db` file per project, stored at a managed server path.
- **Future engines:** Per-schema, per-container, or per-file isolation.

No project can access another project's database. No project can access the application database.

## Rule 3: Add Timeouts and Limits

Every query execution must enforce:

| Control | Default | Purpose |
|---------|---------|---------|
| Query timeout | 5 seconds | Prevent runaway queries |
| Row limit | 1000 rows | Prevent memory exhaustion |
| Query length limit | 10,000 characters | Prevent abuse |
| Database file size limit | 50 MB | Prevent disk exhaustion |

These values should be configurable via Django settings.

## Rule 4: Do Not Expose Filesystem Paths

- Internal paths like `/data/templates/42.db` or `/data/projects/107.db` must **never** appear in:
  - API responses
  - Error messages returned to the frontend
  - WebSocket messages
  - Log output visible to users

- Sanitize SQLite error messages to remove path references before returning to the user.

## Rule 5: Do Not Add Arbitrary External Database Connections

In early phases (through Phase 6), all databases are managed by SQLTogether:
- Templates uploaded by teachers
- Project instances created by the backend

Do not add features that allow users to connect to external databases (e.g., "connect to my PostgreSQL server"). This can be considered for much later phases after thorough security review.

## Rule 6: Block Dangerous SQL Commands

Always block, regardless of read-only or write mode:

```
ATTACH DATABASE ...     -- Can open arbitrary files on the server filesystem
DETACH DATABASE ...     -- Related to ATTACH
LOAD_EXTENSION ...      -- Can load arbitrary shared libraries
```

In read-only mode, additionally block:
```
INSERT, UPDATE, DELETE
CREATE, DROP, ALTER
PRAGMA (except safe read-only ones like table_info, table_list)
```

Use `PRAGMA query_only = ON` as defense-in-depth for read-only mode.

## Rule 7: Block Dangerous Implementation Shortcuts

Do not implement any of these shortcuts, even if they seem faster:

- ❌ Using Django's database connection for student queries
- ❌ Using `raw()` or `cursor()` on the default database for student SQL
- ❌ Storing project databases in PostgreSQL schemas using `DATABASES` dict
- ❌ Executing SQL via `subprocess` calling the `sqlite3` CLI
- ❌ Allowing file uploads without size and format validation
- ❌ Running queries without a timeout mechanism
- ❌ Returning raw SQLite error messages (may contain server paths)
- ❌ Opening SQLite databases in WAL mode for student DBs (complicates isolation)

## Rule 8: Templates Are Read-Only

Database templates are master/source databases:
- Created and managed by teachers/admins
- Copied when a project is created
- **Never modified by student query execution**
- Never opened in write mode during student sessions

## Rule 9: Auth and Membership Required

Every query execution request must verify:
1. User is authenticated (valid JWT)
2. User is a member of the project's group (or has a valid share token)
3. Project exists and belongs to the claimed group

Never execute SQL for unauthenticated or unauthorized users.
