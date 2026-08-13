---
id: REQ-SB-11-US-01-T03
title: New app/api/agent_activity_router.py — GET /agent-activity
parent_story: REQ-SB-11-US-01
requirement_id: REQ-SB-11
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-11-US-01-T02]
sprint: "SPRINT-027"
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-11-US-01-T03 — New `app/api/agent_activity_router.py`

## Parent Story

- Story: [[REQ-SB-11-US-01]] — `../UserStories/REQ-SB-11-US-01-agent-activity-and-error-observability.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-11 *Agent Activity & Error Observability*

---

## Objective

Expose `T02`'s `agent_activity.get_agent_activity()` over HTTP as `GET
/agent-activity`, and register the new router in `app/main.py`.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed `app/business/agent_activity.py`.
- `app/main.py` registers `health_check_router`, `email_poc_router`,
  `my_day_router`, `agents_router`, `sections_router`, `providers_router`,
  `skills_router`, `vault_index_router`, `system_health_router` (and any
  others landed by concurrent stories).

**After / Outputs:**
- `app/api/agent_activity_router.py` exists with `GET /agent-activity`.
- `app/main.py` additionally registers `agent_activity_router`.

---

## Files to Modify

- `src/backend/app/api/agent_activity_router.py` (new):

  ```python
  from fastapi import APIRouter

  from app.business import agent_activity

  router = APIRouter(prefix="/agent-activity")


  @router.get("")
  def get_agent_activity() -> dict:
      # Recomputed fresh on every call -- agent_activity.get_agent_activity()
      # has no caching of its own (Scenario 7).
      return agent_activity.get_agent_activity()
  ```

- `src/backend/app/main.py` — add the new router registration:

  ```python
  from app.api.agent_activity_router import router as agent_activity_router
  ...
  app.include_router(agent_activity_router)
  ```

  (Alongside the existing registrations — keep the diff additive, do not
  reorder existing ones.)

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (`ADR-003`) — this router calls `agent_activity.py` only, no direct
  `agent_registry`/`vault_writer`/`outlook_com` reach-around.
- Do not reorder or otherwise change any existing router registration in
  `app/main.py`.
- No query parameters, no caching headers — a plain `GET` returning the
  freshly-recomputed payload every time.

---

## Tests

<!-- No locked AC of its own -- this router's response is genuinely
user-observable only once T04 renders it on a real page. Non-AC smoke
check here, mirroring REQ-SB-31-US-01-T03's own identical split. -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; issue a real
HTTP request via the browser or `Invoke-RestMethod`):

1. Non-AC smoke check: `GET http://127.0.0.1:8001/agent-activity`.
   Confirm the response has `activity_log` (an array, each entry with
   `agent_id`/`agent_name`/`kind`/`text`/`timestamp`, `kind` restricted to
   `"run_event"`/`"run_error"`) matching
   `agent_activity.get_agent_activity()`'s own live output, and
   `outlook_channel` (`{"reachable", "detail"}`) matching
   `outlook_com.check_reachable()`'s own live output.
2. Non-AC smoke check: temporarily close Outlook desktop (or otherwise
   make it unreachable), re-`GET /agent-activity`. Confirm
   `outlook_channel.reachable: false` with a real `detail` message.
   Restart Outlook afterward and confirm it flips back to `true` on the
   very next call — no caching.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `GET /agent-activity` returns `agent_activity.get_agent_activity()`'s
      payload verbatim
- [x] `agent_activity_router` registered in `app/main.py` without changing
      any existing router's behavior
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend page/component that calls this endpoint — `T04`.
- The `email_classification.py` honest-failure-recording fix — `T01`, no
  dependency either way.

---

## Context / Notes

This is a straight `ADR-003`-layered addition, the same shape as
`system_health_router.py`/`my_day_router.py`/`agents_router.py` — no new
dependency, no new middleware.

---

## Implementation Log

**Built 2026-08-13** exactly per the task's own sample. `app/main.py` had
drifted from the task's own "Before" sample by build time (a concurrent
sibling session's own `vault_search_router` addition landed mid-session)
— composed the new `agent_activity_router` import/registration around the
REAL current file, additive only, no existing registration reordered or
touched, matching this project's own established "compose around the
real current file" pattern.

**Manual verification — real HTTP round trip against the real backend
(`uvicorn app.main:app --port 8001`), no mocks:**

1. `GET http://127.0.0.1:8001/agent-activity` returned a real payload
   with `activity_log` (array, each entry `agent_id`/`agent_name`/`kind`/
   `text`/`timestamp`, `kind` restricted to `"run_event"`/`"run_error"`)
   matching `agent_activity.get_agent_activity()`'s own live output
   verbatim, and `outlook_channel` (`{"reachable": true, "detail": null}`
   with Outlook reachable) matching `outlook_com.check_reachable()`'s own
   live output. PASS.
2. Re-`GET /agent-activity` after inducing a real Outlook-unreachable
   state (via the same in-process-monkeypatch technique used for `T02`'s
   own equivalent check, since physically closing Outlook auto-relaunches
   it on this machine) confirmed `outlook_channel.reachable: false` with
   a real `detail` message, then flipped back to `true` on the very next
   call with the monkeypatch reverted — no caching. PASS.

`gate: clear` 2026-08-13 — no MUST-FLAG trigger fired: the real-file
composition around a sibling session's concurrent `main.py` change is a
purely additive reconciliation, not a deviation from any locked
Constraint (no existing registration reordered/touched).
