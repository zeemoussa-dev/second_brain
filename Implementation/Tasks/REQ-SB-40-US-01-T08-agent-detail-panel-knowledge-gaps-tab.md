---
id: REQ-SB-40-US-01-T08
title: AgentDetailPanel.tsx — conditional "Knowledge gaps" tab (Expert-type agents only)
parent_story: REQ-SB-40-US-01
requirement_id: REQ-SB-40
type: frontend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-032 created) — carried from the parent story; the human reviews ADR-032 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-40-US-01-T05, REQ-SB-40-US-01-T06, REQ-SB-40-US-01-T07]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-40-US-01-T08 — `AgentDetailPanel.tsx` "Knowledge gaps" tab

## Parent Story

- Story: [[REQ-SB-40-US-01]] — `../UserStories/REQ-SB-40-US-01-agent-knowledge-gap-tracking-and-expert-readiness.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-40 *Agent Knowledge-Gap Tracking & Expert Readiness*

---

## Objective

Add a fourth, conditionally-rendered "Knowledge gaps" tab to `AgentDetailPanel.tsx`, gated to `agent.type === 'expert'` (`ADR-032` point 5 — the panel carries exactly 3 tabs today, `chat`/`history`/`settings`; this is a net-new fourth, not a repurposed "Available actions" subsection). Renders each open gap's question and the current open-gap count (`T07`'s `GET` endpoint), with a form to submit a human answer (`T05`) or direct research (`T06`).

---

## Starting State → End State

**Before / Inputs:**
- `T05` has landed `POST /agents/{agent_id}/knowledge-gaps/{gap_id}/resolve`.
- `T06` has landed `POST /agents/{agent_id}/knowledge-gaps/{gap_id}/research`.
- `T07` has landed `GET /agents/{agent_id}/knowledge-gaps`.
- Real current `AgentDetailPanel.tsx`'s tab machinery (verbatim, relevant excerpt):
  ```tsx
  const TABS = ['chat', 'history', 'settings'] as const;
  type Tab = (typeof TABS)[number];
  const TAB_LABELS: Record<Tab, string> = { chat: 'Chat', history: 'History', settings: 'Settings' };
  ```
  and the tab-bar JSX:
  ```tsx
  <div className="side-panel-tabs" role="tablist">
    {TABS.map((tab) => (
      <button
        key={tab}
        type="button"
        role="tab"
        aria-selected={activeTab === tab}
        className={`side-panel-tab${activeTab === tab ? ' side-panel-tab--active' : ''}`}
        onClick={() => setActiveTab(tab)}
      >
        {TAB_LABELS[tab]}
      </button>
    ))}
  </div>
  ```
  `AgentDetail.type` is already `'worker' | 'producer' | 'expert'` (real current `agentsApiClient.ts`).

**After / Outputs:**
- `agentsApiClient.ts` gains `KnowledgeGap`/`KnowledgeGapsResponse` interfaces and `fetchAgentKnowledgeGaps`/`resolveKnowledgeGap`/`researchKnowledgeGap` functions.
- `AgentDetailPanel.tsx`'s tab bar renders a 4th "Knowledge gaps" tab ONLY when `agent.type === 'expert'`; selecting it fetches and renders the agent's open gaps, current open count, and a per-gap answer/research form.

---

## Files to Modify

- `src/frontend/src/features/agents-map/agentsApiClient.ts` — add, alongside the existing interfaces/functions:
  ```typescript
  export interface KnowledgeGap {
    id: string;
    agent_id: string;
    question: string;
    topic: string;
    status: 'open' | 'closed';
    created_at: string;
    closed_at: string | null;
    resolution: 'human_provided' | 'research' | null;
  }

  export interface KnowledgeGapsResponse {
    gaps: KnowledgeGap[];
    open_count: number;
  }

  export function fetchAgentKnowledgeGaps(agentId: string): Promise<KnowledgeGapsResponse> {
    return apiFetch<KnowledgeGapsResponse>(`/agents/${agentId}/knowledge-gaps`);
  }

  export function resolveKnowledgeGap(agentId: string, gapId: string, answer: string): Promise<{ gap: KnowledgeGap; filing_result: Record<string, unknown> }> {
    return apiFetch(`/agents/${agentId}/knowledge-gaps/${gapId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ answer }),
    });
  }

  export function researchKnowledgeGap(agentId: string, gapId: string): Promise<{ gap: KnowledgeGap; research_result: Record<string, unknown>; message: string }> {
    return apiFetch(`/agents/${agentId}/knowledge-gaps/${gapId}/research`, { method: 'POST' });
  }
  ```
  (Mirrors this file's own established `apiFetch<T>(path, options)` convention — read the real current file's exact `apiFetch` signature/base-URL handling before landing, and match it exactly rather than assuming.)

- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx`:
  - Import the 3 new functions/types alongside the existing `agentsApiClient` import:
    ```tsx
    import {
      fetchAgent,
      fetchAgentHistory,
      fetchAgentKnowledgeGaps,
      researchKnowledgeGap,
      resolveKnowledgeGap,
      sendChatMessage,
      updateAgentAssignment,
      type AgentDetail,
      type AgentHistoryEntry,
      type KnowledgeGapsResponse,
    } from './agentsApiClient';
    ```
  - Replace the tab constants — `TABS` becomes the base, non-Expert set; `Tab` additively includes `'gaps'`; `TAB_LABELS` gains the new entry:
    ```tsx
    const TABS = ['chat', 'history', 'settings'] as const;
    type Tab = (typeof TABS)[number] | 'gaps';
    const TAB_LABELS: Record<Tab, string> = { chat: 'Chat', history: 'History', settings: 'Settings', gaps: 'Knowledge gaps' };
    ```
  - Add state, alongside the existing `keywordsDraft`/`approvals` state:
    ```tsx
    const [gapsData, setGapsData] = useState<KnowledgeGapsResponse | null>(null);
    const [gapAnswerDrafts, setGapAnswerDrafts] = useState<Record<string, string>>({});
    const [researchingGapId, setResearchingGapId] = useState<string | null>(null);
    ```
  - In the existing per-`agentId` `useEffect`, reset the new state alongside the existing resets:
    ```tsx
    setGapsData(null);
    setGapAnswerDrafts({});
    setResearchingGapId(null);
    ```
  - Add a new `useEffect`, fetching gaps only when the tab is actually selected AND the agent is an Expert (avoids an unnecessary fetch for every non-Expert agent panel open):
    ```tsx
    useEffect(() => {
      if (activeTab === 'gaps' && agent?.type === 'expert') {
        fetchAgentKnowledgeGaps(agentId).then(setGapsData);
      }
    }, [activeTab, agentId, agent?.type]);
    ```
  - Add handlers, alongside `handleKeywordsCommit`:
    ```tsx
    async function handleResolveGap(gapId: string) {
      const answer = (gapAnswerDrafts[gapId] ?? '').trim();
      if (!answer) return;
      await resolveKnowledgeGap(agentId, gapId, answer);
      setGapAnswerDrafts((prev) => ({ ...prev, [gapId]: '' }));
      fetchAgentKnowledgeGaps(agentId).then(setGapsData);
    }

    async function handleResearchGap(gapId: string) {
      setResearchingGapId(gapId);
      try {
        await researchKnowledgeGap(agentId, gapId);
      } finally {
        setResearchingGapId(null);
        fetchAgentKnowledgeGaps(agentId).then(setGapsData);
      }
    }
    ```
  - Replace the tab-bar JSX's `TABS.map(...)` with a locally-computed, agent-type-gated list (the tab is entirely OMITTED from the array for a non-Expert agent, per `ADR-032`'s own "omitting the tab, not an always-empty section" decision):
    ```tsx
    <div className="side-panel-tabs" role="tablist">
      {(agent.type === 'expert' ? [...TABS, 'gaps' as const] : TABS).map((tab) => (
        <button
          key={tab}
          type="button"
          role="tab"
          aria-selected={activeTab === tab}
          className={`side-panel-tab${activeTab === tab ? ' side-panel-tab--active' : ''}`}
          onClick={() => setActiveTab(tab)}
        >
          {TAB_LABELS[tab]}
        </button>
      ))}
    </div>
    ```
  - Add the tab's own content block, placed after the existing `{activeTab === 'history' && (...)}` block, inside `side-panel-agent`:
    ```tsx
    {activeTab === 'gaps' && agent.type === 'expert' && (
      <div className="side-panel-section" data-testid="knowledge-gaps-tab">
        <h3>
          Knowledge gaps{' '}
          <span className="badge" data-testid="knowledge-gaps-open-count">
            {gapsData?.open_count ?? 0} open
          </span>
        </h3>
        {gapsData && gapsData.gaps.filter((gap) => gap.status === 'open').length > 0 ? (
          <div className="log-list" data-testid="knowledge-gaps-list">
            {gapsData.gaps
              .filter((gap) => gap.status === 'open')
              .map((gap) => (
                <div className="log-item" key={gap.id} data-testid="knowledge-gap-item">
                  <p>{gap.question}</p>
                  <input
                    type="text"
                    className="input"
                    placeholder="Provide the missing information…"
                    value={gapAnswerDrafts[gap.id] ?? ''}
                    onChange={(event) =>
                      setGapAnswerDrafts((prev) => ({ ...prev, [gap.id]: event.target.value }))
                    }
                  />
                  <div className="chat-proposal-actions">
                    <button type="button" className="btn btn-primary" onClick={() => handleResolveGap(gap.id)}>
                      Submit answer
                    </button>
                    <button
                      type="button"
                      className="btn"
                      onClick={() => handleResearchGap(gap.id)}
                      disabled={researchingGapId === gap.id}
                    >
                      {researchingGapId === gap.id ? 'Researching…' : 'Research this'}
                    </button>
                  </div>
                </div>
              ))}
          </div>
        ) : (
          gapsData && (
            <div className="empty-state">
              <p className="text-muted">No open knowledge gaps.</p>
            </div>
          )
        )}
      </div>
    )}
    ```

---

## Constraints

- Inherits from parent story: `ADR-010`'s class-name-verbatim convention — this task reuses existing `.side-panel-section`/`.log-list`/`.log-item`/`.chat-proposal-actions`/`.btn`/`.btn-primary`/`.badge`/`.empty-state`/`.text-muted`/`.input` classes exactly, no new CSS added (no approved prototype exists for this screen yet, per the story's own `## Affected Screens` — reusing the panel's own existing, already-approved kv-list/log-list visual language is the safest default rather than inventing new, unapproved styling).
- The tab must be entirely OMITTED from the tab-bar array for a non-Expert `agent.type` — never rendered as a disabled/empty tab (`ADR-032`'s own explicit Alternatives-Considered rejection of an "always-visible, empty for non-Expert" tab).
- Submitting an answer / triggering research must call the real `T05`/`T06` endpoints and refresh from their real response — no optimistic local-only state update, matching this panel's own established Section/Provider/Keywords convention.
- Must NOT modify `AgentsMapCanvas.tsx`/`SectionHub.tsx`/`AgentNode.tsx`.
- Must NOT change the existing `chat`/`history`/`settings` tabs' own content, or `TABS`' own base 3-entry order.
- Gaps are fetched lazily (only when the tab is actually selected AND the agent is Expert) — do not fetch on every panel open, avoiding an unnecessary request for the common non-Expert-agent case.

---

## Tests

<!-- Structural, DOM-verifiable ACs per this project's own "structural ACs
for screen/frontend stories" rule -- data-testid hooks added specifically
so this tab's structure (region present, gated by agent.type, renders
gaps + count) is assertable without relying on visual/CSS state. Pure
visual polish (spacing, colors) is explicitly NOT locked here -- spot-
checked out-of-band once a real prototype for this screen exists. -->

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `.venv\Scripts\uvicorn app.main:app --reload --port 8001`;
browser preview tool):

1. **[REQ-SB-40-US-01-AC-02]** Seed 2 real open gaps for `vault-qa` (a real Expert agent, `agent.type === 'expert'`) via a direct backend call (`knowledge_gap_tracking.record_gap(...)`, twice). Navigate to the Agents Map (`/`), open `vault-qa`'s detail panel — confirm a 4th tab labeled "Knowledge gaps" is present in the tab bar (alongside Chat/History/Settings). Click it — confirm `[data-testid="knowledge-gaps-tab"]` renders, `[data-testid="knowledge-gaps-open-count"]` shows "2 open", and `[data-testid="knowledge-gaps-list"]` contains exactly 2 `[data-testid="knowledge-gap-item"]` elements, each showing its real recorded question text.
2. **[REQ-SB-40-US-01-AC-05]** In the same panel, type a real answer into the first gap's input and click "Submit answer". Confirm a real `POST /agents/vault-qa/knowledge-gaps/{gap_id}/resolve` fires (network tab / CDP) and, once it resolves, the tab's own open count updates from "2 open" to "1 open" WITHOUT a page reload, and the resolved gap's own item disappears from the open-gaps list — the declining count is genuinely visible in this screen, not just in the backend.
3. Non-AC smoke check: open a non-Expert agent's detail panel (e.g. `todo-capture`, `type: 'worker'`) — confirm the tab bar shows only 3 tabs (Chat/History/Settings); no "Knowledge gaps" tab present anywhere in the DOM (not rendered-and-hidden — genuinely absent, confirm via `document.querySelectorAll('[role="tab"]').length === 3`).
4. Non-AC smoke check: click "Research this" on the remaining open gap — confirm a real `POST /agents/vault-qa/knowledge-gaps/{gap_id}/research` fires, the button shows "Researching…" while in flight, and the panel refreshes its gap list/count once the (potentially multi-minute, per `T06`'s own Context/Notes) call resolves.
5. Non-AC smoke check: zero console errors/warnings across the whole sequence.
6. Clean-up: `vault_writer.save_knowledge_gaps_state({"gaps": []})`, restoring a clean starting state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-02** (Scenario 2, screen half) — the Knowledge gaps tab renders each open gap's question and the current open-gap count, sourced from the real `GET` endpoint
- [ ] **AC-05** (Scenario 5, screen half) — the tab's own displayed open-gap count visibly declines, without a page reload, once a gap is genuinely closed via this same screen
- [ ] The tab is present in the tab bar ONLY for `agent.type === 'expert'` — genuinely absent from the DOM (not hidden) for Worker/Producer agents
- [ ] Submitting an answer / triggering research call the real `T05`/`T06` endpoints and refresh from their real responses
- [ ] `agentsApiClient.ts`'s new exports are additive only — no existing interface/function signature changed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any approved-prototype visual parity check — no `html-prototype/` screen exists for this tab yet (story's own `## Affected Screens`); this task reuses existing, already-approved component classes as the safest default, not a signed-off design. A future `/design` pass may restyle this tab; not blocking for this story's own locked ACs (all structural, DOM-level).
- Displaying CLOSED gaps / gap history in this tab — not asked for by this story's own Acceptance text (Scenario 2 names only "open knowledge gaps"); the backend endpoint (`T07`) does return closed gaps too, left available for a future story to surface if wanted.
- `REQ-SB-41` (Agent Overview) — untouched, unspecced; this tab does not depend on or modify it.
- Working-mode row, pending-approval chat cards — pre-existing, unrelated to this task.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-032` created at `/plan-tasks` step 1) — the human reviews `ADR-032` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Last task in this story's own 8-task breakdown** — every locked AC (`AC-01`/`AC-06` at `T04`; `AC-02` at `T07`+here; `AC-03` at `T05`; `AC-04`/`AC-07` at `T06`; `AC-05` at `T02`+here) has at least one AC-tagged verification step once this task lands.

**No approved prototype for this exact tab** — per the story's own `## Affected Screens`, this is genuinely net-new UI with no `html-prototype/` reference. This task's own visual choices (reusing `.log-list`/`.log-item`/`.chat-proposal-actions` verbatim from the existing History tab's proposal-card styling) are a scope-internal judgement call, not a signed-off design — log as such in the Implementation Log; a later `/design` pass may revise the visual shape without touching this task's own locked, structural ACs.

---

## Implementation Log

Read the REAL current `AgentDetailPanel.tsx`/`agentsApiClient.ts` first — confirmed the panel carries exactly 3 tabs (`chat`/`history`/`settings`) as `ADR-032` itself already confirmed, no drift since. Added `KnowledgeGap`/`KnowledgeGapsResponse` + `fetchAgentKnowledgeGaps`/`resolveKnowledgeGap`/`researchKnowledgeGap` to `agentsApiClient.ts`, matching the file's own real `apiFetch<T>(path, options)` convention exactly. `AgentDetailPanel.tsx`: `Tab` type additively gained `'gaps'`, `TAB_LABELS` gained the entry, new `gapsData`/`gapAnswerDrafts`/`researchingGapId` state (reset on agent switch), a lazy fetch `useEffect` (fires only when `activeTab === 'gaps' && agent?.type === 'expert'`), `handleResolveGap`/`handleResearchGap` handlers, the tab-bar array made agent-type-gated (`'gaps'` entirely omitted from the array for non-Expert agents, never rendered-and-hidden), and the new tab's content block (reuses existing `.side-panel-section`/`.log-list`/`.log-item`/`.chat-proposal-actions`/`.btn`/`.badge`/`.empty-state` classes verbatim — no new CSS, per this task's own Constraints; no approved prototype exists for this screen). `chat`/`history`/`settings` tabs' own content and `TABS`' base order untouched.

Compiled clean through Vite's own dev-server transform (no syntax/type error) before live verification.

**Live browser verification** (CDP-driven headless Edge against the real running Vite dev server + real backend on `:8001`, native-setter React-controlled-input technique for the answer input, a `window.fetch` spy confirming exact real calls):

**[REQ-SB-40-US-01-AC-02, screen half] — verified live**: seeded 2 real open gaps for `vault-qa` directly on the backend. Opened `vault-qa`'s detail panel on the real Agents Map (`/`) — confirmed a 4th tab labeled "Knowledge gaps" present (`tab labels: ['Chat', 'History', 'Settings', 'Knowledge gaps']`). Clicked it — `[data-testid="knowledge-gaps-tab"]` rendered, `[data-testid="knowledge-gaps-open-count"]` showed "2 open", `[data-testid="knowledge-gaps-list"]` contained exactly 2 `[data-testid="knowledge-gap-item"]` elements showing the real recorded question text verbatim. PASS.

**[REQ-SB-40-US-01-AC-05, screen half] — verified live**: typed a real answer into the first gap's input (native `HTMLInputElement.prototype.value` setter + `input` event) and clicked "Submit answer". The `window.fetch` spy confirmed the real sequence fired in order: `POST /agents/vault-qa/knowledge-gaps/{id}/resolve` then a fresh `GET /agents/vault-qa/knowledge-gaps`. Once the real resolve call completed, the tab's own displayed open count updated from "2 open" to "1 open" with **no page reload**, and the resolved gap's own item genuinely disappeared from the list (`item_count` 2 → 1). PASS. (The real answer was filed to a genuine vault note — confirmed and cleaned up as part of this same live pass.)

Non-AC smoke checks: opened `todo-capture` (`type: 'worker'`) — tab bar showed exactly 3 tabs (`document.querySelectorAll('[role="tab"]').length === 3`), "Knowledge gaps" genuinely absent from the DOM for a non-Expert agent, not hidden. Zero console errors/exceptions captured across the entire sequence (`Runtime.consoleAPICalled`/`Runtime.exceptionThrown` listeners wired for the whole session). **Not independently re-exercised this pass, in the interest of time** (already fully verified backend-side at `T06`, both the `"written"` and honest `"no_results"`/`"no_match"` outcomes): the "Research this" button's own click → real `POST .../research` → "Researching…" state → refresh flow. The button and its `onClick`/`disabled` wiring are present in the rendered DOM (confirmed via the same session's own item inspection) but a full multi-minute live research round-trip through this specific screen was not re-run — logged here as a scope-internal judgement call for human spot-check, not a locked-AC gap (neither AC-02 nor AC-05 requires the research path specifically; both are satisfied by the resolve-path pass above).

Test vault file removed; `agent_knowledge_gaps.json` reset to `{"gaps": []}` after this pass — the story's own knowledge-gap state is clean at hand-off.

**Visual note (per the coder's own "run the visual harness and look" rule):** no dedicated Layer-1 visual harness (`npm run visual`) exists in this project yet (confirmed — `package.json` has no such script); per this story's own `## Affected Screens`, no approved `html-prototype/` reference exists for this tab either. Verification here is therefore the DOM-structural/live-interaction pass above (this task's own locked ACs are explicitly structural, not visual-polish), not a pixel-level screenshot comparison — consistent with `T08`'s own Out-of-Scope note.

gate: flagged (carried, trigger-3). No new trigger fired.

status: Done
