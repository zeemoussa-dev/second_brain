import type { AgentSection, MockAgent } from './mockAgents';
import { DRILLDOWN_AGENT_RADIUS, polarToCartesian } from './polarLayout';
import { layoutSectionDrilldown } from './layoutAgents';
import { SectionHub } from './SectionHub';
import { AgentNode } from './AgentNode';

interface SectionDrilldownProps {
  section: AgentSection;
  // Full agent list — this component filters to its own section's agents
  // itself, matching AgentsMapCanvas.tsx's own existing inline-filter
  // convention (`agents.filter((agent) => agent.sectionId === section.id)`).
  agents: MockAgent[];
  onBack: () => void;
  onSelectAgent: (agentId: string) => void;
}

// Drill-down Hub sits at the canvas's own literal center (radius 0) — see
// T04's own Objective note on why: there is no Knowledge Base/rings to
// key an off-center Hub position against here, unlike the overview.
const DRILLDOWN_HUB_RADIUS = 0;

export function SectionDrilldown({ section, agents, onBack, onSelectAgent }: SectionDrilldownProps) {
  const sectionAgents = layoutSectionDrilldown(
    agents.filter((agent) => agent.sectionId === section.id),
  );
  const hasAgents = sectionAgents.length > 0;

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
      <div className="agents-map-stage">
        <div className="agents-map-canvas">
          {hasAgents && (
            <svg className="agents-map-lines" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
              {sectionAgents.map((agent) => {
                const point = polarToCartesian(DRILLDOWN_AGENT_RADIUS, agent.angleDeg);
                return (
                  <line
                    key={`drilldown-hub-${agent.id}`}
                    className="cluster-line"
                    x1="50"
                    y1="50"
                    x2={point.x}
                    y2={point.y}
                    stroke="var(--color-accent)"
                  />
                );
              })}
            </svg>
          )}
          <SectionHub section={section} radiusOverride={DRILLDOWN_HUB_RADIUS} />
          {sectionAgents.map((agent) => (
            <AgentNode
              key={agent.id}
              agent={agent}
              onSelect={onSelectAgent}
              radiusOverride={DRILLDOWN_AGENT_RADIUS}
            />
          ))}
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
