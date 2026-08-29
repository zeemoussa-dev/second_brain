import { apiFetch } from '../../api/client';

// 2026-08-29 -- the real Index catalog (GET /indexes, index_router.py),
// for the Preferred Indexes picker. Only id/name are read here; the
// backend's own Index dataclass carries more (folders/tags/schedule/
// real cron status) that this picker doesn't need.
export interface IndexSummary {
  id: string;
  name: string;
}

export function fetchIndexes(): Promise<IndexSummary[]> {
  return apiFetch<IndexSummary[]>('/indexes');
}
