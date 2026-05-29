# Phase 3 SQL Editor Conversion Report

## Short Summary

Phase 3 converted the visible editor experience from Python-oriented to SQL-oriented without adding real SQL execution. The primary collaborative editor now uses CodeMirror SQL support, displays `query.sql`, loads SQL starter text, and routes run/stop actions through a safe placeholder hook. Offline and embedded playgrounds were aligned with the same SQL editor behavior.

No backend SQL execution, project database instances, database templates, backend models, or application database schema changes were implemented.

Note: the requested `docs/PYTHON_EXECUTION_AUDIT.md` file was not present. The Phase 2 audit used for this work was `docs/PHASE_2_PYTHON_EXECUTION_AUDIT.md`.

## Files Changed

- `backend/backend/settings/base.py`
  - Replaced visible starter project template content with SQL examples.
  - Kept existing template constant names to avoid backend/API refactors.
- `frontend/reactapp/package.json`
  - Added `@codemirror/lang-sql`.
  - Removed `@codemirror/lang-python`.
- `frontend/reactapp/package-lock.json`
  - Lockfile updated for CodeMirror SQL support.
- `frontend/reactapp/src/App.jsx`
  - Routed project editor to `SqlEditor`.
- `frontend/reactapp/src/pages/PyIDE.jsx`
  - Renamed/replaced by `SqlEditor.jsx`.
- `frontend/reactapp/src/pages/SqlEditor.jsx`
  - Switched CodeMirror language support to SQL.
  - Changed starter/loading text to SQL comments.
  - Changed download output to `.sql`.
  - Replaced Python runner usage with `useSqlRunner`.
  - Kept Y.js collaboration, chat, voice, drawing, autosave, and project routing code in place.
- `frontend/reactapp/src/hooks/useSqlRunner.js`
  - Added a safe placeholder SQL runner hook.
  - Run/stop actions only emit placeholder result messages.
- `frontend/reactapp/src/components/CodeLayout.jsx`
  - Changed visible editor labels to `query.sql`, `Run Query`, `Stop Query`, and `Results`.
  - Hid the preview/plot toggle unless content exists.
- `frontend/reactapp/src/pages/OfflinePlayground.jsx`
  - Switched to SQL syntax highlighting, SQL starter text, SQL downloads, and placeholder run behavior.
- `frontend/reactapp/src/pages/EmbedPlayground.jsx`
  - Switched to SQL syntax highlighting, SQL labels, and placeholder run behavior.
- `frontend/reactapp/src/components/Modals/CreateProjectModal.jsx`
  - Reworded visible project template options for SQL learning.
- `frontend/reactapp/src/components/Modals/ShareModal.jsx`
  - Reworded share copy from code/offline playground language to query/SQL playground language.
- `frontend/reactapp/src/components/GroupsList.jsx`
  - Reworded visible offline playground links as SQL Playground.
- `frontend/reactapp/src/components/PyodideNotice.jsx`
  - Stubbed old Pyodide notice copy as a SQL editor preview notice.
- `frontend/reactapp/src/pages/About.jsx`
  - Replaced visible Python/data-science wording with SQL workspace and Phase 4 placeholder wording.
- `frontend/reactapp/src/pages/GroupsProjects.jsx`
  - Updated icon alt text from generic code branding to SQLTogether.
- `frontend/reactapp/src/pages/Login.jsx`
  - Reworded visible playground entry as SQL Playground.
- `frontend/reactapp/src/pages/PrivacyPolicy.jsx`
  - Reworded "Code Safety" to "Content Safety".

## Validation Performed

- `npm run build --prefix frontend/reactapp`
  - Passed.
  - Confirms `SqlEditor.jsx`, `OfflinePlayground.jsx`, and `EmbedPlayground.jsx` compile with `@codemirror/lang-sql`.
  - Build warnings remain for large chunks and stale `baseline-browser-mapping` data.
- `npm run lint --prefix frontend/reactapp`
  - Failed on existing baseline issues unrelated to SQL conversion:
    - `frontend/reactapp/src/components/auth.js`: unused `error`.
    - `frontend/reactapp/src/hooks/useVoiceChat.js`: unused `err`.
    - `frontend/reactapp/vite.config.js`: `__dirname` is not defined.
  - Remaining warnings include existing React hook dependency warnings.
  - Editor-local fatal lint errors from the rename were cleaned up.
- Static visible-reference scans:
  - Confirmed active editor/playground files import `@codemirror/lang-sql`.
  - Confirmed visible labels include `query.sql`, `Run Query`, `Stop Query`, and `Results`.
  - Confirmed no active editor UI references to `@codemirror/lang-python`, visible Python branding, Pyodide notices, or `main.py`.
- Dev server smoke check:
  - Started Vite at `http://127.0.0.1:5174/` after sandboxed port binding failed.
  - `curl -I http://127.0.0.1:5174/` returned `HTTP/1.1 200 OK`.
  - `curl -I http://127.0.0.1:5174/groups/1/projects/1` returned `HTTP/1.1 200 OK`, confirming the SPA editor route is served by Vite.

## Remaining Python/Pyodide References

These references remain intentionally dormant for later removal or migration:

- `frontend/reactapp/src/hooks/usePyRunner.js`
  - Legacy Python runner hook. It is no longer imported by the active editor/playground paths.
- `frontend/reactapp/src/pyrunner/Worker.js`
  - Legacy Pyodide worker implementation, including `/main.py` and Python runtime setup.
- `frontend/reactapp/src/pyrunner/TaskClient.js`
  - Legacy Pyodide worker client.
- `frontend/reactapp/package.json`
  - `pyodide-worker-runner`, `comlink`, and `sync-message` remain because the legacy runner files still exist.

Attribution references to PyTogether remain by design and must be preserved.

## Follow-Up Items for Phase 4

- Design and implement isolated project database provisioning for the SQLite MVP.
- Add backend APIs for executing SQL against project databases only.
- Ensure student SQL never runs against the SQLTogether application database.
- Replace the placeholder `useSqlRunner` with a real SQL runner client.
- Define result table, error, timing, row limit, and cancellation behavior.
- Add SQL safety enforcement for SQLite, including statement restrictions and resource limits.
- Remove legacy `usePyRunner`, `pyrunner/`, and Pyodide dependencies after the SQL runner fully replaces them.
- Add tests that prove application database isolation.

## Recommended Prompt to Start Phase 4

Read `AGENTS.md`, `docs/SQLTOGETHER_PHASES.md`, `docs/SQL_SANDBOX_STRATEGY.md`, `docs/PHASE_2_PYTHON_EXECUTION_AUDIT.md`, `docs/PHASE_3_SQL_EDITOR_CONVERSION_REPORT.md`, and the rules in `.agents/rules/`. We are starting Phase 4: SQLite MVP planning and implementation. Use `.agents/workflows/sql-mvp-planning.md`. Plan first before modifying code. The goal is to execute SQL against isolated per-project SQLite databases only, never against the SQLTogether application database.
