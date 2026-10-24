import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router';
import { ApiError } from '../api/client';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { fetchNoteDetail, fetchVaultSearchStatus, type NoteDetail } from '../features/vault-browser/client';
import { NoteEditor } from '../features/vault-browser/NoteEditor';
import type { TocHeading } from '../features/vault-browser/tableOfContents';

/** This page had its own hand-rolled "← Browse & Search" paragraph, in all
 *  three of its states, while the shell already renders a BackControl saying
 *  the same thing (operator, 2026-10-24: "it has its own bread crumbs"). Two
 *  ways back, stacked, in two different styles. The framework component
 *  (`ADR-060`) replaces it: it names where this note sits rather than only
 *  pointing backwards, and it still works on a cold load, where BackControl
 *  correctly hides because there is no history to go back through. */
const BROWSE_CRUMB = { label: 'The Vault', to: '/browse' } as const;

/** One side of a note's links, as a reference rather than a destination.
 *
 * An empty side still renders its heading and says so: "no backlinks" is a
 * fact about the note worth reading, and a section that disappears when empty
 * makes the rail's shape change from note to note.
 */
function LinkList({
  title,
  hint,
  arrow,
  links,
}: {
  title: string;
  hint: string;
  arrow: string;
  links: NoteDetail['forward_links'];
}) {
  return (
    <section className="note-rail-section">
      <h3 className="note-rail-title" title={hint}>
        {title} <span className="note-rail-count">{links.length}</span>
      </h3>
      {links.length === 0 ? (
        <p className="note-rail-empty">None</p>
      ) : (
        <ul className="note-rail-links">
          {links.map((link) => (
            <li key={link.stem}>
              <Link to={`/browse/${link.stem}`} title={`${link.title} — ${link.kind}`}>
                <span className="note-rail-arrow" aria-hidden="true">{arrow}</span>
                {link.title}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function NoteDetailPage() {
  const { stem } = useParams<{ stem: string }>();
  const [detail, setDetail] = useState<NoteDetail | null>(null);
  const [notFound, setNotFound] = useState(false);
  // Only asked when a lookup already failed: on the happy path this page
  // costs exactly what it did before.
  const [building, setBuilding] = useState(false);
  const [headings, setHeadings] = useState<TocHeading[]>([]);

  useEffect(() => {
    if (!stem) return;
    setDetail(null);
    setNotFound(false);
    setHeadings([]);
    fetchNoteDetail(stem).catch((error) => {
      if (error instanceof ApiError && error.status === 404) {
        setNotFound(true);
        // Why it was not found: a vault that does not have it, or a server
        // that has not finished reading the vault. Asked only now, so the
        // ordinary path still costs one request.
        void fetchVaultSearchStatus()
          .then((status) => setBuilding(Boolean(status.building) && !status.indexed))
          .catch(() => setBuilding(false));
        return null;
      }
      throw error;
    }).then((result) => result && setDetail(result));
  }, [stem]);

  if (notFound) {
    return (
      <>
        <Breadcrumbs items={[BROWSE_CRUMB, { label: stem ?? 'Note' }]} />
        <div className="card">
          <div className="empty-state">
            {/* A restarted server has no index until its boot rebuild lands,
                and a note opened in that window answered "no indexed note
                found" for a note that plainly exists (operator, 2026-10-24).
                The lookup fails the same way either way; only the sentence
                differs, and only one of them is true. */}
            {building ? (
              <>
                <p style={{ margin: 0, fontWeight: 600, color: 'var(--color-text)' }}>
                  The index is still building
                </p>
                <p style={{ margin: 'var(--space-1) 0 0' }}>
                  The server reads the whole vault when it starts. This note is almost
                  certainly there — it opens on its own in a moment.
                </p>
              </>
            ) : (
              <p style={{ margin: 0, fontWeight: 600, color: 'var(--color-text)' }}>
                No indexed note found for "{stem}"
              </p>
            )}
          </div>
        </div>
      </>
    );
  }

  if (!detail) {
    return (
      <>
        <Breadcrumbs items={[BROWSE_CRUMB, { label: stem ?? 'Note' }]} />
        <p className="text-muted">Loading...</p>
      </>
    );
  }

  // Without the rail the layout is one column: an empty 240px track beside
  // the note is a margin nobody asked for.
  const hasRail =
    headings.length > 1 || detail.forward_links.length > 0 || detail.backlinks.length > 0;

  return (
    <>
      <Breadcrumbs items={[BROWSE_CRUMB, { label: detail.title }]} />
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

      <div className={`note-detail-layout ${hasRail ? '' : 'has-no-rail'}`}>
        <div className="note-detail-main">
          <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
            <NoteEditor
              stem={detail.stem}
              body={detail.body}
              version={detail.version}
              editable={detail.editable}
              forwardLinks={detail.forward_links}
              onHeadingsExtracted={setHeadings}
              // Kept in state rather than re-fetched: a re-fetch would replace
              // the text under the cursor with the server's copy of what was
              // just typed, which is how an editor eats a keystroke.
              onSaved={({ body, version }) =>
                setDetail((current) => (current ? { ...current, body, version } : current))
              }
            />
          </div>

        </div>

        {/* Everything ABOUT the note, beside the note (operator, 2026-10-24:
            the links "Looks Really Bad And Take alot of Space while they can
            be on the Side Panel ... and be Much Smaller in size"). They were
            two full-width cards below the body, so reading a note meant
            scrolling past its own text to find what it connects to, and a
            note with 30 backlinks buried itself. Sections, one list each, at
            the size of a reference rather than a destination. */}
        {hasRail && (
          <aside className="note-rail" aria-label="About this note">
            {headings.length > 1 && (
              <section className="note-rail-section">
                <h3 className="note-rail-title">On this page</h3>
                <ul className="note-detail-toc-list">
                  {headings.map((heading) => (
                    <li key={heading.slug}>
                      <a href={`#${heading.slug}`} data-level={heading.level}>
                        {heading.text}
                      </a>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            <LinkList
              title="Links out"
              hint="Notes this one links to"
              arrow="→"
              links={detail.forward_links}
            />
            <LinkList
              title="Links in"
              hint="Notes that link to this one"
              arrow="←"
              links={detail.backlinks}
            />
          </aside>
        )}
      </div>
    </>
  );
}
