import { useEffect, useState } from 'react';
import {
  fetchSystemHealth,
  type SystemHealthResponse,
} from '../features/system-health/client';
import { fetchHermesStatus, type HermesServerStatus } from '../features/hermes-ops/client';

function formatDuration(seconds: number | null): string {
  if (seconds === null) return 'an unknown duration';
  const totalSeconds = Math.round(seconds);
  if (totalSeconds < 60) return `${totalSeconds}s`;
  const minutes = Math.floor(totalSeconds / 60);
  const remainingSeconds = totalSeconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

function AppStatusTab({ health, onRefresh }: { health: SystemHealthResponse; onRefresh: () => void }) {
  const hasIssues = !health.mcp.reachable || health.disabled_agents.length > 0;

  return (
    <>
      <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
        <button
          type="button"
          className="btn"
          style={{
            padding: 'var(--space-1) var(--space-3)',
            fontSize: 'var(--font-size-sm)',
            marginRight: 'var(--space-2)',
          }}
          onClick={onRefresh}
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

      <h2 style={{ marginTop: 'var(--space-6)' }}>Scheduling</h2>
      <p
        className="text-muted"
        style={{ fontSize: 'var(--font-size-sm)', marginTop: 'calc(-1 * var(--space-2))' }}
      >
        The three capture-style jobs that can otherwise freeze the app while
        running — whether each is currently running, how long its current or
        most recent run took, and its last real outcome.
      </p>
      <div className="card">
        <div className="item-list">
          {health.scheduling.map((job) => (
            <div className="item-row" key={`${job.agent_id}::${job.capability_id}`}>
              <div className="item-row-main">
                <span className="item-row-title">
                  <span className="mono">{job.agent_id}</span>{' '}
                  {!job.has_run ? (
                    <span className="badge">No runs yet</span>
                  ) : job.running ? (
                    <span className="badge badge-warning">Running</span>
                  ) : job.last_outcome === 'success' ? (
                    <span className="badge badge-success">Success</span>
                  ) : job.last_outcome === 'error' ? (
                    <span className="badge badge-danger">Failed</span>
                  ) : job.last_outcome === 'skipped' ? (
                    <span className="badge badge-warning">Skipped</span>
                  ) : (
                    <span className="badge">Unknown</span>
                  )}
                </span>
                <span className="item-row-meta">
                  {!job.has_run
                    ? 'Not dispatched yet (manually or on a schedule) since run-state tracking was introduced.'
                    : job.running
                      ? `Running for ${formatDuration(job.elapsed_seconds)} so far.`
                      : job.last_outcome === 'error'
                        ? `Last run failed after ${formatDuration(job.last_duration_seconds)}: ${job.last_error_message}`
                        : job.last_outcome === 'skipped'
                          ? 'Last run was skipped — another run was already in progress.'
                          : `Last run took ${formatDuration(job.last_duration_seconds)} — completed successfully.`}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

function HermesStatusTab({ status, onRefresh }: { status: HermesServerStatus; onRefresh: () => void }) {
  return (
    <div className="card">
      <h2>Hermes Server Status</h2>
      <div className="kv-list">
        <div className="kv-row">
          <span className="kv-key">Gateway</span>
          <span className={`badge ${status.reachable ? 'badge-success' : 'badge-danger'}`}>
            {status.reachable ? 'Reachable' : 'Unreachable'}
          </span>
        </div>
        {!status.reachable && status.error && (
          <div className="kv-row">
            <span className="kv-key">Error</span>
            <span className="mono" style={{ fontSize: 'var(--font-size-sm)' }}>{status.error}</span>
          </div>
        )}
        {status.reachable &&
          Object.entries(status)
            .filter(([key]) => key !== 'reachable' && typeof status[key] !== 'object')
            .map(([key, value]) => (
              <div className="kv-row" key={key}>
                <span className="kv-key">{key}</span>
                <span className="mono">{String(value)}</span>
              </div>
            ))}
      </div>
      <button type="button" className="btn" style={{ marginTop: 'var(--space-2)' }} onClick={onRefresh}>
        &#8635; Refresh
      </button>
    </div>
  );
}

const TABS = ['app', 'hermes'] as const;
type Tab = (typeof TABS)[number];
const TAB_LABELS: Record<Tab, string> = { app: 'App Status', hermes: 'Hermes Status' };

export function SystemHealthPage() {
  const [activeTab, setActiveTab] = useState<Tab>('app');
  const [health, setHealth] = useState<SystemHealthResponse | null>(null);
  const [hermesStatus, setHermesStatus] = useState<HermesServerStatus | null>(null);

  const loadHealth = () => {
    fetchSystemHealth().then(setHealth);
  };
  const loadHermesStatus = () => {
    fetchHermesStatus().then(setHermesStatus);
  };

  useEffect(loadHealth, []);
  useEffect(loadHermesStatus, []);

  return (
    <>
      <h1>System Health</h1>
      <p className="text-muted">
        Whether Second Brain's own moving pieces are genuinely working — not
        just "the process is up" — so a real failure is visible at a glance
        instead of discovered by symptom-chasing through individual features
        or digging through raw server logs (REQ-SB-31).
      </p>

      <div className="page-tabs" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            role="tab"
            aria-selected={activeTab === tab}
            className={`page-tab${activeTab === tab ? ' page-tab--active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {TAB_LABELS[tab]}
          </button>
        ))}
      </div>

      {activeTab === 'app' &&
        (health ? <AppStatusTab health={health} onRefresh={loadHealth} /> : <p className="text-muted">Loading...</p>)}
      {activeTab === 'hermes' &&
        (hermesStatus ? (
          <HermesStatusTab status={hermesStatus} onRefresh={loadHermesStatus} />
        ) : (
          <p className="text-muted">Loading...</p>
        ))}
    </>
  );
}
