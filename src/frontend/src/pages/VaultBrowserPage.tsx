import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import {
  fetchVaultSearchStatus,
  fetchNotes,
  fetchTags,
  search,
  type VaultSearchStatus,
  type BrowseResponse,
  type TagCount,
  type SearchResponse,
} from '../features/vault-browser/client';

const PAGE_SIZE = 20;

export function VaultBrowserPage() {
  const [status, setStatus] = useState<VaultSearchStatus | null>(null);
  const [tags, setTags] = useState<TagCount[]>([]);
  const [activeTag, setActiveTag] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [browse, setBrowse] = useState<BrowseResponse | null>(null);
  const [queryInput, setQueryInput] = useState('');
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);

  useEffect(() => {
    fetchVaultSearchStatus().then(setStatus);
  }, []);

  useEffect(() => {
    if (!status?.indexed) return;
    fetchTags().then((response) => setTags(response.tags));
  }, [status]);

  useEffect(() => {
    if (!status?.indexed) return;
    setBrowse(null);
    fetchNotes({ tag: activeTag ?? undefined, page, page_size: PAGE_SIZE }).then(setBrowse);
  }, [status, activeTag, page]);

  const runSearch = () => {
    if (!queryInput.trim()) return;
    setSearchResult(null);
    search(queryInput.trim()).then(setSearchResult);
  };

  if (!status) {
    return (
      <>
        <h1>Browse &amp; Search</h1>
        <p className="text-muted">Loading...</p>
      </>
    );
  }

  if (!status.indexed) {
    return (
      <>
        <h1>Browse &amp; Search</h1>
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">&#128269;</div>
            <p style={{ margin: 0, fontWeight: 600, color: 'var(--color-text)' }}>
              Nothing indexed yet
            </p>
            <p style={{ margin: 'var(--space-1) 0 0' }}>
              Second Brain hasn't built a vault index yet (REQ-SB-01) —
              there is nothing to browse or search. This is not an error
              and not the same as "indexed, but no matches."
            </p>
          </div>
        </div>
      </>
    );
  }

  const totalPages = browse ? Math.max(1, Math.ceil(browse.total / browse.page_size)) : 1;

  return (
    <>
      <h1>Browse &amp; Search</h1>
      <p className="text-muted">
        List, filter, and search your indexed vault notes directly — no
        promotion/approval gate between indexed and usable (REQ-SB-02).
      </p>

      <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
        <h2>Search</h2>
        <div style={{ display: 'flex', gap: 'var(--space-2)', margin: 'var(--space-1) 0 var(--space-3)' }}>
          <input
            className="input"
            type="text"
            value={queryInput}
            placeholder="e.g. masdar renewal terms"
            onChange={(event) => setQueryInput(event.target.value)}
            onKeyDown={(event) => event.key === 'Enter' && runSearch()}
          />
          <button type="button" className="btn btn-primary" style={{ flexShrink: 0 }} onClick={runSearch}>
            Search
          </button>
        </div>
        {searchResult && (
          searchResult.results.length > 0 ? (
            <div className="item-list">
              {searchResult.results.map((result) => (
                <Link className="item-row" to={`/browse/${result.stem}`} key={result.stem}>
                  <div className="item-row-main">
                    <span className="item-row-title">
                      <span className="badge" style={{ marginRight: 'var(--space-1)' }}>#{result.rank}</span>
                      {result.title}
                    </span>
                    <span className="item-row-meta">{result.kind}</span>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <p style={{ margin: 0, fontWeight: 600, color: 'var(--color-text)' }}>
                No notes match "{searchResult.query}"
              </p>
              <p style={{ margin: 'var(--space-1) 0 0' }}>
                Try a different search term, or browse by tag below.
              </p>
            </div>
          )
        )}
      </div>

      <div className="card">
        <h2>Browse by tag</h2>
        <div className="state-switcher" style={{ marginBottom: 'var(--space-3)' }}>
          <button
            type="button"
            className={`btn tag-chip ${activeTag === null ? 'btn-primary' : ''}`}
            onClick={() => { setActiveTag(null); setPage(1); }}
          >
            All notes
          </button>
          {tags.map((tagCount) => (
            <button
              type="button"
              key={tagCount.tag}
              className={`btn tag-chip ${activeTag === tagCount.tag ? 'btn-primary' : ''}`}
              onClick={() => { setActiveTag(tagCount.tag); setPage(1); }}
            >
              {tagCount.tag} ({tagCount.count})
            </button>
          ))}
        </div>

        {!browse ? (
          <p className="text-muted">Loading...</p>
        ) : browse.notes.length > 0 ? (
          <>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
              <span className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
                Showing {(browse.page - 1) * browse.page_size + 1}
                &ndash;{Math.min(browse.page * browse.page_size, browse.total)} of {browse.total} notes
              </span>
              <span style={{ display: 'flex', gap: 'var(--space-2)' }}>
                <button
                  type="button"
                  className="btn"
                  style={{ padding: 'var(--space-1) var(--space-3)', fontSize: 'var(--font-size-sm)' }}
                  disabled={page <= 1}
                  onClick={() => setPage((current) => current - 1)}
                >
                  &larr; Prev
                </button>
                <button
                  type="button"
                  className="btn"
                  style={{ padding: 'var(--space-1) var(--space-3)', fontSize: 'var(--font-size-sm)' }}
                  disabled={page >= totalPages}
                  onClick={() => setPage((current) => current + 1)}
                >
                  Next &rarr;
                </button>
              </span>
            </div>
            <div className="item-list">
              {browse.notes.map((note) => (
                <Link className="item-row" to={`/browse/${note.stem}`} key={note.stem}>
                  <div className="item-row-main">
                    <span className="item-row-title">{note.title}</span>
                    <span className="item-row-meta">
                      <span className="badge" style={{ marginRight: 'var(--space-1)' }}>{note.kind}</span>
                      {note.tags.join(', ')}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </>
        ) : (
          <div className="empty-state">
            <p style={{ margin: 0, fontWeight: 600, color: 'var(--color-text)' }}>
              {activeTag ? `No notes carry the tag "${activeTag}"` : 'No notes indexed'}
            </p>
            <p style={{ margin: 'var(--space-1) 0 0' }}>
              {activeTag
                ? 'This tag currently matches nothing in the index — not an error, and not the same as "vault not indexed yet."'
                : ''}
            </p>
          </div>
        )}
      </div>
    </>
  );
}
