import { apiFetch, ApiError } from '../../api/client';

export interface AgentSummary {
  id: string;
  name: string;
  type: 'worker' | 'producer' | 'expert';
  section_id: string;
  is_background_agent: boolean;
  icon: string | null;
  color: string | null;
  // First settings entry's own value (main.py's own `_agent_summary()`) —
  // null when an agent has no settings at all. Powers the Agents Map's
  // own hover card (operator, 2026-08-16: "a Description of that Agent
  // if Exist"); not shown anywhere else today.
  description: string | null;
  working_mode: 'autonomous' | 'supervised' | 'manual';
  // LangGraph-style connection data (operator, 2026-08-15: "The Data
  // About the Agent should have who is connected to who in order to
  // have a tree, Check Langraph Data... so we can start having a tree
  // view") — typed here so it's available end-to-end, but not yet READ
  // anywhere (no tree-layout/rendering work has started — this pass
  // was scoped to the data itself, per the operator's own "start
  // having" framing). `depends_on` = ids of Agents this one
  // structurally receives from (a pipeline predecessor); empty means
  // either a pipeline's own entry point or a standalone Agent with no
  // pipeline at all. `branch_target_agent_id` = the one Expert Agent
  // id a "Consult Expert"-style stage additively branches out to —
  // distinct from depends_on, a consultation, not a structural edge.
  depends_on: string[];
  branch_target_agent_id: string | null;
}

export function fetchAgentList(): Promise<AgentSummary[]> {
  return apiFetch<AgentSummary[]>('/agents');
}

export interface AgentCapability {
  id: string;
  label: string;
  kind: 'action' | 'skill';
  tool?: string;
}

export interface AgentDetail {
  id: string;
  name: string;
  type: 'worker' | 'producer' | 'expert';
  settings: { key: string; value: string }[];
  capabilities: AgentCapability[];
  section_id: string;
  section_name: string;
  provider_id: string;
  provider_name: string;
  provider_available: boolean;
  keywords: string[];
  working_mode: 'autonomous' | 'supervised' | 'manual';
  scope: string[];
  is_background_agent: boolean;
  icon: string | null;
  color: string | null;
  // REQ-SB-66-US-01-T04's own stored-value-only convention -- the resolved
  // effective default text (when unset) is a runtime call-site concern
  // (T02/T03), never returned here.
  prompt: string | null;
  guardrails: string;
}

export function fetchAgent(agentId: string): Promise<AgentDetail> {
  return apiFetch<AgentDetail>(`/agents/${agentId}`);
}

export function updateAgentAssignment(
  agentId: string,
  body: {
    section_id?: string;
    provider_id?: string;
    keywords?: string[];
    working_mode?: string;
    scope?: string[];
    is_background_agent?: boolean;
    // "" clears the override back to the default (backend's own
    // omitted-vs-empty-string convention, agent_visual_registry.py).
    icon?: string;
    color?: string;
    prompt?: string;
    guardrails?: string;
  },
): Promise<AgentDetail> {
  return apiFetch<AgentDetail>(`/agents/${agentId}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

export function isBackgroundAgent(agent: { is_background_agent: boolean }): boolean {
  return agent.is_background_agent;
}

export interface TriggerActionResult {
  status: 'ok' | 'error';
  message: string;
}

export function triggerAgentAction(agentId: string, actionId: string): Promise<TriggerActionResult> {
  return apiFetch<TriggerActionResult>(`/agents/${agentId}/actions/${actionId}`, { method: 'POST' });
}

export interface ChatResponse {
  reply: string;
  action_triggered: string | null;
}

export function sendChatMessage(agentId: string, message: string): Promise<ChatResponse> {
  return apiFetch<ChatResponse>(`/agents/${agentId}/chat`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

export interface ChatAttachmentResponse {
  reply: string;
  attachment_status:
    | 'filed'
    | 'summarized_unfiled'
    | 'rejected'
    | 'extraction_failed'
    | 'summarization_failed';
  vault_path: string | null;
}

// apiFetch (client.ts) hardcodes 'Content-Type: application/json'
// unconditionally, which would break multipart boundary handling --
// this call intentionally uses a raw fetch instead, duplicating
// client.ts's own BASE_URL fallback (client.ts is out of this task's
// Files to Modify; BASE_URL is not exported from it).
const ATTACHMENT_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

export async function sendChatMessageWithAttachment(
  agentId: string,
  message: string,
  file: File,
): Promise<ChatAttachmentResponse> {
  const formData = new FormData();
  formData.append('message', message);
  formData.append('file', file);
  const response = await fetch(`${ATTACHMENT_BASE_URL}/agents/${agentId}/chat/attachment`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }
  return response.json() as Promise<ChatAttachmentResponse>;
}

export interface AgentHistoryEntry {
  kind: 'chat_user' | 'chat_agent' | 'run_event' | 'proposal';
  text: string;
  timestamp: string;
  pending_approval_id?: string;
}

export function fetchAgentHistory(agentId: string): Promise<AgentHistoryEntry[]> {
  return apiFetch<AgentHistoryEntry[]>(`/agents/${agentId}/history`);
}

// REQ-SB-65-US-01-T01's own real Job-tree sub-resource shape
// (agents_router.py::get_jobs) -- `[]` for every real agent OTHER than
// `email-capture-pipeline` (never a 404, never fabricated); a real,
// freshly-introspected 6-entry tree for that one pipeline id.
export interface JobTreeEntry {
  id: string;
  name: string;
  depends_on: string[];
  section_id: string | null;
}

export function fetchAgentJobs(agentId: string): Promise<JobTreeEntry[]> {
  return apiFetch<JobTreeEntry[]>(`/agents/${agentId}/jobs`);
}

// T06's own GET/PATCH /agents/{agent_id}/jobs/{job_id}/settings response
// shape (ADR-044 Decision 2) -- `prompt` is genuinely OMITTED (key absent,
// never `null`) for a Job with no real runtime call site of its own
// (`thread_match_merge`/`detect_recurring_pattern`), never present-but-inert.
// Optional here so JobSettingsPanel.tsx's own key-presence check
// (`'prompt' in settings`) reflects the real backend contract instead of
// collapsing "absent" and "null" the way a plain `string | null` would.
export interface JobSettings {
  id: string;
  name: string;
  prompt?: string | null;
  guardrails: string;
}

export function fetchJobSettings(agentId: string, jobId: string): Promise<JobSettings> {
  return apiFetch<JobSettings>(`/agents/${agentId}/jobs/${jobId}/settings`);
}

export function updateJobSettings(
  agentId: string,
  jobId: string,
  body: { prompt?: string; guardrails?: string },
): Promise<JobSettings> {
  return apiFetch<JobSettings>(`/agents/${agentId}/jobs/${jobId}/settings`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

export interface KnowledgeGap {
  id: string;
  agent_id: string;
  question: string;
  topic: string;
  status: 'open' | 'closed';
  created_at: string;
  closed_at: string | null;
  resolution: 'human_provided' | 'research' | null;
}

export interface KnowledgeGapsResponse {
  gaps: KnowledgeGap[];
  open_count: number;
}

export function fetchAgentKnowledgeGaps(agentId: string): Promise<KnowledgeGapsResponse> {
  return apiFetch<KnowledgeGapsResponse>(`/agents/${agentId}/knowledge-gaps`);
}

export function resolveKnowledgeGap(agentId: string, gapId: string, answer: string): Promise<{ gap: KnowledgeGap; filing_result: Record<string, unknown> }> {
  return apiFetch(`/agents/${agentId}/knowledge-gaps/${gapId}/resolve`, {
    method: 'POST',
    body: JSON.stringify({ answer }),
  });
}

export function researchKnowledgeGap(agentId: string, gapId: string): Promise<{ gap: KnowledgeGap; research_result: Record<string, unknown>; message: string }> {
  return apiFetch(`/agents/${agentId}/knowledge-gaps/${gapId}/research`, { method: 'POST' });
}

export interface CreateAgentBody {
  name: string;
  type: 'worker' | 'expert' | 'producer';
  domain?: string;
  purpose?: string;
  trigger?: string;
}

export function createAgent(body: CreateAgentBody): Promise<AgentDetail> {
  return apiFetch<AgentDetail>('/agents', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}
