import { useEffect, useState } from 'react';
import { fetchNoteDetail, type NoteDetail } from '../vault-browser/client';
import { NoteBody } from '../vault-browser/NoteBody';
import { addPersonNote } from './cockpitApiClient';

// Explicit Person-note fields, shown as labeled rows in a fixed, sane
// order -- name/type are already covered by the panel's own title/badge,
// so left out here. Anything in frontmatter NOT in this list still
// renders, via the generic fallback loop below (operator, 2026-08-25:
// "we might need... a Generic one if we don't have any matching
// style") -- so an unexpected/future field is never silently dropped.
const PERSON_FIELD_LABELS: Record<string, string> = {
  email: 'Email',
  phone: 'Phone',
  linkedin: 'LinkedIn',
};

// Clicking a Person chip used to navigate to /browse/:stem -- a real,
// separate page -- which meant leaving the Cockpit entirely (operator:
// "which means I lost track of the meeting"). This renders the note's
// real content inside the Cockpit's own side panel instead, reusing the
// app's existing .side-panel-overlay/.side-panel convention
// (AgentDetailPanel.tsx) so the meeting/email you were on is never
// unmounted.
export function PersonNotePanel({ stem, onClose }: { stem: string; onClose: () => void }) {
  const [detail, setDetail] = useState<NoteDetail | null>(null);
  const [noteText, setNoteText] = useState('');
  const [saving, setSaving] = useState(false);

  const load = () => fetchNoteDetail(stem).then(setDetail);
  useEffect(() => { setDetail(null); load(); }, [stem]);

  const handleSaveNote = (event: React.FormEvent) => {
    event.preventDefault();
    if (!noteText.trim() || saving) return;
    setSaving(true);
    addPersonNote(stem, noteText.trim())
      .then(() => { setNoteText(''); return load(); })
      .finally(() => setSaving(false));
  };

  const frontmatter = detail?.frontmatter ?? {};
  const knownEntries = Object.entries(PERSON_FIELD_LABELS)
    .filter(([key]) => frontmatter[key])
    .map(([key, label]) => ({ label, value: String(frontmatter[key]) }));
  const otherEntries = Object.entries(frontmatter)
    .filter(([key, value]) => !(key in PERSON_FIELD_LABELS) && key !== 'type' && key !== 'name' && key !== 'tags' && value)
    .map(([key, value]) => ({ label: key, value: Array.isArray(value) ? value.join(', ') : String(value) }));

  return (
    <>
      <div className="side-panel-overlay" onClick={onClose} />
      <aside className="side-panel" aria-label="Person note">
        <div className="side-panel-header">
          <span className="badge">Person</span>
          <button type="button" className="side-panel-close" aria-label="Close panel" onClick={onClose}>
            &times;
          </button>
        </div>
        {detail ? (
          <div className="side-panel-body">
            <div className="side-panel-section">
              <h2 style={{ marginTop: 0 }}>{detail.title}</h2>
              {(detail.tags.length > 0) && (
                <div className="action-list" style={{ marginBottom: 'var(--space-3)' }}>
                  {detail.tags.map((tag) => <span className="badge" key={tag}>{tag}</span>)}
                </div>
              )}
              {(knownEntries.length > 0 || otherEntries.length > 0) && (
                <div className="kv-list">
                  {[...knownEntries, ...otherEntries].map(({ label, value }) => (
                    <div className="kv-row" key={label}><span className="kv-key">{label}</span><span>{value}</span></div>
                  ))}
                </div>
              )}
            </div>
            <div className="side-panel-section">
              <NoteBody stem={detail.stem} body={detail.body} forwardLinks={detail.forward_links} />
            </div>
            <div className="side-panel-section">
              <h3>Add a note</h3>
              <form onSubmit={handleSaveNote}>
                <textarea
                  className="input" rows={3}
                  placeholder="Note about this person, saved to their own note…"
                  value={noteText} onChange={(e) => setNoteText(e.target.value)}
                  disabled={saving}
                />
                <button type="submit" className="btn btn-primary" style={{ marginTop: 'var(--space-2)' }} disabled={!noteText.trim() || saving}>
                  Save note
                </button>
              </form>
            </div>
          </div>
        ) : (
          <div className="side-panel-body"><p className="text-muted">Loading...</p></div>
        )}
      </aside>
    </>
  );
}
