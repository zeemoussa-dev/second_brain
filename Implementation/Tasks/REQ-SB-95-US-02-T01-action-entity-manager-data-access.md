---
id: REQ-SB-95-US-02-T01
title: Action entity + ActionManager + Actions data access over the data path
parent_story: REQ-SB-95-US-02
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-02-T01 — Action Entity + ActionManager + Actions Data Access

## Parent Story

- Story: [[REQ-SB-95-US-02]] — `../UserStories/REQ-SB-95-US-02-action-sixth-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Make `Action` a real, stored entity: the dataclass, the one Manager that is the
sole gateway onto it, and the raw file I/O under
`<DATA_PATH>/data/Actions/<id>/Action.json` — including the exactly-one-
implementation cardinality rule at save time.

---

## Starting State → End State

**Before / Inputs:**

- No `Action` kind exists anywhere in the backend.
- `app/business/core/index/index_manager.py` + `app/data_access/indexes.py` are
  the shape to mirror function-for-function; `data_access/indexes.py` exposes
  `list_index_ids` / `read_index_json` / `write_index_json` /
  `delete_index_definition` over `("data", "Indexes")` under
  `settings.second_brain_data_path` (read directly).

**After / Outputs:**

- `app/business/core/actions/action.py` — the `Action` entity:
  `id`, `description`, `inputs` (typed entries each with a `required` flag),
  `allowed_callers` (list of agent ids, or `["*"]`), `needs_confirmation`
  (bool), and exactly one `implementation` of kind `skill` | `http` | `ui`
  (`ADR-033` fixes the first two field shapes).
- `app/business/core/actions/action_manager.py` — `get_all()` / `get_by_id()` /
  `create()` / `update()` / `delete()` / `import_action()`, the sole gateway.
  Cardinality is enforced here: zero or two-or-more implementations is a refusal
  naming the rule, never a silently-coerced save.
- `app/data_access/actions.py` — raw I/O only, no defaults applied, no shape
  validated: `list_action_ids` / `read_action_json` / `write_action_json` /
  `delete_action_definition` over `("data", "Actions")`.
- A round-tripped Action returns byte-equivalent `inputs`, `allowed_callers` and
  `needs_confirmation`.

---

## Files to Modify

- `src/backend/app/business/core/actions/__init__.py` (new)
- `src/backend/app/business/core/actions/action.py` (new)
- `src/backend/app/business/core/actions/action_manager.py` (new)
- `src/backend/app/data_access/actions.py` (new)
- `src/backend/tests/test_action_artifact_kind.py` (new — this task's automated tests)

---

## Constraints

- Inherits from parent story.
- **Layering:** the Manager understands the `Action` entity, `data_access/`
  understands files only — no raw path building or JSON reading in the Manager,
  no defaulting or validation in `data_access/`.
- **Instance data, never the repository** — the store is under
  `settings.second_brain_data_path`, not `src/`.
- Save-time *resolution* of the named implementation is `T02`'s scope. This task
  enforces cardinality (exactly one) only.
- Plugin-contributed Actions are `T05`'s scope — `get_all()` here returns stored
  Actions; `T05` composes plugin ones on top.

---

## Tests

**Automated tests** — `src/backend/tests/test_action_artifact_kind.py`, run with
`pytest tests/test_action_artifact_kind.py` from `src/backend`. Monkeypatch
`app.business.core.actions.action_manager.actions_data.write_action_json` /
`read_action_json` the way `tests/test_index_artifact_kind.py` already does, so
no real data path is written.

1. `[REQ-SB-95-US-02-AC-01]` Save an Action with two typed inputs (one required,
   one optional), `allowed_callers: ["cbo-agent"]` and `needs_confirmation:
   true`; assert `write_action_json` received it under its own id, that
   `get_by_id()` returns the same inputs with the same `required` flags, the same
   `allowed_callers` and the same confirmation flag, and that `get_all()` lists
   it with its id, description and implementation kind.
2. `[REQ-SB-95-US-02-AC-01]` Assert the path `data_access/actions.py` builds is
   `<second_brain_data_path>/data/Actions/<id>/Action.json` (assert on the
   resolved `Path`, with `settings.second_brain_data_path` monkeypatched to a
   tmp dir).
3. `[REQ-SB-95-US-02-AC-03]` Save a payload with no implementation; assert the
   refusal names the exactly-one rule and `write_action_json` was never called.
4. `[REQ-SB-95-US-02-AC-03]` Save a payload naming both a `skill` and an `http`
   implementation; assert the same refusal and no write.
5. `[REQ-SB-95-US-02-AC-03]` Save a payload naming exactly one implementation;
   assert it is written.

**Manual verification:** none required for this task — it has no screen.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `Action` entity carries exactly the `ADR-032`/`ADR-033` fields
- [ ] `ActionManager` is the sole gateway; `data_access/actions.py` does raw I/O only
- [ ] Exactly-one-implementation refused at save, with a message naming the rule
- [ ] Round-trip preserves inputs, required flags, `allowed_callers`, confirmation flag
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Save-time implementation resolution and the broken-entry report — `T02`.
- The HTTP API — `T03`.
- Inventory / export / import / dependency resolver — `T04`.
- Plugin-contributed Actions — `T05`.
- Any screen — `T06`.

---

## Context / Notes

`architecture.md` → §An Agent Acts From a Published Catalogue (`REQ-SB-95`) →
**§Action Catalogue — the Sixth Artifact Kind** is authoritative; `ADR-032`
(kind, store, cardinality) and `ADR-033` (`allowed_callers` is a list of agent
ids which are Hermes profile ids; `needs_confirmation` is stored here and
honoured in `US-03`) bound the fields. Read the real current
`data_access/indexes.py` and `index_manager.py` before writing — they are the
precedent, and this project's own Learnings repeatedly record that a task's
illustrative shape must be composed around the real current file.

---

## Implementation Log

_(Filled in by the coder.)_
