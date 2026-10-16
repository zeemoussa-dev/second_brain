---
id: REQ-SB-95-US-02-T04
title: Action as the sixth kind across inventory, dependency resolver, export, import and secret scan
parent_story: REQ-SB-95-US-02
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

# REQ-SB-95-US-02-T04 — The Sixth Kind's Measured Touch Points

## Parent Story

- Story: [[REQ-SB-95-US-02]] — `../UserStories/REQ-SB-95-US-02-action-sixth-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Land `action` as a real artifact kind everywhere the existing five live — the
inventory, the dependency closure, export, import and the secret scan — so an
Action can actually travel in a bundle, which is what makes it an artifact.

---

## Starting State → End State

**Before / Inputs (read directly, not estimated):**

- `business/logic/artifacts_inventory.py` composes exactly five Managers and its
  own module header states `kind` is always one of five and "no 6th value is
  ever produced, since these are the only 5 Managers composed".
- `business/logic/artifact_export.py` holds `_PAYLOAD_FOLDER = {"skill":
  "skills", "template": "templates", "agent": "agents", "index": "indexes", …}`
  — the `"index"` entry exists precisely to stop naive pluralisation — plus one
  payload-writing branch per kind (`elif kind == "index": …` writes
  `indexes/<id>/Index.json`).
- `business/logic/artifact_import.py::_deploy_one` dispatches per kind and falls
  through to `raise ValueError(f"unrecognized artifact kind {kind!r}")`;
  `_next_alternate_id` is the keep-both path.
- `business/logic/artifact_dependency_resolver.py::visit` has one `elif kind ==`
  branch per kind.
- `tests/test_index_artifact_kind.py` is the precedent test file for exactly
  this change, Index-flavoured.

**After / Outputs:**

- `artifacts_inventory.py` composes `ActionManager` as a sixth entry and **its
  module header is corrected** — the "only 5" sentence is part of the change,
  not collateral.
- `artifact_export.py` gains `_PAYLOAD_FOLDER["action"] = "actions"` and the
  payload branch writing `actions/<id>/Action.json`.
- `artifact_dependency_resolver.py` gains an `elif kind == "action"` branch
  pulling in the Skill a `skill`-implementation Action names (recursing into
  that Skill's own existing edges).
- `artifact_import.py` gains `_deploy_action` in the dispatch, with conflict
  detection and the `_next_alternate_id` keep-both path, exactly as `_deploy_index`
  has it.
- `artifact_secret_scan.py` covers the new `Action.json` bytes — they are
  Second-Brain-owned, so they are in the scan's surface.

---

## Files to Modify

- `src/backend/app/business/logic/artifacts_inventory.py`
- `src/backend/app/business/logic/artifact_dependency_resolver.py`
- `src/backend/app/business/logic/artifact_export.py`
- `src/backend/app/business/logic/artifact_import.py`
- `src/backend/app/business/logic/artifact_secret_scan.py`
- `src/backend/tests/test_action_artifact_kind.py` (extend — created by `T01`)

---

## Constraints

- Inherits from parent story.
- **No pre-existing artifact kind changes behaviour.** Skills, Templates,
  Agents, Pipelines and Indexes must return exactly what they returned before.
- The payload folder is `"actions"`, stated explicitly in `_PAYLOAD_FOLDER` —
  never left to `kind + "s"`.
- No new ADR: this is `ADR-013`/`ADR-015`'s machinery extended the way `Index`
  already extended it (`ADR-019`).
- The `ActionCalls/` ledger (`US-03`) and `WorkflowRuns/` (`US-04`) are instance
  data and are **excluded** from export — do not generalise this task's export
  branch to cover them later.

---

## Tests

**Automated tests** — extend `src/backend/tests/test_action_artifact_kind.py`,
run with `pytest tests/test_action_artifact_kind.py` from `src/backend`,
mirroring `tests/test_index_artifact_kind.py`.

1. `[REQ-SB-95-US-02-AC-04]` With Actions present, assert
   `artifacts_inventory.list_all_artifacts()` returns entries with
   `kind == "action"` carrying id, name and description, alongside entries for
   all five pre-existing kinds.
2. `[REQ-SB-95-US-02-AC-04]` Snapshot the inventory entries for the five
   pre-existing kinds with zero Actions present and again with Actions present;
   assert they are identical — adding the sixth kind changed nothing about the
   other five.
3. `[REQ-SB-95-US-02-AC-04]` Assert the inventory returns an empty list for a
   kind with no artifacts rather than omitting the kind or raising.
4. `[REQ-SB-95-US-02-AC-05]` Assert `artifact_export._PAYLOAD_FOLDER["action"]
   == "actions"` (the `test_the_payload_folder_is_not_naively_pluralised`
   precedent, Action-flavoured).
5. `[REQ-SB-95-US-02-AC-05]` Run `artifact_dependency_resolver.resolve_closure`
   on a selection of one `skill`-implementation Action; assert the closure
   contains that Skill with a `depends_via` naming the Action, and that a
   `http`/`ui` Action pulls in nothing extra.
6. `[REQ-SB-95-US-02-AC-05]` Export a bundle containing that Action; assert the
   payload carries `actions/<id>/Action.json` and the Skill's own payload, then
   import it on a clean monkeypatched store and assert the Action is listed and
   its implementation resolves.
7. `[REQ-SB-95-US-02-AC-05]` Import the same bundle a second time with the id
   already present: assert the existing conflict path is taken (no decision →
   honest `failed` outcome naming the missing decision; `keep_both` → a
   `_next_alternate_id` id; `overwrite` → replaced) and that nothing is silently
   overwritten.

**Manual verification steps:**

1. `[REQ-SB-95-US-02-AC-04]` With the backend running and at least one real
   Action saved, `GET /artifacts` and confirm the `action` rows appear beside
   the five existing kinds, every pre-existing row unchanged.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Sixth kind present in inventory, resolver, export, import and secret scan
- [ ] `artifacts_inventory.py`'s "only 5" header corrected in the same change
- [ ] `_PAYLOAD_FOLDER["action"] == "actions"`, stated explicitly
- [ ] Import conflict handling (skip / overwrite / keep-both) works for Actions
- [ ] No pre-existing kind's behaviour changed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The seventh kind (`Workflow`) — `REQ-SB-95-US-04-T04` extends these same files
  afterwards.
- The `SettingsArtifactsPage` tab for the new kind — `T06`.

---

## Context / Notes

`architecture.md` → **§Adding a Kind — the Measured Touch Points** lists these
five files and the exact edit in each; it was written from a direct read of
them. Re-read each real current file before editing — this project's Learnings
record repeated drift between a task's quoted sample and the real file.

---

## Implementation Log

_(Filled in by the coder.)_
