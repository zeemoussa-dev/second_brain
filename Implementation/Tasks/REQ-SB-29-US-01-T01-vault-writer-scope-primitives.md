---
id: REQ-SB-29-US-01-T01
title: Add agent_scopes.json load/save primitives + list_notes_matching_scope to vault_writer.py
parent_story: REQ-SB-29-US-01
requirement_id: REQ-SB-29
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-29-US-01-T01 — `vault_writer.py` scope storage + retrieval primitives

## Parent Story

- Story: [[REQ-SB-29-US-01]] — `../UserStories/REQ-SB-29-US-01-agent-to-tag-folder-scoping.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-29 *Agent-to-Tag/Folder Scoping*

---

## Objective

Add the paired `load_agent_scope()` / `save_agent_scope()` / `load_all_agent_scopes()` pure-I/O primitives for a new, sibling `.second-brain/agent_scopes.json` state file (mirroring `agent_keywords.json`'s exact shape), plus a new, independent `list_notes_matching_scope(scope)` retrieval primitive (mirroring `list_known_customers()`/`list_notes_in_kind_folder()`'s exact frontmatter-scan shape) — no business rules here, per `ADR-003`'s layering.

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.py` already has `load_agent_keywords`/`save_agent_keywords`/`load_all_agent_keywords` (`agent_keywords.json`, `REQ-SB-20-US-01-T01`) as the exact storage-shape precedent.
- `vault_writer.py` already has `list_known_customers()`/`list_notes_in_kind_folder(kind)` as the exact retrieval-shape precedent, and `list_all_note_paths()` (returns every `Work/*/*.md` path) and `read_note(path) -> tuple[dict, str]` (frontmatter, body) as the primitives to compose from.
- `vault_writer.py` currently ends with the `agent_keywords.json`-backed functions, followed by the `_AGENT_WORKING_MODES_FILE`-backed functions and (per `REQ-SB-27-US-01`) skills primitives — read the REAL current end of the file before appending; do not assume it still literally ends where an earlier task's own sample said it did.

**After / Outputs:**
- Four new functions appended to `vault_writer.py`: `load_agent_scope(agent_id: str) -> list[str]`, `save_agent_scope(agent_id: str, scope: list[str]) -> None`, `load_all_agent_scopes() -> dict[str, list[str]]`, `list_notes_matching_scope(scope: list[str]) -> list`. No existing function's behavior changed.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add a new constant next to the existing `_AGENT_KEYWORDS_FILE` constant:
  ```python
  _AGENT_SCOPES_FILE = "agent_scopes.json"
  ```
  Append at the end of the file:
  ```python
  def _agent_scopes_path():
      state_dir = settings.vault_path / _STATE_DIR
      state_dir.mkdir(parents=True, exist_ok=True)
      return state_dir / _AGENT_SCOPES_FILE


  def _load_agent_scopes_index() -> dict[str, list[str]]:
      path = _agent_scopes_path()
      if not path.exists():
          return {}
      return json.loads(path.read_text(encoding="utf-8"))


  def load_agent_scope(agent_id: str) -> list[str]:
      """Pure I/O -- returns [] if agent_scopes.json doesn't exist yet, or
      if agent_id has no entry in it. Mirrors load_agent_keywords's own
      "no assignment yet is the ordinary starting state" reasoning
      (ADR-017 point 2/4) -- an agent with no assigned scope has no bounded
      vault query access (REQ-SB-29-US-01 Scenario 6), not a seeded
      default."""
      return _load_agent_scopes_index().get(agent_id, [])


  def save_agent_scope(agent_id: str, scope: list[str]) -> None:
      """Whole-list replace for agent_id's own entry -- mirrors
      save_agent_keywords's exact free-text kv-list editing UX; no
      incremental add/remove-one-scope-entry primitive exists or is
      needed."""
      path = _agent_scopes_path()
      index = _load_agent_scopes_index()
      index[agent_id] = scope
      path.write_text(json.dumps(index, indent=2), encoding="utf-8")


  def load_all_agent_scopes() -> dict[str, list[str]]:
      """Whole-file read -- mirrors load_all_agent_keywords's own shape,
      kept for parity/future consumers."""
      return _load_agent_scopes_index()


  def list_notes_matching_scope(scope: list[str]) -> list:
      """Mirrors list_known_customers()'s/list_notes_in_kind_folder()'s
      exact frontmatter-scan pattern (REQ-SB-29-US-01) -- a note matches
      when its `tags` list intersects `scope` (tag-scoped, e.g.
      "customer/masdar") OR its immediate Work/<kind>/ folder name is
      itself named in `scope` (folder-scoped, e.g. "Pipeline"). Must NOT
      compose vault_indexing.get_index()/vault_search.py (ADR-024/
      ADR-026, REQ-SB-01/REQ-SB-02) -- this story's own Constraints reject
      building against the general indexer or any embeddings/ranking; this
      stays a narrow, independent frontmatter/folder scan, same shape as
      the two precedent functions above. An empty `scope` returns [] --
      never the whole vault, never a silent fallback."""
      if not scope:
          return []
      matches = []
      for path in list_all_note_paths():
          frontmatter, _ = read_note(path)
          tags = frontmatter.get("tags") or []
          kind_folder = path.parent.name
          if any(tag in scope for tag in tags) or kind_folder in scope:
              matches.append(path)
      return sorted(matches)
  ```

---

## Constraints

- Inherits from parent story: multi-scope-per-agent (a list, never a single string); the retrieval primitive must NOT compose `vault_indexing.get_index()`/`vault_search.py` (`REQ-SB-01`/`REQ-SB-02` stay unrelated, per the story's own Constraints and `Implementation/Architecture/architecture.md`'s "Agent-to-Tag/Folder Vault Scoping" section).
- This file lives in `data_access/` only — no business rules, no HTTP concerns, no reference to `agent_registry.py`/`scope_registry.py`.
- Must NOT modify any existing `vault_writer.py` function's behavior — additive only.
- No starting-scope seed content is written by this task — `agent_scopes.json` does not exist until the first `save_agent_scope` call, mirroring `agent_keywords.json`'s own "seeded empty" precedent.
- `list_notes_matching_scope` must return `[]` (never every note in the vault) for an empty `scope` list — an empty scope is not a wildcard.

---

## Tests

<!-- This task has no locked AC of its own — vault_writer.py's primitives
are an internal data_access building block with no directly observable
HTTP/user-facing outcome by themselves; every locked AC is verified
further up the chain (T04/T05) once the business layer and API surface
exist. Mirrors REQ-SB-20-US-01-T01's own precedent for the identical
shape of task. -->

**Manual verification steps:**
1. Non-AC smoke check (storage): in a Python shell against the backend `.venv` (`.venv\Scripts\python.exe`, real configured `vault_path`), confirm `load_agent_scope("email-capture")` returns `[]` when `.second-brain/agent_scopes.json` does not yet exist; confirm `load_all_agent_scopes()` returns `{}` too. Call `save_agent_scope("email-capture", ["customer/masdar", "Pipeline"])`; confirm the file now exists with `{"email-capture": ["customer/masdar", "Pipeline"]}`. Confirm `load_agent_scope("email-capture")` now returns that list, `load_agent_scope("todo-capture")` (never saved) still returns `[]`, and `load_all_agent_scopes()` returns the single-entry index. Delete the throwaway file afterward.
2. Non-AC smoke check (retrieval): confirm `list_notes_matching_scope([])` returns `[]`. Pick one real, currently-existing vault note (any kind/customer tag combination available in the real configured vault); call `list_notes_matching_scope([<that note's own real customer tag>])` and confirm the returned list includes that note's own path. Call `list_notes_matching_scope([<that note's own real kind-folder name>])` and confirm the same note is returned via the folder-match branch. Call `list_notes_matching_scope(["definitely-not-a-real-tag-or-folder-xyz"])` and confirm `[]` is returned (no fabricated/partial match).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `load_agent_scope(agent_id)` returns `[]` when the file doesn't exist or `agent_id` has no entry, else that agent's own list
- [x] `save_agent_scope(agent_id, scope)` writes `scope` verbatim under `agent_id`'s key, preserving every other agent's existing entry
- [x] `load_all_agent_scopes()` returns the whole index dict (`{}` if the file doesn't exist)
- [x] `list_notes_matching_scope(scope)` returns `[]` for an empty `scope`; otherwise every note whose `tags` intersect `scope` or whose immediate kind-folder name is in `scope`, and nothing else
- [x] `list_notes_matching_scope` does not import or call anything from `vault_indexing.py`/`vault_search.py`
- [x] No existing `vault_writer.py` function's behavior changed
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Composition with `agent_registry.py`/the new `scope_registry.py`, and the whole-list-replace business rule enforcement — `T02`.
- Any API surface — `T03`.
- The scope-aware MCP tool that composes `list_notes_matching_scope` with `read_note` to return real note content — `T04`.

---

## Context / Notes

Append the new constant/functions after the real current end of the file — confirm the actual last function present (not necessarily `load_agent_keywords`'s trio, since `REQ-SB-27-US-01`'s skills primitives and others may have landed after it) before appending, per this project's own established "compose around the REAL current file" Learnings pattern.

`list_notes_matching_scope`'s tag-vs-folder disambiguation logic (matching against `frontmatter.get("tags")` and `path.parent.name`) is this task's own ordinary implementation-latitude call, explicitly delegated by the architect ("Tag-vs-folder disambiguation inside the primitive is ordinary /plan-tasks implementation latitude, not a further architectural fork" — `architecture.md`, "Agent-to-Tag/Folder Vault Scoping" section).

---

## Implementation Log

**2026-08-14 — Implemented and verified.** Real current file end confirmed
via `grep ^def` before appending — the file has grown well beyond the
task's own "ends with agent_keywords/_AGENT_WORKING_MODES_FILE" sample
(a full Task-notes pipeline, `REQ-SB-09`, landed after it; real end of
file was `record_task_note` at line 1387). Appended `_AGENT_SCOPES_FILE`
constant next to the other `_AGENT_*_FILE` constants, and the four new
functions verbatim as specified, after the real last function
(`record_task_note`).

This task carries no locked AC of its own (non-AC smoke checks only, per
its own Tests block).

**Smoke check 1 (storage):** `load_agent_scope("email-capture")` → `[]`
before any save; `load_all_agent_scopes()` → `{}`. After
`save_agent_scope("email-capture", ["customer/masdar", "Pipeline"])`, the
file existed with `{"email-capture": ["customer/masdar", "Pipeline"]}`;
`load_agent_scope("email-capture")` returned that list;
`load_agent_scope("todo-capture")` (never saved) still returned `[]`;
`load_all_agent_scopes()` returned the single-entry index. Throwaway file
deleted afterward (confirmed `path.exists()` → `False`). PASS.

**Smoke check 2 (retrieval):** `list_notes_matching_scope([])` → `[]`.
Real vault has 593 notes under `Work/`. Picked a real note
(`Work/Customers/Aldar.md`, tags `["customer/aldar", "kind/customer"]`)
— note the tag-scan primitive matches against the literal `tags` list
value (`customer/aldar`, the slugified form `list_known_customers()`
does NOT itself return — that function reads the separate `customer`
frontmatter field, not `tags`; confirmed by direct inspection, not
assumed), not `list_known_customers()`'s own returned display names.
`list_notes_matching_scope(["customer/aldar"])` → 12 matches, including
the sample note. `list_notes_matching_scope(["Customers"])` (the sample
note's own kind-folder name) → 22 matches, including the sample note —
folder-match branch confirmed. `list_notes_matching_scope(["definitely-
not-a-real-tag-or-folder-xyz"])` → `[]`, no fabricated match. PASS.

Confirmed by direct source reading: `list_notes_matching_scope` imports
only `list_all_note_paths`/`read_note`, both pre-existing `vault_writer.py`
functions — no `vault_indexing`/`vault_search` import or call anywhere in
this module (only two docstring mentions of those module names, both
prose, `grep`-confirmed).

No existing function's behavior changed — purely additive.

`gate: clear` 2026-08-14 — no MUST-FLAG trigger fired; all AC-less
Acceptance Criteria checkboxes below satisfied by direct verification.

Status: `Ready` → `Done`.
