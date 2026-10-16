---
id: REQ-SB-95-US-04-T01
title: Workflow entity + WorkflowManager + Workflows data access over the data path
parent_story: REQ-SB-95-US-04
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-02-T01]
created: 2026-10-16
updated: 2026-10-16
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

- [ ] `Workflow` entity with ordered steps, per-step confirmation and a report definition
- [ ] `WorkflowManager` as sole gateway; raw I/O only in `data_access/workflows.py`
- [ ] Step order preserved exactly on round-trip
- [ ] Nothing shared with, imported from, or written into `Pipeline`
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

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

_(Filled in by the coder.)_
