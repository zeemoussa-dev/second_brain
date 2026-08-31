import { apiFetch } from '../../api/client';

export interface CockpitPersonChip {
  name: string;
  email: string | null;
  has_note: boolean;
  note_path: string | null;
}

export interface CockpitDocument {
  title: string;
  filename: string | null;
  note_path: string;
}

export interface CockpitOverview {
  // null = no prep pass has run yet for this meeting/email (Research
  // Expert isn't wired up yet -- see BUG-037's own follow-up discussion).
  // The frontend renders this as an honest "not prepped yet" state, never
  // a fabricated summary.
  summary: string | null;
  related_documents: CockpitDocument[];
  articles: { title: string; url: string }[];
}

export interface CockpitChatMessage {
  // 'system' (REQ-SB-82-US-04, Scenario 6) -- an honest "bring someone in
  // first" notice, never a fabricated Expert/user reply. Pre-US-04
  // messages carry neither `id` nor `reply_to_message_id`.
  speaker: 'user' | 'agent' | 'system';
  agent_id: string | null;
  agent_name: string | null;
  text: string;
  id?: string;
  reply_to_message_id?: string | null;
}

export interface CockpitThread {
  messages: CockpitChatMessage[];
  brought_in_agent_ids: string[];
  // Moderator-recommended roster (REQ-SB-82-US-03, ADR-009) -- an
  // additive, non-authoritative hint list; never restricts manual
  // bring-in. Computed/cached server-side, honest-empty [] when neither
  // match track finds a real match.
  recommended_agent_ids: string[];
}

export interface CockpitData {
  subject: Record<string, unknown>;
  people: CockpitPersonChip[];
  overview: CockpitOverview;
  thread: CockpitThread;
}

export function fetchCockpit(subjectKind: string, stem: string): Promise<CockpitData> {
  return apiFetch<CockpitData>(`/cockpit/${subjectKind}/${stem}`);
}

// Persists a brought-in Expert onto this subject's real, per-subject
// roster (REQ-SB-82-US-01, ADR-007) -- survives reload/navigation.
export function bringInAgent(subjectKind: string, stem: string, agentId: string): Promise<CockpitThread> {
  return apiFetch<CockpitThread>(`/cockpit/${subjectKind}/${stem}/roster`, {
    method: 'POST',
    body: JSON.stringify({ agent_id: agentId }),
  });
}

export function removeAgent(subjectKind: string, stem: string, agentId: string): Promise<CockpitThread> {
  return apiFetch<CockpitThread>(`/cockpit/${subjectKind}/${stem}/roster/${agentId}`, {
    method: 'DELETE',
  });
}

export interface SendMessageResult {
  thread: CockpitThread;
  // Who the message was routed to (or null for the honest no-Experts-
  // brought-in case, Scenario 6) -- the reply itself is dispatched in the
  // BACKGROUND and hasn't landed yet when this resolves, so the caller
  // shows this as an "X is typing..." indicator and polls for the reply.
  answering: { agent_id: string; agent_name: string } | null;
}

// Routes the message to the ONE brought-in Expert it belongs to (an
// explicit leading @mention always overrides the routing decision), or
// the Research Agent on no match/a tie -- REQ-SB-82-US-04. Returns fast,
// before the routed reply itself is ready.
// `replyToMessageId` (REQ-SB-82-US-06-T07) is a strong hint into the
// moderator's routing reasoning, never a hard override (ADR-012 point 4)
// -- omitted from the request body entirely when not provided, matching
// `T06`'s own optional-field passthrough on the router side.
export function sendMessage(
  subjectKind: string,
  stem: string,
  text: string,
  replyToMessageId?: string,
): Promise<SendMessageResult> {
  return apiFetch<SendMessageResult>(`/cockpit/${subjectKind}/${stem}/message`, {
    method: 'POST',
    body: JSON.stringify(replyToMessageId ? { text, reply_to_message_id: replyToMessageId } : { text }),
  });
}

// Uploads a file/screenshot during a live meeting, stored attached to it
// (REQ-... operator, 2026-08-27) -- lands under the subject's own real
// folder via vault_manager's `file` Template, same shape `capture-files`
// already uses. Returns the real thread with a system confirmation
// message already appended, so the caller can render it immediately.
export function uploadDocument(subjectKind: string, stem: string, file: File): Promise<{ filename: string; note_path: string; size: number }> {
  const formData = new FormData();
  formData.append('file', file);
  return apiFetch(`/cockpit/${subjectKind}/${stem}/documents`, {
    method: 'POST',
    body: formData,
  });
}

// Appends a timestamped line to the Person note's own "## Personal
// Notes" section (creates the section on first use) -- operator,
// 2026-08-25: "Notes about the person during the meeting, saved to
// their note." Scoped to Person notes only; general note editing
// doesn't exist anywhere else in the app yet.
export function addPersonNote(stem: string, text: string): Promise<{ line: string }> {
  return apiFetch<{ line: string }>(`/cockpit/person/${stem}/notes`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
}
