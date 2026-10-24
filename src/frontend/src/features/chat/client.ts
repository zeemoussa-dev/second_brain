import { apiFetch } from '../../api/client';

/** A row in the chat list. Summaries only — drawing twenty rows should not
 *  cost twenty threads' worth of text. */
export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

/** What the panel needs to put a thread back on screen. `localId` is not here
 *  on purpose: it is assigned per mount and means nothing on the way back in,
 *  so the panel re-issues one for every message it loads. */
export interface StoredMessage {
  role: 'user' | 'agent';
  text: string;
  isError?: boolean;
  activity?: string[];
}

export interface Conversation extends Omit<ConversationSummary, 'message_count'> {
  messages: StoredMessage[];
}

export function listConversations(): Promise<{ conversations: ConversationSummary[] }> {
  return apiFetch<{ conversations: ConversationSummary[] }>('/chats');
}

export function createConversation(): Promise<ConversationSummary> {
  return apiFetch<ConversationSummary>('/chats', { method: 'POST' });
}

export function readConversation(id: string): Promise<Conversation> {
  return apiFetch<Conversation>(`/chats/${encodeURIComponent(id)}`);
}

/** The whole thread, as the page now has it. A replace rather than an append
 *  because a streamed reply is edited in place as it arrives — "append this
 *  message" would need the client to track which of its own bubbles had
 *  already been sent and which had changed since. */
export function saveMessages(id: string, messages: StoredMessage[]): Promise<ConversationSummary> {
  return apiFetch<ConversationSummary>(`/chats/${encodeURIComponent(id)}/messages`, {
    method: 'PUT',
    body: JSON.stringify({ messages }),
  });
}

export function deleteConversation(id: string): Promise<{ deleted: boolean }> {
  return apiFetch<{ deleted: boolean }>(`/chats/${encodeURIComponent(id)}`, { method: 'DELETE' });
}
