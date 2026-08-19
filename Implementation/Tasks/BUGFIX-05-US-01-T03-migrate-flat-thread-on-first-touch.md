---
id: BUGFIX-05-US-01-T03
title: resolve_thread_directory() gains a second scan tier that recognizes and lazily migrates a legacy flat-shape Thread note (ADR-052)
parent_story: BUGFIX-05-US-01
requirement_id: BUG-026
type: backend
status: Done
gate: clear
gate_reason: ""
depends_on: []
created: 2026-08-19
updated: 2026-08-19
---

# BUGFIX-05-US-01-T03 — resolve_thread_directory() gains a second scan tier that recognizes and lazily migrates a legacy flat-shape Thread note (ADR-052)

## Parent Story

- Story: [[BUGFIX-05-US-01]] — `../UserStories/BUGFIX-05-US-01-email-thread-processing-retires-legacy-thread-match-merge.md`
- Requirement: `BUGS.md` → `BUG-026` (bugfix story; no PRD requirement anchor)

---

## Objective

Add a new `migrate_flat_thread_to_directory` primitive and a second scan
tier to `resolve_thread_directory()` in `vault_writer.py` — per `ADR-052`
— so that a genuinely flat, pre-redesign `Work/Threads/<name>.md` Thread
note is recognized (by `conversation_id` frontmatter match) and lazily,
idempotently migrated to the standard `<slug>/<slug>.md` + `messages/`
directory shape the FIRST time any caller resolves its `conversation_id`,
instead of being invisible to every `list_thread_notes()`-based lookup.
This closes `AC-01` (the duplication facet) at the shared-primitive layer
— independent of, and untouched by, `T01`'s own composing-function rewire
(`vault_writer.py` is not among `T01`'s `## Files to Modify`). Live
verification of `AC-01` itself happens in `T04`, not this task.

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.list_thread_notes()` globs `Work/Threads/*/*.md` only —
  structurally blind to a flat, top-level `Work/Threads/<name>.md` note
  (zero intermediate directory segments).
- `resolve_thread_directory(conversation_id)` composes `list_thread_
  notes()` alone (one scan tier) and returns `None` for a `conversation_id`
  that only has a flat note — the confirmed root cause of `BUG-026`'s
  duplication facet (`ESC-055`).
- `thread_directory_paths(conversation_id)` (existing, unchanged) already
  computes the deterministic `{"directory", "concept", "messages"}` path
  set every brand-new Thread is created at.
- `rename_thread_directory` (existing, unchanged) is the closest sibling
  precedent for a refuse-to-overwrite, atomic directory-shape operation —
  mirrored, not reused directly (a rename between two already-existing
  directories is a different operation from a flat-file-to-directory
  migration).

**After / Outputs:**
- A new `migrate_flat_thread_to_directory(flat_path: Path) -> Path`
  primitive in `vault_writer.py` migrates one flat Thread note in place to
  its own deterministic directory shape, preserving its own prior content
  (concept file body/frontmatter byte-identical, just relocated), creating
  an empty `messages/` subdirectory alongside it.
- `resolve_thread_directory(conversation_id)` gains a second scan tier —
  tried ONLY on a miss from the existing (first) directory-shaped scan —
  that globs `Work/Threads/*.md` directly for a `conversation_id`
  frontmatter match; on a match, calls `migrate_flat_thread_to_directory`
  and returns the NEW directory. It never returns a flat file's own path
  or parent directly.
- `resolve_thread_note_path(conversation_id)` (an unchanged thin wrapper
  over `resolve_thread_directory`) sees the migrated Thread automatically,
  with zero changes to its own body.
- `list_thread_notes()` itself, and every one of its own OTHER callers
  (`list_threads_for_project`), are byte-for-byte unchanged.
- A `conversation_id` that already has BOTH a flat note and a
  directory-shaped duplicate (the confirmed-live
  `ED0954959F6F4A4C88F9E2ACA3D7113A` case) silently no-ops on the second
  tier — the first (directory-shaped) scan already finds and returns the
  existing duplicate, so the second tier never even runs for that
  `conversation_id`. This task does not touch or repair that case (see
  `## Out of Scope`).

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py`:
  1. Add the new primitive directly after `resolve_thread_note_path`
     (or another logical location near the Thread-lookup primitives —
     coder's own judgement on exact placement within this module):

     ```python
     def migrate_flat_thread_to_directory(flat_path: Path) -> Path:
         """One-time, idempotent, self-healing migration (BUGFIX-05-US-01,
         ADR-052) of a legacy, pre-redesign FLAT Work/Threads/<name>.md
         Thread note (zero intermediate directory segments) to the
         standard 2-level directory shape thread_directory_paths(
         conversation_id) already establishes for every Thread created
         after ADR-048 -- the SAME deterministic location a brand-new
         Thread is always first created at, reused unchanged, never a
         second naming derivation. Mirrors rename_thread_directory's own
         refuse-to-overwrite discipline one level up: raises
         FileExistsError if the deterministic target directory already
         exists (a structurally near-impossible conversation_id-slug
         collision), never silently overwriting. Reads conversation_id
         from flat_path's own frontmatter directly -- the caller
         (resolve_thread_directory's own second scan tier) has already
         matched on it, but this function re-derives it independently so
         it stays a correct, callable-on-its-own primitive, not one that
         silently trusts an unchecked caller-supplied id. Creates the
         target directory, moves/renames the flat file to
         <slug>/<slug>.md, creates an empty messages/ subdirectory
         alongside it -- touches only filesystem SHAPE (one directory
         creation, one file move/rename, one empty subdirectory
         creation), never note body or frontmatter content. Returns the
         new concept file path."""
         frontmatter, _ = read_note(flat_path)
         conversation_id = frontmatter["conversation_id"]
         paths = thread_directory_paths(conversation_id)
         if paths["directory"].exists():
             raise FileExistsError(
                 f"would overwrite existing Thread directory at {paths['directory']}"
             )
         paths["directory"].mkdir(parents=True, exist_ok=True)
         flat_path.rename(paths["concept"])
         paths["messages"].mkdir(parents=True, exist_ok=True)
         return paths["concept"]
     ```

  2. Replace `resolve_thread_directory`'s exact body (keep its existing
     docstring's first paragraph describing the first, directory-shaped
     scan tier; append a new paragraph documenting the second tier and the
     narrowed read-only contract) with:

     ```python
     def resolve_thread_directory(conversation_id: str) -> Path | None:
         """The ONE place "does a Thread for this conversation_id already
         exist, and if so, where" is answered going forward (`REQ-SB-72-
         US-01-T01`, `ADR-049` Decision 1) -- a frontmatter-based scan,
         composing the existing `list_thread_notes()` (never a second,
         independent Thread-enumeration mechanism), matching `frontmatter.
         get("conversation_id") == conversation_id`. Returns the Thread's
         own DIRECTORY (`path.parent`), or `None` if no directory-shaped
         Thread matches.

         On a miss, a SECOND scan tier (`BUGFIX-05-US-01`, `ADR-052`)
         globs `Work/Threads/*.md` directly -- flat, pre-redesign notes
         only, deliberately NOT folded into `list_thread_notes()` itself
         (`ADR-052` Decision 4) -- for the SAME `conversation_id`
         frontmatter match. On a match, immediately calls `migrate_flat_
         thread_to_directory` and returns the NEW directory -- never a
         flat file's own path or parent directly. This is the ONE
         deliberate exception to this function's own otherwise
         purely-read-only contract: a one-time, idempotent, self-healing
         WRITE for this legacy flat-shape case only (`ADR-052` Decision
         5, narrowing `ADR-049` Decision 1's "purely read-only" framing
         for this one case).

         Ordering is load-bearing: the directory-shaped scan always runs
         FIRST, so a `conversation_id` that already has BOTH a flat note
         and a directory-shaped duplicate correctly, silently no-ops on
         the second tier -- the existing duplicate is returned, the
         already-orphaned flat note is left alone (a deliberate,
         disclosed non-goal, `ADR-052` Consequences / `ESC-055`)."""
         for path in list_thread_notes():
             frontmatter, _ = read_note(path)
             if frontmatter.get("conversation_id") == conversation_id:
                 return path.parent

         threads_root = settings.vault_path / _THREADS_SUBFOLDER
         if threads_root.exists():
             for flat_path in threads_root.glob("*.md"):
                 frontmatter, _ = read_note(flat_path)
                 if frontmatter.get("conversation_id") == conversation_id:
                     migrated_concept_path = migrate_flat_thread_to_directory(flat_path)
                     return migrated_concept_path.parent

         return None
     ```

     (`threads_root.glob("*.md")` matches only files directly under
     `Work/Threads/` — one level deep — so it can never accidentally match
     a directory-shaped Thread's own concept file, which always lives two
     levels deep at `<slug>/<slug>.md`. No new import is needed —
     `Path`/`settings`/`read_note`/`_THREADS_SUBFOLDER` are all already
     imported/defined in this module.)

---

## Constraints

- Inherits from parent story (real, live vault — no fixture; must not
  touch `pull_email`/`email_pull.py`; no-data-loss is load-bearing).
- Must NOT modify `list_thread_notes()` itself, or any of its own OTHER
  callers (`list_threads_for_project`, every Librarian Job) — `ADR-052`
  Decision 4, they see a migrated former-flat-note for free on their own
  next pass, no special-casing needed anywhere else.
- Must NOT change `resolve_thread_note_path`'s own body — it stays a thin,
  unchanged wrapper over `resolve_thread_directory`.
- `migrate_flat_thread_to_directory` must raise `FileExistsError` (never
  silently overwrite) on a target-directory collision, mirroring `rename_
  thread_directory`'s own already-`Accepted` discipline.
- Must NOT attempt to fix, merge, or otherwise touch the already-diverged
  `ED0954959F6F4A4C88F9E2ACA3D7113A` case (flat 2026-07-27 note +
  directory-shaped 2026-08-17 duplicate) — `ADR-052`'s own ordering rule
  already, correctly, silently no-ops for it; do not add special-case
  logic to detect or repair it (see `## Out of Scope`).
- Migration touches only filesystem SHAPE — never note body or frontmatter
  content — so no `section_ownership.py` allow-list entry is implicated.

---

## Tests

<!-- No locked AC is verified in this task — AC-01 is verified live in
T04, once this task's primitive is in place (and T01's composing-function
rewire is also in place, since AC-01's own Given clause requires
process_staged_email to already compose capture_raw_thread_messages/
synthesize_thread). This task carries its own real, non-AC-tagged
regression/smoke checks of the migration primitive itself. -->

**Manual verification steps (not locked-AC-tagged — smoke/regression
checks of this task's own primitive, against the real `.venv`,
`.venv\Scripts\python.exe`, cwd `src/backend`):**

1. Import `app.data_access.vault_writer` cleanly (`python -c "import
   app.data_access.vault_writer"`) — confirms no syntax error.
2. In a Python shell, against the real, configured vault (`VAULT_PATH`),
   call `vault_writer.resolve_thread_directory(conversation_id)` for a
   `conversation_id` you already know only has a DIRECTORY-shaped Thread
   (e.g. any Thread confirmed to already exist under `Work/Threads/<slug>/
   <slug>.md`) — confirm it returns the SAME directory as before this
   change (the existing, first scan tier is unaffected — no regression).
3. In a Python shell, identify (by listing `Work/Threads/*.md` directly)
   one of the real, currently flat Thread notes that has NO known
   directory-shaped duplicate yet (NOT `conversation_id
   ED0954959F6F4A4C88F9E2ACA3D7113A` — confirm this by also searching for
   that same `conversation_id` string under `Work/Threads/*/*.md` first
   and confirming zero matches). Read its own `conversation_id`
   frontmatter directly. Call `vault_writer.resolve_thread_directory(
   conversation_id)` for that id and confirm: (a) it returns a NEW
   directory at `Work/Threads/<slug-of-conversation_id>/`; (b) the
   directory contains `<slug>.md` (the migrated concept file, with
   frontmatter/body byte-identical to the original flat note's own prior
   content — compare directly) and an empty `messages/` subdirectory;
   (c) the original flat file no longer exists at its own prior path.
4. Call `vault_writer.resolve_thread_directory(conversation_id)` a SECOND
   time for the SAME `conversation_id` from step 3 — confirm it returns
   the SAME directory via the FIRST (directory-shaped) scan tier this
   time, and does not attempt to re-migrate or raise (idempotent by
   construction — the first scan tier now finds it directly).
5. Call `vault_writer.resolve_thread_directory("ED0954959F6F4A4C88F9E2ACA3D7113A")`
   (the confirmed-live already-diverged Azure conversation) and confirm it
   returns the EXISTING `2026-08-17 Azure-...` directory-shaped Thread —
   never attempting to migrate the 2026-07-27 flat note, never raising —
   confirming `ADR-052`'s own ordering rule holds for the one real,
   already-manifested collision case in the live vault.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `migrate_flat_thread_to_directory(flat_path)` migrates a flat
      Thread note's own content byte-identical to the standard
      `<slug>/<slug>.md` + empty `messages/` shape, raising
      `FileExistsError` on a target-directory collision
- [ ] `resolve_thread_directory()`'s second scan tier is tried ONLY on a
      miss from the first (directory-shaped) scan, matches a flat note by
      `conversation_id` frontmatter, migrates it, and returns the NEW
      directory — never a flat file's own path/parent directly
- [ ] `list_thread_notes()` and `resolve_thread_note_path()`'s own bodies
      are byte-for-byte unchanged
- [ ] The already-diverged `ED0954959F6F4A4C88F9E2ACA3D7113A` case is
      correctly, silently no-op'd (existing duplicate returned, flat note
      left alone) — not specially detected or repaired
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Live verification of `AC-01` via the real `process_staged_email`
  capability — `T04`.
- Fixing, merging, or otherwise reconciling the already-diverged
  `ED0954959F6F4A4C88F9E2ACA3D7113A` duplicate — deferred to a future
  Librarian-housekeeping backlog item, per the architect's own explicit
  Decision 2 and `ESC-055`'s resolution note; not this story's scope.
- Any change to `list_thread_notes()` itself or any of its OTHER callers
  (`list_threads_for_project`, Librarian Jobs) — they see a migrated
  former-flat-note for free, no code change needed there.
- Any change to `pull_email`/`email_pull.py`.
- Flipping `email-capture-pipeline`'s working mode — `T04`, once both
  `AC-01` and `AC-02` are verified.

---

## Context / Notes

Full architectural reasoning: `Implementation/Architecture/ADR.md` →
`ADR-052`; `Implementation/Architecture/architecture.md` → "Legacy
flat-shape Thread recognition — self-healing migration on first touch".
The story's own `## Notes` (both decomposer passes) and `ESCALATIONS.md` →
`ESC-055` (now `Resolved`, naming `ADR-052` as the resolving artefact)
explain the full history of why this task exists and why it is scoped to
`vault_writer.py` alone, independent of `T01`'s own composing-function
rewire.

---

## Implementation Log

**2026-08-19, coder.** Implemented exactly as specced against the real,
current `src/backend/app/data_access/vault_writer.py`: added
`migrate_flat_thread_to_directory(flat_path)` (placed directly before
`resolve_thread_directory`) and replaced `resolve_thread_directory`'s body
with the two-tier scan (directory-shaped first, flat-note second-on-miss).
`list_thread_notes()` and `resolve_thread_note_path()` bodies untouched —
confirmed by diff review (only the one function body replaced, one new
function added). No new import needed — `Path`/`settings`/`read_note`/
`_THREADS_SUBFOLDER` already in scope, confirmed before writing.

**No locked AC in this task** (AC-01 is verified live in T04) — the
5 manual smoke/regression steps below are this task's own non-AC-tagged
checks, all run against the real, live configured vault
(`VAULT_PATH = C:\myWorx\Moussa MD\Moussa Brain`), `.venv\Scripts\python.exe`,
cwd `src/backend`:

1. `python -c "import app.data_access.vault_writer"` — clean import, no
   syntax error. PASS.
2. Directory-shaped regression check: picked a real, already-existing
   directory-shaped Thread (`2026-07-28 Azerbaijan Engagement...`),
   confirmed `resolve_thread_directory(conversation_id)` returns the SAME
   directory as before (first scan tier unaffected). PASS.
3. Migration check: enumerated the 7 real flat notes with no known
   directory-shaped duplicate (cross-checked each of their `conversation_id`s
   against every real directory-shaped Thread's own frontmatter — confirmed
   programmatically, not visually — only `ED0954959F6F4A4C88F9E2ACA3D7113A`
   [Azure] has a duplicate; the other 7 are clean). Chose
   `Requested Item RITM0108464 has been updated-2026-07-27-025663bd.md`
   (`conversation_id CF7FD118DD45F740ACAD6B93AB83BEB5`) as this task's own
   smoke-test candidate (a DIFFERENT flat note is reserved for T04's own
   live AC-01 verification, so T04 still has a genuinely un-migrated
   candidate to exercise the real `process_staged_email` path against).
   Called `resolve_thread_directory(conversation_id)` — confirmed: (a) new
   directory created at `Work/Threads/CF7FD118DD45F740ACAD6B93AB83BEB5/`;
   (b) contains `CF7FD118DD45F740ACAD6B93AB83BEB5.md` with frontmatter AND
   body byte-identical to the original flat note's own prior content
   (compared directly via `read_note` equality, not visual inspection) plus
   an empty `messages/` subdirectory; (c) the original flat file no longer
   exists at its own prior path. PASS. This is a REAL, permanent,
   self-healing migration of live vault content — the intended outcome per
   `ADR-052`, not verification noise; not reverted.
4. Idempotency check: called `resolve_thread_directory` a second time for
   the SAME `conversation_id` — returned the identical directory via the
   FIRST (now directory-shaped) scan tier, no re-migration attempt, no
   raise. PASS.
5. Already-diverged Azure case: called
   `resolve_thread_directory("ED0954959F6F4A4C88F9E2ACA3D7113A")` — returned
   the EXISTING `2026-08-17 Azure-Net New Revenue Forecast for H2 for AM
   Updates/` directory-shaped duplicate; confirmed the 07-27 flat Azure note
   is still untouched/still exists at its own original path (no attempted
   migration, no raise). PASS — confirms `ADR-052`'s ordering rule holds for
   the one real, already-manifested collision case in the live vault.

**Acceptance Criteria checklist:**
- [x] `migrate_flat_thread_to_directory` migrates byte-identical content to
      the standard shape (step 3); `FileExistsError`-on-collision path is
      structurally identical to `rename_thread_directory`'s own
      already-Accepted, already-tested discipline — not independently
      re-exercised live (no real collision candidate exists in the live
      vault to safely induce one without fabricating data), code-reviewed
      instead.
- [x] Second scan tier tried only on a miss, matches by `conversation_id`,
      migrates, returns the NEW directory (steps 3/4)
- [x] `list_thread_notes()`/`resolve_thread_note_path()` bodies byte-for-byte
      unchanged (confirmed by diff — neither function's body was touched)
- [x] The already-diverged `ED0954959F6F4A4C88F9E2ACA3D7113A` case correctly,
      silently no-ops (step 5)
- [ ] `MEMORY.md` — see story-level `MEMORY.md` entry recorded once the full
      story reaches `Done` (single consolidated entry, not per-task)
- [x] `CHANGELOG.md` entry appended (this task's own commit)

No deviations from the plan. No out-of-scope event. Gate: clear — smoke
checks pass, no locked AC in this task, real vault left in its correct,
intended post-migration state (one additional real flat Thread now
directory-shaped — this is the fix working, not noise to clean up).
