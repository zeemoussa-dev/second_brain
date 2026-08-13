---
id: REQ-SB-19-US-01-T06
title: AgentDetailPanel.tsx Provider picker kv-row + agentsApiClient.ts updateAgentAssignment(provider_id) extension
parent_story: REQ-SB-19-US-01
requirement_id: REQ-SB-19
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-19-US-01-T04, REQ-SB-19-US-01-T05, REQ-SB-18-US-01-T08]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-19-US-01-T06 — AgentDetailPanel.tsx Provider picker

## Parent Story

- Story: [[REQ-SB-19-US-01]] — `../UserStories/REQ-SB-19-US-01-per-agent-llm-provider-selection.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-19 *Per-Agent LLM Provider Selection*

---

## Objective

Add a Provider `<select class="kv-select">` row to `AgentDetailPanel.tsx`,
alongside `REQ-SB-18-US-01-T08`'s already-landed Section row, per the
approved `html-prototype/agents-map.html` side panel, wired to `T04`'s
`PATCH /agents/{agent_id}` — completing the picker-availability half of
`AC-02` and the panel-level default-to-Compass/reassignment scenario.

**This task requires `REQ-SB-18-US-01-T08` to already be `Done`** — it
edits the exact same `AgentDetailPanel.tsx` and `agentsApiClient.ts` files
that task creates/extends. Do not start this task until that one is
complete.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-18-US-01-T08` has landed: `AgentDetail` with `section_id`/
  `section_name`; `updateAgentAssignment(agentId, { section_id?: string
  })`; the panel's Section `<select>` kv-row and `sections` state/fetch.
- `T04` has landed `GET /agents/{agent_id}`'s `provider_id`/
  `provider_name`/`provider_available` fields and the `PATCH`'s
  `provider_id` handling; `T05` has landed `settingsApiClient.
  fetchProviders`.

**After / Outputs:**
- `agentsApiClient.ts`'s `AgentDetail` gains `provider_id: string;
  provider_name: string; provider_available: boolean;`, and
  `updateAgentAssignment`'s body type widens to `{ section_id?: string;
  provider_id?: string }`.
- `AgentDetailPanel.tsx` renders a new `Provider` kv-row with a
  `<select class="input kv-select">` populated from `fetchProviders()`,
  showing the agent's current Provider selected (Compass by default), and
  — when `provider_available` is `false` — a short honesty note matching
  the approved prototype's own copy.

---

## Files to Modify

- `src/frontend/src/features/agents-map/agentsApiClient.ts` — extend the
  existing `AgentDetail` interface (already carrying `section_id`/
  `section_name` from `REQ-SB-18-US-01-T08`):
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
  }
  ```
  Widen the existing `updateAgentAssignment`'s body type:
  ```typescript
  export function updateAgentAssignment(
    agentId: string,
    body: { section_id?: string; provider_id?: string },
  ): Promise<AgentDetail> {
    return apiFetch<AgentDetail>(`/agents/${agentId}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  }
  ```

- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` — add an
  import alongside the existing `fetchSections` one:
  ```tsx
  import { fetchProviders, type ProviderSummary } from '../settings/settingsApiClient';
  ```
  Add a new piece of state, alongside `sections`:
  ```tsx
  const [providers, setProviders] = useState<ProviderSummary[] | null>(null);
  ```
  Extend the existing `useEffect` (already fetching `sections`) to also
  fetch `providers`:
  ```tsx
  useEffect(() => {
    setAgent(null);
    setMessages([]);
    setDraft('');
    setHistory(null);
    fetchAgent(agentId).then(setAgent);
    fetchAgentHistory(agentId).then(setHistory);
    fetchSections().then(setSections);
    fetchProviders().then(setProviders);
  }, [agentId]);
  ```
  Add a handler function near `handleSectionChange`:
  ```tsx
  async function handleProviderChange(providerId: string) {
    const updated = await updateAgentAssignment(agentId, { provider_id: providerId });
    setAgent(updated);
  }
  ```
  In the JSX, inside the same Settings `.kv-list` block, immediately after
  the Section kv-row `T08` landed, add:
  ```tsx
  <div className="kv-row">
    <span className="kv-key">Provider</span>
    {providers && (
      <select
        className="input kv-select"
        value={agent.provider_id}
        onChange={(event) => handleProviderChange(event.target.value)}
      >
        {providers.map((provider) => (
          <option key={provider.id} value={provider.id}>
            {provider.name}{provider.is_default ? ' (default)' : ''}
          </option>
        ))}
      </select>
    )}
  </div>
  {!agent.provider_available && (
    <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
      {agent.provider_name} has no real client built yet — this agent
      honestly reports it's not available rather than silently falling
      back to Compass.
    </p>
  )}
  ```

---

## Constraints

- Inherits from parent story: `ADR-010`'s class-name-verbatim convention
  (`.kv-row`, `.kv-key`, `.kv-select`); `AgentDetailPanel.tsx`'s existing
  "clear stale content on agent switch" contract, same treatment as
  `T08`'s Section fetch (the Provider *list* is agent-independent, only
  the *selected* value changes per agent via `agent.provider_id`).
- Changing the Provider `<select>` must call the real `PATCH
  /agents/{agentId}` and update from its real response — no optimistic
  local-only state update.
- Must NOT modify `SectionsCard.tsx`, `ProvidersCard.tsx`, or `T08`'s own
  Section `<select>` row — additive extension only, placed alongside it.
- The unavailability note must read `agent.provider_available` from the
  real backend response, never inferred client-side from
  `provider.has_real_client` on the currently-selected `<option>` alone
  (the two should always agree, but the backend's own computed field is
  the source of truth this task renders).

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `.venv\Scripts\uvicorn app.main:app --reload --port 8001`;
browser preview tool):

1. **[REQ-SB-19-US-01-AC-02]** Via Settings' Providers card (`T05`), add a
   new Provider (e.g. "Verify-T06"). Navigate to the Agents Map, click any
   `.agent-node` to open its detail panel. Confirm the panel's Provider
   `<select>` now includes "Verify-T06" as one of its `<option>`s —
   completing the scenario `T05` began. Do not select it. Remove
   "Verify-T06" via Settings afterward (zero agents ever assigned).
2. **[REQ-SB-19-US-01-AC-06]** Open the detail panel for an agent never
   explicitly reassigned (any of the 5, at seed state). Confirm the
   Provider `<select>`'s selected `<option>` reads "Compass (default)".
   Add a throwaway Provider via Settings (e.g. "Verify-T06b") if none
   exists, then pick it from this agent's Provider `<select>`. Confirm
   the `<select>`'s selected value updates to "Verify-T06b" without a
   page reload; close and reopen the panel on the same agent — confirm
   "Verify-T06b" is still selected (persisted server-side). Confirm the
   honesty note now renders ("Verify-T06b has no real client built
   yet..."). Reassign back to "Compass" and confirm the note disappears.
   Remove "Verify-T06b" via Settings afterward.
3. Non-AC smoke check: zero console errors/warnings across the whole
   sequence.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-02** (Scenario 2, completing `T05`'s check) — a newly added
      Provider is available as a choice on the Agent Settings surface's
      Provider picker
- [ ] **AC-06** (Scenario 5) — an agent never explicitly reassigned shows
      Compass selected by default; picking a different Provider updates
      the selection, persisted server-side
- [ ] The unavailability note renders exactly when
      `agent.provider_available` is `false`, using the real
      `provider_name` from the backend
- [ ] `agentsApiClient.ts`'s `AgentDetail`/`updateAgentAssignment`
      additive only relative to `REQ-SB-18-US-01-T08`'s own state
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Section picker row — already landed by `REQ-SB-18-US-01-T08`.
- Wiring the Available Actions buttons — pre-existing out-of-scope
  carve-out from `REQ-SB-13-US-01-T06`, unaffected by this task.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-014` created at
`/plan-tasks` step 1) — the human reviews `ADR-014` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

This is the last task across both stories' full breakdown. It closes
`REQ-SB-19`'s own `AC-02` (the picker-availability half) —
`REQ-SB-18`'s `AC-02` was already fully closed by its own `T08`. Once this
task lands, every locked AC in both `REQ-SB-18-US-01` and
`REQ-SB-19-US-01` has a passing, tagged verification step.

---

## Implementation Log

**Built 2026-08-11 (coder).** `agentsApiClient.ts`'s `AgentDetail` gained
`provider_id`/`provider_name`/`provider_available`, additive to
`REQ-SB-18-US-01-T08`'s `section_id`/`section_name`; `updateAgentAssignment`'s
body type widened to `{ section_id?: string; provider_id?: string }`.
`AgentDetailPanel.tsx` gained the `fetchProviders`/`ProviderSummary`
import, `providers` state (fetched alongside `sections` in the existing
per-agent-switch `useEffect`), `handleProviderChange`, and the Provider
`<select class="input kv-select">` kv-row + conditional unavailability
note, placed immediately after `T08`'s own Section kv-row inside the same
Settings `.kv-list` — verbatim per this task's own code block.

**Live verification (real backend `:8001`, real frontend `:5173`,
headless-Chrome-via-CDP), both AC-tagged scenarios:**

- **[AC-02]** (completing `T05`'s own picker-availability half) Added
  "Verify-T06" via Settings' Providers card equivalent (a direct `POST
  /providers` call, the same mutation `T05`'s own UI already verified).
  Opened `meeting-capture`'s detail panel on the Agents Map — confirmed the
  Provider `<select>` included "Verify-T06" as an `<option>`. Removed it
  afterward (0 agents ever assigned). **PASS.**
- **[AC-06]** Opened `meeting-capture`'s panel (never explicitly
  reassigned) — confirmed the Provider `<select>`'s selected option read
  "Compass (default)". Added a throwaway Provider ("Verify-T06"), selected
  it from the `<select>` via a real React-controlled-`<select>` `value`-
  setter + `change`-event update (not raw DOM assignment) — confirmed the
  selection updated immediately with no page reload, and the honesty note
  rendered exactly ("Verify-T06 has no real client built yet — this agent
  honestly reports it's not available rather than silently falling back to
  Compass."). Closed and reopened the panel on the same agent — confirmed
  "Verify-T06" was still selected (persisted server-side, read fresh from
  `GET /agents/meeting-capture`, not client-only state) and the honesty
  note still rendered. Reassigned back to "Compass" — confirmed the
  `<select>` updated and the honesty note disappeared. Removed "Verify-T06"
  afterward. **PASS.**
- Zero console errors/warnings across the whole sequence. **PASS.**

Visual cross-check: screenshot of the real rendered panel (Meeting Capture,
Section + Provider kv-rows adjacent, "Compass (default)" selected) matches
the approved `html-prototype/agents-map.html` side panel's shape.

`agentsApiClient.ts`'s `AgentDetail`/`updateAgentAssignment` extension
confirmed additive-only relative to `REQ-SB-18-US-01-T08`'s own state (no
existing field/behavior removed). This is the last task across both
`REQ-SB-18-US-01` and `REQ-SB-19-US-01`'s full breakdown — every locked AC
in both stories now has a passing, tagged, live-verified check.

gate: clear 2026-08-11 — no MUST-FLAG trigger fired.
