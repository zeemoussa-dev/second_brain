import { apiFetch } from '../../api/client';

export interface SystemHealthProvider {
  id: string;
  name: string;
  endpoint: string;
  model: string;
  credential_set: boolean;
  is_default: boolean;
  has_real_client: boolean;
  agent_ids: string[];
  agent_names: string[];
}

export interface SystemHealthDisabledAgent {
  agent_id: string;
  agent_name: string;
  provider_name: string | null;
}

export interface SystemHealthSchedulingEntry {
  agent_id: string;
  capability_id: string;
  has_run: boolean;
  running: boolean;
  started_at: string | null;
  finished_at: string | null;
  last_outcome: 'success' | 'error' | 'skipped' | null;
  last_error_message: string | null;
  last_duration_seconds: number | null;
  elapsed_seconds: number | null;
}

export interface SystemHealthResponse {
  mcp: { reachable: boolean };
  providers: SystemHealthProvider[];
  disabled_agents: SystemHealthDisabledAgent[];
  scheduling: SystemHealthSchedulingEntry[];
}

export function fetchSystemHealth(): Promise<SystemHealthResponse> {
  return apiFetch<SystemHealthResponse>('/system-health');
}
