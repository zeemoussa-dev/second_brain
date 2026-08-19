import { apiFetch } from '../../api/client';

export interface AgentSchedule {
  agent_id: string;
  capability_id: string;
  interval_value: number;
  interval_unit: 'minutes' | 'hours';
  created_at: string;
  updated_at: string;
}

export function fetchSchedules(agentId: string): Promise<AgentSchedule[]> {
  return apiFetch<AgentSchedule[]>(`/agents/${agentId}/schedules`);
}

export function createSchedule(
  agentId: string,
  body: { capability_id: string; interval_value: number; interval_unit: string },
): Promise<AgentSchedule> {
  return apiFetch<AgentSchedule>(`/agents/${agentId}/schedules`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function updateSchedule(
  agentId: string,
  capabilityId: string,
  body: { interval_value?: number; interval_unit?: string; new_capability_id?: string },
): Promise<AgentSchedule> {
  return apiFetch<AgentSchedule>(`/agents/${agentId}/schedules/${capabilityId}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

export function removeSchedule(agentId: string, capabilityId: string): Promise<{ removed: boolean }> {
  return apiFetch<{ removed: boolean }>(`/agents/${agentId}/schedules/${capabilityId}`, { method: 'DELETE' });
}

export function runScheduleNow(agentId: string, capabilityId: string): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(`/agents/${agentId}/schedules/${capabilityId}/run-now`, {
    method: 'POST',
  });
}
