---
id: BUGFIX-05-US-01-T05
title: Preserve a freshly-migrated flat Thread's pre-migration ## Summary via a one-time pre_migration_summary.md sidecar (ADR-053)
parent_story: BUGFIX-05-US-01
requirement_id: BUG-026
type: backend
status: Done
gate: clear
gate_reason: ""
depends_on: [BUGFIX-05-US-01-T03]
created: 2026-08-19
updated: 2026-08-19
---

# BUGFIX-05-US-01-T05 — Preserve a freshly-migrated flat Thread's pre-migration ## Summary via a one-time pre_migration_summary.md sidecar (ADR-053)

## Parent Story

- Story: [[BUGFIX-05-US-01]] — `../UserStories/BUGFIX-05-US-01-email-thread-processing-retires-legacy-thread-match-merge.md`
- Requirement: `BUGS.md` → `BUG-026` (bugfix story; no PRD requirement anchor)

---

## Objective

Close `ESC-056`'s own content-loss gap per `ADR-053`: `migrate_flat_thread_
to_directory` (`vault_writer.py`, `T03`) gains one additional,
content-preservation step — before the file move, it reads the flat
note's own pre-migration `## Summary` and, if non-empty, writes it
verbatim to a new sidecar file, `<new-directory>/pre_migration_summary.
md`, living OUTSIDE `messages/`. `synthesize_thread`
(`email_classification.py`) gains one small, additive read/fold/archive
step — immediately before its existing Compass call, it folds that
sidecar's text in as prior-history grounding (never a second Compass
call), then renames the sidecar to `pre_migration_summary.consumed.md`
on a successful synthesis only, never deleting it. This is a deliberate,
disclosed departure from `BUGFIX-05-US-01-T01`'s own task-level "must NOT
modify `email_classification.py`" constraint — that constraint was scoped
to `T01`'s own narrower rewire concern, not a standing prohibition;
`ADR-053` supersedes it for this one, narrow, additive change only. This
task closes `AC-01`'s re-locked "genuinely preserved" clause at the
implementation layer — live, end-to-end verification (via the real
`process_staged_email` capability) happens in `T04`, not this task, since
the two write/read halves are tightly coupled (one sidecar, written by
one function and consumed by another in the SAME pipeline tick) and
cannot be meaningfully verified in isolation from each other.

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.migrate_flat_thread_to_directory(flat_path)` (`T03`,
  `Done`) performs a pure filesystem-shape migration only — no sidecar,
  no content-preservation step. Confirmed live (`ESC-056`) to silently
  lose a freshly-migrated flat Thread's real, substantive pre-migration
  `## Summary` the first time `synthesize_thread` next runs on it (which
  regenerates `## Summary` purely from `messages/`, which the migration
  correctly leaves empty).
- `email_classification.synthesize_thread(conversation_id)` (already
  `Done`, `REQ-SB-71-US-02`, untouched by `T01`) composes `full_content`
  from every raw message note under the Thread's own current `messages/`
  directory alone and calls `compass_client.summarize_content` exactly
  once, writing the result to `## Summary` via `replace_body_section`.
- `vault_writer.list_all_note_paths()` excludes `index.md`/`log.md`/
  `captures.md` by filename (`_OKF_RESERVED_FILENAMES`) — no equivalent
  exclusion exists yet for a Thread-directory sidecar file.
- **A real, already-live residual gap this task also closes:** `T03`'s own
  smoke test already permanently migrated one real flat Thread
  (`conversation_id CF7FD118DD45F740ACAD6B93AB83BEB5`, "Requested Item
  RITM0108464 has been updated") to the standard directory shape, BEFORE
  this sidecar mechanism existed — its own real, substantive pre-migration
  `## Summary` is currently still intact on its migrated concept file
  (confirmed byte-identical by `T03`'s own Implementation Log,
  `synthesize_thread` has not run on it since), but it has NO sidecar —
  the exact same content-loss failure `ESC-056` found would silently recur
  for this ONE specific, already-migrated, real Thread the next time a
  genuinely new message naturally arrives for it. This task performs a
  bounded, one-time manual backfill for this ONE Thread only (see step 6
  in `## Tests` below) — not a general retroactive-backfill mechanism, and
  not a new architectural decision (it is a direct, narrow application of
  `ADR-053`'s own already-decided sidecar shape to one already-known real
  case).

**After / Outputs:**
- `migrate_flat_thread_to_directory` writes a `pre_migration_summary.md`
  sidecar (plain text, no frontmatter) into the new Thread directory,
  verbatim from the flat note's own pre-migration `## Summary`, BEFORE the
  file move — a true no-op (no file written) when that Summary is empty.
- `synthesize_thread` prepends that sidecar's text (when present) to
  `full_content` as an explicitly-labeled prior-history block ahead of the
  real per-message content, feeding the SAME existing Compass call — never
  a second call, never a new function. On a successful synthesis, the
  sidecar is renamed in place to `pre_migration_summary.consumed.md`
  (archive-not-delete, fed exactly once). On a failed synthesis
  (`CompassError`), it is left untouched, retried on the next successful
  run.
- `list_all_note_paths()` excludes both `pre_migration_summary.md` and
  `pre_migration_summary.consumed.md` by filename.
- `Requested Item RITM0108464 has been updated`'s own already-migrated
  Thread directory has a real, correctly-populated `pre_migration_
  summary.md` sidecar, written from its own still-intact current
  `## Summary`, so its next natural `synthesize_thread` run folds its real
  history in instead of silently losing it.
- No `section_ownership.py` change. `_build_graph()`/`_GRAPH`/`get_job_
  tree()` and every graph node function remain byte-for-byte unchanged.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py`:
  1. Extend `migrate_flat_thread_to_directory`'s own docstring with one
     additional paragraph (per `ADR-053` Decision 1) and insert the new
     sidecar-write step BETWEEN the target-directory `mkdir` and the flat
     file `rename` — replace the function's exact body with:

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
         creation), never note body or frontmatter content -- EXCEPT for
         one narrow, disclosed exception (BUGFIX-05-US-01, ADR-053):
         BEFORE the rename, reads the flat note's own pre-migration
         ## Summary via the existing read_body_section primitive (no new
         reader) and, if non-empty, writes it VERBATIM to a new sidecar
         file, <new-directory>/pre_migration_summary.md -- plain text, no
         frontmatter, created AFTER the target directory but BEFORE the
         flat file is renamed, living OUTSIDE messages/ so it is
         structurally invisible to list_thread_notes() and to
         synthesize_thread's own messages_dir glob. If the flat note's
         own ## Summary is empty, no sidecar file is written -- a true
         no-op. synthesize_thread folds this sidecar into its own next
         real synthesis as prior-history grounding and archives it to
         pre_migration_summary.consumed.md on success. Returns the new
         concept file path."""
         frontmatter, _ = read_note(flat_path)
         conversation_id = frontmatter["conversation_id"]
         paths = thread_directory_paths(conversation_id)
         if paths["directory"].exists():
             raise FileExistsError(
                 f"would overwrite existing Thread directory at {paths['directory']}"
             )
         paths["directory"].mkdir(parents=True, exist_ok=True)
         pre_migration_summary = read_body_section(flat_path, "## Summary")
         if pre_migration_summary:
             (paths["directory"] / "pre_migration_summary.md").write_text(
                 pre_migration_summary, encoding="utf-8"
             )
         flat_path.rename(paths["concept"])
         paths["messages"].mkdir(parents=True, exist_ok=True)
         return paths["concept"]
     ```

  2. Add a new reserved-filename set directly after `_OKF_RESERVED_
     FILENAMES` and extend `list_all_note_paths`'s own filter — replace:

     ```python
     _OKF_RESERVED_FILENAMES = {"index.md", "log.md", "captures.md"}
     ```

     with:

     ```python
     _OKF_RESERVED_FILENAMES = {"index.md", "log.md", "captures.md"}
     _THREAD_SIDECAR_RESERVED_FILENAMES = {
         "pre_migration_summary.md", "pre_migration_summary.consumed.md",
     }
     ```

     and replace `list_all_note_paths`'s own `return` statement:

     ```python
         return sorted(
             path for path in work_root.rglob("*.md")
             if path.name not in _OKF_RESERVED_FILENAMES and path.is_file()
         )
     ```

     with:

     ```python
         return sorted(
             path for path in work_root.rglob("*.md")
             if path.name not in _OKF_RESERVED_FILENAMES
             and path.name not in _THREAD_SIDECAR_RESERVED_FILENAMES
             and path.is_file()
         )
     ```

     (Append one sentence to `list_all_note_paths`'s own docstring naming
     the new exclusion and `BUGFIX-05-US-01`/`ADR-053` — do not otherwise
     alter its docstring.)

- `src/backend/app/business/email_classification.py`:
  1. In `synthesize_thread`, immediately BEFORE the existing
     `full_content = "\n\n---\n\n".join(...)` assignment, insert:

     ```python
         pre_migration_summary_path = path.parent / "pre_migration_summary.md"
         pre_migration_summary_text = (
             pre_migration_summary_path.read_text(encoding="utf-8")
             if pre_migration_summary_path.exists() else ""
         )

     ```

  2. Replace the existing `full_content = "\n\n---\n\n".join(...)` block
     (unchanged internals) with the SAME block, then immediately append
     the prior-history prepend:

     ```python
         full_content = "\n\n---\n\n".join(
             f"From: {message['sender']} <{message['sender_email']}>\n"
             f"Received: {message['received']}\nSubject: {message['subject']}\n\n"
             f"{message['body']}"
             for message in messages
         )
         if pre_migration_summary_text:
             full_content = (
                 "Prior history (pre-migration Summary, preserved verbatim "
                 "from before this Thread was migrated to its current "
                 "shape):\n" + pre_migration_summary_text
                 + "\n\n---\n\n" + full_content
             )
     ```

  3. In the existing `try` block, immediately AFTER the existing
     `vault_writer.replace_body_section(path, "## Summary", ...)` call
     (still inside the `try`, before the `except compass_client.
     CompassError` line), insert:

     ```python
             if pre_migration_summary_path.exists():
                 pre_migration_summary_path.rename(
                     path.parent / "pre_migration_summary.consumed.md"
                 )
     ```

     (Do NOT add any handling inside the `except compass_client.
     CompassError` branch — the sidecar must be left completely untouched
     on a failed synthesis, which is what leaving that branch unchanged
     already achieves.)

  4. Append one short paragraph to `synthesize_thread`'s own docstring
     documenting the sidecar read/fold/archive step and referencing
     `BUGFIX-05-US-01`/`ADR-053` — do not alter any other existing
     paragraph of that docstring.

---

## Constraints

- Inherits from parent story (real, live vault — no fixture; must not
  touch `pull_email`/`email_pull.py`; no-data-loss is load-bearing, not a
  convenience).
- Must NOT modify `synthesize_thread`'s create-vs-update decision,
  classification call, tags/customer/participants frontmatter logic,
  `route_to_project` trigger, or Files/OKF companion writes — only the
  three additive changes named above (sidecar read before `full_content`
  is built; prior-history prepend; sidecar archive-rename on success).
- Must reuse the EXISTING `read_body_section` primitive for the
  pre-migration read in `migrate_flat_thread_to_directory` — no new
  reader.
- The sidecar file must be plain text with no frontmatter block, and must
  be written OUTSIDE `messages/` (directly under the new Thread
  directory) — never inside `paths["messages"]`.
- The sidecar must be written ONLY when the flat note's own pre-migration
  `## Summary` is non-empty — a genuinely empty Summary must produce no
  sidecar file at all (a true no-op), not an empty sidecar file.
- The archive-rename to `pre_migration_summary.consumed.md` must happen
  ONLY inside the `try` block, only after the `replace_body_section` call
  has already succeeded — never on a `CompassError`, never speculatively
  before the Compass call.
- Must NOT add any new `section_ownership.py` allow-list entry — `##
  Summary`'s existing `{"email_classification.synthesize_thread"}` entry
  is unchanged; the sidecar is never written via `replace_body_section`
  and carries no `## `-level header of its own.
- Must NOT modify `_build_graph()`, `_GRAPH`, `get_job_tree()`,
  `EmailCapturePipelineState`, or any `_..._node`/`_route_after_...`
  function — untouched by this task.
- Must NOT modify `resolve_thread_directory()`'s own second-scan-tier
  logic beyond what already exists (`T03`) — this task only extends
  `migrate_flat_thread_to_directory`'s own body, which that scan tier
  already calls unchanged.
- The one-time manual backfill for `CF7FD118DD45F740ACAD6B93AB83BEB5`
  (`RITM0108464`) must use ONLY its own current, real, live `## Summary`
  content (read directly, verbatim) — never a fabricated or
  reconstructed one — and must re-confirm, at execution time, that its
  `messages/` directory is still empty and its `## Summary` is still
  intact before writing the sidecar (if a genuinely new message already
  landed for it naturally since `T03`'s own smoke test, its Summary may
  already have been regenerated/lost independently of this task — if so,
  do not fabricate a sidecar from stale/incorrect assumptions; escalate
  the finding instead of silently proceeding).

---

## Tests

<!-- No locked AC is verified in this task — AC-01 is verified live,
end-to-end, in T04, once this task's write+read halves are both in
place (they are tightly coupled: a sidecar written by one function and
consumed by another in the SAME pipeline tick cannot be meaningfully
verified in isolation from each other). This task carries its own real,
non-AC-tagged regression/smoke checks of both halves plus the one-time
RITM0108464 backfill. -->

**Manual verification steps (live against the real configured vault —
`VAULT_PATH`; real `.venv\Scripts\python.exe`, cwd `src/backend`):**

1. Import `app.data_access.vault_writer` and
   `app.business.email_classification` cleanly (confirms no syntax
   error).
2. Enumerate the real flat Thread notes still live (`Work/Threads/*.md`)
   and pick one with a real, non-empty, substantive `## Summary`, EXPLICITLY
   DIFFERENT from `conversation_id 041969487D51E942B77F5CD4A13A6CC2`
   (`Compass Alert- Failed API Calls`, reserved for `T04`'s own live
   `AC-01` re-verification) and from `CF7FD118DD45F740ACAD6B93AB83BEB5`
   (already migrated by `T03`) and from
   `ED0954959F6F4A4C88F9E2ACA3D7113A` (the already-diverged Azure case).
   Record its own `conversation_id` and its full pre-migration
   `## Summary` text (baseline).
3. Call `vault_writer.migrate_flat_thread_to_directory(flat_path)`
   directly for the step-2 candidate. Confirm: (a) a new directory exists
   at the deterministic slug location; (b) a `pre_migration_summary.md`
   file exists directly under that directory (NOT under `messages/`),
   with text byte-identical to step 2's own recorded baseline; (c) the
   migrated concept file's own frontmatter/body are otherwise
   byte-identical to the original flat note's own prior content, just
   relocated; (d) `messages/` exists and is empty; (e) the original flat
   file no longer exists at its own prior path.
4. Confirm `vault_writer.list_all_note_paths()` does NOT include the
   `pre_migration_summary.md` path from step 3.
5. Stage one new, clearly-marked synthetic message
   (`id: "T05-VERIFICATION-0001"`) for the SAME `conversation_id` (via
   the real `email_staging.stage_email` primitive, per this project's
   own disclosed substitute precedent). Call
   `email_classification.synthesize_thread(conversation_id)` directly
   (a Stage-2-only unit call — the full, real capability-endpoint proof
   is `T04`'s own job, not this task's). Confirm: (a) the regenerated
   `## Summary` genuinely reflects content from BOTH the step-2 baseline
   text's own real subject matter AND the new synthetic message — read it
   directly and confirm both are represented, not just that it is
   non-empty; (b) `pre_migration_summary.md` no longer exists at its own
   path; `pre_migration_summary.consumed.md` now exists there instead,
   with the SAME text as the step-2 baseline (archived, not deleted); (c)
   `vault_writer.list_all_note_paths()` still excludes both filenames.
6. Call `synthesize_thread(conversation_id)` a SECOND time (stage one more
   new synthetic message first) for the SAME `conversation_id`. Confirm
   the regenerated `## Summary` no longer re-prepends the step-2 baseline
   text (only the real message content is reflected this time) and
   `pre_migration_summary.consumed.md` is untouched (still present,
   unchanged content) — confirms the fold-in happens EXACTLY ONCE.
7. **One-time backfill for the already-migrated, sidecar-less
   `RITM0108464` Thread** (`conversation_id
   CF7FD118DD45F740ACAD6B93AB83BEB5`): read its current concept file
   directly. Confirm its `messages/` directory is still empty and its
   `## Summary` still holds real, substantive pre-migration content (not
   already regenerated/lost by an intervening natural update since `T03`'s
   own smoke test). If confirmed, read that `## Summary` text via
   `read_body_section` and write it verbatim to a new
   `pre_migration_summary.md` sidecar directly under that Thread's own
   directory (the SAME shape `migrate_flat_thread_to_directory` now
   produces for a fresh migration) — a manual, one-time application of
   this task's own already-built mechanism to this one specific,
   already-migrated real Thread, not a new code path. If its `messages/`
   is no longer empty or its Summary has already changed, STOP and
   escalate this finding instead of proceeding (see `## Constraints`).
8. Cleanup: delete only the synthetic raw message notes/participant
   entries steps 5/6 produced (clearly-marked synthetic content) — do NOT
   revert the migration, the sidecar-consumption, or the `RITM0108464`
   backfill; these are the correct, permanent, intended real end states.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `migrate_flat_thread_to_directory` writes `pre_migration_summary.md`
      verbatim (via `read_body_section`, no new reader), OUTSIDE
      `messages/`, before the rename, only when the flat note's own
      `## Summary` is non-empty
- [x] `synthesize_thread` folds the sidecar's text into its SAME existing
      Compass call (never a second call) as an explicitly-labeled
      prior-history block, when the sidecar is present
- [x] On a successful synthesis, the sidecar is renamed to
      `pre_migration_summary.consumed.md`; on a failed synthesis it is
      left completely untouched
- [x] `list_all_note_paths()` excludes both `pre_migration_summary.md`
      and `pre_migration_summary.consumed.md`
- [x] No `section_ownership.py` change
- [x] `RITM0108464`'s already-migrated, sidecar-less Thread has a
      correctly-backfilled `pre_migration_summary.md` sidecar (or the
      backfill is explicitly escalated as not-safe, per step 7)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Live, end-to-end verification of `AC-01` via the real
  `process_staged_email` capability endpoint, and the working-mode flip —
  `T04`.
- Any general, proactive, bulk backfill mechanism for other
  already-migrated Threads — this task's own `RITM0108464` backfill is a
  bounded, one-time, manually-verified application to the ONE specific
  real Thread this story's own `T03` smoke test already migrated before
  this sidecar mechanism existed; not a standing capability.
- Fixing, merging, or otherwise reconciling the already-diverged
  `ED0954959F6F4A4C88F9E2ACA3D7113A` duplicate — deferred to a future
  Librarian-housekeeping backlog item, per the architect's own explicit
  Decision 2 and `ESC-055`'s resolution note.
- Any change to `pull_email`/`email_pull.py`.
- Any change to `_build_graph()`/`_GRAPH`/`get_job_tree()`/graph node
  functions, or to `resolve_thread_directory()`'s own scan-tier ordering.

---

## Context / Notes

Full architectural reasoning: `Implementation/Architecture/ADR.md` →
`ADR-053`; `Implementation/Architecture/architecture.md` → "Migration
content-preservation — the `pre_migration_summary.md` sidecar". The
story's own `## Notes` (all four decomposer/architect passes) and
`ESCALATIONS.md` → `ESC-056` (now `Resolved`, naming `ADR-053` as the
resolving artefact) explain the full history of why this task exists.
`T04`'s own recommended live-verification target
(`conversation_id 041969487D51E942B77F5CD4A13A6CC2`, "Compass Alert-
Failed API Calls") is deliberately reserved, not consumed by this task's
own smoke test — its own restoration is confirmed byte-identical in
`T04`'s own Implementation Log.

---

## Implementation Log

**2026-08-19, coder.** Implemented `ADR-053`'s sidecar mechanism exactly
per this task's own `## Files to Modify` code blocks:
- `vault_writer.migrate_flat_thread_to_directory` now reads the flat
  note's own pre-migration `## Summary` via `read_body_section` and, if
  non-empty, writes it verbatim to `<new-directory>/pre_migration_
  summary.md` BEFORE the rename; a true no-op when the Summary is empty.
- `vault_writer.list_all_note_paths` now also excludes
  `pre_migration_summary.md`/`pre_migration_summary.consumed.md` via the
  new `_THREAD_SIDECAR_RESERVED_FILENAMES` set.
- `email_classification.synthesize_thread` now reads the sidecar (if
  present) immediately before composing `full_content`, prepends it as an
  explicitly-labeled prior-history block feeding the SAME existing
  Compass call, and — only inside the `try` block, only after
  `replace_body_section` succeeds — renames it to `pre_migration_summary.
  consumed.md`. Left completely untouched on `CompassError`. No
  `section_ownership.py` change; no `_build_graph`/graph-node change.

**Import check (step 1):** `.venv\Scripts\python.exe -c "import app.data_
access.vault_writer; import app.business.email_classification"` — clean,
no error.

**Candidate selection (step 2):** Enumerated `Work/Threads/*.md` (7 flat
notes). Chose `Masdar Data -2026-07-27-7aa33daf.md` (`conversation_id
45597B7A26F545B3882C53D78B52C628`) — explicitly different from
`041969487D51E942B77F5CD4A13A6CC2` (Compass Alert, reserved for `T04`,
re-confirmed byte-identical/restored before this task touched anything),
`CF7FD118DD45F740ACAD6B93AB83BEB5` (`RITM0108464`, already migrated by
`T03`), and `ED0954959F6F4A4C88F9E2ACA3D7113A` (Azure, already diverged).
Baseline `## Summary` recorded verbatim via `read_body_section` (722
chars, the real Masdar pricing-table content).

**Steps 3-4 — migration + sidecar write:** Called `vault_writer.migrate_
flat_thread_to_directory(flat_path)` directly. Confirmed: new directory
at `Work/Threads/45597B7A26F545B3882C53D78B52C628/`; `pre_migration_
summary.md` written directly under that directory (NOT under
`messages/`), byte-identical to the step-2 baseline (confirmed via
Python string equality, not visual inspection); `messages/` created and
empty; original flat file gone. `list_all_note_paths()` confirmed to NOT
include the sidecar path.

**Step 5 — fold-in + archive (PASS):** Staged one synthetic message
(`id: "T05-VERIFICATION-0001"`, subject prefixed `[BUGFIX-05-US-01-T05
verification]`) via `email_staging.stage_email`. **Assumption/judgement
call (logged per Pipeline.md's scope-internal-judgement-call guidance):**
rather than invoking `raw_message_capture.capture_raw_thread_messages`
(which would trigger a REAL Outlook-COM fetch via `pull_and_stage_emails`
— out of this Stage-2-only unit call's intent and a real stall/hang risk
per this session's own standing constraints), wrote the raw message note
directly via `vault_writer.create_raw_message_note` (Stage 1's own real,
unmodified write primitive) with the exact staged content, then removed
the staged entry — mechanically equivalent to what Stage 1 would have
drained, without the COM dependency. Called `email_classification.
synthesize_thread(conversation_id)` directly. Result: `synthesized: True`,
no `summary_error`. Read the regenerated `## Summary` directly: it
genuinely describes BOTH the original pricing-table content (Sentinel &
Cloud $39,000, AVD $30,000, DBX Executive Dashboard $50,000, etc.) AND the
new synthetic message's own content (the follow-up call reference) —
never a bare replacement. `pre_migration_summary.md` no longer exists;
`pre_migration_summary.consumed.md` exists in its place, text-identical to
the step-2 baseline (722 chars). `list_all_note_paths()` re-confirmed to
exclude both filenames.

**Step 6 — exactly-once fold-in (PASS):** Staged/wrote a second synthetic
raw message note (`id: "T05-VERIFICATION-0002"`) the same way, called
`synthesize_thread` again. Regenerated `## Summary` now reflects ONLY the
two synthetic messages (the pricing-table content is no longer
re-prepended — confirmed by direct reading). `pre_migration_summary.
consumed.md` confirmed byte- and mtime-unchanged (untouched) — the fold-in
happened exactly once, on the first successful synthesis only.

**Step 7 — RITM0108464 backfill (PASS):** Re-confirmed at execution time
(fresh, not trusting `T03`'s own prior log): `CF7FD118DD45F740ACAD6B93AB83BEB5`'s
`messages/` still empty (0 files) and its `## Summary` still real and
substantive (537 chars, the OMNI/SCTASK0199006 content) — no intervening
natural update since `T03`. Read that `## Summary` via `read_body_section`
and wrote it verbatim to a new `pre_migration_summary.md` sidecar directly
under that Thread's own directory (confirmed byte-identical). No
escalation needed — preconditions held.

**Step 8 — cleanup (done):** Deleted both synthetic raw message notes
under the Masdar Data Thread's `messages/` (now empty again). Removed
`verification@example.invalid` from that Thread's `participants`
frontmatter (via `upsert_frontmatter_key`), leaving `amraze@microsoft.com`
only. Confirmed `email_staging` empty. Found and declined (via the real
`POST /pending-approvals/{id}/decline` endpoint) two stray
`acknowledge_classification_failure` Pending Approvals (`6a6555d8a8a7`,
`ffbca35a94ec`) referencing only the synthetic verification subjects — no
other stray approvals from this task's own activity. Did NOT revert the
migration, the sidecar-consumption, or the RITM0108464 backfill — per this
task's own Constraints, these are the correct, permanent, intended real
end states. **Disclosed note:** after cleanup, the Masdar Data Thread's
live-facing `## Summary` reflects only the two (now-deleted) synthetic
messages' content, since `messages/` is empty again and nothing re-runs
synthesis; the real, original pre-migration content is NOT lost — it
remains durably archived, verbatim, at `pre_migration_summary.consumed.
md` (722 chars, unchanged) — exactly the "correct, permanent, intended
real end state" this task's Constraints describe, mirroring every other
un-migrated flat Thread's own "self-heals the next time a real message
lands" contract.

**Acceptance Criteria checklist:**
- [x] `migrate_flat_thread_to_directory` writes `pre_migration_summary.md`
      verbatim, OUTSIDE `messages/`, before the rename, only when non-empty
- [x] `synthesize_thread` folds the sidecar into its SAME existing Compass
      call as an explicitly-labeled prior-history block
- [x] On success the sidecar is renamed to `pre_migration_summary.
      consumed.md`; left untouched on failure (mechanism confirmed by code
      review — no `CompassError` occurred in this task's own live runs to
      trigger the untouched-on-failure branch directly, but the `try`-block
      placement is confirmed correct by inspection)
- [x] `list_all_note_paths()` excludes both filenames
- [x] No `section_ownership.py` change
- [x] `RITM0108464`'s Thread has a correctly-backfilled `pre_migration_
      summary.md` sidecar
- [x] `MEMORY.md` updated (see repo-root `MEMORY.md`)
- [x] `CHANGELOG.md` entry appended

gate: clear 2026-08-19 — no triggers fired (no ADR change — implements an
already-Accepted `ADR-053`; one scope-internal judgement call disclosed
above, not a MUST-FLAG assumption about requirements; no new dependency;
no contradictory inputs). **Task Done.**
