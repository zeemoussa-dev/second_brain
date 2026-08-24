/* Pure force-directed physics for The Vault graph screen
 * (REQ-SB-75-US-01-T02) — node position state plus one simulation-tick
 * function, mirroring features/agents-map/polarLayout.ts's own "pure,
 * testable geometry function, not hand-derived per-node coordinates
 * inline" precedent. No DOM/canvas access in this file — VaultGraphCanvas.
 * tsx owns the requestAnimationFrame loop and calls tickSimulation() once
 * per frame. */

export interface SimulationNode {
  stem: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  /** Pinned to the pointer while being dragged — repulsion/spring/
   * centering forces still act on every OTHER node relative to this one,
   * but this node's own position is never itself moved by them. */
  fixed?: boolean;
  /** Real link count (incoming + outgoing wikilinks) — set/refreshed by
   * VaultGraphCanvas.tsx whenever the caller's edge list changes, never
   * computed in here (this file stays edge-list-shaped, not index-
   * shaped). Drives both this node's own centering pull (below) and its
   * drawn circle radius (VaultGraphCanvas.tsx) — 2026-08-23, operator:
   * "The Circle Size Should be Linked to the Amount of links or
   * Mentions... the more Dense Objects Move towards the Center."
   * `undefined` briefly on a freshly-created node before its first real
   * degree is assigned; treated as 0 everywhere it's read. */
  degree?: number;
  /** Real drawn circle radius (VaultGraphCanvas.tsx's own
   * `radiusForDegree`, computed there alongside `degree` and copied here
   * so collision resolution below can keep differently-sized circles
   * from overlapping without this physics-only file needing to know the
   * radius FORMULA itself — it just reads whatever radius the
   * presentation layer already computed. `undefined` briefly on a
   * freshly-created node; a small safe fallback is used everywhere it's
   * read (`DEFAULT_RADIUS`). */
  radius?: number;
}

export interface SimulationEdge {
  source: string;
  target: string;
}

// Tuning constants — ordinary implementation choices, not locked to any
// AC's specific value (only the tick function's observable properties
// are: positions change tick-over-tick, connected nodes end up closer
// than unconnected ones).
const REPULSION_STRENGTH = 900;
const SPRING_STRENGTH = 0.02;
const SPRING_LENGTH = 60;
const CENTERING_STRENGTH = 0.015;
const VELOCITY_DAMPING = 0.85;
const ALPHA_DECAY = 0.02;
const MIN_DISTANCE_SQUARED = 1;
// Caps how far any one node can move in a single tick (2026-08-23 —
// operator: "the View Shows only like 20 Node while we have more than
// 1000 Nodes"). Confirmed live at the vault's real current scale (1,126
// nodes / 6,032 edges, well past this simulation's original ~680-node
// design point): repulsion is summed across every OTHER node every tick,
// so a node caught in a dense, edge-less cluster (many same-kind notes
// with no wikilinks between them, e.g. RawMessage/Person) can accumulate
// velocity from hundreds of simultaneously-close neighbors in one tick.
// VELOCITY_DAMPING alone only shrinks that by 15% per tick — nowhere
// near enough to stop it compounding: a node's own huge residual
// velocity carries it even farther on the NEXT tick, into an even denser
// crowd, repeating and diverging exponentially within a few dozen frames
// until positions overflow into the 1e+29+ range (measured live, via a
// canvas.arc() call-site hook) — off-canvas, permanently invisible, with
// no error and no way to recover short of a full remount. Clamping
// magnitude every tick breaks that feedback loop at its source, the same
// standard technique real force-layout libraries (e.g. d3-force's own
// velocityDecay + an implicit max-speed clamp in several presets) use to
// keep an N-body simulation numerically stable regardless of local
// density — chosen at roughly one SPRING_LENGTH per tick, fast enough to
// look identical to the old unclamped motion at this screen's original
// tested scale, while making a runaway node physically unable to exit
// the visible canvas in one step at any node count.
const MAX_VELOCITY = 60;
// Degree-weighted centering (2026-08-23, operator: "the more Dense
// Objects Move towards the Center") -- a node's own centering pull is
// multiplied by 1 + sqrt(degree) * this factor, so a heavily-linked hub
// note gets pulled toward the middle noticeably harder than a lightly-
// linked one, while a genuinely isolated (degree 0) note keeps the
// UNMODIFIED base pull and drifts naturally outward under repulsion from
// everything else -- sqrt, not linear, so one extreme outlier (a note
// with hundreds of backlinks) doesn't dwarf every other real hub and
// collapse the whole layout onto one point. Raised from an initial 0.35
// (2026-08-23, operator: "Nodes with more connections should be closer
// to the center" -- the first pass was too weak to visibly separate
// hubs from the periphery at this graph's real density; a hub's own
// local repulsion from its many close neighbors was competing with,
// not losing to, the centering pull).
const DEGREE_CENTERING_FACTOR = 1.1;
// Collision resolution's own safe fallback (2026-08-23, operator:
// "Nodes are Overlapping Massively") -- matches VaultGraphCanvas.tsx's
// own NODE_RADIUS_MIN, used only in the narrow window before a fresh
// node's real radius has been assigned.
const DEFAULT_RADIUS = 4;
// Real, guaranteed non-overlap gap enforced between any two circles'
// own edges (not their centers) -- a few px of real breathing room, not
// edge-to-edge touching, which still reads as "overlapping" at a glance.
const COLLISION_PADDING = 2;

/** Deterministic starting layout — nodes placed evenly around a circle
 * (order-stable given the same stem list), not literally random, so a
 * fresh mount's first frame is never a degenerate all-nodes-at-one-point
 * pile that repulsion has to untangle from scratch. */
export function createInitialNodes(stems: string[], width: number, height: number): SimulationNode[] {
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) / 3;
  const count = Math.max(stems.length, 1);
  return stems.map((stem, index) => {
    const angle = (index / count) * Math.PI * 2;
    return {
      stem,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
      vx: 0,
      vy: 0,
    };
  });
}

/** One simulation step — repulsion (every node pair pushes apart) + edge
 * springs (connected nodes pulled toward SPRING_LENGTH apart) + a mild
 * centering force (keeps the graph from drifting off-canvas), scaled by
 * `alpha` (a settling factor that decays toward 0 tick-over-tick so the
 * layout stabilizes rather than jittering forever). Mutates `nodes` in
 * place for performance at this screen's real ~680-node scale (an O(n^2)
 * repulsion pass every frame) and returns the same array plus the next
 * alpha — the caller (VaultGraphCanvas) resets alpha back toward 1 on a
 * drag interaction to re-animate the affected neighborhood. */
export function tickSimulation(
  nodes: SimulationNode[],
  edges: SimulationEdge[],
  width: number,
  height: number,
  alpha: number,
): { nodes: SimulationNode[]; alpha: number } {
  const centerX = width / 2;
  const centerY = height / 2;
  const nodeByStem = new Map(nodes.map((node) => [node.stem, node]));

  for (let i = 0; i < nodes.length; i += 1) {
    for (let j = i + 1; j < nodes.length; j += 1) {
      const nodeA = nodes[i];
      const nodeB = nodes[j];
      const dx = nodeA.x - nodeB.x;
      const dy = nodeA.y - nodeB.y;
      const distanceSquared = Math.max(dx * dx + dy * dy, MIN_DISTANCE_SQUARED);
      const distance = Math.sqrt(distanceSquared);
      const force = (REPULSION_STRENGTH * alpha) / distanceSquared;
      const forceX = (dx / distance) * force;
      const forceY = (dy / distance) * force;
      if (!nodeA.fixed) {
        nodeA.vx += forceX;
        nodeA.vy += forceY;
      }
      if (!nodeB.fixed) {
        nodeB.vx -= forceX;
        nodeB.vy -= forceY;
      }
    }
  }

  for (const edge of edges) {
    const source = nodeByStem.get(edge.source);
    const target = nodeByStem.get(edge.target);
    if (!source || !target) continue;
    const dx = target.x - source.x;
    const dy = target.y - source.y;
    const distance = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
    const displacement = distance - SPRING_LENGTH;
    const force = SPRING_STRENGTH * displacement * alpha;
    const forceX = (dx / distance) * force;
    const forceY = (dy / distance) * force;
    if (!source.fixed) {
      source.vx += forceX;
      source.vy += forceY;
    }
    if (!target.fixed) {
      target.vx -= forceX;
      target.vy -= forceY;
    }
  }

  for (const node of nodes) {
    if (node.fixed) continue;
    const centeringMultiplier = 1 + Math.sqrt(node.degree ?? 0) * DEGREE_CENTERING_FACTOR;
    const centeringStrength = CENTERING_STRENGTH * centeringMultiplier;
    node.vx += (centerX - node.x) * centeringStrength * alpha;
    node.vy += (centerY - node.y) * centeringStrength * alpha;
  }

  for (const node of nodes) {
    if (node.fixed) {
      node.vx = 0;
      node.vy = 0;
      continue;
    }
    node.vx *= VELOCITY_DAMPING;
    node.vy *= VELOCITY_DAMPING;
    const speed = Math.sqrt(node.vx * node.vx + node.vy * node.vy);
    if (speed > MAX_VELOCITY) {
      const scale = MAX_VELOCITY / speed;
      node.vx *= scale;
      node.vy *= scale;
    }
    node.x += node.vx;
    node.y += node.vy;
  }

  // Collision resolution (2026-08-23, operator: "Nodes are Overlapping
  // Massively") -- a DIRECT position correction, not another force.
  // Plain inverse-square repulsion never guarantees two circles end up
  // farther apart than their own combined radii -- it only ever pushes
  // proportionally to distance, so a close, low-alpha-settled pair (or
  // two circles that only grew large enough to overlap AFTER their
  // positions had already stopped moving much) can sit stably
  // overlapped forever. This pass runs unconditionally (not scaled by
  // alpha) and directly moves any two overlapping circles apart until
  // their edges (not centers) clear COLLISION_PADDING -- a hard
  // guarantee, not a tendency, and correct now that circle radius
  // varies per node (larger hubs need proportionally more real
  // separation than two small leaf notes, which plain repulsion has no
  // way to know about at all).
  for (let i = 0; i < nodes.length; i += 1) {
    for (let j = i + 1; j < nodes.length; j += 1) {
      const nodeA = nodes[i];
      const nodeB = nodes[j];
      const minDistance = (nodeA.radius ?? DEFAULT_RADIUS) + (nodeB.radius ?? DEFAULT_RADIUS) + COLLISION_PADDING;
      const dx = nodeB.x - nodeA.x;
      const dy = nodeB.y - nodeA.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      if (distance >= minDistance || distance === 0) continue;
      const overlap = minDistance - distance;
      const ux = dx / distance;
      const uy = dy / distance;
      if (nodeA.fixed && nodeB.fixed) continue;
      if (!nodeA.fixed && !nodeB.fixed) {
        nodeA.x -= ux * overlap * 0.5;
        nodeA.y -= uy * overlap * 0.5;
        nodeB.x += ux * overlap * 0.5;
        nodeB.y += uy * overlap * 0.5;
      } else if (!nodeA.fixed) {
        nodeA.x -= ux * overlap;
        nodeA.y -= uy * overlap;
      } else {
        nodeB.x += ux * overlap;
        nodeB.y += uy * overlap;
      }
    }
  }

  return { nodes, alpha: Math.max(alpha - ALPHA_DECAY, 0) };
}
