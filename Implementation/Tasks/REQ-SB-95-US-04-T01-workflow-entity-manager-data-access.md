---
id: REQ-SB-95-US-04-T01
title: Workflow entity + WorkflowManager + Workflows data access over the data path
parent_story: REQ-SB-95-US-04
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "trigger: scope-internal judgement calls logged for human spot-check — the step-id minting rule, the report-definition shape, a colliding step id re-keyed rather than refused, and no publication trigger on this Manager (see Implementation Log)"
phase: P2
depends_on: [REQ-SB-95-US-02-T01]
created: 2026-10-16
updated: 2026-10-18
---

# REQ-SB-95-US-04-T01 — Workflow Entity + WorkflowManager + Data Access

## Parent Story

- Story: [[REQ-SB-95-US-04]] — `../UserStories/REQ-SB-95-US-04-workflow-seventh-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Make `Workflow` a real, stored entity — the ordered steps the operator
documents for a kind of request — with its own Manager and its own store,
sharing nothing with `Pipeline`.

---

## Starting State → End State

**Before / Inputs:**

- No `Workflow` kind exists.
- `business/core/pipelines/pipeline_manager.py` is the nearest step-based shape
  to **read for reference** and is not to be shared, extended or migrated.
- `app/data_access/indexes.py` + `actions.py` (`REQ-SB-95-US-02-T01`) are the
  file-per-id data-access shape to mirror.

**After / Outputs:**

- `app/business/core/workflows/workflow.py` — the `Workflow` entity: `id`, the
  kind of request it handles, an **ordered** list of steps each naming an
  Action id (plus that step's inputs or input mapping), a per-step
  `needs_confirmation` flag, and what is reported back.
- `app/business/core/workflows/workflow_manager.py` — the sole gateway:
  `get_all()` / `get_by_id()` / `create()` / `update()` / `delete()` /
  `import_workflow()`.
- `app/data_access/workflows.py` — raw I/O only over
  `<DATA_PATH>/data/Workflows/<id>/Workflow.json`.
- Step order is preserved exactly on round-trip — it is the operator's
  documented order, not a set.

---

## Files to Modify

- `src/backend/app/business/core/workflows/__init__.py` (new)
- `src/backend/app/business/core/workflows/workflow.py` (new)
- `src/backend/app/business/core/workflows/workflow_manager.py` (new)
- `src/backend/app/data_access/workflows.py` (new)
- `src/backend/tests/test_workflow_artifact_kind.py` (new)

---

## Constraints

- Inherits from parent story.
- **`Pipeline` is left exactly as it is** (`ADR-032`). No shared store, no
  shared Manager, no migration, no re-labelling. `PipelineManager` is reference
  shape only.
- **Layering:** Manager understands the entity, `data_access/` understands
  files only.
- **Documented by the operator, not inferred by the model** — nothing here
  generates, suggests or derives a Workflow.
- Step validation against the Action catalogue is `T02`; this task stores what
  it is given, in order.
- No branching, loops or conditional steps — ordered steps only (story
  Non-Goals).

---

## Tests

**Automated tests** — `src/backend/tests/test_workflow_artifact_kind.py`, run
with `pytest tests/test_workflow_artifact_kind.py` from `src/backend`,
monkeypatching the data access as `tests/test_index_artifact_kind.py` does.

1. `[REQ-SB-95-US-04-AC-01]` Save a Workflow with an id, a request kind, three
   ordered steps (the second marked as needing confirmation) and a report
   definition; assert `write_workflow_json` received it under its own id, and
   that `get_by_id()` returns the same three steps **in the same order**, the
   same per-step confirmation flags and the same report definition.
2. `[REQ-SB-95-US-04-AC-01]` Assert the path built is
   `<second_brain_data_path>/data/Workflows/<id>/Workflow.json`.
3. `[REQ-SB-95-US-04-AC-01]` Re-order the steps, save, re-read; assert the new
   order is returned and no step was dropped or duplicated.
4. `[REQ-SB-95-US-04-AC-07]` Assert `workflow_manager.py` and
   `data_access/workflows.py` import nothing from `business/core/pipelines/`
   and write nothing under the Pipelines store (assert on the module's imports
   and on the tmp-dir contents after a save).

**Manual verification steps:** none required — this task has no screen.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `Workflow` entity with ordered steps, per-step confirmation and a report definition
- [x] `WorkflowManager` as sole gateway; raw I/O only in `data_access/workflows.py`
- [x] Step order preserved exactly on round-trip
- [x] Nothing shared with, imported from, or written into `Pipeline`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Referential integrity with the Action catalogue — `T02`.
- The API — `T03`. Inventory/export/import — `T04`. Runs — `T05`.
  Publication — `T06`. Screen — `T07`.

---

## Context / Notes

`architecture.md` → **§Workflow — the Seventh Artifact Kind**; `ADR-032` fixes
the kind, the store and step-references-Action; `ADR-034` fixes the
one-directional referential discipline `T02` then implements.

---

## Implementation Log

**2026-10-18 — built and verified. `4393124` (code + tests).**

### Verification (automated mode)

Baseline measured on this checkout immediately before starting: **567 passed,
0 failed, 41.54s** (both known flakes green that run). After:
**576 passed, 0 failed, 35.17s** — +9, exactly this task's tests.
`src/backend/tests/test_workflow_artifact_kind.py`, run with
`.venv/Scripts/python.exe -m pytest -q`.

| Test step | AC-ID | Observed outcome |
|---|---|---|
| 1. Save id + request kind + three ordered steps (2nd needs confirmation) + report definition; written under its own id; `get_by_id()` returns the same three steps in the same order, same flags, same report | `REQ-SB-95-US-04-AC-01` | **Pass.** `test_a_saved_workflow_round_trips_its_ordered_steps_and_report`: the store holds exactly `["mail-me-the-team-list"]` with `id` matching; reopened steps are `[("collect","list-team-actions",False), ("send","send-mail",True), ("log","append-capture",False)]`, each step's own `inputs` intact, report `description`/`include_step_ids` identical |
| 2. The path built is `<second_brain_data_path>/data/Workflows/<id>/Workflow.json` | `REQ-SB-95-US-04-AC-01` | **Pass.** `test_the_store_is_the_data_paths_own_workflows_folder`: `workflow_file()` equals `tmp_path/data/Workflows/<id>/Workflow.json`, and a real write/list/read round-trips through it |
| 3. Re-order the steps, save, re-read; new order returned, no step dropped or duplicated | `REQ-SB-95-US-04-AC-01` | **Pass.** `test_reordering_the_steps_saves_and_returns_the_new_order`: order becomes `["log","collect","send"]` on disk *and* on read, still 3 steps with 3 distinct ids, and each step kept its own confirmation flag rather than the flag of the position it moved into |
| 4. `workflow_manager.py` and `data_access/workflows.py` import nothing from `business/core/pipelines/` and write nothing under the Pipelines store | `REQ-SB-95-US-04-AC-07` | **Pass.** `test_the_workflow_kind_imports_nothing_from_pipelines` walks both modules' ASTs — zero imported names containing "pipeline". `test_saving_a_workflow_writes_nothing_outside_its_own_store`: after a real `create()` against `tmp_path`, the complete tree is exactly `data`, `data/Workflows`, `data/Workflows/<id>`, `data/Workflows/<id>/Workflow.json`, and `tmp_path/pipelines` does not exist |

Three tests beyond the decomposer's four, all `AC-01`, covering Manager
surface the task's own Objective names and nothing else would have exercised:
`import_workflow()` keeps the documented step order; a step saved without an id
is minted one that survives a reorder; `delete()`/`get_by_id()`/`update()`
answer an unknown id rather than raising. Plus one cost test.

### Cost pinned by equality (`BUG-086`)

`test_reading_a_workflow_costs_exactly_one_read`, counting real data-access
calls: `create()` = **1 write + 1 read** (the read is the created entity
coming back); `get_by_id()` = **exactly 1 read, 0 lists, 0 writes**;
`get_all()` over three Workflows = **exactly 1 list + 3 reads**, no per-step
read and no second pass. Equality, not a bound — six tasks build on this
Manager.

### Where the writes, sockets and subprocesses went (proved before the suite ran)

Ran the new test file under an interceptor wrapping `Path.write_text` /
`write_bytes` / `open` / `mkdir`, `builtins.open` (write modes), `os.makedirs`
/ `os.remove`, `shutil.rmtree`, `socket.socket.connect`, `subprocess.Popen`,
`urllib.request.urlopen` and `httpx.HTTPTransport.handle_request`:
**29 write attempts, every one under pytest's own tmp root; 0 socket
connects; 0 subprocess launches; 0 outbound HTTP calls.** Nothing reached the
operator's vault, data path, Hermes home or `:8001`. (Two entries the probe
flagged as "outside temp" were `\\.\nul` and a `\\?\`-prefixed pytest garbage
dir — long-path prefix, same temp root.) The suite-wide Hermes sandbox in
`tests/conftest.py` was left untouched and un-bypassed; this Manager fires no
publication, so it never reaches that seam at all.

### File-list check for a missing switch-on site (applied at the start)

**Nothing missing.** This task adds a new package and a new data-access module
that only its own test imports; there is no router, no `main.py` call and no
registry to add it to at this stage. Confirmed against the precedent rather
than assumed: the Action equivalent, `REQ-SB-95-US-02-T01` (`4ecd43c`),
touched **exactly the same five-file shape** and nothing else. The switch-on
sites for this kind are already named in the downstream tasks that own them —
`T03` lists `app/main.py` for the router, `T04` the inventory/export/import
modules, `T06` publication. `src/backend` has no packaging manifest, and
`pytest.ini`'s `testpaths = tests` picks the new test file up with no
registration. No escalation.

### Judgement calls (scope-internal — `gate: flagged` for a spot-check)

1. **A step carries its own stable `id`, minted when absent, and never its
   position.** `T05` must refuse an outcome "for a step id not in the
   Workflow", which needs step identity to exist; a positional id would
   re-point at a different step on every reorder. Minted as
   `step-<uuid4[:8]>`. A caller-supplied id is kept verbatim, which is what
   makes a reorder save keep pointing at the same steps.
2. **A colliding step id is re-keyed and logged, not refused.** Two steps
   sharing an id is already-ambiguous input; failing the save would lose the
   other steps the operator authored, and keeping both would make one
   unaddressable at run time. No new exception type was introduced, so `T03`
   has no extra refusal to map.
3. **The report definition is `{description, include_step_ids}`**, with an
   empty `include_step_ids` meaning *every step, in documented order*. The
   task says "what is reported back" without fixing a shape; this is the
   minimum `T05` can compose a report from and `T07` can edit. `report` is
   always present (never `None`), so the run engine never has to decide what a
   missing definition meant.
4. **No publication trigger on this Manager**, unlike `ActionManager`.
   `T06` owns publishing Workflows into agent context; a trigger added now
   would fire into a published block that does not exist. Consequence: this
   Manager also stays clear of the background-thread and Hermes seams.
5. **`update(steps=[...])` replaces the whole list** rather than merging by
   step id — a merge would have to tell "the operator deleted this step" from
   "the caller only sent the ones it changed", which is undecidable from here.
   A reorder *is* a full-list save.
6. **No step-count, empty-`request_kind` or duplicate-`action_id` validation.**
   The task is explicit: `T02` owns validation, `T01` stores what it is given,
   in order.
