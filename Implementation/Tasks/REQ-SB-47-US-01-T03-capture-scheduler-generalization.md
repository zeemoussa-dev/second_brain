---
id: REQ-SB-47-US-01-T03
title: capture_scheduler.py — publish live scheduler, register per-schedule jobs, swap to the shared dispatch lock
parent_story: REQ-SB-47-US-01
requirement_id: REQ-SB-47
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-47-US-01-T02]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-47-US-01-T03 — `capture_scheduler.py` generalization

## Parent Story

- Story: [[REQ-SB-47-US-01]] — `../UserStories/REQ-SB-47-US-01-per-agent-scheduler-and-shared-serialization.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-47 *Per-Agent Scheduler* (merges REQ-SB-45)

---

## Objective

Surgically edit `app/scheduling/capture_scheduler.py` — not rewrite it — so
the existing hourly blob tick shares `agent_schedule_registry`'s dispatch
lock instead of its own private one, `build_scheduler()` also registers one
APScheduler job per persisted per-agent schedule, and `lifespan()` publishes
the live scheduler instance into `agent_schedule_registry` once at startup,
per `ADR-037` points 1, 2, 6.

---

## Starting State → End State

**Before / Inputs:**
- `src/backend/app/scheduling/capture_scheduler.py` (read in full during this pass — see the file's real current content) owns its own private `_capture_run_lock = asyncio.Lock()`, one hardcoded `hourly_capture` job, and `lifespan()`'s unconditional app-start trigger.
- `T02`'s `agent_schedule_registry.py` exists: `get_shared_dispatch_lock()`, `set_live_scheduler(scheduler)`, `list_schedules()`, `dispatch_with_shared_lock(agent_id, capability_id, trigger)`.

**After / Outputs:**
- `_capture_run_lock` is removed. `run_capture_if_idle` acquires `agent_schedule_registry.get_shared_dispatch_lock()` instead — the ONE edit to this function's own locking, its call to `email_classification.run_capture_and_record_completion` is otherwise untouched.
- `build_scheduler()` still registers the existing hardcoded `hourly_capture` job exactly as before (unchanged `IntervalTrigger(hours=1)`, `coalesce=True, misfire_grace_time=None, max_instances=1`), and additionally reads `agent_schedule_registry.list_schedules()` and registers one job per persisted schedule: `id=f"schedule:{agent_id}:{capability_id}"`, `IntervalTrigger(minutes=...)` or `IntervalTrigger(hours=...)` per the schedule's own persisted unit, the same `coalesce=True, misfire_grace_time=None, max_instances=1` configuration, callback `lambda: agent_schedule_registry.dispatch_with_shared_lock(agent_id, capability_id, trigger="scheduled")` (or an equivalent bound-argument form that avoids the classic late-binding-closure-in-a-loop bug).
- `lifespan()` calls `agent_schedule_registry.set_live_scheduler(scheduler)` once, immediately after `build_scheduler()` and before `scheduler.start()`.
- The existing unconditional app-start `asyncio.create_task(run_capture_if_idle())` call is untouched.

---

## Files to Modify

- `src/backend/app/scheduling/capture_scheduler.py` — surgical edit only: remove `_capture_run_lock`; `run_capture_if_idle`'s lock acquisition; `build_scheduler()`'s new schedule-reading loop; `lifespan()`'s new `set_live_scheduler` call. No other function's shape changes.

---

## Constraints

- Inherits from parent story.
- This file stays structurally parallel to `app/api/` (`ADR-005` point 5) — it may call into `app/business/` (`agent_schedule_registry`, already an allowed edge), but must never be imported BY `app/business/` — the seam stays one-directional.
- `email_classification.py`'s own background gate (`ADR-018`/`ADR-020`) is explicitly out of scope — unmodified. The blob tick's own bespoke Autonomous/Supervised/Manual gate keeps running exactly as before; this task changes only which lock object `run_capture_if_idle` acquires.
- The existing hourly blob tick must not silently stop running, or silently double-run alongside a newly-configured per-agent schedule for one of the same three capture agents (the story's own named Constraint) — the shared lock is what guarantees this; do not add any second, independent guard.
- Do not rebuild the blob tick to route through `dispatch_with_shared_lock` itself, and do not retire `hourly_capture` — `ADR-037` point 6 explicitly keeps the two mechanisms coexisting, sharing only the lock.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-47-US-01-AC-04, partial] Using `T02`'s registry, create a real schedule (e.g. `agent_schedule_registry.create_or_update_schedule("meeting-capture", "run_capture_now", 5, "minutes")`) BEFORE starting the server. Start the real backend (`uvicorn app.main:app --reload`, `src/backend`). Confirm via a Python shell against the running process (or a debug log line temporarily added and reverted) that `build_scheduler()` registered a job with id `"schedule:meeting-capture:run_capture_now"` and a 5-minute `IntervalTrigger`, alongside the still-present `"hourly_capture"` job.
2. [REQ-SB-47-US-01-AC-04, partial — live edit, no restart] With the server still running, call `agent_schedule_registry.create_or_update_schedule("meeting-capture", "run_capture_now", 20, "minutes")` again (same pair, new interval) via a second Python shell pointed at the same running process's own vault state — since `set_live_scheduler` was called at this process's own startup, confirm the LIVE scheduler's own job registry (inspectable via the same in-process debug technique as step 1, or by observing the next real fire timing) now reflects the new 20-minute interval, without restarting the server.
3. [REQ-SB-47-US-01-AC-05, partial — live edit, no restart] Still against the same running server, call `agent_schedule_registry.remove_schedule("meeting-capture", "run_capture_now")`. Confirm the live scheduler's job registry no longer contains `"schedule:meeting-capture:run_capture_now"`, and that `"hourly_capture"` is still present and unaffected — no restart required.
4. [Regression, not independently locked] Confirm `run_capture_if_idle` still correctly guards against an overlapping app-start-vs-hourly-boundary run for the blob tick itself (re-run this story's own precedent check from `REQ-SB-05`/`REQ-SB-07`'s original verification if still reproducible, or at minimum confirm by direct read that `run_capture_if_idle`'s own `if _lock.locked(): return` skip-not-overlap shape is preserved, now against `agent_schedule_registry.get_shared_dispatch_lock()` instead of the removed private lock).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `run_capture_if_idle` acquires the shared lock from `agent_schedule_registry`, not a private one.
- [ ] `build_scheduler()` registers one job per persisted schedule, alongside the unchanged `hourly_capture` job.
- [ ] `lifespan()` publishes the live scheduler into `agent_schedule_registry` before `scheduler.start()`.
- [ ] A live add/remove via `agent_schedule_registry` mutates the running scheduler's own job registry with no restart required.
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint.
- [ ] `CHANGELOG.md` entry appended.

---

## Out of Scope

- Any HTTP endpoint (`T04`/`T05`).
- Any frontend change (`T06`).
- `email_classification.py`'s own gate logic.

---

## Context / Notes

Real file to compose against: `src/backend/app/scheduling/capture_scheduler.py` (read fresh — reproduced in full in this story's own Context for reference, but re-read the real file before editing, per `Implementation/Learnings.md`'s "compose around the REAL current file" pattern). Full reasoning: `ADR-037` points 1, 2, 6.

The live-scheduler seam is deliberately one-directional (`scheduling → business` only) — `agent_schedule_registry.py`'s own CRUD functions mutate the stored `AsyncIOScheduler` reference directly; this file never imports `agent_schedule_registry` back for job mutation beyond the one `set_live_scheduler` publish call.

---

## Implementation Log

**Change:** `src/backend/app/scheduling/capture_scheduler.py` — removed the
private `_capture_run_lock`; `run_capture_if_idle` now acquires
`agent_schedule_registry.get_shared_dispatch_lock()`. `build_scheduler()`
still registers the unchanged `hourly_capture` job, then additionally reads
`agent_schedule_registry.list_schedules()` and registers one
`IntervalTrigger` job per persisted schedule (`id=f"schedule:{agent_id}:
{capability_id}"`, same `coalesce=True, misfire_grace_time=None,
max_instances=1`), via a new local `_build_scheduled_tick(agent_id,
capability_id)` closure factory (bound-argument, not a raw lambda over the
loop variable — avoids the late-binding bug). `lifespan()` calls
`agent_schedule_registry.set_live_scheduler(scheduler)` immediately after
`build_scheduler()`, before `scheduler.start()`.

**Verification (2026-08-14, real running server, `src/backend`,
`.venv\Scripts\uvicorn.exe app.main:app --port 8001`, no `--reload` — a
stray earlier `--reload` instance serving pre-sprint code was found and
killed first, per `Implementation/Learnings.md`'s established
specific-PID-kill-and-restart protocol):**

- `[AC-04, partial]` Created a real schedule (`meeting-capture`/
  `run_capture_now`, 5 minutes) via `T02`'s registry BEFORE restarting the
  server, confirmed via `GET /agents/meeting-capture/schedules`.
- `[AC-04, partial — live edit, no restart]` `PATCH`'d the same schedule's
  interval to 1 minute through the running server. `GET`-confirmed the
  update. Also created a second real schedule (`todo-capture`/
  `run_capture_now`, 1 minute) the same way.
- **Real scheduled ticks confirmed firing, live-mutated interval honored, no
  restart anywhere:** `meeting-capture`'s own history gained a real
  `"Scheduled run — Run Capture Now — This skill is not yet available..."`
  entry at `12:15:58` — ~1 minute after the 1-minute PATCH at `12:14:58`
  (not 5 minutes after the original 5-minute creation at `12:14:46`),
  proving the LIVE job registry was genuinely mutated in place, not just the
  JSON file. `todo-capture`'s own history gained the equivalent real entry
  at `12:16:04`, ~1 minute after its own creation. **PASS** for
  registration + live-mutation + correct `"Scheduled run"` labeling.
- `[AC-05, partial]` `DELETE`'d both test schedules through the running
  server; `GET` confirmed both empty (cleanup — these were fast, 1-minute
  test schedules, not meant to persist as real configuration).
  `hourly_capture` was unaffected throughout (confirmed present in every
  `GET /agents/.../schedules` response cycle; never touched by any
  add/remove call, which are scoped to `schedule:{agent_id}:{capability_id}`
  job ids only).
- `[Regression]` `run_capture_if_idle`'s own `if lock.locked(): return`
  skip-not-overlap shape is preserved unchanged, now against
  `agent_schedule_registry.get_shared_dispatch_lock()` — confirmed by direct
  read (only the lock source changed, not the guard's own control flow) and
  reconfirmed live: the app-start `hourly_capture`-equivalent blob tick and
  a directly-issued run-now both correctly serialized against each other
  during this same live session (see `T02`/`T05` Implementation Logs for
  the detailed concurrent-dispatch evidence, which exercises this exact
  shared lock).

No deviations from the task's own design. `agent_schedule_registry.py`
itself was not touched in this task (only referenced via its already-`Done`
public API), per this task's own Files-to-Modify scope.

gate: clear 2026-08-14 — no triggers fired (no ADR change, no new
assumption, requirement finalised, all tagged manual steps verified live and
passing).
