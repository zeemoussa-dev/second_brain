import { apiFetch } from '../../api/client';

export type BootStageId = 'checking_hermes' | 'loading_sections' | 'loading_agents' | 'loading_skills' | 'loading_providers';
export type BootStageStatus = 'pending' | 'in_progress' | 'done' | 'failed';

export interface BootStage {
  id: BootStageId;
  status: BootStageStatus;
}

export interface BootStatus {
  mode: 'cold_boot' | 'hot_reload';
  state: 'booting' | 'ready' | 'failed';
  current_stage: BootStageId | null;
  stages: BootStage[];
  hermes_reachable: boolean | null;
  error: { file: string; message: string } | null;
  loaded_at: number | null;
}

export function getBootStatus(): Promise<BootStatus> {
  return apiFetch<BootStatus>('/boot-status');
}

export function retryBoot(): Promise<BootStatus> {
  return apiFetch<BootStatus>('/boot-status/retry', { method: 'POST' });
}
