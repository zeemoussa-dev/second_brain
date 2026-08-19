---
id: REQ-SB-44-US-01
title: Inbox Cockpit — the Meeting Cockpit's 3-panel pattern adapted for email, with sender/CC/thread people chips, attachment review, and reviewable (never auto-sent) draft replies
requirement_ids: [REQ-SB-44]
requirement_section: "REQ-SB-44: Inbox Cockpit — Expert-Assisted Email Workspace"
phase: P1
status: Done
gate: flagged
gate_reason: "shipped 2026-08-14, SPRINT-041 — all 13 locked ACs verified live; 2 scope-internal judgement calls (T01/T03) logged for human spot-check; see REVIEW-QUEUE.md."
sprint: SPRINT-041
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-44-US-01 — Inbox Cockpit — the Meeting Cockpit's 3-panel pattern adapted for email, with sender/CC/thread people chips, attachment review, and reviewable (never auto-sent) draft replies

## Story

**As a** Second Brain user
**I want** clicking an email to open a dedicated 3-panel workspace where I
can see everyone on the thread, review any attachments, bring in whichever
Expert agents I need help from into one shared chat that can help me
understand the email and draft a reply as text, and do quick on-the-spot
research that I explicitly choose to save or discard
**So that** I can handle an email with the right context and help at hand,
without anything being sent on my behalf and without anything being filed
into my vault that I didn't explicitly approve

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-44: Inbox Cockpit —
  Expert-Assisted Email Workspace* — "Clicking an email (from My Day's
  Emails list) opens the same 3-panel workspace pattern as REQ-SB-43's
  Meeting Cockpit, adapted for email. The right panel shows the email's
  info, with every person on it — sender plus any CC'd or thread
  participants — rendered as a clickable chip linking to their existing
  Person note, and the email's attachments (if any) surfaced for review.
  The middle panel is a unified multi-agent chat where brought-in Experts
  can help the user understand the email and draft a reply as text — this
  pass never sends anything on the user's behalf. The left panel lists
  the user's available Agents (to bring into the chat) and this email's
  own quick-research results. From the chat, the user can trigger
  on-the-spot research and, for each result, explicitly choose whether to
  save it into the vault or discard it." Acceptance: "Clicking an email
  item opens a 3-panel Inbox Cockpit: the right panel shows the email's
  info with the sender and every CC'd/thread participant as a clickable
  chip linking to their Person note (when one exists), plus the email's
  attachments if any; the middle panel is one unified chat thread in
  which every Expert the user has brought in can respond, including
  drafting a reply as reviewable text (never sent automatically); the
  left panel lists the user's available Agents (to bring into the chat)
  and this email's own quick-research results. From the chat, the user
  can trigger on-the-spot research, and each research result offers an
  explicit choice to save it as a new note wikilinked to the Email note,
  or discard it."
- **PRD breadcrumb (2026-08-13, operator-directed, cited verbatim):**
  "Same Idea for the inbox." Reuses `REQ-SB-43`'s own already-settled
  decisions verbatim: one unified multi-agent chat thread (not one thread
  per Expert); the research list is scoped to this one email, not a
  cross-email personal library; a saved research result becomes a new,
  standalone note wikilinked to the email's own Email note (`REQ-SB-07`'s
  capture pipeline output — see the Dependencies note below), not
  appended into it. Clarified via requirements-gathering session, verbatim
  decisions on the genuine ways email differs from a meeting: (1) unlike
  the Meeting Cockpit (research/prep only, never acts on the real-world
  event), this chat CAN draft a reply as reviewable text — but sending is
  explicitly out of scope for this pass; drafting a reply is not itself a
  vault-mutating or externally-visible action, so it does not need
  working-mode/approval gating the way a real send would; a future send
  capability, if ever built, is a separate, later decision requiring its
  own Supervised/Manual approval gating (mirroring `REQ-SB-21`), not
  assumed or half-built here. (2) people chips cover the sender AND any
  CC'd/thread participants, not sender-only, mirroring a meeting's
  multi-attendee chip row rather than a single-person case. (3)
  attachments are in scope this pass, surfaced for the brought-in Experts
  to review — this creates a real, hard dependency on `REQ-SB-28` (File
  Upload for Agents), unlike `REQ-SB-43` which has no attachment concept
  at all.
- **`REQ-SB-43-US-01`'s own already-settled resolutions are reused
  verbatim here, not re-derived:** the unified-thread requirement
  (Scenario 5/6 below mirror `REQ-SB-43-US-01`'s Scenario 5/6 exactly),
  the meeting-scoped-vs-email-scoped research-list pattern (Scenario 7
  below mirrors it, scoped to email instead), the explicit-save-or-
  discard research flow (Scenario 8-10 below), the plain-non-clickable-
  chip fallback for a person with no existing Person note (Scenario 3
  below, same honesty-posture precedent), the per-Expert reply
  attribution requirement (Scenario 6 below), and the same two genuinely
  open questions `REQ-SB-43-US-01` itself flagged (entry-point mechanics
  — not applicable here in the same way, since an email has no
  before/during-meeting distinction; and the `REQ-SB-21` working-mode
  interaction for a brought-in Expert's OTHER actions, e.g. a triggered
  Skill, distinct from drafting a reply which is resolved below).
- **Drafting a reply does not need working-mode/approval gating — this
  much IS resolved, operator-confirmed, unlike the still-open general
  `REQ-SB-21`-interaction question `REQ-SB-43-US-01` flagged.** Drafting
  reviewable text is neither a vault write nor an externally-visible
  action; it produces no side effect outside the chat thread the user is
  already looking at. A future send capability would need its own
  Supervised/Manual gate (mirroring `REQ-SB-21`) — explicitly not built
  or assumed here. Whether a brought-in Expert's OTHER kind of action
  inside this cockpit (e.g. triggering a Skill) needs working-mode
  gating remains the same open question `REQ-SB-43-US-01` already
  flagged — not re-resolved or re-guessed here, tracked as the identical
  open item.
- **Genuinely open, left to `/spec`/`/plan-tasks` — resolved here where a
  safe default exists, flagged where it does not:**
  - **Whether a drafted reply persists anywhere** (saved as a draft
    object the user can return to, or purely ephemeral within the chat
    session until copied out). **Genuinely unresolved, not guessed
    here** — flagged below. No Scenario or Constraint below asserts
    either answer; Scenario 5b (below) only asserts that a drafted reply
    is never sent automatically, remaining agnostic to persistence.
  - **Whether today's Email note frontmatter/`email_classification.py`
    capture CC'd-recipient or thread-participant data at all.** A direct
    check of `architecture.md`'s Data Model this session confirms: **no**
    — the Email note's own frontmatter carries `subject`, `sender`,
    `sender_email`, `received`, `outlook_entry_id`, `conversation_id`
    only (`architecture.md` → "Data Model" intro), no `cc`/
    `thread_participants`-equivalent field anywhere. This is a real,
    confirmed gap, not assumed — capturing CC'd/thread-participant data
    is genuinely new capture-side work (extending
    `outlook_com.py`/`email_classification.py`), not just a cockpit-side
    read of already-captured data. Left to `/plan-tasks`, not designed
    here.
  - **How an attachment surfaced here relates to `REQ-SB-28`'s own
    Compass-summarize/attach-and-handoff mechanism** (reused directly, or
    a separate read-only preview). **Genuinely unresolved, not guessed
    here** — flagged below. Scenario 4 (below) asserts only that
    attachments are surfaced for review, deliberately not asserting which
    mechanism does the surfacing.
  - **The same open questions `REQ-SB-43-US-01` already named for its own
    entry-point/multi-agent-attribution mechanics** — resolved identically
    here, by direct reuse of that story's own resolutions (see above).
- **A real, hard, currently-unmet dependency: `REQ-SB-28-US-01` (File
  Upload for Agents).** Checked directly at the point of writing this
  story: `REQ-SB-28-US-01` is `status: Ready`, `gate: flagged` (not
  `Draft` as the PRD's own context text states — that text was written
  before `REQ-SB-28-US-01` advanced; recorded honestly here, not
  silently trusted) — its own remaining gate is an `ADR-034` human
  review, not a re-spec. **Still not `Done`** — this story's attachments
  half specifically (Scenario 4, plus any Expert action that consumes an
  attachment's summarized content) cannot be built until
  `REQ-SB-28-US-01` ships. The rest of this story (people chips, unified
  chat, on-the-spot research) has no dependency on `REQ-SB-28` and is not
  blocked by it.
- **Depends on:** `REQ-SB-07-US-01` (Scheduled Recurring Agent Capture,
  **Done** — the email-classification pipeline that produces Email
  notes, cited by the PRD's own dependency line as "Email notes, Done").
  `REQ-SB-10-US-01` (Person notes, **Done**) — the people chips' link
  target. `REQ-SB-18-US-01`/`REQ-SB-20-US-01` (Sections/Experts, both
  **Done**) — for "bring Experts as needed." `REQ-SB-28-US-01` (File
  Upload for Agents, **Ready, not yet Done**) — hard prerequisite for the
  attachments half specifically, per above. `REQ-SB-36-US-01`
  (web-research Skill, **Done**) — the likely mechanism for on-the-spot
  research, not confirmed as final here.
- **No `html-prototype/` screen covers this.** `my-day-emails.html`'s
  rows are a flat, non-clickable `.item-row` list (same shape as
  `my-day-calendar.html`, confirmed by direct inspection) — there is no
  click affordance, no 3-panel layout, no people-chip-row concept, no
  attachment-review concept, no multi-agent chat/draft-reply concept, and
  no quick-research list/save-or-discard concept anywhere in the approved
  prototype. A `/design` pass is needed before this story can proceed
  past `/plan-tasks` — see the flag below.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then
edge cases and error states. Do NOT add AC-IDs — the decomposer assigns them
at /plan-tasks. These scenarios mirror REQ-SB-43-US-01's own resolved
scenarios wherever the PRD explicitly says to reuse them, adapted for email;
they deliberately do not assert draft-reply persistence, the attachment-
surfacing mechanism, or the CC/thread-participant capture mechanism — all
three are left open per the Context above. -->

### Scenario 1: Clicking an email item opens the 3-panel Inbox Cockpit

```gherkin
Given the user is viewing My Day's Emails list
When the user clicks an email item
Then a 3-panel Inbox Cockpit opens for that specific email
```

<!-- AC-ID: REQ-SB-44-US-01-AC-01 -->

### Scenario 2: The right panel shows the email's info with sender and CC'd/thread-participant chips linking to existing Person notes

```gherkin
Given the Inbox Cockpit is open for an email whose sender, and any CC'd
    or thread participants, include at least one person with an existing
    Person note in the vault
When the user views the right panel
Then the email's info (at least subject and received date) is shown
  And the sender, plus every CC'd or thread participant with an existing
    Person note, is rendered as a clickable chip that links to that
    Person note
```

<!-- AC-ID: REQ-SB-44-US-01-AC-02 -->

### Scenario 3: A sender or CC'd/thread participant with no existing Person note renders a plain, non-clickable chip

```gherkin
Given the Inbox Cockpit is open for an email with a sender or a CC'd/
    thread participant who has no existing Person note in the vault
When the user views the right panel's people chips
Then that person's chip renders as a plain, non-clickable indicator —
    never a broken or fabricated link to a note that doesn't exist
```

<!-- AC-ID: REQ-SB-44-US-01-AC-03 -->

### Scenario 4: The email's attachments, if any, are surfaced for review

```gherkin
Given the Inbox Cockpit is open for an email that has one or more
    attachments
When the user views the right panel
Then the email's attachments are listed and surfaced for the user and any
    brought-in Expert to review
```

<!-- AC-ID: REQ-SB-44-US-01-AC-04 -->

### Scenario 4b: An email with no attachments shows no attachment section content

```gherkin
Given the Inbox Cockpit is open for an email with no attachments
When the user views the right panel
Then no attachment is listed, and no attachment-review affordance implies
    one exists
```

<!-- AC-ID: REQ-SB-44-US-01-AC-05 -->

### Scenario 5: The left panel lists the user's available Agents to bring into the chat

```gherkin
Given the Inbox Cockpit is open
When the user views the left panel
Then the user's available Agents are listed, from which the user can
    choose which to bring into this email's chat
```

<!-- AC-ID: REQ-SB-44-US-01-AC-06 -->

### Scenario 5b: Bringing an Expert into the chat adds it to the one shared, unified conversation thread

```gherkin
Given the Inbox Cockpit is open with its chat thread empty or already
    containing messages
When the user brings an Expert agent into the chat from the left panel
Then that Expert becomes able to respond in the same one shared chat
    thread — no new, separate thread is created for that Expert
When the user brings a second, different Expert into the same chat
Then both Experts respond within that identical single shared thread,
    not two parallel threads
```

<!-- AC-ID: REQ-SB-44-US-01-AC-07 -->

### Scenario 6: Each Expert's reply in the shared thread is attributed to the specific Expert that produced it

```gherkin
Given two or more Experts have been brought into the Inbox Cockpit's chat
    thread
When any of those Experts responds in the thread
Then that reply is visibly attributed to the specific Expert that
    produced it, distinguishable from a reply by any other Expert in the
    same thread
```

<!-- AC-ID: REQ-SB-44-US-01-AC-08 -->

### Scenario 7: The chat can draft a reply as reviewable text, and it is never sent automatically

```gherkin
Given the Inbox Cockpit's chat is open, with or without a brought-in
    Expert
When the user asks a brought-in Expert to draft a reply to this email
Then a draft reply is produced as reviewable text within the chat thread
  And the draft is never sent on the user's behalf — no outbound email is
    dispatched by this action, this pass, under any circumstance
```

<!-- AC-ID: REQ-SB-44-US-01-AC-09 -->

### Scenario 8: The left panel's quick-research results are scoped to this one email

```gherkin
Given the user has generated quick-research results in more than one
    different email's own Inbox Cockpit
When the user views one specific email's Inbox Cockpit left panel
Then only that email's own quick-research results are listed — results
    generated while working on a different email are not shown
```

<!-- AC-ID: REQ-SB-44-US-01-AC-10 -->

### Scenario 9: Triggering on-the-spot research from the chat produces a result the user must explicitly save or discard

```gherkin
Given the Inbox Cockpit's chat is open
When the user triggers on-the-spot research from the chat
Then a research result is produced and shown to the user
  And the result offers an explicit choice to save it into the vault or
    discard it — it is not automatically saved or automatically
    discarded
```

<!-- AC-ID: REQ-SB-44-US-01-AC-11 -->

### Scenario 10: Saving a research result creates a new standalone note wikilinked to the Email note

```gherkin
Given an on-the-spot research result is shown to the user with a pending
    save-or-discard choice
When the user chooses to save it
Then a new, standalone note is created (not appended into the Email
    note's own body) and wikilinked to this email's own Email note
  And the new note appears in this email's own quick-research results
    list in the left panel
```

<!-- AC-ID: REQ-SB-44-US-01-AC-12 -->

### Scenario 11: Discarding a research result creates no note

```gherkin
Given an on-the-spot research result is shown to the user with a pending
    save-or-discard choice
When the user chooses to discard it
Then no note is created in the vault
  And the discarded result does not appear in this email's own
    quick-research results list
```

<!-- AC-ID: REQ-SB-44-US-01-AC-13 -->

## Affected Screens

- `html-prototype/my-day-emails.html` — email rows are currently a flat,
  non-clickable `.item-row` list; they need to become clickable, opening
  the new Inbox Cockpit. **Not present in the approved prototype in any
  form.**
- A new Inbox Cockpit screen (3 panels: info/people-chips/attachments
  right, unified multi-agent chat with draft-reply middle, Agents-to-
  bring-in + quick-research list left) — **entirely net-new; no
  `html-prototype/` screen covers any part of it,** though it shares
  the same 3-panel *pattern* `REQ-SB-43-US-01`'s Meeting Cockpit
  introduces (its own design is also still pending — see that story). See
  the flag below and the Notes' Prototype parity subsection. (Building
  the prototype itself is the designer's task at `/design`, not done
  here.)

## Dependencies

- **Blocked by:** `REQ-SB-28-US-01` (File Upload for Agents, **Ready,
  gate: flagged, not yet Done**) — hard prerequisite for the attachments
  half of this story specifically (Scenario 4, and any Expert action that
  consumes an attachment's summarized content). **Not satisfied yet as of
  this spec pass.** The rest of this story is not blocked by it.
- **Blocked by:** `REQ-SB-07-US-01` (Scheduled Recurring Agent Capture,
  **Done**) — the email-capture pipeline that produces the Email notes
  this cockpit opens against. Satisfied.
- **Blocked by:** `REQ-SB-10-US-01` (People Living Documents, **Done**)
  — the people chips' link target. Satisfied.
- **Blocked by:** `REQ-SB-18-US-01`/`REQ-SB-20-US-01` (Sections and
  Expert-type agents, both **Done**) — must exist as a real, addressable
  concept to be "brought in." Both satisfied.
- **Related to:** `REQ-SB-43-US-01` (Meeting Cockpit, `Draft`, flagged,
  not yet built) — this story adapts that story's own 3-panel pattern and
  reuses several of its already-resolved decisions verbatim (unified
  chat, per-Expert attribution, scoped research list, explicit
  save-or-discard, non-clickable-chip fallback). Not a build dependency
  (the pattern is reused conceptually, not by code reuse requiring that
  story to ship first), but the two stories should be designed
  consistently — recommend running `/design` for both together.
- **Related to, not blocking:** `REQ-SB-36-US-01` (web-research Skill,
  **Done**) — the likely mechanism for on-the-spot research, per the
  PRD's own context; not confirmed as the final mechanism here.
- **Related to, genuinely unclear (not blocking, but not resolved):**
  `REQ-SB-21-US-01` (Agent Working Modes, **Done**) — whether a
  Supervised/Manual gate applies to a brought-in Expert's OTHER actions
  (distinct from drafting a reply, which is resolved not to need gating —
  see Context) inside this cockpit is the same open question
  `REQ-SB-43-US-01` already flagged.
- **External:** none new.

## Constraints

- **This pass never sends anything on the user's behalf** — drafting a
  reply produces reviewable text only; no outbound email dispatch of any
  kind is built or triggered by this story.
- **One shared, unified chat thread** — every brought-in Expert responds
  within the same single thread; never one thread per Expert.
- **People chips cover the sender AND every CC'd/thread participant** —
  not sender-only.
- **The quick-research results list is scoped to one email** — never a
  cross-email personal library.
- **A saved research result is always a new, standalone note, wikilinked
  to the Email note — never appended into the Email note's own body.**
- **A people chip must never link to a Person note that does not exist**
  — render a plain, non-clickable indicator instead (Scenario 3).
- **Every reply in the shared chat thread must be attributable to the
  specific Expert that produced it** — the exact visual mechanism is left
  to `/design`.
- **Attachments, if present, must be surfaced for review** — the exact
  mechanism (reusing `REQ-SB-28`'s summarize-and-handoff flow directly, or
  a separate read-only preview) is left open, not decided here.
- **This story cannot fully build its attachments half until
  `REQ-SB-28-US-01` reaches `Done`** — a currently-unmet dependency, not
  a guess to work around.
- **Capturing CC'd/thread-participant data is genuinely new capture-side
  work** — no existing Email note frontmatter field carries it today
  (confirmed by direct inspection); this is not solvable by a cockpit-
  side read alone.
- **Draft-reply persistence — left open, not decided here** (see the flag
  below). Do not assume either "saved as a returnable draft object" or
  "purely ephemeral" without a resolution.

## Implementation Tasks

| Task | Title | Depends on | ACs covered |
|---|---|---|---|
| [[REQ-SB-44-US-01-T01]] | `outlook_com.resolve_mail_recipients` + Email note `recipients` frontmatter field | — | (supports AC-02) |
| [[REQ-SB-44-US-01-T02]] | `my_day.list_email_items` gains `"stem"` | — | (supports AC-01) |
| [[REQ-SB-44-US-01-T03]] | `app/business/cockpit/attachments.py` — list + hand-off-to-chat (composes `REQ-SB-28-US-01`'s `upload_storage`/`summarize_file` directly) | `REQ-SB-28-US-01-T01`, `REQ-SB-28-US-01-T03`, `REQ-SB-28-US-01-T04`, `REQ-SB-43-US-01-T02` | AC-04, AC-05 |
| [[REQ-SB-44-US-01-T04]] | Extend `cockpit_router.py` — `GET/POST /cockpit/email/{stem}/attachments...` | T03, `REQ-SB-43-US-01-T05` | AC-04, AC-05 |
| [[REQ-SB-44-US-01-T05]] | Extend `cockpitApiClient.ts` — attachment fetch/hand-off | T04, `REQ-SB-43-US-01-T07` | (supports AC-04, AC-05) |
| [[REQ-SB-44-US-01-T06]] | `InboxCockpitPage.tsx` + `/inbox-cockpit/:stem` route + clickable Emails rows + `AttachmentsPanel.tsx` + draft-copy affordance | T05, `REQ-SB-43-US-01-T08`, T02 | AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08, AC-09, AC-10, AC-11, AC-12, AC-13 |

**Cross-story dependency (real, currently unmet at spec time):** `T03`'s
own `depends_on` includes `REQ-SB-28-US-01-T01`/`T03`/`T04` — those tasks
were `status: Ready`, not `Done`, when this story was decomposed
(`ADR-036` point 5, mirroring `REQ-SB-39-US-02`'s own precedent for a
`Ready`-not-`Done` cross-story dependency). `T04`/`T05`/`T06` transitively
wait on `T03`. `T01`/`T02` carry no such dependency and may build
immediately.

**Shared-module dependency (this story builds ON `REQ-SB-43-US-01`, not a
duplicate):** `T04`/`T05`/`T06` each `depends_on` a `REQ-SB-43-US-01` task
(`T05`/`T07`/`T08` respectively) — this story extends the SAME
`cockpit_router.py`/`cockpitApiClient.ts`/`Cockpit.tsx` files that story
builds, per `ADR-036` point 3's "SHARE, do not fork" instruction, rather
than creating parallel per-kind modules.

Dependency graph: `T01`/`T02` independent. `REQ-SB-28-US-01-T01/T03/T04` →
`T03` → `T04` (+ `REQ-SB-43-US-01-T05`) → `T05` (+ `REQ-SB-43-US-01-T07`) →
`T06` (+ `REQ-SB-43-US-01-T08`, `T02`). No cycles.

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — N/A, manual-mode verification still the live default project-wide; every locked AC verified live per-task
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Actually sending a drafted reply** — explicitly out of scope this
  pass; a future send capability is a separate, later decision requiring
  its own Supervised/Manual approval gating (mirroring `REQ-SB-21`), not
  assumed or half-built here.
- **One chat thread per brought-in Expert** — explicitly rejected; one
  shared, unified thread only.
- **A cross-email personal research library** — the research list is
  scoped to one email only.
- **A create-Person-note flow from a people chip with no existing Person
  note** — same open, deliberately-not-built follow-on question
  `REQ-SB-43-US-01` already named; this pass builds only the honest
  plain-indicator fallback (Scenario 3).
- **Resolving whether `REQ-SB-21` working-mode gating applies to a
  brought-in Expert's OTHER actions inside this cockpit** (distinct from
  drafting a reply, which is resolved) — explicitly left open.
- **New capture-side CC'd/thread-participant extraction logic itself** —
  the genuine gap is confirmed and recorded (see Context/Constraints),
  but building the extraction is left to `/plan-tasks`, not designed
  here.
- **Resolving or building the attachment-surfacing mechanism's exact
  relationship to `REQ-SB-28`** — left to `/plan-tasks`.
- **Deciding or building draft-reply persistence** — left open, not
  decided here.
- **Any change to `REQ-SB-20`'s own Hub-routing mechanism or behavior** —
  out of scope; unchanged, same as `REQ-SB-43-US-01`.

## Notes

**Prototype parity (my-day-emails.html + net-new Inbox Cockpit screen):**

- `my-day-emails.html`'s email `.item-row` list — **Superseded, not
  covered.** Rows are currently flat and non-clickable; they need to
  become clickable, opening the new cockpit. **`net-new-design-needed`.**
- The Inbox Cockpit's 3 panels (right: info + people chips + attachments;
  middle: unified multi-agent chat with draft-reply; left: available
  Agents + scoped quick-research list) — **entirely net-new; no coverage
  anywhere in `html-prototype/`,** though it shares the same 3-panel
  *pattern* as the also-unspecced Meeting Cockpit (`REQ-SB-43-US-01`).
  **`net-new-design-needed`.**

**Why `gate: flagged`:**

1. Two material assumptions were made, each on a narrow, precedent-
   grounded basis, not a guess: a people chip with no existing Person
   note renders as a plain, non-clickable indicator (reused verbatim from
   `REQ-SB-43-US-01`'s own resolution); drafting a reply needs no
   working-mode/approval gating, because it is neither a vault write nor
   an externally-visible action (directly grounded in the operator's own
   verbatim clarification, quoted in Context). Neither assumption
   resolves a genuinely contested product question by guessing.
2. `REQ-SB-44` is not marked `<!-- Draft -->`/unfinalised in the PRD.
3. N/A here (architect/ADR trigger) — but `/plan-tasks` should expect a
   real, new architectural decision for the same multi-agent-in-one-thread
   chat mechanism `REQ-SB-43-US-01` needs, plus new capture-side work for
   CC'd/thread-participant data.
4. No `ESCALATIONS.md` entry was written by this pass.
5. Not oversized — one bounded 3-panel workspace, mirroring
   `REQ-SB-43-US-01`'s own scope reasoning (shared pattern, composed of
   already-Done mechanisms plus one still-Ready dependency); kept as one
   story per this project's "no independent value alone" test.
6. N/A (coder trigger).
7. No contradictory PRD inputs found — the PRD's own context text's
   "REQ-SB-28, Draft" characterization is superseded by this session's own
   direct check (now `Ready`), recorded honestly in Context/Dependencies
   rather than silently trusted or silently corrected without a note.
8. **The two genuinely open, live reasons for `gate: flagged`, both named
   directly by the PRD's own context, not guessed past:** (a) whether a
   drafted reply persists anywhere; (b) how a surfaced attachment relates
   to `REQ-SB-28`'s own mechanism. Neither is guessed at. **A third,
   independent, equally-controlling flag: `new-dependency`** — this story
   has a real, hard, currently-unmet dependency on `REQ-SB-28-US-01`
   (`Ready`, not `Done`) for its attachments half. **The overall
   controlling flag, however, is `net-new-design-needed`** — no
   `html-prototype/` screen covers any part of this workspace.

**What to do next:** run `/design REQ-SB-44` (ideally alongside
`/design REQ-SB-43` for layout consistency) for the 3-panel Inbox
Cockpit; separately, decide draft-reply persistence and the attachment-
surfacing mechanism's relationship to `REQ-SB-28` before `/plan-tasks`
locks the design; and track `REQ-SB-28-US-01`'s own remaining `ADR-034`
human review — this story's attachments half cannot build until that
story reaches `Done`.

gate: flagged 2026-08-13 — net-new-design-needed (no prototype coverage
for the clickable email row or any part of the 3-panel workspace) plus
unclear-requirement (draft-reply persistence; the attachment-surfacing
mechanism's relationship to REQ-SB-28) plus new-dependency
(REQ-SB-28-US-01 is Ready, not yet Done — a real, currently-unmet
blocker for the attachments half). A `REVIEW-QUEUE.md` entry has been
added.

**Update, 2026-08-13 (operator decisions, relayed directly).** Both
`unclear-requirement` items are now resolved: (a) a drafted reply is
ephemeral — it lives only in the chat session, with no returnable-draft
storage built this pass; closing the cockpit without copying it out
loses it, by design. (b) A surfaced attachment reuses `REQ-SB-28`'s own
Compass-summarize/handoff mechanism directly, not a separate read-only
preview — this keeps one attachment-handling mechanism in the codebase
instead of two, and means this half's `new-dependency` block on
`REQ-SB-28-US-01` (`Ready`, not `Done`) is unchanged and still real:
the attachments half cannot build until that story reaches `Done`, gate
still stands on `net-new-design-needed` pending `/design REQ-SB-44`.

**Update, 2026-08-14 (`/plan-tasks REQ-SB-44-US-01` step 1 — architect).**
Design already approved (operator, 2026-08-13); this pass settles this
story's remaining architect-level open items via a new ADR shared with
`REQ-SB-43-US-01`, per `Implementation/Pipeline.md`'s MUST-FLAG trigger 3
— `gate:` flips back to `flagged` accordingly (does not halt the
decomposer, which proceeds in the same `/plan-tasks` pass). The shared
3-panel pattern SHARES one backend `app/business/cockpit/` module and one
frontend `Cockpit` component with `REQ-SB-43-US-01` (attachment review and
the draft-reply area are additive props, not a fork — a draft reply itself
needs no new backend concept, matching the operator's own ephemeral-only
resolution). The `REQ-SB-28-US-01` dependency (`Ready`, not `Done`) is
confirmed real and unchanged — the decomposer must give this story's
attachment-review task(s) a `depends_on` edge onto
`REQ-SB-28-US-01-T03`/`T04`, mirroring `REQ-SB-39-US-02`'s own precedent for
a `Ready`-not-`Done` cross-story dependency; the rest of this story is not
blocked by it. New Email-note frontmatter field, `recipients:
list[{"name","email"}]`, mirroring the Meeting note's `attendees` shape,
captured via a generalized `outlook_com.py` recipients-resolution function
— deliberately does not extend `people_extraction.ensure_person_note` to
CC'd/thread participants (matches this story's own "no create-Person-note
flow" Non-Goal). Full reasoning: `Implementation/Architecture/ADR.md` →
`ADR-036`.

**Architecture scope:** §Meeting & Inbox Cockpits — multi-agent
shared-thread workspace (REQ-SB-43-US-01, REQ-SB-44-US-01, see ADR-036),
§Data Model (the new Email `recipients` frontmatter field), §In-App Agent
Orchestration (LangGraph) & Shared MCP Server (read-only context — the
composed, unmodified `run_agent_conversation`/`ADR-015` conversation graph
and `skill_registry.invoke_skill`'s gate, neither modified by this story).

---

**Decomposer pass (`/plan-tasks` step 2, 2026-08-14).** All 13 Gherkin
scenarios tightened (no substantive wording change) and locked as
`REQ-SB-44-US-01-AC-01`..`AC-13` (`locked: true`, no non-locked
exceptions). 6 task files created (`T01`-`T06`, flat root) — this story
builds ON TOP of `REQ-SB-43-US-01`'s SHARED `cockpit_router.py`/
`cockpitApiClient.ts`/`Cockpit.tsx` (per `ADR-036` point 3), never
duplicating them: `T04`/`T05`/`T06` each carry a `depends_on` edge onto the
corresponding `REQ-SB-43-US-01` task (`T05`/`T07`/`T08`).

**The cross-story `REQ-SB-28-US-01` dependency is wired exactly as the
architect instructed** — `T03` (`app/business/cockpit/attachments.py`)
carries `depends_on: [REQ-SB-28-US-01-T01, REQ-SB-28-US-01-T03,
REQ-SB-28-US-01-T04, REQ-SB-43-US-01-T02]`. `T01`/`T03` are genuine, direct
composition dependencies (this task's own code calls `upload_storage`'s and
`skill_tools.summarize_file`'s real functions directly); `T04` is included
per the architect's own explicit `ADR-036` point 5 instruction even though
this task's own code does NOT call `T04`'s HTTP endpoint directly (that
endpoint ends in an unwanted Vault-Filing-Expert auto-file for an
already-vault-saved email attachment reviewed in chat, not the desired
outcome here) — this deliberate distinction (dependency listed per
instruction; composition choice documented separately) is recorded
explicitly in `T03`'s own Context/Notes, not silently reconciled either
way. `T04`/`T05`/`T06` transitively wait on `T03`; `T01`/`T02` (the
`recipients` capture field and the `my_day` stem field) carry no such
dependency and build immediately — matching the story's own "the rest of
this story is not blocked by it" framing.

**Two decomposer-level judgment calls, documented, not guessed past (both
single defensible readings, not MUST-FLAG triggers):**
1. Draft-reply's own "distinct affordance" (operator-resolved to be
   ephemeral, frontend-only, per `ADR-036` point 3) is built as a generic
   per-message Copy button on every Expert reply in the Inbox Cockpit
   (`enableDraftCopyAffordance`), not a detected-intent-specific
   treatment — there is no reliable signal distinguishing "this reply was
   a requested draft" from "this reply was an ordinary answer" without a
   new backend concept, which `ADR-036` explicitly rules out. Scenario 7's
   own "reviewable text, never sent automatically" is satisfied by
   construction either way (no send capability exists anywhere in this
   story).
2. The on-the-spot research mechanism reuses `REQ-SB-43-US-01-T04`'s own
   `research.py` UNCHANGED (already generic over `subject_kind`) — no new
   REQ-SB-44-specific research task was created; this story's own `AC-10`
   through `AC-13` are verified against that SAME module/router, at the
   `email` `subject_kind`, inside this story's own `T06`.

**AC → task mapping:** `T01`/`T02` are infra-only (support `AC-02`/`AC-01`
respectively, no AC-tagged step of their own — mirrors `REQ-SB-40-US-01-T01`'s
own precedent for a supporting-only task). `T03`/`T04` jointly own `AC-04`/
`AC-05` at the backend layer (real file-listing/hand-off, real HTTP). `T06`
(the final integration task) owns the full page-level set `AC-01`-`AC-13`,
per this project's own "the frontend/integration task carries most of the
live-verification weight" precedent — every locked AC has at least one
AC-tagged manual verification step across the task set.

**No new decomposer-owned MUST-FLAG trigger fired this pass** — every
module/function/field name and endpoint shape this decomposition builds
against is `ADR-036`'s own already-made Decision, save the two judgment
calls named above, each a single defensible reading, not a guess filling a
genuinely contested gap; no locked AC is unverifiable; `depends_on` is
acyclic (including the cross-story edges); no task exceeds one working
session. `gate` stays `flagged` — trigger-3 (`ADR-036` created) and the
real cross-story `new-dependency` on `REQ-SB-28-US-01` are both carried
unchanged from the architect pass, per this file's own rule "if the
architect flagged the story this run for an ADR change, leave it `gate:
flagged`." No new `REVIEW-QUEUE.md` entry needed — the architect's own
2026-08-14 entry already asks the human to review `ADR-036`, the shared
module shape, and the `REQ-SB-28-US-01` sequencing together, which this
pass's 6 task files now make reviewable. No `ESCALATIONS.md` entry written
by this pass. `status:` was already `Ready` entering this pass (set
alongside the architect's own step-1 update); this pass confirms that
status is now fully earned — every AC locked, every task written and set
to `status: Ready` in lockstep, `depends_on` acyclic (including the real,
disclosed cross-story `REQ-SB-28-US-01` edge) — rather than transitioning
it. Building `T03`-`T06` in practice still waits on `REQ-SB-28-US-01`
reaching `Done`, per its own `depends_on` chain — `/implement-sprint`
routes around this automatically (`Implementation/Pipeline.md` hard rule
9), not a gate concern for this pass.

---

**Coder pass (`/implement-sprint SPRINT-041`, 2026-08-14).** All 6 tasks
(`T01`-`T06`) built and marked `Done`; all 13 locked ACs verified live
(real Outlook-capture-pipeline composition, real HTTP, real headless-Edge
browser CDP session driving the actual running app, real Compass/
Anthropic Provider calls) — see each task's own Implementation Log for
the full per-AC evidence. Built directly ON TOP of `REQ-SB-43-US-01`'s
SHARED `app/business/cockpit/`/`cockpit_router.py`/`cockpitApiClient.ts`/
`Cockpit.tsx`, per `ADR-036` point 3 — zero duplication; the Meeting
Cockpit's own existing routes/exports/behavior confirmed byte-for-byte
unchanged throughout. Two scope-internal judgement calls, both disclosed
and both correcting an illustrative task code sample against a real,
confirmed primitive limitation, not guesses filling a genuine gap: `T01`
writes `recipients` as a JSON-encoded string (not a raw list literal),
reusing `SPRINT-040`'s own already-established workaround for
`vault_writer.py`'s confirmed list-of-dicts round-trip limitation; `T03`'s
`_attachments_dir` skips slugification entirely (the input is already the
exact slug, confirmed live against real vault fixtures) rather than
reaching into `vault_writer.py`'s private `_slugify`. Neither weakens any
locked AC. No new `ESCALATIONS.md` entry; no locked AC blocked. Status →
`Done`.
