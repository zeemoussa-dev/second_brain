import { apiFetch } from '../../api/client';

export interface CockpitPersonChip {
  name: string;
  email: string | null;
  has_note: boolean;
  note_path: string | null;
}

export interface CockpitMessage {
  speaker: 'user' | 'agent';
  agent_id: string | null;
  agent_name: string | null;
  text: string;
  timestamp: string;
}

export interface CockpitThread {
  messages: CockpitMessage[];
  brought_in_agent_ids: string[];
}

export interface CockpitResearchResult {
  stem: string;
  title: string;
}

export interface CockpitPersonNoteProposal {
  id: string;
  note_path: string;
  person_name: string;
  instruction: string;
  status: 'pending' | 'confirmed' | 'discarded';
  timestamp: string;
}

export interface CockpitData {
  subject: Record<string, unknown>;
  people: CockpitPersonChip[];
  thread: CockpitThread;
  research_results: CockpitResearchResult[];
  person_note_proposals: CockpitPersonNoteProposal[];
}

export function fetchCockpit(subjectKind: string, stem: string): Promise<CockpitData> {
  return apiFetch<CockpitData>(`/cockpit/${subjectKind}/${stem}`);
}

export function bringInAgent(subjectKind: string, stem: string, agentId: string): Promise<CockpitThread> {
  return apiFetch<CockpitThread>(`/cockpit/${subjectKind}/${stem}/bring-in`, {
    method: 'POST',
    body: JSON.stringify({ agent_id: agentId }),
  });
}

export function sendCockpitMessage(
  subjectKind: string, stem: string, message: string, addressedAgentIds?: string[],
): Promise<CockpitThread> {
  return apiFetch<CockpitThread>(`/cockpit/${subjectKind}/${stem}/message`, {
    method: 'POST',
    body: JSON.stringify({
      message,
      ...(addressedAgentIds && addressedAgentIds.length > 0 ? { addressed_agent_ids: addressedAgentIds } : {}),
    }),
  });
}

export interface CockpitResearchTrigger {
  status: 'found' | 'no_results' | 'no_match';
  summary?: string;
  query?: string;
}

export function triggerCockpitResearch(
  subjectKind: string, stem: string, requestingAgentId: string, query: string,
): Promise<CockpitResearchTrigger> {
  return apiFetch<CockpitResearchTrigger>(`/cockpit/${subjectKind}/${stem}/research`, {
    method: 'POST',
    body: JSON.stringify({ requesting_agent_id: requestingAgentId, query }),
  });
}

export function saveCockpitResearch(
  subjectKind: string, stem: string, query: string, summary: string,
): Promise<{ note_path: string }> {
  return apiFetch<{ note_path: string }>(`/cockpit/${subjectKind}/${stem}/research/save`, {
    method: 'POST',
    body: JSON.stringify({ query, summary }),
  });
}

export function confirmPersonNoteProposal(
  subjectKind: string, stem: string, proposalId: string,
): Promise<CockpitPersonNoteProposal> {
  return apiFetch<CockpitPersonNoteProposal>(
    `/cockpit/${subjectKind}/${stem}/person-note-proposals/${proposalId}/confirm`,
    { method: 'POST' },
  );
}

export function discardPersonNoteProposal(
  subjectKind: string, stem: string, proposalId: string,
): Promise<CockpitPersonNoteProposal> {
  return apiFetch<CockpitPersonNoteProposal>(
    `/cockpit/${subjectKind}/${stem}/person-note-proposals/${proposalId}/discard`,
    { method: 'POST' },
  );
}

export interface CockpitAttachment {
  filename: string;
  size: number;
}

export function fetchCockpitAttachments(stem: string): Promise<CockpitAttachment[]> {
  return apiFetch<CockpitAttachment[]>(`/cockpit/email/${stem}/attachments`);
}

export function handOffAttachment(stem: string, filename: string): Promise<{ status: string; summary?: string }> {
  return apiFetch<{ status: string; summary?: string }>(`/cockpit/email/${stem}/attachments/${filename}/hand-off`, {
    method: 'POST',
  });
}
