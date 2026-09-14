import type { ComponentType } from 'react';

// The contract between the framework's frontend and an installed plugin's
// screens (ADR-022). A plugin's `ui/index.tsx` default-exports a `PluginUi`;
// the Marketplace copies that folder to `src/plugins/<plugin-id>/` and the app
// is rebuilt with it.

/** A screen. `path` is absolute and must be `/<plugin-id>` or under it, so a
 * plugin can neither shadow a framework route nor another plugin's. */
export interface PluginRoute {
  path: string;
  component: ComponentType;
}

/** A sidebar entry. `to` follows the same `/<plugin-id>` rule as routes. */
export interface PluginNavEntry {
  to: string;
  label: string;
  icon?: string;
}

/** A Settings page. `path` is relative to `/settings/plugins/<plugin-id>`;
 * an empty path is the plugin's main settings page. */
export interface PluginSettingsPage {
  path: string;
  label: string;
  component: ComponentType;
}

export interface PluginUi {
  routes?: PluginRoute[];
  nav?: PluginNavEntry[];
  settingsPages?: PluginSettingsPage[];
}

export interface MountedRoute extends PluginRoute {
  pluginId: string;
}

export interface MountedNavEntry extends PluginNavEntry {
  pluginId: string;
}

export interface MountedSettingsPage extends PluginSettingsPage {
  pluginId: string;
}
