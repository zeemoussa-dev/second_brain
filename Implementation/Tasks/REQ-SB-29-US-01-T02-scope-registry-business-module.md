---
id: REQ-SB-29-US-01-T02
title: New scope_registry.py business module — get/set agent vault scope
parent_story: REQ-SB-29-US-01
requirement_id: REQ-SB-29
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-29-US-01-T01]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-29-US-01-T02 — `scope_registry.py` business module

## Parent Story

- Story: [[REQ-SB-29-US-01]] — `../UserStories/REQ-SB-29-US-01-agent-to-tag-folder-scoping.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-29 *Agent-to-Tag/Folder Scoping*

---

## Objective

Add a new `app/business/scope_registry.py` module (sibling to `agent_keywords.py`, composed *alongside* `agent_registry.py`, unmodified) exposing `get_agent_scope`/`set_agent_scope`, mirroring `agent_keywords.py`'s exact composition shape over `T01`'s new `vault_writer` primitives.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed `vault_writer.load_agent_scope`/`save_agent_scope`/`load_all_agent_scopes`.
- `app/business/agent_keywords.py` already exists as the exact shape precedent: `get_agent_keywords(agent_id)` / `set_agent_keywords(agent_id, keywords) -> list[str]`, both one-line compositions over the matching `vault_writer` primitives.

**After / Outputs:**
- New `src/backend/app/business/scope_registry.py`: `get_agent_scope(agent_id: str) -> list[str]`, `set_agent_scope(agent_id: str, scope: list[str]) -> list[str]`.

---

## Files to Modify

- `src/backend/app/business/scope_registry.py` (new):
  ```python
  """Per-agent vault tag/folder scope -- what an agent CAN REACH, not what
  it knows (REQ-SB-29-US-01; keywords, REQ-SB-20/ADR-017, describe what an
  agent knows -- a deliberately separate, non-overlapping dimension).
  Mirrors agent_keywords.py's exact composition shape. Composed alongside
  app/business/agent_registry.py, not inside it -- agent_registry.py
  itself is not modified (ADR-011 point 2's "agent identity/type/actions
  stay hardcoded" reasoning stays untouched).

  get_agent_scope is also the real per-agent scope lookup ADR-025 point 6's
  fail-closed vault_write_tools._is_within_assigned_scope(...) seam names
  as a stable future contract (REQ-SB-04-US-01-T03, still blocked, ESC-026)
  -- this function's own name/signature must stay stable; wiring that seam
  to actually call it is REQ-SB-04-US-01-T03's own task, not this one."""
  from app.data_access import vault_writer


  def get_agent_scope(agent_id: str) -> list[str]:
      return vault_writer.load_agent_scope(agent_id)


  def set_agent_scope(agent_id: str, scope: list[str]) -> list[str]:
      """Whole-list replace semantics, matching the free-text kv-list
      editing UX the Agent Settings panel already uses for Keywords."""
      vault_writer.save_agent_scope(agent_id, scope)
      return scope
  ```

---

## Constraints

- Inherits from parent story: multi-scope-per-agent (whole-list replace, never a single-value model).
- `agent_registry.py` is NOT modified by this task.
- No cross-agent scan function is added here (unlike `agent_keywords.py`'s `list_candidate_agents_for_keyword_match`) — this story's own Non-Goals rule out any routing/matching mechanism reusing scope; `get_agent_scope`/`set_agent_scope` are the whole of this module.

---

## Tests

<!-- This task has no locked AC of its own — a one-line business-layer
composition with no directly observable HTTP/user-facing outcome by
itself; every locked AC is verified further up the chain (T04/T05).
Mirrors REQ-SB-20-US-01-T02's own precedent for the identical shape of
task. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv` (real configured `vault_path`), confirm `scope_registry.get_agent_scope("email-capture")` returns `[]` before any assignment. Call `scope_registry.set_agent_scope("email-capture", ["customer/masdar"])`; confirm it returns `["customer/masdar"]` and that `vault_writer.load_agent_scope("email-capture")` independently confirms the same persisted value. Delete the throwaway `agent_scopes.json` entry (or the whole file, if it did not exist before this check) afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `get_agent_scope(agent_id)` returns `vault_writer.load_agent_scope(agent_id)` verbatim
- [x] `set_agent_scope(agent_id, scope)` calls `vault_writer.save_agent_scope(agent_id, scope)` and returns `scope`
- [x] `agent_registry.py` not modified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any API surface — `T03`.
- The scope-aware MCP tool — `T04`.
- Wiring `vault_write_tools._is_within_assigned_scope`'s real body to call `get_agent_scope` — `REQ-SB-04-US-01-T03` (still blocked; `ESC-026` stays `Open` until that story is decomposed and built).

---

## Context / Notes

**Why this file's public contract matters beyond this story:** `get_agent_scope(agent_id)`'s name and signature are treated as effectively public API, not private to this story's own retrieval feature — `Implementation/Architecture/architecture.md`'s "Agent-to-Tag/Folder Vault Scoping" section is explicit that a future, still-blocked `REQ-SB-04-US-01-T03` task depends on calling it exactly as named here. Do not rename or reshape it without checking that note first.

---

## Implementation Log

**2026-08-14 — Implemented and verified.** New `src/backend/app/business/
scope_registry.py` created exactly as specified — a two-function
composition over `T01`'s `vault_writer.load_agent_scope`/
`save_agent_scope`. `app/business/agent_registry.py` was not touched
(confirmed — not in this task's own diff).

This task carries no locked AC of its own (non-AC smoke check only, per
its own Tests block).

**Smoke check:** `.second-brain/agent_scopes.json` did not exist before
this check. `scope_registry.get_agent_scope("email-capture")` → `[]`
before assignment. `scope_registry.set_agent_scope("email-capture",
["customer/masdar"])` → returned `["customer/masdar"]`; an independent
`vault_writer.load_agent_scope("email-capture")` call confirmed the same
persisted value. Since the file did not exist before this check, the
whole throwaway file was deleted afterward (confirmed
`path.exists()` → `False`), restoring the clean pre-task state. PASS.

`gate: clear` 2026-08-14 — no MUST-FLAG trigger fired.

Status: `Ready` → `Done`.
