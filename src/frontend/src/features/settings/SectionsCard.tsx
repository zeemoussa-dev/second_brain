import { useEffect, useState } from 'react';
import { VisualPicker } from '../agents-map/VisualPicker';
import { getVisualIconName } from '../agents-map/visualOptions';
import { Field } from './Field';
import { fetchVaultOverview } from './vaultApiClient';
import {
  createSection,
  deleteSection,
  fetchSections,
  updateSection,
  type SectionSummary,
} from './settingsApiClient';

export function SectionsCard() {
  const [sections, setSections] = useState<SectionSummary[] | null>(null);
  const [allFolders, setAllFolders] = useState<string[]>([]);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [nameDrafts, setNameDrafts] = useState<Record<string, string>>({});
  const [descriptionDrafts, setDescriptionDrafts] = useState<Record<string, string>>({});
  const [fallbackAgentDrafts, setFallbackAgentDrafts] = useState<Record<string, string>>({});
  const [newName, setNewName] = useState('');
  const [blockedMessage, setBlockedMessage] = useState<string | null>(null);

  function reload() {
    fetchSections().then((result) => {
      setSections(result);
      setNameDrafts(Object.fromEntries(result.map((section) => [section.id, section.name])));
      setDescriptionDrafts(Object.fromEntries(result.map((section) => [section.id, section.description ?? ''])));
      setFallbackAgentDrafts(Object.fromEntries(result.map((section) => [section.id, section.fallback_agent_id ?? ''])));
    });
  }

  useEffect(() => {
    reload();
    // Same real, live folder list Vault Overview / Index Filtering
    // already show -- never a hardcoded set, so a new top-level Work/
    // folder shows up here automatically the next time it has a note.
    fetchVaultOverview().then((overview) => setAllFolders(Object.keys(overview.folder_counts).sort()));
  }, []);

  function toggleExpanded(id: string) {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    const name = newName.trim();
    if (!name) return;
    await createSection(name);
    setNewName('');
    reload();
  }

  async function handleSaveName(section: SectionSummary) {
    const name = (nameDrafts[section.id] ?? section.name).trim();
    if (!name) return;
    await updateSection(section.id, { name });
    reload();
  }

  async function handleSaveDescription(section: SectionSummary) {
    await updateSection(section.id, { description: (descriptionDrafts[section.id] ?? '').trim() });
    reload();
  }

  async function handleIconChange(section: SectionSummary, icon: string) {
    await updateSection(section.id, { icon });
    reload();
  }

  async function handleColorChange(section: SectionSummary, color: string) {
    await updateSection(section.id, { color });
    reload();
  }

  async function handleVisualReset(section: SectionSummary) {
    await updateSection(section.id, { icon: '', color: '' });
    reload();
  }

  async function handleSaveFallbackAgent(section: SectionSummary) {
    await updateSection(section.id, { fallback_agent_id: (fallbackAgentDrafts[section.id] ?? '').trim() });
    reload();
  }

  async function handleToggleFolder(section: SectionSummary, folder: string) {
    const next = section.folders.includes(folder)
      ? section.folders.filter((f) => f !== folder)
      : [...section.folders, folder];
    await updateSection(section.id, { folders: next });
    reload();
  }

  async function handleDelete(sectionId: string) {
    setBlockedMessage(null);
    const result = await deleteSection(sectionId);
    if (!result.ok) {
      setBlockedMessage(result.message);
      return;
    }
    reload();
  }

  return (
    <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
      <h2>Sections</h2>
      <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
        Business-domain groupings agents belong to, shown as Hubs on the Agents Map. Independent of an agent's
        Worker/Producer/Expert Type. Click a section to expand it and edit its name, description, icon, or color —
        the same settings reachable from its Hub on the map.
      </p>
      {blockedMessage && (
        <p className="text-muted" data-testid="sections-blocked-message">
          <span className="badge badge-danger">Deletion blocked</span> {blockedMessage}
        </p>
      )}
      {sections && (
        <div className="item-list" style={{ marginBottom: 'var(--space-4)' }}>
          {sections.map((section) => {
            const blocked = section.agent_ids.length > 0;
            const isOpen = expanded[section.id] ?? false;
            return (
              <div
                className="item-row"
                key={section.id}
                data-section-row={section.id}
                style={{ flexDirection: 'column', alignItems: 'stretch' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--space-2)' }}>
                  <button
                    type="button"
                    onClick={() => toggleExpanded(section.id)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: 'inherit',
                      background: 'none', border: 'none', cursor: 'pointer', padding: 0, textAlign: 'left', flex: 1,
                    }}
                  >
                    <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: '18px', color: 'var(--color-text-muted)' }}>
                      {isOpen ? 'expand_more' : 'chevron_right'}
                    </span>
                    <span className="material-symbols-outlined" aria-hidden="true" style={{ fontSize: '22px', color: section.color ?? 'var(--color-accent)' }}>
                      {getVisualIconName(section.icon) ?? 'hub'}
                    </span>
                    <span className="item-row-title">
                      {section.name}{' '}
                      <span className="item-row-meta">
                        {blocked ? `${section.agent_ids.length} agent(s) assigned` : 'No agents assigned'}
                      </span>
                    </span>
                  </button>
                  <button
                    type="button"
                    className="btn btn-danger"
                    disabled={blocked}
                    title={blocked ? 'Move all agents out of this section first' : undefined}
                    onClick={() => handleDelete(section.id)}
                  >
                    Delete
                  </button>
                </div>
                {isOpen && (
                  <div style={{ marginTop: 'var(--space-3)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                    <Field label="Name">
                      <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                        <input
                          className="input"
                          value={nameDrafts[section.id] ?? section.name}
                          onChange={(event) => setNameDrafts((prev) => ({ ...prev, [section.id]: event.target.value }))}
                        />
                        <button type="button" className="btn" onClick={() => handleSaveName(section)}>Save</button>
                      </div>
                    </Field>
                    <Field label="Description">
                      <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                        <textarea
                          className="input"
                          rows={2}
                          style={{ width: '100%', resize: 'vertical' }}
                          value={descriptionDrafts[section.id] ?? ''}
                          onChange={(event) => setDescriptionDrafts((prev) => ({ ...prev, [section.id]: event.target.value }))}
                        />
                        <button type="button" className="btn" onClick={() => handleSaveDescription(section)}>Save</button>
                      </div>
                    </Field>
                    <Field label="Icon & color">
                      <VisualPicker
                        selectedIcon={section.icon}
                        selectedColor={section.color}
                        onSelectIcon={(icon) => handleIconChange(section, icon)}
                        onSelectColor={(color) => handleColorChange(section, color)}
                        onReset={() => handleVisualReset(section)}
                      />
                    </Field>
                    <Field label="Folders (this Section's own content index)">
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
                        {allFolders.map((folder) => {
                          const checked = section.folders.includes(folder);
                          return (
                            <label
                              key={folder}
                              className={`badge ${checked ? 'badge-success' : ''}`}
                              style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                            >
                              <input
                                type="checkbox"
                                checked={checked}
                                onChange={() => handleToggleFolder(section, folder)}
                                style={{ margin: 0 }}
                              />
                              {folder}
                            </label>
                          );
                        })}
                        {allFolders.length === 0 && <span className="text-muted">No folders found yet.</span>}
                      </div>
                    </Field>
                    <Field label="Fallback agent (Hermes profile name)">
                      <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                        <input
                          className="input"
                          placeholder="e.g. customer-hub"
                          value={fallbackAgentDrafts[section.id] ?? ''}
                          onChange={(event) => setFallbackAgentDrafts((prev) => ({ ...prev, [section.id]: event.target.value }))}
                        />
                        <button type="button" className="btn" onClick={() => handleSaveFallbackAgent(section)}>Save</button>
                      </div>
                      <span className="item-row-meta">
                        Answers when a mentioned entity in this Section has no dedicated Expert. Leave blank for none.
                      </span>
                    </Field>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
      <form onSubmit={handleCreate} className="item-row-actions" style={{ alignItems: 'flex-end' }}>
        <Field label="Section name">
          <input
            className="input"
            placeholder="e.g. Operations"
            value={newName}
            onChange={(event) => setNewName(event.target.value)}
          />
        </Field>
        <button type="submit" className="btn btn-primary">Create section</button>
      </form>
    </div>
  );
}
