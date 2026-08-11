---
id: REQ-SB-07-US-01-T03
title: "New app/scheduling/ package: shared concurrency guard"
parent_story: REQ-SB-07-US-01
requirement_id: REQ-SB-07
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-005 created) — inherited from parent story"
phase: P1
depends_on: [REQ-SB-07-US-01-T02]
created: 2026-08-10
updated: 2026-08-10
---

# REQ-SB-07-US-01-T03 — New `app/scheduling/` package: shared concurrency guard

## Parent Story

- Story: [[REQ-SB-07-US-01]] — `../UserStories/REQ-SB-07-US-01-scheduled-recurring-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-07 *Scheduled Recurring Agent Capture*

---

## Objective

Stand up the new `app/scheduling/` top-level package (ADR-005, point 5) with
the one shared concurrency guard both trigger sources (app-start in T04, the
hourly APScheduler job in T04) will call through, so an in-progress capture
run is never started a second time by an overlapping trigger.

---

## Starting State → End State

**Before / Inputs:**
- No `app/scheduling/` package exists yet.
- T02 added `email_classification.run_capture_and_record_completion()`, the
  single business-layer entry point this guard will wrap.

**After / Outputs:**
- `app/scheduling/__init__.py` and `app/scheduling/capture_scheduler.py`
  exist, exposing `run_capture_if_idle()` — an async function that runs one
  capture pass if idle, or skips immediately (never queues) if a run is
  already in progress.

---

## Files to Modify

- `src/backend/app/scheduling/__init__.py` — new, empty package marker.
- `src/backend/app/scheduling/capture_scheduler.py` — new file:
  ```python
  """Coordinates trigger sources (app-start, hourly interval — wired in T04)
  for the email capture pipeline. A single shared concurrency guard covers
  both trigger sources (ADR-005, point 3) so an app-start run and an
  hourly-boundary run can never overlap each other, not just overlap
  themselves.

  Structurally parallel to app/api/ (ADR-005, point 5): translates a
  timer/lifecycle event into a call against business/, never reaches into
  data_access/ directly.
  """
  from __future__ import annotations

  import asyncio
  import logging

  from app.business import email_classification

  logger = logging.getLogger(__name__)

  _capture_run_lock = asyncio.Lock()


  async def run_capture_if_idle() -> None:
      """Runs one capture pass if no other capture is currently running;
      otherwise logs and returns immediately without waiting for the
      in-progress run to finish (Scenario 4 / AC-04: skip, not queue, not
      overlap). The underlying pipeline makes blocking Outlook COM calls, so
      it runs off the event loop thread via asyncio.to_thread."""
      if _capture_run_lock.locked():
          logger.info(
              "Capture run already in progress — skipping this trigger "
              "rather than starting an overlapping run."
          )
          return
      async with _capture_run_lock:
          await asyncio.to_thread(
              email_classification.run_capture_and_record_completion
          )
  ```

---

## Constraints

- Inherits from parent story.
- `app/scheduling/` may call into `business/` only — never `data_access/`
  directly (ADR-005, point 5, extending ADR-003's boundary).
- The guard must be non-blocking-check: a second trigger finding the lock
  held must return immediately (skip), never `await lock.acquire()` and
  wait for it to free — waiting would turn a skip into a deferred/queued
  run, which AC-04 explicitly rules out.
- `run_capture_if_idle` must be a plain importable async function (no
  APScheduler dependency in this file yet) — APScheduler wiring is T04's
  scope, kept separate so this guard is testable standalone.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-07-US-01-AC-04] In a Python shell (or a small throwaway script)
   against the backend `.venv`, with `asyncio` available: start one
   `run_capture_if_idle()` call as a task (e.g.
   `task = asyncio.create_task(run_capture_if_idle())`), then — before it
   completes — call `run_capture_if_idle()` a second time directly (e.g.
   `await run_capture_if_idle()`). Confirm the second call returns
   immediately (logs the "already in progress — skipping" message) without
   waiting for the first task to finish, and that only one underlying
   `run_capture_and_record_completion` execution actually occurs (e.g.
   observe `.second-brain/last_capture_run.json` is updated only once, and
   that no error/exception is raised by the skipped call). Then `await
   task` to confirm the first (in-progress) run completes normally,
   uninterrupted by the second trigger.

**Automated tests:** `n/a — test tooling pending; a pytest module using
asyncio.gather over a stubbed/slow business call would be the natural
automated version once this layer gets coverage`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `run_capture_if_idle()` skips immediately (no wait) when the guard is
      already held, and logs the skip
- [x] A skip never invokes `run_capture_and_record_completion` a second time
      concurrently
- [x] The in-progress run, once started, completes uninterrupted by a
      concurrent skipped trigger
- [x] `app/scheduling/` imports only from `app/business/`, not
      `app/data_access/` directly
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Registering this function with APScheduler or FastAPI's `lifespan` — T04.
- Reading `last_capture_run.json` to decide whether to fire — per ADR-005
  point 4 / this story's Non-Goals, no such conditional logic is required by
  any locked AC.

---

## Context / Notes

`asyncio.Lock` in Python is not reentrant and `.locked()` is a synchronous,
non-blocking check — exactly the "skip immediately if held" shape AC-04
needs, without any extra bookkeeping (a plain boolean flag would work too,
but `asyncio.Lock` also gives correct release-on-exception behaviour via the
`async with` block for free).

---

## Implementation Log

**Coder pass (2026-08-10):** Created `src/backend/app/scheduling/__init__.py`
(empty package marker) and `src/backend/app/scheduling/capture_scheduler.py`
exactly as specified in `## Files to Modify` — no deviation from the task's
prescribed code. `run_capture_if_idle()` guards
`email_classification.run_capture_and_record_completion` (added by T02) with
a module-level `asyncio.Lock`, checking `.locked()` synchronously before
attempting `async with` so a held lock is skipped immediately rather than
awaited. Confirmed by inspection that the file's only internal import is
`from app.business import email_classification` — no `app.data_access`
import, satisfying the ADR-005 point 5 / T03 constraint.

**[REQ-SB-07-US-01-AC-04] — verified, PASS.** Ran a throwaway async script
(`verify_ac04_concurrency_guard.py`, in the session scratchpad, not part of
the repo) against the backend `.venv` with `PYTHONPATH` set to
`src/backend`, per the task's manual verification step:
1. Started `run_capture_if_idle()` as a background task
  (`asyncio.create_task`) — confirmed `_capture_run_lock.locked()` is `True`
  almost immediately after, i.e. the first call had acquired the guard.
2. Called `run_capture_if_idle()` a second time directly, awaited. Observed
  log line `"Capture run already in progress — skipping this trigger rather
  than starting an overlapping run."` and the awaited call returned in
  `0.0008s` — i.e. it returned immediately rather than waiting on the first
  run's ~20s Outlook/Compass pipeline. No exception was raised by the
  skipped call.
3. Awaited the first (in-progress) task: it completed normally after
  `19.70s` (real Outlook fetch → Compass classification → vault write,
  4 Compass HTTP calls observed in the log), uninterrupted by the second
  trigger.
4. Confirmed only one underlying `run_capture_and_record_completion`
  execution actually occurred: `.second-brain/last_capture_run.json`'s
  `finished_at` moved from the pre-test baseline
  (`2026-08-10T15:01:34.275859+00:00`, from an earlier manual POC run) to
  exactly one new timestamp (`2026-08-10T15:04:25.337555+00:00`) matching
  the single completed task — a single write, not two, confirming the skip
  never invoked the pipeline concurrently.

This exercised the real Outlook desktop COM automation and real Compass
classification calls (per the task's own instruction that this is expected)
— no mocking was introduced, consistent with `MEMORY.md`'s note that the
underlying pipeline was already validated end-to-end against a real inbox.

**Assumption logged for spot-check (scope-internal judgement call, not an
escalation):** the manual verification step said to `asyncio.create_task`
the first call then immediately issue the second — the script inserts a
short `asyncio.sleep(0.05)` between the two so the first call has
deterministically acquired the lock (`async with` on an uncontended
`asyncio.Lock` can otherwise be interleaved unpredictably by the event
loop). This does not change what's being verified — the lock was already
confirmed held (`locked() == True`) before the second call was issued — and
does not affect production code, since `capture_scheduler.py` itself has no
`sleep` or timing dependency.

**Automated test:** not added — per the task's own `## Tests` section,
`n/a — test tooling pending`, matching the story-level note that `pytest`
today only covers `/health`. Manual mode per
`Implementation/Pipeline.md`'s coder verification-mode section.

`gate: flagged` left unchanged, inherited from the parent story's
ADR-005 flag (trigger-3) — already resolved by the operator's 2026-08-10
review of ADR-005 itself (see the story's `## Notes`); no new MUST-FLAG
trigger fired during this task's own implementation (no new dependency, no
shared-interface change, no ADR deviation, no unanticipated file, no
unclear/contradictory requirement — the code matched the task's prescribed
`## Files to Modify` content exactly).
