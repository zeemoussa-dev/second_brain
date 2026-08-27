import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { VaultSettingsNav } from '../features/settings/VaultSettingsNav';
import { fetchVaultOverview, rebuildVaultIndex, type VaultOverview } from '../features/settings/vaultApiClient';

export function SettingsVaultPage() {
  const [overview, setOverview] = useState<VaultOverview | null>(null);
  const [rebuilding, setRebuilding] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  function reload() {
    fetchVaultOverview().then(setOverview);
  }

  useEffect(() => {
    reload();
  }, []);

  async function handleRebuild() {
    setRebuilding(true);
    setMessage(null);
    const result = await rebuildVaultIndex();
    setRebuilding(false);
    setMessage(
      result.agent_index_rebuild_triggered
        ? 'Backend index rebuilt now; the agent-facing index is rebuilding in the background (also runs every 30 minutes on its own).'
        : 'Backend index rebuilt.',
    );
    reload();
  }

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <h1>Vault</h1>
      <div className="vault-settings-layout">
        <VaultSettingsNav />
        <div className="vault-settings-content">
          <h2>Overview</h2>
          {overview && (
            <>
              <div className="kv-list" style={{ marginBottom: 'var(--space-4)' }}>
                <div className="kv-row"><span className="kv-key">Total notes indexed</span><span>{overview.total_notes}</span></div>
                <div className="kv-row"><span className="kv-key">Last rebuilt</span><span>{overview.last_rebuilt_at ?? 'Never'}</span></div>
              </div>
              <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)', textTransform: 'uppercase' }}>Notes per folder</p>
              <div className="kv-list" style={{ marginBottom: 'var(--space-4)' }}>
                {Object.entries(overview.folder_counts).map(([folder, count]) => (
                  <div className="kv-row" key={folder}><span className="kv-key">{folder}</span><span>{count}</span></div>
                ))}
              </div>
            </>
          )}
          <button type="button" className="btn btn-primary" disabled={rebuilding} onClick={handleRebuild}>
            {rebuilding ? 'Rebuilding…' : 'Rebuild index'}
          </button>
          {message && <p className="text-muted" style={{ marginTop: 'var(--space-2)' }}>{message}</p>}
        </div>
      </div>
    </>
  );
}
