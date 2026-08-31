---
id: REQ-SB-82-US-06-T07
title: Cockpit.tsx / cockpitApiClient.ts — reply-to-message write-side UI (strong hint, not override)
parent_story: REQ-SB-82-US-06
requirement_id: REQ-SB-82
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-82-US-06-T06]
created: 2026-08-31
updated: 2026-08-31
---

# REQ-SB-82-US-06-T07 — Cockpit.tsx / cockpitApiClient.ts: reply-to-message write-side UI (strong hint, not override)

## Parent Story

- Story: [[REQ-SB-82-US-06]] — `../UserStories/REQ-SB-82-US-06-live-routing-fix-and-reply-to-message.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Add the missing WRITE-side "pick a message to reply to" affordance to
`Cockpit.tsx`'s Chat tab composer, wired to send the selected message's real
`id` as `reply_to_message_id` (`T06`), reusing the existing "↳ replying
to: …" READ-side rendering unchanged.

---

## Starting State → End State

**Before / Inputs:**
- `cockpitApiClient.ts::sendMessage(subjectKind, stem, text)` takes plain
  text only. `Cockpit.tsx`'s `ChatMessage` component already renders a
  "↳ replying to: …" strip for any message with a `reply_to_message_id`
  that resolves to a parent in the current thread (shipped,
  `REQ-SB-82-US-04`) — reused unchanged here.
- No affordance exists anywhere for the USER to choose "reply to this
  message" before sending a new one.

**After / Outputs:**
- `sendMessage` gains an optional 4th parameter,
  `replyToMessageId?: string`, included in the `POST .../message` body
  when present.
- Each rendered `ChatMessage` (user or agent, not `system`) exposes a
  small "Reply" affordance (per this project's own existing icon-button
  convention, e.g. `material-symbols-outlined` `reply` icon, `aria-label`
  "Reply to this message") that sets local state
  `replyToMessageId: string | null` to that message's own `id` when
  clicked. A message with no real `id` (pre-`REQ-SB-82-US-04` legacy data)
  does not render the affordance — matches the existing "missing `id` is
  un-threadable" convention already documented in `chat_store.py`.
- When `replyToMessageId` is set, a small preview strip renders directly
  above the composer's `<textarea>` (e.g. `data-role="reply-to-preview"`),
  showing a truncated quote of the selected message's own text (reusing
  the existing `truncate` helper) plus a cancel/`×` control that clears
  `replyToMessageId` without sending anything.
- `handleSend` passes `replyToMessageId ?? undefined` to `sendMessage(...)`
  and clears `replyToMessageId` back to `null` once the send call
  resolves (success or failure — matches the existing `draft`-clearing
  pattern).
- **Stale-reference safety (Scenario 8):** if `replyToMessageId` is set but
  no longer resolves to a message actually present in `data.thread.
  messages` (e.g. a reload replaced `data` with fresher state that dropped
  it — a defensive, not expected-in-practice, case since the id came from
  the currently-rendered thread), the preview strip does not render a
  broken/blank quote — it silently falls back to treating the selection as
  cleared, and Send still works normally with `reply_to_message_id`
  omitted.

---

## Files to Modify

- `src/frontend/src/features/cockpit/cockpitApiClient.ts` —
  `sendMessage`'s new optional parameter.
- `src/frontend/src/features/cockpit/Cockpit.tsx` — the per-message Reply
  affordance, `replyToMessageId` state, the composer preview strip, and
  `handleSend`'s wiring.

---

## Constraints

- Inherits from parent story.
- **Reply-to is a hint, never a hard override of who answers** — this task
  only wires the UI/API plumbing; the actual routing decision is `T05`'s
  concern and is NOT re-implemented or second-guessed here.
- **DOM-structural ACs only, no locked assertion on exact visual styling**
  — per this project's own "structural ACs for screens" convention: lock
  only that the Reply affordance renders, that the preview strip renders
  with the selected message's own text, and that Send still works with a
  stale reference — never pixel-level/colour/hover assertions.
- **This screen's exact visual treatment is `net-new-design-needed`** (no
  `html-prototype/` coverage) — the shape implemented here (a per-message
  Reply action + a composer-preview-strip-with-cancel) is a decomposer-
  made, disclosed judgement call (see the parent story's own Notes,
  "Decomposer pass"), not a signed-off prototype design. Flagged for a
  non-blocking design spot-check once built — do not block the task on
  this.
- Reuse the existing `.chat-message-reply-to`/`ChatMessage` READ-side
  rendering unchanged — do not restructure it.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-82-US-06-AC-03]` Render the Cockpit Chat tab with 2+ real
   messages in the thread; click the Reply affordance on one message;
   confirm a `[data-role="reply-to-preview"]` element renders showing that
   message's own (truncated) text. Type a new message and Send; using a
   `window.fetch` spy (or an equivalent captured-request technique),
   confirm the outgoing `POST .../message` body includes
   `reply_to_message_id` equal to the selected message's real `id`.
2. Click the preview strip's cancel control; confirm
   `[data-role="reply-to-preview"]` no longer renders and a subsequent Send
   omits `reply_to_message_id` from the request body (no AC tag — supports
   the "hint, not override" Constraint's own UI-level cancel path).
3. `[REQ-SB-82-US-06-AC-08]` With `replyToMessageId` set to a value that
   does not correspond to any message currently in `data.thread.messages`
   (e.g. programmatically set local state to a random string, simulating a
   stale reference), confirm no broken/blank quoted preview renders (the
   preview element either doesn't render, or falls back to the cleared
   state) and that Send still succeeds normally with no thrown error/crash
   in the browser console.
4. Confirm a message with no `id` field (a pre-existing legacy message, if
   any real one exists in the test vault's own chat state; otherwise
   simulate via local state) does not render the Reply affordance (no AC
   tag — supports the "un-threadable" convention already established for
   this schema).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] A Reply affordance renders on each real (non-`system`), `id`-bearing
      message
- [x] Selecting a message to reply to renders a preview strip with a
      cancel control, and the outgoing send includes that message's real
      `id` as `reply_to_message_id`
- [x] Cancelling clears the selection; a subsequent send omits the field
- [x] A stale/unresolvable reply-to reference never renders a broken quote
      and never blocks Send
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any backend routing-decision behavior — `T05`.
- The single-agent Chat panel — `T08`, an architecturally separate,
  client-side-only mechanism.
- Final visual polish beyond the DOM-structural shape described above —
  non-blocking design spot-check, not a locked AC.

---

## Context / Notes

`ADR-012` point 4 and the story's own Notes ("Decomposer pass," reply-to UI
subsection) are the authoritative context for this task's own judgement
call. The existing "↳ replying to: …" rendering in `ChatMessage` already
covers the READ side for both auto-threaded AND user-chosen reply-to
messages identically — no change needed there.

---

## Implementation Log

**Coder pass (2026-08-31).** Read `ADR-012` points 4/5, the real current
`Cockpit.tsx`/`cockpitApiClient.ts` (confirmed matching the task's own
Starting State), and `T08`'s already-`Done` `AgentChatPanel.tsx` diff/log
for the established shape/class-name convention before starting. Changed
only the two files in `## Files to Modify`:

- `cockpitApiClient.ts` -- `sendMessage` gained a 4th optional parameter
  `replyToMessageId?: string`; the outgoing JSON body includes
  `reply_to_message_id` only when a value is supplied (mirrors `T06`'s own
  optional-field passthrough on the router side -- omitted entirely, never
  sent as `null`).
- `Cockpit.tsx`:
  - `ChatMessage` gained an `onReply: (messageId: string) => void` prop and
    a per-message Reply button (`chat-message-reply-btn`,
    `aria-label="Reply to this message"`, `material-symbols-outlined`
    `reply` icon -- same class names/convention as `T08`'s own affordance),
    rendered only when `message.id` exists (a pre-`REQ-SB-82-US-04` legacy
    message has no `id` and is structurally excluded by this guard). The
    `system`-speaker early return already excludes system notices, so no
    extra check was needed there.
  - New `replyToMessageId: string | null` state on `Cockpit`, wired to
    every rendered `ChatMessage` via `onReply={setReplyToMessageId}`.
  - A preview strip (`chat-reply-to-preview`, `data-role="reply-to-preview"`)
    renders directly above the composer `<form>` only when
    `replyToMessageId` resolves against the CURRENT
    `data.thread.messages` (Scenario 8's own stale-reference guard) --
    truncated quote (`_REPLY_PREVIEW_MAX_CHARS = 140`, same ceiling `T08`
    uses) plus a cancel button (`aria-label="Cancel reply"`) that clears
    the selection.
  - `handleSend` resolves `replyToId` against the CURRENT `data.thread.
    messages` before appending the new optimistic message, passes it to
    `sendMessage(...)`, and clears `replyToMessageId` synchronously at the
    top of `handleSend` (same "clear on send, regardless of outcome" spot
    as `draft` above it) -- matching `T08`'s own already-`Done`
    reconciliation of the task's "matches the existing draft-clearing
    pattern" wording against its "once the send call resolves" wording
    (both tasks resolved this the same way independently: immediate,
    synchronous clear).

No deviations from the plan; no new dependency, shared-interface change
beyond the already-planned optional `reply_to_message_id` field (`T06`,
already `Done`), or unanticipated file. `tsc -p tsconfig.app.json --noEmit`
shows the same pre-existing error set as the unmodified baseline (verified
via `git stash`/`git stash pop` around a baseline compile) -- 7
`agents-map`/pre-existing `CSSProperties` errors plus one pre-existing
`Cockpit.tsx` `PersonChip`/`onOpen` error at (shifted) line 474, all
outside this task's own edits.

**Verification (manual mode, real dev server + real headless-Edge CDP
session, this project's own established technique):**

- Confirmed Vite (`localhost:5173`) was serving the real, edited
  `Cockpit.tsx` module (transform fetch contained `reply-to-preview`/
  `chat-message-reply-btn`/`Cancel reply`, no parse error) and the real
  backend (`localhost:8001`) was up before any interaction testing.
- **Real subject used:** `meeting:2026-07-20-Shady-Moussa Sync` (a real,
  already-indexed vault note, empty thread at the start). Backed up the
  real `.second-brain/cockpit_chat.json` byte-for-byte (confirmed via
  `wc -c` size match) before seeding any test state, per this project's
  own "back up real production state, run a deliberate test, then
  restore it" established pattern (`SPRINT-030`/`035`). Seeded 2 brought-in
  Experts and several real messages via the app's own already-`Done`
  `/roster` and `/message` endpoints (never a fabricated write) to get
  real, `id`-bearing messages to interact with.
- Drove a real headless Edge (`--headless=new --remote-debugging-port`)
  against `http://localhost:5173/meeting-cockpit/...` via a minimal
  Node+native-`fetch`+native-`WebSocket` CDP client (no new dependency),
  React-controlled-`<textarea>`-input via the native value setter +
  `input` event, and a real `window.fetch` spy for outgoing-request
  capture -- all this project's own established techniques.
- `[REQ-SB-82-US-06-AC-03]` **PASS.** Rendered thread showed 4 real
  bubbles (2 user, 1 system, 1 agent reply with its own auto-threaded
  "↳ replying to: ..." strip, confirming the READ-side rendering is reused
  unchanged); 3 Reply buttons rendered (on every non-`system` bubble, all
  of which carry real `id`s) -- the `system` bubble correctly has none.
  Clicked Reply on "T07 verification seed message ONE" ->
  `[data-role="reply-to-preview"]` rendered exactly
  `"↳ Replying to: T07 verification seed message ONE×"`. Typed a new
  message and clicked Send; the real `window.fetch` spy captured the
  outgoing body as
  `{"text":"Follow-up after reply-to selection","reply_to_message_id":
  "67b288419cd8464a8fd0f7d9f1df0df5"}` -- the exact real `id` of the
  selected message. Preview cleared immediately after send. Zero console
  exceptions throughout.
- `[REQ-SB-82-US-06-AC-08]` **PASS.** Selected Reply on a real message
  (preview confirmed rendered). A first attempt to induce staleness via
  the real async dispatched-reply/poll path proved unreliable (routing to
  an agent, hence a live poll start, was not deterministic across sends
  with blank Compass credentials -- disclosed, not a defect in this
  task's own code) so verification used this project's own established
  React-Fiber direct-dispatch-invoke technique instead: located the real,
  live `Cockpit` component's own Fiber, walked its real hook chain to the
  `data` `useState` slot, and invoked its own real `dispatch` with a
  thread whose messages list had the selected message removed --
  genuinely exercising the real component's own real `setData` call, the
  same shape a real `fetchCockpit()` response landing via the poll/upload
  refresh paths would produce, not a fabricated DOM patch. Result: the
  preview strip disappeared (`null`) with no broken/blank quote. A
  subsequent Send completed with the outgoing body
  `{"text":"Send after stale reply-to reference (take 2)"}` --
  `reply_to_message_id` entirely absent (never a stale/broken value), and
  no crash/console exception.
- Cancel control (unlocked, Tests block step 2): selected a reply target
  (preview rendered), clicked its cancel button (preview disappeared),
  sent a plain message -- captured outgoing body was
  `{"text":"Plain send after cancel"}`, no `reply_to_message_id` key.
- No-`id` legacy message (unlocked, Tests block step 4): verified by
  direct code inspection rather than live induction (every message
  currently reachable in this real vault's thread carries a real `id`,
  since `chat_store.append_message` has unconditionally assigned one since
  `REQ-SB-82-US-04`) -- the `{message.id && (...)}` guard in `ChatMessage`
  structurally prevents the button from rendering whenever `id` is falsy,
  the same technique already relied on for the `system`-speaker exclusion
  a few lines above it.
- **Real-data cleanup, independently confirmed:** restored
  `.second-brain/cockpit_chat.json` from the pre-test backup (byte-for-byte
  `diff` confirmed identical afterward), then independently re-fetched
  `GET /cockpit/meeting/2026-07-20-Shady-Moussa Sync` live and confirmed
  the thread is back to its original empty state (`brought_in_agent_ids:
  []`, `messages: []`) -- the real meeting note's own chat history carries
  no trace of this task's test messages. Killed the headless Edge instance
  by its own specific PID tree (`taskkill /PID <pid> /T /F`), not `/IM`.

gate: clear 2026-08-31 -- no MUST-FLAG trigger fired for this task itself
(no new dependency, no shared-interface/ADR change beyond what `T05`/`T06`
already built, no unanticipated file, every locked AC verified live with a
real positive result). The one scope-internal judgement call worth noting
for spot-check: reconciling `handleSend`'s "clears... once the send call
resolves" vs. "matches the existing draft-clearing pattern" wording by
clearing `replyToMessageId` immediately/synchronously (same spot as
`draft`) -- independently arrived at the same resolution `T08`'s own coder
pass already used for the identical wording in its own task file, so this
is now a 2x-consistent reading, not a guess.
