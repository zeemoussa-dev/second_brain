import { apiFetch } from '../../api/client';

export interface SkillSummary {
  id: string;
  name: string;
  description: string;
  tool: string;
  mutates: boolean;
}

export function fetchSkills(): Promise<SkillSummary[]> {
  return apiFetch<SkillSummary[]>('/skills');
}

export function fetchAgentSkills(agentId: string): Promise<SkillSummary[]> {
  return apiFetch<SkillSummary[]>(`/agents/${agentId}/skills`);
}

export function grantAgentSkill(agentId: string, skillId: string): Promise<{ granted: boolean }> {
  return apiFetch<{ granted: boolean }>(`/agents/${agentId}/skills/${skillId}`, { method: 'POST' });
}

export function revokeAgentSkill(agentId: string, skillId: string): Promise<{ revoked: boolean }> {
  return apiFetch<{ revoked: boolean }>(`/agents/${agentId}/skills/${skillId}`, { method: 'DELETE' });
}
