---
id: REQ-SB-87-US-02-T02
title: Migrate rename_thread.py onto vault_manager.py
parent_story: REQ-SB-87-US-02
requirement_id: REQ-SB-87
type: backend
status: Done
gate: flagged
gate_reason: "Two disclosed scope-internal judgement calls need human spot-check (not blocking): (1) the 'already renamed' no-op check now compares against vault_manager._slugify(conversation_id), not vault_lib._slugify, since T01 made vault_manager the actual directory-naming authority. (2) A real regression was found and fixed live: vault_manager.update() lacks upsert_frontmatter_key()'s own no-op safety on a fence-less file, which would have corrupted a raw .md-named attachment's bytes via the pre-existing files_dir glob's dual match -- fixed with an explicit frontmatter-fence guard at the call site (see MEMORY.md Constraint entry and Implementation Log)."
phase: P1
depends_on: [REQ-SB-87-US-02-T01]
created: 2026-09-01
updated: 2026-09-02
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

- [x] Thread resolution uses `vault_manager.find_by_id`
- [x] `thread_name`/backlink/`source_thread` updates use
      `vault_manager.update`
- [x] Physical directory rename + collision-suffix logic byte-for-byte
      preserved
- [x] File-companion `is_file()` guard preserved
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

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

**What was built:** `rename_thread.py` migrated per the task's End-State.
Thread resolution now goes through `vault_manager.find_by_id(vault_path,
conversation_id, note_name="Threads")` (the Thread's own real, stable
`id`, per `REQ-SB-87-US-02-T01`) instead of `vault_lib.resolve_thread_
directory`. The concept note's own `thread_name`, every RawMessage's own
`thread` backlink, and every file companion's own `source_thread` field
now go through `vault_manager.update(vault_path, note_path,
frontmatter={...})` instead of `vault_lib.upsert_frontmatter_key`. The
physical directory rename (`vault_lib.rename_thread_directory`) and the
`sha256(conversation_id)[:8]` collision-suffix disambiguation (including
the space-reserved-before-truncation fix) stay HAND-WRITTEN, byte-for-byte
unchanged — `vault_manager.py` has no primitive for physically renaming a
note's own directory/file stem (disclosed in the task's own End-State,
confirmed correct: no such primitive exists anywhere in `vault_manager.py`,
`bump_folder_date` is a narrower, different operation).

**Scope-internal judgement call 1 (logged for human spot-check):** the
"already renamed" no-op check (`directory.name != ...`) now compares
against `vault_manager._slugify(conversation_id)`, not
`vault_lib._slugify(conversation_id)` — because `REQ-SB-87-US-02-T01`
made `vault_manager.create()` the actual authority for how a raw Thread
directory gets named (`own_folder`/`plain_filename`/`plain_folder`, all
`true` on the real `thread` Template.json). Using `vault_lib`'s own
80-char-capped slugify here would misdetect the not-yet-renamed state for
a conversation_id long enough that the two slugify functions' differing
max-length caps (120 vs. 80) disagree. Confirmed real conversation_ids in
this deployment are 32 hex chars (well under either cap), so this is a
correctness fix for future-proofing, not a currently-observable bug — but
it is the objectively correct mapping regardless. Does NOT touch the
preserved physical-rename/collision logic, which still uses
`vault_lib._slugify` (matching its own explicitly-preserved 80-char
collision-suffix budget, verified live below).

**Scope-internal judgement call 2 / real regression found and fixed live
(logged for human spot-check):** `vault_manager.update()` has no
equivalent to `vault_lib.upsert_frontmatter_key()`'s own real no-op
safety on a file with no frontmatter fence — `update()` unconditionally
writes a synthetic `---\n...\n---\n` block via `write_note()`, even onto
a file that never had one, whereas `upsert_frontmatter_key`'s own
`insert_frontmatter_key_if_missing` silently no-ops (finds no
`"\n---\n"`, returns without writing). The PRE-EXISTING (unchanged)
`new_files_dir.glob("*/*.md")` companion loop can match TWO real files
under the documented `.md`-named-attachment companion-directory collision
case (`vault_lib`'s own 2026-08-21 finding, the reason the `is_file()`
guard exists): the real, frontmatter'd companion note (safe) AND the raw,
UNFENCED attachment bytes copy sharing the identical `*.md` glob pattern
at the same directory level (unsafe). Confirmed live (see verification
below): without an extra guard, this migration would have corrupted a
real `"# Project Scaffold..."` attachment by injecting a synthetic
frontmatter block ahead of its real content — the ORIGINAL code was safe
here only because `upsert_frontmatter_key`'s own no-op behavior masked
it. Fixed by adding an explicit `path.read_text().startswith("---\n")`
gate immediately before the `vault_manager.update()` call in the file-
companion loop (this file only, no other file touched) — reproduces
`upsert_frontmatter_key`'s own no-op safety exactly, satisfying this
task's own Constraint of "matching today's real `upsert_frontmatter_key`
calls exactly." Generalized rule recorded in `MEMORY.md` for any future
`upsert_frontmatter_key` → `vault_manager.update` call-site migration.

**Live verification (real scratch vault, distinct `--vault-path`, never
the live vault — `C:\scratch-sb87t02\vault`, removed after verification
completed):** the prior `T01` scratch sample no longer existed on disk
(cleaned up after that task's own verification), so a fresh sample was
pulled: 60 real emails via the real, unmodified `list_recent_emails.py`
against the operator's own live Outlook (31 distinct `conversation_id`s,
11 with 2+ messages), ingested one at a time via the already-migrated,
already-`Done` `ingest_email.py --vault-path <scratch> --input-file
<one-email JSON>` (matching real per-email subprocess dispatch), seeded
with a copy of the real, live `thread/Template.json`.

- `[REQ-SB-87-US-02-AC-03]` **PASS.** Test 1 (relabel + backlinks): a real
  Thread (`conversation_id=EB609A9E52DF4C008B3FCEB8C3318119`, subject "Re:
  Masdar Open Items", 3 real messages) renamed from its raw
  conversation_id-slug directory to `"2026-09-01 Masdar Open Items"`
  (date from the latest message's own `received`, "Re:" stripped from
  `thread_name`); all 3 real RawMessage notes' own `thread` frontmatter
  updated to `[[2026-09-01 Masdar Open Items]]`, confirmed by reading the
  real on-disk frontmatter directly (not trusting stdout). Re-running
  against the now-renamed Thread returned `{"renamed": false, "reason":
  "already renamed"}` — correct no-op, confirmed via `vault_manager.
  _slugify` comparison working correctly against the real
  `vault_manager`-created directory name.
- `[REQ-SB-87-US-02-AC-03]` **PASS.** Test 2 (collision disambiguation):
  two real, distinct conversation_ids
  (`AAB6D7AAE6CD144B962483FAEE332736`/`8A6E9A2008D468468341B1FF5BE708AA`)
  engineered (via `vault_manager.update`, itself already verified above)
  to share an identical `thread_name`/latest-`received` date, producing an
  identical `"<date> <subject>"` stem landing EXACTLY at `_slugify`'s own
  80-char cap. Renaming the first Thread produced the clean 80-char stem;
  renaming the second produced `sha256(conversation_id)[:8]`-suffixed,
  correctly disambiguated (`...XXXXX-ac596e59`, matching the real computed
  hash, len=80, NOT truncated away by the 80-char cap — the
  space-reserved-before-truncation fix confirmed still working). The
  second Thread's own message backlinks correctly point at the
  disambiguated stem, not the collided one; the first Thread's own
  content was confirmed undisturbed. Re-running against the disambiguated
  Thread B was a correct no-op.
- (Unlabeled, supporting) **PASS.** File-companion `is_file()` guard +
  the newly-found frontmatter-fence guard, both against a real Thread
  (`conversation_id=2DF89901A3BB9D4E816AE10B83EA86B6`): a normal (PDF)
  file companion's `source_thread` was correctly updated to the new stem
  after rename; the documented `.md`-named-attachment case (`vault_lib.
  write_file_companion(file_slug="... project-scaffold.md",
  original_filename="project-scaffold.md", ...)`, reproducing the real
  2026-08-21 collision shape byte-for-byte) confirmed BOTH real files
  under the resulting companion directory: the real companion note (ends
  `....md.md`) got its `source_thread` correctly updated, and the raw
  attachment bytes (`project-scaffold.md`, no frontmatter fence) were
  confirmed BYTE-FOR-BYTE UNCHANGED after the fix (confirmed corrupted
  WITHOUT the fix first, by direct before/after content comparison, then
  confirmed clean with the fix in place).
- (Unlabeled, supporting) **PASS.** `{"renamed": false, "reason": "no
  Thread found for this conversation_id"}` confirmed live for a
  nonexistent conversation_id — the original no-Thread/no-messages-yet
  reason paths are unchanged (no code path modified there beyond the
  `vault_manager.find_by_id`/`read_note` swap).

**Scratch artefacts cleaned up:** `C:\scratch-sb87t02\` (scratch vault,
60-email sample, driver/verification scripts, output JSON) removed after
verification completed — nothing left behind outside this repo.

**Escalations / review-queue items written by this task:** none new.
Both judgement calls above are scope-internal (stayed entirely within
this task's own single `## Files to Modify` file, matched the parent
story's own "matching today's real `upsert_frontmatter_key` calls
exactly" Constraint) — logged here and in `MEMORY.md` for human
spot-check, not escalated, per this project's own established "log it,
don't block, flag the task's gate" pattern (`SPRINT-037`/`SPRINT-024`
precedent). `REVIEW-QUEUE.md` updated with a pointer to this task
alongside the still-open `REQ-SB-87-US-02-T01` filename-convention
spot-check item.

**Task marked `Done`.** This task's own one locked AC (`AC-03`) verified
live with a real, positive result across both required Tests steps plus
the unlabeled supporting no-op/no-Thread checks. `gate: flagged` — two
disclosed scope-internal judgement calls (the `_slugify` correctness fix,
and the real frontmatter-fence regression found and fixed live) need
human spot-check, neither blocks `T03`.
