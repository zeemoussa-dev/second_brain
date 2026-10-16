---
id: REQ-SB-95-US-02-T03
title: Actions CRUD API — app/api/actions_router.py
parent_story: REQ-SB-95-US-02
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-02-T02]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-02-T03 — Actions CRUD API

## Parent Story

- Story: [[REQ-SB-95-US-02]] — `../UserStories/REQ-SB-95-US-02-action-sixth-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Expose the Action catalogue over HTTP — list, read, create, update, delete —
on one flat, single-purpose router, surfacing the Manager's refusals and the
per-Action resolution status honestly.

---

## Starting State → End State

**Before / Inputs:**

- `ActionManager` is complete (`T01`/`T02`) and reachable only from Python.
- `app/api/skills_router.py` and `app/api/index_router.py` are the flat,
  single-surface router convention; `app/api/` has no `actions_router.py`.

**After / Outputs:**

- `app/api/actions_router.py` — `GET /actions`, `GET /actions/{action_id}`,
  `POST /actions`, `PUT /actions/{action_id}`, `DELETE /actions/{action_id}`.
- The list response carries each Action's id, description, implementation kind
  and its live `resolves` | `broken` status with the named cause.
- A refused save (non-resolving implementation, or not exactly one) returns a
  4xx whose body carries the Manager's own message naming the cause — the API
  never rewrites or flattens it to a generic error.
- The router is registered in `app/main.py` alongside the existing routers.

---

## Files to Modify

- `src/backend/app/api/actions_router.py` (new)
- `src/backend/app/main.py` (register the router — one line, same shape as the existing registrations)
- `src/backend/tests/test_actions_api.py` (new)

---

## Constraints

- Inherits from parent story.
- The router holds no business rules: cardinality, resolution and the broken
  status all come from `ActionManager`. The API layer composes, it does not
  decide.
- `POST /actions/{action_id}/call` is **not** this task — it lands on this same
  router in `REQ-SB-95-US-03-T02`. Leave room for it; do not stub it.
- Deleting an Action gains a Workflow reverse-lookup guard in
  `REQ-SB-95-US-04-T02`; this task's delete is unguarded and that is correct for
  now, because no Workflow kind exists yet.

---

## Tests

**Automated tests** — `src/backend/tests/test_actions_api.py`, run with
`pytest tests/test_actions_api.py` from `src/backend`, driving the real app
object through `httpx.ASGITransport(app=app)` (this project's established
technique) with the Action data access monkeypatched.

1. `[REQ-SB-95-US-02-AC-01]` `POST /actions` with a complete, resolvable Action;
   assert `201`/`200`, then `GET /actions` lists it with its id, description and
   implementation kind, and `GET /actions/{id}` returns exactly the inputs,
   required flags, `allowed_callers` and confirmation flag that were posted.
2. `[REQ-SB-95-US-02-AC-02]` `POST /actions` naming an implementation that does
   not resolve; assert a 4xx whose body names what did not resolve, and that a
   following `GET /actions` does not list it.
3. `[REQ-SB-95-US-02-AC-03]` `POST /actions` with zero implementations, then
   with two; assert both are refused with the exactly-one message, and that a
   third post naming exactly one succeeds.
4. `[REQ-SB-95-US-02-AC-07]` With a saved Action whose implementation has since
   stopped resolving, assert `GET /actions` returns it with its `broken` status
   and the named cause rather than omitting it or failing the whole list.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Flat `actions_router.py` with full CRUD, registered in `app/main.py`
- [ ] Manager refusal messages reach the client intact
- [ ] List response carries the live resolution status per Action
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The call route and the invocation gate — `REQ-SB-95-US-03-T02`.
- Plugin-contributed Actions in the list — `T05` (they arrive through
  `ActionManager.get_all()`, so this router needs no change for them).
- Any screen — `T06`.

---

## Context / Notes

`architecture.md` → **§Action Catalogue — the Sixth Artifact Kind**: "`app/api/
actions_router.py` — flat, single-purpose, same convention as
`skills_router.py`/`index_router.py`. CRUD plus the call route below."

---

## Implementation Log

_(Filled in by the coder.)_
