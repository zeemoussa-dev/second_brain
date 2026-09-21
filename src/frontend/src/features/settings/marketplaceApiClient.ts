import { apiFetch } from '../../api/client';

// Settings > Marketplace -- a thin client over GET /marketplace,
// GET /marketplace/{id}/{version}/preflight, POST .../install and
// POST /marketplace/{id}/uninstall (ADR-022).
//
// Preflight is a separate call from install on purpose: it changes nothing,
// so the card can show what installing would do before the operator commits.

export interface MarketplacePackage {
  version: string;
  name?: string;
  description?: string;
  framework_api?: number | null;
  requires?: string[];
  compatible?: boolean;
  // Set only when this version's plugin.json cannot be read. Listed anyway,
  // so a broken package is visible rather than silently missing.
  error: string | null;
}

/** Where an installed plugin came from. Absent means this framework's own
 * Marketplace; otherwise the repository or folder it was installed from
 * (REQ-SB-92), which is what an update pulls again. */
export interface PluginSource {
  kind: 'git' | 'path';
  location: string;
  ref?: string | null;
  commit?: string | null;
}

export interface MarketplacePlugin {
  id: string;
  installed_version: string | null;
  source?: PluginSource | null;
  // Newest first. Empty for a plugin installed from its own repository.
  packages: MarketplacePackage[];
}

export interface MarketplacePreflight {
  plugin_id: string;
  version: string;
  ok: boolean;
  problems: string[];
  installed_version: string | null;
  replaces: string | null;
  // Templates the package brings: written when missing, kept (never
  // overwritten) when the install already has one with that id.
  templates?: { install: string[]; keep: string[] };
}

export interface MarketplaceSourcePreflight extends MarketplacePreflight {
  source: PluginSource;
}

export interface MarketplaceInstallResult {
  installed: boolean;
  plugin_id: string;
  version: string;
  replaced?: string | null;
  source?: PluginSource | null;
  restart_required?: boolean;
  problems: string[];
}

export interface MarketplaceUninstallResult {
  uninstalled: boolean;
  plugin_id: string;
  removed?: string[];
  refused_outside_plugin_folders?: string[];
  restart_required?: boolean;
  reason: string | null;
}

export function fetchMarketplace(): Promise<MarketplacePlugin[]> {
  return apiFetch('/marketplace');
}

export function preflightPlugin(id: string, version: string): Promise<MarketplacePreflight> {
  return apiFetch(`/marketplace/${encodeURIComponent(id)}/${encodeURIComponent(version)}/preflight`);
}

export function installPlugin(id: string, version: string): Promise<MarketplaceInstallResult> {
  return apiFetch(`/marketplace/${encodeURIComponent(id)}/${encodeURIComponent(version)}/install`, {
    method: 'POST',
  });
}

export function uninstallPlugin(id: string): Promise<MarketplaceUninstallResult> {
  return apiFetch(`/marketplace/${encodeURIComponent(id)}/uninstall`, { method: 'POST' });
}

// Installing from where a plugin lives, so it never has to be published into
// the framework's own tree (REQ-SB-92). Preflight clones, reads and discards.
export interface PluginSourceRequest {
  kind: 'git' | 'path';
  location: string;
  ref?: string | null;
}

export function preflightSource(source: PluginSourceRequest): Promise<MarketplaceSourcePreflight> {
  return apiFetch('/marketplace/source/preflight', { method: 'POST', body: JSON.stringify(source) });
}

export function installFromSource(source: PluginSourceRequest): Promise<MarketplaceInstallResult> {
  return apiFetch('/marketplace/source/install', { method: 'POST', body: JSON.stringify(source) });
}

/** Pulls the plugin's recorded repository and ref again and re-installs it. */
export function updatePlugin(id: string): Promise<MarketplaceInstallResult> {
  return apiFetch(`/marketplace/${encodeURIComponent(id)}/update`, { method: 'POST' });
}
