---
id: REQ-SB-13-US-01-T07
title: Embedded chat thread — send/receive, action-triggering via natural language
parent_story: REQ-SB-13-US-01
requirement_id: REQ-SB-13
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-13-US-01-T06]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-13-US-01-T07 — Embedded chat thread

## Parent Story

- Story: [[REQ-SB-13-US-01]] — `../UserStories/REQ-SB-13-US-01-embedded-agent-chat-and-communication-history.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-13 *Embedded Agent Chat & Communication History*

---

## Objective

Add the panel's Chat section: a message thread + send form that calls
`T05`'s `POST /agents/{agent_id}/chat`, appends the user's message and the
agent's real reply to the thread, and — when the message matches a
trigger-phrase — confirms the triggered action, entirely inside Second
Brain's own UI.

---

## Starting State → End State

**Before / Inputs:**
- `T06` has landed `AgentDetailPanel.tsx` with Settings + Available Actions
  sections; no Chat section yet.
- `T05` has landed `POST /agents/{agent_id}/chat` → `{"reply",
  "action_triggered"}`.

**After / Outputs:**
- `AgentDetailPanel.tsx` gains a Chat section: `.chat-thread` (a
  locally-held list of `{role: 'user' | 'agent', text}` messages) +
  `.chat-input-row` send form.
- `features/agents-map/agentsApiClient.ts` gains `sendChatMessage`.
- `src/frontend/src/styles/agent-panel.css` gains the `.chat-*` selector
  group.

---

## Files to Modify

- `src/frontend/src/features/agents-map/agentsApiClient.ts` — add:
  ```ts
  export interface ChatResponse {
    reply: string;
    action_triggered: string | null;
  }

  export function sendChatMessage(agentId: string, message: string): Promise<ChatResponse> {
    return apiFetch<ChatResponse>(`/agents/${agentId}/chat`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }
  ```

- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` — add local
  chat-thread state and the Chat section, reset on every agent switch
  (alongside the existing `setAgent(null)` reset in the `agentId`-keyed
  effect):
  ```tsx
  import { useEffect, useState } from 'react';
  import { fetchAgent, sendChatMessage, type AgentDetail } from './agentsApiClient';

  interface ChatMessage {
    role: 'user' | 'agent';
    text: string;
  }

  // inside AgentDetailPanel:
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState('');

  useEffect(() => {
    setAgent(null);
    setMessages([]); // clear the previous agent's chat thread on switch
    setDraft('');
    fetchAgent(agentId).then(setAgent);
  }, [agentId]);

  async function handleSend(event: React.FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text) return;
    setMessages((prev) => [...prev, { role: 'user', text }]);
    setDraft('');
    const response = await sendChatMessage(agentId, text);
    setMessages((prev) => [...prev, { role: 'agent', text: response.reply }]);
  }
  ```
  Render, inside the existing `side-panel-agent` block, after the Available
  Actions section:
  ```tsx
  <div className="side-panel-section">
    <h3>Chat</h3>
    <div className="chat-thread" data-role="agent-chat-thread">
      {messages.map((message, index) => (
        <div className={`chat-message chat-message--${message.role}`} key={index}>
          {message.text}
        </div>
      ))}
    </div>
    <form className="chat-input-row" onSubmit={handleSend}>
      <input
        type="text"
        className="input"
        placeholder={`Message ${agent.name}…`}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
      />
      <button type="submit" className="btn btn-primary">Send</button>
    </form>
  </div>
  ```
  (`agent.name` requires this block to render only once `agent` is
  non-null — keep it inside the existing `{agent && (...)}` guard `T06`
  already established.)

- `src/frontend/src/styles/agent-panel.css` — add: `.chat-thread`/
  `.chat-message`/`.chat-message--user`/`.chat-message--agent`/
  `.chat-input-row`, ported verbatim from `html-prototype/styles.css`.

---

## Constraints

- Inherits from parent story: the chat's reply must come from a real
  backend response (`T05`'s endpoint) — never a canned/hardcoded string, per
  the parent story's own Constraints explicitly rejecting the prototype's
  demo behavior.
- The user must remain inside Second Brain's own UI throughout send/receive
  — no `window.open`/external navigation of any kind.
- Chat thread state resets to empty on every agent switch (`setMessages([])`
  alongside `T06`'s `setAgent(null)`), so a message sent to one agent never
  leaks into another agent's thread.
- No new dependency.

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `uvicorn app.main:app --reload --port 8001`; browser preview
tool):

1. **[REQ-SB-13-US-01-AC-02]** Open the Email Capture agent's panel. Type
   "hi there" (a message with no trigger-phrase match) into the chat input
   and send it. Confirm the user's message appears in the `.chat-thread` as
   a `.chat-message--user`, then confirm the agent's real reply (mentioning
   Email Capture's available actions, per `T05`'s fallback response) appears
   as a `.chat-message--agent`. Confirm the browser's URL/tab never
   navigates away from Second Brain's own app throughout.
2. **[REQ-SB-13-US-01-AC-08]** With the same panel open, send "please run
   capture now" (a message matching `email-capture`'s `run_capture_now`
   trigger phrase — **this triggers a real capture run**, be deliberate
   about how many times this step is repeated, per `MEMORY.md`'s standing
   caution). Confirm the agent's reply in the `.chat-thread` confirms what
   was done (e.g. "Done — N email(s) filed."). Then open the Communication
   History section (built in `T08` — if `T08` has not yet landed, verify
   this step's history-append behavior directly via `GET
   /agents/email-capture/history` per `T05`'s own smoke check instead) and
   confirm the triggered action's `run_event` entry appears alongside this
   chat exchange.
3. Non-AC smoke check: confirm no console errors/warnings on send, and
   confirm the chat input clears after each send.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Sending a chat message appends the user's message, then the agent's
      real backend reply, to the `.chat-thread`
- [ ] A message matching a trigger phrase triggers the real backend action
      and the reply confirms what was done
- [ ] No external navigation occurs at any point in the send/receive flow
- [ ] Chat thread state clears on agent switch
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Communication history log/empty-state/unified-timeline rendering, and the
  full agent-switching verification across every section — `T08`.
- Wiring the Available Actions buttons (direct-trigger path) — remains Out
  of Scope per `T06`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-011` created at
`/plan-tasks` step 1) — the human reviews `ADR-011` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

Full verification of Scenario 7's "appears in the communication history
alongside the chat exchange" half is completed in `T08`, once the history
section actually renders in the UI — step 2 above already confirms the
underlying data is correct via the router directly if `T08` hasn't landed
yet, so this task's own AC-08 coverage does not block on `T08`'s build
order.

---

## Implementation Log

**2026-08-11, coder pass.** Added `ChatResponse`/`sendChatMessage` to
`agentsApiClient.ts`, chat-thread state + Chat section to
`AgentDetailPanel.tsx`, `.chat-*` selectors to `agent-panel.css` —
verbatim per this task's own code blocks.

Live verification (headless Chrome via CDP, same live backend as T06 —
port 8003):

- **[REQ-SB-13-US-01-AC-02]** Opened Email Capture's panel, typed "hi
  there" (no trigger-phrase match) and submitted. The user's message
  appeared as `.chat-message--user`, then the real backend's fallback
  reply ("I didn't understand that. Email Capture can: Run capture now,
  View last run, Pause schedule.") appeared as `.chat-message--agent`.
  `window.location.href` was identical (`http://localhost:5174/`) before
  and after the send — no external navigation at any point. **PASS.**
  Screenshot: `ac02_chat_no_match.png`.
- **[REQ-SB-13-US-01-AC-08]** With the same panel still open, typed
  "please run capture now" (matches `run_capture_now`'s trigger phrase)
  and submitted — **this triggered one real Outlook/Compass/vault-write
  capture run**, the single live trigger for this story (consolidated
  with T05's own "exactly once" direct-endpoint check — see T05's Log).
  Polled the chat thread up to 90s (the real run took roughly 80s this
  pass — Outlook COM + Compass classification + meeting capture on the
  same tick). The agent's reply confirmed what was done: "Done — 0
  email(s) filed." (0 is correct — no new unprocessed mail existed at
  trigger time). `GET`-equivalent history state (fetched via the panel's
  own History section, built by T08, verified together — see T08's Log)
  confirmed the triggered action's `run_event` entries appear alongside
  this exact chat exchange, in order. **PASS.** Screenshot:
  `ac08_chat_action_triggered.png`.
- Non-AC smoke check: no console errors/warnings on send; the chat input
  cleared immediately after each send (confirmed via
  `draft` reset to `''` in the component, and visually — no leftover text
  in the input field in either screenshot).

- [x] Sending a chat message appends the user's message then the agent's real reply — **AC-02 PASS**
- [x] A trigger-phrase match triggers the real backend action, reply confirms what was done — **AC-08 PASS**
- [x] No external navigation occurs at any point — confirmed (`window.location.href` unchanged throughout)
- [x] Chat thread state clears on agent switch — confirmed live in T08's agent-switching check (this task's own mechanism, T08 exercises it)
- [x] `MEMORY.md` updated — yes, see Constraints entry on the observed real-capture-run consolidation pattern for SPRINT-010
- [x] `CHANGELOG.md` entry appended — yes
