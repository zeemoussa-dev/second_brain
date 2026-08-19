---
id: REQ-SB-37-US-01-T02
title: agent_registry.py — AGENTS renamed _SEED_AGENTS, seed-plus-persisted overlay, new create_agent()
parent_story: REQ-SB-37-US-01
requirement_id: REQ-SB-37
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-37-US-01-T01]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-37-US-01-T02 — agent_registry.py — seed-plus-persisted overlay + create_agent()

## Parent Story

- Story: [[REQ-SB-37-US-01]] — `../UserStories/REQ-SB-37-US-01-agent-creation.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-37 *Agent Creation Wizard*

---

## Objective

Turn `agent_registry.py` from a fully static, hardcoded registry into a
static-seed-plus-persisted-JSON-overlay store, exactly per `ADR-030`:
rename `AGENTS` to `_SEED_AGENTS` (byte-identical, unchanged); make
`get_agent`/`list_agents` seed-then-persisted merges; add `create_agent`.
This is the one file every already-`Done` self-healing per-agent registry
(`section_registry.py`, `provider_registry.py`, `working_mode_registry.py`,
`skill_registry.py`, `agent_keywords.py`) depends on to pick up a created
agent automatically, with zero changes to any of those five files.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed `vault_writer.load_agents_registry_state()` /
  `save_agents_registry_state()`.
- `agent_registry.py`'s current, real shape (read this file directly
  before editing — reproduced here for reference, must not drift):
  `AGENTS: dict[str, dict]` (7 entries), `get_agent(agent_id)`,
  `list_agents()`, `get_action(agent_id, action_id)`.

**After / Outputs:**
- `agent_registry.py` exposes the exact same public call signatures
  (`get_agent`, `list_agents`, `get_action`) plus one new function
  (`create_agent`) — every existing caller elsewhere in the codebase needs
  zero changes (`ADR-030` Consequences).

---

## Files to Modify

- `src/backend/app/business/agent_registry.py` — full rewrite, per `ADR-030`
  points 2-5:
  1. Rename the module-level `AGENTS` dict to `_SEED_AGENTS` — **otherwise
     byte-identical**: same 7 keys (`email-capture`, `meeting-capture`,
     `todo-capture`, `people-producer`, `vault-qa`, `vault-filing-expert`,
     `compass-expert`), same nested `settings`/`actions` shape, in the same
     order. Do not reformat, reorder, or alter any entry's content.
  2. Update the module docstring to describe the new seed-plus-persisted
     shape (mirroring `skill_registry.py`'s own docstring style):
     ```python
     """Known-agent registry: a static, in-code seed set (_SEED_AGENTS,
     ADR-011 points 1/3/4, still Accepted) merged at read time with a new
     persisted .second-brain/agents_registry.json overlay for runtime-
     created agents (ADR-030, supersedes ADR-011 point 2 only). The 7
     shipped agents remain app/deployment configuration, in code, never
     migrated into the persisted store. Only email-capture's
     run_capture_now and compass-expert's build_knowledge have a real
     handler this pass (see app/api/agents_router.py) — every other
     declared action has none yet, seed or created.
     """
     from app.data_access import vault_writer
     ```
  3. Add the new `_load_state()`, owning only the *created* side (no
     self-healing loop — a created agent's own record already carries
     every field it needs at creation time):
     ```python
     def _load_state() -> dict:
         state = vault_writer.load_agents_registry_state()
         if state is None:
             state = {"created_agents": {}}
             vault_writer.save_agents_registry_state(state)
         return state
     ```
  4. Rewrite `get_agent`/`list_agents` as seed-then-persisted merges (seed
     agents always first, preserving today's existing 7-agent ordering):
     ```python
     def get_agent(agent_id: str) -> dict | None:
         if agent_id in _SEED_AGENTS:
             return _SEED_AGENTS[agent_id]
         return _load_state()["created_agents"].get(agent_id)


     def list_agents() -> list[dict]:
         state = _load_state()
         seed_entries = [
             {"id": agent_id, "name": agent["name"], "type": agent["type"]}
             for agent_id, agent in _SEED_AGENTS.items()
         ]
         created_entries = [
             {"id": agent_id, "name": agent["name"], "type": agent["type"]}
             for agent_id, agent in state["created_agents"].items()
         ]
         return seed_entries + created_entries
     ```
  5. `get_action` is unchanged in body — it already calls the now-merged
     `get_agent` internally:
     ```python
     def get_action(agent_id: str, action_id: str) -> dict | None:
         agent = get_agent(agent_id)
         if agent is None:
             return None
         return next((a for a in agent["actions"] if a["id"] == action_id), None)
     ```
  6. Add `create_agent`:
     ```python
     def create_agent(name: str, type: str, settings: list[dict] | None = None) -> dict:
         """agent_id is derived via vault_writer.tag_slug(name), keeping
         every agent-identifying id in this codebase human-readable and
         consistent (email-capture, compass-expert, widgets-expert), not a
         UUID/integer. Unlike create_section's idempotent-collapse-on-
         collision semantic, disambiguates on collision (-2, -3, ...)
         against the union of _SEED_AGENTS and created_agents keys — two
         distinct agent-creation calls must never silently collide into
         one shared identity, and a created agent's slug must never be
         allowed to shadow a shipped agent's id. actions: [] mirrors the
         already-Done vault-filing-expert/compass-expert "starts with zero
         pre-seeded actions" precedent — REQ-SB-39's Skills unification
         remains the only path to a created agent gaining a capability,
         via the already-Done skill_registry.grant_skill_access."""
         state = _load_state()
         known_ids = set(_SEED_AGENTS.keys()) | set(state["created_agents"].keys())
         base_id = vault_writer.tag_slug(name)
         agent_id = base_id
         suffix = 2
         while agent_id in known_ids:
             agent_id = f"{base_id}-{suffix}"
             suffix += 1
         record = {"name": name, "type": type, "settings": settings or [], "actions": []}
         state["created_agents"][agent_id] = record
         vault_writer.save_agents_registry_state(state)
         return {"id": agent_id, **record}
     ```

---

## Constraints

- Inherits from parent story and `ADR-030` in full.
- `_SEED_AGENTS`'s 7 entries must remain byte-identical to the current
  `AGENTS` dict's content — this task renames, it does not migrate, edit,
  reorder, or drop any seed entry.
- `get_agent`/`list_agents`/`get_action`'s public call signature and return
  shape must not change — every existing caller outside this file (all five
  self-healing registries, `agents_router.py`, `agent_chat.py`,
  `agent_orchestration`) must work unmodified.
- `list_agents()` must always return seed entries **before** created
  entries, preserving today's existing 7-agent ordering exactly.
- `create_agent`'s collision handling must be numeric-suffix
  disambiguation (`-2`, `-3`, ...) — never `create_section`'s
  idempotent-collapse-on-collision semantic; never allow a created agent's
  slug to shadow a `_SEED_AGENTS` key.
- May import `vault_writer` only (its first-ever dependency, per `ADR-030`
  Consequences) — must not import `section_registry`/`provider_registry`/
  any other per-agent-property module (`ADR-014`'s "composed alongside, not
  inside" layering stays intact).
- Do not touch any of `section_registry.py`, `provider_registry.py`,
  `working_mode_registry.py`, `skill_registry.py`, `agent_keywords.py` —
  `ADR-030`'s entire point is that none of them need a change.

---

## Tests

<!-- Pure business-logic layer, one below every locked AC's own
user/API-observable outcome — no locked AC is tagged here directly,
mirroring REQ-SB-27-US-01-T03's own precedent. Every locked AC is verified
downstream, in T03/T04. -->

**Manual verification steps** (Python shell, from `src/backend`, backend
`.venv` active; delete any leftover `.second-brain/agents_registry.json`
first):

1. Non-AC smoke check: `from app.business import agent_registry` — call
   `agent_registry.list_agents()`. Confirm it returns exactly the 7 seed
   agents, in the same order as before this task (`email-capture`,
   `meeting-capture`, `todo-capture`, `people-producer`, `vault-qa`,
   `vault-filing-expert`, `compass-expert`), each with `{"id", "name",
   "type"}`. Confirm `agent_registry.get_agent("compass-expert")` still
   returns the full, unchanged record (same `settings`/`actions` as
   before).
2. Non-AC smoke check: call `agent_registry.get_agent("not-a-real-agent")`
   — confirm `None` (not a `KeyError`).
3. Non-AC smoke check: call `agent_registry.create_agent("Widgets Expert",
   "expert", settings=[{"key": "Domain", "value": "Widgets manufacturing"}])`.
   Confirm the returned dict has `id == "widgets-expert"`,
   `name == "Widgets Expert"`, `type == "expert"`, the given `settings`,
   and `actions == []`. Confirm `agent_registry.get_agent("widgets-expert")`
   now returns that same record, and `agent_registry.list_agents()` now
   has 8 entries, with the 7 seed agents still first, in their original
   order, and `widgets-expert` last.
4. Non-AC smoke check (collision disambiguation): call `agent_registry.
   create_agent("Widgets Expert", "expert")` a second time (same name).
   Confirm the returned `id == "widgets-expert-2"` — a genuinely distinct
   id, not the same record returned again (unlike `create_section`'s
   idempotent-collapse behavior). Confirm `list_agents()` now has 9
   entries, both `widgets-expert` and `widgets-expert-2` present and
   distinct.
5. Non-AC smoke check (seed-shadow guard): call `agent_registry.
   create_agent("Compass Expert", "expert")` (a name that slugs to an
   existing **seed** agent's id, `compass-expert`). Confirm the returned
   `id` is `"compass-expert-2"` (or the next free numeric suffix), never
   `"compass-expert"` itself — a created agent must never shadow a shipped
   agent's id. Confirm `agent_registry.get_agent("compass-expert")` still
   returns the original **seed** record afterward, unchanged.
6. Non-AC smoke check: confirm every existing caller pattern still works —
   `agent_registry.get_action("email-capture", "run_capture_now")` returns
   the same action dict as before this task.
7. Clean-up: delete `.second-brain/agents_registry.json` — `T03`'s own
   verification does not depend on any pre-existing state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `_SEED_AGENTS` is byte-identical in content to the former `AGENTS`
      dict — same 7 entries, unchanged
- [x] `get_agent`/`list_agents`/`get_action` keep their exact existing call
      signature and return shape — no caller outside this file needs to
      change
- [x] `list_agents()` always returns seed entries before created entries,
      preserving today's existing 7-agent ordering
- [x] `create_agent` derives `agent_id` via `vault_writer.tag_slug(name)`,
      disambiguating on collision (numeric suffix) against the union of
      `_SEED_AGENTS` and `created_agents` keys — never collapses, never
      shadows a seed id
- [x] `create_agent`'s returned/stored record has `actions: []` and the
      given `settings` (or `[]` if omitted)
- [x] None of `section_registry.py`/`provider_registry.py`/
      `working_mode_registry.py`/`skill_registry.py`/`agent_keywords.py`
      modified by this task
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any HTTP surface (`POST /agents`) — `T03`.
- Any frontend — `T04`.
- Sections/Providers/working-mode/keywords/skills assignment for a created
  agent — each already self-heals via its own `agent_registry.list_agents()`
  call, per `ADR-030`; no code change needed anywhere in those five files.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-030` created at
`/plan-tasks` step 1) — the human reviews `ADR-030` and this task
breakdown together; the pipeline does not halt, so this task proceeds to
`Ready` alongside the rest of the story.

Full reasoning for every decision in this task's own code block:
`Implementation/Architecture/ADR.md` → `ADR-030`. Read `agent_registry.py`'s
REAL current file before editing (not a stale copy) — reconcile this
task's own code sample against it if anything has drifted since this task
was written, per this project's own established "compose around the real
current file" convention.

---

## Implementation Log

**Coder pass, 2026-08-14.** Read the real current `agent_registry.py`
before editing — matched the task's own "Before" description exactly (7
seed entries, `get_agent`/`list_agents`/`get_action`), no drift since this
task was written. Implemented exactly per the task's own code sample:
`AGENTS` → `_SEED_AGENTS` (byte-identical content, confirmed by diff —
only the name changed), new module docstring, new `_load_state()`,
seed-then-persisted `get_agent`/`list_agents`, unchanged-body `get_action`
(now calling the merged `get_agent`), new `create_agent`. Confirmed via
`grep` that no other file in `src/backend` accesses `agent_registry.AGENTS`
directly — every caller goes through `get_agent`/`list_agents`/`get_action`,
so no other file needed a change.

No locked AC is tagged in this task (pure business-logic layer, per its own
`## Tests` note) — all 7 non-AC smoke-check steps run for real, from
`src/backend`, against the real configured vault:

1. `list_agents()` → confirmed exactly the 7 seed agents, same order as
   before (`email-capture, meeting-capture, todo-capture, people-producer,
   vault-qa, vault-filing-expert, compass-expert`); `get_agent("compass-
   expert")` → confirmed full, unchanged record.
2. `get_agent("not-a-real-agent")` → confirmed `None`, not a `KeyError`.
3. `create_agent("Widgets Expert", "expert", settings=[{"key": "Domain",
   "value": "Widgets manufacturing"}])` → confirmed
   `id == "widgets-expert"`, `name`, `type`, `settings`, `actions == []`
   all correct; `get_agent("widgets-expert")` returns the same record;
   `list_agents()` now has 8 entries, 7 seed first in original order,
   `widgets-expert` last.
4. `create_agent("Widgets Expert", "expert")` a second time → confirmed
   `id == "widgets-expert-2"`, a genuinely distinct id; `list_agents()`
   now has 9 entries, both present and distinct.
5. `create_agent("Compass Expert", "expert")` (slugs to the seed
   `compass-expert` id) → confirmed returned `id == "compass-expert-2"`,
   never shadowing the seed id; `get_agent("compass-expert")` afterward
   still returns the original, unchanged seed record.
6. `get_action("email-capture", "run_capture_now")` → confirmed same
   action dict as before this task.
7. Deleted `.second-brain/agents_registry.json` — confirmed removed, no
   pre-existing state left for `T03`'s own verification.

`section_registry.py`/`provider_registry.py`/`working_mode_registry.py`/
`skill_registry.py`/`agent_keywords.py` — confirmed none modified by this
task (only `agent_registry.py` in the diff).

gate: clear 2026-08-14 — no MUST-FLAG trigger fired during this coder pass.

**Status: Done.**
