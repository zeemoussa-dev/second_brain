---
id: REQ-SB-43-US-01-T03
title: New app/business/cockpit/people.py + people_extraction.find_existing_person_note(email) — resolves attendees/recipients into chips, never creating a Person note
parent_story: REQ-SB-43-US-01
requirement_id: REQ-SB-43
type: backend
status: Done
gate: flagged
gate_reason: "scope-internal judgment call — real vault_writer.py frontmatter-parser limitation found live, worked around entirely within this task's own 2 files, no shared-interface change; see Implementation Log."
phase: P1
depends_on: []
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-43-US-01-T03 — `app/business/cockpit/people.py`

## Parent Story

- Story: [[REQ-SB-43-US-01]] — `../UserStories/REQ-SB-43-US-01-meeting-cockpit-expert-assisted-workspace.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-43 *Meeting Cockpit — Expert-Assisted Meeting Workspace*

---

## Objective

New `app/business/cockpit/people.py::resolve_people_chips(subject_kind, subject_note_stem) -> list[dict]` — reads the subject note's `attendees` frontmatter list (Meeting; `recipients` for Email is `REQ-SB-44`'s own field, this task only needs `attendees` to be real today) and resolves each person into a clickable-or-plain chip, via a NEW, read-only `people_extraction.find_existing_person_note(email) -> dict | None` — the first pure lookup in that module (every existing entry point either creates-or-finds or writes a link); the Cockpit must never create a Person note as a side effect of merely opening (`ADR-036` point 7).

---

## Starting State → End State

**Before / Inputs:**
- `app.business.vault_indexing.get_index() -> dict[str, dict]` is Done (`ADR-024`) — keyed by note stem, each entry carries `frontmatter`.
- `app.data_access.vault_writer.person_note_exists(email)`/`person_note_path(email)`/`read_note(path)` are Done (used internally by `people_extraction.ensure_person_note`).
- `people_extraction.py` has no pure "find, never create" lookup today.

**After / Outputs:**
- `people_extraction.py` gains:
  ```python
  def find_existing_person_note(email: str) -> dict | None:
      """Read-only -- returns {"note_path": str, "name": str} if a Person
      note already exists for this email, else None. NEVER creates a
      Person note (unlike ensure_person_note) -- the Cockpit must not
      mutate the vault as a side effect of merely opening (ADR-036 point
      7). Reuses person_note_exists/person_note_path's own real identity
      convention -- no new normalization scheme."""
      if not email or not vault_writer.person_note_exists(email):
          return None
      note_path = vault_writer.person_note_path(email)
      frontmatter, _ = vault_writer.read_note(note_path)
      return {"note_path": str(note_path), "name": frontmatter.get("name") or frontmatter.get("subject") or email}
  ```
- New `app/business/cockpit/people.py`:
  ```python
  """Cockpit people-chip resolution (ADR-036 point 7) -- reads a subject
  note's attendees/recipients frontmatter list directly, resolving each
  person via people_extraction's new read-only lookup. Never creates a
  Person note."""
  from __future__ import annotations

  from app.business import people_extraction, vault_indexing

  _ATTENDEE_FIELD_BY_KIND = {"meeting": "attendees", "email": "recipients"}


  def resolve_people_chips(subject_kind: str, subject_note_stem: str) -> list[dict]:
      entry = vault_indexing.get_index().get(subject_note_stem)
      if entry is None:
          return []
      field = _ATTENDEE_FIELD_BY_KIND.get(subject_kind, "attendees")
      people = entry["frontmatter"].get(field) or []
      chips = []
      for person in people:
          existing = people_extraction.find_existing_person_note(person.get("email", ""))
          chips.append({
              "name": person.get("name") or person.get("email") or "Unknown",
              "email": person.get("email"),
              "has_note": existing is not None,
              "note_path": existing["note_path"] if existing else None,
          })
      return chips
  ```

---

## Files to Modify

- `src/backend/app/business/people_extraction.py` — add `find_existing_person_note`, additive alongside the existing functions.
- `src/backend/app/business/cockpit/people.py` (new) — per the code block above.

---

## Constraints

- `find_existing_person_note` NEVER calls `create_person_note_baseline`/`ensure_person_note_baseline_frontmatter` or any other write primitive — pure read.
- `resolve_people_chips` reads the subject note's frontmatter via `vault_indexing.get_index()` only (already-indexed data, `ADR-024`) — never a fresh `vault_writer.read_note()` call of its own for the subject note (the index already has its frontmatter).
- `_ATTENDEE_FIELD_BY_KIND["email"] = "recipients"` is forward-declared for `REQ-SB-44`'s own new field — this task does not require any Email note to actually carry a `recipients` field yet (an absent field reads as `[]`, per `ADR-036`'s own Consequences: "the Cockpit's own people-chip resolution must treat a missing field as an empty list, not an error").
- A missing/empty `attendees`/`recipients` field, or an unindexed `subject_note_stem`, returns `[]` — never raises.
- Does not modify `customer_hub_linking.py`/`partner_hub_linking.py`/`ensure_person_note`/any existing `people_extraction.py` function.

---

## Tests

**Manual verification steps** (Python shell, backend `.venv`, `PYTHONPATH=.`; use a real Meeting note already captured in the dev vault with at least one real attendee, or write one via `vault_writer.write_note` for this test):
1. **[REQ-SB-43-US-01-AC-02]** Pick (or create) a real Meeting note whose `attendees` frontmatter includes a person with an ALREADY-existing Person note (e.g. someone `retrofit_people_from_emails`/an earlier real capture already created). `vault_indexing.rebuild_index()` first (ensure the note is indexed). `cockpit.people.resolve_people_chips("meeting", "<that-meeting-stem>")` — confirm the matching entry has `has_note == True` and a real `note_path`.
2. **[REQ-SB-43-US-01-AC-03]** In the same call, confirm an attendee with NO existing Person note has `has_note == False`, `note_path is None` — never a fabricated path.
3. Non-AC smoke check: `people_extraction.find_existing_person_note("")` → `None` (blank email, no crash).
4. Non-AC smoke check: `cockpit.people.resolve_people_chips("meeting", "a-stem-that-does-not-exist")` → `[]`.
5. Non-AC smoke check: confirm `find_existing_person_note` never created a Person note as a side effect — before/after file count under the vault's `Work/People/` folder is unchanged by this entire verification session.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `find_existing_person_note` is read-only, never creates a Person note, returns `None` for a blank/unresolvable email
- [ ] `resolve_people_chips` resolves each `attendees`/`recipients` entry into `{"name", "email", "has_note", "note_path"}`
- [ ] A missing field or unindexed stem returns `[]`, never raises
- [ ] No existing `people_extraction.py` function modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The shared thread mechanism — `T02`.
- Quick research / save-discard — `T04`.
- The HTTP router — `T05`.
- `REQ-SB-44`'s own `recipients` frontmatter capture — that story's own task.

---

## Context / Notes

Full mechanism/reasoning: `ADR-036` point 7. `find_existing_person_note` is the FIRST pure lookup in `people_extraction.py` — every existing entry point either creates-or-finds (`ensure_person_note`) or writes a link (`link_email_to_person`); read that module's real current shape before adding this function, to place it consistently alongside the others.

---

## Implementation Log

**Real, disclosed technical finding, scope-internal judgment call, not guessed
past (logged for human spot-check, not a MUST-FLAG escalation — stayed entirely
within this task's own 2 declared files, no shared-interface change):**
`ADR-036` point 7 states the Meeting note's `attendees` field is "already-
established" as `list[{"name","email"}]` frontmatter. Direct investigation of
the REAL, current `meeting_classification.py`/`vault_writer.py` found this is
NOT accurate — Meeting notes carry NO `attendees` frontmatter field at all
today (only `type`/`customer`/`subject`/`start`/`end`/`location`/`organizer`/
`tags`); attendee data lives solely as body-level `**Attendees:** [[wikilinks]]`.
Worse, a live test proved `vault_writer.py`'s own real
`_format_frontmatter_value`/`_parse_frontmatter_value` pair does not support a
list-of-dicts literal at all — writing `{"attendees": [{"name":...,
"email":...}, ...]}` via `write_note` produces a Python-repr frontmatter line
(`attendees: [{'name': ...}]`, invalid to re-parse) that round-trips back as an
empty list, silently losing the data, regardless of whether the source is a
real captured note or a hand-constructed test note. This is a genuine
structural gap in a shared primitive, not "no real data yet."

**Fix, entirely within this task's own file scope:** `cockpit/people.py` gained
`_coerce_people_list`, accepting EITHER a real `list` (spec'd shape, forward-
compatible with a future `vault_writer.py` change) OR a JSON-encoded `str`
(decoded via `json.loads`) — the only shape the CURRENT frontmatter parser can
actually round-trip correctly (its existing quoted-string branch, unmodified).
No change to `vault_writer.py`/any shared interface. Documented in the
function's own docstring so a future story that adds real `attendees`/
`recipients` capture knows to write it as a JSON string (or that
`vault_writer.py` itself needs a native list-of-dicts branch first).

**Manual verification (real `.venv`, real vault):**
1. **AC-02:** wrote a real test Meeting note (`Work/Meetings/cockpit-t03-test-meeting.md`) via `vault_writer.write_note`, `attendees` field = `json.dumps([...])` containing a real attendee (`a.tuffaha@core42.ai`, an already-existing real Person note) + a fabricated non-existent attendee. `vault_indexing.rebuild_index()`. `resolve_people_chips("meeting", "cockpit-t03-test-meeting")` → the real attendee resolved `has_note: True`, `note_path` pointing at the real, existing `Work/People/a.tuffaha@core42.ai.md`. Confirmed.
2. **AC-03:** in the same call, the fabricated attendee resolved `has_note: False`, `note_path: None` — never a fabricated path. Confirmed.
3. Non-AC: `find_existing_person_note("")` → `None`. Confirmed.
4. Non-AC: `resolve_people_chips("meeting", "a-stem-that-does-not-exist")` → `[]`. Confirmed.
5. Non-AC: `Work/People/` file count (135) unchanged across this entire verification session — confirmed `find_existing_person_note` never created a Person note as a side effect.
6. Cleanup: test Meeting note deleted, confirmed absent.

**Real-data caveat, honestly disclosed:** because no task in this sprint writes
`attendees`/`recipients` onto real captured notes (explicitly out of scope per
the story's own Non-Goals), every REAL, pipeline-captured Meeting note in the
vault today has no `attendees` field at all and will honestly resolve to `[]`
via this function's own required Constraint ("a missing/empty field... returns
[], never raises") until a future story adds real capture-time writing of this
field using the JSON-string convention documented above.

gate: flagged 2026-08-14 — scope-internal judgment call (the `_coerce_people_list`
workaround above), logged for human spot-check; no ESCALATIONS.md entry (stayed
within this task's own file scope, no shared-interface change, no ADR
contradiction — the fix corrects `ADR-036`'s own inaccurate factual premise about
an "already-established" field, not a deviation from an actual architectural
decision).
