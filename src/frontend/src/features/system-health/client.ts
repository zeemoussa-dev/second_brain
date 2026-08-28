import { apiFetch } from '../../api/client';

export interface SystemHealthProvider {
  id: string;
  name: string;
  endpoint: string;
  model: string;
  credential_set: boolean;
  is_default: boolean;
  has_real_client: boolean;
}

export interface SystemHealthResponse {
  providers: SystemHealthProvider[];
}

export function fetchSystemHealth(): Promise<SystemHealthResponse> {
  return apiFetch<SystemHealthResponse>('/system-health');
}
