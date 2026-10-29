import { useEffect, useState } from 'react';
import { Link } from 'react-router';
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

/** How the log is grouped. `none` is kept and is the default: the log
 *  is chronological, and chronological is the right answer to "what
 *  just happened" — grouping is for the other question, "what has this
 *  agent been doing", and the page should not silently decide which
 *  one you came with. */
type Grouping = 'none' | 'agent' | 'day' | 'source' | 'outcome';

const GROUPING_LABELS: Record<Grouping, string> = {
  none: 'Chronological',
  agent: 'By agent',
  day: 'By day',
  source: 'By where it came from',
  outcome: 'By how it ended',
};

function outcomeOf(session: HermesSession): string {
  if (session.is_active) return 'Still running';
  if (session.end_reason && session.end_reason.includes('error')) return 'Failed';
  return 'Done';
}

export function AgentActivityPage() {
  const [sessions, setSessions] = useState<HermesSession[] | null>(null);
  const [agentNames, setAgentNames] = useState<Map<string, string>>(new Map());
  const [grouping, setGrouping] = useState<Grouping>('none');

  const load = () => {
    Promise.all([fetchHermesSessions(50), fetchAgentList()]).then(([sessionsResponse, agents]) => {
      setSessions(sessionsResponse.sessions);
      setAgentNames(new Map(agents.map((agent) => [agent.id, agent.name])));
    });
  };

  useEffect(load, []);

  /** The sessions in named groups, in the order the groups should
   *  read. Chronological order WITHIN a group is preserved in every
   *  case — grouping answers "whose" or "when", never "in what order",
   *  and reshuffling inside a group would lose the one ordering the
   *  log is actually built on. */
  function group(all: HermesSession[]): Array<[string, HermesSession[]]> {
    if (grouping === 'none') return [['', all]];
    const buckets = new Map<string, HermesSession[]>();
    for (const session of all) {
      const key =
        grouping === 'agent'
          ? (session.profile && agentNames.get(session.profile)) ?? session.profile ?? 'Unknown agent'
          : grouping === 'day'
            // `started_at` is nullable, and a session with no start is
            // real — it is grouped as such rather than crashing the
            // page or being silently dated today.
            ? (session.started_at === null
                ? 'No start recorded'
                : new Date(session.started_at).toLocaleDateString())
            : grouping === 'source'
              ? SOURCE_LABELS[session.source] ?? session.source
              : outcomeOf(session);
      buckets.set(key, [...(buckets.get(key) ?? []), session]);
    }
    // Biggest group first for agent and source — "who is busiest" is
    // the question those two are asked with. Day stays newest-first,
    // which is what the log already is.
    const entries = [...buckets.entries()];
    return grouping === 'day'
      ? entries
      : entries.sort((left, right) => right[1].length - left[1].length);
  }

  return (
    <>
      <h1>Agent Activity</h1>
      {/* The doors are the other half of this page's question: a session
          list says what ran, entry points say where it came in from. */}
      <p className="auth-note">
        Click a session to read what the agent decided, which tools it called and what each
        answered. <Link to="/entry-points">Entry points</Link> shows which outside door reaches
        which agent.
      </p>
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

      <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
        <label>
          Group{' '}
          <select
            className="input"
            data-testid="activity-grouping"
            value={grouping}
            onChange={(event) => setGrouping(event.target.value as Grouping)}
          >
            {(Object.keys(GROUPING_LABELS) as Grouping[]).map((key) => (
              <option key={key} value={key}>{GROUPING_LABELS[key]}</option>
            ))}
          </select>
        </label>
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
          group(sessions).map(([heading, inGroup]) => (
            <div key={heading || 'all'}>
              {heading && (
                <h3 className="activity-group-heading" data-testid="activity-group">
                  {heading} <span className="badge">{inGroup.length}</span>
                </h3>
              )}
              <div className="log-list">
            {inGroup.map((session) => (
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
                  <Link to={`/agent-activity/${encodeURIComponent(session.id)}`}>
                    {session.title || '(untitled session)'}
                  </Link>
                  {' — '}
                  {session.message_count} message{session.message_count === 1 ? '' : 's'}
                  {session.ended_at !== null && ` — ${formatDuration(session.started_at, session.ended_at)}`}
                </span>
                <span className="log-item-meta">{formatTimestamp(session.started_at)}</span>
              </div>
            ))}
              </div>
            </div>
          ))
        )}
      </div>
    </>
  );
}
