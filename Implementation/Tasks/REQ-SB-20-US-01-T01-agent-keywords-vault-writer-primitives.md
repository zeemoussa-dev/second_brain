---
id: REQ-SB-20-US-01-T01
title: Add agent_keywords.json load/save primitives to vault_writer.py
parent_story: REQ-SB-20-US-01
requirement_id: REQ-SB-20
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-017 created) — carried from the parent story; the human reviews ADR-017 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: []
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-20-US-01-T01 — Add `agent_keywords.json` load/save primitives to `vault_writer.py`

## Parent Story

- Story: [[REQ-SB-20-US-01]] — `../UserStories/REQ-SB-20-US-01-section-hub-intelligence-and-cross-section-routing.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-20 *Section Hub Intelligence & Cross-Section Routing*

---

## Objective

Add the paired `load_agent_keywords()` / `save_agent_keywords()` / `load_all_agent_keywords()` pure-I/O primitives for a new, seventh `.second-brain/` state file (`agent_keywords.json`), per `ADR-017` point 2 — no business rules here (composition with `section_registry`/`agent_registry` is `T02`'s job), per `ADR-003`'s layering.

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.py` already has the `agent_communication_history.json` primitive pair (`append_agent_history_entry`/`load_agent_history`, `ADR-011`) as the closest existing shape precedent — a flat, per-agent-id-keyed JSON index, not `agent_sections.json`'s registry+assignments shape (`ADR-017` point 1 explicitly rejects mirroring that shape for keywords).
- `vault_writer.py` currently ends (after `load_providers_state`) with the `_AGENT_PROVIDERS_FILE`-backed functions.

**After / Outputs:**
- Three new functions appended to `vault_writer.py`: `load_agent_keywords(agent_id: str) -> list[str]`, `save_agent_keywords(agent_id: str, keywords: list[str]) -> None`, `load_all_agent_keywords() -> dict[str, list[str]]`. No existing function's behavior changed.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add a new constant next to the existing `_AGENT_PROVIDERS_FILE` constant:
  ```python
  _AGENT_KEYWORDS_FILE = "agent_keywords.json"
  ```
  Append at the end of the file:
  ```python
  def _agent_keywords_path():
      state_dir = settings.vault_path / _STATE_DIR
      state_dir.mkdir(parents=True, exist_ok=True)
      return state_dir / _AGENT_KEYWORDS_FILE


  def _load_agent_keywords_index() -> dict[str, list[str]]:
      path = _agent_keywords_path()
      if not path.exists():
          return {}
      return json.loads(path.read_text(encoding="utf-8"))


  def load_agent_keywords(agent_id: str) -> list[str]:
      """Pure I/O — returns [] if agent_keywords.json doesn't exist yet, or
      if agent_id has no entry in it (ADR-017 point 2/4: an agent with no
      keywords is the ordinary, expected starting state — no seed list,
      unlike Sections/Providers, since free-text keywords have no sensible
      universal default)."""
      return _load_agent_keywords_index().get(agent_id, [])


  def save_agent_keywords(agent_id: str, keywords: list[str]) -> None:
      """Whole-list replace for agent_id's own entry — mirrors the
      free-text kv-list editing UX the Settings panel already uses for
      other per-agent fields (ADR-017 point 3); no incremental
      add/remove-one-keyword primitive exists or is needed."""
      path = _agent_keywords_path()
      index = _load_agent_keywords_index()
      index[agent_id] = keywords
      path.write_text(json.dumps(index, indent=2), encoding="utf-8")


  def load_all_agent_keywords() -> dict[str, list[str]]:
      """Whole-file read — needed because the routing node (REQ-SB-20-US-01-T05)
      must scan every OTHER agent's keywords, not one agent's own; no
      existing vault_writer primitive does a whole-file read for a
      per-agent-keyed store (ADR-017 point 2)."""
      return _load_agent_keywords_index()
  ```

---

## Constraints

- Inherits from parent story: `ADR-017` point 1's exact file shape (`{agent_id: [keyword, ...]}`) — this task does not enforce that shape (pure I/O, whatever `keywords` list is handed to `save_agent_keywords` is written verbatim under that `agent_id` key), enforcement/composition is `T02`'s job.
- This file lives in `data_access/` only — no business rules, no HTTP concerns, no reference to `agent_registry.py`/`section_registry.py`.
- Must NOT modify any existing `vault_writer.py` function's behavior — additive only.
- No starting-keyword seed content is written by this task — `agent_keywords.json` does not exist until the first `save_agent_keywords` call (`ADR-017`'s own Consequences: "seeded empty — no starting-keyword seed list").

---

## Tests

<!-- This task has no locked AC of its own — vault_writer.py's primitives
are an internal data_access building block with no directly observable
HTTP/user-facing outcome by themselves; every locked AC is verified further
up the chain (T05/T06) once the business layer and API surface exist. Its
own verification is a non-AC smoke check, mirroring REQ-SB-18-US-01-T01's
own precedent for the identical shape of task. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv` (`.venv\Scripts\python.exe`, real configured `vault_path`), confirm `load_agent_keywords("email-capture")` returns `[]` when `.second-brain/agent_keywords.json` does not yet exist. Confirm `load_all_agent_keywords()` returns `{}` too. Call `save_agent_keywords("email-capture", ["email", "inbox"])`; confirm the file now exists with `{"email-capture": ["email", "inbox"]}` (`json.loads` round-trips it identically). Call `load_agent_keywords("email-capture")` again; confirm it now returns `["email", "inbox"]`. Call `load_agent_keywords("todo-capture")` (never saved); confirm it returns `[]` — a different, still-unassigned agent is unaffected. Call `load_all_agent_keywords()`; confirm it returns `{"email-capture": ["email", "inbox"]}`. Delete the throwaway file afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `load_agent_keywords(agent_id)` returns `[]` when the file doesn't exist or `agent_id` has no entry, else that agent's own list
- [x] `save_agent_keywords(agent_id, keywords)` writes `keywords` verbatim under `agent_id`'s key, preserving every other agent's existing entry
- [x] `load_all_agent_keywords()` returns the whole index dict (`{}` if the file doesn't exist)
- [x] No existing `vault_writer.py` function's behavior changed
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Composition with `section_registry.py`/`agent_registry.py`, the keyword-substring matching function, and the whole-list-replace business rule enforcement — all `T02` (`agent_keywords.py`).
- Any API surface — `T03`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-017` created at `/plan-tasks` step 1) — the human reviews `ADR-017` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

`vault_writer.py` currently ends with the `_AGENT_PROVIDERS_FILE`-backed functions (`load_providers_state`, per `REQ-SB-19-US-01-T01`); append the three new functions and the new constant directly after them. No new imports required — `json`, `settings`, `_STATE_DIR` all already exist in this module.

---

## Implementation Log

**Built 2026-08-12 (coder).** Added `_AGENT_KEYWORDS_FILE` constant and
`load_agent_keywords`/`save_agent_keywords`/`load_all_agent_keywords`
appended verbatim per this task's own code block, after `load_skills_state`/
`save_skills_state` (the real current end of `vault_writer.py` — one
sibling file further than the task's own "ends with `_AGENT_PROVIDERS_FILE`-
backed functions" description, since `REQ-SB-27-US-01`'s skills primitives
have since landed there; composed after the real current end of the file,
not the stale described position — no behavior difference, purely additive
either way).

**Live verification (real backend `.venv`, real configured `vault_path`):**
non-AC smoke check — `load_agent_keywords("email-capture")` returned `[]`
before any file existed; `load_all_agent_keywords()` returned `{}`;
`save_agent_keywords("email-capture", ["email", "inbox"])` created
`agent_keywords.json` with exactly `{"email-capture": ["email", "inbox"]}`;
`load_agent_keywords("email-capture")` returned `["email", "inbox"]`;
`load_agent_keywords("todo-capture")` (never saved) returned `[]`,
unaffected; `load_all_agent_keywords()` returned the single-entry index.
Throwaway file deleted afterward (real production file did not exist yet
at this point in the build — no lasting state affected). **PASS.**

No locked AC — non-AC smoke check only, per this task's own `## Tests`
placement rule (verified further up the chain at `T02`/`T05`/`T06`).

gate: flagged (carried, `ADR-017` — unresolved by this task itself, per
its own gating note).
