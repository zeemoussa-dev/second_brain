import { apiFetch } from '../../api/client';

export interface AgentActivityLogEntry {
  agent_id: string;
  agent_name: string;
  kind: 'run_event' | 'run_error';
  text: string;
  timestamp: string;
}

export interface AgentActivityOutlookChannel {
  reachable: boolean;
  detail: string | null;
}

export interface AgentActivityResponse {
  activity_log: AgentActivityLogEntry[];
  outlook_channel: AgentActivityOutlookChannel;
}

export function fetchAgentActivity(): Promise<AgentActivityResponse> {
  return apiFetch<AgentActivityResponse>('/agent-activity');
}
