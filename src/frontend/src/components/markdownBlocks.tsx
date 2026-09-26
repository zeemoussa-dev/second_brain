import type { ReactNode } from 'react';
import { isValidElement } from 'react';
import remarkGfm from 'remark-gfm';
import { MermaidDiagram } from './MermaidDiagram';
import { remarkCallouts } from './remarkCallouts';

// One rule for fenced code blocks, shared by every markdown surface (chat, note
// bodies, Cockpit summaries) so a ```mermaid block draws the same everywhere and
// none of them has to know how. Everything that is not mermaid stays the plain
// `<pre>` react-markdown would have rendered.

/** The markdown a note is actually written in, for every surface that renders one.
 *
 * `remark-gfm` was passed by chat and by nothing else, so the same file read
 * correctly when an agent quoted it and badly in the note view: no tables, no
 * task lists, no strikethrough, no autolinks -- 364 of the reporting vault's
 * notes contain a table (`BUG-080`). Callouts are Obsidian's, not CommonMark's,
 * and are handled here for the same reason. Kept as one exported list rather
 * than a `remarkPlugins` prop per surface, because a list each caller assembles
 * is exactly how the surfaces drifted apart in the first place. */
export const NOTE_MARKDOWN_PLUGINS = [remarkGfm, remarkCallouts];

/** The mermaid source inside a react-markdown `<pre>`, or null for any other
 * fenced block. react-markdown gives `<pre>` a single `<code>` child carrying the
 * fence's language as `language-<name>`. */
function mermaidSource(children: ReactNode): string | null {
  if (!isValidElement(children)) return null;
  const props = children.props as { className?: string; children?: ReactNode };
  if (!/(^|\s)language-mermaid(\s|$)/.test(props.className ?? '')) return null;
  const code = props.children;
  return typeof code === 'string' ? code.replace(/\n$/, '') : null;
}

export function MarkdownPre({ children }: { children?: ReactNode }) {
  const diagram = mermaidSource(children);
  return diagram !== null ? <MermaidDiagram code={diagram} /> : <pre>{children}</pre>;
}
