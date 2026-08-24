import type { CSSProperties } from 'react';
import type { MockAgent } from './mockAgents';
import { polarToCartesian, type Point } from './polarLayout';
import { getVisualIconName, getIconColorForBackground } from './visualOptions';

interface AgentNodeProps {
  agent: MockAgent;
  onSelect: (agentId: string) => void;
  // Overview-level Option D rendering: every agent always renders as a
  // small, unlabeled dot (hover/focus reveals its label via
  // .agent-node--compact's own CSS, never a density threshold).
  compact?: boolean;
  // Section View drill-down only (operator, 2026-08-15: "Now Agents will
  // be Bigger 0.75 of the Hub") — a bigger footprint than the overview's
  // own 25%-of-Hub .agent-node width, since the drill-down gives one
  // Section the whole canvas instead of a crowded shared arc.
  large?: boolean;
  // Drill-down ("Agents Tree") placement: a fixed ring radius instead of
  // the overview's own depth-based agent.radius, since the drill-down has
  // no Hub-to-title band to spread pipeline depth against.
  radiusOverride?: number;
  // Off-center origin agent.angleDeg/radius are measured from — defaults
  // to the canvas's own literal center (polarToCartesian's own default).
  // SectionDrilldown.tsx passes its own bottom-anchored Hub position here
  // (operator, 2026-08-15: "the title and the Subtitle Rendered at the
  // Bottom... with the Hub then All Agents Appear on top there") so
  // Agents fan out from THAT point, not canvas center.
  center?: Point;
  // Overview "Section rotation" wheel (SectionHub.tsx's own prop of the
  // same name) — added to agent.angleDeg so an agent stays visually
  // attached to its own (already-rotating) Hub instead of the ring turning
  // out from under it. Undefined/0 everywhere else.
  angleOffsetDeg?: number;
  // Overview hover-dim (SectionHub.tsx's own prop of the same name) — true
  // when a DIFFERENT Section than this agent's own is currently hovered.
  dimmed?: boolean;
  // Overview hover-dim — reports hover enter/leave so AgentsMapCanvas can
  // keep its shared hoveredSectionId pointed at THIS agent's own Section
  // while the cursor is over it (operator, 2026-08-15: "Remove the
  // Agents Hover as it affects the Section Hover"). An Agent node has to
  // keep real pointer-events to stay clickable, so it unavoidably sits on
  // top of its own Section's hover-wedge — without this, the cursor
  // passing over an agent made the wedge (and hoveredSectionId) drop out
  // from under it, stuttering the Section's own zoom/glow/title every
  // time the mouse crossed an agent dot. Omitted at the drill-down call
  // site (SectionDrilldown.tsx/ClusterDrilldown.tsx have no Section-level
  // hover-zoom to keep alive).
  onHoverChange?: (hovering: boolean) => void;
  // Section View only: true when THIS Agent's own AgentDetailPanel is
  // currently open (operator, 2026-08-16: "when the Panel Open The
  // Agent will be Zoomed in to 3x with now 2 Borders will be added one
  // the closer one is 2x the Original Border") — thickens this node's
  // own border to 2x via .agent-node--focused. The matching OUTER halo
  // ring (1x border, 0.8 alpha) and the canvas-level center+3x pan/zoom
  // live in SectionDrilldown.tsx instead, since both need to render
  // outside this node's own `overflow: hidden` box.
  focused?: boolean;
}

export function AgentNode({ agent, onSelect, compact, large, radiusOverride, angleOffsetDeg, dimmed, center, onHoverChange, focused }: AgentNodeProps) {
  const radius = radiusOverride ?? agent.radius;
  const { x, y } = polarToCartesian(radius, agent.angleDeg + (angleOffsetDeg ?? 0), center);
  // Filled vs. border-only-with-faint-fill (operator, 2026-08-15: "The
  // Autonmous Agents will be Filled and Human Assistant will be a
  // border with a background 10% alpha") — "Human Assistant" covers
  // both non-autonomous modes together (supervised/manual), not a
  // 3-way split; see agent-node--assisted in agents-map.css.
  const className = [
    'agent-node',
    `agent-node--${agent.type}`,
    agent.workingMode === 'autonomous' ? 'agent-node--autonomous' : 'agent-node--assisted',
    compact ? 'agent-node--compact' : null,
    large ? 'agent-node--large' : null,
    dimmed ? 'is-dimmed' : null,
    focused ? 'agent-node--focused' : null,
  ].filter(Boolean).join(' ');
  // Visual-tab override (agent.icon/agent.color) — null falls back to
  // this node's own default type-colored treatment untouched.
  const iconName = getVisualIconName(agent.icon);
  const style: CSSProperties = { top: `${y}%`, left: `${x}%` };
  if (agent.color) {
    style['--node-color' as string] = agent.color;
    // Only meaningful for a CUSTOM color -- the 3 default Type colors
    // keep using --color-on-accent via the CSS fallback below, unchanged.
    const iconColor = getIconColorForBackground(agent.color);
    if (iconColor) style['--node-icon-color' as string] = iconColor;
  }
  return (
    <button
      type="button"
      className={className}
      style={style}
      data-agent-id={agent.id}
      onClick={() => onSelect(agent.id)}
      onMouseEnter={() => onHoverChange?.(true)}
      onMouseLeave={() => onHoverChange?.(false)}
    >
      {iconName && <span className="material-symbols-outlined agent-node-icon" aria-hidden="true">{iconName}</span>}
      <span className="agent-node-label">{agent.label}</span>
      <span className="agent-node-type">{agent.type}</span>
    </button>
  );
}
