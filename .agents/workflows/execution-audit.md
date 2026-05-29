# Workflow: Execution Audit

Use this workflow to audit the current Python execution system in the PyTogether codebase **before modifying or replacing it**.

This audit is required before Phase 3 (Convert Editor to SQL).

---

## Purpose

The inherited PyTogether codebase executes Python in the browser using Pyodide (WebAssembly). SQLTogether will replace this with server-side SQL execution. Before making any changes, you must fully understand the current execution system so you can:

1. Replace it safely without breaking collaboration features
2. Know which files to modify, replace, or keep
3. Avoid accidentally removing language-agnostic infrastructure

---

## Step 1: Find Pyodide

Locate all Pyodide-related code:

- [ ] `frontend/reactapp/src/pyrunner/Worker.js` — Web Worker that loads Pyodide
  - Document: What CDN is used? What version? What packages are installed?
  - Document: What is the `PYTHON_RUNNER_WRAPPER` script doing?
  - Document: How are `init()` and `runCode()` exposed?

- [ ] `frontend/reactapp/src/pyrunner/TaskClient.js` — Comlink bridge
  - Document: How does the main thread communicate with the worker?
  - Document: How are interrupts handled?

- [ ] `frontend/reactapp/package.json` — Dependencies
  - Document: Which npm packages are Pyodide-specific?
  - List: `pyodide-worker-runner`, `comlink`, `sync-message`, `anser`

---

## Step 2: Find Web Workers

- [ ] Identify all Web Worker files (files imported with `?worker` suffix)
- [ ] Check `vite.config.js` for worker-related configuration
- [ ] Check `sw.js` (service worker) — is it related to Pyodide or general PWA?
- [ ] Determine if Comlink or sync-message are used anywhere else besides Pyodide

---

## Step 3: Find the Run Button Flow

Trace the execution from button click to output:

- [ ] `CodeLayout.jsx` — Find the "Run" button (`onRun` prop)
- [ ] `PyIDE.jsx` — Find where `onRun` is connected (`runner.runCode(...)`)
- [ ] `usePyRunner.js` — Find `runCode(codeString)` function
- [ ] `TaskClient.js` — Find `runCodeTask(entry, outputCallback, inputCallback)`
- [ ] `Worker.js` — Find `runCode` function and `check_entry` Python function
- [ ] Document the complete chain: Button → Hook → Client → Worker → Pyodide → Callbacks

Also trace the "Stop" button:
- [ ] `CodeLayout.jsx` — Find the "Stop" button (`onStop` prop)
- [ ] `PyIDE.jsx` — Find where `onStop` is connected (`runner.stopCode()`)
- [ ] `usePyRunner.js` — Find `stopCode()` function
- [ ] `TaskClient.js` — Find `taskClient.interrupt()`

---

## Step 4: Find Editor Language Configuration

- [ ] `PyIDE.jsx` — Find `import { python } from "@codemirror/lang-python"`
- [ ] `PyIDE.jsx` — Find where `python()` is used in the CodeMirror `extensions` array
- [ ] Note what other extensions are in the array (these are language-agnostic):
  - `yCollab(...)` — Y.js collaboration (KEEP)
  - `errorLineField` — Error line highlighting (KEEP)
- [ ] Check if `python()` is used anywhere else in the codebase
- [ ] Find the `basicSetup` configuration — is any of it Python-specific?

---

## Step 5: Find Output Components

- [ ] `CodeLayout.jsx` — Find the console panel rendering
- [ ] `PyIDE.jsx` — Find `consoleSlot` construction (renders `runner.consoleOutput`)
- [ ] `PyIDE.jsx` — Find `plotSlot` or plot content (renders `runner.plotSrc`)
- [ ] `PyIDE.jsx` — Find `inputSlot` (renders input prompt for Python's `input()` function)
- [ ] `usePyRunner.js` — Find output processing:
  - `show_image` type → `setPlotSrc` (Python matplotlib plots)
  - `input_prompt` type → `setWaitingForInput` (Python input() calls)
  - `internal_error` / `stderr` type → error display
  - Default → standard output text
- [ ] Determine which output types are Python-specific vs reusable:
  - Plot panel: **Python-specific** (matplotlib) — will be removed or repurposed
  - Input panel: **Python-specific** (input() function) — will be removed
  - Console text output: **Partially reusable** — will become result table + error display

---

## Step 6: Find Backend Involvement

- [ ] Check if the Django backend is involved in Python execution
  - **Expected answer: No.** Pyodide runs entirely in the browser.
  - The backend handles Y.js sync, auth, groups, projects — not Python execution.
- [ ] Verify that `codes/consumers.py` is Y.js sync only (not Python execution)
- [ ] Verify that `codes/tasks.py` is Y.js persistence only (not Python execution)
- [ ] Verify that `codes/models.py` stores editor text content (not Python-specific)
- [ ] Check backend URL patterns for any execution-related endpoints
  - `backend/urls.py`, `users/urls.py`, `usergroups/urls.py`, `projects/urls.py`

---

## Step 7: Document Flow Before Modifying Code

Produce a written document (or update `docs/PYTHON_TO_SQL_CONVERSION_GUIDE.md`) with:

1. **Complete execution flow diagram** (button → hook → client → worker → output)
2. **File categorization:**

| Category | Files |
|----------|-------|
| Python-specific (REPLACE) | Worker.js, TaskClient.js, usePyRunner.js, PyodideNotice.jsx |
| Python-labeled (MODIFY) | PyIDE.jsx, CodeLayout.jsx, OfflinePlayground.jsx, EmbedPlayground.jsx |
| Language-agnostic (KEEP) | useVoiceChat.js, useSharedCanvas.js, consumers.py, tasks.py, all auth/group/project code |

3. **Dependency changes** (packages to remove, packages to add)
4. **Risks and dependencies** (what must be replaced before what can be removed)

---

## Output

After completing this audit, you should be able to answer:

1. How does Python execution currently work, end to end?
2. Which files are purely Python-specific and can be safely removed?
3. Which files contain a mix of Python and generic code?
4. What is the exact replacement plan for each Python-specific component?
5. What is the backend's role (or lack thereof) in execution?
6. What npm packages need to be added and removed?

**Do not modify any source code during this audit. Documentation only.**
