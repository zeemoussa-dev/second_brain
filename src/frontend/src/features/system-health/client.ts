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

// When a capture last actually brought a note in, read from the vault rather
// than from a job's own report (`BUG-085`): email capture failed for four days
// while every job status said `ok`, because "0 emails this week" looks exactly
// like a quiet week.
export interface SystemHealthCapture {
  id: string;
  label: string;
  last_captured_at: string | null;
  age_hours: number | null;
  state: 'fresh' | 'stale' | 'nothing';
  stale_after_hours: number;
}

export interface SystemHealthResponse {
  providers: SystemHealthProvider[];
  plugins: SystemHealthPlugin[];
  captures: SystemHealthCapture[];
}

export function fetchSystemHealth(): Promise<SystemHealthResponse> {
  return apiFetch<SystemHealthResponse>('/system-health');
}
