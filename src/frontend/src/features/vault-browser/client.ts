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
  /** When the note file last changed. Only the browse LIST carries it — it
   *  costs a stat per note, and that is affordable for a page of twenty and
   *  not for a graph of hundreds. */
  modified_at?: string | null;
}

export interface BrowseResponse {
  total: number;
  page: number;
  page_size: number;
  notes: NoteSummary[];
}

export function fetchNotes(
  params: {
    tag?: string;
    kind?: string;
    folder?: string;
    sort?: string;
    page?: number;
    page_size?: number;
  } = {},
): Promise<BrowseResponse> {
  const query = new URLSearchParams();
  if (params.tag) query.set('tag', params.tag);
  if (params.kind) query.set('kind', params.kind);
  if (params.folder) query.set('folder', params.folder);
  if (params.sort) query.set('sort', params.sort);
  if (params.page) query.set('page', String(params.page));
  if (params.page_size) query.set('page_size', String(params.page_size));
  const qs = query.toString();
  return apiFetch<BrowseResponse>(`/vault-search/notes${qs ? `?${qs}` : ''}`);
}

/** A tag category or a folder, with everything beneath it counted.
 *  The same shape for both, because they are the same thing to navigate:
 *  a path, a name, how much is under it, and what is under it. */
export interface TreeNode {
  path: string;
  name: string;
  count: number;
  children: TreeNode[];
}

export function fetchTagTree(): Promise<{ tags: TreeNode[] }> {
  return apiFetch<{ tags: TreeNode[] }>('/vault-search/tag-tree');
}

export function fetchFolders(): Promise<{ folders: TreeNode[] }> {
  return apiFetch<{ folders: TreeNode[] }>('/vault-search/folders');
}

export interface ScopedGraph {
  nodes: { stem: string; title: string; kind: string; tags: string[] }[];
  edges: { source: string; target: string }[];
  /** How many notes the scope really holds — `nodes` may be capped. */
  total: number;
  truncated: boolean;
}

export function fetchScopedGraph(
  params: { tag?: string; kind?: string; folder?: string; limit?: number } = {},
): Promise<ScopedGraph> {
  const query = new URLSearchParams();
  if (params.tag) query.set('tag', params.tag);
  if (params.kind) query.set('kind', params.kind);
  if (params.folder) query.set('folder', params.folder);
  if (params.limit) query.set('limit', String(params.limit));
  const qs = query.toString();
  return apiFetch<ScopedGraph>(`/vault-search/graph${qs ? `?${qs}` : ''}`);
}

export interface KindCount {
  kind: string;
  count: number;
}

export function fetchKinds(): Promise<{ kinds: KindCount[] }> {
  return apiFetch<{ kinds: KindCount[] }>('/vault-search/kinds');
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
  /** The window of the note's text the match sits in — plain text, so the
   *  highlight is this app's job and not the API's. Empty when the note has
   *  nothing to quote. */
  snippet?: string;
  /** Which ranker found it, and at what rank: `{keyword: 3, semantic: 1}`.
   *  Only the hybrid endpoint reports this. */
  matched_by?: { keyword?: number; semantic?: number };
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  /** Hybrid only. False means the meaning half could not run — the index was
   *  never built, or this subscription cannot call the embedding model — and
   *  these results are keyword-only. */
  semantic_available?: boolean;
  semantic_error?: string | null;
}

/** Keyword and meaning, fused.
 *
 * `/hybrid` rather than `/search`, which is keyword alone: this one degrades
 * to exactly that when the semantic half is unavailable, and says so in
 * `semantic_available`, so it is never the worse answer. The screen spent
 * months calling the weaker endpoint while the semantic index sat unused
 * (found 2026-10-24).
 */
export function search(query: string, limit = 20): Promise<SearchResponse> {
  return apiFetch<SearchResponse>(
    `/vault-search/hybrid?q=${encodeURIComponent(query)}&limit=${limit}`,
  );
}

export interface NoteDetail extends NoteSummary {
  frontmatter: Record<string, unknown>;
  // Real markdown body text (2026-08-23) -- read fresh from disk, never
  // cached in the index (vault_indexing.py's own established reasoning,
  // ADR-026). Raw, wikilinks and all -- NoteDetailPage.tsx does the
  // wikilink -> real note / markdown -> HTML rendering.
  body: string;
  forward_links: NoteSummary[];
  backlinks: NoteSummary[];
  /** The note's content as it was when this was read. Sent back on save so a
   *  file an agent rewrote in the meantime refuses rather than loses one of
   *  the two versions. */
  version: string;
  /** False for a captured message, whose body is HTML on disk and markdown
   *  here: saving what is on screen would replace the original with a
   *  rendering of itself. */
  editable: boolean;
}

/** Compass fixes the typing in a draft. Takes the TEXT, not the note's name:
 *  what wants tidying is what is in the editor, which is the whole point of
 *  tidying before it is saved. */
export function tidyText(text: string): Promise<{ text: string; changed: boolean }> {
  return apiFetch<{ text: string; changed: boolean }>('/vault-search/tidy', {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
}

export function saveNoteBody(
  stem: string,
  body: string,
  version: string,
): Promise<{ ok: boolean; version: string }> {
  return apiFetch<{ ok: boolean; version: string }>(
    `/vault-search/notes/${encodeURIComponent(stem)}/body`,
    { method: 'PUT', body: JSON.stringify({ body, version }) },
  );
}

export function fetchNoteDetail(stem: string): Promise<NoteDetail> {
  return apiFetch<NoteDetail>(`/vault-search/notes/${encodeURIComponent(stem)}`);
}

export interface ScopeSuggestions {
  tags: TagCount[];
  folders: string[];
}

export function fetchScopeSuggestions(): Promise<ScopeSuggestions> {
  return apiFetch<ScopeSuggestions>('/vault-search/scope-suggestions');
}
