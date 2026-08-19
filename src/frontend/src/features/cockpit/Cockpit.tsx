import { useEffect, useState } from 'react';
import { fetchAgentList, isBackgroundAgent, type AgentSummary } from '../agents-map/agentsApiClient';
import {
  fetchCockpit, bringInAgent, sendCockpitMessage, triggerCockpitResearch, saveCockpitResearch,
  confirmPersonNoteProposal, discardPersonNoteProposal,
  type CockpitData,
} from './cockpitApiClient';
import { ChatMessageText } from '../../components/ChatMessageText';

const MENTION_TOKEN_RE = /@(\S+)/g;

function normalizeForMatch(value: string): string {
  return value.toLowerCase().replace(/\s+/g, '');
}

function resolveMentionedAgents(text: string, candidates: AgentSummary[]): AgentSummary[] {
  const resolved: AgentSummary[] = [];
  const seenIds = new Set<string>();
  for (const match of text.matchAll(MENTION_TOKEN_RE)) {
    const normalizedToken = normalizeForMatch(match[1]);
    const agent = candidates.find(
      (a) => normalizeForMatch(a.id) === normalizedToken || normalizeForMatch(a.name) === normalizedToken,
    );
    if (agent && !seenIds.has(agent.id)) {
      seenIds.add(agent.id);
      resolved.push(agent);
    }
  }
  return resolved;
}

interface CockpitProps {
  subjectKind: 'meeting' | 'email';
  subjectNoteStem: string;
  subjectTitleFields: { label: string; key: string }[]; // e.g. [{label:'Time',key:'start'}]
  attachmentsSlot?: React.ReactNode;    // REQ-SB-44-US-01 only, undefined here
  enableDraftCopyAffordance?: boolean;  // REQ-SB-44-US-01 only, undefined/false here
}

export function Cockpit({
  subjectKind, subjectNoteStem, subjectTitleFields, attachmentsSlot, enableDraftCopyAffordance,
}: CockpitProps) {
  const [data, setData] = useState<CockpitData | null>(null);
  const [availableAgents, setAvailableAgents] = useState<AgentSummary[] | null>(null);
  const [messageInput, setMessageInput] = useState('');
  const [pendingResearch, setPendingResearch] = useState<{ query: string; summary: string } | null>(null);
  const [sending, setSending] = useState(false);

  const reload = () => fetchCockpit(subjectKind, subjectNoteStem).then(setData);
  useEffect(() => { reload(); fetchAgentList().then(setAvailableAgents); }, [subjectKind, subjectNoteStem]);

  const hasExperts = (data?.thread.brought_in_agent_ids.length ?? 0) > 0;
  const agentById = new Map((availableAgents ?? []).map((agent) => [agent.id, agent]));
  const bringInCandidates = (availableAgents ?? []).filter((agent) => !isBackgroundAgent(agent));

  // REQ-SB-51-US-01-T04 already filters Background Agents out of bringInCandidates;
  // mention matching/suggestions reuse that same filtered list, never availableAgents directly.
  const mentionedAgents = resolveMentionedAgents(messageInput, bringInCandidates);
  const hasResolvableMention = mentionedAgents.length > 0;
  const canSend = messageInput.trim().length > 0 && (hasExperts || hasResolvableMention);

  const mentionQueryMatch = messageInput.match(/@(\S*)$/);
  const mentionQuery = mentionQueryMatch ? mentionQueryMatch[1] : null;
  const mentionSuggestions = mentionQuery
    ? bringInCandidates.filter((agent) => {
        const q = normalizeForMatch(mentionQuery);
        return normalizeForMatch(agent.id).includes(q) || normalizeForMatch(agent.name).includes(q);
      })
    : [];

  const handleSendMessage = (event: React.FormEvent) => {
    event.preventDefault();
    if (!canSend || sending) return;
    setSending(true);
    Promise.all(mentionedAgents.map((agent) => bringInAgent(subjectKind, subjectNoteStem, agent.id)))
      .then(() => sendCockpitMessage(subjectKind, subjectNoteStem, messageInput, mentionedAgents.map((agent) => agent.id)))
      .then((updatedThread) => {
        setMessageInput('');
        setData((current) => (current ? { ...current, thread: updatedThread } : current));
      })
      .finally(() => setSending(false));
  };

  return (
    <div className="cockpit-layout">
      <div>
        <div className="card">
          <h3>Available Agents</h3>
          <div className="item-list">
            {bringInCandidates.map((agent) => {
              const inChat = data?.thread.brought_in_agent_ids.includes(agent.id) ?? false;
              return (
                <div className="item-row" key={agent.id}>
                  <div className="item-row-main">
                    <span className="item-row-title">{agent.name}</span>
                    <span className="item-row-meta">{agent.type}</span>
                  </div>
                  <div className="item-row-actions">
                    {inChat ? (
                      <span className="badge badge-success">In this chat</span>
                    ) : (
                      <button type="button" className="btn" onClick={() => bringInAgent(subjectKind, subjectNoteStem, agent.id).then(reload)}>
                        + Bring in
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          <h3 style={{ marginTop: 'var(--space-6)' }}>Quick research ({subjectKind === 'meeting' ? 'this meeting' : 'this email'})</h3>
          {data?.research_results.length ? (
            <div className="item-list">
              {data.research_results.map((result) => (
                <div className="item-row" key={result.stem}>
                  <div className="item-row-main"><span className="item-row-title">{result.title}</span></div>
                  <span className="badge badge-success">Saved</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <p className="text-muted">Nothing yet — trigger on-the-spot research from the chat once you've brought in an Expert.</p>
            </div>
          )}
        </div>
      </div>

      <div>
        <div className="card">
          <h3>Chat</h3>
          {data?.thread.messages.length ? (
            <div className="chat-thread">
              {data.thread.messages.map((message, index) => (
                <div className={`chat-message chat-message--${message.speaker === 'user' ? 'user' : 'agent'}`} key={index}>
                  {message.speaker === 'agent' && (
                    <span
                      className="chat-message-author"
                      style={{ '--author-color': `var(--agent-color-${agentById.get(message.agent_id ?? '')?.type ?? 'expert'})` } as React.CSSProperties}
                    >
                      {message.agent_name}
                    </span>
                  )}
                  <ChatMessageText text={message.text} />
                  {enableDraftCopyAffordance && message.speaker === 'agent' && (
                    <button type="button" className="btn" style={{ marginLeft: 'var(--space-3)' }}
                      onClick={() => navigator.clipboard.writeText(message.text)}>
                      Copy
                    </button>
                  )}
                </div>
              ))}
              {sending && (
                <div className="chat-message chat-message--agent chat-message--pending" aria-live="polite">
                  <span className="chat-typing-dot" />
                  <span className="chat-typing-dot" />
                  <span className="chat-typing-dot" />
                </div>
              )}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">💬</div>
              <p><strong>No Experts brought in yet.</strong></p>
              <p className="text-muted">Use "+ Bring in" on the left to add an Expert to this meeting's shared chat.</p>
            </div>
          )}
          {pendingResearch && (
            <div className="chat-proposal">
              <span className="badge badge-warning">Awaiting your decision</span>
              <p>{pendingResearch.summary}</p>
              <div className="chat-proposal-actions">
                <button type="button" className="btn btn-primary" onClick={() =>
                  saveCockpitResearch(subjectKind, subjectNoteStem, pendingResearch.query, pendingResearch.summary)
                    .then(() => { setPendingResearch(null); reload(); })
                }>Save to vault</button>
                <button type="button" className="btn btn-danger" onClick={() => setPendingResearch(null)}>Discard</button>
              </div>
            </div>
          )}
          {data?.person_note_proposals.map((proposal) => (
            <div className="chat-proposal" key={proposal.id}>
              <span className="badge badge-warning">Awaiting your decision</span>
              <p>Propose an update to <strong>{proposal.person_name}</strong>'s note: {proposal.instruction}</p>
              <div className="chat-proposal-actions">
                <button type="button" className="btn btn-primary" onClick={() =>
                  confirmPersonNoteProposal(subjectKind, subjectNoteStem, proposal.id).then(reload)
                }>Confirm</button>
                <button type="button" className="btn btn-danger" onClick={() =>
                  discardPersonNoteProposal(subjectKind, subjectNoteStem, proposal.id).then(reload)
                }>Discard</button>
              </div>
            </div>
          ))}
          <form className="chat-input-row" onSubmit={handleSendMessage} style={{ position: 'relative' }}>
            <input
              type="text" className="input"
              placeholder={hasExperts ? 'Message the chat…' : 'Bring in an Expert, or type @agent_id, to start chatting…'}
              value={messageInput} onChange={(e) => setMessageInput(e.target.value)}
              disabled={sending}
            />
            <button type="submit" className="btn btn-primary" disabled={!canSend || sending}>
              Send
            </button>
            {mentionQuery !== null && mentionQuery.length > 0 && mentionSuggestions.length > 0 && (
              <div
                className="card mention-suggestion-list" data-testid="mention-suggestions"
                style={{ position: 'absolute', top: '100%', left: 0, zIndex: 10, marginTop: 'var(--space-1)', minWidth: '240px' }}
              >
                <div className="item-list">
                  {mentionSuggestions.map((agent) => (
                    <div
                      className="item-row" key={agent.id} style={{ cursor: 'pointer' }}
                      onClick={() => setMessageInput((current) => current.replace(/@(\S*)$/, `@${agent.id} `))}
                    >
                      <div className="item-row-main">
                        <span className="item-row-title">{agent.name}</span>
                        <span className="item-row-meta">{agent.id}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </form>
          {hasExperts && (
            <button type="button" className="btn" disabled={!messageInput} style={{ marginTop: 'var(--space-2)' }}
              onClick={() => {
                const requestingAgentId = data!.thread.brought_in_agent_ids[0];
                triggerCockpitResearch(subjectKind, subjectNoteStem, requestingAgentId, messageInput).then((result) => {
                  if (result.status === 'found') setPendingResearch({ query: result.query!, summary: result.summary! });
                  setMessageInput('');
                  reload();
                });
              }}>
              Quick research
            </button>
          )}
        </div>
      </div>

      <div className="card">
        <h3>{String(data?.subject.subject ?? '')}</h3>
        <div className="kv-list">
          {subjectTitleFields.map(({ label, key }) => (
            <div className="kv-row" key={key}><span className="kv-key">{label}</span><span>{String(data?.subject[key] ?? '')}</span></div>
          ))}
        </div>
        <h3 style={{ marginTop: 'var(--space-6)' }}>{subjectKind === 'meeting' ? 'Attendees' : 'People on this email'}</h3>
        <div className="action-list">
          {data?.people.map((person) => person.has_note ? (
            <a className="btn tag-chip" href={`/browse/${person.note_path?.split(/[\\/]/).pop()?.replace('.md', '')}`} key={person.email}>{person.name}</a>
          ) : (
            <span className="tag-chip--static" key={person.email}>{person.name} <span className="text-muted">(no note yet)</span></span>
          ))}
        </div>
        {attachmentsSlot}
      </div>
    </div>
  );
}
