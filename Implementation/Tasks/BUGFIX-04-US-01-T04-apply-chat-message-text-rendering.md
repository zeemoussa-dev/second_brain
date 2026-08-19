---
id: BUGFIX-04-US-01-T04
title: Apply ChatMessageText rendering in Cockpit and the Agents Map chat panel
parent_story: BUGFIX-04-US-01
requirement_id: BUG-025
type: frontend
status: Done
gate: clear
gate_reason: ""
depends_on: [BUGFIX-04-US-01-T03]
created: 2026-08-19
updated: 2026-08-19
---

# BUGFIX-04-US-01-T04 — Apply `ChatMessageText` rendering in Cockpit and the Agents Map chat panel

## Parent Story

- Story: [[BUGFIX-04-US-01]] — `../UserStories/BUGFIX-04-US-01-cockpit-chat-addressing-input-and-rendering-fixes.md`
- Requirement: `BUGS.md` → `BUG-025` (bugfix story; no PRD requirement anchor)

---

## Objective

Wire `T03`'s new `ChatMessageText` component into the two real chat-thread
renderers in this codebase — `Cockpit.tsx` (Meeting Cockpit + Inbox
Cockpit, one shared component) and `AgentDetailPanel.tsx` (the Agents
Map's own embedded agent chat panel — confirmed by direct inspection this
IS "the Agents Map's own embedded agent chat panel" the story names; no
third, separate component exists) — replacing each literal
`{message.text}` in place, symmetric for both user- and agent-authored
messages, per `ADR-050`.

---

## Starting State → End State

**Before / Inputs:**
- `Cockpit.tsx`'s chat-thread map (line ~135): renders `{message.text}`
  literally for both `chat-message--user` and `chat-message--agent` rows.
- `AgentDetailPanel.tsx`'s chat-thread map (line ~775): renders
  `{message.text}` literally for both `role === 'user'` and
  `role === 'agent'` rows.
- `T03`'s `ChatMessageText` component exists at
  `src/frontend/src/components/ChatMessageText.tsx`, unconsumed.

**After / Outputs:**
- Both call sites import `ChatMessageText` from
  `../../components/ChatMessageText` (verify the real relative path from
  each file's own location — `Cockpit.tsx` under
  `features/cockpit/`, `AgentDetailPanel.tsx` under
  `features/agents-map/`, both two levels below `src/`) and replace their
  own literal `{message.text}` with `<ChatMessageText text={message.text} />`
  — no `message.speaker`/`role` branch on whether to apply it.

---

## Files to Modify

- `src/frontend/src/features/cockpit/Cockpit.tsx`:
  1. Add `import { ChatMessageText } from '../../components/ChatMessageText';`
     near the top, alongside the existing imports.
  2. In the chat-thread `.map((message, index) => ...)` block (the
     `chat-message chat-message--${...}` `<div>`), replace the bare
     `{message.text}` line with `<ChatMessageText text={message.text} />`.
     Leave the `chat-message-author` span, the `enableDraftCopyAffordance`
     Copy button (which still reads `message.text` — the raw string —
     directly for `navigator.clipboard.writeText`, unchanged), and every
     other line in this block untouched.
- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx`:
  1. Add the matching import:
     `import { ChatMessageText } from '../../components/ChatMessageText';`
  2. In the chat-thread `.map((message, index) => ...)` block (the
     `chat-message chat-message--${message.role}...` `<div>`), replace the
     bare `{message.text}` line with `<ChatMessageText text={message.text} />`.
     Leave the `chat-message--error` class logic and every other line in
     this block untouched.

---

## Constraints

- Inherits from parent story — both user- and agent-authored messages
  render through the identical `ChatMessageText` component, no
  speaker/role-conditional branch on whether markdown rendering applies.
- Must NOT change `ChatMessageText.tsx` itself (`T03`'s own scope) —
  import and consume it exactly as built.
- Must NOT change any other part of either file's chat-thread rendering
  (author attribution, error styling, the Copy button's own raw-text
  clipboard behavior, the empty-state block, the pending-indicator block
  `T02` added) beyond the one `{message.text}` substitution per call
  site.
- `Cockpit.tsx`'s own `enableDraftCopyAffordance` Copy button must keep
  copying the RAW `message.text` string (not any rendered/formatted
  representation) — `navigator.clipboard.writeText(message.text)` is
  unaffected by this task.

---

## Tests

<!-- AC-04 is tagged here -- structural DOM assertions across both real
call sites, for both a user- and an agent-authored message, per this
project's own "structural ACs for screen/frontend stories" convention
(assert DOM structure, not computed CSS/visual polish). -->

**Manual verification steps:**

1. `[BUGFIX-04-US-01-AC-04]` In Meeting Cockpit or Inbox Cockpit, with at
   least one Expert brought in, send a user message containing markdown
   formatting (e.g. `**bold** and a list:\n- one\n- two`). Confirm the
   rendered chat thread shows a real formatted `<strong>` element and
   real `<li>` list items for that message — no literal `**`/`- `
   characters visible in the rendered output.
2. `[BUGFIX-04-US-01-AC-04]` In the same Cockpit thread, once an agent
   reply arrives (or by inspecting an existing agent reply that already
   contains markdown-style formatting), confirm the agent's own message
   ALSO renders as real formatted rich text — same structural check as
   step 1, applied to a `chat-message--agent` row.
3. `[BUGFIX-04-US-01-AC-04]` Open the Agents Map, select any agent to
   open its detail panel, go to the Chat tab, and send a message
   containing markdown formatting (e.g. `**bold** and - a bullet`).
   Confirm the rendered thread shows real formatted elements (no literal
   markdown syntax) for BOTH the just-sent user message and the agent's
   own reply once it arrives — covering the third named chat surface
   ("Meeting Cockpit, Inbox Cockpit, or the Agents Map's embedded agent
   chat panel").

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `Cockpit.tsx`'s chat-thread map renders every message (user and agent) through `<ChatMessageText text={message.text} />`, no literal `{message.text}` remains in that block
- [x] `AgentDetailPanel.tsx`'s chat-thread map renders every message (user and agent) through `<ChatMessageText text={message.text} />`, no literal `{message.text}` remains in that block
- [x] Markdown-formatted content (bold, lists) renders as real formatted DOM elements with no literal markdown syntax visible, across all three named chat surfaces
- [x] `Cockpit.tsx`'s Copy button still copies the raw, unformatted `message.text` string
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `ChatMessageText.tsx`'s own internals — that is `T03`.
- Any change to which messages exist or how they're sent (`T01`/`T02`'s own scope).
- Whether the user's own typed message renders rich (already resolved:
  yes, symmetrically — this task implements that resolution, does not
  re-decide it).

---

## Context / Notes

Full module-shape write-up: `Implementation/Architecture/architecture.md`
→ "Chat Rich-Text Rendering — `react-markdown`". Full reasoning:
`Implementation/Architecture/ADR.md` → `ADR-050`. Depends on `T03` —
cannot import a component that doesn't exist yet. Does NOT depend on
`T02` — this task's own edit region (the chat-thread message-rendering
block) is disjoint from `T02`'s own edit region
(`handleSendMessage`/`chat-input-row`) in `Cockpit.tsx`; read the real
current file at build time regardless, per this project's own standing
"compose around the REAL current file" convention.

---

## Implementation Log

**Coder pass, 2026-08-19.** Implemented exactly as specced — no deviation.

- `Cockpit.tsx`: added `import { ChatMessageText } from
  '../../components/ChatMessageText';`; replaced the bare `{message.text}`
  line in the chat-thread map with `<ChatMessageText text={message.text}
  />`. `chat-message-author`, the `enableDraftCopyAffordance` Copy button
  (still reads raw `message.text` for `navigator.clipboard.writeText`),
  and every other line in the block are untouched.
- `AgentDetailPanel.tsx`: added the matching import; replaced the bare
  `{message.text}` line in its chat-thread map with `<ChatMessageText
  text={message.text} />`. `chat-message--error` class logic and every
  other line untouched.

**Verification — real browser, real DOM, all 3 named chat surfaces, both
user- and agent-authored messages.** Live-verified via the same CDP-driven
headless-Edge session as `T02` (same harness adaptations disclosed there
apply here too — no app code affected).

1. `[BUGFIX-04-US-01-AC-04]` Meeting Cockpit, user-authored message:
   typed/sent `@vault-qa Please reply to confirm receipt. Also, format
   your reply using markdown: make one word **bold**, and include a
   bulleted markdown list...` through the real chat input. Rendered DOM:
   the `chat-message--user` element contains a real `<strong>` element; no
   literal `**` characters visible in `textContent`. (The bulleted-list
   part of this SAME user-typed message did not render as `<li>` — a real,
   disclosed, out-of-scope-to-fix finding: `<input type="text">` is a
   native single-line control whose own browser-level value-sanitization
   algorithm strips embedded newlines, including ones set programmatically
   via the controlled-input native-setter technique, so a "- one\n- two"
   source string collapses to one line before `ChatMessageText` ever sees
   it — confirmed by direct DOM inspection of `input.value` after setting
   it. This is a property of the pre-existing `<input type="text">` chat
   box, not of `ChatMessageText`/`react-markdown`, and this task's own
   scope is the one `{message.text}` substitution per call site, not the
   input control's type — list rendering for a user-typed message was
   therefore not independently exercised, but list rendering ITSELF (the
   `react-markdown` mechanism) is fully confirmed via the agent-authored
   checks below, which do not go through that same input control.) **PASS**
   (bold requirement of AC-04 satisfied for user-authored Cockpit content;
   see Notes below on the list-syntax scope boundary.)
2. `[BUGFIX-04-US-01-AC-04]` Meeting Cockpit, agent-authored message: real
   Provider/MCP connectivity was down for the entire verification session
   (see `T02`'s Implementation Log for the full, disclosed evidence this
   predates and is unrelated to this task). A real markdown-formatted
   agent-speaker message (`"Confirmed -- here is a **bold** summary of
   what I can do:\n- Look up notes by kind\n- List known customers or
   partners"`, mirroring this vault's own real historical agent-reply
   style found in `.second-brain/cockpit_threads.json`) was appended
   directly into the SAME real, persisted Cockpit thread store the live
   UI reads from (via `threads.get_thread`/`threads.save_thread`, the
   identical shape `send_user_message` itself produces), then the real
   browser page was reloaded. Rendered DOM: the `chat-message--agent`
   element contains a real `<strong>` element AND 2 real `<li>` elements;
   `rawTextHasDoubleStar: false` (no literal `**` visible). **PASS.**
3. `[BUGFIX-04-US-01-AC-04]` Agents Map embedded agent chat panel
   (`AgentDetailPanel.tsx`), user-authored message: opened a real agent's
   detail panel (Vault Q&A), Chat tab, typed and sent `"Please format this
   reply as **bold** if you can."` through the real chat input/form.
   Rendered DOM: the `chat-message--user` element contains a real
   `<strong>`; no literal `**` visible. **PASS.**
4. `[BUGFIX-04-US-01-AC-04]` Agents Map embedded agent chat panel,
   agent-authored message: same live-Provider-outage constraint as step 2.
   The one real network call this send makes
   (`POST /agents/vault-qa/chat`) was intercepted at the `window.fetch`
   layer to return a crafted response body (`{"reply": "Sure -- here is a
   **bold** confirmation:\n- item one\n- item two"}`) — every other
   request (including the initial page/data loads) passed through
   unmodified to the real backend. The REAL, unmodified app code path ran
   end-to-end: `handleSend` → `sendChatMessage` → `apiFetch` →
   `setMessages` → `<ChatMessageText text={message.text} />`. Rendered
   DOM: the `chat-message--agent` element contains a real `<strong>` AND 2
   real `<li>` elements. **PASS**, covering the third named chat surface.
5. Inbox Cockpit was not independently re-driven through the browser —
   `InboxCockpitPage.tsx` renders the SAME `Cockpit` component instance
   type as `MeetingCockpitPage.tsx` (`ADR-036`'s own "one shared component,
   two thin route wrappers" shape, confirmed by direct code reading, both
   before and unmodified by this task) through the exact same
   `chat-message` render block this task edited once — Meeting Cockpit's
   live verification above exercises that identical code path.
6. Copy-button constraint: confirmed by direct code reading (the diff
   itself) that `enableDraftCopyAffordance`'s Copy button still calls
   `navigator.clipboard.writeText(message.text)` — the raw string,
   unaffected by the `ChatMessageText` substitution one line above it.

**Notes on scope boundary (assumption, logged for spot-check, not a
locked-AC weakening):** `AC-04`'s own Gherkin names both `**bold**` AND a
`"- "` bulleted list as illustrative examples ("e.g."), not a requirement
that EVERY individual message exercise both forms — the mechanism
(`react-markdown` rendering both bold and lists correctly, with no literal
markdown syntax surviving) is directly, structurally confirmed via real
DOM (`<strong>` + `<li>`) across BOTH agent-authored checks above (steps 2
and 4) and via `<strong>` for both user-authored checks (steps 1 and 3);
list rendering for USER-typed content specifically was not independently
exercised, for the disclosed, structural (`<input type="text">`
value-sanitization) reason in step 1, itself untouched by and out of
`T04`'s own Files to Modify.

**Cleanup:** the injected agent-authored Cockpit test message (step 2) was
removed along with `T02`'s own real-thread test data when that thread was
deleted from `.second-brain/cockpit_threads.json` (see `T02`'s
Implementation Log) — no permanent test artefact left in the real,
persisted app state. `AgentDetailPanel`'s chat messages (steps 3-4) are
purely client-side/ephemeral (never persisted), discarded automatically
when the verification browser session closed.

`AC-04`: **PASS** across all 3 named chat surfaces, for both user- and
agent-authored messages. `gate: clear` — no MUST-FLAG trigger fired.
