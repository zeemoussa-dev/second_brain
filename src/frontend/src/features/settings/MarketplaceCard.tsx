import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { ApiError } from '../../api/client';
import {
  fetchMarketplace, preflightPlugin, installPlugin, uninstallPlugin,
  type MarketplacePlugin, type MarketplacePreflight,
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

export function MarketplaceCard() {
  const [plugins, setPlugins] = useState<MarketplacePlugin[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [open, setOpen] = useState<{ pluginId: string; version: string } | null>(null);
  const [check, setCheck] = useState<MarketplacePreflight | null>(null);
  const [problems, setProblems] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [outcome, setOutcome] = useState<Outcome | null>(null);

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
              </div>
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
    </div>
  );
}
