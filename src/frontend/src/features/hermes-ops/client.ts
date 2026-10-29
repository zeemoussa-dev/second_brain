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

// A crawler as the Crawlers screen reads one (`REQ-SB-102`): Hermes'
// own job, plus the fields its client drops, plus what the operator
// calls it. `/hermes/cron/jobs` above is untouched — it is Hermes' own
// shape and other callers depend on it.

/** What a crawler actually runs. `kind` is derived, because the jobs on
 *  a real install are not one shape: most run a `script` with no
 *  prompt at all, some carry a one-sentence `instruction`, and a few
 *  spell out numbered `steps`. A screen that assumed any one of those
 *  would show nothing for most of them. `unknown` is honest and real —
 *  a job this app can see running but cannot see the definition of. */
export interface CrawlerDefinition {
  kind: 'script' | 'steps' | 'instruction' | 'unknown';
  /** The .py for a script job, or the skill for an agent one. */
  runs: string;
  /** The prompt verbatim, when there is one. */
  says: string;
  skills: string[];
  steps: Array<{ number: string; says: string }>;
}

export interface Crawler extends HermesCronJob {
  /** The operator's own name for it. Empty means it has none and
   *  Hermes' `name` is what to show. */
  friendly_name: string;
  tags: string[];
  definition: CrawlerDefinition;
  /** Why a run that reports `delivery_failed` failed — Hermes keeps
   *  this apart from `last_error`, and without it that state has no
   *  explanation anywhere on the screen. */
  delivery_error: string | null;
  origin: Record<string, unknown> | null;
  model: string | null;
}

export interface CrawlersView {
  crawlers: Crawler[];
  /** Every tag in use, for the filter — derived from the crawlers, so
   *  a tag cannot linger in the filter after the last job using it
   *  loses it. */
  tags: string[];
  annotations_unreadable: string | null;
}

export function fetchCrawlers(): Promise<CrawlersView> {
  return apiFetch<CrawlersView>('/hermes/crawlers');
}

export function saveCrawlerAnnotation(
  jobId: string, friendlyName: string, tags: string[],
): Promise<{ friendly_name: string; tags: string[] }> {
  return apiFetch(`/hermes/crawlers/${encodeURIComponent(jobId)}/annotation`, {
    method: 'PUT',
    body: JSON.stringify({ friendly_name: friendlyName, tags }),
  });
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

// ---- one session, read as a conversation (REQ-SB-100) -----------------

/** A tool call lifted out of the message it rode in on and paired with
 * the `tool` message that answered it. Hermes stores those as two rows
 * joined by `tool_call_id`, so without this join a call and its result
 * sit far apart in the raw list. */
export interface TranscriptToolCall {
  id: string | null;
  name: string | null;
  arguments: unknown;
  answered: boolean;
  answer: string | null;
  answered_by_tool: string | null;
  unreadable?: string;
}

export interface TranscriptTurn {
  id: number | null;
  role: string;
  said: string | null;
  /** The model's own account of why, when it recorded one. */
  thinking: string | null;
  tool_calls: TranscriptToolCall[];
  at: number | null;
  tokens: number | null;
  finish_reason: string | null;
  effect_disposition: string | null;
  raw: Record<string, unknown>;
}

export interface SessionTranscript {
  reachable: boolean;
  error?: string;
  session_id: string;
  session?: Record<string, unknown>;
  pagination?: { limit: number; offset: number; order: string; returned: number } | null;
  turns: TranscriptTurn[];
  what_happened: {
    turns_by_role: Record<string, number>;
    /** The sequence of tools IS the route the session actually took. */
    tools_in_order: string[];
    distinct_tools: string[];
    tool_calls_without_an_answer: number;
  };
  counts: { messages_in: number; turns_out: number; tool_answers_folded_in: number };
}

export function fetchSessionTranscript(
  sessionId: string, limit = 200, offset = 0,
): Promise<SessionTranscript> {
  return apiFetch<SessionTranscript>(
    `/hermes/sessions/${encodeURIComponent(sessionId)}/transcript?limit=${limit}&offset=${offset}`,
  );
}

// ---- the outside doors (REQ-SB-102) -----------------------------------

export interface EntryPointObservation {
  source: string;
  chat_id: string;
  chat_name: string | null;
  chat_type: string | null;
  answered_by: string[];
  session_count: number;
  last_seen: string | null;
  last_session_id: string | null;
}

export interface EntryPoint {
  label?: string;
  source: string;
  chat_id: string;
  agent_id: string | null;
  /** Whose door this is (`REQ-SB-103`) — the person a Workflow's human
   *  step asks when a run comes in through it. A reference, not a
   *  snapshot: renaming a person fixes every door at once, while a run
   *  keeps who it resolved to when it started. Absent means nobody is
   *  declared, which is a real state and never back-filled with the
   *  operator. */
  owner_user_id?: string | null;
  status: 'agrees' | 'drifted' | 'declared_only' | 'observed_only';
  observed: EntryPointObservation | null;
  answered_by: string[];
}

export interface EntryPointsView {
  reachable: boolean;
  error?: string;
  entry_points: EntryPoint[];
  summary: { by_status: Record<string, number>; needs_attention: EntryPoint[] };
  scanned: { sessions_read: number; window: number; internal_sources_excluded: string[] } | null;
}

export function fetchEntryPoints(): Promise<EntryPointsView> {
  return apiFetch<EntryPointsView>('/hermes/entry-points');
}

export function saveEntryPoints(entries: Array<Partial<EntryPoint>>): Promise<EntryPointsView> {
  return apiFetch<EntryPointsView>('/hermes/entry-points', {
    method: 'PUT',
    body: JSON.stringify(entries),
  });
}

/** The `when` on each of one agent's specialist edges (`REQ-SB-102`).
 * Saving does NOT rewrite the soul — publishing is the separate,
 * deliberate `publishSpecialists` call, because a prompt change is a
 * behaviour change on a live agent. */
export function saveRoutingConditions(
  agentId: string, conditions: Record<string, string>,
): Promise<Record<string, string>> {
  return apiFetch<Record<string, string>>(
    `/hermes/agents/${encodeURIComponent(agentId)}/routing-conditions`,
    { method: 'PUT', body: JSON.stringify(conditions) },
  );
}

/** Writes this agent's specialist block, conditions included, into its
 * real SOUL.md. One agent, explicitly, never a sweep. */
export function publishSpecialists(agentId: string): Promise<unknown> {
  return apiFetch<unknown>(
    `/agents/${encodeURIComponent(agentId)}/specialists/regenerate`, { method: 'POST' },
  );
}

// ---- editing one agent's flow (REQ-SB-102) ---------------------------

/** Replaces this agent's specialist list. `depends_on` is the SHAPE of
 * the flow and lives in Hermes' registry, unlike the routing conditions
 * beside it which are this app's own annotation — so this write goes
 * through the agent's own PATCH, the same one the Agents Map uses. */
export function setSpecialists(agentId: string, dependsOn: string[]): Promise<unknown> {
  return apiFetch<unknown>(`/agents/${encodeURIComponent(agentId)}`, {
    method: 'PATCH',
    body: JSON.stringify({ depends_on: dependsOn }),
  });
}

/** Who may call one Action. Assigning an Action TO an agent is the same
 * field read from the other end, so this is the Action's own update
 * rather than a second store that could disagree with it. */
export function setAllowedCallers(actionId: string, callers: string[]): Promise<unknown> {
  return apiFetch<unknown>(`/actions/${encodeURIComponent(actionId)}`, {
    method: 'PUT',
    body: JSON.stringify({ allowed_callers: callers }),
  });
}

export interface SkillSummary { id: string; name?: string; description?: string }

export function fetchAllSkills(): Promise<SkillSummary[]> {
  return apiFetch<SkillSummary[]>('/skills');
}

export function fetchAgentSkills(agentId: string): Promise<SkillSummary[]> {
  return apiFetch<SkillSummary[]>(`/agents/${encodeURIComponent(agentId)}/skills`);
}

export function deploySkill(agentId: string, skillId: string): Promise<{ detail: string }> {
  return apiFetch<{ detail: string }>(
    `/agents/${encodeURIComponent(agentId)}/skills/${encodeURIComponent(skillId)}`,
    { method: 'POST' },
  );
}

export function undeploySkill(agentId: string, skillId: string): Promise<{ detail: string }> {
  return apiFetch<{ detail: string }>(
    `/agents/${encodeURIComponent(agentId)}/skills/${encodeURIComponent(skillId)}`,
    { method: 'DELETE' },
  );
}
