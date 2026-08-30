import { useEffect, useState } from 'react';
import { fetchSections, updateSection, type SectionSummary } from '../settings/settingsApiClient';
import { VisualPicker } from './VisualPicker';
import { FieldEditorModal } from './FieldEditorModal';
import { ExpandableText } from './ExpandableText';
import { ChecklistPicker, type ChecklistItem } from './ChecklistPicker';
import { fetchScopeSuggestions, type ScopeSuggestions } from '../vault-browser/client';

interface SectionDetailPanelProps {
  sectionId: string;
  onClose: () => void;
  // Mirrors AgentDetailPanel's own onAgentUpdated -- this panel's own
  // `section` state updates immediately on every save, but the map
  // canvas's own separate `sections` state (what Hub color/icon actually
  // renders from) only refreshes when the parent re-fetches. AgentsMapPage
  // passes its existing refreshAgents here (it already re-fetches
  // fetchSections() as part of the same layout pass, so no new fetch is
  // needed for this).
  onSectionUpdated?: () => void;
}

const TABS = ['overview', 'settings'] as const;
type Tab = (typeof TABS)[number];
const TAB_LABELS: Record<Tab, string> = { overview: 'Overview', settings: 'Settings' };

// Section's own detail panel (operator, 2026-08-23: "the Hub can be
// clicked and has its own Settings, Overview tab... Section Color and
// Icon, Description and Name") -- deliberately a much smaller sibling of
// AgentDetailPanel.tsx (two tabs, no Chat/History/Schedule/Skills — a
// Section has none of those concerns), reusing the same `.side-panel-*`
// shell/CSS and the same VisualPicker component that file already uses
// for icon/color.
export function SectionDetailPanel({ sectionId, onClose, onSectionUpdated }: SectionDetailPanelProps) {
  const [section, setSection] = useState<SectionSummary | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [nameDraft, setNameDraft] = useState('');
  const [descriptionDraft, setDescriptionDraft] = useState('');
  const [savingName, setSavingName] = useState(false);
  const [savingDescription, setSavingDescription] = useState(false);
  // 2026-08-29 audit -- subtitle/folders/fallback_agent_id were all real,
  // already-wired fields (both the backend and SectionSummary itself
  // already had them) that this panel simply never surfaced; folders/
  // fallback_agent_id were already editable in Settings > Sections
  // (SectionsCard.tsx) but not here, subtitle was missing everywhere.
  const [subtitleDraft, setSubtitleDraft] = useState('');
  const [savingSubtitle, setSavingSubtitle] = useState(false);
  const [foldersDraft, setFoldersDraft] = useState('');
  const [savingFolders, setSavingFolders] = useState(false);
  const [fallbackAgentIdDraft, setFallbackAgentIdDraft] = useState('');
  const [savingFallbackAgentId, setSavingFallbackAgentId] = useState(false);
  // 2026-08-29 (operator: "a Big Pop up so we can fill the fields that
  // needs a space to fill") -- same big-popup pattern AgentDetailPanel.tsx
  // now uses. Folders gets the real vault-folder checklist (same data
  // source as the Vault Scope picker's own folder half); Description/
  // Subtitle just get more room to type in.
  const [openFieldEditor, setOpenFieldEditor] = useState<null | 'description' | 'subtitle' | 'folders'>(null);
  const [savingFieldEditor, setSavingFieldEditor] = useState(false);
  const [foldersEditorDraft, setFoldersEditorDraft] = useState<string[]>([]);
  const [scopeSuggestions, setScopeSuggestions] = useState<ScopeSuggestions | null>(null);

  useEffect(() => {
    setSection(null);
    fetchSections().then((sections) => {
      const found = sections.find((s) => s.id === sectionId) ?? null;
      setSection(found);
      setNameDraft(found?.name ?? '');
      setDescriptionDraft(found?.description ?? '');
      setSubtitleDraft(found?.subtitle ?? '');
      setFoldersDraft((found?.folders ?? []).join(', '));
      setFallbackAgentIdDraft(found?.fallback_agent_id ?? '');
    });
  }, [sectionId]);

  useEffect(() => {
    fetchScopeSuggestions().then(setScopeSuggestions);
  }, []);

  async function applyUpdate(fields: {
    name?: string; icon?: string; color?: string; description?: string;
    subtitle?: string; folders?: string[]; fallback_agent_id?: string;
  }) {
    const updated = await updateSection(sectionId, fields);
    setSection(updated);
    onSectionUpdated?.();
    return updated;
  }

  async function handleSaveName() {
    const name = nameDraft.trim();
    if (!name) return;
    setSavingName(true);
    try {
      await applyUpdate({ name });
    } finally {
      setSavingName(false);
    }
  }

  async function handleSaveDescription() {
    setSavingDescription(true);
    try {
      await applyUpdate({ description: descriptionDraft.trim() });
    } finally {
      setSavingDescription(false);
    }
  }

  async function handleSaveSubtitle() {
    setSavingSubtitle(true);
    try {
      await applyUpdate({ subtitle: subtitleDraft.trim() });
    } finally {
      setSavingSubtitle(false);
    }
  }

  async function handleSaveFolders() {
    setSavingFolders(true);
    try {
      const folders = foldersDraft.split(',').map((entry) => entry.trim()).filter((entry) => entry.length > 0);
      await applyUpdate({ folders });
    } finally {
      setSavingFolders(false);
    }
  }

  async function handleSaveFallbackAgentId() {
    setSavingFallbackAgentId(true);
    try {
      await applyUpdate({ fallback_agent_id: fallbackAgentIdDraft.trim() });
    } finally {
      setSavingFallbackAgentId(false);
    }
  }

  async function handleIconChange(iconId: string) {
    await applyUpdate({ icon: iconId });
  }

  async function handleColorChange(colorHex: string) {
    await applyUpdate({ color: colorHex });
  }

  async function handleVisualReset() {
    // "" is the backend's own clear-to-default sentinel, same convention
    // AgentDetailPanel's handleVisualReset already relies on.
    await applyUpdate({ icon: '', color: '' });
  }

  function openFoldersEditor() {
    setFoldersEditorDraft(section?.folders ?? []);
    setOpenFieldEditor('folders');
  }

  function toggleFolderInDraft(folder: string) {
    setFoldersEditorDraft((prev) => (prev.includes(folder) ? prev.filter((f) => f !== folder) : [...prev, folder]));
  }

  async function handleSaveFieldEditor() {
    if (!openFieldEditor) return;
    setSavingFieldEditor(true);
    try {
      if (openFieldEditor === 'description') {
        await applyUpdate({ description: descriptionDraft.trim() });
      } else if (openFieldEditor === 'subtitle') {
        await applyUpdate({ subtitle: subtitleDraft.trim() });
      } else if (openFieldEditor === 'folders') {
        const updated = await applyUpdate({ folders: foldersEditorDraft });
        setFoldersDraft(updated.folders.join(', '));
      }
      setOpenFieldEditor(null);
    } finally {
      setSavingFieldEditor(false);
    }
  }

  return (
    <>
      <div className="side-panel-overlay" onClick={onClose} />
      <aside className="side-panel" aria-label="Section details">
        <div className="side-panel-header">
          <span className="badge">Section detail</span>
          <button type="button" className="side-panel-close" aria-label="Close panel" onClick={onClose}>
            &times;
          </button>
        </div>
        {!section && (
          <div className="side-panel-body">
            <div className="side-panel-loading" data-testid="section-detail-loading">
              <span className="side-panel-loading-spinner" aria-hidden="true" />
              Loading section…
            </div>
          </div>
        )}
        {section && (
          <>
            <div className="side-panel-title">
              <h2>{section.name}</h2>
            </div>
            <div className="side-panel-tabs" role="tablist">
              {TABS.map((tab) => (
                <button
                  key={tab}
                  type="button"
                  role="tab"
                  aria-selected={activeTab === tab}
                  className={`side-panel-tab${activeTab === tab ? ' side-panel-tab--active' : ''}`}
                  onClick={() => setActiveTab(tab)}
                >
                  {TAB_LABELS[tab]}
                </button>
              ))}
            </div>
            <div className="side-panel-body">
              {activeTab === 'overview' && (
                <div className="side-panel-section" data-testid="section-overview-tab">
                  <h3>Overview</h3>
                  <div className="kv-list">
                    <div className="kv-row">
                      <span className="kv-key">Name</span>
                      <span>{section.name}</span>
                    </div>
                    <div className="kv-row">
                      <span className="kv-key">Subtitle</span>
                      <ExpandableText text={section.subtitle || 'No subtitle set yet'} />
                    </div>
                    <div className="kv-row">
                      <span className="kv-key">Description</span>
                      <ExpandableText text={section.description || 'No description set yet'} />
                    </div>
                    <div className="kv-row">
                      <span className="kv-key">Folders</span>
                      <span>{section.folders.length > 0 ? section.folders.join(', ') : 'No folders assigned yet'}</span>
                    </div>
                    <div className="kv-row">
                      <span className="kv-key">Fallback agent</span>
                      <span>{section.fallback_agent_id || 'None set'}</span>
                    </div>
                    <div className="kv-row">
                      <span className="kv-key">Agents ({section.agent_ids.length})</span>
                      <span>{section.agent_ids.length > 0 ? section.agent_ids.join(', ') : 'No agents assigned yet'}</span>
                    </div>
                  </div>
                </div>
              )}
              {activeTab === 'settings' && (
                <div className="side-panel-section" data-testid="section-settings-tab">
                  <h3>Name</h3>
                  <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                    <input
                      className="input"
                      value={nameDraft}
                      onChange={(event) => setNameDraft(event.target.value)}
                    />
                    <button
                      type="button"
                      className="btn"
                      disabled={savingName || !nameDraft.trim() || nameDraft.trim() === section.name}
                      onClick={handleSaveName}
                    >
                      Save
                    </button>
                  </div>

                  <h3 style={{ marginTop: 'var(--space-4)' }}>Description</h3>
                  <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                    <textarea
                      className="input"
                      rows={3}
                      style={{ width: '100%', resize: 'vertical' }}
                      placeholder="What this Section is for — shown on its own Overview tab."
                      value={descriptionDraft}
                      onChange={(event) => setDescriptionDraft(event.target.value)}
                    />
                    <button
                      type="button"
                      className="kv-expand-btn"
                      aria-label="Edit Description in a bigger view"
                      data-testid="expand-description"
                      onClick={() => setOpenFieldEditor('description')}
                    >
                      <span className="material-symbols-outlined">open_in_full</span>
                    </button>
                  </div>
                  <button
                    type="button"
                    className="btn"
                    style={{ marginTop: 'var(--space-2)' }}
                    disabled={savingDescription || descriptionDraft.trim() === (section.description ?? '')}
                    onClick={handleSaveDescription}
                  >
                    Save
                  </button>

                  <h3 style={{ marginTop: 'var(--space-4)' }}>Subtitle</h3>
                  <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                    <input
                      className="input"
                      style={{ width: '100%' }}
                      placeholder="Shown under the Section's title on the Agents Map"
                      value={subtitleDraft}
                      onChange={(event) => setSubtitleDraft(event.target.value)}
                    />
                    <button
                      type="button"
                      className="kv-expand-btn"
                      aria-label="Edit Subtitle in a bigger view"
                      data-testid="expand-subtitle"
                      onClick={() => setOpenFieldEditor('subtitle')}
                    >
                      <span className="material-symbols-outlined">open_in_full</span>
                    </button>
                    <button
                      type="button"
                      className="btn"
                      disabled={savingSubtitle || subtitleDraft.trim() === (section.subtitle ?? '')}
                      onClick={handleSaveSubtitle}
                    >
                      Save
                    </button>
                  </div>

                  <h3 style={{ marginTop: 'var(--space-4)' }}>Folders</h3>
                  <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                    <input
                      className="input"
                      style={{ width: '100%' }}
                      placeholder="e.g. Customers, Opportunities"
                      value={foldersDraft}
                      onChange={(event) => setFoldersDraft(event.target.value)}
                    />
                    <button
                      type="button"
                      className="kv-expand-btn"
                      aria-label="Edit Folders in a bigger view"
                      data-testid="expand-folders"
                      onClick={openFoldersEditor}
                    >
                      <span className="material-symbols-outlined">open_in_full</span>
                    </button>
                    <button
                      type="button"
                      className="btn"
                      disabled={savingFolders || foldersDraft.trim() === section.folders.join(', ')}
                      onClick={handleSaveFolders}
                    >
                      Save
                    </button>
                  </div>
                  <span className="item-row-meta">Which top-level vault folders this Section's own content index covers.</span>

                  <h3 style={{ marginTop: 'var(--space-4)' }}>Fallback agent</h3>
                  <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                    <input
                      className="input"
                      style={{ width: '100%' }}
                      placeholder="e.g. customer-hub"
                      value={fallbackAgentIdDraft}
                      onChange={(event) => setFallbackAgentIdDraft(event.target.value)}
                    />
                    <button
                      type="button"
                      className="btn"
                      disabled={savingFallbackAgentId || fallbackAgentIdDraft.trim() === (section.fallback_agent_id ?? '')}
                      onClick={handleSaveFallbackAgentId}
                    >
                      Save
                    </button>
                  </div>
                  <span className="item-row-meta">
                    Answers when a mentioned entity in this Section has no dedicated Expert. Leave blank for none.
                  </span>

                  <h3 style={{ marginTop: 'var(--space-4)' }}>Icon &amp; Color</h3>
                  <VisualPicker
                    selectedIcon={section.icon}
                    selectedColor={section.color}
                    onSelectIcon={handleIconChange}
                    onSelectColor={handleColorChange}
                    onReset={handleVisualReset}
                  />
                </div>
              )}
            </div>
          </>
        )}
      </aside>
      {openFieldEditor === 'description' && (
        <FieldEditorModal
          title="Description"
          onClose={() => setOpenFieldEditor(null)}
          onSave={handleSaveFieldEditor}
          saving={savingFieldEditor}
        >
          <textarea
            className="input field-editor-textarea"
            value={descriptionDraft}
            onChange={(event) => setDescriptionDraft(event.target.value)}
            placeholder="What this Section is for — shown on its own Overview tab."
            data-testid="field-editor-description-textarea"
          />
        </FieldEditorModal>
      )}
      {openFieldEditor === 'subtitle' && (
        <FieldEditorModal
          title="Subtitle"
          onClose={() => setOpenFieldEditor(null)}
          onSave={handleSaveFieldEditor}
          saving={savingFieldEditor}
        >
          <textarea
            className="input field-editor-textarea"
            value={subtitleDraft}
            onChange={(event) => setSubtitleDraft(event.target.value)}
            placeholder="Shown under the Section's title on the Agents Map"
            data-testid="field-editor-subtitle-textarea"
          />
        </FieldEditorModal>
      )}
      {openFieldEditor === 'folders' && (
        <FieldEditorModal
          title="Folders"
          description="Real top-level vault folders — select every one this Section's own content index covers."
          onClose={() => setOpenFieldEditor(null)}
          onSave={handleSaveFieldEditor}
          saving={savingFieldEditor}
        >
          {scopeSuggestions ? (
            <ChecklistPicker
              items={scopeSuggestions.folders.map((folder): ChecklistItem => ({ id: folder, label: folder }))}
              selectedIds={foldersEditorDraft}
              onToggle={toggleFolderInDraft}
              emptyLabel="No real vault folders found yet."
            />
          ) : (
            <p className="text-muted">Loading real vault folders…</p>
          )}
        </FieldEditorModal>
      )}
    </>
  );
}
