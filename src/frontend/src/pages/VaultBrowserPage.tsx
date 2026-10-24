import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { VaultGraphCanvas } from '../features/vault-graph/VaultGraphCanvas';
import { SnippetText } from '../features/vault-browser/SnippetText';
import { TagClusters } from '../features/vault-browser/TagClusters';
import { VaultNavigator } from '../features/vault-browser/VaultNavigator';
import {
  fetchVaultSearchStatus,
  fetchFolders,
  fetchKinds,
  fetchNotes,
  fetchScopedGraph,
  fetchTagTree,
  search,
  type VaultSearchStatus,
  type BrowseResponse,
  type KindCount,
  type ScopedGraph,
  type TreeNode,
  type SearchResponse,
} from '../features/vault-browser/client';

const PAGE_SIZE = 20;

/** Nodes the graph will draw before it stops being readable. Past this it is a
 *  cloud: the backend returns the most connected ones and says it truncated,
 *  so the screen can say "narrow it down" instead of hanging. */
const GRAPH_NODE_LIMIT = 300;

/** The Vault — everything indexed, in one screen (operator, 2026-10-24: "Need
 *  to Merge the Vault with the Search").
 *
 * Search, the note list and the knowledge graph were three ways of looking at
 * one vault, on two screens, with a different idea of "what you are looking
 * at" each. Now there is one scope — a tag branch, a folder, a kind, a query —
 * and two ways to read it: **List** or **Graph**.
 *
 * **Where a note is, as something you can walk.** 312 tags across 15
 * categories and folders eight deep do not fit in a chip row, so the
 * navigator is a tree of either, and a tag means the branch under it.
 *
 * **The URL is the state.** Query, tag, folder, kind, sort, page and view all
 * live in it, so any view can be linked and reached with Back. Filters are
 * written with `replace` (`ADR-041`): changing a filter is not a journey.
 */
export function VaultBrowserPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get('q') ?? '';
  const activeTag = searchParams.get('tag');
  const activeFolder = searchParams.get('folder');
  const activeKind = searchParams.get('kind');
  const sort = searchParams.get('sort') ?? 'name';
  const view = searchParams.get('view') === 'graph' ? 'graph' : 'list';
  const navigateBy = searchParams.get('by') === 'folders' ? 'folders' : 'tags';
  const page = Math.max(1, Number(searchParams.get('page') ?? 1) || 1);

  const [status, setStatus] = useState<VaultSearchStatus | null>(null);
  const [tagTree, setTagTree] = useState<TreeNode[]>([]);
  const [folderTree, setFolderTree] = useState<TreeNode[]>([]);
  const [kinds, setKinds] = useState<KindCount[]>([]);
  const [graph, setGraph] = useState<ScopedGraph | null>(null);
  const [browse, setBrowse] = useState<BrowseResponse | null>(null);
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    fetchVaultSearchStatus().then(setStatus);
  }, []);

  // While the server is still reading the vault, ask again rather than making
  // the operator reload. Stops the moment there is an index, so a built vault
  // costs one request as before.
  useEffect(() => {
    if (!status || status.indexed || !status.building) return;
    const timer = setInterval(() => {
      fetchVaultSearchStatus().then(setStatus).catch(() => {});
    }, 2000);
    return () => clearInterval(timer);
  }, [status]);

  useEffect(() => {
    if (!status?.indexed) return;
    fetchTagTree().then((response) => setTagTree(response.tags));
    fetchFolders().then((response) => setFolderTree(response.folders));
    fetchKinds().then((response) => setKinds(response.kinds));
  }, [status]);


  useEffect(() => {
    if (!status?.indexed || query || view === 'graph') return;
    setBrowse(null);
    fetchNotes({
      tag: activeTag ?? undefined,
      folder: activeFolder ?? undefined,
      kind: activeKind ?? undefined,
      sort,
      page,
      page_size: PAGE_SIZE,
    }).then(setBrowse);
  }, [status, activeTag, activeFolder, activeKind, sort, page, query, view]);

  // The graph is fetched for the SCOPE, never for the whole vault: unscoped it
  // is 4,300 nodes, which is a cloud. With nothing selected the graph view
  // shows tag clusters instead and no fetch happens at all.
  useEffect(() => {
    const scoped = Boolean(activeTag || activeFolder || activeKind);
    if (!status?.indexed || view !== 'graph' || !scoped) {
      setGraph(null);
      return;
    }
    fetchScopedGraph({
      tag: activeTag ?? undefined,
      folder: activeFolder ?? undefined,
      kind: activeKind ?? undefined,
      limit: GRAPH_NODE_LIMIT,
    }).then(setGraph);
  }, [status, view, activeTag, activeFolder, activeKind]);

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
  const updateParams = useCallback(
    (changes: Record<string, string | null>, historyMode: 'push' | 'replace') => {
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
    },
    [searchParams, setSearchParams],
  );

  // Stable, so the memoised navigator can actually skip its 2,281 folder
  // nodes: a fresh arrow every render would change the prop every time and
  // make the memo pure overhead.
  const selectScope = useCallback(
    (path: string | null) =>
      updateParams(
        navigateBy === 'tags' ? { tag: path, folder: null } : { folder: path, tag: null },
        'replace',
      ),
    [updateParams, navigateBy],
  );

  if (!status) {
    return (
      <>
        <h1>The Vault</h1>
        <p className="text-muted">Loading…</p>
      </>
    );
  }

  // Two different answers that used to look the same. The index lives in the
  // server's memory, so a restart has none until the boot rebuild lands, and
  // for those seconds this screen told the operator their vault was empty
  // (2026-10-24: "When I just Restart the Server Nothing Indexed Yet Appear
  // Which is not true"). It waits and says so instead, and the poll above
  // brings it back by itself.
  if (!status.indexed && status.building) {
    return (
      <>
        <h1>The Vault</h1>
        <div className="card">
          <div className="empty-state">
            <span className="material-symbols-outlined empty-state-icon" aria-hidden="true">
              hourglass_top
            </span>
            <p className="empty-state-title">Building the index…</p>
            <p style={{ margin: 'var(--space-1) 0 0' }}>
              The server reads the whole vault when it starts, and it is still reading. Your
              notes are all there — this page opens on its own the moment it finishes.
            </p>
          </div>
        </div>
      </>
    );
  }

  if (!status.indexed) {
    return (
      <>
        <h1>The Vault</h1>
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
  const scopeSelected = activeTag ?? activeFolder;
  const scopeLabel = activeTag ?? (activeFolder ? `📁 ${activeFolder}` : null);

  return (
    <>
      <h1>The Vault</h1>
      <p className="text-muted">
        Everything indexed from your vault — searchable by wording and by meaning, walkable
        by tag or by folder.
      </p>

      <div className="card browse-card">
        <SearchBox
          query={query}
          onSearch={(text) => updateParams({ q: text }, 'push')}
          onClear={() => updateParams({ q: null }, 'push')}
        />

        {/* Filters stay visible while searching: they are how you get back to
            the list, and hiding them would make the screen change shape. */}
        <div className="browse-filters">
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

            {/* List or Graph: two readings of the SAME scope, which is the
                whole point of merging the two screens. The toggle is here
                rather than in the navigator because it changes how the
                results are drawn, not what they are. */}
            <span className="browse-view-toggle">
              {(['list', 'graph'] as const).map((candidate) => (
                <button
                  key={candidate}
                  type="button"
                  className={`btn btn-compact ${view === candidate ? 'btn-primary' : ''}`}
                  aria-pressed={view === candidate}
                  onClick={() => updateParams({ view: candidate === 'list' ? null : candidate }, 'replace')}
                >
                  <span className="material-symbols-outlined" aria-hidden="true">
                    {candidate === 'list' ? 'list' : 'hub'}
                  </span>
                  {candidate === 'list' ? 'List' : 'Graph'}
                </button>
              ))}
            </span>
          </div>
        </div>

        <div className="vault-layout">
          <aside className="vault-navigator">
            <div className="vault-navigator-switch">
              {(['tags', 'folders'] as const).map((candidate) => (
                <button
                  key={candidate}
                  type="button"
                  className={`btn btn-compact ${navigateBy === candidate ? 'btn-primary' : ''}`}
                  aria-pressed={navigateBy === candidate}
                  // Switching how you navigate drops the other axis's
                  // selection: a folder filter left behind while you browse
                  // tags is an invisible reason the list is short.
                  onClick={() =>
                    updateParams(
                      { by: candidate === 'tags' ? null : candidate, tag: null, folder: null },
                      'replace',
                    )
                  }
                >
                  {candidate === 'tags' ? 'Tags' : 'Folders'}
                </button>
              ))}
            </div>
            <VaultNavigator
              nodes={navigateBy === 'tags' ? tagTree : folderTree}
              selected={navigateBy === 'tags' ? activeTag : activeFolder}
              emptyLabel={
                navigateBy === 'tags' ? 'No tags in the index yet.' : 'Every note sits at the vault root.'
              }
              onSelect={selectScope}
            />
          </aside>

          <div className="vault-results">
        {scopeLabel && (
          <p className="vault-scope">
            Showing <strong>{scopeLabel}</strong>
            <button
              type="button"
              className="btn-link"
              onClick={() => updateParams({ tag: null, folder: null }, 'replace')}
            >
              clear
            </button>
          </p>
        )}

        {view === 'graph' ? (
          <GraphView
            graph={graph}
            scopeSelected={scopeSelected}
            tagTree={tagTree}
            activeTag={activeTag}
            onDrillDown={(path) => updateParams({ tag: path, by: null, folder: null }, 'replace')}
          />
        ) : showingSearch ? (
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
            <div className="note-list">
              {browse.notes.map((note) => (
                <Link className="note-row" to={`/browse/${note.stem}`} key={note.stem}>
                  <span className="note-row-kind">{note.kind}</span>
                  <span className="note-row-title" title={note.title}>
                    {note.title}
                  </span>
                  <NoteRowTags tags={note.tags} />
                  <span className="note-row-when">{whenInWords(note.modified_at)}</span>
                </Link>
              ))}
            </div>
          </>
        ) : (
          <div className="empty-state">
            <p className="empty-state-title">
              {scopeSelected || activeKind ? 'Nothing matches these filters' : 'No notes indexed'}
            </p>
            {(scopeSelected || activeKind) && (
              <p style={{ margin: 'var(--space-1) 0 0' }}>
                The index has notes, just none in{' '}
                {scopeLabel ? <strong>{scopeLabel}</strong> : null}
                {scopeLabel && activeKind ? ' of kind ' : null}
                {activeKind ? <strong>{activeKind}</strong> : null}.{' '}
                <button
                  type="button"
                  className="btn-link"
                  onClick={() => updateParams({ tag: null, folder: null, kind: null }, 'replace')}
                >
                  Clear the filters
                </button>
              </p>
            )}
          </div>
        )}
          </div>
        </div>
      </div>
    </>
  );
}

/** The search field, owning its own draft.
 *
 * It lived on the page, which made every keystroke re-render the page — and
 * the page renders the navigator: 312 tag nodes, or **2,281 folder nodes** on
 * this vault, every one a component, doubled again by StrictMode in
 * development. Typing was slower than typing (operator, 2026-10-24: "Search
 * your notes is not entering text").
 *
 * Here the draft is local, so a keystroke re-renders this field and nothing
 * else. The page still owns the committed query — it is in the URL — and this
 * only owns what has been typed but not yet submitted.
 */
function SearchBox({
  query,
  onSearch,
  onClear,
}: {
  query: string;
  onSearch: (text: string) => void;
  onClear: () => void;
}) {
  const [draft, setDraft] = useState(query);

  // The committed query changing from outside (Back, a cleared filter, a
  // pasted link) is the one time the box should be rewritten under the
  // person typing in it.
  useEffect(() => {
    setDraft(query);
  }, [query]);

  return (
    <div className="browse-search-row">
      <span className="material-symbols-outlined browse-search-icon" aria-hidden="true">
        search
      </span>
      <input
        className="input browse-search-input"
        type="search"
        value={draft}
        placeholder="Search your notes…"
        aria-label="Search your notes"
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter') onSearch(draft.trim());
          if (event.key === 'Escape') {
            setDraft('');
            onClear();
          }
        }}
      />
      <button type="button" className="btn btn-primary" onClick={() => onSearch(draft.trim())}>
        Search
      </button>
      {query && (
        <button
          type="button"
          className="btn"
          onClick={() => {
            setDraft('');
            onClear();
          }}
        >
          Clear
        </button>
      )}
    </div>
  );
}

/** How many tag chips fit on a row before they are the row.
 *
 * Two is what a real note carries here, but a handful carry six, and a row
 * that grows to fit them makes the whole list ragged. */
const TAGS_PER_ROW = 2;

/** A note's tags, as chips, by their LAST segment.
 *
 * The full path is the problem this solves: a real tag in this vault is
 * `customer/abu-dhabi-agriculture-and-food-safety-authority` — 54 characters —
 * and two of them joined into a meta line is longer than any title, in every
 * row, wrapping. The leaf is the part that identifies the thing; the path is
 * on hover for when it matters.
 */
function NoteRowTags({ tags }: { tags: string[] }) {
  if (tags.length === 0) return <span className="note-row-tags" />;
  const shown = tags.slice(0, TAGS_PER_ROW);

  return (
    <span className="note-row-tags">
      {shown.map((tag) => (
        <span className="note-tag" key={tag} title={tag}>
          {tag.split('/').pop()}
        </span>
      ))}
      {tags.length > shown.length && (
        <span className="note-tag is-more" title={tags.slice(TAGS_PER_ROW).join('\n')}>
          +{tags.length - shown.length}
        </span>
      )}
    </span>
  );
}

/** "3 days ago" rather than a timestamp: in a list you are judging recency,
 *  not reading a date. The exact one is on hover. */
function whenInWords(iso?: string | null): string {
  if (!iso) return '';
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '';
  const days = Math.floor((Date.now() - then) / 86_400_000);
  if (days <= 0) return 'today';
  if (days === 1) return 'yesterday';
  if (days < 30) return `${days}d ago`;
  if (days < 365) return `${Math.floor(days / 30)}mo ago`;
  return `${Math.floor(days / 365)}y ago`;
}

/** The same scope as the list, drawn as a graph.
 *
 * With nothing selected it is the tag CLUSTERS, not the vault: 4,300 nodes at
 * once is a cloud nobody can read, and the top of the tag tree is fifteen
 * bubbles you can actually aim at (operator, 2026-10-24). Choosing one drills
 * into its children; once a branch holds notes rather than more tags, the real
 * force graph takes over.
 */
function GraphView({
  graph,
  scopeSelected,
  tagTree,
  activeTag,
  onDrillDown,
}: {
  graph: ScopedGraph | null;
  scopeSelected: string | null;
  tagTree: TreeNode[];
  activeTag: string | null;
  onDrillDown: (path: string) => void;
}) {
  // The children of whatever is selected, so the clusters keep drilling
  // rather than jumping straight to notes at the second level.
  const childrenOfSelection = useMemo(() => {
    if (!activeTag) return tagTree;
    const find = (nodes: TreeNode[]): TreeNode | null => {
      for (const node of nodes) {
        if (node.path === activeTag) return node;
        const inside = find(node.children);
        if (inside) return inside;
      }
      return null;
    };
    return find(tagTree)?.children ?? [];
  }, [tagTree, activeTag]);

  if (!scopeSelected) {
    return (
      <TagClusters
        nodes={tagTree}
        onDrillDown={onDrillDown}
        heading="Your vault by tag — pick one to go inside. Sized by how much is in it."
      />
    );
  }

  if (!graph) return <p className="text-muted">Drawing the graph…</p>;

  return (
    <>
      {childrenOfSelection.length > 0 && (
        <TagClusters
          nodes={childrenOfSelection}
          onDrillDown={onDrillDown}
          heading={`Inside ${activeTag} — go deeper, or read the notes below.`}
        />
      )}
      {graph.truncated && (
        <p className="text-muted vault-graph-truncated">
          This branch holds {graph.total} notes; showing the {graph.nodes.length} most linked.
          Narrow it down to see all of them.
        </p>
      )}
      {graph.nodes.length > 0 ? (
        <VaultGraphCanvas nodes={graph.nodes} edges={graph.edges} />
      ) : (
        <p className="text-muted">Nothing in this branch to draw.</p>
      )}
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
