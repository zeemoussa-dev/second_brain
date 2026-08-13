import { apiFetch } from '../../api/client';

export interface AgentSummary {
  id: string;
  name: string;
  type: 'worker' | 'producer' | 'expert';
  section_id: string;
}

export function fetchAgentList(): Promise<AgentSummary[]> {
  return apiFetch<AgentSummary[]>('/agents');
}

export interface AgentDetail {
  id: string;
  name: string;
  type: 'worker' | 'producer' | 'expert';
  settings: { key: string; value: string }[];
  actions: { id: string; label: string }[];
  section_id: string;
  section_name: string;
  provider_id: string;
  provider_name: string;
  provider_available: boolean;
  keywords: string[];
  working_mode: 'autonomous' | 'supervised' | 'manual';
}

export function fetchAgent(agentId: string): Promise<AgentDetail> {
  return apiFetch<AgentDetail>(`/agents/${agentId}`);
}

export function updateAgentAssignment(
  agentId: string,
  body: { section_id?: string; provider_id?: string; keywords?: string[]; working_mode?: string },
): Promise<AgentDetail> {
  return apiFetch<AgentDetail>(`/agents/${agentId}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

export interface TriggerActionResult {
  status: 'ok' | 'error';
  message: string;
}

export function triggerAgentAction(agentId: string, actionId: string): Promise<TriggerActionResult> {
  return apiFetch<TriggerActionResult>(`/agents/${agentId}/actions/${actionId}`, { method: 'POST' });
}

export interface ChatResponse {
  reply: string;
  action_triggered: string | null;
}

export function sendChatMessage(agentId: string, message: string): Promise<ChatResponse> {
  return apiFetch<ChatResponse>(`/agents/${agentId}/chat`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

export interface AgentHistoryEntry {
  kind: 'chat_user' | 'chat_agent' | 'run_event' | 'proposal';
  text: string;
  timestamp: string;
  pending_approval_id?: string;
}

export function fetchAgentHistory(agentId: string): Promise<AgentHistoryEntry[]> {
  return apiFetch<AgentHistoryEntry[]>(`/agents/${agentId}/history`);
}
