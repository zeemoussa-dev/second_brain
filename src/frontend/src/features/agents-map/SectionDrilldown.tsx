import { useEffect, useRef, useState, type CSSProperties } from 'react';
import type { AgentSection, MockAgent } from './mockAgents';
import { DRILLDOWN_HUB_ANGLE_DEG, polarToCartesian, pointTowards } from './polarLayout';
import { layoutSectionDrilldown, type DependencyEdge } from './layoutAgents';
import { SectionHub } from './SectionHub';
import { AgentNode } from './AgentNode';

interface SectionDrilldownProps {
  section: AgentSection;
  // Full Section list, in the same order AgentsMapCanvas lays out the
  // overview — used only to compute the previous/next Section for the
  // edge chevrons below, never for layout math here.
  sections: AgentSection[];
  // Full agent list — this component filters to its own section's agents
  // itself, matching AgentsMapCanvas.tsx's own existing inline-filter
  // convention (`agents.filter((agent) => agent.sectionId === section.id)`).
  agents: MockAgent[];
  // Real depends_on pipeline connections (layoutAgents.ts's own
  // buildDependencyEdges, already computed once at the top level) —
  // operator, 2026-08-15: "All Agents including Jobs are connected to
  // the Hub no More Pipeline with Zigzag view is Visiable" — this view
  // used to draw a straight line from EVERY agent to the Hub regardless
  // of real pipeline structure, which visually flattened the Agents'
  // own tree-shaped positions into what looked like a plain spoke
  // fan. Filtered to this Section's own edges below.
  dependencyEdges: DependencyEdge[];
  onBack: () => void;
  // Edge chevron paging (ported from html-prototype's own #skillmapChevL/
  // R) — pages directly to the previous/next Section without returning to
  // the overview first. Provided by AgentsMapCanvas.tsx's own
  // handleNavigateSection.
  onNavigate: (sectionId: string) => void;
  onSelectAgent: (agentId: string) => void;
  // Currently-open AgentDetailPanel's own agent id (AgentsMapPage.tsx),
  // null when none is open — operator, 2026-08-16: "when the Panel Open
  // The Agent will be Zoomed in to 3x". Only ever drives the focus
  // treatment below when it matches one of THIS Section's own agents;
  // otherwise (a different Section's agent, or none) the canvas stays
  // at its normal framing.
  selectedAgentId: string | null;
  // 2026-08-23 -- opens SectionDetailPanel for this Section's own Hub.
  // Wired ONLY here (not the overview's SectionHub), so a click on the
  // already-non-interactive drill-down Hub gains a real behavior instead
  // of staying a dead click target, while the overview Hub keeps its
  // existing "zoom into this drill-down" meaning unchanged.
  onOpenSectionSettings: (sectionId: string) => void;
}

// Hub now sits near the BOTTOM of the canvas, not literal center (operator,
// 2026-08-15: "I want to Have the title and the Subtitle Rendered at the
// Bottom... with the Hub then All Agents Appear on top there") — 32 units
// straight down (DRILLDOWN_HUB_ANGLE_DEG = 90) from center puts it well
// clear of the title/subtitle block rendered just below it, while leaving
// enough headroom above for Agents to fan out into.
const DRILLDOWN_HUB_RADIUS = 32;
// How far below the Hub's own point the title block sits.
const DRILLDOWN_TITLE_OFFSET = 11;
// Hub's own real visual footprint in THIS view -- half of
// `.hub-node--large`'s own 9.375% width (agents-map.css), NOT
// AgentsMapCanvas.tsx's own HUB_VISUAL_RADIUS -- the Hub no longer
// stays the same visual size between the overview and this view
// (2026-08-28: "the Hub Node in the Drill down View is very small
// compared to Agents around it, should be 2.5x bigger" reversed that
// earlier decision). Used to pull the Hub-side line endpoint to its own
// EDGE, not its center (operator, 2026-08-15: "the Connection Goes to
// the Center of the HUb not to the Edge") -- same "take care of the
// connections" reasoning DRILLDOWN_AGENT_VISUAL_RADIUS_LARGE_TYPE below
// already applied when Expert/Producer nodes got the same 2x treatment;
// a line trimmed by the OLD, smaller radius would stop short of this
// bigger circle's real edge instead of touching it.
const DRILLDOWN_HUB_VISUAL_RADIUS = 4.6875;
// Half of `.agent-node--large`'s own 3.75% width (agents-map.css) — same
// edge-not-center derivation as DRILLDOWN_HUB_VISUAL_RADIUS above, but for
// the AGENT end of a line (operator, 2026-08-16: "the Lines move to the
// center of the Agent not the edge" — Agents render much bigger here than
// in the overview's tiny dots, so an untrimmed center endpoint is now
// visually obvious).
const DRILLDOWN_AGENT_VISUAL_RADIUS = 1.875;
// Expert/Producer nodes render at 2x width in this view (agents-map.css's
// own `.agent-node--large.agent-node--expert`/`--producer` rule, operator
// 2026-08-25: "Experts and Producers to be 2x the current size... take
// care of the connections") — a line trimmed by the flat radius above
// would stop short of (or poke into) the now-bigger circle's real edge.
// Half of that rule's own 7.5% width.
const DRILLDOWN_AGENT_VISUAL_RADIUS_LARGE_TYPE = 3.75;

function drilldownAgentVisualRadius(type: MockAgent['type']): number {
  return type === 'expert' || type === 'producer'
    ? DRILLDOWN_AGENT_VISUAL_RADIUS_LARGE_TYPE
    : DRILLDOWN_AGENT_VISUAL_RADIUS;
}
// How far the whole canvas zooms in on a clicked Agent while its detail
// panel is open (operator, 2026-08-16: "The Agent will be Zoomed in to
// 3x"). A CAMERA move on the whole `.agents-map-canvas` (pan + scale),
// not a per-node CSS transform — scaling just the one node would
// visually detach it from its own connector lines/Hub, which stay put
// in the node's normal coordinate space.
const FOCUS_ZOOM_SCALE = 3;
// The outer ring's own halo width (5.5%, bigger than .agent-node--large's
// 3.75%, leaving a visible gap) lives entirely in agents-map.css's own
// .agent-focus-ring rule — nothing here needs that value, since the ring
// is positioned via the same top/left % point the focused node itself
// uses.

export function SectionDrilldown({ section, sections, agents, dependencyEdges, onBack, onNavigate, onSelectAgent, selectedAgentId, onOpenSectionSettings }: SectionDrilldownProps) {
  const sectionAgents = layoutSectionDrilldown(
    // Hub agents never appear in `agents` at all -- excluded upstream in
    // AgentManager.get_all (2026-08-28, business logic, not a frontend
    // filter); this Section's own SectionHub center node below already
    // represents it.
    agents.filter((agent) => agent.sectionId === section.id),
  );
  const hasAgents = sectionAgents.length > 0;
  // Which Agent (if any) is currently hovered/zoomed (operator,
  // 2026-08-16: "show the Agent name we zoomed on and a Description of
  // that Agent if Exist below the name and the type") — drives the
  // floating info card rendered near the end of this component, as a
  // SIBLING of the Agent nodes rather than a child of one: `.agent-node`
  // itself needs `overflow: hidden` (the oval-shape fix), which would
  // clip any child content that tries to render outside its own tiny
  // circle, so the card has to live outside that clipping box entirely.
  const [hoveredAgentId, setHoveredAgentId] = useState<string | null>(null);
  // Measured, not the canvas's own literal 50% — operator, 2026-08-16:
  // "now the Agent is in the Center Behind the Panel not between the
  // panel and Side Bar". AgentDetailPanel (agent-panel.css's own
  // `.side-panel`) is a `position: fixed; right: 0;` overlay,
  // `width: min(560px, 100vw)`, that opens as PART OF the exact same
  // click that sets `focused` here — so whenever there's a focused
  // Agent to center on, that panel is already covering the canvas's
  // own right edge. Recomputed on resize below; defaults to a literal
  // 50 (no panel-awareness needed) whenever nothing is focused.
  const stageRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLDivElement | null>(null);
  const [focusTargetXPercent, setFocusTargetXPercent] = useState(50);

  const currentIndex = sections.findIndex((candidate) => candidate.id === section.id);
  // A single Section has no distinct previous/next to page to (the modulo
  // wrap below would just point back at itself) — chevrons only render
  // once there is somewhere else to go.
  const canPage = sections.length > 1 && currentIndex !== -1;
  const previousSection = canPage
    ? sections[(currentIndex - 1 + sections.length) % sections.length]
    : null;
  const nextSection = canPage
    ? sections[(currentIndex + 1) % sections.length]
    : null;

  // The Hub's own off-center point (bottom of the canvas) — everything
  // else in this view (connector lines, Agents, the title block) is
  // positioned relative to THIS point, not literal canvas center, via
  // polarToCartesian's own optional `center` param.
  const hubPoint = polarToCartesian(DRILLDOWN_HUB_RADIUS, DRILLDOWN_HUB_ANGLE_DEG);
  const titleStyle: CSSProperties = { top: `${hubPoint.y + DRILLDOWN_TITLE_OFFSET}%`, left: `${hubPoint.x}%` };
  if (section.color) titleStyle['--section-color' as string] = section.color;

  // Hoisted out of the SVG-only block below (was a render-scoped IIFE) so
  // the hover card near the end of this component can reuse the exact
  // same per-agent points instead of recomputing them a second time.
  const pointById = new Map(
    sectionAgents.map((agent) => [agent.id, polarToCartesian(agent.radius, agent.angleDeg, hubPoint)]),
  );
  // Keyed alongside pointById so the connector lines below can trim each
  // endpoint by THAT agent's own real visual radius (drilldownAgentVisual
  // Radius), not one flat constant that no longer holds now that Expert/
  // Producer nodes render bigger than Worker nodes in this view.
  const agentById = new Map(sectionAgents.map((agent) => [agent.id, agent]));
  const sectionDependencyEdges = dependencyEdges.filter((edge) => edge.sectionId === section.id);
  // Only the terminal/producer stage (nothing depends_on IT — the one
  // that actually writes to the vault) connects straight to the Hub;
  // every earlier stage already has a real line to its own successor
  // below. Fixed 2026-08-23 (operator: "Link to the Hub Should be The
  // Nodes that Actually write to the Vault... the nodes that Write to
  // the Hub are the Farest from the Section Hub, Which is not
  // Correct") — same bug/fix as AgentsMapCanvas.tsx's own overview
  // rendering: this used to filter to agents with no PREDECESSOR (the
  // pipeline's own entry point), the exact opposite of what the operator
  // asked for and the longest possible line (an entry point sits at the
  // OUTERMOST radius, layoutAgents.ts's own depth->radius flip).
  const agentsWithSuccessor = new Set(sectionDependencyEdges.map((edge) => edge.fromAgentId));
  const terminalAgents = sectionAgents.filter((agent) => !agentsWithSuccessor.has(agent.id));
  const hoveredAgent = hoveredAgentId ? sectionAgents.find((agent) => agent.id === hoveredAgentId) ?? null : null;
  const hoveredAgentPoint = hoveredAgent ? pointById.get(hoveredAgent.id) ?? null : null;
  // Only resolves when the open panel's agent belongs to THIS Section —
  // sectionAgents is already filtered down to it, so a different
  // Section's own selectedAgentId correctly falls through to null here.
  const focusedAgent = selectedAgentId ? sectionAgents.find((agent) => agent.id === selectedAgentId) ?? null : null;
  const focusedAgentPoint = focusedAgent ? pointById.get(focusedAgent.id) ?? null : null;

  useEffect(() => {
    if (!focusedAgent) {
      setFocusTargetXPercent(50);
      return;
    }
    const recompute = () => {
      const stageEl = stageRef.current;
      const canvasEl = canvasRef.current;
      if (!stageEl || !canvasEl) return;
      // NOT canvasEl.getBoundingClientRect() — once focused, the canvas
      // itself already carries the 3x pan/zoom `transform` (canvasStyle
      // below), and getBoundingClientRect() reports the PAINTED
      // (post-transform) box, not the natural one percentages need to
      // be computed against. `.agents-map-stage` (this canvas's own
      // offsetParent, always `position: relative`) never gets that
      // transform, so it's always safe to measure directly; combined
      // with the canvas's own offsetLeft/offsetWidth (also transform-
      // immune — `transform` only affects paint, never the box model),
      // this gives the canvas's TRUE natural position/size regardless
      // of whatever transform is currently live on it.
      const stageRect = stageEl.getBoundingClientRect();
      const naturalLeft = stageRect.left + canvasEl.offsetLeft;
      const naturalWidth = canvasEl.offsetWidth;
      if (naturalWidth === 0) return;
      // The Sidebar (shell.css's own .app-shell grid) isn't an overlay —
      // it's a real layout column, so the canvas's own left edge already
      // starts past it; only the panel's fixed-right width needs
      // accounting for here.
      const panelWidth = Math.min(560, window.innerWidth);
      const visibleRightEdge = window.innerWidth - panelWidth;
      const visibleCenterX = (naturalLeft + visibleRightEdge) / 2;
      setFocusTargetXPercent(((visibleCenterX - naturalLeft) / naturalWidth) * 100);
    };
    recompute();
    window.addEventListener('resize', recompute);
    return () => window.removeEventListener('resize', recompute);
  }, [focusedAgent]);
  // Hover wins over focus when both happen to apply (e.g. the panel is
  // open for one Agent while the cursor sits over a different one) —
  // otherwise focus alone keeps the info card up for as long as the
  // panel stays open, not just while actively hovering (operator:
  // "Name is Visible" while the panel is open).
  const activeAgent = hoveredAgent ?? focusedAgent;
  const activeAgentPoint = hoveredAgent ? hoveredAgentPoint : focusedAgentPoint;
  // Camera-style pan+zoom on the whole canvas (see FOCUS_ZOOM_SCALE's
  // own comment) — translate so the focused point lands at
  // (focusTargetXPercent, 50) — the panel-aware X target computed
  // above, not a literal 50 — then scale up around the canvas's own
  // center (transform-origin stays default 50% 50%; unchanged).
  // Percentage translate() values resolve against the canvas's own
  // (unscaled) box, so both terms below need pre-multiplying by the
  // scale factor to still land exactly on target once the scale is
  // also applied — general form of `S*(target-x)`, with an extra
  // `(focusTargetXPercent - 50)` correction term since scale() itself
  // still pivots around literal canvas-center, not around the shifted
  // target (verified algebraically, not just eyeballed).
  const canvasStyle: CSSProperties | undefined = focusedAgentPoint
    ? {
        transform: `translate(${FOCUS_ZOOM_SCALE * (50 - focusedAgentPoint.x) + (focusTargetXPercent - 50)}%, ${FOCUS_ZOOM_SCALE * (50 - focusedAgentPoint.y)}%) scale(${FOCUS_ZOOM_SCALE})`,
      }
    : undefined;

  return (
    <div className="explore-drilldown active" data-agents-drilldown>
      <button
        type="button"
        className="btn"
        data-role="agents-drilldown-back"
        onClick={onBack}
      >
        &larr; Back to Agents Map
      </button>
      {previousSection && (
        <button
          type="button"
          className="section-edge-nav section-edge-nav--left"
          onClick={() => onNavigate(previousSection.id)}
          aria-label={`Previous section: ${previousSection.label}`}
        >
          <span className="section-edge-chev" aria-hidden="true">&lsaquo;</span>
          <span className="section-edge-label">{previousSection.label}</span>
        </button>
      )}
      {nextSection && (
        <button
          type="button"
          className="section-edge-nav section-edge-nav--right"
          onClick={() => onNavigate(nextSection.id)}
          aria-label={`Next section: ${nextSection.label}`}
        >
          <span className="section-edge-label">{nextSection.label}</span>
          <span className="section-edge-chev" aria-hidden="true">&rsaquo;</span>
        </button>
      )}
      <div className="agents-map-stage" ref={stageRef}>
        <div className="agents-map-canvas" style={canvasStyle} ref={canvasRef}>
          {/* Ghost-name watermark (ported from html-prototype's own
              #skillmapGhostName) — large, faint background text naming the
              focused Section. Rendered first (no explicit z-index) so it
              paints/stacks behind the connector-line SVG and the Hub/
              agent nodes below, which all carry their own explicit
              z-index. */}
          <div className="section-ghost-name" aria-hidden="true">{section.label}</div>
          {hasAgents && (
            <svg className="agents-map-lines" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
              {terminalAgents.map((agent) => {
                const point = pointById.get(agent.id);
                if (!point) return null;
                const hubEdge = pointTowards(hubPoint, point, DRILLDOWN_HUB_VISUAL_RADIUS);
                const agentEdge = pointTowards(point, hubPoint, drilldownAgentVisualRadius(agent.type));
                return (
                  <line
                    key={`drilldown-hub-${agent.id}`}
                    className="cluster-line"
                    x1={hubEdge.x}
                    y1={hubEdge.y}
                    x2={agentEdge.x}
                    y2={agentEdge.y}
                    stroke="var(--color-text)"
                  />
                );
              })}
              {sectionDependencyEdges.map((edge) => {
                const fromPoint = pointById.get(edge.fromAgentId);
                const toPoint = pointById.get(edge.toAgentId);
                if (!fromPoint || !toPoint) return null;
                const fromType = agentById.get(edge.fromAgentId)?.type;
                const toType = agentById.get(edge.toAgentId)?.type;
                const fromEdge = pointTowards(fromPoint, toPoint, drilldownAgentVisualRadius(fromType ?? 'worker'));
                const toEdge = pointTowards(toPoint, fromPoint, drilldownAgentVisualRadius(toType ?? 'worker'));
                return (
                  <line
                    key={`drilldown-dep-${edge.id}`}
                    className="cluster-line"
                    x1={fromEdge.x}
                    y1={fromEdge.y}
                    x2={toEdge.x}
                    y2={toEdge.y}
                    stroke="var(--color-text)"
                  />
                );
              })}
            </svg>
          )}
          <SectionHub
            section={section}
            radiusOverride={DRILLDOWN_HUB_RADIUS}
            large
            // Cancels the Section's own overview hubAngleDeg so this
            // Hub always lands at DRILLDOWN_HUB_ANGLE_DEG (straight
            // down from center) regardless of where it sat on the
            // overview map — the exact same point hubPoint above
            // computes.
            angleOffsetDeg={DRILLDOWN_HUB_ANGLE_DEG - section.hubAngleDeg}
            onActivate={() => onOpenSectionSettings(section.id)}
          />
          {sectionAgents.map((agent) => (
            <AgentNode
              key={agent.id}
              // Operator, 2026-08-15: "Section Icons will be displayed"
              // — an agent with no icon override of its own falls back
              // to THIS Section's own icon (every agent here belongs to
              // it), instead of rendering as a plain dot.
              agent={agent.icon ? agent : { ...agent, icon: section.icon }}
              onSelect={onSelectAgent}
              large
              // Operator, 2026-08-15: "Some Agents display a text inside
              // the circle this is not a behavior needed if no icon just
              // display the empty circle if there is an Icon Display the
              // icone" — without `compact`, the label/type spans render
              // as normal (always-visible) flex children, so an Agent
              // with little else competing for the tiny circle's own
              // space could show cropped label text instead of a clean
              // empty dot. `compact` (the SAME convention the overview
              // already uses) keeps them invisible until hover/focus,
              // matching "icon or empty circle" exactly — the name is
              // still reachable via hover, focus, or clicking through to
              // the detail panel.
              compact
              center={hubPoint}
              onHoverChange={(hovering) => setHoveredAgentId(hovering ? agent.id : null)}
              focused={agent.id === selectedAgentId}
            />
          ))}
          {/* Title + subtitle, rendered near the Hub at the bottom
              (operator, 2026-08-15: "I want to Have the title and the
              Subtitle Rendered at the Bottom... with the Hub") — reuses
              the overview's own .section-title/-subtitle/-accent
              treatment for one consistent Section-identity language,
              not hover-interactive here (no Section-level hover-zoom to
              trigger in this single-Section view). */}
          <div className="section-title" style={titleStyle}>
            {section.label}
            {section.subtitle && <span className="section-title-subtitle">{section.subtitle}</span>}
            <span className="section-title-accent" style={{ background: section.color ?? 'var(--color-accent)' }} />
          </div>
          {/* Outer focus-ring halo (operator, 2026-08-16: "2 Borders
              will be added one the closer one is 2x the Original
              Border and 1 outer 1x the Size and 0,8 the Alpha") — the
              INNER ring is just the focused AgentNode's own border,
              thickened via .agent-node--focused (AgentNode.tsx/
              agents-map.css). This OUTER one has to live out here as a
              sibling instead, for the same overflow:hidden-escapes-a-
              child reason the hover/focus info card below does — sized
              bigger than the node itself so it reads as a halo around
              it, not a second ring drawn ON it. */}
          {focusedAgent && focusedAgentPoint && (() => {
            const ringStyle: CSSProperties = {
              top: `${focusedAgentPoint.y}%`,
              left: `${focusedAgentPoint.x}%`,
            };
            if (focusedAgent.color) ringStyle['--node-color' as string] = focusedAgent.color;
            return <div className={`agent-focus-ring agent-focus-ring--${focusedAgent.type}`} style={ringStyle} />;
          })()}
          {/* Hover/focus info card (operator, 2026-08-16: "show the
              Agent name we zoomed on and a Description of that Agent
              if Exist below the name and the type of that agent" —
              stays up for as long as the panel is open, not just while
              actively hovering, via activeAgent = hoveredAgent ??
              focusedAgent above) — a SIBLING of the Agent nodes, not a
              child of one: `.agent-node` needs `overflow: hidden` for
              its own oval-shape fix, which would clip any child trying
              to render outside that tiny circle. Positioned at the
              same point the node itself sits at, offset down past its
              own visual radius. */}
          {activeAgent && activeAgentPoint && (() => {
            const cardStyle: CSSProperties = {
              top: `${activeAgentPoint.y + drilldownAgentVisualRadius(activeAgent.type) + 3}%`,
              left: `${activeAgentPoint.x}%`,
            };
            if (activeAgent.color) cardStyle['--node-color' as string] = activeAgent.color;
            return (
              <div className={`agent-hover-card agent-hover-card--${activeAgent.type}`} style={cardStyle}>
                <span className="agent-hover-card-name">{activeAgent.label}</span>
                <span className="agent-hover-card-type">{activeAgent.type}</span>
                {activeAgent.description && (
                  <p className="agent-hover-card-description">{activeAgent.description}</p>
                )}
              </div>
            );
          })()}
        </div>
      </div>
      {!hasAgents && (
        <div className="empty-state">
          <p className="text-muted">No agents in this section yet.</p>
        </div>
      )}
    </div>
  );
}
