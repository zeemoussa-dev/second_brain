import { useState } from 'react';

// The central Knowledge Base element — ported from the approved
// html-prototype/agents-map-skilltree-exploration.html redesign (operator,
// 2026-08-14/15): a dense, seeded-random dot constellation (not the
// previous hand-authored 23-neuron/42-synapse mesh), fully transparent at
// rest, no border/background/label — the dot field itself is the only
// visual. Colors cycle through this app's own real agent-type tokens plus
// the shared accent, matching the constellation's own real data grounding.
// 220 * 1.5 (operator, 2026-08-15: "increase the number of points by 50%").
const DOT_COUNT = 330;
const DOT_COLOR_VARS = [
  'var(--agent-color-worker)',
  'var(--agent-color-producer)',
  'var(--agent-color-expert)',
  'var(--color-accent)',
];

interface ConstellationDot {
  cx: number;
  cy: number;
  r: number;
  color: string;
  opacity: number;
}

// Small seeded LCG (same recipe as the prototype's own renderKbConstellation)
// so the scatter is deterministic across reloads/renders, not different
// every time — module-level, computed once, not per-render.
function generateConstellation(): ConstellationDot[] {
  let seed = 1337;
  const rnd = () => {
    seed = (seed * 9301 + 49297) % 233280;
    return seed / 233280;
  };
  const dots: ConstellationDot[] = [];
  for (let i = 0; i < DOT_COUNT; i += 1) {
    const angle = rnd() * Math.PI * 2;
    // Radius biased toward center (rnd()^1.7) — most dots land close in,
    // progressively fewer reach the outer edge.
    const radius = 3 + 41 * Math.pow(rnd(), 1.7);
    dots.push({
      cx: 50 + radius * Math.cos(angle),
      cy: 50 + radius * Math.sin(angle),
      r: 0.35 + rnd() * 1.0,
      color: DOT_COLOR_VARS[i % DOT_COLOR_VARS.length],
      opacity: 0.3 + rnd() * 0.4,
    });
  }
  return dots;
}

const CONSTELLATION = generateConstellation();

export function KnowledgeBaseNode() {
  const [isSpinning, setIsSpinning] = useState(false);

  // Always rotating now, not just on hover (operator, 2026-08-15: "rotate
  // at a very slow speed then the current speed when hover maintain") —
  // a slow ambient idle spin at rest, speeding up to the existing hover
  // rate on `.is-spinning`. Both rules share the same `animation-name`
  // (agents-map.css's own `.kb-brain-svg`/`.kb-brain-svg.is-spinning`,
  // only `animation-duration` differs), so the CSS animation itself
  // keeps rotating continuously across the hover/unhover toggle — no
  // manual computed-transform freezing needed anymore (that was only
  // ever working around the OLD fully-static rest state).
  return (
    <div
      className="kb-node"
      onMouseEnter={() => setIsSpinning(true)}
      onMouseLeave={() => setIsSpinning(false)}
    >
      <svg
        className={`kb-brain-svg${isSpinning ? ' is-spinning' : ''}`}
        viewBox="0 0 100 100"
      >
        {CONSTELLATION.map((dot, index) => (
          <circle
            key={index}
            cx={dot.cx.toFixed(1)}
            cy={dot.cy.toFixed(1)}
            r={dot.r.toFixed(2)}
            fill={dot.color}
            opacity={dot.opacity.toFixed(2)}
          />
        ))}
      </svg>
    </div>
  );
}
