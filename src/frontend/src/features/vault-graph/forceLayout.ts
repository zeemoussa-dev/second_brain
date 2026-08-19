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
    node.vx += (centerX - node.x) * CENTERING_STRENGTH * alpha;
    node.vy += (centerY - node.y) * CENTERING_STRENGTH * alpha;
  }

  for (const node of nodes) {
    if (node.fixed) {
      node.vx = 0;
      node.vy = 0;
      continue;
    }
    node.vx *= VELOCITY_DAMPING;
    node.vy *= VELOCITY_DAMPING;
    node.x += node.vx;
    node.y += node.vy;
  }

  return { nodes, alpha: Math.max(alpha - ALPHA_DECAY, 0) };
}
