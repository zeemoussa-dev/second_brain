---
id: REQ-SB-42-US-01-T07
title: Agents Map overview — AgentNode.tsx/AgentsMapCanvas.tsx render live activity glow, pending-approval highlight, and the Hub-routed traveling pulse from the SSE snapshot
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

# REQ-SB-42-US-01-T07 — Overview activity rendering

## Parent Story

- Story: [[REQ-SB-42-US-01]] — `../UserStories/REQ-SB-42-US-01-real-time-agent-activity-pulses.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-42 *Real-Time Agent Activity Pulses (Agents Map)*

---

## Objective

Wire `T06`'s `subscribeToAgentPresence` into `AgentsMapCanvas.tsx`, apply `.agent-node--activity-glow`/`.agent-node--pending-approval` to the matching `AgentNode`, and render the Hub-routed traveling pulse (`.affinity-line.active` + `.route-pulse-dot` via SVG `<animateMotion>`) between the two specific agents named in each `hub_routes` entry — exactly the approved `html-prototype/agents-map.html` `REQ-SB-42` design-pass treatment. Port the three new CSS rules into the real frontend stylesheet (mechanical, zero-judgement port of already-approved design, per this project's own established precedent).

---

## Starting State → End State

**Before / Inputs:**
- `T06` has landed `subscribeToAgentPresence(onSnapshot) -> cleanup`.
- `src/frontend/src/features/agents-map/AgentNode.tsx` renders a plain `.agent-node` button, className built from `agent.type`/`compact` only.
- `src/frontend/src/features/agents-map/AgentsMapCanvas.tsx` renders the overview canvas (Hub nodes, agent nodes, `.cluster-line`/`.spoke-line` SVG lines) from static `sections`/`agents` props only — no live data.
- `src/frontend/src/styles/agents-map.css` has `.kb-pulse-dot`/`.cluster-line` but none of `.agent-node--activity-glow`/`.agent-node--pending-approval`/`.route-pulse-dot`/`.affinity-line`.

**After / Outputs:**
- `src/frontend/src/styles/agents-map.css` gains the three CSS blocks copied verbatim from `html-prototype/styles.css`'s own "Agent activity pulses (REQ-SB-42)" section (the `agentActivityGlow` keyframe, `.agent-node--activity-glow`, `.agent-node--pending-approval`, `.agent-node--pending-approval .agent-node-type`, `.route-pulse-dot`) plus the `.affinity-line`/`.affinity-line.active` rules from that same stylesheet's "Agents Map layout exploration" section — same selectors, same values, ported not redesigned.
- `AgentNode.tsx` gains an `activityState?: 'glow' | 'pending-approval' | null` prop, appended to the existing className array:
  ```typescript
  const className = [
    'agent-node',
    `agent-node--${agent.type}`,
    compact ? 'agent-node--compact' : null,
    activityState === 'glow' ? 'agent-node--activity-glow' : null,
    activityState === 'pending-approval' ? 'agent-node--pending-approval' : null,
  ].filter(Boolean).join(' ');
  ```
- `AgentsMapCanvas.tsx`:
  - `useEffect` on mount: `subscribeToAgentPresence(setPresenceSnapshot)`, returning the cleanup function.
  - For each rendered `AgentNode`, computes `activityState` from the snapshot: `pending_approval_agent_ids.includes(agent.id)` → `'pending-approval'` (checked FIRST — takes precedence, Scenario 4's own "never simultaneously" Constraint); else `active[agent.id]` present → `'glow'`; else `null`.
  - For each `hub_routes` entry, computes both agents' cartesian positions (`polarToCartesian(RING_RADIUS[agent.type], agent.angleDeg)`, looked up from the `agents` prop by `from_agent_id`/`to_agent_id`) and renders one `<line className="affinity-line active" .../>` plus one `<circle className="route-pulse-dot" r="1.6"><animateMotion dur="1.6s" repeatCount="indefinite" path={\`M${x1},${y1} L${x2},${y2}\`} /></circle>` inside the existing `<svg className="agents-map-lines">`, alongside the existing `.cluster-line`/`.spoke-line` elements — same SVG, same viewBox, no new `<svg>`.

---

## Files to Modify

- `src/frontend/src/styles/agents-map.css` — port the CSS rules named above (append; do not edit any existing rule).
- `src/frontend/src/features/agents-map/AgentNode.tsx` — add `activityState` prop and its className branch.
- `src/frontend/src/features/agents-map/AgentsMapCanvas.tsx` — subscribe to `agent-presence/client.ts`, compute per-agent `activityState`, pass it to each `AgentNode`, render the traveling-pulse `<line>`/`<circle>` for each `hub_routes` entry.

---

## Constraints

- Pending-approval takes precedence over the animated glow when both would otherwise apply to the same agent — Scenario 4's own Constraint ("this agent is never shown with the animated glow/pulse while its pending-approval record remains open, even if it is also otherwise idle").
- The existing `kb-pulse-dot` decorative animation, `.cluster-line`/`.spoke-line` rendering, and the existing zoom/drilldown state machine in `AgentsMapCanvas.tsx` are UNCHANGED by this task — this task only ADDS the subscription, the per-node `activityState` computation, and the new SVG elements alongside the existing ones (Scenario 8).
- CSS is PORTED verbatim from `html-prototype/styles.css` — no new visual design invented here (no `/design` pass was needed for a mechanical port of already-approved rules; visual-polish deviations, if any are later spotted, are a non-blocking out-of-band spot-check, not a locked AC).
- `subscribeToAgentPresence`'s cleanup function MUST be called in the `useEffect`'s own cleanup (return value) — an unmounted `AgentsMapCanvas` must not leak an open `EventSource` connection.
- Do not change `AgentNode.tsx`'s existing `compact`/`radiusOverride` prop behavior.

---

## Tests

<!-- Structural/DOM-observable steps -- this project has no jsdom/automated
runner yet (manual mode); verify via a real dev server + browser (headless
Chrome/CDP or the OS-installed Edge headless-screenshot technique, per this
project's own established precedent) against real, monkeypatched or
directly-induced backend activity state, per T02-T04's own real dispatch
call sites. -->

**Manual verification steps** (real backend + frontend dev servers running):
1. **[REQ-SB-42-US-01-AC-01]** Trigger a real capture run for an agent visible on the overview (e.g. `POST /agents/email-capture/skills/summarize-file/invoke`-equivalent is Skill-scoped — simplest real trigger: call `run_capture_for_agent` via whatever real HTTP path already exists, or directly `agent_presence.start_activity("email-capture", "capture")` in a Python shell against the SAME running backend process for a controlled, real induction). While active, load/refresh the Agents Map overview in a browser — confirm the `email-capture` node carries `agent-node--activity-glow` in its rendered `className` (DOM inspection via CDP `Runtime.evaluate` or devtools). Call `agent_presence.end_activity(...)` with the matching token (or simply wait for the real capture call to finish) — confirm the class is removed within ~1s, without a page refresh.
2. **[REQ-SB-42-US-01-AC-02]** Repeat step 1's shape using `agent_presence.start_activity("vault-qa", "chat")`/`end_activity` (or a real `POST /agents/vault-qa/chat` call) — confirm the same `agent-node--activity-glow` class appears/clears on `vault-qa`'s node.
3. **[REQ-SB-42-US-01-AC-03]** `agent_presence.start_hub_routing("meeting-capture", "vault-qa")` in a Python shell against the running backend — confirm, in the open browser, a NEW `<line class="affinity-line active">` and `<circle class="route-pulse-dot">` render inside `.agents-map-lines`, positioned between `meeting-capture`'s and `vault-qa`'s real rendered coordinates (not a generic glow on either node). `agent_presence.end_hub_routing(<token>)` — confirm both elements are removed within ~1s.
4. **[REQ-SB-42-US-01-AC-04]** Create a real pending-approval record for a visible agent (e.g. `pending_approval_registry.create_pending_approval("people-producer", "background", None, "test")`) — confirm `people-producer`'s node carries `agent-node--pending-approval`, NOT `agent-node--activity-glow`. While that record is still open, also `agent_presence.start_activity("people-producer", "capture")` — confirm the node STILL shows only `agent-node--pending-approval`, never both classes together (precedence). Resolve the approval — confirm the class clears within ~1s.
5. **[REQ-SB-42-US-01-AC-05]** Induce two DIFFERENT agents' activity states simultaneously (e.g. `email-capture` glowing via `start_activity` AND `people-producer` pending-approval via a new record) — confirm each node shows exactly its own correct class, independently, at the same time.
6. **[REQ-SB-42-US-01-AC-06]** With no induced state on a given agent, confirm its node carries neither new class.
7. **[REQ-SB-42-US-01-AC-08]** Confirm the existing `kb-pulse-dot` circles are still present and animating exactly as before this task (visual/DOM spot-check — the element still exists with its own unmodified class list).
8. Clean-up: clear every induced `_active`/`_hub_routes`/pending-approval record created for this verification session.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Overview subscribes to `agent-presence/client.ts` on mount, unsubscribes on unmount
- [ ] `AgentNode.tsx` applies `agent-node--activity-glow`/`agent-node--pending-approval` per its `activityState` prop
- [ ] Pending-approval takes precedence over glow for the same agent
- [ ] A `hub_routes` entry renders a `.affinity-line.active` + `.route-pulse-dot` between the two named agents' own real positions
- [ ] The existing `kb-pulse-dot`/`cluster-line`/`spoke-line` rendering and the zoom/drilldown state machine are unaffected
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Section drill-down's own equivalent treatment — `T08`.
- Any backend change.

---

## Context / Notes

Full mechanism/reasoning: `ADR-035` point 5; visual reference: `html-prototype/agents-map.html`'s approved `REQ-SB-42` design-pass "Agent activity pulses (REQ-SB-42 demo)" state (its own top-of-file breadcrumb, revision 2026-08-13) — read that file's real, current markup/CSS before porting; do not assume the code samples in this task are byte-for-byte identical to what the prototype actually contains.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
