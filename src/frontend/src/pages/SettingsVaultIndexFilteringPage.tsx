import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { VaultSettingsNav } from '../features/settings/VaultSettingsNav';
import {
  fetchIndexConfig,
  setFolderIncluded,
  type IndexConfigFolder,
} from '../features/settings/vaultApiClient';

export function SettingsVaultIndexFilteringPage() {
  const [folders, setFolders] = useState<IndexConfigFolder[] | null>(null);
  const [saving, setSaving] = useState<Record<string, boolean>>({});

  function reload() {
    fetchIndexConfig().then((result) => setFolders(result.folders));
  }

  useEffect(() => {
    reload();
  }, []);

  async function handleToggle(folder: IndexConfigFolder) {
    setSaving((prev) => ({ ...prev, [folder.name]: true }));
    await setFolderIncluded(folder.name, !folder.included);
    setSaving((prev) => ({ ...prev, [folder.name]: false }));
    reload();
  }

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <h1>Vault</h1>
      <div className="vault-settings-layout">
        <VaultSettingsNav />
        <div className="vault-settings-content">
          <h2>Index Filtering</h2>
          <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
            Which top-level vault folders the agent-facing index actually covers. A folder left on is walked every
            rebuild; turning one off skips it entirely — useful for a noisy or irrelevant folder you don't want
            agents searching. This only controls the index Hermes agents read, not the vault itself.
          </p>
          {folders && (
            <div className="item-list">
              {folders.map((folder) => (
                <div className="item-row" key={folder.name} data-index-folder-row={folder.name}>
                  <div className="item-row-main">
                    <span className="item-row-title">{folder.name}</span>
                    <span className="item-row-meta">
                      {folder.included ? 'Included in the agent index' : 'Excluded from the agent index'}
                    </span>
                  </div>
                  <div className="item-row-actions">
                    <button
                      type="button"
                      className={folder.included ? 'btn' : 'btn btn-primary'}
                      disabled={saving[folder.name]}
                      onClick={() => handleToggle(folder)}
                    >
                      {folder.included ? 'Exclude' : 'Include'}
                    </button>
                  </div>
                </div>
              ))}
              {folders.length === 0 && <p className="text-muted">No folders found yet.</p>}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
