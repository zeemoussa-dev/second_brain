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

export interface SystemHealthResponse {
  providers: SystemHealthProvider[];
  disabled_agents: SystemHealthDisabledAgent[];
}

export function fetchSystemHealth(): Promise<SystemHealthResponse> {
  return apiFetch<SystemHealthResponse>('/system-health');
}
