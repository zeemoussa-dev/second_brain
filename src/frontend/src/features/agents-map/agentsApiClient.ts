import { apiFetch, ApiError, API_BASE_URL } from '../../api/client';
// The Hermes cron job shape is already declared once, for the Hermes Ops
// screen, off the same backend dataclass -- the profile debug view extends it
// rather than declaring a second copy to drift (REQ-SB-99-US-01, ESC-066).
import type { HermesCronJob } from '../hermes-ops/client';

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
  // 2026-08-22 -- a genuinely SHORT excerpt (the real first sentence,
  // never fabricated) of `prompt` below, distinct from it -- the hover
  // card on the map uses AgentSummary's own copy of this same field;
  // Overview shows it here as its own row, separate from the full prompt.
  description: string | null;
  // REQ-SB-66-US-01-T04's own stored-value-only convention -- the resolved
  // effective default text (when unset) is a runtime call-site concern
  // (T02/T03), never returned here.
  prompt: string | null;
  guardrails: string;
  // 2026-08-29 -- real, currently-ENABLED Hermes toolset names for this
  // profile (e.g. "terminal", "file"). A full REPLACE list on write, not
  // an additive patch.
  tools: string[];
  // 2026-08-29 -- who this agent relays UP to (real specialists-relay
  // direction, confirmed live: a child's own depends_on points at its
  // parent, e.g. energy-expert.depends_on == ["industry-expert"]) --
  // NOT the older LangGraph-era pipeline-predecessor meaning
  // AgentSummary's own same-named field still documents; that one is a
  // separate, still-unbuilt concept.
  depends_on: string[];
  // 2026-08-29 -- real Index ids (business/core/index/) this agent
  // should consult first when looking for data in the vault.
  preferred_index_ids: string[];
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
    tools?: string[];
    depends_on?: string[];
    preferred_index_ids?: string[];
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

// One real SSE frame from POST .../chat/stream (agents_router.py's own
// `_stream_reply`) -- 'activity' is a real thinking/status signal
// (distinct from the actual reply), 'delta' is one streamed reply
// chunk, 'complete' carries the FULL final reply (not just the last
// chunk), 'error' ends the stream early.
export type ChatStreamEvent =
  | { type: 'activity'; text: string }
  | { type: 'delta'; text: string }
  | { type: 'complete'; text: string }
  /** The agent is blocked, waiting to be allowed to do something. The
   *  turn has NOT ended — Hermes holds it open until `approval.respond`
   *  answers this `request_id`, which is why typing a reply could never
   *  work: a new prompt is not what it is waiting for. */
  | { type: 'approval'; text: string; request_id: string; command: string }
  | { type: 'error'; detail: string };

// Raw `fetch`, not apiFetch (2026-08-24) -- apiFetch always awaits and
// parses one whole JSON body; this reads the response as a live byte
// stream instead. Reuses ATTACHMENT_BASE_URL (below) rather than a
// second identically-valued constant -- both are "real fetch, not
// apiFetch's one-shot-JSON contract" call sites for the same reason.
export async function streamChatMessage(
  agentId: string,
  message: string,
  onEvent: (event: ChatStreamEvent) => void,
  signal?: AbortSignal,
  /** The stored conversation this turn belongs to, so the BACKEND saves
   *  it when the reply lands rather than relying on this page still
   *  being mounted to hear it. Omitted by callers with no stored
   *  conversation (Cockpit, the agent side panels), and the backend
   *  then saves nothing. */
  conversationId?: string,
): Promise<void> {
  const response = await fetch(`${ATTACHMENT_BASE_URL}/agents/${agentId}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      ...(conversationId ? { conversation_id: conversationId } : {}),
    }),
    signal,
    // The session is an httponly cookie on a different origin (:8001 against
    // this :5173), so `fetch` omits it unless asked. `apiFetch` sets this once
    // for everything that goes through it; a raw fetch has to say it itself,
    // and this one did not -- so every chat message since sign-in landed was
    // sent anonymously and answered 401, which the panel showed as "Something
    // went wrong sending that message" (operator hit it, 2026-10-24).
    credentials: 'include',
  });
  if (!response.ok || !response.body) {
    throw new ApiError(response.status, await response.text());
  }
  await readStreamInto(response, onEvent);
}

/** Reads one SSE response into `onEvent`. Shared by the message stream
 *  and the approval stream: two copies of the frame-splitting would be
 *  two places for a half-arrived frame to be handled differently. */
async function readStreamInto(
  response: Response,
  onEvent: (event: ChatStreamEvent) => void,
): Promise<void> {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    // SSE frames are separated by a blank line; a frame can arrive
    // split across multiple stream chunks, so only fully-terminated
    // frames (buffer holds a real "\n\n") are ever parsed out here —
    // the remainder waits in `buffer` for the rest to arrive.
    let separatorIndex: number;
    while ((separatorIndex = buffer.indexOf('\n\n')) !== -1) {
      const rawFrame = buffer.slice(0, separatorIndex);
      buffer = buffer.slice(separatorIndex + 2);
      const dataLine = rawFrame.split('\n').find((line) => line.startsWith('data: '));
      if (!dataLine) continue;
      try {
        onEvent(JSON.parse(dataLine.slice('data: '.length)) as ChatStreamEvent);
      } catch {
        // A malformed frame is skipped, not fatal to the whole stream --
        // matches this app's own "surface what's real, don't crash the
        // thread over one bad chunk" posture elsewhere in chat handling.
      }
    }
  }
}

// 2026-08-24 -- pairs with the backend's own new session-continuity fix
// (chat_sessions.py): a chat turn now reuses the same live Hermes
// session across messages instead of starting fresh every time, so
// there needs to be a real way to deliberately end a conversation too.
export function resetChatSession(agentId: string): Promise<{ reset: boolean }> {
  return apiFetch<{ reset: boolean }>(`/agents/${agentId}/chat/reset`, { method: 'POST' });
}

export interface ChatAttachmentResponse {
  reply: string;
  // 'sent_to_agent': saved to the install and handed to the agent with the
  // message; 'rejected': not sent (empty, too large, unsaveable), and `reply`
  // says why.
  attachment_status: 'sent_to_agent' | 'rejected';
  vault_path: string | null;
}

// apiFetch (client.ts) hardcodes 'Content-Type: application/json'
// unconditionally, which would break multipart boundary handling --
// this call intentionally uses a raw fetch instead, duplicating
// client.ts's own BASE_URL fallback (client.ts is out of this task's
// Files to Modify; BASE_URL is not exported from it).
// Shares api/client.ts's corrected origin: a loopback spelling that differs
// from the page's is rewritten there, and re-reading the env var here would
// reintroduce the cookie mismatch on this path (REQ-SB-101).
const ATTACHMENT_BASE_URL = API_BASE_URL;

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
    credentials: 'include',
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
  // 2026-08-22 -- per-Step type ('worker' by default, 'producer' for a
  // pipeline's own real entry point that pulls raw data from an external
  // source like Outlook). Optional so a Job source that predates this
  // field degrades to the parent Pipeline's own type at the splice site.
  type?: 'worker' | 'producer' | 'expert';
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

// Matches AgentCreateBody (agents_router.py) field-for-field -- the
// previous shape here (name/type/domain/purpose/trigger) never lined up
// with the real backend model (id/section_id required and absent;
// domain/purpose/trigger not real fields at all), so every submission
// 422'd before AgentManager.create() ever ran. Rebuilt 2026-08-30
// alongside the Create Agent wizard rebuild.
export interface CreateAgentBody {
  id: string;
  name: string;
  section_id: string;
  type: 'worker' | 'expert' | 'producer' | 'hub';
  is_background_agent?: boolean;
  depends_on?: string[];
  description?: string;
  prompt?: string;
  guardrails?: string;
  scope?: string[];
  preferred_index_ids?: string[];
  tools?: string[];
  clone_from?: string;
}

export function createAgent(body: CreateAgentBody): Promise<AgentDetail> {
  return apiFetch<AgentDetail>('/agents', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

// ---------------------------------------------------------------------------
// GET /hermes/agents/{id}/profile-detail (REQ-SB-99-US-01, ADR-043) -- what one
// Hermes profile really is on disk right now, in one deliberately-expensive
// read-only call. Only HermesProfileDetailPage asks for it; nothing on a
// listing path does, and nothing on the agent panel's mount does (BUG-086).
//
// Every region below carries its OWN `read` flag and its OWN `error`, and an
// unread region's payload is `null` -- never `[]`, `{}` or `''`, which are what
// a region that WAS read and genuinely holds nothing returns. The types keep
// that distinction (`| null` on every payload) because collapsing it on this
// side would re-introduce exactly the dishonesty the endpoint was built to end
// (BUG-085/BUG-088): a region that could not be read must never render as a
// region holding nothing.
// ---------------------------------------------------------------------------

/** How one config key relates to the two layers, as `profile_detail.py` reports
 *  it. `profile`/`install_root` are the layers' own names; the other three are
 *  the view's. Deliberately NOT narrowed to a closed union: an answer this
 *  frontend has not heard of must render as itself, never be silently dropped. */
export type HermesConfigKeySource = string;

export interface HermesProfileSoulRegion {
  read: boolean;
  /** The file it came from, or would have come from. */
  path: string | null;
  /** `read` | `absent` | `unreadable` | `not_read`. */
  status: string;
  /** The SOUL.md verbatim. `null` means no read succeeded; `''` means the file
   *  really is empty, which is a different, equally honest answer. */
  text: string | null;
  error: string;
}

export interface HermesProfileSkillRow {
  /** `<category>/<slug>` as it sits in the profile's own skills/ tree. */
  skill_id: string;
  slug: string;
  deployed_version: string | null;
  /** `null` when the framework catalog has no such skill at all. */
  catalog_version: string | null;
  /** `current` | `stale` | `modified` | `missing` | `unknown_to_framework`. */
  status: string;
}

export interface HermesProfileSkillsRegion {
  read: boolean;
  items: HermesProfileSkillRow[] | null;
  error: string;
}

export interface HermesProfileConfigLayer {
  /** `profile` or `install_root` -- never a merged third value. */
  source: string;
  path: string;
  status: string;
  /** This one file's own mapping, as written. `null` when it could not be read. */
  values: Record<string, unknown> | null;
  error: string;
}

/** One layer that really sets this key, with the file it was read from. A key
 *  set in both layers carries two of these and NO single value: Hermes' own
 *  precedence between the files is not readable from this repository, so there
 *  is no effective value to show (ADR-043). */
export interface HermesProfileConfigOccurrence {
  source: string;
  path: string;
  value: unknown;
}

export interface HermesProfileConfigKey {
  key: string;
  /** Only set when exactly one layer sets this key -- `null` otherwise. */
  value: unknown;
  source: HermesConfigKeySource;
  path: string | null;
  occurrences: HermesProfileConfigOccurrence[];
}

export interface HermesProfileConfigRegion {
  read: boolean;
  layers: HermesProfileConfigLayer[] | null;
  keys: HermesProfileConfigKey[] | null;
  error: string;
}

/** A Hermes cron job as `cron_status.list_cron_jobs()` serves it -- the same
 *  dataclass the Hermes Ops screen already renders, plus the `scope` label
 *  saying which directory's jobs.json it came from (a job's profile binding is
 *  a directory, not a field). Extended rather than re-declared so there is one
 *  shape for one fact. */
export interface HermesProfileCronJob extends HermesCronJob {
  scope: 'install' | 'profile';
}

export interface HermesProfileCronRegion {
  read: boolean;
  /** Exactly the jobs in this profile's own cron/ directory. */
  items: HermesProfileCronJob[] | null;
  /** The install-root jobs -- the ones that run with no `-p`. Kept separate so
   *  a job is never attributed to a profile that does not own it. */
  install_level: HermesProfileCronJob[] | null;
  /** True for the primary profile, which IS <HERMES_HOME>: its own cron
   *  directory and the install's are the same one, so `install_level` is empty
   *  by construction rather than because the install has no jobs. */
  install_level_is_this_profile: boolean | null;
  error: string;
}

export interface HermesProfileToolsetsRegion {
  read: boolean;
  /** `{toolset: enabled}`. `null` on a failed read -- never `{}`, which is the
   *  real answer "the read worked and nothing is enabled". */
  items: Record<string, boolean> | null;
  error: string;
}

export interface HermesProfileDetail {
  profile_id: string;
  /** `readable: false` means <HERMES_HOME> itself is absent or is not a
   *  directory. Every region is then unread, and none may be rendered. */
  install: { readable: boolean; path: string; error: string };
  soul: HermesProfileSoulRegion;
  skills: HermesProfileSkillsRegion;
  config: HermesProfileConfigRegion;
  cron_jobs: HermesProfileCronRegion;
  toolsets: HermesProfileToolsetsRegion;
}

export function fetchHermesProfileDetail(agentId: string): Promise<HermesProfileDetail> {
  return apiFetch<HermesProfileDetail>(`/hermes/agents/${agentId}/profile-detail`);
}

/** Answer the approval an agent's chat session is blocked on, and read
 *  the rest of that turn as it continues.
 *
 *  `always` is Hermes' own `all` flag — approve this and everything
 *  like it for the rest of the session. That is what "always approve"
 *  means and it is not something a typed reply can express, which is
 *  why typing one did nothing (operator, 2026-10-24).
 *
 *  No `request_id` is sent: the backend knows which request this
 *  agent's session is waiting on, and accepting one here would let a
 *  caller answer an approval it never saw. */
export async function answerChatApproval(
  agentId: string,
  choice: 'approve' | 'deny',
  always: boolean,
  onEvent: (event: ChatStreamEvent) => void,
  conversationId?: string,
): Promise<void> {
  const response = await fetch(`${ATTACHMENT_BASE_URL}/agents/${agentId}/chat/approval`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      choice,
      always,
      ...(conversationId ? { conversation_id: conversationId } : {}),
    }),
    credentials: 'include',
  });
  if (!response.ok || !response.body) {
    throw new ApiError(response.status, await response.text());
  }
  await readStreamInto(response, onEvent);
}
