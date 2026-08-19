import { apiFetch } from '../../api/client';

export interface VaultGraphNode {
  stem: string;
  title: string;
  kind: string;
  tags: string[];
}

export interface VaultGraphEdge {
  source: string;
  target: string;
}

export interface VaultGraphResponse {
  nodes: VaultGraphNode[];
  edges: VaultGraphEdge[];
}

export function fetchVaultGraph(): Promise<VaultGraphResponse> {
  return apiFetch<VaultGraphResponse>('/vault-search/graph');
}
