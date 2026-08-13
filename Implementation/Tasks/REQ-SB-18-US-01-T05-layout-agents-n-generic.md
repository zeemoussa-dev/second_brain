---
id: REQ-SB-18-US-01-T05
title: layoutAgents.ts becomes N-section-generic, driven by real GET /sections + GET /agents
parent_story: REQ-SB-18-US-01
requirement_id: REQ-SB-18
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-18-US-01-T03, REQ-SB-18-US-01-T04]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-18-US-01-T05 — layoutAgents.ts becomes N-section-generic

## Parent Story

- Story: [[REQ-SB-18-US-01]] — `../UserStories/REQ-SB-18-US-01-dynamic-agent-sections-and-assignment.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-18 *Dynamic Agent Sections & Agent-to-Section Assignment*

---

## Objective

Replace `layoutAgents.ts`'s fixed 3-section `SECTION_META`/`TYPE_TO_SECTION`
lookup with a genuinely N-section-generic computation, driven by the real
`GET /sections` list and each agent's own `section_id` (`T04`'s new field
on `GET /agents`) — hub angles are computed, evenly spaced around the full
circle, not hand-placed (`ADR-014` point 6). `mockAgents.ts`'s shared
types drop the no-longer-meaningful `AgentSection.type` field and widen
`SectionId` to a plain `string`.

---

## Starting State → End State

**Before / Inputs:**
- `mockAgents.ts` defines `SectionId = 'capture' | 'people' | 'qa'` and
  `AgentSection` with a `type: AgentType` field.
- `layoutAgents.ts` derives section membership from `agent.type` via a
  fixed `TYPE_TO_SECTION` lookup and 3 hand-placed `hubAngleDeg` values in
  `SECTION_META`.
- `agentsApiClient.ts`'s `AgentSummary` interface has no `section_id`
  field (added by this task, since `layoutAgents` is its only consumer).
- `T03` has landed `GET /sections`; `T04` has landed `section_id` on
  `GET /agents`.

**After / Outputs:**
- `mockAgents.ts`: `SectionId = string`; `AgentSection` has no `type`
  field.
- `agentsApiClient.ts`'s `AgentSummary` gains `section_id: string`.
- `layoutAgents(agents, sections)` takes the real `GET /sections` list
  alongside `GET /agents`; section membership comes from each agent's own
  `section_id`; N sections' hub angles are spaced evenly around the full
  circle.

---

## Files to Modify

- `src/frontend/src/features/agents-map/mockAgents.ts` — replace the type
  definitions:
  ```typescript
  export type AgentType = 'worker' | 'producer' | 'expert';
  export type SectionId = string;

  export interface AgentSection {
    id: SectionId;
    label: string;
    hubLabel: string;
    hubAngleDeg: number; // this section's Hub position on the hub band (r=32)
  }

  export interface MockAgent {
    id: string;
    label: string;
    type: AgentType;
    sectionId: SectionId;
    angleDeg: number; // this agent's position on its type's ring
  }

  // Real agent data now comes from the backend (GET /agents, agent_registry.py)
  // via features/agents-map/agentsApiClient.ts + layoutAgents.ts — this file
  // keeps only the shared type definitions above. AgentSection has no `type`
  // field as of ADR-014 (REQ-SB-18-US-01) — a Section is user-created and can
  // hold agents of any Type, so it no longer has one Type to tint by.
  ```

- `src/frontend/src/features/agents-map/agentsApiClient.ts` — add
  `section_id` to the existing `AgentSummary` interface:
  ```typescript
  export interface AgentSummary {
    id: string;
    name: string;
    type: 'worker' | 'producer' | 'expert';
    section_id: string;
  }
  ```
  (No other change to this file in this task — `T08` adds
  `updateAgentAssignment` and extends `AgentDetail` separately.)

- `src/frontend/src/features/agents-map/layoutAgents.ts` — replace the
  entire file:
  ```typescript
  import type { AgentSection, MockAgent } from './mockAgents';
  import type { AgentSummary } from './agentsApiClient';

  export interface SectionSummary {
    id: string;
    name: string;
    agent_ids: string[];
  }

  // Agents within a section fan out either side of that section's own hub
  // angle, evenly spaced across this arc — same visual convention the
  // original hand-placed mock data used (ADR-010), just computed instead of
  // hardcoded.
  const SECTION_ARC_SPAN_DEG = 80;

  // Purely cosmetic starting rotation for the first (sorted) hub — no
  // functional consequence, matches the prior layout's own top-left-ish
  // starting orientation (ADR-014 point 6).
  const HUB_ANGLE_OFFSET_DEG = -90;

  export interface AgentMapLayout {
    sections: AgentSection[];
    mapAgents: MockAgent[];
  }

  /** Real GET /agents + GET /sections -> the {sections, mapAgents} shape
   * AgentsMapCanvas renders. Section membership comes from each agent's own
   * section_id (no longer derived from `type`); N sections' hub angles are
   * spaced evenly around the full circle, replacing the fixed 3-entry
   * SECTION_META/TYPE_TO_SECTION lookup (ADR-014 point 6). */
  export function layoutAgents(agents: AgentSummary[], sectionList: SectionSummary[]): AgentMapLayout {
    const sortedSections = [...sectionList].sort((a, b) => a.id.localeCompare(b.id));
    const n = sortedSections.length;

    const sections: AgentSection[] = sortedSections.map((section, index) => ({
      id: section.id,
      label: section.name,
      hubLabel: `${section.name} Hub`,
      hubAngleDeg: n === 0 ? 0 : index * (360 / n) + HUB_ANGLE_OFFSET_DEG,
    }));

    const agentsBySection = new Map<string, AgentSummary[]>();
    for (const agent of agents) {
      const list = agentsBySection.get(agent.section_id) ?? [];
      list.push(agent);
      agentsBySection.set(agent.section_id, list);
    }

    const mapAgents: MockAgent[] = [];
    for (const section of sections) {
      const sectionAgents = agentsBySection.get(section.id) ?? [];
      const count = sectionAgents.length;
      sectionAgents.forEach((agent, index) => {
        const offset = count === 1 ? 0 : (index / (count - 1) - 0.5) * SECTION_ARC_SPAN_DEG;
        mapAgents.push({
          id: agent.id,
          label: agent.name,
          type: agent.type,
          sectionId: section.id,
          angleDeg: section.hubAngleDeg + offset,
        });
      });
    }

    return { sections, mapAgents };
  }
  ```

- `src/frontend/src/pages/AgentsMapPage.tsx` — fetch both lists and pass
  both to `layoutAgents`:
  ```tsx
  import { useEffect, useState } from 'react';
  import { AgentsMapCanvas } from '../features/agents-map/AgentsMapCanvas';
  import { AgentDetailPanel } from '../features/agents-map/AgentDetailPanel';
  import { fetchAgentList } from '../features/agents-map/agentsApiClient';
  import { fetchSections } from '../features/settings/settingsApiClient';
  import { layoutAgents } from '../features/agents-map/layoutAgents';
  import type { AgentSection, MockAgent } from '../features/agents-map/mockAgents';

  export function AgentsMapPage() {
    const [sections, setSections] = useState<AgentSection[]>([]);
    const [agents, setAgents] = useState<MockAgent[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

    useEffect(() => {
      let cancelled = false;
      Promise.all([fetchAgentList(), fetchSections()])
        .then(([agentList, sectionList]) => {
          if (cancelled) return;
          const layout = layoutAgents(agentList, sectionList);
          setSections(layout.sections);
          setAgents(layout.mapAgents);
        })
        .catch(() => {
          if (!cancelled) {
            setSections([]);
            setAgents([]);
          }
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
      return () => {
        cancelled = true;
      };
    }, []);

    const hasAgents = agents.length > 0;

    return (
      <>
        <h1>Agents Map</h1>
        <AgentsMapCanvas sections={sections} agents={agents} onSelectAgent={setSelectedAgentId} />
        {!loading && !hasAgents && (
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
  (This task's own `layoutAgents` change is a breaking signature change —
  `AgentsMapPage.tsx` is the only caller, updated here in the same task so
  the app never sits in a broken intermediate state.)

  This introduces a dependency from `AgentsMapPage.tsx` on
  `features/settings/settingsApiClient.ts`'s `fetchSections` — that module
  does not exist yet at this task's own build time (`T07` creates it).
  This task must create a **minimal placeholder**
  `src/frontend/src/features/settings/settingsApiClient.ts` containing
  only:
  ```typescript
  import { apiFetch } from '../../api/client';
  import type { SectionSummary } from '../agents-map/layoutAgents';

  export type { SectionSummary };

  export function fetchSections(): Promise<SectionSummary[]> {
    return apiFetch<SectionSummary[]>('/sections');
  }
  ```
  `T07` extends this same file with `createSection`/`renameSection`/
  `deleteSection` and the parallel Sections-area component — it does not
  recreate the file, it adds to what this task lands (see `T07`'s own
  Starting State).

---

## Constraints

- Inherits from parent story: `ADR-010`'s styling/class-name convention
  (unaffected here — this task touches no CSS/JSX rendering, only
  layout-geometry logic and type plumbing); `ADR-014` point 6's exact
  angle-spacing formula.
- Must NOT change `polarLayout.ts`'s ring-radius geometry — ring
  placement stays Type-driven, untouched by this task (`ADR-014`'s own
  explicit non-goal).
- `layoutAgents`'s hub-angle computation must be genuinely N-generic — no
  hardcoded section id/count anywhere in the function body.
- `HUB_ANGLE_OFFSET_DEG`'s exact value has no functional consequence
  (purely cosmetic starting rotation) — do not treat it as load-bearing.

---

## Tests

<!-- This task's own change (a pure layout-geometry function + type
plumbing) has no independent DOM signature to assert — its correctness is
verified through T06's rendering of its output. This task's Tests are
non-AC smoke checks on the computed data only. -->

**Manual verification steps** (`src/frontend`: `npm run dev`; `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; browser preview
tool, browser DevTools console for ad hoc `import`-free inspection is not
available in this stack — verify via a temporary `console.log(layout)` in
`AgentsMapPage.tsx`, removed before this task is marked Done):

1. Non-AC smoke check: with the real backend running (5 seed sections, 5
   agents each defaulted to `"technical"` per `T02`'s seed), load `/`.
   Temporarily log the computed `{sections, mapAgents}` — confirm exactly
   5 `sections` entries with `hubAngleDeg` values spaced 72° apart
   (`360/5`), and all 5 `mapAgents` entries have `sectionId ===
   "technical"` (matching the un-reassigned seed default). Remove the
   temporary log before marking this task Done.
2. Non-AC smoke check: via `Invoke-RestMethod` or the browser,
   `PATCH /agents/vault-qa` with `{"section_id": "sales"}` (reassign one
   agent). Reload `/` and repeat step 1's temporary log — confirm
   `vault-qa` now appears in the `"sales"` section's `mapAgents` entries,
   not `"technical"`'s. Revert with `PATCH /agents/vault-qa` `{"section_id":
   "technical"}` afterward so later tasks' verification starts from the
   clean seed state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `mockAgents.ts`'s `AgentSection` has no `type` field; `SectionId` is
      `string`
- [ ] `agentsApiClient.ts`'s `AgentSummary` gains `section_id: string`
- [ ] `layoutAgents(agents, sections)` computes N evenly-spaced hub angles
      and derives section membership from each agent's own `section_id`,
      with no hardcoded section id/count
- [ ] `AgentsMapPage.tsx` fetches both `GET /agents` and `GET /sections`
      and passes both to `layoutAgents`
- [ ] A minimal `features/settings/settingsApiClient.ts` exists with
      `fetchSections` (extended, not replaced, by `T07`)
- [ ] `polarLayout.ts` / ring-radius geometry unchanged
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- `AgentsMapCanvas.tsx`'s section-boundary divider lines / `SectionHub.tsx`'s
  coloring — `T06`.
- `SectionsCard.tsx` and the rest of `settingsApiClient.ts`'s CRUD calls —
  `T07`.
- `AgentDetailPanel.tsx`'s Section picker — `T08`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-014` created at
`/plan-tasks` step 1) — the human reviews `ADR-014` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

This task deliberately creates a minimal `settingsApiClient.ts` (rather
than waiting for `T07`) because `layoutAgents`'s own new signature
requires a real `GET /sections` call from the moment this task lands —
sequencing it the other way (deferring `fetchSections` to `T07`) would
leave `AgentsMapPage.tsx` broken between this task and `T07`. `T07`'s own
Starting State names this file as already-existing and extends it, not a
`(new)` file — no collision.

---

## Implementation Log

**2026-08-11 — Done.** `mockAgents.ts`'s `AgentSection` dropped `type`,
`SectionId` widened to `string`; `agentsApiClient.ts`'s `AgentSummary`
gained `section_id`; `layoutAgents.ts` rewritten to the N-generic
computation exactly per the task's own code block; `AgentsMapPage.tsx`
fetches both `GET /agents` and `GET /sections` (via the new minimal
`features/settings/settingsApiClient.ts`, created here as this task's own
Starting State directs, extended by `T07`) and passes both to
`layoutAgents`.

`npx tsc --noEmit` clean after this task's own edits (checked
incrementally alongside `T06`'s edits, since `AgentsMapCanvas.tsx` — not
in this task's own `Files to Modify` — still referenced the now-dropped
`AgentSection.type` at one additional spot besides the two `T06` already
covers; see `T06`'s own Implementation Log for that finding and fix).

Live verification (real backend `:8001`, real frontend `npm run dev`
`:5173`, headless-Chrome-via-CDP per the established pattern): confirmed
live as part of `T06`'s own DOM-level check (below) — exactly 5 `sections`
computed with `hubAngleDeg` values 72° apart (`360/5`), and all 5 agents
grouped under `"technical"` (the un-reassigned seed default). Reassignment
propagation (`PATCH /agents/vault-qa {"section_id":"sales"}` moving an
agent's rendered cluster) is exercised and confirmed as part of `T08`'s
own AC-09 live check, consolidating the same real-side-effect step across
tasks per this project's established pattern (MEMORY.md).

`polarLayout.ts` untouched — confirmed by diff. No hardcoded section
id/count anywhere in `layoutAgents`'s body — confirmed by inspection
(the function only reads `sectionList`/`agents`, computes `n` and per-index
angles).

gate: clear 2026-08-11 — no MUST-FLAG trigger fired; implemented exactly
per the task's own literal code block, no assumption needed.
