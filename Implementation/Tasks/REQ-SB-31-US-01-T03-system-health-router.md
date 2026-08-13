---
id: REQ-SB-31-US-01-T03
title: New app/api/system_health_router.py — GET /system-health
parent_story: REQ-SB-31-US-01
requirement_id: REQ-SB-31
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-31-US-01-T02]
sprint: "SPRINT-019"
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-31-US-01-T03 — New `app/api/system_health_router.py`

## Parent Story

- Story: [[REQ-SB-31-US-01]] — `../UserStories/REQ-SB-31-US-01-system-health-view.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-31 *System Health View*

---

## Objective

Expose `T02`'s `system_health.get_system_health()` over HTTP as `GET
/system-health`, and register the new router in `app/main.py`.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed `app/business/system_health.py`.
- `app/main.py` registers `health_check_router`, `email_poc_router`,
  `my_day_router`, `agents_router`, `sections_router`, `providers_router`,
  `skills_router`.

**After / Outputs:**
- `app/api/system_health_router.py` exists with `GET /system-health`.
- `app/main.py` additionally registers `system_health_router`.

---

## Files to Modify

- `src/backend/app/api/system_health_router.py` (new):
  ```python
  from fastapi import APIRouter

  from app.business import system_health

  router = APIRouter(prefix="/system-health")


  @router.get("")
  def get_system_health() -> dict:
      # Recomputed fresh on every call -- system_health.get_system_health()
      # has no caching of its own (Scenario 7).
      return system_health.get_system_health()
  ```

- `src/backend/app/main.py` — add the new router registration:
  ```python
  from app.api.system_health_router import router as system_health_router
  ...
  app.include_router(system_health_router)
  ```
  (Alongside the existing registrations — keep the diff additive, do not
  reorder existing ones.)

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (`ADR-003`) — this router calls `system_health.py` only, no direct
  `provider_registry`/`agent_registry`/`vault_writer` reach-around.
- Do not reorder or otherwise change any existing router registration in
  `app/main.py`.
- No query parameters, no caching headers — a plain `GET` returning the
  freshly-recomputed payload every time.

---

## Tests

<!-- No locked AC of its own -- this router's response is genuinely
user-observable only once T04 renders it on a real page. Non-AC smoke
check here, mirroring REQ-SB-19-US-01-T03's / REQ-SB-12-US-02-T03's own
identical split. -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; issue a real
HTTP request via the browser or `Invoke-RestMethod`):

1. Non-AC smoke check: `GET http://127.0.0.1:8001/system-health`. Confirm
   the response has `mcp.reachable: true`, a `providers` array matching
   `GET /providers`'s own live output plus each entry's additional
   `agent_names` (resolved display names, matching `agent_ids`),
   `disabled_agents` (empty for the real vault's default all-Compass
   assignment), and `last_capture_run` matching the real
   `.second-brain/last_capture_run.json` contents (or `null` if that file
   doesn't exist yet).
2. Non-AC smoke check: temporarily reassign one agent to a Provider with
   no real client (same throwaway-Provider pattern established in earlier
   stories' own verification), re-`GET /system-health`. Confirm that
   agent now appears in `disabled_agents`. Revert the reassignment
   afterward and confirm it disappears again on the next `GET` (proving
   no caching — Scenario 7).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `GET /system-health` returns `system_health.get_system_health()`'s
      payload verbatim
- [x] `system_health_router` registered in `app/main.py` without changing
      any existing router's behavior
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend page/component that calls this endpoint — `T04`.
- The `run_agent_conversation` crash-gap fix — `T01`, no dependency
  either way.

---

## Context / Notes

This is a straight `ADR-003`-layered addition, the same shape as
`my_day_router.py`/`agents_router.py`/`providers_router.py` — no new
dependency, no new middleware.

---

## Implementation Log

**Build (2026-08-12).** `app/api/system_health_router.py` created exactly
per the task's own literal code sample (`GET ""` under the
`/system-health` prefix, returning `system_health.get_system_health()`
verbatim). `app/main.py` gained the import and one additive
`app.include_router(system_health_router)` line, alongside — not
reordering — every existing registration.

**Verification — non-AC smoke checks (2026-08-12), against the real
running backend on port `8001`:**

1. `GET http://127.0.0.1:8001/system-health` returned `mcp.reachable:
   true`, a `providers` array matching `GET /providers`'s own live output
   plus each entry's `agent_names`, `disabled_agents: []` (real vault
   default all-Compass), and `last_capture_run` matching the real
   `.second-brain/last_capture_run.json` contents byte-for-byte. **PASS.**
   (Consolidated with `T02`'s own identical smoke check 1 — same live
   call, one real HTTP round-trip, evidence shared across both tasks per
   this project's own "consolidate a real-side-effect verification step
   across sibling tasks" pattern, `Implementation/MEMORY.md`.)
2. Reassigned `people-producer` to a throwaway no-real-client Provider
   (same live reassignment `T02`'s own step 3 used), re-`GET
   /system-health` — confirmed `people-producer` now appears in
   `disabled_agents`. Reverted the reassignment and deleted the throwaway
   Provider, re-`GET /system-health` on the very next call — confirmed it
   disappears again with no caching (Scenario 7). **PASS.**

Full transcripts (request/response bodies) are in this sprint's own live
verification session.

`gate: clear` 2026-08-12 — this task's own file (`system_health_router.py`)
was built and verified exactly as spec'd, no correction needed here (the
one live-discovered correction belongs to `T02`'s own file,
`system_health.py`, logged there). No MUST-FLAG trigger fired. `status:
Done`.
