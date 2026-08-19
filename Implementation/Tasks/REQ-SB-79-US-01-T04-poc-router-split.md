---
id: REQ-SB-79-US-01-T04
title: email_poc_router.py — replace the shared housekeeping-pass POC route with two per-pipeline routes
parent_story: REQ-SB-79-US-01
requirement_id: REQ-SB-79
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-79-US-01-T02]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-79-US-01-T04 — `email_poc_router.py` route split

## Parent Story

- Story: [[REQ-SB-79-US-01]] — `../UserStories/REQ-SB-79-US-01-librarian-two-sub-pipelines.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-79 *The Librarian — Two Sub-Pipelines*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Two Sub-Pipelines" § "`email_poc_router.py`"; `Implementation/Architecture/ADR.md` → `ADR-058` Decision 6

---

## Objective

Replace `/poc/librarian-run-housekeeping-pass` with `/poc/librarian-run-threads-cleaning-pass`/`/poc/librarian-run-company-partner-building-pass`, so each new pipeline stays independently, manually triggerable via its own real HTTP endpoint (standing project convention).

---

## Starting State → End State

**Before / Inputs:**
- `email_poc_router.py` line ~195: `@router.post("/librarian-run-housekeeping-pass")` → `librarian_run_housekeeping_pass_endpoint()` → `return run_housekeeping_pass()`.
- `T02` has replaced `run_housekeeping_pass()` with `run_threads_cleaning_pass()`/`run_company_partner_building_pass()`.

**After / Outputs:**
- The single old route/endpoint function is REPLACED by two:

  ```python
  @router.post("/librarian-run-threads-cleaning-pass")
  def librarian_run_threads_cleaning_pass_endpoint() -> dict:
      return run_threads_cleaning_pass()


  @router.post("/librarian-run-company-partner-building-pass")
  def librarian_run_company_partner_building_pass_endpoint() -> dict:
      return run_company_partner_building_pass()
  ```

- Every OTHER per-Job endpoint in this file (`/poc/librarian-rename-threads`, `-link-thread-messages`, `-backfill-files`, `-populate-related`, `-backfill-company-folders`, `-propose-customer-backfill`, `-propose-company-review`) is UNCHANGED — same function, same route.

---

## Files to Modify

- `src/backend/app/api/email_poc_router.py` — route replacement above; update the `from app.business.pipelines.librarian_housekeeping import (...)` import list to include the two new orchestrator names in place of the old one.

---

## Constraints

- Inherits from parent story.
- **Every per-Job endpoint stays byte-identical** — this task touches only the one orchestrating route.
- Mirrors the existing `/poc/librarian-*` naming convention exactly.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. Start the real backend. `POST /poc/librarian-run-housekeeping-pass` — confirm it now `404`s (route removed).
2. `POST /poc/librarian-run-threads-cleaning-pass` — confirm a real `200` and a result dict with exactly the 4 Threads Cleaning job keys.
3. `POST /poc/librarian-run-company-partner-building-pass` — confirm a real `200` and a result dict with `backfill_company_folders`/`retrofit_people_from_emails` keys.
4. Spot-check one unrelated existing route (`/poc/librarian-rename-threads`) still `200`s unchanged.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Old `/poc/librarian-run-housekeeping-pass` route removed
- [ ] Both new routes confirmed live, each delegating to the correct new orchestrator
- [ ] Every other per-Job POC endpoint confirmed unchanged
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `pending_approvals_router.py` — confirmed needing zero change (`ADR-058` Decision 7).
- The Skill/MCP-tool wrappers (a separate reachability surface) — `T03`.

---

## Context / Notes

None beyond the architecture reference above.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
