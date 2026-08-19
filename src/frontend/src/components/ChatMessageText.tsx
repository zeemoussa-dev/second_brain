import ReactMarkdown from 'react-markdown';

export interface ChatMessageTextProps {
  text: string;
}

/** Renders chat message text (user- or agent-authored, symmetric — no
 * speaker/role branch) as formatted rich text via react-markdown, zero
 * additional remark/rehype plugins (ADR-050): CommonMark's own default
 * feature set (bold/italic, bulleted/numbered lists, links, inline/block
 * code, headings) already covers the operator-resolved markdown subset.
 * Default-safe by omission -- react-markdown never invokes
 * dangerouslySetInnerHTML and never parses raw HTML embedded in `text`
 * unless the rehype-raw plugin is explicitly added, which this
 * component does not do; link/image URLs pass through react-markdown's
 * own built-in defaultUrlTransform unmodified. */
export function ChatMessageText({ text }: ChatMessageTextProps) {
  return <ReactMarkdown>{text}</ReactMarkdown>;
}
