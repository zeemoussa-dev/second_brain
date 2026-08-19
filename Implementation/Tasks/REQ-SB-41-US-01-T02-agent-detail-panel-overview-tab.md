---
id: REQ-SB-41-US-01-T02
title: AgentDetailPanel.tsx — new Overview default-landing tab (Purpose/Guardrails/Working-mode/Scope + Expert-only gap count)
parent_story: REQ-SB-41-US-01
requirement_id: REQ-SB-41
type: frontend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-033 created) — carried from the parent story; the human reviews ADR-033 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-41-US-01-T01, REQ-SB-40-US-01-T08, REQ-SB-29-US-01-T05]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-41-US-01-T02 — `AgentDetailPanel.tsx` Overview tab

## Parent Story

- Story: [[REQ-SB-41-US-01]] — `../UserStories/REQ-SB-41-US-01-agent-overview-surface.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-41 *Agent Overview Surface*

---

## Objective

Make Overview `AgentDetailPanel.tsx`'s new default-landing tab (`TABS` gains `'overview'`, first; `activeTab` no longer defaults to `'chat'`), rendering the agent's Purpose, Guardrails statement, Working mode, and Vault Scope (real value or honest "not assigned" state), plus — for Expert-type agents only — a one-line open-knowledge-gap count linking into the existing Gaps tab. Chat remains one click away, fully unmodified (`ADR-033`).

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed the 7-agent Purpose backfill in `agent_registry.py`.
- `REQ-SB-40-US-01-T08` (a sibling, already-`Ready` task on a different story) has landed a conditionally-rendered `'gaps'` tab: base `TABS = ['chat', 'history', 'settings']`, `type Tab = (typeof TABS)[number] | 'gaps'`, `TAB_LABELS` gains `gaps: 'Knowledge gaps'`, the tab bar computes `(agent.type === 'expert' ? [...TABS, 'gaps' as const] : TABS)`, and `agentsApiClient.ts` carries `fetchAgentKnowledgeGaps`/`KnowledgeGapsResponse`/`KnowledgeGap` (see that task file for the exact shape). **Read the real current file before diffing** — do not assume this task's own "before" sample still matches byte-for-byte; compose this task's diff around whatever `T08` actually landed.
- `REQ-SB-29-US-01-T05` (a sibling, already-`Ready` task on a different story) has landed `AgentDetail.scope: string[]` on `agentsApiClient.ts`'s interface, and a "Vault scope" kv-row on the Settings tab. This task's own Overview Scope region reads the same `agent.scope` field — read-only here, does not duplicate or replace the Settings tab's own editable row.
- Real current `AgentDetailPanel.tsx` tab machinery, before `T08`/`T05` land (reproduced for reference only — the coder composes around the REAL current file, which will already include `T08`'s and `T05`'s own landed diffs by the time this task builds, per its own `depends_on`):
  ```tsx
  const TABS = ['chat', 'history', 'settings'] as const;
  type Tab = (typeof TABS)[number];
  const TAB_LABELS: Record<Tab, string> = { chat: 'Chat', history: 'History', settings: 'Settings' };
  // ...
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  // ...
  useEffect(() => {
    setAgent(null);
    // ...
    setActiveTab('chat');
    // ...
  }, [agentId]);
  ```

**After / Outputs:**
- `AgentDetailPanel.tsx`'s tab bar renders `'overview'` first, ahead of `chat`/`history`/`settings`(/`gaps`); `activeTab`'s initial and per-agent-reset value is `'overview'`.
- A new Overview tab content block renders 4 regions (Purpose, Working mode, Guardrails, Vault scope) plus, for `agent.type === 'expert'` only, a one-line "Open knowledge gaps: N" summary with a button that switches `activeTab` to `'gaps'`, and a "Chat with `<name>`" affordance that switches `activeTab` to `'chat'`.

---

## Files to Modify

- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx`:
  - Extend the existing `agentsApiClient` import to include the Overview's own dependencies (alongside whatever `T08`/`T05` already added):
    ```tsx
    import {
      fetchAgent,
      fetchAgentHistory,
      fetchAgentKnowledgeGaps,
      sendChatMessage,
      updateAgentAssignment,
      type AgentDetail,
      type AgentHistoryEntry,
      type KnowledgeGapsResponse,
      // ...whatever T08/T05 already imported (resolveKnowledgeGap, researchKnowledgeGap, etc.)
    } from './agentsApiClient';
    ```
  - Change the base `TABS` constant to add `'overview'` first — this is the ONLY edit to the `TABS`/`Tab`/`TAB_LABELS` declarations; `T08`'s own `'gaps'` handling (the `(typeof TABS)[number] | 'gaps'` union and the `[...TABS, 'gaps']` tab-bar computation) is untouched and cascades automatically once `'overview'` is in the base array:
    ```tsx
    const TABS = ['overview', 'chat', 'history', 'settings'] as const;
    type Tab = (typeof TABS)[number] | 'gaps'; // unchanged from T08 — only the base TABS array above changed
    const TAB_LABELS: Record<Tab, string> = {
      overview: 'Overview',
      chat: 'Chat',
      history: 'History',
      settings: 'Settings',
      gaps: 'Knowledge gaps', // unchanged from T08
    };
    ```
  - Change `activeTab`'s initial state:
    ```tsx
    const [activeTab, setActiveTab] = useState<Tab>('overview');
    ```
  - Add gap-count state for the Overview's own composed reads, alongside whatever `T08` already added (`gapsData`/`setGapsData` — reuse that exact state, do not add a second, parallel piece of state):
    ```tsx
    // gapsData/setGapsData already declared by T08 — reused here, not redeclared.
    ```
  - In the existing per-`agentId` `useEffect`, change the reset value from `'chat'` to `'overview'` (alongside whatever `T08`/`T05` already added to this same effect):
    ```tsx
    setActiveTab('overview'); // was 'chat'
    ```
  - Add a new `useEffect`, fetching gaps for the Overview's own gap-count line (mirrors `T08`'s own `'gaps'`-tab effect, triggered on `'overview'` instead — both effects coexist, each fetching only when its own tab is actually active):
    ```tsx
    useEffect(() => {
      if (activeTab === 'overview' && agent?.type === 'expert') {
        fetchAgentKnowledgeGaps(agentId).then(setGapsData);
      }
    }, [activeTab, agentId, agent?.type]);
    ```
  - Add a small module-level helper, alongside the component (or inline where used — coder's own latitude):
    ```tsx
    function getAgentPurpose(agent: AgentDetail): string {
      const purposeEntry = agent.settings.find((row) => row.key === 'Purpose');
      if (purposeEntry) return purposeEntry.value;
      const domainEntry = agent.settings.find((row) => row.key === 'Domain');
      if (domainEntry) return domainEntry.value;
      return 'No stated purpose recorded for this agent.';
    }

    const WORKING_MODE_LABELS: Record<AgentDetail['working_mode'], string> = {
      autonomous: 'Autonomous',
      supervised: 'Supervised',
      manual: 'Manual',
    };

    const GUARDRAILS_STATEMENT =
      "Replies are grounded in what this agent's own tools actually find in the vault — it honestly says it doesn't know rather than guessing.";
    ```
  - Add the tab's own content block, placed as the FIRST conditional block inside `side-panel-agent` (ahead of the existing `settings`/`chat`/`history` blocks — order in the JSX has no behavioral effect, but mirrors `'overview'`'s own first position in `TABS`):
    ```tsx
    {activeTab === 'overview' && (
      <div className="side-panel-section" data-testid="agent-overview-tab">
        <h3>Overview</h3>
        <div className="kv-list">
          <div className="kv-row" data-testid="overview-purpose">
            <span className="kv-key">Purpose</span>
            <span>{getAgentPurpose(agent)}</span>
          </div>
          <div className="kv-row" data-testid="overview-working-mode">
            <span className="kv-key">Working mode</span>
            <span>{WORKING_MODE_LABELS[agent.working_mode]}</span>
          </div>
          <div className="kv-row" data-testid="overview-guardrails">
            <span className="kv-key">Guardrails</span>
            <span>{GUARDRAILS_STATEMENT}</span>
          </div>
          <div className="kv-row" data-testid="overview-scope">
            <span className="kv-key">Vault scope</span>
            <span>{agent.scope.length > 0 ? agent.scope.join(', ') : 'No vault scope assigned yet'}</span>
          </div>
        </div>
        {agent.type === 'expert' && (
          <p className="text-muted" data-testid="overview-gap-count">
            Open knowledge gaps: {gapsData?.open_count ?? 0}{' '}
            <button type="button" className="btn" onClick={() => setActiveTab('gaps')} data-testid="overview-gap-count-link">
              View
            </button>
          </p>
        )}
        <div className="side-panel-section-actions">
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setActiveTab('chat')}
            data-testid="overview-chat-link"
          >
            Chat with {agent.name}
          </button>
        </div>
      </div>
    )}
    ```

---

## Constraints

- Inherits from parent story and `ADR-033` in full.
- `ADR-010`'s class-name-verbatim convention — reuse existing `.side-panel-section`/`.kv-list`/`.kv-row`/`.kv-key`/`.text-muted`/`.btn`/`.btn-primary` classes exactly; no new CSS added (no approved prototype exists for this screen, per the story's own `## Affected Screens`). `data-testid` hooks are added specifically so this tab's structure is assertable without relying on visual/CSS state, per this project's own "structural ACs for screen/frontend stories" rule.
- **Do not touch `T08`'s own `'gaps'` handling** beyond the base `TABS` array — the `Tab` union, `TAB_LABELS.gaps`, the `[...TABS, 'gaps']` tab-bar computation, the `'gaps'`-tab content block, and `T08`'s own `gapsData`/`gapAnswerDrafts`/`researchingGapId` state and handlers are all untouched; this task reuses `gapsData`/`setGapsData` (already declared by `T08`) rather than redeclaring it.
- **Do not touch `T05`'s own "Vault scope" Settings kv-row** — this task's own Scope region is a read-only display of the same `agent.scope` field on the Overview tab; it does not add editing, and does not remove or relocate the Settings tab's own editable row.
- The Overview's own gap-count fetch must be lazy — only when `activeTab === 'overview'` AND `agent.type === 'expert'` — mirroring `T08`'s own established "don't fetch for every non-Expert panel open" convention.
- Guardrails copy is a static string, identical for every agent — no per-agent variation, no new field, no new endpoint (`ADR-033` point 4 / the story's own Constraints).
- Purpose must never be fabricated or derived from Skills/Scope/Actions at display time — read `settings` only (`"Purpose"` then `"Domain"`), falling back to the honest "No stated purpose recorded for this agent." string.
- Must NOT modify `AgentsMapCanvas.tsx`/`SectionHub.tsx`/`AgentNode.tsx`.
- Must NOT change the existing `chat`/`history`/`settings` tabs' own content or behavior (Scenario 7's regression guard) — this task only changes `TABS`' order/default-selection and adds the new `'overview'` content block.

---

## Tests

<!-- Structural, DOM-verifiable ACs per this project's own "structural ACs
for screen/frontend stories" rule -- data-testid hooks added specifically
so this tab's structure (region present, correct content sourced from the
real GET /agents/{agent_id} response, gap-count gated by agent.type) is
assertable without relying on visual/CSS state. Pure visual polish (spacing,
colors) is explicitly NOT locked here -- spot-checked out-of-band once a
real prototype for this screen exists (no `html-prototype/` coverage today,
per the story's own `## Affected Screens`). -->

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `.venv\Scripts\uvicorn app.main:app --reload --port 8001`;
browser preview tool):

1. **[REQ-SB-41-US-01-AC-01]** Navigate to the Agents Map (`/`), open any agent's detail panel (e.g. `vault-qa`). Confirm the panel opens with `[data-testid="agent-overview-tab"]` already rendered and the "Overview" tab marked `aria-selected="true"` in the tab bar — the panel does NOT land on Chat. Confirm the tab bar's first tab is labeled "Overview", ahead of "Chat"/"History"/"Settings". Click `[data-testid="overview-chat-link"]` — confirm `activeTab` switches to Chat (the existing chat thread/input renders) in one click.
2. **[REQ-SB-41-US-01-AC-02]** With `vault-qa`'s Overview open, confirm `[data-testid="overview-purpose"]` shows the real backfilled Purpose text from `T01` ("Answers questions about the vault's contents, grounded in the indexed vault; reachable from this panel and Hermes channels." or `T01`'s own copy-edited equivalent) — not a placeholder, not fabricated. Independently confirm via `GET /agents/vault-qa` that this text matches a real `settings` entry with `"key": "Purpose"`.
3. **[REQ-SB-41-US-01-AC-03]** Still on `vault-qa`'s Overview, confirm `[data-testid="overview-working-mode"]` shows the agent's current working mode (e.g. "Autonomous"). Switch to the Settings tab, change the working mode via its existing `<select>`, switch back to Overview — confirm `[data-testid="overview-working-mode"]` reflects the new value without a page reload.
4. **[REQ-SB-41-US-01-AC-04]** Confirm `[data-testid="overview-guardrails"]` renders the static guardrails statement. Open a second, different agent's panel (e.g. `todo-capture`) — confirm the SAME statement text renders there too (identical for every agent, not per-agent-configurable).
5. **[REQ-SB-41-US-01-AC-05]** Choose an agent and, via its Settings tab's "Vault scope" row (`T05`), assign a real scope value (e.g. `"customer/masdar"`), blur to commit. Switch to Overview — confirm `[data-testid="overview-scope"]` shows `"customer/masdar"`, sourced from the real `GET /agents/{agent_id}` `scope` field (independently confirm via a direct `GET` call). Close and reopen the panel — confirm the assigned scope still renders on Overview (server-side persistence, not local-only state).
6. **[REQ-SB-41-US-01-AC-06]** Open an agent with no assigned scope (a fresh agent, or the same agent reset to `{"scope": []}` via `PATCH`). Confirm `[data-testid="overview-scope"]` shows the honest `"No vault scope assigned yet"` text — the Scope region is present and rendered, never omitted, never showing a fabricated value.
7. Non-AC smoke check (Expert-only gap count): seed 2 real open gaps for `vault-qa` (`knowledge_gap_tracking.record_gap(...)`, twice). Open `vault-qa`'s Overview — confirm `[data-testid="overview-gap-count"]` shows "Open knowledge gaps: 2". Click `[data-testid="overview-gap-count-link"]` — confirm `activeTab` switches to the existing Gaps tab (`T08`'s own content renders, showing the same 2 open gaps). Open a non-Expert agent (e.g. `todo-capture`) — confirm `[data-testid="overview-gap-count"]` is absent entirely from the DOM (not hidden).
8. **[REQ-SB-41-US-01-AC-07]** From any agent's Overview, click through to Chat, send a message, confirm the existing chat behavior (reply rendering, history recording) is unchanged from before this task. Switch to History and Settings tabs — confirm both render their pre-existing content exactly as before (Settings still shows Section/Provider/Working-mode/Keywords/Vault-scope rows and Available actions; History still shows the existing log).
9. Non-AC smoke check: zero console errors/warnings across the whole sequence.
10. Clean-up: `PATCH /agents/<agent-id>` with `{"scope": []}` on any agent given a real scope value during verification, and `vault_writer.save_knowledge_gaps_state({"gaps": []})`, restoring clean state before later verification runs.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-01** (Scenario 1) — the panel opens with Overview selected by default, showing purpose/scope-state/guardrails/working-mode, before landing on Chat; Chat is reachable in one click from the Overview
- [x] **AC-02** (Scenario 2) — the Overview states the agent's purpose, sourced from its real `settings` `"Purpose"`/`"Domain"` entry, or the honest no-purpose-recorded string when neither exists
- [x] **AC-03** (Scenario 3) — the Overview shows the agent's current working mode, reflecting the real, live value
- [x] **AC-04** (Scenario 4) — the Overview states the grounding/guardrail behavior, identical for every agent
- [x] **AC-05** (Scenario 5) — the Overview shows a real assigned Vault Scope value once one exists, sourced from the real `scope` field, surviving a panel close/reopen
- [x] **AC-06** (Scenario 6) — an agent with no assigned scope shows an honest "no scope assigned" state on the Overview, never omitted or fabricated
- [x] **AC-07** (Scenario 7) — Chat, History, and Settings tabs' own content and behavior are unchanged by this task
- [x] The Expert-only gap-count line is present ONLY for `agent.type === 'expert'`, genuinely absent from the DOM (not hidden) otherwise
- [x] `TABS`' only change is the addition of `'overview'`, first in the array — `T08`'s own `'gaps'` handling is untouched
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint — n/a, no new decision/pattern/constraint emerged (composes `ADR-033`'s already-recorded decisions)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any approved-prototype visual parity check — no `html-prototype/` screen exists for this tab yet (story's own `## Affected Screens`); this task reuses existing, already-approved component classes as the safest default, not a signed-off design. A future `/design` pass may restyle this tab; not blocking for this story's own locked ACs (all structural, DOM-level).
- Editing Vault Scope, Working mode, Section, Provider, or Keywords from the Overview tab — all remain Settings-tab-only, read-only here (`T05`'s/the existing rows' own scope, unchanged).
- Any change to the Guardrails behavior itself, or a per-agent Guardrails toggle — `REQ-SB-33`'s own guardrail mechanism is not touched; this task only states it.
- Resolving/researching a knowledge gap from the Overview tab — `T08`'s own Gaps tab remains the only place to act on a gap; the Overview's own gap-count line only links there.
- A new Skills-aware Purpose region — `REQ-SB-39` is unbuilt; Purpose reads only `settings`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-033` created at `/plan-tasks` step 1) — the human reviews `ADR-033` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Shared-file coordination — read before touching `AgentDetailPanel.tsx`/`agentsApiClient.ts`:** both files are actively-extended shared files (`REQ-SB-18/19/20/21/29/40-US-01` have all landed rows/tabs here). This task's own `depends_on` on `REQ-SB-40-US-01-T08` and `REQ-SB-29-US-01-T05` exists specifically because this task's own diff composes directly with theirs in the same file (the base `TABS` array `T08` also touches; the `agent.scope` field `T05` also adds) — build this task AFTER both have landed, and re-read the real current file immediately before applying this task's own diff, per this project's own established Learnings pattern (repeat drift on this exact file has been found live multiple times already).

**Last task in this story's own 2-task breakdown** — every locked AC (`AC-01`–`AC-07`) has its own AC-tagged verification step in this task's `## Tests` block once it lands.

Full reasoning for every navigation/data-source/backfill/gap-count decision: `Implementation/Architecture/ADR.md` → `ADR-033`. Full file-level shape: `Implementation/Architecture/architecture.md` → "Agent Overview surface" (under "My Day & Agent Panel APIs").

---

## Implementation Log

Read the REAL current `AgentDetailPanel.tsx`/`agentsApiClient.ts` first, per this task's own shared-file-coordination note. Confirmed both `T08` (`'gaps'` tab, `gapsData`/`gapAnswerDrafts`/`researchingGapId` state, `fetchAgentKnowledgeGaps`/`KnowledgeGapsResponse` already imported) and `T05` (`AgentDetail.scope: string[]`, the Settings "Vault scope" `kv-row`) had already landed exactly as this task's own `depends_on` anticipated. **One real drift from this task's own "before" sample, noted for transparency, not a blocker:** `REQ-SB-39` (Unify Agent Capabilities Under Skills) has also since landed — `agent.actions`/the "Available actions" block referenced in this task's own Context no longer exist; the real Settings tab now renders `agent.capabilities`/a "Capabilities" block instead. This is out of scope for this task (the Overview's own Purpose region reads only `settings`, never `actions`/`capabilities`, per this task's own Constraints) and required no change to this task's own diff.

Applied exactly the diff this task specifies: `TABS` gained `'overview'` first (`Tab`/`TAB_LABELS.gaps`/the `[...TABS, 'gaps']` tab-bar computation from `T08` untouched beyond that); `activeTab`'s initial state and per-agent-switch reset value changed `'chat'` → `'overview'`; a second lazy `useEffect` added, firing only when `activeTab === 'overview' && agent?.type === 'expert'`, reusing `T08`'s own `gapsData`/`setGapsData` (not redeclared); added `getAgentPurpose`/`WORKING_MODE_LABELS`/`GUARDRAILS_STATEMENT` module-level helpers; added the new Overview content block as the first conditional inside `side-panel-agent`, reusing `.side-panel-section`/`.kv-list`/`.kv-row`/`.kv-key`/`.text-muted`/`.btn`/`.btn-primary` verbatim (no new CSS). No import changes were needed — `fetchAgentKnowledgeGaps`/`KnowledgeGapsResponse`/`updateAgentAssignment`/`AgentDetail` were already imported by `T08`/`T05`; `KnowledgeGap` (this task's own sample import) was not actually referenced anywhere in this task's own code, so it was not added, to avoid an unused-import lint/type warning. `chat`/`history`/`settings` tabs' own content and behavior untouched.

`tsc -b` compiled clean (zero errors) before live verification.

**Live browser verification** (CDP-driven headless Edge, `--headless=new --remote-debugging-port=9333`, against the real running Vite dev server on `:5173` and the real backend on `:8001`; native-setter React-controlled-input technique for the `<select>`/scope `<input>`; `Runtime.consoleAPICalled`/`Runtime.exceptionThrown` listeners wired for the whole session — zero console errors/warnings/exceptions captured):

**[REQ-SB-41-US-01-AC-01] — verified live.** Opened `vault-qa` from the real Agents Map (`data-agent-id="vault-qa"` node click) — panel opened with `[data-testid="agent-overview-tab"]` already rendered, tab bar's first tab labeled "Overview" with `aria-selected="true"`, NOT landing on Chat. Clicked `[data-testid="overview-chat-link"]` — `activeTab` switched to Chat in one click, the real chat thread (`[data-role="agent-chat-thread"]`) rendered. PASS.

**[REQ-SB-41-US-01-AC-02] — verified live**, three agents across three different types (per this project's own spot-check convention): `vault-qa` (Expert) → `"Answers questions about the vault's contents, grounded in the indexed vault; reachable from this panel and Hermes channels."`; `todo-capture` (Worker) → `"Automatically captures Outlook Tasks into the vault on an hourly schedule."`; `people-producer` (Producer) → `"Builds and maintains a person note for every new email sender or meeting attendee, preserving any user-added content."` — all real, distinct, non-placeholder text, independently cross-checked against a direct `GET /agents/{id}` call each. PASS.

**[REQ-SB-41-US-01-AC-03] — verified live.** `vault-qa`'s Overview showed "Autonomous". Switched to Settings, changed the Working mode `<select>` to "Supervised" (native `HTMLSelectElement.prototype.value` setter + `change` event — real `PATCH /agents/vault-qa` fired, confirmed via a direct follow-up `GET` showing `"working_mode": "supervised"`), switched back to Overview (no page reload) — `[data-testid="overview-working-mode"]` read "Supervised", the new live value. Reverted to "Autonomous" as part of clean-up. PASS.

**[REQ-SB-41-US-01-AC-04] — verified live.** `[data-testid="overview-guardrails"]` on `vault-qa` and `[data-testid="overview-guardrails"]` on `todo-capture` (a different agent, different type) both rendered byte-identical text — the static, non-configurable statement. PASS.

**[REQ-SB-41-US-01-AC-05] — verified live.** Assigned a real scope via the Settings "Vault scope" input (native-setter + Fiber-props direct `onBlur` invoke, per this project's own established technique) — `"customer/masdar"`, real `PATCH /agents/vault-qa` confirmed. Closed and reopened the panel (real remount, not a page reload) — `[data-testid="overview-scope"]` showed `"customer/masdar"`, independently confirmed via a direct `GET /agents/vault-qa` returning `"scope": ["customer/masdar"]`. Reset to `[]` as part of clean-up. PASS.

**[REQ-SB-41-US-01-AC-06] — verified live**, on all three spot-checked agents (`vault-qa`/`todo-capture`/`people-producer`, each with no scope assigned): `[data-testid="overview-scope"]` rendered the honest `"No vault scope assigned yet"` text — the region present, never omitted, never fabricated. PASS.

**[REQ-SB-41-US-01-AC-07] — verified live.** From `vault-qa`'s Overview, clicked into Chat and sent a real message — reply rendered, history recorded (unchanged chat behavior). Switched to History — "Communication history" heading + existing log/empty-state rendering, unchanged. Switched to Settings — all pre-existing rows present (`Section`/`Provider`/`Working mode`/`Keywords`/`Vault scope`, plus the now-`REQ-SB-39` "Capabilities" block, itself out of this task's own scope and untouched by this task's diff). PASS.

**Non-AC smoke check (Expert-only gap count, Tests step 7)** — seeded 2 real open gaps for `vault-qa` via `knowledge_gap_tracking.record_gap(...)`. `vault-qa`'s Overview showed `[data-testid="overview-gap-count"]` = "Open knowledge gaps: 2"; clicked `[data-testid="overview-gap-count-link"]` — `activeTab` switched to the existing Gaps tab, `[data-testid="knowledge-gaps-tab"]` rendered with 2 `[data-testid="knowledge-gap-item"]` entries (the same 2 real gaps, `T08`'s own content). Opened `todo-capture` (Worker) and `people-producer` (Producer) — `[data-testid="overview-gap-count"]` genuinely absent from the DOM for both (`querySelector` returned `null`, not a hidden element). Cleaned up: gaps state reset to `{"gaps": []}`, `count_open_gaps("vault-qa")` confirmed back to 0. PASS.

**`TABS`/gap-gating structural checks** — `TABS`' only diff is the `'overview'` addition, first; `T08`'s own `'gaps'` handling (union type, `TAB_LABELS.gaps`, the `[...TABS, 'gaps']` tab-bar computation, the `'gaps'` content block, `gapsData`/`gapAnswerDrafts`/`researchingGapId`) is byte-for-byte untouched. Confirmed via direct diff review before and after this task's own edit.

**Visual note (per the coder's own "run the visual harness and look" rule):** no dedicated Layer-1 visual harness (`npm run visual`) exists in this project yet, and no `html-prototype/` screen covers this tab (per this story's own `## Affected Screens`) — consistent with `T08`'s own precedent, verification here is the DOM-structural/live-interaction pass above (this task's own locked ACs are explicitly structural), not a pixel-level screenshot comparison.

gate: flagged (carried, trigger-3). No new trigger fired.

status: Done
