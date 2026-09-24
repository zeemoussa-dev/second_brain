import ReactMarkdown from 'react-markdown';
import { Link } from 'react-router';
import { MarkdownPre } from '../components/markdownBlocks';
import { wikilinksToMarkdown } from '../features/vault-browser/wikilinks';

// Rendering vault text -- part of the host contract, not a framework internal
// (`BUG-078`). Before this, a plugin screen could import neither the renderer nor
// mermaid, so any plugin showing a note wrote its own markdown renderer, and after
// the framework learned ```mermaid fences the two disagreed about the same file:
// one app drawing one note two ways. The CBO install's Strategic Entities plugin
// carried ~380 lines of duplicate renderer for exactly this reason.
//
// The framework's own surfaces render through this too (Cockpit summaries), so
// "the way the app does it" is not a claim -- it is the same component.

export interface NoteTextProps {
  /** Markdown as it appears in the note, wikilinks and ```mermaid fences included. */
  text: string;
  /** Wikilink targets that are real notes on this install: those become links into
   * the note view, and everything else renders as plain text rather than a link the
   * vault cannot honour. A screen that has no index simply passes nothing. */
  resolvedStems?: string[];
}

/** One note's text, rendered the way the rest of the app renders it: markdown, real
 * links, and ```mermaid fences as diagrams. */
export function NoteText({ text, resolvedStems = [] }: NoteTextProps) {
  return (
    <ReactMarkdown
      components={{
        pre: MarkdownPre,
        a: ({ href, children }) =>
          href && href.startsWith('/browse/') ? (
            <Link to={href}>{children}</Link>
          ) : (
            <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
          ),
      }}
    >
      {wikilinksToMarkdown(text, resolvedStems)}
    </ReactMarkdown>
  );
}

/** A diagram on its own, for a screen holding mermaid source rather than a note --
 * the shape a plugin's hand-rolled flowchart component was reaching for. */
export { MermaidDiagram } from '../components/MermaidDiagram';
