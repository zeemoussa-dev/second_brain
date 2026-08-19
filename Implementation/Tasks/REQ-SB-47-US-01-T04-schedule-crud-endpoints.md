---
id: REQ-SB-47-US-01-T04
title: New agent_schedules_router.py — GET/POST/PATCH/DELETE schedule CRUD
parent_story: REQ-SB-47-US-01
requirement_id: REQ-SB-47
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-47-US-01-T02, REQ-SB-47-US-01-T03]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-47-US-01-T04 — New `agent_schedules_router.py` — schedule CRUD

## Parent Story

- Story: [[REQ-SB-47-US-01]] — `../UserStories/REQ-SB-47-US-01-per-agent-scheduler-and-shared-serialization.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-47 *Per-Agent Scheduler* (merges REQ-SB-45)

---

## Objective

Add the new API surface `app/api/agent_schedules_router.py`,
`APIRouter(prefix="/agents/{agent_id}/schedules")`, exposing `GET` (list),
`POST` (create), `PATCH /{capability_id}` (edit), and `DELETE
/{capability_id}` (remove) as thin HTTP wrappers over `T02`'s
`agent_schedule_registry` functions, registered in `app/main.py`. The
run-now endpoint on this same router is `T05`, added after this task.

---

## Starting State → End State

**Before / Inputs:**
- No `agent_schedules_router.py` exists; no schedule-related route exists anywhere.
- `T02`'s `agent_schedule_registry.list_schedules`/`create_or_update_schedule`/`remove_schedule` exist and are importable.
- `T03` has wired the live scheduler into `agent_schedule_registry`, so a live create/edit/remove through this router actually mutates the running `AsyncIOScheduler`'s own job registry (`AC-04`/`AC-05`'s "no restart required").
- `pending_approvals_router.py` (read for precedent) is the real, shipped "new dedicated router for a new dedicated concern" shape this task mirrors: a thin `APIRouter`, `HTTPException(status_code=404, ...)` for an unknown resource, a `400` for a refused create.

**After / Outputs:**
- `GET /agents/{agent_id}/schedules` — returns `agent_schedule_registry.list_schedules(agent_id)`; `404` if `agent_id` is unknown (mirrors `skills_router.py::_require_known_agent`).
- `POST /agents/{agent_id}/schedules` — body `{"capability_id": str, "interval_value": int, "interval_unit": "minutes" | "hours"}`; `400` with a clear message on `T02`'s Scenario-9 refusal (ungranted or non-mutating capability); `201`/`200` with the created schedule record otherwise.
- `PATCH /agents/{agent_id}/schedules/{capability_id}` — body carries the new `interval_value`/`interval_unit`, or a new `new_capability_id` to retarget the schedule; calls `create_or_update_schedule` under the resolved target key; `404` if no schedule exists for the given `(agent_id, capability_id)` pair.
- `DELETE /agents/{agent_id}/schedules/{capability_id}` — calls `remove_schedule`; `404` if none existed.
- `app/main.py` — new import + `app.include_router(agent_schedules_router)`, alongside the existing router list.

---

## Files to Modify

- `src/backend/app/api/agent_schedules_router.py` — new file.
- `src/backend/app/main.py` — add the import (alongside the existing `app.api.*_router` import block, ~lines 6-20) and `app.include_router(...)` call (alongside the existing block, ~lines 61-73).

---

## Constraints

- Inherits from parent story.
- Mirror `pending_approvals_router.py`'s/`skills_router.py`'s existing thin-router shape — no business logic in this file; every real decision (refusal, persistence, live-job mutation) stays in `agent_schedule_registry.py` (`T02`).
- `404` for an unknown `agent_id` (reuse `agent_registry.get_agent(agent_id) is None` the same way `skills_router.py::_require_known_agent` already does) BEFORE any `agent_schedule_registry` call.
- Do not add the run-now endpoint in this task — that is `T05`, added to this same file afterward.
- Do not touch `skills_router.py`, `agents_router.py`, or any other existing router.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-47-US-01-AC-01, partial] Start the backend (`uvicorn app.main:app --reload`, `src/backend`). `POST /agents/email-capture/schedules` with `{"capability_id": "run_capture_now", "interval_value": 2, "interval_unit": "hours"}` — expect a success response echoing the created schedule. `GET /agents/email-capture/schedules` and confirm it lists this schedule as active, showing `capability_id` and the configured interval.
2. [REQ-SB-47-US-01-AC-04, partial] `PATCH /agents/email-capture/schedules/run_capture_now` with `{"interval_value": 45, "interval_unit": "minutes"}` — expect success. `GET /agents/email-capture/schedules` again and confirm the SAME entry now reads the new interval (not a second, duplicate entry).
3. [REQ-SB-47-US-01-AC-05, partial] `DELETE /agents/email-capture/schedules/run_capture_now` — expect success. `GET /agents/email-capture/schedules` again and confirm it is no longer listed.
4. [REQ-SB-47-US-01-AC-09, partial] `POST /agents/vault-qa/schedules` with `{"capability_id": "ask_question", "interval_value": 1, "interval_unit": "hours"}` (granted but non-mutating) — expect `400` with a clear, honest message. `POST /agents/vault-qa/schedules` with `{"capability_id": "run_capture_now", ...}` (not granted to this agent at all) — expect the same `400` refusal shape. Confirm `GET /agents/vault-qa/schedules` shows no schedule was created either time.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `GET`/`POST`/`PATCH`/`DELETE` all live at `/agents/{agent_id}/schedules[...]`, registered in `app/main.py`.
- [ ] `POST`/`PATCH` round-trip correctly through `GET` — create, edit-in-place (no duplication), and refusal all observable via real HTTP.
- [ ] `DELETE` round-trips through `GET` — removal observable via real HTTP.
- [ ] Unknown `agent_id` → `404` on every route; Scenario-9 refusal → `400` with a clear message, never a 500 or a fabricated success.
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint.
- [ ] `CHANGELOG.md` entry appended.

---

## Out of Scope

- The run-now endpoint (`T05`).
- Any frontend change (`T06`).
- Run history — reuses the existing `GET /agents/{agent_id}/history` (`REQ-SB-11`, unchanged, no new endpoint needed).

---

## Context / Notes

Real files to compose against: `src/backend/app/api/pending_approvals_router.py` and `src/backend/app/api/skills_router.py` (thin-router precedent), `src/backend/app/main.py` (router-registration precedent, ~lines 6-20 and 61-73). Full reasoning: `ADR-037` point 7.

---

## Implementation Log

**Built:** `src/backend/app/api/agent_schedules_router.py` (new) —
`APIRouter(prefix="/agents/{agent_id}/schedules")`: `GET` (list), `POST`
(create, catches `agent_schedule_registry.ScheduleRefusedError` → `400` with
`.reason`), `PATCH /{capability_id}` (edit — `404` if no schedule exists for
the pair; supports an optional `new_capability_id` to retarget, removing the
prior key's own record so retargeting replaces in place, not duplicates),
`DELETE /{capability_id}` (`404` if none existed). `404` for an unknown
`agent_id` on every route, mirroring `skills_router.py::_require_known_agent`.
`src/backend/app/main.py` — added the import + `app.include_router(...)`,
alongside the existing block.

**Verification (2026-08-14, real HTTP, `src/backend`,
`.venv\Scripts\uvicorn.exe app.main:app --port 8001`):**

- `[AC-01, partial]` `POST /agents/email-capture/schedules`
  `{"capability_id": "run_capture_now", "interval_value": 2,
  "interval_unit": "hours"}` → `200` with the created record. `GET
  /agents/email-capture/schedules` listed it, correct capability + interval.
  **PASS.**
- `[AC-04, partial]` `PATCH .../run_capture_now` `{"interval_value": 45,
  "interval_unit": "minutes"}` → success; `GET` showed the SAME entry
  updated in place (still exactly one), new interval. **PASS.**
- `[AC-05, partial]` `DELETE .../run_capture_now` → success; `GET` showed
  it removed. **PASS.**
- `[AC-09, partial]` `POST /agents/vault-qa/schedules` with `ask_question`
  (granted, non-mutating) → `400` with a clear message. Same for
  `run_capture_now` (ungranted for `vault-qa`) → `400`, same shape. `GET
  /agents/vault-qa/schedules` confirmed empty both times. **PASS.**
- `404` confirmed for an unknown `agent_id`
  (`GET /agents/nonexistent-agent-xyz/schedules` → `404`). **PASS.**

No deviations. `email_classification`/`skills_router.py`/`agents_router.py`
untouched, per this task's own scope.

gate: clear 2026-08-14 — no triggers fired (requirement finalised, no ADR
change, all tagged manual steps verified live and passing).
