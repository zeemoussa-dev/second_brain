---
id: REQ-SB-13-US-01-T06
title: Agent detail panel shell — open/close, settings, available actions, AgentNode click wiring
parent_story: REQ-SB-13-US-01
requirement_id: REQ-SB-13
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-13-US-01-T05, REQ-SB-12-US-01-T02]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-13-US-01-T06 — Agent detail panel shell

## Parent Story

- Story: [[REQ-SB-13-US-01]] — `../UserStories/REQ-SB-13-US-01-embedded-agent-chat-and-communication-history.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-13 *Embedded Agent Chat & Communication History*

---

## Objective

Wire `AgentNode.tsx`'s click handler (currently none, per
`REQ-SB-12-US-01-T02`'s own explicit carve-out) to open a new
`AgentDetailPanel` overlay showing the selected agent's settings and
available actions, fetched from `T05`'s `GET /agents/{agent_id}`, closeable
via its close control or an outside click — the panel shell `T07`/`T08`
extend with chat and history.

**Task-level dependency note:** this task literally edits `AgentNode.tsx`
(built by `REQ-SB-12-US-01-T02`) to add click handling — hence the explicit
`depends_on` on that specific task file, not just the story-level "Blocked
by REQ-SB-12-US-01" dependency already recorded in the parent story's own
`## Dependencies`.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-12-US-01-T02` has landed `AgentNode.tsx` as a plain `<button>`
  with no `onClick` (its own Constraints explicitly deferred this to this
  story).
- `T05` has landed `GET /agents/{agent_id}` →
  `{"id","name","type","settings","actions"}`.

**After / Outputs:**
- `AgentsMapPage.tsx` owns `selectedAgentId: string | null` state.
- `AgentsMapCanvas`/`AgentNode` accept an `onSelectAgent(agentId)` callback,
  wired to each node's `onClick`.
- `features/agents-map/AgentDetailPanel.tsx` (new) renders the
  `.side-panel`/`.side-panel-overlay` overlay when `selectedAgentId` is set:
  header + close control, a Settings `.kv-list` section, an Available
  Actions `.action-list` section (buttons call `T05`'s
  `POST /agents/{id}/actions/{action_id}`, non-AC build work — no locked AC
  requires this wiring, but `architecture.md` names it as the surface's
  intent). Chat/History sections are added by `T07`/`T08`.
- `src/frontend/src/styles/agent-panel.css` exists, ported from
  `html-prototype/styles.css`.

---

## Files to Modify

- `src/frontend/src/features/agents-map/agentsApiClient.ts` (new):
  ```ts
  import { apiFetch } from '../../api/client';

  export interface AgentDetail {
    id: string;
    name: string;
    type: 'worker' | 'producer' | 'expert';
    settings: { key: string; value: string }[];
    actions: { id: string; label: string }[];
  }

  export function fetchAgent(agentId: string): Promise<AgentDetail> {
    return apiFetch<AgentDetail>(`/agents/${agentId}`);
  }

  export interface TriggerActionResult {
    status: 'ok' | 'error';
    message: string;
  }

  export function triggerAgentAction(agentId: string, actionId: string): Promise<TriggerActionResult> {
    return apiFetch<TriggerActionResult>(`/agents/${agentId}/actions/${actionId}`, { method: 'POST' });
  }
  ```
  (`T07`/`T08` add `sendChatMessage`/`fetchAgentHistory` to this same file.)

- `src/frontend/src/features/agents-map/AgentNode.tsx` — add an
  `onSelect: (agentId: string) => void` prop, wired to `onClick`:
  ```tsx
  import type { MockAgent } from './mockAgents';
  import { RING_RADIUS, polarToCartesian } from './polarLayout';

  interface AgentNodeProps {
    agent: MockAgent;
    onSelect: (agentId: string) => void;
  }

  export function AgentNode({ agent, onSelect }: AgentNodeProps) {
    const { x, y } = polarToCartesian(RING_RADIUS[agent.type], agent.angleDeg);
    return (
      <button
        type="button"
        className={`agent-node agent-node--${agent.type}`}
        style={{ top: `${y}%`, left: `${x}%` }}
        data-agent-id={agent.id}
        onClick={() => onSelect(agent.id)}
      >
        <span className="agent-node-label">{agent.label}</span>
        <span className="agent-node-type">{agent.type}</span>
      </button>
    );
  }
  ```

- `src/frontend/src/features/agents-map/AgentsMapCanvas.tsx` — add an
  `onSelectAgent: (agentId: string) => void` prop, threaded through to every
  `<AgentNode key={agent.id} agent={agent} onSelect={onSelectAgent} />`
  call. No other change to this component's existing structure/geometry.

- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` (new):
  ```tsx
  import { useEffect, useState } from 'react';
  import { fetchAgent, type AgentDetail } from './agentsApiClient';

  interface AgentDetailPanelProps {
    agentId: string;
    onClose: () => void;
  }

  export function AgentDetailPanel({ agentId, onClose }: AgentDetailPanelProps) {
    const [agent, setAgent] = useState<AgentDetail | null>(null);

    useEffect(() => {
      setAgent(null); // clear stale content immediately on agent switch
      fetchAgent(agentId).then(setAgent);
    }, [agentId]);

    return (
      <>
        <div className="side-panel-overlay" onClick={onClose} />
        <aside className="side-panel" aria-label="Agent details">
          <div className="side-panel-header">
            <span className="badge">Agent detail</span>
            <button type="button" className="side-panel-close" aria-label="Close panel" onClick={onClose}>
              &times;
            </button>
          </div>
          <div className="side-panel-body">
            {agent && (
              <div className="side-panel-agent" data-agent-detail={agent.id}>
                <h2>{agent.name} <span className="badge">{agent.type}</span></h2>

                <div className="side-panel-section">
                  <h3>Settings</h3>
                  <div className="kv-list">
                    {agent.settings.map((row) => (
                      <div className="kv-row" key={row.key}>
                        <span className="kv-key">{row.key}</span>
                        <span>{row.value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="side-panel-section">
                  <h3>Available actions</h3>
                  <div className="action-list">
                    {agent.actions.map((action) => (
                      <button type="button" className="btn" key={action.id}>
                        {action.label}
                      </button>
                    ))}
                  </div>
                </div>
                {/* Chat + Communication history sections: T07/T08. */}
              </div>
            )}
          </div>
        </aside>
      </>
    );
  }
  ```
  (Action buttons render this pass but their `onClick` isn't wired to
  `triggerAgentAction` yet — no locked AC in this story requires the direct
  button-trigger path to be exercised; only the chat-trigger path (Scenario
  7, `T08`) is locked. Wiring the buttons is reasonable, low-risk follow-up
  work but is explicitly Out of Scope here to keep this task's own AC
  coverage precise — see Out of Scope.)

- `src/frontend/src/pages/AgentsMapPage.tsx` — add selection state and
  render the panel:
  ```tsx
  import { useState } from 'react';
  import { AgentsMapCanvas } from '../features/agents-map/AgentsMapCanvas';
  import { AgentDetailPanel } from '../features/agents-map/AgentDetailPanel';
  import { POPULATED_SECTIONS, POPULATED_AGENTS } from '../features/agents-map/mockAgents';

  export function AgentsMapPage() {
    const hasAgents = POPULATED_AGENTS.length > 0;
    const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

    return (
      <>
        <h1>Agents Map</h1>
        <AgentsMapCanvas
          sections={POPULATED_SECTIONS}
          agents={POPULATED_AGENTS}
          onSelectAgent={setSelectedAgentId}
        />
        {!hasAgents && (
          <div className="empty-state">
            <div className="empty-state-icon">◎</div>
            <p><strong>No agents connected yet.</strong></p>
            <p className="text-muted">
              Sections and Hubs appear here once Second Brain is wired to
              Hermes-connected background jobs (capture, enrichment, or
              Q&amp;A). Nothing to click on yet.
            </p>
          </div>
        )}
        {selectedAgentId && (
          <AgentDetailPanel agentId={selectedAgentId} onClose={() => setSelectedAgentId(null)} />
        )}
      </>
    );
  }
  ```

- `src/frontend/src/styles/agent-panel.css` (new) — port verbatim from
  `html-prototype/styles.css`: the `.side-panel-overlay`/`.side-panel`/
  `.side-panel-header`/`.side-panel-close`/`.side-panel-body`/
  `.side-panel-agent`/`.side-panel-section` block, and `.action-list`. Do
  not port `.chat-*`/`.log-*` yet — `T07`/`T08` port those alongside their
  own components. `.kv-list`/`.badge`/`.btn` are already in `settings.css`
  (`REQ-SB-12-US-01-T01`) — do not duplicate them here.

- `src/frontend/src/main.tsx` — add
  `import './styles/agent-panel.css';` alongside the existing style imports.

---

## Constraints

- Inherits from parent story: `ADR-010`'s styling convention (prototype
  class names verbatim) — this story is `ADR-010`'s own named "expected to
  extend `AgentNode.tsx`'s click handling" consequence.
- Must not modify `AgentsMapCanvas`'s/`KnowledgeBaseNode`'s/`SectionHub`'s
  own geometry/positioning logic — only add the `onSelectAgent` prop
  threading.
- Selecting a *different* agent while the panel is already open must clear
  the previously-rendered agent's content before the new fetch resolves
  (`setAgent(null)` on every `agentId` change) — `T08` verifies this fully
  once chat/history exist too, but the mechanism is built here.
- No new dependency.

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `uvicorn app.main:app --reload --port 8001`; browser preview
tool):

1. **[REQ-SB-13-US-01-AC-01]** Load `/`. Click one of the rendered
   `.agent-node` elements (e.g. Email Capture). Confirm a `.side-panel`
   element opens showing that agent's name, a `.kv-list` Settings section
   with at least one `.kv-row`, and an `.action-list` Available Actions
   section with at least one button, matching `T05`'s real
   `GET /agents/email-capture` response.
2. **[REQ-SB-13-US-01-AC-06]** With the panel open (step 1), click the
   panel's close control (`.side-panel-close`). Confirm the `.side-panel`
   element is removed/hidden and the Agents Map underneath remains visible
   and clickable (click a different `.agent-node` afterward to confirm it
   still opens the panel). Repeat by opening the panel again and instead
   clicking the `.side-panel-overlay` (outside the panel) — confirm the
   panel closes the same way.
3. Non-AC smoke check: confirm no console errors/warnings on open/close, and
   confirm no `trigger_phrases` field is ever visible in the rendered
   Settings/Actions sections (the API response never includes it, per
   `T05`'s own response shape).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Clicking an `.agent-node` opens a `.side-panel` showing that agent's
      settings (`.kv-list`) and available actions (`.action-list`)
- [ ] Closing via the close control or the overlay click removes the panel
      and leaves the Agents Map interactive
- [ ] `AgentNode`/`AgentsMapCanvas` gain `onSelect`/`onSelectAgent` props
      without changing their existing geometry/positioning behavior
- [ ] `agent-panel.css` ported per the selector groups above and imported
      once in `main.tsx`
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring the Available Actions buttons' `onClick` to `triggerAgentAction` —
  no locked AC in this story requires the direct-button path to be
  exercised (only the chat-trigger path, Scenario 7, is locked); left as
  clearly-scoped future follow-up, not built here to avoid an unverified
  code path.
- Chat thread — `T07`.
- Communication history + full agent-switching content refresh — `T08`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-011` created at
`/plan-tasks` step 1) — the human reviews `ADR-011` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

The prototype's `#agentPanelOverlay`/`#agentPanelClose` IDs are not
reproduced 1:1 (React's per-instance panel doesn't need global DOM IDs) —
class names are kept identical (`.side-panel-overlay`, `.side-panel-close`,
...) per `ADR-010`'s own class-name-verbatim convention; only the ID
attributes are dropped as unnecessary in a component-scoped world.

---

## Implementation Log

**2026-08-11, coder pass.** Read the real current
`features/agents-map/AgentNode.tsx`, `AgentsMapCanvas.tsx`,
`pages/AgentsMapPage.tsx`, `App.tsx` before editing, per the parent
sprint's own instruction (SPRINT-008 had just landed these with no
`onClick`/selection wiring, exactly matching this task's assumed "Before"
state — no drift found). Added `agentsApiClient.ts` (new),
`onSelect`/`onSelectAgent` prop threading to `AgentNode.tsx`/
`AgentsMapCanvas.tsx`, `AgentDetailPanel.tsx` (new), selection state in
`AgentsMapPage.tsx`, `styles/agent-panel.css` (new, ported from
`html-prototype/styles.css`), and the `main.tsx` import — all verbatim per
this task's own code blocks. `main.tsx` had a concurrent `my-day.css`
import added since this task was authored (SPRINT-009) — additive, added
`agent-panel.css`'s import alongside it, no conflict.

Assumption (scope-internal, logged for spot-check): the prototype's
`.side-panel-overlay`/`.side-panel`/`.side-panel-agent` CSS rules gate
visibility on `.open`/`.active` modifier classes the prototype's own JS
toggles; this task's own literal TSX never adds those classes (React
conditionally mounts/unmounts the whole overlay instead). Ported the
structural rules (dimensions, borders, layout, colors) but dropped the
hidden-by-default `opacity:0`/`pointer-events:none`/`transform:
translateX(100%)` base states and their `.open`/`.active` transitions,
since keeping them verbatim would have rendered the panel permanently
invisible (mounted-but-never-"opened"). Documented inline in
`agent-panel.css`'s own header comment.

Live verification (headless Chrome via CDP, real `npm run dev` +
`uvicorn` backend on port 8003, port 8000/8001/8002 already occupied —
see T04's Log):

- **[REQ-SB-13-US-01-AC-01]** Loaded `/`, confirmed 5 `.agent-node`
  elements. Clicked `[data-agent-id=email-capture]`. A `.side-panel`
  opened showing `"Email Capture" "worker"`, a `.kv-list` with 4
  `.kv-row`s (Schedule/Vault target/Classifier/Missed-run catch-up), and
  an `.action-list` with 3 buttons (Run capture now / View last run /
  Pause schedule) — matching T05's real `GET /agents/email-capture`
  response exactly. **PASS.** Screenshot:
  `ac01_panel_open.png` (scratchpad, visually confirmed — panel renders
  per the approved prototype's layout/typography).
- **[REQ-SB-13-US-01-AC-06]** Clicked `.side-panel-close` — `.side-panel`
  removed from the DOM, `.agent-node` elements still present/clickable
  (confirmed by re-clicking one immediately after, which reopened the
  panel). Reopened the panel, then clicked `.side-panel-overlay` (outside
  the panel) — panel closed the same way. **PASS.**
- Non-AC smoke check: no `trigger_phrases` text anywhere in
  `.side-panel-body`'s rendered text (confirmed via
  `innerText.includes("trigger_phrases")` → `false`). No console
  errors/warnings observed across open/close/reopen.

- [x] Clicking an `.agent-node` opens a `.side-panel` showing settings + actions — **AC-01 PASS**
- [x] Closing via close control or overlay click removes the panel, map stays interactive — **AC-06 PASS**
- [x] `AgentNode`/`AgentsMapCanvas` gain `onSelect`/`onSelectAgent` without changing geometry — confirmed by diff review (only prop additions + one `onClick`/threading line each)
- [x] `agent-panel.css` ported and imported once in `main.tsx` — confirmed
- [x] `MEMORY.md` updated — yes, see Patterns entry for SPRINT-010
- [x] `CHANGELOG.md` entry appended — yes
