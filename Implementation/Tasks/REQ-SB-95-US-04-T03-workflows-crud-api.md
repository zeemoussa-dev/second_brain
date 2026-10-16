---
id: REQ-SB-95-US-04-T03
title: Workflows CRUD API — app/api/workflows_router.py
parent_story: REQ-SB-95-US-04
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-04-T02]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-04-T03 — Workflows CRUD API

## Parent Story

- Story: [[REQ-SB-95-US-04]] — `../UserStories/REQ-SB-95-US-04-workflow-seventh-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Expose the Workflow catalogue over HTTP on one flat router, surfacing the
Manager's step-validation refusals intact.

---

## Starting State → End State

**Before / Inputs:**

- `WorkflowManager` is complete (`T01`/`T02`) and reachable only from Python.
- `app/api/actions_router.py` (`REQ-SB-95-US-02-T03`) is the immediate
  convention sibling; `pipelines_router.py` and `index_router.py` are the
  established flat-router shape.

**After / Outputs:**

- `app/api/workflows_router.py` — `GET /workflows`,
  `GET /workflows/{workflow_id}`, `POST /workflows`,
  `PUT /workflows/{workflow_id}`, `DELETE /workflows/{workflow_id}`.
- A refused save returns a 4xx carrying the Manager's own message naming the
  step and the unknown action id — never flattened to a generic error.
- Registered in `app/main.py` alongside the existing routers.

---

## Files to Modify

- `src/backend/app/api/workflows_router.py` (new)
- `src/backend/app/main.py` (register the router)
- `src/backend/tests/test_workflows_api.py` (new)

---

## Constraints

- Inherits from parent story.
- No business rules in the router — order, validation and the reverse lookup
  all live in the Managers.
- The run routes (`start`, `next step`, `report outcome`) are **not** this task
  — they land in `T05`. Do not stub them.

---

## Tests

**Automated tests** — `src/backend/tests/test_workflows_api.py`, run with
`pytest tests/test_workflows_api.py` from `src/backend`, over
`httpx.ASGITransport(app=app)`.

1. `[REQ-SB-95-US-04-AC-01]` `POST /workflows` with a request kind and three
   ordered steps against real catalogued Actions; assert success, then
   `GET /workflows/{id}` returns the same steps in the same order with the same
   per-step confirmation flags and the same report definition, and
   `GET /workflows` lists it.
2. `[REQ-SB-95-US-04-AC-02]` `POST /workflows` with a step naming an unknown
   action id; assert a 4xx whose body names the step and the unknown id, and
   that `GET /workflows` does not list it.
3. `[REQ-SB-95-US-04-AC-02]` `PUT /workflows/{id}` pointing a step at an unknown
   action id; assert the refusal and that `GET` still returns the unmodified
   Workflow.

**Manual verification steps:**

1. `[REQ-SB-95-US-04-AC-01]` With the backend running, create a real Workflow
   over HTTP and re-read it; confirm order and flags survive a real round trip
   against the real data path.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Flat `workflows_router.py` with full CRUD, registered in `app/main.py`
- [ ] Manager refusal messages reach the client intact
- [ ] Step order preserved through the API round trip
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Run routes — `T05`. Inventory/export/import — `T04`. Screen — `T07`.

---

## Context / Notes

`architecture.md` → **§Workflow — the Seventh Artifact Kind**. Same flat,
single-purpose router convention the architecture names for `actions_router.py`.

---

## Implementation Log

_(Filled in by the coder.)_
