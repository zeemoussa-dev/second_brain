---
id: REQ-SB-23-US-01
title: My Day Intake Agent (Conversational) — a real chat thread that asks follow-up questions, accepts mid-conversation refinement and organizational hints, then files a vault Note
requirement_ids: [REQ-SB-23]
requirement_section: "REQ-SB-23: My Day Intake Agent (Conversational)"
phase: P1
status: Draft
gate: flagged
gate_reason: "re-spec (ESC-009) — requirement revised 2026-08-11 from one-shot autonomous filing to a real conversational agent; net-new-design-needed (the already-designed one-shot 'Quick Capture' card does not cover the revised conversational requirement); blocked by REQ-SB-25 (Real Conversational Agent Chat) — REQ-SB-25-US-01 now exists as a Draft, flagged story (specced concurrently), not yet Ready/Done; unclear-requirement — destination note kinds and REQ-SB-21 working-mode interaction remain genuinely open, per the revised breadcrumb"
sprint: ""
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-23-US-01 — My Day Intake Agent (Conversational) — a real chat thread that asks follow-up questions, accepts mid-conversation refinement and organizational hints, then files a vault Note

## Story

**As a** Second Brain user
**I want** a dedicated agent, reachable from My Day as a real chat window,
that I can hand a quick note, thought, or fact to at any point in the day —
one that can ask me follow-up questions, let me refine what I said, and
accept hints like "this was yesterday" before it files anything
**So that** the note that actually lands in my vault is accurate and
correctly placed, not a raw, unrefined dump of whatever I first typed

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-23: My Day Intake Agent
  (Conversational)* — "A dedicated agent, reachable from My Day as a real
  chat window, lets the user hand it free-form information throughout the
  day — a quick note, a thought, a fact to remember. The agent can ask
  follow-up/clarifying questions before filing, refines the user's raw text
  into a properly written note, accepts organizational hints from the user
  (e.g. 'this was yesterday') to place the information correctly, and then
  files it into the right place in the vault based on understanding what
  it's about — the same way Email Capture classifies an email by customer,
  but for arbitrary, conversational user-provided input rather than one
  fixed source." Acceptance: "The user can converse with the My Day Agent
  in a real chat thread; the agent may ask follow-up questions before
  filing; the user can refine the note's content and supply organizational
  hints (e.g. a different date) mid-conversation; the agent files the
  resulting note into the vault consistent with the existing schema
  conventions (tags and wikilinks, per the standing design rule),
  classified by what it's about."
- **This is a revision of a previously-drafted story — recorded here, not
  silently overwritten (see `## Notes` for the full "what changed and
  why").** `REQ-SB-23`'s PRD text was revised 2026-08-11 (operator-
  directed), superseding its own original same-day acceptance text ("the
  user can send free-form text... files it into the vault... classified by
  what it's about" — a one-shot input+submit, autonomous-filing design).
  `REQ-SB-23-US-01` was originally drafted against that one-shot design,
  and a `/design` pass had already produced a matching "Quick Capture" card
  (`html-prototype/my-day.html`) — that card does **not** cover this
  revised, genuinely conversational requirement (see `## Notes`'s
  Prototype parity subsection). Full escalation record:
  `ESCALATIONS.md` → `ESC-009`.
- **PRD breadcrumb (2026-08-11, operator-authored, cited verbatim, NOT
  re-decided here):** "supersedes this requirement's original one-shot/
  autonomous framing... `REQ-SB-23-US-01` (already drafted, `/design`
  already run producing a one-shot Quick Capture card in `html-prototype/
  my-day.html`) needs re-speccing and its prototype revising to match: a
  real chat thread (not a single input+submit), the agent's own follow-up
  questions, mid-conversation refinement of the note text, and explicit
  handling of user-supplied temporal/organizational hints that affect
  where/how the note is filed. Depends on REQ-SB-25 (real conversational
  agent chat — this agent needs genuine multi-turn understanding, not
  keyword matching) for its conversational mechanism. Genuinely open, not
  decided here: which note types/kinds it can file into (already-resolved
  schemas only, or can it propose a new kind?), and how working mode
  (REQ-SB-21) interacts with a conversational flow that already involves
  back-and-forth by design. Left to `/spec`."
- **Hard dependency, not yet satisfied: `REQ-SB-25` (Real Conversational
  Agent Chat).** This story's conversational mechanism (follow-up
  questions, mid-conversation refinement, understanding a temporal hint in
  context) needs a real, multi-turn, LLM-backed conversation — exactly what
  `REQ-SB-25` introduces, replacing today's keyword-substring `agent_chat.
  py` matching (`ADR-011`). Checked `Implementation/UserStories/` directly
  at the point of writing this revision: **`REQ-SB-25-US-01` now exists**
  (specced concurrently with this re-spec pass, by a parallel `/spec` run)
  as `status: Draft`, `gate: flagged` — not yet `Ready`/`Done`. Its own
  Notes explicitly name this story (`REQ-SB-23`) as a downstream dependant
  and flag an open scoping question for its `/plan-tasks` pass (whether its
  new "real conversational reply" mechanism should be built narrow or as a
  reusable primitive with this story's near-term reuse in mind). This
  story cannot actually be built until `REQ-SB-25-US-01` ships — recorded
  honestly as a real, currently-unmet dependency, following this project's
  own established pattern for depending on a not-yet-`Done` story (e.g. how
  `REQ-SB-20-US-01` recorded its dependency on `REQ-SB-18-US-01` before
  that story shipped).
- **Destination note kind(s) — re-opened by the revision, genuinely
  unclear, not resolved here.** The original story resolved this narrowly
  (fixed to the generic `Note` kind, `Work/Notes/`, never constructing a
  Person/Meeting/Customer-schema note from free text, reasoning that those
  schemas need fields free text can't reliably supply). The **revised**
  breadcrumb explicitly re-opens this exact question ("which note types/
  kinds it can file into — already-resolved schemas only, or can it
  propose a new kind?") for the conversational design specifically —
  plausibly because a real back-and-forth conversation *could* gather
  structured fields a one-shot submission couldn't (e.g. asking clarifying
  questions could fill in a Meeting's `start`/attendees, or a Person's
  role). Whether the conversational agent should still be fixed to `Note`
  only, or should be allowed to file into other already-resolved schemas
  once the conversation supplies enough structure, is a genuine product/
  architecture judgement call the revision itself flags as open — not
  guessed here. See the flag below.
- **REQ-SB-21 (Agent Working Modes) interaction — genuinely unclear, not
  resolved here.** The original story resolved confirmation-vs-autonomous
  filing from its own one-shot acceptance text (no propose-and-wait
  language, so autonomous). The revised requirement's acceptance text is
  now explicitly conversational — the agent already asks follow-up
  questions and waits for the user's replies before filing, "back-and-forth
  by design," per the breadcrumb's own words. Whether `REQ-SB-21`'s
  Supervised working mode (a *separate*, explicit approval gate before an
  action is taken) layers on top of this agent's own conversational
  back-and-forth, or whether the conversation itself already satisfies
  "human in the loop" so a Supervised gate would be redundant here, is
  exactly the question the revised breadcrumb names as open. Not decided
  here. `REQ-SB-21-US-01` remains its own `Draft`, flagged story, not yet
  built.
- **No `html-prototype/` screen covers this revised surface.**
  `html-prototype/my-day.html`'s existing "Quick Capture" card (designed
  for the prior one-shot version) is a single `.chat-input-row` (one text
  input + one Capture button) plus a flat `.item-list` history of past
  submissions — there is no chat thread, no agent-reply rendering, no
  follow-up-question affordance, and no way to show mid-conversation
  refinement or a temporal-hint exchange anywhere in it. Confirmed by
  direct inspection. This is a genuine `net-new-design-needed` gap for the
  revised requirement, not something the prior design pass already
  happens to cover — see `## Notes`.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. These scenarios replace the prior one-shot-design scenarios
entirely — this is a story revision, not an addition (see Notes). -->

### Scenario 1: Sending the agent free-form text opens a real chat thread

```gherkin
Given the user is on the My Day surface
When the user sends the My Day Agent a quick note, thought, or fact
Then a real chat thread opens (or continues) showing the user's message
  And the agent's reply appears in the same chat thread
```

### Scenario 2: The agent asks a follow-up question before filing

```gherkin
Given the user has sent the My Day Agent free-form text that is
    ambiguous or missing information the agent needs to file it correctly
When the agent processes the message
Then the agent asks a follow-up/clarifying question in the chat thread
    instead of filing immediately
  And the note is not filed until the conversation resolves the ambiguity
```

### Scenario 3: The user refines the note's content mid-conversation

```gherkin
Given the user is in an ongoing conversation with the My Day Agent about a
    piece of information it has not yet filed
When the user sends a follow-up message that changes or adds to what they
    originally said
Then the agent incorporates the refinement into the note it will file
  And the note ultimately filed reflects the refined content, not only the
    user's first message
```

### Scenario 4: The user supplies a temporal/organizational hint that affects filing

```gherkin
Given the user is in an ongoing conversation with the My Day Agent about a
    piece of information it has not yet filed
When the user supplies an organizational or temporal hint (e.g. "this was
    yesterday")
Then the agent uses that hint to place or date the information correctly
  And the filed note reflects the user-supplied hint, not the agent's own
    default assumption
```

### Scenario 5: The agent files the resulting note, classified by what it's about, for a known customer

```gherkin
Given the user has had a conversation with the My Day Agent that
    identifies information clearly about a known customer, e.g. "ADNOC"
  And the vault already has a Customer hub note for "ADNOC"
When the conversation reaches the point where the agent files the note
Then a new Note is filed under Work/Notes/ with type "Note" and customer
    "ADNOC"
  And the note carries a "customer/adnoc" tag and a "kind/note" tag
  And the note's body contains an inline wikilink to the ADNOC Customer hub
    note
```

### Scenario 6: A conversation with no identifiable customer files an unclassified Note

```gherkin
Given the user has had a conversation with the My Day Agent that is not
    about any known customer (e.g. a personal reminder)
When the conversation reaches the point where the agent files the note
Then a new Note is filed under Work/Notes/ with type "Note" and no customer
    field set
  And the note carries only a "kind/note" tag, with no customer tag
  And the note's body contains no customer wikilink
```

### Scenario 7: Two separate conversations the same day file two distinct notes

```gherkin
Given the user has already completed one conversation with the My Day
    Agent today that resulted in a filed note
When the user starts a second, separate conversation about something
    different the same day
Then both conversations result in two distinct Note files, neither
    overwriting the other
  And each note's title reflects its own content, not a generic placeholder
```

### Scenario 8: The user's conversation is preserved even if the agent cannot determine where to file

```gherkin
Given the user is in a conversation with the My Day Agent
When the agent is unable to determine where or how to file the
    information, even after asking follow-up questions
Then the agent honestly tells the user it could not determine where to
    file it
  And the conversation and the user's originally-provided content are not
    silently discarded
```

### Scenario 9: The agent is reachable from the My Day surface as a real chat window

```gherkin
Given the user is viewing the My Day dashboard
When the user looks for a way to talk to the My Day Agent
Then a real chat window is visible and reachable directly from My Day,
    without navigating to the Agents Map or any other page first
```

## Affected Screens

- `html-prototype/my-day.html` — the existing "Quick Capture" card (a
  single input+submit row, designed for the superseded one-shot version)
  **needs to be replaced with a real chat-thread surface** — reachable
  directly from My Day, showing the user's messages, the agent's replies
  (including follow-up questions), and the eventual filed-note
  confirmation. **Not present in the approved prototype** in this shape —
  the existing card does not cover a multi-turn conversation. See the flag
  below. (Revising the prototype itself is the designer's task at
  `/design`, not done here.)

## Dependencies

- **Blocked by:** `REQ-SB-25` (Real Conversational Agent Chat,
  `REQ-SB-25-US-01`, `Draft`, `gate: flagged`) — **now specced (concurrently
  with this re-spec pass), but not yet `Ready`/`Done`.** This story's
  follow-up-question/refinement/hint-understanding behaviour needs a real,
  multi-turn LLM-backed conversation mechanism, which `REQ-SB-25`
  introduces (replacing today's keyword-substring `agent_chat.py`
  matching). **Not satisfied yet as of this spec pass** — `REQ-SB-25-US-01`
  itself still needs its own `/plan-tasks` pass (including a superseding
  ADR over `ADR-007`/`ADR-011`) and a full build before this story can
  build against it.
- **Blocked by:** `REQ-SB-12-US-02` (`Done`) — the My Day surface this
  story's chat entry point attaches to must exist first. Satisfied.
- **Related to:** `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`
  → "Generic customer-related Notes" — the schema this story's filing
  currently targets by precedent (`Work/Notes/`, `type: Note`) — **but see
  the destination-kind flag below; this may not be the final answer for the
  conversational design.**
- **Related to:** `customer_hub_linking.ensure_hub_note_and_link` — reused
  as-is for the customer wikilink, same mechanism Email/Meeting notes
  already use, unchanged by this revision.
- **Related to, genuinely unclear (not blocking, but not resolved):**
  `REQ-SB-21` (Agent Working Modes, `REQ-SB-21-US-01`, `Draft`, flagged,
  not yet built) — how a Supervised working-mode gate would interact with
  this agent's own conversational back-and-forth is an open question, per
  the revised breadcrumb. See the flag below.
- **Related to, not blocking:** `REQ-SB-19` (Per-Agent LLM Provider
  Selection, `REQ-SB-19-US-01`, `Done`) — once this story's real chat
  mechanism is built (via `REQ-SB-25`), it will plausibly route through
  Provider selection the same way `REQ-SB-25` itself does; not resolved
  here, follows from whatever `REQ-SB-25` establishes.
- **External:** none new.

## Constraints

- **Real, multi-turn conversation, not one-shot input+submit** — this is
  the central thing that changed in this revision. Do not build a single
  text-box-and-submit UI; the user and agent must be able to exchange
  multiple messages before a note is filed.
- **The agent may ask follow-up/clarifying questions before filing** — not
  every submission necessarily needs one, but the mechanism must support
  the agent initiating a question and waiting for the user's reply.
- **Mid-conversation refinement and organizational/temporal hints must be
  incorporated into the note actually filed** — the filed note is not
  fixed at the moment of the user's first message.
- **Standing tags-and-wikilinks rule applies** — every filed note with an
  identified customer must carry both the `customer/<slug>` tag and an
  inline `[[Hub]]` wikilink; a note with no identified customer carries
  neither (unchanged from the original story's resolution).
- **Destination note kind(s) — left open, not decided here** (see the flag
  below). Do not assume the answer is still "fixed to `Note` only" just
  because that was the prior, superseded story's resolution — the revised
  breadcrumb explicitly re-opens this question.
- **Working-mode (`REQ-SB-21`) interaction — left open, not decided here**
  (see the flag below).
- **The user's conversation/content must never be silently lost** (Scenario
  8) — mirrors the prior story's "never silently discard on failure"
  constraint, extended to the conversational shape (an agent that cannot
  determine where to file must say so honestly, not go silent).
- This story cannot actually be built until `REQ-SB-25` (Real Conversational
  Agent Chat) exists and ships — a currently-unresolvable dependency, not a
  guess to work around.
- Filenames must not collide across same-day conversations (mirrors
  `MEMORY.md`'s standing "never build a filename from date+subject alone"
  constraint) — exact uniqueness mechanism left to `/plan-tasks`.

## Implementation Tasks

<!-- Left for the architect/decomposer at /plan-tasks, once REQ-SB-25 exists
and the flagged open questions below are resolved. -->

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **A one-shot, single input+submit filing flow** — explicitly superseded
  by this revision; do not build the prior design.
- **Filing into any schema other than the generic `Note` kind, unless the
  open destination-kind question below is resolved to allow more** —
  pending the flagged decision; do not silently expand scope in either
  direction.
- **Proposing brand-new `kind/` values** — not asked for by either the
  original or revised requirement text.
- **A `REQ-SB-21` Supervised-mode approval gate layered on top of this
  agent's own conversational flow** — the interaction between the two is
  explicitly an open question (see the flag below), not built here either
  way.
- **Registering this agent on the Agents Map / Agent Settings panel** —
  unchanged from the prior story's resolution; the requirement's acceptance
  text only requires reachability from My Day.
- **Routing through the Provider-selection mechanism (`REQ-SB-19`)
  directly in this story** — follows from whatever `REQ-SB-25` establishes
  for its own conversational mechanism; not decided independently here.
- **Editing or deleting a filed note, or a past conversation, after the
  fact** — out of scope; the vault's own Obsidian editing capability
  already covers note edits, same as every other note kind.

## Notes

**What changed in this revision, and why (2026-08-11):** `REQ-SB-23`'s PRD
text was revised the same day it was originally written, superseding its
own one-shot/autonomous framing with a genuinely conversational one. This
story is revised **in place** (same file, same ID `REQ-SB-23-US-01`) rather
than as a new story, because it had never advanced past `Draft` — no
tasks were ever created against it, no ACs were ever locked, so there is no
completed downstream artefact this revision would need to unwind or
contradict (Pipeline.md's "specs are append-only" hard rule protects
`Done` stories specifically; a still-`Draft` story is exactly what `/spec`
is expected to keep refining). Concretely, this pass:

- Replaced every Acceptance Criteria scenario. The prior 5 scenarios
  (customer-classified one-shot filing, unclassified one-shot filing,
  same-day no-collision, classification-failure text preservation,
  reachability) are gone, replaced by 9 new scenarios reflecting a real
  chat thread, agent-initiated follow-up questions, mid-conversation
  content refinement, mid-conversation temporal/organizational hints, and
  conversational variants of the same-day-no-collision, content-
  preservation, and reachability guarantees the prior version also cared
  about (Scenarios 7-9 are the direct conversational descendants of the
  prior Scenarios 3/4/5 — same underlying guarantee, new shape).
- Added a hard, currently-unresolvable dependency on `REQ-SB-25` (Real
  Conversational Agent Chat) — the prior version's classification mechanism
  (a single-shot Compass call, mirroring `email_classification.py`) is no
  longer sufficient; a genuine multi-turn conversation needs `REQ-SB-25`'s
  mechanism, which does not yet have a story.
- **Re-opened, not re-resolved:** the destination-note-kind question and
  the `REQ-SB-21` working-mode interaction question. The prior version had
  closed both (fixed to `Note` only; autonomous filing, no working-mode
  interaction). The revised requirement's own breadcrumb explicitly
  reopens both for the conversational design — this pass does not
  re-guess them; they are flagged below, same as the first time this
  story was drafted flagged its own single open question.
- Full escalation record of this re-spec: `ESCALATIONS.md` → `ESC-009`.

**Prototype parity (my-day.html):**

- Existing dashboard (day-section-grid + counts, including the Pending
  Approvals card) — **N/A**, untouched by this story.
- The existing "Quick Capture" card (input + Capture button + flat
  `.item-list` history) — **superseded, not covered.** It was designed for
  the prior one-shot version; it has no chat thread, no agent-reply
  rendering, no follow-up-question affordance, and no way to depict
  mid-conversation refinement or a temporal-hint exchange. **This is a
  genuine `net-new-design-needed` gap for the revised requirement — the
  prior `/design` pass's approval does NOT count as coverage for this new
  shape.** The designer's revision of this screen (per the task that
  requested this re-spec) is separate work, not performed here.

**Why the destination-note-kind question is flagged, not resolved by
reusing the prior story's answer:** the prior resolution ("fixed to `Note`
only, because free text can't reliably supply a Meeting's/Person's
structured fields") was reasoned specifically against a one-shot
submission. A real, multi-turn conversation could plausibly gather
structured fields a one-shot message couldn't (the agent could simply ask
for them) — whether the conversational agent should still be `Note`-only,
or should be allowed to file into other already-resolved schemas once the
conversation supplies enough structure, is a genuine product/architecture
call the revision's own breadcrumb names as open. Guessing either way here
would risk either under-building (artificially capping a genuinely more
capable conversational agent) or over-building (constructing structured
notes from a mechanism never asked to do that). Left to the human.

**Why the `REQ-SB-21` interaction question is flagged:** the revised
requirement's own conversational back-and-forth (follow-up questions,
waiting for the user's replies) already resembles "human in the loop" —
whether a separate Supervised-mode approval gate on top of that is
redundant, complementary, or needs its own distinct UI treatment is
exactly what the revised breadcrumb names as open, not decided here.
`REQ-SB-21-US-01` itself remains `Draft`, unbuilt.

gate: flagged 2026-08-11, gate_reason: re-spec (`ESC-009`) +
net-new-design-needed + blocked-by-REQ-SB-25-US-01 (Draft, not yet
Ready/Done) + unclear-requirement (destination kinds, REQ-SB-21
interaction). REQ-SB-23
itself is finalised PRD text (no `<!-- Draft -->` marker) — the flags are
about the story's re-spec, its now-stale prototype coverage, its
currently-unmet hard dependency, and two genuinely re-opened product
questions, not about the requirement's own finalization state. A
`REVIEW-QUEUE.md` entry has been added.
