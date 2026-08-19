---
id: REQ-SB-38-US-01-T02
title: agents-map.css — port clickable .map-overflow-marker shape from the approved prototype
parent_story: REQ-SB-38-US-01
requirement_id: REQ-SB-38
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-38-US-01-T02 — agents-map.css — port clickable .map-overflow-marker shape

## Parent Story

- Story: [[REQ-SB-38-US-01]] — `../UserStories/REQ-SB-38-US-01-agents-map-density-clustering.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-38 *Agents Map Density Clustering*

---

## Objective

`src/frontend/src/styles/agents-map.css` currently has an earlier,
never-instantiated static-chip version of `.map-overflow-marker` (neutral
border, no hover state, no inner-span structure). Replace it with the
prototype's current, real-button version — `html-prototype/styles.css`'s
`.map-overflow-marker` block plus its `:hover`/`:focus-visible` state and
new `.map-overflow-marker-count`/`.map-overflow-marker-label` inner spans —
ported verbatim (`ADR-010`'s "no renaming/translation step" convention).

---

## Starting State → End State

**Before / Inputs:**
- `src/frontend/src/styles/agents-map.css` (current `.map-overflow-marker`
  block, ~line 328): a static neutral chip — `--color-surface-raised`
  background, `--color-border` dashed border, no hover/focus rule, single
  flat text node (no inner spans).
- `html-prototype/styles.css` (~line 588 onward): the current, real
  `<button>`-shaped version — `--color-accent` dashed border + tinted glow
  at rest (matching `.hub-node`'s own resting treatment), a hover-lift +
  glow on `:hover`/`:focus-visible` (matching `.agent-node`'s own
  hover-lift), and `.map-overflow-marker-count` (bold, accent-colored
  number) / `.map-overflow-marker-label` (small, muted "+") inner spans
  mirroring `.hub-node`'s own bold-main-text + small-muted-subtext
  structure.

**After / Outputs:**
- `agents-map.css`'s `.map-overflow-marker` block, plus the two new
  `:hover`/`:focus-visible` and `.map-overflow-marker-count`/`-label`
  rules, match the prototype byte-for-byte (declarations, not necessarily
  file position). No other rule in this file is touched.

---

## Files to Modify

- `src/frontend/src/styles/agents-map.css` — replace the existing
  `.map-overflow-marker` block (~line 328) with the prototype's current
  version, and add the `:hover`/`:focus-visible` rule plus
  `.map-overflow-marker-count`/`.map-overflow-marker-label`, all ported
  verbatim from `html-prototype/styles.css` (~lines 588-631).

---

## Constraints

- Inherits from parent story: frontend-only; class names unchanged
  (`ADR-010`).
- Verbatim port — no new class names, no renamed selectors, no altered
  color tokens beyond what the prototype itself specifies.
- Must not modify any other existing rule in `agents-map.css`.

---

## Tests

<!-- A CSS-only change has no independent DOM signature — its correctness
is exercised visually once T04 applies these classes. Non-AC smoke checks
only; the story's locked ACs that depend on this styling are verified
end-to-end in T04, per BUGFIX-02-US-01-T02's own established precedent for
this exact file. -->

**Manual verification steps** (`src/frontend`: `npm run dev`; browser
DevTools):

1. Non-AC smoke check: diff the new `.map-overflow-marker` block (and its
   `:hover`/`:focus-visible` rule, `.map-overflow-marker-count`/`-label`)
   against `html-prototype/styles.css`'s current version — confirm
   byte-for-byte declaration parity.
2. Non-AC smoke check: confirm the old static-chip declarations
   (`--color-border` dashed border, no hover rule, no inner-span classes)
   are fully replaced, not left alongside the new block.
3. Non-AC smoke check: `npm run build` (or the dev server's own HMR) picks
   up the new CSS with no syntax errors.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `.map-overflow-marker` matches the prototype's current clickable-
      button shape (accent border/glow at rest)
- [x] `.map-overflow-marker:hover`/`:focus-visible` hover-lift + glow rule
      added, matching the prototype
- [x] `.map-overflow-marker-count`/`.map-overflow-marker-label` inner-span
      rules added, matching the prototype
- [x] No other existing rule in `agents-map.css` modified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Applying these classes to real JSX / rendering the marker element — `T04`.
- The cluster-scoped drill-down view — `T03`.
- `layoutAgents.ts`'s clustering logic — `T01`.

---

## Context / Notes

Independent of every other task in this story (pure CSS change, same
precedent as `BUGFIX-02-US-01-T02`) — placed early in the dependency graph
so `T04` can rely on the classes already existing when it wires up JSX that
references them.

---

## Implementation Log

**2026-08-14 — coder.** Replaced the old static-chip `.map-overflow-marker`
block with the prototype's current clickable-button version, plus the new
`:hover`/`:focus-visible` rule and `.map-overflow-marker-count`/
`-label` inner-span rules. Kept the port's own header comment adapted to
this codebase (no `agents-map.js`/`agents-map.html` references, which don't
exist here) — the task's own wording ("declarations, not necessarily file
position") permits this; every declaration is verbatim.

**Verification (non-AC smoke checks per this task's own Tests block — this
story's locked ACs that depend on this styling are verified end-to-end in
T04):**
1. Diffed the new declaration block (`agents-map.css` lines 340-380) against
   `html-prototype/styles.css` (lines 659-702) via `diff` on the two exact
   line ranges — **zero output, byte-for-byte declaration parity
   confirmed.**
2. Confirmed via `git diff` that the old static-chip declarations
   (`--color-surface-raised` background, `1px dashed --color-border`, no
   hover rule, no inner-span classes) are fully replaced, not left
   alongside the new block, and no other rule in the file was touched.
3. Ran `npm run build` (`tsc -b && vite build`) — succeeded with no syntax
   errors, CSS bundled into `dist/assets/index-*.css` (18.17 kB).

gate: clear 2026-08-14 — no MUST-FLAG trigger fired; verbatim port, no
assumptions, no scope deviation.
