import type { AgentType } from './mockAgents';

export const CENTER = 50;
// Was 3 different radii (producer:30/expert:45/worker:50) — one visual
// ring per Type. Operator, 2026-08-15: "we have a logic to split
// Workers, Producers and Experts in Differnt Location Remove that
// logic for now" + "Bring Agents that Connects to the hub Directly
// Closer". The ring GUIDES (ring-circle/ring-label) were already
// removed in an earlier pass, which left this per-Type position split
// looking arbitrary with nothing marking what it meant — collapsed to
// one shared, closer-to-Hub radius for every Type. Still keyed by
// AgentType (every call site keeps reading `RING_RADIUS[agent.type]`
// unchanged) so re-introducing real per-Type separation later, if ever
// wanted back, is a one-line change here, not a call-site rewrite.
export const RING_RADIUS: Record<AgentType, number> = {
  producer: 32,
  expert: 32,
  worker: 32,
};
// Hub sits well inside the shared Agent radius (32), not on top of it —
// the Hub only needs to clear the KB's own edge (KB width 25.5% =>
// radius 12.75) with a clean margin on both sides. 21 +/- the
// hub-node's own visual radius keeps it entirely between the KB and
// the agents around it.
export const HUB_RADIUS = 21;
export const BOUNDARY_RADIUS = 58;
// Section drill-down ("Agents Tree") ring radius — every agent in the
// drilled-into Section spreads across the full 360deg at this one radius
// (no Type-keyed rings here; the drill-down has no competing rings/KB to
// read against, per the approved design). Matches the reference geometry
// hand-derived and live-verified in html-prototype/agents-map.html
// (BUG-002 fix, Option D).
export const DRILLDOWN_AGENT_RADIUS = 40;
// Drill-down Hub's own facing angle (0 = right, 90 = down, per this
// file's own convention) — shared between SectionDrilldown.tsx (which
// positions the Hub itself here) and layoutAgents.ts's own
// layoutSectionDrilldown (which fans agents out from the OPPOSITE
// direction, `DRILLDOWN_HUB_ANGLE_DEG + 180` = straight up) so both stay
// anchored to the identical point (operator, 2026-08-15: "I want to Have
// the title and the Subtitle Rendered at the Bottom... with the Hub then
// All Agents Appear on top there").
export const DRILLDOWN_HUB_ANGLE_DEG = 90;
// Moved here from AgentsMapCanvas.tsx's own local const — layoutAgents.ts
// now needs it too, to compute each Agent's own depth-based radius
// between the Hub and the title (operator, 2026-08-15: "the Tree lets
// Start by Spreading the Agents between the title and the Hub").
export const SECTION_TITLE_RADIUS = 66;

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
// `center` takes a full Point, not a single scalar (every call site to
// date only ever needed the symmetric default CENTER,CENTER — no caller
// passed an explicit value) — added so a caller can fan Agents out from
// an OFF-CENTER origin, e.g. SectionDrilldown.tsx's own bottom-anchored
// Hub (operator, 2026-08-15: the Section View's Hub/title/subtitle now
// sit near the bottom, not literal canvas center, with Agents fanning
// out above them from that same off-center point).
export function polarToCartesian(radius: number, angleDeg: number, center: Point = { x: CENTER, y: CENTER }): Point {
  const angleRad = (angleDeg * Math.PI) / 180;
  return {
    x: center.x + radius * Math.cos(angleRad),
    y: center.y + radius * Math.sin(angleRad),
  };
}

/** Point `distance` units away from `from`, along the straight line toward
 * `to` — used to pull a connector line's endpoint back from a circular
 * node's own CENTER to its EDGE, in the actual direction of the OTHER
 * end of that specific line (operator, 2026-08-15: "The Lines should
 * Reach the Edge of the Hub not the Center of the hub"). Unlike the
 * KB<->Hub spoke line's own edge trick (subtracting a fixed radius along
 * one shared polar ray, correct there since that line always travels
 * along that exact ray), an Agent<->Hub line travels along a DIFFERENT
 * ray per Agent — plain cartesian direction math, not polar, is what
 * actually generalizes to "the Hub's edge facing THIS ONE agent". */
export function pointTowards(from: Point, to: Point, distance: number): Point {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const length = Math.sqrt(dx * dx + dy * dy) || 1;
  return { x: from.x + (dx / length) * distance, y: from.y + (dy / length) * distance };
}

/** SVG path `d` string for an annular sector (a "pie-slice" ring segment)
 * from `innerRadius` to `outerRadius`, spanning `startAngleDeg` to
 * `endAngleDeg` — used for each Section's own invisible hover target,
 * covering the full wedge between its Hub and its title (operator,
 * 2026-08-15: "the Section Hover is the whole Area between the Hub and
 * the Title"), not just the small Hub hit-region and the title text as
 * two disconnected hotspots with a dead gap between them. */
export function describeAnnularSector(
  innerRadius: number,
  outerRadius: number,
  startAngleDeg: number,
  endAngleDeg: number,
  center: Point = { x: CENTER, y: CENTER },
): string {
  const startOuter = polarToCartesian(outerRadius, startAngleDeg, center);
  const endOuter = polarToCartesian(outerRadius, endAngleDeg, center);
  const startInner = polarToCartesian(innerRadius, startAngleDeg, center);
  const endInner = polarToCartesian(innerRadius, endAngleDeg, center);
  const largeArc = endAngleDeg - startAngleDeg > 180 ? 1 : 0;
  return [
    `M ${startOuter.x} ${startOuter.y}`,
    `A ${outerRadius} ${outerRadius} 0 ${largeArc} 1 ${endOuter.x} ${endOuter.y}`,
    `L ${endInner.x} ${endInner.y}`,
    `A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${startInner.x} ${startInner.y}`,
    'Z',
  ].join(' ');
}
