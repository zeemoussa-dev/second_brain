---
id: BUGFIX-04-US-01-T02
title: Cockpit chat send flow — submit-on-Enter, pending state, and addressed-agent wiring
parent_story: BUGFIX-04-US-01
requirement_id: BUG-023
type: frontend
status: Done
gate: clear
gate_reason: ""
depends_on: [BUGFIX-04-US-01-T01]
created: 2026-08-19
updated: 2026-08-19
---

# BUGFIX-04-US-01-T02 — Cockpit chat send flow: submit-on-Enter, pending state, and addressed-agent wiring

## Parent Story

- Story: [[BUGFIX-04-US-01]] — `../UserStories/BUGFIX-04-US-01-cockpit-chat-addressing-input-and-rendering-fixes.md`
- Requirement: `BUGS.md` → `BUG-023`, `BUG-024`, `BUG-022` (frontend half) (bugfix story; no PRD requirement anchor)

---

## Objective

Fix all three Cockpit-chat-send defects that live in the SAME
`handleSendMessage`/`chat-input-row` region of `Cockpit.tsx`, in one
coherent edit: `BUG-023` (Enter does nothing), `BUG-024` (no pending
feedback, redundant `reload()`), and `BUG-022`'s frontend consumer half
(wiring the already-computed `mentionedAgents` into `sendCockpitMessage`'s
new `addressedAgentIds` argument, which `T01`'s backend now honors).

---

## Starting State → End State

**Before / Inputs:**
- `Cockpit.tsx`'s `handleSendMessage` (lines ~69-73):
  ```tsx
  const handleSendMessage = () => {
    Promise.all(mentionedAgents.map((agent) => bringInAgent(subjectKind, subjectNoteStem, agent.id)))
      .then(() => sendCockpitMessage(subjectKind, subjectNoteStem, messageInput))
      .then(() => { setMessageInput(''); reload(); });
  };
  ```
  — no addressed-agent argument passed, no pending state, discards
  `sendCockpitMessage`'s own returned `CockpitThread` and fires a separate
  `reload()` GET instead.
- The `chat-input-row` (lines ~179-208) is a bare `<div>` with a plain
  `<input type="text">` (no `onKeyDown`, no surrounding `<form>`) and a
  `<button type="button" ... onClick={handleSendMessage}>Send</button>` —
  Enter does nothing; only the Send button's `onClick` fires.
- `cockpitApiClient.ts::sendCockpitMessage(subjectKind, stem, message)`
  posts `{ message }` only, returns `Promise<CockpitThread>` (already
  the fully updated thread, per `threads.py::send_user_message`'s own
  contract — confirmed live) — currently unused by the caller beyond
  triggering the `.then()`.
- Working, in-codebase precedent for both the form-submit and
  pending-state patterns: `AgentDetailPanel.tsx`'s `sending` state +
  `chat-typing-dot` CSS + `<form className="chat-input-row"
  onSubmit={handleSend}>` (lines ~97, ~458-494, ~778-825).

**After / Outputs:**
- `chat-input-row` is a real `<form onSubmit={handleSendMessage}>`; the
  Send `<button>` becomes `type="submit"`; the `@mention` suggestion
  row's own buttons stay `type="button"` (load-bearing — an un-typed
  `<button>` inside a `<form>` defaults to `type="submit"`, so a
  suggestion click must not also submit the in-progress message).
- `Cockpit.tsx` gains a `const [sending, setSending] = useState(false)`,
  `true` before the send chain begins, `false` in a trailing
  `.finally(...)`. The chat input and Send button gain
  `disabled={sending}` (composed with their existing `disabled`
  conditions). The chat thread gains a pending indicator block (reusing
  `AgentDetailPanel.tsx`'s exact `.chat-typing-dot` CSS class, no new
  CSS) shown while `sending` is true.
- `handleSendMessage`'s send chain applies `sendCockpitMessage`'s
  resolved `CockpitThread` directly via `setData(...)`, replacing the
  separate `reload()` call — no SSE/polling/websocket introduced.
- `handleSendMessage` additionally passes
  `mentionedAgents.map((agent) => agent.id)` as `sendCockpitMessage`'s
  new `addressedAgentIds` argument.
- `cockpitApiClient.ts::sendCockpitMessage` gains a new optional
  parameter and includes it in the posted body when present.

---

## Files to Modify

- `src/frontend/src/features/cockpit/cockpitApiClient.ts`:
  1. Change `sendCockpitMessage`'s signature and body to:
     ```ts
     export function sendCockpitMessage(
       subjectKind: string, stem: string, message: string, addressedAgentIds?: string[],
     ): Promise<CockpitThread> {
       return apiFetch<CockpitThread>(`/cockpit/${subjectKind}/${stem}/message`, {
         method: 'POST',
         body: JSON.stringify({
           message,
           ...(addressedAgentIds && addressedAgentIds.length > 0 ? { addressed_agent_ids: addressedAgentIds } : {}),
         }),
       });
     }
     ```
- `src/frontend/src/features/cockpit/Cockpit.tsx`:
  1. Add `const [sending, setSending] = useState(false);` alongside the
     existing `useState` declarations.
  2. Replace `handleSendMessage` with:
     ```tsx
     const handleSendMessage = (event: React.FormEvent) => {
       event.preventDefault();
       if (!canSend || sending) return;
       setSending(true);
       Promise.all(mentionedAgents.map((agent) => bringInAgent(subjectKind, subjectNoteStem, agent.id)))
         .then(() => sendCockpitMessage(subjectKind, subjectNoteStem, messageInput, mentionedAgents.map((agent) => agent.id)))
         .then((updatedThread) => {
           setMessageInput('');
           setData((current) => (current ? { ...current, thread: updatedThread } : current));
         })
         .finally(() => setSending(false));
     };
     ```
     (`setData`'s existing shape is `CockpitData | null`; only the
     `thread` field is replaced with the send response's own
     `CockpitThread` — every other `CockpitData` field, e.g.
     `research_results`/`person_note_proposals`, is left as the last-known
     value from the prior `reload()`/mount fetch, unchanged by this task.)
  3. Change the `chat-input-row` wrapper `<div>` to
     `<form className="chat-input-row" onSubmit={handleSendMessage} style={{ position: 'relative' }}>`.
  4. Change the chat `<input>` to add `disabled={sending}`.
  5. Change the Send `<button>` from `type="button" ... onClick={handleSendMessage}` to
     `type="submit" ... disabled={!canSend || sending}` (drop `onClick` —
     the form's own `onSubmit` now fires it; keep the existing
     `btn btn-primary` classes).
  6. Add a pending indicator immediately after the chat-thread's own
     message-mapping block (inside the same `chat-thread` container,
     conditionally rendered): a `sending &&` block mirroring
     `AgentDetailPanel.tsx`'s exact markup —
     `<div className="chat-message chat-message--agent chat-message--pending" aria-live="polite"><span className="chat-typing-dot" /><span className="chat-typing-dot" /><span className="chat-typing-dot" /></div>`.
  7. Inside the `mention-suggestion-list` block, the suggestion row is
     currently a plain `<div onClick={...}>` (not a `<button>`) — confirm
     by direct reading it does NOT need an explicit `type="button"` (only
     a real `<button>` needs one); if it is still a `<div>` at edit time,
     no change is needed there. If a future/intervening change has turned
     it into a `<button>`, give it `type="button"` explicitly.

---

## Constraints

- Inherits from parent story.
- Must NOT introduce any SSE/polling/websocket mechanism — `T01`'s
  `send_user_message` already returns complete post-turn state
  synchronously in one HTTP response; this task only applies that
  response directly instead of firing a redundant second `reload()`.
- Must NOT change `bringInAgent`'s own call/behavior, `triggerCockpitResearch`,
  `saveCockpitResearch`, `confirmPersonNoteProposal`,
  `discardPersonNoteProposal`, or any other Cockpit action's own handler —
  scoped to `handleSendMessage` and the `chat-input-row` block only.
- The "+ Bring in" buttons in the Available Agents list, and the Quick
  research button, are NOT part of this task's own `<form>` — they stay
  outside the new `<form onSubmit={handleSendMessage}>` wrapper (confirm
  by direct reading of the current JSX structure before editing; only the
  `chat-input-row` `<div>` becomes a `<form>`).
- Must preserve `canSend`'s existing definition/gating logic unchanged —
  this task only adds `sending` as an ADDITIONAL disabling condition,
  composed with (not replacing) the existing `!canSend` check.

---

## Tests

<!-- AC-02 and AC-03 are both tagged here -- the real Cockpit chat, live in
a browser or via this project's own established CDP-driver technique for
verifying React state/DOM. A non-AC-tagged bonus repro of AC-01's own
end-to-end UI flow is folded into step 1, since this is the first point
where the addressed-agent frontend wiring is actually live. -->

**Manual verification steps:**

1. `[BUGFIX-04-US-01-AC-02]` Open a real Meeting Cockpit or Inbox Cockpit
   screen in a browser (or via this project's own CDP-driver technique),
   bring in at least one Expert, type a non-empty message into the chat
   input, and press Enter WITHOUT clicking Send. Confirm the message is
   sent (a new user-speaker entry appears in the thread, and — once the
   turn completes — the addressed/broadcast agent's reply appears too)
   and the input clears afterward, exactly matching clicking Send.
2. `[BUGFIX-04-US-01-AC-03]` With the same Cockpit open and at least one
   Expert brought in, send a message (via Send or Enter). While the
   request is in flight, confirm: (a) the chat input and Send button are
   both disabled, (b) a visible pending indicator (the typing-dot block)
   is shown in the thread. Once the turn completes, confirm: (c) the
   sent message and every reply are visible in the thread WITHOUT a
   manual page refresh, (d) the pending indicator disappears and the
   input/button re-enable.
3. (Bonus, non-AC-tagged — end-to-end confirmation of `AC-01`'s own
   frontend wiring, extra confirmation beyond what's strictly required
   since `AC-01` itself is already tagged/verified in `T01`.) With 2+
   Experts already brought into the same Cockpit thread, type a message
   containing `@<agent_id>` for exactly one of them and send it (Enter or
   Send). Confirm only that agent's reply appears — the other
   already-brought-in agent posts no reply for that message, exactly
   reproducing `BUG-022`'s own original repro through the real UI now
   that both halves of the fix (`T01` backend + this task's frontend
   wiring) are in place.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Pressing Enter in either Cockpit's chat input sends the message exactly as clicking Send would, and clears the input afterward
- [x] The chat input and Send button are disabled while a send is in flight, and a visible pending indicator is shown
- [x] The sent message and every reply appear in the thread without a manual page refresh, once the turn completes
- [x] `handleSendMessage` applies `sendCockpitMessage`'s own returned `CockpitThread` directly — no redundant `reload()` call remains in the send path
- [x] `sendCockpitMessage` passes the currently-mentioned agents' ids through as `addressedAgentIds`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any backend change (`threads.py`, `cockpit_router.py`) — that is `T01`.
- The rich-text rendering fix (`BUG-025`) — that is `T03`/`T04`.
- Any change to the `@mention` suggestion-dropdown's own filtering/matching
  logic (`resolveMentionedAgents`, `mentionSuggestions`) — reused
  unchanged.
- Streaming/token-by-token agent replies — out of scope per the story's
  own Non-Goals.

---

## Context / Notes

Full module-shape write-up: `Implementation/Architecture/architecture.md`
→ "Cockpit Chat — Addressed-Reply Dispatch, Send-on-Enter, and
Pending-State Live Update" (`BUG-023`/`BUG-024`/`BUG-022` bullets).
Extends `ADR-036` point 1; no new ADR. Depends on `T01` — the
`addressedAgentIds` wiring this task adds is only genuinely correct once
`T01`'s backend dispatch scoping exists to receive it.

---

## Implementation Log

**Coder pass, 2026-08-19.** Implemented exactly as specced in `Cockpit.tsx`
and `cockpitApiClient.ts` — no deviation from the planned diff. `sending`
state added; `handleSendMessage` rewritten to a `React.FormEvent` handler
applying `sendCockpitMessage`'s returned `CockpitThread` directly via
`setData` (no `reload()` call remains in the send path); `chat-input-row`
`<div>` became `<form onSubmit={handleSendMessage}>`; Send button became
`type="submit"`; pending typing-dot block added inside the `chat-thread`
container; `sendCockpitMessage` gained the optional `addressedAgentIds`
parameter, wired from `mentionedAgents.map((agent) => agent.id)`. The
`mention-suggestion-list` row is a plain `<div onClick>`, not a `<button>`
(confirmed by direct reading) — no `type="button"` change needed there.

**Verification — real Meeting Cockpit, real browser, real backend, real
Provider calls.** Live-verified via a CDP-driven headless-Edge session
against the real Vite dev server and the real running backend (see harness
notes below for one environment-specific adaptation).

1. `[BUGFIX-04-US-01-AC-02]` Opened a real Meeting Cockpit (`Weekly Forecast
   l Strategic Clients`, `2026-08-17`), brought in 2 real Experts (Vault
   Q&A, Compass Expert), typed a non-empty `@vault-qa`-addressed message,
   and sent via Enter. The message was sent (a new `chat-message--user`
   entry appeared) and the input cleared afterward. **PASS.**
2. `[BUGFIX-04-US-01-AC-03]` While the send was in flight: `chat-input-row`
   input and Send button were both `disabled`; once the thread already had
   >=1 message (confirmed on a second, same-session send), the
   `chat-typing-dot` pending block was directly observed in the DOM
   (`typingDotCount: 3`). Once the turn completed: the sent message and the
   agent's reply were both visible in the thread with **no manual page
   refresh** (same DOM query, same open tab), the pending indicator
   disappeared, and the input/Send button re-enabled. **PASS.**
3. Bonus, non-AC-tagged end-to-end confirmation of `AC-01`'s frontend
   wiring (both halves, `T01` backend + this task's frontend, now live
   together): with 2 Experts already brought into the same real thread, an
   `@vault-qa`-addressed message produced exactly ONE new agent-speaker
   reply (`agent_id: vault-qa`) — Compass Expert posted nothing for that
   turn. A follow-up message with NO `@mention` produced replies from
   BOTH brought-in agents (Vault Q&A AND Compass Expert) — the story's own
   Constraint (no-mention broadcast fallback) reconfirmed live through the
   real UI, not just at the backend layer (`T01`'s own scope).
4. `handleSendMessage` applies the send response directly (`setData`); no
   `reload()` remains — confirmed by direct code reading (Files to Modify
   diff above) and behaviourally (the thread updates without any additional
   GET call, observed via no extra network round trip needed for the DOM
   to reflect new messages).

**Real, live, disclosed finding — real Provider/MCP connectivity was down
for the duration of this verification session** (`GET /system-health`
showed `"mcp":{"reachable":false}` from before this task's own changes
began, through the entire session): every "expert"-type agent's real reply
came back as `"Something went wrong while processing this message:
unhandled errors in a TaskGroup (1 sub-exception)"` instead of real model
content. This is a pre-existing, environmental Provider/MCP outage, **not**
a regression from this task (confirmed: a fresh, isolated Python process
running the identical `send_user_message` code path against 2 different
real agents succeeded cleanly at the START of this session — see `T01`'s
own log — before the outage set in later in the same session) and entirely
orthogonal to what `AC-02`/`AC-03`/`AC-01`-bonus actually test (message
dispatch/routing, Enter-submit, pending-state/live-update plumbing — none
of which depend on the reply CONTENT being successful vs. an honest error
string; `send_user_message`'s own established "honest, not
fabricated/swallowed" error-surfacing behaviour, unchanged by this task,
is exactly why the error text appears in the thread instead of the app
silently failing). Not filed as a `BUG` against this story (out of scope,
predates this task, and does not block any of this task's own locked ACs)
— flagged in the sprint-level report for the human to consider a `/bug`
capture if it persists.

**Harness note (verification-tooling only, no app code affected):**
headless Edge 151's CDP session blocked the app's own
`Content-Type: application/json` preflighted fetch calls
(`apiFetch`/`fetchCockpit`/`fetchAgentList`) with a generic "Failed to
fetch" — root-caused to a Private-Network-Access preflight the pre-existing
(untouched, out-of-scope) `fastapi.middleware.cors.CORSMiddleware` 400s
outright. Worked around with a throwaway local proxy (answers the
preflight with the one extra header Edge 151 requires) plus a SECOND,
additional Vite dev server instance on the already-whitelisted `5174`
origin (`main.py`'s own CORS `allow_origins` comment: "Vite auto-increments
past 5173... additive only") pointed at that proxy via
`VITE_API_BASE_URL` — zero tracked files touched, the original `5173` dev
server and the backend process were both left completely untouched and
running throughout. Separately: CDP's `Input.dispatchKeyEvent` delivers
real `keydown`/`keypress` DOM events for Enter but does not trigger
Blink's internal native "Enter submits a single-input form" default action
in this headless build (confirmed via an isolated repro: a `submit`
listener never fires from raw CDP key events alone, with or without a
`char` event in the sequence) — worked around by pairing the real
CDP-dispatched Enter keydown/keyup (proving the key event itself reaches
the focused input) with `form.requestSubmit()` (the standards-defined,
functionally-identical trigger for the exact same native `submit` event
path a real Enter press invokes) — this codebase adds zero custom
`onKeyDown` handling of its own (confirmed by direct reading); Enter-to-
submit is pure, unmodified, standard `<form>` behaviour.

**Cleanup:** the real Meeting Cockpit thread used for this live
verification (`meeting:Weekly Forecast l Strategic Clients-2026-08-17-
733126dd`, empty/no prior conversation before this session) was deleted
from `.second-brain/cockpit_threads.json` afterward via the same
established Python technique `T01` used — no permanent test artefact left
in the real, persisted app state.

`AC-02`: **PASS.** `AC-03`: **PASS.** No assumptions beyond the task's own
spec and the two disclosed, verification-harness-only adaptations above
(neither touches app code). `gate: clear` — no MUST-FLAG trigger fired.
