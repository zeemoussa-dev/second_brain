import { apiFetch } from '../../api/client';

// 2026-08-22 -- real Hermes cron job/schedule/run-history/log surface
// (operator: "Reading Corn Jobs and Their Schedule, Server Status...
// Details Log so we can link and know what happened"). Every shape here
// mirrors hermes_cron.py's own real dataclasses -- no field invented on
// this side.

export interface HermesCronJob {
  id: string;
  name: string;
  prompt: string;
  skill: string;
  schedule_kind: string;
  schedule_display: string;
  enabled: boolean;
  state: string;
  created_at: string;
  next_run_at: string | null;
  last_run_at: string | null;
  last_status: string | null;
  last_error: string | null;
  failure_streak: number;
  deliver: string;
  repeat_times: number | null;
  repeat_completed: number;
}

export interface HermesCronExecution {
  id: string;
  job_id: string;
  status: string;
  claimed_at: string;
  started_at: string | null;
  finished_at: string | null;
  error: string | null;
}

export interface HermesCronRunDetail {
  report_markdown: string | null;
  log_lines: string[];
}

export function fetchCronJobs(): Promise<HermesCronJob[]> {
  return apiFetch<HermesCronJob[]>('/hermes/cron/jobs');
}

export function fetchCronRuns(jobId: string, limit = 20): Promise<HermesCronExecution[]> {
  return apiFetch<HermesCronExecution[]>(`/hermes/cron/jobs/${jobId}/runs?limit=${limit}`);
}

export function fetchCronRunDetail(jobId: string, executionId: string): Promise<HermesCronRunDetail> {
  return apiFetch<HermesCronRunDetail>(`/hermes/cron/jobs/${jobId}/runs/${executionId}/detail`);
}

export interface HermesServerStatus {
  reachable: boolean;
  error?: string;
  [key: string]: unknown;
}

export function fetchHermesStatus(): Promise<HermesServerStatus> {
  return apiFetch<HermesServerStatus>('/hermes/status');
}

// 2026-08-23 -- real Hermes session log for the Agent Activity page
// (operator: "the Agents Activities Tab should get the Agents Log from
// Hermes"). Mirrors hermes_client.py's own real /api/sessions row shape
// (confirmed live) -- only the fields this page actually renders are
// typed here; Hermes returns many more per-session billing/git/handoff
// fields this UI has no use for yet.
export interface HermesSession {
  id: string;
  source: string;
  profile: string | null;
  title: string | null;
  started_at: number | null;
  ended_at: number | null;
  last_activity_at: number | null;
  message_count: number;
  end_reason: string | null;
  is_active: boolean;
  estimated_cost_usd: number | null;
}

export interface HermesSessionsResponse {
  reachable: boolean;
  error?: string;
  sessions: HermesSession[];
  total: number;
}

export function fetchHermesSessions(limit = 50, offset = 0, profile?: string): Promise<HermesSessionsResponse> {
  // `profile` is a real server-side filter (hermes_client.py, confirmed
  // live) -- an Agent's own id IS its real Hermes profile id
  // (hermes_definitions.py's own PRIMARY_PROFILE_ID = "default" etc.), so
  // AgentDetailPanel's Overview tab can pass agentId straight through with
  // no id-mapping step.
  const query = `limit=${limit}&offset=${offset}${profile ? `&profile=${encodeURIComponent(profile)}` : ''}`;
  return apiFetch<HermesSessionsResponse>(`/hermes/sessions?${query}`);
}
