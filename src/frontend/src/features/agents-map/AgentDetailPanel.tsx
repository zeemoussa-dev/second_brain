import { useEffect, useRef, useState } from 'react';
import {
  fetchAgent,
  fetchAgentHistory,
  sendChatMessage,
  updateAgentAssignment,
  type AgentDetail,
  type AgentHistoryEntry,
} from './agentsApiClient';
import { fetchSections, fetchProviders, type SectionSummary, type ProviderSummary } from '../settings/settingsApiClient';
import {
  fetchPendingApproval,
  approvePendingApproval,
  declinePendingApproval,
  type PendingApproval,
} from './pendingApprovalsApiClient';

interface AgentDetailPanelProps {
  agentId: string;
  onClose: () => void;
}

interface ChatMessage {
  role: 'user' | 'agent';
  text: string;
  isError?: boolean;
}

const TABS = ['chat', 'history', 'settings'] as const;
type Tab = (typeof TABS)[number];
const TAB_LABELS: Record<Tab, string> = { chat: 'Chat', history: 'History', settings: 'Settings' };

export function AgentDetailPanel({ agentId, onClose }: AgentDetailPanelProps) {
  const [agent, setAgent] = useState<AgentDetail | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [history, setHistory] = useState<AgentHistoryEntry[] | null>(null);
  const [sections, setSections] = useState<SectionSummary[] | null>(null);
  const [providers, setProviders] = useState<ProviderSummary[] | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [keywordsDraft, setKeywordsDraft] = useState('');
  const [approvals, setApprovals] = useState<Record<string, PendingApproval>>({});
  const threadEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setAgent(null); // clear stale content immediately on agent switch
    setMessages([]); // clear the previous agent's chat thread on switch
    setDraft('');
    setSending(false);
    setHistory(null); // clear the previous agent's history on switch
    setActiveTab('chat');
    setKeywordsDraft('');
    fetchAgent(agentId).then((detail) => {
      setAgent(detail);
      setKeywordsDraft(detail.keywords.join(', '));
    });
    fetchAgentHistory(agentId).then(setHistory);
    fetchSections().then(setSections);
    fetchProviders().then(setProviders);
  }, [agentId]);

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, sending]);

  useEffect(() => {
    if (!history) return;
    for (const entry of history) {
      if (entry.kind === 'proposal' && entry.pending_approval_id) {
        const id = entry.pending_approval_id;
        // A stale/unresolvable pending_approval_id (e.g. leftover smoke-
        // check history debris) must not surface as an unhandled promise
        // rejection -- the card simply stays in its default pending
        // styling rather than crashing the panel.
        fetchPendingApproval(id)
          .then((approval) => {
            setApprovals((prev) => ({ ...prev, [id]: approval }));
          })
          .catch(() => {});
      }
    }
  }, [history]);

  async function handleSectionChange(sectionId: string) {
    const updated = await updateAgentAssignment(agentId, { section_id: sectionId });
    setAgent(updated);
  }

  async function handleProviderChange(providerId: string) {
    const updated = await updateAgentAssignment(agentId, { provider_id: providerId });
    setAgent(updated);
  }

  async function handleWorkingModeChange(workingMode: string) {
    const updated = await updateAgentAssignment(agentId, { working_mode: workingMode });
    setAgent(updated);
  }

  async function handleApprove(approvalId: string) {
    const updated = await approvePendingApproval(approvalId);
    setApprovals((prev) => ({ ...prev, [approvalId]: updated }));
    fetchAgentHistory(agentId).then(setHistory);
  }

  async function handleDecline(approvalId: string) {
    const updated = await declinePendingApproval(approvalId);
    setApprovals((prev) => ({ ...prev, [approvalId]: updated }));
    fetchAgentHistory(agentId).then(setHistory);
  }

  async function handleKeywordsCommit() {
    const keywords = keywordsDraft
      .split(',')
      .map((keyword) => keyword.trim())
      .filter((keyword) => keyword.length > 0);
    const updated = await updateAgentAssignment(agentId, { keywords });
    setAgent(updated);
    setKeywordsDraft(updated.keywords.join(', '));
  }

  async function handleSend(event: React.FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || sending) return;
    setMessages((prev) => [...prev, { role: 'user', text }]);
    setDraft('');
    setSending(true);
    try {
      const response = await sendChatMessage(agentId, text);
      setMessages((prev) => [...prev, { role: 'agent', text: response.reply }]);
      fetchAgentHistory(agentId).then(setHistory);
    } catch {
      // A real Compass-backed reply can genuinely fail (network error,
      // Provider timeout) -- surfaced honestly in the thread itself, not
      // silently dropped, matching this project's own "honest, not
      // fabricated/swallowed" posture already established for actions.
      setMessages((prev) => [
        ...prev,
        { role: 'agent', text: 'Something went wrong sending that message. Please try again.', isError: true },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <>
      <div className="side-panel-overlay" onClick={onClose} />
      <aside className="side-panel" aria-label="Agent details">
        <div className="side-panel-header">
          <span className="badge">Agent detail</span>
          <button type="button" className="side-panel-close" aria-label="Close panel" onClick={onClose}>
            &times;
          </button>
        </div>
        {agent && (
          <>
            <div className="side-panel-title">
              <h2>{agent.name} <span className="badge">{agent.type}</span></h2>
            </div>
            <div className="side-panel-tabs" role="tablist">
              {TABS.map((tab) => (
                <button
                  key={tab}
                  type="button"
                  role="tab"
                  aria-selected={activeTab === tab}
                  className={`side-panel-tab${activeTab === tab ? ' side-panel-tab--active' : ''}`}
                  onClick={() => setActiveTab(tab)}
                >
                  {TAB_LABELS[tab]}
                </button>
              ))}
            </div>
          </>
        )}
        <div className="side-panel-body">
          {agent && (
            <div className="side-panel-agent" data-agent-detail={agent.id}>
              {activeTab === 'settings' && (
                <>
                  <div className="side-panel-section">
                    <h3>Settings</h3>
                    <div className="kv-list">
                      {agent.settings.map((row) => (
                        <div className="kv-row" key={row.key}>
                          <span className="kv-key">{row.key}</span>
                          <span>{row.value}</span>
                        </div>
                      ))}
                      <div className="kv-row">
                        <span className="kv-key">Section</span>
                        {sections && (
                          <select
                            className="input kv-select"
                            value={agent.section_id}
                            onChange={(event) => handleSectionChange(event.target.value)}
                          >
                            {sections.map((section) => (
                              <option key={section.id} value={section.id}>{section.name}</option>
                            ))}
                          </select>
                        )}
                      </div>
                      <div className="kv-row">
                        <span className="kv-key">Provider</span>
                        {providers && (
                          <select
                            className="input kv-select"
                            value={agent.provider_id}
                            onChange={(event) => handleProviderChange(event.target.value)}
                          >
                            {providers.map((provider) => (
                              <option key={provider.id} value={provider.id}>
                                {provider.name}{provider.is_default ? ' (default)' : ''}
                              </option>
                            ))}
                          </select>
                        )}
                      </div>
                      {!agent.provider_available && (
                        <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
                          {agent.provider_name} has no real client built yet — this agent
                          honestly reports it's not available rather than silently falling
                          back to Compass.
                        </p>
                      )}
                      <div className="kv-row">
                        <span className="kv-key">Working mode</span>
                        <select
                          className="input kv-select"
                          value={agent.working_mode}
                          onChange={(event) => handleWorkingModeChange(event.target.value)}
                        >
                          <option value="autonomous">Autonomous</option>
                          <option value="supervised">Supervised</option>
                          <option value="manual">Manual</option>
                        </select>
                      </div>
                      <div className="kv-row">
                        <span className="kv-key">Keywords</span>
                        <input
                          type="text"
                          className="input kv-select"
                          style={{ minWidth: 220 }}
                          value={keywordsDraft}
                          onChange={(event) => setKeywordsDraft(event.target.value)}
                          onBlur={handleKeywordsCommit}
                          placeholder="No keywords assigned yet"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="side-panel-section">
                    <h3>Available actions</h3>
                    <div className="action-list">
                      {agent.actions.map((action) => (
                        <button type="button" className="btn" key={action.id}>
                          {action.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'chat' && (
                <div className="side-panel-section side-panel-section--chat">
                  <div className="chat-thread" data-role="agent-chat-thread">
                    {messages.length === 0 && (
                      <p className="text-muted chat-thread-empty">
                        Ask {agent.name} anything, or send one of its known trigger
                        phrases to run an action directly.
                      </p>
                    )}
                    {messages.map((message, index) => (
                      <div
                        className={`chat-message chat-message--${message.role}${message.isError ? ' chat-message--error' : ''}`}
                        key={index}
                      >
                        {message.text}
                      </div>
                    ))}
                    {sending && (
                      <div className="chat-message chat-message--agent chat-message--pending" aria-live="polite">
                        <span className="chat-typing-dot" />
                        <span className="chat-typing-dot" />
                        <span className="chat-typing-dot" />
                      </div>
                    )}
                    <div ref={threadEndRef} />
                  </div>
                  <form className="chat-input-row" onSubmit={handleSend}>
                    <input
                      type="text"
                      className="input"
                      placeholder={`Message ${agent.name}…`}
                      value={draft}
                      onChange={(event) => setDraft(event.target.value)}
                      disabled={sending}
                    />
                    <button type="submit" className="btn btn-primary" disabled={sending || !draft.trim()}>
                      {sending ? 'Sending…' : 'Send'}
                    </button>
                  </form>
                </div>
              )}

              {activeTab === 'history' && (
                <div className="side-panel-section">
                  <h3>Communication history</h3>
                  {history && history.length > 0 ? (
                    <div className="log-list">
                      {history.map((entry, index) =>
                        entry.kind === 'proposal' && entry.pending_approval_id ? (
                          <ProposalCard
                            key={index}
                            entry={entry}
                            approval={approvals[entry.pending_approval_id]}
                            onApprove={() => handleApprove(entry.pending_approval_id as string)}
                            onDecline={() => handleDecline(entry.pending_approval_id as string)}
                          />
                        ) : (
                          <div className="log-item" key={index}>
                            <span>{entry.text}</span>
                            <span className="log-item-meta">{entry.timestamp}</span>
                          </div>
                        ),
                      )}
                    </div>
                  ) : (
                    history && (
                      <div className="empty-state">
                        <p className="text-muted">Nothing recorded yet.</p>
                      </div>
                    )
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </aside>
    </>
  );
}

function ProposalCard({
  entry,
  approval,
  onApprove,
  onDecline,
}: {
  entry: AgentHistoryEntry;
  approval: PendingApproval | undefined;
  onApprove: () => void;
  onDecline: () => void;
}) {
  const status = approval?.status ?? 'pending';
  if (status === 'approved') {
    return (
      <div className="chat-proposal chat-proposal--approved">
        <span className="badge badge-success">Approved</span>
        <p>{entry.text}</p>
      </div>
    );
  }
  if (status === 'declined') {
    return (
      <div className="chat-proposal chat-proposal--declined">
        <span className="badge badge-danger">Declined</span>
        <p>{entry.text}</p>
      </div>
    );
  }
  return (
    <div className="chat-proposal">
      <span className="badge badge-warning">Awaiting your approval</span>
      <p>{entry.text}</p>
      <div className="chat-proposal-actions">
        <button type="button" className="btn btn-primary" onClick={onApprove}>Approve</button>
        <button type="button" className="btn btn-danger" onClick={onDecline}>Decline</button>
      </div>
    </div>
  );
}
