---
id: REQ-SB-18-US-01-T06
title: AgentsMapCanvas.tsx N-generic section-boundary dividers + SectionHub.tsx neutral color
parent_story: REQ-SB-18-US-01
requirement_id: REQ-SB-18
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-18-US-01-T05]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-18-US-01-T06 — AgentsMapCanvas.tsx N-generic dividers + SectionHub.tsx neutral color

## Parent Story

- Story: [[REQ-SB-18-US-01]] — `../UserStories/REQ-SB-18-US-01-dynamic-agent-sections-and-assignment.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-18 *Dynamic Agent Sections & Agent-to-Section Assignment*

---

## Objective

Generalize `AgentsMapCanvas.tsx`'s currently-fixed 3 `section-boundary`
divider lines to N lines (one at each pair of adjacent hub angles'
midpoint), replace the per-section-Type stroke coloring on the KB→Hub
spoke-lines and Hub-cluster-lines with a neutral color, and drop
`SectionHub.tsx`'s per-Type `hub-node--{type}` modifier class — a Section
can now hold agents of any Type, so it no longer has one Type to tint by
(`ADR-014` point 6). Renders however many sections `T05`'s `layoutAgents`
computes, including a section with zero agents (Scenario 7).

---

## Starting State → End State

**Before / Inputs:**
- `T05` has landed `layoutAgents` computing N sections with evenly-spaced
  `hubAngleDeg`s, and `AgentSection` has no `type` field.
- `AgentsMapCanvas.tsx` currently renders exactly 3 hardcoded
  `section-boundary` lines at fixed coordinates, and colors `spoke-line`/
  `cluster-line` strokes via `var(--agent-color-${section.type})`
  (`section.type` no longer exists after `T05`).
- `SectionHub.tsx` currently renders `className="hub-node hub-node--
  ${section.type}"` and an inner `{section.type} section` label.

**After / Outputs:**
- `AgentsMapCanvas.tsx` renders N `section-boundary` lines, one per
  adjacent-hub-angle midpoint (wrapping around 360°), and both
  `spoke-line`/`cluster-line` strokes render `var(--color-accent)`
  (neutral) instead of a per-Type color.
- `SectionHub.tsx` renders a plain `hub-node` (no `--{type}` modifier —
  CSS's own `--hub-color, var(--color-accent)` fallback already renders
  it neutral with zero CSS changes needed) and drops the now-meaningless
  Type label.
- A section with zero agents still renders its `SectionHub`/spoke-line
  (no cluster-lines, since there are no agents to connect) — Scenario 7.

---

## Files to Modify

- `src/frontend/src/features/agents-map/AgentsMapCanvas.tsx`:
  - Add a local constant near the top of the file, alongside
    `SECTION_TITLE_RADIUS`:
    ```typescript
    // Section-boundary dividers start at the same inner radius the KB->Hub
    // spoke-lines conceptually originate from (matches the prior fixed
    // geometry's r≈18 starting point — html-prototype/agents-map.html).
    const SECTION_BOUNDARY_INNER_RADIUS = 18;
    ```
  - Replace the three hardcoded `<line className="section-boundary" .../>`
    elements with a computed block:
    ```tsx
    {sections.map((section, index) => {
      const sortedAngles = [...sections.map((s) => s.hubAngleDeg)].sort((a, b) => a - b);
      const currentIndex = sortedAngles.indexOf(section.hubAngleDeg);
      const nextAngle = currentIndex + 1 < sortedAngles.length
        ? sortedAngles[currentIndex + 1]
        : sortedAngles[0] + 360;
      const midAngle = (sortedAngles[currentIndex] + nextAngle) / 2;
      const inner = polarToCartesian(SECTION_BOUNDARY_INNER_RADIUS, midAngle);
      const outer = polarToCartesian(BOUNDARY_RADIUS, midAngle);
      return (
        <line
          key={`${section.id}-boundary`}
          className="section-boundary"
          x1={inner.x}
          y1={inner.y}
          x2={outer.x}
          y2={outer.y}
        />
      );
    })}
    ```
    (Recomputing `sortedAngles` per-iteration is a small, deliberate
    simplicity-over-micro-optimization choice — `sections.length` is at
    most a handful of user-created entries, not a hot loop.)
  - In the existing "KB -> Hub spoke-line per section" block, change
    `stroke={`var(--agent-color-${section.type})`}` to
    `stroke="var(--color-accent)"`.
  - In the existing "Per-section cluster-lines" block, change
    `const stroke = `var(--agent-color-${section.type})`;` to
    `const stroke = 'var(--color-accent)';`. The rest of that block
    (rendering zero cluster-lines when `sectionAgents` is empty) is
    already correct as-is — an empty-agent section's `agentPoints` array
    is empty, so the `lines` array it builds and returns is empty too, no
    change needed there.

- `src/frontend/src/features/agents-map/SectionHub.tsx` — replace the
  whole file:
  ```tsx
  import type { AgentSection } from './mockAgents';
  import { HUB_RADIUS, polarToCartesian } from './polarLayout';

  export function SectionHub({ section }: { section: AgentSection }) {
    const { x, y } = polarToCartesian(HUB_RADIUS, section.hubAngleDeg);
    return (
      <div
        className="hub-node"
        style={{ top: `${y}%`, left: `${x}%` }}
      >
        {section.hubLabel}
      </div>
    );
  }
  ```
  (Dropping the `hub-node--{type}` modifier class means every hub renders
  via `.hub-node`'s own `--hub-color, var(--color-accent)` CSS fallback —
  no CSS file edit needed. The `.hub-node--worker/producer/expert` rules
  in `agents-map.css` become unused dead code; leaving them in place is
  deliberate — pruning unused CSS is not this task's job and risks an
  unrelated diff.)

---

## Constraints

- Inherits from parent story: `ADR-010`'s class-name-verbatim convention
  (`.section-boundary`, `.spoke-line`, `.cluster-line`, `.hub-node` all
  keep their existing class names — only the computed count/coloring
  changes); `ADR-014` point 6.
- Must NOT change `AgentsMapCanvas.tsx`'s KB element, ring circles, radar
  spokes, ring labels, or `AgentNode`/`SECTION_TITLE_RADIUS` rendering —
  only the `section-boundary` line count and the spoke-/cluster-line
  stroke color.
- Must NOT modify `agents-map.css` — the neutral color comes from the
  CSS's own pre-existing fallback (`--hub-color, var(--color-accent)`)
  once the `--{type}` modifier class is no longer applied; no new rule
  needed.
- A section with zero agents must still render its own `SectionHub` and
  spoke-line — do not filter sections down to only non-empty ones
  anywhere in this file (the existing `hasAgents = sections.length > 0 &&
  agents.length > 0` first-run gate is a page-level empty-state check, not
  a per-section filter, and stays as-is).

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `.venv\Scripts\uvicorn app.main:app --reload --port 8001`;
browser preview tool):

1. **[REQ-SB-18-US-01-AC-08]** With the real backend seeded (5 sections:
   Technical/Sales/Productivity/Customers/Products, all 5 agents
   defaulted to `"technical"` per `T02`'s seed — Sales/Productivity/
   Customers/Products each have zero agents at this point in the build
   sequence), load `/`. Confirm exactly 5 `.hub-node` elements render (one
   per section, including the 4 zero-agent ones), each showing its
   section's `hubLabel` text (e.g. "Sales Hub"), and exactly 5
   `.section-boundary` lines render (one per adjacent-hub-angle
   midpoint). Confirm no `.cluster-line` connects to any zero-agent
   section's hub (only `Technical`'s hub has cluster-lines, to its 5
   agents).
2. Non-AC smoke check: confirm every `.hub-node` renders with the same
   neutral accent color (no per-section color variation) — visually
   inspect or confirm via computed style that no `.hub-node--worker`/
   `--producer`/`--expert` class is present on any `.hub-node` element.
   Confirm every `.spoke-line` and `.cluster-line` renders the same
   neutral stroke color.
3. Non-AC smoke check: zero console errors/warnings on load.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-08** (Scenario 7) — a zero-agent section's hub renders on the
      map, with no code change/restart required to reflect a section
      created in `T02`'s seed or via later CRUD
- [ ] N `.section-boundary` lines render, one per adjacent-hub-angle
      midpoint (wrapping around 360°), replacing the fixed 3
- [ ] `.hub-node` renders with no per-Type modifier class; spoke-lines and
      cluster-lines render a neutral stroke color
- [ ] KB element, ring circles, radar spokes, ring labels, `AgentNode`
      rendering unchanged
- [ ] `agents-map.css` not modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- `SectionsCard.tsx`, `settingsApiClient.ts`'s CRUD calls — `T07`.
- `AgentDetailPanel.tsx`'s Section picker (Scenarios 5, 6, 8 — `AC-06`,
  `AC-07`, `AC-09`) — `T08`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-014` created at
`/plan-tasks` step 1) — the human reviews `ADR-014` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

---

## Implementation Log

**2026-08-11 — Done.** `AgentsMapCanvas.tsx`: added
`SECTION_BOUNDARY_INNER_RADIUS`; replaced the 3 hardcoded
`section-boundary` lines with the N-generic adjacent-midpoint computation;
changed the KB->Hub spoke-line and per-section cluster-line strokes to
`var(--color-accent)`, exactly per the task's own code block.
`SectionHub.tsx` replaced whole-file per the task's own code — plain
`hub-node` class, no `--{type}` modifier, dropped the Type label.

**Assumption logged (scope-internal, not an escalation):** this task's own
`Files to Modify` diff for `AgentsMapCanvas.tsx` covers only the
`section-boundary`/`spoke-line`/`cluster-line` blocks, but a third,
untouched spot in the same file — the section-title's `<span
className="section-title-accent" style={{ background:
\`var(--agent-color-${'{'}section.type{'}'})\` }} />` — also read the
now-dropped `AgentSection.type` field (removed by `T05`'s `mockAgents.ts`
edit), which would have been a TypeScript compile error (`npx tsc
--noEmit` caught it) left unaddressed. This is the exact same "Section no
longer has one Type to tint by" reasoning `ADR-014` point 6 already gives
for the two spots this task's own diff explicitly names, so fixed it the
same way (`var(--color-accent)`) rather than leaving the build broken —
logged here for human spot-check per Pipeline.md's "scope-internal
judgement calls are not escalations" rule, since it's a small, same-file,
same-pattern fix, not a new file/dependency/interface change.

Live verification (real backend `:8001`, real frontend `npm run dev`
`:5173`, headless-Chrome-via-CDP):
- **[REQ-SB-18-US-01-AC-08]** Loaded `/` with the real seeded backend (5
  sections, all 5 agents defaulted to `"technical"`). DOM inspection
  confirmed: exactly 5 `.hub-node` elements (`Technical Hub`, `Sales Hub`,
  `Productivity Hub`, `Customers Hub`, `Products Hub` — the 4 zero-agent
  sections' hubs all render), exactly 5 `.section-boundary` lines, and
  exactly 15 `.cluster-line` elements (Technical's 5-agent complete graph:
  5 hub-to-agent + `C(5,2)=10` agent-agent pairs = 15) — zero cluster-lines
  connect to any zero-agent section's hub.
- Non-AC smoke check: every `.hub-node` has zero `hub-node--*` modifier
  classes (confirmed via `classList` inspection across all 5); every
  `.spoke-line`/`.cluster-line` renders `stroke="var(--color-accent)"`
  (confirmed the full set of distinct stroke values across both is exactly
  `["var(--color-accent)"]`).
- Non-AC smoke check: zero console errors/warnings across the load (CDP
  `Runtime.consoleAPICalled`/`exceptionThrown` listener captured only the
  expected Vite HMR/React-DevTools-suggestion messages).

KB element, ring circles, radar spokes, ring labels, `AgentNode` rendering
unchanged — confirmed by diff (only the three named blocks plus the
logged section-title-accent fix were touched). `agents-map.css` not
modified — confirmed by diff.

gate: clear 2026-08-11 — no MUST-FLAG trigger fired. The section-title-
accent fix above is a scope-internal judgement call (logged for
spot-check), not a MUST-FLAG trigger — same file already in scope, same
neutral-color pattern the task's own two other edits already establish,
no new dependency/interface/ADR deviation.
