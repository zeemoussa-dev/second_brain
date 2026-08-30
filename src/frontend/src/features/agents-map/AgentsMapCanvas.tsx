import { useEffect, useRef, useState, type CSSProperties, type ReactElement } from 'react';
import type { AgentSection, MockAgent } from './mockAgents';
import type { ClusterMarker, DependencyEdge } from './layoutAgents';
import type { JobTreeEntry } from './agentsApiClient';
import type { PipelineRef } from './pipelineJobTreeAdapter';
import {
  HUB_RADIUS,
  RING_RADIUS,
  SECTION_TITLE_RADIUS,
  describeAnnularSector,
  pointTowards,
  polarToCartesian,
} from './polarLayout';
import { KnowledgeBaseNode } from './KnowledgeBaseNode';
import { SectionHub } from './SectionHub';
import { AgentNode } from './AgentNode';
import { SectionDrilldown } from './SectionDrilldown';
import { ClusterDrilldown } from './ClusterDrilldown';

// <line>'s x1/y1/x2/y2 were never standardized as CSS "geometry
// properties" the way <rect>'s x/y/width/height or <circle>'s cx/cy/r
// were (SVG2 only extended that CSS-stylable list to rect/circle/
// ellipse's own shape properties) -- confirmed live, 2026-08-30, via
// transitionrun/transitionend listeners AND by trying to assign them
// through `element.style` directly (both silently no-op; a matching
// `.cluster-line { transition: x1 ... }` CSS rule never fires because
// there is no real CSS property underneath it to transition). A plain
// JSX x1={}/y1={} attribute change on rotate therefore always SNAPS,
// no CSS trick fixes it. The only reliable fix is animating the
// attribute values ourselves, frame by frame, matching the connected
// node's own 500ms 'ease' timing (cubic ease-out is the closest
// single-formula approximation) so the line visually keeps pace with
// its node instead of arriving instantly.
interface LinePoints {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

function easeOutCubic(t: number): number {
  return 1 - (1 - t) ** 3;
}

function useAnimatedLinePoints(target: LinePoints, durationMs: number): LinePoints {
  const [display, setDisplay] = useState<LinePoints>(target);
  const displayRef = useRef<LinePoints>(target);
  const rafRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    const from = displayRef.current;
    if (from.x1 === target.x1 && from.y1 === target.y1 && from.x2 === target.x2 && from.y2 === target.y2) {
      return;
    }
    const start = performance.now();
    const step = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      const eased = easeOutCubic(t);
      const next: LinePoints = {
        x1: from.x1 + (target.x1 - from.x1) * eased,
        y1: from.y1 + (target.y1 - from.y1) * eased,
        x2: from.x2 + (target.x2 - from.x2) * eased,
        y2: from.y2 + (target.y2 - from.y2) * eased,
      };
      displayRef.current = next;
      setDisplay(next);
      if (t < 1) rafRef.current = requestAnimationFrame(step);
    };
    rafRef.current = requestAnimationFrame(step);
    return () => {
      if (rafRef.current !== undefined) cancelAnimationFrame(rafRef.current);
    };
    // target's own 4 numbers are the real, stable dependencies -- not
    // the `target` object itself, which is a fresh literal every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target.x1, target.y1, target.x2, target.y2, durationMs]);

  return display;
}

function AnimatedLine({
  className,
  x1,
  y1,
  x2,
  y2,
  stroke,
}: {
  className: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  stroke: string;
}) {
  const points = useAnimatedLinePoints({ x1, y1, x2, y2 }, 500);
  return (
    <line
      className={className}
      x1={points.x1}
      y1={points.y1}
      x2={points.x2}
      y2={points.y2}
      stroke={stroke}
    />
  );
}

// The KB<->Hub spoke line AND its own traveling pulse dots (below) share
// ONE animated point pair -- the dots' <animateMotion path="..."> string
// was still being rebuilt from the raw, un-interpolated kbEdge/hubEdge on
// every rotate (2026-08-30, operator: "you just missed the dots on the
// lines between hubs and KB"), so changing `path` mid-rotate snapped the
// dot onto the new straight-line trajectory instantly even after the
// line itself started gliding via AnimatedLine above. Recomputing `path`
// from this SAME useAnimatedLinePoints() output every animation frame
// keeps the dot's path sliding in lockstep with the line's own endpoints
// instead of jumping ahead of them -- retargeting `path` on a running
// <animateMotion> does not reset its own timeline/progress, so the dot
// stays at the same relative position along the trajectory as it moves.
function SpokeConnector({
  kbEdge,
  hubEdge,
  durIn,
  durOut,
  beginIn,
  beginOut,
  dimmed,
}: {
  kbEdge: { x: number; y: number };
  hubEdge: { x: number; y: number };
  durIn: string;
  durOut: string;
  beginIn: string;
  beginOut: string;
  dimmed: boolean;
}) {
  const points = useAnimatedLinePoints(
    { x1: kbEdge.x, y1: kbEdge.y, x2: hubEdge.x, y2: hubEdge.y },
    500,
  );
  const pathIn = `M ${points.x1.toFixed(2)} ${points.y1.toFixed(2)} L ${points.x2.toFixed(2)} ${points.y2.toFixed(2)}`;
  const pathOut = `M ${points.x2.toFixed(2)} ${points.y2.toFixed(2)} L ${points.x1.toFixed(2)} ${points.y1.toFixed(2)}`;
  return (
    <g className={dimmed ? 'is-dimmed' : undefined}>
      <line
        className="spoke-line"
        x1={points.x1}
        y1={points.y1}
        x2={points.x2}
        y2={points.y2}
        stroke="var(--color-accent)"
      />
      <circle className="spoke-pulse-dot" r="0.3">
        <animateMotion dur={`${durIn}s`} begin={`${beginIn}s`} repeatCount="indefinite" path={pathIn} />
      </circle>
      <circle className="spoke-pulse-dot" r="0.3">
        <animateMotion dur={`${durOut}s`} begin={`${beginOut}s`} repeatCount="indefinite" path={pathOut} />
      </circle>
    </g>
  );
}

// Spoke-line endpoints pulled to each circle's own EDGE, not center
// (operator, 2026-08-14/15, porting the prototype's own real technique).
// KB_EDGE_RADIUS = the KB node's own real width footprint / 2 (25.5% —
// 34% * .75, operator 2026-08-15 "Make the Vault Visual smaler to .75"
// — was still 17, the OLD 34%-width value, until the operator's next
// pass flagged the connector lines as no longer reaching the shrunk
// KB: "the Connections to the Hub need to reach the Vault That is now
// Broken when we did the Modification"). HUB_VISUAL_RADIUS = the Hub
// node's own real width footprint / 2 (5% — was also still the OLD 6%
// -width value of 3 from before that Hub was sized down; corrected
// here too, same class of bug, same fix).
const KB_EDGE_RADIUS = 12.75;
const HUB_VISUAL_RADIUS = 2.5;

interface AgentsMapCanvasProps {
  sections: AgentSection[];
  // Overview's own compact-dot set (REQ-SB-38-US-01: already excludes any
  // agent a cluster marker now represents — T01's own `mapAgents`
  // contract).
  agents: MockAgent[];
  // Every agent, unreduced — fed to SectionDrilldown/ClusterDrilldown so
  // neither drill-down ever loses an agent T01's clustering hid from the
  // overview (Scenario 6/AC-06's own "must not narrow the full drill-down"
  // constraint; ClusterDrilldown/T03 filters this down to one cluster's
  // own agentIds).
  fullAgents: MockAgent[];
  clusters: ClusterMarker[];
  // Real depends_on pipeline connections (layoutAgents.ts's own
  // buildDependencyEdges) — replaces the old all-pairs agent<->agent
  // mesh (operator, 2026-08-15: "there is too many Dependencies which
  // will not be true").
  dependencyEdges: DependencyEdge[];
  // Currently-open AgentDetailPanel's own agent id (AgentsMapPage.tsx's
  // selectedAgentId), null when none is open. Passed through to
  // SectionDrilldown so it can apply the click-to-focus
  // center+zoom+ring treatment (operator, 2026-08-16: "when the Panel
  // Open The Agent will be Zoomed in to 3x...") — Section View only,
  // not the overview.
  selectedAgentId: string | null;
  onSelectAgent: (agentId: string) => void;
  // 2026-08-23 -- opens SectionDetailPanel (Overview/Settings tabs, Name/
  // Description/Icon/Color) for a Section's own Hub. Only reachable once
  // already inside that Section's drill-down (SectionDrilldown.tsx passes
  // this as the inner Hub's onActivate) -- the overview's own Hub click
  // still zooms into the drill-down first, matching the existing "click an
  // Agent inside a drill-down to open its own detail panel" pattern rather
  // than overloading the overview Hub click with two different meanings.
  onSelectSection: (sectionId: string) => void;
  // 2026-08-30 (operator: "Currently we don't have any Access to the
  // pipeline") -- every real Pipeline's own {id, name, description} plus
  // its own Job tree (Steps, each with real depends_on). NOT rendered
  // here -- the operator corrected this mid-build ("The pipeline Title
  // should be only Displayed in the drill down not in the map"), so
  // this component only relays both straight through to
  // SectionDrilldown, which does the real placement/hover work.
  pipelineRefs: PipelineRef[];
  pipelineJobTrees: Map<string, JobTreeEntry[]>;
  onSelectPipeline: (pipelineId: string) => void;
  // 2026-08-30 -- PipelineDetailPanel's own currently-hovered Step id
  // (AgentsMapPage.tsx), relayed straight through to SectionDrilldown,
  // which does the real focus-camera work. See that component's own
  // prop comment for the full "why."
  externalFocusAgentId?: string | null;
  // 2026-08-30 -- PipelineDetailPanel's own currently-OPEN Pipeline id
  // (AgentsMapPage.tsx's selectedPipelineId), relayed straight through
  // to SectionDrilldown -- drives the idle ring/card fallback + the
  // whole-chain camera fit. See that component's own prop comment.
  pipelineFocusId?: string | null;
}

// Widened click-to-zoom target (REQ-SB-38-US-01) — BUG-002 Option D's
// original zoomTargetSectionId/activeSectionId pair only ever addressed a
// Section. A cluster marker's click needs a second, distinct identity so
// its own click target can never collide with a Section Hub's (cluster ids
// are always `${sectionId}-${type}-cluster`, never a bare sectionId).
type ZoomTarget = { kind: 'section'; id: string } | { kind: 'cluster'; id: string };

export function AgentsMapCanvas({
  sections, agents, fullAgents, clusters, dependencyEdges, selectedAgentId, onSelectAgent, onSelectSection,
  pipelineRefs, pipelineJobTrees, onSelectPipeline, externalFocusAgentId, pipelineFocusId,
}: AgentsMapCanvasProps) {
  const hasAgents = sections.length > 0 && agents.length > 0;

  // Drill-down / semantic-zoom state (BUG-002 fix, Option D) — both local
  // to this component (architect's Notes): `zoomTarget` drives the
  // overview's own .explore-zoom-overview/.zooming-out CSS transition (set
  // the instant a Hub or cluster marker is clicked, cleared only on Back);
  // `activeTarget` mounts that target's own drill-down, set only once the
  // CSS transition has actually finished (transitionend), so the
  // drill-down never appears mid-zoom.
  const [zoomTarget, setZoomTarget] = useState<ZoomTarget | null>(null);
  const [activeTarget, setActiveTarget] = useState<ZoomTarget | null>(null);
  const overviewCanvasRef = useRef<HTMLDivElement | null>(null);

  // Section-rotation wheel (ported from html-prototype's own #skillmapRotor
  // — "Arrows at the bottom so I can Rotate which section is at the top").
  // A base angle offset added to every Section's hubAngleDeg (and, so
  // agents/lines/titles stay attached to their own Hub, every derived angle
  // below) — local-only, deliberately not threaded up to AgentsMapPage:
  // nothing outside this overview reads it, and it never applies inside a
  // Section's own drill-down (that view has no competing rings/KB to turn
  // against, matching the prototype's own "Section Rotation is a
  // Default-map-only concept" rule).
  const [rotationDeg, setRotationDeg] = useState(0);

  // Hover-dim (ported from html-prototype's own hover-dim/title-glow pass
  // — "when I hover a Section Other Sections go Dimmed the title of that
  // Section goes to a Yellow Color"). One Section id at a time; cleared on
  // mouseleave from whichever Hub/hit-region/title triggered it.
  const [hoveredSectionId, setHoveredSectionId] = useState<string | null>(null);

  useEffect(() => {
    const canvasEl = overviewCanvasRef.current;
    if (!canvasEl || !zoomTarget || activeTarget?.id === zoomTarget.id) return;

    const handleTransitionEnd = (event: TransitionEvent) => {
      if (event.target !== canvasEl) return;
      setActiveTarget(zoomTarget);
    };
    canvasEl.addEventListener('transitionend', handleTransitionEnd);
    return () => canvasEl.removeEventListener('transitionend', handleTransitionEnd);
  }, [zoomTarget, activeTarget]);

  const handleActivateSection = (sectionId: string) => {
    setZoomTarget({ kind: 'section', id: sectionId });
  };

  const handleActivateCluster = (clusterId: string) => {
    setZoomTarget({ kind: 'cluster', id: clusterId });
  };

  const handleBack = () => {
    setActiveTarget(null);
    setZoomTarget(null);
  };

  // Edge chevron paging (ported from html-prototype's own #skillmapChevL/R)
  // — pages directly between two Section drill-downs without an
  // intermediate return to the overview animation. The overview is already
  // fully scaled-out/opacity-0 behind the active drill-down (zoomTarget is
  // already set), so this just swaps BOTH zoomTarget and activeTarget to
  // the new Section in one go instead of routing back through the
  // transitionend-gated flow handleActivateSection/the effect above use for
  // a fresh overview->drilldown entry.
  const handleNavigateSection = (sectionId: string) => {
    const target: ZoomTarget = { kind: 'section', id: sectionId };
    setZoomTarget(target);
    setActiveTarget(target);
  };

  const activeSection = activeTarget?.kind === 'section'
    ? sections.find((section) => section.id === activeTarget.id) ?? null
    : null;
  const activeCluster = activeTarget?.kind === 'cluster'
    ? clusters.find((cluster) => cluster.id === activeTarget.id) ?? null
    : null;
  const activeClusterSection = activeCluster
    ? sections.find((section) => section.id === activeCluster.sectionId) ?? null
    : null;

  return (
    <>
      {/* `is-inactive` once a drill-down is fully mounted (operator,
          2026-08-15: "the Section view is Appearing When I Scroll only")
          — this stage is a flex child of AgentsMapPage.tsx's own
          `.agents-map-page` column; `opacity: 0` (from `.zooming-out`
          below) hides it visually once a Section/cluster is activated,
          but does NOT remove it from FLEX LAYOUT — it kept reserving a
          full screen's worth of `flex: 1` space in the column
          simultaneously with the drill-down's own `.explore-drilldown`
          block rendered right after it, pushing the now-visible
          drill-down below the fold, needing a scroll to reach. `
          is-inactive` (agents-map.css) takes it out of flow entirely via
          `position: absolute` once `activeTarget` is set — which only
          happens AFTER the zoom-in transition has already finished (the
          `transitionend` effect above), so the transition itself still
          plays out normally in-flow beforehand. */}
      <div className={`agents-map-stage${activeTarget ? ' is-inactive' : ''}`}>
        <div
          ref={overviewCanvasRef}
          className={`agents-map-canvas explore-zoom-overview${zoomTarget ? ' zooming-out' : ''}`}
        >
          {/* No dashed background grid at all (operator, 2026-08-15,
              second pass: "The map still Have Dashed Separator and a Text
              for Worker, Producer and Expert in the background Shouldn't
              be there") — the earlier pass removed radar-spoke/ring-
              circle/boundary-circle but kept section-boundary (the dashed
              per-Section divider lines) and the WORKER/EXPERT/PRODUCER
              ring-label text, reasoning they were "functional, not
              decorative." Operator says otherwise — both removed too, so
              the background is now purely the KB/Hub/Agent nodes and
              their real connector lines, nothing else. */}
          <svg className="agents-map-lines" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
            {hasAgents && (
              <>
                {sections.map((section) => {
                  // Invisible hover target spanning the WHOLE wedge between
                  // this Section's own Hub and its title (operator,
                  // 2026-08-15: "the Section Hover is the whole Area
                  // between the Hub and the Title") — the Hub's own small
                  // hit-region and the title text were each independently
                  // hoverable already, but the empty space between them
                  // (past the Hub, short of the title) was dead — hovering
                  // there did nothing. `fill="transparent"` (not `none`) +
                  // `pointerEvents: 'all'` makes an otherwise-invisible
                  // shape genuinely hoverable across every browser, not
                  // just ones that treat a transparent fill as painted by
                  // default. Sits UNDER every HTML node (hub-node/
                  // agent-node/title all carry their own explicit z-index,
                  // this SVG doesn't) — hovering directly on one of those
                  // still resolves to that element's own handler first,
                  // this wedge only ever catches the gaps around them.
                  const sortedAngles = [...sections.map((s) => s.hubAngleDeg)].sort((a, b) => a - b);
                  const currentIndex = sortedAngles.indexOf(section.hubAngleDeg);
                  const prevAngle = currentIndex > 0
                    ? sortedAngles[currentIndex - 1]
                    : sortedAngles[sortedAngles.length - 1] - 360;
                  const nextAngle = currentIndex + 1 < sortedAngles.length
                    ? sortedAngles[currentIndex + 1]
                    : sortedAngles[0] + 360;
                  const wedgeStartAngle = (prevAngle + section.hubAngleDeg) / 2 + rotationDeg;
                  const wedgeEndAngle = (section.hubAngleDeg + nextAngle) / 2 + rotationDeg;
                  return (
                    <path
                      key={`${section.id}-hover-wedge`}
                      d={describeAnnularSector(HUB_RADIUS, SECTION_TITLE_RADIUS, wedgeStartAngle, wedgeEndAngle)}
                      fill="transparent"
                      style={{ pointerEvents: 'all', cursor: 'pointer' }}
                      onMouseEnter={() => setHoveredSectionId(section.id)}
                      onMouseLeave={() => setHoveredSectionId(null)}
                      // Operator, 2026-08-16: "The Clicking Area of the
                      // Section is only the hub not the whole Section as
                      // Hover" — this wedge already covers the Section's
                      // whole hover-zoom footprint (the gaps around the
                      // Hub/Agents/title); it just never had a click
                      // handler, so navigating in only worked if you
                      // landed exactly on the Hub's own small hit-region.
                      onClick={() => handleActivateSection(section.id)}
                    />
                  );
                })}

                {sections.map((section, index) => {
                  // Endpoints pulled to each circle's own EDGE, not center
                  // (operator, 2026-08-14/15, porting the prototype's own
                  // real technique) — KB_EDGE_RADIUS = 17 (KB's real 34%
                  // width / 2), HUB_EDGE_RADIUS = HUB_RADIUS(21) minus the
                  // Hub node's own real 3-unit visual radius (6% width / 2).
                  const kbEdge = polarToCartesian(KB_EDGE_RADIUS, section.hubAngleDeg + rotationDeg);
                  const hubEdge = polarToCartesian(HUB_RADIUS - HUB_VISUAL_RADIUS, section.hubAngleDeg + rotationDeg);
                  // Desynced per-Section timing (operator: "the circles
                  // need to be moving in random times not same over on all
                  // lines") — deterministic from index, not truly random,
                  // so it's stable across re-renders.
                  const durIn = (2.2 + (index % 4) * 0.2).toFixed(1);
                  const durOut = (2.6 + ((index + 2) % 4) * 0.2).toFixed(1);
                  const beginIn = ((index % 3) * 0.3).toFixed(1);
                  const beginOut = (0.5 + (index % 5) * 0.15).toFixed(2);
                  const spokeDimmed = hoveredSectionId !== null && hoveredSectionId !== section.id;
                  return (
                    <SpokeConnector
                      key={`${section.id}-spoke`}
                      kbEdge={kbEdge}
                      hubEdge={hubEdge}
                      durIn={durIn}
                      durOut={durOut}
                      beginIn={beginIn}
                      beginOut={beginOut}
                      dimmed={spokeDimmed}
                    />
                  );
                })}

                {sections.map((section) => {
                  // Hub's own CENTER — used only as the FROM point for
                  // pointTowards() below, never as a line endpoint itself
                  // anymore (operator, 2026-08-15, correcting the previous
                  // pass's own "goes to the center" read: "The Lines
                  // should Reach the Edge of the Hub not the Center of
                  // the hub"). Each Agent sits at a different angle from
                  // the Hub, so — unlike the KB<->Hub spoke-line above,
                  // which can subtract a fixed radius along its own one
                  // shared polar ray — getting "the Hub's edge facing
                  // THIS agent" needs real per-line direction math, done
                  // per agent below via pointTowards().
                  const hubCenter = polarToCartesian(HUB_RADIUS, section.hubAngleDeg + rotationDeg);
                  const sectionAgents = agents.filter((agent) => agent.sectionId === section.id);
                  const agentPoints = sectionAgents.map((agent) => ({
                    agent,
                    // Depth-based radius (layoutAgents.ts's own
                    // computeAgentDepth), not the old flat Type-keyed
                    // RING_RADIUS (operator, 2026-08-15: "the Tree lets
                    // Start by Spreading the Agents between the title
                    // and the Hub").
                    point: polarToCartesian(agent.radius, agent.angleDeg + rotationDeg),
                  }));
                  // White, not accent-colored (operator, 2026-08-15:
                  // "Lines that Connects Agents should be White Slimmer").
                  const stroke = 'var(--color-text)';
                  // Only an agent with no real dependency-tree SUCCESSOR
                  // gets a direct Hub line — the terminal/producer stage
                  // that actually writes to the vault, not the entry point
                  // that merely fetches raw external data. A standalone
                  // agent (no depends_on either direction) is both its own
                  // root and its own terminal, so the plain single-agent
                  // case is unchanged. Fixed 2026-08-23 (operator: "Link to
                  // the Hub Should be The Nodes that Actually write to the
                  // Vault, I can See The nodes that Write to the Hub are
                  // the Farest from the Section Hub, Which is not
                  // Correct") — this previously filtered to ROOTS (agents
                  // with no PREDECESSOR), which drew the Hub spoke to the
                  // pipeline's own entry point instead: backwards from the
                  // operator's own original 2026-08-16 framing ("it should
                  // be the last one in the Tree"), and the longest possible
                  // line (root sits at the OUTERMOST radius per the
                  // depth->radius flip below), which is also what made it
                  // sweep across other chains' territory and cross their
                  // own inner edges.
                  const agentsWithSuccessor = new Set(
                    dependencyEdges.filter((edge) => edge.sectionId === section.id).map((edge) => edge.fromAgentId),
                  );
                  const lines: ReactElement[] = agentPoints
                    .filter(({ agent }) => !agentsWithSuccessor.has(agent.id))
                    .map(({ agent, point }) => {
                      const hubEdge = pointTowards(hubCenter, point, HUB_VISUAL_RADIUS);
                      return (
                        <AnimatedLine
                          key={`${section.id}-hub-${agent.id}`}
                          className="cluster-line"
                          x1={hubEdge.x}
                          y1={hubEdge.y}
                          x2={point.x}
                          y2={point.y}
                          stroke={stroke}
                        />
                      );
                    });
                  // Real depends_on connections only, not every possible
                  // pair (operator, 2026-08-15: "there is too many
                  // Dependencies which will not be true limit Max Agent
                  // Connection to 5") — layoutAgents.ts's own
                  // buildDependencyEdges already applies the 5-connection
                  // cap and scopes each edge to its own Section; this just
                  // resolves the two endpoint ids to this render's own
                  // rotated points.
                  const pointById = new Map(agentPoints.map(({ agent, point }) => [agent.id, point]));
                  for (const edge of dependencyEdges) {
                    if (edge.sectionId !== section.id) continue;
                    const fromPoint = pointById.get(edge.fromAgentId);
                    const toPoint = pointById.get(edge.toAgentId);
                    if (!fromPoint || !toPoint) continue;
                    lines.push(
                      <AnimatedLine
                        key={`${section.id}-dep-${edge.id}`}
                        className="cluster-line"
                        x1={fromPoint.x}
                        y1={fromPoint.y}
                        x2={toPoint.x}
                        y2={toPoint.y}
                        stroke={stroke}
                      />,
                    );
                  }
                  const clusterLinesDimmed = hoveredSectionId !== null && hoveredSectionId !== section.id;
                  // Zoom this Section's own Hub<->Agent/dependency lines
                  // together with the Hub+Agents themselves (operator,
                  // 2026-08-15: "Only the Hub is Zooming not the Whole
                  // Section" -> clarified: "Hub + its Agents + its lines
                  // together") — anchored on the SAME Hub point the HTML
                  // .section-node-group wrapper below scales around, so
                  // both layers (this SVG <g> and that HTML wrapper) grow
                  // in visual lockstep. The KB<->Hub spoke line (its own
                  // separate <g> above) is deliberately NOT included here
                  // — one of ITS endpoints is the KB itself, which isn't
                  // part of this Section's own zooming subtree, so
                  // scaling it would visibly detach that line from the KB.
                  const isSectionHoveredForLines = hoveredSectionId === section.id;
                  const linesGroupStyle: CSSProperties | undefined = isSectionHoveredForLines
                    ? { transform: 'scale(1.1)', transformOrigin: `${hubCenter.x}px ${hubCenter.y}px` }
                    : undefined;
                  return (
                    <g
                      key={`${section.id}-lines`}
                      className={clusterLinesDimmed ? 'is-dimmed' : undefined}
                      style={linesGroupStyle}
                    >
                      {lines}
                    </g>
                  );
                })}
              </>
            )}
          </svg>
          <KnowledgeBaseNode />
          {/* One wrapper per Section, containing that Section's own Hub AND
              its own Agents — the actual "whole Section" hover-zoom unit
              (operator, 2026-08-15: "Only the Hub is Zooming not the Whole
              Section", clarified as "Hub + its Agents + its lines
              together"). `position: absolute; inset: 0` unconditionally
              (not toggled by hover) is what makes this safe: it makes the
              wrapper the containing block for its `position: absolute`
              Hub/Agent children EVERY render, hovered or not, so those
              children's own top/left percentages always resolve against
              this exact box (identical in size/position to
              .agents-map-canvas itself) — the SVG lines' matching <g>
              transform above shares the same Hub-anchored transform-origin
              so both layers zoom in lockstep. */}
          {hasAgents && sections.map((section) => {
            const hubPoint = polarToCartesian(HUB_RADIUS, section.hubAngleDeg + rotationDeg);
            const sectionAgentsForGroup = agents.filter((agent) => agent.sectionId === section.id);
            const isSectionHovered = hoveredSectionId === section.id;
            const groupClassName = `section-node-group${isSectionHovered ? ' is-hovered' : ''}`;
            const groupStyle: CSSProperties = { transformOrigin: `${hubPoint.x}% ${hubPoint.y}%` };
            const isGroupDimmed = hoveredSectionId !== null && !isSectionHovered;
            return (
              <div key={`${section.id}-node-group`} className={groupClassName} style={groupStyle}>
                <SectionHub
                  section={section}
                  onActivate={() => handleActivateSection(section.id)}
                  angleOffsetDeg={rotationDeg}
                  dimmed={isGroupDimmed}
                  isHovered={isSectionHovered}
                  onHoverChange={(hovering) => setHoveredSectionId(hovering ? section.id : null)}
                />
                {sectionAgentsForGroup.map((agent) => (
                  <AgentNode
                    key={agent.id}
                    agent={agent}
                    onSelect={onSelectAgent}
                    compact
                    angleOffsetDeg={rotationDeg}
                    dimmed={isGroupDimmed}
                    onHoverChange={(hovering) => setHoveredSectionId(hovering ? section.id : null)}
                  />
                ))}
              </div>
            );
          })}
          {hasAgents && clusters.map((cluster) => {
            const { x, y } = polarToCartesian(RING_RADIUS[cluster.type], cluster.angleDeg + rotationDeg);
            const clusterDimmed = hoveredSectionId !== null && hoveredSectionId !== cluster.sectionId;
            return (
              <button
                key={cluster.id}
                type="button"
                className={`map-overflow-marker${clusterDimmed ? ' is-dimmed' : ''}`}
                style={{ top: `${y}%`, left: `${x}%` }}
                data-cluster-id={cluster.id}
                onClick={() => handleActivateCluster(cluster.id)}
              >
                <span className="map-overflow-marker-count">{cluster.count}</span>
                <span className="map-overflow-marker-label">+</span>
              </button>
            );
          })}
          {hasAgents && sections.map((section) => {
            const { x, y } = polarToCartesian(SECTION_TITLE_RADIUS, section.hubAngleDeg + rotationDeg);
            const isHoveredTitle = hoveredSectionId === section.id;
            const isDimmedTitle = hoveredSectionId !== null && !isHoveredTitle;
            const titleClassName = [
              'section-title',
              isHoveredTitle ? 'is-hovered' : null,
              isDimmedTitle ? 'is-dimmed' : null,
            ].filter(Boolean).join(' ');
            // Every Section's own color (operator, 2026-08-15: "the Hover
            // effect of the Section Change the Section title to that Same
            // Color") — `--section-color` backs `.section-title.is-hovered`
            // (agents-map.css), falling back to --color-accent when a
            // Section has none set; the underline accent bar below uses
            // the same color always, not just on hover, for one
            // consistent per-Section identity.
            const titleStyle: CSSProperties = { top: `${y}%`, left: `${x}%` };
            if (section.color) titleStyle['--section-color' as string] = section.color;
            return (
              <div
                key={`${section.id}-title`}
                className={titleClassName}
                style={titleStyle}
                onMouseEnter={() => setHoveredSectionId(section.id)}
                onMouseLeave={() => setHoveredSectionId(null)}
                onClick={() => handleActivateSection(section.id)}
              >
                {section.label}
                {/* Operator, 2026-08-15: "I need to have a Section
                    Subtitle... The Subtitle will be Displayed in the
                    Agent Map" — null (a Section with none set) renders
                    nothing extra, same convention color/icon already
                    use. */}
                {section.subtitle && <span className="section-title-subtitle">{section.subtitle}</span>}
                <span className="section-title-accent" style={{ background: section.color ?? 'var(--color-accent)' }} />
              </div>
            );
          })}
        </div>
      </div>
      {hasAgents && !zoomTarget && !activeTarget && (
        // Section-rotation arrows (ported from html-prototype's own
        // #skillmapRotateControls) — hidden once a Section/cluster is
        // focused, matching the prototype's own "the wheel itself isn't
        // relevant once you're inside a Section's own dedicated view" rule.
        <div className="map-rotate-controls">
          <button
            type="button"
            className="map-rotate-btn"
            onClick={() => setRotationDeg((deg) => deg - 60)}
            aria-label="Rotate sections left"
          >
            &#9666;
          </button>
          <span className="map-rotate-label">Rotate</span>
          <button
            type="button"
            className="map-rotate-btn"
            onClick={() => setRotationDeg((deg) => deg + 60)}
            aria-label="Rotate sections right"
          >
            &#9656;
          </button>
        </div>
      )}
      {activeSection && (
        <SectionDrilldown
          section={activeSection}
          sections={sections}
          agents={fullAgents}
          dependencyEdges={dependencyEdges}
          selectedAgentId={selectedAgentId}
          onBack={handleBack}
          onNavigate={handleNavigateSection}
          onSelectAgent={onSelectAgent}
          onOpenSectionSettings={onSelectSection}
          pipelineRefs={pipelineRefs}
          pipelineJobTrees={pipelineJobTrees}
          onSelectPipeline={onSelectPipeline}
          externalFocusAgentId={externalFocusAgentId}
          pipelineFocusId={pipelineFocusId}
        />
      )}
      {activeCluster && activeClusterSection && (
        <ClusterDrilldown
          cluster={activeCluster}
          section={activeClusterSection}
          agents={fullAgents}
          onBack={handleBack}
          onSelectAgent={onSelectAgent}
        />
      )}
    </>
  );
}
