---
id: REQ-SB-08-US-01
title: Meeting notes captured from calendar sync, classified by customer via attendees, and linked to Person notes
requirement_ids: [REQ-SB-08]
requirement_section: "REQ-SB-08: Meetings Capture Pipeline"
phase: P1
status: Done
gate: clear
gate_reason: "Resolved 2026-08-12 — operator approved ADR-013 as written. T06 eligible for /plan-sprints."
sprint: "SPRINT-006"
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-08-US-01 — Meeting notes captured from calendar sync, classified by customer via attendees, and linked to Person notes

## Story

**As a** Second Brain user
**I want** every calendar meeting synced from Outlook to become a Meeting-type
note in my vault — classified by customer from its attendees' companies,
wikilinked to that customer's hub note when one matches, and linked to a
Person note for every attendee — on the same recurring schedule email capture
already runs on
**So that** my calendar shows up in my knowledge base the same way my email
already does, without me creating a single meeting note by hand, and reruns
never produce duplicate notes

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-08: Meetings Capture Pipeline* — "Calendar
  meetings are captured into the vault the same way email is (REQ-SB-03's
  pattern): synced via the Hermes-wrapped Outlook skill, classified by customer,
  and filed as Meeting-type notes, on the recurring schedule from REQ-SB-07."
  Acceptance: "Running the scheduled capture produces one Meeting-type note per
  calendar event in the sync window, classified by customer the same way email
  is, with no duplicate notes on rerun."
- **Schema already resolved** — `Implementation/Plans/
  2026-08-10-vault-taxonomy-draft.md` → "Meetings (resolved 2026-08-11)", and
  `MEMORY.md`'s matching 2026-08-11 Decision entry. This story cites and
  implements that schema; it does not redesign it. **One note per meeting, not
  a separate Meeting-Minutes type** — minutes/notes live in the same
  living-document note's body (auto-populated baseline + user-added content
  preserved, same pattern as Person/Customer notes).
  `Work/Meetings/<subject>-<date>-<entry-id-suffix>.md` (`Meetings` is a `kind`
  folder, dynamically discovered by `list_known_kinds()` — no code change
  needed for it to be found; the EntryID-suffix filename rule already fixed
  for email collisions applies identically — two meetings can share a subject
  and date):
  ```yaml
  type: Meeting
  customer: ADNOC          # derived from attendee company matches, per below
  subject: "..."
  start: 2026-08-12T10:00:00Z
  end: 2026-08-12T11:00:00Z
  location: "..."
  organizer: "..."
  tags: [customer/adnoc, kind/meeting]   # customer/ tag only if a match was found
  ```
  Body starts with the same inline-wikilink convention as Email/Person notes:
  `**Customer:** [[ADNOC]]` when an attendee's company matches a known
  customer (reusing `customer_hub_linking`'s existing mechanism directly, no
  new concept), followed by `**Attendees:** [[Person1]], [[Person2]], ...` —
  every attendee gets the exact `ensure_person_note` treatment `REQ-SB-10`
  already built for email senders (`app/business/people_extraction.py`,
  `Done`), extended from "sender" to "attendee" as the person-identifying
  event. Below that: free-form space for the user's own meeting notes/minutes
  — never programmatically rewritten once added, per the living-document rule.
- **This is REQ-SB-10-US-01's own named follow-on.** That story's Non-Goals
  explicitly flagged "Meeting-attendee-based Person backfill/capture —
  blocked on REQ-SB-08 ... which does not exist yet" and its Dependencies
  section named this exact story as the one that would "replicate this
  story's 'ensure Person note exists and is up to date' mechanism for
  meeting attendees." `people_extraction.ensure_person_note(name, email)` is
  already written generically enough (per `architecture.md`'s own note) for
  this story to call it per-attendee without changing it.
- **Customer derivation for a meeting — resolved, mechanism deferred.** Per
  the taxonomy doc: "check each attendee's company (same
  `derive_company_from_email`/`find_matching_customer` logic
  `people_extraction.py` already has) and use the first/majority match; no
  match means no `customer` tag on the meeting." This is the intended
  *behaviour*; the exact **tie-breaking mechanism** (majority vs.
  organizer-priority vs. first-match) is explicitly left to `/plan-tasks`, not
  decided here — the same style of deferral `REQ-SB-10-US-01` used for its own
  domain-parsing mechanics.
- **Genuinely new scope beyond REQ-SB-10/14's reuse-only shape: calendar
  fetch does not exist in this codebase yet.** `app/data_access/
  outlook_com.py` currently only fetches mail (`list_recent_mail`) —
  `list_recent_mail` explicitly *excludes* meeting-invite items
  (`_MEETING_MESSAGE_CLASS_PREFIX`) rather than surfacing them, and there is
  no calendar-reading function of any kind. This story requires a **new**
  Outlook COM calendar-read function (event subject/start/end/location/
  organizer/attendees) — per `MEMORY.md`'s Hermes integration-sourcing
  precedence, this should wrap/port the equivalent already-working capability
  from agentic-map's own `services/gateway/outlook_com.py`
  (`list_upcoming_events`/`list_calendar_since`), which this project never
  ported because only mail was needed until now — not build fresh from
  scratch. Which of those two semantics (or both) defines "the sync window"
  the PRD's acceptance text references is an open architecture-level question,
  not decided here (see Constraints).
- **REQ-SB-07's scheduler currently wires only the email pipeline.**
  `run_capture_and_record_completion` (REQ-SB-07-US-01, `Done`) calls
  `classify_recent_emails` directly. Whether Meetings capture rides the same
  hourly scheduler tick (added as a second call in that wrapper) or needs its
  own scheduled job/wiring is a real architecture question for `/plan-tasks`
  — noted here, not decided.
- Builds on already-`Done` infrastructure: `app/business/
  email_classification.py` / the scheduler (`REQ-SB-07-US-01`) for the
  recurring-schedule pattern; `app/business/people_extraction.py`
  (`REQ-SB-10-US-01`) for attendee Person-note creation, reused as-is; `app/
  business/customer_hub_linking.py` / `app/data_access/vault_writer.py`
  (`REQ-SB-14-US-01`) for the customer-hub-linking half, reused as-is with the
  same "only call the granular primitives after a confirmed match" carve-out
  `REQ-SB-10-US-01` already established (do not blindly call
  `ensure_hub_note_and_link` for every derived company/customer guess).
- No `html-prototype/` screen applies — like `REQ-SB-07/10/14-US-01`, this is
  backend/vault-structure work with no user-facing screen.
- This capture pipeline runs against the user's real, live Outlook calendar
  and Obsidian vault (`VAULT_PATH` in `src/backend/.env`, live Outlook desktop
  COM automation) — not a fixture/test vault or mocked calendar.

## Scoping decision (one story, not two — operator-confirmed 2026-08-11)

The PRD frames this as one acceptance outcome ("running the scheduled capture
produces one Meeting-type note per calendar event ... with no duplicate notes
on rerun") and the underlying pieces — calendar fetch, customer derivation,
note write, attendee linking, dedup — share one vertical flow the same shape
as the original email-capture pipeline (fetch → classify → write, later
wrapped by REQ-SB-07's scheduler). None of the pieces has real standalone
value on its own (a calendar-fetch function that writes nothing to the vault
satisfies no observable acceptance criterion), which is the same
no-independent-value test `REQ-SB-10-US-01`/`REQ-SB-14-US-01` used to justify
staying as one story each. On that basis this story is **one story**, decomposed
into several tasks at `/plan-tasks` (plausibly more than those two stories'
four-task shape, given the added calendar-fetch layer and the still-open
scheduler-wiring question).

**Operator confirmed this scoping call directly** (2026-08-11, in response to
the `REVIEW-QUEUE.md` entry this story was originally flagged with): stay as
one story, matching the analyst's own reasoning above. See `## Notes` for the
resolution record.

## Acceptance Criteria

### Scenario 1: A calendar meeting produces a Meeting note, classified by customer from its attendees

```gherkin
Given a calendar event exists in the capture pipeline's sync window, with one
    or more attendees, and at least one attendee's company matches an existing
    Customer hub note
When the scheduled capture run processes calendar events
Then a Meeting note is created at Work/Meetings/<subject>-<date>-<entry-id-
    suffix>.md with subject, start, end, location, and organizer populated
    from the calendar event, the kind/meeting tag present, and a
    customer/<slug> tag for the matched customer
  And the note's body includes a [[wikilink]] to that customer's hub note
  And the note's body lists the meeting's attendees as [[wikilinks]] to their
    Person notes
```
<!-- AC-ID: REQ-SB-08-US-01-AC-01 -->

### Scenario 2: Rerunning the scheduled capture does not duplicate Meeting notes

```gherkin
Given a Meeting note already exists for a given calendar event
When the scheduled capture run processes the same calendar event again
Then no duplicate Meeting note is created for that event
  And the existing note is left unchanged apart from topping up any baseline
    fields it may still be missing
```
<!-- AC-ID: REQ-SB-08-US-01-AC-02 -->

### Scenario 3: No customer tag or wikilink when no attendee's company matches a known customer

```gherkin
Given a calendar event's attendees' companies do not match any existing
    Customer hub note
When the Meeting note is created
Then the note carries the kind/meeting tag but no customer/<slug> tag
  And no wikilink to a Customer hub note is added to the note's body
  And no new Customer hub note is created
  And the note's attendees still gain [[wikilinks]] to their Person notes,
    unaffected by the absence of a customer match
```
<!-- AC-ID: REQ-SB-08-US-01-AC-03 -->

### Scenario 4: Each attendee gets a Person note, exactly as email senders already do

```gherkin
Given a calendar event has one or more attendees not yet known to the vault
When the Meeting note is created
Then a Person note is created for each attendee (per REQ-SB-10's
    ensure_person_note mechanism, extended from "sender" to "attendee") with
    at least name and email populated
  And each such Person note's company tag and customer wikilink (if
    applicable) follow the exact same rules REQ-SB-10 already established for
    email senders
```
<!-- AC-ID: REQ-SB-08-US-01-AC-04 -->

### Scenario 5: An attendee who already has a Person note is reused, not duplicated

```gherkin
Given an attendee of a calendar event already has a Person note (e.g. created
    earlier from email capture)
When the Meeting note is created
Then no duplicate Person note is created for that attendee
  And the meeting is linked to that attendee's existing Person note
  And that Person note's baseline fields are topped up (if any were missing)
    without overwriting any manually-added content, per REQ-SB-10's
    preserve-manual-edits rule
```
<!-- AC-ID: REQ-SB-08-US-01-AC-05 -->

### Scenario 6: Manually-added meeting notes/minutes survive later automated updates

```gherkin
Given a Meeting note already exists and has user-added content beyond its
    auto-populated baseline (minutes, free-form notes, or other content added
    below the auto-generated header)
When the scheduled capture run processes that same calendar event again
Then the user's manually-added content is preserved unchanged
  And only missing baseline fields (frontmatter, tags, the customer wikilink
    line, or newly-added attendee links) are topped up if needed — never
    overwriting content the user has already added themselves
```
<!-- AC-ID: REQ-SB-08-US-01-AC-06 -->

### Scenario 7: Two meetings sharing the same subject and date do not collide

```gherkin
Given two distinct calendar events share the same subject and the same date
When both are processed by the scheduled capture run
Then each produces its own distinct Meeting note (disambiguated by the
    entry-id-suffix in the filename), and neither note is silently
    overwritten by the other
```
<!-- AC-ID: REQ-SB-08-US-01-AC-07 -->

### Scenario 8: A meeting with no attendees still produces a note, without erroring

```gherkin
Given a calendar event in the sync window has no attendees (e.g. a personal
    focus block, or an event with only an organizer)
When the scheduled capture run processes that event
Then a Meeting note is still created with its subject/start/end/location/
    organizer fields populated
  And no Attendees line and no customer tag/wikilink are added
  And the capture run completes without erroring on that event
```
<!-- AC-ID: REQ-SB-08-US-01-AC-08 -->

### Scenario 9: Each occurrence of a recurring meeting produces its own Meeting note

```gherkin
Given a recurring calendar meeting has multiple occurrences falling within
    the sync window
When the scheduled capture run processes those occurrences
Then a separate Meeting note is created for each distinct occurrence
    (distinguished by its own date and entry-id-suffix), not one shared note
    for the whole series
  And rerunning the capture does not duplicate any already-captured
    occurrence's note
```
<!-- AC-ID: REQ-SB-08-US-01-AC-09 -->

### Scenario 10: Meeting capture runs on the same recurring schedule as email capture

```gherkin
Given the scheduled capture run fires per REQ-SB-07's recurring schedule
    (hourly, once on app start, and catching up a missed run)
When that scheduled run executes
Then it processes calendar events for the sync window in addition to email,
    with no separate manual trigger required for meetings specifically
```
<!-- AC-ID: REQ-SB-08-US-01-AC-10 -->

### Scenario 11: The vault owner's own email is excluded from attendee processing

```gherkin
Given a calendar event's attendee list includes the vault owner's own email
    address, alongside other real attendees
When the Meeting note is created
Then no Person note is created or updated for the vault owner's own email
  And the vault owner's own email does not participate in the meeting's
    customer derivation (their company, if any, is not considered for a
    customer match)
  And every other attendee is still processed normally (Person notes
    created/reused, customer derivation still runs against their companies)
```
<!-- AC-ID: REQ-SB-08-US-01-AC-11 -->

## Affected Screens

None — backend/vault-structure only. No `html-prototype/` screen exists or is
needed for this capability; Obsidian's own note/graph views are the surface
this story affects, not a Second Brain UI screen.

## Dependencies

- **Blocked by:** none in the hard sense — the recurring-schedule
  infrastructure (`REQ-SB-07-US-01`, `Done`), the attendee Person-note
  mechanism (`REQ-SB-10-US-01`, `Done`), and the customer-hub-linking
  primitives (`REQ-SB-14-US-01`, `Done`) all already exist and work. The one
  genuinely new dependency this story introduces is a calendar-read function
  in `app/data_access/outlook_com.py`, which does not exist yet and must be
  built as part of this story's own tasks (not a separate blocking story).
- **Related to:** REQ-SB-10 (`REQ-SB-10-US-01`) — this story is that story's
  own named follow-on, activating the "Meeting-based half" of People backfill
  its Non-Goals explicitly left blocked.
- **Related to:** REQ-SB-14 (`REQ-SB-14-US-01`) — reuses its hub-note
  file-I/O primitives and "ensure hub note exists, then link" pattern for the
  meeting-customer-match half, with the same non-blind-call carve-out
  `REQ-SB-10-US-01` established.
- **Related to:** REQ-SB-07 (`REQ-SB-07-US-01`) — this story's capture must
  ride "the recurring schedule from REQ-SB-07" per the PRD text; the exact
  wiring (same scheduler tick vs. new job) is an open question for
  `/plan-tasks`, not decided here.
- **Related to:** REQ-SB-09 (To-Do Task Capture Pipeline) — a sibling,
  not-yet-specced capture pipeline referencing the same recurring schedule;
  not built or touched by this story.
- **External:** Outlook desktop COM automation (live, real, already this
  project's established integration path for Outlook — no new external
  system, but a new *capability* — calendar read — against that same
  existing system).

## Constraints

- Follows the resolved Meetings schema exactly — `type`, `customer`,
  `subject`, `start`, `end`, `location`, `organizer`, `tags` frontmatter;
  inline-body `**Customer:**`/`**Attendees:**` wikilink lines. Not redesigned
  here.
- Attendee Person-note creation must call `people_extraction.ensure_person_note`
  as-is (already generic per `architecture.md`'s own note that it "can call it
  the same way" for meeting attendees) — not a parallel/duplicate mechanism.
- Customer derivation must reuse `people_extraction.derive_company_from_email`
  / `find_matching_customer` per attendee, per the resolved schema, and must
  not blindly call `customer_hub_linking.ensure_hub_note_and_link` for an
  unconfirmed match — the same carve-out `REQ-SB-10-US-01` established (only
  the granular `ensure_customer_hub_note`/`link_note_to_customer_hub`
  primitives, only after a confirmed match).
- The exact customer-derivation tie-break rule (majority vs.
  organizer-priority vs. first-match among multiple attendee-company matches)
  is left to `/plan-tasks`, per the taxonomy doc.
- **Operator-confirmed (2026-08-11): the vault owner's own email is excluded
  from attendee processing.** A meeting's attendee list is filtered to
  exclude the vault owner's own email address before Person-note creation
  and customer derivation run — no Person note is ever created about the
  vault owner themselves, and their own email does not participate in
  customer-match derivation. The exact mechanism for identifying "the vault
  owner's own email" (e.g. an Outlook COM current-user/mailbox-owner lookup
  vs. a new configured value) is an architecture-level decision left to
  `/plan-tasks`, not decided here — only the *behavior* (exclude, don't
  include) is resolved.
- A new Outlook Calendar COM-read function is required in `app/data_access/
  outlook_com.py` (no such function exists today — `list_recent_mail`
  explicitly excludes meeting items). Per `MEMORY.md`'s Hermes
  integration-sourcing precedence, port/wrap agentic-map's existing
  `list_upcoming_events`/`list_calendar_since` precedent rather than
  designing fresh; which one (or both) defines "the sync window," and the
  exact dedup key (EntryID vs. a recurring-series-instance identifier such as
  `GlobalAppointmentID`), are architecture-level decisions for `/plan-tasks`.
- Whether Meetings capture rides REQ-SB-07's existing hourly scheduler tick or
  needs its own scheduled wiring is left to `/plan-tasks`.
- Must respect the `api → business → data_access` layer boundary (ADR-003).
- The capture must be idempotent — rerunning must never create duplicate
  Meeting notes, duplicate attendee links, or duplicate customer wikilinks
  (Scenarios 2, 6, 9).
- This work runs against the user's real, live Outlook calendar and Obsidian
  vault (`VAULT_PATH` in `src/backend/.env`) — not a fixture/test calendar or
  vault; no-data-loss and idempotency are load-bearing, not conveniences.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-08-US-01-T01 | backend | New `list_calendar_events` calendar-read primitive | `app/data_access/outlook_com.py` | `Implementation/Tasks/REQ-SB-08-US-01-T01-calendar-read-primitive.md` |
| REQ-SB-08-US-01-T02 | backend | Meeting-note file-I/O primitives, incl. the growable Attendees-line upsert | `app/data_access/vault_writer.py` | `Implementation/Tasks/REQ-SB-08-US-01-T02-meeting-note-vault-writer-primitives.md` |
| REQ-SB-08-US-01-T03 | backend | New `meeting_classification.py` orchestration module + `Settings.self_email` | `app/business/meeting_classification.py` (new), `app/config.py`, `.env.example` | `Implementation/Tasks/REQ-SB-08-US-01-T03-meeting-classification-orchestration.md` |
| REQ-SB-08-US-01-T04 | backend | Wire meeting capture into REQ-SB-07's existing hourly scheduled run | `app/business/email_classification.py` | `Implementation/Tasks/REQ-SB-08-US-01-T04-scheduler-wiring.md` |
| REQ-SB-08-US-01-T05 | backend | New `POST /poc/classify-meetings` manual trigger endpoint | `app/api/email_poc_router.py` | `Implementation/Tasks/REQ-SB-08-US-01-T05-manual-classify-meetings-endpoint.md` |
| REQ-SB-08-US-01-T06 | backend | Replace EntryID with GlobalAppointmentID as the occurrence dedup/filename key (ADR-013, resolves ESC-002) — additive, added 2026-08-11 after the story's own Done pass | `app/data_access/outlook_com.py`, `app/data_access/vault_writer.py`, `app/business/meeting_classification.py` | `Implementation/Tasks/REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass — all 11 (`AC-01`–`AC-11`)
      verified live against the real Outlook calendar and vault; see each
      task's own Implementation Log for the per-AC evidence
- [x] Every Implementation Task above is complete (T01-T05, all `Done`)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists) — n/a, manual-mode verification per Pipeline.md's live default
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Building REQ-SB-09** (To-Do Task Capture Pipeline) — a separate,
  not-yet-specced sibling story referencing the same recurring schedule.
- **Any Second Brain UI surfacing of Meetings data** — no application screen
  is added or changed; REQ-SB-11 (Agent Activity & Error Observability) is
  the future story that will surface capture-run history/status, not this one.
- **The exact customer-derivation tie-breaking algorithm** among multiple
  attendee-company matches — architecture-level detail for `/plan-tasks` (see
  Constraints), not decided here.
- **The exact calendar-sync-window definition and dedup key** (which of
  agentic-map's `list_upcoming_events`/`list_calendar_since` semantics
  applies, or both, and the precise event-instance identifier used for
  dedup/filenames) — architecture-level detail for `/plan-tasks`.
- **The exact mechanism for identifying "the vault owner's own email"**
  (Outlook COM current-user lookup vs. a new configured value) — the
  *behavior* (exclude the vault owner from attendee processing) is resolved
  (operator-confirmed 2026-08-11, see Constraints); only the identification
  mechanism is left to `/plan-tasks`.
- **Collapsing a recurring meeting series into one note** — explicitly not
  done; each occurrence gets its own note per Scenario 9, matching the
  resolved schema's date-in-filename convention.
- **Meeting-Minutes as a separate note type** — explicitly rejected by the
  already-resolved schema; minutes live in the same Meeting note's body.
- A `Meeting` Obsidian template for manual entry — out of this story's
  automated-capture scope; would belong with `REQ-SB-15`'s
  manual-entry-templates pattern if the operator later wants one added there.

## Notes

**Prototype parity:** not applicable — this story has no screen surface.
`html-prototype/` was checked and contains no screen relevant to Meetings
capture; this is backend/vault-structure work only, same shape as
`REQ-SB-07/10/14-US-01`.

**Originally flagged (gate: flagged), now resolved (gate: clear), 2026-08-11:**

This story was flagged for two reasons, both now resolved directly by the
operator rather than guessed:

1. **Scoping call** (one story vs. splitting calendar-fetch out) — operator
   confirmed **one story**, matching the analyst's own no-independent-value
   reasoning (see "Scoping decision" above).
2. **Self/organizer-attendee interpretation gap** — operator confirmed the
   vault owner's own email is **excluded** from attendee processing (no
   Person note about the vault owner, their email doesn't participate in
   customer derivation) — see Constraints and Scenario 11.

Every other implementation-mechanism question (tie-break rule, sync-window
definition, dedup key, scheduler wiring, self-email identification
mechanism) remains an intentional architecture-level deferral for
`/plan-tasks`, in the same style `REQ-SB-10/14` used successfully — none of
these individually warrant a flag.

No material assumption was made; no `ESCALATIONS.md` entry was needed (no
PRD contradiction, no out-of-scope event — this was a scoping/interpretation
question resolved by the operator, not a requirement dispute). The
`REVIEW-QUEUE.md` entry pointing here has been removed now that both open
points are resolved.

---

**Architect pass, `/plan-tasks` step 1, 2026-08-11 — `gate: flagged`
(trigger 3, ADR-008 created).**

**Architecture scope:** `architecture.md` → Source Layout (new
`app/business/meeting_classification.py` paragraph) and Data Model →
"Meeting Notes & Calendar-Attendee Extraction (REQ-SB-08)". The
decomposer/coder are bounded by that section plus the already-Accepted
"Person Notes & Email-Sender Extraction" and "Customer Hub Notes & Graph
Linking" sections (reused as-is, not reopened) and
[ADR-008](../Architecture/ADR.md).

The five architecture-level questions this story explicitly deferred are
now resolved, each with reasoning in `architecture.md` and/or
[ADR-008](../Architecture/ADR.md):

1. **New calendar-read function.** `app/data_access/
   outlook_com.py::list_calendar_events(days_back, days_ahead, limit)` —
   ports agentic-map's `list_upcoming_events`/`list_calendar_since` COM
   mechanics (`GetDefaultFolder(9)`, `IncludeRecurrences = True`) into this
   codebase's `list_recent_mail`-shaped conventions (plain sync function,
   same CoInitialize/CoUninitialize bracketing, same best-effort
   per-item skip). **The sync window is a single bounded range around
   "now"** (`[now - days_back, now + days_ahead]`) — neither agentic-map
   semantic alone: forward-only (`list_upcoming_events`) would never
   capture an already-happened meeting worth adding minutes to; the
   watermark-based delta sync (`list_calendar_since`) would import a new
   persisted-cursor concept this project's email pipeline doesn't use and
   a documented past bug (wrong watermark field for recurring series).
   Per-event fields: `id`, `subject`, `start`, `end`, `location`,
   `organizer`, `attendees: list[{"name", "email"}]` (`To`+`Cc` merged —
   the resolved schema doesn't distinguish required/optional attendees).
   Full reasoning: ADR-008.
2. **Dedup key: Outlook `EntryID`, not `GlobalAppointmentID`.** Matches
   Scenario 9's own text ("entry-id-suffix") and agentic-map's precedent,
   which treats each `IncludeRecurrences`-expanded occurrence as a plain
   item with its own EntryID, with no additional series-identifier
   mechanism. A new `.second-brain/processed_meeting_ids.json` mirrors
   `processed_email_ids.json` exactly. One known, honestly-flagged risk
   recorded in ADR-008's Consequences: EntryID stability across recurring-
   occurrence expansion is unverified against a real recurring series in
   either codebase yet — a superseding ADR is the path if a live collision
   is ever observed, not a silent workaround.
3. **Customer tie-break: majority vote, first-encountered as tiebreak.**
   Tally each attendee's matched customer (via the unchanged
   `derive_company_from_email`/`find_matching_customer`); most matches
   wins; ties broken by attendee order (`To` then `Cc`). Chosen over
   organizer-priority (Outlook's `Organizer` property has no readily
   available email address to resolve — new, unproven COM work) and pure
   first-match (an ordering artifact, not a real signal). Recorded in
   `architecture.md` as a business-rule decision, not its own ADR — no new
   tool/framework/structural-boundary choice.
4. **Scheduler wiring: rides REQ-SB-07's existing hourly job.**
   `email_classification.run_capture_and_record_completion` gains one more
   call, `meeting_classification.classify_recent_meetings()`, alongside
   `classify_recent_emails()`, before the single
   `vault_writer.record_capture_run_completed()` call. Zero changes to
   `app/scheduling/capture_scheduler.py`. Extends ADR-005 (which
   explicitly anticipated this path) without rewriting or superseding it.
5. **Vault-owner self-email source: a new `Settings.self_email` config
   value** (`.env`-sourced, required, alongside `VAULT_PATH`/`COMPASS_*`)
   — not a dynamic Outlook COM `CurrentUser` lookup. Reasoning: this is a
   static identity fact about a single-user deployment (same category as
   `VAULT_PATH`), not open-ended vault content the "derive, don't hardcode"
   pattern protects against; a COM lookup would add a new failure surface
   (delegate mailboxes, shared accounts, multiple profiles) for something
   already known with certainty. `meeting_classification.py` filters it
   (case-insensitive) out of the attendee list before Person-note creation
   or customer derivation (Scenario 11).

**New module shape:** `app/business/meeting_classification.py` (new)
mirrors `email_classification.py`'s shape exactly (fetch → derive customer
via attendees → write note → link customer hub + attendee Person notes →
dedup), reusing `people_extraction.ensure_person_note` and
`customer_hub_linking`'s granular primitives as-is (no changes to either
module's existing public functions), per this story's Constraints.
`vault_writer.py` gains meeting-note baseline-frontmatter primitives
(mirroring the Person/Customer-hub insert-only-if-missing contract) and one
genuinely new primitive for the growable `**Attendees:** [[P1]], [[P2]],
...]` body line (a per-attendee-wikilink upsert, distinct from the
single-target `insert_body_line_if_missing` reused as-is for the
`**Customer:** [[Hub]]` line) — exact function shape left to the
decomposer/coder.

**Gating:** `gate: flagged`, `gate_reason: trigger-3 (ADR-008 created)`. A
`REVIEW-QUEUE.md` pointer has been added for a human to review ADR-008
before the build starts. Per the pipeline contract, this does **not** halt
`/plan-tasks` — the decomposer proceeds so the human reviews ADR-008 and
the resulting task breakdown together in one pass. No `ESCALATIONS.md`
entry was needed: none of the five decisions contradicts an Accepted ADR,
the PRD, or a `MEMORY.md` constraint — each is a genuine open mechanism
question the story itself deferred to this pass, resolved with recorded
reasoning and alternatives, not a dispute.

---

**Decomposer pass, `/plan-tasks` step 2, 2026-08-11 — `status: Draft →
Ready`, `gate: flagged` (unchanged).**

**AC authoring + locking:** all 11 of the analyst's untagged Gherkin
scenarios are locked as `REQ-SB-08-US-01-AC-01` through `AC-11`, in
scenario order (Scenario 11 — the vault-owner self-email exclusion the
architect resolved this pass — is `AC-11`). No wording was materially
tightened beyond the analyst's own text; every scenario was already
buildable as written.

**Task breakdown — 5 tasks, larger than REQ-SB-10/14's 4-task shape per
this story's own scoping note, driven by the new calendar-fetch layer:**

1. **T01** (`app/data_access/outlook_com.py`) — the new
   `list_calendar_events` calendar-read primitive (ADR-008 point 1).
2. **T02** (`app/data_access/vault_writer.py`) — Meeting-note file-I/O
   primitives, including the genuinely new `upsert_attendee_links`
   per-attendee-wikilink-upsert primitive `architecture.md` flagged as
   needed (distinct from the single-target `insert_body_line_if_missing`).
3. **T03** (new `app/business/meeting_classification.py` +
   `Settings.self_email`) — the orchestration module: vault-owner
   exclusion, majority-vote customer tie-break, create-vs-top-up, attendee
   Person-note reuse, granular-primitives-only customer-hub linking.
4. **T04** (`app/business/email_classification.py`) — the two-line
   scheduler-wiring change (ADR-008 point 4); zero changes to
   `app/scheduling/capture_scheduler.py`, per the ADR.
5. **T05** (`app/api/email_poc_router.py`) — a new
   `POST /poc/classify-meetings` manual trigger endpoint, mirroring
   `/poc/classify-emails`'s shape, giving both the operator and this
   story's own live verification a way to run Meetings capture on demand
   rather than waiting on the hourly tick.

T01 and T02 are independent (both `depends_on: []`); T03 depends on both;
T04 and T05 both depend only on T03 (independent of each other) — acyclic.

**AC → verification mapping:** `AC-10` (Scenario 10 — rides the same
recurring schedule) is tagged in T04, verified by starting the dev server
and confirming Meetings capture fires as a side effect of the same
app-start trigger email capture already uses, with `capture_scheduler.py`
itself untouched. The remaining ten locked ACs (`AC-01`–`AC-09`, `AC-11`)
are all tagged in T05, exercised live against the real Outlook calendar and
vault via the new manual endpoint — mirroring `REQ-SB-10-US-01-T04`'s own
shape of concentrating the bulk of a story's live verification into one
endpoint-driving task. T01/T02/T03 each carry non-AC-tagged smoke checks
only (their functions are exercised end-to-end by T04/T05), matching the
same non-AC-smoke-check precedent `REQ-SB-10-US-01-T01`/`T02` established.

**One decomposer-level design resolution, logged (not a MUST-FLAG
trigger):** `meeting_classification.classify_recent_meetings` does **not**
gate on `load_processed_meeting_ids()` as an early skip-check the way
`classify_recent_emails` gates on `load_processed_email_ids()`. Scenario
2's and Scenario 6's own Gherkin text both describe an in-window calendar
event still flowing through the top-up path on every rerun ("topping up
any baseline fields it may still be missing"), not being permanently
skipped — so the no-duplicate guarantee for Meetings comes from the
deterministic EntryID-suffixed filename plus `meeting_note_exists()`'s
create-vs-top-up branch (the same "ensure" idempotency pattern already
used for Person/Customer-hub notes), not from ID-based skipping.
`processed_meeting_ids.json` is still written every run (ADR-008's
specified file *shape*), functioning as an audit trail for future
observability (REQ-SB-11) rather than a loop gate. This does not
contradict ADR-008 (which specifies the file's shape and its role as "one
dedup mechanism," not that it must hard-skip the loop), the PRD, or any
`MEMORY.md` constraint — it is a mechanism-level resolution of the same
kind the architect pass already made five of, recorded in
`REQ-SB-08-US-01-T03`'s own Constraints/Context for the coder, not
requiring escalation.

**Status vs. gate:** all three status-advance conditions are met — every
AC is locked (11/11), every locked AC has at least one AC-tagged
verification step (`AC-01`–`AC-09`, `AC-11` in T05; `AC-10` in T04), and
`depends_on` is acyclic (T01/T02 → T03 → {T04, T05}). Story `status:`
advances `Draft → Ready`; all five tasks are set `status: Ready` in
lockstep. **`gate` stays `flagged`** (unchanged from the architect pass) —
per this role's own rule, an ADR-creation flag from step 1 is left set so
the human reviews ADR-008 and this task breakdown together in one pass; no
new MUST-FLAG trigger fired during this decomposition pass itself (no
material assumption beyond the one design resolution logged above, no new
`Draft`/unfinalised requirement relied on, no `ESCALATIONS.md` entry, no
oversized task, every locked AC is verifiable, no contradictory inputs, no
genuinely unclear breakdown). The existing `REVIEW-QUEUE.md` entry for
ADR-008 review already covers this story; no second entry was added.

---

**Product-owner pass (`/plan-sprints`), 2026-08-11.** Grouped into
**SPRINT-006** as a single-story sprint — see that sprint file for full
grouping rationale and sizing. `sprint: SPRINT-006` written above
(bidirectional link). ADR-008 was reviewed and approved by the operator
2026-08-11, per the sprint's own gating note; `gate: flagged` left
unchanged on this story per this role's own scope (resetting it is not
this role's job).

---

**Coder pass (`/implement-sprint`), 2026-08-11 — `status: Ready → Done`.**
All five tasks (T01-T05) built and verified live against the real,
configured Outlook calendar and Obsidian vault (`VAULT_PATH`), in
dependency order (T01/T02 → T03 → {T04, T05}). All 11 locked ACs
(`AC-01`-`AC-11`) verified live — 38 real Meeting notes correctly captured
under `Work/Meetings/`, correctly classified by customer via attendee
majority vote, correctly wikilinked to both the matched Customer hub note
and every attendee's Person note, idempotent across multiple reruns (byte-
for-byte unchanged where nothing should change, manually-added content
preserved), and — the story's own most-important AC — the vault owner's
own email (`<operator>@core42.ai`, sourced into `Settings.self_email`
via a one-time, read-only Outlook `CurrentUser` COM probe, not a guess or a
runtime dynamic lookup, consistent with ADR-008's own reasoning) confirmed
excluded from both Person-note creation and customer derivation on **real**
self-organized meetings, not just a throwaway construction. Full per-AC
evidence lives in each task's own Implementation Log; the fullest detail is
in `REQ-SB-08-US-01-T05`'s.

**One genuine architectural finding surfaced during live verification,
escalated per this role's own MUST-FLAG rules — not silently patched:**
ADR-008 explicitly, honestly flagged "EntryID stability across
`IncludeRecurrences = True` occurrence expansion" as unverified, naming a
superseding ADR as the required path "if observed" rather than a silent
workaround. Live verification of Scenario 9 against a real recurring
meeting found exactly that: 3 real occurrences of "Weekly Forecast l
Strategic Clients" all share one identical, full `EntryID` — not a
coincidental suffix match. Today's Meeting notes are all still correct
(the 3 occurrences happen to fall on 3 different dates, so their filenames,
which also incorporate the date, don't collide) — but the underlying
per-occurrence dedup key ADR-008 specified is empirically not unique per
occurrence, meaning a future same-date recurring collision could silently
merge two distinct meetings into one note. Full technical detail:
`ESCALATIONS.md` → `ESC-002`. `REVIEW-QUEUE.md` carries a pointer for a
human decision (superseding ADR vs. accepted known limitation) — this does
**not** block marking this story `Done`, since every locked AC passed
against the real data available today; it is prospective risk, recorded
honestly per ADR-008's own pre-authorized escalation path, not a deviation
from it.

`gate: flagged` set (superseding the earlier, now-resolved ADR-008-review
flag) with the new `ESC-002` reason — this is a genuinely new trigger from
this coder pass, not a leftover.

---

**Architect pass (out-of-cycle, operator-directed fix), 2026-08-11 —
resolving `ESC-002`. `status:` unchanged (`Done`); `gate: flagged`
(trigger-3, new ADR).**

**Operator decision, 2026-08-11: "fix this now,"** per `ADR-008`'s own
pre-authorized path for exactly this finding. New superseding ADR,
[ADR-013](../Architecture/ADR.md), replaces `EntryID` with
`AppointmentItem.GlobalAppointmentID` (a SHA-256 hash of the full string,
not a raw slice — see the ADR for why a raw slice would be equally
unsafe) as the Meeting-occurrence dedup/filename key, with a
backward-compatible legacy-`EntryID`-path fallback check so none of the
38 already-captured real Meeting notes needs migrating or renaming.
`ADR-008` itself is **not** edited — it remains `Accepted`; only its
point 2 is superseded, linked both ways.

**Architecture scope for this fix:** `architecture.md` → "Meeting Notes &
Calendar-Attendee Extraction (REQ-SB-08)" → the "Occurrence dedup key"
bullet (rewritten this pass) plus [ADR-013](../Architecture/ADR.md). The
coder implementing `REQ-SB-08-US-01-T06` is bounded by that section and
ADR alone — no other part of `architecture.md` changed.

**Why this is a new task under this same, already-`Done` story, not a new
story:** every one of this story's 11 locked ACs still passes against the
real data they were verified against — this is not a failing AC (unlike a
`BUGS.md` defect), it is a hardening fix for a risk `ADR-008` itself
pre-named and pre-authorized a superseding-ADR response to. No AC wording
is changed. Per hard rule 1 ("completed tasks and done stories are
frozen"), the story's own `status:` stays `Done` and its existing,
already-`Done` tasks (`T01`-`T05`) are not reopened or rewritten; the fix
is tracked as a new, purely additive task,
[REQ-SB-08-US-01-T06](../Tasks/REQ-SB-08-US-01-T06-global-appointment-id-dedup-key-fix.md),
`status: Ready`. `SPRINT-006` (this story's own sprint) is likewise left
`Done`/untouched — `T06` sits outside any current sprint grouping and
needs the product-owner to assign it a new `SPRINT-NNN` at the next
`/plan-sprints` pass before `/implement-sprint` can build it; that
assignment is not this pass's call to make.

**Gating:** `gate: flagged`, `gate_reason: trigger-3 (ADR-013 created)`.
The `REVIEW-QUEUE.md` entry that already existed for this story (for
`ESC-002`) is updated in place, not duplicated, to point at `ADR-013` and
`T06` for the human's review-and-approve step. No new `ESCALATIONS.md`
entry was needed for this pass itself — `ESC-002` already recorded the
finding; this pass records its resolution design (not yet built) in
`ESC-002`'s own entry, per `ESCALATIONS.md`'s existing conventions for a
"fix designed, not yet built" state.

---

**Architect pass (out-of-cycle, operator-directed fix), 2026-08-12 —
resolving `ESC-012`, a fix-that-itself-didn't-work found while building
`T06` against the ADR-013 design above. `status:` unchanged (`Done`);
`gate: flagged` (trigger-3, new ADR).**

`T06`'s own live verification found `ADR-013`'s central premise —
`GlobalAppointmentID` is guaranteed unique per occurrence — is **false on
this Outlook installation**, the exact same shape of defect `ESC-002`
already found for `EntryID`. Full detail: `ESCALATIONS.md` → `ESC-012`,
and `T06`'s own task file's Implementation Log. **Operator decision,
2026-08-12: technical path explicitly delegated** ("fix it based on
assumptions I don't have an answer for") — resolved directly, not guessed:
a new superseding ADR, [ADR-019](../Architecture/ADR.md), stops depending
on any Outlook-provided identity field for occurrence disambiguation
entirely. The new primary dedup/filename key is a SHA-256 hash of
`subject` + the occurrence's own full, precise start timestamp (already
returned by `list_calendar_events`, currently only used coarsely as the
filename's date component) — a structural uniqueness guarantee (two
distinct occurrences cannot share an identical start moment), not an
empirical claim about one specific Outlook COM property's behaviour.
`ADR-013`'s point 3 (the legacy-`EntryID`-path coexistence check) is kept
unmodified — still no migration of any of the 39 already-captured real
Meeting notes. `ADR-013`'s own middle `GlobalAppointmentID`-hash fallback
tier is dropped (dead code — confirmed live that zero real notes were ever
created under it). `ADR-013`'s own `Status:` is updated to `Superseded by
ADR-019` (points 1/2 only; point 3 reused) — `ADR-008` remains untouched,
as it already was.

**Architecture scope for this second fix:** `architecture.md` → "Meeting
Notes & Calendar-Attendee Extraction (REQ-SB-08)" → the "Occurrence dedup
key" bullet (rewritten again this pass) plus
[ADR-019](../Architecture/ADR.md) — supersedes `T06`'s own prior scope note
above (the `ADR-013` bullet/ADR pairing) for this same task. The coder
resuming `REQ-SB-08-US-01-T06` is bounded by the current "Occurrence dedup
key" bullet and `ADR-019` alone — the `ADR-013`-era version of that bullet
and `ADR-013` itself (now `Superseded by ADR-019`) no longer describe the
design to build.

**Why this stays the same task (`T06`), not a new one:** `T06` was never
`Done` — it is `Blocked`, its own build already superseded by this ADR
before it ever shipped. This is the same "additive hardening on an
already-`Done` story, story ACs never reworded" posture the first
`ADR-013` pass already established; nothing here reopens
`REQ-SB-08-US-01`'s own 11 locked ACs a second time.

**Gating:** `gate: flagged`, `gate_reason: trigger-3 (ADR-019 created)`.
The `REVIEW-QUEUE.md` entry for `T06`/`SPRINT-017` (already open for
`ESC-012`) is updated in place, not duplicated, to point at `ADR-019` and
`T06`'s redesigned spec for the human's review-and-approve step.
`ESCALATIONS.md` → `ESC-012` is flipped to `Resolved` this same pass,
naming `ADR-019` as the resolving artefact (design-level resolution — `T06`
still needs to be rebuilt and live-verified against the new design to close
it operationally, same "design vs. built-and-verified" distinction
`ESC-002` already used).

---

**Product-owner pass (`/plan-sprints`), 2026-08-12 — `T06` assigned its own
new sprint, `SPRINT-017`.** Per this story's own note above ("`T06` sits
outside any current sprint grouping and needs the product-owner to assign
it a new `SPRINT-NNN`"), and per the operator's 2026-08-12 approval of
`ADR-013` recorded in `REVIEW-QUEUE.md` ("gate: reset to clear... T06
eligible for /plan-sprints"): `REQ-SB-08-US-01-T06` is grouped into a new,
standalone single-task sprint, `SPRINT-017`
(`Implementation/Sprints/SPRINT-017-meeting-dedup-key-hardening.md`),
`status: Ready`, `gate: clear`.

**This story's own `sprint:` field (above) is deliberately left
`"SPRINT-006"`, unchanged** — it accurately reflects where this story's
original 11-AC scope (`T01`-`T05`) was built and verified. The one-story-
one-`sprint:`-field convention this project's tooling otherwise assumes
does not cleanly represent "one additional, later task on an already-`Done`
story living in a second sprint" — `SPRINT-017`'s own file is the
authoritative bidirectional link for `T06` specifically (its own `Stories
in Scope` table names this story and this task explicitly, scoped to
`T06` only). `/implement-sprint`'s own task-queue-building step (all
flat-root tasks whose `parent_story` is in the sprint, filtered to
*buildable* status) resolves this correctly in practice: `T01`-`T05` are
already `Done` and will not be re-picked-up by `SPRINT-017`; only `T06`
(`status: Ready`) is buildable there. Flagged to `REVIEW-QUEUE.md` as a
mechanism note for human awareness (not a blocker) — see the new entry
there.

**Separately noted, not resolved by this pass (outside product-owner
scope — Forbidden: tasks):** `REQ-SB-08-US-01-T06`'s own file frontmatter
still literally reads `gate: flagged` (stale — predates the operator's
2026-08-12 `ADR-013` approval recorded in `REVIEW-QUEUE.md`). This
sprint-assembly pass proceeded on the authority of `REVIEW-QUEUE.md`'s own
more-recent, dated resolution, not the stale field; the task file's own
frontmatter should be synced to `gate: clear` the next time it's touched
(e.g. by the coder at `/implement-sprint`).
