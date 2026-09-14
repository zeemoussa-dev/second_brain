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

export interface MarketplacePlugin {
  id: string;
  installed_version: string | null;
  // Newest first.
  packages: MarketplacePackage[];
}

export interface MarketplacePreflight {
  plugin_id: string;
  version: string;
  ok: boolean;
  problems: string[];
  installed_version: string | null;
  replaces: string | null;
}

export interface MarketplaceInstallResult {
  installed: boolean;
  plugin_id: string;
  version: string;
  replaced?: string | null;
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
