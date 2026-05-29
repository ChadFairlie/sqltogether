# SQLTogether Codex Instructions

You are working on SQLTogether.

SQLTogether is an independent adaptation of PyTogether into a collaborative SQL teaching and learning environment.

## Required Context

Before doing project work, read:

- docs/AGENT_HANDOFF_GUIDE.md
- docs/SQLTOGETHER_PHASES.md
- docs/SQLTOGETHER_PRODUCT_PLAN.md
- docs/SQLTOGETHER_ARCHITECTURE.md
- docs/SQL_SANDBOX_STRATEGY.md

Also follow these Antigravity-compatible rules:

- .agents/rules/sqltogether-project-rules.md
- .agents/rules/sql-safety-rules.md
- .agents/rules/attribution-rules.md

## Workflow Files

When I mention a phase or workflow, read the matching file in:

- .agents/workflows/

Examples:

- Phase planning: .agents/workflows/phase-planning.md
- Implementation review: .agents/workflows/implementation-review.md
- Python execution audit: .agents/workflows/execution-audit.md
- SQLite MVP planning: .agents/workflows/sql-mvp-planning.md

## Project Rules

- Work in phases.
- Do not perform massive rewrites.
- Preserve existing authentication, groups, projects, collaboration, autosave, and editor functionality where possible.
- Preserve PyTogether attribution in README, NOTICE, and LICENSE.
- Do not remove original MIT license notices.
- Do not present SQLTogether as the official PyTogether project.
- Student SQL must never run against the SQLTogether application database.
- SQL execution must use isolated project databases.
- Start with SQLite for the MVP unless explicitly told otherwise.

## Operating Mode

Before implementing a phase:

1. Read the relevant docs and workflow files.
2. Summarize the intended changes.
3. List affected files.
4. List risks.
5. Wait for confirmation if the task is planning-only.

After implementing:

1. Summarize changes.
2. List files changed.
3. List checks run.
4. List remaining risks.