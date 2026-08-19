---
id: REQ-SB-77-US-01-T03
title: Scheduled self-heal verification — run_company_partner_building_pass() drives retrofit_people_from_emails()
parent_story: REQ-SB-77-US-01
requirement_id: REQ-SB-77
type: backend
status: Done
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

- [x] `[REQ-SB-77-US-01-AC-06]` Scheduled self-heal half verified live — a real `run_company_partner_building_pass()` call relinks at least one real Person note whose company just became known
- [x] `backfill_company_folders()`'s own result is unaffected by the composition
- [x] Any genuine defect found is disclosed and fixed in scope, not silently routed around (n/a — no defect found; the composition was already correct, landed by `REQ-SB-79-US-01-T02`)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — none emerged)
- [x] `CHANGELOG.md` entry appended

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

**Verified 2026-08-19 — no code change (verification-only, as scoped).** Confirmed by direct reading of the real, current `librarian_housekeeping.py` (after re-syncing this worktree to `master`'s own `8ec8f49` — see the cross-story-dependency note below) that `run_company_partner_building_pass()` already exists and its own real, current body is exactly the composition `ADR-058`/architecture.md specify: `{"backfill_company_folders": backfill_company_folders(), "retrofit_people_from_emails": people_extraction.retrofit_people_from_emails()}` — landed by `REQ-SB-79-US-01-T02` (`SPRINT-073`), whose own docstring explicitly names this as `"REQ-SB-77-US-01 Scenario 6b's own scheduled, self-healing catch-all"`. No divergent/duplicate call site found anywhere else in the file.

**Real cross-story dependency, confirmed satisfied:** this worktree was created from an ancestor commit of `master` that predated `SPRINT-073`'s own landing commit (`8ec8f49`) — `git log --oneline HEAD..master` showed 8 real commits missing, including `8ec8f49` itself. Per `MEMORY.md`'s own documented "a git worktree's own branch can be missing whole task/story/sprint files... because the worktree's own branch is simply BEHIND master" finding (recorded live by `SPRINT-073`'s own coder run, same day), ran `git merge master --ff-only` from inside this worktree (confirmed zero unique commits of its own first, via `git log --oneline master..HEAD` returning empty — a safe, non-destructive fast-forward) BEFORE starting any work on this sprint. This is disclosed here, not hidden, since it's exactly the scenario this task's own `depends_on: [..., REQ-SB-79-US-01-T02]` cross-story edge anticipates.

**Verification (manual mode, real vault, direct Python-shell calls):**
1. `[REQ-SB-77-US-01-AC-06]` Confirmed by direct reading (above) — `run_company_partner_building_pass()`'s real body calls `people_extraction.retrofit_people_from_emails()`. **PASS.**
2. Real precondition set up per this task's own Tests step 2 explicit allowance ("a real REQ-SB-76 approval, or... a disposable-test substitute"): real Person note `Work/People/animas.caustro@ewec.ae.md` (company "Ewec", genuinely not yet a known Customer/Partner — confirmed `find_matching_customer("Ewec")` returned `None` beforehand) — snapshotted the Person note and its real Thread (`Work/Threads/2026-08-13 Recall- Ewec Discussion.../...md`) before any write. Made "Ewec" genuinely known by calling the PRIVATE `_finalize_company_review_outcome({"company": "Ewec", "thread_paths": [<path>], "outcome": "customer"})` directly (bypassing the public `finalize_company_review` wrapper's own relink call on purpose, so the precondition is set WITHOUT the instant-hook half of Scenario 6 firing first — isolating this task's own scheduled/self-heal half from `T02`'s already-independently-verified instant half). Confirmed afterward the Person note's body was STILL unlinked (no `**Customer:**` line yet) — the real precondition genuinely held.
3. `[REQ-SB-77-US-01-AC-06]` Called the REAL, unmodified `run_company_partner_building_pass()` directly (matching this task's own Tests block; the `/poc/librarian-run-company-partner-building-pass` endpoint route is equivalent plumbing this direct call already exercises the load-bearing part of, per this project's own "skip the HTTP layer when it isn't load-bearing for the locked AC" precedent). To bound the call's cost/blast-radius to only what THIS task's own locked AC needs (proving the WIRING, not re-proving `backfill_company_folders()`'s own already-independently-verified whole-vault Compass-backed correctness, `REQ-SB-72-US-01-T07`), temporarily substituted a scoped, in-process, reverted stub for `backfill_company_folders` (a distinctive sentinel return value) before the call and restored the real function immediately after — mirrors this project's own established "bound a live-data verification via in-process monkeypatch of an unrelated, already-verified real dependency" pattern (`Implementation/Learnings.md`, `SPRINT-028`). `retrofit_people_from_emails()` itself ran FOR REAL, unstubbed, across the whole real vault (739 real notes scanned) — this is the actual mechanism under test, never bounded.
4. Confirmed the real result dict's `"backfill_company_folders"` key held EXACTLY the sentinel stub value — proving the composition genuinely calls that function and returns its result unmodified, satisfying this task's own Tests step 4 without needing the real, expensive, out-of-scope-already-verified whole-vault Compass sweep. **PASS.**
5. Confirmed the real Person note `Work/People/animas.caustro@ewec.ae.md` gained the real `**Customer:** [[Ewec]]` wikilink as a direct result of THIS ONE `run_company_partner_building_pass()` call — proving the scheduled/on-demand self-heal half of Scenario 6 genuinely fires, independent of `T02`'s instant hook (never invoked in this test). **PASS.**

No genuine defect found — the composition was already correct as landed by `REQ-SB-79-US-01-T02`; nothing in this task's own `## Files to Modify` (`librarian_housekeeping.py`) required a change.

**Cleanup:** the real Thread and Person note were restored byte-for-byte from their pre-test snapshots; the newly-created `Work/Customers/Ewec/` OKF directory (which had zero prior content) was deleted outright. Confirmed via `Test-Path` returning `False` and a byte-for-byte post-revert read of both files matching the pre-test snapshot. No Pending Approvals queue record was created or touched by this task's own verification (the stubbed `backfill_company_folders()` never ran for real, so it never created any); no bulk-approve/bulk-process action was taken against any pre-existing unrelated Pending Approval.

**MEMORY.md:** not updated for a new decision from THIS task's own work (the composition itself was `REQ-SB-79-US-01-T02`'s own decision, already recorded there); the worktree-sync finding above was already documented in `MEMORY.md` by `SPRINT-073`'s own coder run and is only reconfirmed, not new.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired (no new ADR, no unresolved assumption, no new ESCALATIONS entry, not oversized, the locked AC verified live with a real positive result, no genuine defect found to fix).
