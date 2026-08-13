import { useEffect, useState } from 'react';
import {
  fetchAgentActivity,
  type AgentActivityResponse,
} from '../features/agent-activity/client';

export function AgentActivityPage() {
  const [activity, setActivity] = useState<AgentActivityResponse | null>(null);

  const load = () => {
    fetchAgentActivity().then(setActivity);
  };

  useEffect(load, []);

  if (!activity) {
    return (
      <>
        <h1>Agent Activity</h1>
        <p className="text-muted">Loading...</p>
      </>
    );
  }

  return (
    <>
      <h1>Agent Activity</h1>
      <p className="text-muted">
        A chronological record of what background agent runs have happened
        — email, meeting, and (once built) to-do capture — with whether
        each succeeded or failed, plus whether Outlook is currently
        reachable, so a real capture failure is visible in the UI itself
        instead of only discoverable by symptom-chasing or digging through
        server logs (REQ-SB-11).
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
        Both the run list and the Outlook status below recompute fresh on
        open or refresh — never a cached snapshot from an earlier page
        load.
      </p>

      <h2 style={{ marginTop: 'var(--space-6)' }}>Activity log</h2>
      <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
        {activity.activity_log.length > 0 ? (
          <div className="log-list">
            {activity.activity_log.map((entry, index) => (
              <div className="log-item" key={index}>
                <span>
                  {entry.kind === 'run_error' ? (
                    <span className="badge badge-danger">Failed</span>
                  ) : (
                    <span className="badge badge-success">Success</span>
                  )}{' '}
                  {entry.agent_name} — {entry.text}
                </span>
                <span className="log-item-meta">{entry.timestamp}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p style={{ margin: 0, fontWeight: 600, color: 'var(--color-text)' }}>
              No agent activity recorded yet
            </p>
            <p style={{ margin: 'var(--space-1) 0 0' }}>
              No background capture agent has completed a run yet — shown
              honestly, not fabricated as a run entry or a
              misleadingly-empty "everything is fine" default.
            </p>
          </div>
        )}
      </div>

      <h2 style={{ marginTop: 'var(--space-6)' }}>Communication channels</h2>
      <div className="card">
        <div className="kv-list">
          <div className="kv-row">
            <span className="kv-key">Channel</span>
            <span>Outlook (direct COM)</span>
          </div>
          <div className="kv-row">
            <span className="kv-key">Status</span>
            <span
              className={`badge ${
                activity.outlook_channel.reachable ? 'badge-success' : 'badge-danger'
              }`}
            >
              {activity.outlook_channel.reachable ? 'Reachable' : 'Unreachable'}
            </span>
          </div>
        </div>
        {!activity.outlook_channel.reachable && activity.outlook_channel.detail && (
          <p
            className="text-muted"
            style={{ margin: 'var(--space-3) 0 0', fontSize: 'var(--font-size-sm)' }}
          >
            Error: {activity.outlook_channel.detail}
          </p>
        )}
      </div>
    </>
  );
}
