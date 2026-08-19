---
id: REQ-SB-42-US-01-T08
title: Section drill-down — SectionDrilldown.tsx renders the identical activity glow/pending-approval treatment, plus the approved captioned-cluster-line traveling-pulse proposal for the Hub-routed case
parent_story: REQ-SB-42-US-01
requirement_id: REQ-SB-42
type: frontend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-42-US-01-T06]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-42-US-01-T08 — Section drill-down activity rendering

## Parent Story

- Story: [[REQ-SB-42-US-01]] — `../UserStories/REQ-SB-42-US-01-real-time-agent-activity-pulses.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-42 *Real-Time Agent Activity Pulses (Agents Map)*

---

## Objective

Apply the identical `.agent-node--activity-glow`/`.agent-node--pending-approval` treatment (Scenarios 1/2/4) to `SectionDrilldown.tsx`'s own agent nodes, and — for the Hub-routed traveling-pulse case (Scenario 3), where the request's other endpoint agent lives in a different Section not visible on this canvas — implement the operator-approved drill-down proposal from `html-prototype/agents-map.html`'s own `REQ-SB-42` design pass: render the traveling pulse along THIS Section's own existing Hub↔agent `.cluster-line`, with a one-line text caption naming the other Section/agent it continues to/from off-canvas.

---

## Starting State → End State

**Before / Inputs:**
- `T07` has landed the overview's own `AgentNode` `activityState` prop and CSS port; `T06` has landed `subscribeToAgentPresence`.
- `src/frontend/src/features/agents-map/SectionDrilldown.tsx` renders one Section's own agents around a center Hub, `.cluster-line` per agent, no live data.

**After / Outputs:**
- `SectionDrilldown.tsx` subscribes to `subscribeToAgentPresence` the same way `AgentsMapCanvas.tsx` does (or receives the snapshot as a prop from its parent — decomposer/coder's own call; a single subscription shared between the overview and an active drill-down, passed down as a prop, avoids two independent `EventSource` connections open at once for the same data, PREFERRED over a second independent subscription).
- Each `AgentNode` rendered in the drill-down gets the same `activityState` computation `T07` established (pending-approval takes precedence over glow).
- For a `hub_routes` entry where EITHER `from_agent_id` OR `to_agent_id` belongs to this drill-down's own Section (the OTHER agent does not): render the traveling pulse (`.route-pulse-dot` via `<animateMotion>`) along this Section's own existing `Hub → thatAgent` `.cluster-line` path (`M50,50 L${x},${y}`, the same path the existing `<line className="cluster-line">` already uses), plus a one-line `<p className="text-muted">` caption naming the other agent/Section it continues to/from (e.g. `"<Agent>'s traveling pulse continues, via this Section's Hub, to <OtherAgent> in the <OtherSection> drill-down."`) — mirroring `html-prototype/agents-map.html`'s own approved proposal text exactly in spirit, not verbatim-copied prose.
- A `hub_routes` entry where NEITHER agent belongs to this drill-down's own Section renders nothing in this view.

---

## Files to Modify

- `src/frontend/src/features/agents-map/SectionDrilldown.tsx` — add the `activityState` computation/prop-threading, the traveling-pulse-along-cluster-line rendering, and the caption text.
- `src/frontend/src/features/agents-map/AgentsMapCanvas.tsx` — pass the already-subscribed presence snapshot down to `<SectionDrilldown>` as a new prop (avoids a second `EventSource` connection; `T07`'s own subscription is reused, not duplicated).

---

## Constraints

- Reuses `T07`'s own `AgentNode` `activityState` prop and CSS classes — no new CSS class introduced for the node treatment itself.
- The Section's own existing `Hub → agent` `.cluster-line` is REUSED for the traveling-pulse path — this is the ONLY connecting line already present in a drill-down; do NOT invent a new line geometry connecting to an off-canvas agent's own (non-existent-here) position.
- One live `EventSource` connection shared between the overview and its active drill-down (via prop-passing) — not a second independent subscription per drill-down mount/unmount cycle.
- The pending-approval/glow precedence rule (`T07`) applies identically here.
- Does not modify `AgentsMapCanvas.tsx`'s own zoom/transition state machine (`zoomTargetSectionId`/`activeSectionId`) — only adds the new snapshot prop being threaded through.

---

## Tests

**Manual verification steps** (real backend + frontend dev servers; drill into a Section that contains one endpoint of an induced Hub-routed pair):
1. **[REQ-SB-42-US-01-AC-01]** With `email-capture` (a Worker in the Capture Section) glowing via `agent_presence.start_activity("email-capture", "capture")`, click into the Capture Section's own drill-down — confirm `email-capture`'s node carries `agent-node--activity-glow` there too (same treatment as the overview, Constraint: "both surfaces must show this").
2. **[REQ-SB-42-US-01-AC-02]** Repeat with a `"chat"`-kind activity on an agent in whichever Section is currently drilled into.
3. **[REQ-SB-42-US-01-AC-03]** `agent_presence.start_hub_routing("meeting-capture", "vault-qa")` (two agents in different Sections). Drill into `meeting-capture`'s own Section — confirm the traveling pulse renders along the Section's own `Hub → meeting-capture` `.cluster-line`, with a caption naming `vault-qa`/its Section. Back out and drill into `vault-qa`'s own Section — confirm the SAME hub-routing state renders the pulse along THAT Section's own `Hub → vault-qa` line, with a caption naming `meeting-capture`/its Section (both endpoints independently correct). Drill into a third, uninvolved Section — confirm no pulse renders there.
4. **[REQ-SB-42-US-01-AC-04]** Create a pending-approval record for an agent in the currently-drilled-into Section — confirm the steady highlight renders identically to the overview.
5. **[REQ-SB-42-US-01-AC-05]** Two agents in the SAME drilled-into Section independently active at once (e.g. one glowing, one pending-approval) — confirm both render correctly and independently in the same drill-down view.
6. **[REQ-SB-42-US-01-AC-06]** An idle agent in the drilled-into Section shows neither class.
7. Non-AC smoke check: confirm only ONE `EventSource` connection is open (browser devtools Network tab, `eventsource` filter) while a drill-down is active — not two.
8. Clean-up: clear every induced state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Drill-down applies the identical glow/pending-approval treatment as the overview, sharing one subscription
- [ ] A Hub-routed pair with one endpoint in the drilled-into Section renders the traveling pulse along that Section's own Hub→agent `.cluster-line`, with a caption naming the other agent/Section
- [ ] A Hub-routed pair with NEITHER endpoint in the drilled-into Section renders nothing extra in that view
- [ ] Only one live `EventSource` connection open at a time (shared, not duplicated)
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The overview's own treatment — `T07` (already built; this task only threads its snapshot down).
- A real cross-drill-down animation (the pulse visibly leaving one Section's drill-down and arriving in another's) — explicitly not built, per the approved design's own "genuinely open... NOT built here" note.
- Any backend change.

---

## Context / Notes

Full mechanism/reasoning: `ADR-035` point 5; visual reference: `html-prototype/agents-map.html`'s approved `REQ-SB-42` design-pass drill-down proposal (its own top-of-file breadcrumb, "GENUINELY OPEN... this pass's own PROPOSAL" — approved by the operator 2026-08-13 per the architect's Notes on the parent story). This proposal is a smaller, self-contained approximation scoped to what one Section's own drill-down can actually draw — it is NOT the same connecting-line geometry as the overview (which draws one straight `.affinity-line` directly between the two agents).

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
