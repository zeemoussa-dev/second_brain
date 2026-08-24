import { useEffect, useState } from 'react';
import { fetchHermesSessions, type HermesSession } from '../features/hermes-ops/client';
import { fetchAgentList } from '../features/agents-map/agentsApiClient';

// Real Hermes session log (operator, 2026-08-23: "the Agents Activities
// Tab should get the Agents Log from Hermes") -- replaces the earlier
// Second-Brain-native "run_event/run_error" activity log, which had gone
// silently dead: its own backend router (agent_activity_router.py) had
// already been removed with nothing left importing it, and its data
// source (agent_registry.list_agents()) has returned [] since agent
// orchestration moved to Hermes this same session. `/hermes/sessions`
// (hermes_client.py, already live/verified) is the real replacement --
// every genuine session Hermes has run, cron and interactive alike.

function formatTimestamp(epochSeconds: number | null): string {
  if (epochSeconds === null) return '—';
  return new Date(epochSeconds * 1000).toLocaleString();
}

function formatDuration(startedAt: number | null, endedAt: number | null): string {
  if (startedAt === null || endedAt === null) return '—';
  const totalSeconds = Math.max(0, Math.round(endedAt - startedAt));
  if (totalSeconds < 60) return `${totalSeconds}s`;
  const minutes = Math.floor(totalSeconds / 60);
  const remainingSeconds = totalSeconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

const SOURCE_LABELS: Record<string, string> = {
  cron: 'Cron',
  whatsapp: 'WhatsApp',
  'second-brain': 'Second Brain',
  desktop: 'Desktop',
  tui: 'Terminal',
};

export function AgentActivityPage() {
  const [sessions, setSessions] = useState<HermesSession[] | null>(null);
  const [agentNames, setAgentNames] = useState<Map<string, string>>(new Map());

  const load = () => {
    Promise.all([fetchHermesSessions(50), fetchAgentList()]).then(([sessionsResponse, agents]) => {
      setSessions(sessionsResponse.sessions);
      setAgentNames(new Map(agents.map((agent) => [agent.id, agent.name])));
    });
  };

  useEffect(load, []);

  return (
    <>
      <h1>Agent Activity</h1>
      <p className="text-muted">
        A real, chronological log of every session Hermes has actually run
        — cron jobs and interactive chats alike — pulled directly from
        Hermes' own session history, not a Second-Brain-native record kept
        separately from what actually happened.
      </p>
      <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
        <button
          type="button"
          className="btn"
          style={{
            padding: 'var(--space-1) var(--space-3)',
            fontSize: 'var(--font-size-sm)',
            marginRight: 'var(--space-2)',
          }}
          onClick={load}
        >
          &#8635; Refresh
        </button>
        Recomputes fresh on open or refresh — never a cached snapshot from
        an earlier page load.
      </p>

      <h2 style={{ marginTop: 'var(--space-6)' }}>Hermes session log</h2>
      <div className="card">
        {sessions === null ? (
          <p className="text-muted">Loading...</p>
        ) : sessions.length === 0 ? (
          <div className="empty-state">
            <p style={{ margin: 0, fontWeight: 600, color: 'var(--color-text)' }}>
              No sessions recorded yet
            </p>
            <p style={{ margin: 'var(--space-1) 0 0' }}>
              Hermes hasn't run any session yet — shown honestly, not
              fabricated as an entry.
            </p>
          </div>
        ) : (
          <div className="log-list">
            {sessions.map((session) => (
              <div className="log-item" key={session.id}>
                <span>
                  {session.is_active ? (
                    <span className="badge badge-warning">Active</span>
                  ) : session.end_reason && session.end_reason.includes('error') ? (
                    <span className="badge badge-danger">Failed</span>
                  ) : (
                    <span className="badge badge-success">Done</span>
                  )}{' '}
                  <span className="badge">{SOURCE_LABELS[session.source] ?? session.source}</span>{' '}
                  <strong>{(session.profile && agentNames.get(session.profile)) ?? session.profile ?? 'Unknown agent'}</strong>
                  {' — '}
                  {session.title || '(untitled session)'}
                  {' — '}
                  {session.message_count} message{session.message_count === 1 ? '' : 's'}
                  {session.ended_at !== null && ` — ${formatDuration(session.started_at, session.ended_at)}`}
                </span>
                <span className="log-item-meta">{formatTimestamp(session.started_at)}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
