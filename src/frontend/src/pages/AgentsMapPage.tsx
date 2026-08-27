import { useCallback, useEffect, useState } from 'react';
import { AgentsMapCanvas } from '../features/agents-map/AgentsMapCanvas';
import { AgentDetailPanel } from '../features/agents-map/AgentDetailPanel';
import { SectionDetailPanel } from '../features/agents-map/SectionDetailPanel';
import { JobSettingsPanel } from '../features/agents-map/JobSettingsPanel';
import { AgentsMapSearchPalette } from '../features/agents-map/AgentsMapSearchPalette';
import { AgentsMapAboutPanel } from '../features/agents-map/AgentsMapAboutPanel';
import { CreateAgentWizardModal } from '../features/agents-map/CreateAgentWizardModal';
import { fetchAgentList, type AgentDetail, type JobTreeEntry } from '../features/agents-map/agentsApiClient';
import { PageLoading } from '../components/PageLoading';
import { fetchSections } from '../features/settings/settingsApiClient';
import { layoutAgents, type ClusterMarker, type DependencyEdge } from '../features/agents-map/layoutAgents';
import { spliceAllPipelineJobTrees, fetchAllPipelineJobTrees } from '../features/agents-map/pipelineJobTreeAdapter';
import type { AgentSection, MockAgent } from '../features/agents-map/mockAgents';

export function AgentsMapPage() {
  const [sections, setSections] = useState<AgentSection[]>([]);
  const [agents, setAgents] = useState<MockAgent[]>([]);
  // Every fetched agent, unreduced (REQ-SB-38-US-01) — `agents` above is
  // `layout.mapAgents`, which now deliberately excludes any agent a
  // cluster marker represents (T01). SectionDrilldown/ClusterDrilldown
  // both need the full set so a Section's own full drill-down never loses
  // an agent to clustering (Scenario 6) and a cluster's own drill-down can
  // resolve its represented agent ids to real agent data.
  const [fullAgents, setFullAgents] = useState<MockAgent[]>([]);
  const [clusters, setClusters] = useState<ClusterMarker[]>([]);
  const [dependencyEdges, setDependencyEdges] = useState<DependencyEdge[]>([]);
  // REQ-SB-66-US-01-T07 -- the SAME per-pipeline Job trees
  // spliceAllPipelineJobTrees already consumes below, flattened and also
  // stored here (no new fetch) so a later click can be resolved against
  // real Job ids without asking the backend a second time (ADR-044
  // Decision 3). Generalized 2026-08-22 from one hardcoded pipeline to
  // every real Pipeline (ADR-004) -- flat, since a Job is looked up by id
  // alone regardless of which Pipeline it came from.
  const [jobs, setJobs] = useState<JobTreeEntry[]>([]);
  // Job id -> its own real parent Pipeline id -- a flattened `jobs` array
  // alone loses this once there's more than one Pipeline (2026-08-22);
  // JobSettingsPanel needs the REAL parent, not a hardcoded one, to ask
  // the right /agents/{id}/jobs/{jobId}/settings endpoint.
  const [jobPipelineIds, setJobPipelineIds] = useState<Map<string, string>>(new Map());
  const [loading, setLoading] = useState(true);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  // 2026-08-23 -- SectionDetailPanel's own id, independent of
  // selectedAgentId (a Section Hub and an Agent node are never the same
  // click target, so no id-collision handling is needed the way
  // selectedJob below disambiguates within selectedAgentId).
  const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);
  // REQ-SB-46-US-01-T01 — the popup wizard's own open/closed flag; the
  // conditional mount below (`{isWizardOpen && <CreateAgentWizardModal .../>}`)
  // is what makes Scenario 11's "closing discards the draft" true by
  // construction, mirroring this file's own existing
  // `{selectedAgentId && <AgentDetailPanel .../>}` pattern.
  const [isWizardOpen, setIsWizardOpen] = useState(false);

  // Extracted so a newly created agent (T05's real onCreated call) can
  // re-run the exact same fetch/layout sequence the mount effect below
  // already runs, refreshing the map with zero duplicated logic.
  const refreshAgents = useCallback(() => {
    let cancelled = false;
    Promise.all([
      fetchAgentList(),
      fetchSections(),
      // fetchAllPipelineJobTrees already degrades per-pipeline internally
      // (a failed /pipelines or individual /jobs fetch just means that
      // Pipeline's single summary node stays unspliced) -- never left to
      // this Promise.all's own rejection, never the full blank-map
      // fallback below (REQ-SB-65-US-01-T02's own degrade constraint).
      fetchAllPipelineJobTrees(),
    ])
      .then(([agentList, sectionList, pipelineJobTrees]) => {
        if (cancelled) return;
        const adaptedAgentList = spliceAllPipelineJobTrees(agentList, pipelineJobTrees);
        const layout = layoutAgents(adaptedAgentList, sectionList);
        setSections(layout.sections);
        setAgents(layout.mapAgents);
        setClusters(layout.clusters);
        setDependencyEdges(layout.dependencyEdges);
        setJobs(Array.from(pipelineJobTrees.values()).flat());
        const pipelineIdByJobId = new Map<string, string>();
        for (const [pipelineId, jobList] of pipelineJobTrees) {
          for (const job of jobList) pipelineIdByJobId.set(job.id, pipelineId);
        }
        setJobPipelineIds(pipelineIdByJobId);
        // Was a manually-built placeholder array (angleDeg:0, radius:0 —
        // "recomputed by layoutSectionDrilldown() inside every drill-down
        // consumer, never rendered"). That comment stopped being true once
        // layoutSectionDrilldown() started STRETCHING the overview's own
        // already-computed angleDeg/radius instead of discarding them
        // (operator, 2026-08-15: "Same Branch View... more space so
        // spread them") — fed all-zero placeholders, every agent's
        // radiusFraction came out identically negative, collapsing the
        // whole Section View's Agents onto one point below the visible
        // canvas ("The View is empty"). `layout.mapAgents` already has
        // real, tree-shaped geometry AND already contains every eligible
        // agent (clustering — the ONLY reason this used to need a
        // separately-built "full", cluster-marker-unreduced set — is
        // itself dead code right now, `layout.clusters` always `[]`), so
        // reusing it here directly is both simpler and correct.
        setFullAgents(layout.mapAgents);
      })
      .catch(() => {
        if (!cancelled) {
          setSections([]);
          setAgents([]);
          setFullAgents([]);
          setClusters([]);
          setDependencyEdges([]);
          setJobs([]);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => refreshAgents(), [refreshAgents]);

  function handleAgentCreated(_agent: AgentDetail) {
    setIsWizardOpen(false);
    refreshAgents();
  }

  const hasAgents = agents.length > 0;

  // ADR-044 Decision 3 -- resolves a clicked id against the already-fetched
  // Job list (no new fetch); `null` means selectedAgentId is a real Agent
  // id (or nothing is selected), so AgentDetailPanel mounts exactly as
  // before. AgentsMapCanvas.tsx's own click-handling stays uniform -- this
  // branch lives entirely here, one layer up.
  const selectedJob = selectedAgentId ? jobs.find((job) => job.id === selectedAgentId) ?? null : null;

  return (
    // Flex column filling `.main`'s own real height (operator, 2026-08-15:
    // "Not fixed I need to Scoll a full Page to See the Map" — a PRIOR fix
    // attempt guessed a fixed `calc(100vh - Npx)` offset to approximate
    // the topbar's own footprint, which only ever worked by coincidence at
    // the exact viewport size it was measured against; CSS Grid items
    // (`.main` itself, via `.app-shell`'s own `display: grid`) have a
    // definite size for percentage resolution, so `min-height: 100%` here
    // tracks `.main`'s REAL height directly — whatever it actually is —
    // instead of guessing it. `.agents-map-stage` (agents-map.css) is
    // `flex: 1` so it fills exactly whatever's left after the topbar,
    // with no magic numbers on either side.
    <div className="agents-map-page">
      {/* Top bar (operator, 2026-08-15: "Bring the Page Header top Bar
          and Fit it into our current design") — ported from html-
          prototype/agents-map-skilltree-exploration.html's own
          `.skillmap-topbar` (left: search + doctrine triggers, center:
          wordmark, right: live counts). Adapted, not copied verbatim:
          the app already has its own "Second Brain" wordmark in the
          persistent Sidebar, so the center slot shows this page's own
          title instead of a redundant second wordmark; the prototype's
          fullscreen-toggle button has no real feature behind it here,
          so it's dropped rather than ported as a dead control. */}
      <div className="agents-map-topbar">
        <div className="agents-map-topbar-left">
          <AgentsMapSearchPalette agents={fullAgents} sections={sections} onSelectAgent={setSelectedAgentId} />
          <AgentsMapAboutPanel sectionCount={sections.length} agentCount={fullAgents.length} />
        </div>
        <span className="agents-map-topbar-title">Agents Map</span>
        <span className="agents-map-topbar-right">
          {sections.length} section{sections.length === 1 ? '' : 's'} &middot; {fullAgents.length} agent{fullAgents.length === 1 ? '' : 's'} mapped
        </span>
      </div>
      {loading ? (
        <div className="agents-map-stage">
          <PageLoading title="Loading your Agents Map…" />
        </div>
      ) : (
        <AgentsMapCanvas
          sections={sections}
          agents={agents}
          fullAgents={fullAgents}
          clusters={clusters}
          dependencyEdges={dependencyEdges}
          selectedAgentId={selectedAgentId}
          onSelectAgent={setSelectedAgentId}
          onSelectSection={setSelectedSectionId}
        />
      )}
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
      {selectedAgentId && selectedJob && (
        <JobSettingsPanel
          agentId={jobPipelineIds.get(selectedJob.id) ?? selectedJob.id}
          jobId={selectedJob.id}
          onClose={() => setSelectedAgentId(null)}
        />
      )}
      {selectedAgentId && !selectedJob && (
        <AgentDetailPanel
          agentId={selectedAgentId}
          onClose={() => setSelectedAgentId(null)}
          onAgentUpdated={refreshAgents}
        />
      )}
      {selectedSectionId && (
        <SectionDetailPanel
          sectionId={selectedSectionId}
          onClose={() => setSelectedSectionId(null)}
          onSectionUpdated={refreshAgents}
        />
      )}
      <button
        type="button"
        className="map-fab"
        data-testid="map-fab-create-agent"
        onClick={() => setIsWizardOpen(true)}
        aria-label="Create agent"
      >
        +
      </button>
      {isWizardOpen && (
        <CreateAgentWizardModal
          onClose={() => setIsWizardOpen(false)}
          onCreated={handleAgentCreated}
        />
      )}
    </div>
  );
}
