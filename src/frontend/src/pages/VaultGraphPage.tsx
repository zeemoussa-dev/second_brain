import { useEffect, useMemo, useState } from 'react';
import { fetchVaultGraph, type VaultGraphResponse } from '../features/vault-graph/client';
import { VaultGraphCanvas } from '../features/vault-graph/VaultGraphCanvas';

export function VaultGraphPage() {
  const [graph, setGraph] = useState<VaultGraphResponse | null>(null);
  // Empty set = every kind checked (visible) — this is the default, "the
  // whole real graph" state (Scenario 4's own "the full real graph is
  // shown again" baseline).
  const [hiddenKinds, setHiddenKinds] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchVaultGraph().then(setGraph);
  }, []);

  // Search narrows the CANDIDATE set every kind-count and the canvas
  // itself are computed from — an unchecked kind's own live count then
  // always equals "how many of this kind currently match the search AND
  // are hidden," never a stale full-corpus number once a search term is
  // typed (T03's own "recomputed from the one fetched snapshot" Constraint).
  const searchMatchedNodes = useMemo(() => {
    if (!graph) return [];
    const term = searchTerm.trim().toLowerCase();
    if (!term) return graph.nodes;
    return graph.nodes.filter(
      (node) => node.title.toLowerCase().includes(term) || node.stem.toLowerCase().includes(term),
    );
  }, [graph, searchTerm]);

  const kindCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const node of searchMatchedNodes) {
      counts.set(node.kind, (counts.get(node.kind) ?? 0) + 1);
    }
    return counts;
  }, [searchMatchedNodes]);

  const sortedKinds = useMemo(() => Array.from(kindCounts.keys()).sort(), [kindCounts]);

  const visibleNodes = useMemo(
    () => searchMatchedNodes.filter((node) => !hiddenKinds.has(node.kind)),
    [searchMatchedNodes, hiddenKinds],
  );

  const visibleEdges = useMemo(() => {
    if (!graph) return [];
    const visibleStems = new Set(visibleNodes.map((node) => node.stem));
    return graph.edges.filter((edge) => visibleStems.has(edge.source) && visibleStems.has(edge.target));
  }, [graph, visibleNodes]);

  function toggleKind(kind: string) {
    setHiddenKinds((current) => {
      const next = new Set(current);
      if (next.has(kind)) next.delete(kind);
      else next.add(kind);
      return next;
    });
  }

  if (!graph) {
    return (
      <div className="vault-graph-page">
        <h1>The Vault</h1>
        <p className="text-muted">Loading...</p>
      </div>
    );
  }

  return (
    <div className="vault-graph-page">
      <div className="vault-graph-topbar">
        <div className="vault-graph-topbar-left">
          <h1 className="vault-graph-title">The Vault</h1>
          <span className="text-muted vault-graph-count">
            {visibleNodes.length} of {graph.nodes.length} notes
          </span>
        </div>
        <input
          className="input vault-graph-search"
          type="text"
          placeholder="Search by title or stem..."
          value={searchTerm}
          onChange={(event) => setSearchTerm(event.target.value)}
        />
      </div>
      <div className="vault-graph-filters">
        {sortedKinds.map((kind) => {
          const isHidden = hiddenKinds.has(kind);
          return (
            <button
              key={kind}
              type="button"
              className={`vault-graph-kind-chip${isHidden ? ' is-hidden' : ''}`}
              onClick={() => toggleKind(kind)}
              aria-pressed={!isHidden}
            >
              {kind} ({kindCounts.get(kind) ?? 0})
            </button>
          );
        })}
      </div>
      <div className="vault-graph-stage">
        <VaultGraphCanvas nodes={visibleNodes} edges={visibleEdges} />
      </div>
    </div>
  );
}
