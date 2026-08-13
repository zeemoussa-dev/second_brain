---
id: REQ-SB-02-US-01-T04
title: VaultBrowserPage.tsx + NoteDetailPage.tsx, plus nav wiring
parent_story: REQ-SB-02-US-01
requirement_id: REQ-SB-02
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: MVP
depends_on: [REQ-SB-02-US-01-T03, REQ-SB-12-US-01-T01]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-02-US-01-T04 — `VaultBrowserPage.tsx` + `NoteDetailPage.tsx`

## Parent Story

- Story: [[REQ-SB-02-US-01]] — `../UserStories/REQ-SB-02-US-01-browse-and-search.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-02 *Browse & Search*

**Task-level dependency note:** this task edits `App.tsx`/`Sidebar.tsx`
(built by `REQ-SB-12-US-01-T01`) — the same explicit cross-story
`depends_on` shape `REQ-SB-31-US-01-T04`/`REQ-SB-12-US-02-T04` already
established for the identical reason.

---

## Objective

Build the real Browse & Search UI against `T03`'s `/vault-search/...`
endpoints, per the approved prototype (`html-prototype/vault-browser.html`,
`html-prototype/note-detail.html`): a search box + ranked results, a
tag-filter chip row + paginated browse list, a note-detail view with
forward-link/backlink navigation, and the honest "nothing indexed yet"
state gating the whole page — plus a new top-level nav item and two new
routes.

---

## Starting State → End State

**Before / Inputs:**
- `T03` has landed `GET /vault-search/status|notes|notes/{stem}|search|tags`.
- `App.tsx` routes `/`, `/my-day` (+ drill-downs), `/settings`,
  `/system-health` inside `<AppShell>`; `Sidebar.tsx` has nav items for
  Agents Map, My Day, Settings, System Health.
- `styles/settings.css`/`styles/shell.css` already carry `.card`,
  `.badge*`, `.kv-list`, `.item-list`, `.empty-state`,
  `.btn`/`.btn-primary`, `.input`, `.mono`, `.text-muted` — no need to
  re-add any of those. `a.item-row`/`button.item-row` and `.tag-chip` are
  **not** yet ported to `src/frontend` — this task is the first to need
  them (see the new `styles/vault-browser.css` below).

**After / Outputs:**
- `src/frontend/src/features/vault-browser/client.ts` exists.
- `src/frontend/src/pages/VaultBrowserPage.tsx` exists (route `/browse`).
- `src/frontend/src/pages/NoteDetailPage.tsx` exists (route
  `/browse/:stem`).
- `src/frontend/src/styles/vault-browser.css` exists (two small additive
  rules, ported verbatim from `html-prototype/styles.css`).
- `App.tsx` gains both routes; `Sidebar.tsx` gains one new nav item;
  `main.tsx` imports the new stylesheet.

---

## Files to Modify

- `src/frontend/src/styles/vault-browser.css` (new — ported verbatim from
  `html-prototype/styles.css`'s own "Clickable item-row + tag chip"
  section; no renaming, per `ADR-010` Decision 3):
  ```css
  a.item-row,
  button.item-row {
    text-decoration: none;
    color: inherit;
    border: none;
    width: 100%;
    text-align: left;
    font: inherit;
    cursor: pointer;
  }

  a.item-row:hover,
  button.item-row:hover {
    background: color-mix(in srgb, var(--color-accent) 12%, var(--color-surface-raised));
  }

  .tag-chip {
    border-radius: 999px;
    font-size: var(--font-size-sm);
    padding: 2px var(--space-3);
  }
  ```

- `src/frontend/src/main.tsx` — add one import, additive only, alongside
  the existing `styles/*.css` imports:
  ```tsx
  import './styles/vault-browser.css'
  ```

- `src/frontend/src/features/vault-browser/client.ts` (new):
  ```typescript
  import { apiFetch } from '../../api/client';

  export interface VaultSearchStatus {
    indexed: boolean;
    last_rebuilt_at: string | null;
  }

  export function fetchVaultSearchStatus(): Promise<VaultSearchStatus> {
    return apiFetch<VaultSearchStatus>('/vault-search/status');
  }

  export interface NoteSummary {
    stem: string;
    title: string;
    kind: string;
    tags: string[];
  }

  export interface BrowseResponse {
    total: number;
    page: number;
    page_size: number;
    notes: NoteSummary[];
  }

  export function fetchNotes(
    params: { tag?: string; page?: number; page_size?: number } = {},
  ): Promise<BrowseResponse> {
    const query = new URLSearchParams();
    if (params.tag) query.set('tag', params.tag);
    if (params.page) query.set('page', String(params.page));
    if (params.page_size) query.set('page_size', String(params.page_size));
    const qs = query.toString();
    return apiFetch<BrowseResponse>(`/vault-search/notes${qs ? `?${qs}` : ''}`);
  }

  export interface TagCount {
    tag: string;
    count: number;
  }

  export function fetchTags(): Promise<{ tags: TagCount[] }> {
    return apiFetch<{ tags: TagCount[] }>('/vault-search/tags');
  }

  export interface SearchResult extends NoteSummary {
    rank: number;
    score: number;
  }

  export interface SearchResponse {
    query: string;
    results: SearchResult[];
  }

  export function search(query: string, limit = 20): Promise<SearchResponse> {
    return apiFetch<SearchResponse>(
      `/vault-search/search?q=${encodeURIComponent(query)}&limit=${limit}`,
    );
  }

  export interface NoteDetail extends NoteSummary {
    frontmatter: Record<string, unknown>;
    forward_links: NoteSummary[];
    backlinks: NoteSummary[];
  }

  export function fetchNoteDetail(stem: string): Promise<NoteDetail> {
    return apiFetch<NoteDetail>(`/vault-search/notes/${encodeURIComponent(stem)}`);
  }
  ```

- `src/frontend/src/pages/VaultBrowserPage.tsx` (new):
  ```tsx
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
  ```

- `src/frontend/src/pages/NoteDetailPage.tsx` (new):
  ```tsx
  import { useEffect, useState } from 'react';
  import { Link, useParams } from 'react-router';
  import { ApiError } from '../api/client';
  import { fetchNoteDetail, type NoteDetail } from '../features/vault-browser/client';

  export function NoteDetailPage() {
    const { stem } = useParams<{ stem: string }>();
    const [detail, setDetail] = useState<NoteDetail | null>(null);
    const [notFound, setNotFound] = useState(false);

    useEffect(() => {
      if (!stem) return;
      setDetail(null);
      setNotFound(false);
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
              <span className="badge" style={{ marginRight: 'var(--space-1)' }} key={tag}>{tag}</span>
            ))}
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
      </>
    );
  }
  ```

- `src/frontend/src/App.tsx` — add the imports and routes, additive only:
  ```tsx
  import { VaultBrowserPage } from './pages/VaultBrowserPage';
  import { NoteDetailPage } from './pages/NoteDetailPage';
  ...
  <Route path="/browse" element={<VaultBrowserPage />} />
  <Route path="/browse/:stem" element={<NoteDetailPage />} />
  ```

- `src/frontend/src/components/shell/Sidebar.tsx` — add one new
  `<NavLink>` after System Health, additive only:
  ```tsx
  <NavLink
    to="/browse"
    className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
  >
    <span className="nav-icon">&#128269;</span>
    <span className="nav-label">Browse &amp; Search</span>
  </NavLink>
  ```

---

## Constraints

- Inherits from parent story, and `ADR-010`'s conventions: `react-router`
  `<Link>`/`<NavLink>`/`useParams` for navigation, native `fetch` behind
  the existing `apiFetch` client, class names reused verbatim from
  already-ported CSS wherever possible — the only new CSS is the two rules
  in `vault-browser.css` above (already documented in
  `html-prototype/styles.css`, ported verbatim, no renaming).
- `GET /vault-search/status` is checked **first**, on every mount, before
  any other `/vault-search/...` call fires — `indexed: false` must replace
  the entire page with the honest empty state, never a partial page with a
  broken/empty list underneath (Scenario 7).
- The tag-filter chip row renders the **real** tags from `GET
  /vault-search/tags` — never a hardcoded/illustrative tag list.
- A `404` from `GET /vault-search/notes/{stem}` must render an honest "no
  such note" state on `NoteDetailPage`, not an uncaught error/blank page.
- Do not modify `MyDayPage.tsx`, `SettingsPage.tsx`, `SystemHealthPage.tsx`,
  `AgentsMapPage.tsx`, or any other existing page/route.

---

## Tests

<!-- Structural ACs, per the decomposer's own "durable design layer" rule
-- DOM structure/regions, not visual polish. jsdom sees no computed CSS/
layout/colour; pure visual polish is spot-checked against the approved
prototype out-of-band, not a locked AC. -->

**Manual verification steps** (frontend dev server running against the
real backend on port `8001`; open `http://localhost:5173/browse` in a
browser):

1. **[REQ-SB-02-US-01-AC-01]** With the real, already-indexed vault, open
   `/browse`. Confirm the "Browse by tag" card's "All notes" view lists
   real indexed notes, correctly paginated (`Showing X–Y of <total>
   notes`), and Prev/Next work.
2. **[REQ-SB-02-US-01-AC-02]** Click a real tag chip (one with real
   matches). Confirm the list narrows to only notes carrying that tag.
3. **[REQ-SB-02-US-01-AC-03]** Click a note row with at least one real
   link. Confirm `NoteDetailPage` renders its Forward links/Backlinks as
   real, clickable rows, and clicking one navigates to that target note's
   own detail view (a real route change, not a static swap).
4. **[REQ-SB-02-US-01-AC-04]** Type a real query with known relevant notes
   into the search box, submit. Confirm ranked results render, most
   relevant first.
5. **[REQ-SB-02-US-01-AC-05]** Type a nonsense query, submit. Confirm the
   honest "No notes match ..." empty state renders, not an error.
6. **[REQ-SB-02-US-01-AC-06]** Click a tag chip with zero real matches (or
   temporarily use a browser devtools override / a throwaway tag string
   via the URL if no real zero-match tag exists). Confirm the honest
   "No notes carry the tag ..." empty state renders.
7. **[REQ-SB-02-US-01-AC-07]** Temporarily point `VITE_API_BASE_URL` (or
   the dev proxy) at a backend instance whose index has never been
   rebuilt this process lifetime (e.g. a freshly-started backend, checked
   via `GET /vault-search/status` returning `indexed: false` **before**
   the app-start scheduler tick completes — a narrow timing window; if
   impractical to catch live, verify this state via a direct, disclosed,
   reverted stub of `fetchVaultSearchStatus()` returning `{"indexed":
   false, "last_rebuilt_at": null}`, mirroring this codebase's own
   established temporary-client-side-stub-and-revert pattern for AC states
   real data can't produce naturally). Confirm the entire page is replaced
   by the honest "Nothing indexed yet" state — no search box, no tag
   chips, no list underneath.
8. Non-AC structural check: confirm a `Browse & Search` `.nav-item`
   renders in the sidebar on every page, correctly `active` only on
   `/browse`/`/browse/:stem`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-02-US-01-AC-01` — the full indexed note list renders,
      correctly paginated
- [x] `REQ-SB-02-US-01-AC-02` — a real tag filter correctly narrows the
      list, using the real tag list from `GET /vault-search/tags`
- [x] `REQ-SB-02-US-01-AC-03` — a note's forward-links/backlinks render as
      real, clickable navigation between notes
- [x] `REQ-SB-02-US-01-AC-04` — a real search query renders ranked results
- [x] `REQ-SB-02-US-01-AC-05` — a non-matching search query renders an
      honest empty state, not an error
- [x] `REQ-SB-02-US-01-AC-06` — a non-matching tag filter renders an
      honest empty state, not an error
- [x] `REQ-SB-02-US-01-AC-07` — an unindexed backend replaces the entire
      page with an honest "nothing indexed yet" state
- [x] New `Browse & Search` nav item present and correctly highlighted
      only on `/browse`/`/browse/:stem`
- [x] A `404` note-detail lookup renders an honest "no such note" state,
      not an uncaught error
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any backend change — `T01`/`T02`/`T03`.
- A visual/interactive wikilink-graph canvas — resolved out of scope for
  this story (see the story's own Constraints/Non-Goals).
- Editing notes from within this UI — read-only throughout.
- Auto-refresh/polling of `/vault-search/status` beyond per-mount fetch.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-026` created at
`/plan-tasks`) — see `REVIEW-QUEUE.md`. This task itself introduces no new
architectural decision of its own; it consumes `T03`'s already-designed
API surface exactly as `architecture.md`'s "Browse & Search" section
describes.

Region-for-region parity target: `html-prototype/vault-browser.html` (this
task's `VaultBrowserPage.tsx`) and `html-prototype/note-detail.html` (this
task's `NoteDetailPage.tsx`) — reuse their own documented class usage
(`.card`, `.item-list`/`.item-row`, `.tag-chip`, `.badge*`, `.empty-state`,
`.kv-list`) rather than inventing new markup shapes.

---

## Implementation Log

**2026-08-13 — Built and live-verified in a real browser against the real
backend/vault.** All files built exactly as specified: `styles/
vault-browser.css` (ported verbatim), `features/vault-browser/client.ts`,
`pages/VaultBrowserPage.tsx`, `pages/NoteDetailPage.tsx`, `App.tsx` routes
(`/browse`, `/browse/:stem`), `Sidebar.tsx` new nav item, `main.tsx`
stylesheet import. `npx tsc --noEmit` — clean, zero errors.

**`npm run build` — pre-existing, out-of-scope failure, not caused by this
task:** production build fails in `styles/agent-panel.css` (`SPRINT-010`'s
own file, untracked/uncommitted from a prior session, not in this task's
`## Files to Modify`) — a `lightningcss` "Invalid dangling combinator in
selector" error pointing at a comment block, unrelated to any file this
task touches. Confirmed via `git status` that `agent-panel.css` is
pre-existing and untracked (`??`), not modified by this task. `npx tsc
--noEmit` (the check this task can actually attest to) is clean. Not
fixed — out of this task's own scope (`agent-panel.css` is not in `##
Files to Modify`); flagged to `REVIEW-QUEUE.md` for a human decision on
whether to fix/commit that file.

**Live browser verification** (real dev server on `:5173` against the real
backend on `:8001`, driven via this project's own established zero-
dependency headless-Chrome-via-CDP pattern — Node v22's built-in `fetch`/
`WebSocket`, no Playwright/Puppeteer):
- **[AC-01]** `/browse` — real 503-note list, "Showing 1–20 of 503 notes",
  Prev/Next present, sidebar `Browse & Search` nav item correctly
  `active` — PASS (screenshot: real list rendered, matches prototype
  region-for-region).
- **[AC-02]** Clicked the real `customer/masdar (54)` tag chip — list
  narrowed to 20/54, every visible row's meta line carries the tag —
  PASS.
- **[AC-06]** Zero-match tag state verified via a disclosed, reverted
  client-side `window.fetch` stub rewriting the tag query param to a
  genuinely nonexistent tag (no real zero-match tag exists in the live
  vault at verification time — mirrors this task's own Tests item 6's
  explicitly sanctioned "throwaway tag string" fallback) — rendered "No
  notes carry the tag customer/masdar" honestly, not an error; reverted
  immediately after — PASS.
- **[AC-04]** Typed "masdar renewal", clicked Search — real ranked
  results rendered, `#1 Masdar` (Customer hub) first, most relevant
  first, matching the HTTP layer's own already-verified ranking — PASS.
- **[AC-05]** Typed the nonsense query
  `zzqxvbjklmnop9999nonexistenttoken` (see `T02`'s own logged AC-05
  substitution note), clicked Search — honest "No notes match ..." empty
  state rendered, not an error — PASS.
- **[AC-03]** Clicked a real note row (`-o=exchangelabs-ou=exchange
  administrative group (fydibohf23spdlt)-cn=recipients`, a real legacy
  Person note with 0 forward links / 16 real backlinks) — real client-side
  route change to `/browse/-o=exchangelabs-...`, `NoteDetailPage` rendered
  its real backlinks as clickable rows; clicked the first backlink
  ("Building the Infra Foundation for Masdar Data Lake") — real second
  route change, that note's own detail rendered correctly — genuine
  multi-hop wikilink navigation confirmed live, not a static swap — PASS.
- A direct `GET /browse/_no_such_stem_` navigation rendered the honest
  `No indexed note found for "_no_such_stem_"` state, not a blank/crashed
  page — PASS (additional non-AC structural check, matches the task's own
  404-handling Constraint).
- **[AC-07]** Verified via a disclosed, reverted client-side stub of
  `fetchVaultSearchStatus()`'s underlying `window.fetch('/vault-search/
  status')` call returning `{"indexed": false, "last_rebuilt_at": null}`,
  triggered via an SPA client-side remount (nav away/back, not a hard
  page reload — a hard reload would wipe the in-page stub, a testing-tool
  detail, not a product behavior) — the entire page was replaced by
  "Nothing indexed yet," with no search box, no tag chips, no list
  underneath — PASS; reverted immediately after.
- Non-AC structural check: `Browse & Search` `.nav-item` renders on every
  page, correctly `active` only on `/browse`/`/browse/:stem` — PASS.

**Visual/Layer-1 review:** screenshots captured at each state above and
reviewed directly (not just traced) — region-for-region match against
`html-prototype/vault-browser.html`/`note-detail.html` (`.card`,
`.item-list`/`.item-row`, `.tag-chip`, `.badge`, `.empty-state` all render
with correct computed styling, no layout breakage).

No deviation from the plan. `MyDayPage.tsx`/`SettingsPage.tsx`/
`SystemHealthPage.tsx`/`AgentsMapPage.tsx` untouched (confirmed via `git
status` — only this task's own listed files changed).

gate: flagged 2026-08-13 — the pre-existing `agent-panel.css` production-
build failure (unrelated to this task's own files) is logged to
`REVIEW-QUEUE.md` for a human decision; not itself a locked-AC failure
(every locked AC above passed via the dev server, the same verification
surface this task's own Tests specify).
