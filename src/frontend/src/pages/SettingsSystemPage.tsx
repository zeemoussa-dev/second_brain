import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import {
  fetchSystemSettings,
  shutdownSystem,
  testSystemField,
  updateSystemSettings,
  type SystemSettingField,
} from '../features/settings/settingsApiClient';

export function SettingsSystemPage() {
  const [fields, setFields] = useState<SystemSettingField[] | null>(null);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [testing, setTesting] = useState<Record<string, boolean>>({});
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [restartRequired, setRestartRequired] = useState(false);
  const [saving, setSaving] = useState(false);
  const [shuttingDown, setShuttingDown] = useState(false);

  function reload() {
    fetchSystemSettings().then((result) => {
      setFields(result.fields);
      setDrafts(Object.fromEntries(result.fields.map((field) => [field.key, field.value])));
    });
  }

  useEffect(() => {
    reload();
  }, []);

  const dirty = fields?.some((field) => drafts[field.key] !== field.value) ?? false;

  async function handleTest(key: string) {
    setTesting((prev) => ({ ...prev, [key]: true }));
    const status = await testSystemField(key);
    setFields((prev) => prev?.map((field) => (field.key === key ? { ...field, status } : field)) ?? null);
    setTesting((prev) => ({ ...prev, [key]: false }));
  }

  async function handleSave() {
    if (!fields) return;
    setSaving(true);
    setSaveMessage(null);
    const patch = Object.fromEntries(
      fields.filter((field) => drafts[field.key] !== field.value).map((field) => [field.key, drafts[field.key]]),
    );
    const result = await updateSystemSettings(patch);
    setSaving(false);
    if (!result.ok) {
      setSaveMessage(result.message);
      return;
    }
    setRestartRequired(true);
    setSaveMessage('Saved. Restart the backend for these changes to take effect.');
    reload();
  }

  async function handleShutdown() {
    if (!window.confirm('Shut down the Second Brain backend now? You will need to restart it yourself.')) {
      return;
    }
    setShuttingDown(true);
    await shutdownSystem();
  }

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <h1>System</h1>
      <p className="text-muted">Core, system-wide configuration — where Second Brain looks for Hermes, your vault, and its own data.</p>

      {fields && (
        <div className="item-list" style={{ marginBottom: 'var(--space-4)' }}>
          {fields.map((field) => (
            <div className="item-row" key={field.key} data-system-field={field.key}>
              <span className="material-symbols-outlined settings-card-icon" aria-hidden="true">
                {field.icon}
              </span>
              <div className="item-row-main" style={{ flex: 1 }}>
                <span className="item-row-title">
                  {field.label}{' '}
                  <span className={`badge ${field.status.ok ? 'badge-success' : 'badge-danger'}`}>
                    {field.status.detail}
                  </span>
                </span>
                <span className="item-row-meta">{field.description}</span>
                <input
                  className="input"
                  value={drafts[field.key] ?? ''}
                  onChange={(event) => setDrafts((prev) => ({ ...prev, [field.key]: event.target.value }))}
                />
              </div>
              <div className="item-row-actions">
                <button type="button" className="btn" disabled={testing[field.key]} onClick={() => handleTest(field.key)}>
                  {testing[field.key] ? 'Testing…' : 'Test'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {saveMessage && <p className="text-muted">{saveMessage}</p>}
      <button type="button" className="btn btn-primary" disabled={!dirty || saving} onClick={handleSave}>
        {saving ? 'Saving…' : 'Save changes'}
      </button>

      <div className="card" style={{ marginTop: 'var(--space-6)' }}>
        <h2>Shut down</h2>
        <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
          Gracefully stops the backend process{restartRequired ? ' — needed to apply your saved changes' : ''}.
          You restart it yourself afterward.
        </p>
        <button type="button" className="btn btn-danger" disabled={shuttingDown} onClick={handleShutdown}>
          <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: '16px', verticalAlign: 'middle', marginRight: '4px' }}>
            power_settings_new
          </span>
          {shuttingDown ? 'Shutting down…' : 'Shut down backend'}
        </button>
      </div>
    </>
  );
}
