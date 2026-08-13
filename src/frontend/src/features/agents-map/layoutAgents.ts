import type { AgentSection, MockAgent } from './mockAgents';
import type { AgentSummary } from './agentsApiClient';

export interface SectionSummary {
  id: string;
  name: string;
  agent_ids: string[];
}

// Agents within a section fan out either side of that section's own hub
// angle, evenly spaced across this arc — same visual convention the
// original hand-placed mock data used (ADR-010), just computed instead of
// hardcoded. Capped well below a section's own wedge width (360/n) so an
// agent can never fan out past a neighboring section's boundary (BUG-009:
// a fixed 80deg span overflowed the 72deg wedge produced by 5 sections).
const SECTION_ARC_SPAN_DEG_CAP = 80;
const SECTION_ARC_SPAN_FRACTION = 0.8;

// Purely cosmetic starting rotation for the first (sorted) hub — no
// functional consequence, matches the prior layout's own top-left-ish
// starting orientation (ADR-014 point 6).
const HUB_ANGLE_OFFSET_DEG = -90;

export interface AgentMapLayout {
  sections: AgentSection[];
  mapAgents: MockAgent[];
}

/** Real GET /agents + GET /sections -> the {sections, mapAgents} shape
 * AgentsMapCanvas renders. Section membership comes from each agent's own
 * section_id (no longer derived from `type`); N sections' hub angles are
 * spaced evenly around the full circle, replacing the fixed 3-entry
 * SECTION_META/TYPE_TO_SECTION lookup (ADR-014 point 6). */
export function layoutAgents(agents: AgentSummary[], sectionList: SectionSummary[]): AgentMapLayout {
  const sortedSections = [...sectionList].sort((a, b) => a.id.localeCompare(b.id));
  const n = sortedSections.length;

  const sections: AgentSection[] = sortedSections.map((section, index) => ({
    id: section.id,
    label: section.name,
    hubLabel: `${section.name} Hub`,
    hubAngleDeg: n === 0 ? 0 : index * (360 / n) + HUB_ANGLE_OFFSET_DEG,
  }));

  const agentsBySection = new Map<string, AgentSummary[]>();
  for (const agent of agents) {
    const list = agentsBySection.get(agent.section_id) ?? [];
    list.push(agent);
    agentsBySection.set(agent.section_id, list);
  }

  const wedgeWidthDeg = n === 0 ? 360 : 360 / n;
  const sectionArcSpanDeg = Math.min(SECTION_ARC_SPAN_DEG_CAP, wedgeWidthDeg * SECTION_ARC_SPAN_FRACTION);

  const mapAgents: MockAgent[] = [];
  for (const section of sections) {
    const sectionAgents = agentsBySection.get(section.id) ?? [];
    const count = sectionAgents.length;
    sectionAgents.forEach((agent, index) => {
      const offset = count === 1 ? 0 : (index / (count - 1) - 0.5) * sectionArcSpanDeg;
      mapAgents.push({
        id: agent.id,
        label: agent.name,
        type: agent.type,
        sectionId: section.id,
        angleDeg: section.hubAngleDeg + offset,
      });
    });
  }

  return { sections, mapAgents };
}

/** One Section's own agents -> that same set with angleDeg replaced by an
 * evenly-spaced full-360deg spread, for the drill-down "Agents Tree" view
 * (SectionDrilldown.tsx). Deliberately NOT a branch inside layoutAgents()
 * / SECTION_ARC_SPAN_DEG — conflating the overview's per-Section wedge
 * model and the drill-down's full-circle model in one function/constant
 * is BUG-002's own root-cause shape (a fixed arc that doesn't scale to
 * how much angular budget is actually available). sectionId/hub geometry
 * are irrelevant here since the drill-down centers on the Section's own
 * Hub, not the shared Knowledge Base. */
export function layoutSectionDrilldown(sectionAgents: MockAgent[]): MockAgent[] {
  const n = sectionAgents.length;
  return sectionAgents.map((agent, index) => ({
    ...agent,
    angleDeg: n === 0 ? 0 : (index / n) * 360 + HUB_ANGLE_OFFSET_DEG,
  }));
}
