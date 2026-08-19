---
id: REQ-SB-47-US-01-T01
title: invoke_skill — new "scheduled" trigger literal + Manual-mode silent-skip branch
parent_story: REQ-SB-47-US-01
requirement_id: REQ-SB-47
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-47-US-01-T01 — invoke_skill "scheduled" trigger + Manual-mode skip branch

## Parent Story

- Story: [[REQ-SB-47-US-01]] — `../UserStories/REQ-SB-47-US-01-per-agent-scheduler-and-shared-serialization.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-47 *Per-Agent Scheduler* (merges REQ-SB-45)

---

## Objective

Extend `skill_registry.invoke_skill`'s `trigger` parameter to accept a new
`"scheduled"` literal for fully-automatic ticks with no user in the loop, and
add the one new Manual-mode gate branch that skips a `"scheduled"` dispatch
silently — no history entry — mirroring the existing background-tick
"Manual stays dormant" precedent, per `ADR-037` point 5.

---

## Starting State → End State

**Before / Inputs:**
- `src/backend/app/business/skill_registry.py::invoke_skill(agent_id, skill_id, args, trigger: Literal["chat", "direct", "hub_routed"])` — the ONE gated dispatch path every real caller passes through (`ADR-029` point 1). Its Manual-mode branch today only special-cases `mode == "manual" and trigger == "hub_routed"`.
- No `"scheduled"` trigger value exists anywhere in this function today.

**After / Outputs:**
- `invoke_skill`'s `trigger` parameter type is `Literal["chat", "direct", "hub_routed", "scheduled"]`.
- A new branch, inserted alongside the existing `mode == "manual" and trigger == "hub_routed"` refusal: `mode == "manual" and trigger == "scheduled"` → returns `{"status": "skipped_manual", "reason": "This agent is in Manual mode — its scheduled runs stay dormant."}`, writing **zero** `vault_writer.append_agent_history_entry` calls for this branch.
- Every other mode/trigger combination is unchanged — in particular, Supervised + `mutates is True` + `trigger == "scheduled"` falls into the existing pending-approval branch unmodified (same decision table, one more `trigger` value), and `trigger == "direct"` (the existing literal "run now" will keep reusing) is completely untouched by this task.

---

## Files to Modify

- `src/backend/app/business/skill_registry.py` — `invoke_skill`'s signature (`trigger` type) and its Manual-mode gate body only. No other function in this file changes.

---

## Constraints

- Inherits from parent story.
- Do not touch the Supervised-mode branch, the access check, or `_dispatch_skill` — this task is scoped to exactly one new `Literal` value and one new `if` branch.
- The new `"skipped_manual"` branch must record **zero** history entries — this is what lets `agent_schedule_registry.dispatch_with_shared_lock` (`T02`) distinguish it from every other outcome, all of which ARE recorded.
- `skill_tools.py`, `agent_registry.py`, and every other file in this module are out of scope — unchanged.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-47-US-01-AC-08] In a Python shell (`src/backend`), pick a known agent and set it to Manual mode via `working_mode_registry.set_agent_working_mode(agent_id, "manual")`. Call `skill_registry.invoke_skill(agent_id, "<a granted mutating skill_id>", None, trigger="scheduled")` — expect `{"status": "skipped_manual", ...}`. Immediately call `vault_writer.load_agent_history(agent_id)` and confirm its length is unchanged from before the call (no new entry appended). Then call `skill_registry.invoke_skill(agent_id, "<same skill_id>", None, trigger="direct")` — expect the SAME outcome `trigger="direct"` already produces today for this agent/skill (a real dispatch result or the honest "not available" stub) — i.e. the run executes/attempts to execute, unaffected by Manual mode. Restore the agent's prior working mode afterward.
2. [REQ-SB-47-US-01-AC-08, regression] Repeat step 1's first call (`trigger="scheduled"`) for the same agent set to Autonomous mode instead — expect the call to fall through to the SAME dispatch outcome `trigger="direct"` already produces for Autonomous mode (unaffected — the new branch only fires for Manual). Repeat once more for Supervised mode with a `"mutates": True` skill — expect the existing `{"status": "pending", ...}` pending-approval outcome, identical in shape to what `trigger="direct"` already produces under Supervised, confirming the decision table gained one more `trigger` value, not new behavior for the other two modes.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `invoke_skill` accepts `trigger="scheduled"` without raising.
- [ ] Manual mode + `trigger="scheduled"` → `{"status": "skipped_manual", ...}`, zero history entries written.
- [ ] Manual mode + `trigger="direct"` is unaffected — still executes/attempts exactly as before this task.
- [ ] Autonomous/Supervised modes + `trigger="scheduled"` fall through to the same outcome `trigger="direct"` already produces for those modes.
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint.
- [ ] `CHANGELOG.md` entry appended.

---

## Out of Scope

- The shared dispatch lock and `dispatch_with_shared_lock` (`T02`).
- Registering any real scheduled job (`T03`).
- Any HTTP-layer endpoint (`T04`/`T05`).
- Any frontend change (`T06`).

---

## Context / Notes

Real file to compose against: `src/backend/app/business/skill_registry.py` — re-read it fresh before editing (`Implementation/Learnings.md`'s own "compose around the REAL current file" pattern, reconfirmed across `SPRINT-019/020/021/027`). Full architectural reasoning: `ADR-037` point 5, `Implementation/Architecture/architecture.md` → "Per-Agent Scheduler & Shared Outlook-COM Dispatch Lock."

This task is the first in this story's dependency chain — `T02`'s `dispatch_with_shared_lock` calls `invoke_skill` with a `trigger` value that includes `"scheduled"`, and needs this task's Manual-mode branch to exist for `AC-08`'s dormant-Manual guarantee to hold for real, not just for the literal type-hint to be technically satisfied.

---

## Implementation Log

**Change:** `src/backend/app/business/skill_registry.py::invoke_skill` — `trigger`
type extended to `Literal["chat", "direct", "hub_routed", "scheduled"]`; one new
branch inserted immediately after the existing `mode == "manual" and trigger ==
"hub_routed"` branch: `mode == "manual" and trigger == "scheduled"` →
`{"status": "skipped_manual", "reason": "This agent is in Manual mode — its
scheduled runs stay dormant."}`, no `vault_writer.append_agent_history_entry`
call. No other line in the file changed.

**Assumption (scope-internal, logged per Pipeline.md):** the task's own Test
step 1 names `email-capture`'s `run_capture_now` as the example skill; I
substituted `meeting-capture`'s `run_capture_now` (also real, granted,
`mutates: True`, migration-seeded) for the live verification below to avoid
triggering a real, multi-minute Outlook-COM capture run for a check that does
not need one — `meeting-capture`'s on-demand path is the existing honest
"not available" stub (per the story's own disclosed known limitation), which
still fully exercises the gate branch under test. `email-capture`'s real
dispatch path is separately, genuinely exercised live in `T02`/`T03`/`T05`.

**Verification (2026-08-14, `src/backend`, `.venv/Scripts/python.exe`, real
in-process calls against the real `.second-brain/` state):**

- `[AC-08]` Set `meeting-capture` to Manual. `invoke_skill(..., trigger="scheduled")`
  → `{'status': 'skipped_manual', ...}`. `vault_writer.load_agent_history
  ("meeting-capture")` length unchanged (64 → 64) — confirmed zero history entry
  written. **PASS.**
- `[AC-08]` Same agent still Manual, `invoke_skill(..., trigger="direct")` →
  `{'available': False, 'message': 'This skill is not yet available...'}` — the
  same honest stub outcome `trigger="direct"` already produced before this
  task, confirming Manual mode does not affect `"direct"`. **PASS.**
- `[AC-08, regression]` Autonomous mode: `trigger="scheduled"` and
  `trigger="direct"` returned byte-identical results (both the honest stub) —
  confirmed falls through unaffected. **PASS.**
- `[AC-08, regression]` Supervised mode: both `trigger="scheduled"` and
  `trigger="direct"` returned `{'status': 'pending', ...}` (a real pending
  approval created each time, ids `4e5ef1403765`/`424ad11f9f8f`) — identical
  decision-table shape, one more `trigger` value, confirmed. **PASS.**

`meeting-capture`'s working mode was captured, mutated for the test, and
restored to its true pre-test value (`autonomous`, confirmed via a final
`get_agent_working_mode` read) after the run — no lasting state change to the
real vault beyond the two Supervised-mode pending-approval records the test
itself intentionally created (a real, honest byproduct of the gate under
test, left in place per this project's own precedent of not silently
reverting real state the check itself produced).

gate: clear 2026-08-14 — no triggers fired (no ADR change, no new
assumption beyond the scope-internal one logged above, requirement finalised,
all 4 tagged manual steps verified live and passing).
