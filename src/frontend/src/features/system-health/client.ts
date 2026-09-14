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

// What the backend plugin host did with one installed plugin at startup
// (ADR-022). Only `loaded` plugins serve routes or screens.
export interface SystemHealthPlugin {
  id: string;
  name: string;
  version: string;
  status: 'loaded' | 'refused' | 'disabled' | 'invalid';
  reason: string | null;
  routes_prefix: string | null;
}

export interface SystemHealthResponse {
  providers: SystemHealthProvider[];
  plugins: SystemHealthPlugin[];
}

export function fetchSystemHealth(): Promise<SystemHealthResponse> {
  return apiFetch<SystemHealthResponse>('/system-health');
}
