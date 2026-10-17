---
id: REQ-SB-95-US-02-T03
title: Actions CRUD API — app/api/actions_router.py
parent_story: REQ-SB-95-US-02
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "Four scope-internal judgement calls, all recorded in the Implementation Log and none of them blocking: a Manager refusal is 409 (not 422, which FastAPI owns for its own list-shaped validation detail); POST returns 200 (no route in app/api returns 201); the tests use fastapi.testclient.TestClient rather than the httpx.ASGITransport this task names, because no test in this repo uses ASGITransport and twelve use TestClient; and POST onto an existing id overwrites, which is ActionManager.create's own behaviour and was deliberately not guarded here. Spot-check only — no REVIEW-QUEUE entry was added, per that file's standing 2026-09-06 instruction not to refill it with scope-internal judgement-call spot-checks."
phase: P2
depends_on: [REQ-SB-95-US-02-T02]
created: 2026-10-16
updated: 2026-10-17
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

- [x] Flat `actions_router.py` with full CRUD, registered in `app/main.py`
- [x] Manager refusal messages reach the client intact
- [x] List response carries the live resolution status per Action
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

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

**Coder, 2026-10-17 — Done. Automated verification.**

Suite baseline before the first edit: **448 passed** (`.venv/Scripts/python.exe -m
pytest -q` from `src/backend`, at commit `2d7a91e`). Final: **457 passed** — the
same 448 plus this task's 9. No pre-existing failure, no regression. (The 448
baseline is 6 above the 442 quoted when this task was handed over: another
session's untracked `tests/test_screen_build_lock.py` is in this checkout.)

### Locked ACs — observed outcomes

Every AC below is an AC-tagged automated test in
`src/backend/tests/test_actions_api.py`, driven over HTTP against the real
`app.main.app` object (so each one also proves the router is registered, not
merely importable). `pytest tests/test_actions_api.py -q` → **9 passed**.

| AC-ID | Test(s) | Observed |
|---|---|---|
| `REQ-SB-95-US-02-AC-01` | `test_a_complete_action_is_saved_listed_and_reopens_as_saved`, `test_an_edit_round_trips_and_an_unknown_id_is_404`, `test_deleting_removes_it_from_the_catalogue` | PASS. `POST /actions` → 200; `GET /actions` lists it with id, description and `implementation_kind`; `GET /actions/{id}` returns both inputs with their `required` flags intact (`[True, False]`), both `allowed_callers` and `needs_confirmation: true` exactly as posted. Edit round-trips, unknown id is 404 on both GET and PUT, delete removes it from the catalogue. |
| `REQ-SB-95-US-02-AC-02` | `test_an_implementation_that_does_not_resolve_is_refused_and_not_listed`, `test_each_implementation_kind_is_refused_on_its_own_terms`, `test_an_edit_onto_an_unresolvable_implementation_is_refused` | PASS. An undeployed Skill is refused 409 with the Manager's own sentence — `detail` contains `vault-search` and `not deployed`; a following `GET /actions` returns `[]` and the store is empty. A bad `http` path and an unregistered `ui` feature key are each refused naming what the operator typed. An edit onto an unresolvable implementation is refused and the stored definition is byte-identical afterwards. |
| `REQ-SB-95-US-02-AC-03` | `test_zero_and_two_implementations_are_refused_and_exactly_one_saves`, `test_putting_a_get_body_straight_back_is_refused_loudly` | PASS. Zero implementations and two are both refused 409 carrying `exactly one implementation` (the two-case names them: `skill, ui`), nothing written; a third POST naming exactly one succeeds and is listed. The stored definition holds only the kind it named — no present-and-null kinds. |
| `REQ-SB-95-US-02-AC-07` | `test_an_action_that_stopped_resolving_is_listed_as_broken` | PASS. Two resolving Actions both list `resolves`; after the Skill is undeployed, `GET /actions` still lists the broken one, with `status: broken`, `implementation_kind: skill`, its description intact, and a reason naming the skill and `not deployed`. The healthy Action beside it is unaffected and the whole list does not fail. `GET /actions/{id}` on the broken one is still 200. |

**Live check on the running install** (the backend was **restarted** with
`tools\backend.cmd restart` to do it — `--reload` had NOT picked the new router
up, `GET /actions` → 404 before the restart, which is the known unreliability on
this host): after restart `GET /actions` → `200 []`, and
`POST /actions {"id":"probe-only","description":"x"}` →
`{"detail":"an Action has exactly one implementation -- one of skill, http or
ui, never zero and never two; this one names none"}` with the catalogue still
`[]` afterwards. The Manager's message reaches a real HTTP client verbatim.

### Judgement calls made inside scope (the `gate: flagged` reason)

1. **409 for a Manager refusal, not 422.** FastAPI already owns 422 for its own
   request-validation errors, whose `detail` is a *list* of error objects. Sending
   a Manager refusal under the same code would force `T06`'s screen to tell two
   `detail` shapes apart before it could show the operator anything. 409 is also
   what `sections_router.py` and `blueprints_router.py` already return when a
   Manager refuses a write. `detail` is the Manager's message as a plain string.
2. **POST returns 200, not 201.** The task permitted either. No route anywhere in
   `app/api/` returns 201 (checked), so 200 keeps one convention across the API.
3. **Tests use `fastapi.testclient.TestClient`, not `httpx.ASGITransport`.** This
   task calls ASGITransport "this project's established technique"; it is not —
   **no** test in `src/backend/tests/` uses it, and **twelve** use `TestClient`
   (`test_blueprints_api.py` et al). Both drive the real app object in-process;
   the established one was used.
4. **POST onto an existing id overwrites it** — `ActionManager.create`'s own
   behaviour, left alone. A duplicate-id guard would be a business rule living in
   the API layer, which this task's Constraints forbid ("the router holds no
   business rules"). Noted rather than fixed: it belongs to whoever owns the
   Manager, and no AC asks for it.

No `ESCALATIONS.md` entry and no `REVIEW-QUEUE.md` entry: nothing out of scope
occurred, nothing is blocked, and `REVIEW-QUEUE.md`'s own standing 2026-09-06
instruction names "scope-internal judgement-call spot-checks" as the noise that
filled it unread. The `gate: flagged` on this task is the spot-check surface.

### Two notes `T06` needs (surface audited in both directions)

- **`implementation` has a different read shape and write shape, and the editor
  must map between them.** A write sends the kind as a KEY —
  `{"implementation": {"skill": {"skill_id": "..."}}}` — because which keys are
  present is what "exactly one" is counted over, and that is also what
  `Action.json` stores. A read returns the `Action` entity, whose implementation
  is FLAT — `{"kind": "skill", "skill_id": "...", "method": "", "path": "",
  "feature_key": ""}`. The entity shape was kept on the read because every other
  detail route here returns the real dataclass. `GET`-then-`PUT` of the same body
  is therefore refused by the exactly-one rule — **loudly, never silently** — and
  that is pinned by its own test so `T06` meets it as a contract rather than as a
  surprise.
- **Three fields are read-only and are not accepted on a write:** `id` after
  creation, `created_at` and `updated_at` (the Manager owns both timestamps). The
  editor must render them as facts, never as inputs — everything else the read
  returns (`description`, `inputs`, `allowed_callers`, `needs_confirmation`,
  `implementation`) the write path does accept, so there are no other one-way
  fields to mislead the operator.

`GET /actions` composes `get_all()` with `resolution_report()`. An Action present
in the first and absent from the second (only reachable by a write landing between
the two reads) is listed as `broken`, never as healthy and never dropped — an
unchecked entry shown as fine is the exact failure `ADR-032` exists to prevent.

`POST /actions/{action_id}/call` was left out entirely rather than stubbed, as the
Constraints require; `REQ-SB-95-US-03-T02` adds it to this router.
