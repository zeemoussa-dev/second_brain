import { useEffect, useMemo, useRef, useState } from 'react';
import { ApiError } from '../../api/client';
import { saveNoteBody, tidyText, type NoteSummary } from './client';
import { NoteBody } from './NoteBody';
import { findEmptySections, type TocHeading } from './tableOfContents';

/** How long after the last keystroke the note saves itself. Long enough that
 *  a sentence is one save rather than forty, short enough that walking away
 *  mid-thought does not lose it. */
const AUTOSAVE_PAUSE_MS = 1200;

type SaveState = 'idle' | 'dirty' | 'saving' | 'saved' | 'conflict' | 'failed';

/** The note, read and written in the same place (operator, 2026-10-24: "Is
 * there a way to edit the text in place like you do in apps instead of Having
 * a Textbox and a Button").
 *
 * Click the text and it becomes editable where it sits, in the same type at
 * the same width, with no mode switch to find and no Save to press: it saves
 * itself when you pause, when you leave, or on Ctrl+S. What you edit is the
 * markdown itself, so `**bold**` shows its asterisks while you are in it and
 * renders again when you leave -- the alternative is a WYSIWYG that rewrites
 * markdown on save, on notes that agents parse.
 *
 * **It can refuse to save, and that is the point.** The agents write these
 * same files. A save carries the version the editor opened, and a file that
 * moved on since is refused with the operator's text still on screen, rather
 * than one writer silently erasing the other.
 */
export function NoteEditor({
  stem,
  body,
  version,
  editable,
  forwardLinks,
  onHeadingsExtracted,
  onSaved,
}: {
  stem: string;
  body: string;
  version: string;
  editable: boolean;
  forwardLinks: NoteSummary[];
  onHeadingsExtracted?: (headings: TocHeading[]) => void;
  onSaved: (saved: { body: string; version: string }) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(body);
  const [state, setState] = useState<SaveState>('idle');
  const [refusal, setRefusal] = useState<string | null>(null);
  const textarea = useRef<HTMLTextAreaElement | null>(null);
  // What the draft was before Compass touched it, so "undo" is exact rather
  // than a second trip to a model to put it back.
  const [beforeTidy, setBeforeTidy] = useState<string | null>(null);
  const [tidying, setTidying] = useState(false);
  // The version moves with every successful save; the one the editor holds has
  // to move with it, or typing a second sentence would conflict with itself.
  const heldVersion = useRef(version);
  const caretOnOpen = useRef<number | null>(null);

  useEffect(() => {
    heldVersion.current = version;
  }, [version]);

  // A note replaced underneath the editor (navigating to another one) starts
  // clean rather than carrying the previous note's draft into it.
  useEffect(() => {
    setEditing(false);
    setDraft(body);
    setState('idle');
    setRefusal(null);
  }, [stem, body]);

  const emptySections = useMemo(() => findEmptySections(body), [body]);

  function beginEditing(offset?: number) {
    if (!editable) return;
    caretOnOpen.current = offset ?? null;
    setDraft(body);
    setEditing(true);
  }

  // Focus and caret have to wait for the textarea to exist, and the caret is
  // the whole point of clicking an empty section: you land where the missing
  // content goes, not at the top of the note.
  useEffect(() => {
    if (!editing || !textarea.current) return;
    const field = textarea.current;
    field.style.height = 'auto';
    field.style.height = `${field.scrollHeight}px`;
    field.focus();
    const at = caretOnOpen.current ?? field.value.length;
    field.setSelectionRange(at, at);
  }, [editing]);

  async function save(text: string) {
    if (text === body) {
      setState('idle');
      return;
    }
    setState('saving');
    setRefusal(null);
    try {
      const result = await saveNoteBody(stem, text, heldVersion.current);
      heldVersion.current = result.version;
      setState('saved');
      onSaved({ body: text, version: result.version });
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setState('conflict');
        setRefusal(detailOf(error));
        return;
      }
      setState('failed');
      setRefusal(error instanceof Error ? detailOf(error) : 'The note could not be saved.');
    }
  }

  // Saves on a pause. Cleared on every keystroke, so it fires once per pause
  // rather than once per character.
  useEffect(() => {
    if (!editing || state !== 'dirty') return;
    const timer = setTimeout(() => void save(draft), AUTOSAVE_PAUSE_MS);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `save` closes over draft; re-running on it would restart the timer forever.
  }, [draft, editing, state]);

  async function tidy() {
    setTidying(true);
    setRefusal(null);
    try {
      const result = await tidyText(draft);
      if (!result.changed) {
        setState('idle');
        setRefusal('Nothing to fix — Compass found no spelling mistakes.');
        return;
      }
      setBeforeTidy(draft);
      setDraft(result.text);
      // Deliberately NOT saved: a model rewrote the operator's words, so the
      // operator gets to look at it. Marking it dirty is what makes the
      // ordinary autosave pick it up once they carry on.
      setState('dirty');
    } catch (error) {
      setState('failed');
      setRefusal(error instanceof Error ? detailOf(error) : 'Compass could not tidy this.');
    } finally {
      setTidying(false);
    }
  }

  if (editing) {
    return (
      <div className="note-editing">
        <textarea
          ref={textarea}
          className="note-body note-editor-field"
          value={draft}
          spellCheck
          aria-label="Note text"
          onChange={(event) => {
            setDraft(event.target.value);
            setState('dirty');
            const field = event.target;
            field.style.height = 'auto';
            field.style.height = `${field.scrollHeight}px`;
          }}
          onBlur={() => {
            if (state === 'dirty') void save(draft);
            // A conflict keeps the editor open: closing it would put the
            // operator's unsaved text behind a rendered copy of the version
            // that beat it.
            if (state !== 'conflict' && state !== 'failed') setEditing(false);
          }}
          onKeyDown={(event) => {
            if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
              event.preventDefault();
              void save(draft);
            }
            if (event.key === 'Escape') {
              setDraft(body);
              setState('idle');
              setEditing(false);
            }
          }}
        />
        <div className="note-editor-bar">
          <button
            type="button"
            className="btn btn-compact"
            disabled={tidying || !draft.trim()}
            // onMouseDown, not onClick: the textarea's blur fires first and
            // would close the editor out from under the button.
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => void tidy()}
            title="Compass fixes spelling and punctuation only — links, headings and lists are checked and left alone"
          >
            {tidying ? 'Tidying…' : '✨ Tidy the typing'}
          </button>
          {beforeTidy !== null && (
            <button
              type="button"
              className="btn btn-compact"
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => {
                setDraft(beforeTidy);
                setBeforeTidy(null);
                setState('dirty');
              }}
            >
              Undo tidy
            </button>
          )}
          <span className="note-editor-hint">
            Saves itself when you pause · Ctrl+S now · Esc to drop changes
          </span>
        </div>
        <SaveStatus state={state} refusal={refusal} />
      </div>
    );
  }

  return (
    <div
      className={`note-reading ${editable ? 'is-editable' : ''}`}
      // A click anywhere in the text starts editing there-ish. Not on a link:
      // following a wikilink is the other thing a click in a note means, and
      // it is the one the operator asked for explicitly.
      onClick={(event) => {
        if ((event.target as HTMLElement).closest('a, button')) return;
        beginEditing();
      }}
    >
      <NoteBody
        stem={stem}
        body={body}
        forwardLinks={forwardLinks}
        onHeadingsExtracted={onHeadingsExtracted}
        emptySections={editable ? emptySections : []}
        onAddToSection={(offset) => beginEditing(offset)}
      />
      {state === 'saved' && <SaveStatus state={state} refusal={null} />}
    </div>
  );
}

function SaveStatus({ state, refusal }: { state: SaveState; refusal: string | null }) {
  if (state === 'conflict' || state === 'failed') {
    return (
      <p className="note-save-refusal" role="alert">
        {refusal}
        {state === 'conflict' && (
          <>
            {' '}
            <button type="button" onClick={() => window.location.reload()}>
              Reload the note
            </button>
          </>
        )}
      </p>
    );
  }
  const said =
    state === 'saving' ? 'Saving…' : state === 'saved' ? 'Saved' : state === 'dirty' ? 'Unsaved' : '';
  if (!said) return null;
  return (
    <p className={`note-save-state is-${state}`} role="status">
      {said}
    </p>
  );
}

/** The backend's own words. Every refusal here is written to be read by the
 *  person who hit it -- "an agent writes these files too" explains itself in a
 *  way "409" never will. */
function detailOf(error: Error): string {
  const body = error.message?.trim() ?? '';
  try {
    const parsed = JSON.parse(body);
    if (typeof parsed?.detail === 'string') return parsed.detail;
  } catch {
    // Not JSON: the message as it stands is the best available.
  }
  return body || 'The note could not be saved.';
}
