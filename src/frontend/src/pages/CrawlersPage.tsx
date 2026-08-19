import { useCallback, useEffect, useState } from 'react';
import { AgentDetailPanel } from '../features/agents-map/AgentDetailPanel';
import { fetchAgentList, type AgentSummary } from '../features/agents-map/agentsApiClient';
import { fetchSections, type SectionSummary } from '../features/settings/settingsApiClient';

// Own page, own route (operator, 2026-08-15: "I want to Remove the
// Background Agents to the SidePanel (New Page and call then
// Crawlers)") — previously a rail at the bottom of the Agents Map
// (AgentsMapCanvas.tsx's own now-removed "Background Agents" card).
// Independent fetch/filter, not derived from AgentsMapPage's own
// layoutAgents() call — a Crawler is never placed on the Map's ring
// layout at all, so there's no ring-geometry reason to route through
// that shared computation here.
export function CrawlersPage() {
  const [crawlers, setCrawlers] = useState<AgentSummary[]>([]);
  const [sections, setSections] = useState<SectionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

  const refresh = useCallback(() => {
    let cancelled = false;
    Promise.all([fetchAgentList(), fetchSections()])
      .then(([agentList, sectionList]) => {
        if (cancelled) return;
        setCrawlers(agentList.filter((agent) => agent.is_background_agent));
        setSections(sectionList);
      })
      .catch(() => {
        if (!cancelled) {
          setCrawlers([]);
          setSections([]);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => refresh(), [refresh]);

  function sectionName(sectionId: string): string {
    return sections.find((section) => section.id === sectionId)?.name ?? sectionId;
  }

  return (
    <>
      <h1>Crawlers</h1>
      <p className="text-muted">
        Background agents that run on their own schedule, not addressed
        directly — moved out of the Agents Map so the map stays focused on
        agents you can click into.
      </p>
      <div className="card">
        {!loading && crawlers.length === 0 ? (
          <div className="empty-state">
            <p className="text-muted">No Crawlers — every agent is currently addressable.</p>
          </div>
        ) : (
          <div className="item-list">
            {crawlers.map((agent) => (
              <div
                className="item-row"
                key={agent.id}
                onClick={() => setSelectedAgentId(agent.id)}
                style={{ cursor: 'pointer' }}
              >
                <div className="item-row-main">
                  <span className="item-row-title">{agent.name}</span>
                  <span className="item-row-meta">{sectionName(agent.section_id)} &middot; {agent.type}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      {selectedAgentId && (
        <AgentDetailPanel agentId={selectedAgentId} onClose={() => setSelectedAgentId(null)} />
      )}
    </>
  );
}
