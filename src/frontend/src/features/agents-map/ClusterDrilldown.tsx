import type { AgentSection, MockAgent } from './mockAgents';
import type { ClusterMarker } from './layoutAgents';
import { DRILLDOWN_AGENT_RADIUS, polarToCartesian } from './polarLayout';
import { layoutSectionDrilldown } from './layoutAgents';
import { SectionHub } from './SectionHub';
import { AgentNode } from './AgentNode';

interface ClusterDrilldownProps {
  cluster: ClusterMarker;
  // The Section this cluster belongs to — used only to build this
  // drill-down's own heading label (SectionHub is reused unchanged, no new
  // props); never used to filter agents (see below).
  section: AgentSection;
  // Full agent list — filtered here to exactly cluster.agentIds, NOT by
  // sectionId (that would re-include the 5 agents already visible as
  // individual dots on the overview, and any other Type-ring's agents in
  // this Section).
  agents: MockAgent[];
  onBack: () => void;
  onSelectAgent: (agentId: string) => void;
}

// Drill-down Hub sits at the canvas's own literal center (radius 0),
// mirroring SectionDrilldown.tsx's own convention — angle is irrelevant at
// radius 0 (polarToCartesian collapses to the center regardless of angle).
const DRILLDOWN_HUB_RADIUS = 0;

const CLUSTER_TYPE_LABEL: Record<ClusterMarker['type'], string> = {
  worker: 'Worker',
  expert: 'Expert',
  producer: 'Producer',
};

/** A small sibling to SectionDrilldown.tsx, scoped to one cluster marker's
 * own represented agents instead of a whole Section — reuses
 * layoutSectionDrilldown()/SectionHub/AgentNode unchanged (T01/existing),
 * matching SectionDrilldown's own structural/CSS convention (Back button,
 * .explore-drilldown shape, empty-state handling). */
export function ClusterDrilldown({ cluster, section, agents, onBack, onSelectAgent }: ClusterDrilldownProps) {
  const clusterAgentIds = new Set(cluster.agentIds);
  const clusteredAgents = layoutSectionDrilldown(
    agents.filter((agent) => clusterAgentIds.has(agent.id)),
  );
  const hasAgents = clusteredAgents.length > 0;

  const clusterHubSection: AgentSection = {
    id: cluster.id,
    label: section.label,
    hubLabel: `${section.label} — ${CLUSTER_TYPE_LABEL[cluster.type]} overflow (+${cluster.count})`,
    hubAngleDeg: cluster.angleDeg,
    // This cluster marker represents a subset of `section`'s own agents —
    // reuse its color/icon rather than falling back to the generic default.
    color: section.color,
    icon: section.icon,
    subtitle: section.subtitle,
  };

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
              {clusteredAgents.map((agent) => {
                const point = polarToCartesian(DRILLDOWN_AGENT_RADIUS, agent.angleDeg);
                return (
                  <line
                    key={`cluster-drilldown-hub-${agent.id}`}
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
          <SectionHub section={clusterHubSection} radiusOverride={DRILLDOWN_HUB_RADIUS} />
          {clusteredAgents.map((agent) => (
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
          <p className="text-muted">No agents in this cluster.</p>
        </div>
      )}
    </div>
  );
}
