import { useEffect, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeSlug from 'rehype-slug';
import { Link } from 'react-router';
import type { NoteSummary } from './client';
import { extractHeadings, type TocHeading } from './tableOfContents';

interface NoteBodyProps {
  stem: string;
  body: string;
  forwardLinks: NoteSummary[];
  // NoteDetailPage.tsx renders the jump-to-section list; it's fed from
  // here (not re-derived separately) so the ids the list links to and
  // the ids the actual rendered headings carry can never drift apart.
  onHeadingsExtracted?: (headings: TocHeading[]) => void;
}

const EMBED_PATTERN = /!\[\[([^\]]+)\]\]/g;
const WIKILINK_PATTERN = /\[\[([^\]]+)\]\]/g;

// Duplicated from agentsApiClient.ts's own identical `ATTACHMENT_BASE_URL`
// convention -- client.ts doesn't export its BASE_URL, so any call site
// building a raw (non-apiFetch) URL keeps its own copy of this same
// fallback per this codebase's established pattern.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

// 2026-08-23 -- operator: "when I click on a node The Next View should
// be the MD file it self displayed in a nice HTML formatting with links
// to the Files and Tags etc". Real `[[wikilink]]`/`[[target|alias]]`
// syntax isn't standard CommonMark, so react-markdown (ChatMessageText.
// tsx's own established, zero-plugin, safe-by-omission convention --
// never rehype-raw, never dangerouslySetInnerHTML) never recognizes it
// on its own. Pre-processes the raw body into plain markdown link/image
// syntax BEFORE handing it to ReactMarkdown.
//
// 2026-08-24 (operator: "Images are not shown") -- Obsidian's own
// `![[filename]]` EMBED syntax (a captured File note's own real, sibling
// images, e.g. `Work/Files/<date>/<name>/slide-14.png` next to its own
// `.md`) is handled FIRST and separately from a plain `[[wikilink]]`,
// since `![[x]]` contains `[[x]]` as a literal substring -- resolving
// wikilinks first would mangle it. Points at the new
// `/vault-search/notes/{stem}/assets/{filename}` route (vault_search.py's
// `resolve_asset_path`, confirmed live it serves the real sibling file);
// an embed for a file that doesn't actually exist there renders as a
// real, honest broken-image (never silently dropped, never a fabricated
// placeholder) -- the browser's own native "image failed to load" state.
function resolveEmbedsAndWikilinks(body: string, forwardLinks: NoteSummary[], stem: string): string {
  const withImages = body.replace(EMBED_PATTERN, (_match, inner: string) => {
    const filename = inner.trim();
    const url = `${API_BASE_URL}/vault-search/notes/${encodeURIComponent(stem)}/assets/${encodeURIComponent(filename)}`;
    return `![${filename}](${url})`;
  });
  const stemByLowerStem = new Map(forwardLinks.map((link) => [link.stem.toLowerCase(), link.stem]));
  return withImages.replace(WIKILINK_PATTERN, (_match, inner: string) => {
    const [rawTarget, rawAlias] = inner.split('|');
    const target = rawTarget.trim();
    const alias = (rawAlias ?? rawTarget).trim();
    const resolvedStem = stemByLowerStem.get(target.toLowerCase());
    if (!resolvedStem) return alias;
    return `[${alias}](/browse/${encodeURIComponent(resolvedStem)})`;
  });
}

/** Renders one note's real markdown body as formatted rich text, with
 * real wikilinks resolved to clickable in-app navigation (react-router
 * `<Link>`, no full page reload), real image embeds resolved to actual
 * inline images, every other link (a genuine external URL in the body,
 * if any) left as a normal new-tab anchor, and every heading given a
 * real jump-to-section id via `rehype-slug` -- a pure AST transform
 * (not a React-render-time side effect), which is what makes it safe
 * under React 18 StrictMode's double-invoked renders; an earlier
 * hand-rolled version that mutated a plain counter while rendering each
 * heading desynced its own ids from the ToC the moment StrictMode
 * double-invoked it (confirmed live, 2026-08-24). `tableOfContents.ts`'s
 * own `extractHeadings` (NoteDetailPage.tsx's ToC list) uses the exact
 * same underlying `github-slugger` library `rehype-slug` wraps, so the
 * two independently-computed id sets can never disagree. */
export function NoteBody({ stem, body, forwardLinks, onHeadingsExtracted }: NoteBodyProps) {
  const markdown = useMemo(() => resolveEmbedsAndWikilinks(body, forwardLinks, stem), [body, forwardLinks, stem]);
  const headings = useMemo(() => extractHeadings(body), [body]);

  useEffect(() => {
    onHeadingsExtracted?.(headings);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- onHeadingsExtracted is a fresh closure every parent render; keying off `headings` alone (its own real content dependency) avoids an infinite notify loop.
  }, [headings]);

  return (
    <ReactMarkdown
      rehypePlugins={[rehypeSlug]}
      components={{
        img: ({ src, alt }) => (typeof src === 'string' ? <img className="note-body-image" src={src} alt={alt ?? ''} loading="lazy" /> : null),
        a: ({ href, children }) => {
          if (href && href.startsWith('/browse/')) {
            return <Link to={href}>{children}</Link>;
          }
          return (
            <a href={href} target="_blank" rel="noopener noreferrer">
              {children}
            </a>
          );
        },
      }}
    >
      {markdown}
    </ReactMarkdown>
  );
}
