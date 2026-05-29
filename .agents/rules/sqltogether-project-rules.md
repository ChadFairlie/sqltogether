# SQLTogether Project Rules

These are persistent workspace rules for all agents working on SQLTogether.

## Identity

- SQLTogether is a **collaborative browser-based SQL teaching and learning platform**.
- It is adapted from PyTogether (a collaborative Python IDE).
- The core value proposition is: **write SQL, run queries, see results, learn together in real time**.

## Development Approach

1. **Follow phased development.** See `docs/SQLTOGETHER_PHASES.md`. Complete each phase before moving to the next.
2. **Preserve existing collaboration features** (Y.js real-time sync, chat, voice chat, drawing). These are valuable and language-agnostic.
3. **Do not perform massive rewrites.** Make small, focused, reversible changes.
4. **Document affected files before major changes.** List what you plan to modify and why before doing it.
5. **Prefer small commits/changes.** Each change should be independently verifiable.
6. **Read the planning docs** in `docs/` and the rules in `.agent/rules/` before implementing anything.

## Terminology

Use SQL-focused terminology consistently:

| Use This | Not This |
|----------|----------|
| query | code / script |
| run query / execute query | run code |
| result table | console output |
| query editor | code editor |
| query.sql | main.py |
| query history | execution log |
| database template | starter file |
| project database | sandbox |
| SQL error | traceback |

## Architecture Rules

1. **Student SQL must never run against the application database** (PostgreSQL).
2. Each project gets its own **isolated database instance** (SQLite file for MVP).
3. **Database templates** are read-only master databases owned by groups.
4. The backend executes SQL — **not the browser**.
5. File paths of database files are **never exposed** to the frontend or users.

## What NOT to Do

- ❌ Do not delete Python/Pyodide code until it is safely replaced (follow the phase plan).
- ❌ Do not remove licensing or attribution (see `.agent/rules/attribution-rules.md`).
- ❌ Do not add SQL engines beyond SQLite until Phase 7.
- ❌ Do not add exercises/lessons until Phase 8.
- ❌ Do not connect user queries to `DATABASES['default']`.
- ❌ Do not rewrite `codes/consumers.py` — it is the Y.js sync consumer, not Python execution.
- ❌ Do not rewrite `codes/tasks.py` — it is Y.js persistence, not Python execution.
