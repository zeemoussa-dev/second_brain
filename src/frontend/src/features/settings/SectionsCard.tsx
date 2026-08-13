import { useEffect, useState } from 'react';
import {
  createSection,
  deleteSection,
  fetchSections,
  renameSection,
  type SectionSummary,
} from './settingsApiClient';

export function SectionsCard() {
  const [sections, setSections] = useState<SectionSummary[] | null>(null);
  const [newName, setNewName] = useState('');
  const [renameDrafts, setRenameDrafts] = useState<Record<string, string>>({});
  const [blockedMessage, setBlockedMessage] = useState<string | null>(null);

  function reload() {
    fetchSections().then(setSections);
  }

  useEffect(() => {
    reload();
  }, []);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    const name = newName.trim();
    if (!name) return;
    await createSection(name);
    setNewName('');
    reload();
  }

  async function handleRename(sectionId: string, currentName: string) {
    const name = (renameDrafts[sectionId] ?? currentName).trim();
    if (!name) return;
    await renameSection(sectionId, name);
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
        Business-domain groupings agents belong to, shown as Hubs on the
        Agents Map. Independent of an agent's Worker/Producer/Expert Type.
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
            return (
              <div className="item-row" key={section.id} data-section-row={section.id}>
                <div className="item-row-main">
                  <span className="item-row-title">{section.name}</span>
                  <span className="item-row-meta">
                    {blocked ? `${section.agent_ids.length} agent(s) assigned` : 'No agents assigned'}
                  </span>
                </div>
                <div className="item-row-actions">
                  <input
                    className="input"
                    style={{ width: 'auto' }}
                    value={renameDrafts[section.id] ?? section.name}
                    onChange={(event) =>
                      setRenameDrafts((prev) => ({ ...prev, [section.id]: event.target.value }))
                    }
                  />
                  <button type="button" className="btn" onClick={() => handleRename(section.id, section.name)}>
                    Rename
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
              </div>
            );
          })}
        </div>
      )}
      <form onSubmit={handleCreate} className="item-row-actions">
        <label className="text-muted" htmlFor="newSectionName" style={{ fontSize: 'var(--font-size-sm)' }}>
          Section name
        </label>
        <input
          id="newSectionName"
          className="input"
          placeholder="e.g. Operations"
          value={newName}
          onChange={(event) => setNewName(event.target.value)}
        />
        <button type="submit" className="btn btn-primary">Create section</button>
      </form>
    </div>
  );
}
