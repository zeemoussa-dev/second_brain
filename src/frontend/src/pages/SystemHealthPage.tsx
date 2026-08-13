import { useEffect, useState } from 'react';
import {
  fetchSystemHealth,
  type SystemHealthResponse,
} from '../features/system-health/client';

export function SystemHealthPage() {
  const [health, setHealth] = useState<SystemHealthResponse | null>(null);

  const load = () => {
    fetchSystemHealth().then(setHealth);
  };

  useEffect(load, []);

  if (!health) {
    return (
      <>
        <h1>System Health</h1>
        <p className="text-muted">Loading...</p>
      </>
    );
  }

  const hasIssues = !health.mcp.reachable || health.disabled_agents.length > 0;

  return (
    <>
      <h1>System Health</h1>
      <p className="text-muted">
        Whether Second Brain's own moving pieces are genuinely working — not
        just "the process is up" — so a real failure is visible at a glance
        instead of discovered by symptom-chasing through individual features
        or digging through raw server logs (REQ-SB-31).
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
        Every check below recomputes fresh on open or refresh — never a
        cached snapshot from an earlier page load.
      </p>

      <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
        <h2>Health Issues</h2>
        {hasIssues ? (
          <div className="item-list">
            {!health.mcp.reachable && (
              <div className="item-row">
                <div className="item-row-main">
                  <span className="item-row-title">
                    MCP / Agent-orchestration path{' '}
                    <span className="badge badge-danger">Unreachable</span>
                  </span>
                  <span className="item-row-meta">
                    GET /mcp did not respond with its expected "alive" signal
                    (HTTP 406) — no response, or an unexpected response.
                  </span>
                </div>
              </div>
            )}
            {health.disabled_agents.map((agent) => (
              <div className="item-row" key={agent.agent_id}>
                <div className="item-row-main">
                  <span className="item-row-title">
                    {agent.agent_name} <span className="badge badge-danger">Disabled</span>
                  </span>
                  <span className="item-row-meta">
                    Selected Provider ({agent.provider_name ?? 'none'}) has no
                    real client configured yet.
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-state-icon">&#10003;</div>
            <p style={{ margin: 0, fontWeight: 600, color: 'var(--color-text)' }}>
              No Health Issues
            </p>
            <p style={{ margin: 'var(--space-1) 0 0' }}>
              MCP/agent-orchestration is reachable and every agent's selected
              Provider has a real client configured.
            </p>
          </div>
        )}
      </div>

      <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
        <h2>MCP / Agent-orchestration path</h2>
        <div className="kv-list">
          <div className="kv-row">
            <span className="kv-key">Mount</span>
            <span className="mono">GET /mcp</span>
          </div>
          <div className="kv-row">
            <span className="kv-key">Status</span>
            <span className={`badge ${health.mcp.reachable ? 'badge-success' : 'badge-danger'}`}>
              {health.mcp.reachable ? 'Reachable' : 'Unreachable'}
            </span>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
        <h2>Providers</h2>
        <p
          className="text-muted"
          style={{ fontSize: 'var(--font-size-sm)', marginTop: 'calc(-1 * var(--space-3))' }}
        >
          Rolled up per distinct Provider, from each agent's own selection.
          "Available" means a real client is configured for it — not that it
          has been verified reachable right now.
        </p>
        <div className="item-list">
          {health.providers.map((provider) => (
            <div className="item-row" key={provider.id}>
              <div className="item-row-main">
                <span className="item-row-title">
                  {provider.name}{' '}
                  {provider.has_real_client ? (
                    <span className="badge badge-success">Available</span>
                  ) : (
                    <span className="badge badge-warning">No client built yet</span>
                  )}
                </span>
                <span className="item-row-meta">
                  {provider.agent_names.length > 0
                    ? `Selected by ${provider.agent_names.length} agent(s) (${provider.agent_names.join(', ')})`
                    : 'Not currently selected by any agent'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <h2 style={{ marginTop: 'var(--space-6)' }}>Last capture run</h2>
      <div className="card">
        {health.last_capture_run ? (
          <div className="kv-list">
            <div className="kv-row">
              <span className="kv-key">Last completed</span>
              <span className="mono">{health.last_capture_run.finished_at}</span>
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <p style={{ margin: 0, fontWeight: 600, color: 'var(--color-text)' }}>
              No capture run has completed yet
            </p>
            <p style={{ margin: 'var(--space-1) 0 0' }}>
              <span className="mono">last_capture_run.json</span> does not
              exist yet — shown honestly, not fabricated as a timestamp or a
              misleadingly healthy-looking default.
            </p>
          </div>
        )}
      </div>
    </>
  );
}
