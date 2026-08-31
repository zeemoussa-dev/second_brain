---
id: REQ-SB-82-US-06
title: Live-question routing fix (short-reply shortcut + always-on LLM moderator) and reply-to-message, in both Cockpit and the single-agent Chat panel
requirement_ids: [REQ-SB-82]
requirement_section: "REQ-SB-82: Cockpit Mechanics — Prep, Research, and Moderation"
phase: P2
status: Done
gate: flagged
gate_reason: "All 8 tasks (T01-T08) built and Done 2026-08-31; every locked AC (AC-01 through AC-08) verified live with a real positive result -- see each task's own Implementation Log. gate stays flagged (unchanged from the decomposer pass): the pending human ADR-011/ADR-012 review (trigger-3, architect-appended this story's own run) is a human-only step the coder cannot clear. The two narrower items the decomposer left open are both now resolved by the real build: (a) Compass gpt-oss-120b credentials -- T02/T03 both additionally ran a real, disclosed live round trip against the real .env credential (see their own Implementation Logs; T05's own AC-02 happy-path remains monkeypatch-scoped per its own Tests block, a narrower, still-open item for the human's own REVIEW-QUEUE.md read); (b) the reply-to-message UI's visual treatment -- T07 (Cockpit) and T08 (AgentChatPanel) both built and live-verified their own decomposer-authored DOM-structural ACs; the non-blocking design spot-check against the resulting shape is now genuinely actionable (both surfaces built), not merely anticipated. ESC-059/REQ-SB-82-US-04 reconciliation already resolved 2026-08-31 (see REVIEW-QUEUE.md, that story is now Done/gate:clear). See REVIEW-QUEUE.md for the full breakdown."
sprint: SPRINT-078
created: 2026-08-31
updated: 2026-08-31
---

# REQ-SB-82-US-06 — Live-question routing fix (short-reply shortcut + always-on LLM moderator) and reply-to-message, in both Cockpit and the single-agent Chat panel

## Story

**As a** Second Brain user chatting with multiple Experts in a Meeting/Inbox
Cockpit (or with one Agent in the standalone single-agent Chat panel)
**I want** a short, low-signal reply like "Yes" to go straight back to
whoever I was just talking to, a real reasoning pass (not a keyword
coincidence) to decide who answers a genuinely new question, and the
ability to explicitly mark a new message as a reply to one specific earlier
message
**So that** a plain acknowledgment never gets hijacked by a different Expert
or the Research Agent again, an ambiguous question gets routed by something
that actually reasons about it instead of guessing on a shared word, and I
can point at exactly which earlier point I'm following up on in either chat
surface

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-82: Cockpit Mechanics — Prep,
  Research, and Moderation*, "Meeting Moderator" bullet — "During the
  meeting, routes each question to the ONE Expert it actually belongs to
  instead of broadcasting to everyone brought in." PRD breadcrumb (verbatim,
  2026-08-25 operator): "Direct Messages to the Write Agent when I ask a
  Question instead of having my Questions Goes to all Agents at the same
  time." **Reply-to-message itself is not literal PRD text** — it is a new
  capability the operator asked for while designing THIS fix (captured in
  full in `Implementation/Plans/2026-08-31-cockpit-live-routing-and-reply-
  to-message.md`), the same way `REQ-SB-82-US-04`'s own `@mention`
  override and Customer-Section fallback were operator elaborations made
  during live build sessions, not pre-written PRD text — directly serving
  the same "route my question correctly" intent the PRD's own text already
  states, not a scope invention.
- **Origin — a real, reproducible bug, root-caused against the actual
  code, not guessed:** operator report, verbatim: "When an Agent Respond to
  something and I say Yes a different Agent Picked the thread." Confirmed
  live by direct reading of `app/business/cockpit/moderator.py`'s own
  module docstring ("no LLM call, no Hermes profile involvement") and its
  `route_question` — pure tokenized keyword-overlap between the message
  text and each brought-in agent's own `name`/`description`. A low-signal
  reply like "Yes" carries no domain vocabulary, so it can't score against
  whoever just answered and falls through to a coincidental match, the
  "suggest an Expert" honest system message, or the Research Agent
  fallback. There is no "who answered last" concept anywhere in
  `chat_store.py`'s own thread schema
  (`{"brought_in_agent_ids": [...], "messages": [...],
  "recommended_agent_ids": [...]}` — confirmed by direct reading, no
  `last_answering_agent_id`-shaped field exists).
- **This is one of six substories `REQ-SB-82` now splits into — see
  `REQ-SB-82-US-01`'s own Context for the original five-way split
  rationale.** This story resolves the specific open sub-question
  `REQ-SB-82-US-04`'s own file names ("the exact routing-decision
  mechanism... is genuinely unresolved") — but see the important
  correction immediately below: that mechanism turns out to be LESS
  unresolved, and this story's own remaining gap NARROWER, than
  `REQ-SB-82-US-04`'s still-`Draft` file currently states.
- **A real, disclosed correction to the planning session's own
  investigation, found by this pass's own direct code-reading, 2026-08-31
  (`ESCALATIONS.md` → `ESC-059`):** the plan doc's Origin section is
  accurate about `moderator.py` remaining pure keyword-overlap today (see
  above) — but `app/business/cockpit/chat_turn.py`, which the plan doc
  frames as part of the still-open problem, is **already a substantially
  built, live, CHANGELOG-documented mechanism** (`CHANGELOG.md`'s own
  multiple dated `feat:`/`fix: REQ-SB-82-US-04` entries): live per-question
  routing scoped to the brought-in roster, an explicit `@mention` override
  ("give me the Ability to Force Redirection to Agent... with @"), a
  genuine tie-break (never guesses — falls back to the Research Agent), an
  honest "no one here looks right, try X" suggestion before ever falling
  back to research, a Customer-Section fallback agent, fully async
  background dispatch with an "X is typing…" indicator, and a real
  `reply_to_message_id` threaded-reply mechanism. `chat_store.py`'s own
  `append_message` already gives every message a real `id` and an optional
  `reply_to_message_id` (its own docstring: "(REQ-SB-82-US-04)").
  `Cockpit.tsx` already renders the threaded "↳ replying to: …" strip for
  these auto-threaded replies. **None of this changes the design decisions
  already made with the operator for THIS story (short-reply shortcut,
  always-on LLM moderator, reply-to-message as a hint vs. context-anchor) —
  those stand as resolved.** What it changes is the accurate shape of what
  is genuinely still missing (see below) versus what this story can build
  directly ON TOP OF as already-real infrastructure. `REQ-SB-82-US-04`'s
  own story file (`status: Draft`, `gate: flagged`, still dated
  2026-08-25) was never updated to reflect this shipped work, and
  `BACKLOG.md`'s `REQ-SB-82` row is equally stale on this point — logged as
  `ESC-059`, not resolved by this pass (editing another story is out of
  this `/spec` run's own bounds); the human resolving this story's own
  `REVIEW-QUEUE.md` entry should also reconcile `REQ-SB-82-US-04`'s status.
- **What is genuinely still missing, confirmed by direct reading (this is
  the real scope of this story):**
  - No "last-answering agent" concept in `chat_store.py`'s schema (needed
    for the short-reply shortcut) — confirmed above.
  - `moderator.route_question` is still pure deterministic tokenized
    overlap — no LLM call anywhere in `chat_turn.py`/`moderator.py`.
  - No Compass HTTP client exists anywhere in the real `src/backend` tree
    (confirmed by a direct search of `app/data_access/` — `compass_client.py`
    exists only inside separate, isolated `.claude/worktrees/` copies
    belonging to other/parallel work, never on this branch). `config.py`
    (`compass_base_url`/`compass_api_key`/`compass_model`, lines 10-12) and
    `.env.example` (`COMPASS_BASE_URL`/`COMPASS_API_KEY`/`COMPASS_MODEL`,
    currently blank placeholders) already anticipate it; nothing calls it.
    `providers.py`'s `Provider` record surfaces these same settings
    read-only for the System Health page only. `provider_manager.py`'s own
    `_REAL_CLIENT_PROVIDER_IDS = {"compass", "anthropic-claude"}` already
    flags Compass as `has_real_client=True` — today that flag is aspirational
    for Compass (no real client exists yet); this story is what would make
    it literally true for the first time.
  - **A real, disclosed wrinkle on the ADR question:** `provider_manager.py`'s
    own comment and `REQ-SB-36-US-01`'s own task files cite `ADR-022` as an
    already-`Accepted` decision governing `has_real_client`/provider
    plumbing and the (also real, shipped) Anthropic web-search client. Direct
    reading of `Implementation/Architecture/ADR.md` found no such entry — its
    real highest-numbered entry is `ADR-010`. Whether `ADR-022` exists under
    a different number, was decided but never actually written into the
    ledger despite being referenced as Accepted, or the ledger itself has a
    real gap, is unresolved here — `/plan-tasks`' architect step needs to
    investigate this directly before deciding whether the new Compass
    routing client extends an existing ADR or needs a fresh one.
  - No user-facing "reply to this specific message" affordance exists in
    either chat surface today. `cockpitApiClient.ts`'s own
    `sendMessage(subjectKind, stem, text)` takes plain text only — no
    `reply_to_message_id` parameter from the caller; the field that exists
    today is only ever set server-side, automatically, when a dispatched
    reply threads onto the question that triggered it. `AgentChatPanel.tsx`
    has **zero** message-id or persistence concept at all — its own local
    `ChatMessage` interface (`role`/`text`/`isError`/`activity`/
    `isStreaming`) carries no `id` field, and its send path
    (`streamChatMessage`/`sendChatMessageWithAttachment` against
    `agentsApiClient`) is a stateless streaming call, never backed by
    `chat_store.py`/the Cockpit persistence layer at all — a materially
    bigger technical gap for this surface than the plan's own "shared
    primitive" framing implies; `/plan-tasks` will very likely need a
    lighter-weight, purely client-side reply-to mechanism here (no backend
    schema change needed, since nothing here persists today), separate in
    shape from Cockpit's own DB-level `reply_to_message_id`.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then
edge cases and error states. Do NOT add AC-IDs — the decomposer assigns them
at /plan-tasks. These scenarios describe only the externally observable
routing/reply behaviour; they deliberately do not assert the exact
short-reply detection rule, the exact Compass request/response contract, or
the exact reply-to-message visual treatment — all left open per Context. -->

### Scenario 1: A short, low-signal reply goes straight back to whoever answered last, without a fresh routing decision

```gherkin
Given a Cockpit's Chat has an Expert (or the Research Agent/Customer-Section
    fallback) who just answered the user's previous question
When the user sends a short, low-signal acknowledgment message (e.g. "Yes",
    "ok", "sure", "go ahead")
Then the message is routed directly to that same agent who answered last
  And no full moderator routing decision (deterministic or LLM-based) is
    needed to reach that outcome
```
<!-- AC-ID: REQ-SB-82-US-06-AC-01 -->

### Scenario 2: A substantive question is routed by a real reasoning pass, not a coincidental keyword match

```gherkin
Given two or more Experts are brought into a Cockpit's Chat
When the user asks a substantive question (not a short/low-signal message)
Then the routing decision is produced by a real model call reasoning over
    the brought-in Experts' own name/description, the recent conversation
    history, and the new message's own text
  And exactly one Expert (or the Research Agent fallback) responds — never
    a broadcast to everyone brought in
```
<!-- AC-ID: REQ-SB-82-US-06-AC-02 -->

### Scenario 3: Marking a new message as a reply to a specific earlier message feeds the Cockpit moderator a strong hint, not a hard override

```gherkin
Given a Cockpit's Chat has more than one brought-in Expert and prior
    messages already exist
When the user marks a new message as a reply to one specific earlier
    message, then sends it
Then the routing decision takes which earlier message this new one is
    replying to into account as part of its reasoning
  And the moderator may still route to a different Expert than whoever sent
    the message being replied to, when the new message's own content
    clearly belongs elsewhere
```
<!-- AC-ID: REQ-SB-82-US-06-AC-03 -->

### Scenario 4: Marking a new message as a reply to a specific earlier message anchors context in the single-agent Chat panel, without affecting who answers

```gherkin
Given the user is in the single-agent Chat panel with an existing message
    history
When the user marks a new message as a reply to one specific earlier
    message, then sends it
Then the one agent's reply is generated with that specific earlier message
    included as anchoring context
  And there is only ever the one agent to answer — marking a message as a
    reply never changes who answers in this surface
```
<!-- AC-ID: REQ-SB-82-US-06-AC-04 -->

### Scenario 5: The LLM-based moderator still has final say even when a reply-to hint points at a specific Expert

```gherkin
Given the user marks a new message as a reply to an earlier message from
    one specific brought-in Expert (Scenario 3)
When that new message's own text clearly asks a question belonging to a
    DIFFERENT brought-in Expert's own domain
Then the routing decision sends it to the Expert whose domain the question
    actually belongs to, not automatically back to whoever sent the message
    being replied to
```
<!-- AC-ID: REQ-SB-82-US-06-AC-05 -->

### Scenario 6: A Compass call failure degrades to the existing deterministic routing rather than breaking the chat

```gherkin
Given a substantive question would normally be routed by the LLM-based
    moderator (Scenario 2)
When the Compass client call fails (e.g. network error, timeout, or a
    non-success response)
Then the moderator falls back to the existing deterministic
    keyword-overlap routing to decide who answers
  And the user is never shown a broken chat and is never given a silently
    fabricated routing decision
```
<!-- AC-ID: REQ-SB-82-US-06-AC-06 -->

### Scenario 7: A short-reply shortcut with no prior answering agent in the thread falls through to normal routing

```gherkin
Given a Cockpit's Chat has Experts brought in but no Expert has yet
    answered any question in this thread
When the user sends a short, low-signal acknowledgment message
Then the message is routed normally (the LLM-based moderator, or its
    deterministic degrade path) instead of the short-reply shortcut, since
    there is no "last-answering agent" yet to route to
```
<!-- AC-ID: REQ-SB-82-US-06-AC-07 -->

### Scenario 8: Replying to a message that can no longer be resolved does not break the chat

```gherkin
Given the user's client holds a reference to an earlier message to reply to
    (in either the Cockpit or the single-agent Chat panel)
When that reference can no longer be resolved against the current thread
    (e.g. stale client state after a reload) and the user sends anyway
Then the message still sends and is routed/answered normally
  And the unresolved reply-to reference is never shown as a broken or blank
    quoted reply, and never crashes the chat
```
<!-- AC-ID: REQ-SB-82-US-06-AC-08 -->

<!-- All 8 scenarios locked by the decomposer, 2026-08-31 (`/plan-tasks` step
2). Tightened only for precision (Scenario 1's "that same Expert" widened to
"that same agent" since ADR-012 sets last_answering_agent_id/name for ANY
dispatched reply -- Expert, Research Agent, or Customer-Section fallback
alike, not Experts only; Scenario 8's "in either the Cockpit or the
single-agent Chat panel" made explicit since the story's own Constraints
already state this applies to both surfaces). No AC is left non-locked --
every scenario describes an externally observable outcome the coder can
verify without needing the exact detection rule/Compass contract/UI
treatment, all still deliberately left open per the story's own Notes. -->

## Decomposer-authored scope-internal judgement calls

- **Short-reply detection rule (pre-authorized for this pass, per Notes item
  (2)):** a message qualifies for the shortcut when, after trimming
  whitespace, it does NOT end in `?` (a trailing question mark is always
  treated as substantive) AND EITHER (a) its lowercased,
  trailing-punctuation-stripped form exactly matches a small fixed
  acknowledgment vocabulary (`yes/y/yep/yeah/ya/no/nope/nah/ok/okay/k/kk/
  sure/fine/alright/go ahead/go on/please do/do it/sounds good/got it/
  noted/understood/thanks/thank you/thx/ty/will do/on it/ack/roger/cool/
  great/perfect`), OR (b) its stripped length is <= 3 characters (catches a
  novel ultra-short ack like "np" without the question-mark exclusion
  letting a genuinely short real question like "Why?"/"Cost?" slip through
  the vocabulary gap). Combines BOTH the length-threshold and
  fixed-vocabulary options the story's own Constraints left open, per this
  run's own explicit authorization to decide rather than re-escalate.
  Implemented in `chat_turn.py` (`REQ-SB-82-US-06-T04`).

## Affected Screens

- `src/frontend/src/features/cockpit/Cockpit.tsx` — the REAL, current
  screen (see `REQ-SB-82-US-01`'s own Context for why the stale
  `html-prototype/meeting-cockpit.html`/`inbox-cockpit.html` are not the
  design authority here). Needs a new, user-facing "reply to this message"
  affordance in the composer — today's `sendMessage(subjectKind, stem,
  text)` takes plain text only (confirmed, `cockpitApiClient.ts`). The
  existing auto-threaded "↳ replying to: …" READ-side rendering (`chat-
  message-reply-to`, already shipped per `REQ-SB-82-US-04`'s real build) is
  reused unchanged for rendering a user-chosen reply-to too — only the
  missing WRITE-side "pick a message to reply to" affordance is new. **No
  `html-prototype/` screen shows this pattern anywhere — `net-new-
  design-needed`** for the affordance itself (not for the message
  rendering, which already exists).
- `src/frontend/src/features/chat/AgentChatPanel.tsx` — needs an
  entirely new reply-to affordance, starting from zero: no message-id or
  persistence concept exists here today at all (confirmed — see Context).
  **`net-new-design-needed`,** same reasoning as above, plus a materially
  larger technical gap than Cockpit's own (nothing here persists today).

## Dependencies

- **Blocked by:** `REQ-SB-82-US-01` (Persisted Cockpit Chat, **Done**) —
  this story adds a new field to the same `chat_store.py`/`ADR-007`
  schema that story built.
- **A real, disclosed, non-standard relationship to `REQ-SB-82-US-04`**
  (see Context/`ESC-059`): this story extends the SAME already-shipped
  `chat_turn.py`/`moderator.py` functions that story's own file still
  describes as unbuilt (`status: Draft`, `gate: flagged`). Not marked a
  conventional "blocked by" edge, since the code this story builds on is
  confirmed live and working today — flagged instead so the human
  reconciles `REQ-SB-82-US-04`'s own status alongside this story's own
  flag, before `/plan-tasks` commits to a task breakdown that assumes one
  state or the other.
- **Related to, not blocking:** `REQ-SB-83` (Customer Experts) —
  `moderator.match_customer_fallback_agent` already composes against it;
  unaffected by this story's own changes.
- **External:** real Compass `gpt-oss-120b` credentials
  (`COMPASS_BASE_URL`/`COMPASS_API_KEY`/`COMPASS_MODEL`) — currently blank
  placeholders in `.env.example`. Until real values are provisioned, every
  message exercises the degrade path (Scenario 6) rather than the LLM-based
  happy path (Scenario 2); `/plan-tasks` should confirm real credentials
  exist (or can be obtained) before tasks assume the happy path is
  end-to-end testable.

## Constraints

- The short-reply shortcut fires only for genuinely low-signal messages —
  never for a substantive question that merely happens to be short (exact
  detection rule left to `/plan-tasks`, see Notes).
- The LLM-based moderator runs on every message not caught by the
  short-reply shortcut — the operator's explicit "always on" choice, never
  gated to ambiguous-only cases.
- A Compass client failure always degrades to the existing deterministic
  `route_question`, never a broken chat and never a silently fabricated
  routing decision (Scenario 6) — matches this project's standing honesty
  posture and the same error-handling shape `chat_turn.py::_reply_via_agent`
  already uses for a Hermes-side failure.
- Reply-to-message in the Cockpit is always a strong hint into the
  moderator's reasoning, never a hard override — the moderator retains
  final say (Scenario 5).
- Reply-to-message in the single-agent Chat panel never changes who
  answers — only one agent exists there (Scenario 4).
- Never fabricate a routing decision, a reply, or a resolved reply-to
  reference that doesn't genuinely exist (Scenario 8).
- The exact short-reply detection rule, the exact Compass request/response
  contract, and the exact reply-to-message visual treatment in both
  surfaces are all left open — not decided here (see Context/Notes).

## Implementation Tasks

<!-- Decomposer's own table, /plan-tasks step 2, 2026-08-31 -- supersedes the
analyst-authored sketch above. Re-scoped against ADR-011/ADR-012's real
decisions and split finer than the original 7-task sketch (short-reply
shortcut and LLM-primary routing separated; API-layer reply_to_message_id
passthrough separated from the chat_turn.py orchestration change) to keep
each task to one working session, per the story's own oversized-decomposition
flag (Notes item 5). -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-82-US-06-T01 | backend | `chat_store.py`: additive `last_answering_agent_id`/`last_answering_agent_name` per-subject field + setter | `app/business/cockpit/chat_store.py` | `REQ-SB-82-US-06-T01-chat-store-last-answering-agent.md` |
| REQ-SB-82-US-06-T02 | backend | `app/data_access/compass_client.py` — new raw-HTTP Compass `gpt-oss-120b` client (ADR-011) | `app/data_access/compass_client.py` (new) | `REQ-SB-82-US-06-T02-compass-client.md` |
| REQ-SB-82-US-06-T03 | backend | `moderator.py`: new LLM-based routing function composing `compass_client` (ADR-012 point 2) | `app/business/cockpit/moderator.py` | `REQ-SB-82-US-06-T03-moderator-llm-routing.md` |
| REQ-SB-82-US-06-T04 | backend | `chat_turn.py`: short-reply shortcut (pre-routing check) + persist `last_answering_agent` on every dispatched reply | `app/business/cockpit/chat_turn.py` | `REQ-SB-82-US-06-T04-short-reply-shortcut.md` |
| REQ-SB-82-US-06-T05 | backend | `chat_turn.py`: wire LLM moderator as PRIMARY routing with `route_question` demoted to the degrade path; resolve an optional `reply_to_message_id` hint into the moderator's prompt | `app/business/cockpit/chat_turn.py`, `app/business/cockpit/moderator.py` | `REQ-SB-82-US-06-T05-llm-primary-routing-and-reply-hint.md` |
| REQ-SB-82-US-06-T06 | backend | `cockpit_router.py`: accept optional `reply_to_message_id` on `POST .../message`, threaded to `chat_turn.send_user_message` | `app/api/cockpit_router.py` | `REQ-SB-82-US-06-T06-router-reply-to-message-id.md` |
| REQ-SB-82-US-06-T07 | frontend | Reply-to-message write-side UI + wiring in `Cockpit.tsx`/`cockpitApiClient.ts` (strong hint, not override; stale-reference-safe) | `src/frontend/src/features/cockpit/Cockpit.tsx`, `src/frontend/src/features/cockpit/cockpitApiClient.ts` | `REQ-SB-82-US-06-T07-cockpit-reply-to-message-ui.md` |
| REQ-SB-82-US-06-T08 | frontend | Reply-to-message UI + client-side context-anchoring in `AgentChatPanel.tsx` (no backend dependency) | `src/frontend/src/features/chat/AgentChatPanel.tsx` | `REQ-SB-82-US-06-T08-agent-chat-panel-reply-to.md` |

**Dependency graph:** `T01 -> T04 -> T05`; `T02 -> T03 -> T05`; `T05 -> T06 ->
T07`; `T08` has no dependencies (fully client-side, no backend coupling).
Acyclic.

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **`REQ-SB-82-US-04`'s own remaining, separately-flagged scope** —
  whatever genuinely remains open once its own status is reconciled against
  its real shipped code (see `ESC-059`); untouched by this story either
  way.
- **Reconciling `REQ-SB-82-US-04`'s own story file/status/`BACKLOG.md`
  row** — that is the human's own follow-up per `ESC-059`, not this
  story's own build work.
- **Any change to `REQ-SB-20`'s own Hub-routing mechanism or behavior** —
  a separate, agent-initiated mechanism; unaffected here, same as
  `REQ-SB-43-US-01`'s own precedent for the two mechanisms coexisting.
- **Provider CRUD API/UI** (`ProviderManager` already has `create`/
  `update`/`delete` with no router exposing them) — out of scope unless
  `/plan-tasks` finds it genuinely needed to configure the new Compass
  client; a static `.env`-sourced read (the settings already exist) is
  expected to be sufficient for a first pass.
- **Any general-purpose "reply to any message" convention beyond Cockpit
  and the single-agent Chat panel** — no other chat surface in this app is
  touched by this story.

## Notes

**Prototype parity:**

- `Cockpit.tsx`'s existing chat-thread/composer region — **Specced** for
  the shortcut/LLM-moderator's routing EFFECT (Scenarios 1-2, 5-7): no new
  visual region, the same message rendering, just a different routing
  decision behind it. The auto-threaded "↳ replying to: …" READ-side
  rendering is **Specced/reused**, not rebuilt. The composer's own
  "pick a message to reply to" WRITE-side affordance (Scenarios 3, 8) is
  **`net-new-design-needed`** — no `html-prototype/` screen shows this
  pattern anywhere.
- `AgentChatPanel.tsx` — the context-anchoring affordance (Scenario 4) is
  **`net-new-design-needed`** in full — no prototype coverage, and (per
  Context) no existing persistence/id concept to build the affordance on
  top of either.

**Why `gate: flagged`:**

1. No material assumption was made filling a genuine PRD gap in the
   Gherkin itself — every scenario asserts only the design already
   resolved with the operator in the plan doc, or an observable, honestly-
   left-open outcome (e.g. Scenario 8's "does not crash," not a specific
   resolution mechanism).
2. `REQ-SB-82` is not marked `<!-- Draft -->`/unfinalised in the PRD
   (confirmed by direct reading, `Documentation/PRD.md` line 4238
   onward).
3. **N/A here directly** (architect/ADR trigger) — but `/plan-tasks`
   should expect a real architectural decision for the new Compass client
   (first-ever direct-to-LLM client in this backend), including resolving
   the disclosed `ADR-022` ledger discrepancy above before deciding
   whether it extends an existing ADR or needs a fresh one.
4. **`ESCALATIONS.md` → `ESC-059` was written by this pass** — a real,
   disclosed finding that `REQ-SB-82-US-04`'s own story file is stale
   relative to its real, already-shipped, CHANGELOG-documented scope,
   found while grounding this story's own Dependencies.
5. Not judged oversized enough to force a split before `/plan-tasks`, but
   a real candidate the decomposer should weigh, matching
   `REQ-SB-82-US-04`'s own precedent: this story bundles a schema change, a
   short-reply shortcut, brand-new backend LLM-client infrastructure, a
   moderator rewrite with a degrade path, and reply-to-message UI in TWO
   materially different surfaces (one already has the storage substrate,
   one starts from zero). Kept as one story here because the pieces are
   tightly coupled (the reply-to-message hint only has value once the
   LLM-based moderator can actually reason over it) — flagged for the
   decomposer to consider a further task-level (or story-level) split.
6. N/A (coder trigger).
7. No contradictory PRD inputs — but a real, disclosed contradiction
   between the planning session's own investigation and the actual current
   code was found and corrected in Context (`chat_turn.py`'s own scope is
   substantially already shipped) — logged as `ESC-059`, not treated as a
   PRD-contradiction trigger since the PRD itself is not the source of the
   discrepancy.
8. **The controlling flags:** (a) the exact short-reply detection rule is
   left open (length threshold vs. fixed vocabulary vs. both); (b) the
   exact Compass `gpt-oss-120b` request/response contract needs confirming
   against the model's own real API, not assumed; (c) whether the new
   Compass client needs its own ADR or extends an existing one is
   genuinely unresolved, compounded by the disclosed `ADR-022` ledger gap;
   (d) the exact reply-to-message UI treatment in both surfaces is
   `net-new-design-needed`, with `AgentChatPanel.tsx` additionally lacking
   any persistence substrate to build on.

**What to do next:** `/plan-tasks` should (1) confirm real Compass
`gpt-oss-120b` credentials/API shape before committing to the LLM-moderator
design; (2) resolve the short-reply detection rule; (3) investigate the
disclosed `ADR-022` ledger discrepancy and decide the new Compass client's
ADR treatment; (4) run `/design` for the reply-to-message affordance in
both `Cockpit.tsx` and `AgentChatPanel.tsx` before cutting frontend tasks,
matching the established design-first-precursor discipline for genuinely
new UI patterns. Separately, the human resolving this story's own
`REVIEW-QUEUE.md` entry should reconcile `REQ-SB-82-US-04`'s own
`status`/`gate` against its real shipped scope (`ESC-059`).

gate: flagged 2026-08-31 — trigger-3 (Compass client is very plausibly
ADR-worthy, compounded by a disclosed `ADR-022` ledger discrepancy) plus
trigger-8 (short-reply rule, Compass contract, and reply-to-message UI
treatment all genuinely open) plus net-new-design-needed (reply-to-message
has no `html-prototype/` coverage in either surface) plus `ESC-059`
(`REQ-SB-82-US-04`'s own story file found stale relative to its real
shipped scope). A `REVIEW-QUEUE.md` entry has been added.

**Architect pass (2026-08-31) — `/plan-tasks` step 1:**

- **`ADR-022` investigated and resolved as orphaned, not extendable.**
  Confirmed by direct reading: no `ADR-022` exists anywhere in
  `Implementation/Architecture/ADR.md` (real highest entry was `ADR-010`
  before this pass); it belongs to the pre-2026-08-20 archived ADR
  sequence and governed `compass_client.py`/`anthropic_client.py`, both
  deleted 2026-08-27 in the "backend now fully agentic" purge
  (`MEMORY.md`). No worktree/branch holds a viable, current-architecture
  copy of either file. Every existing citation of `ADR-022`
  (`provider_manager.py`'s own comment, `REQ-SB-36-US-01-T01`/`T02`,
  `SPRINT-022-web-research-skill.md`) should be read as dead,
  pre-redesign history — not edited retroactively (specs/tasks are
  append-only), just superseded going forward by `ADR-011` below.
- **Two new ADRs appended** (trigger-3 fires, story stays `gate:
  flagged` — decomposer runs next regardless, per Pipeline.md):
  - **`ADR-011`** — the new Compass `gpt-oss-120b` HTTP client is a
    fresh, first-principles decision (NOT a restored `ADR-022`): lives
    in `app/data_access/compass_client.py` (raw I/O layer, sibling to
    `app/hermes/rest.py`'s own httpx precedent, deliberately NOT inside
    `app/hermes` itself — that package is Hermes-gateway-only by its own
    2026-08-27 hard rule), raises a dedicated error on any failure, and
    consumes `app.config.settings` directly rather than routing through
    `ProviderManager` (a CRUD/data Manager for the Provider entity, not
    a runtime call dispatcher).
  - **`ADR-012`** — Cockpit routing becomes LLM-primary
    (`moderator.py` gains a new function composing `compass_client`),
    with the existing deterministic `route_question` retained unmodified
    as the explicit degrade path (Scenario 6). The short-reply shortcut
    and the Cockpit reply-to-message hint are both additive fields on
    `ADR-007`'s existing `chat_store.py` per-subject schema
    (`last_answering_agent_id`/`last_answering_agent_name`, and an
    optional caller-supplied `reply_to_message_id` on the outgoing
    message) — no new store, no hard override. The single-agent Chat
    panel's reply-to mechanism is explicitly out of `ADR-012`'s scope:
    client-side context-anchoring only, no backend schema change, no
    LLM-moderator involvement (confirmed zero persistence concept exists
    there today).
- **Architecture scope: §Cockpit Persisted Chat (`ADR-007`), §Meeting
  Moderator Roster Recommendation (`ADR-009`), §Cockpit Live Routing &
  Reply-to-Message (`ADR-011`, `ADR-012`)** — `architecture.md`, updated
  2026-08-31. The decomposer/coder are bounded to these sections; the
  reply-to-message UI's own visual treatment is deliberately NOT
  architecturally specified here (net-new-design-needed, deferred to
  `/design`).
- **Not resolved by this pass** (left for `/plan-tasks`'s decomposer/the
  coder, per the story's own Constraints and this pass's own ADRs): the
  exact short-reply detection rule; the exact Compass request/response
  JSON contract (needs live verification once real credentials exist);
  the reply-to-message visual treatment in both surfaces.
- `REVIEW-QUEUE.md`'s existing `REQ-SB-82-US-06` entry updated with this
  pass's own resolution of its item (3) (the `ADR-022` question) — items
  (1), (2), (4) remain open for the decomposer/`/design`/the coder, as
  before.

**Decomposer pass (2026-08-31) — `/plan-tasks` step 2:**

- **All 8 scenarios locked** as `REQ-SB-82-US-06-AC-01` through `AC-08`
  (tightened only for precision, see the acceptance-criteria block above) —
  none marked `locked: false`; every locked AC describes an externally
  observable outcome the coder can verify today (via a real call plus
  engineered/monkeypatched Compass responses where the real credential
  isn't provisioned yet — trigger-6, "AC cannot be verified," does NOT
  fire for any of the 8).
- **Item (1), Compass credentials — handled, not re-escalated,** per this
  run's own explicit scoping: `T02`/`T03`/`T05`'s own `AC-02` verification
  step passes via a scoped, disclosed monkeypatch of `compass_client`
  (this project's own established pattern, `SPRINT-022`/`024`/`050`), with
  the real live happy-path against Compass's actual API explicitly
  disclosed in each task's own Tests block as blocked-pending-credentials
  — never silently skipped or claimed as a full pass. `AC-06`'s degrade
  path is fully, genuinely verifiable today (a real network/auth failure
  against blank credentials against `settings.compass_base_url=""` IS the
  real failure case ADR-011 itself names).
- **Item (2), the short-reply detection rule — decided, not re-escalated,**
  per this run's own explicit authorization: see "Decomposer-authored
  scope-internal judgement calls" above (question-mark exclusion + fixed
  vocabulary + a 3-character length floor, combining BOTH options the
  Constraints left open). Implemented in `T04`.
- **Item (4), the reply-to-message UI treatment — still genuinely
  net-new-design-needed, NOT unilaterally resolved by this pass** (this
  run's own launch instructions pre-cleared only items (1) and (2) for a
  decomposer judgement call, not this one). `T07`/`T08` lock only
  DOM-structural/behavioural ACs, per this project's own established
  "structural ACs for screens" convention (a locked AC may assert a
  reply-affordance element renders / a selected-message preview renders /
  a cancel control renders — never an exact visual/pixel/colour
  treatment). Each task's own Notes documents the specific, standard
  chat-reply interaction shape (a per-message "Reply" action; a quoted
  preview strip above the composer with a cancel control) as a decomposer-
  made, disclosed judgement call for the coder to build against, matching
  this project's own "log it as a scope-internal judgement call for human
  spot-check rather than blocking the build on a trivial, zero-ambiguity
  gap" pattern (`SPRINT-021`/`037`/`049`) — flagged for a non-blocking
  design spot-check against this shape once built, not a full `/design`
  prototype-sign-off gate before build (the pattern itself — a reply
  action plus a quoted composer preview — is standard across chat UIs and
  carries little real design risk relative to, say, a net-new dashboard
  layout).
- **`ESC-059`/`REQ-SB-82-US-04` reconciliation is ALREADY resolved**
  (confirmed by direct reading, `REQ-SB-82-US-04`'s own file:
  `status: Done`, `gate: clear`, dated 2026-08-31, with its own
  `## Reconciliation Note`) — the human already closed this loop before
  this decomposer pass ran; no action remains here.
- **Status → `Ready`** (all 3 decomposer status criteria met: every AC
  locked; every locked AC has ≥1 AC-tagged verification step across
  `T01`-`T08`; `depends_on` is acyclic — see the dependency-graph line
  under Implementation Tasks). **`gate` stays `flagged`**, per Pipeline.md's
  own explicit rule for this exact situation ("if the architect flagged
  the story this run for an ADR change, leave it gate: flagged — the human
  reviews the ADR and your tasks together") — the architect appended
  `ADR-011`/`ADR-012` this same run. `REVIEW-QUEUE.md`'s existing
  `REQ-SB-82-US-06` entry updated with this pass's own disposition (see
  above); no new `ESCALATIONS.md` entry needed (no backward step, no
  out-of-scope event this pass).

**Coder pass (2026-08-31) — `T07` (last remaining task) built and `Done`,
story → `Done`:** all 8 tasks (`T01`-`T08`) now `Done`; every locked AC
(`AC-01` through `AC-08`) independently verified live per each task's own
Implementation Log, with a real positive result for every one (no AC left
`Blocked`, no locked AC weakened/omitted). `T07` built the Cockpit
write-side reply-to-message UI (a per-message Reply affordance + a
composer preview strip with cancel, matching `T08`'s already-`Done`
convention) and verified `AC-03`/`AC-08` live against a real vault subject
(seeded and fully reverted afterward, byte-for-byte confirmed via `diff`
plus an independent live re-fetch). `gate` stays `flagged` — this coder
pass cannot clear the pending human `ADR-011`/`ADR-012` review (a human-
only step); see `REVIEW-QUEUE.md` for the closing disposition and the
now-actionable non-blocking design spot-check (both `T07`/`T08` UI shapes
are built). `SPRINT-078` closes alongside this story (see its own drafted
Retrospective).
