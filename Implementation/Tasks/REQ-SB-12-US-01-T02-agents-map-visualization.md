---
id: REQ-SB-12-US-01-T02
title: Agents Map polar-grid visualization (mock data, polarLayout, canvas + node components)
parent_story: REQ-SB-12-US-01
requirement_id: REQ-SB-12
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-12-US-01-T01]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-12-US-01-T02 — Agents Map polar-grid visualization

## Parent Story

- Story: [[REQ-SB-12-US-01]] — `../UserStories/REQ-SB-12-US-01-app-shell-agents-map-and-settings.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-12 *Primary Application UI Shell — Agents Map & My Day*

---

## Objective

Build the real Agents Map page: a central Knowledge Base element with every
configured agent arranged around it on a polar grid (angle = section, radius
= agent type — Worker outermost, Expert middle, Producer innermost), backed
by local mock data standing in for the not-yet-built "list configured
agents" backend endpoint, plus the first-run empty state. Reproduces
`html-prototype/agents-map.html`'s approved visual design via a pure
geometry function instead of the prototype's hand-derived per-node
percentages (ADR-010 Decision 4).

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed `AppShell`/`Sidebar`/routing and a placeholder
  `pages/AgentsMapPage.tsx` (`<h1>Agents Map</h1>`).
- `html-prototype/agents-map.html` is the approved design source for both
  the populated state (lines 298–507) and the first-run state (lines
  183–290).

**After / Outputs:**
- `src/frontend/src/features/agents-map/mockAgents.ts`,
  `polarLayout.ts`, `AgentsMapCanvas.tsx`, `KnowledgeBaseNode.tsx`,
  `SectionHub.tsx`, `AgentNode.tsx` all exist.
- `src/frontend/src/styles/agents-map.css` exists, ported from the
  prototype.
- `pages/AgentsMapPage.tsx` renders `<AgentsMapCanvas>` fed the populated
  mock dataset, plus the first-run empty-state message path (exercised via
  the manual verification steps below, then left wired to the populated
  dataset as the pass's shipped state).

---

## Files to Modify

- `src/frontend/src/features/agents-map/mockAgents.ts` (new):
  ```ts
  export type AgentType = 'worker' | 'producer' | 'expert';
  export type SectionId = 'capture' | 'people' | 'qa';

  export interface AgentSection {
    id: SectionId;
    label: string;
    type: AgentType; // this section's Hub ring/color
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

  // Populated state — mirrors html-prototype/agents-map.html's exact
  // 5-agent example 1:1 (REQ-SB-07/08/09 Capture, REQ-SB-10 People,
  // REQ-SB-03 Q&A) — none invented, per the prototype's own design-
  // rationale comment. Angles derived from the prototype's own computed
  // top/left percentages (verified by hand: x = 50 + r*cos(angle),
  // y = 50 + r*sin(angle), angle in degrees, 0 deg = due right,
  // increasing clockwise since SVG y grows downward).
  export const POPULATED_SECTIONS: AgentSection[] = [
    { id: 'capture', label: 'Capture', type: 'worker', hubLabel: 'Capture Hub', hubAngleDeg: -30 },
    { id: 'people', label: 'People', type: 'producer', hubLabel: 'People Hub', hubAngleDeg: 45 },
    { id: 'qa', label: 'Knowledge Q&A', type: 'expert', hubLabel: 'Q&A Hub', hubAngleDeg: 210 },
  ];

  export const POPULATED_AGENTS: MockAgent[] = [
    { id: 'email-capture', label: 'Email Capture', type: 'worker', sectionId: 'capture', angleDeg: -70 },
    { id: 'meeting-capture', label: 'Meeting Capture', type: 'worker', sectionId: 'capture', angleDeg: -30 },
    { id: 'todo-capture', label: 'To-Do Capture', type: 'worker', sectionId: 'capture', angleDeg: 10 },
    { id: 'people-producer', label: 'People Notes', type: 'producer', sectionId: 'people', angleDeg: 90 },
    { id: 'vault-qa', label: 'Vault Q&A', type: 'expert', sectionId: 'qa', angleDeg: 210 },
  ];

  // First-run state — no agents/sections configured yet (Scenario 3).
  export const FIRST_RUN_SECTIONS: AgentSection[] = [];
  export const FIRST_RUN_AGENTS: MockAgent[] = [];
  ```

- `src/frontend/src/features/agents-map/polarLayout.ts` (new):
  ```ts
  import type { AgentType } from './mockAgents';

  export const CENTER = 50;
  export const RING_RADIUS: Record<AgentType, number> = {
    producer: 30,
    expert: 45,
    worker: 50,
  };
  export const HUB_RADIUS = 32;
  export const BOUNDARY_RADIUS = 58;

  export interface Point {
    x: number;
    y: number;
  }

  /** Ring radius + angle (degrees, 0 = due right, clockwise-positive since
   * the shared 0-100 SVG viewBox's y-axis grows downward) -> {x, y} on that
   * viewBox. Replaces html-prototype/agents-map.html's hand-derived
   * per-node percentages (its own revision comments document ~6 rounds of
   * manually re-deriving every coordinate by hand — ADR-010 Decision 4)
   * with one shared, reusable computation. */
  export function polarToCartesian(radius: number, angleDeg: number, center = CENTER): Point {
    const angleRad = (angleDeg * Math.PI) / 180;
    return {
      x: center + radius * Math.cos(angleRad),
      y: center + radius * Math.sin(angleRad),
    };
  }
  ```

- `src/frontend/src/features/agents-map/KnowledgeBaseNode.tsx` (new) —
  the central KB element: a `.kb-node` div containing the prototype's
  `.kb-brain-svg` (port the exact `<svg class="kb-brain-svg">` markup from
  `html-prototype/agents-map.html` lines 208–280 — the 16 outer-ring lines,
  6 mid-ring lines, 6 center-spoke lines, 4 cross-diagonal lines, 23
  `.kb-neuron` circles, center neuron, and 2 `.kb-pulse-dot`
  `<animateMotion>` circles — verbatim, it is static approved-design SVG,
  not derived from any layout function) plus a `.kb-node-label` span
  ("Knowledge Base" / "Vault indexed" sub-label, matching the prototype).
  No props needed this pass (no "not-indexed" scenario in this story).

- `src/frontend/src/features/agents-map/SectionHub.tsx` (new):
  ```tsx
  import type { AgentSection } from './mockAgents';
  import { HUB_RADIUS, polarToCartesian } from './polarLayout';

  export function SectionHub({ section }: { section: AgentSection }) {
    const { x, y } = polarToCartesian(HUB_RADIUS, section.hubAngleDeg);
    return (
      <div
        className={`hub-node hub-node--${section.type}`}
        style={{ top: `${y}%`, left: `${x}%` }}
      >
        {section.hubLabel}
        <span className="hub-node-type">{section.type} section</span>
      </div>
    );
  }
  ```

- `src/frontend/src/features/agents-map/AgentNode.tsx` (new):
  ```tsx
  import type { MockAgent } from './mockAgents';
  import { RING_RADIUS, polarToCartesian } from './polarLayout';

  export function AgentNode({ agent }: { agent: MockAgent }) {
    const { x, y } = polarToCartesian(RING_RADIUS[agent.type], agent.angleDeg);
    return (
      <button
        type="button"
        className={`agent-node agent-node--${agent.type}`}
        style={{ top: `${y}%`, left: `${x}%` }}
        data-agent-id={agent.id}
      >
        <span className="agent-node-label">{agent.label}</span>
        <span className="agent-node-type">{agent.type}</span>
      </button>
    );
  }
  ```
  (Rendered as a real `<button>` — the correct structural/interactive
  affordance for a clickable node — but with no `onClick` handler wired
  yet: click-to-open-detail-panel is REQ-SB-13-US-01's scope, not built
  here, per `architecture.md`'s explicit carve-out.)

- `src/frontend/src/features/agents-map/AgentsMapCanvas.tsx` (new) — owns
  the one connected SVG background layer plus positions its KB/Hub/Agent
  children, mirroring `html-prototype/agents-map.html`'s single
  `<svg class="agents-map-lines">`:
  ```tsx
  import type { AgentSection, MockAgent } from './mockAgents';
  import { BOUNDARY_RADIUS, HUB_RADIUS, RING_RADIUS, polarToCartesian } from './polarLayout';
  import { KnowledgeBaseNode } from './KnowledgeBaseNode';
  import { SectionHub } from './SectionHub';
  import { AgentNode } from './AgentNode';

  interface AgentsMapCanvasProps {
    sections: AgentSection[];
    agents: MockAgent[];
  }

  export function AgentsMapCanvas({ sections, agents }: AgentsMapCanvasProps) {
    const hasAgents = sections.length > 0 && agents.length > 0;
    return (
      <div className="agents-map-stage">
        <div className="agents-map-canvas">
          <svg className="agents-map-lines" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
            {/* Ambient radar background: always rendered, even first-run —
                port the 12 .radar-spoke <line> elements verbatim from
                html-prototype/agents-map.html lines 190-201 (every 30 deg,
                center to r=58), plus the 3 .ring-circle (r=30/45/58) and
                .boundary-circle (r=58) from lines 202-205/320-323. */}
            {hasAgents && (
              <>
                {/* Section-boundary guide lines, KB-to-Hub .spoke-line per
                    section, and per-section .cluster-line to each agent —
                    port verbatim from html-prototype/agents-map.html lines
                    326-352, computing each line's Hub/agent endpoint via
                    polarToCartesian(HUB_RADIUS, section.hubAngleDeg) /
                    polarToCartesian(RING_RADIUS[agent.type], agent.angleDeg)
                    instead of the prototype's literal coordinates, so the
                    lines always match wherever SectionHub/AgentNode
                    actually render. Ring-label text elements (Producer/
                    Expert/Worker, lines 355-357) also only render when
                    hasAgents. */}
              </>
            )}
          </svg>
          <KnowledgeBaseNode />
          {hasAgents && sections.map((section) => <SectionHub key={section.id} section={section} />)}
          {hasAgents && agents.map((agent) => <AgentNode key={agent.id} agent={agent} />)}
          {hasAgents && sections.map((section) => (
            <div key={`${section.id}-title`} className="section-title" /* position per prototype's section-title placement, lines 486-497 */>
              {section.label}
              <span className="section-title-accent" style={{ background: `var(--agent-color-${section.type})` }} />
            </div>
          ))}
        </div>
      </div>
    );
  }
  ```
  The commented placeholders above mark ambient/decorative SVG chrome
  (radar spokes, ring/boundary circles, section-boundary/spoke/cluster
  lines, ring-labels, section-title positions) that must be built to
  reproduce the approved prototype's visual design in full, computed from
  `polarToCartesian` where the prototype used a literal coordinate and
  ported verbatim where the prototype used a fixed decorative value (the
  12 radar spokes, the 3 ring radii, the boundary radius) — **none of this
  ambient chrome is independently locked-AC-verified** (it has no
  behavioral signal beyond what AC-02/AC-03 already check structurally);
  it is verified by the non-blocking prototype spot-check in step 5 below,
  per the decomposer's screen-story rule (pure visual fidelity is not a
  locked AC). The 12 radar-spoke `<line>` elements are fixed decorative
  geometry (not data-driven) — inline them as static SVG matching the
  prototype's own literal coordinates (lines 190–201), no new
  `polarLayout.ts` export needed for them.

- `src/frontend/src/pages/AgentsMapPage.tsx` — replace the `T01`
  placeholder body:
  ```tsx
  import { AgentsMapCanvas } from '../features/agents-map/AgentsMapCanvas';
  import { POPULATED_SECTIONS, POPULATED_AGENTS } from '../features/agents-map/mockAgents';

  export function AgentsMapPage() {
    const hasAgents = POPULATED_AGENTS.length > 0;
    return (
      <>
        <h1>Agents Map</h1>
        <AgentsMapCanvas sections={POPULATED_SECTIONS} agents={POPULATED_AGENTS} />
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
      </>
    );
  }
  ```
  Ships wired to `POPULATED_SECTIONS`/`POPULATED_AGENTS` as this pass's
  real rendered state (mirroring what a real "list configured agents"
  endpoint would return once one exists) — Scenario 3's first-run state is
  verified per step 2 below by temporarily swapping in
  `FIRST_RUN_SECTIONS`/`FIRST_RUN_AGENTS`, confirming in the browser, then
  reverting.

- `src/frontend/src/styles/agents-map.css` (new) — port verbatim from
  `html-prototype/styles.css`: `.agents-map-stage`/`.agents-map-canvas`/
  `.agents-map-lines` + its child selectors (lines 318–350), the full
  `.kb-node`/`.kb-brain-svg`/`.kb-neuron`/`.kb-pulse-dot`/
  `.kb-node-label`/`kbPulse`/`neuronPulse` keyframes block (352–432), the
  `.hub-node` block + type variants (434–476), the `.agent-node` block +
  hover + type variants + `nodeFadeIn` keyframe (478–526), the
  `.agent-node--compact`/`.map-overflow-marker` scale-to-~100-agents
  primitives (528–578 — port as defined, not instantiated, matching the
  prototype's own "ready to apply, unused in this demo" comment), and
  `.section-title` + `.agent-type-legend` (580–620). `.empty-state` itself
  is already in `settings.css` (`T01`) — do not duplicate it here.

---

## Constraints

- Inherits from parent story: ADR-010 Decision 4 (component structure) and
  its exact radii (Producer r=30, Expert r=45, Worker r=50, Hub band r=32,
  boundary r=58, KB edge ~r=17).
- `AgentNode`/`SectionHub`/`KnowledgeBaseNode` are rendering-only this pass
  — no click handlers, no REQ-SB-13 detail-panel wiring.
- Must not modify `T01`'s `AppShell`/`Sidebar`/`App.tsx`/routing.
- `polarLayout.ts` must be a pure function (no side effects, no DOM/React
  dependency) — reusable by a future story without pulling in this
  feature's components.

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`, use the
browser preview tool at `/`):

1. **[REQ-SB-12-US-01-AC-02]** Load `/`. Confirm exactly one `.kb-node`
   element is rendered at the center of the canvas. Confirm 5
   `.agent-node` elements are rendered (inspect via the browser preview
   tool's element inspector or React DevTools), each carrying exactly one
   of the classes `.agent-node--worker` (3 nodes: Email Capture, Meeting
   Capture, To-Do Capture), `.agent-node--producer` (1 node: People
   Notes), or `.agent-node--expert` (1 node: Vault Q&A) — matching
   `POPULATED_AGENTS`'s `type` field.
2. **[REQ-SB-12-US-01-AC-03]** Temporarily edit `AgentsMapPage.tsx` to
   import and pass `FIRST_RUN_SECTIONS`/`FIRST_RUN_AGENTS` instead of the
   populated constants. Reload `/` in the browser. Confirm the `.kb-node`
   element still renders, confirm zero `.agent-node` and zero `.hub-node`
   elements are rendered, and confirm the `.empty-state` element renders
   with the "No agents connected yet" message. Revert the edit back to
   `POPULATED_SECTIONS`/`POPULATED_AGENTS` (this story's shipped state)
   and reload once more to confirm the populated state is restored.
3. Non-AC smoke check: confirm each `.agent-node`'s inline
   `top`/`left` style falls within the canvas's 0–100% coordinate space
   (no node renders off-canvas or overlapping the KB) — a `polarToCartesian`
   sign/angle error would typically show up as a node in the wrong
   quadrant or coincident with the center.
4. Non-AC smoke check: confirm no console errors/warnings on load or on
   the temporary first-run swap in step 2.
5. **Non-blocking design spot-check** (not a locked AC — visual polish has
   no DOM signal, per the decomposer's screen-story rule): compare the
   populated Agents Map's rendered radar background, rings, section-
   boundary/spoke/cluster lines, ring labels, and section titles side by
   side with `html-prototype/agents-map.html`'s populated state in a
   browser. Note any visible discrepancy in the Implementation Log for
   human review — it does not block this task's completion.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `mockAgents.ts` exports the exact populated 5-agent/3-section dataset
      and the empty first-run dataset
- [x] `polarLayout.ts`'s `polarToCartesian` is a pure function using the
      exact ADR-010 radii; `SectionHub`/`AgentNode` positions are computed
      from it, never hardcoded percentages
- [x] `AgentsMapCanvas`/`KnowledgeBaseNode`/`SectionHub`/`AgentNode` exist
      as separate components per ADR-010 Decision 4
- [x] Populated state renders 1 KB element + 5 correctly-type-classed agent
      nodes; first-run state renders the KB element + empty-state message +
      zero agent/hub nodes
- [x] `agents-map.css` ported per the selector groups above
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Click-to-open agent detail panel — REQ-SB-13-US-01.
- Real backend data-fetching — no endpoint exists yet; `api/client.ts`
  (from `T01`) stays unused.
- `SettingsPage`/`MyDayPage` content.
- Additional agent types beyond Worker/Producer/Expert.

---

## Context / Notes

The ambient SVG chrome (radar spokes, rings, boundary, section-boundary/
spoke/cluster lines, ring labels) is real build work required by this
task's Objective (matching the approved design) even though it carries no
independently locked AC of its own — build it in full per
`html-prototype/agents-map.html`'s populated-state markup (lines 298–358),
computing every line endpoint that depends on a Hub/agent position via
`polarToCartesian` rather than copying the prototype's literal numbers, so
the lines never drift out of sync with where the nodes actually render.

---

## Implementation Log

**Built 2026-08-11.** All files created exactly per `## Files to Modify`.
`polarToCartesian(radius, angleDeg)` positions verified by hand against
every literal coordinate in `html-prototype/agents-map.html`'s populated
state (all 3 Hub positions, all 5 agent positions) — exact percentage
match confirmed live (see verification below), so `mockAgents.ts`'s
angle values are correctly derived.

**Assumption (scope-internal, logged for spot-check, not an escalation):**
`main.tsx`'s `agents-map.css` import — T01's own text anticipated this
("once T02 creates it... import the three that exist after this task")
but `main.tsx` is not listed under this task's own `## Files to Modify`.
Added the one-line import to the already-existing `main.tsx` (owned by
this story, already touched by T01) since omitting it would silently ship
the Agents Map unstyled — treated as completing T01's own explicit intent
rather than an out-of-scope file.

**Assumption (scope-internal, non-blocking — visual only):** the
`AgentSection` interface (per this task's own prescribed code) carries
only `hubAngleDeg`, not a separate "section midpoint angle." The
prototype's `.section-title` elements sit at each section's true angular
midpoint, which for Capture (-30) and Q&A (210) equals `hubAngleDeg`, but
for People the Hub is deliberately offset to 45 degrees (to avoid
overlapping the People Notes agent, which already occupies the Producer
ring at angle 90 — see the prototype's own round-5 comment) while the
section's true midpoint is 90. Reused `hubAngleDeg` for `.section-title`
positioning uniformly (no new field added, since this task's own
`AgentSection` shape is prescribed verbatim in `## Files to Modify` and
this is pure ambient-chrome visual polish with no locked AC) — the
practical effect is only the "PEOPLE" section title renders at angle 45
instead of 90, a minor, non-blocking visual deviation confirmed in the
screenshot spot-check below. Section-boundary guide lines and radar
spokes were kept as fixed literal geometry (ported verbatim, same
treatment as the prototype's own fixed decorative values), since they are
generic 3-way dividers not tied to any per-section data field.

**AC-02 (populated: KB + 5 typed agent nodes) — PASS.** Loaded `/`.
Confirmed exactly 1 `.kb-node`, exactly 5 `.agent-node` elements: 3
`.agent-node--worker` (Email/Meeting/To-Do Capture), 1
`.agent-node--producer` (People Notes), 1 `.agent-node--expert` (Vault
Q&A) — matches `POPULATED_AGENTS`. Also confirmed 3 `.hub-node` elements
(Capture/People/Q&A Hubs). Screenshot spot-check: layout, colors, lines,
and labels visually match `html-prototype/agents-map.html`'s populated
state closely (see the People-section-title angle deviation noted above
as the one visible discrepancy).

**AC-03 (first-run empty state) — PASS.** Temporarily swapped
`AgentsMapPage.tsx` to import `FIRST_RUN_SECTIONS`/`FIRST_RUN_AGENTS`
(exact swap the task's own Tests section describes). Reloaded: `.kb-node`
still renders (1), zero `.agent-node`, zero `.hub-node`, `.empty-state`
renders with "No agents connected yet." + explanatory text. Screenshot
confirms the radar/ring background still renders ambient (matching the
prototype's first-run state — KB indexed, no configured entities).
Reverted the edit back to `POPULATED_SECTIONS`/`POPULATED_AGENTS` and
reloaded; confirmed the populated state is restored (5 agent nodes, 3 hub
nodes, exactly as before the swap) — this task's real shipped state.

**Non-AC smoke checks — PASS.** All 5 agent-node inline `top`/`left`
percentages fall within [0, 100] and match the prototype's own literal
coordinates to within rounding (e.g. Email Capture: computed
`top:3.015%, left:67.101%` vs. prototype's `top:3.01%, left:67.1%`).
Zero console errors/warnings across the populated load, the first-run
swap, and the revert (only Vite HMR/React DevTools informational
messages).

**Verification tooling:** same headless-Chrome-CDP driver script noted in
`T01`'s Implementation Log (no new project dependency).

gate: clear 2026-08-11 — no triggers fired beyond the two logged
scope-internal assumptions above (a task-boundary completeness gap and a
non-blocking visual-only positioning choice, neither weakening a locked
AC nor touching an out-of-scope file in spirit).
