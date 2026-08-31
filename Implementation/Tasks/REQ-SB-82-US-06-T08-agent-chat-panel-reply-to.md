---
id: REQ-SB-82-US-06-T08
title: AgentChatPanel.tsx — client-side reply-to/context-anchoring affordance (no backend dependency)
parent_story: REQ-SB-82-US-06
requirement_id: REQ-SB-82
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-08-31
updated: 2026-08-31
---

# REQ-SB-82-US-06-T08 — AgentChatPanel.tsx: client-side reply-to/context-anchoring affordance (no backend dependency)

## Parent Story

- Story: [[REQ-SB-82-US-06]] — `../UserStories/REQ-SB-82-US-06-live-routing-fix-and-reply-to-message.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Add a reply-to-message affordance to `AgentChatPanel.tsx`, starting from
zero message-id/persistence concept, that anchors the referenced earlier
message's own text as extra context in the outgoing request — purely
client-side, no backend schema change, no LLM-moderator involvement
(`ADR-012` point 5: only one agent ever answers here, so reply-to can never
change who answers).

---

## Starting State → End State

**Before / Inputs:**
- `AgentChatPanel.tsx`'s local `ChatMessage` interface
  (`role`/`text`/`isError`/`activity`/`isStreaming`) has no `id` field and
  no persistence — a stateless streaming call. `sendChatMessage`/
  `streamChatMessage`/`sendChatMessageWithAttachment` (`agentsApiClient.ts`)
  each take only a plain `message: string` — no separate context
  parameter.

**After / Outputs:**
- `ChatMessage` gains a client-only `localId: string` (assigned at append
  time, e.g. a simple incrementing counter or `crypto.randomUUID()` — never
  persisted, never sent to the backend as-is).
- Each rendered message (not the live-streaming placeholder bubble) exposes
  a Reply affordance, same shape/convention as `T07`'s Cockpit one (a
  small icon button, `aria-label="Reply to this message"`), setting local
  state `replyToLocalId: string | null` to that message's own `localId`.
- A preview strip renders above the composer when `replyToLocalId` is set
  (`data-role="reply-to-preview"`, truncated quoted text, cancel control) —
  same DOM-structural shape as `T07`'s, for a consistent pattern across
  both surfaces (this task builds it independently — no shared component
  is introduced, per `ADR-012` point 5's own "these two features share
  only the same user-facing verb, not an implementation").
- **Context-anchoring mechanism:** when sending with a `replyToLocalId`
  selected, `handleSend` composes the outgoing `message` text sent to
  `sendChatMessageWithAttachment`/`streamChatMessage` as the referenced
  message's own text plus the user's new text (e.g. a quoted-context
  prefix: `> {parentText}\n\n{userText}`) — this is the real anchoring
  mechanism (Scenario 4's "included as anchoring context"), since neither
  API function accepts a separate context parameter and no backend change
  is in scope (`ADR-012` point 5). The user-facing chat bubble still shows
  only the user's own typed text (`bubbleText`), never the composed
  quoted-prefix version — the anchoring is invisible plumbing, not a
  visible echo.
- `replyToLocalId` clears after send (success or failure), same pattern as
  `attachedFile`/`draft`.
- **Stale-reference safety (Scenario 8):** `replyToLocalId` is only ever
  set to a `localId` that exists in the CURRENT `messages` array (selected
  directly from a rendered message), so it cannot itself go stale within
  one mount — but `useEffect`'s existing agent-switch/`handleNewChat`
  reset (which clears `messages` to `[]`) must also clear
  `replyToLocalId`, so a leftover selection from before a reset never
  produces a broken preview referencing a message that no longer exists.

---

## Files to Modify

- `src/frontend/src/features/chat/AgentChatPanel.tsx` — the `ChatMessage`
  interface, per-message Reply affordance, `replyToLocalId` state, the
  composer preview strip, `handleSend`'s message-composition change, and
  the agent-switch/`handleNewChat` reset extension.

---

## Constraints

- Inherits from parent story.
- **No backend/API-client file changes** (`ADR-012` point 5 — explicitly
  no schema change for this surface); `agentsApiClient.ts` is out of this
  task's `## Files to Modify`.
- **Never changes who answers** — there is only ever the one `agentId` this
  panel is pointed at; this task must not introduce any routing/agent-
  selection logic.
- **DOM-structural ACs only** — same "structural ACs for screens"
  convention as `T07`; no locked assertion on exact visual styling. This
  surface's own visual treatment is `net-new-design-needed` (decomposer-
  made judgement call, disclosed in the parent story's Notes, flagged for
  a non-blocking design spot-check, not a `/design` prototype gate before
  build).
- Do not persist `replyToLocalId`/message ids anywhere (no `localStorage`,
  no backend call) — purely in-memory for the current mount, matching
  `ADR-012`'s own explicit rejection of building a Chat-panel-side store.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-82-US-06-AC-04]` Render the panel with an existing message
   history (send 2+ messages first); click Reply on an earlier message;
   confirm `[data-role="reply-to-preview"]` renders with that message's own
   text. Send a new message; using a `window.fetch`/`streamChatMessage`
   call-argument spy, confirm the outgoing `message` payload sent to the
   backend contains BOTH the referenced message's own text AND the user's
   newly typed text — while the rendered user bubble in the DOM shows only
   the user's own typed text, not the quoted prefix. Confirm no second
   agent/routing concept is invoked anywhere in this flow (this panel only
   ever has the one `agentId` it was given).
2. `[REQ-SB-82-US-06-AC-08]` Select a message to reply to, then trigger
   `handleNewChat()` (or switch `agentId`, which resets `messages`);
   confirm `replyToLocalId` is cleared along with `messages`, and no
   broken/blank preview renders afterward; confirm a subsequent Send in
   the fresh thread works normally with no crash.
3. Cancel a selected reply-to via the preview strip's cancel control;
   confirm the preview disappears and the next Send's outgoing `message`
   is the plain user text with no quoted prefix (no AC tag — supports the
   "hint is optional, cancellable" shape, mirroring `T07`'s own cancel
   check).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] A Reply affordance renders on each real message; selecting one shows
      a preview strip with a cancel control
- [x] Sending with a reply-to selection composes the outgoing request text
      to include the referenced message's own text as anchoring context,
      while the rendered user bubble stays clean (just the typed text)
- [x] Only ever one agent answers — no routing/agent-selection logic
      introduced
- [x] A reply-to selection is cleared on thread reset (`handleNewChat`/
      agent switch) and never produces a broken preview
- [x] No backend/API-client file touched
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any Cockpit change — `T07`, an architecturally separate mechanism
  despite the shared "reply-to-message" user-facing verb.
- Any backend/API contract change.
- Persisting this panel's own message history/reply-to state across a
  reload — explicitly rejected by `ADR-012` point 5 for this pass.

---

## Context / Notes

`ADR-012` point 5 (`Implementation/Architecture/ADR.md`) is the
authoritative design — read it before starting; it explicitly names this
mechanism as diverging in shape from Cockpit's own `T07`, sharing only the
user-facing verb "reply to."

---

## Implementation Log

**Coder pass (2026-08-31).** Read `ADR-012` point 5 and the current, real
`AgentChatPanel.tsx` before starting (confirmed zero `id`/persistence
concept, matching the task's own Starting State). Implemented entirely
within `src/frontend/src/features/chat/AgentChatPanel.tsx`, no other file
touched:

- `ChatMessage` gained `localId: string`, assigned via a simple
  incrementing counter (`nextLocalIdRef`/`generateLocalId()`) at every
  message-append site (user bubble, streaming placeholder, attachment
  reply, error bubble) — not `crypto.randomUUID()`, per the task's own
  first-listed "simple incrementing counter" option; purely in-memory,
  never persisted.
- `replyToLocalId: string | null` state; a per-message Reply button
  (`aria-label="Reply to this message"`, `material-symbols-outlined`
  `reply` icon) renders on every finalized (`!isStreaming`) bubble.
- A composer preview strip (`data-role="reply-to-preview"`) renders above
  the form when `replyToLocalId` resolves against the CURRENT `messages`
  array (`resolvedReplyToMessage`, recomputed every render) — truncated
  quoted text (140-char ceiling) + a cancel button
  (`aria-label="Cancel reply"`).
- `handleSend` resolves `replyToMessage` from the pre-append `messages`
  array, composes `outgoingText = replyToMessage ? "> {parentText}\n\n
  {userText}" : userText`, and sends THAT to both
  `sendChatMessageWithAttachment` and `streamChatMessage`. `bubbleText`
  (what actually renders in the thread) is built from the plain typed
  `text` only, unchanged from before — the anchoring stays invisible
  plumbing. `replyToLocalId` clears immediately on send (same place/
  pattern as `draft`/`attachedFile`), regardless of outcome.
- Both existing reset paths (`useEffect` on `[agentId]`, `handleNewChat`)
  now also clear `replyToLocalId`, per Scenario 8.
- **Scope-internal judgement call (log for human spot-check):** the task's
  `## Files to Modify` names only the `.tsx` file, no CSS file — so the
  new `chat-message-reply-btn`/`chat-reply-to-preview*` class names carry
  no dedicated stylesheet rules yet (render unstyled/browser-default).
  This matches the task's own "DOM-structural ACs only... visual
  treatment is net-new-design-needed... flagged for a non-blocking design
  spot-check" Constraint — read as deliberate (visual polish explicitly
  deferred), not an omission, since adding CSS wasn't in scope. Flagging
  per `SPRINT-037`'s own precedent for a scope-adjacent gap resolved by
  reading the task's own Constraints rather than silently expanding
  `## Files to Modify`.
- Also included the Reply affordance on `isError` bubbles (not explicitly
  excluded by the task, unlike Cockpit's `T07` which excludes only
  `system`-role messages — no such role exists in this panel) — a minor,
  disclosed judgement call; harmless (an unusual but not broken reply
  target).

**Verification (manual mode — real dev server + real headless-browser CDP
session, per this project's own established technique):**

- Real Vite dev server confirmed serving the edited module (transform
  fetch returned 200, contained `generateLocalId`/`reply-to-preview`, no
  parse error) before any interaction testing.
- Drove a real headless Edge (`--headless=new --remote-debugging-port`)
  against the real running frontend (`http://localhost:5173/chat`,
  `AgentChatPanel` pointed at `agentId="default"`) via a minimal
  Node+native-`fetch`+native-`WebSocket` CDP client (no new dependency),
  this project's own established pattern.
- **Disclosed verification-method substitution:** the real backend
  `/chat/stream` reply for this dev environment's Primary agent was
  observed taking 5-6 real minutes and then genuinely erroring
  (unrelated to this task — zero backend files are in scope here). Since
  `handleSend`'s own composition of the outgoing request (the actual
  mechanism under test) fires the instant `streamChatMessage`/`fetch` is
  called, BEFORE any response arrives, verification used a scoped
  `window.fetch` stub for ONLY the `/chat/stream` endpoint's RESPONSE (a
  fast synthetic SSE `complete` frame) — the REQUEST itself (URL, method,
  and critically the composed `message` body) was captured from the
  REAL, unmodified `fetch` call before the stub substituted anything.
  Every other part of the flow (real DOM, real React state transitions,
  real click/keyboard handlers, the real composed request) exercised
  genuine, unmodified app code. This is the same "closest-to-real
  substitute for a genuinely slow/uncontrolled external dependency"
  technique this project's own Learnings already document
  (`SPRINT-025`/`027`/`028`).

- `[REQ-SB-82-US-06-AC-04]` **PASS.** Sent 2 real messages (2 user + 2
  agent bubbles rendered, 4 Reply buttons). Clicked Reply on the FIRST
  message ("What is the capital of France?") — `[data-role="reply-to-
  preview"]` rendered with `"↳ Replying to: What is the capital of
  France?"`. Sent a new message ("Follow-up: what is its population?")
  with a real `window.fetch` spy on the `/chat/stream` call: the captured
  outgoing body was
  `{"message":"> What is the capital of France?\n\nFollow-up: what is
  its population?"}` — contains BOTH the referenced message's own text
  AND the new text, exactly as designed. The rendered user bubble showed
  only `"Follow-up: what is its population?"` (plus the Reply icon's own
  glyph text, an artefact of `.textContent` reading the icon span too) —
  no quoted prefix leaked into the visible bubble. No second-agent/
  routing code path exists anywhere in this component (confirmed by
  direct code review of the diff — `agentId` is passed through unchanged,
  no new routing/selection logic was introduced).
- `[REQ-SB-82-US-06-AC-08]` **PASS.** Selected a message to reply to
  (preview confirmed rendered), then clicked the real "New chat" button
  (confirmed NOT disabled at click time — an earlier verification attempt
  falsely read this as broken because the test harness itself polled the
  wrong signal for "still sending", see below). Result:
  `{"messageCount":0,"previewRendered":false}` — both `messages` and
  `replyToLocalId` cleared together, no broken/blank preview. A
  subsequent real Send in the fresh thread completed normally
  (`messageCount:2`, no console exception).
- Cancel control (unlocked, supports the Tests block's step 3): selected
  a reply target (preview rendered), clicked the preview's own cancel
  button (preview disappeared), sent a plain message — captured outgoing
  body was `{"message":"Plain message with no reply-to."}`, no quoted
  prefix.
- Zero console errors/exceptions across the entire session (`Runtime.
  exceptionThrown` listener wired from the start; only benign Vite/React
  DevTools info lines were ever recorded).
- `tsc -p tsconfig.app.json --noEmit`: zero errors in
  `AgentChatPanel.tsx` (8 pre-existing errors remain in unrelated files —
  `AgentNode.tsx`/`AgentsMapCanvas.tsx`/`SectionDrilldown.tsx`/
  `SectionHub.tsx`/`Cockpit.tsx` — confirmed pre-existing, not touched by
  this task).

**Harness note (not a product defect):** an early verification pass
mis-timed "wait until not sending" against the in-bubble typing-dot
placeholder, which can disappear as soon as the FIRST delta arrives —
well before the real `sending` state (gated on the stream's own
`complete` frame) actually flips false. This made "New chat" read as a
false negative (disabled, so the click silently no-op'd) purely inside
the test harness. Fixed by polling the Send button's own "Sending…"
label instead, which tracks the real state directly — re-run above is
the corrected, passing result.

**No backend/API-client file touched** — confirmed; only
`AgentChatPanel.tsx` was edited.

gate: clear 2026-08-31 — no MUST-FLAG trigger fired for this task itself
(no new dependency, no shared-interface/ADR change, no unanticipated
file, every locked AC verified live). The CSS-omission judgement call
above is a scope-internal note for human spot-check, already anticipated
and pre-cleared by the story's own decomposer pass (net-new-design-needed,
non-blocking), not a new escalation.
