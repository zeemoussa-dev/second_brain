import { useEffect, useRef, useState, type ChangeEvent, type FormEvent, type KeyboardEvent } from 'react';
import { fetchAgentList, isBackgroundAgent, type AgentSummary } from '../agents-map/agentsApiClient';
import { getVisualIconName } from '../agents-map/visualOptions';
import {
  bringInAgent, fetchCockpit, removeAgent, sendMessage, uploadDocument,
  type CockpitChatMessage, type CockpitData, type CockpitDocument,
} from './cockpitApiClient';
import { PersonNotePanel } from './PersonNotePanel';
import { ChatMessageText } from '../../components/ChatMessageText';

// Same auto-grow ceiling as the established multiline chat input
// (AgentChatPanel.tsx, operator: "need to grow bigger to show at least 3
// to 5 lines") -- reused verbatim so both chat surfaces behave the same.
const _CHAT_INPUT_MAX_HEIGHT_PX = 132;

// How long to keep polling for a dispatched reply -- EVERY reply (a
// routed Expert or the Research Agent fallback) is dispatched in the
// background now (REQ-SB-82-US-04), so this governs all of them, not just
// research. Window (5s x 72 = 360s) matches chat_sessions.py's own
// _CHAT_TURN_TIMEOUT_S -- found live that a real web-research turn
// (actual tool calls, not a canned reply) routinely runs multiple
// minutes, well past an initially-assumed 60s window.
const _REPLY_POLL_INTERVAL_MS = 5000;
const _REPLY_POLL_MAX_ATTEMPTS = 72;

// Same "truncated quote" convention AgentChatPanel.tsx's own reply-to
// preview (REQ-SB-82-US-06-T08, already Done) uses for its own,
// independently-built mechanism -- same user-facing verb/shape per
// ADR-012 points 4/5, not a shared component.
const _REPLY_PREVIEW_MAX_CHARS = 140;

interface PendingAnswer {
  messageId: string;
  agentId: string;
  agentName: string;
}

type CockpitTab = 'overview' | 'chat' | 'people' | 'documents' | 'articles';

const NAV_ITEMS: { tab: CockpitTab; icon: string; label: string }[] = [
  { tab: 'overview', icon: '▦', label: 'Overview' },
  { tab: 'chat', icon: '\u{1F4AC}', label: 'Chat' },
  { tab: 'people', icon: '\u{1F465}', label: 'People' },
  { tab: 'documents', icon: '\u{1F4C4}', label: 'Documents' },
  { tab: 'articles', icon: '\u{1F4F0}', label: 'Articles' },
];

interface CockpitProps {
  subjectKind: 'meeting' | 'email';
  subjectNoteStem: string;
  // e.g. [{label:'Time',key:'start'}] -- rendered in the right rail's
  // Meeting/Email info panel on every tab except Chat.
  infoFields: { label: string; key: string }[];
}

function PersonChip({ person, onOpen }: { person: CockpitData['people'][number]; onOpen: (stem: string) => void }) {
  if (!person.has_note) {
    return <span className="tag-chip--static" key={person.email}>{person.name} <span className="text-muted">(no note yet)</span></span>;
  }
  const stem = person.note_path?.split(/[\\/]/).pop()?.replace('.md', '') ?? '';
  return <button type="button" className="btn tag-chip" onClick={() => onOpen(stem)} key={person.email}>{person.name}</button>;
}

function truncate(text: string, max: number): string {
  return text.length > max ? `${text.slice(0, max).trimEnd()}…` : text;
}

// A message with `reply_to_message_id` (REQ-SB-82-US-04, Scenario 4)
// stays in its natural chronological position (never reordered/moved
// next to its question -- that would disturb everything exchanged since)
// but carries a quoted "replying to" strip so it's visibly threaded
// rather than an undifferentiated new message at the bottom.
function ChatMessage({
  message, parent, onReply,
}: {
  message: CockpitChatMessage;
  parent: CockpitChatMessage | undefined;
  // REQ-SB-82-US-06-T07 -- the WRITE-side "pick a message to reply to"
  // affordance. Only rendered for a real, `id`-bearing message (a
  // pre-REQ-SB-82-US-04 legacy message has no `id` and is un-threadable,
  // same convention `chat_store.py` already documents).
  onReply: (messageId: string) => void;
}) {
  if (message.speaker === 'system') {
    return <div className="chat-message chat-message--system">{message.text}</div>;
  }
  return (
    <div className={`chat-message chat-message--${message.speaker === 'user' ? 'user' : 'agent'}`}>
      {message.speaker === 'agent' && <span className="chat-message-author">{message.agent_name}</span>}
      {parent && (
        <div className="chat-message-reply-to">↳ replying to: “{truncate(parent.text, 80)}”</div>
      )}
      <ChatMessageText text={message.text} />
      {message.id && (
        <button
          type="button"
          className="chat-message-reply-btn"
          aria-label="Reply to this message"
          onClick={() => onReply(message.id!)}
        >
          <span className="material-symbols-outlined" aria-hidden="true">reply</span>
        </button>
      )}
    </div>
  );
}

function DocumentRow({ doc }: { doc: CockpitDocument }) {
  return (
    <div className="item-row" key={doc.note_path}>
      <span className="material-symbols-outlined cockpit-person-icon" aria-hidden="true">description</span>
      <span className="item-row-title">{doc.filename ?? doc.title}</span>
    </div>
  );
}

function ExpertRow({ agent, onClick, title }: { agent: AgentSummary; onClick: () => void; title: string }) {
  const iconName = getVisualIconName(agent.icon) ?? 'psychology';
  return (
    <button type="button" className="item-row cockpit-person-row" onClick={onClick} title={title}>
      <span className="material-symbols-outlined cockpit-person-icon" aria-hidden="true">{iconName}</span>
      <span className="item-row-title">{agent.name}</span>
    </button>
  );
}

export function Cockpit({ subjectKind, subjectNoteStem, infoFields }: CockpitProps) {
  const [tab, setTab] = useState<CockpitTab>('overview');
  const [data, setData] = useState<CockpitData | null>(null);
  const [experts, setExperts] = useState<AgentSummary[] | null>(null);
  const [openPersonStem, setOpenPersonStem] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  // Who's currently being asked, keyed by the question's own message id --
  // an array (not one value) since a second message can be sent, and
  // routed to a DIFFERENT agent, while an earlier one is still pending
  // (Scenario 3: never blocked). Rendered as "X is typing..." (operator,
  // 2026-08-26: "You need to show me what's happening").
  const [answering, setAnswering] = useState<PendingAnswer[]>([]);
  const [uploading, setUploading] = useState(false);
  // REQ-SB-82-US-06-T07 -- which earlier message the next Send should
  // mark as a reply-to hint (ADR-012 point 4: a strong hint into the
  // moderator's reasoning, never a hard override). Purely local UI
  // selection state, never persisted itself -- only the resulting
  // `reply_to_message_id` sent with the next message is.
  const [replyToMessageId, setReplyToMessageId] = useState<string | null>(null);
  const pollTimeoutsRef = useRef<Set<ReturnType<typeof setTimeout>>>(new Set());
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchCockpit(subjectKind, subjectNoteStem).then(setData);
    fetchAgentList().then(setExperts);
    return () => {
      pollTimeoutsRef.current.forEach(clearTimeout);
      pollTimeoutsRef.current.clear();
    };
  }, [subjectKind, subjectNoteStem]);

  // Every dispatched reply (a routed Expert or the Research Agent
  // fallback) lands in the background with no push mechanism -- polls for
  // its threaded reply, stopping once it's seen or after
  // _REPLY_POLL_MAX_ATTEMPTS (also clearing its own "typing" entry either way).
  const pollForAnswer = (pendingMessageId: string, attemptsLeft: number) => {
    if (attemptsLeft <= 0) {
      setAnswering((current) => current.filter((a) => a.messageId !== pendingMessageId));
      return;
    }
    const timeoutId = setTimeout(() => {
      pollTimeoutsRef.current.delete(timeoutId);
      fetchCockpit(subjectKind, subjectNoteStem).then((fresh) => {
        setData(fresh);
        const arrived = fresh.thread.messages.some((m) => m.reply_to_message_id === pendingMessageId);
        if (arrived) {
          setAnswering((current) => current.filter((a) => a.messageId !== pendingMessageId));
        } else {
          pollForAnswer(pendingMessageId, attemptsLeft - 1);
        }
      });
    }, _REPLY_POLL_INTERVAL_MS);
    pollTimeoutsRef.current.add(timeoutId);
  };

  const handleSend = (e: FormEvent | KeyboardEvent) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text || sending) return;
    setSending(true);
    setDraft('');
    // Resolved against the CURRENT thread, before this send's own new
    // message is appended below -- a `replyToMessageId` that no longer
    // resolves (Scenario 8) simply yields `undefined` here, and the send
    // proceeds as a plain, un-hinted message rather than a broken one.
    const replyToId = data?.thread.messages.find((m) => m.id === replyToMessageId)?.id;
    // Cleared on send, regardless of outcome -- same pattern as `draft`
    // above (AgentChatPanel.tsx's own T08 reply-to affordance clears its
    // equivalent selection the same way, for the same reason).
    setReplyToMessageId(null);
    // Optimistic append (operator, 2026-08-26: "The Message Don't get
    // added to the chat until Something happen") -- shows immediately,
    // replaced by the server's own authoritative thread (real id
    // included) the moment the fast routing-decision response lands.
    setData((current) => current ? {
      ...current,
      thread: {
        ...current.thread,
        messages: [...current.thread.messages, {
          speaker: 'user', agent_id: null, agent_name: null, text,
        }],
      },
    } : current);
    sendMessage(subjectKind, subjectNoteStem, text, replyToId).then(({ thread, answering: nowAnswering }) => {
      setData((current) => (current ? { ...current, thread } : current));
      setSending(false);
      const userMessage = [...thread.messages].reverse().find((m) => m.speaker === 'user' && m.text === text);
      if (userMessage?.id && nowAnswering) {
        setAnswering((current) => [
          ...current,
          { messageId: userMessage.id!, agentId: nowAnswering.agent_id, agentName: nowAnswering.agent_name },
        ]);
        pollForAnswer(userMessage.id, _REPLY_POLL_MAX_ATTEMPTS);
      }
    }).catch(() => {
      // The user's own message is persisted server-side regardless of
      // whether routing/the Hermes turn itself failed (chat_turn.py
      // appends it before routing) -- re-fetch so it shows up rather than
      // leaving the input stuck on "Sending..." with no visible message.
      setSending(false);
      fetchCockpit(subjectKind, subjectNoteStem).then(setData);
    });
  };

  // Plain Enter sends, Shift+Enter OR Alt+Enter inserts a real newline --
  // same convention as the established multiline chat input
  // (AgentChatPanel.tsx, operator: "when I try to do a multiline text
  // Alt+Enter Doesn't create a new line"). A <textarea> doesn't
  // auto-submit its form on Enter the way a single <input> does, so this
  // handler is what makes plain Enter still send.
  const handleDraftKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.altKey) {
      event.preventDefault();
      handleSend(event);
    }
  };

  // Auto-grows the textarea as real content wraps, same 3-to-5-line
  // ceiling as AgentChatPanel.tsx.
  const handleDraftChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    setDraft(event.target.value);
    const el = event.target;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, _CHAT_INPUT_MAX_HEIGHT_PX)}px`;
  };

  // Upload a file/screenshot straight into this meeting's own folder
  // (operator, 2026-08-27: "I will need to upload a file or a Screenshot
  // while I am in the meeting... I don't have upload button in the
  // screen") -- persisted immediately (not attached-then-sent, unlike the
  // Agent Chat panel's own ephemeral attach flow), with a system
  // confirmation appended to the live chat so it reads as a real event in
  // the conversation, not a silent background write.
  const handleFileSelect = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (!file) return;
    setUploading(true);
    uploadDocument(subjectKind, subjectNoteStem, file)
      .then(() => fetchCockpit(subjectKind, subjectNoteStem))
      .then(setData)
      .finally(() => setUploading(false));
  };

  // Real, persisted roster (REQ-SB-82-US-01, ADR-007) -- derived from the
  // fetched thread every render, never held as its own local useState, so
  // it can never drift from the real backend value.
  const broughtInIds = new Set(data?.thread.brought_in_agent_ids ?? []);
  // Moderator-recommended roster (REQ-SB-82-US-03) -- additive/
  // informational only. An id already brought in renders ONLY under "In
  // this chat" (never duplicated into "Recommended"); a still-recommended
  // id is also excluded from the plain "Experts" list below so it isn't
  // shown twice, one Add action per agent at a time (scope-internal
  // judgement call, since Recommended's own Add already brings it in the
  // same real way).
  const recommendedIds = new Set(data?.thread.recommended_agent_ids ?? []);
  const allExperts = (experts ?? []).filter((agent) => agent.type === 'expert' && !isBackgroundAgent(agent));
  const inChat = allExperts.filter((agent) => broughtInIds.has(agent.id));
  const recommended = allExperts.filter((agent) => recommendedIds.has(agent.id) && !broughtInIds.has(agent.id));
  const available = allExperts.filter((agent) => !broughtInIds.has(agent.id) && !recommendedIds.has(agent.id));

  const bringIn = (id: string) => {
    bringInAgent(subjectKind, subjectNoteStem, id).then((thread) => {
      setData((current) => (current ? { ...current, thread } : current));
    });
  };
  const remove = (id: string) => {
    removeAgent(subjectKind, subjectNoteStem, id).then((thread) => {
      setData((current) => (current ? { ...current, thread } : current));
    });
  };

  return (
    <div className="cockpit-layout">
      <nav className="cockpit-nav">
        {NAV_ITEMS.map((item) => (
          <button
            type="button"
            key={item.tab}
            className={tab === item.tab ? 'cockpit-nav-item active' : 'cockpit-nav-item'}
            onClick={() => setTab(item.tab)}
          >
            <span className="cockpit-nav-icon" aria-hidden="true">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      <div className="cockpit-main-column">
        {tab === 'overview' && (
          <div className="cockpit-panel">
            <div className="cockpit-section">
              <h3>{subjectKind === 'meeting' ? 'Meeting summary' : 'Email summary'}</h3>
              {data?.overview.summary ? (
                <p>{data.overview.summary}</p>
              ) : (
                <p className="text-muted">No prep summary yet.</p>
              )}
            </div>
            <div className="cockpit-section">
              <h3>People ({data?.people.length ?? 0})</h3>
              {data?.people.length ? (
                <div className="action-list">
                  {data.people.map((person) => <PersonChip person={person} onOpen={setOpenPersonStem} key={person.email} />)}
                </div>
              ) : (
                <p className="text-muted">No people resolved yet.</p>
              )}
            </div>
            <div className="cockpit-section">
              <h3>Related documents ({data?.overview.related_documents.length ?? 0})</h3>
              {data?.overview.related_documents.length ? (
                <div className="item-list">
                  {data.overview.related_documents.map((doc) => <DocumentRow doc={doc} key={doc.note_path} />)}
                </div>
              ) : (
                <p className="text-muted">Nothing gathered yet.</p>
              )}
            </div>
            <div className="cockpit-section">
              <h3>Articles ({data?.overview.articles.length ?? 0})</h3>
              {data?.overview.articles.length ? (
                <div className="item-list">
                  {data.overview.articles.map((article) => (
                    <div className="item-row" key={article.url}>
                      <a href={article.url} target="_blank" rel="noreferrer">{article.title}</a>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted">Nothing gathered yet.</p>
              )}
            </div>
          </div>
        )}

        {tab === 'chat' && (
          <div className="cockpit-panel">
            <h3>Chat</h3>
            {/* .chat-thread ALWAYS renders (matches AgentChatPanel.tsx's own
                established structure) -- the empty-state message lives
                INSIDE it as a plain line, never a separate block swapped
                in place of it. Swapping in a differently-laid-out block
                when there are no messages was what pushed the Send button
                to the middle of the panel (operator, 2026-08-27: "when the
                Chat is empty, the Send Button is in the middle of the
                screen") -- .chat-thread's own flex:1 sizing now applies
                consistently whether it holds real messages or just the
                empty note, so the input row stays pinned at the bottom
                either way. */}
            <div className="chat-thread">
              {data?.thread.messages.length ? (
                data.thread.messages.map((message, index) => {
                  const parent = message.reply_to_message_id
                    ? data.thread.messages.find((m) => m.id === message.reply_to_message_id)
                    : undefined;
                  return (
                    <ChatMessage
                      message={message}
                      parent={parent}
                      onReply={setReplyToMessageId}
                      key={message.id ?? index}
                    />
                  );
                })
              ) : (
                <p className="text-muted chat-thread-empty">
                  No messages yet. Bring in an Expert, then ask a question below.
                </p>
              )}
              {answering.map((a) => (
                <div className="chat-message chat-message--agent chat-message--typing" key={a.messageId}>
                  <span className="chat-message-author">{a.agentName}</span>
                  <span className="typing-indicator" aria-label={`${a.agentName} is typing`}>
                    <span /><span /><span />
                  </span>
                </div>
              ))}
            </div>
            <p className="chat-mention-hint text-muted">
              Tip: start with <code>@expert-name</code> to send straight to a specific Expert.
              Shift+Enter for a new line.
            </p>
            {/* REQ-SB-82-US-06-T07 -- Scenario 8: `replyToMessage` is
                undefined the moment `replyToMessageId` no longer resolves
                against the CURRENT `data.thread.messages` (e.g. a stale
                selection after fresher data replaced it), so this strip
                simply doesn't render rather than showing a broken/blank
                quote. `handleSend` independently re-resolves the same
                reference at send time, so Send always still works either way. */}
            {(() => {
              const replyToMessage = data?.thread.messages.find((m) => m.id === replyToMessageId);
              return replyToMessage ? (
                <div className="chat-reply-to-preview" data-role="reply-to-preview">
                  <span className="chat-reply-to-preview-text">
                    ↳ Replying to: {truncate(replyToMessage.text, _REPLY_PREVIEW_MAX_CHARS)}
                  </span>
                  <button
                    type="button"
                    className="btn"
                    aria-label="Cancel reply"
                    onClick={() => setReplyToMessageId(null)}
                  >
                    ×
                  </button>
                </div>
              ) : null;
            })()}
            <form className="chat-input-row" onSubmit={handleSend}>
              <input
                ref={fileInputRef}
                type="file"
                style={{ display: 'none' }}
                onChange={handleFileSelect}
              />
              <button
                type="button"
                className="chat-attach-btn"
                aria-label="Attach a file or screenshot to this meeting"
                title="Attach a file or screenshot to this meeting"
                disabled={uploading}
                onClick={() => fileInputRef.current?.click()}
              >
                <span className="material-symbols-outlined" aria-hidden="true">attach_file</span>
              </button>
              <textarea
                className="input chat-message-input"
                placeholder="Ask a question… (@mention to redirect)"
                rows={3}
                value={draft}
                onChange={handleDraftChange}
                onKeyDown={handleDraftKeyDown}
                disabled={sending}
              />
              <button type="submit" className="btn btn-primary" disabled={sending || !draft.trim()}>
                {sending ? 'Sending…' : 'Send'}
              </button>
            </form>
          </div>
        )}

        {tab === 'people' && (
          <div className="cockpit-panel">
            <h3>{subjectKind === 'meeting' ? 'Attendees' : 'People on this email'}</h3>
            {data?.people.length ? (
              <div className="action-list">
                {data.people.map((person) => <PersonChip person={person} key={person.email} />)}
              </div>
            ) : (
              <div className="empty-state"><p className="text-muted">No people resolved yet.</p></div>
            )}
          </div>
        )}

        {tab === 'documents' && (
          <div className="cockpit-panel">
            <h3>Documents</h3>
            {data?.overview.related_documents.length ? (
              <div className="item-list">
                {data.overview.related_documents.map((doc) => <DocumentRow doc={doc} key={doc.note_path} />)}
              </div>
            ) : (
              <div className="empty-state">
                <p className="text-muted">Nothing uploaded yet.</p>
                <p className="text-muted">Use the attach button in Chat to add a file or screenshot.</p>
              </div>
            )}
          </div>
        )}

        {tab === 'articles' && (
          <div className="cockpit-panel">
            <h3>Articles you might need</h3>
            <div className="empty-state"><p className="text-muted">Nothing gathered yet.</p></div>
          </div>
        )}
      </div>

      {tab === 'chat' ? (
        <div className="cockpit-panel">
          {recommended.length > 0 && (
            <>
              <div className="cockpit-group-label">Recommended</div>
              <div className="item-list">
                {recommended.map((agent) => (
                  <div className="cockpit-expert-recommended" key={agent.id}>
                    <ExpertRow agent={agent} title="Add to chat" onClick={() => bringIn(agent.id)} />
                  </div>
                ))}
              </div>
            </>
          )}
          {inChat.length > 0 && (
            <>
              <div className="cockpit-group-label" style={{ marginTop: recommended.length > 0 ? 'var(--space-4)' : 0 }}>In this chat</div>
              <div className="item-list">
                {inChat.map((agent) => (
                  <ExpertRow agent={agent} key={agent.id} title="Remove from chat" onClick={() => remove(agent.id)} />
                ))}
              </div>
            </>
          )}
          <div
            className="cockpit-group-label"
            style={{ marginTop: inChat.length > 0 || recommended.length > 0 ? 'var(--space-4)' : 0 }}
          >
            {inChat.length > 0 ? 'Bring in another Expert' : 'Experts'}
          </div>
          {available.length ? (
            <div className="item-list">
              {available.map((agent) => (
                <ExpertRow agent={agent} key={agent.id} title="Bring into this chat" onClick={() => bringIn(agent.id)} />
              ))}
            </div>
          ) : (
            <div className="empty-state"><p className="text-muted">No more Experts available.</p></div>
          )}
        </div>
      ) : (
        <div className="cockpit-panel">
          <h3>{subjectKind === 'meeting' ? 'Meeting info' : 'Email info'}</h3>
          <div className="kv-list">
            {infoFields.map(({ label, key }) => (
              <div className="kv-row" key={key}><span className="kv-key">{label}</span><span>{String(data?.subject[key] ?? '')}</span></div>
            ))}
          </div>
        </div>
      )}

      {openPersonStem && <PersonNotePanel stem={openPersonStem} onClose={() => setOpenPersonStem(null)} />}
    </div>
  );
}
