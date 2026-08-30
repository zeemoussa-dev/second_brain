import { apiFetch } from '../../api/client';

// 2026-08-30 (operator: "Currently we don't have any Access to the
// pipeline") -- the real Pipeline dataclass (business/core/pipelines),
// GET /pipelines/{id}. Distinct from AgentDetail -- a Pipeline has no
// tools/scope/depends_on of its own, but does have real cron status and
// a Steps list neither AgentDetail nor JobSettings expose together.
export interface PipelineStep {
  id: string;
  name: string;
  description: string;
  depends_on: string[];
  type: 'worker' | 'producer';
}

export interface PipelineDetail {
  id: string;
  name: string;
  description: string;
  section_id: string;
  cron_profile_id: string | null;
  cron_job_id: string | null;
  cron_enabled: boolean | null;
  cron_schedule: string | null;
  cron_last_run_at: string | null;
  cron_next_run_at: string | null;
  cron_last_status: string | null;
  steps: PipelineStep[];
}

export function fetchPipelineDetail(pipelineId: string): Promise<PipelineDetail> {
  return apiFetch<PipelineDetail>(`/pipelines/${pipelineId}`);
}
