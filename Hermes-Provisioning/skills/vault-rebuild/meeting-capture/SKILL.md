---
name: meeting-capture
description: Captures calendar meetings into the vault -- one folder per meeting/series, one file per recurring occurrence -- mirroring email-thread-capture's own structure.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, meeting, calendar, capture]
---

# Meeting Capture

Mechanical, no-judgment capture of Outlook calendar events into the
vault -- the Meetings equivalent of `email-thread-capture`. Every event
in a bounded calendar window becomes a real Meeting note (or one
occurrence of a recurring series), with attendees turned into bare
Person notes and, where a confident match exists, linked to a related
email Thread. **Never summarizes, never derives a Customer/Partner tag**
-- both are separate, later, deliberate passes (see "What this does NOT
do" below), matching this codebase's own established discipline for
Threads (a wrong immediate-derivation attempt there caused real bugs;
Meetings intentionally does not repeat that mistake).

## Prerequisites

- `pywin32` (`pip install pywin32`) and Outlook desktop running and
  signed in.
- Vault path (pass as `--vault-path` / `SECOND_BRAIN_VAULT_PATH` env
  var): `C:\myWorx\Moussa MD\Moussa Brain`
- Optional `SECOND_BRAIN_SELF_EMAIL` / `--self-email`: excludes the
  vault owner's own address from every meeting's own attendee list --
  they are never captured as an attendee of their own meeting.

## Structure this builds

```
Work/Meetings/<date> <Subject>/       -- ONE-TIME meeting
    <date> <Subject>.md               -- the only file; this meeting only
                                          ever happens once, so this IS
                                          the occurrence.

Work/Meetings/<Subject>/               -- RECURRING series (no date --
                                           the folder spans every
                                           occurrence)
    <Subject>.md                        -- series concept note; "## History"
                                           lists every occurrence
                                           (wikilinks down, dated), mirrors
                                           a Thread concept's own
                                           "## Related".
    occurrences/
        <date> <time> <Subject>.md      -- one real file PER OCCURRENCE,
                                            mirrors Threads' own messages/
                                            folder shape exactly. Never one
                                            ever-growing note for the whole
                                            series (operator, 2026-08-21,
                                            explicit correction of an
                                            earlier design that did that).
```

Both note kinds share the same frontmatter shape: `type, recurrence,
organizer, teams_link, dial_in, attendees, tags, thread,
calendar_event_id`/`calendar_series_id`, `start, end, location`
(start/end/location live on whichever file IS the occurrence -- the
single file for one-time, each occurrence file for recurring; the
series concept file itself carries none of the three, since it spans
many).

Body: `## Summary` / `## Quick Notes` (2026-08-21, operator: WhatsApp
findings sent to Hermes land here -- matching mechanism for "which
meeting" is a separate, later design, not built yet -- this is just the
reserved section) / `## Personal Notes` / `## Actions` / `## Related`
(Person + Company wikilinks, same pattern as Threads); a recurring
series' own concept note additionally gets `## History`.

## How to Run

One script, one call (mirrors email capture's own primary path). **Use
the script's own full absolute path, never a bare filename** (2026-08-21
bug fix, live-confirmed in a sibling Skill: a bare filename with no
`cwd` set failed 19 times in a row in a real cron run -- a cron-triggered
agent's own default working directory is the user's home folder, not
this Skill's own `scripts/`. The absolute-path form removes that
dependency entirely, even when a `cwd` parameter is also available):

```
terminal(command="python \"C:\\Users\\mahmoud.moussa\\AppData\\Local\\hermes\\skills\\vault-rebuild\\meeting-capture\\scripts\\run_full_meeting_capture.py\"")
```

This script is naturally recurring-safe as-is (a bounded calendar
window, resolved-by-calendar-id dedup) -- suitable for a recurring
Hermes cron job directly, no separate delta variant needed the way email
capture's own full-history pull required one.

Env vars: `SECOND_BRAIN_VAULT_PATH` (default matches Prerequisites),
`SECOND_BRAIN_SELF_EMAIL`, `SECOND_BRAIN_MEETING_DAYS_BACK` (default 7),
`SECOND_BRAIN_MEETING_DAYS_AHEAD` (default 14).

Prints `{"events_in_window", "processed", "series_created",
"one_time_meetings_created", "occurrences_created", "attendees_linked",
"threads_linked", "errors"}`.

**Never wrap this in `bash -lc "..."`** (or any other `-c`/`-lc`
shell-string form) -- Hermes' own `terminal` tool categorically requires
human approval for that shape, which stalls a cron-triggered run with no
one there to approve it (the exact same class of issue documented in
`email-thread-capture`'s own SKILL.md and `summarize-and-tag-threads`'s
own SKILL.md -- read either for the full incident). A bare `python ...`
command, no shell wrapper at all, is confirmed to run without a prompt.

## What this does NOT do

- **Never derives a Customer/Partner tag at capture time.** A meeting
  only ever gets `tags: ["kind/meeting"]` here. Company tagging is a
  separate, later, deliberate pass (not yet built -- would mirror
  `create-companies-partners`'s own `retag_threads_by_participant_company`,
  applied to Meeting attendees instead of Thread participants).
- **Never summarizes.** `## Summary` stays empty -- that's a future
  agent-driven pass, same relationship `summarize-and-tag-threads` has to
  `email-thread-capture`.
- **Never resolves "which meeting" for a WhatsApp Quick Note.** The
  `## Quick Notes` section exists in the schema now; the actual
  send-a-WhatsApp-message-to-Hermes-and-have-it-land-in-the-right-meeting
  mechanism is explicitly deferred (operations, 2026-08-21: "this design
  is for later, I just need a section in the MD file for that").

## Thread linking

Every ingested meeting attempts to link to a related email Thread via
`link_meeting_to_thread.py`, two strategies in order:

1. **Primary:** exact `conversation_id` match against an existing
   Thread's own `conversation_id` frontmatter.
2. **Fallback:** attendee-overlap + date-proximity heuristic against
   every Thread's own `participant_links` (resolved to real emails via
   each linked Person note) and `last_message_at`. Both an overlap bar
   (>= a configured floor shared attendees, OR exactly 1 shared attendee
   that is the entirety of the smaller side, when the 1:1 carve-out is
   enabled) and a date-proximity bar (within a configured day window)
   must clear -- a false-positive link is worse than no link, so either
   bar failing leaves the meeting unlinked, never a guess.

Both thresholds live in `.second-brain/meeting_thread_link_config.json`
(self-healing to `attendee_overlap_floor: 2`,
`one_on_one_carve_out_enabled: true`, `date_proximity_days: 7` on first
read) -- real, accessible config, never a hardcoded literal. Once a
meeting has a `thread` value, it is never reconsidered on a later rerun.

## Pitfalls

- **Attendee data (department/role/company) is Outlook GAL-derived,
  internal-only** -- exactly the same caveat email capture's own
  SKILL.md documents: populated for Exchange-resolved attendees, blank
  for anyone external. Never guessed.
- **A recurring series' identity is its own `calendar_series_id`
  (Outlook's GlobalAppointmentID), not its subject text** -- the series
  folder is resolved by SCANNING existing Meeting notes for a matching
  `calendar_series_id`, never recomputed from subject alone, so a small
  subject-text drift across occurrences (a typo fixed, a location added
  to the title) never splits one real series into two folders.
- **One-time meetings dedupe by their own deterministic `<date>
  <Subject>` path** (with a hash-of-EntryID suffix on a genuine name
  collision) -- safe to re-run `run_full_meeting_capture.py` any time;
  an already-captured event is topped up, never duplicated.

## Verification

- Report the eight result counts.
- Spot-check one one-time meeting (single file, start/end/location/
  attendees populated) and, if any recurring series exists in the
  window, its own concept note's `## History` (every occurrence
  wikilinked, dated) plus one occurrence file under `occurrences/`.
- If `threads_linked` is non-zero, open one linked meeting and confirm
  its `thread` value resolves to a real, sensible Thread.
