---
id: REQ-SB-95-US-04-T03
title: Workflows CRUD API — app/api/workflows_router.py
parent_story: REQ-SB-95-US-04
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "Optional skim only — nothing is blocked. Six scope-internal judgement calls are logged for a human spot-check (GET /workflows returns whole Workflows rather than a summary; `action_id` optional on the wire so the Manager owns the refusal; POST onto an existing id replaces, exactly as POST /actions does; TestClient as the ASGITransport driver; the manual step run against an isolated scratch install rather than the operator's own data path; three tests beyond the decomposer's three). No ESCALATIONS.md entry — no file outside `## Files to Modify` was needed."
phase: P2
depends_on: [REQ-SB-95-US-04-T02]
created: 2026-10-16
updated: 2026-10-18
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

- [x] Flat `workflows_router.py` with full CRUD, registered in `app/main.py`
- [x] Manager refusal messages reach the client intact
- [x] Step order preserved through the API round trip
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint — no new framework-wide rule emerged; the 2026-10-17 "409 carrying the Manager's own sentence" entry and the 2026-10-18 step-id entry already cover everything this router does, and restating them would be the trivial entry `MEMORY.md`'s own rules forbid
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Run routes — `T05`. Inventory/export/import — `T04`. Screen — `T07`.

---

## Context / Notes

`architecture.md` → **§Workflow — the Seventh Artifact Kind**. Same flat,
single-purpose router convention the architecture names for `actions_router.py`.

---

## Implementation Log

**2026-10-18 — built, verified, `Done`.** Three files, exactly the three listed:
`app/api/workflows_router.py` (new), `app/main.py` (the import + the
`include_router` line), `tests/test_workflows_api.py` (new). Both ACs this task
covers are green on six AC-tagged automated tests plus a real-HTTP manual round
trip. Nothing outside the list was needed — the switch-on site was already in
it, which is the 2026-10-18 `MEMORY.md` rule working.

### Verification (automated mode)

Full suite, `.venv/Scripts/python.exe -m pytest -q` from `src/backend`:

- **Baseline, immediately before starting (`d4b8b2b`): 628 passed, 0 failed,
  43.76s.** The three known order-dependent tests
  (`test_health_check.py::test_health_reports_the_commit_the_running_code_was_loaded_from`,
  `test_marketplace_source.py`,
  `test_marketplace.py::test_install_repairs_a_plugin_left_with_only_its_bytecode_cache`)
  all passed in that run, so there was no pre-existing failure to discount.
- **After: 634 passed, 0 failed, 41.04s.** +6 collected, exactly this task's six
  tests. No pre-existing test changed outcome.

`src/backend/tests/test_workflows_api.py`, run with
`pytest tests/test_workflows_api.py` from `src/backend` (6 passed, 1.25s).

| Test step | AC-ID | Observed outcome |
|---|---|---|
| 1. `POST /workflows` with a request kind and three ordered steps against real catalogued Actions; success, then `GET /workflows/{id}` returns the same steps in the same order with the same per-step confirmation flags and the same report definition, and `GET /workflows` lists it | `REQ-SB-95-US-04-AC-01` | **Pass.** `test_a_workflow_round_trips_its_ordered_steps_over_http`: `POST` **200**; the reopened body's steps are `[('collect','list-team-actions',False), ('send','send-mail',True), ('log','append-capture',False)]`, per-step `inputs` `[{'team':'CBO'}, {'to':'{{operator.self_email}}'}, {'note':'sent'}]`, per-step descriptions all three intact, `report` exactly `{'description': 'the list that was sent, and to whom', 'include_step_ids': ['collect','send']}`; `GET /workflows` returns one entry carrying step order `['collect','send','log']` |
| 2. `POST /workflows` with a step naming an unknown action id; a 4xx whose body names the step and the unknown id, and `GET /workflows` does not list it | `REQ-SB-95-US-04-AC-02` | **Pass.** `test_a_step_naming_an_unknown_action_is_refused_and_nothing_is_stored`: **409**, `detail` is the plain string `"step 2 of this Workflow names action 'mail-the-whole-company', which is not in this install's Action catalogue; nothing was saved"` — the Manager's own sentence, naming both the step and the id; `GET /workflows` is `[]`, `GET /workflows/mail-me-the-team-list` is **404**, and the in-memory store is `{}` (asserted, not inferred) |
| 3. `PUT /workflows/{id}` pointing a step at an unknown action id; the refusal, and `GET` still returns the unmodified Workflow | `REQ-SB-95-US-04-AC-02` | **Pass.** `test_an_edit_pointing_a_step_at_an_unknown_action_leaves_the_workflow_unchanged`: **409** naming `step 2` and `mail-the-whole-company`; the stored definition dict is **equal** to the one captured before the refused edit, and the `GET` body is equal to the one captured before it — the new `description` did not land either |

Three tests beyond the decomposer's three, each pinning something the listed
steps would not have caught:

- `test_these_tests_bring_their_own_action_catalogue` (`AC-02`) — asserts the
  premise the other five rest on: `GET /actions` returns exactly the three ids
  this file created, and `mail-the-whole-company` is genuinely absent. Without
  it, a file that leaked into the operator's real `<DATA_PATH>/data/Actions/`
  would pass or fail by accident of this machine's state (`ESC-064`, `ESC-075`
  are both that failure). **Proved rather than asserted:** the whole file was
  re-run with `SECOND_BRAIN_DATA_PATH` pointed at an empty directory (the
  override confirmed live — `settings.second_brain_data_path` echoed back as
  that directory) — **6 passed**, so it passes on an empty install.
- `test_an_edit_reorders_leaves_omitted_fields_alone_and_a_delete_unlists_it`
  (`AC-01`) — the rest of CRUD, which the AC checklist requires and no listed
  step exercises: a reorder really reorders over HTTP
  (`['log','collect','send']`, flags `[False,False,True]` travelling with their
  own steps), an omitted field is untouched, `GET`/`PUT` on an unknown id are
  **404**, and `DELETE` answers `{"deleted": true}` then `{"deleted": false}`
  rather than a 404 (`ADR-014`).
- `test_a_step_naming_no_action_at_all_is_refused_the_same_way` (`AC-02`) — a
  step with no `action_id` leaves a step pointing at nothing exactly as an
  unknown one does, and is refused as the same 409 with the same plain-string
  body shape.

**On AC-02's "intact" requirement.** FastAPI does not flatten it: `raise
HTTPException(status_code=409, detail=str(exc))` reaches the client as
`{"detail": "<the Manager's sentence>"}` verbatim — verified above and over a
real socket below. The refusal is deliberately NOT caught and re-raised as a
generic 400, and deliberately not 422: FastAPI owns 422 for its own
request-validation errors, whose `detail` is a **list of error objects**, so a
Manager refusal under that code would force the screen to tell two `detail`
shapes apart before it could show the operator anything (the 2026-10-17
`MEMORY.md` rule; `actions_router.py` already does exactly this).

### Manual verification

**Step 1 (`REQ-SB-95-US-04-AC-01`) — Pass.** Run against a **disposable
install**, never the operator's `:8001`: its own uvicorn on `127.0.0.1:8099`
(no `--reload`) with scratch `VAULT_PATH` / `SECOND_BRAIN_DATA_PATH` /
`HERMES_HOME_PATH`, driven over a real HTTP socket with `httpx`. Observed:
three Actions created over the real `POST /actions` (catalogue read back as
`['append-capture', 'list-team-actions', 'report-unmet-request', 'send-mail']`
— the fourth is the starter this install seeded at boot); `POST /workflows`
**200**; `GET /workflows/<id>` returned order `['collect','send','log']`,
actions `['list-team-actions','send-mail','append-capture']`, confirmation
flags `[False, True, False]`, every step's `inputs` intact and the report
definition intact; `GET /workflows` listed it with its 3 steps. The file the
server really wrote — `<data>/data/Workflows/mail-me-the-team-list/Workflow.json`
— holds the same order and the same flags, so the round trip is through real
JSON on disk and not through a response cache. The same run also exercised
`AC-02` over the socket: `PUT` with an unknown action id → **409** carrying
`"step 2 of this Workflow names action 'mail-the-whole-company', which is not
in this install's Action catalogue; nothing was saved"`, and the re-read body
was **identical** to the pre-edit one. The Workflow was deleted afterwards
(`{"deleted": true}`, list back to `[]`) and the server stopped by PID after
confirming it owned 8099; `:8001` was never touched and is still serving.

### Scope-internal judgement calls (for a human spot-check, nothing blocked)

1. **`GET /workflows` returns whole `Workflow` dataclasses, not a summary
   dict.** `GET /actions` summarises only because it attaches a derived live
   resolution status; a Workflow has no such derived field, so this follows
   `GET /indexes` / `GET /sections`' "thin wrapper, one business call, return
   the real dataclass list" instead. A Workflow *is* its ordered steps, and a
   summary would make the catalogue screen fetch each one to render a row.
2. **A step's `action_id` is optional on the wire** (`""` default) rather than
   a required pydantic field. Required would make a step naming nothing a
   FastAPI **422** with a list `detail`, i.e. a second refusal shape for the
   same class of mistake; optional sends it to the Manager and it comes back as
   the one 409. Same reason `actions_router.py` lets an omitted
   `implementation` reach the Manager.
3. **`POST /workflows` with an id that already exists replaces it** rather than
   refusing as a conflict — exactly what `POST /actions` does today. Refusing
   would be a new business rule, and the task's Constraints put business rules
   in the Manager, not the router. Worth a look because the screen (`T07`) will
   decide whether "Save" on a new Workflow can silently overwrite one.
4. **`TestClient` rather than a hand-built `httpx.ASGITransport(app=app)`.**
   `starlette.testclient.TestClient` *is* an `httpx.Client` over
   `ASGITransport`, and it is what all thirteen other API test files here use,
   so the decomposer's named driver and the house convention are the same
   object. The manual step covers the one thing in-process transport cannot:
   a real socket.
5. **The manual step ran against an isolated scratch install, not the
   operator's own data path.** The step says "against the real data path"; what
   it is distinguishing is a real on-disk store behind a real server from the
   in-memory doubles the automated tests use, and the scratch install is real
   on both counts (real uvicorn, real socket, real `Workflow.json` read back
   off disk). Using the operator's live install would have planted a fabricated
   Workflow and three fabricated Actions in it — and a fabricated Action
   republishes into agent context. `REQ-SB-95-US-02-T06`'s isolated-install
   precedent and the "six other sessions share this checkout" constraint both
   point the same way.
6. **Six tests rather than three** — the three extras are listed above with
   what each one pins.

### Out of scope, deliberately not done

- **Run routes.** `POST /workflows/{id}/runs` and the one-step-at-a-time routes
  (`ADR-034`) are `T05`'s and are not stubbed: a route that existed and did
  nothing would read, to an agent, exactly like a run engine that silently
  loses steps. Note for `T05`: they are free of this router's paths — a run
  route is three segments where `GET|PUT|DELETE /workflows/{workflow_id}` is
  two.
- **`MEMORY.md`.** Nothing new at framework level; see the Acceptance Criteria
  note above.

gate: flagged 2026-10-18 (coder) — trigger 1 only (scope-internal judgement
calls, listed above). No locked AC went unverified, no `ESCALATIONS.md` entry,
no file outside `## Files to Modify` was touched, no new dependency, no shared
interface changed, no ADR deviated from.
