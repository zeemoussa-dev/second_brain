import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { ApiError } from '../../api/client';
import { Field } from './Field';
import {
  fetchMarketplace, preflightPlugin, installPlugin, uninstallPlugin,
  preflightSource, installFromSource, updatePlugin,
  type MarketplacePlugin, type MarketplacePreflight, type MarketplaceSourcePreflight,
  type PluginSource, type PluginSourceRequest,
} from './marketplaceApiClient';

// Settings > Marketplace (ADR-022). Mirrors the Blueprints card: a version is
// always checked before install is offered, so the operator sees what would
// happen -- and what would stop it -- before anything changes on disk.

function problemsFrom(error: unknown): string[] {
  // A refused install is a 409 whose body is {"detail": {..., "problems": [...]}};
  // a refused uninstall (a piece held open, BUG-065) carries {"detail": {..., "reason": "..."}}.
  if (error instanceof ApiError) {
    try {
      const body = JSON.parse(error.message);
      if (Array.isArray(body?.detail?.problems)) return body.detail.problems;
      if (typeof body?.detail?.reason === 'string') return [body.detail.reason];
      if (typeof body?.detail === 'string') return [body.detail];
    } catch {
      // Not JSON: fall through to the raw message.
    }
    return [error.message];
  }
  return [String(error)];
}

interface Outcome {
  pluginId: string;
  message: string;
  restartRequired: boolean;
}

const EMPTY_SOURCE: PluginSourceRequest = { kind: 'git', location: '', ref: '' };

/** "github.com/me/sb-plugins-x @ main", or the folder, with the commit when known. */
function describeSource(source: PluginSource): string {
  const where = source.kind === 'git' ? source.location.replace(/^https?:\/\//, '') : source.location;
  const ref = source.ref ? ` @ ${source.ref}` : '';
  const commit = source.commit ? ` (${source.commit.slice(0, 7)})` : '';
  return `${where}${ref}${commit}`;
}

export function MarketplaceCard() {
  const [plugins, setPlugins] = useState<MarketplacePlugin[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [open, setOpen] = useState<{ pluginId: string; version: string } | null>(null);
  const [check, setCheck] = useState<MarketplacePreflight | null>(null);
  const [problems, setProblems] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [source, setSource] = useState<PluginSourceRequest>(EMPTY_SOURCE);
  const [sourceCheck, setSourceCheck] = useState<MarketplaceSourcePreflight | null>(null);
  const [sourceProblems, setSourceProblems] = useState<string[]>([]);

  function reload() {
    return fetchMarketplace().then(setPlugins).catch((e) => setLoadError(String(e)));
  }

  useEffect(() => {
    reload();
  }, []);

  async function runCheck(pluginId: string, version: string) {
    setOpen({ pluginId, version });
    setCheck(null);
    setProblems([]);
    setOutcome(null);
    try {
      setCheck(await preflightPlugin(pluginId, version));
    } catch (e) {
      setProblems(problemsFrom(e));
    }
  }

  async function install(pluginId: string, version: string) {
    setBusy(true);
    setProblems([]);
    try {
      const result = await installPlugin(pluginId, version);
      setOutcome({
        pluginId,
        message: result.replaced
          ? `Replaced ${result.replaced} with ${version}.`
          : `Installed ${version}.`,
        restartRequired: Boolean(result.restart_required),
      });
      setCheck(null);
      await reload();
    } catch (e) {
      setProblems(problemsFrom(e));
    } finally {
      setBusy(false);
    }
  }

  function sourceRequest(): PluginSourceRequest {
    return { kind: source.kind, location: source.location.trim(), ref: source.ref?.trim() || null };
  }

  async function checkSource() {
    setBusy(true);
    setSourceProblems([]);
    setSourceCheck(null);
    setOutcome(null);
    try {
      setSourceCheck(await preflightSource(sourceRequest()));
    } catch (e) {
      setSourceProblems(problemsFrom(e));
    } finally {
      setBusy(false);
    }
  }

  async function installSource() {
    setBusy(true);
    setSourceProblems([]);
    try {
      const result = await installFromSource(sourceRequest());
      setOutcome({
        pluginId: result.plugin_id,
        message: result.replaced
          ? `Replaced ${result.replaced} with ${result.version} from ${describeSource(result.source!)}.`
          : `Installed ${result.plugin_id} ${result.version} from ${describeSource(result.source!)}.`,
        restartRequired: Boolean(result.restart_required),
      });
      setSourceCheck(null);
      setSource(EMPTY_SOURCE);
      await reload();
    } catch (e) {
      setSourceProblems(problemsFrom(e));
    } finally {
      setBusy(false);
    }
  }

  async function update(pluginId: string) {
    setBusy(true);
    setProblems([]);
    try {
      const result = await updatePlugin(pluginId);
      setOutcome({
        pluginId,
        message: `Updated to ${result.version} from ${describeSource(result.source!)}.`,
        restartRequired: Boolean(result.restart_required),
      });
      await reload();
    } catch (e) {
      setProblems(problemsFrom(e));
    } finally {
      setBusy(false);
    }
  }

  async function uninstall(pluginId: string) {
    if (!window.confirm(`Uninstall ${pluginId}? Notes it wrote into your vault stay where they are.`)) return;
    setBusy(true);
    setProblems([]);
    try {
      const result = await uninstallPlugin(pluginId);
      const refused = result.refused_outside_plugin_folders ?? [];
      setOutcome({
        pluginId,
        message: refused.length
          ? `Uninstalled, but these recorded paths were outside the plugin folders and were NOT deleted: ${refused.join(', ')}`
          : 'Uninstalled.',
        restartRequired: Boolean(result.restart_required),
      });
      setOpen(null);
      setCheck(null);
      await reload();
    } catch (e) {
      setProblems(problemsFrom(e));
    } finally {
      setBusy(false);
    }
  }

  if (loadError && !plugins) return <p className="error-text">{loadError}</p>;
  if (!plugins) return <p className="text-muted">Loading the Marketplace…</p>;
  if (plugins.length === 0) return <p className="text-muted">No plugins are published in this Marketplace yet.</p>;

  return (
    <div className="card">
      {plugins.map((plugin) => {
        const newest = plugin.packages.find((p) => !p.error) ?? plugin.packages[0];
        return (
          <div key={plugin.id} className="blueprint-row">
            <div className="blueprint-head">
              <span className="material-symbols-outlined" aria-hidden="true">extension</span>
              <div>
                <strong>{newest?.name ?? plugin.id}</strong>{' '}
                {plugin.installed_version ? (
                  <span className="badge badge-success">installed {plugin.installed_version}</span>
                ) : (
                  <span className="badge">not installed</span>
                )}
                {newest?.description && <p className="text-muted">{newest.description}</p>}
                {plugin.installed_version && plugin.source && (
                  <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
                    from {describeSource(plugin.source)}
                  </p>
                )}
              </div>
              {plugin.installed_version && plugin.source && (
                <button type="button" className="btn" disabled={busy} onClick={() => update(plugin.id)}>
                  {busy ? 'Working…' : 'Update'}
                </button>
              )}
              {plugin.installed_version && (
                <button type="button" className="btn" disabled={busy} onClick={() => uninstall(plugin.id)}>
                  Uninstall
                </button>
              )}
            </div>

            <ul className="blueprint-agents">
              {plugin.packages.map((pkg) => (
                <li key={pkg.version}>
                  <strong>{pkg.version}</strong>{' '}
                  {pkg.error ? (
                    <span className="error-text">{pkg.error}</span>
                  ) : (
                    <>
                      {pkg.compatible
                        ? <span className="badge badge-success">compatible</span>
                        : <span className="badge badge-warning">framework API {String(pkg.framework_api)}</span>}
                      {pkg.requires && pkg.requires.length > 0 && (
                        <span className="text-muted"> — requires {pkg.requires.join(', ')}</span>
                      )}{' '}
                      <button
                        type="button"
                        className="btn"
                        disabled={busy || plugin.installed_version === pkg.version}
                        onClick={() => runCheck(plugin.id, pkg.version)}
                      >
                        {plugin.installed_version === pkg.version ? 'Installed' : 'Check'}
                      </button>
                    </>
                  )}
                </li>
              ))}
            </ul>

            {open?.pluginId === plugin.id && check && (
              <div className="blueprint-preflight">
                {check.ok ? (
                  <p className="text-muted">
                    Ready to install {check.version}
                    {check.replaces ? `, replacing the installed ${check.replaces}` : ''}.
                    {check.templates && check.templates.install.length > 0 && (
                      <> Adds Templates: {check.templates.install.join(', ')}.</>
                    )}
                    {check.templates && check.templates.keep.length > 0 && (
                      <> Keeps the existing {check.templates.keep.join(', ')} as they are.</>
                    )}
                  </p>
                ) : (
                  <>
                    <p><strong>Cannot install:</strong></p>
                    <ul className="blueprint-problems">
                      {check.problems.map((problem) => <li key={problem}>{problem}</li>)}
                    </ul>
                  </>
                )}
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={!check.ok || busy}
                  onClick={() => install(plugin.id, check.version)}
                >
                  {busy ? 'Working…' : check.replaces ? `Replace ${check.replaces}` : 'Install'}
                </button>
              </div>
            )}

            {open?.pluginId === plugin.id && problems.length > 0 && (
              <ul className="blueprint-problems">
                {problems.map((problem) => <li key={problem} className="error-text">{problem}</li>)}
              </ul>
            )}

            {outcome?.pluginId === plugin.id && (
              <div className="blueprint-result">
                <p><strong>{outcome.message}</strong></p>
                {outcome.restartRequired && (
                  // A plugin's backend is loaded at startup; its screens are picked
                  // up by the frontend straight away.
                  <p className="error-text">
                    Restart the backend for this to take full effect — use Shut down on{' '}
                    <Link to="/settings/system">Settings → System</Link>, then start it again.
                  </p>
                )}
              </div>
            )}
          </div>
        );
      })}

      <div className="blueprint-row" data-role="install-from-source">
        <div className="blueprint-head">
          <span className="material-symbols-outlined" aria-hidden="true">cloud_download</span>
          <div>
            <strong>Install from a repository</strong>
            <p className="text-muted">
              A plugin lives in its own repository. Install it straight from there — it never has to be
              published into this framework. The same checks run either way, and what is installed remembers
              where it came from, so Update pulls that repository again.
            </p>
          </div>
        </div>

        <div className="item-row-actions" style={{ flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <Field label="Source">
            <select
              className="input"
              style={{ width: 'auto' }}
              value={source.kind}
              onChange={(event) => setSource((prev) => ({ ...prev, kind: event.target.value as 'git' | 'path' }))}
            >
              <option value="git">Git repository</option>
              <option value="path">Folder on this machine</option>
            </select>
          </Field>
          <Field label={source.kind === 'git' ? 'Repository URL' : 'Folder path'}>
            <input
              className="input"
              style={{ minWidth: '22rem' }}
              value={source.location}
              placeholder={source.kind === 'git' ? 'https://github.com/you/sb-plugins-example' : 'C:\\path\\to\\plugin'}
              onChange={(event) => setSource((prev) => ({ ...prev, location: event.target.value }))}
            />
          </Field>
          {source.kind === 'git' && (
            <Field label="Branch, tag or commit">
              <input
                className="input"
                value={source.ref ?? ''}
                placeholder="main"
                onChange={(event) => setSource((prev) => ({ ...prev, ref: event.target.value }))}
              />
            </Field>
          )}
          <button type="button" className="btn" disabled={busy || !source.location.trim()} onClick={checkSource}>
            {busy ? 'Working…' : 'Check'}
          </button>
        </div>

        {sourceCheck && (
          <div className="blueprint-preflight">
            {sourceCheck.ok ? (
              <p className="text-muted">
                Ready to install {sourceCheck.plugin_id} {sourceCheck.version} from {describeSource(sourceCheck.source)}
                {sourceCheck.replaces ? `, replacing the installed ${sourceCheck.replaces}` : ''}.
                {sourceCheck.templates && sourceCheck.templates.install.length > 0 && (
                  <> Adds Templates: {sourceCheck.templates.install.join(', ')}.</>
                )}
                {sourceCheck.templates && sourceCheck.templates.keep.length > 0 && (
                  <> Keeps the existing {sourceCheck.templates.keep.join(', ')} as they are.</>
                )}
              </p>
            ) : (
              <>
                <p><strong>Cannot install:</strong></p>
                <ul className="blueprint-problems">
                  {sourceCheck.problems.map((problem) => <li key={problem}>{problem}</li>)}
                </ul>
              </>
            )}
            <button
              type="button"
              className="btn btn-primary"
              disabled={!sourceCheck.ok || busy}
              onClick={installSource}
            >
              {busy ? 'Working…' : sourceCheck.replaces ? `Replace ${sourceCheck.replaces}` : 'Install'}
            </button>
          </div>
        )}

        {sourceProblems.length > 0 && (
          <ul className="blueprint-problems">
            {sourceProblems.map((problem) => <li key={problem} className="error-text">{problem}</li>)}
          </ul>
        )}
      </div>
    </div>
  );
}
