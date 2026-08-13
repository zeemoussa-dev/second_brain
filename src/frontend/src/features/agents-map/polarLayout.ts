import type { AgentType } from './mockAgents';

export const CENTER = 50;
export const RING_RADIUS: Record<AgentType, number> = {
  producer: 30,
  expert: 45,
  worker: 50,
};
// Hub sits well inside the Producer ring (radius 30), not on top of it —
// Ring 3 (Producer, innermost) is agent territory; the Hub only needs to
// clear the KB's own edge (KB width 34% => radius 17) with a clean margin
// on both sides. 21 +/- the hub-node's own (now-smaller) visual radius
// keeps it entirely between the KB and the Producer ring's own agents.
export const HUB_RADIUS = 21;
export const BOUNDARY_RADIUS = 58;
// Section drill-down ("Agents Tree") ring radius — every agent in the
// drilled-into Section spreads across the full 360deg at this one radius
// (no Type-keyed rings here; the drill-down has no competing rings/KB to
// read against, per the approved design). Matches the reference geometry
// hand-derived and live-verified in html-prototype/agents-map.html
// (BUG-002 fix, Option D).
export const DRILLDOWN_AGENT_RADIUS = 40;

export interface Point {
  x: number;
  y: number;
}

/** Ring radius + angle (degrees, 0 = due right, clockwise-positive since
 * the shared 0-100 SVG viewBox's y-axis grows downward) -> {x, y} on that
 * viewBox. Replaces html-prototype/agents-map.html's hand-derived
 * per-node percentages (its own revision comments document ~6 rounds of
 * manually re-deriving every coordinate by hand — ADR-010 Decision 4)
 * with one shared, reusable computation. */
export function polarToCartesian(radius: number, angleDeg: number, center = CENTER): Point {
  const angleRad = (angleDeg * Math.PI) / 180;
  return {
    x: center + radius * Math.cos(angleRad),
    y: center + radius * Math.sin(angleRad),
  };
}
