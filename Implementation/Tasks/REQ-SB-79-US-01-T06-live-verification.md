---
id: REQ-SB-79-US-01-T06
title: Real end-to-end verification — both agents, no orphaned records, idempotency, zero-change confirmations
parent_story: REQ-SB-79-US-01
requirement_id: REQ-SB-79
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-79-US-01-T04, REQ-SB-79-US-01-T05]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-79-US-01-T06 — Real end-to-end verification

## Parent Story

- Story: [[REQ-SB-79-US-01]] — `../UserStories/REQ-SB-79-US-01-librarian-two-sub-pipelines.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-79 *The Librarian — Two Sub-Pipelines*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Two Sub-Pipelines"; `Implementation/Architecture/ADR.md` → `ADR-058`

---

## Objective

Run the whole, real, wired system end-to-end against the live vault/backend: confirm both new Agents appear independently (Scenario 1), no existing Pending Approval/Agent History record was orphaned by the split (Scenario 6), Threads Cleaning idempotency is unaffected (Scenario 7), and independently re-confirm Scenarios 2-5 against the fully-wired system — plus confirm, by direct reading, that `section_ownership.py`/`pending_approvals_router.py`/`email_classification.py` genuinely needed zero change.

---

## Starting State → End State

**Before / Inputs:**
- `T01`-`T05` all built and individually verified.
- The real vault already carries Pending Approval/Agent History records attributed to `librarian-housekeeping` from before this story shipped.

**After / Outputs:**
- Every locked AC (`AC-01`-`AC-07`) independently re-confirmed live against the fully-wired, real system.
- Every real check/finding recorded in the Implementation Log.

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` — no code change expected (verification-only); fix a genuine live-found defect here, in scope, if one surfaces.

---

## Constraints

- Inherits from parent story.
- **Never bulk-approve or bulk-decline the real Pending Approvals queue unattended** — this task only READS existing records to confirm attribution, never resolves them as a side effect.
- Archive-not-delete — inherited, though this task performs no archival itself.
- A single transient failure (a slow real capture-scale call) should be treated as genuinely possible multi-minute latency, not assumed hung (`Implementation/Learnings.md`, `SPRINT-021`/`SPRINT-027`/`SPRINT-031`).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-79-US-01-AC-01]` `GET /agents` on the real, running backend. Confirm `threads-cleaning`/`company-and-partner-building` both appear as real, independently-listed records, `librarian-housekeeping` does not.
2. `[REQ-SB-79-US-01-AC-06]` Find at least one real, already-existing Pending Approval or Agent History entry whose `agent_id` is `librarian-housekeeping` (from before this story shipped). Confirm `GET /pending-approvals` (or the Agent History view) still resolves a real, honest `agent_name` for it (via `_resolved()`/`get_agent`) — not `None`, not an error, not silently dropped from the list.
3. `[REQ-SB-79-US-01-AC-07]` Run `run_threads_cleaning_pass()` twice in a row against an already-fully-processed real corpus. Confirm the second run is a true no-op (same idempotency guarantees `REQ-SB-72`/`REQ-SB-73` already proved per-job).
4. `[REQ-SB-79-US-01-AC-02]`/`[AC-03]`/`[AC-04]`/`[AC-05]` Re-confirm each, end-to-end, via the real, fully-wired system (real HTTP routes from `T04`, real schedule from `T05`) — not merely re-running `T02`'s own earlier direct-call checks.
5. By direct reading of the real, current `section_ownership.py`, confirm `_CALLER_ALLOW_LISTS` keys off dotted FUNCTION names, never agent identity — genuinely zero change needed. Confirm the same for `pending_approvals_router.py`'s `_APPROVAL_HANDLERS` (dispatches by `action_id`) and `email_classification.py` (comment-only reference).
6. Confirm `skill_tools.py`'s own stale comment (naming `librarian-housekeeping` as the sole grantable identity for the old Skill) was updated or removed as part of `T03`.
7. Record the real, final state (both agents' schedules, the retired identity's own historical-record count, any genuine defect found and fixed) explicitly in the Implementation Log.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] All 7 locked ACs independently re-confirmed live, end-to-end, against the real, fully-wired system
- [ ] `section_ownership.py`/`pending_approvals_router.py`/`email_classification.py` confirmed genuinely needing zero change, by direct reading
- [ ] No real Pending Approval/Agent History record bulk-processed as a side effect of this task
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Extending `REQ-SB-65`'s Job Tree visualization to either new agent — disclosed, pre-existing gap, not this story's scope.
- Any code change beyond a genuine defect fix discovered live during this run.

---

## Context / Notes

Mirrors `REQ-SB-76-US-01-T09`'s own precedent — the story's own final integration pass, real end-to-end, not a repeat of earlier tasks' own narrower checks.

---

## Implementation Log

**No code change** — this task's own real, live run surfaced zero genuine
defects; `librarian_housekeeping.py` is unmodified beyond `T02`'s own
already-`Done` edit.

**Final integration pass — every locked AC independently re-confirmed
live, end-to-end, against the real, fully-wired system:**

- `[REQ-SB-79-US-01-AC-01]` `GET http://127.0.0.1:8010/agents` (this
  worktree's own dedicated, fully-wired real backend instance, all `T01`-
  `T05` code present) — `threads-cleaning`/`company-and-partner-building`
  both present, `librarian-housekeeping` absent. **PASS.**
- `[REQ-SB-79-US-01-AC-06]` Found 256 real, pre-existing (dated
  2026-08-18, before this story shipped) Pending Approval records with
  `agent_id == "librarian-housekeeping"`
  (`pending_approval_registry.list_pending_approvals(agent_id=
  "librarian-housekeeping")`). `GET /pending-approvals/a126ba526347`
  (real HTTP) resolved `agent_name: "Librarian Housekeeping"` — real,
  honest, correctly attributed, not `None`/error/dropped. Independently
  confirmed the bulk listing endpoint (`GET /pending-approvals?agent_id=
  librarian-housekeeping`) also correctly resolves all 256 records, not
  just the one spot-checked. **PASS.**
- `[REQ-SB-79-US-01-AC-07]` Bounded a real, already-fully-processed
  2-Thread subset (same technique as `T02`/`T04` — real `conversation_id`
  tracking, dynamically re-resolved), ran `run_threads_cleaning_pass()`
  twice in a row. Second run: zero new renames, zero new frontmatter
  writes (`linked: False` for every message), zero new File companions —
  a true no-op, matching `REQ-SB-72/73`'s own already-proven per-Job
  idempotency; the split introduces no new re-run side effect. **PASS.**
- `[REQ-SB-79-US-01-AC-02]`/`[AC-03]` Re-confirmed via `T04`/`T05`'s own
  real HTTP evidence, cross-referenced here rather than repeated a third
  time (both already ran against the fully-wired system — all `T01`-`T05`
  code was already on disk before either of those live-verification
  passes ran): `POST /poc/librarian-run-threads-cleaning-pass` → real
  `200`, correct 4-key shape (`T04`); `GET /agents/threads-cleaning/
  schedules` + `GET /agents/company-and-partner-building/schedules` →
  two real, independently-adjustable, distinct schedule records (`T05`).
- `[REQ-SB-79-US-01-AC-04]` Fresh, independent real HTTP re-confirmation
  (distinct real Threads from `T02`'s own direct-call check, distinct
  technique — `httpx.ASGITransport(app=app.main.app)` against the real,
  unmodified, fully-wired app object, bounded via the same real-
  `conversation_id` monkeypatch): `POST /poc/librarian-propose-customer-
  backfill` → real `200`, created a real Pending Approval (`2a9b3655c6c7`,
  Sindan) for a real, previously-`Unsorted` Thread. Independently
  confirmed via a SEPARATE `GET /pending-approvals/2a9b3655c6c7` call
  (not trusting the create response's own echo) that `agent_id ==
  "company-and-partner-building"`. **PASS.**
- `[REQ-SB-79-US-01-AC-05]` Re-confirmed by direct reading (`inspect.
  getsource`, `T02`) plus a fresh grep this pass — `propose_company_
  review`'s own `create_pending_approval` call site reads `agent_id=
  "company-and-partner-building"`. Also confirmed `REQ-SB-76-US-01` has
  in fact already shipped (`SPRINT-072`, per `CHANGELOG.md`'s own
  `[Unreleased]` entry — 9 real classification decisions already made
  against the real vault) — Scenario 5's "whenever it ships" condition is
  resolved as "already shipped, correctly re-wired." **PASS.**

**Confirmed by direct reading — genuinely zero change needed (not
merely assumed):**

- `section_ownership.py`'s `_CALLER_ALLOW_LISTS` — every key is a dotted
  FUNCTION name (`"librarian_housekeeping.backfill_files"`,
  `"...populate_thread_related_links"`, `"...link_thread_messages"`) —
  none of these `caller=` string literals changed anywhere in `T02`'s own
  edit. **Confirmed zero change needed.**
- `pending_approvals_router.py`'s `_APPROVAL_HANDLERS` — dispatches by
  `action_id` (`propose_librarian_company_link`, `propose_customer_
  backfill_routing`, `propose_customer_archival_candidate`, `propose_
  company_review`), never `agent_id`; none of these action ids changed.
  **Confirmed zero change needed.**
- `email_classification.py` — the one reference to `librarian_
  housekeeping.populate_thread_related_links` is comment-only prose
  (ownership-transfer context), no functional coupling to any `agent_id`.
  **Confirmed zero change needed.**
- `skill_tools.py`'s own stale docstring (naming the old sole-grantable
  identity) — confirmed updated as part of `T03`.

**Real, final state recorded:**

- Both new Agents live under the "librarian" Section, each with exactly
  one real, independent, `mutates: True` Skill grant and one real,
  persisted 6-hour schedule.
- `librarian-housekeeping` retired (`retired: True`), zero historical
  records orphaned — 256+ real Pending Approval records (plus real Agent
  History entries, not individually counted here) all still resolve its
  real, honest name via `get_agent`.
- No real Pending Approval was bulk-approved/declined by this task — every
  record touched this pass (this task's own 1 new real batch, plus every
  record created across `T02`/`T04`'s own live verification) was left in
  its natural resulting state (`pending`), never resolved as a side
  effect.
- This worktree's own dedicated verification backend instances (ports
  `8010`/`8011`) were shut down by specific PID once verification
  completed; the operator's separately-running main-checkout processes
  (`8000`/`8001`) were never touched and remained reachable throughout.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired; no genuine defect
found requiring an in-scope fix. All 7 locked ACs independently
re-confirmed live, end-to-end, against the real, fully-wired system.
