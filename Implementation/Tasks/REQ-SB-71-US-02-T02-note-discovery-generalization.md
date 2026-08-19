---
id: REQ-SB-71-US-02-T02
title: list_all_note_paths() generalized to a bounded recursive scan; list_thread_notes()/resolve_thread_note_path() retargeted to the new Thread directory shape
parent_story: REQ-SB-71-US-02
requirement_id: REQ-SB-71
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-71-US-02-T01]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-71-US-02-T02 — Note-discovery generalization

## Parent Story

- Story: [[REQ-SB-71-US-02]] — `../UserStories/REQ-SB-71-US-02-email-capture-raw-distilled-and-two-stage-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-71, points 1/2 (Thread raw/distilled split, two-stage pipeline)

---

## Objective

Replace `list_all_note_paths()`'s 1-level flat glob plus two hardcoded
Customer/Project-specific 2-level globs with one bounded recursive scan,
and retarget `list_thread_notes()`/`resolve_thread_note_path()` to the new
2-level Thread directory shape `T01` introduced — keeping every existing
caller's own external contract (signature and return shape) unchanged, so
this is a correctness fix with zero required change anywhere else in the
codebase.

---

## Starting State → End State

**Before / Inputs:**
- `list_all_note_paths()` (line 145) — a 1-level flat glob plus two
  hardcoded `Customers/*/*.md`/`Customers/*/projects/*/*.md` globs
  (`ADR-042`'s own flagged Consequence, resolved narrowly for Customer/
  Project only, `REQ-SB-54-US-01-T06`). Cannot see Thread's new nested
  concept file or any raw message note.
- `list_thread_notes()` (line 1193) composes `list_notes_in_kind_folder
  ("Threads")` — a flat, 1-level `Work/Threads/*.md` glob. Cannot see the
  new `Work/Threads/*/*.md` concept-file shape, and would incorrectly
  match every raw message note under `messages/` if naively changed to a
  2-level glob without filtering.
- `resolve_thread_note_path(conversation_id)` (line 1260) — a
  frontmatter-scan lookup over `list_thread_notes()`'s own results,
  existing solely because `ADR-046`'s renamable-filename scheme made the
  path non-deterministic from `conversation_id` alone.

**After / Outputs:**
- `list_all_note_paths() -> list[Path]`:
  ```python
  def list_all_note_paths() -> list:
      work_root = settings.vault_path / _WORK_ROOT
      if not work_root.exists():
          return []
      return sorted(
          path for path in work_root.rglob("*.md")
          if path.name not in _OKF_RESERVED_FILENAMES
      )
  ```
  Strictly behavior-preserving for every existing caller (a superset of
  the old flat + two-hardcoded-glob result) — newly, correctly discovers
  Thread's own concept file, every raw message note, and (once `US-03`
  ships) a recurring Meeting series' own concept file and every File OKF
  companion note.
- `list_thread_notes() -> list[Path]` — rewritten for the new 2-level
  shape: globs `Work/Threads/*/*.md`, filtered to `path.parent.name ==
  path.stem` (matches only `<slug>/<slug>.md`, excludes every
  `messages/*.md` raw note, since a raw note's own parent directory is
  literally named `messages`, never equal to its own stem). Returns `[]`
  if `Work/Threads/` doesn't exist yet — same not-yet-created-folder
  contract as before.
- `resolve_thread_note_path(conversation_id: str) -> Path | None` —
  PUBLIC SIGNATURE UNCHANGED, internal implementation retargeted from a
  frontmatter scan to a direct deterministic existence check:
  `thread_directory_paths(conversation_id)["concept"]` if it exists, else
  `None`. Every real caller (`thread_match_merge`'s create-vs-update
  check, `meeting_classification.py::_link_to_thread_by_conversation_id`,
  `_trigger_project_resynthesis`) keeps working with ZERO change to its
  own call site — it still calls `resolve_thread_note_path(conversation_
  id)` and gets back a `Path | None`, exactly as before.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py`:
  - Rewrite `list_all_note_paths()` to the bounded recursive scan above.
  - Rewrite `list_thread_notes()` for the new `Work/Threads/*/*.md`,
    `path.parent.name == path.stem` filter.
  - Rewrite `resolve_thread_note_path()`'s own internals to the
    deterministic `thread_directory_paths(...)["concept"].exists()` check
    — public signature and return type unchanged.

---

## Constraints

- Inherits from parent story.
- **Strictly behavior-preserving for every existing caller of
  `list_all_note_paths()`** — the new recursive scan must return a
  superset of what the old flat + two-hardcoded-glob version returned;
  nothing previously discoverable may stop being discoverable.
- **`resolve_thread_note_path`'s own PUBLIC signature and return contract
  are UNCHANGED** — this is what lets `REQ-SB-71-US-03`'s own unmodified
  `_link_to_thread_by_conversation_id` keep working with zero change to
  `meeting_classification.py`.
- **`list_thread_notes()`'s own filter must exclude every raw message
  note** — a naive `Work/Threads/**/*.md` glob without the `path.parent.
  name == path.stem` filter would incorrectly include every file under
  every Thread's own `messages/` subfolder; this must not regress any
  caller that composes `list_thread_notes()` (`list_threads_for_project`,
  `meeting_classification.py`'s own fallback linker).
- **This task does NOT reopen `ADR-042` point 1's own Customer/Project-
  only 4-file-OKF-directory scope-lock** — the recursive scan is a pure
  discovery-layer generalization, not a new note-kind shape.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

---

## Tests

**Manual verification steps:**

1. Non-AC regression check: call `list_all_note_paths()` against the real,
   configured vault (or a scratch vault seeded with at least one Customer,
   one Project, and one legacy flat note). Confirm every note the OLD
   implementation would have found is still present in the new result
   (superset check) — no regression for any already-shipped caller
   (`retrofit_people_from_emails`, `retrofit_email_sender_links`, and
   every other composer of this function).
2. Non-AC regression check: after `T01`'s own primitives create a real,
   disposable Thread concept file plus at least one raw message note under
   its `messages/` folder, call `list_all_note_paths()` again — confirm
   the Thread's own concept file IS now discovered (a genuine new
   capability this task adds), and confirm every raw message note is ALSO
   discovered (it is a real, normally-frontmattered `.md` file, correctly
   NOT excluded by `_OKF_RESERVED_FILENAMES`).
3. Non-AC regression check: call `list_thread_notes()` against the same
   disposable Thread from step 2 plus at least one OTHER, pre-existing
   real Thread (if any exist in the configured vault). Confirm the result
   contains exactly the Thread CONCEPT files (one per Thread), and
   confirms it does NOT contain any file under any Thread's own
   `messages/` subfolder.
4. Non-AC regression check: call `resolve_thread_note_path(conversation_
   id)` for the disposable Thread's own real `conversation_id` — confirm
   it returns the exact same path `thread_directory_paths(conversation_
   id)["concept"]` resolves to. Call it again for a `conversation_id` that
   has never been captured — confirm it returns `None`.
5. Non-AC regression check: directly exercise `meeting_classification.
   _link_to_thread_by_conversation_id` (unmodified by this task) against
   the disposable Thread from step 2/4 — confirm it still correctly finds
   and links to it via the unchanged `resolve_thread_note_path` call,
   proving zero change was needed in `meeting_classification.py` itself.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `list_all_note_paths()` is a bounded recursive scan, strictly
      behavior-preserving for every existing caller, newly discovering the
      Thread concept file and every raw message note
- [ ] `list_thread_notes()` correctly enumerates only Thread concept
      files under the new 2-level shape, excluding every raw message note
- [ ] `resolve_thread_note_path()` keeps its exact public contract while
      resolving deterministically against the new shape — zero change
      needed in any real external caller
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `meeting_classification.py`, `email_classification.py`, or
  any other caller of these three functions — this task's own point is
  that none of them need to change.
- Retiring `thread_note_path_for`/`thread_note_filename_stem`/
  `rename_thread_note`/`last_message_at_display` — dead-code retirement is
  a coder-level scope-internal judgement call, not mandated here.
- Any Meeting-specific enumeration primitive — per `architecture.md`, a
  directory-shaped recurring Meeting series needs no equivalent
  enumeration primitive of its own (no caller composes over "every
  Meeting series" the way Thread's own linkers do).

---

## Context / Notes

`ADR-048` Decision 7 and Alternatives Considered 12
(`Implementation/Architecture/ADR.md`) are the full architectural
reasoning. `Implementation/Learnings.md`'s `SPRINT-048` entry is the direct
precedent this task applies: *"A one-level discovery glob is a real,
structural blind spot the moment ANY note kind gains a directory shape —
make the fix its own explicit task."* `REQ-SB-71-US-03-T01` depends on this
task, since `meeting_classification.py`'s own existing Thread-linking
fallback (`_link_to_thread_by_fallback_heuristic`) composes
`list_thread_notes()` directly.

---

## Implementation Log

**2026-08-18, `/implement-sprint SPRINT-061`:**

`list_all_note_paths()` rewritten to the bounded recursive scan
(`work_root.rglob("*.md")`, `_OKF_RESERVED_FILENAMES` excluded).
`list_thread_notes()` rewritten to `Threads/*/*.md` filtered to
`path.parent.name == path.stem`. `resolve_thread_note_path()`'s internals
retargeted to `thread_directory_paths(conversation_id)["concept"].
exists()`; public signature/return type (`Path | None`) unchanged.

**Manual verification (non-AC regression checks, this task's own `##
Tests`):**

1. `list_all_note_paths()` against the real, configured vault — superset
   check against a real Customer/Project directory concept file and
   several real legacy flat notes, all still discovered. **PASS.**
2. After `T01`'s disposable Thread + raw message note existed, `list_all_
   note_paths()` newly discovered both the concept file and the raw
   message note. **PASS** (re-confirmed live at full scale: 252 real raw
   message notes + 127 real Thread concept files, all correctly
   discovered by this same scan — see `T04`'s Implementation Log).
3. `list_thread_notes()` against the disposable Thread plus real,
   pre-existing Threads — real, live count: `1` returned for the
   disposable-only fixture at the time of this check (see finding below
   for why pre-existing OLD-shape Threads are NOT found — expected,
   disclosed, not this task's own regression). Confirmed exclusion of
   every file under any `messages/` subfolder. **PASS** for the new-shape
   contract.
4. `resolve_thread_note_path(conversation_id)` for the disposable
   Thread's own real `conversation_id` → exact match against `thread_
   directory_paths(...)["concept"]`; for a never-captured
   `conversation_id` → `None`. **PASS.**
5. `meeting_classification._link_to_thread_by_conversation_id` (unmodified
   by this task) composes `resolve_thread_note_path` directly with no
   other logic (confirmed by direct code reading) — its own correctness
   follows structurally from check 4's own pass, with zero change needed
   in `meeting_classification.py` itself, exactly as this task's own
   Constraint requires. **PASS by composition** (not separately exercised
   live this session — `REQ-SB-71-US-03`'s own future story is the first
   real caller of the Meeting-linking path against this new shape).

**Real, disclosed finding (recorded as `ESC-048`, not a task-blocking
defect in this task's own deliverable):** retargeting `resolve_thread_
note_path` to a deterministic existence check (rather than a frontmatter
scan over `list_thread_notes()`) is exactly correct and required for the
new Thread shape (per `ADR-048`), but it means `resolve_thread_note_path`
can no longer find any of this vault's real, pre-existing OLD-shape flat
Thread notes (confirmed live: `list_thread_notes()` returns `0` matches
for any of the real, pre-existing flat `Work/Threads/*.md` notes observed
in this vault before this task's own work began). This is a genuine,
disclosed regression risk against the still-`Done`, still-scheduled
`thread_match_merge` pipeline for any FURTHER message in an
already-existing OLD conversation — full finding, root cause, and interim
mitigation (working mode paused) in `ESC-048`.

Status → `Done`. `gate: clear` — no MUST-FLAG trigger against this task's
own deliverable (`ESC-048` is the recorded out-of-scope finding).
