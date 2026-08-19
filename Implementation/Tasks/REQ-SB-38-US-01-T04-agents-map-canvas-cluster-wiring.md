---
id: REQ-SB-38-US-01-T04
title: AgentsMapCanvas.tsx — render cluster markers, widen click-to-zoom state, wire cluster drill-down
parent_story: REQ-SB-38-US-01
requirement_id: REQ-SB-38
type: frontend
status: Done
gate: flagged
gate_reason: "scope-internal judgement call — src/frontend/src/pages/AgentsMapPage.tsx (not in this task's or any sibling task's declared Files to Modify) required a minimal, mechanical edit to thread layout.clusters and a full/unreduced agent list down to AgentsMapCanvas; see Implementation Log"
phase: P1
depends_on: [REQ-SB-38-US-01-T01, REQ-SB-38-US-01-T02, REQ-SB-38-US-01-T03]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-38-US-01-T04 — AgentsMapCanvas.tsx — cluster marker render + click wiring

## Parent Story

- Story: [[REQ-SB-38-US-01]] — `../UserStories/REQ-SB-38-US-01-agents-map-density-clustering.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-38 *Agents Map Density Clustering*

---

## Objective

Wire everything the prior three tasks built into `AgentsMapCanvas.tsx`:
render one `.map-overflow-marker` button per `T01`-produced cluster
descriptor (styled via `T02`), widen the existing
`zoomTargetSectionId`/`activeSectionId` click-to-zoom state (`BUG-002`
Option D) to also address a cluster's own distinct identity, and mount
`T03`'s cluster-scoped drill-down component on a marker click — while
confirming the Section Hub's own existing click path still opens the full,
unclustered drill-down, unaffected by the widened state.

---

## Starting State → End State

**Before / Inputs:**
- `AgentsMapCanvas.tsx` renders every agent in `agents` (from
  `layoutAgents()`'s `mapAgents`) as an `AgentNode`, and every Section as a
  `SectionHub` whose click sets `zoomTargetSectionId`, later
  `activeSectionId`, mounting `SectionDrilldown`.
- `T01` changes `layoutAgents()`'s return shape to also produce `clusters`
  (cluster descriptors) alongside a `mapAgents` that no longer includes
  clustered-away agents.
- `T02` ports the clickable `.map-overflow-marker` CSS shape.
- `T03` delivers a new component that renders a drill-down scoped to one
  cluster's own represented agent ids.

**After / Outputs:**
- `AgentsMapCanvas.tsx` renders one `.map-overflow-marker` button (count +
  "+", via `T02`'s CSS) per `T01` cluster descriptor, positioned at that
  descriptor's own fan-slot angle, alongside the existing (now-reduced)
  `AgentNode` set.
- Clicking a cluster marker opens `T03`'s component scoped to only that
  cluster's represented agents, reusing the existing zoom-then-mount
  mechanism (transform/fade transition, `transitionend`-gated mount) —
  not a new interaction pattern. The cluster's own identity is distinct
  from any real `sectionId` so it never collides with a Section Hub's own
  click target.
- Clicking "Back to Agents Map" from a cluster's drill-down restores the
  overview exactly as it was — same individual dots, same cluster
  marker(s) — unchanged.
- Clicking a Section's own Hub (not a cluster marker) continues to open
  `SectionDrilldown` with every agent in that Section, including the ones a
  cluster marker represents on the overview — completely unaffected by the
  new cluster-click path.

---

## Files to Modify

- `src/frontend/src/features/agents-map/AgentsMapCanvas.tsx` — render
  `T01`'s `clusters` as `.map-overflow-marker` buttons (own component or
  inline, coder's choice); widen the local `zoomTargetSectionId`/
  `activeSectionId` state (e.g. a discriminated union, or a second
  id/subset pair) to also carry a cluster's own target identity, following
  the same `useState`-local pattern already established here; mount `T03`'s
  component instead of `SectionDrilldown` when the active target is a
  cluster.

---

## Constraints

- Inherits from parent story: clicking a cluster marker must reuse the
  existing click-to-zoom mechanism (`BUG-002` Option D,
  `zoomTargetSectionId`/`activeSectionId`), not a new interaction pattern.
- Clicking a Section's own Hub must continue to show every agent in that
  Section, unclustered — this task must not narrow or otherwise change that
  existing full drill-down.
- A cluster marker's own click-target identity must be distinct from any
  real `sectionId`, so a Section Hub's click target and a cluster marker's
  click target never collide.
- `AgentNode.tsx`/`SectionHub.tsx` are reused unchanged — no new props
  beyond what already exists.

---

## Tests

**Manual verification steps** (`src/frontend`: `npm run dev`; browser):

1. [REQ-SB-38-US-01-AC-01] Load the Agents Map overview against a Section
   with 15 same-Type agents. Expect exactly 5 `AgentNode` dots plus one
   `.map-overflow-marker` element for that `(Section x Type-ring)` group,
   showing a count of 10 and a "+".
2. [REQ-SB-38-US-01-AC-03] Click the cluster marker from step 1, confirm
   the cluster drill-down opens, then click "Back to Agents Map". Expect
   the overview to reappear showing the same 5 individual dots and the same
   cluster marker as before, unchanged.
3. [REQ-SB-38-US-01-AC-06] From the same overview (with a visible cluster
   marker), click that Section's own Hub, not the cluster marker. Expect
   the existing full `SectionDrilldown` to open, showing all 15 agents,
   including the 10 the cluster marker represents — none collapsed or
   hidden.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] One `.map-overflow-marker` button renders per `T01` cluster
      descriptor, at the group's own fan-slot angle, showing count + "+"
- [x] Clicking a cluster marker opens `T03`'s component scoped to only that
      cluster's agents, via the existing zoom-then-mount mechanism
- [x] "Back to Agents Map" from a cluster's drill-down restores the
      overview unchanged
- [x] Clicking a Section's own Hub still opens the full, unclustered
      `SectionDrilldown`, unaffected by the cluster-click path
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `layoutAgents.ts`'s clustering logic — `T01`.
- `.map-overflow-marker` CSS itself — `T02`.
- The cluster drill-down component's own internals — `T03`.

---

## Context / Notes

Final wiring task — depends on all three prior tasks. See
`Implementation/Architecture/architecture.md` → "Agents Map — Density
Clustering (REQ-SB-38-US-01)": "Click-to-zoom state widens, does not
duplicate" — the decomposer/coder own the exact shape of the widened state
(discriminated union vs. a second id/subset pair); this is ordinary
component-state design within the already-established local-`useState`
pattern, not a new architectural question.

---

## Implementation Log

**2026-08-14 — coder.** `AgentsMapCanvas.tsx`: added `clusters:
ClusterMarker[]` and `fullAgents: MockAgent[]` props; renders one
`.map-overflow-marker` button per cluster (positioned via
`polarToCartesian(RING_RADIUS[cluster.type], cluster.angleDeg)`, `+N` count/
label spans, `data-cluster-id`); widened the local click-to-zoom state from
`zoomTargetSectionId`/`activeSectionId` (`string | null`) to a
`ZoomTarget = { kind: 'section' | 'cluster'; id: string } | null` pair
(`zoomTarget`/`activeTarget`) — same local-`useState`/`transitionend`-gated
mount pattern, unchanged in shape, just widened to carry a `kind`. Mounts
`ClusterDrilldown` (`T03`) when `activeTarget.kind === 'cluster'`,
`SectionDrilldown` unchanged when `'section'`. A cluster's own click target
(`cluster.id`, always `${sectionId}-${type}-cluster`) can never collide
with a real `sectionId`.

**Scope-internal judgement call — `src/frontend/src/pages/AgentsMapPage.tsx`
(logged per coder.md, not in this or any sibling task's declared Files to
Modify; task's own gate set to `flagged` for human spot-check).** Two
things surfaced only at this integration task, live, that could not be
solved within `AgentsMapCanvas.tsx` alone:
1. `AgentsMapCanvas` cannot compute `clusters` itself — `AgentsMapPage.tsx`
   is the sole caller of `layoutAgents()`; without threading
   `layout.clusters` through, cluster rendering is structurally impossible
   from `AgentsMapCanvas.tsx` alone, for ANY part of this task, not just an
   edge case.
2. `T01`'s own locked `mapAgents` reduction (only visible-on-overview
   agents) means the SAME reduced `agents` prop, if also fed to
   `SectionDrilldown`/`ClusterDrilldown`, silently drops the very agents a
   cluster marker represents — a real, live-confirmed violation of this
   task's own Constraint ("Clicking a Section's own Hub must continue to
   show every agent in that Section, unclustered — this task must not
   narrow ... that existing full drill-down") and Scenario 6/AC-06.

Resolution: `AgentsMapPage.tsx` gained one new state
(`clusters`) and one new, purely-derived state (`fullAgents` — every
fetched agent, unreduced, mapped from the raw `AgentSummary[]` the page
already fetches; `angleDeg: 0` placeholder, immediately recomputed by
`layoutSectionDrilldown()` inside both drill-down consumers, never
rendered as-is) — both fed into `<AgentsMapCanvas>` as two new props via
the exact same state-then-pass-through pattern this file already uses for
`sections`/`agents` (zero new business logic, zero design ambiguity, no
new interface with any consumer outside this one caller). This was the
minimum change that made T04's own already-authored Objective/Constraints
achievable at all; verified live below that AC-06 genuinely fails without
it (a real, not hypothetical, integration gap) and passes with it.

**Verification (manual mode — real running dev server @
`http://localhost:5173`, real backend @ `http://localhost:8001`, real
CDP-driven headless Edge, no mocks):** the seeded vault had only 3
`productivity`/`worker` and 1 `technical`/`expert` agents — no group
naturally over `VISIBLE_SLOT_CAP`. Created 8 real `worker`-type agents via
the live `POST /agents` endpoint (`t04-cluster-test-worker-1..8`); all 8
landed in the `technical` section by `create_agent`'s own default,
bringing `technical/worker` to 8 real agents (over the cap) alongside the
1 pre-existing `technical/expert` (`compass-expert`, untouched, under any
cap). Confirmed via `GET /agents` before navigating.

- **AC-01:** overview showed exactly 5 individually-rendered
  `.agent-node--worker.agent-node--compact` dots for the `technical`
  group (`t04-cluster-test-worker-1..5`) plus exactly 1
  `.map-overflow-marker` (`data-cluster-id="technical-worker-cluster"`,
  count text `"3"`, label text `"+"`) — the other 3
  `productivity`/`worker` agents (`email-capture`/`meeting-capture`/
  `todo-capture`, under cap) rendered individually as always, unaffected.
  Screenshot: overview shows 5 blue worker dots + 1 dashed "3 +" marker
  near TECHNICAL. **PASS.**
- **AC-03:** clicked the marker — `ClusterDrilldown` opened
  (`[data-agents-drilldown]` present), showing exactly
  `t04-cluster-test-worker-6/7/8` (the marker's own 3 represented ids,
  confirmed via `data-agent-id` query) with real names/hub label
  `"Technical — Worker overflow (+3)"` (screenshot). Clicked "Back to
  Agents Map" — overview's own dot-id set and marker-id set, compared
  by exact array equality before vs. after, were identical; the
  drill-down unmounted. **PASS.**
- **AC-06:** clicked the `technical` Section's own Hub
  (`[data-section-id="technical"]`, not the marker) — the full,
  unclustered `SectionDrilldown` opened showing all 9 `technical` agents
  (`compass-expert` + all 8 `t04-cluster-test-worker-*`, including the 3
  the marker represents on the overview), real names, none collapsed or
  hidden (screenshot confirms all 9 spokes off one Hub). **PASS** — this
  is the specific check that would have failed without the
  `AgentsMapPage.tsx` `fullAgents` wiring above (empirically the
  motivating reason for that judgement call, not merely theorized).

**Cleanup:** restored `.second-brain/agents_registry.json` to its
pre-run `{"created_agents": {}}` state and removed the 8 test-agent
entries from `.second-brain/agent_sections.json`'s `assignments` (both
data files, not code — the app's own `_load_state()` reads fresh from
disk on every call, no in-process cache to invalidate). Confirmed via a
fresh `GET /agents` afterward: back to the original 7 real agents.
Killed the throwaway headless-Edge process by its own specific PID
(`taskkill /PID <pid> /F`, per this project's own established
specific-PID-kill protocol); confirmed its CDP port no longer reachable.

`npm run build` (`tsc -b && vite build`) passed with no errors throughout.

gate: flagged 2026-08-14 — scope-internal judgement call (above,
`AgentsMapPage.tsx`) for human spot-check; not a hard escalation (no new
external dependency, no shared interface with any consumer outside this
one caller, no ADR deviation) but a genuine file-scope deviation from this
task's own declared `## Files to Modify`, disclosed per coder.md's own
"log as assumption, flag the task" instruction for exactly this class of
finding.
