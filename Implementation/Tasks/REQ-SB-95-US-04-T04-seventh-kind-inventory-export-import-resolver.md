---
id: REQ-SB-95-US-04-T04
title: Workflow as the seventh kind across inventory, dependency resolver, export and import
parent_story: REQ-SB-95-US-04
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-04-T01, REQ-SB-95-US-02-T04]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-04-T04 — The Seventh Kind's Measured Touch Points

## Parent Story

- Story: [[REQ-SB-95-US-04]] — `../UserStories/REQ-SB-95-US-04-workflow-seventh-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Land `workflow` as a real artifact kind in the inventory, the dependency
closure, export and import — including the new Workflow → Action → Skill edge —
so a Workflow can travel in a bundle and arrive runnable.

---

## Starting State → End State

**Before / Inputs:**

- `REQ-SB-95-US-02-T04` has already added the sixth kind to
  `artifacts_inventory.py`, `artifact_dependency_resolver.py`,
  `artifact_export.py`, `artifact_import.py` and `artifact_secret_scan.py`, and
  corrected the "only 5" header. **Re-read each real current file** — this task
  extends that change, it does not repeat it.
- `ActionCalls/` and `WorkflowRuns/` are instance data and are excluded from
  export (`ADR-033`/`ADR-034`).

**After / Outputs:**

- `artifacts_inventory.py` composes `WorkflowManager` as a seventh entry, header
  accurate.
- `artifact_export.py` gains `_PAYLOAD_FOLDER["workflow"] = "workflows"` and the
  payload branch writing `workflows/<id>/Workflow.json`.
- `artifact_dependency_resolver.py` gains an `elif kind == "workflow"` branch
  pulling in every Action its steps name, **recursing into those Actions' own
  implementation Skills**.
- `artifact_import.py` gains `_deploy_workflow` in the dispatch with conflict
  detection and the `_next_alternate_id` keep-both path.
- `artifact_secret_scan.py` covers the new `Workflow.json` bytes.
- Nothing under `ActionCalls/` or `WorkflowRuns/` is exportable.

---

## Files to Modify

- `src/backend/app/business/logic/artifacts_inventory.py`
- `src/backend/app/business/logic/artifact_dependency_resolver.py`
- `src/backend/app/business/logic/artifact_export.py`
- `src/backend/app/business/logic/artifact_import.py`
- `src/backend/app/business/logic/artifact_secret_scan.py`
- `src/backend/tests/test_workflow_artifact_kind.py` (extend — created by `T01`)

---

## Constraints

- Inherits from parent story.
- **No pre-existing artifact kind changes behaviour** — including `action`,
  which landed one task-chain earlier.
- `_PAYLOAD_FOLDER["workflow"] = "workflows"` stated explicitly, never
  `kind + "s"`.
- `ActionCalls/` and `WorkflowRuns/` stay out of export — a run is not a
  capability.
- **`Pipeline` untouched**: no Pipeline entry, behaviour, schedule or label
  changes as a side effect of adding the seventh kind.

---

## Tests

**Automated tests** — extend `src/backend/tests/test_workflow_artifact_kind.py`,
run with `pytest tests/test_workflow_artifact_kind.py` from `src/backend`.

1. `[REQ-SB-95-US-04-AC-04]` With Workflows present, assert
   `artifacts_inventory.list_all_artifacts()` returns entries with
   `kind == "workflow"` alongside all six pre-existing kinds.
2. `[REQ-SB-95-US-04-AC-04]` Snapshot the entries for the six pre-existing kinds
   with zero Workflows and again with Workflows present; assert they are
   identical.
3. `[REQ-SB-95-US-04-AC-05]` Assert
   `artifact_export._PAYLOAD_FOLDER["workflow"] == "workflows"`.
4. `[REQ-SB-95-US-04-AC-05]` Run `resolve_closure` on a selection of one
   Workflow whose steps name two Actions, one of them `skill`-implemented;
   assert the closure contains both Actions **and** that Skill, each with a
   `depends_via` naming what pulled it in.
5. `[REQ-SB-95-US-04-AC-05]` Export that Workflow, assert the payload carries
   `workflows/<id>/Workflow.json` plus both Actions and the Skill; import onto a
   clean monkeypatched store and assert every step of the imported Workflow
   resolves there.
6. `[REQ-SB-95-US-04-AC-07]` Assert a Pipeline's inventory entry, stored JSON
   and schedule fields are byte-identical before and after Workflows exist, and
   that no Pipeline appears under any `workflow` kind.
7. `[REQ-SB-95-US-04-AC-07]` Assert nothing from `ActionCalls/` or
   `WorkflowRuns/` is included in an export of everything.

**Manual verification steps:**

1. `[REQ-SB-95-US-04-AC-04]` With the backend running and a real Workflow saved,
   `GET /artifacts` and confirm the `workflow` rows appear beside the six
   existing kinds, every pre-existing row unchanged.
2. `[REQ-SB-95-US-04-AC-07]` Confirm the install's real Pipelines still list
   with their own steps and schedules, and that their Hermes cron jobs are
   untouched.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Seventh kind present in inventory, resolver, export, import and secret scan
- [ ] Workflow → Action → Skill closure, recursing correctly
- [ ] `_PAYLOAD_FOLDER["workflow"] == "workflows"`, stated explicitly
- [ ] Import conflict handling works for Workflows
- [ ] No pre-existing kind changed; Pipelines provably untouched
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The `SettingsArtifactsPage` tab for the seventh kind — `T07`.
- Workflow runs — `T05`.

---

## Context / Notes

`architecture.md` → **§Adding a Kind — the Measured Touch Points** names the
exact edit per file and the genuinely new edges ("Workflow → every Action its
steps name (recursing into those Actions' own Skills)"). Compose every edit
around the real current file — these five modules will have just been changed
by `REQ-SB-95-US-02-T04`.

---

## Implementation Log

_(Filled in by the coder.)_

---

## Scope extension — 2026-10-18 (unblocks `ESC-076`)

**Added to `## Files to Modify`:** `src/backend/app/business/logic/artifact_import_conflicts.py`
— the `_MANAGER_BY_KIND` entry only.

That module is the **sixth** `business/logic/artifact_*.py` file that enumerates
artifact kinds; this task's list named the other five. Adding `workflow` to the
export side without it makes
`test_action_artifact_kind.py::test_the_gate_accepts_every_kind_the_export_can_emit`
fail — that test exists to catch exactly this drift, and it is doing its job. Add
`"workflow": WorkflowManager` to the map and that test goes green again; **do not edit
the test**, and do not touch anything else in the conflicts module.

`test_action_artifact_kind.py` itself stays out of scope. If it needs a change beyond
going green on its own, stop and escalate.
