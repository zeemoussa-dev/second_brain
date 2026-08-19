---
id: REQ-SB-77-US-01-T03
title: Scheduled self-heal verification — run_company_partner_building_pass() drives retrofit_people_from_emails()
parent_story: REQ-SB-77-US-01
requirement_id: REQ-SB-77
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-77-US-01-T01, REQ-SB-79-US-01-T02]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-77-US-01-T03 — Scheduled self-heal verification (Scenario 6b)

## Parent Story

- Story: [[REQ-SB-77-US-01]] — `../UserStories/REQ-SB-77-US-01-people-notes-linked-to-company-partner-note.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-77 *People Notes Linked to Their Real Company/Partner Note*
- Architecture: `Implementation/Architecture/architecture.md` → "People Notes Retroactively Linked to Company/Partner" § "Two real trigger points (Scenario 6)", point 2; "The Librarian — Two Sub-Pipelines" § "Orchestrating capability split"

---

## Objective

Confirm, live, that `REQ-SB-79-US-01`'s own `run_company_partner_building_pass()` genuinely drives the already-existing `people_extraction.retrofit_people_from_emails()` on its own independent schedule — the self-healing catch-all half of Scenario 6. **Verification-only** — the literal one-line composition (`"retrofit_people_from_emails": people_extraction.retrofit_people_from_emails()`) is written as part of `REQ-SB-79-US-01-T02`'s own scope (`librarian_housekeeping.py`, in that story's own Files to Modify), per `ADR-058`/architecture.md — this task never duplicates that edit.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-79-US-01-T02` has landed: `librarian_housekeeping.run_company_partner_building_pass()` exists and, per its own architected body, calls both `backfill_company_folders()` and `people_extraction.retrofit_people_from_emails()`.
- `T01` has added `relink_people_for_thread_paths` (not directly exercised by this task, but the sibling mechanism `retrofit_people_from_emails` already provides the whole-vault self-heal — see Context).

**After / Outputs:**
- A real, direct call to `run_company_partner_building_pass()` is confirmed to (a) run `backfill_company_folders()`, and (b) genuinely relink at least one real Person note whose company only just became known — proving the composed self-heal fires as designed. No code change expected; if a genuine defect surfaces (e.g. the composition is missing, or a Person note is not actually relinked), fix it in scope, disclosed in the Implementation Log.

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` — no code change expected (verification-only); fix a genuine live-found defect here, in scope, if one surfaces.

---

## Constraints

- Inherits from parent story.
- **This task cannot start before `REQ-SB-79-US-01-T02` is `Done`** — `run_company_partner_building_pass()` does not exist before then. This is a real, disclosed cross-story dependency (see the parent story's own `## Notes`), not a soft sequencing preference.
- Never duplicate the composition itself into a second call site — if it is missing entirely (a genuine defect in `REQ-SB-79-US-01-T02`), report it explicitly rather than silently adding a second, divergent wiring path.
- Never bulk-approve or bulk-process any unrelated real Pending Approvals queue records as a side effect of this task's own verification.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-77-US-01-AC-06]` Confirm, by direct reading of `librarian_housekeeping.run_company_partner_building_pass()`'s own real, current source, that it calls `people_extraction.retrofit_people_from_emails()` (the composition `ADR-058`/architecture.md specify).
2. Set up a real precondition: at least one real Person note whose company is NOT yet a known Customer/Partner, plus that same company becoming known (via a real or disposable-test Customer/Partner confirmation).
3. Call `run_company_partner_building_pass()` directly (or via its own real `/poc/librarian-run-company-partner-building-pass` endpoint, once `REQ-SB-79-US-01-T04` lands). Confirm the targeted Person note gains its real wikilink as a direct result of this one call — proving the scheduled/on-demand self-heal half of Scenario 6 genuinely fires, independent of the instant hook (`T02`).
4. Confirm `backfill_company_folders()`'s own real result is still present in the returned dict, unaffected by the added `retrofit_people_from_emails` call.
5. Record the real outcome (function existed as expected / defect found and fixed) explicitly in the Implementation Log.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `[REQ-SB-77-US-01-AC-06]` Scheduled self-heal half verified live — a real `run_company_partner_building_pass()` call relinks at least one real Person note whose company just became known
- [ ] `backfill_company_folders()`'s own result is unaffected by the composition
- [ ] Any genuine defect found is disclosed and fixed in scope, not silently routed around
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Writing the `run_company_partner_building_pass()`/`retrofit_people_from_emails` composition itself — `REQ-SB-79-US-01-T02`'s own scope.
- The instant hook — `T02`.
- Any change to the actual 6-hour default schedule interval or its own operator-adjustability — `REQ-SB-79-US-01`'s own scope.

---

## Context / Notes

**Why this task exists as verification-only, not a code task:** the literal composition line lives inside `run_company_partner_building_pass()`'s own function body, which `REQ-SB-79-US-01-T02` writes as part of its own `librarian_housekeeping.py` edit (per `ADR-058` Decision 3 / architecture.md's own "Orchestrating capability split" code block, already specifying the exact `retrofit_people_from_emails()` call). Duplicating that edit here would create two divergent authors for the same line. This task's own job is closing the loop: independently confirming, live, that the composition landed correctly and genuinely produces Scenario 6's own self-healing outcome — the same "independently confirm a new mechanism is correct via a controlled case" discipline this project's own `Implementation/Learnings.md` (`SPRINT-028`) already establishes.

**Real cross-story dependency:** this task's own `depends_on` names `REQ-SB-79-US-01-T02` directly (a task ID, not a story ID) — see the parent story's own `## Notes` ("Decomposer pass") for the full reasoning on why this is recorded as a task-level edge now rather than deferred to `depends_on_sprints`.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
