import { apiFetch } from '../../api/client';

// 2026-08-29 -- the real, agent-independent Hermes toolset catalog
// (GET /tools, tools_router.py). Names only; which of these are
// currently enabled for a given agent is AgentDetail.tools, not this.
export function fetchToolCatalog(): Promise<string[]> {
  return apiFetch<string[]>('/tools');
}
