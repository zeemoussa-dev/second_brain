---
id: REQ-SB-27-US-01-T01
title: Add agent_skills.json load/save primitives to vault_writer.py
parent_story: REQ-SB-27-US-01
requirement_id: REQ-SB-27
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-27-US-01-T01 — Add agent_skills.json load/save primitives to vault_writer.py

## Parent Story

- Story: [[REQ-SB-27-US-01]] — `../UserStories/REQ-SB-27-US-01-skills-repository-registration-and-access.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-27 *Skills Repository*

---

## Objective

Add the paired `load_skills_state()` / `save_skills_state()` pure-I/O
primitives for a new, sibling `.second-brain/` state file
(`agent_skills.json`), mirroring `load_sections_state()`/
`save_sections_state()`'s exact shape (`ADR-014` point 1's own pattern,
extended one concern over) — no business rules (validation, grant/revoke
logic) here; that lives in `T03`'s `skill_registry.py`.

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.py` already has `load_sections_state()`/
  `save_sections_state()` and `load_providers_state()`/
  `save_providers_state()` as the two most recent sibling-file pairs to
  mirror.

**After / Outputs:**
- Two new functions appended to `vault_writer.py`: `load_skills_state()
  -> dict | None`, `save_skills_state(state: dict) -> None`. No existing
  function's behavior changed.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add a new constant
  alongside `_AGENT_PROVIDERS_FILE` (or whichever sibling constant is
  physically last in the file at the time this task runs):
  ```python
  _AGENT_SKILLS_FILE = "agent_skills.json"
  ```
  Append at the end of the file:
  ```python
  def _skills_state_path():
      state_dir = settings.vault_path / _STATE_DIR
      state_dir.mkdir(parents=True, exist_ok=True)
      return state_dir / _AGENT_SKILLS_FILE


  def load_skills_state() -> dict | None:
      """Pure I/O — returns None if agent_skills.json doesn't exist yet (no
      default content is computed here, per ADR-003; explicit-grant-only,
      no self-healing default assignment, is a business-layer decision
      owned by app/business/skill_registry.py)."""
      path = _skills_state_path()
      if not path.exists():
          return None
      return json.loads(path.read_text(encoding="utf-8"))


  def save_skills_state(state: dict) -> None:
      path = _skills_state_path()
      path.write_text(json.dumps(state, indent=2), encoding="utf-8")
  ```

---

## Constraints

- Inherits from parent story: the file shape is
  `{"assignments": {<agent_id>: [<skill_id>, ...]}}` — no top-level
  catalog list (unlike `agent_sections.json`'s `"sections"` array), since
  the skill catalog itself is code-level (`skill_tools.py`), never
  user-created or persisted. This task does not enforce that shape (pure
  I/O) — enforcement is `T03`'s job.
- This file lives in `data_access/` only — no business rules, no HTTP
  concerns, no reference to `agent_registry`/`skill_tools`.
- Must NOT modify any existing `vault_writer.py` function's behavior —
  additive only. Append after whichever sibling-file function pair is
  physically last in the file at the time this task runs, not interleaved.

---

## Tests

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`
   (real `vault_path`), confirm `load_skills_state()` returns `None`
   when `.second-brain/agent_skills.json` does not yet exist. Call
   `save_skills_state({"assignments": {"test-agent": ["test-skill"]}})`;
   confirm the file now exists with that exact content. Call
   `load_skills_state()` again; confirm it returns that same dict
   verbatim. Delete the throwaway file afterward — `T03`'s own
   verification does not depend on any pre-existing state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `load_skills_state()` returns `None` when the file doesn't exist,
      else the parsed JSON dict, verbatim
- [x] `save_skills_state(state)` writes `state` verbatim as indented JSON
- [x] No existing `vault_writer.py` function's behavior changed
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Skill catalog metadata, `@mcp.tool()` registration — `T02`
  (`skill_tools.py`).
- Grant/revoke CRUD, `has_skill_access`, `invoke_skill`, explicit-grant-
  only enforcement — `T03` (`skill_registry.py`).
- Any API surface — `T04` (`skills_router.py`).

---

## Context / Notes

**This task carries no locked AC-tagged step** — mirrors
`REQ-SB-19-US-01-T01`'s own precedent (a pure-I/O primitives task with
only a non-AC smoke check; every locked AC on this story is
user/API-observable and is verified in `T04`'s `## Tests`, the router
task, since this story ships zero UI).

**Was never blocked** by this story's own cross-story dependency on
`REQ-SB-25-US-01`'s scaffolding (`app/api/mcp_server.py`) — this task
only touches `vault_writer.py`, independent of the MCP server. It was
written at `status: Draft` / `gate: flagged` only because task `status:`
moves in lockstep with the parent story (Pipeline.md); now that
`REQ-SB-27-US-01-T02`'s real `depends_on` edge is wired
(`REQ-SB-25-US-01-T05`, see `ESCALATIONS.md` → `ESC-011`, `Resolved`) and
the parent story has advanced to `Ready`, this task moves to `Ready` in
lockstep too.

---

## Implementation Log

**2026-08-12 — coder.** Added `_AGENT_SKILLS_FILE` constant and
`_skills_state_path`/`load_skills_state`/`save_skills_state` to
`src/backend/app/data_access/vault_writer.py`, verbatim per this task's
own `## Files to Modify` code block — appended immediately after the new
`REQ-SB-26-US-01-T01` memory primitives (the physically-last sibling-file
pair in the file at the time this task ran, per this task's own "append
after whichever sibling-file function pair is physically last" instruction)
— no deviation.

**Non-AC smoke check (pass):** `load_skills_state()` returned `None` with
no `agent_skills.json` present; `save_skills_state({"assignments":
{"test-agent": ["test-skill"]}})` created the file with that exact
content; `load_skills_state()` returned it back verbatim. Throwaway file
deleted afterward.

No existing `vault_writer.py` function's behavior changed. `status: Ready
→ Done`.

`gate: clear 2026-08-12` — no MUST-FLAG trigger fired: implemented exactly
per the task's own literal code sample, no deviation, no assumption.
