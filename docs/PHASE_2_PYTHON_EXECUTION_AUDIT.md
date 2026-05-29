# Phase 2 Python Execution Audit

Date: 2026-05-29

Scope: planning and audit only. No source code changes are part of Phase 2.

This document maps the inherited Python/Pyodide execution path so later phases can replace it with SQL execution without breaking collaboration, persistence, groups, auth, chat, voice, or drawing.

## Summary

Python execution currently runs entirely in the browser. The Django backend is not involved in executing Python code. The backend stores and syncs editor text through Y.js, Redis, and the `Code` model, but it never receives a "run code" request.

Current execution chain:

```text
CodeLayout Run button
  -> PyIDE onRun
  -> usePyRunner.runCode(codeString)
  -> TaskClient.runCodeTask(entry, outputCallback, inputCallback)
  -> Worker.runCode(...)
  -> Pyodide
  -> Python check_entry(entry, callback)
  -> PyodideRunner.run(code_to_run)
  -> output callback parts
  -> usePyRunner terminalRef.pushToStdout(parts)
  -> consoleOutput / plotSrc / waitingForInput / errorLine state
  -> PyIDE consoleSlot / plotSlot / inputSlot
  -> CodeLayout panels
```

Target SQL execution should not reuse this browser execution chain. Phase 4 should introduce a backend SQL execution service that executes against isolated project SQLite databases, never against the Django application database.

## Pyodide Loading Flow

Primary file: `frontend/reactapp/src/pyrunner/Worker.js`.

Important references:

- Imports `loadPyodide` from `pyodide` and helpers from `pyodide-worker-runner` at `Worker.js:2-9`.
- Loads Pyodide from jsDelivr with `indexURL: "https://cdn.jsdelivr.net/pyodide/v0.29.0/full/"` at `Worker.js:144-148`.
- Calls `initPyodide(pyodide)` at `Worker.js:150`.
- Loads `micropip` at `Worker.js:152-154`.
- Installs Python packages at `Worker.js:156-185`.
- Applies `pyodide_http.patch_all()` at `Worker.js:187-190`.
- Runs the wrapper script with `pyodide.runPython(PYTHON_RUNNER_WRAPPER)` at `Worker.js:192`.
- Exposes `init` and `runCode` through Comlink at `Worker.js:198-236`.

Installed packages:

| Package | Purpose |
| --- | --- |
| `python_runner` | Provides `PyodideRunner` used to execute submitted Python. |
| `colorama` | Imported and patched so `colorama.init` becomes a no-op. |
| `matplotlib` | Plot support. |
| `Pillow` | GIF animation rendering support for matplotlib animations. |
| `pandas` | Preinstalled data science package. |
| `scipy` | Preinstalled data science package. |
| `numpy` | Preinstalled data science package. |
| `pyodide-http` | Patches HTTP libraries for Pyodide/browser behavior. |

The loading process is wrapped in `PyodideFatalErrorReloader`, so calls go through `reloader.withPyodide(...)`.

## Python Runner Wrapper

`PYTHON_RUNNER_WRAPPER` is a Python script embedded in `Worker.js:12-140`.

It does the following:

- Imports `PyodideRunner` from `python_runner` and creates `default_runner` at `Worker.js:12-30`.
- Imports matplotlib and animation support at `Worker.js:31-35`.
- Patches `colorama.init` to a no-op at `Worker.js:36-40`.
- Replaces `plt.show` with `custom_plt_show` at `Worker.js:42-98`.
- Serializes matplotlib static plots or animations into base64 image data and emits output type `show_image` at `Worker.js:56-94`.
- Replaces traceback serialization to filter out `python_runner` and `<exec>` frames at `Worker.js:103-115`.
- Converts `traceback` and `syntax_error` output types into `internal_error` at `Worker.js:117-127`.
- Defines `check_entry(entry, callback)` at `Worker.js:129-139`.

`check_entry` is the Python execution boundary. It:

- Reads the submitted code from `entry.input`.
- Sets the logical filename to `/main.py`.
- Sets the runner callback.
- Calls `default_runner.run(code_to_run)`.
- Clears tracing with `sys.settrace(None)` in a `finally` block.

## Worker and Interrupt Communication

Primary file: `frontend/reactapp/src/pyrunner/TaskClient.js`.

Important references:

- Imports the worker with Vite's worker suffix: `./Worker.js?worker` at `TaskClient.js:1`.
- Creates a `sync-message` channel scoped to `/` at `TaskClient.js:6`.
- Creates `taskClient = new PyodideClient(() => new MyPyodideWorker(), channel)` at `TaskClient.js:8`.
- `runCodeTask(entry, outputCallback, inputCallback)` wraps callbacks and calls `taskClient.workerProxy.runCode` at `TaskClient.js:10-25`.
- Callback functions are proxied through Comlink at `TaskClient.js:23-24`.
- Interrupts are surfaced as `InterruptError` and converted to an `{ interrupted: true }` result at `TaskClient.js:26-35`.

Stop behavior:

- `usePyRunner.stopCode()` calls `taskClient.interrupt()` at `usePyRunner.js:151-156`.
- The hook clears `waitingForInput`, marks execution not running, and appends `>>> Stopped by user`.

## Run Button Flow

Primary files:

- `frontend/reactapp/src/components/CodeLayout.jsx`
- `frontend/reactapp/src/pages/PyIDE.jsx`
- `frontend/reactapp/src/hooks/usePyRunner.js`
- `frontend/reactapp/src/pyrunner/TaskClient.js`
- `frontend/reactapp/src/pyrunner/Worker.js`

Detailed flow:

1. `CodeLayout` renders the Run button when `isLoading` and `isRunning` are false at `CodeLayout.jsx:280-295`.
2. Clicking Run calls `onRun()` and forces the console visible at `CodeLayout.jsx:288-290`.
3. `PyIDE` passes `onRun={() => runner.runCode(ytextRef.current ? ytextRef.current.toString() : code)}` at `PyIDE.jsx:827`.
4. `runner` is created by `usePyRunner()` at `PyIDE.jsx:133`.
5. `usePyRunner.runCode(codeString)` starts at `usePyRunner.js:122`.
6. The hook sets `isRunning`, clears `errorLine` and `plotSrc`, and appends `>>> Running...` at `usePyRunner.js:123-128`.
7. The hook calls `runCodeTask({ input: codeString }, outputCallback, inputCallback)` at `usePyRunner.js:129-134`.
8. `TaskClient.runCodeTask` calls `taskClient.workerProxy.runCode` at `TaskClient.js:20-25`.
9. `Worker.runCode` builds a `makeRunnerCallback` bridge at `Worker.js:205-213`.
10. `Worker.runCode` calls `pyodide_worker_runner.install_imports(entry.input)` before execution at `Worker.js:215-221`.
11. `Worker.runCode` retrieves Python `check_entry` and calls it at `Worker.js:223-225`.
12. `check_entry` calls `default_runner.run(code_to_run)` at `Worker.js:129-139`.
13. Output returns through the callback into `usePyRunner` and is rendered by `PyIDE` and `CodeLayout`.

Stop button flow:

1. `CodeLayout` renders Stop when `isRunning` is true at `CodeLayout.jsx:285-286`.
2. `PyIDE` passes `onStop={runner.stopCode}` at `PyIDE.jsx:828`.
3. `usePyRunner.stopCode()` calls `taskClient.interrupt()` at `usePyRunner.js:151-156`.
4. `TaskClient.runCodeTask` catches `InterruptError` at `TaskClient.js:26-35`.

## Output Flow

Primary files:

- `frontend/reactapp/src/hooks/usePyRunner.js`
- `frontend/reactapp/src/pages/PyIDE.jsx`
- `frontend/reactapp/src/components/CodeLayout.jsx`

State owned by `usePyRunner`:

| State | Current use |
| --- | --- |
| `consoleOutput` | Ordered terminal entries rendered by console panels. |
| `plotSrc` | Base64 image or GIF URL for matplotlib output. |
| `waitingForInput` | Enables an input panel for Python `input()`. |
| `errorLine` | Drives CodeMirror line decoration for Python traceback line numbers. |
| `isLoading` | Tracks Pyodide initialization. |
| `isRunning` | Tracks active Python execution. |

Callback processing:

- `terminalRef.current.pushToStdout(parts)` is configured at `usePyRunner.js:76-120`.
- Output type `show_image` sets `plotSrc` at `usePyRunner.js:81-82`.
- Output type `input_prompt` writes a system entry and sets `waitingForInput` at `usePyRunner.js:83-86`.
- Output types `internal_error` and `stderr` become error/progress entries at `usePyRunner.js:87-107`.
- Python traceback line numbers are parsed from `/main.py` at `usePyRunner.js:100-106`.
- Other parts become normal output at `usePyRunner.js:108-111`.

Rendering in `PyIDE`:

- Console entries are transformed into `consoleSlot` at `PyIDE.jsx:662-686`.
- ANSI text is converted to HTML with `Anser.ansiToHtml` at `PyIDE.jsx:680-681`.
- Python input prompt UI is built as `inputSlot` at `PyIDE.jsx:688-701`.
- Plot output is passed to `CodeLayout` as an `<img>` at `PyIDE.jsx:811`.

Rendering in `CodeLayout`:

- Console header and body are rendered at `CodeLayout.jsx:331-364`.
- Input content is rendered below the console at `CodeLayout.jsx:366-368`.
- Plot panel is rendered when `showPlot` is true at `CodeLayout.jsx:370-380` and beyond.

Reusable vs Python-specific output pieces:

| Piece | Classification | Future action |
| --- | --- | --- |
| `consoleOutput` text list | Partially reusable | Replace with result table/error model or keep temporarily for system messages. |
| `plotSrc` / Plot panel | Python-specific | Remove or repurpose after SQL results UI exists. |
| `waitingForInput` / input panel | Python-specific | Remove for SQL execution. |
| `errorLine` | Partially reusable | Could be retained only if SQL parser/backend can return editor line numbers. |
| `Anser` ANSI rendering | Python-specific unless SQL errors use ANSI | Likely remove once console is replaced. |

## Editor Language Configuration

Primary file: `frontend/reactapp/src/pages/PyIDE.jsx`.

Current configuration:

- Imports `python` from `@codemirror/lang-python` at `PyIDE.jsx:12`.
- Uses `python()` in the CodeMirror extensions array at `PyIDE.jsx:608-612`.
- Keeps `yCollab(...)` in the same extensions array at `PyIDE.jsx:610`.
- Keeps `errorLineField` in the same extensions array at `PyIDE.jsx:611`.
- Basic setup at `PyIDE.jsx:619-630` is editor behavior, not Python-specific.

Other Python-mode usage:

- `OfflinePlayground.jsx` imports `python` at `OfflinePlayground.jsx:11` and uses `python()` at `OfflinePlayground.jsx:243`.
- `EmbedPlayground.jsx` imports `python` at `EmbedPlayground.jsx:8` and uses `python()` at `EmbedPlayground.jsx:307`.

Keep:

- `yCollab(...)` in the main collaborative editor. It syncs text and awareness, not Python.
- `errorLineField` if future SQL errors can map to line numbers.
- CodeMirror basic setup unless a later SQL editor design changes it deliberately.

Replace in Phase 3:

- `@codemirror/lang-python` dependency.
- `python()` extensions.
- Python loading text and editor terminology.

## Python Labels and Download Options

Primary file: `frontend/reactapp/src/components/CodeLayout.jsx`.

Current Python-labeled UI:

- Download options are `.py`, `.txt`, `.docx`, `.pdf` at `CodeLayout.jsx:236-241`.
- Editor file label is `main.py` at `CodeLayout.jsx:319`.
- Console header is `Console` at `CodeLayout.jsx:341-344`.
- Plot panel exists at `CodeLayout.jsx:370-380` and beyond.

Download implementation in `PyIDE`:

- Builds filename from project name at `PyIDE.jsx:509-513`.
- Saves `.py` with MIME type `text/python` at `PyIDE.jsx:514`.
- Saves `.txt`, `.pdf`, and `.docx` at `PyIDE.jsx:515-523`.

Standalone playground download implementation:

- `OfflinePlayground.jsx` saves `.py` with MIME type `text/python` at `OfflinePlayground.jsx:147-152`.

Phase 3 should change visible file terminology (`main.py` -> `query.sql`) and download behavior (`.py` -> `.sql`) without rewriting the layout.

## Pyodide Notice Modal

Primary file: `frontend/reactapp/src/components/PyodideNotice.jsx`.

Current behavior:

- Component is named `PyodideModal` at `PyodideNotice.jsx:4`.
- Uses localStorage key `pyodideModalShown` at `PyodideNotice.jsx:7-16`.
- Announces Pyodide and CPython at `PyodideNotice.jsx:32-34`.
- Lists scientific stack, traceback handling, and CPython compatibility at `PyodideNotice.jsx:37-60`.

Current usage:

- No active imports of `PyodideNotice.jsx` were found by repository search.

Future action:

- Safe to remove after verifying no route or lazy import was added.
- Alternatively replace with a SQLTogether-specific notice, but do not keep Pyodide-specific copy.

## Offline and Embed Playground Usage

### OfflinePlayground

Primary file: `frontend/reactapp/src/pages/OfflinePlayground.jsx`.

Python/Pyodide-specific pieces:

- Imports `Anser` at `OfflinePlayground.jsx:7`.
- Imports `python` at `OfflinePlayground.jsx:11`.
- Imports `usePyRunner` at `OfflinePlayground.jsx:21`.
- Default starter content is Python at `OfflinePlayground.jsx:41-47`.
- Creates `runner = usePyRunner()` at `OfflinePlayground.jsx:72`.
- Uses `python()` in CodeMirror at `OfflinePlayground.jsx:243`.
- Renders console output with `Anser.ansiToHtml` at `OfflinePlayground.jsx:256-280`.
- Renders Python input UI at `OfflinePlayground.jsx:282-300`.
- Renders plot output from `runner.plotSrc` at `OfflinePlayground.jsx:325-333`.
- Runs code via `runner.runCode(code)` at `OfflinePlayground.jsx:341-345`.

Generic pieces worth preserving or repurposing:

- Local state and localStorage persistence.
- Snippet loading from `/api/public/snippet/:token`.
- Local drawing canvas via `useLocalCanvas`.
- Download shell, if updated to SQL.

### EmbedPlayground

Primary file: `frontend/reactapp/src/pages/EmbedPlayground.jsx`.

Python/Pyodide-specific pieces:

- Imports `Anser` at `EmbedPlayground.jsx:4`.
- Imports `python` at `EmbedPlayground.jsx:8`.
- Imports `usePyRunner` at `EmbedPlayground.jsx:17`.
- Creates `runner = usePyRunner()` at `EmbedPlayground.jsx:61`.
- Auto-scrolls on `runner.consoleOutput` at `EmbedPlayground.jsx:110-115`.
- Auto-focuses input on `runner.waitingForInput` at `EmbedPlayground.jsx:117-125`.
- Stop button calls `runner.stopCode` at `EmbedPlayground.jsx:254-255`.
- Run button calls `runner.runCode(code)` at `EmbedPlayground.jsx:257-259`.
- File label is `main.py` at `EmbedPlayground.jsx:275`.
- Uses `python()` in CodeMirror at `EmbedPlayground.jsx:301-307`.
- Renders plot output from `runner.plotSrc` at `EmbedPlayground.jsx:343-351`.
- Renders console output with `Anser.ansiToHtml` at `EmbedPlayground.jsx:353-375`.
- Renders Python input UI at `EmbedPlayground.jsx:378-397`.

Generic pieces worth preserving or repurposing:

- Snippet fetch from `/api/public/snippet/:token`.
- Read-only/reset-to-original snippet behavior.
- Local drawing controls and layout shell.

## Plot Panel

Plot support is Python-specific in the current codebase.

Source of plot data:

- `Worker.js` patches `plt.show` and emits `show_image` output at `Worker.js:42-98`.
- `usePyRunner` converts `show_image` parts to a data URL in `plotSrc` at `usePyRunner.js:81-82`.

Display points:

- Main editor passes `runner.plotSrc` to `CodeLayout` at `PyIDE.jsx:811`.
- Offline playground passes `runner.plotSrc` to `CodeLayout` at `OfflinePlayground.jsx:325-333`.
- Embed playground renders `runner.plotSrc` inline at `EmbedPlayground.jsx:343-351`.
- `CodeLayout` has a plot panel controlled by `showPlot` at `CodeLayout.jsx:370-380` and related resize state.

Future action:

- Remove plot-specific execution and UI when SQL result tables are implemented.
- If a future SQL charting feature is desired, it should be designed separately and should not depend on Pyodide/matplotlib.

## Web Workers, Service Worker, and Vite Configuration

Worker files:

- The only `?worker` import found is `TaskClient.js:1`, importing `./Worker.js?worker`.

Vite configuration:

- `vite.config.js` aliases `comlink` to its ESM build at `vite.config.js:26-30`.
- `vite.config.js` excludes `pyodide` from dependency optimization at `vite.config.js:32-34`.
- `vite.config.js` sets worker format to ES modules at `vite.config.js:36-38`.
- Dev server COOP/COEP headers are set at `vite.config.js:40-45`, likely supporting Pyodide/worker isolation requirements.
- PWA configuration injects `src/sw.js` at `vite.config.js:10-23`.

Service worker:

- `src/sw.js` imports `serviceWorkerFetchListener` from `sync-message` at `sw.js:2`.
- `serviceWorkerFetchListener()` is registered at `sw.js:10`.
- Other `sw.js` routes are general PWA/API/static caching and are not themselves Python execution.

Future action:

- Once Pyodide is removed, verify whether `sync-message`, Comlink aliasing, Pyodide optimize exclusion, worker format, and COOP/COEP headers are still needed.
- Do not remove the PWA service worker blindly; only remove the `sync-message` dependency if no other code uses it.

## Python/Pyodide-Specific npm Dependencies

Primary file: `frontend/reactapp/package.json`.

Current dependencies:

| Package | Line | Classification | Future action |
| --- | ---: | --- | --- |
| `@codemirror/lang-python` | 16 | Python syntax highlighting | Replace with `@codemirror/lang-sql` in Phase 3. |
| `anser` | 21 | ANSI terminal output rendering | Remove if result table/errors replace console ANSI output. |
| `comlink` | 24 | Worker/main-thread RPC | Remove if no workers remain after Pyodide replacement. |
| `pyodide-worker-runner` | 31 | Pyodide lifecycle and runner bridge | Remove after SQL runner replacement. |
| `sync-message` | 39 | Service-worker channel used by `PyodideClient` | Remove after Pyodide client removal, if not otherwise used. |

Note: the `pyodide` package is present transitively through `pyodide-worker-runner`, not as a direct package.json dependency.

Future SQL dependency:

- Add `@codemirror/lang-sql` when converting editor language in Phase 3.

## Backend Involvement in Python Execution

Finding: the backend is not involved in Python execution.

Backend responsibilities today:

- Auth and group/project membership.
- Project CRUD and starter text creation.
- Y.js WebSocket sync for editor text.
- Chat messages.
- Voice signaling.
- Redis-backed active user tracking.
- Celery persistence of Y.js documents into `Code.content`.
- Public snippet retrieval.

No backend execution endpoint exists:

- `backend/backend/urls.py` includes only admin, `users.urls`, and `usergroups.urls` at `backend/urls.py:4-10`.
- `users.urls` contains auth, share-link validation, and public snippet routes at `users/urls.py:7-24`.
- `usergroups.urls` contains group routes and nested project routes at `usergroups/urls.py:4-12`.
- `projects.urls` contains list/create/edit/delete/get/share/snippet routes at `projects/urls.py:4-20`.
- No `run`, `execute`, `query`, or Python execution endpoint exists in these URL patterns.

Backend files verified language-agnostic:

- `codes/consumers.py` handles Y.js updates, awareness, chat, voice signaling, membership checks, and Redis YDoc state. It syncs text; it does not execute Python.
- `codes/tasks.py` persists dirty Y.js project documents and cleans ghost active projects. It does not execute Python.
- `codes/models.py` stores `Code.content` as text. The model name is Python-era terminology, but the field is language-agnostic.
- `utils/redis_helpers.py` persists YDoc text to `Code.content` and manages Redis keys. It does not execute Python.

Backend Python-specific data:

- `backend/backend/settings/base.py` still contains Python starter templates (`NONE_TEMPLATE`, `PYTEST_TEMPLATE`, `PLT_TEMPLATE`) at `base.py:221-282`.
- `backend/projects/serializers.py` exposes template choices `none`, `pytest`, and `plt` and creates `Code.content` from those settings at `serializers.py:18-45`.

Future action:

- Phase 3 should convert starter text and template labels if in scope.
- Phase 4 should add SQL execution endpoints and models using isolated project databases. It must not use Django's default database connection for student SQL.

## File Map

### Python-specific: Replace or remove after replacement exists

| File | Why |
| --- | --- |
| `frontend/reactapp/src/pyrunner/Worker.js` | Pyodide loader, package installer, Python runner wrapper, matplotlib handling. |
| `frontend/reactapp/src/pyrunner/TaskClient.js` | Pyodide worker client, Comlink bridge, interrupt channel. |
| `frontend/reactapp/src/hooks/usePyRunner.js` | Pyodide init, Python execution state, console/plot/input/error handling. |
| `frontend/reactapp/src/components/PyodideNotice.jsx` | Pyodide-specific notice copy and localStorage key. |

### Mixed: Modify carefully

| File | Python-specific parts | Generic parts to preserve |
| --- | --- | --- |
| `frontend/reactapp/src/pages/PyIDE.jsx` | `usePyRunner`, `python()`, console/plot/input slots, `.py` download, Python loading text. | Y.js setup, WebSocket setup, auth/share token handling, chat, voice, drawing, awareness, project name editing. |
| `frontend/reactapp/src/components/CodeLayout.jsx` | `main.py`, `.py`, Console/Plot labels if result UI replaces them. | Layout shell, resizing, chat panel, connected users, drawing/voice control slots, run/stop button slots. |
| `frontend/reactapp/src/pages/OfflinePlayground.jsx` | `usePyRunner`, `python()`, Python starter text, console/plot/input output. | Local editor state, localStorage persistence, snippet loading, local drawing, download shell. |
| `frontend/reactapp/src/pages/EmbedPlayground.jsx` | `usePyRunner`, `python()`, `main.py`, console/plot/input output. | Snippet fetch, read-only embed layout, reset-to-original behavior, local drawing. |
| `frontend/reactapp/src/sw.js` | `sync-message` listener for Pyodide client channel. | PWA precache and route caching. |
| `frontend/reactapp/vite.config.js` | Pyodide optimize exclusion, Comlink alias, worker settings, possibly COOP/COEP headers. | React, Tailwind, PWA setup. |
| `frontend/reactapp/package.json` | Python/Pyodide dependencies. | React, Vite, Y.js, UI, auth, document export dependencies. |
| `backend/backend/settings/base.py` | Python starter templates. | Django settings and shared app config. |
| `backend/projects/serializers.py` | Python starter template choices and initial code selection. | Project creation serializer and `Code.content` creation pattern. |

### Language-agnostic: Keep

| File or area | Why |
| --- | --- |
| `frontend/reactapp/src/hooks/useVoiceChat.js` | Voice chat is language-agnostic. |
| `frontend/reactapp/src/hooks/useSharedCanvas.js` | Collaborative drawing is language-agnostic. |
| `frontend/reactapp/src/hooks/useLocalCanvas.js` | Local drawing is language-agnostic. |
| `frontend/reactapp/src/components/GroupsList.jsx` | Group UI is language-agnostic. |
| `frontend/reactapp/src/components/ProjectsList.jsx` | Project UI is language-agnostic. |
| `frontend/reactapp/src/components/Modals/ShareModal.jsx` | Share mechanics are language-agnostic, though copy may need SQL terminology. |
| `frontend/reactapp/src/components/auth.js` | Auth helper is language-agnostic. |
| `frontend/reactapp/src/components/ProtectedRoute.jsx` | Routing guard is language-agnostic. |
| `frontend/reactapp/src/components/PublicRoute.jsx` | Routing guard is language-agnostic. |
| `frontend/reactapp/src/components/SharedProjectHandler.jsx` | Share-link routing is language-agnostic. |
| `frontend/reactapp/axiosConfig.jsx` | HTTP client setup is language-agnostic. |
| `backend/users/` | Authentication and user identity are language-agnostic. |
| `backend/usergroups/` | Group ownership and membership are language-agnostic. |
| `backend/projects/` | Project CRUD is mostly language-agnostic, except starter template choices. |
| `backend/codes/consumers.py` | Y.js sync, chat, voice signaling, awareness, and active user tracking. |
| `backend/codes/tasks.py` | Y.js persistence and cleanup tasks. |
| `backend/codes/models.py` | Stores editor text as `content`. |
| `backend/utils/redis_helpers.py` | Redis/YDoc persistence helpers. |

## Replacement Plan by Phase

### Phase 3: Convert editor experience to SQL

Do:

- Replace `@codemirror/lang-python` with `@codemirror/lang-sql`.
- Replace all `python()` editor extensions with `sql()`.
- Change visible Python file labels and download extension to SQL.
- Replace starter editor content with SQL-oriented text.
- Stub or replace `usePyRunner` enough that Run/Stop UI does not break before backend execution exists.
- Remove or disable visible Pyodide-specific UI.

Do not:

- Implement backend SQL execution.
- Delete backend collaboration or persistence code.
- Delete `pyrunner/` until imports are removed and replacement runner behavior exists.

### Phase 4: Add SQLite execution

Do:

- Add a backend SQL execution app/service.
- Execute only against isolated project SQLite files.
- Add auth and membership checks.
- Add timeout, row limit, query length limit, and dangerous statement controls.
- Return result table data and sanitized errors.
- Log query history.

Do not:

- Execute student SQL through Django `DATABASES["default"]`, ORM raw cursors, or the app PostgreSQL database.

## Risks and Dependencies

1. `PyIDE.jsx` mixes Python execution with critical collaboration. Rewriting it wholesale risks breaking Y.js sync, awareness, chat, voice, drawing, share tokens, and autosave.
2. `CodeLayout.jsx` is mostly generic. Rewriting it wholesale risks layout regressions. Prefer targeted label/output-slot changes.
3. `usePyRunner` owns several UI states. A replacement hook should provide compatible loading/running/error/result state before imports are removed.
4. `pyrunner/` cannot be deleted until all imports from `usePyRunner` and callers are removed.
5. `sync-message` is wired into the service worker for Pyodide communication. Removing it requires checking `TaskClient.js`, `sw.js`, and PWA behavior together.
6. The backend currently has no execution endpoint. SQL execution is a new server-side responsibility and must be implemented with the sandbox rules from `docs/SQL_SANDBOX_STRATEGY.md`.
7. Existing starter templates in backend settings and project serializer are Python-specific. They affect new project content but are not execution logic.
8. Public snippets currently expose editor text and use Offline/Embed playgrounds that execute Python locally. They need a SQL-era behavior decision before removing Pyodide.

## Phase 2 Definition of Done

- Complete execution flow documented: done.
- Pyodide loading flow documented: done.
- Output, input, error, and plot flows documented: done.
- CodeMirror Python configuration documented: done.
- `main.py` and download options documented: done.
- `PyodideNotice.jsx`, OfflinePlayground, and EmbedPlayground documented: done.
- Python/Pyodide npm dependencies identified: done.
- Backend involvement verified: done. Current backend does not execute Python.
- File map created: done.
- Source code unchanged by this audit: required.
