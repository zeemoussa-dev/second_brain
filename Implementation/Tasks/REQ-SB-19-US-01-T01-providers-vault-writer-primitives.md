---
id: REQ-SB-19-US-01-T01
title: Add agent_providers.json load/save primitives to vault_writer.py
parent_story: REQ-SB-19-US-01
requirement_id: REQ-SB-19
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-19-US-01-T01 — Add agent_providers.json load/save primitives to vault_writer.py

## Parent Story

- Story: [[REQ-SB-19-US-01]] — `../UserStories/REQ-SB-19-US-01-per-agent-llm-provider-selection.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-19 *Per-Agent LLM Provider Selection*

---

## Objective

Add the paired `load_providers_state()` / `save_providers_state()`
pure-I/O primitives for a new, seventh `.second-brain/` state file
(`agent_providers.json`), per `ADR-014` point 1 — no business rules
(seeding, defaulting) here; that lives in `T02`'s `provider_registry.py`.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-18-US-01-T01` has landed the sibling `load_sections_state`/
  `save_sections_state` pair (same shape, same file, independent
  concern) — this task mirrors it exactly for Providers. Both tasks are
  independent (`depends_on: []`) and can land in either order.

**After / Outputs:**
- Two new functions appended to `vault_writer.py`:
  `load_providers_state() -> dict | None`, `save_providers_state(state:
  dict) -> None`. No existing function's behavior changed.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add a new constant
  alongside `_AGENT_SECTIONS_FILE` (if `REQ-SB-18-US-01-T01` has already
  landed) or alongside `_AGENT_HISTORY_FILE` otherwise:
  ```python
  _AGENT_PROVIDERS_FILE = "agent_providers.json"
  ```
  Append at the end of the file:
  ```python
  def _providers_state_path():
      state_dir = settings.vault_path / _STATE_DIR
      state_dir.mkdir(parents=True, exist_ok=True)
      return state_dir / _AGENT_PROVIDERS_FILE


  def load_providers_state() -> dict | None:
      """Pure I/O — returns None if agent_providers.json doesn't exist yet
      (no default content is computed here, per ADR-003; the non-trivial
      pre-seeded Compass entry is a business-layer decision, owned by
      app/business/provider_registry.py, ADR-014 point 1)."""
      path = _providers_state_path()
      if not path.exists():
          return None
      return json.loads(path.read_text(encoding="utf-8"))


  def save_providers_state(state: dict) -> None:
      path = _providers_state_path()
      path.write_text(json.dumps(state, indent=2), encoding="utf-8")
  ```

---

## Constraints

- Inherits from parent story: `ADR-014` point 1's exact file shape
  (`{"providers": [{"id","name","endpoint","credential","model"}],
  "assignments": {<agent_id>: <provider_id>}}`) — this task does not
  enforce that shape (pure I/O), enforcement is `T02`'s job.
- This file lives in `data_access/` only — no business rules, no HTTP
  concerns, no reference to `app.config.settings.compass_*`.
- Must NOT modify any existing `vault_writer.py` function's behavior —
  additive only. If `REQ-SB-18-US-01-T01` has already landed by the time
  this task runs, append after its two new functions, not interleaved.

---

## Tests

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`
   (real `vault_path`), confirm `load_providers_state()` returns `None`
   when `.second-brain/agent_providers.json` does not yet exist. Call
   `save_providers_state({"providers": [{"id": "test", "name": "Test",
   "endpoint": "https://example.test", "credential": "secret", "model":
   "test-model"}], "assignments": {}})`; confirm the file now exists with
   that exact content. Call `load_providers_state()` again; confirm it
   returns that same dict, including the plaintext `credential` value (no
   masking happens at this layer — masking/never-returning-credential is
   `T03`'s router-layer job). Delete the throwaway file afterward — `T02`'s
   own verification will re-seed it.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `load_providers_state()` returns `None` when the file doesn't
      exist, else the parsed JSON dict (including `credential`, verbatim
      — no masking at this layer)
- [ ] `save_providers_state(state)` writes `state` verbatim as indented
      JSON
- [ ] No existing `vault_writer.py` function's behavior changed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Seeding the pre-populated Compass entry, self-healing default
  assignment, CRUD, `has_real_client`, or the block-until-unused remove
  check — all `T02` (`provider_registry.py`).
- Any API surface, or ever returning `credential` from an HTTP response —
  `T03`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-014` created at
`/plan-tasks` step 1) — the human reviews `ADR-014` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

---

## Implementation Log

**Built 2026-08-11 (coder).** `_AGENT_PROVIDERS_FILE = "agent_providers.json"` constant
added alongside `_AGENT_SECTIONS_FILE` (already landed by `REQ-SB-18-US-01-T01`);
`_providers_state_path()`/`load_providers_state()`/`save_providers_state()`
appended at the end of `vault_writer.py`, verbatim per this task's own code
block — pure I/O, no business rules.

**Non-AC smoke check (per this task's own Tests):** in a real Python shell
against `src/backend`'s `.venv` (real `vault_path`): removed any
pre-existing `.second-brain/agent_providers.json`; confirmed
`load_providers_state()` returned `None`; called
`save_providers_state({"providers": [{"id": "test", ...}], "assignments":
{}}})`; confirmed the file now existed with that exact content; confirmed
`load_providers_state()` returned the same dict, including the plaintext
`credential` value verbatim (no masking at this layer, as expected — `T03`'s
job); deleted the throwaway file afterward. **PASS.**

No existing `vault_writer.py` function's behavior changed — purely
additive. No new decision/pattern/constraint beyond what `ADR-014` already
records (this task is a mechanical mirror of `REQ-SB-18-US-01-T01`'s own
already-landed `load_sections_state`/`save_sections_state` pair). No
assumptions made; no locked AC on this task (this task carries no AC-tagged
step — its manual smoke check is explicitly non-AC per the task's own
Tests section).

gate: clear 2026-08-11 — no MUST-FLAG trigger fired.
