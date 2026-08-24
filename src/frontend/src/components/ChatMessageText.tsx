import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export interface ChatMessageTextProps {
  text: string;
}

// A direct-image URL -- common real extensions, an optional query string
// (SAS tokens/cache-busters on a real generated-image URL are the normal
// case, e.g. Azure Blob Storage/DALL-E links). Anything else is treated
// as an ordinary link, never guessed at harder than this.
const IMAGE_URL_PATTERN = /\.(png|jpe?g|gif|webp|svg|avif)(\?.*)?$/i;

/** Renders chat message text (user- or agent-authored, symmetric — no
 * speaker/role branch) as formatted rich text via react-markdown
 * (ADR-050). `remark-gfm` (2026-08-24, operator: "Generate a picture...
 * showed a link, The Link is not clickable" — ADR-050's own explicit
 * "cheap, additive follow-on if a future story needs it" for exactly
 * this) adds GFM's autolink-literals: a bare URL in the text (the
 * common shape a generated-image reply actually comes back as, not
 * markdown link syntax) now renders as a real, clickable link instead
 * of inert plain text. Still zero raw-HTML plugins (no `rehype-raw`,
 * no `dangerouslySetInnerHTML`) -- ADR-050's own safe-by-omission
 * sanitization posture is unchanged; GFM only affects markdown parsing,
 * not HTML handling. Link/image URLs still pass through react-markdown's
 * own built-in `defaultUrlTransform`, stripping non-http(s)/mailto/tel
 * schemes.
 *
 * New this pass: a link (or a real markdown image) whose URL looks like
 * a direct image renders INLINE as a real, clickable thumbnail rather
 * than plain link text (operator: "The Image should be displayed in the
 * chat clicking on it open it in a pop") -- clicking it opens a
 * lightweight full-size lightbox overlay, closing on backdrop click or
 * Escape. Applies everywhere this component is used (every chat
 * surface shares it, ADR-050 Decision 3) -- one fix, not one per
 * surface. */
export function ChatMessageText({ text }: ChatMessageTextProps) {
  const [lightboxSrc, setLightboxSrc] = useState<string | null>(null);

  // Escape closes regardless of what currently has focus -- the
  // backdrop's own onKeyDown only fires when IT is focused, which isn't
  // guaranteed (a click that opened it moves focus to the button that
  // was clicked, not the backdrop itself).
  useEffect(() => {
    if (!lightboxSrc) return;
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setLightboxSrc(null);
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [lightboxSrc]);

  return (
    <>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          img: ({ src, alt }) =>
            typeof src === 'string' ? (
              <button
                type="button"
                className="chat-inline-image-btn"
                onClick={() => setLightboxSrc(src)}
                aria-label={alt ? `Open image: ${alt}` : 'Open image'}
              >
                <img className="chat-inline-image" src={src} alt={alt ?? ''} />
              </button>
            ) : null,
          a: ({ href, children }) => {
            if (href && IMAGE_URL_PATTERN.test(href)) {
              return (
                <button
                  type="button"
                  className="chat-inline-image-btn"
                  onClick={() => setLightboxSrc(href)}
                  aria-label="Open image"
                >
                  <img className="chat-inline-image" src={href} alt="" />
                </button>
              );
            }
            return (
              <a href={href} target="_blank" rel="noopener noreferrer">
                {children}
              </a>
            );
          },
        }}
      >
        {text}
      </ReactMarkdown>
      {lightboxSrc && (
        <div
          className="chat-image-lightbox-backdrop"
          role="button"
          tabIndex={0}
          aria-label="Close image"
          onClick={() => setLightboxSrc(null)}
          onKeyDown={(event) => {
            if (event.key === 'Escape' || event.key === 'Enter') setLightboxSrc(null);
          }}
        >
          <img className="chat-image-lightbox-image" src={lightboxSrc} alt="" />
        </div>
      )}
    </>
  );
}
