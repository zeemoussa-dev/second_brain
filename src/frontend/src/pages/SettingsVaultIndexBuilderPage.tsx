import { Link } from 'react-router';
import { VaultSettingsNav } from '../features/settings/VaultSettingsNav';

export function SettingsVaultIndexBuilderPage() {
  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <h1>Vault</h1>
      <div className="vault-settings-layout">
        <VaultSettingsNav />
        <div className="vault-settings-content">
          <h2>Index Builder</h2>
          <div className="card">
            <p className="text-muted">
              Still being designed — an option to build an index.md for the vault and per-section. Not built yet.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
