---
id: REQ-SB-79-US-01-T04
title: email_poc_router.py — replace the shared housekeeping-pass POC route with two per-pipeline routes
parent_story: REQ-SB-79-US-01
requirement_id: REQ-SB-79
type: backend
status: Done
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

**Change:** `src/backend/app/api/email_poc_router.py` — import list updated
to the two new orchestrator names; `/poc/librarian-run-housekeeping-pass`
replaced by `/poc/librarian-run-threads-cleaning-pass`/`/poc/librarian-run-
company-partner-building-pass`, each a 2-line delegate to the matching
`T02` orchestrator. Every other per-Job route untouched (zero lines
changed for any of them).

**Note:** this task's own `## Acceptance Criteria` are task-level only —
the story's own AC-coverage table (`REQ-SB-79-US-01` `## Notes`) does not
assign this task any locked `[REQ-SB-79-US-01-AC-NN]` ID; its own Tests
block carries none either. Verified anyway, per the standing "perform the
Tests block" duty.

**Sequencing note:** this task's own Tests block requires "start the real
backend" — `main.py` still imported the pre-`T05` names at the time `T02`/
`T03`/`T04` landed, so the FULL app could not boot until `T05` also landed
(a real, structural fact confirmed by attempting `import app.main`, which
raised `ImportError` on the still-old `email_poc_router.py` import list
before this task's own edit, and would have raised on `main.py`'s own
still-old imports even after this task alone). Built `T04`'s code
immediately after `T02` per the dependency graph, then built `T05`
immediately after, then ran BOTH tasks' own live HTTP verification
together against one real, fully-wired backend — reported here and cross-
referenced from `T05`'s own Implementation Log.

**Live verification (real HTTP, this worktree's own dedicated backend
instances — never the operator's separately-running main-checkout
processes on 8000/8001):**

- Old route removed: `POST http://127.0.0.1:8010/poc/librarian-run-
  housekeeping-pass` → real `404`. **PASS.**
- Unrelated existing per-Job route unchanged: `POST .../poc/librarian-
  rename-threads` → real `200`, real result dict (141 real Threads
  processed, `skipped_already_renamed`/5 genuine pre-existing filename
  collisions — unrelated, pre-existing, disclosed condition, not
  introduced by this task). **PASS.**
- New routes confirmed live and correctly delegating: rather than paying
  a ~2-hour full-141-Thread real-Compass-sweep cost twice over HTTP purely
  to re-prove plumbing already function-level-proven in `T02`'s own
  bounded live verification, launched a SEPARATE, temporary, bounded-scope
  real server (port `8011` — monkeypatches `vault_writer.list_thread_
  notes` to 2 real, dynamically-tracked Threads BEFORE importing `app.main`,
  so the real, unmodified route/orchestrator code runs genuinely over a
  real HTTP request/response cycle, just bounded in Thread count).
  `POST .../poc/librarian-run-threads-cleaning-pass` → real `200`, dict
  keys exactly `{rename_threads, link_thread_messages, backfill_files,
  populate_thread_related_links}`. `POST .../poc/librarian-run-company-
  partner-building-pass` → real `200`, dict keys exactly `{backfill_
  company_folders, retrofit_people_from_emails}`. Both **PASS**. The
  bounded server (port `8011`, PIDs `39664`/`29200`) was shut down by
  specific PID immediately after.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired. Bounded-server
verification methodology disclosed for human spot-check (same reasoning
as `T02`/`T03`).
