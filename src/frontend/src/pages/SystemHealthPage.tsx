import { useEffect, useState } from 'react';
import {
  fetchSystemHealth,
  type SystemHealthResponse,
} from '../features/system-health/client';
import { fetchHermesStatus, type HermesServerStatus } from '../features/hermes-ops/client';

function AppStatusTab({ health, onRefresh }: { health: SystemHealthResponse; onRefresh: () => void }) {
  const hasIssues = health.disabled_agents.length > 0;

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
              Every agent's selected Provider has a real client configured.
            </p>
          </div>
        )}
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
