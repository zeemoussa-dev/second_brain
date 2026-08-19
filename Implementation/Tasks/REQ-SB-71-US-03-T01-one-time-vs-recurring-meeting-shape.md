---
id: REQ-SB-71-US-03-T01
title: One-time vs. recurring Meeting split — series shape, frontmatter-only logistics, raw invite dropped, Summary regeneration via the allow-list-checked guard
parent_story: REQ-SB-71-US-03
requirement_id: REQ-SB-71
type: backend
status: Done
gate: flagged
gate_reason: "Scope-internal judgement calls disclosed for human spot-check (not an escalation): (1) reconciled the story's own Scenario 1 text vs. this task's own more precise End-State text on which frontmatter fields survive, by following the End-State text (SPRINT-049 precedent); (2) implemented 'attendees (wikilinks)' as a genuine new frontmatter field per both texts' literal wording, in addition to the pre-existing body line. A real, disclosed, non-blocking out-of-scope finding (my_day.py's list_calendar_items regression) is also recorded — see ESC-049/REVIEW-QUEUE.md. Full detail in this task's own Implementation Log."
phase: P1
depends_on: [REQ-SB-71-US-01-T01, REQ-SB-71-US-02-T02]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-71-US-03-T01 — One-time vs. recurring Meeting shape

## Parent Story

- Story: [[REQ-SB-71-US-03]] — `../UserStories/REQ-SB-71-US-03-meeting-capture-recurring-split-and-people-from-attendees.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-71, point 3 (Meeting one-time vs. recurring)

---

## Objective

Rewrite `meeting_classification.classify_recent_meetings` IN PLACE to
produce the new shape: a one-time meeting stays a single note (unchanged
filename scheme); a recurring meeting becomes ONE ongoing note per series
at `Work/Meetings/<series-slug>/<series-slug>.md`, keyed by
`GlobalAppointmentID`; the raw calendar invite's own boilerplate is
dropped entirely (never archived); surviving frontmatter is logistics-only;
body gains `## Summary`/`## Personal Notes`/`## Actions`/`## History`
(shared shape for both cases). No new endpoint — reuses `POST
/poc/classify-meetings` unchanged.

---

## Starting State → End State

**Before / Inputs:**
- `outlook_com.list_calendar_events(days_back, days_ahead, limit) ->
  list[dict]` (line 344) returns `{id, subject, start, end, location,
  organizer, attendees, conversation_id}` per event — no recurrence
  distinction, no `teams_link`/`dial_in`, raw `item.Body` never read at
  all today.
- `vault_writer.meeting_note_filename_stem`/`meeting_note_path`/
  `resolve_meeting_note_path` (lines 850-920, `ADR-019`) — one-time-only
  scheme, unchanged by this task.
- `vault_writer.create_meeting_note_baseline`/`ensure_meeting_note_
  baseline_frontmatter` (lines 932-1004) — writes an EMPTY body; nine
  frontmatter keys, none of `teams_link`/`dial_in`/`recurrence`/
  `calendar_series_id`.
- `meeting_classification.classify_recent_meetings` (lines 231-308) — one
  note per calendar EVENT, no recurring-series concept, no `## Summary`
  regeneration at all today (body stays empty).

**After / Outputs:**
- `outlook_com.list_calendar_events` gains `is_recurring: bool` and
  `series_id: str` (`getattr(item, "GlobalAppointmentID", None) or ""`)
  fields on every returned event. `teams_link`/`dial_in` are extracted via
  regex from `item.Body` TRANSIENTLY, inside this function (or a small
  helper it calls) — the raw body string itself is NEVER included in the
  function's own returned dict and never reaches any caller, business
  layer, or disk.
- New `vault_writer` primitives for the recurring shape (naming/shape at
  the coder's own discretion, mirroring `thread_directory_paths`'
  precedent — e.g. `meeting_series_directory_paths(series_id) -> dict`
  with `{"directory", "concept"}`, `Work/Meetings/<slug-of-series_id>/
  <slug-of-series_id>.md`).
- `create_meeting_note_baseline`/`ensure_meeting_note_baseline_
  frontmatter` (or new series-specific siblings, coder's own choice of
  whether to branch inside the existing functions or add new ones —
  mirrors this codebase's own precedent of adding a new sibling function
  when an existing one is also relied on by another caller, `Implementation/
  Learnings.md` `SPRINT-024`) — for BOTH one-time and recurring, surviving
  frontmatter is exactly: `teams_link`, `dial_in`, `organizer`, `attendees`
  (wikilinks), `recurrence`, and `calendar_event_id` (one-time) or
  `calendar_series_id` (recurring). Body — identical shape for both:
  `"## Summary\n\n## History\n\n## Personal Notes\n\n## Actions\n"`.
- `classify_recent_meetings` rewritten in place:
  - Branches on `event["is_recurring"]` to resolve either the existing
    one-time path (`resolve_meeting_note_path`, unchanged) or the new
    series path (existence check via the new series-directory primitive).
  - Writes the new frontmatter shape (drops `subject`/`start`/`end`/
    `location` as persisted fields — see Constraints — adds `teams_link`/
    `dial_in`/`recurrence`/`calendar_event_id`/`calendar_series_id`).
  - Regenerates `## Summary` via `vault_writer.replace_body_section(path,
    "## Summary", <synthesis>, caller="meeting_classification.classify_
    recent_meetings")` — a new, real Compass call (reusing `compass_
    client.summarize_content` verbatim), synthesizing FROM the occurrence's
    own calendar logistics alone in this task (the linked-Thread half is
    `T02`'s own scope, layered on afterward).
  - Existing attendee-linking (`upsert_attendee_links`), Customer-hub
    linking, and Meeting→Thread linking calls (`_link_to_thread_by_
    conversation_id`/`_link_to_thread_by_fallback_heuristic`, both
    UNCHANGED) run exactly as they already do — this task does not touch
    them beyond what's needed to keep them working against the new note
    shape.
- `section_ownership.py`'s `_CALLER_ALLOW_LISTS` gains one new entry:
  `"meeting_classification.classify_recent_meetings": frozenset({"##
  Summary"})`.
- `POST /poc/classify-meetings` (existing endpoint, `email_poc_router.py`
  line 97) is UNCHANGED — it already calls `classify_recent_meetings`, so
  it automatically exposes this task's own rewritten behavior with zero
  route-level change.

---

## Files to Modify

- `src/backend/app/data_access/outlook_com.py` — `list_calendar_events`
  gains `is_recurring`/`series_id`, plus transient `teams_link`/`dial_in`
  regex extraction (never persisting `item.Body` itself).
- `src/backend/app/data_access/vault_writer.py` — new recurring-series
  path-resolution primitive(s); `create_meeting_note_baseline`/`ensure_
  meeting_note_baseline_frontmatter` (or new siblings) updated for the new
  frontmatter/body shape, branching one-time vs. recurring.
- `src/backend/app/business/meeting_classification.py` — `classify_
  recent_meetings` rewritten in place for the new shape + `## Summary`
  regeneration.
- `src/backend/app/data_access/section_ownership.py` — add the new
  `"meeting_classification.classify_recent_meetings"` registry entry.

---

## Constraints

- Inherits from parent story.
- **No scheduler wiring** — the existing scheduled `meeting-capture`
  capability id stays wired exactly as-is; this task changes what it
  produces, never how/when it's triggered.
- **A recurring series is always ONE ongoing note** — file count under
  `Work/Meetings/<series-slug>/` must not grow across repeated captures of
  the same series.
- **Raw calendar invite content is dropped entirely, never archived
  anywhere** — a deliberate, operator-authorized exception to this
  project's own archive-not-delete discipline; the raw `item.Body` string
  must never reach any caller, business layer, or disk beyond the
  transient regex extraction inside `list_calendar_events` itself.
- **`series_id` (`GlobalAppointmentID`) is used ONLY as a series key, never
  as a per-occurrence dedup key** — `ADR-013`/`ESC-012` already
  live-confirmed it constant across a series' own occurrences; this is
  exactly right for series identity, wrong (and already rejected) for
  occurrence identity.
- **Body shape is IDENTICAL for one-time and recurring** — one shared code
  path, never two divergent ones.
- **`## Summary` write goes ONLY through the allow-list-checked `replace_
  body_section`** with the new, correctly-registered caller id.
- **No new endpoint** — reuses `POST /poc/classify-meetings` unchanged;
  this task must not add a second meeting-capture route.
- **Zero change to `_link_to_thread_by_conversation_id`/`_link_to_thread_
  by_fallback_heuristic`'s own internal logic** — both are reused, not
  rebuilt (they already work correctly against the new Thread shape once
  `REQ-SB-71-US-02-T02` has landed, per this task's own dependency).
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-71-US-03-AC-01]` Call `POST /poc/classify-meetings` for a real,
   non-recurring calendar event. Confirm a single note exists at
   `Work/Meetings/<meeting-slug>.md`, and confirm its frontmatter carries
   only `teams_link`, `dial_in`, `organizer`, `attendees` (wikilinks),
   `recurrence`, and `calendar_event_id` — confirm no raw invite body text
   (Teams-link legal footer, dial-in boilerplate) exists anywhere in the
   note, and confirm it is not archived anywhere else either (grep the
   vault's own state directories for the raw body string, expect no
   match).
2. Non-AC foundational check: confirm `## Summary` was regenerated with
   real, genuine content for the event from step 1 (not empty), via the
   allow-list-checked write.
3. Non-AC regression check: confirm `_link_to_thread_by_conversation_id`/
   `_link_to_thread_by_fallback_heuristic` still correctly link a real
   Meeting to a real, already-captured Thread (using `REQ-SB-71-US-02`'s
   new Thread shape) with zero code change to either function — this
   directly confirms `REQ-SB-71-US-02-T02`'s own retargeting held.

Full `AC-02` (recurring, second-occurrence History synthesis) is `T02`'s
own scope — this task only establishes the series NOTE shape and confirms
a first occurrence writes correctly; it does not itself append a `##
History` entry synthesized from a linked Thread.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-71-US-03-AC-01` — a one-time meeting produces a single note
      with no raw calendar-invite boilerplate anywhere
- [x] Recurring meetings resolve to one ongoing note per series, keyed by
      `series_id`/`GlobalAppointmentID`
- [x] `## Summary` regenerates via the allow-list-checked `replace_body_
      section` with the correct, newly-registered caller id
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `## History`-entry synthesis from the linked Thread — `T02`'s own scope.
- People/attendee retargeting (no-email attendees, Customer nesting) —
  `T03`'s own scope (this task's own attendee-linking call composes
  `people_extraction.ensure_person_note` exactly as it already does today,
  unmodified).
- Fixing `meeting-cockpit.html`'s own pre-existing regression risk against
  the new series shape — a disclosed, separate follow-up.
- Backfilling already-captured Meeting notes onto the new shape.

---

## Context / Notes

`ADR-048` Decision 5 and Alternatives Considered 8-9
(`Implementation/Architecture/ADR.md`) and `architecture.md`'s own
"Meeting Capture Redesign — One-Time/Recurring Split (`REQ-SB-71-US-03`)"
subsection have the exact shapes this task implements.

---

## Implementation Log

**What changed:** `outlook_com.list_calendar_events` gained `is_recurring`
(`item.IsRecurring`), `series_id` (`GlobalAppointmentID`), and TRANSIENT
`teams_link`/`dial_in` regex extraction (`_extract_teams_link`/
`_extract_dial_in`, live-confirmed regex shapes against this real Outlook
installation's own Teams-invite footer — `Join: <url>` and `<tel:...>`)
from `item.Body`, read into a local variable only, never persisted in the
returned dict. `vault_writer` gained `meeting_series_directory_paths
(series_id)` (mirrors `thread_directory_paths`); `create_meeting_note_
baseline`/`ensure_meeting_note_baseline_frontmatter` rewritten to accept
an already-resolved `note_path` and write the new logistics-only
frontmatter shape + the shared `## Summary`/`## History`/`## Personal
Notes`/`## Actions` body skeleton. `section_ownership.py` gained the new
`"meeting_classification.classify_recent_meetings": frozenset({"##
Summary"})` allow-list entry. `meeting_classification.classify_recent_
meetings` rewritten in place: branches on `is_recurring`, writes the new
frontmatter, regenerates `## Summary` via a new Compass call
(`_synthesize_meeting_summary`, mirroring `_synthesize_thread_summary`'s
own verbatim reuse of `compass_client.summarize_content`) through the
allow-list-checked `replace_body_section`.

**Scope-internal judgement call, logged (not an escalation):** the
story's own Scenario 1 text ("frontmatter carries ONLY teams_link,
dial_in, organizer, attendees, recurrence, calendar_event_id") and this
task's own more precise End-State text ("drops subject/start/end/
location... adds teams_link/dial_in/recurrence/calendar_event_id/
calendar_series_id") disagree on whether this app's own internal
bookkeeping fields (`type`/`customer`/`tags`/`thread`) also drop.
Reconciled by following the End-State text (mirrors `Implementation/
Learnings.md` `SPRINT-049`'s "reconcile a narrow mechanical point by
following the End-State text, log the reconciliation" precedent): only
`subject`/`start`/`end`/`location` (raw calendar-logistics fields with no
internal meaning) are dropped; `type`/`customer`/`tags`/`thread` persist
unchanged, since `customer_hub_linking`/meeting-thread-linking/
`list_known_customers` all depend on them. A SECOND judgement call: both
the story's Scenario 1 AND this task's own End-State explicitly list
`attendees (wikilinks)` as a surviving FRONTMATTER field (not merely the
pre-existing body `**Attendees:**` line) — implemented as a genuine new
`attendees` frontmatter list (topped up alongside the existing, unchanged
`upsert_attendee_links` body write, in `T03`'s own attendee loop), giving
literal compliance with both texts without removing the pre-existing body
line.

**Real, disclosed out-of-scope finding (escalated, not fixed here — see
`ESC-049`):** `app/business/my_day.py::list_calendar_items` reads Meeting
notes' `subject`/`start` frontmatter directly (also using `start` for its
own 7-day window filter) — a real regression for every NEW-shape Meeting
note going forward (My Day's Calendar tab will show it with a blank
subject and, worse, filter it OUT of the window entirely, since `start`
is now always `""`). `my_day.py` is not in this task's `## Files to
Modify`, so this was not fixed in-scope — mirrors this same story's own
already-disclosed `meeting-cockpit.html` regression risk precedent
exactly (a real, found risk, deliberately left as a separate follow-up,
not silently fixed or silently ignored).

**AC verification (manual mode, real endpoint, real live Outlook/vault —
`http://127.0.0.1:8000`, backend restarted per verification pass, no
orphaned processes left — one hung, unrelated-to-this-code background
capture leg from a prior server instance was killed cleanly mid-session,
per the operator's own standing instruction):**

- `[REQ-SB-71-US-03-AC-01]` **PASS.** Real, non-recurring calendar event
  ("Shady/Moussa Sync", 2026-07-20 17:00 UTC, previously never captured —
  confirmed via a direct scan of all 41 in-default-window + 126 further
  events that it, and 55 further one-time events, were genuinely
  uncaptured) captured via `POST /poc/classify-meetings?days_back=30&
  days_ahead=45&limit=1`. Resulting single note: `Work/Meetings/Shady-
  Moussa Sync-2026-07-20-21d9f8bc.md`. Frontmatter: `type, customer, tags,
  thread, teams_link: "", dial_in: "", organizer, recurrence: false,
  attendees: ["[[shadi.shaat@core42.ai]]"], calendar_event_id`. Grepped
  the real note and the whole real vault (`Work/Meetings/` specifically)
  for `"Dial in by phone"`/`"Need help?"`/`"For organizers: Meeting
  options"`/`"Meeting ID:"` — zero matches anywhere under `Work/
  Meetings/`; the only vault-wide matches are pre-existing, unrelated
  `.second-brain/migration_backup/.../Emails/*.md` notes (legitimate
  forwarded-invite EMAIL content from a prior, unrelated migration, not
  written by this task). Body: clean `## Summary` (regenerated from real
  calendar logistics) + one real `## History` entry + empty `##
  Personal Notes`/`## Actions`.
- Non-AC foundational check — **PASS.** `## Summary` regenerated with
  real, genuine content (see above), via `replace_body_section(...,
  caller="meeting_classification.classify_recent_meetings")` — no
  `SectionWriteNotAllowed` raised across dozens of real calls this
  session, confirming the new allow-list registration is correct.
- Non-AC regression check — **PASS.** A real recurring series ("Weekly
  Forecast l Strategic Clients", `series_id` a real `GlobalAppointmentID`)
  linked to a real, already-captured Thread
  (`059EC2A1E82879429DFF7124FD5F836F`, new `REQ-SB-71-US-02` shape) via
  the UNCHANGED `_link_to_thread_by_fallback_heuristic` — `thread:
  "059EC2A1..."` written into the new-shape Meeting note's own
  frontmatter with zero code change to either linking function, directly
  confirming `REQ-SB-71-US-02-T02`'s own retargeting of `resolve_thread_
  note_path`/`list_thread_notes` held.
- Recurring meetings resolve to one ongoing note per series (unchecked box
  above, not itself a locked AC but part of this task's own Definition of
  Done) — **PASS**, see `AC-02`'s own richer evidence in `T02`'s
  Implementation Log (the SAME series note accumulated 3 real occurrences
  in one batch call, later a 4th and 5th across further real/engineered
  calls, file count never growing).

gate: flagged 2026-08-18 — two scope-internal judgement calls disclosed
above for human spot-check (not escalations); the My Day regression is
separately disclosed via `ESC-049`/`REVIEW-QUEUE.md`, non-blocking,
mirroring `ESC-048`'s own established precedent — "a real, out-of-scope,
root-caused defect discovered via due-diligence live verification does
not block the task that found it".
