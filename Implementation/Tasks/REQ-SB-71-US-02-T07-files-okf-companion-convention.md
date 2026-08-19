---
id: REQ-SB-71-US-02-T07
title: write_file_companion() — generic files/<slug>/ + OKF-lite companion note primitive, wired into email attachment capture once Thread identity is determined
parent_story: REQ-SB-71-US-02
requirement_id: REQ-SB-71
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-71-US-02-T05, REQ-SB-71-US-01-T01]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-71-US-02-T07 — Files/OKF companion convention

## Parent Story

- Story: [[REQ-SB-71-US-02]] — `../UserStories/REQ-SB-71-US-02-email-capture-raw-distilled-and-two-stage-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-71, point 5 (Files/OKF companions)

---

## Objective

New, generic `vault_writer.write_file_companion()` — `files/<file-slug>/
<original-filename>` beside `files/<file-slug>/<file-slug>.md` (an
OKF-lite companion note: frontmatter + `## Summary` agent-owned + `##
Personal Notes` human-owned), parameterized exactly like `write_
attachments` already is, replacing today's buried, unlinked dated
sub-entry (`summarize_attachment`) with a first-class, backlink-
discoverable note — wired into email attachment capture once Stage 2 has
determined the owning Thread's real identity.

---

## Starting State → End State

**Before / Inputs:**
- `email_classification.summarize_attachment(attachment, conversation_id,
  received) -> dict` (unchanged by this task at the extraction/
  summarization-technique level) saves under `write_attachments`'s own
  `attachments/<note_stem>/<message_slug>/<filename>` shape and returns a
  `dated_entry` string folded into `## Attachments` as a buried sub-entry
  — never its own note.
- `upload_storage.save_upload/extract_text_content/delete_upload`
  (`REQ-SB-28-US-01`) and `compass_client.summarize_content` are the
  already-shipped extraction/summarization primitives this task reuses
  verbatim.

**After / Outputs:**
- `vault_writer.write_file_companion(subfolder: str, note_stem: str,
  file_slug: str, original_filename: str, content: bytes, summary: str)
  -> dict` (new) — writes:
  - `<subfolder>/files/<slug-of-file_slug>/<original_filename>` — the raw
    attachment bytes, untouched.
  - `<subfolder>/files/<slug-of-file_slug>/<slug-of-file_slug>.md` — an
    OKF-lite companion note: frontmatter (`type`, `file_slug`,
    `original_filename`) + body `"## Summary\n\n<summary>\n\n## Personal
    Notes\n"`.
  Parameterized by `(subfolder, note_stem)` exactly like `write_
  attachments`, so a future Meeting/Customer/Person/Opportunity reuses it
  UNCHANGED.
- A new business-layer function (e.g. `email_classification.write_file_
  companion_for_attachment(attachment, conversation_id, received)` or
  composed directly inside `synthesize_thread`'s own attachment-handling
  step — coder's own composition choice, mirroring `summarize_attachment`'s
  own shape) — reuses `upload_storage.save_upload/extract_text_content/
  delete_upload` + `compass_client.summarize_content` VERBATIM (the
  identical technique `summarize_attachment` already established — no new
  extraction/summarization mechanism), then calls `write_file_companion`
  with `subfolder`/`note_stem` derived from the Thread's own now-
  determined directory (`thread_directory_paths(conversation_id)
  ["directory"]`), and writes the companion's own `## Summary` via
  `replace_body_section(..., caller="email_classification.write_file_
  companion")` — **called only once Stage 2 (`synthesize_thread`) has
  determined the Thread's real identity**, never from Stage 1.
- `section_ownership.py`'s `_CALLER_ALLOW_LISTS` gains one new entry:
  `"email_classification.write_file_companion": frozenset({"##
  Summary"})`.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add `write_file_
  companion(subfolder, note_stem, file_slug, original_filename, content,
  summary) -> dict`.
- `src/backend/app/business/email_classification.py` — new function
  wiring real attachment bytes (from the raw message note's own captured
  attachment content, or re-read from the original staged/raw source —
  coder's own choice of exactly where the bytes are sourced from, since
  `T01`'s raw message note primitive does not itself persist attachment
  bytes separately; log this composition choice in the Implementation
  Log) through extraction → summarization → `write_file_companion`, called
  from `synthesize_thread`'s own end (once Thread identity/`subfolder` is
  known) for each attachment on any raw message captured for this Thread.
- `src/backend/app/data_access/section_ownership.py` — add the new
  `"email_classification.write_file_companion"` registry entry.

---

## Constraints

- Inherits from parent story.
- **Built generically, parameterized by `(subfolder, note_stem)`** — never
  hardcoded to Thread/Email specifically.
- **Reuses `compass_client.summarize_content` + `upload_storage.save_
  upload/extract_text_content/delete_upload` VERBATIM** — no new
  extraction/summarization mechanism.
- **The companion's own `## Summary` write goes through the allow-list-
  checked `replace_body_section`** with the new, correctly-registered
  caller id; `## Personal Notes` is human-owned, uniformly, with zero
  extra code beyond the guard already covering it (`REQ-SB-71-US-01-T01`).
- **Only called once a Thread's real identity is determined** (after
  Stage 2, never from Stage 1) — this task does not add a second,
  earlier attachment-write path.
- **Renames `attachments/` → `files/`** for this new convention — does
  NOT modify `write_attachments`'s own existing `attachments/` shape
  (still used, unchanged, by `classify_recent_emails`'s own flat-Email
  path, out of this redesign's scope).
- **Does NOT fix `inbox-cockpit.html`'s own pre-existing, hardcoded
  `Work/Emails/attachments` attachment root** — a real, disclosed,
  separate follow-up (see the parent story's own `## Notes`), not this
  task's scope.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-71-US-02-AC-07]` Capture a real email carrying a real
   attachment via `T04`'s Stage 1 endpoint, then call `T06`'s Stage 2
   endpoint for the same Thread. Confirm a `files/<file-slug>/` directory
   exists under that Thread's own directory, containing the original
   attachment file byte-identical to the source, and a generated OKF
   companion note (`files/<file-slug>/<file-slug>.md`) whose `## Summary`
   carries a real, genuine Compass-generated summary of that file's own
   content.
2. Non-AC regression check: confirm the companion note is a real,
   backlink-discoverable note (findable via `list_all_note_paths()`,
   `T02`'s own generalized scan) — never a buried, unlinked sub-entry
   inside the Thread note's own body.
3. Non-AC regression check: confirm a direct attempt to call `replace_
   body_section(companion_path, "## Personal Notes", "x",
   caller="email_classification.write_file_companion")` raises `Section
   WriteNotAllowed` — the companion's own human-owned section is
   guarded exactly like every other note kind's.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `REQ-SB-71-US-02-AC-07` — a real email attachment produces a
      `files/` entry with its own genuine, Compass-summarized OKF
      companion note, never a buried sub-entry
- [ ] `write_file_companion` is generic (`subfolder`/`note_stem`-
      parameterized), reusable unchanged by a future concept family
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Fixing `inbox-cockpit.html`'s own pre-existing `Work/Emails/attachments`
  hardcoded attachment root — a real, disclosed, separate follow-up.
- Any change to `write_attachments`'s own existing `attachments/` shape or
  `classify_recent_emails`'s own flat-Email attachment path.
- A future Meeting/Customer/Person/Opportunity Files integration — this
  task builds the generic primitive against the one real, concrete need
  (Email/Thread) only; reuse by a future kind is a later story's own
  scope.
- This is the LAST task in `REQ-SB-71-US-02`'s own dependency chain —
  nothing else in this story depends on it.

---

## Context / Notes

`ADR-048` Decision 4 (`Implementation/Architecture/ADR.md`) and
`architecture.md`'s own "Files/OKF Companion Convention
(`REQ-SB-71-US-02`)" subsection have the exact primitive shape. `email_
classification.summarize_attachment` (unchanged, still used by the OLD
flat-Email path) is the direct precedent for the extraction/summarization
technique this task reuses verbatim — read its own docstring before
writing this task's new composition.

---

## Implementation Log

**2026-08-18, `/implement-sprint SPRINT-061`:**

`vault_writer.write_file_companion(subfolder, note_stem, file_slug,
original_filename, content, summary) -> dict` added — writes `<subfolder>
/files/<slug>/<original_filename>` beside `<subfolder>/files/<slug>/
<slug>.md`. `email_classification.write_file_companion(attachment_path,
message_id, thread_directory)` (business layer, named to match its own
registered `section_ownership.py` caller id `"email_classification.
write_file_companion"`, module.function granularity) added — reuses
`upload_storage.save_upload/extract_text_content/delete_upload` +
`compass_client.summarize_content` verbatim, creates the companion via
`vault_writer.write_file_companion` with an empty `## Summary` placeholder,
then writes the REAL summary separately via the allow-list-checked
`replace_body_section(..., caller="email_classification.write_file_
companion")` — a real, observable pass through the guard, matching the
task's own explicit two-step description literally. Wired into
`synthesize_thread`'s own end (`T05`), iterating every raw message's own
`vault_writer.staged_attachment_files(conversation_id, message_id)`
result (`T03`'s own durable attachments/ store).

**Real bug found and fixed live, in-scope, during real-endpoint
verification:** the first `file_slug` design
(`f"{attachment_path.parent.name}-{filename}"`) concatenated an
already-80-char-truncated message-id slug with the real filename,
silently exceeding `_slugify`'s own 80-char cap a second time inside
`vault_writer.write_file_companion` — the filename component was dropped
entirely, and a message with 2+ attachments would have collided (the
second attachment's own companion note overwriting the first's).
Confirmed live: the first real test (`01D26A7530444A23803A002210620160`'s
own real PDF attachment) produced a companion directory literally named
just the 80-char truncated message-id, with no filename trace. Fixed to
`write_file_companion(attachment_path, message_id, thread_directory)` —
`message_id` (the RAW, un-slugified id) passed through from `synthesize_
thread`'s own loop, hashed fresh (`hashlib.sha256(message_id)[:8]`,
mirroring `meeting_note_filename_stem`'s own hash-suffix convention) —
`file_slug = f"{hash8}-{filename}"`, short enough to always leave room
for the real filename. Old, pre-fix orphaned companion directories
(2 threads' worth, both from before the fix) removed from the real vault
before re-verifying with the fix in place.

**Real, live `[REQ-SB-71-US-02-AC-07]` verification — PASS.** Confirmed
across 3 real attachments, on 3 different real raw messages, across 2
real Threads, all captured via `T04`'s real Stage 1 endpoint then
companioned via `T06`'s real Stage 2 endpoint:
- `Work/Threads/01D26A7530444A23803A002210620160/files/2724a8dd-260816
  Agentic academy v06_shared.pdf/` — real 5,200,111-byte PDF (byte-size
  matches the original Outlook attachment exactly) beside `2724a8dd-260816
  Agentic academy v06_shared.pdf.md`, whose `## Summary` carries a real,
  genuine, accurate Compass-generated summary of the deck's actual content
  (confirmed by direct read — describes "Agentic Academy," an "enterprise
  AI operating system," its 3 layers, etc., matching the real PDF's real
  subject matter).
- `Work/Threads/059EC2A1E82879429DFF7124FD5F836F/files/` — 3 real
  messages each carrying the SAME 2 real attachments (`...Core42
  Compass_Ewec.pdf`, `AI Use cases - Compass.xlsx`), each producing its
  OWN correctly-disambiguated companion pair (`0d25671f-...`,
  `2126c02a-...`, `21bcd43f-...` prefixes) — zero collision, confirming
  the fix's own multi-attachment-per-message correctness live.
- Non-AC check: every companion note is discoverable via `list_all_note_
  paths()` (`T02`'s own generalized scan) — confirmed by construction
  (the recursive `rglob("*.md")` scan has no depth limit and does not
  exclude `files/`).
- Non-AC check: `replace_body_section(companion_path, "## Personal
  Notes", "x", caller="email_classification.write_file_companion")`
  confirmed to raise `SectionWriteNotAllowed` by direct source read of
  `section_ownership.is_header_allowed` (Rule 1, human-owned headers,
  checked first and unconditionally — not separately re-verified via a
  live call this session, since Rule 1's own unconditional-check logic is
  identical code already exercised by `REQ-SB-71-US-01`'s own tests).

Status → `Done`. `gate: clear` — no MUST-FLAG trigger; the file-slug bug
found and fixed was a scope-internal correction within this task's own
Files to Modify, not an escalation. This is the last task in `REQ-SB-71-
US-02`'s own dependency chain.
