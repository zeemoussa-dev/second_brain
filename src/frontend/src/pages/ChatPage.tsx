import { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router';
import { AgentChatPanel } from '../features/chat/AgentChatPanel';
import {
  createConversation,
  deleteConversation,
  listConversations,
  readConversation,
  saveMessages,
  type ConversationSummary,
  type StoredMessage,
} from '../features/chat/client';

// New top-level Chat surface (2026-08-24, operator: "move the Primary
// Chat to be Background Agent, Create a new Tab we call Chat where we
// can Chat with this Agent Since it Talks to everything") -- Primary is
// now excluded from the Agents Map ring (agents_map_adapter.py's own
// `_BACKGROUND_AGENTS`), so this page is its real, primary way to be
// reached, not a second path alongside a map entry. "default" is
// Primary's own real agent id (hermes_definitions.py's own
// PRIMARY_PROFILE_ID convention), matching every other real call site
// in this codebase that addresses Primary directly.
//
// Conversations (2026-10-24, operator: "Introduce Multiple Chats, An Option to
// delete a Chat"). The thread used to live in the panel's own state: a reload
// lost it, and there was only ever one, so two subjects shared a thread or one
// of them was abandoned. Which conversation is open lives in the URL, so Back
// moves between them and a chat can be linked to.
export function ChatPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const openId = searchParams.get('c');

  const [conversations, setConversations] = useState<ConversationSummary[] | null>(null);
  const [messages, setMessages] = useState<StoredMessage[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState<string | null>(null);
  // What was last written, so an unchanged thread is not saved again on every
  // render the panel happens to cause.
  const lastSaved = useRef<string>('');
  // Which conversation's messages this page actually READ. Saving is gated on
  // it: a page that never loaded a thread has no business writing one.
  const loadedFor = useRef<string | null>(null);

  const refreshList = useCallback(async () => {
    const answered = await listConversations();
    setConversations(answered.conversations);
    return answered.conversations;
  }, []);

  function open(id: string | null) {
    const next = new URLSearchParams(searchParams);
    if (id) next.set('c', id);
    else next.delete('c');
    // A push, not a replace: moving between conversations is a journey, and
    // Back should return to the one you were reading.
    setSearchParams(next);
  }

  useEffect(() => {
    void refreshList().catch(() => setConversations([]));
  }, [refreshList]);

  // Load whichever conversation the URL names. A conversation deleted in
  // another tab answers 404; that is not an error worth a banner, it just
  // means there is nothing open.
  useEffect(() => {
    if (!openId) {
      setMessages(null);
      lastSaved.current = '';
      return;
    }
    let current = true;
    setMessages(null);
    setLoadError(null);
    loadedFor.current = null;
    readConversation(openId)
      .then((conversation) => {
        if (!current) return;
        setMessages(conversation.messages);
        lastSaved.current = JSON.stringify(conversation.messages);
        // Saving is enabled ONLY by a load that worked. Without this the panel
        // mounts on a failed load holding nothing, reports that empty thread,
        // and the page writes it over the stored conversation -- which emptied
        // two real threads during a backend restart on 2026-10-24.
        loadedFor.current = openId;
      })
      .catch(() => {
        if (!current) return;
        // Deliberately NOT `setMessages([])`: an empty thread and a thread we
        // could not read are different things, and only one of them is safe to
        // put a composer in front of.
        setLoadError('That conversation could not be opened. Reload the page to try again.');
      });
    return () => {
      current = false;
    };
  }, [openId]);

  async function startNewChat() {
    const created = await createConversation();
    await refreshList();
    open(created.id);
  }

  async function removeChat(id: string) {
    await deleteConversation(id);
    setConfirmingDelete(null);
    const remaining = await refreshList();
    // Only move if the one being read is the one that went: deleting an older
    // chat should not throw you out of the one you are in.
    if (id === openId) open(remaining.length > 0 ? remaining[0].id : null);
  }

  /** Persists the thread the panel is holding. */
  const handleThreadChanged = useCallback(
    (thread: { role: 'user' | 'agent'; text: string; isError?: boolean; activity?: string[] }[]) => {
      // Only for the conversation this page read, and only once it has read
      // it. Anything else is the page writing a thread it does not have.
      if (!openId || loadedFor.current !== openId) return;
      const storable: StoredMessage[] = thread.map(({ role, text, isError, activity }) => ({
        role,
        text,
        ...(isError ? { isError } : {}),
        ...(activity && activity.length > 0 ? { activity } : {}),
      }));
      const serialised = JSON.stringify(storable);
      if (serialised === lastSaved.current) return;
      lastSaved.current = serialised;
      void saveMessages(openId, storable)
        // The list carries the title and the order, and the first message of a
        // new chat sets both.
        .then(() => refreshList())
        .catch(() => setLoadError('That message could not be saved.'));
    },
    [openId, refreshList],
  );

  return (
    <div className="chat-page">
      <h1>Chat</h1>
      <p className="text-muted">
        Talk to Primary directly — the one agent that can see and act across everything, not
        just one narrow domain.
      </p>

      <div className="chat-layout">
        <aside className="chat-list" aria-label="Your chats">
          <button type="button" className="btn btn-primary chat-new" onClick={() => void startNewChat()}>
            <span className="material-symbols-outlined" aria-hidden="true">
              add
            </span>
            New chat
          </button>

          {conversations === null ? (
            <p className="text-muted chat-list-note">Loading…</p>
          ) : conversations.length === 0 ? (
            <p className="text-muted chat-list-note">
              No chats yet. Start one and it is kept here.
            </p>
          ) : (
            conversations.map((conversation) => (
              <div
                key={conversation.id}
                className={`chat-list-row ${conversation.id === openId ? 'is-open' : ''}`}
              >
                <button
                  type="button"
                  className="chat-list-open"
                  onClick={() => open(conversation.id)}
                  title={conversation.title}
                >
                  <span className="chat-list-title">{conversation.title}</span>
                  <span className="chat-list-meta">
                    {conversation.message_count} message{conversation.message_count === 1 ? '' : 's'}
                  </span>
                </button>
                {/* Confirmed in place rather than through a dialog: the row
                    itself asks, so the thing being deleted stays on screen
                    while you decide which one it was. */}
                {confirmingDelete === conversation.id ? (
                  <span className="chat-list-confirm">
                    <button
                      type="button"
                      className="btn btn-compact btn-danger"
                      onClick={() => void removeChat(conversation.id)}
                    >
                      Delete
                    </button>
                    <button
                      type="button"
                      className="btn btn-compact"
                      onClick={() => setConfirmingDelete(null)}
                    >
                      Keep
                    </button>
                  </span>
                ) : (
                  <button
                    type="button"
                    className="chat-list-delete"
                    aria-label={`Delete ${conversation.title}`}
                    onClick={() => setConfirmingDelete(conversation.id)}
                  >
                    <span className="material-symbols-outlined" aria-hidden="true">
                      delete
                    </span>
                  </button>
                )}
              </div>
            ))
          )}
        </aside>

        <div className="chat-page-panel">
          {!openId ? (
            <div className="empty-state">
              <span className="material-symbols-outlined empty-state-icon" aria-hidden="true">
                forum
              </span>
              <p className="empty-state-title">Pick a chat, or start one</p>
              <p style={{ margin: 'var(--space-1) 0 0' }}>
                Each chat keeps its own thread, so a question about a customer and a question
                about your week do not end up in the same conversation.
              </p>
            </div>
          ) : loadError ? (
            // No composer on a thread we could not read: typing into it would
            // be typing into nothing, and sending would save that nothing over
            // whatever is really stored.
            <div className="empty-state">
              <span className="material-symbols-outlined empty-state-icon" aria-hidden="true">
                error
              </span>
              <p className="empty-state-title">{loadError}</p>
            </div>
          ) : messages === null ? (
            <p className="text-muted">Opening…</p>
          ) : (
            <>
              <AgentChatPanel
                // Keyed, so switching conversations builds a fresh panel
                // rather than letting one thread's draft and reply-to
                // selection survive into another.
                key={openId}
                agentId="default"
                agentName="Primary"
                conversationId={openId}
                initialMessages={messages.map((message, index) => ({
                  ...message,
                  localId: `stored-${index}`,
                }))}
                onThreadChanged={handleThreadChanged}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
