# Agent Handoff Guide — SQLTogether

This guide is for AI agents working on SQLTogether. Read this first before doing any work.

---

## 1. Project Summary

**SQLTogether** is a collaborative browser-based SQL teaching and learning environment.

It is adapted from [PyTogether](https://github.com/SJRiz/pytogether), a collaborative Python IDE by Syed Jawad Rizvi. SQLTogether replaces Python execution with SQL query execution against isolated sandbox databases, while preserving the real-time collaboration features (Y.js, WebSockets, chat, voice, drawing).

**Current status:** Early adaptation. The codebase still contains Python/Pyodide execution code that will be incrementally replaced.

---

## 2. Repository Structure (Observed)

```
sqltogether/
├── backend/                       # Django project
│   ├── backend/                   # Django config (settings, urls, asgi, celery, jwt middleware)
│   │   └── settings/              # Split settings (dev, prod, etc.)
│   ├── users/                     # Custom User model (email-based auth)
│   ├── usergroups/                # Group model (owner, members, access code)
│   ├── projects/                  # Project model (belongs to group)
│   ├── codes/                     # Code model + Y.js WebSocket consumer + Celery tasks
│   ├── utils/                     # Redis helpers for Y.js persistence
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.dev
├── frontend/
│   └── reactapp/                  # React + Vite app
│       ├── src/
│       │   ├── App.jsx            # Router
│       │   ├── pages/             # PyIDE, GroupsProjects, Login, Register, About, etc.
│       │   ├── components/        # CodeLayout, GroupsList, ProjectsList, PyodideNotice, etc.
│       │   ├── hooks/             # usePyRunner, useVoiceChat, useSharedCanvas, etc.
│       │   ├── pyrunner/          # Pyodide Web Worker + TaskClient (Python-specific)
│       │   └── main.jsx, index.css
│       ├── package.json
│       └── vite.config.js
├── docs/                          # Planning documents (YOU SHOULD READ THESE)
├── .agent/                        # Agent rules and workflows
├── docker-compose-dev.yaml        # Dev Docker setup (Django, PostgreSQL, Redis, Celery)
├── docker-compose.yaml            # Prod Docker setup
├── self-hosting/                  # Self-hosting config (nginx, docker-compose)
├── package.json                   # Root package.json (npm run dev orchestrator)
├── README.md                      # Project README (already rebranded)
├── NOTICE.md                      # PyTogether attribution
└── LICENSE                        # MIT License (original copyright preserved)
```

---

## 3. Architecture Summary

| Component | Technology | Notes |
|-----------|------------|-------|
| Frontend | React + Vite + TailwindCSS | Single-page app |
| Editor | CodeMirror (currently Python mode) | Will change to SQL mode |
| Real-time sync | Y.js (CRDT) over WebSocket | Language-agnostic, keep as-is |
| Backend | Django + Django REST Framework | REST API + WebSocket consumers |
| WebSocket | Django Channels | Y.js sync, chat, voice signaling |
| Async tasks | Celery + Celery Beat | Y.js persistence, cleanup |
| App database | PostgreSQL | Users, groups, projects, metadata — NEVER for student SQL |
| Cache/broker | Redis | Y.js state, channel layer, Celery broker |
| Current execution | Pyodide (browser WebAssembly) | Will be replaced by server-side SQL execution |
| Target execution | Server-side SQLite (MVP) | Backend executes SQL against isolated .db files |

### Critical Architecture Rule

> **Student SQL must NEVER execute against the application database (PostgreSQL).**
> Student SQL runs only against isolated project database files (SQLite for MVP).

---

## 4. Active Priorities

The project follows a phased development plan. See `docs/SQLTOGETHER_PHASES.md` for full details.

**Current priority: Phase 0 — Stabilize the imported codebase.**

Before any code changes, confirm the app runs and document its current state.

---

## 5. Coding Rules

1. **Do phased development.** Follow the phases in order. Do not skip ahead.
2. **Preserve collaboration features.** Y.js, WebSockets, chat, voice, and drawing are valuable and language-agnostic.
3. **Do not perform massive rewrites.** Make small, focused changes.
4. **Document affected files before major changes.** List what you'll modify and why.
5. **Prefer small commits.** Each change should be reviewable and reversible.
6. **Keep terminology SQL-focused.** Use "query" not "code", "result table" not "console output", "query.sql" not "main.py".
7. **Do not invent new architecture** unless the planning docs explicitly call for it.
8. **Read the planning docs** before implementing any phase: `SQLTOGETHER_PRODUCT_PLAN.md`, `SQLTOGETHER_ARCHITECTURE.md`, `SQLTOGETHER_PHASES.md`, `SQL_SANDBOX_STRATEGY.md`, `PYTHON_TO_SQL_CONVERSION_GUIDE.md`.

---

## 6. Safety Rules

1. **Never run student SQL against the app database** (PostgreSQL `DATABASES['default']`).
2. **Use isolated project databases** (one SQLite file per project for MVP).
3. **Add timeouts** (default 5 seconds), **row limits** (default 1000), **query length limits** (default 10KB).
4. **Do not expose filesystem paths** in API responses or error messages.
5. **Do not add arbitrary external DB connections** in early phases.
6. **Block dangerous SQLite commands:** `ATTACH DATABASE`, `LOAD_EXTENSION`, dangerous PRAGMAs.
7. **Templates are read-only** from the student perspective.

See `docs/SQL_SANDBOX_STRATEGY.md` for full details.

---

## 7. Attribution Rules

1. **Preserve PyTogether credit** in README, NOTICE.md, and LICENSE.
2. **Preserve the original MIT license notice** with copyright `(c) 2025 Syed Jawad Rizvi`.
3. **Do not remove the original copyright** — only add a separate copyright for SQLTogether contributions.
4. **Do not present SQLTogether as official PyTogether** — it is an independent adaptation.
5. **Keep the NOTICE.md file** with a link to the original PyTogether repository.
6. **Do not remove links to the original repo** unless replacing with proper attribution.

---

## 8. Phase Order

| Phase | Name | Status |
|-------|------|--------|
| 0 | Stabilize imported codebase | **← Current** |
| 1 | Rebrand safely | Not started |
| 2 | Audit Python execution path | Not started |
| 3 | Convert editor to SQL | Not started |
| 4 | Add MVP SQLite execution | Not started |
| 5 | Add group database templates | Not started |
| 6 | Teacher remote teaching tools | Not started |
| 7 | Multiple SQL engine support | Not started |
| 8 | Lessons/exercises | Not started |
| 9 | Hardening/deployment | Not started |

**Rule:** Complete Phase 0 before starting Phase 1. Complete Phase 1 and 2 before Phase 3. Etc.

---

## 9. How to Report Changes

When you complete a phase or significant piece of work:

1. **List files modified, added, or deleted.**
2. **Summarize what changed and why.**
3. **Note any issues discovered.**
4. **Confirm the app still runs** (or explain what's broken and why).
5. **Update phase status** in this guide if applicable.
6. **Suggest the next recommended action.**

---

## 10. Validation Checklist

Run this checklist after any code changes:

- [ ] App still builds (`npm run dev` starts without errors)
- [ ] Backend starts (Django, PostgreSQL, Redis, Celery containers)
- [ ] Frontend starts (Vite dev server on localhost:5173)
- [ ] Can log in and create/join a group
- [ ] Can create a project and open the editor
- [ ] Collaboration features work (Y.js sync, chat)
- [ ] Attribution preserved (README, NOTICE, LICENSE unchanged or still crediting PyTogether)
- [ ] No SQL safety rules violated
- [ ] Phase scope respected (didn't do work belonging to a later phase)
- [ ] No unrelated files modified

---

## 11. Common Mistakes to Avoid

| Mistake | Why It's Bad | What to Do Instead |
|---------|-------------|-------------------|
| Deleting `pyrunner/` before Phase 3 | Breaks the app — PyIDE.jsx imports from it | Wait until Phase 3, build replacement first |
| Connecting student SQL to PostgreSQL | Massive security risk | Always use isolated project databases |
| Rewriting `CodeLayout.jsx` entirely | Breaks collaboration UI layout | Make targeted label/option changes only |
| Removing `codes/consumers.py` | This is the Y.js WebSocket consumer, NOT Python execution | Keep it — it's language-agnostic |
| Removing `codes/tasks.py` | This is the Celery Y.js persistence, NOT Python execution | Keep it — it's language-agnostic |
| Skipping Phase 0 | You don't know if the app works | Always verify baseline first |
| Adding DuckDB or PostgreSQL before SQLite MVP | Overbuilding before basics work | SQLite first (Phase 4), other engines later (Phase 7) |
| Removing original copyright | Violates MIT license | Keep `(c) 2025 Syed Jawad Rizvi` in LICENSE |
| Massive multi-file rewrites | Hard to debug, easy to break things | Small focused changes, one file at a time |

---

## 12. Key Documents to Read

| Document | Path | Purpose |
|----------|------|---------|
| Product Plan | `docs/SQLTOGETHER_PRODUCT_PLAN.md` | Vision, users, concepts, MVP scope |
| Architecture | `docs/SQLTOGETHER_ARCHITECTURE.md` | System design, models, flows |
| Phases | `docs/SQLTOGETHER_PHASES.md` | Detailed roadmap with tasks and definitions of done |
| Sandbox Strategy | `docs/SQL_SANDBOX_STRATEGY.md` | SQL safety, isolation, limits |
| Conversion Guide | `docs/PYTHON_TO_SQL_CONVERSION_GUIDE.md` | Python-specific files and what to do with them |
| Project Rules | `.agent/rules/sqltogether-project-rules.md` | Workspace-level development rules |
| SQL Safety Rules | `.agent/rules/sql-safety-rules.md` | SQL execution safety rules |
| Attribution Rules | `.agent/rules/attribution-rules.md` | License and credit rules |
