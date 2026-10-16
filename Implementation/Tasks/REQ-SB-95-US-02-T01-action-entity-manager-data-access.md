---
id: REQ-SB-95-US-02-T01
title: Action entity + ActionManager + Actions data access over the data path
parent_story: REQ-SB-95-US-02
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "trigger-1 (two scope-internal judgement calls logged as assumptions: the stored `implementation` object is keyed BY kind so the exactly-one rule is a property of the saved file, and `data_access.action_file()` is public rather than private)"
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

- [x] `Action` entity carries exactly the `ADR-032`/`ADR-033` fields
- [x] `ActionManager` is the sole gateway; `data_access/actions.py` does raw I/O only
- [x] Exactly-one-implementation refused at save, with a message naming the rule
- [x] Round-trip preserves inputs, required flags, `allowed_callers`, confirmation flag
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      — deliberately NOT updated: no atomic framework rule emerged (see the log below)
- [x] `CHANGELOG.md` entry appended

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

**2026-10-16 — built, all five AC-tagged tests passing.**

### What was built

- `src/backend/app/business/core/actions/action.py` — `Action`, `ActionInput`,
  `ActionImplementation`, plus the `IMPLEMENTATION_KINDS = ("skill", "http", "ui")`
  tuple that both the entity and the cardinality rule read. Field shapes per
  `ADR-033`: a `skill` names the deployed Skill by the bare slug
  `SkillManager.deploy(skill_id, profile_id)` itself takes; an `http` names
  `method` + `path` on this app's own route table; a `ui` names a registered
  front-end `feature_key`.
- `src/backend/app/business/core/actions/action_manager.py` — `get_all()` /
  `get_by_id()` / `create()` / `update()` / `delete()` / `import_action()`.
  Cardinality is enforced in one place, `_require_exactly_one_implementation()`,
  shared by all three write paths, and it raises
  `ActionImplementationCardinalityError` **before** any write.
- `src/backend/app/data_access/actions.py` — `list_action_ids` /
  `read_action_json` / `write_action_json` / `delete_action_definition` over
  `("data", "Actions")`, mirroring `data_access/indexes.py` function for
  function. No defaults applied, no shape validated, and deliberately no
  cardinality check (a refusal must not depend on which door the write came
  through).
- `src/backend/app/business/core/actions/__init__.py` — package docstring,
  including the `ADR-033` warning that `section_access.json` already calls a
  Skill's declared write caller an "Action" and that this kind is unrelated to it.
- `src/backend/tests/test_action_artifact_kind.py` — the five AC-tagged tests.

### Verification — automated (`pytest` from `src/backend`)

Command: `.venv/Scripts/python.exe -m pytest tests/test_action_artifact_kind.py -q`
→ **5 passed in 0.08s**. Full suite, `.venv/Scripts/python.exe -m pytest -q` →
**415 passed, 1 warning in 59.43s** (410 before this task + the 5 added here; no
pre-existing test changed).

| AC | Test (observed outcome) |
|---|---|
| `REQ-SB-95-US-02-AC-01` | `test_a_saved_action_round_trips_everything_the_operator_authored` — **passed.** Saved with two typed inputs (`entity_name` required, `note` optional), `allowed_callers: ["cbo-agent"]`, `needs_confirmation: true`; `write_action_json` received it under `make-strategic-entity` with `"id": "make-strategic-entity"`; `get_by_id()` returned both inputs with their original `required` flags (`True`/`False`, not coerced), the same `allowed_callers` and `needs_confirmation is True`; `get_all()` listed `("make-strategic-entity", "Promote a customer to a Strategic Entity", "skill")`. |
| `REQ-SB-95-US-02-AC-01` | `test_the_store_is_the_data_paths_own_actions_folder` — **passed.** With `settings.second_brain_data_path` monkeypatched to a tmp dir, the resolved `Path` is `<tmp>/data/Actions/make-strategic-entity/Action.json`; a real write landed there and read back through `list_action_ids`/`read_action_json`. |
| `REQ-SB-95-US-02-AC-03` | `test_an_action_naming_no_implementation_is_refused` — **passed.** `ActionImplementationCardinalityError`: "an Action has exactly one implementation -- one of skill, http or ui, never zero and never two; this one names none". The recorded write attempts list was empty. |
| `REQ-SB-95-US-02-AC-03` | `test_an_action_naming_two_implementations_is_refused` — **passed.** A payload naming both a `skill` and an `http` raised the same refusal; no write attempt recorded. |
| `REQ-SB-95-US-02-AC-03` | `test_an_action_naming_exactly_one_implementation_is_saved` — **passed.** One `http` implementation was written verbatim and read back as `kind == "http"`, `path == "/vault-index/refresh"`. |

**Manual verification:** none required (no screen), as the Tests block states.

### Scope-internal judgement calls (assumptions for human spot-check)

1. **The stored `implementation` object is keyed BY kind** —
   `"implementation": {"skill": {"skill_id": "vault-search"}}`, not
   `{"kind": "skill", ...}`. `AC-03` requires a payload that *names both a skill
   and an http* to be refusable, which a single normalised `kind` field cannot
   even express; keying by kind makes "exactly one" a property of the saved file
   itself, so `create()`, `update()` and `import_action()` share one rule, one
   message, and one shape with no normalisation step between payload and store.
   **Downstream consequence:** `T02`–`T06`, and the `actions/<id>/Action.json`
   bundle payload in `T04`, inherit this shape.
2. **`data_access.actions.action_file()` is public** where
   `indexes.py`'s equivalent `_index_file()` is private — the task's own Tests
   block asks for an assertion on "the resolved `Path`", and `T02`'s broken-entry
   report will want the same resolver rather than rebuilding the path.
3. **An action id is taken verbatim**, not slugged and not shape-checked, exactly
   as the `Index`/`Pipeline` precedents take theirs. Validating the id's shape
   belongs to the API layer (`T03`), which is where a caller-supplied id first
   arrives.
4. **No long-path helper in `list_action_ids()`.** The 260-character trap is real
   on this host, but this store is a fixed two-level folder in the App Database
   Folder (`data/Actions/<id>/Action.json`) with no recursion and no vault
   involvement — it is not a vault walk, and the `Index` precedent this task is
   told to mirror reads it the same way.
5. **`get_all()` and `get_by_id()` tolerate a definition with no implementation**
   (it reads back as `implementation=None`) rather than raising, so one bad entry
   cannot make the whole catalogue unreadable. That is the hook `T02`'s read-side
   broken-entry status attaches to; the save path is what guarantees it cannot
   arise from this app.

### Not done, deliberately

- **`MEMORY.md` was not touched.** Nothing here is an atomic framework rule that
  future tasks must not break: the store path and the cardinality rule are
  already `ADR-032`'s, the field shapes already `ADR-033`'s, and the
  "`Action` names two different things" warning is already recorded in `ADR-033`
  and restated in the new package docstring. `CLAUDE.md` forbids trivial entries.
- Save-time resolution (`T02`), the API (`T03`), inventory/export/import (`T04`),
  plugin Actions (`T05`) and the screen (`T06`) — untouched, as the Out of Scope
  section requires. No file outside `## Files to Modify` was changed apart from
  `CHANGELOG.md` and the story/sprint/BACKLOG status propagation.

gate: flagged 2026-10-16 — trigger 1 (material assumption). The task is `Done`
and nothing is blocked; the flag is a spot-check of judgement call 1 above,
because the stored JSON shape it fixes is inherited by five downstream tasks and
by the portable bundle. No `ESCALATIONS.md` entry — nothing out of scope, no new
dependency, no shared-interface change, no ADR deviation, no unanticipated file.
