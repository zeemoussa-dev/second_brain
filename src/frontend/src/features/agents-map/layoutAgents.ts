import type { AgentSection, AgentType, MockAgent } from './mockAgents';
import { isBackgroundAgent, type AgentSummary } from './agentsApiClient';
import { DRILLDOWN_HUB_ANGLE_DEG, HUB_RADIUS, SECTION_TITLE_RADIUS } from './polarLayout';

export interface SectionSummary {
  id: string;
  name: string;
  agent_ids: string[];
  color: string | null;
  icon: string | null;
  // Operator, 2026-08-15: "I need to have a Section Subtitle and
  // Description The Subtitle will be Displayed in the Agent Map The
  // Description will be used later." `subtitle` flows into
  // AgentSection.subtitle below and renders under the Section title
  // (AgentsMapCanvas.tsx). `description` is typed here so it's
  // available end-to-end, but deliberately NOT threaded into
  // AgentSection/rendered anywhere yet, per the operator's own "will be
  // used later" framing — a future Section detail/about surface reads
  // it from this same SectionSummary fetch.
  subtitle: string | null;
  description: string | null;
}

// Agents within a section fan out either side of that section's own hub
// angle, evenly spaced across this arc — same visual convention the
// original hand-placed mock data used (ADR-010), just computed instead of
// hardcoded. Capped well below a section's own wedge width (360/n) so an
// agent can never fan out past a neighboring section's boundary (BUG-009:
// a fixed 80deg span overflowed the 72deg wedge produced by 5 sections).
const SECTION_ARC_SPAN_DEG_CAP = 80;
const SECTION_ARC_SPAN_FRACTION = 0.8;

// Purely cosmetic starting rotation for the first (sorted) hub — no
// functional consequence, matches the prior layout's own top-left-ish
// starting orientation (ADR-014 point 6).
const HUB_ANGLE_OFFSET_DEG = -90;

// Radial band an agent's depth maps into — inset from HUB_RADIUS/
// SECTION_TITLE_RADIUS themselves so depth-0 agents clear the Hub's own
// visual radius and the deepest agents in a pipeline stay clear of the
// title text (operator, 2026-08-15: "the Tree lets Start by Spreading the
// Agents between the title and the Hub").
// Exported so layoutSectionDrilldown (below) can remap FROM this exact
// band when stretching the overview's own tree shape into the drill-down's
// own bigger one.
export const AGENT_RADIUS_MIN = HUB_RADIUS + 8;
export const AGENT_RADIUS_MAX = SECTION_TITLE_RADIUS - 10;

// Depth-to-radius mapping is otherwise exact, so every agent AT THE SAME
// DEPTH lands on the literal same radius — a whole Section's worth of
// depth-1 (or depth-2, etc.) agents forming a visible perfect concentric
// ring around the KB (operator, 2026-08-15: "the Agents Appear like they
// are in Circles equal Distance around the KB Which doen't fit my Tree
// Concept they need to have a + - Number to be more Tree Looking"). A
// small, deterministic (hash of the agent's own id — stable across
// re-renders/re-fetches, not `Math.random()`) +/- offset breaks that up
// without disturbing the actual depth ordering: capped at a FRACTION of
// the gap between two adjacent depth rings (`radiusStep` below) so a
// jittered agent can never visually drift into a neighboring depth's own
// band and read as the wrong pipeline stage.
const RADIUS_JITTER_FRACTION = 0.35;
const RADIUS_JITTER_MAX = 3;

/** Deterministic pseudo-random value in [-1, 1] from `id` — same id
 * always jitters the same direction/amount, so the Map doesn't visibly
 * shuffle itself on every re-fetch. */
function hashToUnitOffset(id: string): number {
  let hash = 0;
  for (let i = 0; i < id.length; i += 1) {
    hash = (hash * 31 + id.charCodeAt(i)) | 0;
  }
  return ((Math.abs(hash) % 2000) / 1000) - 1;
}

/** Longest-path depth of `agentId` via its own `depends_on` edges (0 = a
 * pipeline's own entry point, or a standalone agent with no pipeline at
 * all) — mirrors LangGraph's own topological notion of "how many hops
 * from the start of the graph", per the operator's earlier "Check
 * Langraph Data" framing. Memoized in `cache` since a fork/merge pipeline
 * (e.g. the 6-stage Consult-Expert/Store shape in sample_data.py)
 * revisits the same predecessor from multiple branches. `visiting` guards
 * against a cycle in malformed data turning this into infinite recursion
 * — sample data has none, but agent data ultimately comes over the wire. */
function computeAgentDepth(
  agentId: string,
  agentsById: Map<string, AgentSummary>,
  cache: Map<string, number>,
  visiting: Set<string> = new Set(),
): number {
  const cached = cache.get(agentId);
  if (cached !== undefined) return cached;
  if (visiting.has(agentId)) return 0;
  const agent = agentsById.get(agentId);
  if (!agent || agent.depends_on.length === 0) {
    cache.set(agentId, 0);
    return 0;
  }
  visiting.add(agentId);
  const depth = 1 + Math.max(
    ...agent.depends_on.map((depId) => computeAgentDepth(depId, agentsById, cache, visiting)),
  );
  visiting.delete(agentId);
  cache.set(agentId, depth);
  return depth;
}

// Fixed zigzag swing for a straight (single-child) run of stages —
// deliberately NOT scaled by how many stages are in the run (operator,
// 2026-08-15: "if we have a 10 Stages Pipeline they can fit between the
// same spaces") — a 4-stage and a 10-stage linear chain both oscillate
// within this same bounded band, they just alternate sides more times.
const ZIGZAG_AMPLITUDE_DEG = 6;

/** Leaf count (every terminal node — nothing else depends on it — under
 * `id`'s own subtree via `childrenOf`), the unit `assignTreeAngles`
 * partitions angular TERRITORY by. `visiting` guards a cycle in
 * malformed data the same way computeAgentDepth's own does. */
function computeLeafCount(
  id: string,
  childrenOf: Map<string, string[]>,
  cache: Map<string, number>,
  visiting: Set<string> = new Set(),
): number {
  const cached = cache.get(id);
  if (cached !== undefined) return cached;
  if (visiting.has(id)) return 1;
  visiting.add(id);
  const children = childrenOf.get(id) ?? [];
  const count = children.length === 0
    ? 1
    : children.reduce((sum, childId) => sum + computeLeafCount(childId, childrenOf, cache, visiting), 0);
  visiting.delete(id);
  cache.set(id, count);
  return count;
}

/** Zigzag angle assignment for one Section's own agents — replaces the
 * old evenly-spaced index fan (operator, 2026-08-15: "the Spread of
 * Agents is Programatic I need some Math Envolved... to make it look
 * like a tree branches" + "Agents that communicate with each others
 * should be near by"), then a leaf-count dendrogram that averaged every
 * chain node onto its one child's own angle, collapsing a straight
 * pipeline onto one thin radial spoke ("I see Lots of Experts in the
 * pipeline and Less Jobs That Makes the visual Look Weird" — confirmed
 * with the operator this belonged in this layout math, not sample
 * data), then briefly a weighted-subtree-size partition that spread a
 * chain out but grew its OWN territory linearly with stage count. This
 * version: a branch/fan point (>1 child, e.g. Fetch fanning into two
 * Classify stages) still subdivides its own [lo, hi] territory among its
 * children proportional to each child's own LEAF count (so an entire
 * multi-stage branch and a single standalone leaf don't get equal
 * territory when they visibly ARE unequal complexity) — but a straight
 * (single-child) run no longer shrinks or advances that territory at
 * all: every stage in the run keeps the SAME [lo, hi] handed down from
 * its nearest branch ancestor (or its own root slot, sized by the whole
 * chain's own total leaf count — 1, same as a lone Expert, since a
 * straight chain has exactly one terminal stage) and just alternates
 * ZIGZAG_AMPLITUDE_DEG to either side of that fixed range's center as
 * depth increases (operator: "Make it a bit of ZigZag It will be move
 * visually Appealing"). Since the swing amplitude is a flat constant,
 * not a fraction of chain length, any run — 4 stages or 10 — fans out
 * inside the exact same fixed territory ("fit between the same
 * spaces"), radius (computeAgentDepth's own depth-to-radius mapping)
 * doing the rest of the work of keeping every stage visually distinct.
 * A node with more than one `depends_on` entry (a Merge stage) only
 * contributes its own arc width under its FIRST resolvable parent — the
 * "primary" edge — so a converging Merge doesn't double-book territory
 * under two different parents; every real parent still gets its own
 * dependency line drawn (buildDependencyEdges below), this only decides
 * ANGLE ownership. */
function assignTreeAngles(
  sectionAgents: AgentSummary[],
  sectionStartAngle: number,
  sectionArcSpanDeg: number,
): Map<string, number> {
  const idsInSection = new Set(sectionAgents.map((agent) => agent.id));
  const primaryParentOf = new Map<string, string>();
  for (const agent of sectionAgents) {
    const parent = agent.depends_on.find((id) => id !== agent.id && idsInSection.has(id));
    if (parent) primaryParentOf.set(agent.id, parent);
  }

  const childrenOf = new Map<string, string[]>();
  for (const [child, parent] of primaryParentOf) {
    const list = childrenOf.get(parent) ?? [];
    list.push(child);
    childrenOf.set(parent, list);
  }

  const roots = sectionAgents.filter((agent) => !primaryParentOf.has(agent.id));
  if (roots.length === 0) return new Map();

  const leafCountCache = new Map<string, number>();
  const leafCountOf = (id: string) => computeLeafCount(id, childrenOf, leafCountCache);

  const angles = new Map<string, number>();
  // `zigzagIndex` counts how many stages deep into the CURRENT straight
  // run this node is (0 = the run's own first stage, dead center) —
  // reset to 0 every time a branch point hands territory to a fresh
  // child, since that child starts its own new run.
  function place(id: string, lo: number, hi: number, zigzagIndex: number) {
    const center = (lo + hi) / 2;
    const amplitude = Math.min(ZIGZAG_AMPLITUDE_DEG, ((hi - lo) / 2) * 0.8);
    const offset = zigzagIndex === 0 ? 0 : amplitude * (zigzagIndex % 2 === 1 ? -1 : 1);
    const nodeAngle = center + offset;
    angles.set(id, nodeAngle);

    const children = childrenOf.get(id) ?? [];
    if (children.length === 1) {
      // A straight run keeps the SAME [lo, hi] band across every stage
      // (this run's own fixed territory) — deliberately NOT re-centered
      // on this node's own zigzag offset, so the run zigzags within one
      // stable band rather than drifting.
      place(children[0], lo, hi, zigzagIndex + 1);
    } else if (children.length > 1) {
      // A branch point's own children must fan out around where this
      // node was ACTUALLY drawn (nodeAngle), not around the un-offset
      // [lo, hi] midpoint — otherwise a branch reached via an odd
      // zigzagIndex (this node itself pulled off-center) hands its
      // children a territory centered on a point the node was never
      // drawn at, visually tearing the fork away from its own parent.
      // Re-center a same-width window on nodeAngle before partitioning.
      const halfWidth = (hi - lo) / 2;
      const branchLo = nodeAngle - halfWidth;
      const branchHi = nodeAngle + halfWidth;
      const totalChildLeaves = children.reduce((sum, childId) => sum + leafCountOf(childId), 0) || 1;
      let cursor = branchLo;
      let remainingLeaves = totalChildLeaves;
      for (const childId of children) {
        const childLeaves = leafCountOf(childId);
        const childWidth = remainingLeaves > 0 ? ((branchHi - cursor) * childLeaves) / remainingLeaves : 0;
        place(childId, cursor, cursor + childWidth, 0);
        cursor += childWidth;
        remainingLeaves -= childLeaves;
      }
    }
  }

  const totalRootLeaves = roots.reduce((sum, root) => sum + leafCountOf(root.id), 0) || 1;
  let rootCursor = sectionStartAngle;
  for (const root of roots) {
    const width = (sectionArcSpanDeg * leafCountOf(root.id)) / totalRootLeaves;
    place(root.id, rootCursor, rootCursor + width, 0);
    rootCursor += width;
  }

  return angles;
}

/** One real pipeline connection: `fromAgentId` (a `depends_on`
 * predecessor) -> `toAgentId` (the dependent successor that receives from
 * it). Replaces the old "every agent in a Section connects to every other
 * agent" mesh (operator, 2026-08-15: "there is too many Dependencies
 * which will not be true") — that mesh drew a line between every PAIR of
 * agents sharing a Section regardless of any real relationship, which is
 * what made the view unreadable once a Section held more than a handful
 * of agents. */
export interface DependencyEdge {
  id: string;
  sectionId: string;
  fromAgentId: string;
  toAgentId: string;
}

// Real data-model constraint, not an arbitrary safety margin (operator,
// 2026-08-15: "Jobs will have only 2 Dependencies in and out This is
// clean the visual alot") — a Job's own `depends_on` never exceeds 2
// entries (at most a 2-way Merge) and never fans out to more than 2
// dependents (at most a 2-way Classify/branch split). Enforced
// direction-aware, not as one combined total, so a busy fan-out stage
// with 2 children and a busy merge with 2 parents can each still reach
// their own real cap independently.
//
// MAX_OUTGOING raised to 3 (2026-08-24, found live: "Solutions Expert in
// Compass not linked to Compass Expert in Agentic Map") — `compass-expert`
// is the first individual AGENT (not a pipeline Job) to have more than 2
// real dependents, relaying to 3 sub-specialists by explicit design
// (`compass-pricing-expert`/`compass-solutions`/`compass-models-expert`,
// see MEMORY.md's own "one real domain, one Hermes profile" entries) --
// the cap silently dropped the 3rd edge (`compass-solutions`, whichever
// happened to iterate last) with no visual indication anything was
// missing. Safe to raise: real pipeline Jobs never exceed 2 by the same
// data-model constraint this cap already documents, so this only ever
// changes rendering for a case like compass-expert's.
const MAX_INCOMING_CONNECTIONS = 2;
const MAX_OUTGOING_CONNECTIONS = 3;

function buildDependencyEdges(
  mapAgents: MockAgent[],
  agentsById: Map<string, AgentSummary>,
): DependencyEdge[] {
  const agentIdSet = new Set(mapAgents.map((agent) => agent.id));
  const sectionIdByAgentId = new Map(mapAgents.map((agent) => [agent.id, agent.sectionId]));
  const outgoingCounts = new Map<string, number>();
  const incomingCounts = new Map<string, number>();
  const edges: DependencyEdge[] = [];
  for (const agent of mapAgents) {
    const fullAgent = agentsById.get(agent.id);
    if (!fullAgent) continue;
    for (const depId of fullAgent.depends_on) {
      if (depId === agent.id || !agentIdSet.has(depId)) continue;
      const outgoing = outgoingCounts.get(depId) ?? 0;
      const incoming = incomingCounts.get(agent.id) ?? 0;
      if (outgoing >= MAX_OUTGOING_CONNECTIONS || incoming >= MAX_INCOMING_CONNECTIONS) continue;
      outgoingCounts.set(depId, outgoing + 1);
      incomingCounts.set(agent.id, incoming + 1);
      edges.push({
        id: `${depId}->${agent.id}`,
        sectionId: sectionIdByAgentId.get(agent.id) ?? '',
        fromAgentId: depId,
        toAgentId: agent.id,
      });
    }
  }
  return edges;
}

// One overflowing (sectionId, agentType) group, in the group's own last fan
// slot: `id` is a synthetic click-target identity (never a real sectionId,
// so a cluster marker's click target can never collide with a Section
// Hub's own — AgentsMapCanvas.tsx/T04's own widened click-to-zoom state
// relies on this).
export interface ClusterMarker {
  id: string;
  sectionId: string;
  type: AgentType;
  angleDeg: number;
  count: number;
  agentIds: string[];
}

export interface AgentMapLayout {
  sections: AgentSection[];
  mapAgents: MockAgent[];
  clusters: ClusterMarker[];
  backgroundAgents: AgentSummary[];
  dependencyEdges: DependencyEdge[];
}

/** Real GET /agents + GET /sections -> the {sections, mapAgents, clusters}
 * shape AgentsMapCanvas renders. Section membership comes from each agent's
 * own section_id (no longer derived from `type`); N sections' hub angles
 * are spaced evenly around the full circle, replacing the fixed 3-entry
 * SECTION_META/TYPE_TO_SECTION lookup (ADR-014 point 6). */
export function layoutAgents(agents: AgentSummary[], sectionList: SectionSummary[]): AgentMapLayout {
  const sortedSections = [...sectionList].sort((a, b) => a.id.localeCompare(b.id));
  const n = sortedSections.length;

  const sections: AgentSection[] = sortedSections.map((section, index) => ({
    id: section.id,
    label: section.name,
    hubLabel: `${section.name} Hub`,
    hubAngleDeg: n === 0 ? 0 : index * (360 / n) + HUB_ANGLE_OFFSET_DEG,
    color: section.color,
    icon: section.icon,
    subtitle: section.subtitle,
  }));

  // REQ-SB-51-US-01 -- a Background Agent never occupies a ring slot,
  // counts toward VISIBLE_SLOT_CAP crowding, or appears in a cluster
  // marker: excluded here, before agentsBySection is built, not after.
  const backgroundAgents = agents.filter((agent) => isBackgroundAgent(agent));
  const addressableAgents = agents.filter((agent) => !isBackgroundAgent(agent));

  const agentsBySection = new Map<string, AgentSummary[]>();
  for (const agent of addressableAgents) {
    const list = agentsBySection.get(agent.section_id) ?? [];
    list.push(agent);
    agentsBySection.set(agent.section_id, list);
  }

  const wedgeWidthDeg = n === 0 ? 360 : 360 / n;
  const sectionArcSpanDeg = Math.min(SECTION_ARC_SPAN_DEG_CAP, wedgeWidthDeg * SECTION_ARC_SPAN_FRACTION);

  // No more Type-grouped crowding cap / cluster-marker overflow here
  // (operator, 2026-08-15: "remove the Agents Grouping the Old Logic") —
  // every Section's own agents now fan out individually, uncapped.
  // REQ-SB-38-US-01's own crowding cap was already keyed to
  // RING_RADIUS[agent.type] making visual sense of "too many dots
  // overlapping on the SAME ring"; now that RING_RADIUS collapsed to one
  // shared radius for every Type (the operator's own preceding request,
  // "remove that [Worker/Producer/Expert position-split] logic"), a
  // per-Type cap no longer maps to anything the viewer can actually see
  // — grouping by Type here would just be an arbitrary, invisible
  // bucket. `clusters` stays in AgentMapLayout's own return shape
  // (always empty now) rather than ripping out ClusterMarker/
  // ClusterDrilldown.tsx/etc. wholesale — same "collapse the values,
  // don't tear out the structure" reversible pattern already used for
  // the RING_RADIUS change.
  // Depth lookups need every agent's dependencies resolvable, including
  // ones excluded above (backgroundAgents) or in a different section than
  // their dependent — built from the full, unfiltered `agents` param.
  const agentsById = new Map(agents.map((agent) => [agent.id, agent]));
  const depthCache = new Map<string, number>();
  // 2026-08-23 (operator: "the Agents that are solo, They are Far away
  // from the Section Hub They need to be Closer") -- a genuinely solo
  // agent (no depends_on AND nothing else depends on it -- Primary/
  // files-manager/notes-manager/opp-manager today, none of which belong
  // to any real pipeline) was falling into the SAME depth-0 branch as a
  // pipeline's own entry point (Fetch Emails, Scan Threads, etc.),
  // landing at AGENT_RADIUS_MAX -- the single farthest ring on the map,
  // identical to "raw external data source", which a standalone agent
  // conceptually isn't. Computed globally (not per-section) since
  // depends_on can reference an agent outside its own section.
  const agentsWithDependents = new Set<string>();
  for (const agent of agents) {
    for (const depId of agent.depends_on) agentsWithDependents.add(depId);
  }

  const mapAgents: MockAgent[] = [];
  const clusters: ClusterMarker[] = [];
  for (const section of sections) {
    const sectionAgents = agentsBySection.get(section.id) ?? [];
    const depths = sectionAgents.map((agent) => computeAgentDepth(agent.id, agentsById, depthCache));
    const maxDepth = depths.length > 0 ? Math.max(...depths) : 0;
    const sectionStartAngle = section.hubAngleDeg - sectionArcSpanDeg / 2;
    const treeAngles = assignTreeAngles(sectionAgents, sectionStartAngle, sectionArcSpanDeg);

    sectionAgents.forEach((agent, index) => {
      const angleDeg = treeAngles.get(agent.id) ?? section.hubAngleDeg;
      // A section with no multi-stage pipeline (maxDepth 0 — every agent
      // is its own entry point) has no depth to spread across, so those
      // agents sit at the band's own midpoint rather than all collapsing
      // onto AGENT_RADIUS_MIN.
      // 2026-08-22 (operator-directed): depth-0 (a pipeline's own entry
      // point, e.g. "Fetch Meetings" -- the real step that pulls from
      // Outlook) renders at AGENT_RADIUS_MAX, OUTERMOST; the deepest
      // dependent (the step everything else feeds into) renders closest
      // to the Hub at AGENT_RADIUS_MIN -- data flows inward from the raw
      // outside source toward the Hub, not outward from it. Inverted from
      // the original depth/maxDepth fraction (which put depth-0 innermost)
      // via `1 - ...`; every other consumer of `radius` below (jitter,
      // drill-down stretch) is unaffected, since they only care about the
      // final numeric value, not which direction depth maps to.
      const isSolo = agent.depends_on.length === 0 && !agentsWithDependents.has(agent.id);
      const baseRadius = maxDepth === 0
        ? (AGENT_RADIUS_MIN + AGENT_RADIUS_MAX) / 2
        : AGENT_RADIUS_MIN + (1 - depths[index] / maxDepth) * (AGENT_RADIUS_MAX - AGENT_RADIUS_MIN);
      const radiusStep = maxDepth > 0 ? (AGENT_RADIUS_MAX - AGENT_RADIUS_MIN) / maxDepth : (AGENT_RADIUS_MAX - AGENT_RADIUS_MIN);
      const jitterAmplitude = Math.min(RADIUS_JITTER_MAX, radiusStep * RADIUS_JITTER_FRACTION);
      const radius = isSolo
        // Random (deterministic per id, same convention as the jitter
        // above) 25%-50% of the way from the Hub out to baseRadius —
        // "between 50% and 25% of the Current Distance", current being
        // where this agent would otherwise have landed.
        ? HUB_RADIUS + (0.25 + 0.25 * ((hashToUnitOffset(agent.id) + 1) / 2)) * (baseRadius - HUB_RADIUS)
        : Math.min(
            AGENT_RADIUS_MAX,
            Math.max(AGENT_RADIUS_MIN, baseRadius + jitterAmplitude * hashToUnitOffset(agent.id)),
          );
      mapAgents.push({
        id: agent.id,
        label: agent.name,
        type: agent.type,
        sectionId: section.id,
        angleDeg,
        radius,
        icon: agent.icon,
        color: agent.color,
        description: agent.description,
        workingMode: agent.working_mode,
      });
    });
  }

  const dependencyEdges = buildDependencyEdges(mapAgents, agentsById);

  return { sections, mapAgents, clusters, backgroundAgents, dependencyEdges };
}

// Drill-down "Agents Tree" radial band — bigger than the overview's own
// AGENT_RADIUS_MIN/MAX since one Section now owns the whole canvas
// instead of sharing it with every other Section around the KB (operator,
// 2026-08-15: "we have More Space So Spread them").
// MAX kept just under 50 * sin(90 - DRILLDOWN_ANGULAR_HALF_WIDTH_DEG's own
// complement) — concretely, radius * sin(HALF_WIDTH) must stay <= 50 (the
// Hub's own horizontal room to the canvas edge) even for an agent sitting
// at BOTH max radius AND the widest angular swing simultaneously; at
// HALF_WIDTH = 85deg, sin(85deg) ~= 0.996, so MAX = 50 still leaves a
// small safety margin (50 * sin85 ~= 49.8) instead of clipping off the
// left/right edge.
const DRILLDOWN_TREE_RADIUS_MIN = 14;
const DRILLDOWN_TREE_RADIUS_MAX = 50;

// Half-width of the upward-facing fan Agents spread across, centered on
// "straight up" from the Hub (DRILLDOWN_HUB_ANGLE_DEG + 180) — was 70deg
// (a conservative first pass), widened to 85deg (operator, 2026-08-15:
// "the Map is Condinced [Condensed] the the middle Alot of empty space...
// which makes agents and jobs over lap while not needed") — a narrow
// 140deg-total cone left most of the actually-available square canvas
// empty on both sides while packing every Agent into a thin central
// wedge, causing exactly the crowding/overlap this widens room for. Not
// a full 90 (which would let an Agent land exactly level with the Hub,
// not above it, and cuts the safety margin above to ~0) — 85 keeps
// Agents visibly fanning "upward" from the Hub while using nearly the
// entire square canvas's own width.
const DRILLDOWN_ANGULAR_HALF_WIDTH_DEG = 85;

/** One Section's own agents (already laid out by layoutAgents() above,
 * for the OVERVIEW's own narrow per-Section wedge) -> that same set
 * remapped into the drill-down "Agents Tree" view's own bigger,
 * bottom-anchored coordinate system (SectionDrilldown.tsx). Reuses,
 * rather than replaces, the overview's own tree shape — "Same Branch
 * View" (operator, 2026-08-15: "I want to Have the title and the
 * Subtitle Rendered at the Bottom... with the Hub then All Agents Appear
 * on top there, Same Branch View but now we have More Space So Spread
 * then") — `angleDeg` already encodes assignTreeAngles' own
 * zigzag/depth-ordered shape and `radius` already encodes
 * computeAgentDepth's own pipeline depth; both get STRETCHED here into a
 * wider angular fan and a bigger radial band, not recomputed from
 * scratch, so the branch shape a viewer saw on the overview map is
 * recognizably the same shape, just given more room. The fan is
 * re-centered on "straight up" from the Hub's own bottom position
 * (DRILLDOWN_HUB_ANGLE_DEG + 180, shared with SectionDrilldown.tsx's own
 * Hub placement) regardless of which direction this Section's Hub
 * happened to face on the overview. */
export function layoutSectionDrilldown(sectionAgents: MockAgent[]): MockAgent[] {
  if (sectionAgents.length === 0) return [];

  const angles = sectionAgents.map((agent) => agent.angleDeg);
  const sourceCenter = (Math.min(...angles) + Math.max(...angles)) / 2;
  const sourceHalfWidth = (Math.max(...angles) - Math.min(...angles)) / 2 || 1;
  const fanCenterDeg = DRILLDOWN_HUB_ANGLE_DEG + 180;
  const radiusSpan = AGENT_RADIUS_MAX - AGENT_RADIUS_MIN || 1;

  return sectionAgents.map((agent) => {
    const widenedOffset = ((agent.angleDeg - sourceCenter) / sourceHalfWidth) * DRILLDOWN_ANGULAR_HALF_WIDTH_DEG;
    const radiusFraction = (agent.radius - AGENT_RADIUS_MIN) / radiusSpan;
    return {
      ...agent,
      angleDeg: fanCenterDeg + widenedOffset,
      radius: DRILLDOWN_TREE_RADIUS_MIN + radiusFraction * (DRILLDOWN_TREE_RADIUS_MAX - DRILLDOWN_TREE_RADIUS_MIN),
    };
  });
}
