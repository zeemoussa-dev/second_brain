---
id: BUGFIX-02-US-01-T01
title: layoutAgents.ts / polarLayout.ts — layoutSectionDrilldown() full-360deg geometry
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

# BUGFIX-02-US-01-T01 — layoutAgents.ts / polarLayout.ts — layoutSectionDrilldown() geometry

## Parent Story

- Story: [[BUGFIX-02-US-01]] — `../UserStories/BUGFIX-02-US-01-agents-map-semantic-zoom-drilldown-containment.md`
- Requirement: `BUGS.md` → `BUG-002` — "Agents Map: sections with 4+ agents
  visually spill into neighboring sections"

---

## Objective

Add a new sibling function `layoutSectionDrilldown()` to `layoutAgents.ts`
(a full-360° agent spread for one Section's own drill-down "Agents Tree",
deliberately separate from the overview's per-Section wedge fan-out — per
the architect's Notes, conflating the two models in one function/constant
is `BUG-002`'s own root-cause shape) and a co-located
`DRILLDOWN_AGENT_RADIUS` constant in `polarLayout.ts`.

---

## Starting State → End State

**Before / Inputs:**
- `layoutAgents.ts` exports only `layoutAgents()`, which fans a Section's
  agents across a fixed `SECTION_ARC_SPAN_DEG = 80` arc centered on that
  Section's `hubAngleDeg` — the overview model, unchanged by this task.
- `polarLayout.ts` exports `CENTER`, `RING_RADIUS`, `HUB_RADIUS`,
  `BOUNDARY_RADIUS`, `polarToCartesian`. No drill-down radius exists yet.
- Reference geometry (already hand-derived and verified, per the approved
  `html-prototype/agents-map.html`'s own top-of-file breadcrumb, "Per-section
  drill-down positions use the same angle x radius trigonometry as the
  exploration's own `renderSectionTree()` — angle = idx/n * 360 - 90,
  radius = 40, agents spread evenly around the full circle").

**After / Outputs:**
- `polarLayout.ts` gains `export const DRILLDOWN_AGENT_RADIUS = 40;`
  alongside the existing `HUB_RADIUS`/`BOUNDARY_RADIUS` constants.
- `layoutAgents.ts` gains `export function layoutSectionDrilldown(sectionAgents: MockAgent[]): MockAgent[]`
  — returns a new array of the same agents with each `angleDeg` replaced by
  an evenly-spaced full-360° position (`index/n * 360 - 90`, matching the
  reference geometry above; `HUB_ANGLE_OFFSET_DEG` reused for the `-90`
  starting rotation rather than a second magic number). A single agent gets
  angle `-90` (top). Zero agents returns `[]`. Radius itself is not part of
  this function's output — the caller (`SectionDrilldown.tsx`, `T05`) applies
  `DRILLDOWN_AGENT_RADIUS` via `AgentNode`'s new `radiusOverride` prop
  (`T03`) at render time, keeping this function's job purely angular, the
  same separation of concerns `layoutAgents()` itself already has (angle
  here, ring radius via `polarLayout.ts`'s `RING_RADIUS` at render time).

---

## Files to Modify

- `src/frontend/src/features/agents-map/polarLayout.ts` — add, directly
  below the existing `HUB_RADIUS`/`BOUNDARY_RADIUS` constants:
  ```typescript
  // Section drill-down ("Agents Tree") ring radius — every agent in the
  // drilled-into Section spreads across the full 360deg at this one radius
  // (no Type-keyed rings here; the drill-down has no competing rings/KB to
  // read against, per the approved design). Matches the reference geometry
  // hand-derived and live-verified in html-prototype/agents-map.html
  // (BUG-002 fix, Option D).
  export const DRILLDOWN_AGENT_RADIUS = 40;
  ```

- `src/frontend/src/features/agents-map/layoutAgents.ts` — add, below the
  existing `layoutAgents()` function:
  ```typescript
  /** One Section's own agents -> that same set with angleDeg replaced by an
   * evenly-spaced full-360deg spread, for the drill-down "Agents Tree" view
   * (SectionDrilldown.tsx). Deliberately NOT a branch inside layoutAgents()
   * / SECTION_ARC_SPAN_DEG — conflating the overview's per-Section wedge
   * model and the drill-down's full-circle model in one function/constant
   * is BUG-002's own root-cause shape (a fixed arc that doesn't scale to
   * how much angular budget is actually available). sectionId/hub geometry
   * are irrelevant here since the drill-down centers on the Section's own
   * Hub, not the shared Knowledge Base. */
  export function layoutSectionDrilldown(sectionAgents: MockAgent[]): MockAgent[] {
    const n = sectionAgents.length;
    return sectionAgents.map((agent, index) => ({
      ...agent,
      angleDeg: n === 0 ? 0 : (index / n) * 360 + HUB_ANGLE_OFFSET_DEG,
    }));
  }
  ```
  (Reuses the existing `HUB_ANGLE_OFFSET_DEG` constant already in this file
  rather than a second `-90` literal — same purely-cosmetic starting
  rotation, same reasoning as `layoutAgents()`'s own use of it.)

---

## Constraints

- Inherits from parent story: frontend-only, no backend/API contract
  change; must not regress `REQ-SB-18-US-01`'s empty-Section handling (an
  empty `sectionAgents` array must return `[]`, not throw).
- Must NOT modify `layoutAgents()`'s own existing behavior, `SECTION_ARC_SPAN_DEG`,
  or any other exported symbol in either file — purely additive.
- `layoutSectionDrilldown()` must not read or depend on `hubAngleDeg` /
  section identity — it operates on a plain agent list, keeping the two
  layout models (overview wedge vs. drill-down full-circle) structurally
  independent, per the architect's Notes.

---

## Tests

<!-- This task's own change (two pure geometry additions) has no independent
DOM signature — its correctness is exercised through T05's/T06's rendering
of its output. Non-AC smoke checks only; the story's one locked AC is
verified end-to-end in T06. -->

**Manual verification steps** (`src/frontend`: `npm run dev`; browser
preview tool or a scratch Node/`tsx` snippet):

1. Non-AC smoke check: call `layoutSectionDrilldown([{id:'a',...},{id:'b',...},{id:'c',...},{id:'d',...},{id:'e',...}])`
   with 5 stub agents (any `sectionId`/`type`) — confirm 5 returned entries
   with `angleDeg` values `-90, -18, 54, 126, 198` (i.e. `-90 + index * 72`),
   each entry otherwise unchanged from its input.
2. Non-AC smoke check: call `layoutSectionDrilldown([])` — confirm it
   returns `[]` without throwing.
3. Non-AC smoke check: confirm `DRILLDOWN_AGENT_RADIUS` is exported from
   `polarLayout.ts` and equals `40`; confirm `npx tsc --noEmit` is clean
   after this task's own edits.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `polarLayout.ts` exports `DRILLDOWN_AGENT_RADIUS = 40`
- [x] `layoutAgents.ts` exports `layoutSectionDrilldown(sectionAgents)`,
      returning an evenly-spaced full-360° `angleDeg` per agent, starting at
      `HUB_ANGLE_OFFSET_DEG`
- [x] Zero-agent input returns `[]`; single-agent input returns that agent
      at `HUB_ANGLE_OFFSET_DEG`
- [x] `layoutAgents()` and `SECTION_ARC_SPAN_DEG` unchanged
- [x] `npx tsc --noEmit` clean
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Applying `DRILLDOWN_AGENT_RADIUS` at render time (`AgentNode`'s
  `radiusOverride` prop) — `T03`.
- Consuming `layoutSectionDrilldown()` to actually render a drill-down —
  `T05` (`SectionDrilldown.tsx`).

---

## Context / Notes

This task is a pure-function, zero-JSX addition — deliberately first in the
dependency graph so every later task (`T05`, transitively `T06`) can rely on
both new exports already existing.

---

## Implementation Log

Applied exactly per this task's own `## Files to Modify` code blocks — no
deviation.

- `polarLayout.ts`: added `export const DRILLDOWN_AGENT_RADIUS = 40;` below
  `HUB_RADIUS`/`BOUNDARY_RADIUS`, verbatim comment included.
- `layoutAgents.ts`: added `export function layoutSectionDrilldown(sectionAgents)`
  below `layoutAgents()`, reusing `HUB_ANGLE_OFFSET_DEG`, verbatim.

**Non-AC smoke checks (manual mode, no test tooling yet):**
1. Traced `layoutSectionDrilldown()` by hand against 5 stub agents
   (`n=5`): `angleDeg` = `-90 + index*72` = `-90, -18, 54, 126, 198` for
   indices 0-4 — matches the task's own expected values exactly; every
   other field on each returned agent is a spread of the input, unchanged.
   PASS.
2. Traced the zero-agent case: `n === 0` short-circuits `angleDeg` per
   entry, and `sectionAgents.map(...)` over `[]` returns `[]` — no throw.
   PASS.
3. `DRILLDOWN_AGENT_RADIUS` confirmed exported and equal to `40` (read
   back from the edited file). `npx tsc --noEmit` (via the portable
   `tools/node` toolchain, `MEMORY.md`'s standing "no admin rights" /
   portable-Node constraint) ran clean, zero errors, after this task's own
   edits. PASS.

No locked AC in this task (non-AC smoke checks only, per the task's own
`## Tests` note — the story's one locked AC is verified end-to-end in
`T06`).

No new decision/pattern/constraint — pure application of the task's own
fully-specified code. `MEMORY.md` not touched by this task.

gate: clear 2026-08-12 — no MUST-FLAG trigger fired: applied verbatim,
purely additive, no assumption, no ADR touched, no escalation.
