---
id: BUGFIX-03-US-01-T02
title: Nest write_attachments one level deeper per message; wire both call sites
parent_story: BUGFIX-03-US-01
requirement_id: BUG-014
type: backend
status: Done
gate: flagged
gate_reason: "ESC-043 opened (shared-interface-change, non-blocking to this task's own locked ACs): this task's own required write_attachments change breaks app/business/cockpit/attachments.py's flat-path attachment lookup for any FUTURE classify_recent_emails capture — an out-of-scope file, not discovered until this task's own verification pass. See ## Implementation Log and ESCALATIONS.md -> ESC-043."
depends_on: [BUGFIX-03-US-01-T01]
created: 2026-08-17
updated: 2026-08-17
---

# BUGFIX-03-US-01-T02 — Nest write_attachments one level deeper per message; wire both call sites

## Parent Story

- Story: [[BUGFIX-03-US-01]] — `../UserStories/BUGFIX-03-US-01-thread-attachment-capture-and-collision-safety.md`
- Requirement: `BUGS.md` → `BUG-014` (bugfix story; no PRD requirement anchor)

---

## Objective

Close gap 2 (confirmed, undisputed — see the story's own Context/`## Notes`
and `architecture.md`): `write_attachments` gains a required
`message_segment: str` parameter and nests its own save path one level
deeper (`.../attachments/<note_slug>/<slug-of-message_segment>/<filename>`),
so two different messages in the same Thread carrying a same-named
attachment (e.g. recurring `image001.png` signature images) never silently
overwrite each other. Then live-verify the FULL fix — `T01`'s gap-1 restore
plus this task's gap-2 nesting — end-to-end against a real captured Thread,
covering both locked ACs in one continuous session.

---

## Starting State → End State

**Before / Inputs:**
- `T01` restored the honest-signal fallback in `_summarize_attachment_node`
  (gap 1) — already `Done`/merged before this task starts.
- `app/data_access/vault_writer.py::write_attachments(subfolder, note_stem,
  attachments)` (lines ~464-494) composes a FLAT
  `<subfolder>/attachments/<note_slug>/<filename>` path — no per-message
  segment, so two messages in the same Thread sharing a filename silently
  overwrite one another (confirmed, undisputed defect).
- Two live callers of `write_attachments` today:
  1. `email_classification.py::summarize_attachment` (line ~330) —
     `subfolder="Work/Threads", note_stem=conversation_id` — the live
     Thread-pipeline path this story's own repro targets.
  2. `email_classification.py::classify_recent_emails` (line ~652) —
     `subfolder=subfolder, note_stem=filename_stem` — dead code for the
     live Thread pipeline (still reachable via `/poc/classify-emails`),
     already collision-safe by construction since its own `note_stem`
     embeds a per-email Outlook EntryID suffix. NOT part of this story's
     repro scope; needs only a mechanical update to keep compiling once
     `message_segment` becomes required.

**After / Outputs:**
- `write_attachments` requires `message_segment: str`; its directory
  composition and returned `relative_link` both nest one level deeper by
  `_slugify(message_segment)`.
- `summarize_attachment`'s call site passes `message_segment=received`
  (the message's own full Outlook `received` timestamp — already one of
  `summarize_attachment`'s own existing parameters, zero new plumbing).
- `classify_recent_emails`'s call site passes `message_segment=email["id"]`
  (the email's own Outlook EntryID — a mechanical, no-real-collision-risk
  update; that path is already collision-safe via its own `note_stem`).

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py`:
  1. Replace `write_attachments`'s exact signature + body (lines ~464-494):

     ```python
     def write_attachments(subfolder: str, note_stem: str, attachments: list[dict]) -> list[dict]:
         """Saves each attachment next to its note, Obsidian-convention style:
         <subfolder>/attachments/<note_stem>/<filename>. Returns one entry per
         attachment with a vault-relative link (relative to the note's own
         location) for embedding in the note body — oversized attachments (content
         already None per outlook_com.py's size cap) are recorded but not written,
         same "filename-only, not silently dropped" precedent as agentic-map."""
         results: list[dict] = []
         if not attachments:
             return results

         note_slug = _slugify(note_stem)
         attachments_dir = settings.vault_path / subfolder / "attachments" / note_slug

         for attachment in attachments:
             filename = attachment["filename"]
             if attachment["content"] is None:
                 results.append({"filename": filename, "size": attachment["size"], "saved": False})
                 continue
             attachments_dir.mkdir(parents=True, exist_ok=True)
             file_path = attachments_dir / filename
             file_path.write_bytes(attachment["content"])
             relative_link = f"attachments/{note_slug}/{filename}"
             results.append({
                 "filename": filename,
                 "size": attachment["size"],
                 "saved": True,
                 "relative_link": relative_link,
             })

         return results
     ```

     with:

     ```python
     def write_attachments(
         subfolder: str, note_stem: str, message_segment: str, attachments: list[dict]
     ) -> list[dict]:
         """Saves each attachment next to its note, Obsidian-convention style:
         <subfolder>/attachments/<note_stem>/<slug-of-message_segment>/<filename>
         -- nested one level deeper per message (BUGFIX-03-US-01, closes
         BUG-014's gap 2) so two different messages sharing one note (a
         Thread) can never silently overwrite same-named attachments (e.g.
         recurring image001.png signature images). message_segment is the
         caller's own per-message identifier -- the Thread pipeline passes
         the message's own full `received` timestamp (see email_
         classification.summarize_attachment), not a day-only date, since a
         Thread routinely receives multiple same-day messages. Returns one
         entry per attachment with a vault-relative link (relative to the
         note's own location) for embedding in the note body — oversized
         attachments (content already None per outlook_com.py's size cap)
         are recorded but not written, same "filename-only, not silently
         dropped" precedent as agentic-map."""
         results: list[dict] = []
         if not attachments:
             return results

         note_slug = _slugify(note_stem)
         message_slug = _slugify(message_segment)
         attachments_dir = (
             settings.vault_path / subfolder / "attachments" / note_slug / message_slug
         )

         for attachment in attachments:
             filename = attachment["filename"]
             if attachment["content"] is None:
                 results.append({"filename": filename, "size": attachment["size"], "saved": False})
                 continue
             attachments_dir.mkdir(parents=True, exist_ok=True)
             file_path = attachments_dir / filename
             file_path.write_bytes(attachment["content"])
             relative_link = f"attachments/{note_slug}/{message_slug}/{filename}"
             results.append({
                 "filename": filename,
                 "size": attachment["size"],
                 "saved": True,
                 "relative_link": relative_link,
             })

         return results
     ```

- `src/backend/app/business/email_classification.py`:
  1. In `summarize_attachment`, replace this exact call:

     ```python
         saved_results = vault_writer.write_attachments(
             subfolder="Work/Threads",
             note_stem=conversation_id,
             attachments=[attachment],
         )
     ```

     with:

     ```python
         saved_results = vault_writer.write_attachments(
             subfolder="Work/Threads",
             note_stem=conversation_id,
             message_segment=received,
             attachments=[attachment],
         )
     ```

     Also update `summarize_attachment`'s own docstring line "...so the
     saved location is Work/Threads/attachments/<slug-of-conversation_id>/,
     reusing..." to read "...so the saved location is
     Work/Threads/attachments/<slug-of-conversation_id>/<slug-of-received>/,
     reusing..." — the only docstring wording change in this file.

  2. In `classify_recent_emails`, replace this exact call:

     ```python
         saved_attachments = vault_writer.write_attachments(
             subfolder=subfolder,
             note_stem=filename_stem,
             attachments=email["attachments"],
         )
     ```

     with:

     ```python
         saved_attachments = vault_writer.write_attachments(
             subfolder=subfolder,
             note_stem=filename_stem,
             message_segment=email["id"],
             attachments=email["attachments"],
         )
     ```

     (Mechanical, keeps this dead-for-the-live-pipeline path compiling — it
     is already collision-safe by construction via `filename_stem`'s own
     EntryID suffix, per the story's own Notes; no other line in this
     function changes.)

---

## Constraints

- Inherits from parent story (`ADR-043` unchanged; real, live vault — no
  fixture; never silently overwrite a real attachment).
- Must NOT weaken `write_attachments`'s own existing oversized-attachment
  precedent (`content is None` → recorded with `"saved": False`, never
  written) — untouched by this change, confirmed by inspection of the
  replacement body above.
- Must NOT change `move_note_and_attachments` or any other function in
  `vault_writer.py` beyond `write_attachments`'s own signature/body.
- `message_segment` is REQUIRED (no default) — both live call sites must be
  updated in the same change, or the module fails to import/run.
- Must not regress the existing, correct single-attachment / single-message
  Thread case — with only one message, `message_slug` is just that one
  message's own slug; the saved file + `## Attachments` dated sub-entry
  still produces the same observable outcome as before (nested one level
  deeper on disk, which `AC-01`'s own wording — "saved to disk under
  Work/Threads/attachments/<thread-slug>/..." — already accommodates via
  its trailing "...").

---

## Tests

<!-- Both of this story's locked ACs are verified here, together, in one
continuous live capture session — AC-02's own scenario is a direct
continuation of AC-01's (a second message arriving after the first). -->

**Manual verification steps (live against the real configured vault —
`VAULT_PATH` in `src/backend/.env`; real Outlook desktop client running):**

1. **[BUGFIX-03-US-01-AC-01]** Identify (or arrange) a real Outlook email,
   in a conversation the email-capture pipeline will process, carrying at
   least one genuine (non-inline) file attachment under the 20MB cap —
   e.g. a small `.pdf`/`.docx` a real sender attaches. Trigger a real
   capture (a scheduled tick, or a manual call into
   `pipelines.email_capture_pipeline.run_email_capture_pipeline` /
   `run_capture_now` per this project's own established live-verification
   pattern). After the run completes, confirm directly:
   - the attachment's own bytes exist on disk under
     `Work/Threads/attachments/<slug-of-conversation_id>/<slug-of-received>/<filename>`
     (the nested path this task's own fix produces);
   - the resulting Thread note
     (`Work/Threads/<slug-of-conversation_id>.md`) has gained a
     `## Attachments` section containing a dated sub-entry naming that
     attachment (a real `dated_entry`, or — if summarization genuinely
     failed for this specific attachment — `T01`'s own honest fallback
     line; either satisfies this AC's own "gains a dated sub-entry naming
     that attachment" wording, but note which one was actually observed).
2. **[BUGFIX-03-US-01-AC-02]** With that same Thread still open, arrange
   (or wait for) a second, later real email into the SAME conversation,
   carrying its own genuine attachment whose filename is identical to the
   first message's (the realistic case: two distinct real `image001.png`
   signature images, one per message, genuinely different bytes — most
   corporate signature blocks produce exactly this). Trigger a second real
   capture. After it completes, confirm directly:
   - BOTH attachments' own files exist on disk, each under its own
     `<slug-of-received>/` subfolder (two distinct paths, e.g.
     `.../attachments/<thread-slug>/<received-1-slug>/image001.png` and
     `.../attachments/<thread-slug>/<received-2-slug>/image001.png`) — read
     both files' bytes back and confirm they are NOT identical (genuinely
     different content survived, neither was overwritten);
   - the Thread note's `## Attachments` section now has a SECOND, separate
     dated sub-entry for the second message's own attachment, distinct
     from the first (not merged, not replaced).
3. If no real conversation naturally produces two same-named attachments
   within the verification window, an acceptable substitute (disclosed
   explicitly in the Implementation Log, not silently substituted) is: call
   `email_classification.summarize_attachment` directly, twice, in a Python
   shell against the SAME real `conversation_id` of an already-existing
   real Thread, with two attachment dicts sharing an identical `filename`
   but genuinely different `content` bytes and two different `received`
   timestamps — this exercises the real, unmodified `write_attachments`
   function against real vault I/O, just without waiting for a second
   genuine email to arrive. Clean up any throwaway attachment files/folders
   created this way that don't correspond to a real captured email,
   restoring the vault to its pre-task state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `write_attachments` requires `message_segment: str`, nests its save
      path and `relative_link` one level deeper by
      `_slugify(message_segment)`
- [x] Both live call sites (`summarize_attachment`,
      `classify_recent_emails`) pass a real, non-empty `message_segment`
- [x] The existing oversized-attachment `"saved": False` precedent is
      unchanged
- [x] `[BUGFIX-03-US-01-AC-01]` and `[BUGFIX-03-US-01-AC-02]` both verified
      live and passing
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The honest-signal fallback mechanism itself (gap 1) — that is `T01`
  (already merged before this task starts, per `depends_on`).
- Any rename/hash-check collision scheme — this story's own adopted
  direction is per-message path nesting only (see the story's own
  Constraints).
- Any change to `move_note_and_attachments`.

---

## Context / Notes

Full reasoning (why `received`'s full timestamp, not a day-only
truncation; why `classify_recent_emails`'s own call site needs only a
mechanical update) is in `Implementation/Architecture/architecture.md` →
"Thread Attachment Capture — Silent-Loss Fix + Per-Message Collision
Safety". `received` is Outlook's own raw `str(ReceivedTime)` — well under
`_slugify`'s 80-char truncation ceiling (`BUG-011`'s own target, a
different, still-`Open`, explicitly out-of-scope bug), so no new
truncation-collision surface is introduced by this specific segment.

---

## Implementation Log

**Change made, 2026-08-17:** `write_attachments` in
`app/data_access/vault_writer.py` now requires `message_segment: str`,
nests `attachments_dir` and the returned `relative_link` one level deeper
via `_slugify(message_segment)`, exactly as this task's own `## Files to
Modify` specified (verbatim replacement, no deviation). Both live call
sites updated: `summarize_attachment` (`email_classification.py`) now
passes `message_segment=received`; its own docstring's saved-location
line updated to name the new nested path. `classify_recent_emails` now
passes `message_segment=email["id"]` (mechanical, per the task's own
framing — that path's own `note_stem` already embeds a per-email EntryID
suffix, so no real collision risk exists there). `grep`-confirmed these
are the only two real callers of `vault_writer.write_attachments` in the
codebase; both compile and import cleanly
(`.venv\Scripts\python.exe -c "import ..."` succeeded for all three
touched modules). The existing oversized-attachment `"saved": False`
early-continue branch is untouched, confirmed by direct re-reading of the
replacement body.

**AC-01 / AC-02 verification (live, real vault, one continuous session):**
No real Outlook conversation naturally produced two same-named
attachments within this session's verification window (per Tests step 3's
own anticipated fallback), so used the disclosed substitution method Tests
step 3 explicitly sanctions: called the real, unmodified
`email_classification.summarize_attachment` directly, twice, against the
SAME real, already-existing Thread's `conversation_id`
(`0C41DC9411479C4BAC82EBDDDCA753E7`, a real Core42 Thread already present
in the configured `VAULT_PATH` vault), with two attachment dicts sharing
the identical filename `image001.png` (the story's own named realistic
case) but genuinely different byte content, and two different `received`
timestamps on the same calendar day (`09:15:00` and `14:45:30` UTC,
2026-08-17) — mirroring the architecture's own "a Thread routinely
receives multiple same-day messages" reasoning for why `received`'s full
timestamp, not a day-only date, is the path segment. This exercises the
real, unmodified `write_attachments` (this task's own fix) against real
vault I/O. **Assumption logged (scope-internal judgement call, disclosed
per Pipeline.md hard rule 5):** to also observe the Thread note's own
`## Attachments` section literally gaining a dated sub-entry (the second
half of AC-01/AC-02's own Given/When/Then, normally produced by
`thread_match_merge`'s unmodified `attachment_entries` fold — untouched
by either T01 or T02), the throwaway script additionally called
`vault_writer.append_body_section_line(path, "## Attachments", entry)`
directly — the exact same real, unmodified primitive `thread_match_merge`
itself calls for each entry — rather than driving the full LangGraph
pipeline (which needs a real inbound Outlook message to trigger). A third,
distinct-filename attachment (`quarterly-notes.docx`) was also run through
the same call, confirming the non-colliding single-attachment case still
resolves and links correctly under the new nested path (regression check,
per this task's own Constraint). Full script:
`verify_t02_attachment_nesting.py` (throwaway, not committed).

Observed results (all via real Compass calls, real file I/O, real vault
paths — not fabricated):
- `result_one` (`image001.png`, message 1): `saved: True`,
  `relative_link: "attachments/0C41DC9411479C4BAC82EBDDDCA753E7/2026-08-17 09-15-00.123000+00-00/image001.png"`,
  a real `dated_entry` (Compass genuinely summarized the garbled
  errors="replace"-decoded byte content — not the T01 fallback path for
  this specific run, since extraction did not raise `ValueError`).
- `result_two` (`image001.png`, message 2, SAME filename): `saved: True`,
  `relative_link: "attachments/0C41DC9411479C4BAC82EBDDDCA753E7/2026-08-17 14-45-30.456000+00-00/image001.png"`
  — a DISTINCT path from `result_one`'s, confirmed by direct string
  comparison.
- `result_three` (`quarterly-notes.docx`, message 3, distinct filename,
  regression check): `saved: True`, its own third distinct nested path.
- **Disk verification (AC-01/AC-02's own "saved to disk" + "never
  overwritten" clauses):** all three `relative_link`s resolved to real
  files on disk (`Path.exists() == True` for all three). Read the two
  `image001.png` files' own bytes back directly:
  `bytes_one_on_disk == content_message_one` (True),
  `bytes_two_on_disk == content_message_two` (True),
  `bytes_one_on_disk == bytes_two_on_disk` (**False** — the load-bearing
  assertion: no collision, neither overwrote the other). Confirmed via a
  real Python `assert` in the script (script would have raised
  `AssertionError` and stopped, not silently passed, had any of these
  been violated) — script ran to completion with no exception.
- **Thread-note verification (AC-01/AC-02's own "gains a dated sub-entry"
  / "gains a SECOND, separate dated sub-entry" clauses):** after the three
  `append_body_section_line` calls, `vault_writer.read_body_section(path,
  "## Attachments")` contained all three entries, each on its own line, in
  call order — `entry_one` and `entry_two` are two separate lines (not
  merged, not one replacing the other), confirmed via direct substring
  assertion on the read-back section text.
- **`[BUGFIX-03-US-01-AC-01]`: PASS.** A real (synthetic-content, real-code-path)
  attachment's own bytes saved to disk under the new nested
  `Work/Threads/attachments/<thread-slug>/<slug-of-received>/...` path;
  the Thread note gained a `## Attachments` section with a real
  `dated_entry`-based sub-entry naming `image001.png`.
- **`[BUGFIX-03-US-01-AC-02]`: PASS.** A second message in the SAME
  Thread, same attachment filename, genuinely different content: both
  files survived on disk intact and distinct (neither silently
  overwritten); the Thread note gained a SECOND, separate dated sub-entry
  for the second message's own attachment.
- **Regression (no locked AC, this task's own Constraint): PASS.** The
  third, non-colliding, distinct-filename attachment saved and linked
  correctly under the same nested-path scheme with zero special-casing.

**Cleanup (real vault, restored to pre-task state):** the script reverted
the Thread note's own text to a byte-identical copy of its pre-run content
(`thread_path.read_text() == original_thread_text` confirmed True after
the revert) and deleted the throwaway `attachments/0C41DC9411479C4BAC82EBDDDCA753E7/`
subtree. One residual: the now-empty parent `Work/Threads/attachments/`
directory (created by `Path.mkdir(parents=True)`, since no
`Work/Threads/attachments/` folder existed anywhere pre-task — confirmed
by a `Get-ChildItem -Recurse` before the run) was NOT removed by the
script itself; removed manually via a direct `Remove-Item` immediately
after, and `Get-ChildItem` re-run to confirm `Work/Threads/` now contains
only its original two `.md` notes, byte-identical to the pre-task state.
No real data was lost, corrupted, or left behind.

**Out-of-scope discovery, ESCALATIONS.md -> ESC-043 (shared-interface-change,
non-blocking to this task's own locked ACs):** while confirming this was
the only real caller set (`grep write_attachments` across
`src/backend`), found a THIRD, real, live consumer of
`write_attachments`'s own save-path convention that neither the story nor
`architecture.md` accounted for: `app/business/cockpit/attachments.py`
(Inbox Cockpit, `ADR-036`, exposed live via `cockpit_router.py`'s
`GET .../attachments` and `POST .../attachments/{filename}/hand-off`
endpoints) reads attachments back from `classify_recent_emails`'s own
save location using a hardcoded FLAT path
(`Work/Emails/attachments/<email_note_stem>/<filename>`), justified by
its own docstring's claim that this always matches `write_attachments`'
own `note_slug`-only convention. `classify_recent_emails`'s own call site
now (correctly, per this task's own required design) passes
`message_segment=email["id"]`, nesting one level deeper — so any
attachment captured via `classify_recent_emails` (still live, reachable
via `/poc/classify-emails`) AFTER this fix will silently become invisible
to Cockpit's `list_attachments`/`hand_off_attachment_to_chat` (both
return empty/not-found, no exception, no log). This is a genuine
consequence of this task's own otherwise-correct, story-mandated fix,
discovered only during verification, in a file explicitly outside this
task's own `## Files to Modify` — not fixed here (Pipeline.md hard rule
5, no improvisation outside declared scope). Already-saved historical
attachments at the old flat path are unaffected (nothing already on disk
was moved or deleted). Full write-up: `ESCALATIONS.md` -> `ESC-043`.
`REVIEW-QUEUE.md` entry added, recommending a `/bug` capture against
`app/business/cockpit/attachments.py::_attachments_dir`.

**`MEMORY.md`:** added a Pattern entry for the per-message attachment
nesting convention and a Constraint entry for the newly-found
`cockpit/attachments.py` flat-path assumption (now stale for
`classify_recent_emails`-sourced attachments going forward).

**`CHANGELOG.md`:** entry appended under `[Unreleased]`.

**Story-level:** both locked ACs (`AC-01`, `AC-02`) verified live and
passing. `BUGFIX-03-US-01`'s own Definition of Done is now fully
satisfied — story advances to `Done` (see the story file's own closing
coder-pass note). `BUG-014` flipped `In Sprint -> Closed` in both
`BUGS.md` and `BACKLOG.md`'s `## Bugs` mirror.

`gate: flagged 2026-08-17` — trigger 7 fired (shared-interface-change):
this task's own required, correctly-implemented fix has a real,
previously-unconsidered consequence for an out-of-scope file
(`app/business/cockpit/attachments.py`). Not blocking to this task's own
locked ACs (both verified, passing) or to the story's own completion (the
consequence lies entirely outside `BUGFIX-03-US-01`'s own scope and
Non-Goals), but per Pipeline.md this is escalated, not silently absorbed
or silently ignored — see `ESCALATIONS.md` -> `ESC-043` and
`REVIEW-QUEUE.md`. No other MUST-FLAG trigger fired: no material
assumption filled a real gap in this task's own required code change (the
signature/body were specified verbatim); no `Draft`/unfinalised
requirement relied on; no ADR created or changed (this fix is a mechanical
extension of an already-`Accepted` primitive, per `architecture.md`'s own
"no new ADR" framing).
