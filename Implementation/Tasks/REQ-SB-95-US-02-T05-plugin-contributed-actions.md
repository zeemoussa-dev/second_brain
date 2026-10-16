---
id: REQ-SB-95-US-02-T05
title: Plugin-contributed Actions through the app.plugin_api facade, composed at read time
parent_story: REQ-SB-95-US-02
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-02-T02]
created: 2026-10-16
updated: 2026-10-16
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

- [ ] `register_action` on the `plugin_api` facade, per-plugin-instance
- [ ] Plugin Actions composed at read time, attributed, never stored
- [ ] Uninstall removes them by construction; stored Actions untouched
- [ ] No plugin id named anywhere in core
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

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

_(Filled in by the coder.)_
