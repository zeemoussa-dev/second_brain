---
id: REQ-SB-95-US-05-T02
title: plugin_api.register_tag_namespace(namespace, entries) — the callable seam, and the single FRAMEWORK_API bump
parent_story: REQ-SB-95-US-05
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

# REQ-SB-95-US-05-T02 — Registering a Tag Namespace

## Parent Story

- Story: [[REQ-SB-95-US-05]] — `../UserStories/REQ-SB-95-US-05-entity-resolution-tag-keyed-index.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Give a plugin one way to say "I own the `<prefix>/` tag namespace, and here is
the function to ask for my current entries" — a callable asked at resolution
time, never a list captured at load time — and handle the single
`FRAMEWORK_API` bump that all of `REQ-SB-95` shares.

---

## Starting State → End State

**Before / Inputs:**

- `app/plugin_api.py`: `FRAMEWORK_API = 7`, and `PluginApi` is one instance per
  plugin carrying per-plugin collections (`routers`, `subject_enrichers`,
  `agent_matchers`, `services`, `people_folders`, `seed_data_files`) with
  `register_*` methods appending to them. `register_subject_enricher` /
  `register_agent_matcher` are the exact callable-seam precedents, and their
  `Callable[...]` type aliases are declared at module level.
- `app/business/core/plugins/plugin_manager.py` aggregates those per-plugin
  collections across `loaded_apis` in `load_all()` (e.g.
  `_plugin_agent_matchers = [m for api in loaded_apis for m in api.agent_matchers]`)
  and exposes `get_*` accessors. **Aggregation is the only place a plugin id is
  known per registration**, so cross-plugin conflict detection belongs there.
- `provide_service` is the precedent for refusing a name another plugin already
  took; `register_agent_matcher`'s docstring is the precedent for "a matcher
  that raises is skipped".
- The plugin host loads only plugins built for its **exact** `FRAMEWORK_API`
  (`MEMORY.md`, 2026-09-21), so the constant moving is what forces every
  installed plugin to be republished.
- `REQ-SB-95-US-02-T05` adds `register_action` to this same file. The two are
  the **only** `plugin_api.py` additions in `REQ-SB-95`.

**After / Outputs:**

- `PluginApi.register_tag_namespace(namespace, entries)` where
  `entries` is a **callable** returning `list[dict]` with `slug`, `name`,
  `aliases`, `domains`, `hub` and `kind`. Stored, **not invoked**, at
  registration. Declared with a module-level type alias beside
  `SubjectEnricher`/`AgentMatcher`, plain dicts out, never a framework entity
  class.
- `PluginManager` aggregates registered namespaces across loaded plugins,
  keeps the owning `plugin_id` per namespace, exposes a `get_tag_namespaces()`
  accessor, and **refuses a second registration of the same prefix naming both
  plugins**.
- **The `FRAMEWORK_API` decision, taken by reading the real file first:**
  - If `register_action` is **already present** in the real current
    `app/plugin_api.py`, this is the later of the two landings — move
    `FRAMEWORK_API` from 7 to 8 here, once, and update the module docstring's
    version narrative the way v7's own paragraph does.
  - If it is **not** present, leave `FRAMEWORK_API` at 7 and add a comment at
    the constant recording that the bump is owed by
    `REQ-SB-95-US-02` (`register_action`) as the later landing.
  - Either way the constant moves **exactly once** for all of `REQ-SB-95`
    (`ADR-037`), and the Implementation Log records which branch was taken and
    why.

---

## Files to Modify

- `src/backend/app/plugin_api.py`
- `src/backend/app/business/core/plugins/plugin_manager.py`
- `src/backend/tests/test_tag_namespace_registration.py` (new)

---

## Constraints

- Inherits from parent story.
- **A callable, never a captured list** (`ADR-037`). `Settings/Entities.md` is
  edited while the app runs, so a list captured at load time is stale by
  lunchtime, and the framework would be holding a copy of the plugin's
  business data.
- **Core names no plugin** (`ADR-022`, `ADR-023`). No `customer`, `partner` or
  `entities` string anywhere in this change.
- `kind` is an **opaque pass-through string** — never enumerated, never
  validated against a list, never mapped to a framework concept.
- **Never bump `FRAMEWORK_API` twice for `REQ-SB-95`**, and never bump it
  "to be safe". An unnecessary bump costs a republish of every installed
  plugin, on top of the seven taken this autumn.
- Do not edit `REQ-SB-95-US-02`'s task files — they belong to another story and
  are already `Ready`. The conditional read above is what makes this safe in
  either landing order; the gap in `US-02-T05`'s instructions is flagged in
  `REVIEW-QUEUE.md`.

---

## Tests

**Automated tests** — `src/backend/tests/test_tag_namespace_registration.py`,
run with `pytest tests/test_tag_namespace_registration.py` from `src/backend`;
follow `tests/test_plugin_host.py`'s existing fake-plugin technique.

1. `[REQ-SB-95-US-05-AC-08]` Register a namespace from a fake plugin with an
   `entries` callable that records every call; assert it was **not** called
   during registration/load, that the registration is attributed to the
   plugin's id, and that it IS called when entries are asked for.
2. `[REQ-SB-95-US-05-AC-08]` Call for entries twice with the callable returning
   different data each time; assert both reads see the current data — proving
   nothing was captured.
3. `[REQ-SB-95-US-05-AC-08]` Load two fake plugins registering the same
   namespace prefix; assert the second is refused and the refusal message names
   **both** plugin ids.
4. `[REQ-SB-95-US-05-AC-08]` Assert the single-bump rule holds against the real
   file: read `app/plugin_api.py`; if `register_action` is present assert
   `FRAMEWORK_API == 8`, otherwise assert `FRAMEWORK_API == 7`. (The same test
   therefore keeps passing whichever of `US-02`/`US-05` lands first, and fails
   loudly if both bumped.)
5. `[REQ-SB-95-US-05-AC-08]` Assert the facade rule: `register_tag_namespace`
   accepts and returns plain data only — no framework entity class crosses the
   seam — and that `kind` is carried through byte-identically for a value the
   framework has never seen.

**Manual verification steps:**

1. `[REQ-SB-95-US-05-AC-08]` With the backend running, install a throwaway
   local plugin that registers a namespace, confirm it loads and appears with
   its namespace attributed to it, then uninstall it and confirm the namespace
   is gone.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `register_tag_namespace(namespace, entries)` on the facade, per-plugin-instance
- [ ] `entries` stored as a callable and invoked only at resolution time
- [ ] Duplicate prefix refused, naming both plugins
- [ ] `FRAMEWORK_API` moved exactly once for all of `REQ-SB-95`, decided by reading the real file
- [ ] No plugin named in core; `kind` opaque
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any plugin's own namespace registration — that is `sb-plugins-entities`' work
  in its own repository (`ADR-023`, `ADR-035`).
- The resolver itself — `T03`.
- The tag-keyed index — `T01` (registration does **not** populate it).

---

## Context / Notes

`architecture.md` → **§Registering a Tag Namespace** and **§One Contract Bump
for All of `REQ-SB-95`**, plus `ADR-037`. Read the real current
`plugin_api.py` and `plugin_manager.py` before editing — the registration shape
must match what is actually there, and `plugin_api.py` is being extended
concurrently by `REQ-SB-95-US-02`.

---

## Implementation Log

_(Filled in by the coder.)_
