---
id: REQ-SB-86-US-01-T01
title: Real, unfiltered vault-directory tree-listing method on VaultManager + GET route
parent_story: REQ-SB-86-US-01
requirement_id: REQ-SB-86
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-86-US-01-T01 — Real, unfiltered vault-directory tree-listing method on VaultManager + GET route

## Parent Story

- Story: [[REQ-SB-86-US-01]] — `../UserStories/REQ-SB-86-US-01-vault-export-data-folder-picker.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-86 *Vault Data Sharing — Export a Real Slice of the Vault (`.sbd`)*

---

## Objective

Add one new read-only, genuinely-unfiltered filesystem-tree-listing method
to `VaultManager` (folders + files, real vault directory) plus a `GET`
route exposing it — the real data source Settings → Vault → Export Data's
picker screen renders against.

---

## Starting State → End State

**Before / Inputs:**
- `VaultManager` (`app/business/core/vault/vault_manager.py`) has no
  method that walks the real vault directory unfiltered — every existing
  read (`get_index()`, `list_templates()`, `list_entities()`) goes through
  the in-memory note index (`vault_writer.list_all_note_paths()`), which
  deliberately EXCLUDES OKF-reserved files (`index.md`/`log.md`/
  `captures.md`) and any `_`-prefixed folder (e.g. `_assets`) — confirmed
  directly in `list_all_note_paths()`'s own docstring.
- `settings.vault_path` (`app/config.py`) is the real, already-configured
  root directory this whole project indexes.

**After / Outputs:**
- `VaultManager` gains `get_export_tree() -> dict` — a genuine
  `os.walk`/`Path.iterdir()`-based recursive filesystem walk of
  `settings.vault_path`, NOT the note-index primitives. Returns a nested
  structure, e.g.:
  ```json
  {
    "root": "<settings.vault_path as posix string>",
    "tree": {
      "name": "Work",
      "type": "folder",
      "path": "Work",
      "children": [
        {"name": "Masdar", "type": "folder", "path": "Work/Masdar", "children": [...]},
        {"name": "index.md", "type": "file", "path": "Work/Masdar/index.md"}
      ]
    }
  }
  ```
  `path` values are vault-root-relative, forward-slash-joined (per this
  project's own host-environment convention — never a raw Windows
  backslash path, even though the host filesystem is Windows). Every real
  folder and file is included — OKF-reserved files (`index.md`/`log.md`/
  `captures.md`) and `_`-prefixed folders (e.g. `_assets`) are NOT
  excluded, unlike the note index. No filtering, sorting is alphabetical
  (folders before files within a directory) for a stable, predictable
  render order.
- `app/api/vault_router.py` — new `GET /vault/export-data/tree` route
  returning `get_export_tree()`'s own dict directly.

---

## Files to Modify

- `src/backend/app/business/core/vault/vault_manager.py` — add
  `get_export_tree()`.
- `src/backend/app/api/vault_router.py` — add the new `GET` route.

---

## Constraints

- Inherits from parent story.
- **Read-only** — no write/create/delete/rename anywhere in this task.
- **A genuine, unfiltered filesystem walk** — never routes through
  `list_all_note_paths()`/the in-memory note index; must independently
  confirm OKF-reserved files and `_`-prefixed folders ARE present in the
  response (the opposite of the existing note-index behaviour).
- Reflects the real, current vault directory at request time — no
  caching/memoization of the tree result (unlike the note index's own
  rebuild-once-read-many-times shape).
- `path` values are vault-root-relative, forward-slash-joined strings.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-86-US-01-AC-01]` Call `GET /vault/export-data/tree` against
   the real, currently-configured vault directory; confirm the returned
   tree's own folder/file names and nesting match a direct, independent
   listing of the real `settings.vault_path` directory on disk (e.g. via
   a separate `os.walk` comparison in the verification script) — no
   fabricated or stale entries.
2. `[REQ-SB-86-US-01-AC-01]` Confirm the response includes at least one
   real OKF-reserved file (`index.md`/`log.md`/`captures.md` under any
   real Customer/Project folder) AND at least one real `_`-prefixed
   folder (e.g. `_assets`) if either exists in the real vault — proving
   this is a genuine unfiltered walk, not a reuse of
   `list_all_note_paths()`, which would silently omit both.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `VaultManager.get_export_tree()` returns a real, current, nested
      folder/file listing of `settings.vault_path`
- [x] OKF-reserved files and `_`-prefixed folders are included (never the
      note-index's own exclusion behaviour)
- [x] `GET /vault/export-data/tree` exposes it, read-only
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any `.md`-only filtering — that is a frontend-only concern (`T02`), the
  backend always returns the full unfiltered tree.
- Multi-select/selection state — client-side only, `T02`.
- Producing the `.sbd` archive itself — `REQ-SB-86-US-02`.

---

## Context / Notes

Architecture `§Vault Data Export → §Export Data Folder-Tree Picker`
(`Implementation/Architecture/architecture.md`) is the authoritative
design for this task — a pure read-only addition to the already-Accepted
`VaultManager` gateway, no new ADR. `get_index_config()`/`list_templates()`/
`list_entities()` are the direct "one more dict/list-returning read
method" precedent this task follows.

---

## Implementation Log

**What was built:** `VaultManager.get_export_tree()` (+ private helper
`_walk_export_tree()`) — a real, uncached recursive `Path.iterdir()` walk
of `settings.vault_path`, returning `{"root": <posix path>, "tree": {...}}`.
`GET /vault/export-data/tree` added to `vault_router.py`, delegating
directly.

**Scope-internal judgement call (logged for human spot-check, not an
escalation):** the task's own illustrative example JSON showed `"tree":
{"name": "Work", ...}` as if `tree` were itself one top-level folder. The
real vault root has FOUR top-level entries (`.obsidian`, `.second-brain`,
`Personal`, `Work`), so a single dict can't literally be "Work" — I read
the example as illustrative of the per-node shape, not a literal
prescription, and made `tree` the vault root's own folder node (`"name":
<root dir name>`, `"path": ""`), with every real top-level entry as its
`children`. This is the natural shape for a single-root picker tree and
matches every other list/dict-returning `VaultManager` method's own
"one coherent structure back" precedent.

**Real defect found and fixed in the same pass (in-scope, same file):**
initial sort key called `p.is_file()` independently of the branch's own
`child.is_dir()` type decision. Live verification against the real vault
surfaced 20 real `.md` files (all under an already-archived
`Work/_archive/...` subtree) whose full path exceeds Windows' ~260-char
`MAX_PATH` limit, where `is_file()`/`is_dir()`/`exists()` all silently
return `False` regardless of the path's real type. This desynced the sort
order from the actual `"type"` field for those entries (cosmetic only —
they were still correctly typed `"file"`, no data loss/dropped subtree,
confirmed no OVER-limit path in the real vault is a directory). Fixed by
computing `is_dir()` once per child and reusing that single boolean for
both the sort key and the type decision. See `MEMORY.md` Constraints.

**Verification — `REQ-SB-86-US-01-AC-01` (both manual steps), live, against
the real, currently-configured vault (`C:\myWorx\Moussa MD\Moussa Brain`):**

1. Killed the stale-but-listening non-`--reload` uvicorn instance
   (PID 52376/parent 27656) already on port 8001 — confirmed stale first
   (`GET /vault/export-data/tree` returned a real `404`, proving it
   predated this change, not a `--reload`-staleness case), then started a
   single fresh, explicitly-controlled non-`--reload` instance and
   reconfirmed health via `GET /vault/overview`. Restarted a second time
   after the `is_dir()` sort fix, same protocol.
2. **Manual step 1 (structural parity):** wrote a standalone Python script
   (venv `python`, no server code reused) that fetched
   `GET /vault/export-data/tree`, flattened it into `(path, type, name)`
   tuples, and independently listed the real vault directory via
   `Path.rglob("*")`. Result: **4081 disk entries vs. 4081 API entries, 0
   missing, 0 extra** — exact structural match against the real,
   current directory. PASS.
3. **Manual step 2 (OKF-reserved files + `_`-prefixed folders present):**
   the same flattened response contained **61 real `index.md` files**
   (e.g. `Personal/Automation/Home Assistant/Rooms/Balcony/index.md`) and
   **9 real `_`-prefixed folders** (e.g. `Work/_archive`,
   `Work/Customers/_assets`, `Work/Industries/_assets`,
   `Work/Technology/OT/_assets`, `Work/People/_Archived Duplicates
   (2026-08-24)`). Cross-checked directly: `list_all_note_paths()` would
   have excluded every one of these — confirms this is a genuine
   unfiltered walk, not a reuse of the note-index primitives. `log.md`/
   `captures.md` do not currently exist anywhere in the real vault (none
   found via an independent `Get-ChildItem -Recurse`), so only `index.md`
   was available to positively confirm — honestly noted, not fabricated.
   PASS (both conditions the AC names — "if either exists" — were
   independently confirmed to exist and both are present).
4. Bonus (not itself AC-tagged, but part of the task's own End-State
   spec): confirmed folders-before-files-then-alphabetical sort order
   holds across the ENTIRE real tree after the `is_dir()` fix (a
   recursive Python check over every node, `True`).

**gate: clear 2026-09-01** — no MUST-FLAG trigger fired: no new
dependency, no shared-interface change, no ADR deviation (this is exactly
the "one more dict/list-returning read method" extension the story's own
architect pass already scoped), no unanticipated file (only the two
`## Files to Modify` files were touched), the one judgement call above is
scope-internal and logged for spot-check rather than an open question.
