# SQLTogether — Product Plan

## 1. Product Purpose

SQLTogether is a collaborative browser-based SQL learning and teaching environment. It enables teachers, tutors, and students to write, run, and discuss SQL queries together in real time — without requiring local database installations or complex setup.

The project is adapted from [PyTogether](https://github.com/SJRiz/pytogether) (a collaborative Python IDE) and inherits its real-time collaboration infrastructure (Y.js, WebSockets, groups, projects, chat, voice, drawing). SQLTogether replaces Python code execution with SQL query execution against isolated sandbox databases.

---

## 2. Target Users

| Role | Description |
|------|-------------|
| **Student** | Writes and runs SQL queries inside a project. Sees results, errors, and query history. Cannot modify group templates. |
| **Teacher / Admin** | Creates groups, manages database templates, monitors student activity, can view/help in student projects. |
| **Tutor / Mentor** | Similar to teacher but may join via invite. Can pair with students in real time. |
| **Self-hoster** | School IT admin or instructor who deploys SQLTogether for their institution. |

---

## 3. Core Concepts

### 3.1 Group

- A classroom, team, or cohort.
- Has an owner (teacher/admin) and members (students).
- Owns one or more **DatabaseTemplates**.
- Members join via access code (inherited from PyTogether).

### 3.2 DatabaseTemplate

- A master/source database schema and data used for teaching.
- Owned by a group.
- **Never modified by student queries.**
- Uploaded or created by the teacher/admin.
- Examples: a `chinook.db`, a `northwind.db`, a custom exercise database.

### 3.3 Project

- A workspace where a student (or team) practices SQL.
- Belongs to a group.
- Selects one DatabaseTemplate at creation time.
- Gets its own **ProjectDatabaseInstance** (a copy of the template).
- Retains the inherited collaboration features: shared editor, chat, voice, drawing.

### 3.4 ProjectDatabaseInstance

- An isolated database copy derived from a template.
- This is the database students query against.
- Can be reset back to the template's original state at any time.
- Completely separate from the SQLTogether application database.
- For the SQLite MVP: a `.db` file on the server, one per project.

### 3.5 Query Run

- A student submits SQL from the editor.
- The backend executes it against the project's isolated database.
- Returns: result rows (as a table), column names, row count, execution time, or an error message.
- Logged for query history.

---

## 4. MVP Scope (Phase 1–5)

The MVP delivers:

- [x] Inherited: user auth, groups, projects, real-time collaboration, chat, voice, drawing
- [ ] SQL editor with syntax highlighting (replace Python mode)
- [ ] Server-side SQL execution against isolated SQLite databases
- [ ] Result table UI for query output
- [ ] Error display for invalid SQL
- [ ] Query history per project
- [ ] Group-owned database templates (SQLite files)
- [ ] Project creation from a selected template
- [ ] Project database reset (re-copy from template)
- [ ] Basic safety: timeouts, row limits, query length limits
- [ ] SELECT/WITH queries by default; careful handling of write queries

### MVP SQL Engine

**SQLite** is the first engine for the MVP.

Reasons:
- Simplest to sandbox (one file per project).
- Easy to copy (file copy = database copy).
- Easy to reset (replace file from template).
- Good enough for beginner-to-intermediate SQL teaching.
- Low infrastructure complexity (no separate DB server needed).

---

## 5. Non-Goals (Explicitly Out of Scope for MVP)

- ❌ Browser-side SQL execution (sql.js / DuckDB-WASM) — too hard to persist and monitor
- ❌ Production database management features
- ❌ Multi-engine support (PostgreSQL, MySQL, DuckDB) — planned for later
- ❌ Complex permission systems (row-level, column-level security)
- ❌ Student SQL running against the application database — **this must never happen**
- ❌ Arbitrary external database connections
- ❌ Automated grading / AI feedback
- ❌ Public/anonymous query execution without auth

---

## 6. Future Goals (Post-MVP)

| Feature | Phase |
|---------|-------|
| DuckDB engine support | Phase 7 |
| PostgreSQL sandbox (per-schema or per-container) | Phase 7 |
| Lessons and exercises with expected results | Phase 8 |
| Starter queries and guided tasks | Phase 8 |
| Progress tracking | Phase 8 |
| Docker/self-hosting hardening | Phase 9 |
| CI pipeline and tests | Phase 9 |
| Security audit and cleanup jobs | Phase 9 |

---

## 7. Safety Principles

These are non-negotiable rules for the entire project lifecycle:

1. **Student SQL must never execute against the SQLTogether application database.**
   - The app DB (PostgreSQL) stores users, groups, projects, permissions, metadata.
   - Student queries go only to isolated ProjectDatabaseInstances.

2. **Every project database is isolated.**
   - For SQLite MVP: each project gets its own `.db` file.
   - One project's queries cannot affect another project's database.

3. **Templates are read-only from the student perspective.**
   - Templates are the master source. Students never write to them.

4. **Query execution has hard limits.**
   - Timeout (e.g., 5 seconds).
   - Row limit (e.g., 1000 rows returned).
   - Query length limit (e.g., 10,000 characters).

5. **Filesystem paths are never exposed to users.**
   - Students see project/template names, not file paths.

6. **No arbitrary external DB connections in early phases.**
   - All databases are managed by SQLTogether.

7. **Attribution is preserved.**
   - PyTogether credit, MIT license, and original copyright remain in README, NOTICE, and LICENSE.
