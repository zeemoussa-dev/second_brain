---
id: REQ-SB-72-US-01-T04
title: Files/OKF backfill Job + structured ## Files section writer
parent_story: REQ-SB-72-US-01
requirement_id: REQ-SB-72
type: backend
status: Done
gate: flagged
gate_reason: "Two real, disclosed out-of-scope defects found live and escalated (ESC-051, ESC-052) — one defensive one-line fix applied in-scope (list_all_note_paths path.is_file() guard) to keep the live system healthy; root causes left unfixed, per this project's disclose-don't-fix precedent. See Implementation Log."
phase: P1
depends_on: [REQ-SB-72-US-01-T01]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-72-US-01-T04 — Files/OKF backfill Job + structured `## Files` section writer

## Parent Story

- Story: [[REQ-SB-72-US-01]] — `../UserStories/REQ-SB-72-US-01-librarian-section-first-housekeeping-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-72 *The Librarian Section — First Housekeeping Pipeline*
- Architecture: `Implementation/Architecture/architecture.md` → "Files/OKF backfill + `## Files` section" (`ADR-049` Decision 3), "Section-ownership registrations"

---

## Objective

Build the Files Backfill Job: for every real attachment Stage 1 already durably persisted with no `files/<slug>/` companion yet, create one via the existing, unchanged `email_classification.write_file_companion`; then write a new, structured `## Files` section onto the owning Thread's own concept file listing every companioned attachment.

---

## Starting State → End State

**Before / Inputs:**
- Real attachment bytes already durably persisted at `Work/Threads/attachments/<slug-of-conversation_id>/<slug-of-message_id>/<filename>` (`raw_message_capture.py`, unchanged, unmodified by this task).
- `email_classification.write_file_companion(attachment_path, message_id, thread_directory)` already creates a `files/<slug>/` companion note + copies the real bytes (`REQ-SB-71-US-02-T07`, unchanged, reused verbatim).
- No Thread concept file has a `## Files` section — `create_thread_note_baseline`'s body is `## Summary` / `## Personal Notes` / `## Actions` / `## Related` only; `replace_body_section` no-ops (never creates) when a header is absent.
- No caller id is registered for a `## Files` write in `section_ownership.py`.

**After / Outputs:**
- New `vault_writer.insert_body_section_if_missing(path, header: str) -> bool` primitive — mirrors `insert_body_line_if_missing`'s own idempotent "top up only if absent" contract, appended here to a `## `-level header: appends `f"\n\n{header}\n"` to the end of the body if `header` is not already present anywhere in the file (checked via the SAME exact-line-match regex `replace_body_section` uses); returns `True` if inserted, `False` if already present. Never touches an already-present header's own content.
- New `librarian_housekeeping.backfill_files() -> dict` Job:
  - Iterates `vault_writer.list_thread_notes()`.
  - For each Thread, resolves its CURRENT `messages/` directory (via the Thread's own already-known path — this Job operates on whatever directory `list_thread_notes()` currently reports, so it is correct for both renamed and not-yet-renamed Threads with no extra resolution step needed).
  - For every raw message under that Thread's `messages/`, calls `vault_writer.staged_attachment_files(conversation_id, message_id)`; for any attachment with no existing `files/<slug>/` companion yet (checked before calling `write_file_companion`, since that function itself has no built-in existence guard), calls `email_classification.write_file_companion(attachment_path, message_id, thread_directory)` — unchanged, never a second, divergent companion primitive.
  - After processing every message, calls `vault_writer.insert_body_section_if_missing(concept_path, "## Files")`, then `vault_writer.replace_body_section(concept_path, "## Files", <structured content>, caller="librarian_housekeeping.backfill_files")` — a WHOLESALE regeneration of the section from the Thread's own current, complete companion set (never a per-run append/patch, mirrors this codebase's own "regenerate, don't patch" invariant), listing each companioned attachment's filename, the owning raw message's own `received` date, a short blurb drawn from the companion note's own `## Summary` (`vault_writer.read_body_section`), and a real `[[wikilink]]` to the companion note itself.
  - Returns `{"companioned": [...], "already_companioned": [...], "threads_updated": [...]}`.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add `insert_body_section_if_missing`.
- `src/backend/app/business/pipelines/librarian_housekeeping.py` — add `backfill_files()` Job.
- `src/backend/app/data_access/section_ownership.py` — add `"librarian_housekeeping.backfill_files": frozenset({"## Files"})` to `_CALLER_ALLOW_LISTS`.

---

## Constraints

- Inherits from parent story.
- Reuses `email_classification.write_file_companion` UNCHANGED — never a second, divergent Files/OKF companion primitive.
- `## Files` is written ONLY by `librarian_housekeeping.backfill_files` — the caller id registered in `section_ownership.py` must be exact-match (`module.function` granularity, per `ADR-048` Decision 2's own established discipline).
- Idempotent: re-running never creates a second companion for an already-companioned attachment, and never duplicates a `## Files` entry (regenerated wholesale, not appended).
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-72-US-01-AC-03]` Direct Python-shell check against the real vault: identify (or construct via a disposable test message + a real staged attachment) a real attachment already durably persisted under `Work/Threads/attachments/...` with no `files/<slug>/` companion yet. Call `librarian_housekeeping.backfill_files()`. Confirm a real `files/<slug>/` directory now exists under the owning Thread, containing the original attachment byte-identical to the source, plus a generated OKF companion note whose `## Summary` carries a real, genuine, content-grounded summary (not a placeholder).
2. `[REQ-SB-72-US-01-AC-04]` Re-run `librarian_housekeeping.backfill_files()` a second time, including over the SAME attachment from step 1. Confirm no second, duplicate companion directory/note is created, and the existing companion note's own content (frontmatter + body) is byte-for-byte unchanged before/after.
3. `[REQ-SB-72-US-01-AC-05]` Confirm the owning Thread's own concept file — across more than the 2 Threads already companioned before this story shipped (use the real vault's existing companioned Threads plus at least one new one from step 1) — carries a structured `## Files` section, distinct from `## Summary`'s own prose, listing each companioned attachment's filename, a real date, a short summary blurb, and a real, working `[[wikilink]]` to the companion note (confirm the link's target file actually exists at the resolved path).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `backfill_files()` creates a real Files/OKF companion for every un-companioned real attachment
- [x] Re-running never creates a duplicate companion
- [x] `## Files` section lists every companioned attachment with filename/date/summary/working link
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `## Related` ownership transfer — `T06`.
- Company-mention detection / Customer folder backfill — `T05`/`T07`.
- The orchestrating `run_housekeeping_pass` capability and the `/poc/librarian-backfill-files` HTTP endpoint — `T08`.

---

## Context / Notes

`write_file_companion`'s own `file_slug = f"{hash8(message_id)}-{filename}"` convention (`REQ-SB-71-US-02-T07`) is what keeps two different messages in the same Thread sharing one same-named attachment from colliding — reused verbatim here, not re-derived.

---

## Implementation Log

**2026-08-18, coder pass.** Added `vault_writer.insert_body_section_if_
missing`, `librarian_housekeeping.backfill_files()`, and the `## Files`
`section_ownership.py` registration.

**Real bug found and fixed during build (before first real run):**
`email_classification.write_file_companion` can honestly FAIL (e.g. a
scanned/image-only PDF with no extractable text) and return `{"saved":
False, "summary_error": ...}` WITHOUT ever creating a companion file —
my own first draft assumed it always succeeds and crashed reading the
non-existent companion immediately after. Fixed by checking `companion_
path.exists()` after the call and recording an honest `"failed"` entry
(additive return key) instead of crashing — confirmed live: 2 real
attachments (`ADNOC Dress Code.pdf`, appearing twice under different
Threads) are genuinely non-extractable scanned PDFs; both honestly
recorded in `"failed"`, the run did not crash or abort.

**Real, live-vault verification against the FULL real 126-Thread corpus:**
- `[REQ-SB-72-US-01-AC-03]` `backfill_files()` run for real: **58 new
  companions created**, 61 already-companioned (from an earlier
  partial/crashed run before the fix was applied — see below), 2 honest
  failures, 26 Threads' own `## Files` sections written/updated. Directly
  confirmed one real new companion's own original attachment file is
  byte-identical to its real source under `Work/Threads/attachments/...`,
  and its companion note's own `## Summary` carries a real, genuine,
  content-grounded summary (not a placeholder) — e.g. a real NDLH/Data
  Lake House proposal PDF summarized accurately. PASS.
- `[REQ-SB-72-US-01-AC-04]` Re-ran `backfill_files()` twice more: second
  run (immediately after the first full real run) reported **0 newly
  companioned, 119 already_companioned, 2 failed (same 2, consistently
  honest re-failure, never silently "fixed" or retried into a fabricated
  success)** — confirmed idempotent. A third re-run's own sampled
  companion note was confirmed SHA-256 byte-identical before/after. PASS.
- `[REQ-SB-72-US-01-AC-05]` Confirmed the real `## Files` section on
  multiple real Threads — both an already-pre-companioned Thread (24
  entries) and multiple newly-backfilled ones (26 `threads_updated` this
  run, well beyond the 2 pre-existing) — each entry carries a real
  filename, real date, a condensed real summary blurb, and a real,
  resolvable `[[wikilink]]` to its own companion note (confirmed the
  target file exists at the resolved path). PASS.

**Two real, out-of-scope defects found and escalated during this live
verification (logged, not silently fixed, per this project's own
established `ESC-046`/`ESC-048`/`ESC-050` disclose-don't-fix precedent —
full detail in `ESCALATIONS.md`):**
- **`ESC-051`** — `vault_writer.write_attachments`'s own `_slugify(...,
  max_len=80)` truncation silently collapses near-identical, long real
  Outlook `message_id`s onto the SAME attachment directory (16 real
  collision groups confirmed) — causes redundant (not lossy) companioning;
  a latent same-filename-overwrite risk is disclosed but not observed to
  have fired. Root cause lives in already-`Done` `REQ-SB-71-US-02-T03`
  code, outside this task's own `## Files to Modify` — NOT fixed here.
- **`ESC-052`** — `email_classification.write_file_companion`'s own
  `file_slug` convention produces a companion DIRECTORY literally named
  `*.md` when the original attachment's own filename already ends in
  `.md` (a real case: an attachment named `project-scaffold.md`) — this
  crashed the real, freshly-restarted backend's own scheduled `vault_
  indexing.rebuild_index()` background task (`PermissionError`, confirmed
  live). Mitigated IN-SCOPE with a defensive, purely-additive `path.
  is_file()` guard on `list_all_note_paths()` (already inside this task's
  own `## Files to Modify`; zero behavior change for any well-formed
  note) — confirmed live: `vault_indexing.rebuild_index()` now completes
  cleanly (640 real entries, no crash) after this one-line fix. The ROOT
  CAUSE (`write_file_companion`'s own `file_slug` construction) is outside
  this task's `## Files to Modify` (`email_classification.py` is not
  listed) and the story's own Constraint requires reusing that function
  UNCHANGED — left disclosed, not fixed.

**Real, disclosed operational finding (mid-session, from the operator's
own live check, addressed):** the running backend at `:8000` was found to
be executing STALE in-memory code (pre-`T01`/`T02` fixes) despite the
on-disk source already being correct — a leftover `python -m uvicorn`
process without `--reload`, started before this session's own edits.
Killed cleanly (that process + an orphaned `--reload` sibling on `:8001`
+ its own orphaned multiprocessing child, none left running), and
restarted ONE fresh `uvicorn app.main:app --reload --port 8000` process —
confirmed healthy (`GET /system-health` -> `200`) before continuing. No
orphaned processes left running as a result of this cleanup.

`gate: flagged 2026-08-18` — two real out-of-scope escalations
(`ESC-051`/`ESC-052`) written this task, per Pipeline.md trigger 4/7; the
in-scope defensive fix is a minimal, zero-behavior-change guard, not a
scope deviation.
