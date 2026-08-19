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

export interface ScopeSuggestions {
  tags: TagCount[];
  folders: string[];
}

export function fetchScopeSuggestions(): Promise<ScopeSuggestions> {
  return apiFetch<ScopeSuggestions>('/vault-search/scope-suggestions');
}
