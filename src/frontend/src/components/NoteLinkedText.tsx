import ReactMarkdown from 'react-markdown';
import { Link } from 'react-router';
import { wikilinksToMarkdown } from '../features/vault-browser/wikilinks';

// Text that came out of a vault note -- a Thread's Summary, say -- rendered as
// markdown with its `[[wikilinks]]` turned into real in-app links to the notes
// they name. Same zero-raw-HTML posture as ChatMessageText (ADR-050): no
// rehype-raw, no dangerouslySetInnerHTML.
//
// `resolvedStems` are the targets that are real notes on this install; the read
// model says which (cockpit_view._summary_links), because only the backend has
// the index. Anything else renders as plain text rather than a dead link.

interface NoteLinkedTextProps {
  text: string;
  resolvedStems: string[];
}

export function NoteLinkedText({ text, resolvedStems }: NoteLinkedTextProps) {
  return (
    <ReactMarkdown
      components={{
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
