---
id: BUGFIX-02-US-01-T03
title: AgentNode.tsx — optional compact and radiusOverride props
parent_story: BUGFIX-02-US-01
requirement_id: BUG-002
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-12
updated: 2026-08-12
---

# BUGFIX-02-US-01-T03 — AgentNode.tsx — compact / radiusOverride props

## Parent Story

- Story: [[BUGFIX-02-US-01]] — `../UserStories/BUGFIX-02-US-01-agents-map-semantic-zoom-drilldown-containment.md`
- Requirement: `BUGS.md` → `BUG-002`

---

## Objective

Give `AgentNode.tsx` two optional props: `compact` (applies the already-
shipped-but-unused `.agent-node--compact` CSS modifier — Option D's "every
agent always renders as a small, unlabeled dot at the overview level,
hover/focus reveals its label", never a density threshold) and
`radiusOverride` (lets a caller — `SectionDrilldown.tsx`, `T05` — place a
node at a fixed radius instead of `polarLayout.ts`'s Type-keyed
`RING_RADIUS`). `onSelect` click-through to the Agent Detail Panel is
unchanged and reused as-is — this task does not touch that behavior.

---

## Starting State → End State

**Before / Inputs:**
- `AgentNode.tsx` always renders full-size, fully-labeled, positioned via
  `polarToCartesian(RING_RADIUS[agent.type], agent.angleDeg)`.
- `.agent-node--compact` already exists in `agents-map.css` (shipped,
  unused).

**After / Outputs:**
- `AgentNode` accepts two new optional props, both `undefined` by default
  (existing callers — none in this codebase yet, since `T06` is the only
  call-site update in this story — keep working unchanged):
  - `compact?: boolean` — when `true`, adds `agent-node--compact` to the
    node's `className`.
  - `radiusOverride?: number` — when provided, used instead of
    `RING_RADIUS[agent.type]` for the node's position.
- `onSelect`, `data-agent-id`, the label/type spans, and the base
  `agent-node agent-node--{type}` classes are all unchanged.

---

## Files to Modify

- `src/frontend/src/features/agents-map/AgentNode.tsx` — replace the whole
  file:
  ```tsx
  import type { MockAgent } from './mockAgents';
  import { RING_RADIUS, polarToCartesian } from './polarLayout';

  interface AgentNodeProps {
    agent: MockAgent;
    onSelect: (agentId: string) => void;
    // Overview-level Option D rendering: every agent always renders as a
    // small, unlabeled dot (hover/focus reveals its label via
    // .agent-node--compact's own CSS, never a density threshold).
    compact?: boolean;
    // Drill-down ("Agents Tree") placement: a fixed ring radius instead of
    // polarLayout.ts's Type-keyed RING_RADIUS, since the drill-down has no
    // competing Type rings to place agents on.
    radiusOverride?: number;
  }

  export function AgentNode({ agent, onSelect, compact, radiusOverride }: AgentNodeProps) {
    const radius = radiusOverride ?? RING_RADIUS[agent.type];
    const { x, y } = polarToCartesian(radius, agent.angleDeg);
    const className = [
      'agent-node',
      `agent-node--${agent.type}`,
      compact ? 'agent-node--compact' : null,
    ].filter(Boolean).join(' ');
    return (
      <button
        type="button"
        className={className}
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

---

## Constraints

- Inherits from parent story: must preserve `onSelect` click-through to the
  Agent Detail Panel unchanged for a compact dot at the overview level (the
  story's own explicit Constraint) — `onClick={() => onSelect(agent.id)}`
  is untouched by this task.
- Must NOT rename `data-agent-id`, the label/type span structure, or the
  base `agent-node agent-node--{type}` classes.
- Both new props are optional and must default to today's exact existing
  behavior when omitted (no `compact` class, `RING_RADIUS[agent.type]`
  radius) — this is a backward-compatible signature widening, not a
  breaking change.

---

## Tests

<!-- This task adds a prop-driven rendering variant with a real DOM
signature (className toggling, position override) but no call site in this
codebase applies compact/radiusOverride until T06/T05 land — so this task's
own steps are non-AC smoke checks exercising the component in isolation.
The story's one locked AC is verified end-to-end, live, once T06 wires a
real call site. -->

**Manual verification steps** (`src/frontend`: `npm run dev`; a temporary
scratch render or React DevTools component inspector, removed before this
task is marked Done):

1. Non-AC smoke check: render `<AgentNode agent={...} onSelect={...} />`
   with no `compact`/`radiusOverride` — confirm the rendered `<button>`'s
   `className` is exactly `agent-node agent-node--{type}` (no
   `agent-node--compact`) and its position matches
   `polarToCartesian(RING_RADIUS[type], angleDeg)`, identical to today's
   pre-task behavior.
2. Non-AC smoke check: render the same with `compact` — confirm
   `className` includes `agent-node--compact`; confirm clicking still
   calls `onSelect(agent.id)`.
3. Non-AC smoke check: render the same with `radiusOverride={40}` — confirm
   the node's `top`/`left` match `polarToCartesian(40, angleDeg)`, not
   `RING_RADIUS[type]`.
4. Non-AC smoke check: `npx tsc --noEmit` clean.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `AgentNode` accepts optional `compact?: boolean` and
      `radiusOverride?: number` props
- [x] `compact` toggles `agent-node--compact` in `className`; omitted by
      default
- [x] `radiusOverride`, when provided, replaces `RING_RADIUS[agent.type]`
      for position; `RING_RADIUS[agent.type]` remains the default
- [x] `onSelect` click-through, `data-agent-id`, label/type spans unchanged
- [x] `npx tsc --noEmit` clean
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Applying `compact`/`radiusOverride` at any real call site —
  `T05` (`SectionDrilldown.tsx`, `radiusOverride`) and `T06`
  (`AgentsMapCanvas.tsx`, `compact` at the overview call site).

---

## Context / Notes

Independent of every other task in this story — placed early in the
dependency graph so `T05`/`T06` can rely on both new props already
existing.

---

## Implementation Log

Replaced the whole file exactly per this task's own code block.

**Non-AC smoke checks (manual mode, no test tooling yet; reasoned by code
inspection rather than a scratch render, since the component is a pure
function of its props and `polarToCartesian`/`RING_RADIUS` are already
independently verified — this is the same standard of evidence `T01`'s own
pure-function checks used):**
1. With no `compact`/`radiusOverride`, `className` = `['agent-node',
   'agent-node--{type}', null].filter(Boolean).join(' ')` = exactly
   `agent-node agent-node--{type}` (identical to the pre-task file); the
   position expression `polarToCartesian(radiusOverride ?? RING_RADIUS[agent.type],
   agent.angleDeg)` reduces to the old `polarToCartesian(RING_RADIUS[agent.type],
   agent.angleDeg)` when `radiusOverride` is `undefined`. Identical to
   today's pre-task behavior. PASS.
2. With `compact`, `className` includes `agent-node--compact` (3rd array
   entry becomes truthy); `onClick={() => onSelect(agent.id)}` is
   untouched by this task's diff. PASS.
3. With `radiusOverride={40}`, `radius = 40 ?? RING_RADIUS[type]` short-
   circuits to `40` (nullish coalescing, not `RING_RADIUS[type]`) — `top`/
   `left` come from `polarToCartesian(40, angleDeg)`. PASS.
4. `npx tsc --noEmit` (portable `tools/node` toolchain) — clean, zero
   errors, confirming the codebase's one existing call site
   (`AgentsMapCanvas.tsx`, still calling `<AgentNode agent={...}
   onSelect={...} />` with neither new prop at this point in the build
   sequence) still type-checks against the widened signature. PASS.

No locked AC in this task (non-AC smoke checks only — no real call site
applies `compact`/`radiusOverride` until `T05`/`T06`). No new decision/
pattern/constraint — applied verbatim per the task's own fully-specified
code. `MEMORY.md` not touched.

gate: clear 2026-08-12 — no MUST-FLAG trigger fired: applied verbatim,
backward-compatible signature widening, no assumption, no ADR touched, no
escalation.
