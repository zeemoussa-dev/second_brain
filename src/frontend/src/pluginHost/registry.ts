import type {
  MountedCockpitInfoField,
  MountedNavEntry,
  MountedRoute,
  MountedSettingsPage,
  PluginUi,
} from './types';

// Build-time composition (ADR-022): every installed plugin's screens are
// compiled into this bundle. Eager, not lazy: a route discovered only after
// the router has rendered would 404 on a deep link or a page refresh.
const pluginModules = import.meta.glob<{ default?: PluginUi }>('../plugins/*/index.tsx', {
  eager: true,
});

// Same rule the backend host applies: an id becomes a URL segment, so anything
// looser could let one plugin's screens land on another's paths.
const VALID_PLUGIN_ID = /^[a-z0-9][a-z0-9-]{0,62}$/;

function belongsToPlugin(pluginId: string, path: string): boolean {
  return path === `/${pluginId}` || path.startsWith(`/${pluginId}/`);
}

function pluginIdFromModulePath(modulePath: string): string {
  // '../plugins/<plugin-id>/index.tsx'
  return modulePath.split('/')[2] ?? '';
}

const COCKPIT_SUBJECT_KINDS = new Set(['email', 'meeting']);

interface Collected {
  routes: MountedRoute[];
  nav: MountedNavEntry[];
  settingsPages: MountedSettingsPage[];
  cockpitInfoFields: MountedCockpitInfoField[];
  problems: string[];
}

function collectPluginContributions(): Collected {
  const collected: Collected = { routes: [], nav: [], settingsPages: [], cockpitInfoFields: [], problems: [] };

  for (const modulePath of Object.keys(pluginModules).sort()) {
    const pluginId = pluginIdFromModulePath(modulePath);
    if (!VALID_PLUGIN_ID.test(pluginId)) {
      collected.problems.push(`"${pluginId}" is not a valid plugin id; none of its screens were mounted`);
      continue;
    }
    const ui = pluginModules[modulePath].default;
    if (!ui || typeof ui !== 'object') {
      collected.problems.push(`${pluginId}: index.tsx has no default export; none of its screens were mounted`);
      continue;
    }

    const seenPaths = new Set<string>();
    for (const route of ui.routes ?? []) {
      if (!belongsToPlugin(pluginId, route.path)) {
        collected.problems.push(`${pluginId}: route "${route.path}" is outside /${pluginId} and was not mounted`);
      } else if (seenPaths.has(route.path)) {
        collected.problems.push(`${pluginId}: route "${route.path}" is declared twice; only the first was mounted`);
      } else {
        seenPaths.add(route.path);
        collected.routes.push({ ...route, pluginId });
      }
    }

    for (const entry of ui.nav ?? []) {
      if (belongsToPlugin(pluginId, entry.to)) {
        collected.nav.push({ ...entry, pluginId });
      } else {
        collected.problems.push(`${pluginId}: nav entry "${entry.label}" points outside /${pluginId} and was not shown`);
      }
    }

    for (const page of ui.settingsPages ?? []) {
      const relativePath = page.path.replace(/^\/+|\/+$/g, '');
      if (relativePath.split('/').includes('..')) {
        collected.problems.push(`${pluginId}: settings page "${page.label}" path "${page.path}" is not allowed`);
        continue;
      }
      const path = relativePath
        ? `/settings/plugins/${pluginId}/${relativePath}`
        : `/settings/plugins/${pluginId}`;
      collected.settingsPages.push({ ...page, path, pluginId });
    }

    for (const field of ui.cockpitInfoFields ?? []) {
      if (COCKPIT_SUBJECT_KINDS.has(field.subjectKind) && field.key && field.label) {
        collected.cockpitInfoFields.push({ ...field, pluginId });
      } else {
        collected.problems.push(`${pluginId}: Cockpit info field "${field.label}" is not a valid email or meeting field and was not shown`);
      }
    }
  }

  for (const problem of collected.problems) {
    console.warn(`[plugins] ${problem}`);
  }
  return collected;
}

const collected = collectPluginContributions();

export const pluginRoutes: readonly MountedRoute[] = collected.routes;
export const pluginNavEntries: readonly MountedNavEntry[] = collected.nav;
export const pluginSettingsPages: readonly MountedSettingsPage[] = collected.settingsPages;

/** A Cockpit's own info fields followed by the installed plugins' fields for
 * that subject kind. A plugin field whose key the Cockpit (or an earlier
 * plugin) already shows is left out, so the same field never appears twice. */
export function withPluginCockpitInfoFields(
  subjectKind: string,
  ownFields: readonly { label: string; key: string }[],
): { label: string; key: string }[] {
  const shownKeys = new Set(ownFields.map((field) => field.key));
  const fields = [...ownFields];
  for (const field of collected.cockpitInfoFields) {
    if (field.subjectKind === subjectKind && !shownKeys.has(field.key)) {
      shownKeys.add(field.key);
      fields.push({ label: field.label, key: field.key });
    }
  }
  return fields;
}
/** Contributions that broke the rules above and were skipped. Shown on the
 * System Health page, because a skipped screen is otherwise just missing. */
export const pluginUiProblems: readonly string[] = collected.problems;
export const installedPluginIds: readonly string[] = Object.keys(pluginModules)
  .map(pluginIdFromModulePath)
  .filter((pluginId) => VALID_PLUGIN_ID.test(pluginId))
  .sort();
