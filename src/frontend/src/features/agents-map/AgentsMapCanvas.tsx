import { useEffect, useRef, useState, type ReactElement } from 'react';
import type { AgentSection, MockAgent } from './mockAgents';
import { BOUNDARY_RADIUS, HUB_RADIUS, RING_RADIUS, polarToCartesian } from './polarLayout';
import { KnowledgeBaseNode } from './KnowledgeBaseNode';
import { SectionHub } from './SectionHub';
import { AgentNode } from './AgentNode';
import { SectionDrilldown } from './SectionDrilldown';

const SECTION_TITLE_RADIUS = 66;
const SECTION_BOUNDARY_INNER_RADIUS = 18;

interface AgentsMapCanvasProps {
  sections: AgentSection[];
  agents: MockAgent[];
  onSelectAgent: (agentId: string) => void;
}

export function AgentsMapCanvas({ sections, agents, onSelectAgent }: AgentsMapCanvasProps) {
  const hasAgents = sections.length > 0 && agents.length > 0;

  // Drill-down / semantic-zoom state (BUG-002 fix, Option D) — both local
  // to this component (architect's Notes): `zoomTargetSectionId` drives
  // the overview's own .explore-zoom-overview/.zooming-out CSS
  // transition (set the instant a Hub is clicked, cleared only on Back);
  // `activeSectionId` mounts that Section's SectionDrilldown, set only
  // once the CSS transition has actually finished (transitionend), so
  // the drill-down never appears mid-zoom.
  const [zoomTargetSectionId, setZoomTargetSectionId] = useState<string | null>(null);
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null);
  const overviewCanvasRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const canvasEl = overviewCanvasRef.current;
    if (!canvasEl || !zoomTargetSectionId || activeSectionId === zoomTargetSectionId) return;

    const handleTransitionEnd = (event: TransitionEvent) => {
      if (event.target !== canvasEl) return;
      setActiveSectionId(zoomTargetSectionId);
    };
    canvasEl.addEventListener('transitionend', handleTransitionEnd);
    return () => canvasEl.removeEventListener('transitionend', handleTransitionEnd);
  }, [zoomTargetSectionId, activeSectionId]);

  const handleActivateSection = (sectionId: string) => {
    setZoomTargetSectionId(sectionId);
  };

  const handleBack = () => {
    setActiveSectionId(null);
    setZoomTargetSectionId(null);
  };

  const activeSection = activeSectionId
    ? sections.find((section) => section.id === activeSectionId) ?? null
    : null;

  return (
    <>
      <div className="agents-map-stage">
        <div
          ref={overviewCanvasRef}
          className={`agents-map-canvas explore-zoom-overview${zoomTargetSectionId ? ' zooming-out' : ''}`}
        >
          <svg className="agents-map-lines" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
            <line className="radar-spoke" x1="50" y1="50" x2="108" y2="50" />
            <line className="radar-spoke" x1="50" y1="50" x2="100.23" y2="79" />
            <line className="radar-spoke" x1="50" y1="50" x2="79" y2="100.23" />
            <line className="radar-spoke" x1="50" y1="50" x2="50" y2="108" />
            <line className="radar-spoke" x1="50" y1="50" x2="21" y2="100.23" />
            <line className="radar-spoke" x1="50" y1="50" x2="-0.23" y2="79" />
            <line className="radar-spoke" x1="50" y1="50" x2="-8" y2="50" />
            <line className="radar-spoke" x1="50" y1="50" x2="-0.23" y2="21" />
            <line className="radar-spoke" x1="50" y1="50" x2="21" y2="-0.23" />
            <line className="radar-spoke" x1="50" y1="50" x2="50" y2="-8" />
            <line className="radar-spoke" x1="50" y1="50" x2="79" y2="-0.23" />
            <line className="radar-spoke" x1="50" y1="50" x2="100.23" y2="21" />
            <circle className="ring-circle" cx="50" cy="50" r={RING_RADIUS.producer} />
            <circle className="ring-circle" cx="50" cy="50" r={RING_RADIUS.expert} />
            <circle className="ring-circle" cx="50" cy="50" r={RING_RADIUS.worker} />
            <circle className="boundary-circle" cx="50" cy="50" r={BOUNDARY_RADIUS} />

            {hasAgents && (
              <>
                {sections.map((section) => {
                  const sortedAngles = [...sections.map((s) => s.hubAngleDeg)].sort((a, b) => a - b);
                  const currentIndex = sortedAngles.indexOf(section.hubAngleDeg);
                  const nextAngle = currentIndex + 1 < sortedAngles.length
                    ? sortedAngles[currentIndex + 1]
                    : sortedAngles[0] + 360;
                  const midAngle = (sortedAngles[currentIndex] + nextAngle) / 2;
                  const inner = polarToCartesian(SECTION_BOUNDARY_INNER_RADIUS, midAngle);
                  const outer = polarToCartesian(BOUNDARY_RADIUS, midAngle);
                  return (
                    <line
                      key={`${section.id}-boundary`}
                      className="section-boundary"
                      x1={inner.x}
                      y1={inner.y}
                      x2={outer.x}
                      y2={outer.y}
                    />
                  );
                })}

                {sections.map((section) => {
                  const hubPoint = polarToCartesian(HUB_RADIUS, section.hubAngleDeg);
                  return (
                    <line
                      key={`${section.id}-spoke`}
                      className="spoke-line"
                      x1="50"
                      y1="50"
                      x2={hubPoint.x}
                      y2={hubPoint.y}
                      stroke="var(--color-accent)"
                    />
                  );
                })}

                {sections.map((section) => {
                  const hubPoint = polarToCartesian(HUB_RADIUS, section.hubAngleDeg);
                  const sectionAgents = agents.filter((agent) => agent.sectionId === section.id);
                  const agentPoints = sectionAgents.map((agent) => ({
                    agent,
                    point: polarToCartesian(RING_RADIUS[agent.type], agent.angleDeg),
                  }));
                  const stroke = 'var(--color-accent)';
                  const lines: ReactElement[] = agentPoints.map(({ agent, point }) => (
                    <line
                      key={`${section.id}-hub-${agent.id}`}
                      className="cluster-line"
                      x1={hubPoint.x}
                      y1={hubPoint.y}
                      x2={point.x}
                      y2={point.y}
                      stroke={stroke}
                    />
                  ));
                  for (let i = 0; i < agentPoints.length; i += 1) {
                    for (let j = i + 1; j < agentPoints.length; j += 1) {
                      lines.push(
                        <line
                          key={`${section.id}-agent-${agentPoints[i].agent.id}-${agentPoints[j].agent.id}`}
                          className="cluster-line"
                          x1={agentPoints[i].point.x}
                          y1={agentPoints[i].point.y}
                          x2={agentPoints[j].point.x}
                          y2={agentPoints[j].point.y}
                          stroke={stroke}
                        />,
                      );
                    }
                  }
                  return lines;
                })}

                <text className="ring-label" x="80" y="51" fontSize="2.6" letterSpacing="0.3">PRODUCER</text>
                <text className="ring-label" x="27.5" y="89.97" fontSize="2.6" letterSpacing="0.3">EXPERT</text>
                <text className="ring-label" x="25" y="8.2" fontSize="2.6" letterSpacing="0.3">WORKER</text>
              </>
            )}
          </svg>
          <KnowledgeBaseNode />
          {hasAgents && sections.map((section) => (
            <SectionHub
              key={section.id}
              section={section}
              onActivate={() => handleActivateSection(section.id)}
            />
          ))}
          {hasAgents && agents.map((agent) => (
            <AgentNode key={agent.id} agent={agent} onSelect={onSelectAgent} compact />
          ))}
          {hasAgents && sections.map((section) => {
            const { x, y } = polarToCartesian(SECTION_TITLE_RADIUS, section.hubAngleDeg);
            return (
              <div key={`${section.id}-title`} className="section-title" style={{ top: `${y}%`, left: `${x}%` }}>
                {section.label}
                <span className="section-title-accent" style={{ background: 'var(--color-accent)' }} />
              </div>
            );
          })}
        </div>
      </div>
      {activeSection && (
        <SectionDrilldown
          section={activeSection}
          agents={agents}
          onBack={handleBack}
          onSelectAgent={onSelectAgent}
        />
      )}
    </>
  );
}
