---
id: REQ-SB-47-US-01-T02
title: New agent_schedule_registry.py — persisted schedule CRUD + shared dispatch lock + live-scheduler seam
parent_story: REQ-SB-47-US-01
requirement_id: REQ-SB-47
type: backend
status: Done
gate: flagged
gate_reason: "scope-internal judgement call — a real, live-discovered duplicate-history-entry defect in this task's own dispatch_with_shared_lock (see Implementation Log) was fixed in-scope with a more robust, generic length-based detection than ADR-037's own illustrative text described; logged for human spot-check per Pipeline.md's scope-internal-judgement-call provision, not an escalation (no new dependency/interface/ADR deviation)."
phase: P1
depends_on: [REQ-SB-47-US-01-T01]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-47-US-01-T02 — New `agent_schedule_registry.py` — CRUD + shared lock + live-scheduler seam

## Parent Story

- Story: [[REQ-SB-47-US-01]] — `../UserStories/REQ-SB-47-US-01-per-agent-scheduler-and-shared-serialization.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-47 *Per-Agent Scheduler* (merges REQ-SB-45)

---

## Objective

Build the new business-layer module `app/business/agent_schedule_registry.py`
— the single canonical home for persisted per-`(agent_id, capability_id)`
schedule CRUD, the shared in-process Outlook-COM dispatch lock, and the seam
that lets it mutate a live `AsyncIOScheduler` without `app/business/` ever
importing `app.scheduling` — plus the paired `vault_writer.py` JSON
persistence primitives it sits on, per `ADR-037` points 1, 2, 3, 4.

---

## Starting State → End State

**Before / Inputs:**
- No `agent_schedule_registry.py` module exists.
- No `.second-brain/agent_schedules.json` sibling store exists.
- `T01`'s `invoke_skill` now accepts `trigger="scheduled"` and silently skips Manual-mode scheduled dispatches.
- `app/business/working_mode_registry.py` and `vault_writer.py`'s `load_working_modes_state`/`save_working_modes_state` pair (lines ~1186-1199) are the real, shipped shape this task's own persistence pair mirrors exactly (pure I/O in `vault_writer.py`, all default/self-healing logic in the business module).
- `app/business/skill_registry.py::list_agent_skills(agent_id)` and `app/business/skill_tools.py::SKILLS[skill_id]["mutates"]` are the real, existing functions this task's own refusal check (Scenario 9) composes against.

**After / Outputs:**
- `app/data_access/vault_writer.py` gains `_AGENT_SCHEDULES_FILE = "agent_schedules.json"` plus `load_agent_schedules_state()`/`save_agent_schedules_state()`, pure I/O, mirroring the working-modes pair's exact shape (returns `None` if the file doesn't exist yet — no default content computed here, per `ADR-003`).
- `app/business/agent_schedule_registry.py` exists, exporting:
  - `list_schedules(agent_id: str | None = None) -> list[dict]`
  - `create_or_update_schedule(agent_id: str, capability_id: str, interval_value: int, interval_unit: str) -> dict` — raises/refuses (see Constraints) unless `capability_id` is in `skill_registry.list_agent_skills(agent_id)` AND `skill_tools.SKILLS[capability_id]["mutates"] is True`; persists under composite key `f"{agent_id}::{capability_id}"`; replaces an existing entry for the same key in place (never duplicates).
  - `remove_schedule(agent_id: str, capability_id: str) -> bool`
  - `set_live_scheduler(scheduler) -> None` and `get_shared_dispatch_lock() -> asyncio.Lock`
  - `dispatch_with_shared_lock(agent_id: str, capability_id: str, trigger: Literal["scheduled", "direct"]) -> dict` — skips (does not queue) with `{"status": "skipped", "message": "skipped — another run is already in progress"}` if the lock is held; otherwise acquires it, calls `await asyncio.to_thread(skill_registry.invoke_skill, agent_id, capability_id, None, trigger)`, and records the outcome to that agent's run history via `vault_writer.append_agent_history_entry` for every status EXCEPT `"skipped_manual"` (`T01`'s new status, which must stay history-free).
- `create_or_update_schedule`/`remove_schedule` also call `.add_job(..., replace_existing=True)` / `.remove_job(...)` directly on whatever `AsyncIOScheduler` instance was last passed to `set_live_scheduler` — a no-op (persist-JSON-only) if none has been set yet, so this module is safely importable/testable in isolation before `T03` wires the real one in.

---

## Files to Modify

- `src/backend/app/business/agent_schedule_registry.py` — new file.
- `src/backend/app/data_access/vault_writer.py` — add the `_AGENT_SCHEDULES_FILE` constant (alongside the other `_AGENT_*_FILE` constants, ~line 27-31) and the `_agent_schedules_state_path()`/`load_agent_schedules_state()`/`save_agent_schedules_state()` trio (alongside the working-modes trio, ~line 1180-1199).

---

## Constraints

- Inherits from parent story.
- `vault_writer.py`'s new pair is pure I/O only (`ADR-003`) — no default-computation, no self-healing logic; that belongs entirely in `agent_schedule_registry.py`.
- Composite-key dict shape (`"<agent_id>::<capability_id>"` → schedule record), NOT a uuid-keyed list — this is what makes "at most one active schedule per (agent, capability) pair" true by construction (`ADR-037`, Alternatives Considered).
- `create_or_update_schedule`'s refusal (Scenario 9 / `AC-09`) must be a clean, catchable/returnable outcome the router (`T04`) can turn into an HTTP `400` with a clear message — do not let it raise an unhandled exception; either return a `{"refused": True, "reason": ...}`-shaped dict or raise a dedicated, narrow exception type the router explicitly catches (coder's implementation choice, log which was picked in the Implementation Log).
- `dispatch_with_shared_lock` is the ONE function through which every scheduled/run-now dispatch passes (mirrors `ADR-005` point 3's "one concurrency guard spans both trigger sources," generalized) — do not add any second lock or bypass path.
- This module must not import `app.scheduling` at all, in either direction — the live-scheduler seam works because the object passed to `set_live_scheduler` is a plain third-party `apscheduler.schedulers.asyncio.AsyncIOScheduler` instance, not `app.scheduling`-owned code (`ADR-037` point 2, `ADR-005` point 5's one-directional `scheduling → business` edge stays intact).
- Do not modify `skill_registry.py`, `skill_tools.py`, or `capture_scheduler.py` in this task — `T01` already landed the one `skill_registry.py` change this module depends on; `capture_scheduler.py`'s own edit is `T03`.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-47-US-01-AC-01, partial] In a Python shell (`src/backend`), call `agent_schedule_registry.create_or_update_schedule("email-capture", "run_capture_now", 90, "minutes")` (a real granted, mutating capability). Expect a success result. Confirm `.second-brain/agent_schedules.json` now contains one entry keyed `"email-capture::run_capture_now"` with `interval_value: 90, interval_unit: "minutes"`. Call `agent_schedule_registry.list_schedules("email-capture")` and confirm it reflects the same capability + interval.
2. [REQ-SB-47-US-01-AC-04, partial] Call `create_or_update_schedule("email-capture", "run_capture_now", 3, "hours")` again (same agent+capability). Confirm `list_schedules("email-capture")` still shows exactly ONE entry for this pair (replaced in place, not duplicated), now reading `interval_value: 3, interval_unit: "hours"`.
3. [REQ-SB-47-US-01-AC-05, partial] Call `agent_schedule_registry.remove_schedule("email-capture", "run_capture_now")` — expect `True`. Confirm `list_schedules("email-capture")` no longer includes it.
4. [REQ-SB-47-US-01-AC-09, partial] Call `create_or_update_schedule("vault-qa", "ask_question", 1, "hours")` — `ask_question` is granted to `vault-qa` but `"mutates": False` — expect a clean refusal (not an unhandled exception), and confirm `list_schedules("vault-qa")` shows no such entry. Call `create_or_update_schedule("vault-qa", "run_capture_now", 1, "hours")` — `run_capture_now` is not granted to `vault-qa` at all — expect the same clean refusal shape, and confirm no entry was created.
5. [REQ-SB-47-US-01-AC-06, partial] Call `await agent_schedule_registry.dispatch_with_shared_lock("email-capture", "run_capture_now", trigger="direct")` (e.g. via `asyncio.run(...)` in the shell). Confirm the returned dict's status matches what `skill_registry.invoke_skill("email-capture", "run_capture_now", None, trigger="direct")` would itself return, and confirm `vault_writer.load_agent_history("email-capture")` gained exactly one new entry recording this outcome.
6. [REQ-SB-47-US-01-AC-07] The shared-lock property. In one `asyncio.run(...)` session, launch two `dispatch_with_shared_lock` calls concurrently via `asyncio.gather` for two DIFFERENT (agent, capability) pairs (e.g. `("email-capture", "run_capture_now")` and `("meeting-capture", "run_capture_now")`) — to make the race observable regardless of each handler's own real latency, temporarily wrap the call in a small script that also starts a third, deliberately slow dummy coroutine holding the lock first (or monkeypatch `skill_registry.invoke_skill` in-process to sleep briefly before returning, reverted immediately after this check), then fire both real dispatches while it's held. Confirm exactly one of the two returns the real dispatch outcome and the other returns `{"status": "skipped", "message": "skipped — another run is already in progress"}`, and confirm the skipped one's outcome is also recorded to that agent's history (per `dispatch_with_shared_lock`'s own "every status except skipped_manual is recorded" rule). Confirm via timestamps/an explicit in-process marker that the two real invocations never overlap.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `create_or_update_schedule`/`list_schedules`/`remove_schedule` persist to `.second-brain/agent_schedules.json` under the composite-key shape, no duplication on repeat create for the same pair.
- [ ] `create_or_update_schedule` cleanly refuses an ungranted or non-mutating `capability_id` — no schedule created, no unhandled exception.
- [ ] `dispatch_with_shared_lock` runs the real dispatch through `invoke_skill`, records every non-`skipped_manual` outcome to run history.
- [ ] The shared lock serializes two concurrent dispatches for different (agent, capability) pairs — one runs, one is honestly skipped and recorded, no overlap.
- [ ] `vault_writer.py`'s new pair is pure I/O, matching its own file-header convention.
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint.
- [ ] `CHANGELOG.md` entry appended.

---

## Out of Scope

- Registering any real APScheduler job or wiring `set_live_scheduler` into the real app lifespan (`T03`).
- Any HTTP endpoint (`T04`/`T05`).
- Any frontend change (`T06`).

---

## Context / Notes

Real precedent to mirror: `src/backend/app/business/working_mode_registry.py` (self-healing-inside-`_load_state()` shape) and `src/backend/app/data_access/vault_writer.py` lines ~1186-1199 (the working-modes I/O pair) — same pattern already reconfirmed for `REQ-SB-51-US-01-T01`'s `background_agent_registry.py`. Full mechanism reasoning: `ADR-037` points 1-4, `Implementation/Architecture/architecture.md` → "Per-Agent Scheduler & Shared Outlook-COM Dispatch Lock."

`AC-07`'s shared-lock property is this story's single most safety-critical guarantee — treat its verification step as load-bearing, not a formality (`Implementation/Learnings.md`, `SPRINT-031`'s "independently test the single highest-risk check first" pattern applies directly here).

---

## Implementation Log

**Built:** `src/backend/app/business/agent_schedule_registry.py` (new) —
`list_schedules`/`create_or_update_schedule`/`remove_schedule` (composite-key
`.second-brain/agent_schedules.json`), `ScheduleRefusedError` (chose the
raise-a-dedicated-exception option named in this task's own Constraints, over
a `{"refused": True, ...}` dict — kept the success return shape uniformly a
plain schedule record), `set_live_scheduler`/`get_shared_dispatch_lock`,
`dispatch_with_shared_lock`. `src/backend/app/data_access/vault_writer.py` —
added `_AGENT_SCHEDULES_FILE` + `load_agent_schedules_state`/
`save_agent_schedules_state`, mirroring the working-modes pair exactly.

**Real, live-discovered defect found and fixed in-scope (scope-internal
judgement call, logged per Pipeline.md, not an escalation):** this task's own
"After/Outputs" text (and `ADR-037` point 1/5's own illustrative description)
said `dispatch_with_shared_lock` records every outcome "except
`skipped_manual`". Running the REAL composed call graph live (not trusting
the illustrative text — `Implementation/Learnings.md`'s repeated
SPRINT-018/019/030 pattern) surfaced a genuine duplicate-history bug: (1) a
Supervised+mutating dispatch's `"pending"` outcome is already recorded by
`invoke_skill`'s own gate (a `"proposal"` entry) — a second generic append
would duplicate it; (2) `run_capture_now`'s real `email-capture` dispatch
(via `email_classification.run_capture_and_record_completion`) ALREADY
writes email-capture's own `run_event`/`run_error` entry internally, with
**no** `"history_recorded"` flag on its return value (unlike `build_knowledge`,
which does set it) — a real, pre-existing inconsistency in the already-shipped
`skill_tools.py`, out of this story's own scope to fix there. Confirmed live:
a real `dispatch_with_shared_lock("email-capture", "run_capture_now",
trigger="direct")` call grew email-capture's own history by 2 entries under
the original design (the blob tick's own internal write + this function's
own generic duplicate), not 1.

**Fix (in-scope, this task's own file):** replaced the flag/status-based
exclusion list with a generic before/after history-length comparison —
`_record_outcome` now skips its own generic append whenever `agent_id`'s
history already grew during the real dispatch just awaited (catches BOTH the
`"pending"` case and the unflagged `run_capture_now` case, and any future
self-recording handler, flagged or not, with zero hardcoded capability_id/
status list beyond the one true "never record" case, `"skipped_manual"`,
which must stay history-free by design regardless of length). Re-verified
live after the fix — see AC-06 below.

**Verification (2026-08-14, real `.second-brain/` state throughout):**

- `[AC-01, partial]` `create_or_update_schedule("email-capture",
  "run_capture_now", 90, "minutes")` → success; `.second-brain/
  agent_schedules.json` gained `"email-capture::run_capture_now"` with
  `interval_value: 90, interval_unit: "minutes"`; `list_schedules
  ("email-capture")` reflected it. **PASS.**
- `[AC-04, partial]` Re-called with `(3, "hours")` for the same pair — exactly
  one entry remained, now reading `3 hours` (replaced in place, not
  duplicated). **PASS.**
- `[AC-05, partial]` `remove_schedule("email-capture", "run_capture_now")` →
  `True`; `list_schedules` no longer includes it. **PASS.**
- `[AC-09, partial]` `create_or_update_schedule("vault-qa", "ask_question",
  1, "hours")` (granted, non-mutating) → `ScheduleRefusedError`, no entry
  created. `create_or_update_schedule("vault-qa", "run_capture_now", 1,
  "hours")` (ungranted) → same refusal shape, no entry created. **PASS.**
- `[AC-06, partial]` Direct real dispatch via HTTP run-now (T05's endpoint,
  same underlying function) for `email-capture`/`run_capture_now`: real
  outcome `{"available":true,"message":"Done — 0 email(s) filed."}`,
  exactly ONE new email-capture history entry ("Capture run completed — 0
  email(s) filed") — confirmed NOT duplicated post-fix. **PASS** (re-run
  after the fix; the pre-fix run showed the now-fixed +2 defect, described
  above).
- `[AC-07]` Shared-lock property, in-process: `asyncio.gather` of two
  `dispatch_with_shared_lock` calls for `meeting-capture`/`run_capture_now`
  and `todo-capture`/`run_capture_now`, with `skill_registry.invoke_skill`
  temporarily monkeypatched (reverted immediately after) to record explicit
  start/end timing markers around the real call. Result: exactly one real
  outcome, one honest `{"status": "skipped", "message": "skipped — another
  run is already in progress"}`; exactly 2 markers total (one start+end
  pair) — confirming the lock genuinely prevented a second real dispatch
  from ever starting, not just that one "won." Both outcomes recorded to
  their own agent's history (meeting hist 67→68, todo hist 38→39). **PASS —
  this is the story's own single highest-risk guarantee; see also T05's
  independent real-HTTP-layer reconfirmation.**

Assumption (scope-internal, logged): substituted `meeting-capture`/
`todo-capture` for the task's own `email-capture`/`meeting-capture` example
pair in the concurrency check (step 6) to keep it fast (both resolve to the
existing honest "not available" stub, avoiding a second real, multi-minute
Outlook-COM blob tick) — still a real, unmocked `invoke_skill` call for each.

gate: flagged 2026-08-14 — trigger 8-adjacent scope-internal judgement call
(the in-scope dedup-logic correction above), not an escalation; human
spot-check recommended per Pipeline.md's scope-internal-judgement-call
provision. No ADR change, no new dependency, no unresolved verification gap.
