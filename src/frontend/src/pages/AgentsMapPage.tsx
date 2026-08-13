import { useEffect, useState } from 'react';
import { AgentsMapCanvas } from '../features/agents-map/AgentsMapCanvas';
import { AgentDetailPanel } from '../features/agents-map/AgentDetailPanel';
import { fetchAgentList } from '../features/agents-map/agentsApiClient';
import { fetchSections } from '../features/settings/settingsApiClient';
import { layoutAgents } from '../features/agents-map/layoutAgents';
import type { AgentSection, MockAgent } from '../features/agents-map/mockAgents';

export function AgentsMapPage() {
  const [sections, setSections] = useState<AgentSection[]>([]);
  const [agents, setAgents] = useState<MockAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchAgentList(), fetchSections()])
      .then(([agentList, sectionList]) => {
        if (cancelled) return;
        const layout = layoutAgents(agentList, sectionList);
        setSections(layout.sections);
        setAgents(layout.mapAgents);
      })
      .catch(() => {
        if (!cancelled) {
          setSections([]);
          setAgents([]);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const hasAgents = agents.length > 0;

  return (
    <>
      <h1>Agents Map</h1>
      <AgentsMapCanvas sections={sections} agents={agents} onSelectAgent={setSelectedAgentId} />
      {!loading && !hasAgents && (
        <div className="empty-state">
          <div className="empty-state-icon">◎</div>
          <p><strong>No agents connected yet.</strong></p>
          <p className="text-muted">
            Sections and Hubs appear here once Second Brain is wired to
            Hermes-connected background jobs (capture, enrichment, or
            Q&amp;A). Nothing to click on yet.
          </p>
        </div>
      )}
      {selectedAgentId && (
        <AgentDetailPanel agentId={selectedAgentId} onClose={() => setSelectedAgentId(null)} />
      )}
    </>
  );
}
