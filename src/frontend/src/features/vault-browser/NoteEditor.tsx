import { useEffect, useMemo, useRef, useState } from 'react';
import { ApiError } from '../../api/client';
import { saveNoteBody, tidyText, type NoteSummary } from './client';
import { MarkdownEditor } from './MarkdownEditor';
import { NoteBody } from './NoteBody';
import {
  extractHeadings,
  findEmptySections,
  sectionRanges,
  type SectionRange,
  type TocHeading,
} from './tableOfContents';

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
  // WHICH section is open, not merely whether one is: clicking a paragraph
  // used to open the entire note as one textarea, which loses the place you
  // clicked and puts every other section one stray keystroke away from being
  // rewritten (operator, 2026-10-24: "Its not anymore that Section I am
  // Clicking"). `null` means nothing is being edited.
  const [section, setSection] = useState<SectionRange | null>(null);
  const editing = section !== null;
  // Only the open section's text. The rest of the note is never in the
  // textarea, so it cannot be touched by accident.
  const [draft, setDraft] = useState('');
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
    setSection(null);
    setDraft('');
    setState('idle');
    setRefusal(null);
  }, [stem, body]);

  const emptySections = useMemo(() => findEmptySections(body), [body]);
  const sections = useMemo(() => sectionRanges(body), [body]);

  // The ToC is the whole note's, always — while a section is open the body is
  // rendered as two fragments, and each would otherwise report only its own
  // half of the headings.
  const headings = useMemo(() => extractHeadings(body), [body]);
  useEffect(() => {
    onHeadingsExtracted?.(headings);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- onHeadingsExtracted is a fresh closure each render; keying off headings avoids a notify loop.
  }, [headings]);

  /** Opens one section. `caretInBody` is an offset into the WHOLE note (what
   *  an empty-section placeholder knows); it is translated to the section's
   *  own coordinates, because that is what the textarea holds. */
  function beginEditing(target: SectionRange | null, caretInBody?: number) {
    if (!editable || !target) return;
    caretOnOpen.current =
      caretInBody === undefined ? null : Math.max(0, caretInBody - target.start);
    setDraft(body.slice(target.start, target.end));
    setSection(target);
  }

  function stopEditing() {
    setSection(null);
    setDraft('');
  }

  /** The section the click landed in: the nearest heading at or above the
   *  clicked block, or the opening text when there is none above it. */
  function sectionAtClick(target: HTMLElement, container: HTMLElement): SectionRange | null {
    let block: HTMLElement | null = target;
    while (block && block.parentElement && block.parentElement !== container) {
      block = block.parentElement;
    }
    let scan: Element | null = block;
    while (scan) {
      const id = scan instanceof HTMLElement ? scan.id : '';
      if (/^H[1-6]$/.test(scan.tagName) && id) {
        return sections.find((candidate) => candidate.slug === id) ?? null;
      }
      scan = scan.previousElementSibling;
    }
    return sections.find((candidate) => candidate.slug === null) ?? sections[0] ?? null;
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

  /** The edited section put back where it came from. The file on disk is
   *  always the whole note, so a section edit is still a whole-note save —
   *  the difference is that everything outside `[start, end)` is carried
   *  across untouched rather than round-tripped through a textarea. */
  function composed(sectionText: string, target: SectionRange): string {
    return body.slice(0, target.start) + sectionText + body.slice(target.end);
  }

  async function save(text: string) {
    if (!section) return;
    const whole = composed(text, section);
    if (whole === body) {
      setState('idle');
      return;
    }
    setState('saving');
    setRefusal(null);
    try {
      const result = await saveNoteBody(stem, whole, heldVersion.current);
      heldVersion.current = result.version;
      setState('saved');
      onSaved({ body: whole, version: result.version });
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

  if (editing && section) {
    return (
      <div className="note-editing">
        {/* The note either side of the open section stays rendered, so a
            section edit reads as a section edit rather than as the document
            being replaced by a box of markdown. */}
        {section.start > 0 && (
          <div className="note-reading is-context">
            <NoteBody stem={stem} body={body.slice(0, section.start)} forwardLinks={forwardLinks} />
          </div>
        )}
        <p className="note-editing-which">
          Editing <strong>{section.text}</strong>
        </p>
        {/* A textarea holds one font and cannot style its own contents, which
            is why clicking into a note used to turn it into flat monospace
            (operator, 2026-10-24). This one keeps the note's own type while
            you edit, hides the markers on lines you are not standing on, and
            draws a table as a table -- over the raw markdown, never a
            document model, so nothing is rewritten behind you. */}
        <MarkdownEditor
          value={draft}
          autofocusAt={caretOnOpen.current ?? undefined}
          onChange={(next) => {
            setDraft(next);
            setState('dirty');
          }}
          onSave={() => void save(draft)}
          onCancel={() => {
            setState('idle');
            stopEditing();
          }}
          onBlur={() => {
            if (state === 'dirty') void save(draft);
            // A conflict keeps the editor open: closing it would put the
            // operator's unsaved text behind a rendered copy of the version
            // that beat it.
            if (state !== 'conflict' && state !== 'failed') stopEditing();
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
            Editing this section only · saves itself when you pause · Ctrl+S now · Esc to
            drop changes
          </span>
        </div>
        <SaveStatus state={state} refusal={refusal} />
        {section.end < body.length && (
          <div className="note-reading is-context">
            <NoteBody stem={stem} body={body.slice(section.end)} forwardLinks={forwardLinks} />
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      className={`note-reading ${editable ? 'is-editable' : ''}`}
      // A click opens the SECTION it landed in, not the note. Not on a link:
      // following a wikilink is the other thing a click in a note means, and
      // it is the one the operator asked for explicitly.
      onClick={(event) => {
        const target = event.target as HTMLElement;
        if (target.closest('a, button')) return;
        beginEditing(sectionAtClick(target, event.currentTarget));
      }}
    >
      <NoteBody
        stem={stem}
        body={body}
        forwardLinks={forwardLinks}
        emptySections={editable ? emptySections : []}
        onAddToSection={(offset) =>
          beginEditing(
            // The placeholder's offset is inside its own section by
            // construction: it is the character after that heading's line.
            sections.find((candidate) => offset > candidate.start && offset <= candidate.end) ?? null,
            offset,
          )
        }
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
