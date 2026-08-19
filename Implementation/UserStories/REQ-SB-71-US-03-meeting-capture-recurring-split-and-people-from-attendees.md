---
id: REQ-SB-71-US-03
title: Meeting Capture Redesign — one-time/recurring split, frontmatter-only logistics, People auto-extraction from attendees (nested under Customer)
requirement_ids: [REQ-SB-71]
requirement_section: "REQ-SB-71: Redesigned Email & Meeting Capture — Raw/Distilled Split, Section-Ownership Enforcement, People Auto-Extraction, File Companion Notes (points 3, 4)"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-048 created) — architect pass, 2026-08-18, superseding the prior gate: clear state. The analyst's own operator-confirmed People-fallback resolution below is unaffected/preserved (T04 may still be locked into a task on that basis) — the flag is the architect's own, added on top, per Implementation/Pipeline.md's ADR trigger. Prior flagged history (trigger-1, material-assumption-pending-confirmation, resolved 2026-08-18) preserved in git history of this file. See ## Notes."
sprint: "SPRINT-062"
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-71-US-03 — Meeting Capture Redesign — one-time/recurring split, frontmatter-only logistics, People auto-extraction from attendees (nested under Customer)

## Story

**As a** Second Brain operator
**I want** a one-time meeting to stay a single note, a recurring meeting to
stay ONE ongoing note per series that gains a new dated `## History` entry
per occurrence (never one file per occurrence), the raw calendar invite's
own boilerplate dropped entirely at capture, and every real meeting
attendee — including the people I meet that I have no email address for —
to get a real Person note auto-created and nested under their primary
Customer
**So that** a recurring meeting's own note reads as one continuous story
instead of fragmenting into a new file every week, my vault never
accumulates Teams-link legal footers and dial-in boilerplate as if they
were data, and I stop losing the people I only ever meet in person or by
video call, never by email

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-71*, points 3 (Meeting one-time vs.
  recurring) and 4 (People auto-extraction), plus the requirement's own
  standing "reachable via a real HTTP endpoint" constraint and its explicit
  "Out of scope — scheduling/autonomous triggering" block. Raised
  2026-08-18. **Supersedes `REQ-SB-56-US-01`'s current Meeting shape going
  forward** — that story stays `Done`, untouched (specs are append-only);
  this is new forward work, mirroring `REQ-SB-53`'s own SUPERSEDED
  precedent.
- **Explicitly, this requirement builds NO scheduling/autonomous
  triggering** — identical standing constraint to `REQ-SB-71-US-02`'s own
  Context. `REQ-SB-56-US-01`'s own existing scheduled `meeting-capture`
  capability stays wired exactly as it is today, untouched. Every Scenario
  below is a direct, real API call the operator (or Claude Code) makes.
- **Real code read directly to ground this story, not assumed:**
  - `app/business/meeting_classification.py::classify_recent_meetings`
    (`REQ-SB-08`/`REQ-SB-56-US-01`) — today's shape: one Meeting note per
    calendar EVENT (`resolve_meeting_note_path` keys by subject+start+
    entry_id), no one-time/recurring distinction at all, and
    `create_meeting_note_baseline` writes the raw calendar fields
    (subject/customer/start/end/location/organizer) directly, with no
    Teams-link/dial-in-boilerplate stripping.
  - **A real, direct finding worth disclosing precisely: attendee Person-
    note extraction ALREADY EXISTS today, in `classify_recent_meetings`
    itself (lines 271-279)** — `people_extraction.ensure_person_note
    (attendee.get("name") or email, email)` is called for every attendee
    with a resolvable email TODAY, `REQ-SB-56-US-01`'s own Scenario 4
    ("attendee Person-note linking") already covers this as EXISTING,
    preserved behavior. **The genuinely new gap, confirmed by direct
    reading of the exact same loop:** `email = attendee.get("email") or "";
    if not email: continue` — an attendee with NO resolvable email is
    SILENTLY SKIPPED today, never gets a Person note at all. This is the
    precise, concrete code location of the operator's own named gap
    ("people I meet that I don't have emails for") — not a vague framing,
    a literal `continue` statement in already-shipped code. This story's
    real, new work for People is narrower than "build extraction from
    scratch": (a) stop skipping the no-email case, giving it a real,
    working dedup key that isn't an email address; (b) retarget where
    EVERY Person note (both the already-working email-keyed case and the
    new no-email case) is written, from flat `Work/People/<slug>.md` to
    nested `Work/Customers/<customer-slug>/People/<person-slug>.md`.
  - `_derive_meeting_customer(attendees)` (lines 36-59, `REQ-SB-56`) —
    already-shipped "customer derivation via majority vote" across an
    event's own attendee list. This is the exact primitive this story
    reuses to determine a Person's own "primary Customer" — not a new
    algorithm.
  - `vault_writer.person_note_path(email)` (line 750) — today's dedup key
    is the lowercased email address, `Work/People/<slug-of-email>.md`, flat,
    no Customer nesting. This story retargets this primitive's own output
    path (and adds a second, name-based key for the no-email case) — see
    `## Notes` for the one genuinely open gap this retargeting surfaces.
  - `outlook_com._resolve_attendees` (lines 271-307) — confirms attendees
    are already resolved as `{"name", "email"}` pairs, the identical shape
    email participants already use — the PRD's own "same extraction logic
    extended to a second source" framing is a literal, accurate
    description of what already exists, not aspirational.
  - `REQ-SB-71-US-02`'s own new Thread shape (this batch's sibling story) —
    a recurring occurrence's `## History` entry must be synthesized "from
    BOTH the calendar event... AND its linked follow-up Thread," per the
    PRD's own point 3. This requires reading the NEW raw/distilled Thread
    shape `REQ-SB-71-US-02` builds (its own `messages/` folder and/or
    distilled `## Summary`), not the OLD single-file Thread shape — a real,
    hard dependency (see `## Dependencies`).
- **Raw calendar invite content is dropped entirely, never archived** — the
  PRD's own explicit, deliberate call: "it is noise, not data." Only
  `teams_link`, `dial_in`, `organizer`, `attendees` (wikilinks),
  `recurrence`, `calendar_event_id`/`calendar_series_id` survive, all in
  frontmatter. This is a real, deliberate departure from this project's own
  otherwise-universal "archive, never delete" discipline (`REQ-SB-59`,
  `REQ-SB-70`) — explicitly authorized by the operator for this one
  specific, named case (boilerplate, not user data), not a general
  precedent this story extends elsewhere.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A real one-time meeting produces a single note with no raw calendar-invite boilerplate

```gherkin
Given a real, non-recurring calendar event
When the operator directly calls the real meeting-capture endpoint for it
Then a single note exists at Work/Meetings/<meeting-slug>.md
  And its frontmatter carries only teams_link, dial_in, organizer,
    attendees (wikilinks), recurrence, and calendar_event_id — no raw
    invite body text (Teams-link legal footer, dial-in boilerplate) exists
    anywhere in the note, and none is archived elsewhere either
```
<!-- AC-ID: REQ-SB-71-US-03-AC-01 -->

### Scenario 2: A recurring meeting's second captured occurrence appends to the SAME note, not a new file

```gherkin
Given a real recurring meeting series already has one captured occurrence,
    at Work/Meetings/<series-slug>/<series-slug>.md, with one dated ##
    History entry
When the operator directly calls the meeting-capture endpoint again for
    that series' next real occurrence
Then the SAME note gains a new, second dated ## History entry — the file
    count under Work/Meetings/<series-slug>/ does not grow, and the
    note's own frontmatter (teams_link, dial_in, organizer, recurrence,
    calendar_series_id) reflects the series, not one single occurrence
  And that new dated entry's content is synthesized from BOTH the
    occurrence's own calendar-event logistics AND its linked follow-up
    Thread's real content — not calendar metadata alone
```
<!-- AC-ID: REQ-SB-71-US-03-AC-02 -->

### Scenario 3: A meeting attendee with no resolvable email still gets a real Person note — the named gap, closed

```gherkin
Given a real meeting attendee has no resolvable email address (the exact
    case meeting_classification.py's own existing attendee loop silently
    skips today)
When that meeting is captured via the real endpoint
Then a real Person note is auto-created for that attendee anyway, keyed by
    a real, working identifier that isn't an email address
  And the Meeting note's own attendees frontmatter wikilinks to that
    Person note, exactly as it already does for an email-resolvable
    attendee
```
<!-- AC-ID: REQ-SB-71-US-03-AC-03 -->

### Scenario 4: A meeting attendee resolved via email is nested under their primary Customer

```gherkin
Given a real meeting attendee has a resolvable email whose domain matches
    an existing real Customer (via the same majority-vote derivation
    meeting_classification.py already uses)
When that meeting is captured via the real endpoint
Then that attendee's Person note is created (or already exists) at
    Work/Customers/<customer-slug>/People/<person-slug>.md — nested under
    that Customer, not the old flat Work/People/ location
```
<!-- AC-ID: REQ-SB-71-US-03-AC-04 -->

### Scenario 5: A Person spanning multiple Customers is wikilinked from the others, never duplicated

```gherkin
Given a real Person's own note already exists nested under one real
    Customer (Work/Customers/<customer-A-slug>/People/<person-slug>.md)
When that same real person is later a meeting attendee (or email
    participant) whose derived Customer is a DIFFERENT real Customer
    (Customer B)
Then no second, duplicate Person note is created and nothing is physically
    moved — the existing note under Customer A is wikilinked from Customer
    B's own relevant note(s) instead
```
<!-- AC-ID: REQ-SB-71-US-03-AC-05 -->

### Scenario 6: A person with no derivable Customer match still gets an honest, working Person note

```gherkin
Given a real meeting attendee (or email participant) has no domain/company
    that matches any existing real Customer
When that meeting (or email) is captured via the real endpoint
Then a real Person note is still created for them — never silently
    dropped — at the existing flat Work/People/<person-slug>.md location,
    the same honest fallback this codebase already uses today for a
    company-less contact, rather than being force-nested under a Customer
    they don't genuinely belong to
```
<!-- AC-ID: REQ-SB-71-US-03-AC-06 -->

### Scenario 7: A manually-added Personal Notes/Actions entry on a Meeting survives byte-for-byte across a History re-synthesis

```gherkin
Given a real recurring Meeting note whose ## Personal Notes and ## Actions
    sections each carry a real, manually-typed entry the operator wrote
    directly in Obsidian
When a further real occurrence of that same series is captured, appending
    a new ## History entry
Then the ## Personal Notes and ## Actions sections' own manually-typed
    content survive byte-for-byte, untouched — neither section is ever
    targeted by this story's own History-synthesis write, via
    REQ-SB-71-US-01's own allow-list-checked replace_body_section
```
<!-- AC-ID: REQ-SB-71-US-03-AC-07 -->

## Affected Screens

None — backend and vault-content only. No PRD text for `REQ-SB-71` names a
UI surface. `html-prototype/vault-browser.html`/`note-detail.html`
(`REQ-SB-14-US-01`) render whatever real note/folder structure exists,
generically. `html-prototype/meeting-cockpit.html` (`REQ-SB-43-US-01`,
`Done`) is a real, disclosed area worth a regression check, not confirmed
safe here — it was built against today's one-note-per-event Meeting shape;
whether its own backend needs updating to read the new series/`##
History` shape correctly for a recurring meeting is a real, disclosed
open question left to the architect, not assumed fixed or silently broken
— see `## Notes`.

## Dependencies

- **Blocked by (hard):** `REQ-SB-71-US-01` (Section-Ownership Enforcement)
  — this story's own Meeting `## Summary`/`## History` regeneration must
  call the allow-list-checked `replace_body_section` from day one.
- **Blocked by (hard):** `REQ-SB-71-US-02` (Email Capture Redesign) — a
  recurring occurrence's `## History` entry synthesis (Scenario 2) reads
  the NEW raw/distilled Thread shape that story builds; this story cannot
  correctly synthesize from a linked Thread until that shape exists.
- **Related to:** `REQ-SB-56-US-01` (`Done`, `SPRINT-053`) — the pipeline
  this story supersedes going forward (Meeting shape only); that story's
  own file stays `Done`, unedited. Its own `_link_to_thread_by_conversation_
  id`/`_link_to_thread_by_fallback_heuristic` linking mechanism is reused,
  not rebuilt, by this story.
- **Related to:** `REQ-SB-10-US-01` (`Done`) — `people_extraction.py`'s
  existing email-participant extraction; this story retargets its own
  Person-note storage primitive (nested-under-Customer), it does not
  rebuild the extraction logic itself.
- **Related to:** `REQ-SB-08-US-01` (`Done`) — the original Meeting-capture
  Worker this story's own predecessor (`REQ-SB-56`) already extended once;
  this story extends it again.
- **Related to, soft only:** `REQ-SB-70-US-01` — the empty `Work/Meetings/`
  scaffold this pipeline writes into; not a hard code dependency.
- **External:** none new.

## Constraints

- **No scheduler wiring, no `agent_schedule_registry` entry, no cron-style
  recurring tick** — identical standing constraint to `REQ-SB-71-US-02`.
  `REQ-SB-56-US-01`'s existing scheduled capability stays untouched.
- **A recurring series is always ONE ongoing note, never one file per
  occurrence** — file count under `Work/Meetings/<series-slug>/` must not
  grow across repeated captures of the same series (Scenario 2).
- **The raw calendar invite's own boilerplate is dropped entirely, never
  archived anywhere** — a deliberate, named exception to this project's
  otherwise-universal archive-not-delete discipline (Scenario 1).
- **No meeting attendee is ever silently skipped for lack of an email
  address** — the operator's own named gap must be genuinely closed
  (Scenario 3), not merely documented as an accepted gap (which the PRD's
  own text reserves for someone who is never a participant/attendee at
  all, a structurally different case).
- **A Person is never physically duplicated or moved across Customers** —
  multi-Customer sprawl is handled by wikilink, never a second note
  (Scenario 5).
- **Meeting `## Summary`/`## History` regeneration must go through
  `REQ-SB-71-US-01`'s own allow-list-checked `replace_body_section`.**
  `## Personal Notes`/`## Actions` are literal, human-owned sections, never
  targeted by any agent write path (Scenario 7).
- **Every capability is reachable only via a real HTTP endpoint.**
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Analyst-authored starting point, non-authoritative — the decomposer's
own table at /plan-tasks supersedes this. -->

<!-- Decomposer table, /plan-tasks, 2026-08-18 — supersedes the analyst's
starting-point table above. `T03` (a new endpoint) is DROPPED — the
architect's own resolved mechanism reuses the EXISTING `/poc/
classify-meetings` endpoint unchanged (no new endpoint is built or
needed); its own reachability is verified inline in `T01`/`T02` instead.
-->

| ID | Type | Task | Files / Area | Depends On | Task File |
|---|---|---|---|---|---|
| REQ-SB-71-US-03-T01 | backend | One-time vs. recurring split — `is_recurring`/`series_id` in `list_calendar_events`, transient `teams_link`/`dial_in` extraction (never persisted), frontmatter-only logistics, `classify_recent_meetings` rewritten in place for the new shape + `## Summary` regeneration via the allow-list-checked `replace_body_section` | `app/data_access/outlook_com.py`, `app/data_access/vault_writer.py`, `app/business/meeting_classification.py`, `app/data_access/section_ownership.py` | REQ-SB-71-US-01-T01, REQ-SB-71-US-02-T02 | `../Tasks/REQ-SB-71-US-03-T01-one-time-vs-recurring-meeting-shape.md` |
| REQ-SB-71-US-03-T02 | backend | `## History`-entry synthesis (dated, growing, unguarded `append_body_section_line`) from the occurrence's own calendar logistics AND its linked Thread's current `## Summary` (`REQ-SB-71-US-02`'s new shape) | `app/business/meeting_classification.py` | REQ-SB-71-US-03-T01, REQ-SB-71-US-02-T05 | `../Tasks/REQ-SB-71-US-03-T02-history-entry-synthesis.md` |
| REQ-SB-71-US-03-T03 | backend | People — `person_note_dedup_key`, `person_note_path(dedup_key, customer)` signature change, `find_person_note_path`; `people_extraction.ensure_person_note` retargeted (checks `find_person_note_path` first, accepts `email=None`); `meeting_classification.py`'s attendee loop stops skipping no-email attendees, nests under the meeting's own derived Customer | `app/data_access/vault_writer.py`, `app/business/people_extraction.py`, `app/business/meeting_classification.py` | REQ-SB-71-US-03-T01 | `../Tasks/REQ-SB-71-US-03-T03-people-nested-under-customer.md` |

## Definition of Done

- [x] The flagged, disclosed unmatched-Customer People fallback (`## Notes`)
      has been confirmed by the operator (or explicitly overridden), before
      `/plan-tasks` locks it into a task — operator-confirmed 2026-08-18
      (see `## Notes`); `T03` locks it in
- [x] All acceptance-criteria scenarios pass — all 7 (`AC-01`..`AC-07`)
      verified live against the real Outlook calendar/vault; see `T01`/
      `T02`/`T03`'s own Implementation Logs
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Any scheduler wiring, `agent_schedule_registry` entry, or cron-style
  recurring tick** — explicitly excluded; `REQ-SB-56`'s existing scheduled
  capability stays wired exactly as-is.
- **Email capture / Thread raw-distilled split / Files convention** —
  `REQ-SB-71-US-02`'s own scope entirely; this story only READS that
  story's new Thread shape for History synthesis.
- **Backfilling already-captured Meeting or People notes onto the new
  shapes** — going-forward capture only, mirroring `REQ-SB-67-US-01`'s/
  `REQ-SB-69-US-01`'s own precedent; a backfill is a `REQ-SB-59`-style
  follow-up, not built here.
- **Archiving the dropped raw calendar-invite content anywhere** — a
  deliberate, operator-authorized exception to this project's own
  archive-not-delete discipline, not an oversight to be "fixed" later.
- **`Work/Opportunities/` integration for any Meeting/Person** — explicitly
  out of scope per the PRD's own `Work/Opportunities/` deferral.
- **Fixing Meeting Cockpit's own pre-existing series/`## History`
  regression risk** (see `## Affected Screens`) — a real, disclosed
  pre-existing risk this story's own reading surfaced, not caused by it;
  left to the architect to decide whether it's in this story's own scope
  or a separate, disclosed follow-up.

## Notes

**Prototype parity:** N/A — no `html-prototype/` screen change for the
capture pipeline itself. `vault-browser.html`/`note-detail.html` already
render vault content generically. `meeting-cockpit.html`'s own real,
disclosed regression risk against the new series shape is named above, not
silently ignored.

**The flagged, disclosed material assumption (why `gate: flagged`, trigger
1) — full reasoning:** the PRD's own point 4 text specifies TWO of the
three possible People-nesting cases explicitly: (a) a Person whose
Customer match is genuine — nest under that Customer (stated directly);
(b) a Person spanning multiple Customers — wikilink from the others, never
duplicated (stated directly, Scenario 5). **It is silent on the third
case: a Person with NO derivable/matched Customer at all** — today's
existing code already handles this gracefully in the FLAT model
(`build_person_tags` already returns `["kind/person"]` only, no company
tag, no wikilink, for exactly this case) — but the new NESTED-under-
Customer model structurally requires a Customer parent, which this case by
definition doesn't have. **This pass resolves it by falling back to
today's existing flat `Work/People/<person-slug>.md` location for this one
case** — reasoning: (1) it reuses an already-proven, already-correct
behavior rather than inventing a new bucket (e.g. a generic `Work/People/`
catch-all under the new model, or forcing an "Unsorted" Customer
directory) that the PRD never named; (2) it mirrors this project's own
repeated "honest absence over a fabricated placement" precedent
(`REQ-SB-69-US-01`'s own Scenario 11 — never a fabricated wikilink for an
unresolved relationship, applied here as "never a fabricated Customer
nesting for an unmatched Person"). **This is disclosed as a genuine,
material assumption, not silently baked in** — a real, different, equally
defensible reading exists (e.g., a dedicated `Work/People/` bucket
reserved specifically for the unmatched case under the NEW model, kept
visually distinct from the old flat shape it's superseding) that the
operator may prefer instead. `REQ-SB-71-US-03-T04`'s own Definition-of-
Done line above requires this be confirmed (or overridden) before
`/plan-tasks` locks a task around it.

**Why the no-email-attendee dedup-key question does NOT also trip a
flag:** unlike the Customer-nesting gap above, this is a mechanism-level
detail with an obvious, low-risk default direction (a name-based slug,
mirroring this codebase's own existing `_slugify` convention, with exact
collision-handling left to the architect) — not a genuinely
unclear/multiple-equally-valid PRODUCT question. The PRD's own text
explicitly wants this gap closed, not left open, so the only real choice
left is HOW, which is squarely the architect's role.

**Why everything else stays `gate: flagged` but not multiply-flagged:**
only ONE MUST-FLAG trigger fired (trigger 1, above) — this pass did not
also find a contradictory input (trigger 7 n/a — the PRD's own text is
internally consistent, it simply leaves this one case unaddressed), did
not make any OTHER material assumption (every other Scenario is grounded
directly in cited PRD text or cited, already-shipped code), and the
mechanism-level questions left to the architect (History-synthesis
mechanics, dedup-key scheme, exact endpoint routes) are ordinary
architect-role deferrals, not analyst-role gaps, mirroring `REQ-SB-69-
US-01`'s own precedent for distinguishing the two.

gate: flagged 2026-08-18 — trigger-1 fired (see above). A `REVIEW-QUEUE.md`
entry has been added; `/plan-tasks REQ-SB-71-US-03` should wait for the
operator to confirm or override the unmatched-Customer People fallback
before `T04` is locked into a task. [Analyst pass, trigger-1 — RESOLVED
2026-08-18, operator confirmed the flat-fallback resolution directly (see
frontmatter `gate_reason` history). See the architect addendum immediately
below for the SEPARATE trigger-3 flag added at `/plan-tasks`, and for
every mechanism-level detail this story's own Notes did not (and could
not, ahead of the architect pass) resolve.]

---

**Architect addendum (2026-08-18, `/plan-tasks` step 1):**

**People mechanism, building directly on the analyst's own operator-
confirmed resolution above:** `vault_writer.person_note_dedup_key(name,
email) -> str` (new) — lowercased email when one exists, unchanged; a
slug of the display name when it does not, closing the exact `if not
email: continue` gap this story's own `## Context` cites (lines 271-279).
`vault_writer.person_note_path` changes signature from `(email)` to
`(dedup_key, customer)` — nests at `Work/Customers/<slug>/People/
<slug-of-dedup_key>.md` when `customer` is a real, matched name; falls
back to the confirmed flat `Work/People/<slug-of-dedup_key>.md` otherwise.
A new `vault_writer.find_person_note_path(dedup_key) -> Path | None`
(vault-wide scan, mirrors `resolve_thread_note_path`'s own "no persisted
index" precedent) is checked FIRST by `people_extraction.ensure_person_
note` — an already-existing note (Scenario 5, nested under a DIFFERENT
Customer than this call derives) is topped up in place, never moved or
duplicated; the calling Meeting's own existing `upsert_attendee_links`
wikilink mechanism (unchanged) naturally satisfies "wikilinked from the
others" once the correct existing path is reused — no new linking
mechanism was invented. Person's own PRD-named `## Glimpse`/`## Personal
Notes` body redesign is explicitly OUT OF SCOPE for this batch (no AC
Scenario here tests Person body content) — a future Person-Synthesizer
story, not built by this one.

**Meeting mechanism:** reuses the EXISTING `POST /poc/classify-meetings`
endpoint and `"meeting-capture"` capability id unchanged — `classify_
recent_meetings` is rewritten in place; `T03`'s own "real meeting-capture
API endpoint(s)" task is therefore a NO-OP/verification task, not new
endpoint work (no separate new endpoint is built or needed). One-time
stays the unchanged `meeting_note_filename_stem` scheme; recurring becomes
`Work/Meetings/<series-slug>/<series-slug>.md`, `series-slug` keyed by
`item.GlobalAppointmentID` (a direct, deliberate reuse of the exact
per-series-constant property `ADR-013`/`ESC-012` already live-confirmed
and rejected as a per-occurrence key — see `ADR-048` Alternatives
Considered 7). `teams_link`/`dial_in` are extracted via regex from
`item.Body` TRANSIENTLY inside `list_calendar_events`; the raw body itself
never reaches this function's own returned dict, never persisted anywhere.
Body shape is IDENTICAL for one-time and recurring: `## Summary`
(regenerated, allow-list-checked, new caller `meeting_classification.
classify_recent_meetings`) + `## History` (growing, unguarded
`append_body_section_line`, one dated entry per occurrence — a one-time
meeting gets exactly one, ever) + `## Personal Notes`/`## Actions`
(human-owned).

**Architecture scope:** `Implementation/Architecture/architecture.md` →
"Vault Base Provisioning + Redesigned Email/Meeting Capture..."
§"Meeting Capture Redesign — One-Time/Recurring Split
(`REQ-SB-71-US-03`)" and §"People — Nested Under Primary Customer
(`REQ-SB-71-US-03`)" — the coder is bounded to those two subsections
(plus the shared §"Section-Ownership Enforcement" table for this story's
own new caller registration, `meeting_classification.classify_recent_
meetings`).

**ADR:** [ADR-048](../Architecture/ADR.md), Decisions 5-6 and Alternatives
Considered 8-11.

**Why `gate: flagged` now (a SEPARATE reason from the already-resolved
trigger-1 above):** trigger-3 fired — this architect pass created
`ADR-048`, which this story depends on (`REQ-SB-71-US-01` hard, `-US-02`
hard) and is itself covered by. Per `Implementation/Pipeline.md`, this
does NOT halt the pipeline — the decomposer still runs next on all four
stories. A `REVIEW-QUEUE.md` entry has been added.

---

**Decomposer addendum (2026-08-18, `/plan-tasks` step 2):**

All 7 Scenarios locked as `REQ-SB-71-US-03-AC-01`..`AC-07`, wording
unchanged from the analyst's own text. 3 tasks — the analyst's own 4-task
starting point is reduced by one: **`T03` ("real meeting-capture API
endpoint(s)") is DROPPED, not built**, per the architect's own explicit
resolution — `classify_recent_meetings` is rewritten IN PLACE behind the
EXISTING, unchanged `POST /poc/classify-meetings` endpoint, so a
dedicated new-endpoint task would be a real no-op with nothing to build or
verify. "Reachable only via a real HTTP endpoint" is satisfied for free by
the existing route; `T01`/`T02`'s own `## Tests` call that real endpoint
directly rather than a raw script, same as every other task in this
batch.

**Real, cross-story dependencies wired explicitly, per this batch's own
instruction:**

- **`T01` `depends_on: [REQ-SB-71-US-01-T01, REQ-SB-71-US-02-T02]`.** The
  first is direct — `T01`'s own rewrite of `classify_recent_meetings`
  regenerates `## Summary` via the allow-list-checked `replace_body_
  section`, needing the guard to exist first. The second is a real, found
  regression risk, not a formality: `meeting_classification.py`'s own
  EXISTING, unmodified `_link_to_thread_by_conversation_id`/`_link_to_
  thread_by_fallback_heuristic` (reused, not rebuilt, per this story's own
  `## Dependencies`) call `vault_writer.resolve_thread_note_path`/
  `list_thread_notes` directly — both retargeted by `REQ-SB-71-US-02-T02`
  to the new Thread directory shape while preserving their own PUBLIC
  signatures. Without that task landing first, this story's own Meeting-
  to-Thread linking would silently break against every NEW-shape Thread
  the moment `REQ-SB-71-US-02` ships, even though `meeting_classification.
  py` itself needs zero code change — this dependency edge is what makes
  that "zero code change" claim actually true, not accidental.
- **`T02` `depends_on: [T01, REQ-SB-71-US-02-T05]`** — `## History`
  synthesis reads the linked Thread's CURRENT `## Summary`
  (`read_body_section`) as written by `REQ-SB-71-US-02`'s own
  `synthesize_thread`; this task cannot be correctly built or verified
  against the OLD Thread shape or an unsynthesized Summary.
- **`T03` `depends_on: [T01]`** only — the People retarget extends the
  SAME `classify_recent_meetings` function `T01` already rewrote (the
  attendee loop lives inside it); sequencing avoids two tasks editing the
  same function's own body concurrently in conflicting ways. `T03` needs
  nothing from `REQ-SB-71-US-02` — `person_note_path`'s own breaking
  signature change is entirely internal to `people_extraction.py`/
  `vault_writer.py` (confirmed by direct repo-wide search: `ensure_
  person_note(name, email)`'s own PUBLIC signature is unchanged, so
  `email_classification.py`'s existing calls into it need zero
  modification).

**Task-count vs. AC-count note:** `T01` alone carries `AC-01` (the
simpler, one-time case); `T02` carries `AC-02`+`AC-07` (the more complex
recurring/History-synthesis case, genuinely separable build-and-verify
work); `T03` carries `AC-03`-`AC-06` (all four People scenarios, one
cohesive retarget). This is not an even 7-ACs-over-3-tasks split by
design — it reflects where the real, separately-verifiable pieces of work
actually are, per this batch's own instruction not to force an
artificially even count.

**Disclosed, decomposer-level scoping call (not a new MUST-FLAG trigger —
explicitly left open by both the analyst's `## Non-Goals` and the
architect, who did not resolve it in this story's own addendum unlike the
sibling `US-02` story):** `meeting-cockpit.html`'s own backend regression
risk against the new recurring-series/`## History` shape (`##
Affected Screens`) is **NOT** folded into any task in this story. It stays
a disclosed, real risk, left as a follow-up for a future story/task —
consistent with the parent story's own `## Non-Goals` ("left to the
architect to decide whether it's in this story's own scope or a separate,
disclosed follow-up"); this pass decides it is a separate follow-up, not
silently fixed or silently left broken.

**Status → `Ready`; `gate` left `flagged`** (architect's own `ADR-048`
flag, not cleared by this pass — the earlier, separate trigger-1 flag was
already resolved by the operator before this pass ran, per this story's
own frontmatter history). No new MUST-FLAG trigger fired during this
decomposer pass: no material assumption beyond what the operator already
confirmed (trigger 1 n/a); nothing `<!-- Draft -->` (trigger 2 n/a); this
pass did not itself touch `ADR-048` (trigger 3 n/a for this role); no
`ESCALATIONS.md` entry (trigger 4 n/a); not oversized — 3 tasks, smaller
than the analyst's own 4-task starting estimate (trigger 5 n/a); every
locked AC got a tagged verification step (trigger 6 n/a); no contradictory
inputs (trigger 7 n/a); the `T03`-drop and the `T01`/`T02`/`T03` split
above are both grounded directly in the architect's own resolved mechanism
and a real, cited call-site dependency, not a coin-flip (trigger 8 n/a).

**AC → verification mapping:** `AC-01` tagged in `T01`; `AC-02`, `AC-07`
tagged in `T02`; `AC-03`-`AC-06` tagged in `T03`. No locked AC is left
unverified.

gate: flagged (unchanged, architect's own `ADR-048` trigger-3) — decomposer
pass added nothing new to flag. See `REVIEW-QUEUE.md`'s existing
`REQ-SB-70-US-01 + REQ-SB-71-US-01 + REQ-SB-71-US-02 + REQ-SB-71-US-03`
entry (already covers all four stories in this batch; not duplicated
here). The earlier, separate `REQ-SB-71-US-03` People-fallback entry is
already marked `RESOLVED 2026-08-18` in that same file.

---

**Coder closing note (2026-08-18, `/implement-sprint SPRINT-062`):**
`status: Done` — all 3 tasks (`T01`/`T02`/`T03`) built and all 7 locked
ACs (`AC-01`..`AC-07`) verified live against the real, live operator
Outlook calendar and vault. A real one-time meeting produced a clean,
boilerplate-free note (`AC-01`); a real recurring series ("Weekly
Forecast l Strategic Clients") accumulated 4 real dated `## History`
entries on the SAME note across multiple real calls (file count never
grew), with one real entry genuinely drawing from a real linked Thread's
own content (`AC-02`); a real manually-added Personal Notes/Actions entry
survived byte-for-byte across a further real History append (`AC-07`).
`AC-03`/`AC-04`/`AC-05`/`AC-06` (the People scenarios) were verified via
a scoped, disclosed, real-endpoint monkeypatch of ONLY the external
Outlook-COM boundary — the real live calendar has zero real no-email-
attendee instances across a 240-day scan, and the real vault currently
carries zero notes with a real `customer` frontmatter value (a same-day
migration reset) — full disclosure, fixture design, and cleanup
confirmation in `T02`'s/`T03`'s own Implementation Logs. All fixture/
engineered artifacts were removed; the real vault carries no synthetic
content from this session's own verification work.

`gate` stays `flagged` — the pre-existing `ADR-048` trigger-3 flag is
unchanged (still awaits the human's own `ADR-048` review, shared across
all four stories in this batch). Two NEW items this pass adds to the
human's own worklist: (1) each of `T01`/`T02`/`T03`'s own disclosed
scope-internal judgement calls (not escalations — see each task's own
Implementation Log), and (2) `ESC-049` (`ESCALATIONS.md`) — a real,
disclosed, non-blocking regression this task's own reading surfaced in
`app/business/my_day.py::list_calendar_items` (reads Meeting `subject`/
`start` frontmatter this story deliberately drops), left as a follow-up,
mirroring this same batch's own `ESC-048` precedent exactly. See
`REVIEW-QUEUE.md` for the human-facing entries.
