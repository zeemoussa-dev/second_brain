---
id: BUGFIX-02-US-01-T05
title: New SectionDrilldown.tsx component — one Section's own full-360deg Agents Tree
parent_story: BUGFIX-02-US-01
requirement_id: BUG-002
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [BUGFIX-02-US-01-T01, BUGFIX-02-US-01-T02, BUGFIX-02-US-01-T03, BUGFIX-02-US-01-T04]
created: 2026-08-12
updated: 2026-08-12
---

# BUGFIX-02-US-01-T05 — New SectionDrilldown.tsx component

## Parent Story

- Story: [[BUGFIX-02-US-01]] — `../UserStories/BUGFIX-02-US-01-agents-map-semantic-zoom-drilldown-containment.md`
- Requirement: `BUGS.md` → `BUG-002`

---

## Objective

Create the new sibling component `SectionDrilldown.tsx` (same "container
composes small presentational children" shape `ADR-010` already established
one view over) — renders one Section's own full-360°, fully-labeled Agents
Tree: a centered `SectionHub`, that Section's own agents spread across the
full circle via `T01`'s `layoutSectionDrilldown()` at `T01`'s
`DRILLDOWN_AGENT_RADIUS`, Hub→agent cluster-lines only (no radar/rings/
boundary/Knowledge Base — the drill-down has none of those), the established
`.empty-state` pattern for a 0-agent Section, and a "Back to Agents Map"
control.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed `layoutSectionDrilldown()` and `DRILLDOWN_AGENT_RADIUS`.
- `T02` has landed `.explore-drilldown`/`.explore-drilldown.active`/
  `.explore-drilldown .hub-node`/`.explore-drilldown .hub-node .hub-node-type`
  in `agents-map.css`.
- `T03` has landed `AgentNode`'s `radiusOverride` prop.
- `T04` has landed `SectionHub`'s `radiusOverride` prop (and `onActivate`,
  unused by this task — this component always omits it, keeping the
  drill-down's own Hub a plain, non-interactive `<div>`, per the
  approved design).
- No `SectionDrilldown.tsx` file exists yet.

**After / Outputs:**
- `src/frontend/src/features/agents-map/SectionDrilldown.tsx` exists,
  exporting `SectionDrilldown`, matching the approved prototype's own
  "Dense section (BUG-002 fix demo)" state markup structurally (not
  literally — real computed geometry, not hand-placed percentages).

---

## Files to Modify

- `src/frontend/src/features/agents-map/SectionDrilldown.tsx` (new file):
  ```tsx
  import type { AgentSection, MockAgent } from './mockAgents';
  import { DRILLDOWN_AGENT_RADIUS, polarToCartesian } from './polarLayout';
  import { layoutSectionDrilldown } from './layoutAgents';
  import { SectionHub } from './SectionHub';
  import { AgentNode } from './AgentNode';

  interface SectionDrilldownProps {
    section: AgentSection;
    // Full agent list — this component filters to its own section's agents
    // itself, matching AgentsMapCanvas.tsx's own existing inline-filter
    // convention (`agents.filter((agent) => agent.sectionId === section.id)`).
    agents: MockAgent[];
    onBack: () => void;
    onSelectAgent: (agentId: string) => void;
  }

  // Drill-down Hub sits at the canvas's own literal center (radius 0) — see
  // T04's own Objective note on why: there is no Knowledge Base/rings to
  // key an off-center Hub position against here, unlike the overview.
  const DRILLDOWN_HUB_RADIUS = 0;

  export function SectionDrilldown({ section, agents, onBack, onSelectAgent }: SectionDrilldownProps) {
    const sectionAgents = layoutSectionDrilldown(
      agents.filter((agent) => agent.sectionId === section.id),
    );
    const hasAgents = sectionAgents.length > 0;

    return (
      <div className="explore-drilldown active" data-agents-drilldown>
        <button
          type="button"
          className="btn"
          data-role="agents-drilldown-back"
          onClick={onBack}
        >
          &larr; Back to Agents Map
        </button>
        <div className="agents-map-stage">
          <div className="agents-map-canvas">
            {hasAgents && (
              <svg className="agents-map-lines" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
                {sectionAgents.map((agent) => {
                  const point = polarToCartesian(DRILLDOWN_AGENT_RADIUS, agent.angleDeg);
                  return (
                    <line
                      key={`drilldown-hub-${agent.id}`}
                      className="cluster-line"
                      x1="50"
                      y1="50"
                      x2={point.x}
                      y2={point.y}
                      stroke="var(--color-accent)"
                    />
                  );
                })}
              </svg>
            )}
            <SectionHub section={section} radiusOverride={DRILLDOWN_HUB_RADIUS} />
            {sectionAgents.map((agent) => (
              <AgentNode
                key={agent.id}
                agent={agent}
                onSelect={onSelectAgent}
                radiusOverride={DRILLDOWN_AGENT_RADIUS}
              />
            ))}
          </div>
        </div>
        {!hasAgents && (
          <div className="empty-state">
            <p className="text-muted">No agents in this section yet.</p>
          </div>
        )}
      </div>
    );
  }
  ```
  (`className="explore-drilldown active"` is applied unconditionally on
  this component's own root — React's conditional mounting by the parent
  [`T06`] already IS the "active" state; there is no separate JS
  class-toggle mechanism to port, unlike the prototype's own plain-JS
  `.active` add/remove. This reuses both CSS rules verbatim per `T02`,
  with zero dead code.)

---

## Constraints

- Inherits from parent story: must not regress `REQ-SB-18-US-01`'s
  empty-Section handling — a 0-agent Section renders its Hub (still
  visible, centered) plus the `.empty-state` block, no cluster-lines,
  no thrown error.
- Must NOT render the Knowledge Base, radar spokes, ring circles, boundary
  circle, or ring labels — none of those exist in this view (a deliberate
  divergence from `AgentsMapCanvas.tsx`'s overview SVG contents, matching
  the approved prototype's own drill-down markup, which has none of them
  either).
- `SectionHub` is always called without `onActivate` in this component —
  the drill-down's own Hub stays non-interactive, per the story's own
  Non-Goals (no nested drill-down-of-a-drill-down).
- Must preserve `AgentNode`'s existing `onSelect` click-through to the
  Agent Detail Panel unchanged (the story's own explicit Constraint) — this
  component's `onSelectAgent` prop is passed straight through as
  `AgentNode`'s `onSelect`.

---

## Tests

<!-- This component has a real DOM signature but is not yet mounted by
anything until T06 wires it into AgentsMapCanvas.tsx's own conditional
render. Non-AC smoke checks only; the story's one locked AC is verified
end-to-end, live, once T06 lands the real mount point. -->

**Manual verification steps** (`src/frontend`: `npm run dev`; a temporary
scratch render passing a stub `section` + `agents` array, removed before
this task is marked Done):

1. Non-AC smoke check: render `<SectionDrilldown section={technicalSection} agents={fiveStubAgents} onBack={fn} onSelectAgent={fn} />`
   — confirm exactly 1 `.hub-node` (a `<div>`, not a `<button>`) at
   `top:50%; left:50%`, exactly 5 `.agent-node` elements (no
   `agent-node--compact` class) spread across the full circle at
   `DRILLDOWN_AGENT_RADIUS`, and exactly 5 `.cluster-line` elements
   (Hub-center to each agent, none agent-to-agent).
2. Non-AC smoke check: render the same with `agents={[]}` (or agents that
   don't match `section.id`) — confirm the Hub still renders, zero
   `.agent-node`/`.cluster-line` elements render, and the `.empty-state`
   block ("No agents in this section yet.") renders.
3. Non-AC smoke check: click the rendered "Back to Agents Map" button —
   confirm `onBack` is called. Click a rendered agent node — confirm
   `onSelectAgent(agentId)` is called.
4. Non-AC smoke check: confirm the rendered root carries
   `className="explore-drilldown active"`; `npx tsc --noEmit` clean.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `SectionDrilldown.tsx` exists, exporting `SectionDrilldown({ section, agents, onBack, onSelectAgent })`
- [x] Filters `agents` to the given `section.id` itself; computes full-360°
      positions via `layoutSectionDrilldown()`
- [x] Renders a centered, non-interactive `SectionHub` (`radiusOverride={0}`,
      no `onActivate`)
- [x] Renders each of the Section's agents via `AgentNode` with
      `radiusOverride={DRILLDOWN_AGENT_RADIUS}`, no `compact`
- [x] Renders one Hub→agent `.cluster-line` per agent, no agent-to-agent
      lines, no radar/rings/boundary/KB
- [x] A 0-agent Section renders its Hub plus `.empty-state`, no thrown error
- [x] "Back to Agents Map" button calls `onBack`; clicking an agent calls
      `onSelectAgent`
- [x] Root element carries `className="explore-drilldown active"`
- [x] `npx tsc --noEmit` clean
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

**Post-hoc confirmation (via `T06`'s own live-browser session, once
mounted):** every checkbox above was re-confirmed against the real running
app, not just this task's own isolated smoke checks — the real Productivity
Section's drill-down rendered exactly 1 centered non-interactive `.hub-node`
`<div>`, exactly 4 fully-labeled `.agent-node` elements, exactly 4
Hub→agent `.cluster-line`s, and the real zero-agent "Sales" Section's
drill-down rendered the Hub plus `.empty-state` with no thrown error. See
`T06`'s own Implementation Log for the full live evidence.

---

## Out of Scope

- Mounting `SectionDrilldown` from `AgentsMapCanvas.tsx` (the
  `activeSectionId` state, the zoom-out CSS transition, wiring
  `SectionHub`'s `onActivate` at the overview call site) — `T06`.
- The overview entrance animation — confirmed story Non-Goal.

---

## Context / Notes

Depends on `T01` (`layoutSectionDrilldown`/`DRILLDOWN_AGENT_RADIUS`), `T02`
(`.explore-drilldown` CSS), `T03` (`AgentNode.radiusOverride`), and `T04`
(`SectionHub.radiusOverride`) — all four of this component's own building
blocks must exist first. Does not depend on `T06`; `T06` depends on this
task instead (the integration direction runs one way).

---

## Implementation Log

Created the new file exactly per this task's own code block. Confirmed
before writing that `.btn` and `.empty-state` (referenced classes this
component reuses, per its own Constraints' "established `.empty-state`
pattern") already exist globally — `src/frontend/src/styles/settings.css`
(both rules), imported app-wide via `main.tsx`'s existing `import
'./styles/settings.css'` — so no additional CSS import/change was needed
in this task, confirmed rather than assumed.

**Non-AC smoke checks (manual mode, no test tooling yet; reasoned by code
inspection since this component is not yet mounted by anything —
confirmed per this task's own "Out of Scope" — same standard `T03`/`T04`
used, plus direct confirmation this task's dependencies (`T01`-`T04`) are
themselves already `Done` and exporting exactly what this file imports):**
1. With a `technicalSection` + 5 stub agents (matching `section.id`):
   `sectionAgents = layoutSectionDrilldown(agents.filter(...))` yields all
   5 with full-360° angles (per `T01`, already independently verified);
   `hasAgents = true`; renders exactly 1 `SectionHub` (no `onActivate`
   passed → `T04`'s `<div className="hub-node">` branch, at
   `radiusOverride={0}` → `top:50%; left:50%`); exactly 5 `AgentNode`s (no
   `compact` passed → `T03`'s no-`agent-node--compact` branch, each at
   `radiusOverride={DRILLDOWN_AGENT_RADIUS}` = `40`); exactly 5
   `<line className="cluster-line">` elements, one per agent, each
   `x1/y1="50"` (Hub center) to that agent's own point — no agent-to-agent
   line generated anywhere in this component. PASS.
2. With `agents=[]}` (or non-matching `sectionId`s): the `.filter(...)`
   yields `[]`; `layoutSectionDrilldown([])` returns `[]` (per `T01`);
   `hasAgents = false` — the `<svg>` block and every `AgentNode` are
   skipped by the `hasAgents &&`/`.map` guards, `SectionHub` still renders
   (unconditional), and the `!hasAgents &&` branch renders `<div
   className="empty-state"><p className="text-muted">No agents in this
   section yet.</p></div>`. No throw. PASS.
3. The "Back to Agents Map" `<button onClick={onBack}>` calls `onBack`
   directly on click; each `AgentNode`'s `onSelect={onSelectAgent}` is
   passed straight through, so clicking one calls
   `onSelectAgent(agentId)` via `T03`'s own unchanged `onClick={() =>
   onSelect(agent.id)}`. PASS.
4. Root element's `className` is the literal string
   `"explore-drilldown active"`, applied unconditionally (matching this
   task's own Objective note that React's conditional mounting by `T06`
   already IS the "active" state, no separate JS class-toggle needed).
   `npx tsc --noEmit` (portable `tools/node` toolchain) — clean, zero
   errors. PASS.

No locked AC in this task (non-AC smoke checks only — not yet mounted
anywhere; the story's one locked AC is verified end-to-end, live, once
`T06` wires the real mount point). No new decision/pattern/constraint —
applied verbatim per the task's own fully-specified code. `MEMORY.md` not
touched.

gate: clear 2026-08-12 — no MUST-FLAG trigger fired: applied verbatim, all
four named dependencies (`T01`-`T04`) already `Done` and exporting exactly
what this file imports, no assumption, no ADR touched, no escalation.
