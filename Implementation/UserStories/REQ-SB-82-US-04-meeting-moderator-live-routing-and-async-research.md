---
id: REQ-SB-82-US-04
title: Meeting Moderator — routes each live question to the ONE Expert it belongs to, falling back to async Research with a threaded reply
requirement_ids: [REQ-SB-82]
requirement_section: "REQ-SB-82: Cockpit Mechanics — Prep, Research, and Moderation"
phase: P2
status: Draft
gate: flagged
gate_reason: "trigger-8 (the exact routing-decision mechanism for 'the ONE Expert it actually belongs to' is genuinely unresolved by the PRD's own text, including the tie-break case) plus net-new-design-needed (threaded/parent-child reply rendering does not exist anywhere in this app today -- the real chat-thread rendering is a flat list) plus a real, load-bearing technical risk disclosed, not glossed over: this codebase's own real Hermes architecture has NO live multi-turn back-channel between separate agent profiles today (MEMORY.md, 2026-08-23) -- routing one live question to a DIFFERENT specialist agent and getting a reply back into ONE shared UI thread in real time has no working precedent in this codebase. See REVIEW-QUEUE.md."
sprint: ""
created: 2026-08-25
updated: 2026-08-25
---

# REQ-SB-82-US-04 — Meeting Moderator — routes each live question to the ONE Expert it belongs to, falling back to async Research with a threaded reply

## Story

**As a** Second Brain user chatting with the Experts I've brought into a
Meeting or Inbox Cockpit
**I want** each question I ask to go to the ONE Expert it actually belongs
to, not broadcast to everyone I've brought in — and if none of them knows
the answer, I want it handed to the Research Agent in the background,
without freezing the chat, with the answer landing as a reply threaded to
my original question once it's ready
**So that** I get one clear, relevant answer per question instead of a wall
of replies from everyone I brought in, and a question nobody in the room
can answer doesn't just dead-end

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-82: Cockpit Mechanics — Prep,
  Research, and Moderation*, "Meeting Moderator" bullet (second half) and
  "Async research + threaded replies" bullet — "During the meeting,
  routes each question to the ONE Expert it actually belongs to instead
  of broadcasting to everyone brought in; when it doesn't know, triggers
  the Research Agent rather than guessing or dead-ending... a Research
  Agent call during a live meeting never blocks the chat; the live
  conversation keeps moving while it works in the background. Its result
  lands as a threaded reply to the question that triggered it (not a new
  flat message), so the chat's own real-time order isn't scrambled by a
  result landing a minute or two later." PRD breadcrumb (verbatim,
  2026-08-25 operator): "Then the meeting Moderator Agent... Assemeble the
  Agents Needed in the meeting he Monitor the chat... Direct Messages to
  the Write Agent when I ask a Question instead of having my Questions
  Goes to all Agents at the same time"; and, on the fallback: "if you
  don't know ask it might end up by something we need to research and
  have an Expert on that Research coming to the meeting," done "Async,
  background it Show things as Replys so Conversation in chat don't get
  lost"; and "One thing Chat doesn't get lost in the meeting in case I
  changed the Page" (this last point is `REQ-SB-82-US-01`'s own concern,
  not re-derived here).
- **This is one of five substories `REQ-SB-82` splits into — see
  `REQ-SB-82-US-01`'s own Context for the full split rationale.** This
  story covers live, per-question routing plus the async-research
  fallback and its threaded reply — deliberately separate from
  `REQ-SB-82-US-03`'s own roster PRE-assembly, since this story's own
  routing/fallback behavior applies to whichever roster exists (whether
  pre-recommended by `US-03` or manually brought in today), and has real,
  independent value on its own.
- **Depends on `REQ-SB-82-US-01` (Persisted Cockpit Chat) — a real, hard
  dependency, not merely related.** A routed reply and a threaded async
  result both need somewhere real to be written — the same persisted
  thread store that story builds; without it, a live conversation this
  story enables would immediately re-inherit the exact "resets on
  reload" problem `REQ-SB-82-US-01` exists to fix.
- **Depends on `REQ-SB-82-US-02` (Research Agent) — a real, hard
  dependency, not merely related.** This story's own fallback mechanism
  is explicitly named in the PRD as calling that exact capability
  ("triggers the Research Agent"); this story does not build its own,
  separate research mechanism.
- **A real, load-bearing technical risk this pass surfaces rather than
  glosses over, found by direct reading of `MEMORY.md`'s own documented
  constraints on this codebase's REAL, current Hermes architecture (not
  the archived pre-pivot LangGraph model REQ-SB-43-US-01's own `ADR-036`
  was designed against):**
  - `MEMORY.md`, 2026-08-22: *"`hermes -p <profile> chat -q '...'`
    (one-shot cross-profile relay) has no live back-channel — if the
    target profile's agent tries to ask a clarifying question... the call
    just blocks and times out (~120s)... Any multi-turn Q&A needed for a
    delegated task must happen on the calling agent's own live channel
    first; only the single, fully-consolidated result... gets relayed in
    one call."*
  - `MEMORY.md`, 2026-08-23: *"`POST /agents/{agent_id}/chat`... is a
    genuinely stateless, one-shot REST turn — it opens a fresh
    `HermesChatSession` per HTTP call and closes it in `finally`, with no
    session/`request_id` continuity held across separate calls."*
  - **What this means for THIS story, concretely:** every real mechanism
    this codebase has today for reaching a DIFFERENT Hermes-mirrored
    specialist agent (e.g. routing a question from whatever's brought
    into a live Cockpit chat over to `azure-expert` or a Customer
    Expert) is either a one-shot, no-back-channel relay, or a stateless
    single-turn REST call with no continuity — neither is, by itself,
    "route this ONE live question to the right Expert, in a SHARED
    thread, while the rest of the conversation with OTHER brought-in
    Experts keeps working." Whether the real, unified multi-agent-in-
    one-thread routing this requirement asks for is buildable by
    composing these existing primitives directly (one stateless
    `/agents/{id}/chat`-style call per routed question, keyed into the
    shared persisted thread), or needs genuinely new session-continuity
    infrastructure, is a real, undecided architectural question — **not
    resolved here**, and explicitly NOT assumed solvable by extension of
    an existing pattern. `/plan-tasks` should investigate this directly
    before committing to a design.
- **Genuinely open, not resolved here — how the Moderator decides which
  ONE Expert "a question actually belongs to."** The PRD's own text
  states the OBSERVABLE requirement (one Expert answers, not a broadcast)
  but not the mechanism. `REQ-SB-20-US-01` (Section Hub Intelligence,
  **Done**) already solved a structurally similar problem — routing an
  agent's own out-of-scope request to the right other agent via
  per-agent keywords — but that mechanism is agent-initiated,
  Hub-mediated cross-Section routing, not a live, user-typed question
  inside a shared multi-agent chat the Moderator is directly monitoring.
  Whether this story reuses that same keyword-match mechanism, a real LLM
  routing judgment (mirroring `REQ-SB-25`'s own move from keyword-match to
  real conversational reasoning), or something else, is left open.
  Relatedly, the tie-break case — a question two or more brought-in
  Experts could plausibly answer — has no PRD-stated resolution either;
  the Scenarios below assert only the OBSERVABLE outcome (exactly one
  Expert responds), not how a tie is broken.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then
edge cases and error states. Do NOT add AC-IDs — the decomposer assigns them
at /plan-tasks. These scenarios describe only the externally observable
routing/fallback/async behaviour; they deliberately do not assert the
routing-decision mechanism, the tie-break rule, or the exact threaded-reply
visual treatment — all left open per Context. -->

### Scenario 1: A question is routed to the one brought-in Expert it belongs to, not broadcast to all

```gherkin
Given two or more Experts are brought into a Cockpit's Chat
When the user asks a question that clearly belongs to one specific
    brought-in Expert's own domain
Then only that one Expert responds to the question
  And the other brought-in Experts do not also produce a reply to the
    same question
```

### Scenario 2: A question none of the brought-in Experts can answer is handed to the Research Agent, not left to dead-end

```gherkin
Given one or more Experts are brought into a Cockpit's Chat
When the user asks a question none of the brought-in Experts can answer
Then the question is handed to the Research Agent (REQ-SB-82-US-02)
    instead of a brought-in Expert guessing at an answer or the chat
    simply going unanswered
```

### Scenario 3: The Research Agent fallback runs in the background without blocking the live chat

```gherkin
Given a question has just been handed to the Research Agent (Scenario 2)
When the user sends a further message to the chat while that research is
    still in progress
Then the chat accepts and responds to that further message normally — the
    user is never blocked waiting for the research to finish
```

### Scenario 4: The Research Agent's result lands as a threaded reply, not a new flat message

```gherkin
Given a Research Agent fallback (Scenario 2) has finished and produced a
    result
When that result is added to the chat
Then it appears as a reply threaded to the SPECIFIC question that
    triggered it — not appended as a new message at the bottom of the
    flat conversation order
  And the chat's own real-time message order (everything exchanged since
    the question was asked) is left undisturbed by the result landing
    later
```

### Scenario 5: A question two or more brought-in Experts could plausibly answer is still routed to exactly one, never broadcast

```gherkin
Given two or more brought-in Experts could each plausibly answer the same
    question
When the user asks that question
Then exactly one Expert responds — never more than one, and never zero
    without falling back to the Research Agent (Scenario 2)
```

### Scenario 6: A message sent with no Experts brought in at all does not silently fail

```gherkin
Given the Cockpit's Chat has no Experts brought in yet
When the user sends a message anyway
Then the user gets an honest, non-broken response to that condition (not
    a silent failure and not a fabricated reply from a nonexistent
    Expert) — the exact behavior (e.g. prompting the user to bring
    someone in first) is left to `/plan-tasks`
```

## Affected Screens

- `src/frontend/src/features/cockpit/Cockpit.tsx` — the REAL, current
  screen (see `REQ-SB-82-US-01`'s own Context for why the stale
  `html-prototype/meeting-cockpit.html`/`inbox-cockpit.html` are not the
  design authority here). The existing flat `chat-thread`/`chat-message`
  rendering has NO threaded/parent-child concept today — confirmed by
  direct inspection (`data.thread.messages.map(...)`, a plain linear
  list). **Threaded-reply rendering is genuinely new UI — no
  `html-prototype/` screen, and no other real chat surface in this app
  (`ChatMessageText`'s own shared usage across every agent panel and both
  Cockpits, per `MEMORY.md` 2026-08-24), shows this pattern anywhere.
  `net-new-design-needed`.**

## Dependencies

- **Blocked by:** `REQ-SB-82-US-01` (Persisted Cockpit Chat, `Draft`, not
  yet built) — the routed reply/threaded result both need the persisted
  thread store that story builds.
- **Blocked by:** `REQ-SB-82-US-02` (Research Agent, `Draft`, not yet
  built) — this story's own fallback calls that exact capability, not a
  separate one.
- **Related to, not blocking:** `REQ-SB-82-US-03` (Moderator roster
  pre-assembly) — shares the "Meeting Moderator" concept and applies to
  whichever roster exists, pre-recommended or manually brought in; not a
  build dependency either direction.
- **Related to, genuinely unclear (not blocking, but not resolved):**
  `REQ-SB-20-US-01` (Section Hub Intelligence, **Done**) — whether this
  story's own routing mechanism reuses that story's keyword-match
  approach; not decided here (see Context).
- **External:** none new, beyond whatever Hermes-side mechanism
  `/plan-tasks` selects for reaching a routed Expert (see the disclosed
  technical risk in Context).

## Constraints

- Exactly one Expert (or the Research Agent fallback) ever responds to a
  given question — never a broadcast to every brought-in Expert
  (Scenarios 1, 5), and never a silent dead-end (Scenario 2).
- The Research Agent fallback must never block the live chat (Scenario
  3).
- A threaded async result must land attached to the SPECIFIC question
  that triggered it, and must never reorder or disturb the chat's own
  real-time message sequence (Scenario 4).
- This story never fabricates an Expert's reply when none of the
  brought-in Experts can genuinely answer (Scenario 2) — matching this
  project's standing honesty posture.
- The exact routing-decision mechanism, the tie-break rule, and the
  threaded-reply's exact visual treatment are all left open — not
  decided here (see Context).

## Implementation Tasks

<!-- Analyst-authored starting point, non-authoritative — the decomposer's
own table at /plan-tasks supersedes this. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-82-US-04-T01 | backend | Routing-decision mechanism (mechanism TBD) + real per-Expert reply, composed against a real, addressable Hermes agent | `app/business/cockpit/`, `app/business/hermes/` | TBD at `/plan-tasks` |
| REQ-SB-82-US-04-T02 | backend | Async, non-blocking Research Agent fallback dispatch + threaded-result write into the persisted thread | `app/business/cockpit/` | TBD at `/plan-tasks` |
| REQ-SB-82-US-04-T03 | frontend | New threaded-reply rendering in the Chat tab | `src/frontend/src/features/cockpit/Cockpit.tsx` | TBD at `/plan-tasks` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Roster pre-assembly (the "Recommended" grouping)** — `REQ-SB-82-US-03`,
  not this story.
- **The Research Agent's own research/write capability** — `REQ-SB-82-
  US-02`, not this story; this story only calls it.
- **Persisting the roster/message store itself** — `REQ-SB-82-US-01`, not
  this story; this story writes into that store, doesn't build it.
- **Resolving the exact routing-decision algorithm or tie-break rule** —
  left open, flagged for a human/architect decision (see `## Notes`).
- **Any change to `REQ-SB-20`'s own Hub-routing mechanism or behavior** —
  a separate, agent-initiated mechanism; unaffected by this story, same
  as `REQ-SB-43-US-01`'s own precedent for the two mechanisms coexisting.

## Notes

**Prototype parity (Cockpit.tsx's real current layout):**

- The existing flat chat-thread rendering — **Specced for non-threaded
  messages** (Scenario 1 — a normal routed reply still renders as an
  ordinary message, same as today). **Not specced for threading** — see
  below.
- Threaded/parent-child reply rendering (Scenario 4) — **`net-new-
  design-needed`.** Confirmed, by direct inspection, that no real chat
  surface anywhere in this app (Cockpit or otherwise) has ever rendered a
  threaded reply; the shared `ChatMessageText`/`.chat-thread` convention
  is flat-list-only today.

**Why `gate: flagged`:**

1. No material assumption was made filling a genuine PRD gap in the
   Gherkin itself — every scenario asserts only what the PRD's own text
   commits to observably. The open items below are genuine, disclosed
   gaps, not guesses.
2. `REQ-SB-82` is not marked `<!-- Draft -->`/unfinalised in the PRD.
3. N/A here (architect/ADR trigger) — but `/plan-tasks` should expect a
   real, load-bearing architectural investigation (see the disclosed
   technical risk in Context) before committing to a routing design —
   this is very plausibly heading toward a new/superseding ADR, similar
   to how `REQ-SB-25` itself triggered one for a comparable reason
   (moving past keyword-match toward something needing real
   orchestration).
4. No `ESCALATIONS.md` entry was written by this pass.
5. **Even after being split out of the larger Moderator mechanism (see
   Context), this remaining scope is still substantial** — live routing +
   async dispatch + threaded UI, against a genuinely unresolved technical
   substrate (see point 3). Kept as one story here because the three
   pieces are tightly coupled (the whole reason for async/threading IS to
   support the routing+fallback flow without blocking), but flagged as a
   real candidate for the decomposer to consider splitting further into
   tasks — or, if `/plan-tasks` finds the routing-mechanism investigation
   alone substantial, for the architect to recommend a further story
   split before tasks are cut.
6. N/A (coder trigger).
7. No contradictory PRD inputs found.
8. **The controlling flags, three real ones:** (a) the routing-decision
   mechanism and tie-break rule are genuinely unresolved by the PRD's own
   text; (b) `net-new-design-needed` — threaded-reply rendering has zero
   precedent anywhere in this app; (c) the disclosed technical risk in
   Context — this codebase's real, current Hermes architecture has no
   proven live multi-turn back-channel between separate agent profiles,
   which is squarely what "route a live question to one Expert inside a
   shared thread" needs.

**What to do next:** `/plan-tasks` should investigate, against the REAL
Hermes agent-reaching primitives (`HermesChatSession`, the WS protocol,
the stateless `/agents/{id}/chat` REST call), whether live per-question
routing into one shared thread is buildable by composing what exists or
needs new session-continuity infrastructure, BEFORE committing to a
design — this is the single highest-risk open item across all of
`REQ-SB-82`'s substories. Separately, run `/design` for the threaded-reply
UI, and decide the routing-decision mechanism/tie-break rule.

gate: flagged 2026-08-25 — unclear-requirement (routing mechanism,
tie-break rule) plus net-new-design-needed (threaded-reply UI) plus a
disclosed real architectural risk (no live cross-agent back-channel
exists in the current Hermes architecture). A `REVIEW-QUEUE.md` entry has
been added.
