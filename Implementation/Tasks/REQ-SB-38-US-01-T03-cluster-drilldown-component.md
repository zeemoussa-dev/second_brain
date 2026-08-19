---
id: REQ-SB-38-US-01-T03
title: New cluster-scoped drill-down component, reusing layoutSectionDrilldown()
parent_story: REQ-SB-38-US-01
requirement_id: REQ-SB-38
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-38-US-01-T01]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-38-US-01-T03 — New cluster-scoped drill-down component

## Parent Story

- Story: [[REQ-SB-38-US-01]] — `../UserStories/REQ-SB-38-US-01-agents-map-density-clustering.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-38 *Agents Map Density Clustering*

---

## Objective

Build a new component — a small sibling to `SectionDrilldown.tsx`, or a
generalization of it to accept an already-filtered agent list plus a
heading — that renders a drill-down scoped to only the agents one cluster
marker represents, reusing `layoutSectionDrilldown()` unmodified (fed the
clustered subset instead of a whole Section's agents) and
`SectionHub`/`AgentNode` unchanged, matching `SectionDrilldown.tsx`'s own
existing shape (Back button, `.explore-drilldown`/`.agents-map-stage`
structure, empty-state handling).

---

## Starting State → End State

**Before / Inputs:**
- `SectionDrilldown.tsx` renders one Section's full, unclustered agent list
  via `layoutSectionDrilldown(agents.filter((agent) => agent.sectionId ===
  section.id))` — filtered by Section id, with no concept of a narrower
  subset.
- `T01`'s `layoutAgents()` now emits a `clusters` entry per overflowing
  `(sectionId, agentType)` group, each carrying the list of agent ids it
  represents.

**After / Outputs:**
- A new component (e.g. `ClusterDrilldown.tsx`) accepts a cluster
  descriptor (or an already-resolved subset of `MockAgent[]` plus a
  heading/label) and the full `agents` list, filters to only the agents the
  cluster represents, and renders them via `layoutSectionDrilldown()` +
  `SectionHub`/`AgentNode`, identical in shape/behavior to
  `SectionDrilldown.tsx` (Back button, same CSS classes) except scoped to
  the narrower subset and never including any agent from that Section that
  is not part of this specific cluster — including agents already visible
  as individual dots on the overview.

---

## Files to Modify

- `src/frontend/src/features/agents-map/` — new component file (e.g.
  `ClusterDrilldown.tsx`), reusing `layoutSectionDrilldown()` from
  `layoutAgents.ts`, `SectionHub`, and `AgentNode` unchanged, matching
  `SectionDrilldown.tsx`'s existing structure and CSS classes
  (`.explore-drilldown`, `.agents-map-stage`, `.agents-map-canvas`, the
  `&larr; Back to Agents Map` button convention).

---

## Constraints

- Inherits from parent story: clicking a cluster marker must open a
  drill-down scoped to only the agents it represents — reusing the
  existing click-to-zoom mechanism (`BUG-002` Option D), not a new
  interaction pattern (the mounting/click wiring itself is `T04`'s job;
  this task builds the component `T04` mounts).
- Must reuse `layoutSectionDrilldown()` unmodified — no new layout function,
  no change to `layoutAgents.ts` (already delivered by `T01`) or
  `polarLayout.ts`.
- Must reuse `SectionHub`/`AgentNode` unchanged — no new props beyond what
  already exists (`radiusOverride`, `onSelect`, etc.).
- Must not filter by `sectionId` alone — must filter to exactly the
  cluster's own represented agent ids, so it never includes an agent
  already visible as an individual dot on the overview.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-38-US-01-AC-02] Render the new component directly with a
   synthetic `agents` list of 15 same-Section, same-Type agents and a
   cluster descriptor representing the 10 overflow agents. Expect the
   rendered `AgentNode` set to contain exactly those 10 agent ids — none of
   the other 5 (individually-visible-on-overview) agents, and no agent from
   any other Section or Type-ring, appears.
2. [REQ-SB-38-US-01-AC-04] Render the same component with a cluster
   descriptor whose represented agent ids are confirmed (via `T01`'s own
   grouping guarantee) to all share one `type`. Expect every `AgentNode`
   rendered inside this drill-down to carry that same `agent-node--<type>`
   class — confirming the drill-down itself never mixes agents from more
   than one Type-ring, independent of `T01`'s own upstream guarantee.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] New component renders only the agents a given cluster represents, via
      `layoutSectionDrilldown()` unmodified
- [x] Reuses `SectionHub`/`AgentNode` unchanged
- [x] Matches `SectionDrilldown.tsx`'s existing structural/CSS convention
      (Back button, `.explore-drilldown` shape)
- [x] Never includes an agent outside the cluster's own represented agent
      ids (not merely filtered by Section)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Mounting this component / wiring its click-to-open, Back-button restore,
  or the widened `zoomTargetSectionId`/`activeSectionId` state — `T04`.
- `layoutAgents.ts`'s clustering logic — `T01` (already delivered, consumed
  here).
- `.map-overflow-marker` CSS — `T02`.

---

## Context / Notes

Depends on `T01` for the cluster descriptor shape (agent ids to filter to).
Does not depend on `T02` — this component renders `SectionHub`/`AgentNode`
and its own `.explore-drilldown` shell, none of which touch
`.map-overflow-marker` (that class only appears on the overview's marker
button, wired in `T04`). See `Implementation/Architecture/architecture.md`
→ "Agents Map — Density Clustering (REQ-SB-38-US-01)": "New component, not
a new mechanism."

---

## Implementation Log

**2026-08-14 — coder.** New `src/frontend/src/features/agents-map/ClusterDrilldown.tsx`
— a sibling to `SectionDrilldown.tsx`, same `.explore-drilldown`/
`.agents-map-stage`/`.agents-map-canvas`/Back-button/empty-state structure.
Accepts `{ cluster: ClusterMarker, section: AgentSection, agents:
MockAgent[], onBack, onSelectAgent }`; filters `agents` to a `Set` of
`cluster.agentIds` (never `sectionId`), feeds the filtered subset to
`layoutSectionDrilldown()` unmodified, renders via `SectionHub`/`AgentNode`
unchanged (no new props on either). `SectionHub`'s heading is built from a
synthetic `AgentSection`-shaped object (`id: cluster.id`, so its click
target — inert here, `onActivate` omitted, same as `SectionDrilldown`'s own
Hub — can never collide with a real Section id) whose `hubLabel` names the
Section + Type + overflow count (e.g. "Section A — Worker overflow (+10)"),
since `SectionHub` itself gets no new props.

**Verification (manual mode).** Ran the task's own two literal
Tests-block scenarios against the REAL component, rendered by the REAL
running Vite dev server + React runtime in a real headless Edge browser via
CDP (not a mock/SSR string diff) — synthetic dataset: 15 same-Section
(`sec-a`)/same-Type (`worker`) agents (5 "visible" + 10 "overflow"), plus
two distractors (one same-Section-different-Type `expert` agent, one
different-Section-same-Type `worker` agent) to make the "never includes an
agent outside the cluster" check meaningful, not just non-crashing. Mounted
via a throwaway `harness-cluster-drilldown.html` + `__harness_cluster_
drilldown_entry.tsx` pair (temporary, added under `src/frontend/`, deleted
immediately after the run — `git status` confirmed zero trace left; not
part of this task's own `## Files to Modify`, so nothing was committed
there).

- **AC-02:** rendered `[data-agent-id]` set = exactly the 10
  `worker-overflow-*` ids; zero of the 5 `worker-visible-*` ids, the
  `expert-in-sec-a` distractor, or the `worker-in-sec-b` distractor
  appeared. **PASS** (real headless-browser DOM query, not asserted from
  code reading).
- **AC-04:** every rendered node's own `agent-node--<type>` class was
  `agent-node--worker` (`Set` of distinct classes had size 1) — confirmed
  independently of `T01`'s own upstream grouping guarantee, at this
  component's own render layer. **PASS.**

Cleanup: the throwaway headless-Edge process (launched on
`--remote-debugging-port=9333`) had already exited on its own by the time
cleanup was attempted (`/json/close` call ended its only tab); confirmed
port 9333 no longer reachable — no orphaned process left running.

gate: clear 2026-08-14 — no MUST-FLAG trigger fired. One scope-internal
judgement call logged above (the synthetic-`AgentSection`-for-heading
shape, since `SectionHub` itself may not gain new props) for human
spot-check.
