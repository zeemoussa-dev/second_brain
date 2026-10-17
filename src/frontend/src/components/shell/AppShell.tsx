import { useState } from 'react';
import { Outlet, useLocation } from 'react-router';
import { Sidebar } from './Sidebar';
import { ErrorBoundary } from '../ErrorBoundary';
import { BackControl } from './BackControl';
import { NavigationTrail } from './NavigationTrailProvider';
import { registerPluginLabels } from './navigationTrail';
import { pluginNavEntries } from '../../pluginHost/registry';

// A plugin names its own screens, so the trail asks the registry rather than
// guessing "Azure Cost" from `/azure-cost-manager`. Registered once, here,
// because the shell is the one place that already knows both sides.
registerPluginLabels(pluginNavEntries);

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const { pathname } = useLocation();

  return (
    <NavigationTrail>
      <div className={collapsed ? 'app-shell sidebar-collapsed' : 'app-shell'}>
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />
        <main className="main">
          <BackControl />
          {/* Inside <main>, so a failed page keeps the sidebar and the way
              back. Keyed by pathname, not by the full location: navigating
              away clears a caught error, while a filter rewriting its own
              query string must not remount the page and throw its state
              away (ADR-041 writes filters with replace for the same reason). */}
          <ErrorBoundary key={pathname}>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </NavigationTrail>
  );
}
