---
id: REQ-SB-95-US-04-T02
title: Referential integrity with the Action catalogue — save-time step validation and delete-time reverse lookup
parent_story: REQ-SB-95-US-04
requirement_id: REQ-SB-95
type: backend
status: Blocked
gate: flagged
gate_reason: "ESC-075 — the save-time check correctly refuses T01's own step fixtures, and `tests/test_workflow_artifact_kind.py` is outside this task's `## Files to Modify`. Both locked ACs are built, verified and committed (`d71630f`); six T01 tests stay red until that file is authorised."
phase: P2
depends_on: [REQ-SB-95-US-04-T01, REQ-SB-95-US-02-T03]
created: 2026-10-16
updated: 2026-10-18
---

# REQ-SB-95-US-04-T02 — Referential Integrity With the Action Catalogue

## Parent Story

- Story: [[REQ-SB-95-US-04]] — `../UserStories/REQ-SB-95-US-04-workflow-seventh-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Make a Workflow invalid by construction rather than by review: a step naming an
unknown Action is refused at save, and deleting an Action that a Workflow step
names reports the referencing Workflows before anything is removed.

---

## Starting State → End State

**Before / Inputs:**

- `WorkflowManager` (`T01`) stores whatever steps it is given.
- `ActionManager.delete()` (`REQ-SB-95-US-02-T01`) deletes unguarded — correct
  until now, because no Workflow kind existed.
- `MEMORY.md`'s Skill-needs-Template precedent (2026-09-06) is the
  one-directional discipline to follow.

**After / Outputs:**

- `WorkflowManager.create()` / `update()` validate every step against the live
  Action catalogue before anything is written; an unknown action id is refused
  with a message naming **which step** and **which id**, and nothing is written.
- Action deletion asks the Workflow side for referencing Workflows; if any
  exist the operator is told which, and the Action is **not** deleted.
- An Action no Workflow references deletes exactly as it did before.
- The edge runs **one direction only**: a Workflow step names an Action; an
  Action stores nothing about Workflows.

---

## Files to Modify

- `src/backend/app/business/core/workflows/workflow_manager.py`
- `src/backend/app/business/core/actions/action_manager.py` (the delete-time reverse lookup)
- `src/backend/app/api/actions_router.py` (surface the blocked delete honestly)
- `src/backend/tests/test_workflow_action_integrity.py` (new)

---

## Constraints

- Inherits from parent story.
- **Invalid by construction, not by review** (`ADR-032`) — enforced at save and
  at delete, never by a later audit.
- **One direction only** (`ADR-034`): no back-reference list is stored on an
  Action. The reverse lookup is computed by asking `WorkflowManager`.
- The lookup must not introduce an import cycle between the two Managers — if
  a direct import would create one, inject the lookup rather than restructuring
  either Manager.
- No Workflow may ever be left holding a step that points at nothing.

---

## Tests

**Automated tests** — `src/backend/tests/test_workflow_action_integrity.py`,
run with `pytest tests/test_workflow_action_integrity.py` from `src/backend`.

1. `[REQ-SB-95-US-04-AC-02]` Save a Workflow whose second step names an action
   id that is not in the catalogue; assert the refusal names step 2 and that
   id, and that `write_workflow_json` was never called.
2. `[REQ-SB-95-US-04-AC-02]` Save the same Workflow with every step naming a
   real catalogued Action; assert it is written.
3. `[REQ-SB-95-US-04-AC-02]` Update an existing valid Workflow to point one step
   at an unknown action id; assert the refusal and that the stored Workflow is
   unchanged on disk.
4. `[REQ-SB-95-US-04-AC-06]` With a Workflow whose step names Action `X`,
   attempt to delete `X`; assert the operation is refused, the response names
   the referencing Workflow(s), `delete_action_definition` was never called, and
   the Workflow still holds its step.
5. `[REQ-SB-95-US-04-AC-06]` Delete an Action that no Workflow references;
   assert it is deleted normally.
6. `[REQ-SB-95-US-04-AC-06]` Assert no Action record gains any
   workflow-reference field (the stored `Action.json` is byte-identical before
   and after a Workflow references it).

**Manual verification steps:**

1. `[REQ-SB-95-US-04-AC-06]` With the backend running, create a real Workflow
   referencing a real Action, `DELETE /actions/{id}` and confirm the real
   response names the referencing Workflow and the Action is still present.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Save-time step validation naming the step and the unknown id
- [x] Delete-time reverse lookup reporting referencing Workflows, deletion blocked
- [x] One-directional edge; no back-reference stored on an Action
- [x] No import cycle between the two Managers
- [x] `MEMORY.md` — no new framework constraint emerged (see the log; the one
      candidate is `ESC-075`'s, and it belongs to the decomposer rule the
      2026-10-18 entry already records)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The editor offering only catalogued Actions (the second half of `AC-02`) —
  `T07`.
- Export-time dependency closure — `T04`.

---

## Context / Notes

`architecture.md` → **§Workflow — the Seventh Artifact Kind** ("Referential
integrity, one direction only") and `ADR-034`'s last decision bullet are
authoritative, including the `MEMORY.md` Skill-needs-Template precedent for why
the edge runs one way.

---

## Implementation Log

**2026-10-18 — built, verified, and `Blocked` on `ESC-075`. `d71630f` (code +
tests).** Both locked ACs are green on 10 new AC-tagged tests. What blocks the
task is not this task's code: the save-time check correctly refuses `T01`'s own
step fixtures, and that file is outside this task's `## Files to Modify`.

### Verification (automated mode)

Baseline measured on this checkout immediately before starting, at `78fb600`:
**617 passed, 1 failed, 47.22s** — the failure being
`test_marketplace.py::test_install_repairs_a_plugin_left_with_only_its_bytecode_cache`,
which **passes alone** (28 passed, 3.15s), so a suite-ordering flake and not
mine. After: **622 passed, 6 failed, 41.27s**. 618 → 628 collected, +10 exactly
this task's tests; the 6 failures are all one cause and are `ESC-075`.

`src/backend/tests/test_workflow_action_integrity.py`, run with
`.venv/Scripts/python.exe -m pytest -q` from `src/backend`.

| Test step | AC-ID | Observed outcome |
|---|---|---|
| 1. Save a Workflow whose second step names an uncatalogued id; the refusal names step 2 and that id, and `write_workflow_json` was never called | `REQ-SB-95-US-04-AC-02` | **Pass.** `test_a_step_naming_an_unknown_action_is_refused_naming_the_step_and_the_id`: `WorkflowStepActionNotFoundError("step 2 of this Workflow names action 'post-to-slack', which is not in this install's Action catalogue; nothing was saved")`, and the recorded write attempts are `[]` — measured on a fixture that records every attempt, not inferred from an empty store |
| 2. The same Workflow with every step naming a real catalogued Action is written | `REQ-SB-95-US-04-AC-02` | **Pass.** `test_a_workflow_whose_every_step_is_catalogued_is_written`: one write, `['mail-me-the-team-list']`, and the three steps come back as `['list-team-actions', 'send-mail', 'list-team-actions']` with confirmation flags `[False, True, False]` — the validation refuses the unknown id and nothing else |
| 3. Update a stored valid Workflow to point one step at an unknown id; the refusal, and the stored Workflow unchanged on disk | `REQ-SB-95-US-04-AC-02` | **Pass.** `test_pointing_a_stored_workflow_at_an_unknown_action_leaves_it_unchanged`: refusal names step 2; `json.dumps(stored, sort_keys=True)` is **identical** before and after, write attempts are still only the first valid save, and a re-read returns the original three action ids |
| 4. With a Workflow whose step names `X`, delete `X`: refused, the response names the referencing Workflow(s), `delete_action_definition` never called, the Workflow still holds its step | `REQ-SB-95-US-04-AC-06` | **Pass.** `test_deleting_an_action_a_workflow_step_names_is_refused_naming_the_workflows`, driven over the real `DELETE /actions/send-mail`: **409**, body `"action 'send-mail' was not deleted: it is a step of workflow 'mail-me-the-team-list'. Remove the step from each first, so no documented handling is left pointing at nothing"`; recorded deletions `[]`; the Action still in the store; the Workflow still holds `['list-team-actions', 'send-mail']`. Also pinned: the refused delete fired **0** catalogue publications |
| 5. Delete an Action no Workflow references; deleted normally | `REQ-SB-95-US-04-AC-06` | **Pass.** `test_an_action_no_workflow_references_deletes_normally`: **200** `{"deleted": true}`, recorded deletions `['append-capture']`, gone from the store, and `DELETE /actions/never-existed` still answers `{"deleted": false}` rather than a 404 |
| 6. No Action record gains a workflow-reference field — stored `Action.json` byte-identical before and after a Workflow references it | `REQ-SB-95-US-04-AC-06` | **Pass.** `test_an_action_record_gains_no_workflow_reference_field`: `json.dumps(..., sort_keys=True)` identical at all three points (before the Workflow, after it, after the refused delete), and the serialised record contains no substring `workflow` at all — not even an empty back-reference key |

Four tests beyond the decomposer's six, each pinning a Constraint the task
states but no listed step would have caught:

- `test_a_step_naming_no_action_at_all_is_refused_by_the_same_rule` (`AC-02`) —
  "no Workflow may ever be left holding a step that points at nothing" covers
  `action_id: ""`, which would otherwise sail through as a step naming nothing.
- `test_the_manager_refuses_the_same_deletion_whatever_door_it_came_through`
  (`AC-06`) — the guard is the Manager's, not the router's, so "invalid by
  construction" is true of the backend rather than of one route.
- `test_the_action_side_imports_nothing_from_the_workflows_package_at_module_scope`
  (`AC-06`) — the no-import-cycle Constraint, asserted on both modules' syntax
  trees rather than promised in a comment.
- the cost test below.

**Manual verification step (`AC-06`, "with the backend running"):** not
performed, deliberately. It needs `POST /workflows`, and there is no Workflows
router until `T03` — a Workflow can only be created through the Manager today,
so the manual step as written is not reachable from this task. The same
refusal is nevertheless exercised over the real HTTP surface in test 4 above,
through `DELETE /actions/{id}` on the real `app.main.app` with `TestClient`,
which is what proves the route is registered and the 409 reaches a client with
the Manager's sentence intact. The route-level half of the manual step is
therefore covered; the `POST /workflows` half belongs to `T03`'s own manual
step, which already exists.

### Cost pinned by equality (`BUG-086`)

`test_validating_a_save_reads_the_catalogue_once_and_a_delete_scans_workflows_once`,
counting real data-access calls:

- A **three**-step save: `list_action_ids` == **2**, `read_action_json` == **3**
  (one per catalogued Action). The two listings are `get_all()`'s own and the
  plugin-composition's, both pre-existing.
- A **one**-step save: `list_action_ids` == **2**, `read_action_json` == **3** —
  *identical*, which is the real claim: cost is a property of the catalogue, not
  of the Workflow's length. Reading the catalogue per step is the
  `O(steps × catalogue)` shape `_ResolutionSources` exists to avoid.
- A guarded delete over two stored Workflows: `list_workflow_ids` == **1**,
  `read_workflow_json` == **2** — once per stored Workflow, none per step.
- `delete("never-existed")`: `list_workflow_ids` == **0**,
  `read_workflow_json` == **0**. The reverse lookup is asked only after the id
  is known to exist, so an id that deletes nothing scans nothing.

### Where the writes, sockets and subprocesses went (proved before the suite ran)

Ran the new test file behind an interceptor wrapping `Path.write_text` /
`write_bytes` / `open` / `mkdir` / `touch` / `unlink` / `rename` / `replace`,
`builtins.open` (write modes), `os.makedirs` / `os.remove`, `shutil.rmtree`,
`socket.socket.connect`, `subprocess.Popen`, `urllib.request.urlopen` and
`httpx.HTTPTransport.handle_request`: **28 write attempts, every one under
pytest's own tmp root** except `\\.\nul` and pytest's own
`src/backend/.pytest_cache` bookkeeping; **0 outbound HTTP**; **3 loopback
socket connects** to ephemeral high ports (anyio's blocking portal behind
`TestClient`, never `:8001`); **1 subprocess**, `git rev-parse HEAD`, which is
`app/main.py`'s existing commit lookup at import and is read-only. Nothing
reached the operator's vault, data path or Hermes home.

`tests/conftest.py`'s suite-wide Hermes sandbox was left untouched and
un-bypassed. This file **tightens** it: the catalogue-publication trigger is
replaced by a counter, so these tests spawn no background thread at all, and
"a refused delete publishes nothing" becomes an assertion instead of a silence.

### File-list check for a missing switch-on site (applied at the start)

**Nothing missing — the declared list is complete for the code.**
`ActionManager.delete()` has **exactly one** caller in the whole backend
(`grep`-verified: `app/api/actions_router.py:273`), and that router is already
in the list and already mounted in `app/main.py`; the save-time half is reached
through `WorkflowManager`, whose only caller today is this task's own test file
(`T03` owns the router that will call it, and already names `app/main.py`).
`src/backend` has no packaging manifest and `pytest.ini`'s `testpaths = tests`
picks the new file up with no registration.

**What the list WAS missing is on the test side, not the wiring side** —
`ESC-075`, below. The standing rule asks "what single edit, in a file this task
does not otherwise touch, is the difference between this code existing and this
code running?"; the answer here is "none". The question that would have caught
this one is its mirror: *which existing test stops being true the moment this
gate exists?*

### Blocker — `ESC-075` (why this task is `Blocked`, not `Done`)

The save-time check refuses `T01`'s own step fixtures. Every step in
`tests/test_workflow_artifact_kind.py` names an invented action id
(`list-team-actions`, `send-mail`, `append-capture`) that no install
catalogues, so six of its nine tests now fail on one error:
`WorkflowStepActionNotFoundError: step 1 ... 'list-team-actions' ... is not in
this install's Action catalogue`. That file is outside this task's
`## Files to Modify`, so the correct code was committed and the task stopped
rather than a `Done` task's test file being edited (`Pipeline.md` hard rule 5).

There is no in-scope alternative: `AC-02` is locked as a refusal **at save, in
the Manager, with nothing written** — the decomposer's own step asserts
`write_workflow_json` was never called — so the check cannot move to the router
or to a later audit without weakening it. The fix is ~6 lines (an autouse
fixture cataloguing those three ids for that file only) and changes no `AC-01`
assertion; it is also needed on its own merits, because without it those tests
now consult the operator's **real** `<DATA_PATH>/data/Actions/` store and would
pass or fail by accident of the machine. `ESC-064`, two days earlier, is the
identical case one kind along and was resolved by authorising the file.

### Judgement calls (scope-internal — `gate: flagged` for a spot-check)

1. **The refusal names the step by POSITION, not by step id.** The operator is
   looking at an ordered editor, and a step that has not been saved yet has no
   id they have ever seen. (`T01`'s stable step ids remain the run-time
   addressing scheme — untouched.)
2. **A step naming no action at all raises the same exception type** rather
   than a second one. Both leave a step pointing at nothing, and a second type
   would give `T03` two refusals to map onto the same 409.
3. **The lookup's import is deferred inside the function, not injected via a
   parameter.** The Constraint allows injection "rather than restructuring
   either Manager"; a parameter would make the guard a property of whoever
   remembered to pass it, which is exactly what "invalid by construction" rules
   out. The deferred import is the in-repo precedent —
   `AgentManager._action_catalogue()` does the same thing against this same
   module, for this same reason — and the absence of a module-scope import on
   the Action side is asserted on the syntax tree.
4. **`import_workflow()` is NOT held to the catalogue.** A bundle carries a
   Workflow's Actions alongside it (`T04`'s closure) and nothing fixes which is
   provisioned first, so a live-catalogue check would refuse bundles that are
   complete. Exactly the line `import_action` already draws (cardinality yes,
   resolution no). The consequence is accepted and named: an imported Workflow
   can arrive holding a reference this install cannot resolve.
5. **`update()` does not re-validate steps it was not given.** Renaming a
   Workflow must not be refused because of something that changed elsewhere —
   `ActionManager.update()`'s omitted-implementation rule, same reasoning.
6. **The read side was left forgiving, and no `resolution_report()` was added
   for Workflows.** A Workflow whose step names a missing Action still lists
   and still opens, the way a broken Action still lists — it is honest by not
   disappearing. A per-Workflow broken/reason report mirroring
   `ActionManager.resolution_report()` would be the fuller version of that
   honesty, but no AC asks for it and nothing would call it until `T03`/`T07`;
   it is noted here as the obvious follow-up rather than built speculatively.
7. **No `MEMORY.md` entry.** Nothing here is a new framework-wide hard rule:
   the one-directional discipline is already recorded (Skill-needs-Template,
   2026-09-06) and `ADR-034` restates it. The one candidate worth considering
   belongs to the human resolving `ESC-075` — the 2026-10-18 decomposer rule
   about naming the **switch-on** site has a mirror, the **fixture** site, and
   `ESC-064` + `ESC-075` are now two instances of it.

---

## Scope extension — 2026-10-18 (unblocks `ESC-075`)

**Added to `## Files to Modify`:** `src/backend/tests/test_workflow_artifact_kind.py`,
scoped to **the one autouse fixture** and nothing else.

`T01` wrote those step fixtures (`list-team-actions`, `send-mail`, `append-capture`)
before a save-time catalogue gate existed, so no install catalogues them. The gate is
correct and the fixtures are now invalid — refusing them is the locked `AC-02`
behaviour working, not a regression. `ESC-064` was the identical case one story
earlier and was resolved the same way.

Independently of this task, that fixture is **needed**: without it those tests consult
the operator's real `<DATA_PATH>/data/Actions/` store, so their result depends on what
Actions happen to exist on the machine. Fix that while you are there — a test should
not be able to see the operator's catalogue at all.

Do not weaken the gate to accommodate the fixtures, and do not edit the assertions:
catalogue the ids the fixtures use, in the test's own store.
