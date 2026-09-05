import { apiFetch, ApiError } from '../../api/client';

// Vault settings (Settings > Vault, 2026-08-27) -- Overview (reuses the
// existing POST /vault-index/rebuild), read-only Templates, and the
// Entities CRUD registry (Work/Entities.md, relocated to
// .second-brain/Settings/Entities.md).

export interface VaultOverview {
  total_notes: number;
  last_rebuilt_at: string | null;
  folder_counts: Record<string, number>;
}

export function fetchVaultOverview(): Promise<VaultOverview> {
  return apiFetch<VaultOverview>('/vault/overview');
}

export function rebuildVaultIndex(): Promise<{
  notes_indexed: number;
  rebuilt_at: string;
  agent_index_rebuild_triggered: boolean;
}> {
  return apiFetch('/vault-index/rebuild', { method: 'POST' });
}

// Index Filtering (2026-08-27, operator: "Index Filtering a new settings
// feature... instead of Hardcoding files") -- which top-level Work/
// folders the standalone agent-facing indexer
// (Hermes-Provisioning/shared/build_vault_index.py) actually walks.
export interface IndexConfigFolder {
  name: string;
  included: boolean;
}

export function fetchIndexConfig(): Promise<{ folders: IndexConfigFolder[] }> {
  return apiFetch('/vault/index-config');
}

export function setFolderIncluded(folderName: string, included: boolean): Promise<{ folders: IndexConfigFolder[] }> {
  return apiFetch(`/vault/index-config/${encodeURIComponent(folderName)}`, {
    method: 'PATCH',
    body: JSON.stringify({ included }),
  });
}

export interface VaultTemplateSection {
  name: string;
  access: string;
}

export interface VaultTemplate {
  id: string;
  note_name?: string;
  on_missing: string;
  on_existing_title: string;
  sections: VaultTemplateSection[];
  frontmatter_defaults: Record<string, unknown>;
  note_own_folder: boolean;
  note_filename_plain: boolean;
  error?: string;
}

export function fetchVaultTemplates(): Promise<{ templates: VaultTemplate[] }> {
  return apiFetch('/vault/templates');
}

export interface VaultEntity {
  name: string;
  section: 'customer' | 'partner';
  aliases: string;
  affiliate_of: string;
  created: boolean;
  ignore: boolean;
  domain: string;
}

export function fetchVaultEntities(): Promise<{ entities: VaultEntity[] }> {
  return apiFetch('/vault/entities');
}

export interface VaultEntityPatch {
  name?: string;
  section?: string;
  aliases?: string;
  affiliate_of?: string;
  domain?: string;
  ignore?: boolean;
}

export function updateVaultEntity(name: string, patch: VaultEntityPatch): Promise<VaultEntity> {
  return apiFetch<VaultEntity>(`/vault/entities/${encodeURIComponent(name)}`, {
    method: 'PATCH',
    body: JSON.stringify(patch),
  });
}

export function deleteVaultEntity(name: string): Promise<{ deleted: boolean }> {
  return apiFetch(`/vault/entities/${encodeURIComponent(name)}`, { method: 'DELETE' });
}

export interface NewVaultEntity {
  name: string;
  section: 'customer' | 'partner';
  domain?: string;
  aliases?: string;
  affiliate_of?: string;
}

export function createVaultEntity(fields: NewVaultEntity): Promise<VaultEntity> {
  return apiFetch<VaultEntity>('/vault/entities', {
    method: 'POST',
    body: JSON.stringify(fields),
  });
}

// Export Data (REQ-SB-86-US-01-T02) -- a genuine, unfiltered real-filesystem
// tree of settings.vault_path (T01), the source the Export Data folder-tree
// picker page renders/selects against.
export interface VaultTreeNode {
  name: string;
  type: 'folder' | 'file';
  path: string;
  children?: VaultTreeNode[];
}

export function fetchVaultExportTree(): Promise<{ root: string; tree: VaultTreeNode }> {
  return apiFetch('/vault/export-data/tree');
}

// Export flow (REQ-SB-86-US-02-T03) -- a dedicated fetch, not apiFetch,
// since it must resolve response.blob() for the real .sbd bytes rather
// than JSON. Mirrors artifactsApiClient.ts's own commitExport() shape.
const EXPORT_DATA_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8001';

export async function exportVaultData(
  selection: string[],
  extraction: 'flat' | 'hierarchy',
): Promise<Blob> {
  const response = await fetch(`${EXPORT_DATA_BASE_URL}/vault/export-data/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ selection, extraction }),
  });
  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }
  return response.blob();
}
