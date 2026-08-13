---
id: REQ-SB-18-US-01-T01
title: Add agent_sections.json load/save primitives to vault_writer.py
parent_story: REQ-SB-18-US-01
requirement_id: REQ-SB-18
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-18-US-01-T01 — Add agent_sections.json load/save primitives to vault_writer.py

## Parent Story

- Story: [[REQ-SB-18-US-01]] — `../UserStories/REQ-SB-18-US-01-dynamic-agent-sections-and-assignment.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-18 *Dynamic Agent Sections & Agent-to-Section Assignment*

---

## Objective

Add the paired `load_sections_state()` / `save_sections_state()` pure-I/O
primitives for a new, sixth `.second-brain/` state file
(`agent_sections.json`), per `ADR-014` point 1 — no business rules (seeding,
defaulting) here, per `ADR-003`'s layering; that lives in `T02`'s
`section_registry.py`.

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.py` already has the `agent_communication_history.json`
  primitive pair (`append_agent_history_entry`/`load_agent_history`,
  `ADR-011`) as the most recent `.second-brain/` state-file precedent —
  this task mirrors its file-path-resolution shape, not its
  index/append shape (sections have no per-agent append log; they're one
  whole-document read/write).

**After / Outputs:**
- Two new functions appended to `vault_writer.py`:
  `load_sections_state() -> dict | None`, `save_sections_state(state:
  dict) -> None`. No existing function's behavior changed.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add a new constant next
  to the existing `_AGENT_HISTORY_FILE` constant:
  ```python
  _AGENT_SECTIONS_FILE = "agent_sections.json"
  ```
  Append at the end of the file (after `load_agent_history`):
  ```python
  def _sections_state_path():
      state_dir = settings.vault_path / _STATE_DIR
      state_dir.mkdir(parents=True, exist_ok=True)
      return state_dir / _AGENT_SECTIONS_FILE


  def load_sections_state() -> dict | None:
      """Pure I/O — returns None if agent_sections.json doesn't exist yet
      (no default content is computed here, per ADR-003; the non-trivial
      starting-5-sections default is a business-layer decision, owned by
      app/business/section_registry.py, ADR-014 point 1)."""
      path = _sections_state_path()
      if not path.exists():
          return None
      return json.loads(path.read_text(encoding="utf-8"))


  def save_sections_state(state: dict) -> None:
      path = _sections_state_path()
      path.write_text(json.dumps(state, indent=2), encoding="utf-8")
  ```

---

## Constraints

- Inherits from parent story: `ADR-014` point 1's exact file shape
  (`{"sections": [{"id", "name"}], "assignments": {<agent_id>:
  <section_id>}}`) — this task does not enforce that shape (pure I/O,
  whatever `state` dict is handed to `save_sections_state` is written
  verbatim), enforcement of the shape is `T02`'s job.
- This file lives in `data_access/` only — no business rules, no HTTP
  concerns, no reference to `agent_registry.py`.
- Must NOT modify any existing `vault_writer.py` function's behavior —
  additive only.

---

## Tests

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`
   (`.venv\Scripts\python.exe`, real configured `vault_path`), confirm
   `load_sections_state()` returns `None` when
   `.second-brain/agent_sections.json` does not yet exist. Call
   `save_sections_state({"sections": [{"id": "test", "name": "Test"}],
   "assignments": {}})`; confirm the file now exists with that exact
   content (`json.loads` round-trips it identically). Call
   `load_sections_state()` again; confirm it now returns that same dict.
   Delete the throwaway file afterward (or overwrite it — `T02`'s own
   verification will re-seed it).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `load_sections_state()` returns `None` when the file doesn't exist,
      else the parsed JSON dict
- [ ] `save_sections_state(state)` writes `state` verbatim as indented JSON
- [ ] No existing `vault_writer.py` function's behavior changed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Seeding the starting 5 sections, self-healing default assignment, CRUD,
  or the block-until-empty delete check — all `T02` (`section_registry.py`).
- Any API surface — `T03`, `T04`.

---

## Context / Notes

`vault_writer.py` currently ends with `load_agent_history`; append the two
new functions and the new constant directly after it. No new imports
required — `json`, `settings`, `_STATE_DIR` all already exist in this
module.

**Gating note:** this story is `gate: flagged` (`ADR-014` created at
`/plan-tasks` step 1) — the human reviews `ADR-014` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

---

## Implementation Log

**2026-08-11 — Done.** Added `_AGENT_SECTIONS_FILE` constant and
`_sections_state_path`/`load_sections_state`/`save_sections_state` to
`vault_writer.py`, placed directly after `load_agent_history`, matching
the task's own code block verbatim.

Non-AC smoke check (per this task's own `## Tests`): ran a Python shell
against the real backend `.venv` and real configured `vault_path`.
`load_sections_state()` returned `None` (no `.second-brain/
agent_sections.json` existed yet). Called `save_sections_state({"sections":
[{"id": "test", "name": "Test"}], "assignments": {}})`; the file was
created and `load_sections_state()` round-tripped the identical dict.
Deleted the throwaway file afterward — confirmed absent again.

gate: clear 2026-08-11 — no MUST-FLAG trigger fired; implemented exactly
per the task's own literal code block, no assumption needed.
