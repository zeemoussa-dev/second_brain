---
id: REQ-SB-51-US-01-T05
title: Agents Map — new "Background Agents" rail
parent_story: REQ-SB-51-US-01
requirement_id: REQ-SB-51
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-51-US-01-T04]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-51-US-01-T05 — Agents Map — new "Background Agents" rail

## Parent Story

- Story: [[REQ-SB-51-US-01]] — `../UserStories/REQ-SB-51-US-01-background-agents-excluded-from-addressing.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-51 *Background Agents — Excluded from Inter-Agent Addressing, Displayed Separately*

---

## Objective

Render `AgentMapLayout.backgroundAgents` (`T04`) in a new, clearly-labeled "Background Agents" rail on the Agents Map — separate from the Section/ring canvas — reusing the screen's own existing `.card`/`.item-list` vocabulary; clicking a row opens the same agent detail panel as clicking any agent on the main map.

---

## Starting State → End State

**Before / Inputs:**
- `src/frontend/src/pages/AgentsMapPage.tsx` fetches `GET /agents` + sections, calls `layoutAgents()`, and passes `{sections, agents, fullAgents, clusters, onSelectAgent}` to `AgentsMapCanvas` (line 65-71). It has no `backgroundAgents` state.
- `src/frontend/src/features/agents-map/AgentsMapCanvas.tsx` renders the Section/ring canvas plus `SectionDrilldown`/`ClusterDrilldown`; it has no `backgroundAgents` prop or rail region.
- `T04`'s `layoutAgents()` now returns `backgroundAgents: AgentSummary[]` on its `AgentMapLayout` result.
- No prototype screen depicts this rail (confirmed by the analyst's own inspection of `agents-map.html`) — resolved as not requiring a fresh `/design` pass; exact placement/styling is coder latitude, reusing the existing `.card`/`.item-list` classes already present on this same screen (e.g. the demo-state legend card, `agents-map.html` line ~1232).

**After / Outputs:**
- `AgentsMapPage.tsx` holds `backgroundAgents` state (set from `layout.backgroundAgents`) and passes it to `AgentsMapCanvas`.
- `AgentsMapCanvas.tsx` renders a new `.card`/`.item-list` region labeled "Background Agents", listing each background agent's name + type, below/beside the Section/ring canvas.
- Clicking a row calls the existing `onSelectAgent` callback with that agent's id, opening the same `AgentDetailPanel` any other agent click opens.
- A Background Agent never occupies a ring slot and is never folded into a cluster marker (already guaranteed by `T04`'s partition — this task only renders the excluded set, it does not re-introduce them to the ring).

---

## Files to Modify

- `src/frontend/src/pages/AgentsMapPage.tsx`:
  - Import `type AgentSummary` from `'../features/agents-map/agentsApiClient'`.
  - Add `const [backgroundAgents, setBackgroundAgents] = useState<AgentSummary[]>([]);`.
  - In the `useEffect`'s `.then(([agentList, sectionList]) => {...})` (line 26-43), add `setBackgroundAgents(layout.backgroundAgents);`; in the `.catch(...)` branch (line 44-51), reset it to `[]`.
  - Pass `backgroundAgents={backgroundAgents}` to `<AgentsMapCanvas .../>` (line 65-71).
- `src/frontend/src/features/agents-map/AgentsMapCanvas.tsx`:
  - Import `type AgentSummary` from `'./agentsApiClient'`.
  - Add `backgroundAgents: AgentSummary[];` to `AgentsMapCanvasProps` (line 14-28) and destructure it in the component signature (line 37).
  - Render a new region (e.g. after the closing `</div>` of `.agents-map-stage`, before the `{activeSection && ...}` block) using `.card`/`.item-list`/`.item-row` classes — same vocabulary `Cockpit.tsx`'s "Available Agents" list already uses — with an `<h3>Background Agents</h3>` heading, one row per `backgroundAgents` entry (name + type), and an `onClick={() => onSelectAgent(agent.id)}` on each row. Render nothing (or an empty-state line) when `backgroundAgents.length === 0`.

---

## Constraints

- Inherits from parent story.
- Reuse the existing `.card`/`.item-list`/`.item-row` classes verbatim — no new visual chrome invented (per the story's own Notes and this session's established "small, standard, vocabulary-reusing addition doesn't need a fresh `/design` pass" convention).
- The rail is purely additive to `AgentsMapCanvas`'s existing render tree — do not alter the Section/ring canvas, `SectionDrilldown`, or `ClusterDrilldown` rendering.
- This is a **structural** addition (a `.card`/`.item-list` region with clickable rows) — lock its DOM-structure verification below; pure visual placement/spacing polish is not itself a locked-AC concern.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-51-US-01-AC-07] With `todo-capture` marked as a Background Agent, load the Agents Map screen. Confirm `todo-capture` does not occupy a position on any Section's ring and is never folded into a cluster marker's count (inspect the rendered SVG/DOM — no `AgentNode`/cluster-marker element references `todo-capture`'s id). Confirm a separate, clearly-labeled "Background Agents" region is present on the same screen listing `todo-capture`. Click `todo-capture`'s row in that region and confirm the same `AgentDetailPanel` opens as clicking any agent on the main map (same side-panel markup, `data-agent-detail="todo-capture"`).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `AgentsMapPage.tsx` fetches and threads `backgroundAgents` through to `AgentsMapCanvas`.
- [ ] `AgentsMapCanvas.tsx` renders a distinct, labeled "Background Agents" `.card`/`.item-list` region.
- [ ] A background agent never appears on the ring or in a cluster marker.
- [ ] Clicking a background-agent row opens the same `AgentDetailPanel` as any other agent.
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint.
- [ ] `CHANGELOG.md` entry appended.

---

## Out of Scope

- The Settings-tab checkbox control (`T06`).
- Any visual polish beyond reusing the existing `.card`/`.item-list` vocabulary (non-blocking design spot-check against the prototype, not a locked AC).

---

## Context / Notes

Real files to compose against: `src/frontend/src/pages/AgentsMapPage.tsx` (88 lines) and `src/frontend/src/features/agents-map/AgentsMapCanvas.tsx` (249 lines) — re-read both fresh before editing. `Cockpit.tsx`'s "Available Agents" `.card`/`.item-list`/`.item-row` markup (line 33-56) is the closest real precedent for this rail's own structure.

---

## Implementation Log

Re-read both real current files before editing (`AgentsMapPage.tsx`, 120
lines; `AgentsMapCanvas.tsx`, 249 lines — both grown since this task's
own estimate, from `SPRINT-043`'s wizard-modal work). `AgentsMapPage.tsx`
gained `backgroundAgents` state (set from `layout.backgroundAgents` in
the success branch, reset to `[]` in the catch branch), threaded to
`AgentsMapCanvas` as a new prop. `AgentsMapCanvas.tsx` gained a new
`.card`/`.item-list`/`.item-row` region (`data-testid=
"background-agents-rail"`, reusing `Cockpit.tsx`'s "Available Agents"
markup vocabulary exactly, per Constraints), rendered as a sibling after
`.agents-map-stage`'s closing tag, before the drill-down blocks — purely
additive, no existing render path touched. Each row's `onClick` calls
the existing `onSelectAgent(agent.id)` callback, same as `AgentNode`'s
own click handler. `tsc -b --noEmit` — zero errors.

**[REQ-SB-51-US-01-AC-07] Verified live** (CDP-driven headless Edge
against the real running frontend, `todo-capture` already
`is_background_agent: true` from `T01`'s backfill): loaded the Agents
Map (`/`); confirmed `.agents-map-stage`'s own rendered HTML never
contains `todo-capture`'s id anywhere (no ring `AgentNode`, no cluster
marker) — combined with `T04`'s own already-verified
`layout.clusters`/`layout.mapAgents` exclusion, confirms it is never
folded into a cluster marker's count either. Confirmed a separate,
clearly-labeled "Background Agents" region is present, listing "Email
Capture", "Meeting Capture", "To-Do Capture" (all 3 real backfilled
Workers). Clicked "To-Do Capture"'s row in that region — the same
`AgentDetailPanel` opened, confirmed via `[data-agent-detail="todo-capture"]`
being present, identical markup to clicking any agent on the main map.
PASS.

One real timing issue found and corrected during verification, not a
code defect: an initial CDP pass read the rail's text too soon after
`Page.navigate` (a ~3s fixed wait, before this page's own two chained
`fetch` calls + `layoutAgents()` computation had resolved), observing a
false-negative empty rail. A `Console`/`Runtime.exceptionThrown`
listener plus a longer wait (4s) confirmed no real error — purely a
race, not a bug — and the same 4s+ wait was reused for the final,
passing run above. Extends this project's own established "add a short
wait between a CDP-dispatched state change and reading the resulting DOM
back" precedent (`SPRINT-036`) to an initial page-load data fetch, not
just a dispatched interaction.

gate: clear 2026-08-14 — no triggers fired (purely additive rail reusing
existing visual vocabulary, no ADR touched, no material assumption
beyond coder latitude the task itself grants for exact placement/
styling, the one locked AC verified live with the false-negative timing
issue found, diagnosed, and resolved rather than silently retried).
