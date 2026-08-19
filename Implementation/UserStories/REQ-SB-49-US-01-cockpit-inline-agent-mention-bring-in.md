---
id: REQ-SB-49-US-01
title: Cockpit Inline @agent_id Mention — Bring an Agent Into the Shared Thread From the Chat Input
requirement_ids: [REQ-SB-49]
requirement_section: "REQ-SB-49: Cockpit @Mentions"
phase: P1
status: Done
gate: clear
gate_reason: ""
sprint: "SPRINT-046"
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-49-US-01 — Cockpit Inline @agent_id Mention — Bring an Agent Into the Shared Thread From the Chat Input

## Story

**As a** Second Brain user working inside a Meeting or Inbox Cockpit
**I want** to type `@agent_id` directly in the chat message box to bring
that agent into the shared thread
**So that** I can pull in the Expert I need without leaving the chat input
to find and click the left panel's "+ Bring in" button

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-49: Cockpit @Mentions* — "Inside a
  Cockpit's (`REQ-SB-43`/`REQ-SB-44`, shipped) chat, typing `@agent_id`
  mentions and brings that agent into the shared thread inline (an
  alternative to the left panel's bring-in list)... **Acceptance:** Typing
  `@agent_id` in a Cockpit chat message brings that agent into the shared
  thread inline."
- **PRD breadcrumb (2026-08-14, operator-directed, verbatim example):**
  `"@meeting_Expert Take this file and Extract the info and Store it."`
  Two genuinely distinct mechanisms are bundled under one `@mention`
  syntax; this story covers only the first — the inline bring-in shortcut.
  The second (a person-directed instruction implying a Person-note edit)
  is covered by the sibling story `[[REQ-SB-49-US-02]]`, split out per
  this project's own "no independent value alone" test: this shortcut is
  fully usable, testable, and shippable on its own, with no dependency on
  `REQ-SB-49-US-02`'s materially higher-risk vault-write capability.
- **Grounded directly in the real, shipped Cockpit code (`REQ-SB-43-US-01`/
  `REQ-SB-44-US-01`, both `Done`, `SPRINT-040`/`041`), not re-derived from
  scratch:**
  - `POST /cockpit/{subject_kind}/{stem}/bring-in` (`app/api/
    cockpit_router.py`) → `threads.bring_in_agent(subject_kind, stem,
    agent_id)` (`app/business/cockpit/threads.py`) is the exact, real,
    already-idempotent bring-in action the left panel's "+ Bring in"
    button already calls (`Cockpit.tsx`'s `onClick={() =>
    bringInAgent(subjectKind, subjectNoteStem, agent.id).then(reload)}`).
    This story's inline `@agent_id` mention triggers this SAME call —
    never a second, parallel bring-in code path.
  - The left panel's "Available Agents" list (`fetchAgentList()` →
    `GET /agents`, `agentsApiClient.ts`'s `AgentSummary { id, name, type,
    section_id }`) is the same, single, real, vault/registry-derived list
    both the button and this story's own `@`-suggestion/match source read
    from — never a second, independently-maintained agent list.
  - The chat input (`Cockpit.tsx`'s `chat-input-row`) is a single plain
    text `<input>` today, with no `@`-parsing or autocomplete of any kind.
- **Resolved here, per this task's own explicit "low ambiguity, resolve
  yourself" direction — a sane default, not a guess filling a genuine
  gap:**
  - **Matching:** `@token` matches a real agent whose `id` OR whose `name`
    (case-insensitively, ignoring spaces in `name`) equals `token` — e.g.
    `@vault-qa` matches `id: "vault-qa"`; `@VaultQA` or `@vaultqa` matches
    `name: "Vault Q&A"` loosely. No fuzzy/partial matching, no ranking —
    an unmatched token is left as plain literal text (Scenario 3).
  - **Trigger point:** sending the message (clicking Send / pressing
    Enter) is what triggers the bring-in call(s) for every `@token` in
    that message that resolves to a real agent, before the message itself
    is sent to the (now-updated) set of brought-in agents — mirroring the
    button's own "bring in, then the thread now includes this agent for
    every subsequent message" sequencing, applied to the SAME message
    rather than only future ones.
  - **Suggestions while typing:** a lightweight, standard `@`-mention
    autocomplete affordance (a short dropdown of matching real agents,
    from the same `fetchAgentList()` list) appears once the user types
    `@` plus at least one character — this is a well-understood, common
    chat UI pattern; the exact dropdown visual treatment is left to the
    coder to build against this project's existing `.card`/`.item-list`
    design-system conventions (already approved in `meeting-cockpit.html`/
    `inbox-cockpit.html`), not a `/design` pass. See `## Notes` →
    Prototype parity.
- **Depends on:** `[[REQ-SB-43-US-01]]` (Meeting Cockpit, **Done**),
  `[[REQ-SB-44-US-01]]` (Inbox Cockpit, **Done**) — both ship the exact
  bring-in call, chat thread, and Available Agents list this story
  extends. No other new backend mechanism is required.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then
edge cases and error states. Do NOT add AC-IDs — the decomposer assigns them
at /plan-tasks. -->

### Scenario 1: Typing a real agent's `@agent_id` and sending the message brings that agent into the shared thread

```gherkin
Given a Cockpit is open with a chat message box, and "vault-qa" is a real
    agent not currently brought into this thread
When the user types a message containing "@vault-qa" and sends it
Then the exact same bring-in action the left panel's "+ Bring in" button
    would trigger is called for "vault-qa"
  And "vault-qa" is now shown as brought into this Cockpit's shared thread,
    identically to using the button
  And "vault-qa" is able to respond to this same message, within the
    single shared thread
```
<!-- AC-ID: REQ-SB-49-US-01-AC-01 -->

### Scenario 2: Mentioning an agent already brought into the thread is idempotent — a no-op, not a duplicate

```gherkin
Given a Cockpit's shared thread already has "vault-qa" brought in
When the user sends a message containing "@vault-qa" again
Then no duplicate bring-in entry is created — "vault-qa" remains brought
    in exactly once, matching the existing bring-in action's own
    idempotent behaviour
```
<!-- AC-ID: REQ-SB-49-US-01-AC-02 -->

### Scenario 3: A mentioned token that matches no real agent is left as plain text — never a fabricated match

```gherkin
Given a Cockpit is open with a chat message box
When the user sends a message containing "@not_a_real_agent", a token that
    matches neither the id nor the name of any real agent
Then no agent is brought into the thread for that token
  And the message is sent as ordinary chat text, with "@not_a_real_agent"
    left exactly as typed — never silently matched to the nearest-sounding
    real agent
```
<!-- AC-ID: REQ-SB-49-US-01-AC-03 -->

### Scenario 4: Mentioning more than one real agent in the same message brings all of them in

```gherkin
Given a Cockpit is open with a chat message box, and "vault-qa" and
    "people-producer" are both real agents not yet brought into this thread
When the user sends a single message containing both "@vault-qa" and
    "@people-producer"
Then both agents are brought into the same shared thread
  And both are able to respond within that one shared thread, per
    `REQ-SB-43-US-01`'s own unified-thread behaviour
```
<!-- AC-ID: REQ-SB-49-US-01-AC-04 -->

### Scenario 5: An `@`-mention autocomplete suggests real, currently-available agents as the user types

```gherkin
Given a Cockpit is open with a chat message box
When the user types "@" followed by at least one character in the message
    box
Then a suggestion list of real agents whose id or name matches what has
    been typed so far is shown, drawn from the same Available Agents list
    the left panel already renders
  And no suggestion is ever shown for an agent that does not really exist
```
<!-- AC-ID: REQ-SB-49-US-01-AC-05 -->

## Affected Screens

- `html-prototype/meeting-cockpit.html` — the chat input row
  (`.chat-input-row`, currently a plain `<input>`) gains `@`-mention
  parsing on send and a live suggestion affordance while typing.
- `html-prototype/inbox-cockpit.html` — same chat input row change,
  shared component (`Cockpit.tsx`).

## Dependencies

- **Blocked by:** `[[REQ-SB-43-US-01]]` (Meeting Cockpit, **Done**) —
  supplies the real `bring_in_agent`/shared-thread mechanism and chat
  input this story extends.
- **Blocked by:** `[[REQ-SB-44-US-01]]` (Inbox Cockpit, **Done**) — the
  same shared `Cockpit.tsx` component/chat input, reused for email.
- **Related to:** `[[REQ-SB-49-US-02]]` — the sibling story covering the
  person-directed-instruction half of the same `@mention` syntax; the two
  are independently valuable and independently shippable, but share the
  same chat-input parsing surface (a message may contain both an
  `@agent_id` and an `@PersonName` token at once — this story's parsing
  must not consume/break a person-name token intended for the sibling
  story's own handling).
- **External:** none new.

## Constraints

- **Never a second bring-in code path.** An inline `@agent_id` mention
  must call the exact same real mechanism (`threads.bring_in_agent` via
  `POST /cockpit/{subject_kind}/{stem}/bring-in`) the existing "+ Bring
  in" button already calls — no parallel/duplicate implementation.
- **Never fabricate a match.** An `@token` that does not resolve to a
  real, currently-existing agent (by id or name) is left as plain text,
  never guessed at or silently corrected to the nearest real agent.
- **Idempotent.** Mentioning an already-brought-in agent again must not
  create a duplicate or error.
- **Suggestions are always vault/registry-derived**, from the same
  `fetchAgentList()` source the left panel already uses — never a
  hardcoded or stale list.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-49-US-01-T01 | frontend | `@`-token parsing on send (bring-in wiring, idempotent/multi-mention, honest no-match), send-control gating fix, and live prefix-filtered `@`-autocomplete dropdown | `src/frontend/src/features/cockpit/Cockpit.tsx` | `Implementation/Tasks/REQ-SB-49-US-01-T01-inline-agent-mention-parsing-and-gating.md` |

**Decomposer note (2026-08-14):** collapsed the analyst's provisional
two-row placeholder table into one task. `cockpitApiClient.ts` needs no
new/changed function — `bringInAgent`/`sendCockpitMessage` are reused
exactly as they already exist — so a second `T02` file would have had no
real content of its own. The entire change (token extraction/resolution,
bring-in-before-send, the gating fix, and the live suggestion dropdown) is
one coherent diff inside one file (`Cockpit.tsx`), well within one working
session — not oversized.

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, no frontend test runner scaffolded yet; all ACs verified live via a real CDP browser session
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

**Coder's pass (2026-08-14, `/implement-sprint SPRINT-046`):** `T01` built
and verified live (all 5 ACs, real running frontend/backend, real
`vault-qa`/`people-producer` agents, CDP-driven headless Edge). One
scope-internal judgement call (wiring against `REQ-SB-51-US-01`'s already-
landed `bringInCandidates`, per the story's own pre-authorized soft
dependency) — logged in `T01`'s own Implementation Log, not an
escalation. Story `status: Done`, `gate: clear` (unchanged — no new
trigger fired).

## Non-Goals / Out of Scope

- **Person-directed instructions (`@PersonName`) and any resulting
  Person-note edit** — entirely out of scope here; see `[[REQ-SB-49-US-02]]`.
- **A new backend bring-in mechanism** — this story is a frontend-parsing
  + existing-call-wiring change only; `threads.bring_in_agent` is reused
  unmodified.
- **Fuzzy/ranked matching, or matching a partial substring of an agent's
  name** — exact (case-insensitive) id/name match only, per the resolved
  default above.
- **Any change to `REQ-SB-20`'s own Hub-routing `@`-free mechanism** —
  unrelated and unaffected.

## Notes

**Prototype parity (meeting-cockpit.html / inbox-cockpit.html — chat input row only):**

- `.chat-input-row`'s plain-text `<input>` — **Specced.** This story adds
  `@`-token parsing on send (Scenarios 1-4) and a live suggestion dropdown
  while typing (Scenario 5).
- The suggestion dropdown's own exact visual treatment (position, styling)
  — **Deferred to coder improvisation**, not `/design`: this is a common,
  well-understood chat-UI pattern (`@`-mention autocomplete), and the
  Cockpit's own `.card`/`.item-list`/`.badge` conventions already give a
  coder enough approved visual vocabulary to build it consistently,
  matching this session's own established precedent of not gating a
  small, standard interaction addition to an already-approved screen
  behind a fresh `/design` pass (distinct from `REQ-SB-43`/`44`'s own
  full net-new 3-panel workspace, which genuinely did need one).
- Everything else on both screens (attendee/people chips, research
  panel, message list, per-Expert attribution) — **unchanged, out of
  scope** for this story.

**Why `gate: clear`:** No MUST-FLAG trigger fired. (1) No material
assumption beyond the sane, explicitly pre-authorized defaults named in
Context (exact id/name matching, send-time trigger, common autocomplete
pattern deferred to coder improvisation — not a gap-filling guess). (2)
`REQ-SB-49` is not `<!-- Draft -->`/unfinalised in the PRD. (3) N/A
(architect trigger). (4) No `ESCALATIONS.md` entry written. (5) Not
oversized — a small, single-surface parsing addition reusing an
already-Done backend mechanism end-to-end. (6) N/A (coder trigger). (7)
No contradictory inputs. (8) No genuinely unclear or multiply-valid
scoping question remains — this half of `REQ-SB-49` is low-ambiguity by
the task's own explicit assessment, resolved directly above.

gate: clear 2026-08-14 — no triggers fired (no ADRs touched, no material
assumption beyond pre-authorized sane defaults, requirement finalised,
mechanism reuses REQ-SB-43-US-01/REQ-SB-44-US-01's already-Done bring-in
call unmodified).

**Architect pass (2026-08-14):**

Architecture scope: §Cockpit Inline `@agent_id` Mention — chat-input
parsing over the existing bring-in call (REQ-SB-49-US-01, applies
ADR-036, no new ADR) — `Implementation/Architecture/architecture.md`.

No new ADR. This is client-side parsing/UI logic layered over a single,
already-`Accepted`, unmodified backend call (`ADR-036`'s
`threads.bring_in_agent` / `POST /cockpit/{subject_kind}/{stem}/
bring-in`) — no new endpoint, persisted store, tool, framework, or
structural boundary. Smaller in kind than the already-settled "Skills
grouped by Tool ... applies ADR-015, no new ADR" and "Background Agents
... applies ADR-014/ADR-018, no new ADR" precedents (both touched a real
backend field/endpoint; this story touches neither).

Design recorded in architecture.md: send-time `@token` extraction
(`/@(\S+)/g`) resolved by exact, case-insensitive `id`-or-normalized-
`name` match against the SAME candidate list `Cockpit.tsx`'s "Available
Agents" panel already renders from — never a duplicate/second-fetched
list; each match calls the existing `bringInAgent(...)` before
`sendCockpitMessage(...)`; an unmatched token is left as plain text; a
repeated mention of an already-brought-in agent relies on `bringInAgent`'s
own existing idempotency (no new client-side dedupe). A live,
prefix-filtered suggestion dropdown (`/@(\S*)$/` at the cursor) reads the
same list — a looser filter than send-time's exact-match requirement,
intentionally, for a usable typing affordance; exact dropdown visual
treatment stays coder latitude per this story's own Notes.

Flagged for the decomposer/coder (not an architecture decision, a real
code fact): `Cockpit.tsx`'s Send/input `disabled={!hasExperts}` gate
conflicts with Scenario 1 (sending the very message that brings in the
first agent, with zero agents brought in beforehand) — the gate must be
relaxed or the mention-resolution pass reordered ahead of it; exact
mechanism is task-level implementation latitude.

Composition with `REQ-SB-51-US-01` (Background Agents, Ready, not yet
Done): a soft, same-source dependency, NOT a hard `depends_on`. Both
stories read the same `fetchAgentList()`-sourced list, so a Background
Agent is excluded from `@mention` matching automatically once both are
built, in either build order. If `REQ-SB-51-US-01` lands first, this
story's tasks should wire mention-matching directly against `T04`'s
filtered `bringInCandidates` list. If this story lands first, its tasks
wire against today's unfiltered `availableAgents`, and whichever
`REQ-SB-51-US-01-T04` coder lands second must additionally repoint this
story's mention-matching source at the new filtered variable — a small,
same-file follow-on edit, not a redesign. Full reasoning:
`Implementation/Architecture/architecture.md` → "Cockpit Inline
`@agent_id` Mention."

gate: clear 2026-08-14 (architect) — no ADR created or changed, no
assumptions beyond the analyst's own already-resolved defaults, no
contradiction of any Accepted ADR/PRD text/MEMORY.md constraint. Nothing
written to REVIEW-QUEUE.md or ESCALATIONS.md.

**Decomposer pass (2026-08-14):**

All 5 scenarios locked as `REQ-SB-49-US-01-AC-01`..`AC-05` (Scenario 1→
AC-01, Scenario 2→AC-02, Scenario 3→AC-03, Scenario 4→AC-04, Scenario 5→
AC-05), wording unchanged from the analyst's draft — it was already
buildable as written. One task, `REQ-SB-49-US-01-T01`, covers the whole
story (see the Implementation Tasks note above for why the analyst's
provisional 2-row table collapsed to one real task).

**Send-control gating conflict — resolved concretely, at task level, per
the architect's own explicit delegation:** the real blocker was not only
the Send button's `disabled={!hasExperts}` — the chat `<input>` itself
also carries `disabled={!hasExperts}` today, so a user cannot even TYPE
`@vault-qa` before any agent is brought in, which would make Scenario 1
impossible however the button alone is regated. `T01`'s fix: the `<input>`
becomes unconditionally typable (its own `disabled={!hasExperts}` is
dropped); only the Send button stays gated, now on
`!messageInput.trim() || (!hasExperts && !hasResolvableMention)` —
`hasResolvableMention` is the same exact-match token-resolution function
Scenario 1's own bring-in logic already needs, recomputed on every
keystroke. This makes "an `@mention` in the message text can itself
satisfy the has-an-expert precondition" true by construction, not a
guess — full mechanism in `T01`'s own Context/Notes.

**`REQ-SB-51-US-01` soft dependency:** carried forward as instructed — no
`depends_on` edge written (bare `[]`). `T01`'s own Context/Notes records
the same-source repoint obligation for whichever of the two stories'
coders lands second.

Why `gate: clear`: no MUST-FLAG trigger fired. (1) No material assumption
— the gating-fix mechanism above is a concrete, fully-reasoned resolution
of an already-flagged real code fact, not a gap-filling guess; the
architect's own Notes explicitly delegated the exact mechanism to this
level. (2) `REQ-SB-49` is not `<!-- Draft -->`/unfinalised. (3) No ADR
touched this pass. (4) No `ESCALATIONS.md` entry written. (5) Not
oversized — one file, one task, well within one working session. (6) N/A
(coder-only trigger). (7) No contradictory inputs. (8) No genuinely
unclear or multiply-valid task breakdown remained — the gating fix has
exactly one structurally-correct shape once the input's own `disabled`
prop is recognised as the real blocker, not a coin-flip between equally
valid designs. Every locked AC has a matching AC-tagged manual
verification step in `T01`'s `## Tests`; `depends_on` graph is a single
task with no edges (trivially acyclic). Story and task both advance to
`Ready`.

gate: clear 2026-08-14 (decomposer) — no triggers fired (no ADR touched,
no material assumption beyond the architect's own delegated mechanism, no
`ESCALATIONS.md` entry, not oversized, every locked AC has a tagged
verification step, `depends_on` acyclic).
