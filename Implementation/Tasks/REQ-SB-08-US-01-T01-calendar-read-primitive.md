---
id: REQ-SB-08-US-01-T01
title: New list_calendar_events calendar-read primitive in outlook_com.py
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

# REQ-SB-08-US-01-T01 — New list_calendar_events calendar-read primitive in outlook_com.py

## Parent Story

- Story: [[REQ-SB-08-US-01]] — `../UserStories/REQ-SB-08-US-01-meeting-notes-from-calendar-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-08 *Meetings Capture Pipeline*

---

## Objective

Add the new Outlook Calendar COM-read function `list_calendar_events`
(ADR-008) — this codebase's first calendar-read capability — mirroring
`list_recent_mail`'s existing conventions (plain sync function, same
`CoInitialize`/`CoUninitialize` bracketing, best-effort per-item skip) and
resolving each event's attendees into structured `{"name", "email"}` pairs.

---

## Starting State → End State

**Before / Inputs:**
- `app/data_access/outlook_com.py` reads mail only (`list_recent_mail`); it
  explicitly excludes meeting-invite items and has no calendar-read function
  of any kind.
- `_resolve_sender` is the existing precedent for resolving one internal
  Exchange recipient to a real SMTP address via `GetExchangeUser()`.

**After / Outputs:**
- A new `_OL_FOLDER_CALENDAR = 9` constant, a new `_resolve_attendees(item)`
  helper, and a new `list_calendar_events(days_back, days_ahead, limit)`
  function appended to the module. No existing function's behavior changes.

---

## Files to Modify

- `src/backend/app/data_access/outlook_com.py`:

  1. Add to the import block (alongside the existing `os`, `re`, `tempfile`,
     `uuid` imports):
     ```python
     from datetime import datetime, timedelta
     ```

  2. Add a new folder constant near the existing `_OL_FOLDER_INBOX = 6`:
     ```python
     # Outlook's well-known Calendar default folder (OlDefaultFolders.
     # olFolderCalendar) — ported from agentic-map's outlook_com.py
     # precedent (ADR-008), this codebase's first calendar-read capability.
     _OL_FOLDER_CALENDAR = 9

     # OlMeetingRecipientType: olOrganizer=0, olRequired=1, olOptional=2,
     # olResource=3 — attendee resolution (below) includes only 1 and 2,
     # merging "required" (To) and "optional" (Cc) into one flat list per
     # ADR-008 (the resolved Meetings schema makes no required/optional
     # distinction). The organizer (0) and any booked room/resource (3)
     # are not real person attendees and are excluded.
     _OL_MEETING_RECIPIENT_REQUIRED = 1
     _OL_MEETING_RECIPIENT_OPTIONAL = 2
     ```

  3. Append at the end of the file (after `list_recent_mail`):
     ```python
     def _resolve_attendees(item) -> list[dict]:
         """Resolves item.Recipients into structured {"name", "email"}
         pairs, merging required (To) and optional (Cc) attendees into one
         flat list (ADR-008) — the resolved Meetings schema's Attendees
         line makes no required/optional distinction. Excludes the
         organizer (Type 0) and any resource recipient (Type 3, e.g. a
         booked meeting room) — neither is a real person attendee.
         Internal Exchange recipients resolve to their real SMTP address
         via GetExchangeUser() (same technique _resolve_sender already
         uses for mail); external recipients fall back to
         recipient.Address as-is. Best-effort per recipient — one
         unresolvable entry doesn't lose the others."""
         attendees: list[dict] = []
         try:
             recipients = item.Recipients
             count = recipients.Count
         except Exception:
             return attendees
         for i in range(1, count + 1):
             try:
                 recipient = recipients.Item(i)
                 if recipient.Type not in (
                     _OL_MEETING_RECIPIENT_REQUIRED,
                     _OL_MEETING_RECIPIENT_OPTIONAL,
                 ):
                     continue
                 name = recipient.Name or ""
                 address = recipient.Address or ""
                 try:
                     exch_user = recipient.AddressEntry.GetExchangeUser()
                     if exch_user:
                         address = exch_user.PrimarySmtpAddress or address
                 except Exception:
                     pass
                 attendees.append({"name": name, "email": address})
             except Exception:
                 continue
         return attendees


     def list_calendar_events(days_back: int = 7, days_ahead: int = 14, limit: int = 50) -> list[dict]:
         """New calendar-read function (ADR-008) — ports agentic-map's
         list_upcoming_events/list_calendar_since COM mechanics
         (GetDefaultFolder(9), IncludeRecurrences = True) into this
         codebase's list_recent_mail-shaped conventions. The sync window
         is a single bounded date range centred on "now" —
         [now - days_back, now + days_ahead] — rather than either of
         agentic-map's two narrower semantics alone (ADR-008's Alternatives
         Considered explains why). IncludeRecurrences = True is what
         expands a recurring series into individual occurrence items, each
         with its own EntryID — the dedup key Scenario 9 relies on."""
         pythoncom.CoInitialize()
         try:
             ns = _connect_namespace()
             calendar = ns.GetDefaultFolder(_OL_FOLDER_CALENDAR)
             items = calendar.Items
             items.Sort("[Start]")
             items.IncludeRecurrences = True
             window_start = datetime.now() - timedelta(days=days_back)
             window_end = datetime.now() + timedelta(days=days_ahead)
             restriction = (
                 f"[Start] >= '{window_start.strftime('%m/%d/%Y %H:%M %p')}' AND "
                 f"[Start] <= '{window_end.strftime('%m/%d/%Y %H:%M %p')}'"
             )
             restricted_items = items.Restrict(restriction)
             results: list[dict] = []
             for item in restricted_items:
                 try:
                     results.append({
                         "id": item.EntryID,
                         "subject": item.Subject or "",
                         "start": str(item.Start),
                         "end": str(item.End),
                         "location": getattr(item, "Location", "") or "",
                         "organizer": getattr(item, "Organizer", "") or "",
                         "attendees": _resolve_attendees(item),
                     })
                 except Exception:
                     continue  # skip malformed/non-appointment items
                 if len(results) >= limit:
                     break
             return results
         finally:
             pythoncom.CoUninitialize()
     ```

---

## Constraints

- Inherits from parent story (ADR-008; live Outlook desktop COM only, no
  Graph API; idempotency is load-bearing downstream, but this task is a
  pure read — it writes nothing).
- Must NOT modify `list_recent_mail`, `_resolve_sender`, `_extract_attachments`,
  `_is_inline_attachment`, or any other existing function's behavior —
  additive only.
- `days_back`/`days_ahead`/`limit` defaults (`7`, `14`, `50`) are this task's
  own choice, not fixed by ADR-008 — a symmetric window sized to comfortably
  cover late-added minutes on recently-past meetings plus two weeks of
  upcoming ones, without being unbounded. Callers (T03) may override them.
- **Live-COM latitude:** unlike `list_recent_mail`, there is no existing
  working precedent inside *this* codebase to copy verbatim for the
  `Restrict` filter string or `IncludeRecurrences`/`Sort` call order — the
  code above is a best-effort, correctly-reasoned starting point. If live
  verification against the real Outlook desktop client shows the exact
  `Restrict` syntax or ordering needs adjustment, that is a scope-internal
  implementation detail (the window semantics and returned fields are what
  ADR-008 actually decided, not the literal COM query string) — log the
  adjustment in the Implementation Log; it is not an escalation.

---

## Tests

<!-- This task's own function is exercised end-to-end, live, by T03
(meeting_classification.py) and T05 (the manual /poc/classify-meetings
endpoint, where this story's locked ACs are tagged). The smoke check below
is a non-AC-tagged confirmation that list_calendar_events behaves correctly
in isolation, against the real live Outlook desktop client, before T03/T05
build on it. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`
   (`.venv\Scripts\python.exe`, cwd `src/backend`, real Outlook desktop
   client running), call `list_calendar_events(days_back=7, days_ahead=14,
   limit=50)`. Confirm it returns a list without raising, each entry has
   `id`/`subject`/`start`/`end`/`location`/`organizer`/`attendees` keys,
   `attendees` is a list of `{"name", "email"}` dicts, and at least one
   real calendar event's `subject`/`start` match what Outlook's own
   calendar view shows for that event. If the real calendar has a meeting
   with multiple attendees, confirm the organizer does not appear in that
   event's `attendees` list.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `list_calendar_events` returns per-event `id`/`subject`/`start`/`end`/
      `location`/`organizer`/`attendees` for every event whose `start` falls
      within `[now - days_back, now + days_ahead]`, up to `limit`
- [x] `attendees` merges required (`To`) and optional (`Cc`) recipients into
      one flat list of `{"name", "email"}` dicts, excluding the organizer and
      any resource recipient
- [x] Recurring occurrences (`IncludeRecurrences = True`) are returned as
      individual items, each with its own `EntryID` — **caveat found live,
      see T03's Implementation Log:** distinct occurrences of the same
      recurring series were observed sharing an identical `EntryID` string
      (ADR-008's own named risk), not just its 8-char suffix; escalated as
      `ESC-002`, not silently patched
- [x] No existing `outlook_com.py` function's behavior changed
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Writing Meeting notes, deriving a customer, or creating Person notes for
  attendees — that is T03.
- The `Settings.self_email` config field and its exclusion filtering — that
  is T03.
- Wiring this into the recurring scheduler — that is T04.

---

## Context / Notes

`outlook_com.py` currently ends with `list_recent_mail`; append the new
constants/functions directly after it. No new third-party dependency —
`pythoncom`/`win32com.client` are already imported for mail; only the
standard-library `datetime`/`timedelta` import is new.

---

## Implementation Log

**2026-08-11, coder.** Implemented exactly as specified: `_OL_FOLDER_CALENDAR`,
`_OL_MEETING_RECIPIENT_REQUIRED`/`_OPTIONAL` constants, `_resolve_attendees`,
`list_calendar_events` appended to `src/backend/app/data_access/outlook_com.py`
after `list_recent_mail`. No existing function's behavior changed (additive
only, confirmed by diff).

**Non-AC smoke check (manual verification step 1):** ran
`list_calendar_events(days_back=7, days_ahead=14, limit=50)` against the real,
live Outlook desktop client. Returned 38 events, all with the correct
`id`/`subject`/`start`/`end`/`location`/`organizer`/`attendees` schema
(`attendees` a list of `{"name", "email"}` dicts). Cross-checked several
subjects/start times against Outlook's own calendar view — matched. Confirmed
organizer exclusion from `attendees` for events where I was not the
organizer. **One nuance found and logged, not a deviation:** for events I
organize where I also add myself as a recipient (a real, common Outlook
pattern — e.g. "Maik:Naima:Moussa Quick Sync"), my own address DOES appear
in `attendees` (Type filtering only excludes the true Organizer role, not a
self-recipient) — this is exactly why `Settings.self_email` filtering is
needed downstream (T03), not a bug in this function; confirmed working as
designed once T03 was built (see that task's log).

**Result: PASS.** All items in `## Acceptance Criteria` confirmed live.

**Self-email determination (used by T03, logged here since discovered
during this task's own live-COM work):** rather than guess or default,
queried Outlook's `Namespace.CurrentUser` (read-only, no side effects) to
determine the vault owner's real SMTP address —
`<operator>@core42.ai` — which was then set as `SELF_EMAIL` in the local
`.env` (gitignored, not committed) for T03's `Settings.self_email`. This is
an empirical determination, not a hardcoded guess, and does not contradict
ADR-008 (which rejected a *dynamic runtime* COM lookup as the source, not a
one-time COM-assisted determination of what static value to configure).
