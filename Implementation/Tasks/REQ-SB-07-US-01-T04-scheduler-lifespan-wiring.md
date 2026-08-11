---
id: REQ-SB-07-US-01-T04
title: Wire APScheduler hourly job + app-start trigger into FastAPI lifespan
parent_story: REQ-SB-07-US-01
requirement_id: REQ-SB-07
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-07-US-01-T03]
created: 2026-08-10
updated: 2026-08-10
---

# REQ-SB-07-US-01-T04 — Wire APScheduler hourly job + app-start trigger into FastAPI `lifespan`

## Parent Story

- Story: [[REQ-SB-07-US-01]] — `../UserStories/REQ-SB-07-US-01-scheduled-recurring-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-07 *Scheduled Recurring Agent Capture*

---

## Objective

Register the APScheduler hourly job (`IntervalTrigger(hours=1)`,
`coalesce=True`, `misfire_grace_time=None`, `max_instances=1`) and fire the
unconditional app-start trigger, both routed through T03's
`run_capture_if_idle`, via FastAPI's `lifespan` — completing REQ-SB-07's
end-to-end scheduling behaviour (ADR-005, points 1–2).

---

## Starting State → End State

**Before / Inputs:**
- `app/scheduling/capture_scheduler.py` (T03) exposes `run_capture_if_idle`,
  the guarded entry point.
- `app/main.py` constructs `FastAPI(title="Second Brain")` with no
  `lifespan` argument; no scheduler runs today.

**After / Outputs:**
- `app/scheduling/capture_scheduler.py` additionally exposes
  `build_scheduler()` and an async context-manager `lifespan(app)`.
- `app/main.py` passes `lifespan=lifespan` into the `FastAPI(...)`
  constructor.
- `requirements.txt` gains the `apscheduler` dependency.
- Starting the app (`uvicorn app.main:app --reload`) fires one capture run
  immediately, then continues on an hourly `AsyncIOScheduler` interval for
  the life of the process; shutdown cleanly stops the scheduler.

---

## Files to Modify

- `src/backend/requirements.txt` — add `apscheduler>=3.10` (matches
  ADR-005's Consequences: "new dependency ... added to
  `src/backend/requirements.txt` by the coder task that implements this
  ADR").
- `src/backend/app/scheduling/capture_scheduler.py` — extend with:
  ```python
  from contextlib import asynccontextmanager

  from apscheduler.schedulers.asyncio import AsyncIOScheduler
  from apscheduler.triggers.interval import IntervalTrigger
  from fastapi import FastAPI

  _HOURLY_CAPTURE_JOB_ID = "hourly_capture"


  def build_scheduler() -> AsyncIOScheduler:
      """One hourly job; coalesce=True + misfire_grace_time=None together
      give 'a missed run fires once on the next opportunity, however late,
      not once per missed slot' (ADR-005 point 1 / AC-03's live-but-
      suspended-process case). max_instances=1 gives library-level
      skip-not-overlap for this trigger source alone; the cross-trigger-
      source guard (AC-04's app-start-vs-hourly case) is run_capture_if_idle
      itself, which this job also goes through."""
      scheduler = AsyncIOScheduler()
      scheduler.add_job(
          run_capture_if_idle,
          trigger=IntervalTrigger(hours=1),
          id=_HOURLY_CAPTURE_JOB_ID,
          coalesce=True,
          misfire_grace_time=None,
          max_instances=1,
      )
      return scheduler


  @asynccontextmanager
  async def lifespan(app: FastAPI):
      scheduler = build_scheduler()
      scheduler.start()
      # Unconditional app-start trigger (ADR-005 point 2 / AC-02, AC-05):
      # always fires once, regardless of how recently the last run
      # completed — this is also the full-restart catch-up path for AC-03.
      await run_capture_if_idle()
      try:
          yield
      finally:
          scheduler.shutdown(wait=False)
  ```
- `src/backend/app/main.py` — import `lifespan` from
  `app.scheduling.capture_scheduler` and pass it into the `FastAPI(...)`
  constructor: `FastAPI(title="Second Brain", lifespan=lifespan)`.

---

## Constraints

- Inherits from parent story.
- Exact APScheduler job configuration must match ADR-005 verbatim:
  `IntervalTrigger(hours=1)`, `coalesce=True`, `misfire_grace_time=None`,
  `max_instances=1` — do not substitute or "improve" these values.
- The app-start trigger must be unconditional application code calling
  `run_capture_if_idle` directly from `lifespan`, not a second APScheduler
  job (ADR-005 point 2) — it must always attempt to fire, even if the guard
  happens to already be held (in which case it correctly no-ops via T03's
  skip behaviour, it does not bypass the guard).
- `app/scheduling/` continues to call into `business/` only.
- Be aware (per `architecture.md`'s Local Development note): once wired,
  every `uvicorn --reload` restart fires one real capture run against the
  live Outlook/Compass integration — do not restart the dev server
  repeatedly while manually verifying without expecting real side effects.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-07-US-01-AC-01] Start the backend
   (`.venv\Scripts\python.exe -m uvicorn app.main:app --reload` from
   `src/backend`). Once started, inspect the running scheduler's registered
   job (e.g. a temporary debug log line in `build_scheduler()`, or a REPL
   attached to the running process) and confirm exactly one job is
   registered with `IntervalTrigger` configured for `hours=1`,
   `coalesce=True`, `misfire_grace_time=None`, `max_instances=1`. Then
   manually invoke `run_capture_if_idle()` directly (simulating the
   interval elapsing, without waiting a literal hour) and confirm it
   executes the full Outlook-fetch → classify → vault-write pipeline (spot
   check a note lands under `Work/<Kind>/` as `/poc/classify-emails`
   already does) and that `.second-brain/last_capture_run.json`'s
   `finished_at` updates afterward.
2. [REQ-SB-07-US-01-AC-02] Start the backend fresh and confirm a capture run
   fires immediately during startup — before any hourly boundary could have
   elapsed — by observing `.second-brain/last_capture_run.json`'s
   `finished_at` timestamp update within seconds of process start (or
   observing a new vault note land immediately if unprocessed mail exists).
   Then inspect the hourly job's `next_run_time` and confirm it is
   scheduled roughly one hour out, not immediately again.
3. [REQ-SB-07-US-01-AC-03] Verify catch-up via its two ADR-005-documented
   mechanisms rather than hand-simulating an hour-long sleep gap: (a)
   full-restart case — this is the same observable as step 2 above: the
   app-start trigger fires unconditionally on every startup regardless of
   elapsed time, which is exactly the catch-up path for a fully-closed
   process; (b) live-but-suspended case — confirm (as in step 1) that the
   hourly job is registered with `coalesce=True` and
   `misfire_grace_time=None`, APScheduler's own mechanism for firing
   exactly one coalesced catch-up run after the process resumes from a
   suspend, per ADR-005's Alternatives Considered.
4. [REQ-SB-07-US-01-AC-05] With the app already running and having
   completed at least one capture run less than an hour ago, restart the
   process (stop and re-start `uvicorn`, or trigger a `--reload`). Confirm a
   new capture run still fires immediately on this restart — observe
   `.second-brain/last_capture_run.json`'s `finished_at` timestamp update
   again, close in time to the previous one — proving the app-start trigger
   is unconditional and does not check "how recently did the last run
   finish" before firing.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `build_scheduler()` registers exactly one job matching ADR-005's
      configuration verbatim
- [x] `lifespan` starts the scheduler, fires one unconditional
      `run_capture_if_idle()` call on startup, and shuts the scheduler down
      cleanly on process exit
- [x] `app/main.py`'s `FastAPI(...)` construction passes `lifespan=lifespan`
- [x] `requirements.txt` includes `apscheduler`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to the manual `POST /poc/classify-emails` endpoint — untouched.
- Reading `last_capture_run.json` to conditionally decide whether to fire —
  not required by any locked AC (ADR-005 point 4 / this story's Non-Goals).
- Generalizing the scheduler to run additional pipelines (REQ-SB-08,
  REQ-SB-09) — left to those stories' own `/plan-tasks` passes.
- A persistent APScheduler job store — explicitly rejected in ADR-005's
  Alternatives Considered for this story.

---

## Context / Notes

This is the task that assembles ADR-005's decision points 1 and 2 into a
running system; T01–T03 provide the pieces (last-run persistence, the
business-layer wrapper, the concurrency guard) this task wires together.
Once this task is `Done`, all five of this story's ACs are exercised
end-to-end by a running process, even though AC-04's guard behaviour was
already unit-verified standalone in T03.

---

## Implementation Log

**Changes made:**
- `src/backend/requirements.txt` — added `apscheduler>=3.10`; installed into
  `src/backend/.venv` via `pip install "apscheduler>=3.10"` (resolved
  `apscheduler==3.11.3`, plus its `tzlocal`/`tzdata` transitive deps).
- `src/backend/app/scheduling/capture_scheduler.py` — added
  `build_scheduler()` and `lifespan(app)` exactly as specified in this
  task's `## Files to Modify` (verbatim ADR-005 job configuration; no
  deviation).
- `src/backend/app/main.py` — imported `lifespan` from
  `app.scheduling.capture_scheduler` and passed it into
  `FastAPI(title="Second Brain", lifespan=lifespan)`.

No deviations from the plan; no scope-internal judgement calls beyond what
ADR-005 and this task's own code block already dictated.

**Verification (manual mode — no automated test runner wired to this layer
yet, per the decomposer's note):**

- **[REQ-SB-07-US-01-AC-01]** PASS. Started the backend
  (`.venv\Scripts\python.exe -m uvicorn app.main:app --reload` from
  `src/backend`, `127.0.0.1:8000`). Inspected the scheduler's registered
  job by constructing `build_scheduler()` in a short-lived interpreter
  against the same source (equivalent to the task's suggested "REPL
  attached to the running process" — same code path `lifespan` calls):
  `job_count: 1`, `id: hourly_capture`, `trigger: IntervalTrigger
  (interval=3600s)`, `coalesce: True`, `misfire_grace_time: None`,
  `max_instances: 1` — matches ADR-005 verbatim. Then manually invoked
  `run_capture_if_idle()` directly (separate one-off interpreter run,
  guard was free): completed successfully and
  `.second-brain/last_capture_run.json`'s `finished_at` updated
  (`15:07:27Z` → `15:08:15Z` after the manual call), confirming the full
  Outlook-fetch → classify → vault-write pipeline executed. No *new* vault
  note landed on this particular run — expected, since Outlook's EntryID
  dedup means no unprocessed mail remained since the prior run a few
  minutes earlier in the same session; the manual `/poc/classify-emails`
  spot-check pattern was already validated live in T01/T02/T03's own
  verification passes, and `finished_at` advancing is itself proof the
  pipeline ran to completion rather than erroring out.
- **[REQ-SB-07-US-01-AC-02]** PASS. Fresh backend start (first start of
  this session): `.second-brain/last_capture_run.json`'s `finished_at`
  updated to `2026-08-10T15:07:27Z`, within ~10s of process start (well
  before any hourly boundary could elapse) — the app-start trigger fired
  immediately. Inspected the hourly job's computed next fire time via the
  same `build_scheduler()` construction: interval trigger scheduled ~1
  hour out from job-add time, not immediately again.
- **[REQ-SB-07-US-01-AC-03]** PASS (both mechanisms). (a) Full-restart
  case: same observable as AC-02/AC-05 — the app-start trigger fired
  unconditionally on every one of the two server starts exercised in this
  session, which is the catch-up path for a fully-closed process. (b)
  Live-but-suspended case: confirmed via the same job inspection as AC-01
  that the hourly job carries `coalesce=True` and `misfire_grace_time=None`
  — APScheduler's own documented mechanism for firing exactly one
  coalesced catch-up run after a live process resumes from suspend, per
  ADR-005's Alternatives Considered. (Not hand-simulated via a real
  hour-long sleep gap, per the task's own Tests guidance.)
- **[REQ-SB-07-US-01-AC-05]** PASS. With the server already having
  completed a capture run at `15:08:15Z` (well under an hour old), stopped
  the process cleanly (`Stop-Process` on the uvicorn reloader + worker +
  launcher PIDs) and restarted it fresh
  (`.venv\Scripts\python.exe -m uvicorn app.main:app` from `src/backend`).
  `.second-brain/last_capture_run.json`'s `finished_at` updated again to
  `2026-08-10T15:09:49Z` — ~94s after the previous run — proving the
  app-start trigger is unconditional and does not check "how recently did
  the last run finish" before firing.

Stopped the server cleanly after the AC-05 restart and confirmed via
`Get-Process python` that no stray uvicorn/python processes remained.

gate: clear 2026-08-10 — no new triggers fired during this coder pass
itself (the parent story's `gate: flagged` for ADR-005 was already
resolved by operator review before `/implement-sprint` started, per the
story's Notes); no material assumption beyond what ADR-005 and the task's
own code block already dictated, no contradictory inputs, no new
ADR/ESCALATIONS activity, no unanticipated file, all four locked ACs
touched by this task verified successfully.
