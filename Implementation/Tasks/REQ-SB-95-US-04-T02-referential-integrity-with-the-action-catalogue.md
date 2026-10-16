---
id: REQ-SB-95-US-04-T02
title: Referential integrity with the Action catalogue — save-time step validation and delete-time reverse lookup
parent_story: REQ-SB-95-US-04
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-04-T01, REQ-SB-95-US-02-T03]
created: 2026-10-16
updated: 2026-10-16
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

- [ ] Save-time step validation naming the step and the unknown id
- [ ] Delete-time reverse lookup reporting referencing Workflows, deletion blocked
- [ ] One-directional edge; no back-reference stored on an Action
- [ ] No import cycle between the two Managers
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

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

_(Filled in by the coder.)_
