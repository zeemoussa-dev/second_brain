import { useEffect, useRef } from 'react';
import { defaultKeymap, history, historyKeymap } from '@codemirror/commands';
import { markdown, markdownLanguage } from '@codemirror/lang-markdown';
import { HighlightStyle, syntaxHighlighting, syntaxTree } from '@codemirror/language';
import { EditorState, StateField, type Extension, type Text } from '@codemirror/state';
import {
  Decoration,
  EditorView,
  ViewPlugin,
  WidgetType,
  keymap,
  type DecorationSet,
  type ViewUpdate,
} from '@codemirror/view';
import { tags } from '@lezer/highlight';

/** Live preview: the note keeps looking like the note while you edit it
 *  (operator, 2026-10-24: "If we can Follow the Same style of Text instead of
 *  Shifting completely to plane Text", and "render the Tables as tables when
 *  Editing").
 *
 * **CodeMirror over the raw markdown, never a document model.** It edits the
 * source string and only DECORATES it, so nothing is normalised, reordered or
 * rewritten behind the operator -- which matters here more than usual: these
 * notes are written and parsed by agents, and a `[[wikilink]]` that a
 * WYSIWYG retyped is a broken link. A textarea could not do this; it holds one
 * font and cannot style its own contents, which is why clicking into a note
 * used to turn it into flat monospace.
 *
 * Three things make it read like the note rather than like source:
 *
 * - **Type that matches the rendered note** -- headings are heading-sized, bold
 *   is bold, body text is the body font, code is the only monospace.
 * - **Markers hide on lines the caret is not on.** `## ` and `**` stay real
 *   characters in the file; they are just not drawn while you are elsewhere,
 *   and reappear the moment you put the caret on that line, which is when you
 *   need to see what you are editing.
 * - **A table draws as a table** until the caret enters it, then it is source
 *   again. Editing a rendered table cell-by-cell is where an editor starts
 *   rewriting pipes on the operator's behalf, and this one never does.
 */
export function MarkdownEditor({
  value,
  onChange,
  onSave,
  onCancel,
  onBlur,
  autofocusAt,
}: {
  value: string;
  onChange: (next: string) => void;
  onSave: () => void;
  onCancel: () => void;
  onBlur: () => void;
  /** Where the caret goes when the editor opens — the character the operator
   *  clicked, so editing starts where they were looking. */
  autofocusAt?: number;
}) {
  const host = useRef<HTMLDivElement | null>(null);
  const view = useRef<EditorView | null>(null);
  // The callbacks are fresh closures every render; the editor is built once,
  // so it reads them through a ref rather than being torn down and rebuilt
  // (which would lose the caret, the selection and the undo history).
  const handlers = useRef({ onChange, onSave, onCancel, onBlur });
  handlers.current = { onChange, onSave, onCancel, onBlur };
  // Destroying a FOCUSED editor fires a blur, and the blur handler means "the
  // operator clicked away", which closes the section. React StrictMode mounts
  // every effect, tears it down and mounts it again, so in development the
  // editor opened and vanished instantly -- a flicker and nothing else
  // (operator, 2026-10-24: "the Screen Flicker to show something but It
  // Disappear Straight away"). Reset on each mount, because the ref outlives
  // the double invocation that sets it.
  const tearingDown = useRef(false);

  useEffect(() => {
    if (!host.current) return;
    tearingDown.current = false;

    const state = EditorState.create({
      doc: value,
      extensions: [
        history(),
        keymap.of([
          {
            key: 'Mod-s',
            preventDefault: true,
            run: () => {
              handlers.current.onSave();
              return true;
            },
          },
          {
            key: 'Escape',
            run: () => {
              handlers.current.onCancel();
              return true;
            },
          },
          ...historyKeymap,
          ...defaultKeymap,
        ]),
        markdown({ base: markdownLanguage }),
        syntaxHighlighting(NOTE_HIGHLIGHT),
        livePreview,
        EditorView.lineWrapping,
        NOTE_THEME,
        EditorView.updateListener.of((update) => {
          if (update.docChanged) handlers.current.onChange(update.state.doc.toString());
        }),
        EditorView.domEventHandlers({
          blur: () => {
            // A blur caused by this editor being torn down is not the
            // operator leaving it.
            if (!tearingDown.current) handlers.current.onBlur();
            return false;
          },
        }),
      ],
    });

    const editor = new EditorView({ state, parent: host.current });
    view.current = editor;
    const at = Math.min(autofocusAt ?? state.doc.length, state.doc.length);
    editor.dispatch({ selection: { anchor: at } });
    editor.focus();

    return () => {
      tearingDown.current = true;
      editor.destroy();
      view.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- built once per mount; `value` is the INITIAL document, and re-running on it would rebuild the editor under the operator's cursor on every keystroke.
  }, []);

  // A change from outside (Compass tidied the draft, or Undo put it back) has
  // to reach the document; a change the editor itself made is already there
  // and must not be re-applied, which would bounce the caret to the end.
  useEffect(() => {
    const editor = view.current;
    if (!editor || editor.state.doc.toString() === value) return;
    editor.dispatch({
      changes: { from: 0, to: editor.state.doc.length, insert: value },
    });
  }, [value]);

  return <div className="note-live-editor" ref={host} />;
}

/** Markdown's own tokens, in the note's type. Sizes are the rendered note's,
 *  so a heading does not change size when the caret lands on it. */
const NOTE_HIGHLIGHT = HighlightStyle.define([
  { tag: tags.heading1, fontSize: 'var(--font-size-xl)', fontWeight: '600', lineHeight: '1.3' },
  { tag: tags.heading2, fontSize: 'var(--font-size-lg)', fontWeight: '600', lineHeight: '1.3' },
  { tag: tags.heading3, fontSize: 'var(--font-size-base)', fontWeight: '600' },
  { tag: tags.strong, fontWeight: '700' },
  { tag: tags.emphasis, fontStyle: 'italic' },
  { tag: tags.strikethrough, textDecoration: 'line-through' },
  { tag: tags.link, color: 'var(--color-accent)' },
  { tag: tags.url, color: 'var(--color-accent)' },
  { tag: tags.monospace, fontFamily: 'var(--font-mono)', fontSize: '0.9em' },
  { tag: tags.quote, color: 'var(--color-text-muted)', fontStyle: 'italic' },
  // The markers themselves, for the line the caret IS on: visible, but quiet
  // enough that the prose still reads as prose.
  { tag: tags.processingInstruction, color: 'var(--color-text-muted)', opacity: '0.55' },
]);

const NOTE_THEME = EditorView.theme({
  '&': {
    color: 'var(--color-text)',
    backgroundColor: 'transparent',
    fontFamily: 'var(--font-sans)',
    fontSize: 'var(--font-size-base)',
  },
  '&.cm-focused': { outline: 'none' },
  '.cm-content': { padding: '0', lineHeight: '1.7', caretColor: 'var(--color-text)' },
  '.cm-line': { padding: '0' },
  '.cm-cursor, .cm-dropCursor': { borderLeftColor: 'var(--color-text)' },
  '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection': {
    backgroundColor: 'var(--color-accent-muted)',
  },
  '.cm-scroller': { fontFamily: 'inherit', lineHeight: '1.7' },
});

/** The syntax a reader does not need to see. Each entry is a node type from
 *  the markdown grammar whose own characters are formatting rather than
 *  content -- `##`, `**`, the backticks around code. */
const MARKER_NODES = new Set([
  'HeaderMark',
  'EmphasisMark',
  'StrikethroughMark',
  'CodeMark',
  'QuoteMark',
  'LinkMark',
]);

const hiddenMark = Decoration.replace({});

class TableWidget extends WidgetType {
  // Declared rather than a constructor parameter property: this project
  // compiles with `erasableSyntaxOnly`, which allows only type syntax that
  // vanishes at build time, and a parameter property emits a real assignment.
  rows: string[][];

  constructor(rows: string[][]) {
    super();
    this.rows = rows;
  }

  /** Two tables with the same cells are the same widget, so typing elsewhere
   *  in the note does not rebuild and flicker this one. */
  eq(other: TableWidget): boolean {
    return JSON.stringify(other.rows) === JSON.stringify(this.rows);
  }

  toDOM(): HTMLElement {
    const table = document.createElement('table');
    table.className = 'note-live-table';
    const [head, ...body] = this.rows;
    if (head) {
      const header = table.createTHead().insertRow();
      head.forEach((cell) => {
        const th = document.createElement('th');
        th.textContent = cell;
        header.appendChild(th);
      });
    }
    const tbody = table.createTBody();
    body.forEach((cells) => {
      const row = tbody.insertRow();
      cells.forEach((cell) => {
        row.insertCell().textContent = cell;
      });
    });
    return table;
  }

  /** The caret cannot be placed inside the drawn table: clicking it puts the
   *  caret at its edge and the source appears, which is the one way to edit a
   *  table without this editor ever rewriting a pipe itself. */
  ignoreEvent(): boolean {
    return false;
  }
}

/** Markers hidden — inline decorations, recomputed as the document and the
 *  caret move, which is what makes it "live". */
const markerHiding: Extension = ViewPlugin.fromClass(
  class {
    decorations: DecorationSet;

    constructor(view: EditorView) {
      this.decorations = decorate(view);
    }

    update(update: ViewUpdate) {
      // Selection too, not just the document: the whole point is that the
      // line the caret sits on shows its own syntax.
      if (update.docChanged || update.selectionSet || update.viewportChanged) {
        this.decorations = decorate(update.view);
      }
    }
  },
  { decorations: (plugin) => plugin.decorations },
);

/** Tables drawn — a STATE FIELD, not a view plugin.
 *
 * CodeMirror refuses block decorations from a plugin ("Block decorations may
 * not be specified via plugins"), because a plugin only sees the viewport and
 * a block widget changes the height of the document above it. A field sees the
 * whole state, which is also simpler here: a section is small enough to scan
 * end to end, so there is no viewport arithmetic to get wrong.
 */
const tableRendering: Extension = StateField.define<DecorationSet>({
  create: (state) => tableDecorations(state),
  update(value, transaction) {
    // The selection matters as much as the text: entering a table is what
    // turns it back into source.
    if (transaction.docChanged || transaction.selection) return tableDecorations(transaction.state);
    return value.map(transaction.changes);
  },
  provide: (field) => EditorView.decorations.from(field),
});

const livePreview: Extension = [markerHiding, tableRendering];

function tableDecorations(state: EditorState): DecorationSet {
  const caretLines = new Set(
    state.selection.ranges.flatMap((range) => [
      state.doc.lineAt(range.from).number,
      state.doc.lineAt(range.to).number,
    ]),
  );
  const decorations = [];
  for (const table of tableBlocks(state.doc)) {
    const touched = [...caretLines].some(
      (line) => line >= table.firstLine && line <= table.lastLine,
    );
    if (touched) continue;
    decorations.push(
      Decoration.replace({ widget: new TableWidget(table.rows), block: true }).range(
        table.from,
        table.to,
      ),
    );
  }
  return Decoration.set(decorations);
}

function decorate(view: EditorView): DecorationSet {
  const builder: { from: number; to: number; value: Decoration }[] = [];
  const caretLines = new Set(
    view.state.selection.ranges.flatMap((range) => [
      view.state.doc.lineAt(range.from).number,
      view.state.doc.lineAt(range.to).number,
    ]),
  );

  for (const { from, to } of view.visibleRanges) {
    syntaxTree(view.state).iterate({
      from,
      to,
      enter: (node) => {
        if (!MARKER_NODES.has(node.name)) return;
        const line = view.state.doc.lineAt(node.from).number;
        // Never hide what the operator is standing on.
        if (caretLines.has(line)) return;
        builder.push({ from: node.from, to: node.to, value: hiddenMark });
      },
    });
  }

  builder.sort((a, b) => a.from - b.from || a.to - b.to);
  return Decoration.set(builder.map(({ from, to, value }) => value.range(from, to)));
}

/** Every pipe table in the visible document, as its own block.
 *
 * Read off the lines rather than the syntax tree: a table is simply a run of
 * lines that start with `|`, the grammar's own table node is not always
 * present depending on the parser's extensions, and this stays true for the
 * half-typed table the operator is in the middle of writing.
 */
function tableBlocks(doc: Text) {
  const blocks: {
    from: number;
    to: number;
    firstLine: number;
    lastLine: number;
    rows: string[][];
  }[] = [];
  let line = 1;
  while (line <= doc.lines) {
    if (!isTableLine(doc.line(line).text)) {
      line += 1;
      continue;
    }
    const firstLine = line;
    while (line + 1 <= doc.lines && isTableLine(doc.line(line + 1).text)) line += 1;
    const lastLine = line;
    // Two lines is a header and its divider with no body; one line is someone
    // typing. Neither is a table worth drawing yet.
    if (lastLine - firstLine >= 2) {
      const rows: string[][] = [];
      for (let at = firstLine; at <= lastLine; at += 1) {
        const text = doc.line(at).text;
        if (isDividerLine(text)) continue;
        rows.push(cellsOf(text));
      }
      blocks.push({
        from: doc.line(firstLine).from,
        to: doc.line(lastLine).to,
        firstLine,
        lastLine,
        rows,
      });
    }
    line += 1;
  }
  return blocks;
}

function isTableLine(text: string): boolean {
  return text.trim().startsWith('|');
}

function isDividerLine(text: string): boolean {
  return /^\s*\|?[\s:|-]+\|?\s*$/.test(text) && text.includes('-');
}

function cellsOf(text: string): string[] {
  return text
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((cell) => cell.trim());
}
