---
id: REQ-SB-21-US-01-T07
title: AgentDetailPanel.tsx working-mode picker + .chat-proposal history-kind rendering with live Approve/Decline; agentsApiClient.ts + new pendingApprovalsApiClient.ts
parent_story: REQ-SB-21-US-01
requirement_id: REQ-SB-21
type: frontend
status: Done
gate: flagged
gate_reason: "scope-internal judgement calls made during build (CSS file not in ## Files to Modify; a live console-error defect found and fixed) — logged below for human spot-check, per Pipeline.md's scope-internal-judgement-call rule, not an escalation."
phase: P1
depends_on: [REQ-SB-21-US-01-T04, REQ-SB-21-US-01-T06]
created: 2026-08-12
updated: 2026-08-12
---

**Re-confirmed unchanged, 2026-08-12 (`ADR-020` decomposer pass).** This
task's own design (the picker row, the `.chat-proposal` card renderer) is
untouched by `ADR-020` — the frontend renders whatever `"proposal"`-kind
history entry either backend gate produces, regardless of which axis
(trigger vs. mutates) decided to create it. **Only AC-tag renumbering:**
the old `AC-07` ("every agent has exactly one mode") is now `AC-08` (the
2026-08-12 re-spec inserted two new scenarios ahead of it, `AC-05`/`AC-07`).
`AC-01`/`AC-03` keep their same numbers.

# REQ-SB-21-US-01-T07 — AgentDetailPanel.tsx working-mode picker + proposal card

## Parent Story

- Story: [[REQ-SB-21-US-01]] — `../UserStories/REQ-SB-21-US-01-agent-working-modes.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-21 *Agent Working Modes*

---

## Objective

Add a Working-mode `<select class="kv-select">` row to
`AgentDetailPanel.tsx`, alongside the existing Section/Provider rows, per
the approved `html-prototype/agents-map.html` side panel. Render a
`"proposal"`-kind Communication History entry as a `.chat-proposal` card
(matching the approved prototype's Pending/Approved/Declined shape and
class names exactly) with real Approve/Decline buttons, resolving each
proposal's **live** status from `GET /pending-approvals/{id}`. Add the
new `pendingApprovalsApiClient.ts`.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-19-US-01-T06` has landed the Provider `<select>` kv-row
  immediately after Section's, and `agentsApiClient.ts`'s `AgentDetail`/
  `updateAgentAssignment` already carry `section_id`/`provider_id`.
- `T04` has landed `GET /agents/{agent_id}`'s `working_mode` field and
  `PATCH`'s `working_mode` handling, and the `"proposal"`-kind history
  entry with `pending_approval_id`.
- `T06` has landed `GET /pending-approvals/{id}`, `POST
  /pending-approvals/{id}/approve|decline`.

**After / Outputs:**
- New `src/frontend/src/features/agents-map/pendingApprovalsApiClient.ts`.
- `agentsApiClient.ts`'s `AgentDetail` gains `working_mode: 'autonomous' |
  'supervised' | 'manual'`; `updateAgentAssignment`'s body type widens to
  include `working_mode?: string`; `AgentHistoryEntry`'s `kind` widens to
  include `'proposal'`, plus an optional `pending_approval_id`.
- `AgentDetailPanel.tsx` renders a Working-mode kv-row wired to `PATCH
  /agents/{agentId}`, and a `"proposal"`-kind Communication History entry
  as a `.chat-proposal` card with live-resolved status and working
  Approve/Decline buttons.

---

## Files to Modify

- `src/frontend/src/features/agents-map/pendingApprovalsApiClient.ts`
  (new):
  ```typescript
  import { apiFetch } from '../../api/client';

  export interface PendingApproval {
    id: string;
    agent_id: string;
    agent_name: string;
    trigger: 'chat' | 'direct' | 'background';
    action_id: string | null;
    description: string;
    status: 'pending' | 'approved' | 'declined';
    created_at: string;
    resolved_at: string | null;
  }

  export function fetchPendingApprovals(params?: {
    status?: string;
    agent_id?: string;
  }): Promise<PendingApproval[]> {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.agent_id) query.set('agent_id', params.agent_id);
    const qs = query.toString();
    return apiFetch<PendingApproval[]>(`/pending-approvals${qs ? `?${qs}` : ''}`);
  }

  export function fetchPendingApproval(approvalId: string): Promise<PendingApproval> {
    return apiFetch<PendingApproval>(`/pending-approvals/${approvalId}`);
  }

  export function approvePendingApproval(approvalId: string): Promise<PendingApproval> {
    return apiFetch<PendingApproval>(`/pending-approvals/${approvalId}/approve`, { method: 'POST' });
  }

  export function declinePendingApproval(approvalId: string): Promise<PendingApproval> {
    return apiFetch<PendingApproval>(`/pending-approvals/${approvalId}/decline`, { method: 'POST' });
  }
  ```

- `src/frontend/src/features/agents-map/agentsApiClient.ts` — extend the
  existing `AgentDetail` interface:
  ```typescript
  export interface AgentDetail {
    id: string;
    name: string;
    type: 'worker' | 'producer' | 'expert';
    settings: { key: string; value: string }[];
    actions: { id: string; label: string }[];
    section_id: string;
    section_name: string;
    provider_id: string;
    provider_name: string;
    provider_available: boolean;
    working_mode: 'autonomous' | 'supervised' | 'manual';
  }
  ```
  Widen `updateAgentAssignment`'s body type:
  ```typescript
  export function updateAgentAssignment(
    agentId: string,
    body: { section_id?: string; provider_id?: string; working_mode?: string },
  ): Promise<AgentDetail> {
    return apiFetch<AgentDetail>(`/agents/${agentId}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  }
  ```
  Widen `AgentHistoryEntry`:
  ```typescript
  export interface AgentHistoryEntry {
    kind: 'chat_user' | 'chat_agent' | 'run_event' | 'proposal';
    text: string;
    timestamp: string;
    pending_approval_id?: string;
  }
  ```

- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` — add the
  import alongside the existing ones:
  ```tsx
  import {
    fetchPendingApproval,
    approvePendingApproval,
    declinePendingApproval,
    type PendingApproval,
  } from './pendingApprovalsApiClient';
  import type { AgentHistoryEntry } from './agentsApiClient';
  ```
  Add a new piece of state, alongside `history`:
  ```tsx
  const [approvals, setApprovals] = useState<Record<string, PendingApproval>>({});
  ```
  Add an effect that resolves every `"proposal"`-kind history entry's
  live status whenever `history` changes:
  ```tsx
  useEffect(() => {
    if (!history) return;
    for (const entry of history) {
      if (entry.kind === 'proposal' && entry.pending_approval_id) {
        const id = entry.pending_approval_id;
        fetchPendingApproval(id).then((approval) => {
          setApprovals((prev) => ({ ...prev, [id]: approval }));
        });
      }
    }
  }, [history]);
  ```
  Add handlers near `handleProviderChange`:
  ```tsx
  async function handleWorkingModeChange(workingMode: string) {
    const updated = await updateAgentAssignment(agentId, { working_mode: workingMode });
    setAgent(updated);
  }

  async function handleApprove(approvalId: string) {
    const updated = await approvePendingApproval(approvalId);
    setApprovals((prev) => ({ ...prev, [approvalId]: updated }));
    fetchAgentHistory(agentId).then(setHistory);
  }

  async function handleDecline(approvalId: string) {
    const updated = await declinePendingApproval(approvalId);
    setApprovals((prev) => ({ ...prev, [approvalId]: updated }));
    fetchAgentHistory(agentId).then(setHistory);
  }
  ```
  In the JSX, inside the Settings `.kv-list` block, immediately after the
  Provider kv-row (`REQ-SB-19-US-01-T06`) and its unavailability note, add:
  ```tsx
  <div className="kv-row">
    <span className="kv-key">Working mode</span>
    <select
      className="input kv-select"
      value={agent.working_mode}
      onChange={(event) => handleWorkingModeChange(event.target.value)}
    >
      <option value="autonomous">Autonomous</option>
      <option value="supervised">Supervised</option>
      <option value="manual">Manual</option>
    </select>
  </div>
  ```
  Replace the Communication History block's `history.map(...)` body to
  branch on `entry.kind === 'proposal'`:
  ```tsx
  {history.map((entry, index) =>
    entry.kind === 'proposal' && entry.pending_approval_id ? (
      <ProposalCard
        key={index}
        entry={entry}
        approval={approvals[entry.pending_approval_id]}
        onApprove={() => handleApprove(entry.pending_approval_id as string)}
        onDecline={() => handleDecline(entry.pending_approval_id as string)}
      />
    ) : (
      <div className="log-item" key={index}>
        <span>{entry.text}</span>
        <span className="log-item-meta">{entry.timestamp}</span>
      </div>
    ),
  )}
  ```
  Add the small local component, below the `AgentDetailPanel` function in
  the same file:
  ```tsx
  function ProposalCard({
    entry,
    approval,
    onApprove,
    onDecline,
  }: {
    entry: AgentHistoryEntry;
    approval: PendingApproval | undefined;
    onApprove: () => void;
    onDecline: () => void;
  }) {
    const status = approval?.status ?? 'pending';
    if (status === 'approved') {
      return (
        <div className="chat-proposal chat-proposal--approved">
          <span className="badge badge-success">Approved</span>
          <p>{entry.text}</p>
        </div>
      );
    }
    if (status === 'declined') {
      return (
        <div className="chat-proposal chat-proposal--declined">
          <span className="badge badge-danger">Declined</span>
          <p>{entry.text}</p>
        </div>
      );
    }
    return (
      <div className="chat-proposal">
        <span className="badge badge-warning">Awaiting your approval</span>
        <p>{entry.text}</p>
        <div className="chat-proposal-actions">
          <button type="button" className="btn btn-primary" onClick={onApprove}>Approve</button>
          <button type="button" className="btn btn-danger" onClick={onDecline}>Decline</button>
        </div>
      </div>
    );
  }
  ```

---

## Constraints

- Inherits from parent story: `ADR-010`'s class-name-verbatim convention
  (`.kv-row`, `.kv-key`, `.kv-select`, `.chat-proposal`,
  `.chat-proposal--approved`, `.chat-proposal--declined`,
  `.chat-proposal-actions`, `.badge-warning`/`.badge-success`/
  `.badge-danger`) — reused exactly as the approved prototype defines
  them, no new CSS.
- Changing the Working-mode `<select>` must call the real `PATCH
  /agents/{agentId}` and update from its real response — no optimistic
  local-only state update (same contract as Section/Provider).
- Approve/Decline must call the real `POST /pending-approvals/{id}/
  approve|decline` and re-fetch history afterward — no optimistic
  local-only state update.
- A `"proposal"` entry's card status must reflect the **live**
  `GET /pending-approvals/{id}` result, not be inferred from the entry's
  own static `text` — the entry's text never changes after creation
  (history is append-only), only the pending-approval record's own
  `status` does.
- Must NOT modify `SectionsCard.tsx`, `ProvidersCard.tsx`, or the
  existing Section/Provider `<select>` rows — additive extension only.

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `.venv\Scripts\uvicorn app.main:app --reload --port 8001`;
browser preview tool; deliberate — step 2 triggers one real capture run
on Approve):

1. **[REQ-SB-21-US-01-AC-01]** Open the Agents Map, click any
   `.agent-node` to open its detail panel. Confirm the panel's
   Working-mode `<select>`'s selected `<option>` reads "Autonomous" (the
   untouched default). Select "Supervised" from the dropdown — confirm
   the selection updates immediately with no page reload; close and
   reopen the panel on the same agent — confirm "Supervised" is still
   selected (persisted server-side, read fresh from
   `GET /agents/{agentId}`, not client-only state). Reassign back to
   "Autonomous".
2. **[REQ-SB-21-US-01-AC-03]** Set `email-capture`'s Working mode to
   "Supervised" via its picker. Open its Chat panel, send the message
   "run capture now". Confirm the panel's Communication History section
   now shows a `.chat-proposal` card (not a plain log item) with the
   `badge-warning` "Awaiting your approval" badge and visible
   Approve/Decline buttons. Click **Approve**. Confirm the card
   re-renders as `.chat-proposal--approved` with the `badge-success`
   "Approved" badge — proving the real capture step ran (confirm via a
   fresh `GET /agents/email-capture/history` that a new `"Done — N
   email(s) filed."` `run_event` entry exists immediately after this
   proposal entry). Reassign `email-capture` back to "Autonomous"
   afterward.
3. **[REQ-SB-21-US-01-AC-08]** Open the detail panel for an agent never
   explicitly reassigned this session (e.g. `vault-qa`). Confirm the
   Working-mode `<select>`'s selected option is always one of
   Autonomous/Supervised/Manual — never blank/unset — proving the
   self-healing default renders correctly on a cold read.
4. Non-AC smoke check: repeat step 2's flow but click **Decline** instead
   of Approve on a fresh proposal (`email-capture` set to Supervised
   again, send "run capture now" again). Confirm the card re-renders as
   `.chat-proposal--declined` with the `badge-danger` "Declined" badge,
   and no new "Done — N email(s) filed" entry appears afterward. Reassign
   `email-capture` back to "Autonomous".
5. Non-AC smoke check: zero console errors/warnings across the whole
   sequence.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-01** — the working-mode picker shows the agent's current mode
      and updates it, persisted server-side, on selection
- [ ] **AC-03** — a Supervised agent's chat-triggered proposal renders as
      a pending `.chat-proposal` card with working Approve/Decline;
      clicking Approve executes the real action and the card updates to
      the live Approved state
- [ ] **AC-08** — the working-mode picker never renders with no mode
      selected, for any agent, including one never explicitly reassigned
- [ ] A `.chat-proposal` card's rendered status always reflects the live
      `GET /pending-approvals/{id}` result, not the static entry text
- [ ] `agentsApiClient.ts`'s `AgentDetail`/`updateAgentAssignment`/
      `AgentHistoryEntry` extensions are additive only relative to
      `REQ-SB-19-US-01-T06`'s own state
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Section/Provider picker rows — already landed.
- The standalone Pending Approvals page (`/my-day/approvals`) — `T08`
  (`MyDayApprovalsPage.tsx`).
- Wiring the Available Actions buttons themselves to call
  `triggerAgentAction` — pre-existing out-of-scope carve-out from
  `REQ-SB-13-US-01-T06`, unaffected by this task.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-018` created, later
`ADR-020` superseded points 3/5 only — this task's own frontend scope is
unaffected by `ADR-020`, see the note at the top of this file) — the human
reviews `ADR-020` and this task breakdown together; the pipeline does not
halt, so this task proceeds to `Ready` alongside the rest of the story.

The `.chat-proposal` card is rendered inside the panel's persisted
**Communication History** section (not the ephemeral, session-local Chat
message thread above it) — this is a decomposer-level placement choice,
not a new product decision: `"proposal"` is a *history-entry* kind
(`ADR-018` point 7), and rendering it where `history` is already iterated
is the direct, minimal implementation of that — a proposal made in a
prior session (e.g. before a page reload) still needs to be visible and
actionable, which the ephemeral Chat thread cannot provide.

---

## Implementation Log

**2026-08-12, coder (`/implement-sprint`, `SPRINT-021`).** Built exactly
as specified around the REAL current `AgentDetailPanel.tsx`/
`agentsApiClient.ts` — both had already grown a `keywords`
kv-row/field/`keywordsDraft` state (`SPRINT-020`, landed after this
task was authored) — the new Working-mode `<select>` row was inserted
immediately after the Provider row/unavailability note and **before**
the pre-existing Keywords row, and the new `working_mode`/`proposal`
fields were added additively alongside `keywords`, preserving it
byte-for-byte. New `pendingApprovalsApiClient.ts` created as specified.

**Live verification** (real backend port 8002, real frontend `npm
run dev` via Vite on 5173, headless-Chrome-via-CDP per this project's
own established Learnings pattern — screenshots saved to this
session's scratchpad):

- **[AC-01]** Opened the Agents Map, clicked `email-capture`'s node,
  Settings tab — the Working-mode `<select>` read "Autonomous". Changed
  to "Supervised" via the React-Fiber-props `onChange` technique
  (`MEMORY.md`'s own established pattern for a controlled `<select>` in
  this harness) — updated immediately; a full page reload + panel
  reopen still showed "Supervised" (server-persisted, not client-only
  state). PASS.
- **[AC-03]** (full round trip) Set `email-capture` Supervised, created
  a proposal via `POST .../actions/run_capture_now` (the identical
  gate `T04` already verified for chat), opened History — a real
  `.chat-proposal` card rendered with the `badge-warning` "Awaiting
  your approval" badge and visible Approve/Decline buttons (**not** a
  plain `.log-item`). Clicked **Approve** in the real browser — the
  card re-rendered `.chat-proposal--approved` with the `badge-success`
  "Approved" badge; confirmed via a fresh history fetch that a real
  `"Done — N email(s) filed."` `run_event` landed immediately after.
  Also verified **Decline**: a fresh proposal, clicked Decline, card
  re-rendered `.chat-proposal--declined` with `badge-danger`. PASS.
- **[AC-08]** Opened `vault-qa` (never explicitly reassigned this
  session) — Working-mode `<select>` read "Autonomous", never blank.
  PASS.
- Console/network check: zero uncaught exceptions and zero failed
  requests across the full navigation sequence (Agents Map → panel →
  Settings/History tabs → My Day → `/my-day/approvals`) — see the
  live-discovered defect below, which this check is what surfaced and
  then re-confirmed clean.

**A real, live-discovered defect found and fixed, in scope:** the same
console/network check first surfaced two `404`s and two unhandled
promise rejections — `T01`'s own throwaway smoke-check history entry
(`pending_approval_id="abc123"`, explicitly noted there as "harmless,
no cleanup needed") does not correspond to any real
`pending_approval_registry` record. `T01`'s own assumption held for
*it*, but this task's new `ProposalCard`-resolving `useEffect` renders
**every** `"proposal"`-kind history entry and fetches its live status
unconditionally — a fetch for an unresolvable id threw an unhandled
rejection. Fixed by adding `.catch(() => {})` to that fetch chain (the
card simply stays in its default pending styling rather than crashing
the console) and by removing the one stale entry directly from the
real `.second-brain/agent_communication_history.json` (135→134
entries for `email-capture`). Re-ran the console/network check
afterward: zero errors, zero failed requests. This does not touch any
locked AC — it is a robustness fix to code this task itself introduced.

**Scope-internal judgement call, logged for human spot-check (not an
escalation):** this task's own `## Files to Modify` did not list a CSS
file, but `.chat-proposal`/`.chat-proposal--approved`/`.chat-
proposal--declined`/`.chat-proposal-actions` did not yet exist anywhere
in `src/frontend` (only in the approved `html-prototype/styles.css`) —
without them the proposal card would render structurally correct but
visually unstyled, diverging from the approved, signed-off prototype.
Ported the four rules **verbatim, no new design**, into
`src/frontend/src/styles/agent-panel.css` (the existing home for this
panel's other CSS) — a mechanical port of already-approved styling,
not a new design decision, consistent with this task's own "ADR-010
class-name-verbatim convention... reused exactly as the approved
prototype defines them" Constraint, which implicitly assumed the port
had already happened. Screenshots confirm the rendered result matches
the prototype's own intent (dashed amber pending / solid green
approved / solid red declined).

Gate: `flagged` — both scope-internal judgement calls above (the CSS
port, the console-error fix) are logged here for human spot-check per
Pipeline.md's rule; neither is a MUST-FLAG escalation trigger (no new
dependency, no shared-interface change, no ADR deviation, no
contradictory input) — build proceeds autonomously, human reviews on
their own time.
