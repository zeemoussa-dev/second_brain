---
id: BUGFIX-04-US-01
title: Cockpit chat correctly addresses agents, sends on Enter, updates live, and renders rich text (BUG-022/023/024/025 fix)
requirement_ids: [BUG-022, BUG-023, BUG-024, BUG-025]
requirement_section: "BUGS.md → BUG-022, BUG-023, BUG-024, BUG-025"
status: Done
gate: clear
gate_reason: "Resolved directly, 2026-08-19, operator in full autopilot for the remainder of the session: ADR-050 does not introduce any NEW decision beyond what was already resolved directly moments earlier in this same story's own prior gate_reason (react-markdown, common markdown subset, both-user-and-agent scope) — the architect pass simply formalized that exact resolution into a real ADR (wiring shape, default-safe sanitization posture via react-markdown's own no-raw-HTML default, one shared ChatMessageText.tsx component) plus 3 other scenarios that compose already-Accepted mechanisms with no new ADR needed. No genuinely new design fork was introduced by this architect pass to review. Flag cleared on the same basis ADR-047/048/049 were; eligible for /plan-tasks. Prior flagged history (trigger-3, ADR-050 created) preserved in git history of this file. --- PRECEDING architect gate_reason, preserved verbatim, not retracted: trigger-3 (ADR-050 created) — architect pass, 2026-08-19: BUGFIX-04-US-01's own prior gate_reason (preserved verbatim below) already resolved Scenario 4's three open design questions directly (markdown subset, library=react-markdown, both-user-and-agent scope); this architect pass turned that resolution into a real architectural decision (ADR-050: react-markdown wiring, sanitization posture, shared ChatMessageText.tsx component) and therefore must flag per the ADR-creation trigger regardless of how settled the underlying choice already was — the decomposer still runs (this does not halt the stage) so a human reviews ADR-050 and the resulting tasks together in one pass, per Pipeline.md's own 'forward is autonomous by exception' contract for trigger 3. Scenarios 1-3 (BUG-022/023/024) fired no new trigger — each composes an already-Accepted mechanism (ADR-036, REQ-SB-49-US-01's mention resolution) with no new ADR; see architecture.md's new 'Cockpit Chat — Addressed-Reply Dispatch, Send-on-Enter, and Pending-State Live Update' section. --- PRIOR gate_reason (analyst resolution, preserved, not retracted): Resolved directly, 2026-08-19, operator in full autopilot ('you are in Auto Pilot') for the remainder of the session: the underlying finding stands (REQ-SB-32 was never actually spec'd/built, so Scenario 4 is net-new work, not a regression fix) but the open implementation questions it raised are ordinary, low-risk, easily-reversible frontend choices with no data-integrity or destructive-action stakes — squarely appropriate to resolve directly rather than block overnight. Resolved: (1) markdown subset = the common baseline a Compass-generated response would naturally produce — bold/italic, bulleted/numbered lists, links, inline/block code, headings; (2) library = react-markdown, the standard, well-established choice for this exact purpose in a React app, no exotic alternative needed; (3) user's own sent messages ALSO render as rich text, not just agent replies — grounded directly in the operator's own literal words reporting this bug, 'All Text Should be Rich Text in Chat,' which draws no agent/user distinction. Scenario 4's own Gherkin (already written, observable-behavior-only, no hardcoded library choice) needs no rewording under this resolution. ESC-053 stays Open in ESCALATIONS.md as the permanent record of the REQ-SB-32 discrepancy (append-only, not edited) — this gate_reason is the resolving note."
sprint: "SPRINT-064"
created: 2026-08-19
updated: 2026-08-19 (product-owner pass, /plan-sprints)
---

# BUGFIX-04-US-01 — Cockpit chat correctly addresses agents, sends on Enter, updates live, and renders rich text (BUG-022/023/024/025 fix)

## Story

**As a** Second Brain user working a Meeting Cockpit or Inbox Cockpit chat
(and, for rich text, the Agents Map's own embedded agent chat panel)
**I want** a message I address to one specific agent to be answered only by
that agent, Enter to send exactly like clicking Send, my sent message and
any replies to show up without a manual page refresh, and markdown-
formatted chat content to render as real formatted text
**So that** a multi-agent Cockpit conversation reads and behaves like a
real conversation, instead of every agent talking over each other, the
input silently ignoring standard chat conventions, the thread appearing
frozen after every send, and every reply showing raw `**`/`-` syntax

## Context

Triage batch: `BUG-022`, `BUG-023`, `BUG-024`, `BUG-025` — all logged
`2026-08-19`, all `Open` at triage time, all against Meeting Cockpit /
Inbox Cockpit (`REQ-SB-43-US-01`/`REQ-SB-44-US-01`, `SPRINT-040`/
`SPRINT-041`) and its `@mention` bring-in affordance
(`REQ-SB-49-US-02`, `SPRINT-046`). `BUG-025` additionally names the
Agents Map's own embedded agent chat panel (`REQ-SB-38`/`AgentDetailPanel.tsx`).

### BUG-022 — every agent responds, not just the addressed one (Logic, Major)
- **Screen/route:** Meeting Cockpit and Inbox Cockpit (both).
- **Repro (BUGS.md's own text):** open either Cockpit with more than one
  agent brought into the conversation; send a message intended for one
  specific agent; observe which agent(s) reply.
- **Expected:** only the addressed/relevant agent responds — the Cockpit
  should route the message to the correct single agent.
- **Actual:** every agent in the conversation responds, regardless of who
  the message was actually addressed to.
- **Code-confirmed root cause** (`src/backend/app/business/cockpit/
  threads.py::send_user_message`): the function appends the user's turn,
  then loops `for agent_id in thread["brought_in_agent_ids"]:`
  **unconditionally**, calling `run_agent_conversation` and appending a
  reply for EVERY currently brought-in agent on EVERY message — there is
  no per-message addressee resolution anywhere in this function. The
  frontend's own `@mention` machinery (`Cockpit.tsx`'s
  `resolveMentionedAgents`/`MENTION_TOKEN_RE`, built for
  `REQ-SB-49-US-02`) is used ONLY to auto `bringInAgent(...)` a
  newly-@-mentioned agent before sending — it has no effect on which of
  the agents ALREADY brought in actually respond to that one message.
  Once 2+ agents are in a thread, naming one by `@agent_id` still gets a
  reply from every one of them.

### BUG-023 — pressing Enter does nothing, must click Send (UI, Major)
- **Screen/route:** Meeting Cockpit and Inbox Cockpit (both).
- **Repro:** open either Cockpit's chat input, type a message, press Enter.
- **Expected:** Enter sends the message, matching standard chat-UI
  convention.
- **Actual:** Enter does nothing; the Send button must be clicked.
- **Code-confirmed root cause** (`src/frontend/src/features/cockpit/
  Cockpit.tsx`, the chat input row ~line 179-187): the input is a bare
  `<input type="text" ... value={messageInput} onChange={...} />` with
  **no `onKeyDown` handler and no surrounding `<form>`** — `handleSendMessage`
  is wired only to the Send `<button>`'s `onClick`. This is a real,
  working, in-codebase precedent to mirror: the Agents Map's own chat
  input (`AgentDetailPanel.tsx`) already wraps its input in
  `<form className="chat-input-row" onSubmit={handleSend}>`, which
  correctly fires on both Enter and Send-button click — Cockpit's input
  never adopted that pattern.

### BUG-024 — sent message/replies don't appear until manual refresh (UI, Major)
- **Screen/route:** Meeting Cockpit and Inbox Cockpit (both).
- **Repro:** send a message using the Send button (the working path,
  distinct from `BUG-023`); observe the chat UI without refreshing.
- **Expected:** the sent message appears immediately (optimistic update),
  and any agent reply streams/appears as it arrives, with no manual
  action required.
- **Actual:** nothing visibly changes after clicking Send — no
  confirmation the message was sent, no new messages shown — until the
  page is manually refreshed, at which point the sent message and any
  replies appear.
- **Code-confirmed root cause** (`Cockpit.tsx`'s `handleSendMessage` +
  `cockpit_router.py::send_message` + `threads.py::send_user_message`):
  there is **no polling, no SSE, no websocket anywhere in this codebase**
  (confirmed by direct search of `src/frontend/src` — zero
  `EventSource`/`setInterval`/subscribe-style calls in `Cockpit.tsx` or
  `cockpitApiClient.ts`). The only update mechanism is one explicit
  `reload()` chained after `sendCockpitMessage(...)` resolves. The
  backend's `/message` endpoint IS awaited synchronously end-to-end —
  `send_user_message` blocks on a real, sequential, per-brought-in-agent
  `run_agent_conversation` Provider call for EVERY agent in the loop
  (worsened directly by `BUG-022`: more unaddressed agents dispatched ⇒
  more sequential real model calls ⇒ longer total wait) — before it ever
  returns and the thread is persisted. Unlike the Agents Map's own chat
  (`AgentDetailPanel.tsx`, which sets a `sending` state, disables the
  input, and renders a typing-dot indicator for the exact same
  in-flight-request window), Cockpit's chat input has **no pending/loading
  state at all** — the Send button stays enabled, nothing indicates a
  request is in flight, for however long the full sequential-agent loop
  takes. A user has no feedback to distinguish "still working" from
  "nothing happened," reasonably concludes the app is stuck, and manually
  refreshes — which re-fetches via the mount-time `useEffect`'s own
  `reload()` and shows the (by then likely-arrived) data, indistinguishable
  from "requires a refresh" even though the original `reload()` call, given
  enough patience, would eventually have updated the same screen.

  **Is this the same root cause as BUG-022, or independent? (explicit
  investigation, since both bugs sit inside the same `send_user_message`
  call.)** Independent, code-confirmed: BUG-022 is a pure **server-side
  dispatch-selection** defect (`send_user_message`'s loop has no addressee
  filter at all); BUG-024 is a pure **client-side feedback/UX** defect
  (`Cockpit.tsx` has no pending-state or independent live-update channel,
  unlike its own sibling `AgentDetailPanel.tsx`). Fixing BUG-022 (fewer
  agents dispatched per message) would shrink BUG-024's typical wait
  window but would NOT eliminate it — even a single remaining brought-in
  agent's real Provider call can take many real seconds with zero visible
  feedback today. Both bugs share one contributing architectural factor
  (the synchronous, sequential, multi-agent loop in `send_user_message`)
  without being the same defect — each has its own distinct fix location
  (`threads.py`'s dispatch loop vs. `Cockpit.tsx`'s own missing
  pending-state/live-update handling) and is specced as its own scenario
  below.

### BUG-025 — chat renders plain text, not rich text, in all 3 chat surfaces (UI, Major)
- **Screen/route:** Meeting Cockpit, Inbox Cockpit, and the Agents Map's
  embedded agent chat panel (all three).
- **Repro:** send/receive a message containing markdown formatting (bold,
  lists, links) in any of the three surfaces; observe how it renders.
- **Expected (BUGS.md's own text):** rich text renders as formatted
  content — "this already shipped once (`REQ-SB-32`, 'Rich Text Rendering
  in Agent Chat') and should hold across all three chat surfaces."
- **Actual:** messages render as plain, unformatted text in all three
  surfaces.
- **Code-confirmed, factually different premise — see `gate_reason` and
  `## Notes`:** `REQ-SB-32` was **never spec'd or built.** `BACKLOG.md`
  row 53: `| REQ-SB-32 | Rich Text Rendering in Agent Chat | — | — | — |
  — |` — no story link, no status, no sprint. `Documentation/PRD.md`'s own
  `REQ-SB-32` section carries an explicit unfinalised-requirement comment:
  "Raised 2026-08-12, operator-directed... explicitly logged as a
  discussion topic, not scoped or built this pass... Left to `/spec`,
  whenever picked up," and names three genuinely open design questions
  (which markdown subset, which rendering approach/library, whether user
  messages also render as rich text). Direct code confirms this: neither
  `Cockpit.tsx` (`{message.text}`, line ~135) nor `AgentDetailPanel.tsx`
  (`{message.text}`, line ~775) does anything but render the raw string;
  `package.json` has **no markdown/rich-text dependency at all**
  (`react`, `react-dom`, `react-router` only). Every chat surface has
  always rendered plain text — there is no prior working state to regress
  FROM. BUG-025's own Expected text is still a valid, real, reproducible
  UI gap (confirmed live: raw `**`/`-` syntax IS what actually renders
  today) — only its "already shipped once... should hold" framing is
  incorrect. Scenario 4 below specs the observable Expected outcome
  BUG-025 itself demands, which is a valid target regardless of this
  discrepancy; see `## Notes` for what this means for scoping the fix.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then) by the analyst; the
decomposer locks and AC-IDs these at /plan-tasks. One scenario per bug in
this batch, per the triage-mode contract. -->

### Scenario 1: Only the addressed agent responds to a message (BUG-022)

```gherkin
Given the Cockpit's shared chat (Meeting Cockpit or Inbox Cockpit) already
    has more than one agent brought in
  And the user's message text @-mentions exactly one of those
    already-brought-in agents, by id or name
When the user sends that message
Then only the @-mentioned agent generates and posts a reply to the shared
    thread
  And every OTHER currently brought-in agent posts no reply for that
    message
```
<!-- AC-ID: BUGFIX-04-US-01-AC-01 -->

### Scenario 2: Pressing Enter sends the message (BUG-023)

```gherkin
Given the user has typed a non-empty message into either Cockpit's chat
    input (Meeting Cockpit or Inbox Cockpit)
When the user presses the Enter key, without clicking the Send button
Then the message is sent immediately, exactly as clicking Send would
    behave
  And the chat input clears afterward, matching the existing Send-button
    behavior
```
<!-- AC-ID: BUGFIX-04-US-01-AC-02 -->

### Scenario 3: Sent messages and replies appear without a manual refresh (BUG-024)

```gherkin
Given the user has just sent a message in either Cockpit's chat, via
    Send or Enter
When the send request — and every currently-addressed agent's reply for
    that turn — has completed
Then the sent message and every reply are visible in the chat thread
    without the user performing a manual page refresh
  And the chat gives the user some visible indication a request is in
    flight while waiting for that turn to complete
```
<!-- AC-ID: BUGFIX-04-US-01-AC-03 -->

### Scenario 4: Chat messages render as formatted rich text, not literal markdown (BUG-025)

```gherkin
Given a chat message in Meeting Cockpit, Inbox Cockpit, or the Agents
    Map's embedded agent chat panel contains markdown-style formatting
    (e.g. **bold** text, or a "- " bulleted list)
When that message renders in the chat thread
Then it displays as actual formatted rich text (real bold, a real
    bulleted list, etc.)
  And no literal markdown syntax characters (**, -, #, etc.) are visible
    in the rendered output
```
<!-- AC-ID: BUGFIX-04-US-01-AC-04 -->

## Affected Screens

- `html-prototype/` has no existing Cockpit or Agents-Map-chat-panel
  screen file dedicated to this fix batch — Meeting Cockpit/Inbox Cockpit
  were built straight into `src/frontend` per `REQ-SB-43-US-01`/
  `REQ-SB-44-US-01`'s own scope (no prototype precursor); the Agents Map
  chat panel likewise. No prototype reconciliation applies; this is a
  real-app-only fix batch, same posture as prior Cockpit `BUGFIX`/direct
  fixes in this project.

## Dependencies

- **Blocked by:** none for Scenarios 1-3 — `REQ-SB-43-US-01` (Meeting
  Cockpit), `REQ-SB-44-US-01` (Inbox Cockpit), and `REQ-SB-49-US-02`
  (`@mention` bring-in) are all already `Done`; this batch fixes real
  defects in already-shipped code, not new capability.
- **Related to (not a blocker, see gate_reason):** `REQ-SB-32` (Rich Text
  Rendering in Agent Chat, PRD-Draft, never spec'd/built) — Scenario 4
  effectively delivers `REQ-SB-32`'s own Acceptance text for the first
  time, across 3 real chat surfaces, rather than fixing a regression in
  already-built rendering. See `## Notes`.
- **External:** none new.

## Constraints

- Scenario 1's fix must not regress the existing, correct
  no-mention/broadcast-to-all-brought-in behavior when a message genuinely
  has no `@mention` at all (e.g. a general follow-up after an agent's own
  reply) — today's only-brought-in-agent case (one agent in the thread)
  must keep working exactly as it does today. The precise fallback
  routing rule for a no-mention message in a MULTI-agent thread is an
  architecture/decomposer-level decision, not decided here.
- Scenario 3's fix must not regress `send_user_message`'s own real,
  sequential, per-agent conversational turn — this story does not mandate
  a specific technical mechanism (polling vs. websocket vs. simply making
  the existing `reload()` reliably fire with a visible pending state); the
  concrete approach is left to `/plan-tasks`.
- Scenario 4's rendering fix must not let raw/unescaped user- or
  agent-authored text execute as HTML (a real, if latent, XSS surface the
  instant ANY markdown-to-HTML rendering is introduced) — whichever
  rendering approach `/plan-tasks` adopts must sanitize or use a
  React-safe rendering path, never raw `dangerouslySetInnerHTML` of
  unsanitized content.
- This batch touches three real, live UI surfaces
  (`src/frontend/src/features/cockpit/Cockpit.tsx`,
  `src/frontend/src/features/agents-map/AgentDetailPanel.tsx`) plus the
  backend Cockpit dispatch path (`src/backend/app/business/cockpit/
  threads.py`) — no vault/note-content risk, but a real regression risk
  to already-`Done` Cockpit/Agents-Map-chat behavior; each scenario above
  is independently verifiable and should not require touching the other
  scenarios' own fix locations.

## Implementation Tasks

<!-- Decomposer pass, /plan-tasks step 2, 2026-08-19: supersedes the
analyst's starting-point sketch. Real dependency shape (direct reading of
Cockpit.tsx/AgentDetailPanel.tsx/threads.py/cockpitApiClient.ts/
cockpit_router.py) merges the analyst's T02 (form/Enter) and T03
(pending-state) plus BUG-022's own frontend consumer half into ONE task
(T02) -- all three edit the exact same ~15-line handleSendMessage/
chat-input-row region of Cockpit.tsx, and architecture.md itself presents
them as one composed fix. BUG-025's rich-text fix is split into a shared-
foundation task (T03, the new ChatMessageText.tsx component + the new
react-markdown dependency, no locked AC of its own) and a consumer task
(T04, wiring it into both real call sites, carrying AC-04) -- mirrors this
project's own "generic-primitive-first, kind-specific-wrapper-second"
precedent (SPRINT-048) applied to a shared component instead of a shared
function. See ## Notes for the full dependency-graph rationale. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| BUGFIX-04-US-01-T01 | backend | Scope `send_user_message`'s per-agent dispatch to an optional `addressed_agent_ids` list, falling back to today's broadcast when absent (BUG-022 backend half) | `src/backend/app/business/cockpit/threads.py`, `src/backend/app/api/cockpit_router.py` | `../Tasks/BUGFIX-04-US-01-T01-addressed-agent-dispatch.md` |
| BUGFIX-04-US-01-T02 | frontend | Cockpit chat send flow: submit-on-Enter form (BUG-023), pending/in-flight state applying the send response directly instead of a redundant `reload()` (BUG-024), and wiring `resolveMentionedAgents`' output through to `sendCockpitMessage`'s new `addressedAgentIds` argument (BUG-022 frontend half) | `src/frontend/src/features/cockpit/Cockpit.tsx`, `src/frontend/src/features/cockpit/cockpitApiClient.ts` | `../Tasks/BUGFIX-04-US-01-T02-cockpit-send-flow-enter-and-pending-state.md` |
| BUGFIX-04-US-01-T03 | frontend | New shared `ChatMessageText.tsx` component wrapping `react-markdown` v9.x (zero plugins, default-safe), plus the new `package.json` dependency (BUG-025 foundation, per `ADR-050`) | `src/frontend/package.json`, `src/frontend/src/components/ChatMessageText.tsx` | `../Tasks/BUGFIX-04-US-01-T03-chat-message-text-component.md` |
| BUGFIX-04-US-01-T04 | frontend | Apply `ChatMessageText` in place of each literal `{message.text}` in both Cockpit's and the Agents Map chat panel's chat-thread renders, symmetric for user and agent messages (BUG-025 consumers) | `src/frontend/src/features/cockpit/Cockpit.tsx`, `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` | `../Tasks/BUGFIX-04-US-01-T04-apply-chat-message-text-rendering.md` |

## Definition of Done

- [x] All 4 acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped
      with reason)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] `BUG-022`, `BUG-023`, `BUG-024`, `BUG-025` flipped
      `In Sprint → Closed` in both `BUGS.md` and `BACKLOG.md`'s `## Bugs`
      mirror once this story is `Done`

## Non-Goals / Out of Scope

- Any change to which agents CAN be brought into a Cockpit thread, or the
  `@mention` bring-in mechanism itself (`REQ-SB-49-US-02`) — Scenario 1
  only changes who RESPONDS to an already-brought-in set, not who can join.
  - Full CommonMark support, or any markdown feature beyond the common
    chat-reply subset (bold/italic/lists/links) — the exact subset is an
    open `/plan-tasks` decision per `REQ-SB-32`'s own PRD comment, not
    decided here.
- Whether a user's own typed message (not just an agent's reply) should
  also render as rich text — one of `REQ-SB-32`'s own explicitly-named
  open questions; Scenario 4 is written generically ("a chat message...")
  so `/plan-tasks` can resolve this without re-specing.
- Streaming/token-by-token agent replies — Scenario 3's Expected text
  only requires the sent message and completed replies to appear without
  a manual refresh, not a token-streaming UX (BUG-024's own "streams/
  appears as it arrives" wording is aspirational framing, not a strict
  requirement this scenario locks in).

## Notes

**Prototype parity:** not applicable — no `html-prototype/` screen covers
Cockpit or the Agents Map chat panel; both were built straight into the
real app. Same posture as `BUGFIX-01-US-01`/`BUGFIX-03-US-01`.

**Why `gate: flagged` (triggers 2, 7, 8 — Scenario 4 / `BUG-025` only):**
This triage batch's own briefing characterized `BUG-025` as "a regression
against already-shipped `REQ-SB-32`." Direct re-reading of `BACKLOG.md`
(row 53: no story link, status `—`), `Documentation/PRD.md` (`REQ-SB-32`'s
own comment: "not scoped or built this pass... Left to `/spec`, whenever
picked up"), and the real frontend code (`Cockpit.tsx`/
`AgentDetailPanel.tsx` both render `{message.text}` raw; `package.json`
has zero markdown/rich-text dependencies) all confirm `REQ-SB-32` was
**never actually specced or built** — there is no prior working rich-text
render to have regressed FROM. This is a genuine, material contradiction
between this triage batch's own framing and the real, current state of
the codebase (trigger 7), it rests on a PRD requirement still explicitly
marked as an unresolved discussion topic (trigger 2), and that same PRD
comment names multiple genuinely open, equally-valid design forks —
markdown subset, rendering library/approach, and whether user messages
also render (trigger 8). This does **not** invalidate `BUG-025`'s own
live-observed symptom (raw markdown syntax IS what renders today, in all
3 surfaces, confirmed by direct code reading) — Scenario 4 above specs
that real, valid observable outcome and remains a correct target
regardless of this discrepancy. It DOES mean: (a) the resulting fix is
net-new capability-building, not a small regression patch — expect a real
`/plan-tasks` design pass (library choice, sanitization approach) rather
than a one-line change, unlike Scenarios 1-3; (b) the human should decide
whether `REQ-SB-32`'s own PRD entry should be updated (its Draft/
discussion-only comment removed, formally satisfied by this story) once
Scenario 4 ships, since right now `BACKLOG.md` will show `REQ-SB-32` as
still unlinked/unbuilt even after this bugfix story closes it in
practice — a reconciliation `/plan-tasks`/human step, not decided here.
Full write-up: `ESCALATIONS.md` → `ESC-053`. `REVIEW-QUEUE.md` entry
added pointing here.

Scenarios 1-3 (`BUG-022`/`BUG-023`/`BUG-024`) fired NO trigger — each is a
direct, code-confirmed defect in already-`Done`, already-shipped Cockpit
work (`REQ-SB-43-US-01`/`REQ-SB-44-US-01`/`REQ-SB-49-US-02`, all `Done`),
with an unambiguous, single-interpretation Expected outcome and, for
Scenarios 2/3, a working in-codebase precedent to mirror
(`AgentDetailPanel.tsx`'s own form-submit-on-Enter and pending-state
handling).

**BUG-022 vs. BUG-024 — related or independent? (recorded per the triage
brief's own request):** Independent defects sharing one contributing
architectural factor. BUG-022 is a pure server-side dispatch-selection gap
inside `threads.py::send_user_message`'s per-agent loop (who gets sent
to). BUG-024 is a pure client-side feedback/live-update gap inside
`Cockpit.tsx` (no pending state, no independent update channel beyond one
post-send `reload()` call) — confirmed by direct contrast with
`AgentDetailPanel.tsx`, which already solves the identical "wait for a
real, possibly-slow Provider call" problem with a `sending` state, a
disabled input, and a typing-dot indicator that Cockpit's own chat never
adopted. Both sit inside the same synchronous, sequential,
all-brought-in-agents loop `send_user_message` runs, so fixing BUG-022
(dispatching to fewer agents per message) would shrink BUG-024's typical
wait window as a side effect, but would not fix it outright — a single
remaining agent's real Provider call can still take many seconds with
zero visible feedback. Specced and scoped as two independent scenarios/
fixes (Scenario 1 / `T01` vs. Scenario 3 / `T03`) rather than one, so
either can ship and be verified without depending on the other.

gate: flagged 2026-08-19 — triggers 2/7/8 fired on Scenario 4 (`BUG-025`)
only, per the full reasoning above. No other trigger fired: no ADR
created/changed by this analyst pass (out of scope for `/spec`); no
`ESCALATIONS.md` entry beyond `ESC-053` itself, which this same flag
already names; Scenarios 1-3 are each small, single-fix-location,
one-working-session-sized — not oversized; no contradictory inputs remain
for Scenarios 1-3 (each bug's own repro/expected is unambiguous and
code-confirmed).

**Resolution (2026-08-19, operator in full autopilot for the remainder of
the session):** the three open design questions above are resolved
directly rather than left blocking — all three are ordinary, low-risk,
easily-reversible frontend implementation choices, not data-integrity or
destructive-action decisions, and are squarely the kind of call this
project's own established pattern resolves directly with disclosed
reasoning rather than blocking on unavailable human input (mirrors
`ADR-047`/`ADR-048`/`ADR-049`'s own "resolved directly, reasoning
disclosed" precedent tonight, scaled down to a much smaller, purely
technical decision).
1. **Markdown subset:** the common baseline a Compass-generated response
   would naturally produce — bold/italic, bulleted/numbered lists, links,
   inline/block code, headings. Not exhaustive CommonMark/GFM support;
   covers everything a real agent reply is likely to contain.
2. **Library:** `react-markdown` — the standard, well-established choice
   for this exact purpose in a React app; no exotic alternative needed,
   no new architectural pattern for this codebase to learn.
3. **Scope — does the USER's own sent message also render as rich text,
   or only agent replies?** Both. Grounded directly in the operator's own
   literal words reporting this bug — "All Text Should be Rich Text in
   Chat" — which draws no agent/user distinction; the fix is symmetric
   across every message in the thread, not agent-replies-only.

Scenario 4's own Gherkin (written above, observable-behavior-only, no
hardcoded library choice baked into the AC itself) needs no rewording
under this resolution — it already specs the right target; this
resolution only fills in the implementation-level questions the decomposer
would otherwise have needed a human answer for. `ESC-053` stays `Open` in
`ESCALATIONS.md` as the permanent, unedited record of the original
REQ-SB-32 discrepancy finding — this Notes section is the resolving note,
append-only, not a retraction of that finding. `gate: clear`, eligible for
`/plan-tasks`.

---

**Architect pass (2026-08-19, `/plan-tasks` step 1):**

**ADR-050 created — Scenario 4 / `BUG-025` (trigger 3, `gate: flagged`).**
`Documentation/PRD.md`, `architecture.md`, `ADR.md`, and `MEMORY.md` were
all read fresh; the operator's own already-resolved markdown-subset/
library/scope questions (above) are treated as settled inputs, not
re-litigated. What remained genuinely architectural — exactly how
`react-markdown` is wired (plugin surface) and, specifically, its
sanitization posture against this story's own XSS Constraint — is now
`ADR-050` (`Implementation/Architecture/ADR.md`): `react-markdown` v9.x,
zero remark/rehype plugins (no `remark-gfm`/`rehype-raw`/
`rehype-sanitize`), default-safe by omission (no `dangerouslySetInnerHTML`
path exists absent `rehype-raw`, which this decision does not add; link/
image URLs pass through `react-markdown`'s own built-in
`defaultUrlTransform`, which already strips non-`http(s)`/`mailto`/`tel`
schemes), and one new shared `src/frontend/src/components/
ChatMessageText.tsx` component consumed by both real call sites
(`Cockpit.tsx`'s chat-thread map and `AgentDetailPanel.tsx`'s chat-thread
map — confirmed by direct inspection there is no third, separate Agents-
Map-chat-panel component; `AgentDetailPanel.tsx` IS that surface),
applied symmetrically to both user- and agent-authored messages, per the
operator's own resolution. Full reasoning, every alternative considered
(string→HTML parsers + `dangerouslySetInnerHTML`, hand-assembled `remark`/
`rehype`, a hand-rolled regex transformer, `remark-gfm` now, a second
`rehype-sanitize`/DOMPurify layer, per-file duplicated wiring instead of a
shared component), and consequences: `ADR-050`. Per `Pipeline.md`'s
MUST-FLAG trigger 3, this story's `gate:` flips to `flagged` /
`gate_reason: trigger-3 (ADR-050 created)` even though the underlying
choice was already fully resolved by the operator — the ADR-creation
trigger fires on the act of creating the ADR, not on how contested the
decision was. Per the same trigger's own contract, this does NOT halt
`/plan-tasks` — the decomposer still runs against this story so a human
reviews `ADR-050` and the resulting locked ACs/tasks together in one pass.
A `REVIEW-QUEUE.md` pointer is added; the earlier, now-resolved
`BUGFIX-04-US-01` review-queue entry (about `BUG-025`'s scope/framing) is
marked resolved in place, not deleted.

**Scenarios 1-3 (`BUG-022`/`BUG-023`/`BUG-024`) — no new ADR, no new
trigger.** Each fix composes an already-`Accepted` mechanism without
introducing a new tool, framework, endpoint, persisted store, or
structural boundary:
- **BUG-022:** `threads.py::send_user_message` gains an optional
  `addressed_agent_ids: list[str] | None = None` parameter (and a matching
  optional field on `POST /cockpit/{subject_kind}/{subject_note_stem}
  /message`'s request body); its dispatch loop iterates that list when
  present, falling back to today's `thread["brought_in_agent_ids"]`
  broadcast when absent/empty — preserving the Constraint that a
  no-mention message (including the single-brought-in-agent case) keeps
  behaving exactly as it does today. **The addressee list is `REQ-SB-49-
  US-01`'s existing frontend `resolveMentionedAgents(messageInput,
  bringInCandidates)` output, reused as a second consumer — never a second,
  independently-maintained Python mention parser.** `Cockpit.tsx`'s
  `handleSendMessage` already computes `mentionedAgents` and already
  awaits `bringInAgent(...)` for each before sending; it now additionally
  passes `mentionedAgents.map((agent) => agent.id)` as
  `sendCockpitMessage`'s new `addressedAgentIds` argument.
- **BUG-023:** `Cockpit.tsx`'s `chat-input-row` becomes a real
  `<form onSubmit={handleSendMessage}>` (Send button → `type="submit"`),
  mirroring `AgentDetailPanel.tsx`'s own already-working `<form
  onSubmit={handleSend}>` precedent exactly — no new CSS, no new
  interaction pattern. The `@mention` suggestion-dropdown row buttons stay
  explicit `type="button"` so a suggestion click does not also submit the
  in-progress message.
- **BUG-024:** `Cockpit.tsx` gains a `sending` boolean state (mirroring
  `AgentDetailPanel.tsx`'s own `sending`/typing-dot/disabled-input
  pattern verbatim, same `.chat-typing-dot` CSS class, no new CSS) plus a
  real simplification: `sendCockpitMessage`'s response is already the
  fully updated `CockpitThread` (confirmed live) — the fix applies it
  directly via `setData(...)` instead of firing a separate `reload()` GET
  afterward. **No SSE/polling/websocket is introduced** — `send_user_
  message` already returns complete post-turn state synchronously in one
  HTTP response; `REQ-SB-42`'s existing SSE `agent-presence` channel
  (`ADR-035`) was considered and rejected as an unrelated, broadcast-only
  cross-agent-activity mechanism, not a fit for relaying one thread's own
  completed reply back to one requesting tab.

Full module-shape write-up for all four scenarios: `architecture.md` →
"Cockpit Chat — Addressed-Reply Dispatch, Send-on-Enter, and Pending-State
Live Update" (BUG-022/023/024) and "Chat Rich-Text Rendering —
`react-markdown`" (BUG-025), both appended directly after "Cockpit
Person-Directed Instruction." `architecture.md`'s Tech Stack table and
`Last reviewed` footer are updated accordingly.

**Architecture scope (bounds the decomposer/coder):** `Implementation/
Architecture/architecture.md` → "Cockpit Chat — Addressed-Reply Dispatch,
Send-on-Enter, and Pending-State Live Update (`BUGFIX-04-US-01`,
`BUG-022`/`BUG-023`/`BUG-024`...)" for Scenarios 1-3, and "Chat Rich-Text
Rendering — `react-markdown` (`BUGFIX-04-US-01`, first real delivery of
`REQ-SB-32`, see [ADR-050])" for Scenario 4 — plus, as background context
only (unmodified by this story), §"Meeting & Inbox Cockpits — multi-agent
shared-thread workspace" and §"Cockpit Inline `@agent_id` Mention." No
other `architecture.md` section is in scope.

No assumptions were made beyond the operator's own already-recorded
Scenario 4 resolution (above); no contradiction with any `Accepted` ADR,
PRD text, or `MEMORY.md` constraint (`ADR-036`'s Cockpit shape and `ADR-
015`'s `run_agent_conversation` contract are both extended, not reopened —
confirmed by direct reading before writing `ADR-050` and the two
architecture.md sections above).

---

**Decomposer pass (2026-08-19, `/plan-tasks` step 2):**

**AC locking.** Locked the analyst's 4 untagged Gherkin scenarios verbatim
(no wording tightened — each was already buildable and single-
interpretation as written) as `BUGFIX-04-US-01-AC-01` (Scenario 1,
BUG-022), `AC-02` (Scenario 2, BUG-023), `AC-03` (Scenario 3, BUG-024),
`AC-04` (Scenario 4, BUG-025). All 4 locked by default — none marked
`locked: false`.

**Task decomposition — real dependency shape, not a mechanical 1:1 with
the 4 scenarios.** Read the real current `Cockpit.tsx`, `AgentDetailPanel.
tsx`, `threads.py`, `cockpitApiClient.ts`, and `cockpit_router.py` before
splitting (per this project's own "compose around the REAL current file"
precedent) — confirmed three real findings that shaped the split:
1. `Cockpit.tsx`'s `handleSendMessage` function and its immediately
   surrounding `chat-input-row` JSX (~15 lines total) are the SAME exact
   region all three of BUG-022's frontend consumer half, BUG-023's
   form-wrap, and BUG-024's pending-state/response-application changes
   land in — confirmed by direct reading, not assumed from the story's own
   prose. Splitting these into 3 separate tasks would mean 3 sequential
   edits to the same ~15 lines, each needing to re-read the prior task's
   own just-landed change; combining them into one task (`T02`) is a
   tighter, real dependency-shape fit, still well within one working
   session (~40-50 line diff in one file — not oversized, trigger 5 does
   not fire).
2. `threads.py::send_user_message`'s dispatch loop and `cockpit_router.py`'s
   request body are a clean, independent backend concern (`T01`) with no
   frontend file overlap — kept separate from `T02`.
3. `react-markdown`/`ChatMessageText.tsx` (BUG-025) has a genuine two-phase
   shape: a shared, foundation component with no consumer yet (`T03`, no
   locked AC of its own — the component alone doesn't satisfy AC-04 until
   it's actually wired into a real chat surface) and its two real call-site
   substitutions (`T04`, carries `AC-04`) — mirrors this project's own
   "generic-primitive-first, kind-specific-wrapper-second" precedent
   (`Implementation/Learnings.md`, `SPRINT-048`), applied to a shared
   component instead of a shared function.

**`depends_on` (task IDs only, acyclic by inspection):**
- `BUGFIX-04-US-01-T01`: `[]` — backend-only, no upstream task.
- `BUGFIX-04-US-01-T02`: `[BUGFIX-04-US-01-T01]` — `T02`'s own frontend
  wiring of `mentionedAgents.map((agent) => agent.id)` into
  `sendCockpitMessage`'s new `addressedAgentIds` argument is only
  genuinely correct once `T01`'s backend dispatch scoping exists to
  receive it; sequenced, not left independent.
- `BUGFIX-04-US-01-T03`: `[]` — new file + a `package.json` dependency
  addition, no existing file touched, no upstream task.
- `BUGFIX-04-US-01-T04`: `[BUGFIX-04-US-01-T03]` — cannot import a
  component that doesn't exist yet.
`T02` and `T04` both touch `Cockpit.tsx`, but in two disjoint regions
(the send-flow/input-row block vs. the chat-thread message-rendering
block) with no functional coupling — no `depends_on` edge added between
them; each reads the real current file at build time regardless, per this
project's own standing convention.

**AC → verification mapping.**
- `AC-01` is tagged in `T01`'s own `## Tests` (step 1) — verified directly
  at the backend layer (a real `send_user_message` call with an explicit
  `addressed_agent_ids` list against a real, multi-agent-brought-in
  thread), mirroring this project's own "backend-layer-first live
  verification" precedent (`Implementation/Learnings.md`, `SPRINT-019`/
  `SPRINT-023`) — the NEW logic BUG-022 adds lives entirely in
  `send_user_message`'s dispatch loop; the @-mention-text-to-agent-id
  resolution itself is `REQ-SB-49-US-01`'s own already-shipped, unchanged
  `resolveMentionedAgents`, not re-verified here. `T02` additionally
  carries a non-AC-tagged bonus end-to-end UI repro of the same behavior
  (send an `@agent_id`-addressed message through the real Cockpit chat
  input with 2+ agents brought in), closing the loop once the frontend
  wiring lands — not required for `AC-01`'s own pass/fail, extra
  confirmation per this project's own "add one extra, clearly-labeled real
  end-to-end check beyond what's strictly required" precedent
  (`SPRINT-019`).
- `AC-02` and `AC-03` are both tagged in `T02`'s own `## Tests` (the real
  Cockpit chat, live in a browser or via the established CDP-driver
  technique this project uses for React state verification).
- `AC-04` is tagged in `T04`'s own `## Tests` — structural DOM assertions
  (a `**bold**` source string renders a real `<strong>` element with no
  literal `**` in the rendered text; a `- ` list item renders a real
  `<li>`) across both `Cockpit.tsx` and `AgentDetailPanel.tsx` call sites,
  for both a user- and an agent-authored message.
- `T03` carries its own non-AC-tagged smoke verification (the component
  renders markdown to real DOM elements in isolation) — `AC-04` itself is
  only satisfied once `T04` wires it into a real chat surface, so it is
  not tagged in `T03`.

Every locked AC (`AC-01`-`AC-04`) has at least one matching ID-tagged
verification step — confirmed. `depends_on` is acyclic (`T01→T02`,
`T03→T04`, two independent chains) — confirmed by inspection.

**Gate check — no new trigger fired this pass.** No material assumption
filled a genuine gap (the task-split and dependency-edge choices above
each have one clearly-better answer given the real file-overlap evidence
found by direct reading, not a genuine multiple-equally-valid fork); no
`Draft`/unfinalised requirement newly relied on (the operator's own
Scenario 4 resolution and `ADR-050`, both already `Accepted`/settled, are
treated as fixed inputs, not re-opened); no ADR created or changed by this
pass; no new `ESCALATIONS.md` entry needed; all 4 tasks are small,
single-concern-scoped, well within one working session (the largest,
`T02`, is a ~40-50 line diff in one already-read file) — not oversized;
every locked AC is directly, live-verifiably observable (a real dispatch
count, a real Enter-key send, a real pending indicator + thread update, a
real rendered `<strong>`/`<li>` DOM element) — none unverifiable; no
contradictory inputs remain for this pass (the story's own prior two flags
were both already resolved, by the operator directly and via `ADR-050`,
before this pass began — this pass re-litigates neither). **This story's
own `gate: clear` (set by the operator's own resolution, preserved from
before this pass) is left unchanged** — this decomposer pass introduces no
new MUST-FLAG trigger of its own, so there is no basis to flip it back to
`flagged`. The `REVIEW-QUEUE.md` `ADR-050` pointer entry is checked off in
place (resolved, not deleted) as part of this pass, since the story it
points at has now demonstrably proceeded through `/plan-tasks` with
`ADR-050` as a settled, reviewed input.

`gate: clear 2026-08-19` — story `status:` advances `Draft → Ready`; all 4
tasks are written at `status: Ready`, per Pipeline.md's "task status moves
in lockstep with the story" rule. Eligible for `/plan-sprints`.

---

**Product-owner pass (2026-08-19, `/plan-sprints`):** confirmed the only
`Ready`, ungrouped story this pass (scanned all `Implementation/
UserStories/*.md` for `status: Ready` + `sprint: ""`; three other `Ready`
stories found — `REQ-SB-72-US-01`, `REQ-SB-59-US-01`, `REQ-SB-42-US-01` —
already carry a `sprint:` value and were excluded). Grouped standalone into
a new single-story sprint, `SPRINT-064` (`phase: ""`, per Pipeline.md hard
rule 8's bugfix exception) — its 4 tasks form two independent, acyclic
dependency chains (`T01→T02`, `T03→T04`) exactly as the decomposer recorded
them, no cross-sprint edge needed. `sprint: SPRINT-064` set above
(bidirectional link). No new trigger fired this pass — `gate: clear`,
sprint advanced `Draft → Ready`. `BACKLOG.md`'s Sprint Status table updated
with the new row; the `## Bugs` mirror already carries `BUG-022`-`025` at
`In Sprint` / `Fixed by: BUGFIX-04-US-01` from `/triage`, unchanged by this
pass. Full sprint file: `Implementation/Sprints/
SPRINT-064-cockpit-chat-addressing-input-and-rendering-fixes.md`.

---

**Coder pass (2026-08-19, `/implement-sprint SPRINT-064`):** all 4 tasks
built and verified live, `T01→T02` and `T03→T04` in dependency order. All 4
locked ACs verified against real, live evidence (real backend dispatch, a
real Meeting Cockpit in a real browser, real Enter-key/pending-state/
live-update behavior, real DOM `<strong>`/`<li>` structural checks across
all 3 named chat surfaces) — full evidence in each task's own
Implementation Log. Two disclosed, verification-harness-only adaptations
(neither touches app code, both fully explained in `T02`'s Implementation
Log): a throwaway local proxy + a second, additional Vite dev-server
instance on the already-whitelisted `5174` origin (to work around headless
Edge 151's Private-Network-Access preflight rejection, itself caused by a
pre-existing, unmodified `CORSMiddleware` config gap — see the new
`MEMORY.md` Constraint), and `form.requestSubmit()` paired with a real
CDP-dispatched Enter keydown/keyup (to work around headless Edge 151's CDP
`Input` domain not triggering Blink's native "Enter submits" default
action, itself confirmed unrelated to this codebase's own zero custom
`onKeyDown` handling). One disclosed, live Provider/MCP outage (pre-
existing, predates this task, confirmed via a fresh isolated-process
control that succeeded before the outage set in) meant `AC-04`'s
agent-authored-content checks used content injected directly into the
same real persisted store / intercepted at the one real network call the
send makes, while the RENDERING itself ran through 100% real, unmodified
app code and a real browser DOM — disclosed in full in `T02`/`T04`'s own
Implementation Logs. A genuine, pre-existing, unrelated bug was found
incidentally while selecting a live-verification meeting note
(`app/business/cockpit/people.py::resolve_people_chips` 500s on a Meeting
note whose real `attendees` frontmatter is a list of plain wikilink
strings rather than dicts) — out of this task's own `## Files to Modify`,
not fixed here; flagged in `REVIEW-QUEUE.md` for a `/bug` capture. No
locked AC was weakened, omitted, or deleted. `gate: clear` — no MUST-FLAG
trigger fired by this coder pass itself (the two harness adaptations and
the Provider outage are disclosed, verification-technique/environment
facts, not scope-internal judgement calls that reinterpret a locked AC).
`status: Done`. `BUG-022`/`023`/`024`/`025` flipped `In Sprint → Closed` in
`BUGS.md` and `BACKLOG.md`'s `## Bugs` mirror.
