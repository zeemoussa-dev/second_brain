import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { SnippetText } from '../features/vault-browser/SnippetText';
import {
  fetchVaultSearchStatus,
  fetchKinds,
  fetchNotes,
  fetchTags,
  search,
  type VaultSearchStatus,
  type BrowseResponse,
  type KindCount,
  type TagCount,
  type SearchResponse,
} from '../features/vault-browser/client';

const PAGE_SIZE = 20;

/** How many tag chips before the row becomes a wall. A real vault has hundreds
 *  of tags; rendering all of them put the note list below a screenful of
 *  chips. The rest are one click away. */
const TAGS_SHOWN = 12;

/** Browse & Search over the indexed vault.
 *
 * **One result area, not two.** Search and tag-browse used to be separate
 * cards, so after a search the page showed the matches AND an unrelated page
 * of all notes underneath — two answers at once, neither obviously the one you
 * asked for. A query now replaces the list, and clearing it brings the list
 * back.
 *
 * **The URL is the state.** Query, tag, kind, sort and page all live in it, so
 * a filtered view can be linked, bookmarked and reached with Back. Filters are
 * written with `replace` (`ADR-041`): changing a filter is not a journey, and
 * Back should leave the screen rather than undo a click.
 */
export function VaultBrowserPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get('q') ?? '';
  const activeTag = searchParams.get('tag');
  const activeKind = searchParams.get('kind');
  const sort = searchParams.get('sort') ?? 'name';
  const page = Math.max(1, Number(searchParams.get('page') ?? 1) || 1);

  const [status, setStatus] = useState<VaultSearchStatus | null>(null);
  const [tags, setTags] = useState<TagCount[]>([]);
  const [kinds, setKinds] = useState<KindCount[]>([]);
  const [allTagsShown, setAllTagsShown] = useState(false);
  const [browse, setBrowse] = useState<BrowseResponse | null>(null);
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
  const [searching, setSearching] = useState(false);
  // What is in the box, which is only the URL's `q` once Enter is pressed:
  // searching on every keystroke would embed the whole vault per character.
  const [queryInput, setQueryInput] = useState(query);

  useEffect(() => {
    fetchVaultSearchStatus().then(setStatus);
  }, []);

  useEffect(() => {
    if (!status?.indexed) return;
    fetchTags().then((response) => setTags(response.tags));
    fetchKinds().then((response) => setKinds(response.kinds));
  }, [status]);

  useEffect(() => {
    setQueryInput(query);
  }, [query]);

  useEffect(() => {
    if (!status?.indexed || query) return;
    setBrowse(null);
    fetchNotes({
      tag: activeTag ?? undefined,
      kind: activeKind ?? undefined,
      sort,
      page,
      page_size: PAGE_SIZE,
    }).then(setBrowse);
  }, [status, activeTag, activeKind, sort, page, query]);

  useEffect(() => {
    if (!status?.indexed || !query) {
      setSearchResult(null);
      return;
    }
    setSearching(true);
    search(query)
      .then(setSearchResult)
      .finally(() => setSearching(false));
  }, [status, query]);

  /** Writes the URL, which every read above derives from. `replace` keeps a
   *  filter out of the history stack; a search is a real destination and gets
   *  a push, so Back returns to the list you searched from. */
  function updateParams(changes: Record<string, string | null>, historyMode: 'push' | 'replace') {
    const next = new URLSearchParams(searchParams);
    for (const [key, value] of Object.entries(changes)) {
      if (value === null || value === '') next.delete(key);
      else next.set(key, value);
    }
    // Any filter change invalidates the page number: page 7 of a different
    // filter is usually empty, which reads as "no notes" rather than "wrong
    // page".
    if (!('page' in changes)) next.delete('page');
    setSearchParams(next, { replace: historyMode === 'replace' });
  }

  if (!status) {
    return (
      <>
        <h1>Browse &amp; Search</h1>
        <p className="text-muted">Loading…</p>
      </>
    );
  }

  if (!status.indexed) {
    return (
      <>
        <h1>Browse &amp; Search</h1>
        <div className="card">
          <div className="empty-state">
            <span className="material-symbols-outlined empty-state-icon" aria-hidden="true">
              search
            </span>
            <p className="empty-state-title">Nothing indexed yet</p>
            <p style={{ margin: 'var(--space-1) 0 0' }}>
              No vault index has been built, so there is nothing to browse or search. This
              is not an error, and not the same as “indexed, but no matches” — build the
              index from Settings › Vault.
            </p>
          </div>
        </div>
      </>
    );
  }

  const showingSearch = Boolean(query);
  const results = searchResult?.results ?? [];
  const totalPages = browse ? Math.max(1, Math.ceil(browse.total / browse.page_size)) : 1;
  const visibleTags = allTagsShown ? tags : tags.slice(0, TAGS_SHOWN);

  return (
    <>
      <h1>Browse &amp; Search</h1>
      <p className="text-muted">
        Everything indexed from your vault, searchable by wording and by meaning.
      </p>

      <div className="card browse-card">
        <div className="browse-search-row">
          <span className="material-symbols-outlined browse-search-icon" aria-hidden="true">
            search
          </span>
          <input
            className="input browse-search-input"
            type="search"
            value={queryInput}
            placeholder="Search your notes…"
            aria-label="Search your notes"
            onChange={(event) => setQueryInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') updateParams({ q: queryInput.trim() }, 'push');
              if (event.key === 'Escape') {
                setQueryInput('');
                updateParams({ q: null }, 'replace');
              }
            }}
          />
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => updateParams({ q: queryInput.trim() }, 'push')}
          >
            Search
          </button>
          {showingSearch && (
            <button
              type="button"
              className="btn"
              onClick={() => {
                setQueryInput('');
                updateParams({ q: null }, 'push');
              }}
            >
              Clear
            </button>
          )}
        </div>

        {/* Filters stay visible while searching: they are how you get back to
            the list, and hiding them would make the screen change shape. */}
        <div className="browse-filters">
          <div className="browse-filter-row">
            <span className="browse-filter-label">Tags</span>
            <button
              type="button"
              className={`btn tag-chip ${activeTag === null ? 'btn-primary' : ''}`}
              onClick={() => updateParams({ tag: null, q: null }, 'replace')}
            >
              All
            </button>
            {visibleTags.map((tagCount) => (
              <button
                type="button"
                key={tagCount.tag}
                className={`btn tag-chip ${activeTag === tagCount.tag ? 'btn-primary' : ''}`}
                onClick={() => updateParams({ tag: tagCount.tag, q: null }, 'replace')}
              >
                {tagCount.tag} <span className="tag-chip-count">{tagCount.count}</span>
              </button>
            ))}
            {tags.length > TAGS_SHOWN && (
              <button
                type="button"
                className="btn tag-chip"
                onClick={() => setAllTagsShown((shown) => !shown)}
              >
                {allTagsShown ? 'Show fewer' : `+${tags.length - TAGS_SHOWN} more`}
              </button>
            )}
          </div>

          <div className="browse-filter-row">
            <span className="browse-filter-label">Kind</span>
            <select
              className="input kv-select"
              value={activeKind ?? ''}
              aria-label="Filter by kind"
              onChange={(event) => updateParams({ kind: event.target.value || null, q: null }, 'replace')}
            >
              <option value="">Any kind</option>
              {kinds.map((kindCount) => (
                <option key={kindCount.kind} value={kindCount.kind}>
                  {kindCount.kind} ({kindCount.count})
                </option>
              ))}
            </select>

            <span className="browse-filter-label">Sort</span>
            <select
              className="input kv-select"
              value={sort}
              aria-label="Sort notes"
              disabled={showingSearch}
              title={showingSearch ? 'Search results are ordered by relevance' : undefined}
              onChange={(event) => updateParams({ sort: event.target.value }, 'replace')}
            >
              <option value="name">By name</option>
              <option value="recent">Recently changed</option>
            </select>
          </div>
        </div>

        {showingSearch ? (
          <SearchResults
            query={query}
            searching={searching}
            result={searchResult}
            resultCount={results.length}
          />
        ) : !browse ? (
          <p className="text-muted">Loading…</p>
        ) : browse.notes.length > 0 ? (
          <>
            <div className="browse-result-head">
              <span className="text-muted browse-result-count">
                Showing {(browse.page - 1) * browse.page_size + 1}&ndash;
                {Math.min(browse.page * browse.page_size, browse.total)} of {browse.total} notes
              </span>
              <Pagination
                page={browse.page}
                totalPages={totalPages}
                onGo={(next) => updateParams({ page: String(next) }, 'replace')}
              />
            </div>
            <div className="item-list">
              {browse.notes.map((note) => (
                <Link className="item-row" to={`/browse/${note.stem}`} key={note.stem}>
                  <div className="item-row-main">
                    <span className="item-row-title">{note.title}</span>
                    <span className="item-row-meta">
                      <span className="badge">{note.kind}</span>
                      {note.tags.length > 0 && <span>{note.tags.join(' · ')}</span>}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </>
        ) : (
          <div className="empty-state">
            <p className="empty-state-title">
              {activeTag || activeKind ? 'Nothing matches these filters' : 'No notes indexed'}
            </p>
            {(activeTag || activeKind) && (
              <p style={{ margin: 'var(--space-1) 0 0' }}>
                The index has notes, just none carrying{' '}
                {activeTag ? <strong>{activeTag}</strong> : null}
                {activeTag && activeKind ? ' and ' : null}
                {activeKind ? <strong>{activeKind}</strong> : null}.{' '}
                <button
                  type="button"
                  className="btn-link"
                  onClick={() => updateParams({ tag: null, kind: null }, 'replace')}
                >
                  Clear the filters
                </button>
              </p>
            )}
          </div>
        )}
      </div>
    </>
  );
}

function SearchResults({
  query,
  searching,
  result,
  resultCount,
}: {
  query: string;
  searching: boolean;
  result: SearchResponse | null;
  resultCount: number;
}) {
  if (searching && !result) return <p className="text-muted">Searching…</p>;
  if (!result) return null;

  if (resultCount === 0) {
    return (
      <div className="empty-state">
        <p className="empty-state-title">Nothing matches “{result.query}”</p>
        <p style={{ margin: 'var(--space-1) 0 0' }}>
          Try fewer words, or browse by tag — clearing the search brings the list back.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="browse-result-head">
        <span className="text-muted browse-result-count">
          {resultCount} {resultCount === 1 ? 'match' : 'matches'} for “{result.query}”
        </span>
        {/* Said plainly rather than hidden: these results are keyword-only,
            and an operator wondering why an obvious note is missing deserves
            the reason rather than a worse list with no explanation. */}
        {result.semantic_available === false && (
          <span className="badge badge-warning" title={result.semantic_error ?? undefined}>
            wording only — meaning search unavailable
          </span>
        )}
      </div>
      <div className="item-list">
        {result.results.map((hit) => (
          <Link className="item-row" to={`/browse/${hit.stem}`} key={hit.stem}>
            <div className="item-row-main">
              <span className="item-row-title">{hit.title}</span>
              {hit.snippet && (
                <span className="search-snippet">
                  <SnippetText text={hit.snippet} query={query} />
                </span>
              )}
              <span className="item-row-meta">
                <span className="badge">{hit.kind}</span>
                <MatchedBy matchedBy={hit.matched_by} />
                {hit.tags.length > 0 && <span>{hit.tags.join(' · ')}</span>}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </>
  );
}

/** Why this note is in the list. A hit found only by meaning has none of the
 *  typed words in it, which looks like a mistake until the row says so. */
function MatchedBy({ matchedBy }: { matchedBy?: { keyword?: number; semantic?: number } }) {
  if (!matchedBy) return null;
  const byKeyword = matchedBy.keyword !== undefined;
  const bySemantic = matchedBy.semantic !== undefined;
  if (!byKeyword && !bySemantic) return null;

  const label = byKeyword && bySemantic ? 'wording + meaning' : byKeyword ? 'wording' : 'meaning';
  return <span className="badge search-matched-by">{label}</span>;
}

/** Numbered pages, not just Prev/Next: "Showing 141–160 of 900" with two
 *  arrows makes reaching the end a job. Shows a window around the current page
 *  so a 900-note vault does not render 45 buttons. */
function Pagination({
  page,
  totalPages,
  onGo,
}: {
  page: number;
  totalPages: number;
  onGo: (page: number) => void;
}) {
  if (totalPages <= 1) return null;

  const window = [page - 1, page, page + 1].filter((candidate) => candidate > 1 && candidate < totalPages);
  const numbers = [1, ...window, totalPages].filter(
    (candidate, index, all) => all.indexOf(candidate) === index,
  );

  return (
    <span className="browse-pagination">
      <button type="button" className="btn btn-compact" disabled={page <= 1} onClick={() => onGo(page - 1)}>
        &larr;
      </button>
      {numbers.map((number, index) => (
        <span key={number} className="browse-pagination-number">
          {index > 0 && number - numbers[index - 1] > 1 && (
            <span className="text-muted browse-pagination-gap">…</span>
          )}
          <button
            type="button"
            className={`btn btn-compact ${number === page ? 'btn-primary' : ''}`}
            aria-current={number === page ? 'page' : undefined}
            onClick={() => onGo(number)}
          >
            {number}
          </button>
        </span>
      ))}
      <button
        type="button"
        className="btn btn-compact"
        disabled={page >= totalPages}
        onClick={() => onGo(page + 1)}
      >
        &rarr;
      </button>
    </span>
  );
}
