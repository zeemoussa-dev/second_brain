// Where you came from, so every screen can offer a way back (operator,
// 2026-10-17). See BackControl.tsx on how this relates to ADR-060's
// breadcrumbs -- same complaint, two mechanisms, both kept (2026-10-18).
//
// The app is one router, so a Link from My Day to a note is a history push and
// the browser's own Back already works. What was missing was anything in the UI
// that said so, and any way to NAME the place it would return to -- a screen
// cannot know who opened it, which is exactly the problem `CockpitBackLink`
// solved for one component by having the caller pass `backTo`.
//
// The trail solves it for every screen at once by mirroring the router's own
// stack instead of asking callers to pass anything. It is deliberately in
// memory only: it describes this tab's journey, not a shareable fact about a
// page, so after a refresh there is nothing to name and the control hides.
//
// The provider that fills it lives in NavigationTrail.tsx; this file holds the
// parts that are not components.

import { createContext, useContext } from 'react';

export interface TrailEntry {
  /** Path and query together, so the name reflects the filters too. */
  to: string;
  label: string;
}

export const TrailContext = createContext<TrailEntry | null>(null);

/** The page a Back control would return to, or `null` when the trail is empty
 * (a cold load, or we have already walked all the way back). */
export function usePreviousPage(): TrailEntry | null {
  return useContext(TrailContext);
}

// A path's own name, matched longest-first so `/settings/artifacts` is
// Settings rather than falling through to a guess. Plugin paths are resolved
// from the registry, since a plugin names its own screens.
const FRAMEWORK_LABELS: ReadonlyArray<readonly [string, string]> = [
  ['/agent-activity', 'Agent Activity'],
  ['/system-health', 'System Health'],
  ['/meeting-cockpit', 'Meeting'],
  ['/inbox-cockpit', 'Email'],
  ['/settings', 'Settings'],
  ['/crawlers', 'Crawlers'],
  ['/browse', 'Browse & Search'],
  ['/vault', 'The Vault'],
  ['/chat', 'Chat'],
];

let pluginLabels: ReadonlyArray<readonly [string, string]> = [];

/** Told to the trail by the shell, so this module does not import the plugin
 * registry and the registry does not import the shell. */
export function registerPluginLabels(entries: ReadonlyArray<{ to: string; label: string }>) {
  pluginLabels = entries
    .map((entry) => [entry.to, entry.label] as const)
    .sort((a, b) => b[0].length - a[0].length);
}

export function labelFor(pathname: string): string {
  if (pathname === '/') return 'Agents Map';
  for (const [prefix, label] of [...pluginLabels, ...FRAMEWORK_LABELS]) {
    if (pathname === prefix || pathname.startsWith(prefix + '/')) return label;
  }
  return 'Back';
}
