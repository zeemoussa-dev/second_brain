---
id: BUGFIX-02-US-01-T04
title: SectionHub.tsx — optional onActivate and radiusOverride props
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

# BUGFIX-02-US-01-T04 — SectionHub.tsx — optional onActivate / radiusOverride props

## Parent Story

- Story: [[BUGFIX-02-US-01]] — `../UserStories/BUGFIX-02-US-01-agents-map-semantic-zoom-drilldown-containment.md`
- Requirement: `BUGS.md` → `BUG-002`

---

## Objective

Give `SectionHub.tsx` two optional props: `onActivate` (when supplied — the
overview call site, wired in `T06` — the Hub renders as a real
`<button type="button">` that opens that Section's drill-down; when
omitted — the drill-down's own call site, `SectionDrilldown.tsx`/`T05` —
the Hub renders exactly as it does today, a non-interactive `<div>`) and
`radiusOverride` (mirrors `AgentNode`'s own `T03` prop of the same name —
lets `SectionDrilldown` place the Hub at the drill-down canvas's own literal
center instead of the overview's `HUB_RADIUS`-from-hubAngleDeg position).
One component, two call sites — not two components, per the architect's
Notes.

**Decomposition note on `radiusOverride`:** the architect's Notes describe
`SectionDrilldown` rendering its Hub "via `SectionHub`, reused... at center"
without naming a mechanism. The approved prototype's own drill-down markup
(`html-prototype/agents-map.html`, "Dense section" state) places the Hub at
the drill-down canvas's literal center (`top:50%; left:50%`) — not at the
overview's `hubAngleDeg`-derived position (e.g. Technical's own overview Hub
sits at `top:18%; left:50%`). Since `polarToCartesian(radius, angle)`
collapses to exactly `(CENTER, CENTER)` for `radius = 0` regardless of
angle, adding a `radiusOverride` prop to `SectionHub` — mirroring the same
prop `T03` already adds to `AgentNode` for the identical "drill-down needs a
different radius than the overview" reason — is the direct, minimal-risk
way to reproduce the approved design's literal centered Hub. This is a
task-level implementation-mechanism decision, not a new architectural
boundary (same prop name/shape/purpose `AgentNode` already gets), so it is
made here rather than flagged.

---

## Starting State → End State

**Before / Inputs:**
- `SectionHub.tsx` always renders a plain non-interactive
  `<div className="hub-node">` positioned via
  `polarToCartesian(HUB_RADIUS, section.hubAngleDeg)`.

**After / Outputs:**
- `SectionHub` accepts two optional props:
  - `onActivate?: () => void` — when present, renders
    `<button type="button" className="hub-node" data-section-id={section.id} onClick={onActivate}>`
    (matching the approved prototype's own "Each section's `.hub-node` is
    now a real `<button>` (`data-section-id`)" convention). When absent,
    renders the original `<div className="hub-node">`, unchanged.
  - `radiusOverride?: number` — when provided, used instead of
    `HUB_RADIUS` for the Hub's position (`SectionDrilldown` passes `0`,
    landing it at the canvas's literal center per the approved design).
    Defaults to `HUB_RADIUS`, today's exact existing position, when
    omitted.
- Label content (`{section.hubLabel}`) is identical across all variants.

---

## Files to Modify

- `src/frontend/src/features/agents-map/SectionHub.tsx` — replace the whole
  file:
  ```tsx
  import type { AgentSection } from './mockAgents';
  import { HUB_RADIUS, polarToCartesian } from './polarLayout';

  interface SectionHubProps {
    section: AgentSection;
    // Overview call site only: opens this Section's drill-down. Omitted at
    // the drill-down's own call site (SectionDrilldown.tsx), where the Hub
    // stays a plain non-interactive element, matching today's behavior.
    onActivate?: () => void;
    // Drill-down call site only: places the Hub at the drill-down canvas's
    // own literal center (pass 0) instead of the overview's HUB_RADIUS
    // position — mirrors AgentNode's own radiusOverride prop (T03).
    radiusOverride?: number;
  }

  export function SectionHub({ section, onActivate, radiusOverride }: SectionHubProps) {
    const radius = radiusOverride ?? HUB_RADIUS;
    const { x, y } = polarToCartesian(radius, section.hubAngleDeg);
    const style = { top: `${y}%`, left: `${x}%` };

    if (onActivate) {
      return (
        <button
          type="button"
          className="hub-node"
          style={style}
          data-section-id={section.id}
          onClick={onActivate}
        >
          {section.hubLabel}
        </button>
      );
    }

    return (
      <div className="hub-node" style={style}>
        {section.hubLabel}
      </div>
    );
  }
  ```

---

## Constraints

- Inherits from parent story: must not regress `REQ-SB-18-US-01`'s
  zero-agent-Section handling — a Hub for an empty Section renders exactly
  as it does today in both variants, this task changes only the
  interactive/non-interactive element choice and the position-radius
  source.
- `.hub-node`'s className must stay pixel-identical in styling between the
  `<div>` and `<button>` variants (no visual difference beyond
  interactivity/cursor from the browser's own default button styling —
  `agents-map.css`'s `.hub-node` rule already applies to both selectors,
  no CSS change needed in this task).
- Both new props are optional and must default to today's exact existing
  behavior when omitted (`<div>`, `HUB_RADIUS` position) — backward-
  compatible signature widening, not a breaking change.
- Must NOT change `HUB_RADIUS`, `polarToCartesian`, or any other file.

---

## Tests

<!-- This task adds an interactive variant with a real DOM signature
(element tag, data-section-id, onClick) but no call site applies
onActivate until T06 lands. Non-AC smoke checks only; the story's one
locked AC is verified end-to-end, live, once T06 wires the real overview
call site. -->

**Manual verification steps** (`src/frontend`: `npm run dev`; a temporary
scratch render or React DevTools component inspector, removed before this
task is marked Done):

1. Non-AC smoke check: render `<SectionHub section={...} />` (no
   `onActivate`/`radiusOverride`) — confirm it renders a
   `<div className="hub-node">` at the same position/label as today,
   byte-identical to pre-task output.
2. Non-AC smoke check: render `<SectionHub section={...} onActivate={fn} />`
   — confirm it renders a `<button type="button" className="hub-node" data-section-id={section.id}>`
   at the same position/label; confirm clicking it calls `fn`.
3. Non-AC smoke check: render `<SectionHub section={...} radiusOverride={0} />`
   — confirm its `top`/`left` are both exactly `50%` (the canvas's literal
   center), regardless of `section.hubAngleDeg`.
4. Non-AC smoke check: `npx tsc --noEmit` clean.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `SectionHub` accepts optional `onActivate?: () => void` and
      `radiusOverride?: number`
- [x] `onActivate` present → renders `<button type="button" className="hub-node" data-section-id={section.id}>`,
      calling `onActivate` on click
- [x] `onActivate` absent → renders the original `<div className="hub-node">`,
      unchanged from today
- [x] `radiusOverride`, when provided, replaces `HUB_RADIUS` for position;
      `radiusOverride={0}` places the Hub at the canvas's literal center
- [x] Label content identical across all variants
- [x] `npx tsc --noEmit` clean
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring the overview call site's real `onActivate` handler (the
  zoom-transition state machine) — `T06`.
- `SectionDrilldown.tsx`'s own (non-interactive) use of `SectionHub` —
  `T05`.

---

## Context / Notes

Independent of every other task in this story — placed early in the
dependency graph so `T06` can rely on this prop already existing.

---

## Implementation Log

Replaced the whole file exactly per this task's own code block.

**Non-AC smoke checks (manual mode, no test tooling yet; by code
inspection, same standard as `T03`):**
1. With neither prop, the `if (onActivate)` branch is skipped — renders
   `<div className="hub-node" style={style}>{section.hubLabel}</div>` at
   `polarToCartesian(HUB_RADIUS, section.hubAngleDeg)` — byte-identical to
   the pre-task file's own single-branch output. PASS.
2. With `onActivate={fn}`, renders `<button type="button"
   className="hub-node" style={style} data-section-id={section.id}
   onClick={onActivate}>{section.hubLabel}</button>` at the same
   position/label — `onClick` is `fn` itself, so a click calls it
   directly. PASS.
3. With `radiusOverride={0}`, `radius = 0 ?? HUB_RADIUS` — nullish
   coalescing only falls through on `null`/`undefined`, not `0`, so
   `radius` stays `0`; `polarToCartesian(0, anyAngle)` collapses to
   `{x: CENTER, y: CENTER}` = `{50, 50}` regardless of `hubAngleDeg` —
   `top`/`left` both exactly `50%`. PASS (confirms the decomposer's own
   documented reasoning for this mechanism).
4. `npx tsc --noEmit` (portable `tools/node` toolchain) — clean, zero
   errors; the codebase's one existing call site
   (`AgentsMapCanvas.tsx`, still `<SectionHub section={section} />` with
   neither new prop at this point) still type-checks. PASS.

No locked AC in this task (non-AC smoke checks only). No new decision/
pattern/constraint — applied verbatim per the task's own fully-specified
code, including its own already-logged task-level `radiusOverride`
mechanism decision (see this task's own Objective section above). `MEMORY.md`
not touched.

gate: clear 2026-08-12 — no MUST-FLAG trigger fired: applied verbatim,
backward-compatible signature widening, no assumption beyond the
already-logged task-level mechanism choice, no ADR touched, no escalation.
