import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router';
import { ApiError } from '../api/client';
import { fetchNoteDetail, type NoteDetail } from '../features/vault-browser/client';
import { NoteBody } from '../features/vault-browser/NoteBody';
import type { TocHeading } from '../features/vault-browser/tableOfContents';

export function NoteDetailPage() {
  const { stem } = useParams<{ stem: string }>();
  const [detail, setDetail] = useState<NoteDetail | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [headings, setHeadings] = useState<TocHeading[]>([]);

  useEffect(() => {
    if (!stem) return;
    setDetail(null);
    setNotFound(false);
    setHeadings([]);
    fetchNoteDetail(stem).catch((error) => {
      if (error instanceof ApiError && error.status === 404) {
        setNotFound(true);
        return null;
      }
      throw error;
    }).then((result) => result && setDetail(result));
  }, [stem]);

  if (notFound) {
    return (
      <>
        <p className="text-muted"><Link className="text-muted" to="/browse">&larr; Browse &amp; Search</Link></p>
        <div className="card">
          <div className="empty-state">
            <p style={{ margin: 0, fontWeight: 600, color: 'var(--color-text)' }}>
              No indexed note found for "{stem}"
            </p>
          </div>
        </div>
      </>
    );
  }

  if (!detail) {
    return (
      <>
        <p className="text-muted"><Link className="text-muted" to="/browse">&larr; Browse &amp; Search</Link></p>
        <p className="text-muted">Loading...</p>
      </>
    );
  }

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/browse">&larr; Browse &amp; Search</Link></p>
      <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
        <span className="badge" style={{ marginBottom: 'var(--space-2)', display: 'inline-block' }}>{detail.kind}</span>
        <h1 style={{ marginTop: 0 }}>{detail.title}</h1>
        <div>
          {detail.tags.map((tag) => (
            <Link
              className="badge"
              style={{ marginRight: 'var(--space-1)', textDecoration: 'none' }}
              to={`/browse?tag=${encodeURIComponent(tag)}`}
              key={tag}
            >
              {tag}
            </Link>
          ))}
        </div>
      </div>

      <div className="note-detail-layout">
        <div className="note-detail-main">
          <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
            <h2>Note</h2>
            <div className="note-body">
              <NoteBody
                stem={detail.stem}
                body={detail.body}
                forwardLinks={detail.forward_links}
                onHeadingsExtracted={setHeadings}
              />
            </div>
          </div>

          <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
            <h2>Forward links <span className="text-muted" style={{ fontWeight: 400, fontSize: 'var(--font-size-sm)' }}>— notes this one links to</span></h2>
            {detail.forward_links.length > 0 ? (
              <div className="item-list">
                {detail.forward_links.map((link) => (
                  <Link className="item-row" to={`/browse/${link.stem}`} key={link.stem}>
                    <div className="item-row-main">
                      <span className="item-row-title">&#8594; {link.title}</span>
                      <span className="item-row-meta">{link.kind}</span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-muted" style={{ margin: 0 }}>No outgoing links.</p>
            )}
          </div>

          <div className="card">
            <h2>Backlinks <span className="text-muted" style={{ fontWeight: 400, fontSize: 'var(--font-size-sm)' }}>— notes that link to this one</span></h2>
            {detail.backlinks.length > 0 ? (
              <div className="item-list">
                {detail.backlinks.map((link) => (
                  <Link className="item-row" to={`/browse/${link.stem}`} key={link.stem}>
                    <div className="item-row-main">
                      <span className="item-row-title">&#8592; {link.title}</span>
                      <span className="item-row-meta">{link.kind}</span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-muted" style={{ margin: 0 }}>No notes link to this one yet.</p>
            )}
          </div>
        </div>

        {headings.length > 1 && (
          <aside className="note-detail-toc" aria-label="Jump to section">
            <ul className="note-detail-toc-list">
              {headings.map((heading) => (
                <li key={heading.slug}>
                  <a href={`#${heading.slug}`} data-level={heading.level}>
                    {heading.text}
                  </a>
                </li>
              ))}
            </ul>
          </aside>
        )}
      </div>
    </>
  );
}
