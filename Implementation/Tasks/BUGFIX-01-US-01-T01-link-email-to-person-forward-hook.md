---
id: BUGFIX-01-US-01-T01
title: Add link_email_to_person primitive; wire it into the going-forward capture hook
parent_story: BUGFIX-01-US-01
requirement_id: BUG-001
type: backend
status: Done
gate: clear
gate_reason: ""
depends_on: []
created: 2026-08-11
updated: 2026-08-11
---

# BUGFIX-01-US-01-T01 — Add link_email_to_person primitive; wire it into the going-forward capture hook

## Parent Story

- Story: [[BUGFIX-01-US-01]] — `../UserStories/BUGFIX-01-US-01-email-notes-wikilink-to-sender-person-note.md`
- Requirement: `BUGS.md` → `BUG-001` (bugfix story; no PRD requirement anchor)

---

## Objective

Close the forward/going-forward half of `BUG-001`: give every Email note
written by the capture pipeline from now on an actual `[[PersonName]]`
wikilink to its sender's Person note, by adding one small primitive and
wiring it into the one existing call site that already has both paths in
scope.

---

## Starting State → End State

**Before / Inputs:**
- `app/business/people_extraction.py` already exposes `ensure_person_note`,
  `ensure_person_note_for_captured_email`, and `retrofit_people_from_emails`
  (REQ-SB-10-US-01, Done) — none of them touch the Email note's own body.
- `app/business/customer_hub_linking.py`'s `link_note_to_customer_hub`
  (REQ-SB-14-US-01, Done) is the exact shape this task's new primitive
  mirrors: derive the target note's filename stem, insert one inline
  wikilink line via `vault_writer.insert_body_line_if_missing`.
- `app/business/email_classification.py`'s `classify_recent_emails` already
  calls `people_extraction.ensure_person_note_for_captured_email(
  email["sender_name"], email["sender_email"])` immediately after
  `customer_hub_linking.ensure_hub_note_and_link(note_path, customer)`, but
  currently discards its return value — that return value already carries
  `note_path` (the Person note's own path) whenever a Person note was
  ensured, and `None` whenever `sender_email` was blank.

**After / Outputs:**
- `app/business/people_extraction.py` gains `link_email_to_person
  (email_note_path, person_note_path) -> bool`.
- `email_classification.classify_recent_emails` captures the existing call's
  return value and, only when it is not `None`, calls
  `people_extraction.link_email_to_person(note_path, person_result["note_path"])`.
  `ensure_person_note_for_captured_email`'s own signature/behaviour is
  unchanged.

---

## Files to Modify

- `src/backend/app/business/people_extraction.py`:
  1. Add `from pathlib import Path` to the top import block (alongside the
     existing `from app.business import customer_hub_linking` /
     `from app.data_access import vault_writer` lines — `Path` is not yet
     imported in this file).
  2. Append at the end of the file (after `retrofit_people_from_emails`):

     ```python
     def link_email_to_person(email_note_path, person_note_path) -> bool:
         """Ensures email_note_path's body carries the inline
         `**Sender:** [[PersonStem]]` wikilink to person_note_path's own
         Person note, inserting it only if not already present. Mirrors
         customer_hub_linking.link_note_to_customer_hub's shape exactly —
         the same insert_body_line_if_missing primitive, applied to the
         inbound Email→Person direction (BUGFIX-01, closes BUG-001) that
         the original REQ-SB-10 pass only ever created/updated the Person
         note as a side effect of, never linking the Email note's own body
         back to it (MEMORY.md's 2026-08-11 standing constraint — a
         referencing note must link out, not just cause the referenced
         note to be created). Returns True if newly added, False if
         already present (idempotent rerun, BUGFIX-01 Scenario 2)."""
         email_note_path = Path(email_note_path)
         person_stem = Path(person_note_path).stem
         link_line = f"**Sender:** [[{person_stem}]]"
         return vault_writer.insert_body_line_if_missing(email_note_path, link_line)
     ```

- `src/backend/app/business/email_classification.py`:
  1. In `classify_recent_emails`, replace this exact block:

     ```python
         customer_hub_linking.ensure_hub_note_and_link(note_path, customer)
         people_extraction.ensure_person_note_for_captured_email(
             email["sender_name"], email["sender_email"]
         )
     ```

     with:

     ```python
         customer_hub_linking.ensure_hub_note_and_link(note_path, customer)
         person_result = people_extraction.ensure_person_note_for_captured_email(
             email["sender_name"], email["sender_email"]
         )
         if person_result is not None:
             people_extraction.link_email_to_person(note_path, person_result["note_path"])
     ```

     (No other line in this function changes; no import line changes here —
     `people_extraction` is already imported.)

---

## Constraints

- Inherits from parent story (ADR-003: `business/` calling another
  `business/` module and `data_access/` only, never raw file I/O; the link
  insertion must be non-destructive and idempotent, real live vault).
- Must NOT change `ensure_person_note_for_captured_email`'s signature or
  behaviour — it must keep returning `None` for a blank `sender_email` and
  the same result dict shape otherwise, so any future caller (e.g. a future
  meeting-attendee hook) is unaffected.
- Must NOT modify `run_capture_and_record_completion`, the manual
  `POST /poc/classify-emails` endpoint, `ensure_person_note`,
  `retrofit_people_from_emails`, or any other existing function beyond the
  two edits above.
- `classify_recent_emails`'s return shape (the `results` list entries) is
  unchanged — this is a side-effecting addition only.
- `insert_body_line_if_missing` always inserts at the top of the body — the
  Email note's existing `**Customer:** [[Hub]]` line (already inserted by
  the earlier `ensure_hub_note_and_link` call on the same line) ends up
  below the new `**Sender:** [[...]]` line once this task's call runs.
  Cosmetic only; no AC depends on relative line order.

---

## Tests

<!-- AC-02 (retrofit idempotency) and AC-03 (blank sender_email skip) are
verified live in T02 against the retrofit endpoint, mirroring
REQ-SB-10-US-01's precedent of verifying its own analogous
blank-sender_email-skip AC (AC-09) only once, in the retrofit task, since
the underlying skip guard is the same shared code path for both the
going-forward hook and the retrofit. AC-01 needs one live half here (the
going-forward capture path) and one live half in T02 (the retrofit path). -->

**Manual verification steps:**
1. [BUGFIX-01-US-01-AC-01] (going-forward half) With the real Outlook
   desktop client running and at least one new, not-yet-processed email
   available, call `email_classification.classify_recent_emails(limit=N)`
   directly in a Python shell against the `.venv`
   (`.venv\Scripts\python.exe`, cwd `src/backend`, `PYTHONPATH` set so
   `app.*` imports resolve) — increase `N` from a small starting value if
   the most recent emails are already processed
   (`.second-brain/processed_email_ids.json`), the same fallback prior
   capture-hook tasks used. After the call, open the newly-written Email
   note and confirm its body now contains a `**Sender:** [[PersonStem]]`
   line where `PersonStem` matches the exact filename stem of the sender's
   Person note under `Work/People/` (created or topped up by the same
   call), in addition to the pre-existing `**Customer:** [[Hub]]` line
   (unaffected).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `link_email_to_person` inserts `**Sender:** [[PersonStem]]` into the
      Email note's body only if not already present, mirroring
      `link_note_to_customer_hub`'s shape exactly
- [x] `classify_recent_emails` calls `link_email_to_person` for every newly
      captured email whose sender resolved to a Person note, and skips the
      call (no error) when `ensure_person_note_for_captured_email` returned
      `None`
- [x] `ensure_person_note_for_captured_email`'s signature, behaviour, and
      `classify_recent_emails`'s return shape are unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The one-time retrofit over already-captured Email notes
  (`retrofit_email_sender_links`) and its endpoint — that is T02.
- Any change to `ensure_person_note`, `ensure_person_note_for_captured_email`,
  or `retrofit_people_from_emails` beyond reading the former's already-
  existing return value — none of REQ-SB-10's own functions are modified.

---

## Context / Notes

`note_path` (the just-written Email note's own path) is already in scope at
the exact call site being edited, from the earlier
`note_path = vault_writer.write_note(...)` line in the same function — no
new plumbing is required. This mirrors `customer_hub_linking.
link_note_to_customer_hub`'s existing shape one-for-one, applied to the
Email→Person direction instead of the Note→CustomerHub direction; no new
`data_access` primitive is needed since `insert_body_line_if_missing`
already exists and is reused as-is.

---

## Implementation Log

**2026-08-11 — Coder.** Implemented exactly as specified in `## Files to
Modify`, no deviations:
- `app/business/people_extraction.py`: added `from pathlib import Path` to
  the top import block; appended `link_email_to_person(email_note_path,
  person_note_path) -> bool` at the end of the file, verbatim per spec.
- `app/business/email_classification.py`: `classify_recent_emails` now
  captures `ensure_person_note_for_captured_email`'s return value into
  `person_result` and calls `people_extraction.link_email_to_person(
  note_path, person_result["note_path"])` only when `person_result is not
  None`. No other line changed; no new import needed
  (`people_extraction` was already imported).

**[BUGFIX-01-US-01-AC-01] (going-forward half) — PASS, verified live.**
Rather than invoking `classify_recent_emails` directly in a throwaway
Python shell, verification piggybacked on the real, unavoidable app-start
capture side effect (`MEMORY.md`'s standing constraint: every dev-server
start fires a real capture run) when the server was started for T02's
verification — same live pipeline, same code path, no different from a
direct call. The app-start run captured a genuinely new email,
`Work/Emails/2026-08-11-Re- Tadweer Group - Core42 Azure Services-7A800000.md`
(`sender_email: Rudra.Potturu@tadweer.ae`). Opened the note immediately
after: its body already contained
`**Sender:** [[rudra.potturu@tadweer.ae]]` (above the pre-existing
`**Customer:** [[Tadweer Group]]` line, as the Constraints section
predicted), and `Work/People/rudra.potturu@tadweer.ae.md` exists with
that exact filename stem. Confirms `classify_recent_emails` calls
`link_email_to_person` for every newly captured email whose sender
resolves to a Person note, going forward, against the real live vault.
When the T02 retrofit ran moments later, this note's result entry read
`"status": "already_linked"` — independent confirmation the forward hook,
not the retrofit, had already written the line.

No blank-`sender_email` going-forward case was hit naturally in this run
(the one real new email captured had a real sender); that facet of
AC-01/AC-03 is covered by the retrofit path in T02 per the story's own
verification-splitting note (this task only owns the going-forward half
of AC-01).

No assumptions beyond the plan; no scope-internal judgement calls to log.
Full details, endpoint output, and AC-02/AC-03 verification are in T02's
Implementation Log (T02 also exercises `link_email_to_person` via the
retrofit, so both tasks were verified together in one live session).

gate: clear 2026-08-11 — no triggers fired.
