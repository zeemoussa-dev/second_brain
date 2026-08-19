export type AgentType = 'worker' | 'producer' | 'expert';
export type SectionId = string;

export interface AgentSection {
  id: SectionId;
  label: string;
  hubLabel: string;
  hubAngleDeg: number; // this section's Hub position on the hub band (r=32)
  // Every Section's own color/icon (operator, 2026-08-15: "every section
  // Should have its own Color and Icon") — null falls back to
  // --color-accent / a generic "hub" glyph (SectionHub.tsx).
  color: string | null;
  icon: string | null;
  // Short line displayed under the Section title on the Map (operator,
  // 2026-08-15: "I need to have a Section Subtitle and Description The
  // Subtitle will be Displayed in the Agent Map") — null renders nothing
  // extra, same "no title block glyph" convention `icon`/`color` already
  // use.
  subtitle: string | null;
}

export type WorkingMode = 'autonomous' | 'supervised' | 'manual';

export interface MockAgent {
  id: string;
  label: string;
  type: AgentType;
  sectionId: SectionId;
  angleDeg: number; // this agent's position on its type's ring
  // Radial distance from the Hub, between HUB_RADIUS and
  // SECTION_TITLE_RADIUS — driven by the agent's own pipeline depth
  // (layoutAgents.ts's computeAgentDepth, via depends_on), not agent.type
  // (operator, 2026-08-15: "the Tree lets Start by Spreading the Agents
  // between the title and the Hub"). Drill-down views ignore this in
  // favor of AgentNode's own radiusOverride prop.
  radius: number;
  icon: string | null; // user-picked Visual-tab override — null falls back to the type's default treatment
  color: string | null; // user-picked Visual-tab override — null falls back to --agent-color-<type>
  // Agent's own first-settings-entry value (agentsApiClient.ts's own
  // AgentSummary.description) — null when it has none. Shown in the
  // Section View's hover card (operator, 2026-08-16: "a Description of
  // that Agent if Exist").
  description: string | null;
  // Drives the node's own fill treatment (operator, 2026-08-15: "The
  // Autonmous Agents will be Filled and Human Assistant will be a
  // border with a background 10% alpha") — "Human Assistant" covers
  // both non-autonomous modes (supervised/manual): a human is more
  // actively involved in either, unlike the 3-way distinction
  // elsewhere in the app (Settings' own working-mode selector).
  workingMode: WorkingMode;
}

// Real agent data now comes from the backend (GET /agents, agent_registry.py)
// via features/agents-map/agentsApiClient.ts + layoutAgents.ts — this file
// keeps only the shared type definitions above. AgentSection has no `type`
// field as of ADR-014 (REQ-SB-18-US-01) — a Section is user-created and can
// hold agents of any Type, so it no longer has one Type to tint by.
