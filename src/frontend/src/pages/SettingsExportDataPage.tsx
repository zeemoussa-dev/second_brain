import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router';
import { exportVaultData, fetchVaultExportTree, type VaultTreeNode } from '../features/settings/vaultApiClient';
import { ApiError } from '../api/client';

// Export Data folder-tree browser + multi-select + .md quick filter
// (REQ-SB-86-US-01-T02), relocated 2026-09-02 (operator: "take export
// Data outside of vault settings and be next to the artifacts in
// Settings") -- was SettingsVaultExportDataPage.tsx under Settings ->
// Vault's own sub-nav; now its own top-level Settings section, same flat
// route shape SettingsArtifactsPage.tsx already established. The backend
// routes it calls (GET /vault/export-data/tree, POST /vault/export-data/
// export) are unchanged -- this is a frontend navigation move only, the
// data still genuinely comes from the vault domain.
//
// The Set<string> selection shape mirrors SettingsArtifactsPage.tsx's own
// established ephemeral-multi-select precedent. The selection only ever
// holds real FILE paths -- selecting a folder adds every real file path
// nested beneath it, never the folder's own path, so the Export trigger
// can read this state directly as "the exact files to export" with no
// further expansion.

function extractErrorDetail(error: unknown): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.message) as { detail?: unknown };
      if (typeof parsed.detail === 'string') {
        return parsed.detail;
      }
    } catch {
      // Not JSON -- fall through to the raw message below.
    }
    return error.message;
  }
  return 'Request failed.';
}

function triggerSbdDownload(blob: Blob) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `second-brain-vault-export-${new Date().toISOString().replace(/[:.]/g, '-')}.sbd`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function collectFileDescendantPaths(node: VaultTreeNode): string[] {
  if (node.type === 'file') return [node.path];
  return (node.children ?? []).flatMap(collectFileDescendantPaths);
}

// Narrows a node to only .md files and the folders that contain at least
// one .md file anywhere beneath them -- a folder with zero .md descendants
// is dropped entirely (returns null), never rendered as a fake-empty row.
function filterToMd(node: VaultTreeNode): VaultTreeNode | null {
  if (node.type === 'file') {
    return node.name.toLowerCase().endsWith('.md') ? node : null;
  }
  const filteredChildren = (node.children ?? [])
    .map(filterToMd)
    .filter((child): child is VaultTreeNode => child !== null);
  if (filteredChildren.length === 0) return null;
  return { ...node, children: filteredChildren };
}

export function SettingsExportDataPage() {
  const [root, setRoot] = useState<string | null>(null);
  const [tree, setTree] = useState<VaultTreeNode | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedFilePaths, setSelectedFilePaths] = useState<Set<string>>(new Set());
  const [expandedPaths, setExpandedPaths] = useState<Record<string, boolean>>({});
  const [mdFilterOn, setMdFilterOn] = useState(false);

  // Export flow (REQ-SB-86-US-02-T03).
  const [exportOptionsOpen, setExportOptionsOpen] = useState(false);
  const [extraction, setExtraction] = useState<'flat' | 'hierarchy'>('hierarchy');
  const [exportLoading, setExportLoading] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  useEffect(() => {
    fetchVaultExportTree()
      .then((result) => {
        setRoot(result.root);
        setTree(result.tree);
      })
      .catch(() => setError('Could not load the vault folder tree.'));
  }, []);

  const displayedChildren = useMemo(() => {
    const children = tree?.children ?? [];
    if (!mdFilterOn) return children;
    return children
      .map(filterToMd)
      .filter((child): child is VaultTreeNode => child !== null);
  }, [tree, mdFilterOn]);

  function toggleExpanded(path: string) {
    setExpandedPaths((previous) => ({ ...previous, [path]: !previous[path] }));
  }

  function toggleFileSelected(path: string) {
    setSelectedFilePaths((previous) => {
      const next = new Set(previous);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  }

  function toggleFolderSelected(node: VaultTreeNode) {
    const descendantFiles = collectFileDescendantPaths(node);
    const allAlreadySelected = descendantFiles.length > 0 && descendantFiles.every((path) => selectedFilePaths.has(path));
    setSelectedFilePaths((previous) => {
      const next = new Set(previous);
      descendantFiles.forEach((path) => {
        if (allAlreadySelected) {
          next.delete(path);
        } else {
          next.add(path);
        }
      });
      return next;
    });
  }

  function clearSelection() {
    setSelectedFilePaths(new Set());
  }

  function openExportOptions() {
    setExportError(null);
    setExtraction('hierarchy');
    setExportOptionsOpen(true);
  }

  async function handleConfirmExport() {
    setExportError(null);
    setExportLoading(true);
    try {
      // selectedFilePaths already holds only real file paths -- a folder
      // selection was expanded into its own nested file paths at
      // select-time (see the comment above collectFileDescendantPaths),
      // so no further client-side expansion is needed here.
      const blob = await exportVaultData(Array.from(selectedFilePaths), extraction);
      triggerSbdDownload(blob);
      setExportOptionsOpen(false);
    } catch (error) {
      setExportError(extractErrorDetail(error));
    } finally {
      setExportLoading(false);
    }
  }

  function renderNode(node: VaultTreeNode, depth: number) {
    const isFolder = node.type === 'folder';
    const isExpanded = expandedPaths[node.path] ?? false;
    const descendantFiles = isFolder ? collectFileDescendantPaths(node) : [];
    const isChecked = isFolder
      ? descendantFiles.length > 0 && descendantFiles.every((path) => selectedFilePaths.has(path))
      : selectedFilePaths.has(node.path);

    return (
      <div key={node.path} data-testid={`tree-node-${node.path}`} data-node-type={node.type}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', paddingLeft: `${depth * 20}px`, paddingTop: 'var(--space-1)', paddingBottom: 'var(--space-1)' }}>
          {isFolder ? (
            <button
              type="button"
              onClick={() => toggleExpanded(node.path)}
              aria-label={isExpanded ? 'Collapse folder' : 'Expand folder'}
              style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'flex', alignItems: 'center' }}
            >
              <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: '18px', color: 'var(--color-text-muted)' }}>
                {isExpanded ? 'expand_more' : 'chevron_right'}
              </span>
            </button>
          ) : (
            <span style={{ width: '18px', display: 'inline-block' }} />
          )}
          <input
            type="checkbox"
            data-testid={`tree-node-checkbox-${node.path}`}
            checked={isChecked}
            onChange={() => (isFolder ? toggleFolderSelected(node) : toggleFileSelected(node.path))}
          />
          {/* Name (+ its icon) is its own click target for expand/collapse,
              separate from the checkbox -- operator, 2026-09-02: "the
              Folder names should be clickable to expand and the checkbox
              is the one i click on to select." A file's own name is inert
              (no expand concept), so only the folder case wires an
              onClick. */}
          <span
            data-testid={`tree-node-label-${node.path}`}
            onClick={isFolder ? () => toggleExpanded(node.path) : undefined}
            style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', cursor: isFolder ? 'pointer' : 'default' }}
          >
            <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: '18px', color: 'var(--color-text-muted)' }}>
              {isFolder ? 'folder' : 'description'}
            </span>
            <span>{node.name}</span>
          </span>
        </div>
        {isFolder && isExpanded && (node.children ?? []).map((child) => renderNode(child, depth + 1))}
      </div>
    );
  }

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <h1>Export Data</h1>
      <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
        Browse your real vault's own folder tree and select whichever folders/files you want to
        share. Selecting a folder includes every file nested beneath it; you can also select
        individual files directly.
      </p>

      {error && <p style={{ color: 'var(--color-danger)' }}>{error}</p>}
      {root && (
        <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
          Vault: {root}
        </p>
      )}

      <div className="item-row-actions" style={{ marginBottom: 'var(--space-3)', alignItems: 'center' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <input
            type="checkbox"
            data-testid="md-filter-toggle"
            checked={mdFilterOn}
            onChange={(event) => setMdFilterOn(event.target.checked)}
          />
          .md files only
        </label>
        <button
          type="button"
          className="btn"
          data-testid="clear-selection"
          disabled={selectedFilePaths.size === 0}
          onClick={clearSelection}
        >
          Clear selection
        </button>
        <button
          type="button"
          className="btn btn-primary"
          data-testid="export-selection"
          disabled={selectedFilePaths.size === 0}
          onClick={openExportOptions}
        >
          Export…
        </button>
        <span className="text-muted" data-role="export-data-selection-summary">
          {selectedFilePaths.size} file{selectedFilePaths.size === 1 ? '' : 's'} selected
        </span>
      </div>

      {tree && (
        <div className="card" data-role="export-data-tree">
          {displayedChildren.map((child) => renderNode(child, 0))}
          {displayedChildren.length === 0 && <p className="text-muted">No matching folders/files.</p>}
        </div>
      )}
      {!tree && !error && <p className="text-muted">Loading…</p>}

      {exportOptionsOpen && (
        <div className="card" data-role="export-options" style={{ marginTop: 'var(--space-3)' }}>
          <h3>Export options</h3>
          <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
            Choose how the {selectedFilePaths.size} selected file{selectedFilePaths.size === 1 ? '' : 's'} should
            be arranged inside the downloaded archive.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', marginBottom: 'var(--space-3)' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <input
                type="radio"
                name="export-extraction"
                data-testid="extraction-hierarchy"
                checked={extraction === 'hierarchy'}
                onChange={() => setExtraction('hierarchy')}
              />
              Preserve folder structure (hierarchy-preserving)
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <input
                type="radio"
                name="export-extraction"
                data-testid="extraction-flat"
                checked={extraction === 'flat'}
                onChange={() => setExtraction('flat')}
              />
              Flatten — every file in one folder
            </label>
          </div>
          <button
            type="button"
            className="btn"
            data-testid="export-cancel"
            disabled={exportLoading}
            onClick={() => setExportOptionsOpen(false)}
            style={{ marginRight: 'var(--space-2)' }}
          >
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-primary"
            data-testid="export-confirm"
            disabled={exportLoading}
            onClick={handleConfirmExport}
          >
            {exportLoading ? 'Exporting…' : 'Confirm export'}
          </button>
        </div>
      )}

      {exportError && (
        <div className="card" data-role="export-error" style={{ marginTop: 'var(--space-3)' }}>
          <p style={{ color: 'var(--color-danger)' }}>{exportError}</p>
        </div>
      )}
    </>
  );
}
