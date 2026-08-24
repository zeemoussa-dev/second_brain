import { apiFetch } from '../../api/client';
import type { AgentSummary, JobTreeEntry } from './agentsApiClient';
import { fetchAgentJobs } from './agentsApiClient';

// Real Pipeline refs (GET /pipelines, app/business/hermes/agents_map_
// adapter.py::list_pipeline_refs) -- 2026-08-22, generalized from the
// original single hardcoded EMAIL_CAPTURE_PIPELINE_AGENT_ID (kept below
// for back-compat with any other import site) once a second/third real
// Pipeline (meeting-builder, company-discovery) existed to design this
// against.
export interface PipelineRef {
  id: string;
  name: string;
}

export function fetchPipelineRefs(): Promise<PipelineRef[]> {
  return apiFetch<PipelineRef[]>('/pipelines');
}

// Still real -- 'threads-builder', the first Pipeline this adapter ever
// spliced (originally 'email-capture-pipeline', the old, now-retired
// Second-Brain-native agent it replaced). Not used by fetchAllPipelineJobTrees
// below; kept only for any lingering direct import.
export const EMAIL_CAPTURE_PIPELINE_AGENT_ID = 'threads-builder';

/** Fetches every real Pipeline's own Job tree in one pass -- a failed
 * /pipelines fetch or a failed individual /jobs fetch both degrade to "no
 * splice for that pipeline" (its single summary node stays as-is) rather
 * than blocking the whole map. */
export async function fetchAllPipelineJobTrees(): Promise<Map<string, JobTreeEntry[]>> {
  const trees = new Map<string, JobTreeEntry[]>();
  let refs: PipelineRef[];
  try {
    refs = await fetchPipelineRefs();
  } catch {
    return trees;
  }
  await Promise.all(
    refs.map(async (ref) => {
      try {
        const jobs = await fetchAgentJobs(ref.id);
        if (jobs.length > 0) trees.set(ref.id, jobs);
      } catch {
        // This one Pipeline's summary node stays unspliced -- not fatal.
      }
    }),
  );
  return trees;
}

/** Pure merge: replaces EVERY Pipeline's own single AgentSummary in
 * `agents` with one AgentSummary per real fetched Job for that Pipeline,
 * feeding layoutAgents.ts the real fork/merge/branch tree instead of one
 * opaque node per Pipeline -- with ZERO changes to layoutAgents.ts itself
 * (REQ-SB-65-US-01-T02's original single-Pipeline design, generalized
 * 2026-08-22 to N Pipelines via `pipelineJobTrees`, a pipelineId -> Job[]
 * map from fetchAllPipelineJobTrees above). Every Job entry inherits
 * `type`/`working_mode`/`icon`/`color`/`description` verbatim from its
 * own parent Pipeline agent -- Jobs stay non-addressable, no new visual
 * affordance is introduced (ADR-043 point 6, ADR-041). `is_background_
 * agent` is hardcoded `false` on every spliced Job entry, NOT inherited
 * (ESC-038) -- the original verbatim inheritance made every Job invisible
 * on the ring whenever its own parent Pipeline agent was itself a
 * Background Agent. A Pipeline with no entry in `pipelineJobTrees` (its
 * own /jobs fetch failed or returned []) is left as its single summary
 * node, unchanged -- the Map degrades per-pipeline, never a blank Section
 * or a thrown error. */
export function spliceAllPipelineJobTrees(
  agents: AgentSummary[],
  pipelineJobTrees: Map<string, JobTreeEntry[]>,
): AgentSummary[] {
  if (pipelineJobTrees.size === 0) return agents;

  const result: AgentSummary[] = [];
  for (const agent of agents) {
    const jobs = pipelineJobTrees.get(agent.id);
    if (!jobs || jobs.length === 0) {
      result.push(agent);
      continue;
    }
    for (const job of jobs) {
      result.push({
        id: job.id,
        name: job.name,
        // Per-Step type when the backend provides one (2026-08-22 --
        // operator: the real Outlook-fetching entry-point Step of a
        // pipeline is a 'producer', not a 'worker' like the rest) --
        // falls back to the parent Pipeline's own type for an older Job
        // source with no `type` field yet.
        type: job.type ?? agent.type,
        section_id: job.section_id ?? agent.section_id,
        is_background_agent: false,
        icon: agent.icon,
        color: agent.color,
        description: agent.description,
        working_mode: agent.working_mode,
        depends_on: job.depends_on,
        branch_target_agent_id: null,
      });
    }
  }
  return result;
}
