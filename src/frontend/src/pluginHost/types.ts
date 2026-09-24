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

/** A row in a Cockpit's info panel. `key` is a field of the Cockpit's
 * subject, which a subject enricher of the same plugin can fill. */
export interface PluginCockpitInfoField {
  subjectKind: 'email' | 'meeting';
  label: string;
  key: string;
}

/** What a Cockpit tab's screen is given: which subject it is looking at. The
 * Cockpit is a generic component for chatting with agents about a subject; what
 * an email or a meeting IS belongs to the plugin that understands it (operator,
 * 2026-09-24: "Cockpit is the framework Peice as Component for Agents to chat
 * its Used inside myDay which understands Emails and Calendar"). */
export interface PluginCockpitTabProps {
  subjectKind: 'email' | 'meeting';
  subjectNoteStem: string;
}

/** A tab in the Cockpit, after the framework's own. `id` must be unique within
 * the plugin and becomes part of no URL -- the Cockpit's tabs are local state. */
export interface PluginCockpitTab {
  subjectKind: 'email' | 'meeting';
  id: string;
  label: string;
  icon?: string;
  component: ComponentType<PluginCockpitTabProps>;
}

export interface PluginUi {
  routes?: PluginRoute[];
  nav?: PluginNavEntry[];
  settingsPages?: PluginSettingsPage[];
  cockpitInfoFields?: PluginCockpitInfoField[];
  cockpitTabs?: PluginCockpitTab[];
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

export interface MountedCockpitInfoField extends PluginCockpitInfoField {
  pluginId: string;
}

export interface MountedCockpitTab extends PluginCockpitTab {
  pluginId: string;
}
