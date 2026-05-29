# SQLTogether — Phased Development Roadmap

## Overview

This document defines the phased development plan for converting PyTogether into SQLTogether. Each phase has clear goals, tasks, a definition of done, and explicit warnings about what future agents should not do too early.

**Rule: Complete each phase before moving to the next. Do not skip phases.**

---

## Phase 0: Stabilize Imported Codebase

### Goal
Confirm the inherited PyTogether codebase runs correctly in development. Document the current state.

### Tasks

- [ ] Run `npm install` and `npm run dev` successfully
- [ ] Verify Docker containers start (Django, PostgreSQL, Redis, Celery, Celery Beat)
- [ ] Verify frontend starts on `localhost:5173`
- [ ] Verify backend API responds on `localhost:8000`
- [ ] Create test users and log in
- [ ] Create a group, add a member, create a project
- [ ] Open a project: verify CodeMirror editor loads with Y.js collaboration
- [ ] Verify Python execution works (Pyodide loads in browser)
- [ ] Verify chat, voice, and drawing features work
- [ ] Verify autosave/persistence (Celery snapshot tasks)
- [ ] Document any issues, broken features, or missing setup steps
- [ ] Document environment variables and their purposes
- [ ] Document Docker service roles

### Definition of Done

- [x] App runs in development with `npm run dev` + Docker
- [x] All major inherited features verified working or documented as broken
- [x] Setup instructions confirmed or updated
- [x] No source code changes made (unless fixing a blocking setup bug)

### Do NOT Do Yet

- ❌ Do not rename anything to SQLTogether in code
- ❌ Do not remove Pyodide or Python-related code
- ❌ Do not add SQL execution logic
- ❌ Do not modify models

---

## Phase 1: Rebrand Safely

### Goal
Make the visible UI say "SQLTogether" instead of "PyTogether" without breaking any logic.

### Tasks

- [ ] Update page titles (e.g., `document.title` in `PyIDE.jsx`)
- [ ] Update header text "PyTogether" → "SQLTogether" in `CodeLayout.jsx` (line 212)
- [ ] Update logo references (`/pytog.png` → new SQLTogether logo)
- [ ] Update About page text
- [ ] Update Login/Register page branding
- [ ] Update `package.json` name field (`"pytogether"` → `"sqltogether"`)
- [ ] Update Docker image names in `docker-compose-dev.yaml` (`pytogether-backend` → `sqltogether-backend`)
- [ ] Update `pytogether.org` domain references in `PyIDE.jsx` (lines 251-263)
- [ ] Keep original PyTogether attribution in README, NOTICE.md, LICENSE — do not remove
- [ ] Verify app still runs after all branding changes

### Definition of Done

- [x] UI shows "SQLTogether" everywhere visible to users
- [x] No references to pytogether.org as if this is the official project
- [x] README, NOTICE, LICENSE still credit PyTogether and Syed Jawad Rizvi
- [x] App runs without errors

### Do NOT Do Yet

- ❌ Do not change editor language from Python to SQL
- ❌ Do not remove Pyodide
- ❌ Do not add SQL execution
- ❌ Do not change any backend models

---

## Phase 2: Audit Python Execution Path

### Goal
Document exactly how Python execution works so future phases can safely replace it with SQL execution.

### Tasks

- [ ] Document the Pyodide loading flow: `Worker.js` → `loadPyodide()` → `initPyodide()` → package installs
- [ ] Document the execution flow: `usePyRunner` hook → `TaskClient.js` → `Worker.js` → `check_entry()` → callback
- [ ] Document the output flow: `outputCallback` → `pushToStdout` → `consoleOutput` state
- [ ] Document CodeMirror language configuration: `python()` extension in `PyIDE.jsx` line 609
- [ ] Document the editor file label: `main.py` in `CodeLayout.jsx` line 319
- [ ] Document download options: `.py, .txt, .docx, .pdf` in `CodeLayout.jsx` lines 236
- [ ] Document the `PyodideNotice.jsx` modal
- [ ] Document the `OfflinePlayground.jsx` and `EmbedPlayground.jsx` Pyodide usage
- [ ] Document the Plot panel (matplotlib output)
- [ ] Identify all Python/Pyodide-specific npm packages in `package.json`
- [ ] Identify backend involvement (or lack thereof) in Python execution
- [ ] Create a file map: which files are Python-specific, which are generic, which need both audit and modification

### Definition of Done

- [x] Complete audit document exists mapping every Python execution touchpoint
- [x] Clear list of files to modify, files to replace, files to keep
- [x] No code changes made

### Do NOT Do Yet

- ❌ Do not delete any files
- ❌ Do not modify editor configuration
- ❌ Do not remove Pyodide packages

---

## Phase 3: Convert Editor Experience to SQL

### Goal
Replace the Python editor experience with SQL — syntax highlighting, terminology, starter content, file labels.

### Tasks

- [ ] Replace `@codemirror/lang-python` with `@codemirror/lang-sql` in `package.json`
- [ ] Replace `python()` extension with `sql()` extension in `PyIDE.jsx`
- [ ] Update starter code: `'# Loading code...'` → `'-- Loading query...'` or `'SELECT 1;'`
- [ ] Update file label: `main.py` → `query.sql` in `CodeLayout.jsx`
- [ ] Update download options: `.py` → `.sql` in `CodeLayout.jsx`
- [ ] Update console messages: `"Loading Python interpreter..."` → remove or replace with SQL-relevant messages
- [ ] Rename `usePyRunner` hook → `useSqlRunner` (stub for now — actual execution comes in Phase 4)
- [ ] Remove or stub out `PyodideNotice.jsx`
- [ ] Update `OfflinePlayground.jsx` to remove Pyodide usage (or disable temporarily)
- [ ] Keep Y.js collaboration, chat, voice, drawing — these are language-agnostic
- [ ] Rename `PyIDE.jsx` → `SqlEditor.jsx` (or similar)
- [ ] Update route in `App.jsx` accordingly
- [ ] Verify the editor loads with SQL syntax highlighting

### Definition of Done

- [x] Editor shows SQL syntax highlighting
- [x] No Python-specific labels, terminology, or notices visible
- [x] Collaboration features still work (Y.js, chat, voice, drawing)
- [x] Run/Stop buttons exist but may not execute anything yet (stub)
- [x] App runs without errors

### Do NOT Do Yet

- ❌ Do not implement backend SQL execution
- ❌ Do not add database templates or project database instances
- ❌ Do not modify backend models

---

## Phase 4: Add MVP SQLite Execution

### Goal
Implement server-side SQL query execution against isolated per-project SQLite databases.

### Tasks

- [ ] Create new Django app: `sql_execution` (or `databases`)
- [ ] Add `ProjectDatabaseInstance` model (links project to a SQLite file)
- [ ] Create SQL execution service (`SQLiteExecutionService`)
- [ ] Implement `POST /api/query/run/` endpoint
  - Auth + membership validation
  - Open project's SQLite file
  - Execute SQL with timeout and row limit
  - Return columns, rows, row_count, execution_time_ms
  - Return error message on failure
  - Log query to `QueryLog` model
- [ ] Add `QueryLog` model for query history
- [ ] Add `GET /api/projects/{pid}/query-history/` endpoint
- [ ] Create frontend `useSqlRunner` hook (replace Pyodide execution)
  - Sends POST to backend
  - Handles success (result table data)
  - Handles error (display error message)
  - Handles loading state
- [ ] Create result table UI component
- [ ] Create error display component
- [ ] Wire "Run" button to `useSqlRunner`
- [ ] Add query history panel or section
- [ ] Add safety controls:
  - Query timeout (default 5 seconds)
  - Row limit (default 1000 rows)
  - Query length limit (default 10,000 chars)
  - Consider restricting to SELECT/WITH for MVP (configurable)
- [ ] Create initial project SQLite database on project creation (empty or default)
- [ ] Add Docker volume for project database files
- [ ] Run migrations

### Definition of Done

- [x] Students can write SQL in the editor and click "Run"
- [x] Results appear in a table below the editor
- [x] Errors appear with clear messages
- [x] Query history is logged and viewable
- [x] Timeout and row limits work
- [x] Each project has its own isolated SQLite file
- [x] App DB (PostgreSQL) is never used for student queries
- [x] App runs in development

### Do NOT Do Yet

- ❌ Do not add database templates yet (use a default empty DB for now)
- ❌ Do not add DuckDB or PostgreSQL engines
- ❌ Do not add teacher monitoring tools

---

## Phase 5: Add Group Database Templates

### Goal
Allow teachers to create database templates that projects copy when created.

### Tasks

- [ ] Add `DatabaseTemplate` model
- [ ] Add template upload API (teacher uploads a `.db` file)
- [ ] Add template management UI for group owners
- [ ] Modify project creation flow:
  - UI: select a template when creating a project
  - Backend: copy template `.db` to project `.db` path
- [ ] Add "Reset Database" feature:
  - `POST /api/projects/{pid}/reset-database/`
  - Deletes project `.db`, re-copies from template
  - Requires project member or teacher permission
- [ ] Add template list API per group
- [ ] Add template preview (show tables/schema)
- [ ] Add template file size limits
- [ ] Add sample/starter templates (e.g., a simple `students` table, a `bookstore` schema)

### Definition of Done

- [x] Teachers can upload SQLite templates to a group
- [x] Students see available templates when creating a project
- [x] Project creation copies the selected template
- [x] "Reset Database" restores the project to the template state
- [x] Templates are never modified by student queries
- [x] App runs in development

### Do NOT Do Yet

- ❌ Do not add teacher monitoring/dashboard
- ❌ Do not add exercises or lessons
- ❌ Do not add multi-engine support

---

## Phase 6: Teacher Remote Teaching Tools

### Goal
Give teachers visibility into student activity and the ability to help remotely.

### Tasks

- [ ] Add teacher dashboard: list of active projects in a group
- [ ] Show recent query activity per project (last N queries from QueryLog)
- [ ] Show which students are currently connected (from Redis active sets)
- [ ] Allow teacher to open/view any project in their group (read-only or collaborative)
- [ ] Add query history viewer for teachers (per student, per project)
- [ ] Consider real-time query streaming via WebSocket (optional, may be complex)
- [ ] Add role distinction: group owner = teacher, group member = student
- [ ] Consider adding a "teacher" badge or indicator in the UI

### Definition of Done

- [x] Teachers can see a dashboard of activity in their group
- [x] Teachers can see recent queries from any project
- [x] Teachers can open student projects to observe or help
- [x] Query history is viewable by teachers
- [x] App runs in development

### Do NOT Do Yet

- ❌ Do not add exercises or grading
- ❌ Do not add multi-engine support

---

## Phase 7: Multiple SQL Engine Support

### Goal
Abstract the SQL execution layer to support engines beyond SQLite.

### Tasks

- [ ] Define `SQLExecutionService` abstract base
- [ ] Refactor `SQLiteExecutionService` to implement the interface
- [ ] Add `engine_type` field to `DatabaseTemplate` and `ProjectDatabaseInstance`
- [ ] Add factory: `get_execution_service(engine_type)`
- [ ] Implement `DuckDBExecutionService` (file-based, similar to SQLite)
- [ ] Plan PostgreSQL sandbox approach (per-schema, per-user, or container-based)
- [ ] Implement `PostgresExecutionService` if approach is viable
- [ ] Update template upload to validate engine compatibility
- [ ] Update project creation to use correct engine service
- [ ] Update UI to show engine type

### Definition of Done

- [x] At least one additional engine works end-to-end
- [x] Engine type is stored on templates and instances
- [x] SQLite continues to work unchanged
- [x] App runs in development

---

## Phase 8: Lessons and Exercises

### Goal
Add structured learning features.

### Tasks

- [ ] Design lesson/exercise model (description, starter query, expected result, hints)
- [ ] Add exercise list per template or group
- [ ] Add exercise UI in the project editor
- [ ] Add result comparison (student result vs expected result)
- [ ] Add progress tracking per student
- [ ] Add starter queries that pre-fill the editor
- [ ] Consider guided mode (step-by-step tasks)

### Definition of Done

- [x] Teachers can create exercises attached to a template
- [x] Students can attempt exercises and see if results match
- [x] Progress is tracked

---

## Phase 9: Hardening and Deployment

### Goal
Prepare for production and self-hosted deployments.

### Tasks

- [ ] Security review of all endpoints
- [ ] SQL injection prevention audit
- [ ] Rate limiting on query execution
- [ ] Cleanup jobs for orphaned project databases
- [ ] Docker production config cleanup
- [ ] Self-hosting documentation update
- [ ] Add unit tests for SQL execution service
- [ ] Add integration tests for query flow
- [ ] CI pipeline (GitHub Actions)
- [ ] Performance testing with concurrent users

### Definition of Done

- [x] Security review complete
- [x] Tests pass in CI
- [x] Self-hosting docs are accurate
- [x] Cleanup jobs run reliably

---

## Phase Summary Table

| Phase | Name | Key Deliverable | Depends On |
|-------|------|-----------------|------------|
| 0 | Stabilize | Running app, documented state | — |
| 1 | Rebrand | UI says SQLTogether | 0 |
| 2 | Audit | Python execution documented | 0 |
| 3 | SQL Editor | SQL syntax, no execution yet | 1, 2 |
| 4 | SQLite MVP | Working SQL execution | 3 |
| 5 | Templates | Group database templates, reset | 4 |
| 6 | Teacher Tools | Dashboard, monitoring, help | 5 |
| 7 | Multi-Engine | DuckDB/PostgreSQL support | 4 |
| 8 | Lessons | Exercises, progress tracking | 5 |
| 9 | Hardening | Security, tests, CI, deploy | 6, 7 |

---

## Common Mistakes to Avoid

1. **Do not skip Phase 0.** If the app doesn't run, nothing else matters.
2. **Do not implement SQL execution before the editor conversion.** Phase 3 before Phase 4.
3. **Do not add multi-engine support before SQLite MVP works.** Phase 4 before Phase 7.
4. **Do not delete Python/Pyodide files without completing the audit.** Phase 2 before Phase 3.
5. **Do not modify backend models in Phase 1.** Branding only.
6. **Do not add exercises before templates work.** Phase 5 before Phase 8.
7. **Do not connect student SQL to the app database. Ever.**
