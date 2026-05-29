---
description: # Workflow: Implementation Review - Run this workflow **after completing code changes** to verify nothing is broken and all rules are followed.
---

# Workflow: Implementation Review

Run this workflow **after completing code changes** to verify nothing is broken and all rules are followed.

---

## Checklist

### 1. App Still Builds

- [ ] `npm install` completes without errors (from project root)
- [ ] Frontend starts: `npm run dev --prefix frontend/reactapp` (or via root `npm run dev`)
- [ ] No build errors or import errors in the browser console
- [ ] Backend starts: Docker containers are running (Django, PostgreSQL, Redis, Celery)

### 2. Frontend/Backend Still Start

- [ ] Frontend is accessible at `http://localhost:5173`
- [ ] Backend API responds at `http://localhost:8000`
- [ ] WebSocket connections succeed (check browser console for "WebSocket connected")
- [ ] Login works with test credentials

### 3. Attribution Preserved

- [ ] `README.md` still contains the Attribution section crediting PyTogether
- [ ] `NOTICE.md` still exists and credits PyTogether and Syed Jawad Rizvi
- [ ] `LICENSE` still contains `Copyright (c) 2025 Syed Jawad Rizvi`
- [ ] No branding changes suggest this is the official PyTogether project

### 4. SQL Safety Rules Followed

(Applicable if changes involve SQL execution, database access, or backend endpoints)

- [ ] Student SQL does NOT execute against the app database (PostgreSQL)
- [ ] Project databases are isolated (one per project)
- [ ] Query timeout is enforced
- [ ] Row limit is enforced
- [ ] `ATTACH DATABASE` and `LOAD_EXTENSION` are blocked
- [ ] Filesystem paths are not exposed in API responses or error messages
- [ ] Auth and membership are verified before query execution

### 5. Phase Scope Respected

- [ ] Changes are within the scope of the current phase (see `docs/SQLTOGETHER_PHASES.md`)
- [ ] No features from future phases were implemented
- [ ] No "while I'm here" changes were made outside the phase scope
- [ ] If scope was exceeded, it is documented and justified

### 6. No Unrelated Rewrites

- [ ] Only files relevant to the current phase were modified
- [ ] Collaboration features (Y.js, chat, voice, drawing) still work
- [ ] No unnecessary refactoring was performed
- [ ] No files were deleted without being replaced or confirmed obsolete

### 7. Tests/Checks Documented

- [ ] Changes are summarized in a clear list (files modified, added, deleted)
- [ ] Known issues or incomplete items are documented
- [ ] If automated tests exist, they pass
- [ ] Manual testing steps are documented for any features that can't be automated

---

## How to Use This Workflow

1. After making code changes, go through each checklist item.
2. Mark items as checked or note failures.
3. If any item fails, fix the issue before considering the change complete.
4. Report results to the user with:
   - Summary of changes made
   - Checklist results
   - Any issues found and how they were resolved
   - Recommended next steps
