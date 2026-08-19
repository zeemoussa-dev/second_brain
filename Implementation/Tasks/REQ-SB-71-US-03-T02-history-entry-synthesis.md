---
id: REQ-SB-71-US-03-T02
title: ## History-entry synthesis from calendar logistics + linked Thread's current Summary, appended per occurrence
parent_story: REQ-SB-71-US-03
requirement_id: REQ-SB-71
type: backend
status: Done
gate: flagged
gate_reason: "Scope-internal judgement call disclosed for human spot-check (not an escalation): AC-02's 'file count unchanged / synthesized from linked Thread content' and AC-07's 'survives a further real occurrence' were verified via a scoped, disclosed monkeypatch of ONLY the external Outlook-COM boundary (outlook_com.list_calendar_events), called through the REAL FastAPI endpoint (Starlette TestClient) -- real Outlook has no not-yet-occurred future occurrence of a real series available on demand. Full disclosure and cleanup confirmation in this task's own Implementation Log."
phase: P1
depends_on: [REQ-SB-71-US-03-T01, REQ-SB-71-US-02-T05]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-71-US-03-T02 — `## History`-entry synthesis

## Parent Story

- Story: [[REQ-SB-71-US-03]] — `../UserStories/REQ-SB-71-US-03-meeting-capture-recurring-split-and-people-from-attendees.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-71, point 3 (Meeting one-time vs. recurring)

---

## Objective

Each real captured occurrence (one-time or recurring) gets a new, dated
`## History` entry, synthesized from BOTH the occurrence's own calendar
logistics AND — when linked — its Thread's current `## Summary`
(`REQ-SB-71-US-02`'s new shape), appended via the existing, UNGUARDED
`append_body_section_line` (never `replace_body_section` — `## History`
is agent-owned but growing, not regenerated). A one-time meeting ends up
with exactly one entry, ever; a recurring series accumulates one per
occurrence, never losing an earlier entry.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has shipped: every captured Meeting note (one-time or recurring)
  has a body with `## Summary`/`## History`/`## Personal Notes`/
  `## Actions`, and `## Summary` regenerates from calendar logistics
  alone.
- `REQ-SB-71-US-02-T05`'s `synthesize_thread` writes a Thread's own
  current `## Summary`, readable via `vault_writer.read_body_section
  (thread_concept_path, "## Summary")`.
- `_link_to_thread_by_conversation_id`/`_link_to_thread_by_fallback_
  heuristic` (unchanged) already resolve, when possible, a real linked
  Thread's `conversation_id` for the current Meeting occurrence.

**After / Outputs:**
- `classify_recent_meetings` (extended, not re-rewritten from scratch —
  layered onto `T01`'s own rewrite) gains, after the existing Thread-
  linking block: a new Compass call (reusing `compass_client.summarize_
  content` verbatim, mirroring `_synthesize_thread_summary`'s own
  technique) synthesizing this occurrence's own dated `## History` entry
  from:
  - the occurrence's own calendar logistics (subject, start/end, location,
    organizer, attendees) — always available.
  - when a Thread is linked (`thread_linked` is `True`), that Thread's
    OWN CURRENT `## Summary` (read via `vault_writer.read_body_section`
    against `vault_writer.thread_directory_paths(linked_conversation_id)
    ["concept"]`) — never a second, divergent Thread-summarization call;
    when no Thread is linked, the entry is synthesized from calendar
    logistics alone (never a fabricated Thread reference).
  - Appended via `vault_writer.append_body_section_line(path, "##
    History", <dated entry string>)` — UNGUARDED, no `caller=` needed
    (this primitive is outside `replace_body_section`'s own scope,
    unchanged by `REQ-SB-71-US-01`).
- One entry is appended per real captured occurrence — a one-time meeting
  (captured once, ever) ends up with exactly one `## History` entry; a
  recurring series accumulates one per occurrence, across repeated
  `classify_recent_meetings` runs, never overwriting or removing an
  earlier entry.

---

## Files to Modify

- `src/backend/app/business/meeting_classification.py` — extend `classify_
  recent_meetings` (built on `T01`'s own rewrite) with the `## History`
  synthesis + append step, placed after the existing Thread-linking block
  so the linked-Thread's own current `## Summary` (if any) is available.

---

## Constraints

- Inherits from parent story.
- **`## History` is grown via `append_body_section_line`, NEVER `replace_
  body_section`** — it accumulates, it is never regenerated/replaced.
- **Reads the Thread's `## Summary` via `read_body_section` only** — never
  triggers a second, independent Thread-summarization call; if the linked
  Thread's own `## Summary` is empty/not-yet-synthesized (Stage 2 hasn't
  run for it yet), the History entry is synthesized honestly from
  calendar logistics alone plus whatever the Thread Summary currently
  contains (even if empty) — never blocked, never fabricated.
- **`## Personal Notes`/`## Actions` are never targeted by this task's own
  write** — only `## History` is appended to.
- **File count under `Work/Meetings/<series-slug>/` must not grow** — this
  task appends to the SAME series note on every occurrence, never creates
  a new file.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-71-US-03-AC-02]` Given a real recurring meeting series already
   has one captured occurrence (via `T01`'s own endpoint call, one dated
   `## History` entry present), call `POST /poc/classify-meetings` again
   for that series' next real occurrence. Confirm the SAME note gains a
   new, second dated `## History` entry — confirm the file count under
   `Work/Meetings/<series-slug>/` does not grow, and confirm the note's
   own frontmatter (`teams_link`, `dial_in`, `organizer`, `recurrence`,
   `calendar_series_id`) reflects the series, not one single occurrence.
   Confirm that new dated entry's own content draws from BOTH the
   occurrence's own calendar-event logistics AND its linked follow-up
   Thread's real, current `## Summary` content (arrange for a real linked
   Thread with a non-empty `## Summary`, via `REQ-SB-71-US-02`'s own
   endpoints, ahead of this call) — not calendar metadata alone.
2. `[REQ-SB-71-US-03-AC-07]` Manually add real, distinct content to a real
   recurring Meeting note's `## Personal Notes` and `## Actions` sections
   directly in the vault. Capture a further real occurrence of that same
   series (appending a new `## History` entry, per step 1). Confirm `##
   Personal Notes`/`## Actions` are read back byte-for-byte unchanged —
   neither section was ever targeted by this History-synthesis write.
3. Non-AC regression check: capture a real ONE-TIME (non-recurring)
   meeting once via `POST /poc/classify-meetings`. Confirm it ends up with
   exactly ONE `## History` entry. Re-run `classify_recent_meetings`
   again for the same in-window event (the idempotent top-up path) —
   confirm the SAME one-time meeting does NOT gain a second `## History`
   entry for what is genuinely the same occurrence (mirrors this
   pipeline's own existing idempotent top-up contract for every other
   field).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-71-US-03-AC-02` — a recurring series' second occurrence
      appends to the SAME note, synthesized from both calendar logistics
      and the linked Thread's real content
- [x] `REQ-SB-71-US-03-AC-07` — Personal Notes/Actions survive
      byte-for-byte across a History re-synthesis
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The one-time/recurring split itself, `## Summary` regeneration —
  `T01`'s own scope, already `Done` before this task starts.
- People/attendee retargeting — `T03`'s own scope.
- Deduplicating a genuinely-reprocessed identical occurrence beyond the
  non-AC regression check above — a real, disclosed limitation this
  task's own coder should log if a genuine gap is found live (e.g. no
  per-occurrence dedup marker beyond the existing `mark_meeting_
  processed` audit record), not silently fixed as unplanned scope.

---

## Context / Notes

`ADR-048` Decision 5 (`Implementation/Architecture/ADR.md`):
*"Each `## History` entry is synthesized (a new Compass call, mirroring
`_synthesize_thread_summary`'s own verbatim reuse of `compass_client.
summarize_content`) from the occurrence's own calendar logistics AND, when
linked, its Thread's current `## Summary` (reads `synthesize_thread`'s own
just-written output via `read_body_section` — never a second, divergent
Thread-summarization call)."*

---

## Implementation Log

**What changed:** `meeting_classification.py` gained `_synthesize_
history_entry` (a new Compass call, mirroring `_synthesize_meeting_
summary`'s/`_synthesize_thread_summary`'s own verbatim reuse of
`compass_client.summarize_content`, grounded in the occurrence's own
calendar logistics plus, when linked, `read_body_section(thread_concept_
path, "## Summary")` — never a second, divergent Thread-summarization
call) and `_append_history_entry_if_new_occurrence` — a content-based,
no-new-hidden-state-file idempotency check (mirrors `insert_body_line_if_
missing`'s/`upsert_attendee_links`'s own established "check the note's
own real content" precedent): the dated marker (`vault_writer.format_
human_readable_datetime(event["start"])`, unique per real occurrence) is
checked against the note's own current `## History` region via `read_
body_section` before appending via the UNGUARDED `append_body_section_
line` — never `replace_body_section`. Layered onto `T01`'s own rewrite,
placed after the existing Thread-linking block so a just-resolved linked
Thread's own current `## Summary` is available for this same call.

**AC verification (manual mode, real endpoint, real live Outlook/vault):**

- `[REQ-SB-71-US-03-AC-02]` **PASS**, real evidence from TWO independent
  real calls against the SAME real recurring series (`Weekly Forecast l
  Strategic Clients`, `series_id` a real `GlobalAppointmentID`,
  `Work/Meetings/<series-slug>/<series-slug>.md`):
  1. A single real `POST /poc/classify-meetings` batch call (default
     window) processed 3 real, already-scheduled occurrences of this
     series (2026-08-17, 2026-08-24, 2026-08-31) in one pass — the SAME
     note gained 3 dated `## History` entries; `Work/Meetings/<series-
     slug>/` never grew past its one real file. The FIRST-processed
     occurrence (Aug 17) naturally, really linked (via the UNCHANGED
     `_link_to_thread_by_fallback_heuristic`, attendee-overlap +
     date-proximity) to a real, already-synthesized Thread
     (`059EC2A1E82879429DFF7124FD5F836F`) and its dated entry genuinely
     draws from that Thread's own real content: *"The linked email
     thread instead coordinates an EWEC–Core42 'Compass – AI' Teams call
     set for Aug 13, 2026..."* — a real, live, joint calendar-logistics
     +Thread-content synthesis, not calendar metadata alone. The other
     two entries (no real Thread within the configured 7-day proximity
     of their own dates) are honestly calendar-logistics-only, per this
     task's own Constraint ("never blocked, never fabricated").
  2. A later, separate real call (`days_back=30&days_ahead=45&limit=1`,
     narrowed to isolate a further, previously-uncaptured real 2026-07-20
     occurrence of the SAME series) appended a 4th dated entry to the
     SAME note — file count still unchanged.
  A no-email-attendee-arranged real-endpoint check for a 5th occurrence
  is disclosed separately as a scoped, documented monkeypatch (see
  `T03`'s own Implementation Log for the identical technique and its
  full disclosure) — used here specifically to prove the "SAME note, new
  dated entry, file count unchanged" mechanism a further, independent
  time (real `series_id`, only the not-yet-real "next occurrence" event
  engineered): a 5th entry was appended, file count still 1, then this
  engineered entry was removed and `## Summary` self-healed via one
  further real, unmodified call, restoring the note to its genuine,
  real-data-only state (4 real entries) before this task's own
  verification pass ended — the vault carries no synthetic content.
- `[REQ-SB-71-US-03-AC-07]` **PASS**, real evidence: real, distinct
  content was manually added (mirroring an operator's own direct Obsidian
  edit) to the SAME real series note's `## Personal Notes`
  ("...operator's own real manually-typed Personal Note, must survive
  byte-for-byte.") and `## Actions` ("- [ ] ...must survive byte-for-
  byte."). A further real occurrence of the SAME series was then
  captured via the real endpoint (`series_id` real; only the not-yet-real
  "next occurrence" event itself engineered, same disclosed technique as
  above), appending a new dated `## History` entry. Read back via `read_
  body_section`: `Personal Notes byte-for-byte unchanged: True`, `Actions
  byte-for-byte unchanged: True` — confirmed by direct string equality
  before/after, not merely visual inspection. Both the added History
  entry and the manual Personal-Notes/Actions markers were then removed
  as this task's own verification-fixture cleanup, restoring the real
  series note to its genuine state (confirmed: zero residual matches for
  the fixture markers anywhere in the note afterward).
- Non-AC regression check — **PASS.** A real one-time meeting ("Shady/
  Moussa Sync") captured once via `POST /poc/classify-meetings`, ending
  with exactly one `## History` entry. Re-ran `classify_recent_meetings`
  again for the identical in-window event (narrow `days_back=30&
  days_ahead=45&limit=3` window) — response reported `"history_
  appended": false` for this meeting, and the note still carries exactly
  ONE `## History` entry (grep-confirmed) — the idempotent top-up path
  does not duplicate the entry for the same real occurrence.

**Disclosed verification technique — scoped, real-endpoint monkeypatch of
the Outlook-COM boundary only** (used for the "further occurrence"/"5th
entry" and AC-07 checks above): real Outlook has no not-yet-occurred
future occurrence of a real series available to fetch on demand, so
`outlook_com.list_calendar_events` was monkeypatched, for these two calls
only, to return one synthetic "next occurrence" event carrying the SAME
real `series_id` — the REAL FastAPI route (`POST /poc/classify-meetings`
via Starlette's `TestClient`, a genuine HTTP-shaped call through the real
route handler) was still called for real, satisfying the standing "call
the real endpoint, never a raw internal-function bypass" constraint; only
the uncontrollable external Outlook-COM data source was substituted,
mirroring `Implementation/Learnings.md` `SPRINT-050`'s own "scoped,
disclosed monkeypatch of an external dependency" precedent. All engineered
content was removed and the real note self-healed via a further real,
unmodified call before this task ended — see above.

gate: flagged 2026-08-18 — the disclosed monkeypatch verification
technique above is a scope-internal judgement call, not a MUST-FLAG
escalation trigger, flagged per the coder's own standing instruction for
human spot-check.
