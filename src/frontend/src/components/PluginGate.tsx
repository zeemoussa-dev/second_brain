// A refused plugin says so, instead of rendering and then failing (BUG-088).
//
// Wrapped around every plugin screen by the host registry, so a plugin cannot
// forget to do it and a plugin author never sees this at all.

import type { ReactNode } from 'react';
import { Link } from 'react-router';
import { usePluginLoadStatus } from '../pluginHost/pluginLoadStatus';

export function PluginGate({ pluginId, children }: { pluginId: string; children: ReactNode }) {
  const verdict = usePluginLoadStatus(pluginId);

  // Nothing while the answer is in flight: the check is one cached request,
  // and a spinner that flashes for 20ms is worse than a blank moment.
  if (verdict.state === 'checking') return null;
  if (verdict.state === 'mount') return <>{children}</>;

  const { status } = verdict;
  return (
    <section className="screen-error" role="alert">
      <h1 className="screen-error-title">{status.name} is not running</h1>
      <p className="text-muted">
        The plugin is installed, but this framework did not load it, so its screens
        have no backend to talk to. Everything else in the app still works.
      </p>
      {status.reason && <pre className="screen-error-detail">{status.reason}</pre>}
      <p className="text-muted">
        This usually means the plugin needs rebuilding against the current framework.{' '}
        <Link to="/system-health">System Health</Link> lists every plugin and why each
        one was refused.
      </p>
    </section>
  );
}
