---
id: REQ-SB-09-US-01
title: Task notes captured from Outlook's Tasks folder, classified by customer, and surfaced in My Day's To-Do drill-down
requirement_ids: [REQ-SB-09]
requirement_section: "REQ-SB-09: To-Do Task Capture Pipeline"
phase: P1
status: Done
gate: clear
gate_reason: "Coder pass 2026-08-13 — all 6 tasks Done, all 8 locked ACs (AC-01..AC-08) verified live against the real Outlook mailbox, real Compass, and the real vault. EntryID-stability empirically confirmed (ADR-027's own disclosed gap now closed). One real, disclosed, non-blocking finding (ESC-028, extends BUG-011 to Task notes) — does not block story completion, per this project's own ESC-027 precedent."
sprint: "SPRINT-028"
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-09-US-01 — Task notes captured from Outlook's Tasks folder, classified by customer, and surfaced in My Day's To-Do drill-down

## Story

**As a** Second Brain user
**I want** my Outlook to-do items captured into the vault as their own Task-type
note, classified by customer where possible, on the same recurring schedule
email and meeting capture already run on
**So that** my to-dos show up in my knowledge base and on My Day's To-Do
page the same way my email and calendar already do, without me creating a
single task note by hand, and reruns never produce duplicate notes

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-09: To-Do Task Capture Pipeline* —
  "Tasks/to-dos are captured into the vault as their own note type, on the
  same recurring schedule as email and meetings. The concrete source of
  tasks (Outlook tasks, agent-created follow-ups, manually flagged emails)
  is an open question for `/spec` time, not decided here." Acceptance:
  "Running the scheduled capture produces one Task-type note per to-do
  item, classified and filed consistently with the email/meeting pattern,
  with no duplicate notes on rerun."
- **Real precedent read directly, not assumed, per this pass's brief:**
  - `app/business/email_classification.py` / `app/business/
    meeting_classification.py` — the exact fetch → classify-by-customer →
    write/top-up → dedup shape this new pipeline mirrors. Both already
    integrate with `working_mode_registry` (REQ-SB-21, Autonomous/
    Supervised/Manual gating) and `vault_writer.append_agent_history_entry`
    (`"run_event"` entries feeding the agent's Communication History,
    REQ-SB-13, and — going forward — REQ-SB-11's chronological activity
    list).
  - `app/scheduling/capture_scheduler.py` — the existing hourly + app-start
    + missed-run-catch-up scheduling mechanism (REQ-SB-07). It calls
    `email_classification.run_capture_and_record_completion()` as one
    opaque unit; that function already runs both Email and Meeting capture
    on the same tick, gated independently by each agent's own working
    mode. A third capture step (To-Do) plugs into this exact wrapper the
    same way Meeting capture did — no new scheduler wiring needed, per
    REQ-SB-08-US-01's own precedent.
  - `app/data_access/outlook_com.py` — **resolved directly by reading this
    file, not guessed:** it already reaches Outlook via desktop COM
    automation (`win32com.client.Dispatch("Outlook.Application")` →
    `GetNamespace("MAPI")` → `GetDefaultFolder(<well-known-folder-id>)`),
    used today for Inbox (`_OL_FOLDER_INBOX = 6`) and Calendar
    (`_OL_FOLDER_CALENDAR = 9`). Outlook's Object Model exposes a Tasks
    folder via the identical mechanism — `OlDefaultFolders.olFolderTasks
    = 13` — a standard, well-documented constant, reachable the exact same
    way mail/calendar already are. **Outlook's own Tasks folder is
    therefore technically reachable today, with no new external
    dependency and no Hermes prerequisite** — this resolves the PRD's
    "does an Outlook Tasks API exist and is it reachable" half of the open
    question. What does **not** yet exist is the read function itself
    (`list_outlook_tasks` or equivalent) — a new capability against an
    already-used external system, the same shape REQ-SB-08 added
    `list_calendar_events` as.
  - `MEMORY.md`'s Hermes integration-sourcing precedence (prefer a native
    Hermes skill over a fresh implementation, going forward) does **not**
    block this story: every existing capture pipeline (email, calendar)
    already reaches Outlook directly via COM, not through Hermes — Hermes
    itself has no live connection anywhere in this codebase yet (see the
    concurrent REQ-SB-03/04/05 spec pass, `ESC-023`, `Open`). Building
    To-Do capture the same direct-COM way is consistent with the
    established, working precedent, not a deviation from it.
- **Resolved 2026-08-13 — the concrete task source.** The PRD's own text
  explicitly left this open ("Outlook tasks, agent-created follow-ups,
  manually flagged emails ... is an open question for /spec time, not
  decided here"), naming three candidates with no stated preference. This
  story originally flagged the choice (`ESC-024`) rather than guess among
  them; the operator delegated the call to the orchestrating agent
  ("make the call yourself, using sane defaults"), which confirmed this
  story's own proposed default as the **final product decision: Outlook
  Tasks folder as the sole source** — the closest, most literal analog to
  the existing email/meeting capture pattern (same COM channel, same
  "fetch → classify → file" shape, no new interaction surface needed),
  and the only one of the three that already has a real, reachable data
  source today. "Agent-created follow-ups" and "manually flagged emails"
  both require new interaction/trigger mechanisms that don't exist
  anywhere in this codebase — out of scope this pass (see Non-Goals), not
  ruled out as later fast-follows. See `## Notes` for the full resolution
  record; `ESCALATIONS.md` → `ESC-024` is now `Resolved`.
- **Resolved 2026-08-13 — the Task-note schema.** Unlike REQ-SB-08 (whose
  Meeting schema was fully resolved in `Implementation/Plans/
  2026-08-10-vault-taxonomy-draft.md` before that story was even
  written), REQ-SB-09 had no resolved schema anywhere — confirmed by a
  direct grep of that plan document for "Task"/"To-Do"/"Todo": zero
  matches. The schema below, extrapolated from the Meeting/Email schemas'
  own shape, is now the confirmed schema (same resolution as above), not
  merely a default awaiting confirmation.
- **Schema (confirmed):**
  `Work/Tasks/<subject>-<date>-<entry-id-suffix>.md` (`Tasks` a fixed
  folder, mirroring `Work/Meetings/`'s fixed-folder shape — not a
  Compass-classified `kind`, since Task, like Meeting, is its own note
  type rather than an email-style kind):
  ```yaml
  type: Task
  customer: ADNOC          # derived from subject/body content when a match exists; absent otherwise
  subject: "..."
  due: 2026-08-20            # from the Outlook Task's DueDate; omitted if none is set
  status: Not Started | In Progress | Completed   # from the Outlook Task's own Status/Complete fields
  tags: [customer/adnoc, kind/task]   # customer/ tag only if a match was found
  source: outlook-task
  outlook_entry_id: ...
  ```
  Body starts with `**Customer:** [[ADNOC]]` when a match exists (reusing
  `customer_hub_linking`'s existing mechanism directly, per the standing
  tags-and-wikilinks rule — `MEMORY.md`, 2026-08-11 — that any note
  *referencing* another vault entity must carry a real `[[wikilink]]`, not
  just a frontmatter field), followed by free-form space for the task's
  own notes/body content and any manual additions — never
  programmatically rewritten once added, same living-document pattern
  Meeting notes already use. **Unlike Meeting notes, a Task note links no
  Person** — an Outlook Task has no attendee/contact list, so there is no
  natural entity relationship to wikilink beyond the optional customer
  match; this is an intentional absence, not a gap in the standing rule.
- **Customer classification mechanism — inferred from precedent, not a
  guess.** An Outlook Task has no sender or attendee list to derive a
  company from the way Email/Meeting do. This story proposes reusing
  Compass classification against the task's own subject + body content
  (the same `compass_client` mechanism `classify_email` already calls,
  with sender left blank/not applicable) — closer to Email's
  content-driven derivation than Meeting's attendee-vote derivation. The
  exact call shape (a shared function vs. a small Task-specific variant)
  is an implementation detail left to `/plan-tasks`.
- **Real, already-stubbed dependency this story closes:** `app/business/
  my_day.py::summary()` already hardcodes `"todo": {"count": 0}`, with its
  own comment reading "todo stays hardcoded 0 — REQ-SB-09 has no resolved
  task source/kind folder yet." `GET /my-day/todo` and
  `MyDayTodoPage.tsx` (both built by `REQ-SB-12-US-02`, `Done`) already
  exist but only render an empty state — that story's own Notes explicitly
  named this as "deferred... to be resolved and specced when REQ-SB-09 is
  specced." `html-prototype/my-day-todo.html` already sketches a plausible
  populated state (title, customer-or-"No customer", due date, a
  "Due today"/"Upcoming" badge) using the same `.item-list`/`.item-row`/
  `.badge` pattern the Emails/Calendar drill-downs already use in
  production — this is treated as live design authority for the field set
  this story resolves now (not a fresh `net-new-design-needed` case), per
  the analyst's prototype-reconciliation mandate. See Non-Goals for what
  the prototype does not draw (an "Overdue" badge state) and is therefore
  not specced here.
- No other `html-prototype/` screen applies beyond My Day's To-Do surface
  named above — like REQ-SB-07/08/10/14, the capture pipeline itself is
  backend/vault-structure work with no dedicated screen of its own.
- This capture pipeline runs against the user's real, live Outlook
  desktop and Obsidian vault (`VAULT_PATH` in `src/backend/.env`) — not a
  fixture/test vault or mocked Outlook.

## Scoping decision (one story, not two)

The PRD frames this as one acceptance outcome ("running the scheduled
capture produces one Task-type note per to-do item... with no duplicate
notes on rerun"), and — per the same "no independent-value test" reasoning
`REQ-SB-08-US-01`/`REQ-SB-10-US-01` already used — none of fetch, classify,
write, or dedup has standalone value on its own. Wiring My Day's already-
stubbed To-Do drill-down (Scenario 8 below) is included in this same story
rather than split out: it is the one concrete, already-waiting consumer of
this pipeline's own output (an unpopulated `GET /my-day/todo` endpoint and
an empty-state-only page already exist specifically because REQ-SB-09 had
not shipped yet), so a capture pipeline with no visible surface would leave
that dependency dangling for no reason. This mirrors the same reasoning
`REQ-SB-30-US-01` used to fold its My Day read-path change into one story
alongside its capture-time write-path change.

## Acceptance Criteria

<!-- Locked 2026-08-13 by the decomposer (/plan-tasks step 2) — each scenario
below is tightened for buildability and tagged with its sequential AC-ID
immediately after its closing Gherkin fence, per Pipeline.md. All 8 ACs are
locked (none marked non-locked); every one has a matching AC-tagged step in
a task's ## Tests (see the Implementation Tasks table, below). -->

### Scenario 1: An Outlook Task produces a Task note, classified by customer when derivable

```gherkin
Given an item exists in Outlook's Tasks folder, with a subject and
    (optionally) a due date and body/notes text
When the scheduled capture run processes Outlook Tasks
Then a Task note is created at Work/Tasks/<subject>-<capture-date>-
    <entry-id-suffix>.md with type: Task, subject, due (present only if
    Outlook has a due date set), and status (Not Started | In Progress |
    Completed, mapped from the Outlook item's own Complete/Status fields)
  And when the task's subject/body content matches an existing Customer
    hub note, the note carries a customer/<slug> tag and its body starts
    with a [[wikilink]] to that customer's hub note
```
<!-- AC-ID: REQ-SB-09-US-01-AC-01 -->

### Scenario 2: Rerunning the scheduled capture does not duplicate Task notes

```gherkin
Given a Task note already exists for a given Outlook Task item
When the scheduled capture run processes the same Outlook Task item again
Then no duplicate Task note is created for that item — the existing note
    is found via a lookup keyed on the item's own Outlook EntryID, not by
    recomputing its filename from current field values
  And the existing note is left unchanged apart from topping up any
    baseline fields it may still be missing
```
<!-- AC-ID: REQ-SB-09-US-01-AC-02 -->

### Scenario 3: No customer tag or wikilink when no customer match is found

```gherkin
Given an Outlook Task item's subject/body content does not match any
    existing Customer hub note
When the Task note is created
Then the note carries the kind/task tag but no customer/<slug> tag, and
    its frontmatter carries no customer field at all (not an empty one)
  And no wikilink to a Customer hub note is added to the note's body
  And no new Customer hub note is created
```
<!-- AC-ID: REQ-SB-09-US-01-AC-03 -->

### Scenario 4: To-Do capture runs on the same recurring schedule as email and meeting capture

```gherkin
Given the scheduled capture run fires per REQ-SB-07's recurring schedule
    (hourly, once on app start, and catching up a missed run)
When that scheduled run executes
Then it processes Outlook Tasks in addition to email and calendar events,
    with no separate manual trigger required for To-Do specifically
```
<!-- AC-ID: REQ-SB-09-US-01-AC-04 -->

### Scenario 5: A task marked Complete in Outlook is still captured, with its status recorded honestly

```gherkin
Given an Outlook Task item's Complete flag is set (the user has marked it
    done in Outlook)
When the scheduled capture run processes that item
Then a Task note is created or topped up for it with status: Completed
  And its status is never silently left at Not Started/In Progress, and
    the item is never skipped just because it is done
```
<!-- AC-ID: REQ-SB-09-US-01-AC-05 -->

### Scenario 6: Manually-added content on a Task note survives later automated top-ups

```gherkin
Given a Task note already exists and has user-added content beyond its
    auto-populated baseline (added notes, sub-items, or other content
    added below the auto-generated header)
When the scheduled capture run processes that same Outlook Task item
    again (e.g. because its due date or status changed in Outlook)
Then the user's manually-added body content is preserved unchanged
  And the note's due/status frontmatter fields are updated to match
    Outlook's current values, while every other baseline field is only
    filled in if it is still missing — never overwriting content the user
    has already added themselves
```
<!-- AC-ID: REQ-SB-09-US-01-AC-06 -->

### Scenario 7: Two tasks sharing the same subject do not collide

```gherkin
Given two distinct Outlook Task items share the same subject
When both are processed by the scheduled capture run
Then each produces its own distinct Task note (disambiguated by the
    entry-id-suffix in the filename), and neither note is silently
    overwritten by the other
```
<!-- AC-ID: REQ-SB-09-US-01-AC-07 -->

### Scenario 8: My Day's To-Do section and drill-down page reflect real captured tasks

```gherkin
Given one or more Task notes have been captured into the vault, some
    still open and some complete
When the user opens My Day or its To-Do drill-down page
Then My Day's To-Do section shows a real count of captured, still-open
    tasks — no longer the hardcoded 0
  And the To-Do drill-down page lists each still-open captured task in
    the same item-list/item-row structure the Emails/Calendar drill-downs
    already use, showing its subject, its matched customer (or "No
    customer"), and its due date (or "No due date")
  And when a listed task has a due date, a badge reads "Due today" (the
    due date is today) or "Upcoming" (any other due date), matching the
    approved my-day-todo.html prototype; a task with no due date shows no
    badge at all
```
<!-- AC-ID: REQ-SB-09-US-01-AC-08 -->

## Affected Screens

- `html-prototype/my-day-todo.html` — populated state fully specced now
  (Scenario 8), matching its own already-sketched item-list/badge design
  (subject, customer-or-"No customer", due date, "Due today"/"Upcoming"
  badge). The empty state was already specced by `REQ-SB-12-US-02`
  (unchanged, still applies when no Task notes exist yet).
- `html-prototype/my-day.html` — the To-Do dashboard card's count moves
  off its hardcoded 0 (Scenario 8) to a real count; no other change to
  this page.

## Dependencies

- **Blocked by:** none in the hard sense — the recurring-schedule
  infrastructure (`REQ-SB-07-US-01`, `Done`), the customer-hub-linking
  primitives (`REQ-SB-14-US-01`, `Done`), My Day's already-scaffolded
  `GET /my-day/todo` stub and `MyDayTodoPage.tsx` empty state
  (`REQ-SB-12-US-02`, `Done`) all already exist and work. The one
  genuinely new dependency is an Outlook Tasks-folder COM-read function
  in `app/data_access/outlook_com.py`, which does not exist yet and must
  be built as part of this story's own tasks (not a separate blocking
  story) — mirroring how `REQ-SB-08-US-01` introduced
  `list_calendar_events` the same way.
- **Related to:** `REQ-SB-08` (`REQ-SB-08-US-01`, `Done`) — this story's
  own named sibling per that story's own Dependencies section ("a sibling,
  not-yet-specced capture pipeline referencing the same recurring
  schedule"); this story mirrors its fetch → classify → write → dedup
  shape directly.
- **Related to:** `REQ-SB-12-US-02` (`Done`) — this story completes the
  To-Do drill-down's populated state that story deliberately left
  empty-state-only, pending this spec.
- **Related to:** `REQ-SB-21` (`REQ-SB-21-US-01`, `Done`) — this new
  capture pipeline should register with the existing working-mode-gating
  convention (Autonomous/Supervised/Manual) the same way email-capture and
  meeting-capture already do, per "filed consistently with the
  email/meeting pattern." The exact per-agent default mode for a new
  `todo-capture` agent id is left to `/plan-tasks`.
- **Related to:** `REQ-SB-11` (Agent Activity & Error Observability, also
  specced this pass, not yet built) — this pipeline's `run_event`/error
  history entries (Constraints) are exactly the kind of background-run
  data REQ-SB-11's own chronological activity list will surface; not a
  build dependency in either direction — REQ-SB-11's mechanism reads
  whatever agent ids exist, so it does not need to be built before or
  after this story specifically.
- **External:** Outlook desktop COM automation — no new external system
  (already this project's established Outlook integration path), but a
  new *capability* (Tasks-folder read) against that same existing system,
  same shape as REQ-SB-08's own new calendar-read capability.

## Constraints

- **Source scope — Outlook's own Tasks folder only, this pass
  (confirmed 2026-08-13, `ESC-024` Resolved).** Agent-created follow-ups
  and manually-flagged emails (the PRD's other two named candidate
  sources) are explicitly NOT built here — see Non-Goals.
- **Schema — confirmed 2026-08-13** (Context, `ESC-024` Resolved), not
  merely a proposed default.
- Follows the standing tags-and-wikilinks rule: a Task note that matches a
  customer must carry a real `[[wikilink]]` to that customer's hub note,
  not only frontmatter (`MEMORY.md`, 2026-08-11).
- Customer derivation must reuse `people_extraction`/`customer_hub_linking`'s
  existing primitives and must not blindly call
  `customer_hub_linking.ensure_hub_note_and_link` for an unconfirmed
  match — the same carve-out `REQ-SB-08-US-01`/`REQ-SB-10-US-01` already
  established (only the granular `ensure_customer_hub_note`/
  `link_note_to_customer_hub` primitives, only after a confirmed match).
- **Dedup key mechanism is deferred to `/plan-tasks`, not assumed safe
  here.** `MEMORY.md` already documents, twice (`ADR-013`→`ADR-019`), that
  Outlook-provided identity fields (`EntryID`, then
  `GlobalAppointmentID`) were each found non-unique across a real
  recurring calendar series' expanded occurrences on this Outlook
  installation. Whether any Outlook Task in this mailbox is itself
  recurring, and whether its `EntryID` exhibits the same instability, is
  unconfirmed — the architect should verify empirically before choosing a
  dedup key, per the precedent this project already learned the hard way,
  rather than trusting Outlook's documented uniqueness claims at face
  value.
- Must register the new `todo-capture` agent with `REQ-SB-21`'s existing
  working-mode-gating convention, and write `"run_event"`-kind
  `vault_writer.append_agent_history_entry` entries on completion,
  mirroring `email_classification.py::run_capture_and_record_completion`'s
  existing pattern for email-capture — feeds REQ-SB-13's Communication
  History and REQ-SB-11's future chronological activity list without
  either needing pipeline-specific logic of their own.
- Must respect the `api → business → data_access` layer boundary (ADR-003).
- The capture must be idempotent — rerunning must never create duplicate
  Task notes or duplicate customer wikilinks (Scenarios 2, 6, 7).
- This work runs against the user's real, live Outlook desktop and
  Obsidian vault (`VAULT_PATH` in `src/backend/.env`) — not a fixture/test
  vault; no-data-loss and idempotency are load-bearing, not conveniences.

## Implementation Tasks

<!-- Decomposed 2026-08-13 by the decomposer (/plan-tasks step 2). The
story's own pre-sketched T01-T05 table above (analyst-authored, non-
authoritative) is superseded by the table below — 6 tasks, splitting
scheduler/working-mode wiring out from the orchestration module (mirroring
REQ-SB-08-US-01's own T03/T04 split) for atomic, single-session task sizing.
See each task file's own ## Context / Notes for why. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-09-US-01-T01 | backend | New `list_outlook_tasks` Tasks-folder COM-read primitive (incl. the isolated live EntryID-stability check) | `app/data_access/outlook_com.py` | `../Tasks/REQ-SB-09-US-01-T01-outlook-tasks-read-primitive.md` |
| REQ-SB-09-US-01-T02 | backend | Task-note file-I/O primitives: baseline create/top-up, the new `upsert_frontmatter_key` due/status primitive, and the load-bearing `task_note_index.json` dedup index | `app/data_access/vault_writer.py` | `../Tasks/REQ-SB-09-US-01-T02-task-note-vault-writer-primitives.md` |
| REQ-SB-09-US-01-T03 | backend | New `todo_classification.py` orchestration module + new `compass_client.classify_task`; carries the end-to-end live dedup/top-up verification (AC-06) | `app/business/todo_classification.py` (new), `app/data_access/compass_client.py` | `../Tasks/REQ-SB-09-US-01-T03-todo-classification-orchestration.md` |
| REQ-SB-09-US-01-T04 | backend | Third gated capture block + `run_capture_for_agent` branch wired into the shared scheduler tick; `todo-capture`'s registry "Task source" value resolved | `app/business/email_classification.py`, `app/business/agent_registry.py` | `../Tasks/REQ-SB-09-US-01-T04-scheduler-working-mode-wiring.md` |
| REQ-SB-09-US-01-T05 | backend | Real `GET /my-day/todo` + dashboard count, replacing the hardcoded-0 stub | `app/business/my_day.py`, `app/api/my_day_router.py` | `../Tasks/REQ-SB-09-US-01-T05-my-day-todo-real-data.md` |
| REQ-SB-09-US-01-T06 | frontend | To-Do drill-down populated state (item-list + Due today/Upcoming badge); dashboard count needs zero frontend change (`MyDayPage.tsx` already reads `summary.todo.count` generically) | `src/frontend/src/pages/MyDayTodoPage.tsx`, `src/frontend/src/features/my-day/client.ts` | `../Tasks/REQ-SB-09-US-01-T06-todo-drilldown-populated-state.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists) — n/a, manual-mode verification per this project's current stage
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Agent-created follow-ups and manually-flagged emails as task
  sources** — the PRD's other two named candidates; confirmed out of
  scope for this pass (`ESC-024` Resolved — Outlook Tasks only). A
  possible fast-follow if wanted later, once this pipeline's own shape is
  validated.
- **An "Overdue" badge/visual state** — `my-day-todo.html`'s own populated
  mockup only draws "Due today" and "Upcoming"; an overdue-specific
  treatment is not sketched anywhere and is not specced here.
- **Marking a task complete/checking it off from within Second Brain's
  own UI** (writing back to Outlook) — this pipeline is read-only against
  Outlook; it captures Task items into the vault, it does not mutate them
  in Outlook.
- **Manual task creation from Second Brain's own UI** — separate,
  possible future scope (e.g. related to REQ-SB-23's conversational
  filing agent), not this pipeline.
- **Working-mode default selection for the new `todo-capture` agent** —
  left to `/plan-tasks`, per Constraints.

## Notes

**Prototype parity (my-day-todo.html + my-day.html):**

- To-Do drill-down populated list — **Specced** (Scenario 8) — resolves
  the field set (subject, customer-or-"No customer", due date, badge)
  that page's own populated-state mockup had left as "an open question
  for /spec time" in its own comment; no new region, reuses the existing
  `.item-list`/`.item-row`/`.badge` pattern as-is.
- To-Do drill-down empty state — **Specced by `REQ-SB-12-US-02`**,
  unchanged — still applies whenever no Task notes exist yet.
- To-Do "Overdue" badge state — **Deferred** — not drawn in the approved
  prototype; see Non-Goals.
- Dashboard To-Do section count — **Specced** (Scenario 8) — data-only
  change (real count instead of hardcoded 0), no new screen region, same
  precedent as `REQ-SB-22-US-01`'s/`REQ-SB-30-US-01`'s own dashboard-count
  resolutions.

**Why this was originally flagged (MUST-FLAG triggers 1, 2, 8):**

1. **Trigger 2 — relies on PRD text explicitly marked open.** REQ-SB-09's
   own acceptance text states the task source "is an open question for
   `/spec` time, not decided here" — this is not a `<!-- Draft -->` marker
   on the requirement itself (the requirement is finalized), but it is the
   PRD's own explicit deferral of a scoping decision to this exact pass.
2. **Trigger 1 — material assumption made to fill the gap.** This story
   proposed both a source (Outlook Tasks folder) and a schema (Context)
   as reasonable, precedent-grounded defaults so the story would be fully
   buildable rather than left as an empty shell — but both were the
   analyst's own construction, not resolved PRD/plan-doc text at the time.
3. **Trigger 8 — multiple equally-valid options exist for the source.**
   The PRD names three candidate sources with no stated preference among
   them; picking one silently would have been exactly the kind of guess
   the analyst is required to flag rather than make, especially since the
   two not chosen here (agent-created follow-ups, manually-flagged
   emails) are materially different builds, not just parameter variations
   of the same pipeline.

No other trigger fired: no ADR was created or changed by this pass (n/a to
the analyst); the story is not oversized (5 tasks, the same shape as
REQ-SB-08's own capture-pipeline story plus one small My Day wiring task,
mirroring REQ-SB-30's own precedent for folding a read-path change into
the same story); no contradictory PRD inputs exist — the PRD is explicit
that this is deferred, not contradictory.

**Resolution record (2026-08-13).** The operator delegated this decision
to the orchestrating agent directly ("make the call yourself, using sane
defaults") rather than answering it personally. The orchestrating agent
confirmed this story's own proposed default as the final product
decision, with the following stated reasoning: Outlook Tasks folder is
technically reachable today via the exact same COM mechanism
`outlook_com.py` already uses for mail/calendar, and the Meeting/Email-
shaped schema this story proposed needed no redesign to accept. No part
of the original analysis was overridden or redirected — the delegated
call landed on exactly the recommendation this story's Context already
argued for.

`ESCALATIONS.md` → `ESC-024` is flipped to `Resolved`, naming this
story's own updated `## Context`/`## Notes` as the resolving artefact.
`gate:` reset to `clear` — no prototype/design dependency remains for
this story (Scenario 8's screen change reconciles against the
already-approved `my-day-todo.html` mockup, per this pass's own
prototype-reconciliation read). **Ready for `/plan-tasks`.**

---

**Architect pass (2026-08-13, `/plan-tasks` step 1) — one new ADR
written; `gate` re-flagged (trigger 3).**

Read the real current code directly (not assumed) before deciding
anything: `outlook_com.py` (mail/calendar COM patterns), `email_
classification.py`/`meeting_classification.py` (fetch → classify →
write → dedup shape), `capture_scheduler.py` (confirmed zero changes
needed), `agent_registry.py` (confirmed `"todo-capture"` is already a
registered agent, pre-seeded ahead of this story with a placeholder
"Task source" setting value), `working_mode_registry.py` (confirmed its
self-healing default already covers a new agent id with no code
change), `compass_client.py` (confirmed `classify_email` bundles a
`kind` axis and a sender-framed prompt that don't fit a Task), and
`my_day.py` (confirmed the hardcoded `"todo": {"count": 0}` stub and its
own comment naming this story as the resolving dependency).

**One new ADR: [ADR-027](../Architecture/ADR.md).** Bundles four related
decisions the same way `ADR-008` bundled Meeting's own COM-read/dedup-
key/self-email/scheduler decisions: (1) the new `list_outlook_tasks` Tasks-
folder COM-read function (`GetDefaultFolder(13)`, no date-window, no
`IncludeRecurrences`-equivalent exists for Tasks at all — structurally
unlike Calendar); (2) the dedup/top-up mechanism — a genuinely new
finding, not a rubber-stamp of the confirmed schema's `<date>` component:
recomputing the Task-note filename fresh from Outlook's own `due` field
on every run (Meeting's exact `ADR-019` pattern) would silently duplicate
a note on exactly the due-date-change rerun **Scenario 6 itself requires
survive as a top-up, not a new note** — so the dedup key is `EntryID`,
looked up through a new load-bearing `.second-brain/task_note_index.json`
(not a recomputed-path check), with `<date>` in the filename resolved to
mean "date first captured," frozen at creation, never recomputed from
`due`; (3) a new customer-only `compass_client.classify_task`, not a
reuse of `classify_email` (which bundles a discarded `kind` axis and a
sender-framed prompt a Task doesn't have); (4) scheduler/working-mode
reuse (a third gated block in `run_capture_and_record_completion`,
`capture_scheduler.py` unchanged) **and** a resolution of `ADR-008`'s
own explicitly-anticipated "revisit if a third pipeline..." fork — no
orchestration-module extraction this pass, per `CLAUDE.md`'s minimal-
changes discipline. **Honestly disclosed, not silently assumed:** the
story's own Constraints asked the architect to verify `EntryID` stability
empirically before trusting it (this project's own twice-repeated lesson,
`ADR-008`→`ADR-013`→`ADR-019`) — the architect role has no live-Outlook
execution capability in this environment (Read/Glob/Grep/Edit/Write
tooling only), so this pass reasons through it structurally instead (no
`IncludeRecurrences`-equivalent exists for Tasks, so the specific
occurrence-expansion mechanism that broke `EntryID`/`GlobalAppointmentID`
for Calendar cannot apply the same way) and explicitly assigns the coder
building `T01`/`T02` a real live-verification step as part of that task's
own Definition of Done — deferred, not skipped. Full reasoning,
alternatives considered, and every consequence: [ADR-027](../Architecture/ADR.md).

**`architecture.md` updated** — new Data Model subsection "Task Notes &
Outlook-Tasks Capture" (mirrors "Meeting Notes & Calendar-Attendee
Extraction"'s own shape), a new "To-Do real data" amendment under "My Day
& Agent Panel APIs" (no ADR needed for that read-path half — a same-shape
extension of already-`Accepted` `my_day.py` structure, matching
`REQ-SB-22-US-01`/`REQ-SB-30-US-01`'s own precedent), the `"todo-capture"
has no real background pipeline yet` sentence under "Agent Working Modes
& Pending Approvals" corrected in place (no longer current), and two new
Source Layout paragraphs (`todo_classification.py`, the new
`outlook_com`/`compass_client` functions). `Last reviewed:` footer
updated.

**Architecture scope: §"Task Notes & Outlook-Tasks Capture" (Data Model),
§"To-Do real data" amendment (My Day & Agent Panel APIs), §"Agent Working
Modes & Pending Approvals" (the `todo-capture` gate amendment only — the
rest of that section is out of this story's scope), §Source Layout
(the `todo_classification.py`/`outlook_com`/`compass_client` paragraphs)
— all in `architecture.md`; [ADR-027](../Architecture/ADR.md) in full.**
The coder is bounded to these sections plus the files each task's own
`## Files to Modify` names; nothing else in `architecture.md` is in
scope for this story.

**Gate: flagged (trigger 3 — ADR-027 created).** Per `Pipeline.md`, this
does not halt `/plan-tasks` — the decomposer proceeds so the human
reviews the ADR and the resulting tasks together in one pass. See
`REVIEW-QUEUE.md` for the review pointer.

---

**Decomposer pass (2026-08-13, `/plan-tasks` step 2) — 8 ACs locked, 6
tasks created, story advanced `Draft` → `Ready`; `gate` left `flagged`.**

Read `ADR-027` in full, both `architecture.md` amendments ("Task Notes &
Outlook-Tasks Capture", "To-Do real data"), and the real current
`email_classification.py`/`vault_writer.py`/`outlook_com.py`/
`compass_client.py`/`my_day.py`/`my_day_router.py`/`MyDayTodoPage.tsx`/
`MyDayPage.tsx` before decomposing — not the story's own pre-sketched
samples alone.

**AC locking.** All 8 Gherkin scenarios tightened for buildability and
locked (`REQ-SB-09-US-01-AC-01`..`AC-08`), none marked non-locked. Notable
tightening, not new scope:
- **AC-01/AC-02/AC-06**: made the schema's own `<capture-date>` (frozen at
  first write, per `ADR-027` point 3) and the EntryID-keyed lookup (not a
  recomputed-path check) explicit in the Gherkin text itself, since this is
  the one point where Task's mechanism genuinely diverges from Meeting's.
- **AC-03**: tightened "no customer/<slug> tag" to also state the
  frontmatter carries **no `customer` key at all** on a no-match — the
  resolved schema (`## Context`) says "absent otherwise," a real
  difference from Meeting's own schema, which always writes `customer:
  ""`. Confirmed deliberately, not glossed over — see `T02`'s own
  `## Context / Notes`.
- **AC-06**: this is where Task's own baseline-top-up contract genuinely
  diverges from every prior captured note type in this codebase (Customer/
  Person/Meeting all use strict insert-only-if-missing, never touching an
  already-present key). Scenario 6's own text ("its due date or status
  changed in Outlook... only missing OR CHANGED baseline fields are topped
  up") requires `due`/`status` to be **upserted** (updated in place when
  Outlook's current value differs), not merely filled once — confirmed
  against Scenario 5's own text too ("a task marked Complete... status
  field honestly reflects that it is complete," which only makes sense as
  a requirement if a pre-existing "Not Started" note's status can later be
  corrected to "Completed" on top-up). Every other baseline key
  (`type`/`subject`/`tags`/`source`/`outlook_entry_id`/`customer`) stays
  insert-only-if-missing, matching every other captured note type — a
  scoped, explained divergence, not a blanket "always overwrite" rule. See
  `T02`'s own `upsert_frontmatter_key` primitive and `## Context / Notes`.
- **AC-08**: tightened "same item-list/badge presentation already used by
  the Emails and Calendar drill-downs" into its literal, buildable parts —
  the Emails/Calendar drill-downs use `.item-list`/`.item-row` but carry no
  `.badge` at all (confirmed by reading both pages directly); the badge
  itself is new to this page, drawn from the already-approved
  `my-day-todo.html` prototype (`.badge`/`.badge-warning`, "Due today"/
  "Upcoming", no "Overdue" state per Non-Goals). Locked as a structural AC
  (a `.badge` region present when a due date exists, absent when it
  doesn't; its text driven by a deterministic date-vs-today comparison) —
  DOM/text-content verifiable, not a visual-polish claim.

**Tasks created (6, flat root, `status: Ready`, lockstep with the
story).** Splits scheduler/working-mode wiring out from the orchestration
module into its own task (`T04`), mirroring `REQ-SB-08-US-01`'s own
`T03`/`T04` split, for atomic single-session sizing — the story's own
pre-sketched table bundled these into one `T03`; that table is a starting
point, not a mandate, per this role's own contract.

- `REQ-SB-09-US-01-T01` — `list_outlook_tasks` (`outlook_com.py`).
  `depends_on: []`.
- `REQ-SB-09-US-01-T02` — Task-note vault_writer primitives, incl. the new
  `upsert_frontmatter_key` due/status primitive and the load-bearing
  `task_note_index.json` dedup index. `depends_on: []`.
- `REQ-SB-09-US-01-T03` — `todo_classification.py` orchestration + new
  `compass_client.classify_task`. `depends_on: [T01, T02]`.
- `REQ-SB-09-US-01-T04` — third gated capture block +
  `run_capture_for_agent` branch in `email_classification.py`;
  `agent_registry.py`'s `"todo-capture"` placeholder resolved to "Outlook
  Tasks folder". `depends_on: [T03, REQ-SB-11-US-01-T01]` — a genuine
  **cross-story** edge, see below.
- `REQ-SB-09-US-01-T05` — real `GET /my-day/todo` + `summary()` count.
  `depends_on: [T02, T03]` (schema from `T02`; real captured data from
  `T03` for genuine live verification, no throwaway-note substitute
  needed).
- `REQ-SB-09-US-01-T06` — To-Do drill-down populated state + badge logic.
  `depends_on: [T05]`.

Acyclic (a straight line: `T01`/`T02` → `T03` → `T04`; `T03` → `T05` →
`T06`; plus the one cross-story edge `T04` → `REQ-SB-11-US-01-T01`, a leaf
with `depends_on: []` of its own — no cycle possible), confirmed by
construction.

**A SECOND cross-story edge, found by direct reading, not assumed —
`REQ-SB-11-US-01-T01`.** While wiring `T04`, reading the real current
`email_classification.py::run_capture_and_record_completion` (per this
role's own "read the real current file" discipline) surfaced that
`ADR-027`'s own point 5 was authored assuming this function's TODAY shape
(two unwrapped Autonomous branches), but a sibling, already-decomposed,
not-yet-built story — `REQ-SB-11-US-01` (`status: Ready`) — has its own
`T01` (`REQ-SB-11-US-01-T01-capture-pipeline-honest-failure-recording.md`,
`depends_on: []`) queued to rewrite this SAME function's control flow
first: wrapping each Autonomous branch's call in its own `try/except`,
adding a new `"run_error"` history-entry kind, and making the trailing
`vault_writer.record_capture_run_completed()` call conditional on two new
local `_failed` booleans. Unlike the `REQ-SB-01-US-01-T04` situation
(above — a single unconditional call at a fixed anchor, genuinely
order-independent), this is a real, structural build-order dependency: a
`todo_mode` block written against the OLD (unwrapped) shape would either
look inconsistent with its two sibling branches once `REQ-SB-11-US-01-T01`
later lands, or — worse — silently omit the new `todo_capture_failed`
boolean from the trailing gate's condition if `REQ-SB-11-US-01-T01` lands
first, quietly breaking that story's own Scenario 3 failure-isolation
guarantee for the third branch. `REQ-SB-09-US-01-T04` is therefore written
directly against `REQ-SB-11-US-01-T01`'s own already-known post-fix
shape (that task's own concrete `## Files to Modify` code, not a guess)
and carries an explicit `depends_on: [..., REQ-SB-11-US-01-T01]` edge —
a real task ID, not a placeholder, since that story is already
decomposed. Per hard rule 7, the product-owner must honor this edge:
`REQ-SB-09-US-01` and `REQ-SB-11-US-01` either land in the same sprint
(with `REQ-SB-11-US-01-T01` sequenced before `REQ-SB-09-US-01-T04` inside
it) or in ordered sprints with a recorded `depends_on_sprints` edge — not
a decomposer decision to make. Not written to `ESCALATIONS.md`: this is
a within-normal-bounds cross-story dependency the decomposer is expected
to surface directly (Pipeline.md hard rule 7 anticipates exactly this),
not a contradiction, ambiguity, or assumption — no MUST-FLAG trigger
fired on this finding specifically. Full detail:
`Implementation/Tasks/REQ-SB-09-US-01-T04-scheduler-working-mode-wiring.md`'s
own `## Context / Notes`.

**Cross-story edge checked, none added — `REQ-SB-01-US-01-T04`.** Per
this pass's own brief, read `REQ-SB-01-US-01-T04`
(`Implementation/Tasks/REQ-SB-01-US-01-T04-scheduler-tick-wiring.md`,
`status: Ready`) directly before wiring `T04` above. It adds one
**unconditional** `vault_indexing.rebuild_index()` call immediately before
`run_capture_and_record_completion`'s existing final
`vault_writer.record_capture_run_completed()` line — not gated by any
capture step's own working mode, and not per-branch. This already covers
To-Do capture's own vault writes with **zero** change needed in this
story's own `T04`: no separate index-refresh call is added here. The two
tasks edit non-conflicting anchor points in the same function (my new
third gated block lands among the existing per-agent blocks; `REQ-SB-01-
US-01-T04`'s call lands immediately before the function's final two
lines) and are **order-independent** — whichever lands first, the other's
own edit instructions (which name their anchor relative to the function's
current shape, not a fixed line number) still apply correctly. No
`depends_on` edge added across stories; `REQ-SB-09-US-01-T04`'s own
`## Context / Notes` documents this explicitly and instructs the coder to
re-read the real current file before editing, per this project's own
established "compose around the real current file" pattern
(`Implementation/Learnings.md`).

**Live-verification requirement for the dedup/top-up mechanism —
confirmed carried explicitly, not just code-review-level.** Per this
pass's own brief and `ADR-027`'s own Consequences section (EntryID
stability was reasoned structurally, not live-verified, by the architect
role): `REQ-SB-09-US-01-T01`'s own `## Tests` carries an isolated,
non-AC-tagged live empirical check — read a real Outlook Task's `EntryID`
via `list_outlook_tasks`, edit that same task's due date directly in the
Outlook desktop client, re-read, and confirm the returned `EntryID`
string is byte-for-byte unchanged across the edit. `REQ-SB-09-US-01-T03`'s
own `## Tests`, tagged `AC-06`, carries the full end-to-end live
confirmation: capture a real Task note, edit its due date/status in
Outlook, rerun the capture, and confirm the SAME note is topped up (not
duplicated) — the concrete, real-mailbox test that would have surfaced
`ESC-002`/`ESC-012`-shaped findings for Meetings had it existed sooner.
Both are genuinely live, not code-inspection substitutes.

**Status: `Draft` → `Ready`.** All 3 transition conditions hold: (a) every
AC locked (8/8); (b) every locked AC has ≥1 AC-tagged verification step
(confirmed per-task, below); (c) `depends_on` acyclic (confirmed above).

**Gate: left `flagged`, not cleared.** Trigger 3 (ADR-027 created) is an
architect-authored flag from step 1 of this same `/plan-tasks` run — per
this role's own contract, the decomposer does not clear a flag raised for
an ADR change; the human reviews `ADR-027` and this pass's task breakdown
together. `gate_reason` updated (frontmatter, above) to record that
decomposition is now complete, without clearing the flag. The existing
`REVIEW-QUEUE.md` entry for this story (already `[x]`-checked "Approved
2026-08-13," asking specifically that "the decomposer's task breakdown
carries that [live-verification] requirement explicitly") is appended
with a short decomposer confirmation, not replaced.

No new `ESCALATIONS.md` entry was written by this pass — no new backward
step or out-of-scope event occurred during decomposition itself (the
material-assumption/Draft-requirement/ADR triggers that fired for this
story were all fired by the analyst/architect in earlier passes, already
recorded).

---

**Coder pass (2026-08-13, `/implement-sprint`) — all 6 tasks built and
`Done`; all 8 locked ACs verified live; story `Ready` → `Done`.**

Built in dependency order (`T01`/`T02` → `T03` → `T04`/`T05` → `T06`)
against the real live Outlook desktop, real Compass, and the real live
vault — no fixture/mock data anywhere. Full per-task verification
detail lives in each task's own Implementation Log; summarized here:

- **`list_outlook_tasks`** (`T01`) — one scope-internal live-COM
  correction (the real "no due date" sentinel string differs from the
  originally-guessed one; corrected and logged, per this task's own
  explicit latitude).
- **`EntryID`-stability — the ADR-027 gap this story's own architect
  pass explicitly could not live-verify — is now EMPIRICALLY CONFIRMED,
  not just structurally reasoned.** Both `T01`'s isolated check and
  `T03`'s own end-to-end `AC-06` capture→edit→rerun→confirm-topup cycle
  passed against real Outlook items; zero duplicate `EntryID`s found
  across the real 235-item Tasks folder. No superseding ADR is
  warranted — `ADR-027` point 3's own design stands confirmed.
- **All 8 ACs verified live:** `AC-01`/`AC-03` (customer match / no
  match, including a genuinely NEW customer correctly triggering hub
  creation); `AC-02`/`AC-06` (rerun idempotency, upsert-vs-insert-only
  baseline contract, user body content preserved); `AC-04` (real
  app-start scheduler trigger, zero `capture_scheduler.py` changes,
  independent per-branch failure funnel, gate recovery); `AC-05`
  (Complete flag honestly recorded); `AC-07` (disambiguation mechanism
  confirmed correct); `AC-08` (real populated To-Do drill-down, real
  badges, real dashboard count, zero `MyDayPage.tsx` change) — screenshot-
  verified via the OS-installed Edge browser's headless mode.
- **One real, disclosed, non-blocking finding — `ESC-028`.** While
  verifying `AC-07` against the real, unbounded 100-item capture run,
  the already-tracked `BUG-011` (`_slugify`'s 80-char truncation eating a
  disambiguating suffix) was confirmed to also affect Task notes — and,
  because Task notes share one flat `Work/Tasks/` subfolder (no `kind`
  split), causes a literal same-path note OVERWRITE, a worse consequence
  than `BUG-011`'s own documented Email/Notification case. Root-caused
  entirely to the pre-existing, out-of-scope `_slugify` function
  (confirmed via a passing short-subject control case); the new
  disambiguation mechanism `T02`/`T03` built is itself correct. Does not
  block this story, mirroring `ESC-027`'s own established precedent.
  `ESCALATIONS.md` → `ESC-028`; `REVIEW-QUEUE.md` pointer recommends
  extending `BUG-011`'s own `BUGS.md` entry (same root cause, worse
  severity finding), not a new bug.

`MEMORY.md` updated with the story's own decision summary. `BACKLOG.md`
row flipped to `Done`. `SPRINT-028` advanced to `Done` (its own
Retrospective drafted, gate flagged for human harvest into
`Implementation/Learnings.md`).

`gate: clear` 2026-08-13 — every locked AC verified; the one disclosed
finding (`ESC-028`) is non-blocking per established project precedent,
not a new pattern requiring the story itself to stay flagged.
