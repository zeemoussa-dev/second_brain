export type AgentType = 'worker' | 'producer' | 'expert';
export type SectionId = string;

export interface AgentSection {
  id: SectionId;
  label: string;
  hubLabel: string;
  hubAngleDeg: number; // this section's Hub position on the hub band (r=32)
}

export interface MockAgent {
  id: string;
  label: string;
  type: AgentType;
  sectionId: SectionId;
  angleDeg: number; // this agent's position on its type's ring
}

// Real agent data now comes from the backend (GET /agents, agent_registry.py)
// via features/agents-map/agentsApiClient.ts + layoutAgents.ts — this file
// keeps only the shared type definitions above. AgentSection has no `type`
// field as of ADR-014 (REQ-SB-18-US-01) — a Section is user-created and can
// hold agents of any Type, so it no longer has one Type to tint by.
