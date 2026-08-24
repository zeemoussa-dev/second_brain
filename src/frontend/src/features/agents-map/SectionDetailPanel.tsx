import { useEffect, useState } from 'react';
import { fetchSections, updateSection, type SectionSummary } from '../settings/settingsApiClient';
import { VisualPicker } from './VisualPicker';

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

  useEffect(() => {
    setSection(null);
    fetchSections().then((sections) => {
      const found = sections.find((s) => s.id === sectionId) ?? null;
      setSection(found);
      setNameDraft(found?.name ?? '');
      setDescriptionDraft(found?.description ?? '');
    });
  }, [sectionId]);

  async function applyUpdate(fields: { name?: string; icon?: string; color?: string; description?: string }) {
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
                      <span className="kv-key">Description</span>
                      <span>{section.description || 'No description set yet'}</span>
                    </div>
                    <div className="kv-row">
                      <span className="kv-key">Agents</span>
                      <span>{section.agent_ids.length}</span>
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
                    className="btn"
                    style={{ marginTop: 'var(--space-2)' }}
                    disabled={savingDescription || descriptionDraft.trim() === (section.description ?? '')}
                    onClick={handleSaveDescription}
                  >
                    Save
                  </button>

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
    </>
  );
}
