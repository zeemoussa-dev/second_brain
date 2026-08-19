---
id: REQ-SB-28-US-01-T05
title: AgentDetailPanel.tsx Chat tab attach control + honest-rejection display; agentsApiClient.ts multipart upload call
parent_story: REQ-SB-28-US-01
requirement_id: REQ-SB-28
type: frontend
status: Done
gate: flagged
gate_reason: "scope-internal judgement calls logged in Implementation Log for human spot-check (trigger 8, self-regulating — not an escalation)"
phase: P1
depends_on: [REQ-SB-28-US-01-T04]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-28-US-01-T05 — Frontend attach affordance + honest-rejection UI

## Parent Story

- Story: [[REQ-SB-28-US-01]] — `../UserStories/REQ-SB-28-US-01-file-upload-attach-and-handoff.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-28 *File Upload for Agents*

---

## Objective

Add a minimal, structurally-locked attach affordance to
`AgentDetailPanel.tsx`'s Chat tab (a file input alongside the existing
message input), and a `sendChatMessageWithAttachment` call in
`agentsApiClient.ts` that hits `T04`'s new `POST
/agents/{agent_id}/chat/attachment`. Client-side extension pre-check gives
immediate honest feedback for an unsupported type; the server's own
response (`T04`) is the source of truth for every other rejection/failure
case, always rendered faithfully in the chat thread, never re-worded or
suppressed.

**No `/design` pass covers this surface** (skipped for this batch,
operator direction) — only the DOM-structural signature below is locked;
visual polish (spacing, icon choice, exact styling) is not a locked AC
and is a non-blocking out-of-band spot-check once a real design pass
covers this screen.

---

## Starting State → End State

**Before / Inputs:**
- `AgentDetailPanel.tsx`'s Chat tab has a `.chat-input-row` form: a text
  `<input>`, a submit `<button>`; `handleSend` calls
  `agentsApiClient.sendChatMessage(agentId, text)` only.
- `agentsApiClient.ts` has `sendChatMessage`, no attachment-aware call.
- `T04` has landed `POST /agents/{agent_id}/chat/attachment` (multipart:
  `message` + `file`), returning `{"reply": string, "attachment_status":
  "filed" | "summarized_unfiled" | "rejected" | "extraction_failed" |
  "summarization_failed", "vault_path": string | null}`.

**After / Outputs:**
- `agentsApiClient.ts` additionally exposes:
  ```typescript
  export interface ChatAttachmentResponse {
    reply: string;
    attachment_status:
      | 'filed'
      | 'summarized_unfiled'
      | 'rejected'
      | 'extraction_failed'
      | 'summarization_failed';
    vault_path: string | null;
  }

  // apiFetch (client.ts) hardcodes 'Content-Type: application/json'
  // unconditionally, which would break multipart boundary handling --
  // this call intentionally uses a raw fetch instead, duplicating
  // client.ts's own BASE_URL fallback (client.ts is out of this task's
  // Files to Modify; BASE_URL is not exported from it).
  const ATTACHMENT_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

  export async function sendChatMessageWithAttachment(
    agentId: string,
    message: string,
    file: File,
  ): Promise<ChatAttachmentResponse> {
    const formData = new FormData();
    formData.append('message', message);
    formData.append('file', file);
    const response = await fetch(`${ATTACHMENT_BASE_URL}/agents/${agentId}/chat/attachment`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      throw new ApiError(response.status, await response.text());
    }
    return response.json() as Promise<ChatAttachmentResponse>;
  }
  ```
  (Requires `import { ApiError } from '../../api/client';` additive
  alongside `agentsApiClient.ts`'s existing `apiFetch` import.)
- `AgentDetailPanel.tsx`'s Chat tab gains:
  - State: `attachedFile: File | null`, `attachError: string | null`, a
    `fileInputRef`.
  - `ACCEPTED_EXTENSIONS = ['.pdf', '.txt', '.md']` and a
    `handleFileSelect` handler: rejects an unsupported extension
    immediately (clears the file input, sets `attachError` to a message
    naming the type as unsupported — mirrors `T01`'s own
    `validate_upload` wording, does not need to be byte-identical),
    otherwise sets `attachedFile`.
  - `handleRemoveAttachment`: clears `attachedFile`/`attachError`/the
    file input's value.
  - `handleSend` now branches: if `attachedFile` is set, calls
    `sendChatMessageWithAttachment(agentId, draft.trim(), attachedFile)`
    instead of `sendChatMessage`; the user-bubble text includes the
    filename (`` `${text} [attached: ${attachedFile.name}]`.trim() ``);
    the resulting agent-bubble's `isError` is `true` when
    `response.attachment_status === 'rejected'` (mirrors the existing
    catch block's `isError: true` convention for a genuine send failure).
    Clears `attachedFile`/the file input after sending, same as `draft`
    is cleared today.
  - JSX: a `<input type="file" accept=".pdf,.txt,.md"
    data-role="chat-attach-input" aria-label="Attach file" ...>` inside
    `.chat-input-row`, alongside the existing text input and submit
    button; a small attached-file preview
    (`data-role="chat-attach-preview"`) with a remove control when
    `attachedFile` is set; an inline error
    (`data-role="chat-attach-error"`, `role="alert"`) when `attachError`
    is set.

---

## Files to Modify

- `src/frontend/src/features/agents-map/agentsApiClient.ts` — add
  `ChatAttachmentResponse` and `sendChatMessageWithAttachment`, per the
  code block above. Do not modify `sendChatMessage`, `fetchAgent`,
  `fetchAgentHistory`, `updateAgentAssignment`, `triggerAgentAction`, or
  their existing types.
- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` — Chat tab
  only: add the attach control, preview, inline error, and the
  `handleSend`/state changes above. Do not modify the Settings or History
  tabs, `ProposalCard`, or any handler outside the Chat tab's own scope.

---

## Constraints

- Inherits from parent story: never fabricate or suppress a rejection —
  the server's own `reply` text is always rendered verbatim in the chat
  thread; the client-side extension pre-check is an additive, faster
  first line of feedback, never a replacement for trusting the server's
  own response.
- Structural-only lock (no `/design` pass covers this surface) — do not
  add pixel-specific styling beyond what's needed for the control to be
  visible and usable; visual polish is out of scope (see Objective).
- Must NOT modify `src/frontend/src/api/client.ts` — `apiFetch`'s
  hardcoded JSON `Content-Type` header is left exactly as-is; the
  multipart call bypasses it via a raw `fetch`, per the code sample.
- The existing plain-text send path (`sendChatMessage`, no attachment)
  must remain byte-for-byte unchanged in behavior — mirrors `AC-06`.

---

## Tests

<!-- Structural DOM assertions only, per the structural-ACs-for-screens
rule -- jsdom/a real headless browser sees no computed CSS/layout/colour,
only DOM structure and real fetch calls. -->

**Manual verification steps** (real dev server: `npm run dev` in
`src/frontend`, backend running per `T04`'s own instructions; a
headless-Chrome-via-CDP session or the OS-installed Edge headless
screenshot technique, per this project's own established patterns):

1. **[REQ-SB-28-US-01-AC-01]** Open an agent's detail panel, Chat tab.
   Confirm a `[data-role="chat-attach-input"]` file element is present
   inside `.chat-input-row` (structural signature — the attach control
   exists). Select a real, accepted `.txt` file; confirm a
   `[data-role="chat-attach-preview"]` element appears showing the
   filename. Type a short message and send. Confirm the user bubble in
   `[data-role="agent-chat-thread"]` shows both the message text and the
   filename, and confirm a real network request was made to `POST
   /agents/{agentId}/chat/attachment` (not the plain `/chat` endpoint) —
   via the CDP session's own network-observation, or by confirming the
   `sendChatMessageWithAttachment`/`fetch` call fired (Fiber-props direct-
   invoke of `handleSend`, this project's own established technique, if a
   native file-input `change`/`submit` event proves unreliable in the
   headless harness).
2. **[REQ-SB-28-US-01-AC-07]** Select a real `.png` file via the same
   attach control. Confirm `[data-role="chat-attach-error"]` appears
   immediately (before Send is even pressed) with a message naming
   `.png`/image files as unsupported, and confirm the file input's own
   selection is cleared (no stale rejected file left attached). Confirm
   no network request to `/chat/attachment` fired for this selection.
3. **[REQ-SB-28-US-01-AC-07]** (server-honesty half) Temporarily bypass
   the client-side extension check (e.g. call
   `sendChatMessageWithAttachment` directly against a real `.png` via the
   browser console, simulating a client that skipped pre-validation) —
   confirm the real server response's `attachment_status === "rejected"`
   is rendered as an error-styled agent bubble in the thread (`isError`
   true), the same honest message `T04`'s own real response produced —
   never silently dropped or shown as a normal reply.
4. **[REQ-SB-28-US-01-AC-08]** Repeat step 1 with a real, accepted-
   extension file generated/padded to exceed 20 MB. Confirm the resulting
   agent bubble shows the real server rejection message (size-limit
   wording, distinct from step 2's type wording), rendered as an
   error-styled bubble.
5. Non-AC smoke check: send an ordinary message with no attachment
   selected. Confirm the existing plain-text `POST /chat` call still
   fires (not `/chat/attachment`) and the thread behaves exactly as
   before this task.
6. Non-AC smoke check: attach a real, accepted `.txt` file whose content
   is genuinely summarizable, send it, and confirm the resulting agent
   bubble's text is the real backend `reply` (a filed-confirmation or
   summarized-unfiled message, depending on live Vault Filing Expert
   Provider availability) — not a placeholder.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `[data-role="chat-attach-input"]` renders inside `.chat-input-row`
      on the Chat tab (structural signature, `AC-01`)
- [ ] Attaching a supported file shows a preview and includes the
      filename in the sent message bubble (`AC-01`)
- [ ] An unsupported-type selection shows an honest inline rejection
      immediately, clears the selection, and never sends (`AC-07`)
- [ ] A server-side rejection (bypassing client pre-check, or a
      size-limit rejection) is rendered verbatim as an error-styled
      bubble, never silently dropped (`AC-07`/`AC-08`)
- [ ] The plain-text send path is unchanged in behavior (`AC-06`
      regression guard)
- [ ] `src/frontend/src/api/client.ts` not modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any backend behavior — `T01`-`T04`.
- Visual polish (icon choice, spacing, animation) — no `/design` pass
  covers this surface; a future design pass may restyle this control.
- A progress bar or granular multi-stage status indicator
  (uploading/extracting/summarizing/filing shown as distinct visual
  states) — the response is rendered as a single agent-bubble outcome,
  matching this chat surface's existing one-reply-per-turn shape; a
  richer status UI is a future enhancement, not locked here.

---

## Context / Notes

Read the REAL current `AgentDetailPanel.tsx`/`agentsApiClient.ts` before
applying this task's own code samples — reconcile against whatever
sibling stories may have additively changed in either file since this
task was written (this project's own standing "compose around the REAL
current file" pattern, `Implementation/Learnings.md`).

`ATTACHMENT_BASE_URL`'s duplication of `client.ts`'s own `BASE_URL`
fallback is a deliberate, minimal scope choice — exporting `BASE_URL`
from `client.ts` (or adding multipart support to `apiFetch` itself) would
touch a file outside this story's own architecture-scoped file list;
revisit only if a future story needs a second multipart call site.

---

## Implementation Log

**2026-08-14 — built per the task's own code block, reconciled against
the REAL current `AgentDetailPanel.tsx`/`agentsApiClient.ts` (both
already carry Skills-capabilities-list/Vault-scope-row/Knowledge-gaps-
tab/Overview-tab changes from 4 prior sprints — read in full before
editing, per this project's own standing "compose around the REAL
current file" pattern).** `agentsApiClient.ts` gained `ChatAttachmentResponse`
+ `sendChatMessageWithAttachment` verbatim per the code block, plus the
additive `ApiError` import from `client.ts` (`client.ts` itself not
touched). `AgentDetailPanel.tsx`'s Chat tab gained the `attachedFile`/
`attachError`/`fileInputRef` state, `ACCEPTED_EXTENSIONS`,
`handleFileSelect`/`handleRemoveAttachment`, the branching in
`handleSend`, and the JSX (file input, preview, inline error) — all
scoped to the Chat tab only. Settings/History/Overview/Knowledge-gaps
tabs, `ProposalCard`, and every handler outside the Chat tab (Section/
Provider/working-mode/keywords/scope/gap handlers) are untouched.

**Two scope-internal judgement calls, logged for human spot-check (not
escalations — each is a single defensible reading, not a guess filling
an ambiguous gap):**

1. **Reset `attachedFile`/`attachError` in the existing agent-switch
   `useEffect`** (alongside the already-existing `draft`/`messages`
   reset) — the task's own "After/Outputs" text doesn't explicitly call
   this out, but leaving a staged attachment across an agent switch
   would silently attach the wrong agent's file on the next send; this
   mirrors the existing reset block's own established convention for
   every other piece of per-agent chat-input state.
2. **Loosened `handleSend`'s early-return guard from `!text ||
   sending` to `(!text && !attachedFile) || sending`, and the submit
   button's `disabled` condition to match** — the task's own code
   sample composes `sendChatMessageWithAttachment(agentId, draft.trim(),
   attachedFile)` but doesn't itself redefine the original guard; kept
   verbatim, a file-only send (attach with no typed message) would be
   silently blocked, which contradicts Scenario 1's own framing ("the
   user attaches a file... and sends it") and ordinary chat-attachment
   UX expections (matches every mainstream chat client's own
   file-only-send affordance).

**Verification** (a dedicated `.venv` uvicorn instance on port `8002`
+ a dedicated Vite dev server; two real environment findings surfaced
and worked around, not silently — logged in both `MEMORY.md` and here):

- **Environment finding 1 (CORS):** `main.py`'s existing
  `CORSMiddleware` only allows origins `5173`/`5174` (`ADR-010`) — an
  initial dev server on port `5180` was silently CORS-blocked (rendered
  "No agents connected yet." with zero visible error). Restarted on
  `5174` (free, CORS-allowed, and distinct from the concurrent sibling
  coder's own `5173` listener — confirmed untouched throughout, before
  and after). `main.py` is out of this task's own `Files to Modify` — not
  touched.
- **Environment finding 2 (node not on PATH):** neither `node`/`npm`/
  `npx` resolved on this session's `PATH` (a third confirmed instance of
  this project's own recurring environment antipattern, `SPRINT-027`/
  `028`) — located via the actually-running Vite process's own real
  image path (`Get-CimInstance Win32_Process` → `ExecutablePath`) at
  `C:\myWorx\Projects\Second Brain\tools\node\node.exe`, a project-local
  install (not the registry path those prior sprints checked); added to
  `PATH` for this session only.

**Real CDP-driven headless-Edge session** (`msedge.exe --headless=new
--remote-debugging-port`, a Python `websockets`-based minimal CDP driver
— no Playwright/Puppeteer installed in this repo — real
`DOM.setFileInputFiles` for file-input interaction, real
Fiber-props-`onClick`/`onSubmit` direct-invoke per this project's own
established technique, real `Network.requestWillBeSent` observation):

- **AC-01** (step 1): structural check confirmed
  `[data-role="chat-attach-input"]` renders inside `.chat-input-row`.
  Selected the real `notes.txt` fixture via `DOM.setFileInputFiles` →
  preview `"📎 notes.txtRemove"` appeared. Typed `"here is a real doc"`
  via the native-setter technique, submitted via the real form's own
  `onSubmit` — confirmed the real network request fired to
  `/agents/email-capture/chat/attachment` (not `/chat`); the user bubble
  in `[data-role="agent-chat-thread"]` read `"here is a real doc
  [attached: notes.txt]"`; the attach input and preview both cleared
  after send. Re-connected to the same tab after the real backend
  round-trip completed and confirmed the real agent-bubble reply
  rendered (a genuine `summarized_unfiled` outcome this run — real
  LLM-classification variance from the earlier backend-layer test,
  correctly funneled to an honest "couldn't file it yet
  (pending_approval)... here's the summary" bubble, not silently
  dropped) — also independently satisfies the task's own non-AC smoke
  check (step 6: "a filed-confirmation OR summarized-unfiled message...
  not a placeholder"). The resulting real `propose_new_top_level_area`
  pending-approval record was declined (cleanup), never approved (would
  have created an unwanted throwaway vault area). **Pass.**
- **AC-07** (step 2, client half): selecting the real `photo.png`
  fixture → `[data-role="chat-attach-error"]` appeared immediately with
  `"'.png' files aren't supported yet..."`; the file input's own
  `.value` was confirmed cleared; no preview rendered; confirmed zero
  network requests to `/chat/attachment` fired for this selection.
  **Pass.**
- **AC-07** (step 3, server-honesty half): dynamically imported the
  real, served `agentsApiClient.ts` module in the live page and called
  its real `sendChatMessageWithAttachment('email-capture', ...)`
  directly with a real, valid PNG `File` object (bypassing the client
  pre-check entirely, per the task's own "e.g. call... via the browser
  console" technique) → the real server response, `{"attachment_status":
  "rejected", ...}`, came back honest and unmodified. Separately (not
  conflated with the above), **AC-08**'s own real run (below) exercises
  the identical `response.attachment_status === 'rejected' →
  isError: true` rendering branch in `handleSend` end-to-end through
  the real UI, confirming a server-side rejection genuinely renders as
  an error-styled bubble, not silently dropped. **Pass** (reported as
  two distinct, honestly-separated confirmations, not one).
- **AC-08** (step 4): a real `.txt` padded to 21 MB → client-side
  preview showed it (extension-only client check, as designed); real
  submit → real request to `/chat/attachment` → the real server
  rejection (`"That file is too large (21.0 MB) -- the limit is 20
  MB."`, distinct wording from `AC-07`) rendered in
  `[data-role="agent-chat-thread"]`; the resulting agent bubble's own
  `className` confirmed `"chat-message chat-message--agent
  chat-message--error"` — a real error-styled bubble. **Pass.**
- **AC-06 regression** (step 5, non-AC but verified): an ordinary
  message with no attachment → confirmed the real request fired to
  `/agents/email-capture/chat` (never `/chat/attachment`); confirmed via
  a direct history re-check that exactly one real chat exchange was
  recorded (a `Network.requestWillBeSent` duplicate log entry for the
  same URL was observed and investigated — the real backend history
  confirmed only one actual exchange occurred, so this is a harmless
  DevTools-Protocol logging artifact, not a real double-send; noted
  honestly rather than silently ignored).
- `src/frontend/src/api/client.ts` confirmed not modified (not in this
  task's own `Files to Modify`, and not touched).
- `npx tsc --noEmit -p tsconfig.app.json` — zero errors, both before and
  after the full edit.

**Clean-up:** the dedicated `8002`/`5174` backend/frontend instances and
the headless Edge process were stopped; the concurrent sibling coder's
own `8000`/`8001`/`5173` listeners were confirmed untouched throughout
and after. The `summarize-file` grant to `email-capture` created by
these real chat-attachment calls was deliberately left in place — this
is the intended, real, permanent effect of the shipped feature (`T04`'s
own unconditional `grant_skill_access` call), not test debris.

`gate: flagged` 2026-08-14 — trigger 8 only (two scope-internal
judgement calls above, each single-reading, non-blocking, logged for
human spot-check per this project's own established convention;
neither is a MUST-FLAG escalation). No new dependency, no shared-
interface change, no ADR deviation, no unanticipated file; all 4 of
this task's own locked ACs (`AC-01`, `AC-06` regression, `AC-07`,
`AC-08`) verified live end-to-end through a real browser session against
real backend calls.
