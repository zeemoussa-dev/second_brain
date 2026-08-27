import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { VaultSettingsNav } from '../features/settings/VaultSettingsNav';
import { fetchVaultTemplates, type VaultTemplate } from '../features/settings/vaultApiClient';

export function SettingsVaultTemplatesPage() {
  const [templates, setTemplates] = useState<VaultTemplate[] | null>(null);

  useEffect(() => {
    fetchVaultTemplates().then((result) => setTemplates(result.templates));
  }, []);

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <h1>Vault</h1>
      <div className="vault-settings-layout">
        <VaultSettingsNav />
        <div className="vault-settings-content">
          <h2>Templates</h2>
          <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
            Read-only — the Template.json files that control how each kind of note gets written.
          </p>
          {templates && (
            <div className="item-list">
              {templates.map((template) => (
                <div className="item-row" key={template.id}>
                  <div className="item-row-main">
                    <span className="item-row-title">{template.id}</span>
                    {template.error ? (
                      <span className="item-row-meta">Error: {template.error}</span>
                    ) : (
                      <>
                        <span className="item-row-meta">note_name: {template.note_name ?? '—'}</span>
                        <span className="item-row-meta">
                          on_missing: {template.on_missing} · on_existing_title: {template.on_existing_title}
                        </span>
                        <span className="item-row-meta">
                          sections: {template.sections.map((section) => `${section.name} (${section.access})`).join(', ') || '—'}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              ))}
              {templates.length === 0 && <p className="text-muted">No templates found.</p>}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
