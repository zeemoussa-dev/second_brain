---
id: REQ-SB-37-US-01-T01
title: vault_writer.py — agents_registry.json load/save primitives
parent_story: REQ-SB-37-US-01
requirement_id: REQ-SB-37
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-37-US-01-T01 — vault_writer.py — agents_registry.json load/save primitives

## Parent Story

- Story: [[REQ-SB-37-US-01]] — `../UserStories/REQ-SB-37-US-01-agent-creation.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-37 *Agent Creation Wizard*

---

## Objective

Add the new eleventh `.second-brain/` state-file pair — `load_agents_registry_state()`
/ `save_agents_registry_state()` — byte-for-byte mirroring
`load_skills_state()`/`save_skills_state()`'s existing pure-I/O shape
(`ADR-030` point 1), so `T02`'s `agent_registry.py` has a real, persisted
place to read/write runtime-created agents.

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.py` already has `_STATE_DIR = ".second-brain"` and the
  established `_<NAME>_FILE` constant + `_<name>_state_path()` +
  `load_<name>_state()` / `save_<name>_state()` triad, most directly
  precedented by `_AGENT_SKILLS_FILE` / `_skills_state_path()` /
  `load_skills_state()` / `save_skills_state()`.

**After / Outputs:**
- A new `_AGENTS_REGISTRY_FILE = "agents_registry.json"` constant.
- `load_agents_registry_state() -> dict | None` and
  `save_agents_registry_state(state: dict) -> None`, pure I/O — no default
  content computed here (`ADR-003`; the `{"created_agents": {}}` seed shape
  is a business-layer decision owned by `T02`'s `agent_registry.py`).

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py`:
  1. Add the new file-name constant alongside the existing `_AGENT_*_FILE`
     constants (near line 25, after `_AGENT_SKILLS_FILE`):
     ```python
     _AGENTS_REGISTRY_FILE = "agents_registry.json"
     ```
  2. Add the new path helper + load/save pair, placed alongside
     `_skills_state_path()`/`load_skills_state()`/`save_skills_state()`
     (mirroring that block verbatim, one concept over):
     ```python
     def _agents_registry_state_path():
         state_dir = settings.vault_path / _STATE_DIR
         state_dir.mkdir(parents=True, exist_ok=True)
         return state_dir / _AGENTS_REGISTRY_FILE


     def load_agents_registry_state() -> dict | None:
         """Pure I/O — returns None if agents_registry.json doesn't exist
         yet (no default content is computed here, per ADR-003; the
         {"created_agents": {}} seed shape and the seed-plus-persisted
         merge with _SEED_AGENTS are business-layer decisions owned by
         app/business/agent_registry.py, ADR-030)."""
         path = _agents_registry_state_path()
         if not path.exists():
             return None
         return json.loads(path.read_text(encoding="utf-8"))


     def save_agents_registry_state(state: dict) -> None:
         path = _agents_registry_state_path()
         path.write_text(json.dumps(state, indent=2), encoding="utf-8")
     ```

---

## Constraints

- Inherits from parent story and `ADR-030` point 1 — must mirror
  `load_skills_state()`/`save_skills_state()`'s exact pure-I/O contract:
  returns `None` (never `{}` or a seeded default) when the file doesn't
  exist; no default content computed in `data_access`.
- Do not touch `agent_registry.py` in this task — that composition is
  `T02`'s own scope (`ADR-030` point 3).
- Do not reorder or otherwise change any other function in `vault_writer.py`.

---

## Tests

<!-- This task is pure plumbing one layer below every locked AC's own
user/API-observable outcome — no locked AC is tagged here directly,
mirroring REQ-SB-27-US-01-T01's own precedent (the equivalent
load_skills_state/save_skills_state primitives task also carried zero
AC-tagged steps). Every locked AC is verified downstream, in T03/T04. -->

**Manual verification steps** (Python shell, from `src/backend`, backend
`.venv` active; delete any leftover `.second-brain/agents_registry.json`
first):

1. Non-AC smoke check: `from app.data_access import vault_writer` — call
   `vault_writer.load_agents_registry_state()`. Confirm it returns `None`
   (the file does not exist yet) and that no file was created as a side
   effect of the read.
2. Non-AC smoke check: call
   `vault_writer.save_agents_registry_state({"created_agents": {}})`.
   Confirm `.second-brain/agents_registry.json` now exists, containing
   exactly `{"created_agents": {}}` (indent=2, matching every other
   `_<name>_state_path()`-backed file's own on-disk formatting).
3. Non-AC smoke check: call `vault_writer.load_agents_registry_state()`
   again. Confirm it now returns `{"created_agents": {}}` — a real
   round-trip, not a cached in-process value (mirrors the "no
   module-level caching anywhere" property `ADR-030`'s own Context relies
   on for every other registry).
4. Clean-up: delete `.second-brain/agents_registry.json` — `T02`'s own
   verification does not depend on any pre-existing state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `load_agents_registry_state()` returns `None` when
      `agents_registry.json` doesn't exist yet — no default content
      computed here
- [x] `save_agents_registry_state(state)` writes the given dict verbatim,
      `indent=2`, matching every other `_<name>_state_path()`-backed file's
      on-disk shape
- [x] A real load/save/load round-trip returns the exact dict written, with
      no in-process caching
- [x] `agent_registry.py` not modified by this task
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The `{"created_agents": {}}` seed shape, the seed-plus-persisted merge
  with `_SEED_AGENTS`, and `create_agent` itself — all `T02`.
- Any HTTP surface — `T03`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-030` created at
`/plan-tasks` step 1) — the human reviews `ADR-030` and this task
breakdown together; the pipeline does not halt, so this task proceeds to
`Ready` alongside the rest of the story.

This is the first-ever file I/O `agent_registry.py` will depend on
(`ADR-030` Consequences) — this task itself does not touch
`agent_registry.py`, it only lands the two primitives `T02` composes.

---

## Implementation Log

**Coder pass, 2026-08-14.** Implemented exactly per the task's own code
sample — added `_AGENTS_REGISTRY_FILE = "agents_registry.json"` alongside
the other `_AGENT_*_FILE` constants, and `_agents_registry_state_path()` /
`load_agents_registry_state()` / `save_agents_registry_state()` placed
directly after `save_skills_state()`, mirroring that block verbatim. No
deviation from the plan.

No locked AC is tagged in this task (pure plumbing, per its own `## Tests`
note) — all 4 non-AC smoke-check steps run for real, from `src/backend`,
against the real configured vault (`settings.vault_path`, resolved via
`app.config.settings`, not the backend cwd — confirmed the real
`.second-brain/agents_registry.json` path is vault-relative, same as
every other state file):

1. `load_agents_registry_state()` before the file exists → confirmed `None`,
   confirmed no file was created as a side effect (`path.exists()` still
   `False`).
2. `save_agents_registry_state({"created_agents": {}})` → confirmed
   `.second-brain/agents_registry.json` now exists with exactly
   `{\n  "created_agents": {}\n}` (indent=2), matching every other
   `_<name>_state_path()`-backed file's own on-disk formatting.
3. `load_agents_registry_state()` again → confirmed it returns
   `{'created_agents': {}}`, a real disk round-trip (no module-level
   caching in this file to begin with, consistent with the rest of this
   module).
4. Deleted `.second-brain/agents_registry.json` — confirmed removed, no
   pre-existing state left for `T02`'s own verification.

`agent_registry.py` not touched by this task (confirmed — grep shows zero
edits to that file in this change).

gate: clear 2026-08-14 — no MUST-FLAG trigger fired during this coder pass
(no new assumption beyond the task's own explicit code sample, no ADR
change, no escalation, all steps verified, no ambiguity). Story-level
`gate: flagged` (trigger-3, `ADR-030`) was already resolved by the human
prior to this build starting.

**Status: Done.**
