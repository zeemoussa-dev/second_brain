---
id: REQ-SB-82-US-01
title: Persisted Cockpit Chat — real roster + message-history storage that survives reload and navigation
requirement_ids: [REQ-SB-82]
requirement_section: "REQ-SB-82: Cockpit Mechanics — Prep, Research, and Moderation"
phase: P2
status: Done
gate: clear
gate_reason: "trigger-3 (ADR-007 created) — architect pass, 2026-08-25. Persist-vs-send split itself remains resolved per the operator's 2026-08-25 note below; the flag is solely for the new ADR-007 (Cockpit roster/message persistence mechanism), which needs a human look per the pipeline's own ADR-creation rule."
sprint: "SPRINT-076"
created: 2026-08-25
updated: 2026-08-25
---

# REQ-SB-82-US-01 — Persisted Cockpit Chat — real roster + message-history storage that survives reload and navigation

## Story

**As a** Second Brain user working in a Meeting or Inbox Cockpit
**I want** the Chat tab's brought-in Expert roster and message history to be
saved for real, not just held in the browser tab's own local state
**So that** navigating away and back, or reloading the page, never loses
track of who I'd brought in or what had already been discussed — the chat
becomes the actual record of that meeting/email, not something that resets
the moment I look away

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-82: Cockpit Mechanics — Prep,
  Research, and Moderation*, "Persisted chat" bullet — "Chat's current
  roster/message state is real component state with no backend (2026-08-25
  UI pass, disclosed at the time) — resets on reload. This requirement
  makes it real: survives navigating away and back, survives a reload, is
  the actual record of what was discussed and decided in that meeting."
  REQ-SB-82's own umbrella Acceptance text: "Not yet specced — genuinely
  substantial (new async job infrastructure, a persisted-chat data model,
  cross-agent orchestration) and deliberately routed through the full
  `/spec → /plan-tasks → /plan-sprints → /implement-sprint` pipeline...
  Depends on REQ-SB-43/44 (done), REQ-SB-83 (Customer Experts, for the
  Moderator's own customer-match track)." REQ-SB-83's own customer-match
  track is not this story's concern — see `REQ-SB-82-US-03`.
- **REQ-SB-82 is genuinely large — split at the story level, per this
  project's own "one requirement may split into multiple stories" rule and
  the task's own explicit authorization to do so.** Five real, separable
  mechanisms are named in the PRD text: this story (persisted storage), a
  Research Agent (`REQ-SB-82-US-02`), the Meeting Moderator's own roster
  pre-assembly (`REQ-SB-82-US-03`) and live per-question routing/async
  research fallback (`REQ-SB-82-US-04`), and the Meeting Preparation Agent
  (`REQ-SB-82-US-05`). This story is the FOUNDATIONAL one — it builds the
  durable storage substrate `US-03`/`US-04` both need somewhere to write a
  pre-assembled roster and a routed reply into. See each sibling story's
  own `Dependencies` section for the explicit edges.
- **Confirmed by direct reading of the real, current code — not assumed:**
  - `src/frontend/src/features/cockpit/Cockpit.tsx`'s Chat tab today: a
    `broughtInIds: Set<string>` held in local component `useState`, with
    its own comment explaining exactly why — *"Local-only roster state --
    there's no bring-in/remove endpoint yet (Chat itself isn't wired up),
    so this doesn't persist across a reload."* `bringIn`/`remove` mutate
    only this local state. The message composer (`<input>`/`<button
    type="submit">`) is rendered `disabled`, with placeholder text "Chat
    isn't wired up yet…".
  - `src/frontend/src/features/cockpit/cockpitApiClient.ts`'s
    `CockpitThread` type is ALREADY shaped for a real, persisted,
    per-Expert-attributed message log: `{ messages:
    { speaker: 'user' | 'agent'; agent_id: string | null; agent_name:
    string | null; text: string }[]; brought_in_agent_ids: string[] }` —
    the data CONTRACT this story needs already exists; only the real
    backend behind it does not.
  - `src/backend/app/api/cockpit_router.py`'s `GET
    /cockpit/{subject_kind}/{subject_note_stem}` currently returns
    `"thread": {"messages": [], "brought_in_agent_ids": []}` as an
    **honest, hardcoded empty stub** — its own module docstring states
    this explicitly: *"overview/thread come back as honest empty stubs
    (never fabricated) until the Research Expert and Chat mechanism are
    designed (separate, later discussion)."* That later discussion is this
    requirement.
  - `src/frontend/src/features/cockpit/Cockpit.tsx`'s per-Expert
    attribution UI is ALREADY BUILT and does not need re-inventing: `
    {message.speaker === 'agent' && <span className="chat-message-author">
    {message.agent_name}</span>}` renders above every agent bubble,
    reusing the shared `ChatMessageText` component every other real chat
    surface in this app already uses (`MEMORY.md`, 2026-08-24 entry). Once
    this story returns real, attributed messages, this rendering already
    works — no new frontend attribution component is needed.
- **The prior real backend for this exact surface is confirmed stale, not
  quietly reusable.** `MEMORY.md`'s own 2026-08-25 entry: *"`business/
  cockpit/{threads,research,person_note_proposals,attachments}.py` are
  stale — do not import them without first rewiring against the
  Hermes-based chat/agent model... almost certainly still assume the fully-
  retired Second-Brain-native agent/chat model (`agent_registry.py`,
  emptied 2026-08-22) rather than the `HermesChatSession`-based rebuild."*
  `REQ-SB-43-US-01`'s own already-`Done` build (its `ADR-036`,
  `.second-brain/cockpit_threads.json`, `business/cockpit/threads.py`
  composing `run_agent_conversation` once per brought-in Expert) is the
  SAME mechanism this note calls stale — `run_agent_conversation` itself
  no longer exists in this codebase (the whole LangGraph-native
  orchestration layer it belonged to was archived in the Hermes pivot,
  `main.py`'s own comment: *"old Second-Brain-native Agent orchestration
  layer"*). **This story cannot resurrect `ADR-036`'s design — it needs a
  genuinely new persistence mechanism designed against real Hermes agents
  (each reached via `HermesChatSession`/the WS protocol, `MEMORY.md`
  2026-08-23), which is real, new architectural surface for `/plan-tasks`,
  not decided here.**
- **The current, real Cockpit.tsx layout (2026-08-25 UI makeover) has NO
  approved `html-prototype/` coverage — the existing prototype screens are
  superseded, not current.** `html-prototype/meeting-cockpit.html`/
  `inbox-cockpit.html` show a 3-COLUMN simultaneous grid (available
  Agents+research left, unified chat middle, info+chips right) — the REAL,
  shipped code (`CHANGELOG.md`'s own "Meeting/Inbox Cockpit UI makeover"
  entry) replaced this with a secondary-nav tab layout (Overview/Chat/
  People/Documents/Articles) plus a right rail that swaps between subject-
  info and an Experts-only roster depending on the active tab — a
  materially different shape, built directly in code from the operator's
  live whiteboarding, not through a fresh `/design` pass. This story
  builds ON the REAL current layout (not the stale prototype) — see
  `## Notes`' Prototype parity subsection.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then
edge cases and error states. Do NOT add AC-IDs — the decomposer assigns them
at /plan-tasks. These scenarios describe only the externally observable
persistence behaviour; they deliberately do not assert how a message comes
to exist in the thread (sending/routing is REQ-SB-82-US-04's concern) or the
exact storage mechanism (left to /plan-tasks, see Context). -->

### Scenario 1: Bringing an Expert into a meeting's or email's Chat persists across a reload

```gherkin
Given the user is in a Meeting or Inbox Cockpit's Chat tab
When the user brings an Expert into the chat
  And the page is then reloaded
Then that Expert still appears in the "in this chat" roster after the
    reload — not reset back to empty
```
<!-- AC-ID: REQ-SB-82-US-01-AC-01 -->

### Scenario 2: Removing a brought-in Expert persists across a reload

```gherkin
Given an Expert has been brought into a Cockpit's Chat and the page has
    since been reloaded (Scenario 1)
When the user removes that Expert from the chat
  And the page is reloaded again
Then that Expert no longer appears in the "in this chat" roster after the
    reload
```
<!-- AC-ID: REQ-SB-82-US-01-AC-02 -->

### Scenario 3: The chat's message history persists across a reload

```gherkin
Given a meeting's or email's Chat thread already contains one or more
    messages (from the user or from an Expert, however they came to exist)
When the page is reloaded
Then the same messages, in the same order, with the same speaker/Expert
    attribution, are shown again — none are lost or altered
```
<!-- AC-ID: REQ-SB-82-US-01-AC-03 -->

### Scenario 4: Roster and message history persist when navigating away and back, not only on a hard reload

```gherkin
Given a Cockpit's Chat has a brought-in roster and/or message history
When the user navigates to a different page in the app and then back to
    this same Cockpit
Then the roster and message history are exactly as they were before
    navigating away — identical to the reload case in Scenarios 1-3
```
<!-- AC-ID: REQ-SB-82-US-01-AC-04 -->

### Scenario 5: Persisted chat is scoped to one meeting/email, never shared across subjects

```gherkin
Given the user has brought in Experts and/or exchanged messages in more
    than one different meeting's or email's own Cockpit
When the user opens one specific meeting's or email's Cockpit
Then only that one meeting's/email's own roster and message history are
    shown — another subject's roster/messages are never shown here
```
<!-- AC-ID: REQ-SB-82-US-01-AC-05 -->

### Scenario 6: A meeting/email with no prior chat activity opens with an honestly empty roster and history

```gherkin
Given a meeting or email has never had anyone brought into its Chat or any
    message exchanged
When the user opens its Cockpit's Chat tab
Then the roster is empty and the message history is empty — the same
    honest empty state already shown today, not an error
```
<!-- AC-ID: REQ-SB-82-US-01-AC-06 -->

### Scenario 7: A persisted message retains which Expert produced it, or that it was the user's own

```gherkin
Given the persisted message history contains messages from more than one
    speaker (the user, and one or more different Experts)
When the user views the Chat tab after a reload or navigation
Then each message is still shown attributed to whoever/whichever Expert
    actually produced it, distinguishable from every other speaker in the
    same thread — attribution is not lost by being persisted and re-read
```
<!-- AC-ID: REQ-SB-82-US-01-AC-07 -->

## Affected Screens

- `src/frontend/src/features/cockpit/Cockpit.tsx` (the REAL current
  screen — see Context; `html-prototype/meeting-cockpit.html`/
  `inbox-cockpit.html` are superseded, not the design authority here) —
  the Chat tab's roster (`broughtInIds`) moves from local-only `useState`
  to state loaded from and written back to a real backend; no new visual
  region — the existing "In this chat"/"Bring in another Expert" grouping
  and the existing `chat-message`/`chat-message-author` rendering are
  reused unchanged, now fed real, persisted data instead of an always-empty
  stub.

## Dependencies

- **Blocked by:** `REQ-SB-43-US-01`/`REQ-SB-44-US-01` (Meeting/Inbox
  Cockpit, both **Done**) — this story extends the Chat tab those stories
  shipped; both satisfied.
- **Feeds into (not blocked by):** `REQ-SB-82-US-03` (Moderator roster
  pre-assembly) and `REQ-SB-82-US-04` (Moderator live routing/async
  research) — both need a real place to write a pre-assembled roster and
  a routed/threaded reply; this story is the substrate they build on. See
  those stories' own `Dependencies` for the explicit `depends_on` edge
  back onto this one.
- **External:** none new.

## Constraints

- Persisted roster/message state is always scoped per `(subject_kind,
  subject_note_stem)` pair — never shared or merged across different
  meetings/emails (Scenario 5).
- Never fabricate a message or roster entry that wasn't actually produced
  by the user or a real Expert action.
- This story does NOT resurrect `business/cockpit/threads.py`/`ADR-036`'s
  design as-is — that mechanism composed `run_agent_conversation`, which
  no longer exists post-Hermes-pivot (see Context). The real persistence
  mechanism is a genuinely new `/plan-tasks` decision.
- The exact storage mechanism (a JSON sibling file mirroring the old
  `.second-brain/cockpit_threads.json` convention, or something else) is
  left open, not decided here.
- Per-Expert attribution must survive being persisted and re-read
  (Scenario 7) — the existing `agent_id`/`agent_name` fields already on
  `CockpitThread.messages` (see Context) are the contract to preserve, not
  redesign.

## Implementation Tasks

<!-- Decomposer's own table (/plan-tasks step 2, 2026-08-25) -- supersedes
the analyst-authored starting point above. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-82-US-01-T01 | backend | `chat_store.py` + `vault_writer.py` sibling load/save — real, per-subject-keyed persistence for roster + messages (`ADR-007`) | `app/business/cockpit/chat_store.py` (new), `app/data_access/vault_writer.py` | `Implementation/Tasks/REQ-SB-82-US-01-T01-cockpit-chat-store.md` |
| REQ-SB-82-US-01-T02 | backend | `cockpit_router.py` — `GET` returns real persisted `thread`; new `POST .../roster` / `DELETE .../roster/{agent_id}` | `app/api/cockpit_router.py` | `Implementation/Tasks/REQ-SB-82-US-01-T02-cockpit-roster-endpoints.md` |
| REQ-SB-82-US-01-T03 | frontend | `Cockpit.tsx`/`cockpitApiClient.ts` — roster reads/writes go through the real backend, not local `useState` | `src/frontend/src/features/cockpit/` | `Implementation/Tasks/REQ-SB-82-US-01-T03-cockpit-chat-frontend.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, manual-mode verification per this project's current test-tooling status
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Enabling the Chat composer to actually send a message and receive a
  real reply.** This story builds the durable STORAGE substrate only — a
  roster and message log that survives reload/navigation. Whether/how a
  sent message reaches a real Expert and gets a real reply is
  `REQ-SB-82-US-04`'s concern (targeted routing) — deliberately not
  bundled here, since building a real send path ahead of the Moderator's
  own targeted-routing behavior risks either a broadcast-to-everyone
  implementation that directly contradicts this requirement's own
  Moderator mandate, or rework once routing lands. This is a scoping
  judgment call, not a PRD-dictated boundary — flagged (see `## Notes`).
- **Threaded (parent/child) message rendering** — this story persists a
  flat, ordered message log, matching today's existing flat
  `chat-thread` rendering. Threaded async-research replies are
  `REQ-SB-82-US-04`'s own new UI concept, not built here.
- **Any change to which Experts appear in the "available"/left-side
  roster list** (`type === 'expert'`, non-background) — unchanged; this
  story only makes bring-in/remove and the message log durable.
- **A "Recommended" roster grouping** — that's `REQ-SB-82-US-03`'s own
  concern; this story's roster storage is generic (any Expert can be
  brought in or removed) and doesn't itself distinguish "recommended"
  from "manually brought in."

## Notes

**Prototype parity (Cockpit.tsx's real, current layout vs.
`html-prototype/meeting-cockpit.html`/`inbox-cockpit.html`):**

- The stale prototype's 3-column simultaneous layout — **Superseded, not
  covered.** The real, shipped Cockpit.tsx (2026-08-25 UI makeover) uses a
  materially different secondary-nav-plus-right-rail layout that never
  went through a fresh `/design` pass (built directly from live
  whiteboarding, per `CHANGELOG.md`). This story does not change the
  layout itself, so it inherits this pre-existing gap rather than causing
  it — recorded honestly, not silently ignored.
- The Chat tab's roster grouping ("In this chat"/"Bring in another
  Expert") and message/attribution rendering — **Specced** (Scenarios
  1-7) against the REAL current markup, which already exists and needs no
  new visual region for this story — only its data source changes from
  local state to a real backend.

**Why `gate: flagged`:**

1. One disclosed scoping judgment call, not a guess filling a genuine
   PRD gap: composer-enablement (real send/receive) is deliberately
   deferred to `REQ-SB-82-US-04`, reasoned above (Non-Goals) — a
   defensible reading, not the only one, so flagged per trigger 8 rather
   than silently assumed.
2. `REQ-SB-82` is not marked `<!-- Draft -->`/unfinalised in the PRD.
3. N/A here (architect/ADR trigger) — but `/plan-tasks` should expect a
   real, new architectural decision for the persistence mechanism, since
   the only prior real implementation of this exact surface (`ADR-036`)
   is confirmed stale and cannot be reused as-is (see Context).
4. No `ESCALATIONS.md` entry was written by this pass.
5. Not oversized — deliberately split out of REQ-SB-82's larger scope as
   the one foundational, independently-valuable persistence layer (making
   today's already-real bring-in/remove UI durable has standalone value
   even before any routing intelligence exists).
6. N/A (coder trigger).
7. No contradictory PRD inputs found.
8. **The controlling flag:** trigger 8, the persist-vs-send scope
   boundary named in point 1 above — a real, disclosed judgment call
   among more than one defensible reading, not resolved by the PRD's own
   text either way.

**Resolved 2026-08-25 (operator):** persist-vs-send split confirmed as the
right shape — this story builds durable storage only; `REQ-SB-82-US-04`
builds the real send/routing path on top of it. `/plan-tasks` proceeds to
design the concrete Hermes-agent-backed persistence/attribution mechanism
(no `run_agent_conversation` equivalent exists post-pivot, see Context) —
that is ordinary `/plan-tasks` design work now, not a parked decision.

**Architect pass, 2026-08-25 (`/plan-tasks` step 1):** designed the
concrete persistence mechanism — `ADR-007` (new). One new JSON store,
`.second-brain/cockpit_chat.json`, keyed per `(subject_kind,
subject_note_stem)`, backed by a new `app/business/cockpit/chat_store.py`
module (never reimports the stale `business/cockpit/threads.py`). See
`Implementation/Architecture/architecture.md` §Cockpit Persisted Chat.

**Architecture scope:** §Cockpit Persisted Chat (`Implementation/
Architecture/architecture.md`), `ADR-007`.

gate: flagged 2026-08-25 — trigger-3 (`ADR-007` created). REVIEW-QUEUE.md
entry added; `/plan-tasks` step 2 (decomposer) still proceeds per the
pipeline's own "ADR flags, doesn't halt" rule.

**Decomposer pass, 2026-08-25 (`/plan-tasks` step 2):** all 7 scenarios
tightened and locked as `AC-01`..`AC-07`; every locked AC has at least one
AC-tagged manual verification step across `T01`-`T03` (layered
function-call → real-HTTP → real-browser, per this project's own
established precedent). `depends_on` is acyclic (`T01 -> T02 -> T03`,
linear). Status advanced `Draft -> Ready`; `gate` stays `flagged` per the
decomposer's own rule (the architect's `ADR-007` flag is not cleared by
this pass — the human still reviews `ADR-007` and these tasks together).
No new MUST-FLAG trigger fired during decomposition itself; the existing
trigger-3 flag is carried forward unchanged.

**Operator authorization, 2026-08-25:** "Start Coding" — reviewed the ADR against my own earlier resolution notes (matches exactly), authorized to proceed. gate: clear.

**Product-owner pass, 2026-08-25 (`/plan-sprints`):** grouped into
`SPRINT-076` alongside `REQ-SB-82-US-02` (the two independent foundations
`US-03`/`US-05` both depend on) — see `SPRINT-076`'s own Grouping
Rationale for the full split-vs-combine reasoning against `Learnings.md`'s
sizing calibration. `depends_on` (`T01 -> T02 -> T03`) fully honoured
inside the sprint. gate: clear 2026-08-25 — no MUST-FLAG trigger fired at
this stage.

**Coder pass, 2026-08-25 (`REQ-SB-82-US-01-T01`):** `T01` built and
verified `Done` — real `chat_store.py` + `vault_writer.py` sibling
load/save, `.second-brain/cockpit_chat.json`. `AC-01`/`AC-02`/`AC-05`/
`AC-06` verified live (see the task's own `## Implementation Log`).
`AC-03`/`AC-04`/`AC-07` remain unverified — they need a real message log,
which only exists once `T02` (router)/`T03` (frontend) land. Story status
moved `Ready -> In Progress`; stays `In Progress` until `T02`/`T03` also
close every remaining locked AC.

**Coder pass, 2026-08-25 (`REQ-SB-82-US-01-T02`):** `T02` built and
verified `Done` — `cockpit_router.py`'s `GET` now returns the real
persisted thread (stub removed); new `POST .../roster`/`DELETE
.../roster/{agent_id}` endpoints wired directly onto `T01`'s `chat_store`,
zero parallel persistence logic. `AC-01`/`AC-02`/`AC-03`/`AC-06`/`AC-07`
verified live over the real HTTP layer against the real running backend
and real vault (see the task's own `## Implementation Log`) —
`AC-03`/`AC-07` specifically now confirmed with a real message log for
the first time (seeded directly via `chat_store`, no send endpoint exists
yet). `AC-04` (navigate-away-and-back persistence) and `AC-05`
(no-cross-subject-leakage from the FRONTEND's perspective — `T01` already
confirmed it at the storage layer) remain unverified from this story's
still-`In Progress` perspective — both need `T03`'s real frontend wiring.
Story stays `In Progress`; `T03` (frontend) is the only remaining task —
this task alone does not close the story.

**Coder pass, 2026-08-25 (`REQ-SB-82-US-01-T03`):** `T03` built and
verified `Done` — `Cockpit.tsx`'s `broughtInIds` local `useState` removed
entirely; the roster is now derived every render from the real fetched
`data.thread.brought_in_agent_ids`, and `bringIn`/`remove` call the new
`cockpitApiClient.ts` functions (`bringInAgent`/`removeAgent`) against
`T02`'s real endpoints. `AC-01`/`AC-02`/`AC-04` verified live end-to-end
against the real running frontend (headless-browser CDP session), real
running backend, and a real vault meeting note: brought an Expert in,
hard-reloaded, confirmed it survived (`AC-01`); removed it, hard-reloaded
again, confirmed it was gone (`AC-02`); brought it in again, used real
in-app SPA navigation away and back (not a hard reload), confirmed the
roster was unchanged (`AC-04`) — screenshots captured as evidence, all
scratch roster entries cleaned up afterward via real `DELETE` calls
against the real vault's persisted store. `AC-03`/`AC-06`/`AC-07`
(already verified by `T01`/`T02` at the storage/HTTP layers) needed no
new frontend-specific verification since the rendering path
(`chat-message-author`/`ChatMessageText`) reused unchanged. `AC-05`
(no cross-subject leakage) was already confirmed at the storage layer by
`T01`; this task's per-subject `fetchCockpit(subjectKind,
subjectNoteStem)` call structurally cannot leak across subjects (a fresh
fetch keyed by the URL's own subject on every mount). **All 7 locked ACs
across the whole story are now verified.** Composer stayed disabled
throughout, per Constraints/Non-Goals. Story status advanced `In Progress
-> Done` — all 3 tasks (`T01`/`T02`/`T03`) `Done`, every locked AC
verified. `BACKLOG.md`'s `REQ-SB-82` row updated accordingly.
