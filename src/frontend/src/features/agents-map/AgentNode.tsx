import type { MockAgent } from './mockAgents';
import { RING_RADIUS, polarToCartesian } from './polarLayout';

interface AgentNodeProps {
  agent: MockAgent;
  onSelect: (agentId: string) => void;
  // Overview-level Option D rendering: every agent always renders as a
  // small, unlabeled dot (hover/focus reveals its label via
  // .agent-node--compact's own CSS, never a density threshold).
  compact?: boolean;
  // Drill-down ("Agents Tree") placement: a fixed ring radius instead of
  // polarLayout.ts's Type-keyed RING_RADIUS, since the drill-down has no
  // competing Type rings to place agents on.
  radiusOverride?: number;
}

export function AgentNode({ agent, onSelect, compact, radiusOverride }: AgentNodeProps) {
  const radius = radiusOverride ?? RING_RADIUS[agent.type];
  const { x, y } = polarToCartesian(radius, agent.angleDeg);
  const className = [
    'agent-node',
    `agent-node--${agent.type}`,
    compact ? 'agent-node--compact' : null,
  ].filter(Boolean).join(' ');
  return (
    <button
      type="button"
      className={className}
      style={{ top: `${y}%`, left: `${x}%` }}
      data-agent-id={agent.id}
      onClick={() => onSelect(agent.id)}
    >
      <span className="agent-node-label">{agent.label}</span>
      <span className="agent-node-type">{agent.type}</span>
    </button>
  );
}
