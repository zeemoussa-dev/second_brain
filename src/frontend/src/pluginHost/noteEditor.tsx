import { useCallback, useEffect, useState } from 'react';
import { ApiError } from '../api/client';
import { NoteEditor } from '../features/vault-browser/NoteEditor';
import { fetchNoteDetail, type NoteDetail } from '../features/vault-browser/client';

/** Editing a vault note from a plugin screen -- part of the host contract, not
 * a framework internal (requested by the Entities plugin, 2026-10-24).
 *
 * A plugin showing a Customer hub wants its "Personal Notes" editable in
 * place. Without this it would either hand the operator a read-only rendering
 * and a link away to the Vault, or carry its own editor -- and a second editor
 * means a second idea of what a note is, on files agents are writing at the
 * same time. The `BUG-078` argument for sharing the renderer applies with more
 * force here: a renderer that disagrees shows the wrong thing, an editor that
 * disagrees saves the wrong thing.
 *
 * **`sections` is a boundary, not a filter.** The sections not named are never
 * loaded into the editor and are never in a save: a save splices the edited
 * section back into the stored note, so the parts a plugin was not given are
 * carried across byte for byte. That is what makes it safe to give a plugin
 * one section of a note whose others belong to Hermes.
 *
 * **It can refuse to save, and that is the point.** The agents write these
 * same files. A save carries the version the editor opened and a file that
 * moved on since is refused, with the operator's text still on screen, rather
 * than one writer silently erasing the other.
 *
 * Available from `FRAMEWORK_API` 12 as an ADDITIVE export: the version did not
 * move for it (`ADR-063`'s precedent -- add the capability now, take it in
 * formally at the next planned move), so no installed plugin had to be
 * republished. A plugin built against this host and installed on an older one
 * fails its build on the missing module rather than being refused at load;
 * that is the cost the operator accepted on 2026-10-24.
 */
export interface VaultNoteEditorProps {
  /** The note's filename stem, as `/browse/<stem>` uses it. */
  stem: string;
  /** Limit display and editing to these `##` sections, by their heading text.
   *  Omitted, the whole note is shown. */
  sections?: string[];
  /** False renders the note without opening an editor on click. Default true. */
  editable?: boolean;
  /** Whether to offer "Tidy the typing", which sends the open section to
   *  Compass. Default FALSE here, unlike the framework's own note page: a
   *  plugin screen quietly spending the install's model budget is a decision
   *  its author should make on purpose. */
  offerTidy?: boolean;
  /** After a save that landed, with the note's new body. */
  onSaved?: (saved: { body: string; version: string }) => void;
}

export function VaultNoteEditor({
  stem,
  sections,
  editable = true,
  offerTidy = false,
  onSaved,
}: VaultNoteEditorProps) {
  const [note, setNote] = useState<NoteDetail | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  useEffect(() => {
    let current = true;
    setNote(null);
    setProblem(null);
    fetchNoteDetail(stem)
      .then((detail) => {
        if (current) setNote(detail);
      })
      .catch((error) => {
        if (!current) return;
        setProblem(
          error instanceof ApiError && error.status === 404
            ? `There is no indexed note called "${stem}".`
            : 'That note could not be opened.',
        );
      });
    return () => {
      current = false;
    };
  }, [stem]);

  // The editor hands back the whole note after a save; holding it here is what
  // lets a second edit carry the first one's version rather than the one this
  // component loaded with.
  const handleSaved = useCallback(
    (saved: { body: string; version: string }) => {
      setNote((previous) =>
        previous ? { ...previous, body: saved.body, version: saved.version } : previous,
      );
      onSaved?.(saved);
    },
    [onSaved],
  );

  if (problem) return <p className="error-text">{problem}</p>;
  if (!note) return <p className="text-muted">Opening the note…</p>;

  return (
    <NoteEditor
      stem={note.stem}
      body={note.body}
      version={note.version}
      editable={editable}
      forwardLinks={note.forward_links}
      only={sections}
      offerTidy={offerTidy}
      onSaved={handleSaved}
    />
  );
}
