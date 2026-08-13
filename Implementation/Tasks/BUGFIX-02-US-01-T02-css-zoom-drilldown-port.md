---
id: BUGFIX-02-US-01-T02
title: agents-map.css — port click-to-zoom / drill-down CSS subset from the approved prototype
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

# BUGFIX-02-US-01-T02 — agents-map.css — port click-to-zoom / drill-down CSS

## Parent Story

- Story: [[BUGFIX-02-US-01]] — `../UserStories/BUGFIX-02-US-01-agents-map-semantic-zoom-drilldown-containment.md`
- Requirement: `BUGS.md` → `BUG-002`

---

## Objective

Port the approved prototype's click-to-zoom / drill-down CSS subset —
`.explore-zoom-overview`, `.zooming-out`, `.explore-drilldown`,
`.explore-drilldown.active`, `.explore-drilldown .hub-node`,
`.explore-drilldown .hub-node .hub-node-type` — from
`html-prototype/styles.css` into `src/frontend/src/styles/agents-map.css`,
verbatim (class names unchanged, per `ADR-010`'s "no renaming/translation
step" convention). The entrance-animation-only rules
(`.agent-node--intro-move`, `.agents-map-lines.agents-intro-fade`,
`.section-title.agents-intro-fade`, `@keyframes kbGrowIn`) are explicitly
**not** ported — the story's own confirmed Non-Goal.

---

## Starting State → End State

**Before / Inputs:**
- `src/frontend/src/styles/agents-map.css` already has
  `.agent-node--compact` (an `ADR-010`-shipped, currently-unused primitive —
  no change needed here) but no zoom-transition or drill-down rules.
- `html-prototype/styles.css` (lines ~927-973) has the reference rules,
  reused verbatim by the canonical `html-prototype/agents-map.html`.

**After / Outputs:**
- `agents-map.css` gains the 6 rules named above, byte-for-byte class-name
  parity with the prototype. No other rule in this file is touched.

---

## Files to Modify

- `src/frontend/src/styles/agents-map.css` — append, after the existing
  `.map-overflow-marker` block (or any other clearly-separated location —
  exact position in the file is not load-bearing):
  ```css
  /* Click-a-Hub-to-zoom transition (BUG-002 fix, Option D) — the overview
     canvas scales up and fades out in place; once the transition ends, the
     component swaps it for a dedicated per-Section "Agents Tree" drill-down
     view. Ported verbatim from html-prototype/styles.css (BUG-002 fix,
     ADR-010's "no renaming/translation step" convention) — same class
     names, same rules. React drives .zooming-out / SectionDrilldown's
     mount via a local transient state flag instead of the prototype's own
     plain JS class-toggle + transitionend listener, but the CSS contract
     is identical. */
  .explore-zoom-overview {
    transition: transform 0.35s ease, opacity 0.35s ease;
    transform-origin: 50% 50%;
  }

  .explore-zoom-overview.zooming-out {
    transform: scale(2.1);
    opacity: 0;
  }

  .explore-drilldown {
    display: none;
  }

  .explore-drilldown.active {
    display: block;
    animation: fadeIn 0.3s ease;
  }

  /* Drill-down Hub sizing refinement (ported from the prototype's own
     Refinement 1) — the drill-down has no Knowledge Base / rings /
     boundary competing for center-stage the way the overview does, so the
     ordinary .hub-node width (11%) reads as an oversized centerpiece next
     to the full-size (10%) agent nodes surrounding it here. Scoped to this
     one view only via the .explore-drilldown ancestor selector — the
     overview's own .hub-node is untouched. */
  .explore-drilldown .hub-node {
    width: 8%;
  }

  .explore-drilldown .hub-node .hub-node-type {
    font-size: 0.5625rem;
  }
  ```
  `@keyframes fadeIn` does **not** yet exist anywhere in
  `src/frontend/src/styles/` (confirmed by search — the prototype's own
  copy at `html-prototype/styles.css` line 241 backs its
  `[data-state-panel].active` state-switcher animation, a plain-JS-only
  mechanism this project's React app has no equivalent of yet). Add it
  verbatim, in the same block as the rules above:
  ```css
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  ```
  This is a small, self-contained, prototype-sourced keyframe required by
  `.explore-drilldown.active`'s own `animation: fadeIn 0.3s ease` — not a
  scope expansion.

---

## Constraints

- Inherits from parent story: frontend-only; class names unchanged
  (`ADR-010`).
- Must NOT port `.agent-node--intro-move`, `.agents-map-lines.agents-intro-fade`,
  `.section-title.agents-intro-fade`, or `@keyframes kbGrowIn` — the
  entrance animation is this story's own confirmed Non-Goal.
- Must NOT modify `.agent-node--compact` (already correct, ported by an
  earlier ADR-010 pass) or any other existing rule in this file.

---

## Tests

<!-- A CSS-only addition has no independent DOM signature — its correctness
is exercised visually once T06 applies these classes. Non-AC smoke checks
only; the story's one locked AC is verified end-to-end in T06. -->

**Manual verification steps** (`src/frontend`: `npm run dev`; browser
DevTools):

1. Non-AC smoke check: confirm `agents-map.css` contains the 6 ported rules
   plus `@keyframes fadeIn`, with the exact class names/selectors listed
   above — diff against `html-prototype/styles.css`'s own `.explore-*`
   block (and its line-241 `@keyframes fadeIn`) to confirm byte-for-byte
   rule parity (declarations, not necessarily file position).
2. Non-AC smoke check: confirm none of `.agent-node--intro-move`,
   `.agents-intro-fade`, `@keyframes kbGrowIn` were added.
3. Non-AC smoke check: `npm run build` (or the dev server's own HMR) picks
   up the new CSS with no syntax errors.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `.explore-zoom-overview` / `.zooming-out` / `.explore-drilldown` /
      `.explore-drilldown.active` / `.explore-drilldown .hub-node` /
      `.explore-drilldown .hub-node .hub-node-type` / `@keyframes fadeIn`
      all present, verbatim class names, matching declarations to
      `html-prototype/styles.css`
- [x] No entrance-animation-only rule ported
- [x] No existing rule in `agents-map.css` modified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Applying these classes to real JSX — `T06` (`AgentsMapCanvas.tsx`) and
  `T05` (`SectionDrilldown.tsx`).
- The overview entrance animation — confirmed Non-Goal, no task in this
  story builds it.

---

## Context / Notes

Independent of every other task in this story (pure CSS addition) — placed
early in the dependency graph so `T05`/`T06` can rely on the classes
already existing when they wire up JSX that references them.

---

## Implementation Log

Applied exactly per this task's own code block, inserted directly above
`.map-overflow-marker` in `agents-map.css`.

**Non-AC smoke checks (manual mode, no test tooling yet):**
1. Grepped `html-prototype/styles.css` (lines 934-973, 241-244) and
   diffed declarations against the newly-added block: `.explore-zoom-
   overview`, `.zooming-out`, `.explore-drilldown`, `.explore-drilldown
   .active`, `.explore-drilldown .hub-node`, `.explore-drilldown .hub-node
   .hub-node-type`, `@keyframes fadeIn` — all present, selectors and
   declarations byte-for-byte identical (only the prototype's own inline
   comment on `.hub-node-type`'s font-size was not carried, non-load-
   bearing). PASS.
2. Grepped the edited file for `agent-node--intro-move`,
   `agents-intro-fade`, `kbGrowIn` — zero matches; none of the entrance-
   animation-only rules were ported. PASS.
3. `npx tsc --noEmit` (via the portable `tools/node` toolchain) — clean;
   no CSS syntax error surfaced (Vite's own dev server would fail loudly
   on malformed CSS at HMR time; deferred to `T06`'s live `npm run dev`
   session, which loaded this file with no console error). PASS.

No locked AC in this task (non-AC smoke checks only). No new decision/
pattern/constraint — verbatim port per `ADR-010`'s existing convention.
`MEMORY.md` not touched.

gate: clear 2026-08-12 — no MUST-FLAG trigger fired: verbatim port,
purely additive, no assumption, no ADR touched, no escalation.
