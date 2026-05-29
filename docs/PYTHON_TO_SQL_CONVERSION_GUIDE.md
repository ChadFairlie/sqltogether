# Python-to-SQL Conversion Guide

This guide documents the Python/Pyodide-specific areas in the inherited PyTogether codebase that will need to be modified, replaced, or removed as SQLTogether shifts from Python execution to SQL execution.

> **Important:** This guide is based on actual code inspection of the repository. File paths and line references have been verified against the codebase as of the initial import. However, future agents should re-verify before making changes, as the codebase may evolve.

---

## 1. Python-Specific Areas (Verified)

### 1.1 Pyodide Web Worker — `frontend/reactapp/src/pyrunner/Worker.js`

**What it does:** This is the core Python execution engine. It runs in a Web Worker and:
- Loads Pyodide (CPython compiled to WebAssembly) from jsDelivr CDN
- Installs Python packages: `python_runner`, `colorama`, `matplotlib`, `Pillow`, `pandas`, `scipy`, `numpy`, `pyodide-http`
- Wraps execution in a `PyodideRunner` with custom traceback handling
- Handles `matplotlib` plot output (converts to base64 PNG/GIF)
- Exposes `init()` and `runCode()` via Comlink

**Conversion action:** This entire file will be **replaced**. SQL execution moves to the backend. No Web Worker is needed for SQL.

### 1.2 Task Client — `frontend/reactapp/src/pyrunner/TaskClient.js`

**What it does:** Creates a `PyodideClient` that communicates with the Worker via Comlink and service worker channels. Provides `runCodeTask()` that calls the worker's `runCode` and handles interrupts.

**Conversion action:** This entire file will be **replaced** with a simple HTTP client that sends queries to the backend.

### 1.3 Python Runner Hook — `frontend/reactapp/src/hooks/usePyRunner.js`

**What it does:** React hook that manages:
- Pyodide initialization state (`isLoading`)
- Code execution state (`isRunning`)
- Console output state (`consoleOutput`)
- Plot display state (`plotSrc`)
- Error line highlighting (`errorLine`)
- Input handling (`waitingForInput`, `submitInput`)
- `runCode(codeString)` — sends code to the worker
- `stopCode()` — interrupts execution

**Conversion action:** **Replace** with `useSqlRunner.js` hook that:
- Sends SQL to the backend via HTTP POST
- Manages result table data (columns, rows)
- Manages error messages
- Manages loading state
- No plot support needed
- No input() support needed
- No Pyodide initialization needed

### 1.4 Pyodide Notice Modal — `frontend/reactapp/src/components/PyodideNotice.jsx`

**What it does:** Shows a one-time modal announcing the migration to Pyodide, with features like "Full Scientific Stack", "Better Error Handling", "True Python Compatibility".

**Conversion action:** **Remove entirely** or replace with an SQLTogether welcome/feature notice.

---

## 2. Pyodide/Web Worker npm Packages (Verified in `frontend/reactapp/package.json`)

These packages are Python/Pyodide-specific and should be removed when Pyodide is removed:

| Package | Purpose | Action |
|---------|---------|--------|
| `pyodide-worker-runner` | Manages Pyodide lifecycle in Web Worker | Remove |
| `comlink` | Worker ↔ main thread communication | Remove (unless used elsewhere) |
| `sync-message` | Synchronous messaging for service worker | Remove |
| `anser` | ANSI color code → HTML (for Python terminal output) | Likely remove |

These packages should be **added** for SQL:

| Package | Purpose |
|---------|---------|
| `@codemirror/lang-sql` | SQL syntax highlighting for CodeMirror |

---

## 3. CodeMirror Language Mode (Verified)

### Current Configuration

In `frontend/reactapp/src/pages/PyIDE.jsx`, line 12 and 609:

```javascript
import { python } from "@codemirror/lang-python";  // line 12

// In the CodeMirror component, line 608-611:
extensions={[
  python(),
  yCollab(ytextRef.current, awarenessRef.current, { undoManager: codeUndoManagerRef.current }),
  errorLineField
]}
```

**Conversion action:**
1. Replace import: `import { sql } from "@codemirror/lang-sql";`
2. Replace extension: `sql()` instead of `python()`
3. The `yCollab` and `errorLineField` extensions are language-agnostic — keep them.

### Dependency Change

In `frontend/reactapp/package.json`, line 16:
```json
"@codemirror/lang-python": "^6.2.1",
```

**Conversion action:** Replace with `"@codemirror/lang-sql": "^6.x.x"`.

---

## 4. Run/Output Flow (Verified)

### Current Flow (Python)

```
User clicks "Run" button
  → CodeLayout.jsx: onRun prop called
  → PyIDE.jsx: runner.runCode(ytextRef.current.toString())
  → usePyRunner.js: runCode(codeString)
  → TaskClient.js: runCodeTask(entry, outputCallback, inputCallback)
  → Worker.js: runCode(entry) via Comlink
  → Pyodide executes Python in WebAssembly
  → Output callbacks: stdout, stderr, plots, errors
  → usePyRunner: updates consoleOutput, plotSrc, errorLine
  → CodeLayout.jsx: renders console output
```

### Target Flow (SQL)

```
User clicks "Run Query" button
  → SqlEditor.jsx: runner.runQuery(ytextRef.current.toString())
  → useSqlRunner.js: runQuery(sqlString)
  → HTTP POST /api/query/run/ { project_id, sql }
  → Django view: validates, executes via SQLiteExecutionService
  → Returns: { columns, rows, row_count, execution_time_ms } or { error_message }
  → useSqlRunner: updates resultData or errorMessage
  → CodeLayout.jsx (modified): renders result table or error
```

### Key Differences

| Aspect | Python (Current) | SQL (Target) |
|--------|-------------------|--------------|
| Execution location | Browser (Web Worker) | Server (Django backend) |
| Communication | Comlink + Service Worker | HTTP POST (or WebSocket) |
| Output type | Console text + plots | Table (columns + rows) + errors |
| Input handling | `input()` function | None needed |
| Initialization | Pyodide download (~20MB) | None (backend always ready) |
| Interruption | Worker interrupt | Cancel HTTP request or backend timeout |

---

## 5. Backend/Frontend Files to Inspect During Conversion

### Frontend Files — Will Need Modification

| File | What to Change |
|------|----------------|
| `src/pages/PyIDE.jsx` | Rename, replace python() with sql(), remove usePyRunner, add useSqlRunner |
| `src/hooks/usePyRunner.js` | Replace with useSqlRunner.js |
| `src/pyrunner/Worker.js` | Remove entirely |
| `src/pyrunner/TaskClient.js` | Remove entirely |
| `src/components/PyodideNotice.jsx` | Remove or replace |
| `src/components/CodeLayout.jsx` | Update labels (main.py → query.sql), download options (.py → .sql), console → results |
| `src/pages/OfflinePlayground.jsx` | Remove Pyodide usage, replace with offline SQL or disable |
| `src/pages/EmbedPlayground.jsx` | Remove Pyodide usage, replace with embedded SQL or disable |
| `src/App.jsx` | Update route component names (PyIDE → SqlEditor) |
| `package.json` | Remove Pyodide packages, add SQL packages |

### Frontend Files — Keep As-Is (Language-Agnostic)

| File | Reason |
|------|--------|
| `src/hooks/useVoiceChat.js` | Voice chat is language-agnostic |
| `src/hooks/useSharedCanvas.js` | Drawing is language-agnostic |
| `src/hooks/useLocalCanvas.js` | Local drawing is language-agnostic |
| `src/components/GroupsList.jsx` | Group management is language-agnostic |
| `src/components/ProjectsList.jsx` | Project management is language-agnostic |
| `src/components/auth.js` | Auth is language-agnostic |
| `src/components/ProtectedRoute.jsx` | Routing is language-agnostic |
| `src/components/SharedProjectHandler.jsx` | Share links are language-agnostic |
| `axiosConfig.jsx` | HTTP client config is language-agnostic |

### Backend Files — Keep As-Is

| File | Reason |
|------|--------|
| `users/` (entire app) | User auth is language-agnostic |
| `usergroups/` (entire app) | Group management is language-agnostic |
| `projects/` (entire app) | Project CRUD is language-agnostic (may need minor additions) |
| `codes/consumers.py` | Y.js WebSocket sync is language-agnostic (syncs text, not Python) |
| `codes/tasks.py` | Celery tasks for Y.js persistence are language-agnostic |
| `codes/models.py` | Code model stores text content (works for SQL too) |
| `utils/redis_helpers.py` | Redis helpers are language-agnostic |
| `backend/settings/` | Django config — will need additions for SQL execution settings |

### Backend Files — Will Need New Files

| File | Purpose |
|------|---------|
| `sql_execution/` (new app) | New Django app for SQL execution |
| `sql_execution/models.py` | DatabaseTemplate, ProjectDatabaseInstance, QueryLog |
| `sql_execution/services.py` | SQLiteExecutionService |
| `sql_execution/views.py` | run-query, reset-database, query-history endpoints |
| `sql_execution/urls.py` | URL routing for new endpoints |
| `sql_execution/serializers.py` | DRF serializers for query requests/responses |

---

## 6. How Future Agents Should Audit Before Modifying

### Pre-Modification Checklist

Before changing any file, the agent should:

1. **Read the file completely** — don't assume based on filename.
2. **Identify Python-specific vs generic code** — many files mix both.
3. **Check imports** — what gets imported tells you what the file depends on.
4. **Check for shared state** — Y.js refs, WebSocket refs, and awareness refs are shared across features.
5. **Test before and after** — run the app before modifying, verify it works, then modify, then test again.
6. **Make small changes** — don't rewrite entire files in one step.
7. **Keep a rollback plan** — commit before making changes so you can revert.

### File Inspection Order

When auditing, inspect in this order:

1. `PyIDE.jsx` — the main page that integrates everything
2. `usePyRunner.js` — the Python execution hook
3. `Worker.js` + `TaskClient.js` — the Pyodide worker
4. `CodeLayout.jsx` — the layout shell (Python labels are here)
5. `PyodideNotice.jsx` — the Pyodide modal
6. `OfflinePlayground.jsx` / `EmbedPlayground.jsx` — standalone Pyodide pages
7. `package.json` — dependencies to add/remove
8. `App.jsx` — route names

---

## 7. What NOT to Delete Blindly

> **Critical: Do not delete files without understanding what they do.**

### Files That Look Python-Specific But Contain Generic Code

| File | Python-Specific Part | Generic Part (Keep) |
|------|---------------------|---------------------|
| `PyIDE.jsx` | `usePyRunner` usage, `python()` extension | Y.js setup, WebSocket setup, chat, voice, drawing, awareness |
| `CodeLayout.jsx` | `main.py` label, `.py` download option, Plot panel | Entire layout structure, console panel, chat panel, resize logic |
| `OfflinePlayground.jsx` | Pyodide usage | General page structure (may be repurposed for offline SQL) |

### Files That Should NOT Be Deleted

- `codes/consumers.py` — This is the Y.js WebSocket consumer. It syncs editor text (which will be SQL, not Python). It is NOT a Python execution component.
- `codes/tasks.py` — Celery tasks for persisting Y.js documents. Language-agnostic.
- `codes/models.py` — Stores editor content as text. Works for SQL too.
- Any file in `users/`, `usergroups/`, `projects/` — these are domain models, not Python execution.

### The `pyrunner/` Directory

This entire directory IS Python-specific and CAN be removed — but only after:
1. A replacement `useSqlRunner` hook exists
2. All references to `usePyRunner`, `TaskClient`, and `Worker` are removed from other files
3. The app compiles and runs without errors
