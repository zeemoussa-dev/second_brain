---
id: REQ-SB-95-US-02-T04
title: Action as the sixth kind across inventory, dependency resolver, export, import and secret scan
parent_story: REQ-SB-95-US-02
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "out-of-scope defect found and NOT fixed (ESC-065): artifact_import_conflicts._MANAGER_BY_KIND knows 4 kinds, so the real import route rejects a bundle containing `action` -- or `index`, which has had the same hole since 2026-09-06. T04's own locked ACs are verified green."
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

- [x] Sixth kind present in inventory, resolver, export, import and secret scan
- [x] `artifacts_inventory.py`'s "only 5" header corrected in the same change
- [x] `_PAYLOAD_FOLDER["action"] == "actions"`, stated explicitly
- [x] Import conflict handling (skip / overwrite / keep-both) works for Actions
- [x] No pre-existing kind's behaviour changed
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

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

### 2026-10-16 — built, verified, `Done` (`gate: flagged`, see ESC-065)

**What changed, file by file (all five were re-read in full before editing, per
the task's own Context note):**

- `business/logic/artifacts_inventory.py` — composes `ActionManager` as a sixth
  entry. The module header's "no 6th value is ever produced, since these are the
  only 5 Managers composed" sentence is **corrected in this same change** (it now
  says six, names Action's 2026-10-16 arrival and `ADR-032`, and records that
  `get_all()` returns stored Actions only — plugin-contributed ones are `T05`).
  `Action` carries a real `description` but **no `name` field** (direct read of
  `business/core/actions/action.py`), so its `name` falls back to `action.id`,
  the same fallback `Template` already uses; that is documented in the header too.
- `business/logic/artifact_dependency_resolver.py` — new `elif kind == "action"`
  branch, pulling in the Skill a `skill`-implementation Action names with
  `depends_via = "action:<id> (skill implementation)"`, recursing through the
  existing Skill branch (so that Skill's own Template coupling still applies).
  `http`/`ui` add nothing: both name something that ships with the app. No
  `/`-normalisation here, unlike the Agent branch — `ADR-033` fixes an Action's
  `skill_id` as the bare slug `SkillManager` already keys by.
- `business/logic/artifact_export.py` — `_PAYLOAD_FOLDER["action"] = "actions"`,
  stated explicitly, and the comment above it widened from "only index needs
  stating" to "every kind is stated rather than left to a fallback nobody reads".
  `_text_content_for_scan` gained the `action` branch writing
  `actions/<id>/Action.json`.
- `business/logic/artifact_secret_scan.py` — `_action_content()` registered in
  `_CONTENT_READERS`. It serialises with the identical
  `json.dumps(raw, indent=2)` the export side uses, because a finding's
  `file_path:line` key is only meaningful if both sides produce byte-identical
  text — that equality is itself asserted by a test below.
- `business/logic/artifact_import.py` — `_deploy_action` in the dispatch, same
  shape as `_deploy_index`, with the `_next_alternate_id` keep-both path. It
  deliberately does **not** re-resolve the implementation on the receiving
  install: a bundle legitimately arrives before the Skill it names is deployed
  here, and refusing would lose the definition; the operator sees it as `broken`
  in `resolution_report()` instead, which is what `AC-07` exists for.
- `tests/test_action_artifact_kind.py` — extended with eight tests under a
  `-- The sixth kind across the artifact machinery --` banner.

**Scope-internal judgement calls (logged, not escalated):**

1. **A separate `action_store` fixture rather than editing `T01`'s
   `stored_actions`.** `T01`'s fixture reads with `lambda action_id:
   written[action_id]`, which raises `KeyError` for a missing id — but the real
   `read_action_json` raises `FileNotFoundError`, and that is what
   `ActionManager.get_by_id` catches to answer `None`. `_next_alternate_id`'s
   keep-both probe asks for an id that does *not* exist yet, so the difference
   is load-bearing here and invisible in `T01`'s tests. Added a faithful
   fixture beside it rather than changing the apparatus `T01`'s verified tests
   run on.
2. **The five pre-existing Managers are pinned to fixed stubs in the inventory
   tests.** The live inventory reads this install's real Registry (measured: 41
   Agents, 73 entries), so asserting against it would assert about the machine.
   The pinned entries make "no pre-existing kind changed" a real `==` on the
   full entry list rather than a count.
3. **The import tests drive `artifact_import._deploy_one` directly**, exactly as
   `tests/test_index_artifact_kind.py` does for the Index precedent — see
   `ESC-065` below for why that is not merely convenience.

**Out-of-scope defect found, NOT fixed → `ESC-065` + `REVIEW-QUEUE.md`.**
`artifact_import_conflicts._MANAGER_BY_KIND` knows only skill/template/agent/
pipeline and raises for anything else, and `preview_import`/`commit_import` call
`detect_conflicts()` on the whole manifest first. Measured on this install:

```
kinds known to detect_conflicts: ['agent', 'pipeline', 'skill', 'template']
index  -> ValueError: unrecognized artifact kind 'index' ...
action -> ValueError: unrecognized artifact kind 'action' ...
```

So a bundle containing an `action` — or an `index`, which has had the same hole
since 2026-09-06 — fails as a whole on the real import route. That file is not in
this task's `## Files to Modify`, and `Learnings.md` (2026-09-05) records the
antipattern directly: "finding a bug is not authority to fix it inside someone
else's scope." Logged for a human to assign to a task that owns the file.

---

### Verification — every locked AC, with observed output

Suite run with `.venv/Scripts/python.exe -m pytest` from `src/backend`.
Baseline before any edit: **424 passed**. After: **432 passed** (8 new, 0 broken).

#### `[REQ-SB-95-US-02-AC-04]` — Actions appear as a sixth inventory kind

*Automated, `pytest tests/test_action_artifact_kind.py` — all green.*

| Tests block step | Test | Observed |
|---|---|---|
| 1 | `test_the_inventory_lists_actions_as_a_sixth_kind` | PASSED — the `action` rows equal exactly `[{"kind": "action", "id": "make-strategic-entity", "name": "make-strategic-entity", "description": "Promote a customer to a Strategic Entity"}]`, and the kind set is all six. |
| 2 | `test_the_sixth_kind_changes_nothing_about_the_other_five` | PASSED — the non-`action` entry list is `==` before and after two Actions are created. |
| 3 | `test_a_kind_with_no_artifacts_is_an_absence_not_an_omission_or_an_error` | PASSED — with an empty store the call returns the five pre-existing entries and zero `action` rows; it neither raises nor drops a kind. |

*Manual step 1 — performed live, backend running.* Restarted with
`tools\backend.cmd restart` (`up on http://localhost:8001 -- version 0.11.2,
commit a82273d`), saved one real Action into the App Database Folder
(`.../config/data/Actions/open-the-artifacts-page/Action.json`), then
`GET /artifacts`:

```
BEFORE total=73   skill=8  template=16  agent=41  pipeline=4  index=4
AFTER  total=74   skill=8  template=16  agent=41  pipeline=4  index=4  action=1

action rows:
{ "kind": "action", "id": "open-the-artifacts-page",
  "name": "open-the-artifacts-page",
  "description": "Open Settings > Artifacts (T04 manual verification)" }

pre-existing rows identical: True
```

The verification Action was then deleted (`{'deleted': True}`) and the route
re-read: `FINAL total=73  action rows=0`, `back to the before state: True` —
which also confirms the empty-state half of the AC on the live route.

#### `[REQ-SB-95-US-02-AC-05]` — an exported Action carries the thing it runs

*Automated, same file — all green.*

| Tests block step | Test | Observed |
|---|---|---|
| 4 | `test_the_payload_folder_is_not_naively_pluralised` | PASSED — `_PAYLOAD_FOLDER["action"] == "actions"`. |
| 5 | `test_an_action_pulls_the_skill_it_runs_into_the_closure` | PASSED — closure is exactly `{("action","make-strategic-entity"), ("skill","vault-search")}`; the Skill's `depends_via` is `"action:make-strategic-entity (skill implementation)"`; the `ui` Action's closure is itself alone. |
| 6 | `test_an_exported_action_travels_and_imports_onto_a_clean_store` | PASSED — a real `.sbf` written by `commit_export` and read back by `sbf_archive.read_archive` carries both `actions/make-strategic-entity/Action.json` and `skills/vault-search/SKILL.md`; after clearing the store, `_deploy_one` returns `deployed` and the reopened Action round-trips its description, `("entity_name", True)` input, `allowed_callers`, `needs_confirmation` and `skill` implementation, with `resolution_report()` reporting `["resolves"]`. |
| 7 | `test_importing_an_action_whose_id_exists_never_silently_overwrites` | PASSED — undecided → `failed` with `"no explicit decision supplied"` in the detail; `skip` → `skipped`; `keep_both` → `deployed_as == "make-strategic-entity-imported"`; `overwrite` → replaced. The original definition is asserted untouched after each of the first three. |
| (secret scan) | `test_the_secret_scan_covers_an_actions_own_bytes` | PASSED — `scan_closure` reports one finding `("action", "call-the-provider", "actions/call-the-provider/Action.json")`, and `apply_decisions` keyed by `file_path:line` genuinely redacts it out of the export's own content dict — which is the proof that the scanner and the export agree on the path and the line. |

**Full suite, final:**

```
$ .venv/Scripts/python.exe -m pytest -q
432 passed, 1 warning in 57.43s
```

Nothing was weakened, omitted or skipped; `AC-04` and `AC-05` are the two locked
ACs this task covers and both were verified by the steps the decomposer wrote,
plus the live manual check.
