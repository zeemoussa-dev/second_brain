import { useEffect, useState } from 'react';
import {
  createProvider,
  fetchProviders,
  removeProvider,
  updateProvider,
  type ProviderFormFields,
  type ProviderSummary,
} from './settingsApiClient';

const EMPTY_FORM: ProviderFormFields = { name: '', endpoint: '', credential: '', model: '' };

export function ProvidersCard() {
  const [providers, setProviders] = useState<ProviderSummary[] | null>(null);
  const [newProvider, setNewProvider] = useState<ProviderFormFields>(EMPTY_FORM);
  const [editDrafts, setEditDrafts] = useState<Record<string, ProviderFormFields>>({});
  const [blockedMessage, setBlockedMessage] = useState<string | null>(null);

  function reload() {
    fetchProviders().then((list) => {
      setProviders(list);
      setEditDrafts(
        Object.fromEntries(
          list.map((p) => [p.id, { name: p.name, endpoint: p.endpoint, credential: '', model: p.model }]),
        ),
      );
    });
  }

  useEffect(() => {
    reload();
  }, []);

  async function handleAdd(event: React.FormEvent) {
    event.preventDefault();
    const { name, endpoint, credential, model } = newProvider;
    if (!name || !endpoint || !credential || !model) return;
    await createProvider(newProvider);
    setNewProvider(EMPTY_FORM);
    reload();
  }

  async function handleEdit(providerId: string) {
    const draft = editDrafts[providerId];
    // An empty credential draft leaves the stored value untouched — PATCH
    // omits the field entirely rather than sending an empty string.
    const fields: Partial<ProviderFormFields> = {
      name: draft.name,
      endpoint: draft.endpoint,
      model: draft.model,
    };
    if (draft.credential) fields.credential = draft.credential;
    await updateProvider(providerId, fields);
    reload();
  }

  async function handleRemove(providerId: string) {
    setBlockedMessage(null);
    const result = await removeProvider(providerId);
    if (!result.ok) {
      setBlockedMessage(result.message);
      return;
    }
    reload();
  }

  function updateDraft(providerId: string, patch: Partial<ProviderFormFields>) {
    setEditDrafts((prev) => ({ ...prev, [providerId]: { ...prev[providerId], ...patch } }));
  }

  return (
    <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
      <h2>Providers</h2>
      <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
        LLM Providers agents can be pointed at. Compass is pre-seeded and
        remains every agent's default until explicitly changed. Editing the
        Compass entry here does not change your live Compass connection —
        it stays configured via <span className="mono">.env</span>.
      </p>
      {blockedMessage && (
        <p className="text-muted" data-testid="providers-blocked-message">
          <span className="badge badge-danger">Removal blocked</span> {blockedMessage}
        </p>
      )}
      {providers && (
        <div className="item-list" style={{ marginBottom: 'var(--space-4)' }}>
          {providers.map((provider) => {
            const blocked = provider.agent_ids.length > 0;
            const draft = editDrafts[provider.id];
            return (
              <div className="item-row" key={provider.id} data-provider-row={provider.id}>
                <div className="item-row-main">
                  <span className="item-row-title">
                    {provider.name}{' '}
                    {provider.is_default && <span className="badge">Default</span>}
                    {!provider.has_real_client && (
                      <span className="badge badge-warning">No client built yet</span>
                    )}
                  </span>
                  <span className="item-row-meta">
                    Endpoint: <span className="mono">{provider.endpoint}</span> · Model: {provider.model}
                  </span>
                  <span className="item-row-meta">Used by {provider.agent_ids.length} agent(s)</span>
                </div>
                <div className="item-row-actions">
                  <input
                    className="input"
                    value={draft?.name ?? ''}
                    onChange={(event) => updateDraft(provider.id, { name: event.target.value })}
                  />
                  <input
                    className="input"
                    value={draft?.endpoint ?? ''}
                    onChange={(event) => updateDraft(provider.id, { endpoint: event.target.value })}
                  />
                  <input
                    className="input"
                    type="password"
                    placeholder={provider.credential_set ? '••••••••••••' : 'Never stored in plaintext'}
                    value={draft?.credential ?? ''}
                    onChange={(event) => updateDraft(provider.id, { credential: event.target.value })}
                  />
                  <input
                    className="input"
                    value={draft?.model ?? ''}
                    onChange={(event) => updateDraft(provider.id, { model: event.target.value })}
                  />
                  <button type="button" className="btn" onClick={() => handleEdit(provider.id)}>Save</button>
                  <button
                    type="button"
                    className="btn btn-danger"
                    disabled={blocked}
                    title={blocked ? 'Switch every agent using it to a different Provider first' : undefined}
                    onClick={() => handleRemove(provider.id)}
                  >
                    Remove
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
      <form onSubmit={handleAdd} className="item-row-actions">
        <input className="input" placeholder="Name" value={newProvider.name} onChange={(e) => setNewProvider((p) => ({ ...p, name: e.target.value }))} />
        <input className="input" placeholder="Endpoint" value={newProvider.endpoint} onChange={(e) => setNewProvider((p) => ({ ...p, endpoint: e.target.value }))} />
        <input className="input" type="password" placeholder="Credential" value={newProvider.credential} onChange={(e) => setNewProvider((p) => ({ ...p, credential: e.target.value }))} />
        <input className="input" placeholder="Model" value={newProvider.model} onChange={(e) => setNewProvider((p) => ({ ...p, model: e.target.value }))} />
        <button type="submit" className="btn btn-primary">Add provider</button>
      </form>
    </div>
  );
}
