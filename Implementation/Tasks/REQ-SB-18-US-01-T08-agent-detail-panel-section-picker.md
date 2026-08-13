---
id: REQ-SB-18-US-01-T08
title: AgentDetailPanel.tsx Section picker kv-row + agentsApiClient.ts updateAgentAssignment(section_id)
parent_story: REQ-SB-18-US-01
requirement_id: REQ-SB-18
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-18-US-01-T04, REQ-SB-18-US-01-T06, REQ-SB-18-US-01-T07]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-18-US-01-T08 — AgentDetailPanel.tsx Section picker

## Parent Story

- Story: [[REQ-SB-18-US-01]] — `../UserStories/REQ-SB-18-US-01-dynamic-agent-sections-and-assignment.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-18 *Dynamic Agent Sections & Agent-to-Section Assignment*

---

## Objective

Add a Section `<select class="kv-select">` row to `AgentDetailPanel.tsx`'s
existing Settings `.kv-list`, per the approved `html-prototype/
agents-map.html` side panel, wired to `T04`'s `PATCH /agents/{agent_id}`
— completing the full user journey this story's remaining locked ACs
(reassignment, Type/Section independence, Map reflecting the change)
depend on.

---

## Starting State → End State

**Before / Inputs:**
- `AgentDetailPanel.tsx` (`REQ-SB-13-US-01`) already renders a Settings
  `.kv-list` with rows like `Schedule`/`Vault target`/etc., an Available
  Actions block, Chat, and Communication history — no Section/Provider row
  yet.
- `T04` has landed `GET /agents/{agent_id}`'s `section_id`/`section_name`
  fields and `PATCH /agents/{agent_id}`.
- `T06` has landed the N-generic map rendering; `T07` has landed
  `settingsApiClient.ts`'s `fetchSections`.

**After / Outputs:**
- `agentsApiClient.ts`'s `AgentDetail` interface gains `section_id: string;
  section_name: string;`, and gains `updateAgentAssignment(agentId, {
  section_id?: string }): Promise<AgentDetail>` (`PATCH
  /agents/{agentId}`).
- `AgentDetailPanel.tsx` renders a new `Section` kv-row with a
  `<select class="input kv-select">` populated from `fetchSections()`,
  showing the agent's current section selected; changing it calls
  `updateAgentAssignment` and refreshes the panel's own `agent` state.

---

## Files to Modify

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
  }
  ```
  Add a new function, placed after `fetchAgent`:
  ```typescript
  export function updateAgentAssignment(
    agentId: string,
    body: { section_id?: string },
  ): Promise<AgentDetail> {
    return apiFetch<AgentDetail>(`/agents/${agentId}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  }
  ```
  (`REQ-SB-19-US-01-T06` extends this same function's body type to
  `{ section_id?: string; provider_id?: string }` — that task's own
  `depends_on` names this task explicitly.)

- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` — add
  imports:
  ```tsx
  import { fetchSections, type SectionSummary } from '../settings/settingsApiClient';
  import { updateAgentAssignment } from './agentsApiClient';
  ```
  Add a new piece of state, alongside the existing `agent`/`messages`/etc.
  state:
  ```tsx
  const [sections, setSections] = useState<SectionSummary[] | null>(null);
  ```
  In the existing `useEffect` keyed on `agentId`, add a `fetchSections()`
  call alongside the existing `fetchAgent`/`fetchAgentHistory` calls:
  ```tsx
  useEffect(() => {
    setAgent(null);
    setMessages([]);
    setDraft('');
    setHistory(null);
    fetchAgent(agentId).then(setAgent);
    fetchAgentHistory(agentId).then(setHistory);
    fetchSections().then(setSections);
  }, [agentId]);
  ```
  Add a handler function near `handleSend`:
  ```tsx
  async function handleSectionChange(sectionId: string) {
    const updated = await updateAgentAssignment(agentId, { section_id: sectionId });
    setAgent(updated);
  }
  ```
  In the JSX, inside the existing Settings `.kv-list` block (after the
  `agent.settings.map(...)` rows, still inside the same `<div
  className="kv-list">`), add:
  ```tsx
  <div className="kv-row">
    <span className="kv-key">Section</span>
    {sections && (
      <select
        className="input kv-select"
        value={agent.section_id}
        onChange={(event) => handleSectionChange(event.target.value)}
      >
        {sections.map((section) => (
          <option key={section.id} value={section.id}>{section.name}</option>
        ))}
      </select>
    )}
  </div>
  ```

- `src/frontend/src/styles/settings.css` (or `agent-panel.css` — add
  wherever `.kv-select` most naturally sits alongside the existing
  `.kv-list`/`.kv-row`/`.kv-key` rules already in `settings.css`) — append,
  ported verbatim from `html-prototype/styles.css`:
  ```css
  .kv-select { width: auto; min-width: 160px; padding: 2px var(--space-2); font-size: var(--font-size-sm); }
  ```

---

## Constraints

- Inherits from parent story: `ADR-010`'s class-name-verbatim convention
  (`.kv-row`, `.kv-key`, `.kv-select` matching `html-prototype/
  agents-map.html`'s side panel shape exactly); `AgentDetailPanel.tsx`'s
  existing "clear stale content on agent switch" contract
  (`REQ-SB-13-US-01`) — the new `sections` fetch must follow the same
  per-`agentId`-switch refetch pattern as the existing `agent`/`history`
  fetches (it does not need to be cleared to `null` on switch, since the
  section *list* itself is agent-independent — only the *selected* value
  changes per agent, which `agent.section_id` already handles).
- Changing the Section `<select>` must call the real `PATCH
  /agents/{agentId}` and update from its real response — no optimistic
  local-only state update.
- Must NOT modify `AgentsMapCanvas.tsx`/`SectionHub.tsx`'s own rendering
  (already landed by `T06`) or `AgentNode.tsx`'s ring-placement logic —
  this task only adds the panel's picker row.
- Must NOT add a Provider row here — `REQ-SB-19-US-01-T06`'s own scope.

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `.venv\Scripts\uvicorn app.main:app --reload --port 8001`;
browser preview tool):

1. **[REQ-SB-18-US-01-AC-02]** Via Settings' Sections card (`T07`), create
   a new section (e.g. "Verify-T08"). Navigate to the Agents Map (`/`),
   click any `.agent-node` to open its detail panel. Confirm the panel's
   Section `<select>` now includes "Verify-T08" as one of its `<option>`s
   — the newly created section is available as a picker choice, completing
   the scenario `T07` began. Do not select it (leave the agent's
   assignment unchanged) — this step only confirms availability. Delete
   "Verify-T08" via Settings afterward (zero agents ever assigned to it).
2. **[REQ-SB-18-US-01-AC-06]** With the panel still open on an agent
   currently assigned to `Technical` (the seed default), confirm the
   Section `<select>`'s selected `<option>` is "Technical". Pick "Sales"
   from the dropdown. Confirm the panel's own state updates (the
   `<select>`'s selected value becomes "Sales" without a page reload);
   reopen the panel (close, click the same agent again) and confirm
   "Sales" is still selected — the assignment persisted server-side, not
   just in local component state.
3. **[REQ-SB-18-US-01-AC-07]** On the same agent (now assigned to
   "Sales"), confirm the panel's header badge still shows its original
   Type (e.g. `worker`) — unchanged by the Section reassignment. Navigate
   to the Agents Map and confirm the agent still renders on the same ring
   band it always has (same `agent-node--{type}` class as before this
   story), now clustered near the "Sales" hub instead of "Technical"'s.
   Confirm "Sales"'s hub, on the map, is not exclusively `worker`-typed —
   if a `producer`- or `expert`-typed agent is also reassigned there (or
   already present), it renders under the same hub without issue (a
   Section may hold agents of any Type).
4. **[REQ-SB-18-US-01-AC-09]** With the reassignment from step 2 already
   done (agent moved from Technical to Sales), load `/` (Agents Map)
   fresh. Confirm the agent is grouped under Sales's hub (cluster-lines
   connect it to Sales's `.hub-node`, not Technical's) — no code change or
   restart was needed, this is the real backend state `T04`'s `PATCH`
   persisted.
5. Clean-up: reassign the agent used in steps 2–4 back to "Technical" via
   the panel, so `.second-brain/agent_sections.json` is restored to the
   clean seed state for any later verification.
6. Non-AC smoke check: zero console errors/warnings across the whole
   sequence.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-02** (Scenario 2, completing `T07`'s check) — a newly created
      section is available as a choice on the Agent Settings surface's
      Section picker
- [ ] **AC-06** (Scenario 5) — picking a different section updates the
      agent's assignment, persisted server-side
- [ ] **AC-07** (Scenario 6) — reassigning Section never changes Type or
      ring placement; a Section may hold agents of any Type
- [ ] **AC-09** (Scenario 8) — the Agents Map reflects an agent's
      just-changed section assignment without a code change/restart
- [ ] `agentsApiClient.ts`'s `AgentDetail`/`updateAgentAssignment` additive
      only — no existing field/function signature changed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Provider picker row, `has_real_client` UI messaging — `REQ-SB-19-US-01-T06`.
- Wiring the Available Actions buttons — pre-existing out-of-scope carve-out
  from `REQ-SB-13-US-01-T06`, unaffected by this task.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-014` created at
`/plan-tasks` step 1) — the human reviews `ADR-014` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

**Shared-file coordination (read before touching these files):**
`AgentDetailPanel.tsx` and `agentsApiClient.ts` are edited by two sibling
stories' tasks this sprint — this task (Section portion) and
`REQ-SB-19-US-01-T06` (Provider portion, `depends_on: [...,
REQ-SB-18-US-01-T08]`). This task must land and be `Done` first; the other
task's own spec shows the exact diff it applies on top of this task's
already-landed code (adding a second `<select>` kv-row, extending
`AgentDetail` with `provider_*` fields, and widening
`updateAgentAssignment`'s body type to include `provider_id`). Do not
attempt to pre-build any Provider-related field or row here.

This task is the natural integration point for `AC-06`/`AC-07`/`AC-09`
(rather than a separate end-to-end verification task, per
`REQ-SB-12-US-01-T04`'s precedent) because it is the last task in this
story's own dependency chain that touches both the panel (reassignment)
and, transitively via `T06`'s already-landed rendering, the map (reflected
change) — no further integration task is needed.

---

## Implementation Log

**2026-08-11 — Done.** `agentsApiClient.ts`'s `AgentDetail` gained
`section_id`/`section_name`; added `updateAgentAssignment(agentId, {
section_id? })`. `AgentDetailPanel.tsx` gained the `sections` state (fetched
alongside `agent`/`history` in the existing per-`agentId` `useEffect`), the
`handleSectionChange` handler, and the new `Section` `<select
class="input kv-select">` kv-row inside the existing Settings `.kv-list` —
all per the task's own code blocks verbatim. `.kv-select` CSS rule was
already present in `settings.css` (added by `T07`'s own pass, since it's
part of the identical prototype CSS block) — not duplicated.

Live verification (real backend `:8001`, real frontend `npm run dev`
`:5173`, headless-Chrome-via-CDP):
- **[REQ-SB-18-US-01-AC-02]** Created "Verify-T08" via Settings' Sections
  card, navigated to the Agents Map, opened `email-capture`'s panel —
  confirmed the Section `<select>`'s options included `{"value":
  "verify-t08", "text": "Verify-T08"}` alongside the 5 seed sections,
  without selecting it. Deleted "Verify-T08" afterward (0 agents ever
  assigned).
- **[REQ-SB-18-US-01-AC-06]** Opened `email-capture`'s panel — confirmed
  selected option `"technical"`. Changed the `<select>` to `"sales"` (a
  real `change` event, not a raw API call) — confirmed the `<select>`'s
  value updated to `"sales"` without a page reload. Closed and reopened
  the same agent's panel — confirmed `"sales"` was still selected,
  proving server-side persistence (`GET /agents/email-capture` also
  confirmed `section_id: "sales"` directly).
- **[REQ-SB-18-US-01-AC-07]** The panel's header Type badge read `worker`
  both before and after the Section change — unchanged. Also reassigned
  `vault-qa` (Type `expert`) to `"sales"` via the same picker — confirmed
  a Section can hold agents of more than one Type. After a fresh page
  load, both agents kept their original ring-placement classes
  (`agent-node--worker` for `email-capture`, `agent-node--expert` for
  `vault-qa`) — Section reassignment never touched ring/Type.
- **[REQ-SB-18-US-01-AC-09]** With `email-capture` and `vault-qa` both
  reassigned to Sales, a fresh `/` load showed `.cluster-line` count drop
  from 15 (all 5 agents under Technical) to 9 (`Technical`'s remaining 3
  agents: `C(3,2)+3=6`; `Sales`'s 2 agents: `C(2,2)+2=3`; `6+3=9`) — the
  map reflects the just-changed assignment with no code change/restart,
  confirmed both by DOM topology and a direct `GET /agents` cross-check
  (`section_id: "sales"` for both).
- Clean-up: `PATCH` both agents back to `"technical"` — `GET /agents`/`GET
  /sections` confirmed the full clean seed state restored (all 5 agents on
  Technical, all 5 sections present with correct slug ids).
- Zero console errors/warnings across the whole sequence (CDP console/
  exception listener empty of any `error`/`exception` entries).

`agentsApiClient.ts`'s `AgentDetail`/`updateAgentAssignment` additive only
— confirmed by diff (`fetchAgent`, `triggerAgentAction`, `sendChatMessage`,
`fetchAgentHistory` all unchanged).

Final whole-story pass: `npx tsc --noEmit` and `npm run build` both clean
after all 8 tasks (`dist/` output produced with no errors).

gate: clear 2026-08-11 — no MUST-FLAG trigger fired; implemented exactly
per the task's own literal code block, no assumption needed.
