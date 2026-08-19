---
id: REQ-SB-72-US-01-T03
title: The Rename Job — renames a Thread directory + concept file to <date> <subject-without-Re->
parent_story: REQ-SB-72-US-01
requirement_id: REQ-SB-72
type: backend
status: Done
gate: flagged
gate_reason: "Scope-internal judgement call: most real Threads (124/126) had never been through Stage 2 synthesis and so carried no last_message_at frontmatter — added an honest fallback deriving the rename date from the latest real raw message's own received field. See Implementation Log."
phase: P1
depends_on: [REQ-SB-72-US-01-T01]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-72-US-01-T03 — The Rename Job

## Parent Story

- Story: [[REQ-SB-72-US-01]] — `../UserStories/REQ-SB-72-US-01-librarian-section-first-housekeeping-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-72 *The Librarian Section — First Housekeeping Pipeline*
- Architecture: `Implementation/Architecture/architecture.md` → "Thread rename — a real, atomic whole-directory move" (`ADR-049` Decision 2)

---

## Objective

Build the first Job of the new `app/business/pipelines/librarian_housekeeping.py` module: for every real Thread whose directory still matches its raw `conversation_id` slug, compute its human-readable `<date> <subject-without-Re->` stem and rename it via `T01`'s `rename_thread_directory`.

---

## Starting State → End State

**Before / Inputs:**
- No `app/business/pipelines/librarian_housekeeping.py` module exists yet.
- Every real Thread directory under `Work/Threads/` is still named after its own `conversation_id` slug.

**After / Outputs:**
- New `app/business/pipelines/librarian_housekeeping.py`, with a `rename_threads() -> dict` Job function:
  - Iterates `vault_writer.list_thread_notes()`.
  - For each Thread whose directory name is still the raw `conversation_id` slug (i.e. not already renamed — compare `directory.name` against `_slugify(frontmatter["conversation_id"])`, or equivalently detect the directory is still the `thread_directory_paths(conversation_id)["directory"]` path), reads `thread_name`/`last_message_at` frontmatter, strips a leading `"Re: "` (case-insensitive, repeated) from `thread_name`, derives `date = last_message_at[:10]`, and computes the new stem `f"{date} {subject}"`.
  - Calls `vault_writer.rename_thread_directory(old_directory, new_directory)` where `new_directory = old_directory.parent / _slugify(new_stem)` (reusing `vault_writer`'s own private `_slugify`, or an equivalent already-exported slug helper — never a second, divergent slugging scheme).
  - A genuine collision (`FileExistsError`) is caught per-Thread — skip-and-report, never silently dropping one Thread's rename to save another's; the run continues over the remaining Threads.
  - Already-renamed Threads (directory name no longer matches the raw `conversation_id` slug) are skipped — idempotent by construction; re-running never double-renames.
  - Returns `{"renamed": [{"conversation_id": ..., "old_path": str, "new_path": str}], "skipped_already_renamed": [conversation_id, ...], "collisions": [{"conversation_id": ..., "attempted_stem": str, "error": str}]}`.

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` (new) — `rename_threads()` Job.

---

## Constraints

- Inherits from parent story.
- Reuses `T01`'s `rename_thread_directory`/`resolve_thread_directory` unchanged — never a second, divergent rename mechanism.
- No hash-suffix disambiguation on the new stem — a genuine `<date> <subject>` collision surfaces via `rename_thread_directory`'s own raise, per-Thread, never silently absorbed (`ADR-049` Decision 2 / Alternatives 9).
- Every raw message note under `messages/` and every already-created `files/` companion must move with the renamed directory, byte-for-byte unchanged — this is a property of `rename_thread_directory`'s own atomic move (`T01`), not re-implemented here.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-72-US-01-AC-01]` Direct Python-shell check against the real vault: pick one real, currently-un-renamed Thread directory (`Work/Threads/<slug-of-conversation_id>/`) with a real concept file, real messages under `messages/`, and (if any exist in the real vault) an already-created `files/` companion. Call `librarian_housekeeping.rename_threads()`. Confirm the directory and its concept file are now named `<date> <subject-without-Re->` (e.g. `2026-08-16 Ewec Discussion`), derived from the Thread's own real `thread_name`/`last_message_at` frontmatter, and that every raw message note and every `files/` companion is present, unmoved-in-content, byte-for-byte identical, at the new location — confirm via a before/after listing + hash comparison of each file's own bytes.
2. Re-run `rename_threads()` a second time over the same, now-renamed Thread; confirm it appears in `skipped_already_renamed`, not `renamed` — no second rename attempt, no error.
3. Construct two disposable Threads whose derived `<date> <subject>` stems collide; confirm the run reports one in `collisions` (with the real `FileExistsError` message) while the other still renames successfully — the run does not abort.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `rename_threads()` renames every un-renamed Thread's directory + concept file to `<date> <subject-without-Re->`
- [x] `messages/`/`files/` move intact, byte-for-byte unchanged
- [x] Idempotent: an already-renamed Thread is skipped, never re-renamed
- [x] A genuine stem collision is caught and reported per-Thread, never aborts the whole run
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The orchestrating `run_housekeeping_pass` capability that sequences this Job first, ahead of the other three — `T08`.
- The `/poc/librarian-rename-threads` HTTP endpoint — `T08`.
- Migrating other real callers (`raw_message_capture.py`, `synthesize_thread`, `meeting_classification.py`) off directly composing `thread_directory_paths` — `T02`.

---

## Context / Notes

Build this task BEFORE `T02` in dependency order (`T02` depends on this task) — `T02`'s own AC-02 verification needs a real, already-renamed Thread to exist, which only this task's Job can produce.

---

## Implementation Log

**2026-08-18, coder pass.** Built `rename_threads()` in the new
`src/backend/app/business/pipelines/librarian_housekeeping.py`, composing
`T01`'s `rename_thread_directory` unchanged.

**Assumption logged (scope-internal judgement call, per Pipeline.md — this
task's own gate: flagged for human spot-check, not an escalation):** direct
reading of the real vault found that only 2 of the 126 real Thread
directories had ever gone through Stage 2 (`synthesize_thread`), so only
those 2 carried `last_message_at` frontmatter — the other 124 had only been
through Stage 1 raw capture. The task's own text assumed `last_message_at`
would always be present. Rather than skip 124/126 real Threads (or fail),
added `_latest_message_received_date`: an honest fallback that reads the
Thread's own real, already-captured raw message notes under `messages/`
(sorted, matching `synthesize_thread`'s own ordering contract) and uses the
LATEST one's own real `received` frontmatter field — never a guessed or
placeholder date, the same class of real-data derivation this codebase
already uses elsewhere (`synthesize_thread`'s own `latest_message =
messages[-1]`).

**Real, live-vault verification (AC-01):**
1. Dry-run preview computed every real Thread's derived `<date> <subject>`
   stem before renaming anything — confirmed sane output (leading `Re:`
   stripped, real dates, real subjects) and surfaced 5 genuine real
   `<date> <subject>` collisions among the 126 (10 real Threads mapping to 5
   duplicate stems) ahead of time.
2. Captured SHA-256 hashes of every file under a real target Thread
   (`004771620DBD604FAE3D2CE2A3404608`, concept file + one raw message note)
   before the run.
3. Ran `rename_threads()` for real against the full real vault: **121
   renamed, 0 skipped (first run), 5 collisions** (the same 5 the dry-run
   preview predicted) — each collision's own real `FileExistsError` message
   recorded, the run did NOT abort, all 121 non-colliding Threads renamed
   successfully in the same call. Confirmed the target Thread now lives at
   `Work/Threads/2026-08-12 Your Core42 Compass Portal account verification
   code/`, both files present with IDENTICAL SHA-256 hashes to their
   pre-rename bytes — nothing orphaned or duplicated. PASS (AC-01).
4. Re-ran `rename_threads()` a second time over the same, now-mostly-renamed
   corpus: **0 renamed, 121 skipped_already_renamed, 5 collisions
   (unchanged)** — confirms idempotency: no second rename attempt on an
   already-renamed Thread, no error. PASS.
5. The 5 real collisions are genuine, live evidence for the "skip-and-report,
   never aborts" AC — each remains at its original `conversation_id`-slug
   directory name (un-renamed, by design, since the target stem is already
   taken by another real Thread) and stays that way across reruns; a human
   can resolve each manually (rename one side) if desired — left as-is, not
   silently forced, per this task's own "surfaced, never silently absorbed"
   Constraint. PASS.

`gate: flagged 2026-08-18` — trigger 8 style scope-internal judgement call
(the `last_message_at` fallback), not an escalation; logged here per
Pipeline.md for human spot-check. No ADR deviation, no new dependency, no
shared-interface change — `rename_threads()`'s own public contract matches
`T03`'s own task text exactly.
