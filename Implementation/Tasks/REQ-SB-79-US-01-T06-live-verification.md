---
id: REQ-SB-79-US-01-T06
title: Real end-to-end verification — both agents, no orphaned records, idempotency, zero-change confirmations
parent_story: REQ-SB-79-US-01
requirement_id: REQ-SB-79
type: backend
status: Ready
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

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
