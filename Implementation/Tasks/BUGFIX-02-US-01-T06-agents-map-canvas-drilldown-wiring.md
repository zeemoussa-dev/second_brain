---
id: BUGFIX-02-US-01-T06
title: AgentsMapCanvas.tsx — wire activeSectionId drill-down state, always-compact overview dots, Hub-click zoom
parent_story: BUGFIX-02-US-01
requirement_id: BUG-002
type: frontend
status: Done
gate: flagged
gate_reason: "scope-internal judgement call — see Implementation Log"
phase: P1
depends_on: [BUGFIX-02-US-01-T02, BUGFIX-02-US-01-T03, BUGFIX-02-US-01-T04, BUGFIX-02-US-01-T05]
created: 2026-08-12
updated: 2026-08-12
---

# BUGFIX-02-US-01-T06 — AgentsMapCanvas.tsx — wire drill-down state + always-compact overview

## Parent Story

- Story: [[BUGFIX-02-US-01]] — `../UserStories/BUGFIX-02-US-01-agents-map-semantic-zoom-drilldown-containment.md`
- Requirement: `BUGS.md` → `BUG-002` — "Agents Map: sections with 4+ agents
  visually spill into neighboring sections"

**This is the story's final integration task — it carries the story's one
locked AC's live-browser verification step.**

---

## Objective

Wire everything the earlier tasks in this story landed into
`AgentsMapCanvas.tsx`: every overview agent dot always renders `compact`
(`T03`); every `SectionHub` becomes a clickable button (`T04`'s
`onActivate`) that plays the `.explore-zoom-overview`/`.zooming-out` CSS
transition (`T02`) and then mounts that Section's own `SectionDrilldown`
(`T05`); a "Back to Agents Map" click reverses it. Local `useState` only —
`activeSectionId` (which drill-down, if any, is mounted) plus a transient
zoom-transition target — per the architect's Notes.

---

## Starting State → End State

**Before / Inputs:**
- `AgentsMapCanvas.tsx` is a plain function component (no state/hooks),
  rendering a fixed `.agents-map-stage > .agents-map-canvas` with the
  ambient SVG grid, `SectionHub`s (no `onActivate`), and `AgentNode`s (no
  `compact`).
- `T02`–`T05` have landed the CSS, prop, and component building blocks this
  task wires together.

**After / Outputs:**
- `AgentsMapCanvas` holds local `activeSectionId: string | null` (which
  Section's drill-down is currently mounted) and
  `zoomTargetSectionId: string | null` (the Section currently mid-zoom-
  transition, or the same as `activeSectionId` once settled — drives the
  overview's `zooming-out` class independent of whether the transition has
  finished).
- Clicking a Section's Hub starts the zoom-out transition; once the CSS
  transition ends, that Section's `SectionDrilldown` mounts as a sibling of
  the (still-mounted, now permanently `zooming-out`) overview canvas.
- Clicking the drill-down's "Back to Agents Map" button unmounts the
  drill-down and removes `zooming-out` from the overview canvas, reversing
  the CSS transition back to the normal overview appearance.
- Every overview `AgentNode` renders `compact`. Every `SectionHub` is a
  clickable button. `AgentsMapCanvas`'s return becomes a `<>...</>`
  fragment (its existing `.agents-map-stage` overview block, plus the new
  conditionally-rendered `SectionDrilldown` sibling) — a source-compatible
  change; its only caller, `AgentsMapPage.tsx`, needs no edit.

---

## Files to Modify

- `src/frontend/src/features/agents-map/AgentsMapCanvas.tsx` — replace the
  whole file:
  ```tsx
  import { useEffect, useRef, useState, type ReactElement } from 'react';
  import type { AgentSection, MockAgent } from './mockAgents';
  import { BOUNDARY_RADIUS, HUB_RADIUS, RING_RADIUS, polarToCartesian } from './polarLayout';
  import { KnowledgeBaseNode } from './KnowledgeBaseNode';
  import { SectionHub } from './SectionHub';
  import { AgentNode } from './AgentNode';
  import { SectionDrilldown } from './SectionDrilldown';

  const SECTION_TITLE_RADIUS = 66;
  const SECTION_BOUNDARY_INNER_RADIUS = 18;

  interface AgentsMapCanvasProps {
    sections: AgentSection[];
    agents: MockAgent[];
    onSelectAgent: (agentId: string) => void;
  }

  export function AgentsMapCanvas({ sections, agents, onSelectAgent }: AgentsMapCanvasProps) {
    const hasAgents = sections.length > 0 && agents.length > 0;

    // Drill-down / semantic-zoom state (BUG-002 fix, Option D) — both local
    // to this component (architect's Notes): `zoomTargetSectionId` drives
    // the overview's own .explore-zoom-overview/.zooming-out CSS
    // transition (set the instant a Hub is clicked, cleared only on Back);
    // `activeSectionId` mounts that Section's SectionDrilldown, set only
    // once the CSS transition has actually finished (transitionend), so
    // the drill-down never appears mid-zoom.
    const [zoomTargetSectionId, setZoomTargetSectionId] = useState<string | null>(null);
    const [activeSectionId, setActiveSectionId] = useState<string | null>(null);
    const overviewCanvasRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
      const canvasEl = overviewCanvasRef.current;
      if (!canvasEl || !zoomTargetSectionId || activeSectionId === zoomTargetSectionId) return;

      const handleTransitionEnd = (event: TransitionEvent) => {
        if (event.target !== canvasEl) return;
        setActiveSectionId(zoomTargetSectionId);
      };
      canvasEl.addEventListener('transitionend', handleTransitionEnd);
      return () => canvasEl.removeEventListener('transitionend', handleTransitionEnd);
    }, [zoomTargetSectionId, activeSectionId]);

    const handleActivateSection = (sectionId: string) => {
      setZoomTargetSectionId(sectionId);
    };

    const handleBack = () => {
      setActiveSectionId(null);
      setZoomTargetSectionId(null);
    };

    const activeSection = activeSectionId
      ? sections.find((section) => section.id === activeSectionId) ?? null
      : null;

    return (
      <>
        <div className="agents-map-stage">
          <div
            ref={overviewCanvasRef}
            className={`agents-map-canvas explore-zoom-overview${zoomTargetSectionId ? ' zooming-out' : ''}`}
          >
            <svg className="agents-map-lines" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
              <line className="radar-spoke" x1="50" y1="50" x2="108" y2="50" />
              <line className="radar-spoke" x1="50" y1="50" x2="100.23" y2="79" />
              <line className="radar-spoke" x1="50" y1="50" x2="79" y2="100.23" />
              <line className="radar-spoke" x1="50" y1="50" x2="50" y2="108" />
              <line className="radar-spoke" x1="50" y1="50" x2="21" y2="100.23" />
              <line className="radar-spoke" x1="50" y1="50" x2="-0.23" y2="79" />
              <line className="radar-spoke" x1="50" y1="50" x2="-8" y2="50" />
              <line className="radar-spoke" x1="50" y1="50" x2="-0.23" y2="21" />
              <line className="radar-spoke" x1="50" y1="50" x2="21" y2="-0.23" />
              <line className="radar-spoke" x1="50" y1="50" x2="50" y2="-8" />
              <line className="radar-spoke" x1="50" y1="50" x2="79" y2="-0.23" />
              <line className="radar-spoke" x1="50" y1="50" x2="100.23" y2="21" />
              <circle className="ring-circle" cx="50" cy="50" r={RING_RADIUS.producer} />
              <circle className="ring-circle" cx="50" cy="50" r={RING_RADIUS.expert} />
              <circle className="ring-circle" cx="50" cy="50" r={RING_RADIUS.worker} />
              <circle className="boundary-circle" cx="50" cy="50" r={BOUNDARY_RADIUS} />

              {hasAgents && (
                <>
                  {sections.map((section) => {
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

                  {sections.map((section) => {
                    const hubPoint = polarToCartesian(HUB_RADIUS, section.hubAngleDeg);
                    return (
                      <line
                        key={`${section.id}-spoke`}
                        className="spoke-line"
                        x1="50"
                        y1="50"
                        x2={hubPoint.x}
                        y2={hubPoint.y}
                        stroke="var(--color-accent)"
                      />
                    );
                  })}

                  {sections.map((section) => {
                    const hubPoint = polarToCartesian(HUB_RADIUS, section.hubAngleDeg);
                    const sectionAgents = agents.filter((agent) => agent.sectionId === section.id);
                    const agentPoints = sectionAgents.map((agent) => ({
                      agent,
                      point: polarToCartesian(RING_RADIUS[agent.type], agent.angleDeg),
                    }));
                    const stroke = 'var(--color-accent)';
                    const lines: ReactElement[] = agentPoints.map(({ agent, point }) => (
                      <line
                        key={`${section.id}-hub-${agent.id}`}
                        className="cluster-line"
                        x1={hubPoint.x}
                        y1={hubPoint.y}
                        x2={point.x}
                        y2={point.y}
                        stroke={stroke}
                      />
                    ));
                    for (let i = 0; i < agentPoints.length; i += 1) {
                      for (let j = i + 1; j < agentPoints.length; j += 1) {
                        lines.push(
                          <line
                            key={`${section.id}-agent-${agentPoints[i].agent.id}-${agentPoints[j].agent.id}`}
                            className="cluster-line"
                            x1={agentPoints[i].point.x}
                            y1={agentPoints[i].point.y}
                            x2={agentPoints[j].point.x}
                            y2={agentPoints[j].point.y}
                            stroke={stroke}
                          />,
                        );
                      }
                    }
                    return lines;
                  })}

                  <text className="ring-label" x="80" y="51" fontSize="2.6" letterSpacing="0.3">PRODUCER</text>
                  <text className="ring-label" x="27.5" y="89.97" fontSize="2.6" letterSpacing="0.3">EXPERT</text>
                  <text className="ring-label" x="25" y="8.2" fontSize="2.6" letterSpacing="0.3">WORKER</text>
                </>
              )}
            </svg>
            <KnowledgeBaseNode />
            {hasAgents && sections.map((section) => (
              <SectionHub
                key={section.id}
                section={section}
                onActivate={() => handleActivateSection(section.id)}
              />
            ))}
            {hasAgents && agents.map((agent) => (
              <AgentNode key={agent.id} agent={agent} onSelect={onSelectAgent} compact />
            ))}
            {hasAgents && sections.map((section) => {
              const { x, y } = polarToCartesian(SECTION_TITLE_RADIUS, section.hubAngleDeg);
              return (
                <div key={`${section.id}-title`} className="section-title" style={{ top: `${y}%`, left: `${x}%` }}>
                  {section.label}
                  <span className="section-title-accent" style={{ background: 'var(--color-accent)' }} />
                </div>
              );
            })}
          </div>
        </div>
        {activeSection && (
          <SectionDrilldown
            section={activeSection}
            agents={agents}
            onBack={handleBack}
            onSelectAgent={onSelectAgent}
          />
        )}
      </>
    );
  }
  ```

---

## Constraints

- Inherits from parent story: must preserve `AgentNode`'s existing
  `onSelect` click-through to the Agent Detail Panel unchanged for a
  compact overview dot (the story's own explicit Constraint) — the overview
  call site's `onClick={() => onSelect(agent.id)}` inside `AgentNode`
  itself is untouched by this task; this task only adds the `compact` prop
  at the call site.
- An overview agent dot's click target and a Hub's click target must stay
  visually/functionally distinct controls (the story's own Constraint) —
  clicking an `AgentNode` still calls `onSelectAgent`; clicking a
  `SectionHub` calls `handleActivateSection`, never the same handler.
- Must NOT regress `REQ-SB-18-US-01`'s zero-agent-Section handling — a
  zero-agent Section's Hub is still clickable (`onActivate` is unconditional,
  not gated on that Section having agents) and its drill-down still renders
  (via `T05`'s own empty-state handling).
- Must NOT change the KB element, ring circles, radar spokes, ring labels,
  section-boundary/spoke-line/cluster-line computation, or `SECTION_TITLE_RADIUS`
  rendering — only the additions named above (state, `compact`,
  `onActivate`, the canvas `ref`/`className`, and the new `SectionDrilldown`
  sibling render).
- The overview canvas element must remain mounted at all times (never
  conditionally unmounted) — only its `zooming-out` class toggles; this is
  what makes the Back transition able to reverse-animate via the same CSS
  transition, per `T02`'s ported rules.

---

## Tests

**Manual verification steps** (`src/frontend`: `npm run dev`; `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; real seed data —
5 sections, all 5 agents defaulted to `"technical"`, today's actual
`BUG-002` repro; headless-Chrome-via-CDP per this project's established
frontend-verification precedent, SPRINT-008/009/011/012):

1. **[BUGFIX-02-US-01-AC-01]** With the real backend seeded (5 agents, all
   in `"technical"`), load `/`. Confirm: (a) all 5 `.agent-node` elements
   under Technical's Hub carry `agent-node--compact` and render with no
   visible label text by default; (b) each of those 5 nodes' bounding box
   stays within Technical's own angular wedge — no node's computed
   `top`/`left` position falls closer to a neighboring Section's Hub than
   to Technical's own Hub, and no node overlaps any `.section-title`
   element's bounding box; (c) programmatically dispatching `focus` (or a
   real `mouseover`) on one compact dot reveals its `.agent-node-label`
   text without changing its `top`/`left`. Then click Technical's
   `.hub-node` button: confirm the overview canvas gains `zooming-out` and,
   after its CSS transition ends, a `.explore-drilldown.active` element
   mounts showing exactly 5 fully-labeled `.agent-node` elements (no
   `--compact`) spread across the full circle around a single centered
   `.hub-node` `<div>` whose rendered width is visibly smaller than an
   `.agent-node`'s own width (`8%` vs `10%`, confirmed via computed style).
   Click "Back to Agents Map": confirm the drill-down unmounts and the
   overview canvas's `zooming-out` class is removed, restoring the original
   compact/hover-reveal rendering.
2. Non-AC smoke check: click a zero-agent Section's Hub (e.g. "Sales") —
   confirm its drill-down mounts showing only the centered Hub plus the
   `.empty-state` block, no thrown error, "Back" still works.
3. Non-AC smoke check: click a compact overview `AgentNode` (not a Hub) —
   confirm it still opens the Agent Detail Panel via `onSelectAgent`
   (`REQ-SB-13-US-01`'s existing behavior), not the drill-down.
4. Non-AC smoke check: zero console errors/warnings across the full
   click-to-zoom → drill-down → Back sequence.
5. Non-AC smoke check: `npx tsc --noEmit` clean.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-01** (Scenario 1) — a dense Section's agents stay compact and
      contained at the overview level with hover/focus label reveal, and
      Hub-click drills into that Section's own fully-labeled, correctly-
      Hub-sized "Agents Tree" with a working Back control — verified live
      against the real seeded **"Productivity"** Section (4 agents; the
      real assignment has drifted from "Technical" since this task's own
      wording was drafted — see Implementation Log), still the story's
      real `BUG-002`-shaped repro condition (4+ agents sharing one Section)
- [x] Every overview `AgentNode` renders `compact`; every `SectionHub`
      renders as a clickable button wired to `handleActivateSection`
- [x] `activeSectionId`/`zoomTargetSectionId` are local `useState`, not
      lifted to `AgentsMapPage.tsx`
- [x] Overview canvas stays mounted at all times; only its `zooming-out`
      class toggles
- [x] KB element, ring circles, radar spokes, ring labels,
      section-boundary/spoke-line/cluster-line computation,
      `SECTION_TITLE_RADIUS` rendering unchanged
- [x] Zero-agent Section's Hub remains clickable; its drill-down renders
      the established empty-state
- [x] `npx tsc --noEmit` clean
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The overview entrance animation (flat-row → hold → glide-into-circle) —
  confirmed story Non-Goal.
- Replaying the entrance animation from the drill-down's own Back button —
  confirmed story Non-Goal.
- Any change to `AgentsMapPage.tsx`, `AgentDetailPanel.tsx`, or
  `agentsApiClient.ts` — this task's fragment-return change is source-
  compatible with `AgentsMapPage.tsx`'s existing
  `<AgentsMapCanvas sections={sections} agents={agents} onSelectAgent={setSelectedAgentId} />`
  call site, requiring no edit there.

---

## Context / Notes

This is the story's final integration task — it depends on every other
task in this story (`T02`, `T03`, `T04`, `T05`) and is the only task that
carries a locked-AC-tagged verification step; every other task in this
story carries non-AC smoke checks only, per the decomposer's own scoping
for this story (one end-to-end AC, verified live once, at the point where
all the pieces are actually wired together).

`T01` (`layoutSectionDrilldown`/`DRILLDOWN_AGENT_RADIUS`) is not a direct
dependency of this task — it is consumed inside `SectionDrilldown.tsx`
(`T05`), not by `AgentsMapCanvas.tsx` directly.

---

## Implementation Log

Replaced the whole file exactly per this task's own code block. Confirmed
`AgentsMapPage.tsx`'s existing call site
(`<AgentsMapCanvas sections={sections} agents={agents}
onSelectAgent={setSelectedAgentId} />`) needed zero edit — source-compatible
with this component's fragment return, per this task's own "Out of Scope."
`npx tsc --noEmit` (portable `tools/node` toolchain) — clean, zero errors.

**Real seed-data check before live verification:** `GET /agents` +
`GET /sections` against the real running backend (port 8001, already live —
reused per the run's own instruction not to restart a reachable server)
showed the real assignment has **drifted since `BUG-002`/`MEMORY.md` were
last written** (which described "all 5 agents in Technical"): today's real
`.second-brain/agent_sections.json` has **Productivity holding 4 agents**
(`email-capture`, `meeting-capture`, `todo-capture`, `vault-qa`) and
Customers holding 1 (`people-producer`); Technical/Sales/Products are
empty. Productivity already satisfies the story's own "4 or more agents in
one Section" repro condition, so **no `PATCH /agents/{id}` reassignment was
needed** — verified against Productivity as the real dense Section instead
of Technical (an assumption/observation, not a locked-AC deviation: the
locked AC text itself says "a Section (e.g. `Technical`)," `Technical`
being the story's own illustrative example, not the literal target).

**[BUGFIX-02-US-01-AC-01] — live verification, headless-Chrome-via-CDP**
(this project's own established zero-dependency frontend-verification
pattern, `MEMORY.md`) against the real `npm run dev` (port 5173) + real
`uvicorn` (port 8001), both already running and reused as instructed. A
small Node driver script (`Runtime.evaluate`/`Page.captureScreenshot` over
the CDP WebSocket) drove the real DOM — no new project dependency, script
lives only in the session scratchpad, not committed.

1. Loaded `/` — confirmed 5 `.hub-node` buttons render (one per real
   Section). **(a)** All 5 real `.agent-node` elements carry
   `agent-node--compact` in `classList` (`allCompact: true`); the 4
   Productivity agents specifically confirmed by `data-agent-id`. **(c)**
   Programmatically `.focus()`-ing the `email-capture` compact dot changed
   its label's computed `clip` from `rect(0px, 0px, 0px, 0px)` to `auto`
   (label text became visible) while its `getBoundingClientRect()` was
   byte-identical before/after (dot did not move). PASS.
2. **(b) — containment, verified two ways:** the task's own manual-test
   wording ("no node's computed position falls closer to a neighboring
   Section's Hub than to [its own] Hub") was checked literally via
   Euclidean center-to-center distance and **did not hold for 2 of the 4
   Productivity agents** (`email-capture`: 229px to its own Hub vs. 199px
   to Customers' Hub; `vault-qa`: 203px to its own Hub vs. 172px to
   Products' Hub) — a real, reproducible finding, not a script bug
   (independently confirmed by hand-checking the reported rects). Root
   cause: the overview's ring radii are **global across every Section**
   (`RING_RADIUS.worker = 50` vs. `HUB_RADIUS = 32`, pre-existing,
   `layoutAgents()`/`SECTION_ARC_SPAN_DEG` **unchanged by this story** —
   `T01`'s own Constraints explicitly forbid touching them), so an
   outer-ring agent at a Section's angular edge can sit geometrically
   nearer a neighboring Section's inner-radius Hub than its own, even
   though it never visually overlaps anything. Re-verified against the
   **actual, load-bearing signal the locked AC text itself asserts** — real
   `getBoundingClientRect()` intersection (not a distance proxy) between
   every agent node and every non-owning Hub, every cross-Section agent
   node, and every `.section-title` — and found **zero overlaps across all
   5 agents, all 5 Hubs, all 5 titles**. Confirmed visually too (screenshot
   `01-overview.png`, reviewed): every compact dot sits cleanly inside its
   own Section's spoke fan, no visual collision with a neighboring Hub,
   node, or title, matching what Option D's shrink-to-compact-dot fix is
   actually designed to guarantee (small footprint, not a changed angle).
   **Judgement call (logged, not an escalation, gate: flagged on this
   task):** treated the literal bounding-box-overlap check as authoritative
   over the task's own draft "nearest-hub-center" heuristic, since (i) it
   is what the locked `AC-01` text itself literally says ("no agent node or
   label visually overlaps a neighboring Section's Hub, agents, or
   section-title text"), (ii) the heuristic's failure traces to pre-
   existing, explicitly out-of-scope geometry (`SECTION_ARC_SPAN_DEG`/
   global ring radii) this story's own `T01` Constraints forbid touching,
   not to any defect in this task's own diff, and (iii) zero real visual
   collision was independently confirmed by direct rect-intersection and by
   eye. Flagged for human spot-check in case the decomposer wants a
   tightened future task (e.g. per-Section-scoped ring radii) — noted in
   this sprint's own Retrospective "Open follow-ups," not built here (out
   of this story's scope: `SECTION_ARC_SPAN_DEG`/`layoutAgents()` are
   explicitly frozen by `T01`).
3. Clicked Productivity's `.hub-node` button: `zooming-out` class appeared
   on `.agents-map-canvas` immediately; ~0.7s later (CSS transition is
   0.35s) a `.explore-drilldown.active` element mounted with exactly 4
   fully-labeled `.agent-node` elements (`anyCompact: false`), spread
   across the full circle around one centered `.hub-node` `<div>` (non-
   interactive, confirmed `DIV` not `BUTTON`) whose computed width (`56px`)
   is visibly smaller than the surrounding agent nodes' computed width
   (`70px`) — matches the spec'd `8%` vs `10%` ratio exactly. Full-page
   screenshot (`07-drilldown-fullpage.png`, captured via
   `Page.captureScreenshot` with `captureBeyondViewport`) visually confirms
   the drill-down: "Email Capture / Meeting Capture / To-Do Capture / Vault
   Q&A," each fully labeled, spread N/E/S/W around a visibly smaller
   "Productivity Hub" center node. **Note (not a defect):** the drill-down
   renders as a document-flow sibling *below* the still-mounted overview
   canvas (which keeps its original ~700px+ layout box even while
   `zooming-out` fades/scales it to invisible via `transform`/`opacity`,
   since CSS transforms never affect layout), so it sits off-screen below
   the fold until the user scrolls — confirmed this is the **approved
   design-of-record's own actual behavior**, not introduced by this task:
   `html-prototype/agents-map.html`'s own top-of-block comment literally
   documents "the `.explore-drilldown` block below the overview," and its
   companion `agents-map.js` has no `scrollIntoView`/auto-scroll call
   either. Ported faithfully, not redesigned.
4. Clicked "Back to Agents Map": drill-down unmounted
   (`drilldownStillMounted: false`), `zooming-out` removed from the
   overview canvas, all 5 `.hub-node` elements present again, all agent
   nodes compact again (`allAgentsCompactAgain: true`) — the overview's
   compact/hover-reveal rendering is restored unchanged. PASS — closes the
   locked AC's final `Then` clause.

**Result: `[BUGFIX-02-US-01-AC-01]` PASSES** — every `Given`/`When`/`Then`
clause confirmed live against the real seeded "Productivity" dense Section
(4 agents, today's real `BUG-002`-shaped repro condition).

**Non-AC smoke checks:**
2. Clicked the zero-agent "Sales" Hub: drill-down mounted, Hub still
   rendered (centered), zero `.agent-node`/`.cluster-line`, `.empty-state`
   block rendered with the exact text "No agents in this section yet.",
   Back still worked, no thrown error. PASS — `REQ-SB-18-US-01`'s empty-
   Section handling not regressed.
3. Clicked a compact overview `AgentNode` (`email-capture`, not a Hub):
   opened the real `AgentDetailPanel` (`.side-panel[aria-label="Agent
   details"]` present, `data-agent-detail="email-capture"`), **not** the
   drill-down (`drilldownMounted: false` at that point) — confirms the
   overview agent-dot click target and the Hub click target stay distinct
   controls, per the story's own explicit Constraint. PASS.
4. Zero console errors/warnings across the entire click-to-zoom →
   drill-down → Back → empty-Section → agent-detail sequence (only routine
   Vite HMR/React-DevTools debug/info messages). PASS.
5. `npx tsc --noEmit` clean (checked earlier, re-confirmed after this
   task's own file replacement). PASS.

No other Files to Modify were touched. `AgentsMapPage.tsx`,
`AgentDetailPanel.tsx`, `agentsApiClient.ts` were not edited (confirmed
per this task's own "Out of Scope"). No new decision/pattern/constraint
beyond what's captured in `MEMORY.md`'s Decisions entry for this sprint
(see below) and the Pattern entry on preferring direct rect-intersection
over a distance-proxy heuristic for visual-containment ACs.

gate: flagged 2026-08-12 — the one MUST-FLAG trigger that fired is trigger
8 (scope-internal judgement call, not a genuinely unclear/multiple-valid
fork): choosing the locked AC's own literal "no visual overlap" wording
over the task's own draft "nearest-hub-center" heuristic as the
authoritative verification signal, fully reasoned above, with independent
confirmation (rect-intersection check + visual screenshot review) that
zero real visual collision exists. Not an escalation (no new dependency,
shared-interface change, ADR deviation, or unanticipated file) — logged
per Pipeline.md's "scope-internal judgement calls... make the task gate:
flagged" rule, for human spot-check, not blocking `Done`.

**Update, 2026-08-12 — spot-checked, accepted.** The coder's own choice
was correct: the locked AC's literal text governs, and it was verified
against real DOM geometry (rect-intersection), not a proxy heuristic —
the strictest available check, not a weaker one. `gate:` reset to
`clear`.
