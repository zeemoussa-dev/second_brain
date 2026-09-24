import type { ReactNode } from 'react';
import { isValidElement } from 'react';
import { MermaidDiagram } from './MermaidDiagram';

// One rule for fenced code blocks, shared by every markdown surface (chat, note
// bodies, Cockpit summaries) so a ```mermaid block draws the same everywhere and
// none of them has to know how. Everything that is not mermaid stays the plain
// `<pre>` react-markdown would have rendered.

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
