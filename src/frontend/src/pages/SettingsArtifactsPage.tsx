import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router';
import {
  fetchArtifacts,
  previewExport,
  type ArtifactKind,
  type ArtifactSummary,
  type ArtifactSelectionEntry,
  type ExportPreviewResult,
} from '../features/settings/artifactsApiClient';
import { ArtifactExportModal } from '../features/settings/ArtifactExportModal';
import { ArtifactImportModal } from '../features/settings/ArtifactImportModal';

// Cross-type artifact browser (REQ-SB-85-US-01/02/03), redesigned
// 2026-09-02 per the operator's own design pass: "Same style as the
// Vault Settings" — a local left nav (Templates/Skills/Agents/Pipelines,
// same .vault-settings-layout/-nav shape VaultSettingsNav.tsx already
// established, but tab buttons over local state rather than router Links,
// since all four kinds live on this one route) + a right content panel
// showing only the active kind's items. Selecting an item marks it and
// the mark PERSISTS across tab switches until Cancel; selecting an Agent
// (or any artifact with real dependencies) auto-marks its own real
// dependency closure too, LOCKED (not directly unmarkable — only removing
// the artifact that pulled it in clears it), driven live off the same
// POST /artifacts/export/preview the old inline "Export preview" card
// used to call only after clicking Export. The actual Export/Import
// confirmation flows are both popups now (ArtifactExportModal/
// ArtifactImportModal), not inline page cards.

const KIND_ORDER: ArtifactKind[] = ['skill', 'template', 'agent', 'pipeline'];
const KIND_NAV: { kind: ArtifactKind; icon: string; label: string }[] = [
  { kind: 'template', icon: 'description', label: 'Templates' },
  { kind: 'skill', icon: 'auto_awesome', label: 'Skills' },
  { kind: 'agent', icon: 'smart_toy', label: 'Agents' },
  { kind: 'pipeline', icon: 'conveyor_belt', label: 'Pipelines' },
];
const KIND_LABELS: Record<ArtifactKind, string> = {
  skill: 'Skills', template: 'Templates', agent: 'Agents', pipeline: 'Pipelines',
};

type SelectionState = Record<ArtifactKind, Set<string>>;

function emptySelection(): SelectionState {
  return { skill: new Set(), template: new Set(), agent: new Set(), pipeline: new Set() };
}

export function SettingsArtifactsPage() {
  const [artifacts, setArtifacts] = useState<ArtifactSummary[] | null>(null);
  const [activeKind, setActiveKind] = useState<ArtifactKind>('template');
  const [selection, setSelection] = useState<SelectionState>(emptySelection());
  const [livePreview, setLivePreview] = useState<ExportPreviewResult | null>(null);
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [importModalOpen, setImportModalOpen] = useState(false);

  useEffect(() => {
    fetchArtifacts().then(setArtifacts);
  }, []);

  const groupedByKind = useMemo(() => {
    const groups: Record<ArtifactKind, ArtifactSummary[]> = { skill: [], template: [], agent: [], pipeline: [] };
    for (const artifact of artifacts ?? []) {
      groups[artifact.kind].push(artifact);
    }
    return groups;
  }, [artifacts]);

  const totalSelected = KIND_ORDER.reduce((sum, kind) => sum + selection[kind].size, 0);

  function selectionToPayload(current: SelectionState): ArtifactSelectionEntry[] {
    return KIND_ORDER.flatMap((kind) => Array.from(current[kind]).map((id) => ({ kind, id })));
  }

  // Live dependency-closure preview -- recomputed on every selection
  // change so the side panel can show a dependency-only item as marked
  // and locked the moment its selected parent pulls it in (e.g. clicking
  // an Agent while on the Agents tab immediately locks its Skill on the
  // Skills tab too, with no separate "preview" step to trigger first).
  useEffect(() => {
    let cancelled = false;
    if (totalSelected === 0) {
      setLivePreview(null);
      return;
    }
    previewExport(selectionToPayload(selection)).then((result) => {
      if (!cancelled) {
        setLivePreview(result);
      }
    });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selection]);

  const lockedByKind = useMemo(() => {
    const locked: Record<ArtifactKind, Map<string, string>> = { skill: new Map(), template: new Map(), agent: new Map(), pipeline: new Map() };
    for (const entry of livePreview?.closure ?? []) {
      if (entry.included_reason === 'dependency') {
        locked[entry.kind as ArtifactKind]?.set(entry.id, entry.depends_via ?? '');
      }
    }
    return locked;
  }, [livePreview]);

  function toggleArtifact(kind: ArtifactKind, id: string) {
    setSelection((previous) => {
      const nextKindSet = new Set(previous[kind]);
      if (nextKindSet.has(id)) {
        nextKindSet.delete(id);
      } else {
        nextKindSet.add(id);
      }
      return { ...previous, [kind]: nextKindSet };
    });
  }

  function handleCancel() {
    setSelection(emptySelection());
    setLivePreview(null);
  }

  function handleExported() {
    setExportModalOpen(false);
    handleCancel();
  }

  const activeItems = groupedByKind[activeKind];

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <div className="artifacts-action-bar" style={{ marginBottom: 'var(--space-4)' }}>
        <h1 style={{ margin: 0 }}>Artifacts</h1>
        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
          <button type="button" className="btn" data-testid="clear-selection" disabled={totalSelected === 0} onClick={handleCancel}>
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-primary"
            data-testid="export-selected"
            disabled={totalSelected === 0 || livePreview === null}
            onClick={() => setExportModalOpen(true)}
          >
            Export…
          </button>
          <button type="button" className="btn btn-primary" data-testid="import-trigger" onClick={() => setImportModalOpen(true)}>
            Import…
          </button>
        </div>
      </div>
      <p className="text-muted">
        Every real Skill, Template, Agent, and Pipeline in this deployment, browsable across
        kinds — mark what you want and it stays marked as you switch tabs, ready to Export.
      </p>

      <div className="vault-settings-layout">
        <nav className="vault-settings-nav">
          {KIND_NAV.map((item) => (
            <button
              key={item.kind}
              type="button"
              data-testid={`artifacts-tab-${item.kind}`}
              className={`vault-settings-nav-item artifacts-nav-item${activeKind === item.kind ? ' vault-settings-nav-item--active' : ''}`}
              onClick={() => setActiveKind(item.kind)}
            >
              <span className="material-symbols-outlined" aria-hidden="true">{item.icon}</span>
              {item.label}
              {selection[item.kind].size > 0 && ` (${selection[item.kind].size})`}
            </button>
          ))}
        </nav>

        <div className="vault-settings-content">
          <div className="card">
            <h2>{KIND_LABELS[activeKind]}</h2>
            {artifacts === null && <p className="text-muted">Loading...</p>}
            {artifacts !== null && (
              <div className="item-list artifacts-item-list">
                {activeItems.map((artifact) => {
                  const explicitlySelected = selection[activeKind].has(artifact.id);
                  const lockedVia = lockedByKind[activeKind].get(artifact.id);
                  const locked = Boolean(lockedVia) && !explicitlySelected;
                  return (
                    <div
                      className={`item-row artifacts-item-row${locked ? ' item-row--locked' : ''}`}
                      key={artifact.id}
                      onClick={() => !locked && toggleArtifact(activeKind, artifact.id)}
                      style={{ cursor: locked ? 'not-allowed' : 'pointer' }}
                    >
                      <div className="item-row-main">
                        <span className="item-row-title">{artifact.name}</span>
                        <span className="item-row-meta">{artifact.id}</span>
                        {locked && <span className="item-row-locked-hint">Required by: {lockedVia}</span>}
                      </div>
                      <div className="item-row-actions">
                        <input
                          type="checkbox"
                          data-testid={`artifact-checkbox-${activeKind}-${artifact.id}`}
                          checked={explicitlySelected || locked}
                          disabled={locked}
                          onChange={() => toggleArtifact(activeKind, artifact.id)}
                          onClick={(event) => event.stopPropagation()}
                        />
                      </div>
                    </div>
                  );
                })}
                {activeItems.length === 0 && (
                  <p className="text-muted" data-role={`artifact-empty-${activeKind}`}>
                    No {KIND_LABELS[activeKind]} yet.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {exportModalOpen && livePreview && (
        <ArtifactExportModal
          selection={selectionToPayload(selection)}
          preview={livePreview}
          onClose={() => setExportModalOpen(false)}
          onExported={handleExported}
        />
      )}

      {importModalOpen && <ArtifactImportModal onClose={() => setImportModalOpen(false)} />}
    </>
  );
}
