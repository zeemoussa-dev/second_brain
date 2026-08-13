---
id: REQ-SB-12-US-02-T01
title: New list_notes_in_kind_folder(kind) read primitive in vault_writer.py
parent_story: REQ-SB-12-US-02
requirement_id: REQ-SB-12
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-12-US-02-T01 — New list_notes_in_kind_folder(kind) read primitive in vault_writer.py

## Parent Story

- Story: [[REQ-SB-12-US-02]] — `../UserStories/REQ-SB-12-US-02-my-day-dashboard-and-drilldowns.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-12 *Primary Application UI Shell — Agents Map & My Day*

---

## Objective

Add `list_notes_in_kind_folder(kind: str) -> list`, a same-shape sibling of
`list_all_note_paths()` scoped to one `Work/<kind>/` folder, so My Day's
Emails/Calendar drill-downs can read just their own kind folder instead of
every note under `Work/`.

---

## Starting State → End State

**Before / Inputs:**
- `app/data_access/vault_writer.py`'s `list_all_note_paths()` globs
  `Work/*/*.md` across every kind folder. No primitive reads a single kind
  folder in isolation.

**After / Outputs:**
- A new `list_notes_in_kind_folder(kind: str) -> list` appended to
  `vault_writer.py`, returning sorted `Path` objects for `Work/<kind>/*.md`,
  or `[]` if that kind folder doesn't exist — mirroring
  `list_all_note_paths()`'s existing exists-check/glob/sort shape exactly.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — append directly after
  `list_all_note_paths()`:
  ```python
  def list_notes_in_kind_folder(kind: str) -> list:
      """Same shape as list_all_note_paths(), scoped to one Work/<kind>/
      folder (REQ-SB-12-US-02) — avoids reading and discarding every
      Customer/Person/Partner/Notification/File note just to filter down to
      one kind (e.g. Emails, Meetings). Returns [] if the kind folder
      doesn't exist yet (e.g. Meetings before REQ-SB-08 has ever run) —
      same not-yet-created-folder handling list_all_note_paths() already
      has for Work/ itself."""
      kind_root = settings.vault_path / _WORK_ROOT / kind
      if not kind_root.exists():
          return []
      return sorted(kind_root.glob("*.md"))
  ```

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (ADR-003) — this file stays pure filesystem I/O, no business logic.
- Must NOT modify `list_all_note_paths()` or any other existing function's
  behavior — additive only.
- `kind` is passed in verbatim (e.g. `"Emails"`, `"Meetings"`) — this
  primitive does not validate it against `list_known_kinds()`; an unknown
  kind simply resolves to a non-existent folder and returns `[]`, matching
  `list_all_note_paths()`'s existing tolerance for "folder doesn't exist yet".

---

## Tests

<!-- This primitive is exercised end-to-end by T02 (my_day.py) and T03 (the
router's live endpoints), where this story's locked ACs are tagged. The
smoke check below confirms it in isolation first. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`
   (`.venv\Scripts\python.exe`, cwd `src/backend`, real vault configured via
   `.env`), call `list_notes_in_kind_folder("Emails")`. Confirm it returns a
   non-empty sorted list of `Path` objects, each pointing at a real `.md`
   file under the vault's `Work/Emails/` folder (real captured Email notes
   already exist per `MEMORY.md`). Then call
   `list_notes_in_kind_folder("Meetings")` — confirm it returns `[]` without
   raising (the real vault's `Work/Meetings/` folder does not exist yet,
   since REQ-SB-08 hasn't run).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `list_notes_in_kind_folder(kind)` returns sorted `Work/<kind>/*.md`
      paths, or `[]` if the kind folder doesn't exist
- [x] No existing `vault_writer.py` function's behavior changed
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Reading/projecting note frontmatter into a response shape — that is T02.
- The `/my-day/*` router endpoints — that is T03.

---

## Context / Notes

`_WORK_ROOT` and `settings.vault_path` are already module-level in
`vault_writer.py` (used by `list_all_note_paths()`/`list_known_kinds()`) —
no new import needed.

---

## Implementation Log

Implemented exactly as specified — `list_notes_in_kind_folder(kind)`
appended to `vault_writer.py` directly after `list_all_note_paths()`, no
existing function touched.

**Non-AC smoke check (2026-08-11):** ran against the real vault
(`.venv\Scripts\python.exe`, cwd `src/backend`). `list_notes_in_kind_folder
("Emails")` returned 178 sorted `Path` objects under the real
`Work/Emails/`. `list_notes_in_kind_folder("Meetings")` returned 39 sorted
`Path` objects — **note:** the task's own Tests section expected `[]` here
(written when REQ-SB-08/SPRINT-006 hadn't produced any real Meeting notes
yet); by the time this task ran, SPRINT-006 had landed concurrently and the
real vault's `Work/Meetings/` folder now holds 39 real Meeting notes. This
is a stronger confirmation, not a failure — it exercises the "folder
exists, has notes" branch for real, in addition to the not-yet-existing
branch already covered by `list_notes_in_kind_folder("NoSuchKind")` ->
`[]`. Logged as an assumption (using real current vault state over the
task's now-stale expectation) per the coder's scope-internal-judgement-call
rule, not a deviation from the primitive's own contract.

gate: clear 2026-08-11 — no MUST-FLAG trigger fired for the primitive
itself (the real-vault-state note above is a scope-internal observation,
not an assumption that changed any code).
