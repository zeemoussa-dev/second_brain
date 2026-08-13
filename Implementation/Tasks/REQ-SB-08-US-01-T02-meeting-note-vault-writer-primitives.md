---
id: REQ-SB-08-US-01-T02
title: Add meeting-note file-I/O primitives (incl. the growable Attendees-line upsert) to vault_writer.py
parent_story: REQ-SB-08-US-01
requirement_id: REQ-SB-08
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-08-US-01-T02 — Add meeting-note file-I/O primitives (incl. the growable Attendees-line upsert) to vault_writer.py

## Parent Story

- Story: [[REQ-SB-08-US-01]] — `../UserStories/REQ-SB-08-US-01-meeting-notes-from-calendar-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-08 *Meetings Capture Pipeline*

---

## Objective

Add the low-level file-I/O primitives T03 (`meeting_classification.py`) will
orchestrate on top of: resolving a Meeting note's EntryID-suffixed path,
building its baseline frontmatter, creating/topping-up that baseline, the
occurrence-dedup state file (`processed_meeting_ids.json`, mirroring
`processed_email_ids.json`'s shape per ADR-008), and a genuinely new
primitive — a per-attendee-wikilink **upsert** for the growable
`**Attendees:** [[P1]], [[P2]], ...]` body line, distinct from the
single-target `insert_body_line_if_missing` reused as-is for the
`**Customer:** [[Hub]]` line.

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.py` already has `write_note`, `read_note`, `tag_slug`,
  `build_tags`, `insert_frontmatter_key_if_missing`,
  `insert_body_line_if_missing` (the REQ-SB-14/REQ-SB-10 primitives this
  task mirrors for Meetings), and `load_processed_email_ids`/
  `mark_email_processed` (the dedup-state-file precedent this task mirrors).

**After / Outputs:**
- New items appended to `vault_writer.py`: `_MEETINGS_SUBFOLDER`,
  `_MEETING_NOTE_BASELINE_KEYS`, `meeting_note_filename_stem`,
  `meeting_note_path`, `meeting_note_exists`, `build_meeting_tags`,
  `create_meeting_note_baseline`, `ensure_meeting_note_baseline_frontmatter`,
  `_PROCESSED_MEETINGS_FILE`, `load_processed_meeting_ids`,
  `mark_meeting_processed`, `upsert_attendee_links`. No existing function's
  behavior changed.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py`:

  Append at the end of the file (after `ensure_person_note_baseline_frontmatter`,
  REQ-SB-10's last function):

  ```python
  _MEETINGS_SUBFOLDER = f"{_WORK_ROOT}/Meetings"
  _MEETING_NOTE_BASELINE_KEYS = (
      "type", "customer", "subject", "start", "end", "location", "organizer", "tags",
  )
  _PROCESSED_MEETINGS_FILE = "processed_meeting_ids.json"

  _ATTENDEES_LINE_PATTERN = re.compile(r"^\*\*Attendees:\*\* (.+)$", re.MULTILINE)
  _ATTENDEES_LINE_PREFIX = "**Attendees:** "
  _WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")


  def meeting_note_filename_stem(subject: str, start: str, entry_id: str) -> str:
      """<subject>-<date>-<entry-id-suffix> — the same EntryID-suffix
      disambiguation email filenames already use (MEMORY.md): two meetings
      can share a subject and date, and the 8-char EntryID slice is what
      keeps their notes from colliding (Scenario 7). `start` is the ISO
      datetime string list_calendar_events returns; only its first 10
      characters (the date) are used."""
      date = start[:10]
      return f"{subject}-{date}-{entry_id[-8:]}"


  def meeting_note_path(subject: str, start: str, entry_id: str):
      """Resolves the vault-absolute path a Meeting note lives (or would
      live) at — Work/Meetings/<subject>-<date>-<entry-id-suffix>.md —
      without checking whether it exists yet. Uses the same _slugify()
      write_note() applies to its own filename_stem, so this always
      points at exactly the file create_meeting_note_baseline()/
      write_note() would create."""
      stem = meeting_note_filename_stem(subject, start, entry_id)
      return settings.vault_path / _MEETINGS_SUBFOLDER / f"{_slugify(stem)}.md"


  def meeting_note_exists(subject: str, start: str, entry_id: str) -> bool:
      return meeting_note_path(subject, start, entry_id).exists()


  def build_meeting_tags(customer: str | None) -> list[str]:
      """Mirrors build_person_tags's shape for Meetings. Returns
      ["kind/meeting"] alone when no customer was derived (Scenario 3, 8),
      or ["customer/<slug>", "kind/meeting"] when one was (Scenario 1)."""
      if not customer:
          return ["kind/meeting"]
      return [f"customer/{tag_slug(customer)}", "kind/meeting"]


  def create_meeting_note_baseline(
      subject: str,
      customer: str | None,
      start: str,
      end: str,
      location: str,
      organizer: str,
      entry_id: str,
  ) -> str:
      """Creates a Meeting note for the first time: baseline frontmatter
      (type/customer/subject/start/end/location/organizer/tags) with an
      empty body — the REQ-SB-14/REQ-SB-10 baseline pattern applied to
      Meetings. The **Customer:**/**Attendees:** body lines are never
      written here — they are inserted separately by the orchestration
      layer (T03), the same way link_note_to_customer_hub layers on top of
      ensure_customer_hub_note. Always writes unconditionally, mirroring
      write_note()'s own contract — callers must check meeting_note_exists()
      first (T03 does)."""
      return write_note(
          subfolder=_MEETINGS_SUBFOLDER,
          filename_stem=meeting_note_filename_stem(subject, start, entry_id),
          frontmatter={
              "type": "Meeting",
              "customer": customer or "",
              "subject": subject,
              "start": start,
              "end": end,
              "location": location,
              "organizer": organizer,
              "tags": build_meeting_tags(customer),
          },
          body="",
      )


  def ensure_meeting_note_baseline_frontmatter(
      path,
      subject: str,
      customer: str | None,
      start: str,
      end: str,
      location: str,
      organizer: str,
  ) -> list[str]:
      """Tops up an already-existing Meeting note with any of the eight
      baseline frontmatter keys it is missing, inserting each surgically
      via insert_frontmatter_key_if_missing — never touches a key already
      present, and never touches the body. Returns the list of keys
      actually inserted (empty if the note already had all eight) —
      Scenario 2/6's baseline-preservation mechanism, the same contract
      ensure_person_note_baseline_frontmatter/ensure_hub_note_baseline_
      frontmatter already established."""
      baseline_values = {
          "type": "Meeting",
          "customer": customer or "",
          "subject": subject,
          "start": start,
          "end": end,
          "location": location,
          "organizer": organizer,
          "tags": build_meeting_tags(customer),
      }
      inserted: list[str] = []
      for key in _MEETING_NOTE_BASELINE_KEYS:
          if insert_frontmatter_key_if_missing(path, key, baseline_values[key]):
              inserted.append(key)
      return inserted


  def _processed_meetings_path():
      state_dir = settings.vault_path / _STATE_DIR
      state_dir.mkdir(parents=True, exist_ok=True)
      return state_dir / _PROCESSED_MEETINGS_FILE


  def load_processed_meeting_ids() -> set[str]:
      path = _processed_meetings_path()
      if not path.exists():
          return set()
      return set(json.loads(path.read_text(encoding="utf-8")))


  def mark_meeting_processed(entry_id: str) -> None:
      """Mirrors mark_email_processed's exact shape (ADR-008) — a flat,
      idempotent set-of-EntryIDs audit record. Adding an already-present
      ID is a no-op. Note: meeting_classification.py (T03) does not gate
      reprocessing on this file the way email capture gates on
      processed_email_ids — see T03's own Context/Notes for why (Scenario
      2/6 require an in-window event to still flow through the top-up path
      on every rerun). This file still records every EntryID this pipeline
      has ever seen, for future observability (REQ-SB-11)."""
      path = _processed_meetings_path()
      processed = load_processed_meeting_ids()
      processed.add(entry_id)
      path.write_text(json.dumps(sorted(processed), indent=2), encoding="utf-8")


  def upsert_attendee_links(path, person_stems: list[str]) -> bool:
      """Upserts the growable **Attendees:** [[P1]], [[P2]], ...] body
      line — unlike the single-target insert_body_line_if_missing (a link
      is either present or not), this line can legitimately grow across
      reruns as new attendees are confirmed (Scenario 6). If no Attendees
      line exists yet, inserts one as the first line of the body
      (mirroring insert_body_line_if_missing's insert-at-body-start
      contract). If one already exists, merges in any person_stems not
      already linked — preserving existing wikilink order, appending new
      ones, updating the line in place rather than moving it — never
      removes an existing wikilink. Returns True if the line was created
      or grew, False if every stem in person_stems was already present (a
      true no-op rerun) or if person_stems is empty (Scenario 8 — no
      attendees, no Attendees line at all)."""
      if not person_stems:
          return False
      text = path.read_text(encoding="utf-8")
      match = _ATTENDEES_LINE_PATTERN.search(text)
      if match is None:
          new_line = _ATTENDEES_LINE_PREFIX + ", ".join(f"[[{stem}]]" for stem in person_stems)
          end = text.find("\n---\n", 4)
          if end == -1:
              path.write_text(new_line + "\n\n" + text, encoding="utf-8")
              return True
          body_start = end + 6
          new_text = text[:body_start] + new_line + "\n\n" + text[body_start:]
          path.write_text(new_text, encoding="utf-8")
          return True

      existing_stems = _WIKILINK_PATTERN.findall(match.group(1))
      merged_stems = list(existing_stems)
      changed = False
      for stem in person_stems:
          if stem not in merged_stems:
              merged_stems.append(stem)
              changed = True
      if not changed:
          return False
      new_line = _ATTENDEES_LINE_PREFIX + ", ".join(f"[[{stem}]]" for stem in merged_stems)
      new_text = text[: match.start()] + new_line + text[match.end() :]
      path.write_text(new_text, encoding="utf-8")
      return True
  ```

---

## Constraints

- Inherits from parent story (ADR-003 layering; Meetings never nested under
  a `Customer` folder — a direct extension of ADR-004's folder-vs-tag
  reasoning; idempotency is load-bearing since this runs against the real
  live vault).
- This file lives in `data_access/` only — no business rules (customer
  derivation/tie-break, attendee filtering, the "create vs. top-up"
  decision belong to T03's `meeting_classification.py`), no HTTP concerns.
- Must NOT modify any existing function's behavior — additive only.
- `meeting_note_path()`/`create_meeting_note_baseline()` must use the same
  `meeting_note_filename_stem()` helper for the filename, so path
  resolution and file creation always agree on the same file for the same
  event.
- `upsert_attendee_links` must never remove an already-present `[[stem]]`
  wikilink, and must be a true no-op (no write) when every requested stem
  is already present — Scenario 6's idempotency requirement.
- `mark_meeting_processed`/`load_processed_meeting_ids` are generic state
  primitives only — this task does not decide how (or whether) T03 gates on
  them; see the docstring above and T03's Context/Notes.

---

## Tests

<!-- This task's own functions are exercised end-to-end, live, by T05 (the
manual /poc/classify-meetings endpoint — this story's locked ACs) and T04
(the scheduler wiring — AC-10). The smoke checks below are non-AC-tagged
confirmations that this module's new primitives behave correctly in
isolation before T03/T04/T05 build on them. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`, call
   `create_meeting_note_baseline("Verify T02 Meeting", "Verify Customer",
   "2026-08-20T10:00:00", "2026-08-20T11:00:00", "Room 1", "Someone",
   "abcdef1234567890")`. Confirm a file is created under `Work/Meetings/`
   whose name incorporates the subject, the `2026-08-20` date, and the
   entry-id suffix `34567890`, with frontmatter `type: "Meeting"`,
   `customer: "Verify Customer"`, `subject`/`start`/`end`/`location`/
   `organizer` populated, `tags: ["customer/verify-customer",
   "kind/meeting"]`, and an empty body. Confirm `meeting_note_exists(...)`
   with the same arguments returns `True`.
2. Non-AC smoke check: on the same throwaway note, manually remove the
   `location` frontmatter line, then call
   `ensure_meeting_note_baseline_frontmatter(path, "Verify T02 Meeting",
   "Verify Customer", "2026-08-20T10:00:00", "2026-08-20T11:00:00",
   "Room 1", "Someone")` and confirm only the missing `location` line is
   (re-)inserted — the other seven keys and the (empty) body are
   byte-for-byte unchanged. Re-run the same call and confirm nothing
   changes the second time.
3. Non-AC smoke check: on the same throwaway note (empty body), call
   `upsert_attendee_links(path, ["person-a", "person-b"])`. Confirm the
   body's first line is now `**Attendees:** [[person-a]], [[person-b]]`
   and the call returned `True`. Call `insert_body_line_if_missing(path,
   "**Customer:** [[Verify Customer]]")` next and confirm the body's first
   line is now the Customer line, with the Attendees line immediately
   below it (Customer-above-Attendees, matching the resolved schema's
   documented order — see T03's Context/Notes on call order). Call
   `upsert_attendee_links(path, ["person-a", "person-c"])` again and
   confirm the Attendees line becomes `**Attendees:** [[person-a]],
   [[person-b]], [[person-c]]` (existing stems preserved, `person-c`
   appended, `person-b` not duplicated), the Customer line is unaffected,
   and the call returned `True`. Call it a third time with the same three
   stems and confirm it returns `False` (true no-op, file unchanged).
4. Non-AC smoke check: call `mark_meeting_processed("abcdef1234567890")`
   then `load_processed_meeting_ids()` and confirm the ID is present; call
   `mark_meeting_processed("abcdef1234567890")` again and confirm the file
   is unchanged (idempotent). Delete the throwaway note afterward and, if
   now empty, the `Work/Meetings/` directory and the
   `.second-brain/processed_meeting_ids.json` file it created, restoring
   the vault to its pre-task state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `meeting_note_path`/`meeting_note_exists`/`create_meeting_note_baseline`
      resolve to and create the exact schema from
      `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md` → "Meetings",
      keyed by `meeting_note_filename_stem`
- [x] `build_meeting_tags` returns `["kind/meeting"]` alone when `customer`
      is falsy, or `["customer/<slug>", "kind/meeting"]` otherwise
- [x] `ensure_meeting_note_baseline_frontmatter` tops up missing baseline
      keys only, never resets a present value, never touches the body
- [x] `upsert_attendee_links` creates the Attendees line on first use,
      merges in new stems on rerun without duplicating or removing any,
      and is a true no-op when nothing changed
- [x] `load_processed_meeting_ids`/`mark_meeting_processed` mirror
      `load_processed_email_ids`/`mark_email_processed`'s exact shape
- [x] No existing `vault_writer.py` function's behavior changed
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Deciding customer derivation/tie-break, attendee filtering (including the
  vault-owner self-email exclusion), or which meeting to create/update —
  that is T03.
- Wiring the per-write hook into the capture pipeline — that is T04.
- The manual trigger endpoint — that is T05.

---

## Context / Notes

`vault_writer.py` currently ends with `ensure_person_note_baseline_frontmatter`
(added by `REQ-SB-10-US-01-T01`); append the new Meetings primitives
directly after it. No new imports are required — `settings`, `write_note`,
`read_note`, `insert_frontmatter_key_if_missing`, `insert_body_line_if_missing`,
`tag_slug`, `_slugify`, `_WORK_ROOT`, `_STATE_DIR`, `json`, `re` all already
exist in this module (the two new regex constants use the module's existing
`import re`).

---

## Implementation Log

**2026-08-11, coder.** Implemented exactly as specified: `_MEETINGS_SUBFOLDER`,
`_MEETING_NOTE_BASELINE_KEYS`, `_PROCESSED_MEETINGS_FILE`, the two Attendees-
line regex constants, `meeting_note_filename_stem`, `meeting_note_path`,
`meeting_note_exists`, `build_meeting_tags`, `create_meeting_note_baseline`,
`ensure_meeting_note_baseline_frontmatter`, `_processed_meetings_path`,
`load_processed_meeting_ids`, `mark_meeting_processed`,
`upsert_attendee_links` appended to `src/backend/app/data_access/
vault_writer.py` after `ensure_person_note_baseline_frontmatter`. No existing
function's behavior changed (additive only).

**Non-AC smoke checks (manual verification steps 1-4), run against a real
throwaway note in the live vault, then cleaned up:**
1. `create_meeting_note_baseline(...)` — file created at the expected path/
   name, correct frontmatter, empty body, `meeting_note_exists(...) == True`. PASS.
2. `ensure_meeting_note_baseline_frontmatter(...)` on a note with `location`
   surgically removed — only `location` was re-inserted (`inserted ==
   ["location"]`), the other 7 keys untouched; a second call inserted nothing
   and left the file byte-for-byte identical. PASS. **Test-methodology note
   (not a code issue):** the task's own narrative said to "manually remove
   the location frontmatter line" — doing this via naive `splitlines()`/
   `"\n".join()` silently drops the trailing blank-line body separator
   `write_note()` relies on, corrupting the file in a way no real caller
   would. Redid the removal via a surgical regex substitution instead;
   confirms the actual primitive is correct, the first attempt was a smoke-
   test-script bug, not a `vault_writer.py` bug.
3. `upsert_attendee_links(...)` — created the Attendees line on first call,
   merged in a new stem on the second call without duplicating/removing any,
   and returned `False` (true no-op) on a third call repeating the same set.
   PASS. **One prose-vs-behavior discrepancy found and logged (not a
   deviation — the literal code is exactly as specified in Files to
   Modify):** the task's Tests narrative describes the Customer line ending
   up "immediately below" the Attendees line after `insert_body_line_if_
   missing` runs second; the actual observed output has a **blank line**
   between them (`**Customer:** [[Hub]]\n\n**Attendees:** [[...]]`), because
   `insert_body_line_if_missing` (an existing, unchanged REQ-SB-14 function)
   always appends `"\n\n"` after its inserted line — a paragraph-break
   insert, not a same-block line insert. Order (Customer above Attendees) is
   still exactly right, and no locked AC requires zero blank line between
   them (AC-01 only requires both wikilinks present, in that order) — so
   this is a scope-internal observation, not a fix.
4. `mark_meeting_processed`/`load_processed_meeting_ids` — ID recorded,
   idempotent on rerun (second call left the state file byte-for-byte
   identical). PASS.

Cleaned up the throwaway note, its `Work/Meetings/` directory (now empty),
and `.second-brain/processed_meeting_ids.json` afterward, restoring the vault
to its pre-task state (later re-created for real by T03/T05's own live runs).

**Result: PASS.** All items in `## Acceptance Criteria` confirmed.
