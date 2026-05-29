---
description: # Workflow: Phase Planning - Use this workflow **before implementing any phase** of SQLTogether development.
---

# Workflow: Phase Planning

Use this workflow **before implementing any phase** of SQLTogether development.

---

## Prerequisites

- [ ] You have read `docs/AGENT_HANDOFF_GUIDE.md`
- [ ] You have read `docs/SQLTOGETHER_PHASES.md` to identify which phase you are working on
- [ ] The previous phase is complete and verified

---

## Step 1: Read All Planning Docs

Before doing anything, read these files:

1. `docs/SQLTOGETHER_PRODUCT_PLAN.md` — Understand the product vision and MVP scope
2. `docs/SQLTOGETHER_ARCHITECTURE.md` — Understand the system design and domain models
3. `docs/SQLTOGETHER_PHASES.md` — Read the specific phase you are implementing
4. `docs/SQL_SANDBOX_STRATEGY.md` — Understand safety requirements (especially for Phases 4+)
5. `docs/PYTHON_TO_SQL_CONVERSION_GUIDE.md` — Understand which files are Python-specific vs generic
6. `.agent/rules/sqltogether-project-rules.md` — Development rules
7. `.agent/rules/sql-safety-rules.md` — SQL safety rules
8. `.agent/rules/attribution-rules.md` — Attribution requirements

---

## Step 2: Identify Affected Files

For the phase you are implementing, create a list of:

| Category | Files |
|----------|-------|
| Files to **modify** | (list each file and what will change) |
| Files to **create** | (list each new file and its purpose) |
| Files to **delete** | (list each file and confirm it's safe to remove) |
| Files to **keep unchanged** | (list files that look related but should NOT be touched) |

Verify each file exists in the repository before listing it.

---

## Step 3: Produce Implementation Plan

Write a brief implementation plan that includes:

1. **Phase number and name**
2. **Goal** (one sentence)
3. **Ordered list of changes** (in the order they should be made)
4. **Dependencies** (what must exist before each change)
5. **Testing approach** (how you will verify each change works)

---

## Step 4: List Risks

Identify potential risks:

- What could break?
- What collaboration features might be affected?
- What edge cases exist?
- Are there any safety implications?
- Are there attribution concerns?

---

## Step 5: List Validation Steps

Define how you will validate success:

- [ ] App builds without errors
- [ ] Frontend starts on localhost:5173
- [ ] Backend starts on localhost:8000
- [ ] Core features still work (login, groups, projects, editor, collaboration)
- [ ] Phase-specific features work (per the Definition of Done in SQLTOGETHER_PHASES.md)
- [ ] Attribution preserved
- [ ] SQL safety rules followed (if applicable)
- [ ] No files outside the phase scope were modified

---

## Step 6: Wait Before Coding

**Do NOT start coding until you have completed Steps 1–5.**

If you are an AI agent and the user has not explicitly told you to implement:
- Present your implementation plan
- Wait for approval
- Only then proceed to implementation

If the user has explicitly told you to implement:
- Complete Steps 1–5 as internal checks
- Proceed to implementation
- Report your implementation plan as you go

---

## Output

After completing this workflow, you should have:

1. A clear understanding of what the phase requires
2. A list of affected files
3. An ordered implementation plan
4. Identified risks
5. Validation steps
6. Approval to proceed (or a plan to present for approval)
