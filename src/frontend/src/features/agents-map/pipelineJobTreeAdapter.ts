import type { AgentSummary, JobTreeEntry } from './agentsApiClient';

// The one, literally-known pipeline id this adapter ever splices Jobs for
// (REQ-SB-65-US-01, Scenario 5's own single-Pipeline scope bound) --
// mirrored by AgentsMapPage.tsx's own `fetchAgentJobs(...)` call site.
export const EMAIL_CAPTURE_PIPELINE_AGENT_ID = 'email-capture-pipeline';

/** Pure merge: replaces the single `email-capture-pipeline` AgentSummary in
 * `agents` with one AgentSummary per real fetched Job in `jobs`, feeding
 * layoutAgents.ts the real fork/merge/branch tree instead of one opaque
 * node -- with ZERO changes to layoutAgents.ts itself (REQ-SB-65-US-01-T02).
 * Every Job entry inherits `type`/`working_mode`/`icon`/`color`/
 * `description` verbatim from the original pipeline agent -- Jobs stay
 * non-addressable, no new visual affordance is introduced (ADR-043 point 6,
 * ADR-041). `is_background_agent` is hardcoded `false` on every spliced Job
 * entry, NOT inherited -- ESC-038 (Resolved): the original verbatim
 * inheritance made every Job invisible on the Agents Map ring, since the
 * real `email-capture-pipeline` agent is itself a Background Agent already
 * excluded from the ring by layoutAgents.ts's own filter. The parent
 * pipeline's own real `is_background_agent` flag is untouched -- this only
 * affects the synthetic Job entries this adapter produces. If `jobs` is
 * empty (a failed or not-yet-populated `/jobs` fetch) or no
 * `email-capture-pipeline` entry exists in `agents`, `agents` is returned
 * completely unchanged -- the Map degrades to today's existing single-node
 * rendering, never a blank Section or a thrown error. */
export function spliceEmailCapturePipelineJobTree(
  agents: AgentSummary[],
  jobs: JobTreeEntry[],
): AgentSummary[] {
  if (jobs.length === 0) return agents;

  const pipelineAgent = agents.find((agent) => agent.id === EMAIL_CAPTURE_PIPELINE_AGENT_ID);
  if (!pipelineAgent) return agents;

  const jobAgents: AgentSummary[] = jobs.map((job) => ({
    id: job.id,
    name: job.name,
    type: pipelineAgent.type,
    section_id: job.section_id ?? pipelineAgent.section_id,
    is_background_agent: false,
    icon: pipelineAgent.icon,
    color: pipelineAgent.color,
    description: pipelineAgent.description,
    working_mode: pipelineAgent.working_mode,
    depends_on: job.depends_on,
    branch_target_agent_id: null,
  }));

  return [
    ...agents.filter((agent) => agent.id !== EMAIL_CAPTURE_PIPELINE_AGENT_ID),
    ...jobAgents,
  ];
}
