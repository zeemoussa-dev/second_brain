---
id: REQ-SB-43-US-01
title: Meeting Cockpit — 3-panel prep-and-live workspace with attendee chips, a unified multi-agent Expert chat, and explicit-save on-the-spot research
requirement_ids: [REQ-SB-43]
requirement_section: "REQ-SB-43: Meeting Cockpit — Expert-Assisted Meeting Workspace"
phase: P1
status: Done
gate: flagged
gate_reason: "coder pass (SPRINT-040) — 2 scope-internal judgment calls logged for human spot-check on T03/T08 (a real vault_writer.py frontmatter-parser limitation worked around within task scope; reconciliation against the real approved prototype). No new ESCALATIONS.md entry."
sprint: SPRINT-040
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-43-US-01 — Meeting Cockpit — 3-panel prep-and-live workspace with attendee chips, a unified multi-agent Expert chat, and explicit-save on-the-spot research

## Story

**As a** Second Brain user
**I want** clicking a meeting to open a dedicated 3-panel workspace where I
can see who's in the meeting, bring in whichever Expert agents I need
help from into one shared chat, and do quick on-the-spot research that I
explicitly choose to save or discard
**So that** I can prep for and stay present during a meeting with the
right help at hand, without losing anything useful I looked up along the
way, and without anything being filed into my vault that I didn't
explicitly approve

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-43: Meeting Cockpit —
  Expert-Assisted Meeting Workspace* — "Clicking a meeting (from My Day's
  Calendar) opens a dedicated 3-panel workspace, usable both to prep
  before the meeting and to keep open live during it. The right panel
  shows the meeting's info, with each attendee rendered as a clickable
  chip that links to their existing Person note in the vault. The middle
  panel is a chat where the user can bring in Expert agents as needed —
  every Expert brought in sits in one shared, unified conversation
  thread. The left panel lists the user's available Agents (to bring into
  that chat) and this meeting's own quick-research results. From the
  chat, the user can trigger on-the-spot research and, for each result,
  explicitly choose whether to save it into the vault or discard it."
  Acceptance: "Clicking a meeting item, before or during that meeting,
  opens a 3-panel Meeting Cockpit: the right panel shows the meeting's
  info with every attendee as a clickable chip linking to their Person
  note (when one exists); the middle panel is one unified chat thread in
  which every Expert the user has brought in can respond; the left panel
  lists the user's available Agents (to bring into the chat) and this
  meeting's own quick-research results. From the chat, the user can
  trigger on-the-spot research, and each research result offers an
  explicit choice to save it as a new note wikilinked to the Meeting
  note, or discard it."
- **PRD breadcrumb (2026-08-13, operator-directed, verbatim, NOT
  re-decided here):** "Once I click on a meeting that means I need the
  Help of the Map, The System Check the info of the meeting, Allow me to
  go to the meeting with the Experts that I need their help in that
  meeting and allow me to do a quick research on the spot and I choose
  either to add that to the Vault or no... it will be 3 Panels, Info in
  the right with People in the meeting clickable as Tags or Chips so I
  can know about who are they in the Vault the middle is a Chat Window
  based on the Agent the left in my Agents and the Researches I created
  and I can Bring Experts as needed to the meeting." Clarified via
  requirements-gathering session, verbatim decisions: (1) one workspace
  serves both pre-meeting prep and live, during-the-meeting use — no
  separate mode; (2) the middle panel is a single unified multi-agent
  chat thread, not one thread per brought-in Expert; (3) the left panel's
  research list is scoped to this one meeting, not a cross-meeting
  personal library; (4) saving a quick-research result creates a new,
  standalone note wikilinked to the meeting's own Meeting note
  (`REQ-SB-08`'s existing note type), matching this project's
  established one-note-per-thing pattern (Person/Meeting/Research
  notes), rather than being appended into the Meeting note itself.
- **Decision (1) directly resolves the entry-point/prep-vs-live open
  question, so it is not re-guessed here.** The PRD's own context flags
  "whether prep-mode and live-mode need any different data is unresolved"
  as genuinely open — but the operator's own decision (1) settles the
  product question one level up: there is no separate mode at all, so
  the "different data" question does not arise. Clicking a meeting item
  opens the identical Meeting Cockpit regardless of whether the meeting
  is upcoming or currently in progress — no "meeting currently in
  progress" signal is needed from the capture pipeline for this story to
  be buildable.
- **Distinct from, not a replacement for, `REQ-SB-20`'s Hub routing
  (PRD's own explicit clarification, not re-derived here):**
  `REQ-SB-20`'s cross-section routing is agent-initiated — an agent
  autonomously asks its Hub for help outside its own knowledge. This
  requirement's "bring Experts as needed" is user-initiated — the person
  using Second Brain explicitly chooses which Expert(s) join this
  meeting's chat. Both mechanisms coexist unchanged; this story does not
  modify `REQ-SB-20-US-01`'s own behavior.
- **Genuinely open, left to `/spec`/`/plan-tasks`, per the PRD's own
  context — resolved here where a safe, defensible default exists,
  flagged where it does not:**
  - **How a unified multi-agent chat attributes each reply to the
    specific Expert that produced it.** Resolved to the minimal,
    necessary behavior for "unified thread, multiple Experts" to be
    coherent at all: every reply is visibly attributed to the specific
    Expert that produced it (Scenario 6, below) — without this, a
    "unified" thread with more than one Expert brought in would be
    unreadable. The exact visual mechanism (name badge, avatar, colored
    label, etc.) is left to `/design`, not decided here.
  - **What an attendee chip does when no Person note exists yet for that
    attendee.** Resolved conservatively, by direct precedent: this
    project's standing honesty posture (never fabricate or imply a link
    to something that doesn't exist, `REQ-SB-33-US-01`/`ADR-011`) means a
    chip for an attendee with no Person note renders as a plain,
    non-clickable "no note yet" indicator (Scenario 3, below) rather than
    a broken link. **Whether it should instead open a create-Person-note
    flow is a genuinely separate, additive product decision, not
    resolved here** — flagged below, and left as a candidate follow-on,
    not built in this pass. Note also that `REQ-SB-08`'s own Meeting
    capture pipeline already calls `people_extraction.ensure_person_note`
    for every real attendee at capture time (`architecture.md` →
    "Meeting Notes & Calendar-Attendee Extraction"), so this "no note
    yet" case is expected to be rare for real, pipeline-captured
    meetings — but not structurally impossible (e.g. a meeting captured
    before an attendee-Person-note mechanism existed, or a future
    manually-entered meeting), so the cockpit must still handle it
    honestly rather than assume it never happens.
  - **Whether `REQ-SB-21`'s working-mode gating (Autonomous/Supervised/
    Manual) still applies to a brought-in Expert's actions inside this
    cockpit, or whether being explicitly user-invited changes that.**
    **Genuinely unclear, not resolved here** — flagged below. `REQ-SB-21`'s
    own Manual-mode resolution ("only a direct human ask... no agent can
    trigger an action on a Manual-mode agent") did not contemplate "a
    human explicitly brought this agent into a shared chat" as a trigger
    category at all; whether that counts as "asked" for gating purposes,
    and whether Supervised's mutating-action-proposes-and-waits gate still
    applies once inside this cockpit, is a real product judgment call. No
    Constraint or Scenario below asserts either answer.
  - **The on-the-spot research mechanism itself** (reusing `REQ-SB-36`'s
    existing `web-research` Skill directly, or a new capability).
    Deliberately left open at the mechanism level — the scenarios below
    describe only the externally observable behavior ("the user can
    trigger on-the-spot research from the chat, and each result offers
    an explicit save-or-discard choice"), not which underlying skill or
    call produces the result. `/plan-tasks` decides the concrete
    mechanism.
- **Depends on:** `REQ-SB-08-US-01` (Meeting notes, **Done**) — a Meeting
  note must exist to click into and to wikilink a saved research result
  to. `REQ-SB-10-US-01` (Person notes, **Done**) — the attendee chip's
  link target. `REQ-SB-18-US-01`/`REQ-SB-20-US-01` (Sections/Experts,
  both **Done**) — Sections and Expert-type agents must exist as a real
  concept to be "brought in." `REQ-SB-36` (the web-research Skill this
  likely reuses for on-the-spot research — `REQ-SB-36-US-01`, **Done**;
  `REQ-SB-36-US-02`'s own delegated-chain composition is a separate
  concern, not a hard dependency here).
- **No `html-prototype/` screen covers this.** `my-day-calendar.html`'s
  meeting rows are a flat, non-clickable `.item-row` list (confirmed by
  direct inspection) — there is no click affordance, no 3-panel layout,
  no attendee-chip concept, no multi-agent chat concept, and no
  quick-research list/save-or-discard concept anywhere in the approved
  prototype. A `/design` pass is needed before this story can proceed
  past `/plan-tasks` — see the flag below.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then
edge cases and error states. Do NOT add AC-IDs — the decomposer assigns them
at /plan-tasks. These scenarios describe only the externally observable
behaviour the PRD's own Acceptance text (plus the operator's own resolved
decisions, both cited in Context above) commits to; they deliberately do not
assert a specific chat-attribution visual mechanism, a specific working-mode
interaction for brought-in Experts, or a specific on-the-spot research
mechanism — all three are left open per the Context above. -->

### Scenario 1: Clicking a meeting item opens the 3-panel Meeting Cockpit, before or during the meeting

```gherkin
Given the user is viewing My Day's Calendar list
When the user clicks a meeting item, whether that meeting is upcoming or
    currently in progress
Then a 3-panel Meeting Cockpit opens for that specific meeting
  And the workspace is identical regardless of whether the meeting is
    upcoming or in progress — there is no separate prep-mode/live-mode
```

<!-- AC-ID: REQ-SB-43-US-01-AC-01 -->

### Scenario 2: The right panel shows the meeting's info with attendee chips linking to existing Person notes

```gherkin
Given the Meeting Cockpit is open for a meeting whose attendees include at
    least one person with an existing Person note in the vault
When the user views the right panel
Then the meeting's info (at least subject, time, and customer if known)
    is shown
  And every attendee with an existing Person note is rendered as a
    clickable chip that links to that Person note
```

<!-- AC-ID: REQ-SB-43-US-01-AC-02 -->

### Scenario 3: An attendee with no existing Person note renders a plain, non-clickable chip

```gherkin
Given the Meeting Cockpit is open for a meeting with an attendee who has
    no existing Person note in the vault
When the user views the right panel's attendee chips
Then that attendee's chip renders as a plain, non-clickable indicator —
    never a broken or fabricated link to a note that doesn't exist
```

<!-- AC-ID: REQ-SB-43-US-01-AC-03 -->

### Scenario 4: The left panel lists the user's available Agents to bring into the chat

```gherkin
Given the Meeting Cockpit is open
When the user views the left panel
Then the user's available Agents are listed, from which the user can
    choose which to bring into this meeting's chat
```

<!-- AC-ID: REQ-SB-43-US-01-AC-04 -->

### Scenario 5: Bringing an Expert into the chat adds it to the one shared, unified conversation thread

```gherkin
Given the Meeting Cockpit is open with its chat thread empty or already
    containing messages
When the user brings an Expert agent into the chat from the left panel
Then that Expert becomes able to respond in the same one shared chat
    thread — no new, separate thread is created for that Expert
When the user brings a second, different Expert into the same chat
Then both Experts respond within that identical single shared thread,
    not two parallel threads
```

<!-- AC-ID: REQ-SB-43-US-01-AC-05 -->

### Scenario 6: Each Expert's reply in the shared thread is attributed to the specific Expert that produced it

```gherkin
Given two or more Experts have been brought into the Meeting Cockpit's
    chat thread
When any of those Experts responds in the thread
Then that reply is visibly attributed to the specific Expert that
    produced it, distinguishable from a reply by any other Expert in the
    same thread
```

<!-- AC-ID: REQ-SB-43-US-01-AC-06 -->

### Scenario 7: The left panel's quick-research results are scoped to this one meeting

```gherkin
Given the user has generated quick-research results in more than one
    different meeting's own Meeting Cockpit
When the user views one specific meeting's Meeting Cockpit left panel
Then only that meeting's own quick-research results are listed — results
    generated while working on a different meeting are not shown
```

<!-- AC-ID: REQ-SB-43-US-01-AC-07 -->

### Scenario 8: Triggering on-the-spot research from the chat produces a result the user must explicitly save or discard

```gherkin
Given the Meeting Cockpit's chat is open
When the user triggers on-the-spot research from the chat
Then a research result is produced and shown to the user
  And the result offers an explicit choice to save it into the vault or
    discard it — it is not automatically saved or automatically
    discarded
```

<!-- AC-ID: REQ-SB-43-US-01-AC-08 -->

### Scenario 9: Saving a research result creates a new standalone note wikilinked to the Meeting note

```gherkin
Given an on-the-spot research result is shown to the user with a pending
    save-or-discard choice
When the user chooses to save it
Then a new, standalone note is created (not appended into the Meeting
    note's own body) and wikilinked to this meeting's own Meeting note
  And the new note appears in this meeting's own quick-research results
    list in the left panel
```

<!-- AC-ID: REQ-SB-43-US-01-AC-09 -->

### Scenario 10: Discarding a research result creates no note

```gherkin
Given an on-the-spot research result is shown to the user with a pending
    save-or-discard choice
When the user chooses to discard it
Then no note is created in the vault
  And the discarded result does not appear in this meeting's own
    quick-research results list
```

<!-- AC-ID: REQ-SB-43-US-01-AC-10 -->

### Scenario 11: Bringing an Expert into this cockpit does not change REQ-SB-20's own Hub-routing behavior

```gherkin
Given an Expert agent has been user-brought into a Meeting Cockpit's
    chat
When that same Expert, independently of this cockpit, is later matched
    as the target of a different agent's REQ-SB-20 Hub-routed
    cross-Section request
Then that separate Hub-routing behavior is unaffected by having been
    brought into this or any Meeting Cockpit — the two mechanisms remain
    independent
```

<!-- AC-ID: REQ-SB-43-US-01-AC-11 -->

## Affected Screens

- `html-prototype/my-day-calendar.html` — meeting rows are currently a
  flat, non-clickable `.item-row` list; they need to become clickable,
  opening the new Meeting Cockpit. **Not present in the approved
  prototype in any form.**
- A new Meeting Cockpit screen (3 panels: info/attendee-chips right,
  unified multi-agent chat middle, Agents-to-bring-in + quick-research
  list left) — **entirely net-new; no `html-prototype/` screen covers
  any part of it.** See the flag below and the Notes' Prototype parity
  subsection. (Building the prototype itself is the designer's task at
  `/design`, not done here.)

## Dependencies

- **Blocked by:** `REQ-SB-08-US-01` (Meetings Capture Pipeline, **Done**)
  — a Meeting note must exist for the cockpit to open against and for a
  saved research result to wikilink to. Satisfied.
- **Blocked by:** `REQ-SB-10-US-01` (People Living Documents, **Done**)
  — the attendee chip's link target. Satisfied.
- **Blocked by:** `REQ-SB-18-US-01` (Dynamic Agent Sections, **Done**),
  `REQ-SB-20-US-01` (Section Hub Intelligence & Cross-Section Routing,
  **Done**) — Sections and Expert-type agents must exist as a real,
  addressable concept to be "brought in." Both satisfied.
- **Related to, not blocking:** `REQ-SB-36-US-01` (web-research Skill,
  **Done**) — the likely mechanism for on-the-spot research, per the
  PRD's own context; not confirmed as the final mechanism here (see
  Context).
- **Related to, not blocking:** `REQ-SB-25-US-01` (Real Conversational
  Agent Chat, **Done**) — this story's unified multi-agent chat almost
  certainly composes with the real conversational chat mechanism this
  requirement introduced, but a genuinely new multi-agent-in-one-thread
  concept (this codebase's existing chat is single-agent-per-panel) is
  not something `REQ-SB-25-US-01` itself built — left to `/plan-tasks`.
- **Related to, genuinely unclear (not blocking, but not resolved):**
  `REQ-SB-21-US-01` (Agent Working Modes, **Done**) — whether a
  Supervised/Manual gate applies to a brought-in Expert's actions inside
  this cockpit is an open question, per the flag below.
- **External:** none new.

## Constraints

- **One workspace, no separate prep-mode/live-mode** — operator-resolved;
  clicking a meeting opens the identical cockpit regardless of timing.
- **One shared, unified chat thread** — every brought-in Expert responds
  within the same single thread; never one thread per Expert.
- **The quick-research results list is scoped to one meeting** — never a
  cross-meeting personal library.
- **A saved research result is always a new, standalone note, wikilinked
  to the Meeting note — never appended into the Meeting note's own
  body.**
- **An attendee chip must never link to a Person note that does not
  exist** — render a plain, non-clickable indicator instead when no
  Person note exists yet (Scenario 3).
- **Every reply in the shared chat thread must be attributable to the
  specific Expert that produced it** — the exact visual mechanism is left
  to `/design`.
- **This requirement does not change `REQ-SB-20`'s own Hub-routing
  behavior** — the two mechanisms (user-initiated bring-in here,
  agent-initiated Hub routing there) remain independent, per the PRD's
  own explicit clarification.
- **Working-mode (`REQ-SB-21`) interaction with a brought-in Expert — left
  open, not decided here** (see the flag below). Do not assume either
  "gating still fully applies" or "being invited counts as being asked"
  without a resolution.
- **The on-the-spot research mechanism itself — left open, not decided
  here** (see the flag below and Context).

## Implementation Tasks

| Task | Title | Depends on | ACs covered |
|---|---|---|---|
| [[REQ-SB-43-US-01-T01]] | `vault_writer.py` — `load_cockpit_threads_state`/`save_cockpit_threads_state` (new `.second-brain/cockpit_threads.json`) | — | (supports all) |
| [[REQ-SB-43-US-01-T02]] | `app/business/cockpit/threads.py` — shared multi-party thread, composes `run_agent_conversation` per brought-in Expert | T01 | AC-05, AC-06, AC-11 |
| [[REQ-SB-43-US-01-T03]] | `app/business/cockpit/people.py` + `people_extraction.find_existing_person_note` | — | AC-02, AC-03 |
| [[REQ-SB-43-US-01-T04]] | `app/business/cockpit/research.py` — Hub-routed research trigger, save/discard, scoped list | T02 | AC-07, AC-08, AC-09, AC-10 |
| [[REQ-SB-43-US-01-T05]] | `app/api/cockpit_router.py` — `GET/POST /cockpit/{subject_kind}/{stem}...`, registered in `main.py` | T02, T03, T04 | (supports all) |
| [[REQ-SB-43-US-01-T06]] | `my_day.list_calendar_items` gains `"stem"` | — | (supports AC-01) |
| [[REQ-SB-43-US-01-T07]] | Frontend `cockpit/cockpitApiClient.ts` | T05 | (supports all) |
| [[REQ-SB-43-US-01-T08]] | Shared `Cockpit.tsx` 3-panel component | T07 | AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08, AC-09, AC-10 |
| [[REQ-SB-43-US-01-T09]] | `MeetingCockpitPage.tsx` + `/meeting-cockpit/:stem` route + clickable Calendar rows | T08, T06 | AC-01 |

Dependency graph: `T01 → T02 → T04 → T05 → T07 → T08 → T09`, with `T03`
independently feeding `T05`, and `T06` independently feeding `T09`. No
cycles. `REQ-SB-44-US-01` builds ON TOP of `T02`/`T05`/`T07`/`T08` (the
shared Cockpit module, `ADR-036` point 3) via its own `depends_on` edges,
rather than duplicating any of this story's own tasks.

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — N/A, manual-mode verification still the live default project-wide; every locked AC verified live per-task
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **A separate prep-mode vs. live-mode workspace or data model** —
  explicitly rejected by the operator's own decision; one workspace
  serves both.
- **One chat thread per brought-in Expert** — explicitly rejected; one
  shared, unified thread only.
- **A cross-meeting personal research library** — the research list is
  scoped to one meeting only, per the operator's own resolution.
- **A create-Person-note flow from an attendee chip with no existing
  Person note** — left as a genuinely separate, additive product
  decision (see the flag below); this pass builds only the honest
  plain-indicator fallback (Scenario 3).
- **Resolving whether `REQ-SB-21` working-mode gating applies to a
  brought-in Expert's actions inside this cockpit** — explicitly left
  open (see the flag below); no gating behavior is built either way in
  this pass beyond what `REQ-SB-21-US-01` already provides unmodified.
- **Any change to `REQ-SB-20`'s own Hub-routing mechanism or behavior**
  — explicitly out of scope (Scenario 11); the two mechanisms coexist
  unchanged.
- **Building or confirming the on-the-spot research mechanism's exact
  implementation** — left to `/plan-tasks` (see Context).
- **Editing meeting attendees, or any capture-pipeline change to
  `REQ-SB-08`'s own attendee extraction** — out of scope; this story only
  reads existing Meeting/Person note data.

## Notes

**Prototype parity (my-day-calendar.html + net-new Meeting Cockpit
screen):**

- `my-day-calendar.html`'s meeting `.item-row` list — **Superseded, not
  covered.** Rows are currently flat and non-clickable; they need to
  become clickable, opening the new cockpit. **`net-new-design-needed`.**
- The Meeting Cockpit's 3 panels (right: info + attendee chips; middle:
  unified multi-agent chat; left: available Agents + scoped
  quick-research list) — **entirely net-new; no coverage anywhere in
  `html-prototype/`.** **`net-new-design-needed`.**

**Why `gate: flagged`:**

1. One material assumption was made, on a narrow, precedent-grounded
   basis, not a guess: an attendee chip with no existing Person note
   renders as a plain, non-clickable indicator (this project's standing
   never-fabricate-a-link honesty posture), rather than a create-flow.
   The create-flow alternative is recorded as a genuinely open,
   deliberately-not-built follow-on question, not silently decided
   either way.
2. `REQ-SB-43` is not marked `<!-- Draft -->`/unfinalised in the PRD.
3. N/A here (architect/ADR trigger) — but `/plan-tasks` should expect a
   real, new architectural decision for the multi-agent-in-one-thread
   chat mechanism (this codebase's existing chat is single-agent-per-panel).
4. No `ESCALATIONS.md` entry was written by this pass.
5. Not oversized — one bounded 3-panel workspace composing four already-
   Done mechanisms (Meeting notes, Person notes, Sections/Experts,
   web-research); kept as one story per this project's "no independent
   value alone" test — attendee chips with no chat has no value, a chat
   with no research/save mechanism has no value, and vice versa; the
   PRD itself frames this as one cohesive workspace requirement.
6. N/A (coder trigger).
7. No contradictory PRD inputs found.
8. **The two genuinely open, live reasons for `gate: flagged`, both
   named directly by the PRD's own context, not guessed past:** (a) how
   a unified multi-agent chat attributes each reply to the specific
   Expert that produced it — resolved here to the minimal necessary
   behavior (visible attribution, mechanism left to `/design`), so this
   is a lesser factor; (b) whether `REQ-SB-21`'s working-mode gating
   applies to a brought-in Expert's actions inside this cockpit — this
   one is genuinely unresolved, not guessed at, and is the primary
   `unclear-requirement` reason for the flag. **The controlling flag,
   however, is `net-new-design-needed`** — no `html-prototype/` screen
   covers any part of this workspace.

**What to do next:** run `/design REQ-SB-43` for the 3-panel Meeting
Cockpit layout (clickable meeting rows, attendee chips including the
no-Person-note fallback, the unified multi-agent chat with per-Expert
attribution, and the scoped quick-research list with its
save/discard affordance); separately, decide whether `REQ-SB-21`
working-mode gating applies to a brought-in Expert's actions inside this
cockpit before `/plan-tasks` locks the chat's action-dispatch design.

gate: flagged 2026-08-13 — net-new-design-needed (no prototype coverage
for the clickable meeting row or any part of the 3-panel workspace) plus
unclear-requirement (the REQ-SB-21 working-mode-interaction question,
genuinely unresolved per the PRD's own context). A `REVIEW-QUEUE.md`
entry has been added.

**Update, 2026-08-13 (operator decision, relayed directly).** The
`REQ-SB-21` working-mode-interaction question is now resolved: explicit
user invitation into this cockpit's chat bypasses working-mode gating
for that Expert's actions inside the cockpit session — bringing an
Expert in on purpose is itself the approval; Autonomous/Supervised/
Manual gating (`REQ-SB-21-US-01`) is unaffected everywhere else the
Expert operates. This resolves the `unclear-requirement` half of this
story's flag; `net-new-design-needed` still stands unresolved — `gate:`
stays `flagged` pending `/design REQ-SB-43`.

**Update, 2026-08-14 (`/plan-tasks REQ-SB-43-US-01` step 1 — architect).**
Design already approved (operator, 2026-08-13); this pass settles the
multi-agent-in-one-thread chat mechanism this story's own Context and gate
reasoning both anticipated, via a new ADR shared with `REQ-SB-44-US-01`, per
`Implementation/Pipeline.md`'s MUST-FLAG trigger 3 — `gate:` flips back to
`flagged` accordingly (does not halt the decomposer, which proceeds in the
same `/plan-tasks` pass). Mechanism: composes `ADR-015`'s existing,
unmodified `run_agent_conversation` once per brought-in Expert per message
(new sibling `.second-brain/cockpit_threads.json`, this codebase's first
multi-party thread store), a new shared `app/business/cockpit/` module.
The operator's own working-mode-gate resolution (above) is confirmed, by
direct code investigation, to already hold **by construction** — the
Cockpit's own real mechanisms (an Expert's chat/tool-calling reply; the
user's own explicit research-save) never reach `skill_registry.
invoke_skill`/`_invoke_action`'s gated dispatch path at all, so no new
`"cockpit"` trigger value or gate change is needed. Full reasoning:
`Implementation/Architecture/ADR.md` → `ADR-036`.

**Architecture scope:** §Meeting & Inbox Cockpits — multi-agent
shared-thread workspace (REQ-SB-43-US-01, REQ-SB-44-US-01, see ADR-036),
§In-App Agent Orchestration (LangGraph) & Shared MCP Server (the composed,
unmodified `run_agent_conversation`/`ADR-015` conversation graph and
`skill_registry.invoke_skill`'s gate — both read-only context for this
story, neither modified by it).

---

**Decomposer pass (`/plan-tasks` step 2, 2026-08-14).** All 11 Gherkin
scenarios tightened (no substantive wording change — the analyst's/
architect's own text already read as directly buildable against
`ADR-036`'s real module shape) and locked as `REQ-SB-43-US-01-AC-01`..
`AC-11` (`locked: true`, no non-locked exceptions). 9 task files created
(`T01`-`T09`, flat root), building the SHARED `app/business/cockpit/`
module and shared `Cockpit.tsx` frontend component `ADR-036` designs —
`REQ-SB-44-US-01` builds directly ON TOP of `T02`/`T05`/`T07`/`T08` via its
own `depends_on` edges rather than duplicating them, per `ADR-036` point 3's
explicit "SHARE, do not fork" instruction and this run's own guidance to
sequence the shared module here since this story has no external blocker.
`depends_on` wired acyclic: `T01 → T02 → T04 → T05 → T07 → T08 → T09`, `T03`
feeding `T05` independently, `T06` feeding `T09` independently — no cycles.

**One decomposer-level mechanism judgment call, documented, not guessed
past (single defensible reading, not a MUST-FLAG trigger):** the on-the-spot
research mechanism (left open at the mechanism level by the story's own
Context) is built as an explicit `trigger_research` call — Hub-routing from
the requesting (already brought-in) Expert to a real Research Expert,
mirroring `knowledge_bootstrap.bootstrap_agent_knowledge`'s own proven Hop
1 exactly — rather than free-text-sniffing an ordinary chat message. This
reproduces `html-prototype/meeting-cockpit.html`'s own approved
"research-pending" chat exchange exactly (see `T04`'s own Context/Notes for
the full grounding). Requires at least one Expert already brought in,
mirroring the approved prototype's own empty-state chat-input gating.

**AC → task mapping is deliberately redundant where a Scenario has both a
real backend-level outcome and a real screen-level outcome** (Scenarios
5/6/7/8/9/10 each own an AC-tagged step in BOTH a backend task — `T02`/`T04`
— and the frontend integration task — `T08` — per this project's own
"layer-by-layer live verification" pattern, `Implementation/Learnings.md`).
Scenario 1 (AC-01) is owned solely by `T09` (the real click-through
navigation, a screen-level-only claim); Scenario 11 (AC-11) is owned solely
by `T02` (a real-code-inspection claim that `threads.py` never touches
`route_cross_section_request`, not independently re-verifiable at the
screen level).

**No new decomposer-owned MUST-FLAG trigger fired this pass** — every
module/function name, file, and endpoint shape this decomposition builds
against is `ADR-036`'s own already-made Decision, not a decomposer
assumption, EXCEPT the one on-the-spot-research mechanism call named above,
which is recorded explicitly as a single-defensible-reading judgment call,
not a guess filling a genuine gap between competing options; no locked AC
is unverifiable (every one maps to a real, inspectable outcome — a JSON
thread entry, an HTTP response, a rendered DOM element/class, a real vault
note); `depends_on` is acyclic; no task exceeds one working session (each
is a single new file/module or a tightly-scoped, mechanically-similar
group). `gate` stays `flagged` — trigger-3 (`ADR-036` created) is carried
unchanged from the architect pass, per this file's own rule "if the
architect flagged the story this run for an ADR change, leave it `gate:
flagged`." No new `REVIEW-QUEUE.md` entry needed — the architect's own
2026-08-14 entry already asks the human to review `ADR-036` and the
resulting tasks together, which this pass's 9 task files now make
reviewable. No `ESCALATIONS.md` entry written by this pass. `status:` was
already `Ready` entering this pass (set alongside the architect's own step-1
update); this pass confirms that status is now fully earned — every AC
locked, every task written and set to `status: Ready` in lockstep,
`depends_on` acyclic — rather than transitioning it.

---

**Coder pass (`/implement-sprint SPRINT-040`, 2026-08-14).** All 9 tasks
(`T01`-`T09`) built and verified live, `status: Done`; story `status: Done`.
All 11 locked ACs (`AC-01`..`AC-11`) verified with real, non-fabricated
evidence — see each task's own Implementation Log for full detail. Two
scope-internal judgment calls, both logged for human spot-check (`gate:
flagged`), neither a MUST-FLAG escalation:

1. **`T03` — a real `vault_writer.py` frontmatter-parser limitation.**
   `ADR-036` point 7's claim that Meeting notes' `attendees` field is
   "already-established" as `list[{"name","email"}]` frontmatter is NOT
   accurate against the real, current codebase — no Meeting note carries
   this field today (attendee data lives only as body wikilinks), and
   `vault_writer.py`'s own real frontmatter parser cannot round-trip a
   list-of-dicts literal at all (confirmed live). Worked around entirely
   within `cockpit/people.py`'s own file: accepts a JSON-encoded string as
   well as a native list, documented as the required convention for any
   future story that adds real `attendees`/`recipients` capture. No
   `vault_writer.py`/shared-interface change.
2. **`T08` — reconciliation against the REAL approved prototype**
   (`html-prototype/meeting-cockpit.html`), per this task's own Context/
   Notes directive: real class names (`.cockpit-layout`, `.chat-proposal`,
   `.empty-state`) and a real per-Expert-Type attribution color (via
   `fetchAgentList()`'s own `type` field) used in place of the task's own
   illustrative sample, which had neither.

**Live checks beyond any single task's own scope, mandated by this build's
own launch instructions:** (1) clicking a real meeting row opens the 3-panel
Cockpit for that exact meeting — confirmed; (2) attendee chips correctly link
to real Person notes where one exists, honestly render a plain non-clickable
indicator where none exists (real captured Meeting notes today carry no
`attendees` field at all — verified via a real, hand-constructed test note,
disclosed above) — confirmed; (3) two different real Expert agents
(Vault Q&A, People Notes) brought into the same chat produced a genuinely
single shared thread with each reply visibly, distinctly attributed —
confirmed; (4) on-the-spot research produced a real Anthropic web-search
result with an explicit Save/Discard choice; Save created a real, standalone,
wikilinked note; Discard created nothing — confirmed; (5) `REQ-SB-20`'s own
Hub-routing behavior for a brought-in Expert (`vault-qa`) was independently
re-confirmed byte-identical before and after being brought into a real
Cockpit chat, via a direct `route_cross_section_request` call — confirmed
unaffected.

`BUG-012` (pre-existing, already logged) was not re-discovered as new;
confirmed directly relevant per `ADR-036` point 4's own investigation (the
Cockpit's real mechanisms never reach the gated `invoke_skill` dispatch path
at all, so this pre-existing gap neither newly affects nor is newly
introduced by this story).

Full per-task verification evidence: `Implementation/Tasks/
REQ-SB-43-US-01-T01`..`T09`'s own Implementation Log sections.
