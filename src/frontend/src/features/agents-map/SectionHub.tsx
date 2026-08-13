import type { AgentSection } from './mockAgents';
import { HUB_RADIUS, polarToCartesian } from './polarLayout';

interface SectionHubProps {
  section: AgentSection;
  // Overview call site only: opens this Section's drill-down. Omitted at
  // the drill-down's own call site (SectionDrilldown.tsx), where the Hub
  // stays a plain non-interactive element, matching today's behavior.
  onActivate?: () => void;
  // Drill-down call site only: places the Hub at the drill-down canvas's
  // own literal center (pass 0) instead of the overview's HUB_RADIUS
  // position — mirrors AgentNode's own radiusOverride prop (T03).
  radiusOverride?: number;
}

export function SectionHub({ section, onActivate, radiusOverride }: SectionHubProps) {
  const radius = radiusOverride ?? HUB_RADIUS;
  const { x, y } = polarToCartesian(radius, section.hubAngleDeg);
  const style = { top: `${y}%`, left: `${x}%` };

  if (onActivate) {
    return (
      <button
        type="button"
        className="hub-node"
        style={style}
        data-section-id={section.id}
        onClick={onActivate}
      >
        {section.hubLabel}
      </button>
    );
  }

  return (
    <div className="hub-node" style={style}>
      {section.hubLabel}
    </div>
  );
}
