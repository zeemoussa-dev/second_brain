---
id: REQ-SB-95-US-02-T05
title: Plugin-contributed Actions through the app.plugin_api facade, composed at read time
parent_story: REQ-SB-95-US-02
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "trigger 1/7 — two scope-internal judgement calls to spot-check (PluginContributedAction declared in action_manager.py rather than action.py, which is not in this task's Files to Modify; stored-ids-win collision rule, invented here), and one out-of-scope consequence logged as ESC-069: app/api/actions_router.py belongs to no task but must carry the plugin_id onto the HTTP surface and map the new refusal to 409 before T06's AC-06 row can render"
phase: P2
depends_on: [REQ-SB-95-US-02-T02]
created: 2026-10-16
updated: 2026-10-18
---

# REQ-SB-95-US-02-T05 — Plugin-Contributed Actions

## Parent Story

- Story: [[REQ-SB-95-US-02]] — `../UserStories/REQ-SB-95-US-02-action-sixth-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Let an installed plugin contribute Actions into the one catalogue through the
`app.plugin_api` facade, composed at read time and attributed to the plugin id —
so uninstalling removes them by construction.

---

## Starting State → End State

**Before / Inputs:**

- `app/plugin_api.py`'s `PluginApi` is the single surface a plugin may import
  (`ADR-022`), already carrying `register_router`, `register_subject_enricher`,
  `register_agent_matcher`, `register_people_folders`,
  `register_seed_data_file`, `provide_service` / `get_service` — each a
  per-plugin-instance collection.
- `ActionManager.get_all()` returns stored Actions only.

**After / Outputs:**

- `PluginApi.register_action(...)` alongside the existing registrations, same
  per-plugin-instance collection shape, so every contributed Action is
  attributable to its `plugin_id` without core naming any plugin.
- `ActionManager.get_all()` returns stored Actions **plus** whatever the loaded
  plugins registered; each plugin-contributed entry carries the contributing
  `plugin_id`.
- A plugin Action is **never written** into `<DATA_PATH>/data/Actions/` — it
  exists only while its plugin is loaded.
- A plugin Action's `http` implementation may name its own mounted
  `/plugins/<plugin_id>/...` route and resolves through `T02`'s route-table
  check unchanged.
- A plugin-contributed Action cannot be updated or deleted through
  `ActionManager`'s write path — the refusal says it belongs to its plugin.

---

## Files to Modify

- `src/backend/app/plugin_api.py`
- `src/backend/app/business/core/actions/action_manager.py` (read-time composition)
- `src/backend/app/business/core/plugins/plugin_manager.py` (the real module that already instantiates `PluginApi` and collects per-plugin registrations — read it first)
- `src/backend/tests/test_plugin_actions.py` (new)

---

## Constraints

- Inherits from parent story.
- **Core must not name a plugin** (`ADR-022`). Composition is over whatever is
  registered; no plugin id appears in core code.
- Read-time composition only — zero writes to the Actions store from the plugin
  path, which is what makes `AC-06`'s uninstall clause true by construction
  rather than by a cleanup step.
- The install's own stored Actions must be untouched by any plugin
  registration, load or unload.

---

## Tests

**Automated tests** — `src/backend/tests/test_plugin_actions.py`, run with
`pytest tests/test_plugin_actions.py` from `src/backend`, following
`tests/test_plugin_host.py`'s existing fake-plugin technique.

1. `[REQ-SB-95-US-02-AC-06]` Register two Actions from a fake plugin and save
   one stored Action; assert `ActionManager.get_all()` returns all three in one
   list, and that each plugin one carries the contributing `plugin_id` while the
   stored one carries none.
2. `[REQ-SB-95-US-02-AC-06]` Assert no file was written under the Actions store
   for either plugin Action (the monkeypatched `write_action_json` was never
   called with their ids).
3. `[REQ-SB-95-US-02-AC-06]` Drop the fake plugin's registration (uninstall);
   assert `get_all()` no longer returns its Actions and returns the install's
   own stored Action byte-identically.
4. `[REQ-SB-95-US-02-AC-06]` Attempt to update and to delete a
   plugin-contributed Action through `ActionManager`; assert both are refused
   and nothing is written.

**Manual verification steps:**

1. `[REQ-SB-95-US-02-AC-06]` With a real installed plugin that registers an
   Action, `GET /actions` with the backend running and confirm the plugin's
   Action appears attributed to its plugin id; uninstall it, re-read, confirm it
   is gone and the install's own Actions are unchanged.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `register_action` on the `plugin_api` facade, per-plugin-instance
- [x] Plugin Actions composed at read time, attributed, never stored
- [x] Uninstall removes them by construction; stored Actions untouched
- [x] No plugin id named anywhere in core
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any plugin's own Actions (they live in the plugin repositories — `ADR-023`).
- Showing the plugin attribution on a screen — `T06`.

---

## Context / Notes

`architecture.md` → **§Plugin-Contributed Actions** is authoritative, including
the "composed at read time, never written" decision and why it makes `AC-06`
structural. Read the real current `app/plugin_api.py` and the plugin-host
registry before editing — the registration shape must match what is already
there, not a remembered version of it.

---

## Implementation Log

**2026-10-18 — coder. Built and verified. `68caf71`, `d69e6b2`.**

### Verification — automated, AC-tagged

Runner: `.venv/Scripts/python.exe -m pytest -q` from `src/backend`.
**Baseline measured before the first edit: 465 passed, 0 failed (106s).**
**After: 475 passed, 1 failed (117s)** — the failure is
`tests/test_health_check.py::test_health_reports_the_commit_the_running_code_was_loaded_from`,
the known shared-checkout race (`/health` vs a live `git rev-parse HEAD`; another
session committed mid-run, `8e720ce` → `1bba9e7`). **Re-run alone: 2 passed.** The
collected count moved 465 → 476 because another session added one test while this
one ran; the 10 new tests here are the rest of the delta. No regressions.

`[REQ-SB-95-US-02-AC-06]` — **PASS**, by the four steps this task's `## Tests`
authored, all in `src/backend/tests/test_plugin_actions.py` (10 tests, 4.39s), over
the real loader and the real facade (`test_plugin_host.py`'s fake-plugin technique,
a plugin written into a temporary App Database Folder):

1. *Two plugin Actions + one stored Action in one list, attributed* —
   `test_a_plugins_actions_join_the_installs_own_in_one_catalogue`: `get_all()`
   returns `["own-export", "reporter-monthly", "reporter-weekly"]`; both plugin
   entries carry `plugin_id == "reporter"`; the stored one has **no `plugin_id`
   attribute at all** (`not hasattr`), not an empty one.
   `test_a_contributed_action_keeps_the_fields_the_plugin_declared` pins that the
   declared description, typed inputs with their `required` flags,
   `allowed_callers`, `needs_confirmation` and the `http` implementation all
   survive the composition.
2. *Nothing written* — `test_no_contributed_action_is_ever_written_to_the_actions_store`:
   the recorded `write_action_json` calls are exactly `["own-export"]`; neither
   plugin id has an `Action.json` on disk; `list_action_ids()` is `["own-export"]`.
3. *Uninstall* — `test_uninstalling_the_plugin_takes_its_actions_and_leaves_the_installs_own`:
   after the ownership record drops the plugin and the host reloads, `get_all()` is
   `["own-export"]`, that entity compares equal to the one read before, and its
   `Action.json` is **byte-identical** (`read_bytes()` before == after).
4. *Write paths refused* — `test_a_contributed_action_cannot_be_updated_or_deleted`:
   both `update()` and `delete()` raise `PluginContributedActionIsReadOnlyError`
   naming `reporter`; no write was recorded; the Action still reads as the plugin
   declared it. `test_the_installs_own_action_is_still_writable_while_a_plugin_contributes`
   is the counterweight — the guard must not catch a stored Action.

Three further tests beyond the four required, each pinning something this task's
End State states: the plugin's `http` implementation resolving through `T02`'s
unchanged route-table check (`resolution_report()` → `resolves`); the collision
rule; and a plugin that raises after registering contributing nothing.

### Verification — the manual step, and what it actually showed

`[REQ-SB-95-US-02-AC-06]` manual step (`GET /actions` with a real installed plugin,
then uninstall and re-read) — **performed as an equivalent, out-of-tree probe**
rather than against the live install: no plugin in any plugin repository registers
an Action yet, and installing a fake one into the real App Database Folder would
disturb a shared machine. The probe mounted the real `actions_router` on a bare
FastAPI app against a temporary data path (script kept out of the repo). Observed:

- `GET /actions` → the plugin's Action is listed beside the install's own, with its
  id, description, `implementation_kind` and a live `resolves` status. ✔
- `GET /actions/{id}` → `200`, the full entity. ✔
- After uninstall → `GET /actions` → `[]`; the install's own Actions untouched. ✔
- **`GET /actions` does NOT carry the plugin attribution** — the list builds an
  explicit dict and the detail route's response model is `Action`, so `plugin_id`
  is dropped on the way out. **✘ at the HTTP layer**, correct at the Manager layer
  (tested above). `PUT` on a plugin Action raises out of the router (no 409
  mapping) instead of refusing cleanly.
  Both are in `app/api/actions_router.py`, which is in **neither this task's nor
  `T06`'s** `## Files to Modify`, and "showing the plugin attribution on a screen"
  is this task's own Out of Scope. Logged as **`ESC-069`** + a `REVIEW-QUEUE.md`
  pointer; `T06` cannot render its AC-06 row until that one file is assigned.

### Judgement calls made inside scope (spot-check these)

1. **`PluginContributedAction` is declared in `action_manager.py`, not in
   `action.py`** — a dataclass subclass of `Action` adding `plugin_id`. `action.py`
   is not in this task's `## Files to Modify`, and adding the field to `Action`
   itself would change the shape every stored Action serialises as (a `plugin_id:
   null` on `GET /actions/{id}`) for a property only the read-time composition has.
   The cost is that the attribution is invisible to anything typed on `Action`,
   which is half of the `ESC-069` gap above.
2. **Collision rule, invented here** — the architecture does not say what happens
   when a plugin registers an id the install already stores, or that two plugins
   both claim. Chosen: the install's stored ids win, then first-plugin-wins
   (install order), the dropped one logged at `warning`. It follows the task's own
   "the install's own stored Actions must be untouched" and `register_people_folders`'
   first-wins precedent. Deliberately *not* done: a `provide_service`-style rule
   forcing every contributed id to be prefixed with the plugin id — that would be a
   naming convention for an operator-visible, agent-callable id, which is a product
   decision this task does not own.
3. **`create()` is not guarded.** Saving an Action whose id a plugin contributes is
   allowed and simply makes the stored one win (with the warning). The task names
   update and delete only, and a stored Action is the thing that can be written.
4. **`FRAMEWORK_API` left at 11**, as instructed and as its own comment demands
   (bumping is live on save and takes every installed plugin dark until all are
   republished). So `register_action` is a capability no plugin can yet *declare* a
   dependency on. That is already planned for: `SPRINT-087`'s own notes hand the
   bump to `REQ-SB-95-US-05-T02` (`SPRINT-090`), which reads `plugin_api.py` first
   and bumps only if `register_action` is already there — it now is, so the
   conditional fires. Raised in `REVIEW-QUEUE.md` as a confirmation only; no plugin
   needs it before `T06`.
5. **Plugin Actions now appear in the artifact inventory too**, because
   `artifacts_inventory.py` reads `ActionManager.get_all()` — which the architecture
   requires to be the composed list. Export of one is harmless: `artifact_export.py`
   already `continue`s when there is no `Action.json`, so it contributes no payload
   rather than a broken one. Left as is; both files are out of scope.

### Scope

Only the four files in `## Files to Modify` were touched, plus the standing
`CHANGELOG.md` / `MEMORY.md` / status propagation. `ADR-022`'s "core must not name
a plugin" holds: nothing in `action_manager.py` or anywhere else in core names a
plugin id — composition is over whatever `PluginManager.get_actions()` returns.

gate: flagged 2026-10-18 — triggers 1 and 7: the judgement calls above (material
enough to spot-check) and one out-of-scope event logged as `ESC-069`.
