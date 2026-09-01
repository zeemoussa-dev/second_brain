---
id: REQ-SB-87-US-02-T02
title: Migrate rename_thread.py onto vault_manager.py
parent_story: REQ-SB-87-US-02
requirement_id: REQ-SB-87
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-02-T01]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-02-T02 — Migrate rename_thread.py onto vault_manager.py

## Parent Story

- Story: [[REQ-SB-87-US-02]] — `../UserStories/REQ-SB-87-US-02-email-thread-capture-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Migrate `rename_thread.py`'s own Thread-resolution and frontmatter-update
mechanics onto `vault_manager.py`, preserving its exact real
directory-rename, backlink-update, and same-day-subject-collision
behavior.

---

## Starting State → End State

**Before / Inputs:**
- Real, current `rename_thread.py` (read directly, 2026-09-01): resolves
  the Thread via `vault_lib.resolve_thread_directory`; no-ops if already
  renamed or no messages exist yet; computes `new_stem = "<date>
  <subject>"` from the latest message's own `received` + the Thread's own
  `thread_name`; physically renames the directory
  (`vault_lib.rename_thread_directory`), with a `sha256(conversation_id)[:8]`
  suffix disambiguation on a real stem collision (space reserved BEFORE
  truncation); then `upsert_frontmatter_key`s the concept note's own
  `thread_name`, every RawMessage's own `thread` backlink, and every file
  companion's own `source_thread` field.

**After / Outputs:**
- Thread resolution goes through `vault_manager.find_by_id` (the Thread's
  own real `id`, not a directory-name lookup) instead of
  `vault_lib.resolve_thread_directory`.
- **Disclosed scope-internal judgement call:** `vault_manager.py` has no
  existing primitive for physically renaming a note's own directory/file
  stem (`bump_folder_date` only moves a `note_own_folder`-wrapped note's
  folder forward to a newer DATE, a narrower operation) — the physical
  rename + collision-suffix logic stays HAND-WRITTEN, unchanged, reusing
  the same technique `vault_lib.rename_thread_directory` already uses
  (`Path.rename()`). This is not a "read/create/find/section-write"
  mechanic the parent story's own Constraints name as in-scope to migrate;
  inventing a new engine verb for it is out of scope here (not requested by
  any locked AC). Logged for human spot-check, not an escalation.
- The concept note's own `thread_name` frontmatter update, and every
  RawMessage/file-companion backlink update, go through
  `vault_manager.update(vault_path, note_path, frontmatter={...})` (the
  generic, path-based frontmatter writer — no template/access-control
  needed for these, matching today's real `upsert_frontmatter_key` calls
  exactly).
- The real `sha256(conversation_id)[:8]` collision-suffix logic, with its
  space-reserved-before-truncation fix, is preserved byte-for-byte.

---

## Files to Modify

- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/rename_thread.py`

---

## Constraints

- Inherits from parent story.
- The physical directory rename and collision-suffix disambiguation stay
  hand-written, exactly as today (see the disclosed judgement call above).
- Never lose the `is_file()` guard on file companions (a real
  `"...md"`-named attachment produces a companion DIRECTORY, not a file —
  `upsert_frontmatter_key`/`vault_manager.update`'s own `read_text()` would
  raise `PermissionError` on Windows against a directory).
- Verify against the SAME scratch vault/100-email sample `T01` used —
  never the live vault for this task.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`):**
1. `[REQ-SB-87-US-02-AC-03]` Run `rename_thread.py` against a Thread from
   `T01`'s own scratch sample still slugged from its raw
   `conversation_id`, with existing messages and (if the sample has one) a
   file companion. Confirm the directory and concept-note filename are
   relabeled to `"<date> <subject>"` exactly as today, every message's own
   `thread` backlink and every file companion's own `source_thread` field
   are updated to match.
2. `[REQ-SB-87-US-02-AC-03]` Engineer (in the scratch vault only) two
   Threads whose `conversation_id`s would clean to the IDENTICAL `"<date>
   <subject>"` stem; run `rename_thread.py` against both. Confirm the
   second one is disambiguated via the real `sha256(conversation_id)[:8]`
   suffix, never silently overwriting or crashing, and that a stem already
   near the 80-char cutoff still gets a correctly-appended, non-truncated
   suffix.
3. (Unlabeled, supporting) Run `rename_thread.py` a second time against an
   already-renamed Thread; confirm the existing no-op ("already renamed")
   behavior is preserved.

**Automated tests:** `n/a — no existing pytest harness for this Skill;
verified via scratch-vault CLI runs`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Thread resolution uses `vault_manager.find_by_id`
- [ ] `thread_name`/backlink/`source_thread` updates use
      `vault_manager.update`
- [ ] Physical directory rename + collision-suffix logic byte-for-byte
      preserved
- [ ] File-companion `is_file()` guard preserved
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Inventing a new `vault_manager.py` directory-rename verb — disclosed as
  out of scope above.
- `capture_attachments.py`/`capture_file_link.py`/`link_person_to_thread.py`
  — `T03`.

---

## Context / Notes

Read the real current `rename_thread.py` directly before editing
(reproduced in Starting State above from a 2026-09-01 read).

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
