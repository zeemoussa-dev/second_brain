---
id: REQ-SB-65-US-01
title: Pipeline Job Visualization — render the Email Capture Pipeline's real, running Jobs as a connected tree on the Agents Map, grounded in the actual compiled StateGraph
requirement_ids: [REQ-SB-65]
requirement_section: "REQ-SB-65: Pipeline Job Visualization — the Email Capture Pipeline's Real, Running Internals Rendered as a Tree on the Agents Map"
phase: P1
status: Done
gate: flagged
gate_reason: "Two distinct, named flags stay set: (1) trigger-1 (material assumption), standing breadcrumb from the architect pass, /plan-tasks step 1, 2026-08-16 — resolved the /spec-time trigger-8 open question as Option A (a new read-only endpoint inspecting the real, compiled email_capture_pipeline.py StateGraph, via langgraph's own already-installed Pregel.get_graph() introspection API — confirmed by direct reading of the installed langgraph==1.2.11 package, not assumed); the concrete endpoint route/response shape/frontend-merge design still awaits human confirmation per REVIEW-QUEUE.md, independent of delivery completion. (2) Retro-harvest flag, coder pass, 2026-08-16: SPRINT-051's drafted Retrospective (including ESC-038 as a genuine finding) awaits human propagation into Implementation/Learnings.md. Coder pass, T02 resume, 2026-08-16: ESC-038 RESOLVED — operator decision, is_background_agent hardcoded false on every spliced Job entry (not inherited); T02 rebuilt/re-verified, all 5 locked ACs (AC-01-AC-05) now pass live. Story status Blocked -> Done. See Implementation/Architecture/architecture.md → \"Pipeline Job Tree Visualization\", ESCALATIONS.md ESC-038 (Resolved), REVIEW-QUEUE.md."
sprint: "SPRINT-051"
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-65-US-01 — Pipeline Job Visualization — render the Email Capture Pipeline's real, running Jobs as a connected tree on the Agents Map, grounded in the actual compiled StateGraph

## Story

**As a** Second Brain user
**I want** the Agents Map, viewing the Data Gathering Section, to show the
Email Capture Pipeline's own real Jobs as connected tree nodes reflecting
the actual compiled graph's fork/merge/branch structure — instead of the
single opaque `email-capture-pipeline` node it renders today
**So that** I can see what the pipeline is actually doing internally,
grounded in the real, running graph, never a fabricated or hardcoded shape

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-65: Pipeline Job Visualization —
  the Email Capture Pipeline's Real, Running Internals Rendered as a Tree
  on the Agents Map*. Raised 2026-08-16, same day `SPRINT-049`
  (`REQ-SB-55`, the pipeline itself) and `SPRINT-050` (`REQ-SB-63`, the
  Librarian consult Job added into that same pipeline) both shipped —
  once the operator started visually validating the real pipeline against
  the demo taxonomy's own tree-shaped sample data and recognized
  `AgentSummary.depends_on`/`branch_target_agent_id` were always meant for
  exactly this ("In the Demo API we have a Pipeline where Agents are
  connected in a Tree. That is what Depends on was about in Agents").
- **Two already-real, already-built pieces this story connects — neither
  has ever been wired to the other, confirmed by direct inspection this
  pass, not taken on faith:**
  - `GET /demo/agents`/`GET /demo/pipelines`
    (`src/backend/app/api/demo_taxonomy_router.py`, mounted on the real
    backend at port 8001 — not a separate demo server) return
    `demo_taxonomy.py`'s in-memory sample fixture: a `Pipeline` has
    `id`/`name`/`hub_id`/`description`/`jobs`; each `Job` has
    `id`/`name`/`kind`/`prompt`/`skills`/`depends_on`, and a
    `branch-to-expert`-kind Job additionally carries
    `branch_target_agent_id`. **Confirmed live this pass: zero frontend
    consumers of either endpoint exist** (`grep` across
    `src/frontend/src` for `demo_taxonomy`/`/demo/agents`/`/demo/pipelines`
    returns no matches) — the demo taxonomy has never actually been
    rendered in-browser; only its JSON *shape* has ever been inspected.
  - `src/frontend/src/features/agents-map/layoutAgents.ts` already has
    real, working tree/dependency-edge layout math — `computeAgentDepth`
    (longest-path depth via `depends_on`), `assignTreeAngles` (a
    branch/fan-point-aware zigzag angle assignment, leaf-count-weighted),
    and `buildDependencyEdges` (draws a line per real predecessor→
    dependent pair, capped at 2 in/2 out per the operator's own "Jobs will
    have only 2 Dependencies in and out" data-model constraint) — built
    specifically to consume an `AgentSummary[]` list with real
    `depends_on` edges. **Confirmed live this pass: today it is only ever
    fed real Agents, and every real Agent's own `depends_on` is currently
    always `[]`** (`ADR-043` point 6 collapsed the whole Email Capture
    Pipeline into ONE Agent-tier identity, `email-capture-pipeline`, with
    none of its six Jobs getting their own registry entry) — so this math
    has never yet rendered a real, live multi-node tree; it has only been
    exercised against the demo taxonomy's JSON shape conceptually, never
    live pixels.
- **Verified discrepancy worth recording, found by reading the real code
  directly rather than trusting the PRD's own prose:** the PRD's own text
  names five Jobs (`Classify`, `Thread-Match/Merge`, `Route-to-Project`,
  `Summarize-Attachment`, `Detect-Recurring-Pattern`, plus `Fetch` as a
  pre-graph step). Reading `app/business/pipelines/email_capture_pipeline.py`
  directly (built the SAME day, `SPRINT-049`/`ADR-043`) shows the compiled
  `StateGraph` already has a SIXTH graph node, `consult_librarian` —
  added later the same day by `REQ-SB-63-US-01-T02`
  (`_route_after_thread_match_merge` unconditionally routes to it,
  alongside the conditional `route_to_project` branch). The PRD's own list
  simply predates that same-day addition. **This means "the actual
  compiled graph's structure" this story must render already has 6 graph
  nodes today (`classify`, `summarize_attachment`,
  `detect_recurring_pattern`, `thread_match_merge`, `route_to_project`,
  `consult_librarian`) plus the pre-graph `Fetch` batch step — not the
  5+1 the PRD's own prose enumerates.** Reinforces the requirement's own
  "never fabricated/hardcoded" bar: any implementation that bakes in a
  static list of Job names (5, 6, or otherwise) will silently go stale the
  next time this graph's own topology changes; the visualization must
  read the graph's own real, current structure at render/query time.
- **The exact topology to render (`ADR-043` point 3 + the
  `REQ-SB-63-US-01` amendment, confirmed by direct reading of
  `email_capture_pipeline.py`'s own `_build_graph`):** `classify` is the
  first fork point — unconditionally to `summarize_attachment` (a
  mandatory pass-through, structural no-op when the email has no real
  attachments), additionally/conditionally to `detect_recurring_pattern`
  when the classification flags a recurring-pattern candidate (this
  branch never feeds back in; it terminates on its own).
  `summarize_attachment` always leads to `thread_match_merge` next (fixed
  edge — the fan-in point). `thread_match_merge` is the second fork
  point — unconditionally to `consult_librarian` (fires on every Thread
  update, created or merged alike), additionally/conditionally to
  `route_to_project` only when this pass created a brand-new Thread.
  Neither `consult_librarian` nor `route_to_project` feeds back into
  anything; each terminates on its own edge to the graph's end.
- **This reopens a decision made earlier the same day — genuinely, not
  assumed away.** `ADR-043` point 6 deliberately kept all six Jobs
  invisible: one Agent-tier identity only, no per-Job registry entry, no
  per-Job Map node, no chat/history/Working Mode — reasoning that
  mechanical pipeline verbs are Job-tier, never Agent-tier, per `ADR-041`.
  This requirement does not necessarily overturn that: showing Jobs as
  tree nodes on the Map does not require giving each Job a real,
  independently-addressable Agent identity — it only requires a real DATA
  SOURCE describing the compiled pipeline's own structure. Two
  fundamentally different, equally real shapes for that data source exist
  (see `## Notes` for the full reasoning, both options, and fresh operator
  context received mid-`/spec`-pass leaning toward one of them without
  deciding it): **this is squarely the architect's decision at
  `/plan-tasks`, not something for this pass to guess.**
- **Scope-narrowing, disclosed:** this story targets the Email Capture
  Pipeline specifically, not a general "any Pipeline renders as a tree"
  platform — the demo taxonomy's 150+ generated sample pipelines exist for
  UI density testing, not as a requirement every one of them needs a real
  backend counterpart (mirroring this project's own repeated "prove one
  real thing before generalizing" precedent, `ADR-041`'s own
  Builder-after-one-real-Pipeline sequencing, restated in this PRD
  requirement's own text).

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: The Agents Map's Data Gathering Section shows the Email Capture Pipeline's real Jobs as connected tree nodes, not one opaque node

```gherkin
Given the Agents Map is viewing the Data Gathering Section (the Section
    `email-capture-pipeline` is assigned to, per section_registry's own
    real, persisted state)
When the Section's own Jobs are rendered
Then the Email Capture Pipeline's own real Jobs appear as multiple
    connected tree nodes, not the single opaque `email-capture-pipeline`
    node rendered today
  And the connections between them are drawn as real dependency edges,
    reusing the already-built tree/dependency-edge layout math
    (layoutAgents.ts's assignTreeAngles/buildDependencyEdges/
    computeAgentDepth), not a new, parallel rendering mechanism
```
<!-- AC-ID: REQ-SB-65-US-01-AC-01 -->

### Scenario 2: The rendered tree reflects the real fork/merge/branch shape of the actual compiled graph, not a linear chain

```gherkin
Given the Email Capture Pipeline's real, compiled StateGraph has two fork
    points (Classify forking to Summarize-Attachment unconditionally and
    Detect-Recurring-Pattern conditionally; Thread-Match/Merge forking to
    Consult-Librarian unconditionally and Route-to-Project conditionally)
When the tree is rendered
Then the visualization's own dependency edges reflect that same
    fork/merge/branch shape — the two conditional branch Jobs
    (Detect-Recurring-Pattern, Route-to-Project) are shown as distinct
    from the unconditional path, and Summarize-Attachment's own fan-in
    into Thread-Match/Merge is visible as a real edge
  And the shape is never flattened into a single straight chain that
    loses the fork/merge structure
```
<!-- AC-ID: REQ-SB-65-US-01-AC-02 -->

### Scenario 3: The Job tree is grounded in the real, running pipeline — never fabricated or hardcoded to match the demo taxonomy's own shape

```gherkin
Given the demo taxonomy's own sample Pipeline (GET /demo/pipelines,
    "pipeline-inbound-email-demo") has a superficially similar 6-Job
    fork/merge/branch-to-expert shape to the real Email Capture Pipeline
When the real Email Capture Pipeline's own Job tree is rendered on the
    Agents Map
Then its node/edge data is read from the real, compiled
    email_capture_pipeline.py StateGraph (or an equally live, real source
    of that graph's own current structure) — never copied from, matched
    against, or hardcoded to resemble the demo sample's own fixture data
  And if the real graph's own topology later changes (a Job added,
    removed, or rewired), the rendered tree changes with it without
    requiring a change to any hardcoded Job-name list in the frontend
```
<!-- AC-ID: REQ-SB-65-US-01-AC-03 -->

### Scenario 4: Section membership for the rendered Job tree is resolved live, never hardcoded

```gherkin
Given `email-capture-pipeline`'s own Section assignment is resolved via
    section_registry.py's real, persisted runtime state (currently "Data
    Gathering", an operator-created Section — not a code-level constant)
When the Agents Map renders any Section's own tree of nodes
Then the Email Capture Pipeline's Jobs appear under whichever Section
    currently owns `email-capture-pipeline`, resolved fresh each time —
    never a Section name hardcoded into the visualization itself
```
<!-- AC-ID: REQ-SB-65-US-01-AC-04 -->

### Scenario 5: This story's scope stays bounded to the Email Capture Pipeline — no other Section's rendering changes

```gherkin
Given every other Section on the Agents Map today (Sales, Support,
    Customers, or any other real, operator-created Section) has no
    equivalent compiled-graph Pipeline behind any of its own Agents
When this story ships
Then no other Section's own rendering changes — the Data Gathering
    Section's Email Capture Pipeline is the one concrete Job tree this
    story renders; extending this same treatment to any other Pipeline
    (Meeting Capture/REQ-SB-56, the demo taxonomy's own 150+ generated
    samples, or any future Pipeline) is out of this story's scope
```
<!-- AC-ID: REQ-SB-65-US-01-AC-05 -->

## Affected Screens

- The real Agents Map (`src/frontend/src/features/agents-map/`) — the Data
  Gathering Section's own rendering, both overview and its
  section-drill-down "Agents Tree" view. Reuses the exact SAME dot +
  dependency-line visual language already approved via
  `html-prototype/agents-map.html`'s own "Agents Tree" pattern (already
  live in the real app for Agent-level `depends_on` rendering, just never
  yet fed a real multi-node tree) — no new visual affordance, no new
  screen region, no `html-prototype/` file change. See `## Notes` for the
  full prototype-parity breakdown.

## Dependencies

- **Blocked by:** `REQ-SB-55-US-01` (Email Capture & Threading Pipeline,
  `Done`, `SPRINT-049`) — the real, compiled `StateGraph` this story
  visualizes; without it there is no real internal structure to render.
- **Related to:** `REQ-SB-63-US-01` (The Librarian, `Done`, `SPRINT-050`)
  — added the 6th graph node (`consult_librarian`) into the SAME compiled
  pipeline this story renders; the tree this story builds must reflect
  that node's real presence, not the PRD's own pre-addition 5-Job list
  (see `## Context`'s verified discrepancy) — this is the live state
  the visualization must consult on every render, not a snapshot.
- **Related to:** `ADR-041` (Agent/Pipeline/Job/Hub taxonomy) / `ADR-043`
  (Email Capture & Threading Pipeline, point 6 — Jobs stay tier-less) —
  the open architecture question this story raises without resolving
  (see `## Notes`).
- **Related to:** `REQ-SB-38-US-01` (Agents Map Density Clustering,
  `Done`) — the `layoutAgents.ts` module (`assignTreeAngles`/
  `buildDependencyEdges`/`computeAgentDepth`) this story feeds real data
  into, rather than replacing.
- **External:** none beyond the already-live compiled pipeline module and
  the already-built frontend layout math this story connects.

## Constraints

- **Jobs stay non-addressable in every respect OTHER than their
  structural shape becoming visible, regardless of which data-source
  option the architect picks** — no new chat surface, no independent
  Working Mode, no Pending-Approval `agent_id`, no click-to-open-detail
  behavior distinct from what the rest of the Map already does for a
  non-clickable structural node. Making a Job's SHAPE visible is not the
  same as making it independently addressable (`ADR-041`'s own Job-tier
  default).
- **The rendered tree must be grounded in the real, running compiled
  graph — never fabricated, never hardcoded to match the demo taxonomy's
  own sample shape** (the PRD's own explicit Acceptance bar).
- **Scope stays bounded to the Email Capture Pipeline** — no blanket
  "every Pipeline renders as a tree" platform is attempted here.
- **Reuse the already-built tree/dependency-edge layout math
  (`layoutAgents.ts`)** rather than inventing a parallel rendering
  mechanism — unless the architect's chosen data-source shape genuinely
  requires a thin adapter (a disclosed judgment call for the architect/
  decomposer to make, not assumed here).
- **The exact data-source shape (read-only inspection endpoint vs. a
  lightweight Job registry entry) is NOT built until the architect
  decides it at `/plan-tasks`** — do not silently pick one.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Decomposer-authored, /plan-tasks step 2, 2026-08-16 — supersedes the
analyst's provisional table. Built against the architect's confirmed
Option A design (see ## Notes). -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-65-US-01-T01 | backend | Read-only Job-tree data source — `email_capture_pipeline.get_job_tree()` (real `_GRAPH.get_graph()` introspection) + new `GET /agents/{agent_id}/jobs` route | `app/business/pipelines/email_capture_pipeline.py`, `app/api/agents_router.py` | `../Tasks/REQ-SB-65-US-01-T01-job-tree-data-source.md` |
| REQ-SB-65-US-01-T02 | frontend | Splice the real Job tree into the Agents Map's Data Gathering Section rendering — new adapter + `fetchAgentJobs`, zero changes to `layoutAgents.ts` | `src/frontend/src/features/agents-map/agentsApiClient.ts`, new adapter module in `src/frontend/src/features/agents-map/`, `src/frontend/src/pages/AgentsMapPage.tsx` | `../Tasks/REQ-SB-65-US-01-T02-agents-map-job-tree-rendering.md` |

## Definition of Done

- [x] The data-source open question (read-only inspection endpoint vs.
      Job registry entries) has been confirmed by the architect and
      recorded in this story's `## Notes`
- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Extending this Job-tree visualization to any Pipeline other than
  Email Capture** — the demo taxonomy's 150+ generated sample pipelines,
  a future Meeting Capture pipeline (`REQ-SB-56`, still `Draft`), or any
  other future Pipeline. Future requirement work, mirroring this
  project's own "prove one real thing before generalizing" precedent.
- **Reopening `ADR-043` point 6 to grant a Job a chat surface, an
  independent Working Mode, or a Pending-Approval `agent_id`** —
  regardless of which data-source option is chosen, Jobs stay
  non-addressable in every respect except their structural shape becoming
  visible.
- **A visually distinct Job-node design** (a different shape/icon/color
  than an existing Agent dot) — this story reuses the exact SAME dot +
  dependency-line visual language already established and approved;
  visually distinguishing Job-tier from Agent-tier nodes, if ever needed,
  is a future refinement, not this story's bar.
- **The Pipeline Builder / DAG visual authoring UI** (`ADR-041` points
  5-6) — explicitly a separate, later decision per the operator's own
  fresh confirmation this pass (see `## Notes`); this story is read-only
  visualization of an already hand-coded pipeline, never authoring/
  editing one.
- **The demo taxonomy's own 150+ generated sample data**
  (`GET /demo/agents`/`GET /demo/pipelines`) — stays exactly what it is
  today, an in-memory UI-density-testing fixture; not deleted, not wired
  into the real Map by this story either.

## Notes

**Open architecture question — genuinely open, NOT resolved by this pass
(why `gate: flagged`, trigger-8):**

The PRD's own text is explicit this is an architect-level decision, not
one for `/spec` to guess. Both options remain real, buildable, and
equally valid at this pass's own drafting time:

- **Option A — a new, read-only endpoint that inspects the real, compiled
  `email_capture_pipeline.py` `StateGraph`'s own structure and returns it
  (Jobs stay non-addressable, `ADR-043` intact).** LangGraph's own
  compiled graph object exposes its structure via graph-introspection
  (the exact API — e.g. something in the shape of `.get_graph()`'s own
  nodes/edges — is left for the architect to confirm against the actual
  installed `langgraph` version, not asserted here). Never reopens
  `ADR-043`'s own "Jobs stay tier-less" decision at all — the Map gains a
  new way to LOOK AT an existing structure, nothing about the Job's own
  addressability changes. The frontend would need either a thin adapter
  shaping this data into something `layoutAgents.ts` can consume
  (id/depends_on at minimum), or a small widening of that module's own
  input type — a real, disclosed design choice for whoever picks this
  option to make.
- **Option B — give each Job a genuine, lightweight registry entry
  after all (reopens `ADR-043` for real).** Lets `GET /agents` return
  Jobs alongside real Agents, so `layoutAgents.ts` consumes them with
  ZERO new frontend code. Costs reopening `ADR-043`'s own explicit,
  same-day decision, and requires carefully re-establishing that a
  "registered" Job still carries none of an Agent's other behaviors (no
  chat, no independent Working Mode, no Pending-Approval identity) — a
  real, nontrivial set of side constraints to get right if chosen.

**Fresh operator context, received mid-`/spec`-pass — a real signal
toward Option A, NOT a resolution locked in on the architect's behalf:**
"It was discussed earlier that we will create the Pipeline for now using
coding, but it will need to have a visual tool to do that later, but the
API needed anyway." This confirms and extends the already-recorded
`ADR-041` sequencing decision (`MEMORY.md`, 2026-08-15: "the Builder is
explicitly deferred until at least ONE real Pipeline is hand-built under
this model first... We will build the pipeline Builder once we build
actual Pipeline and know what we need to do"). The new piece: regardless
of when the visual Pipeline BUILDER (an authoring/editing tool) eventually
gets built, a READ/inspection API is needed now, independently of that —
for VISUALIZING an already hand-coded pipeline, not for authoring one.
This leans toward **Option A**: a read-only inspection endpoint is
exactly "the API needed anyway" for visualization, without pre-building
any part of the authoring/management surface Option B's registry entries
would start to resemble. **This is recorded here as a strong signal for
the architect's own consideration at `/plan-tasks`, not a decision this
`/spec` pass is making on the architect's behalf** — both options above
stay recorded in full, and the architect may still confirm Option B if a
concrete reason to prefer it surfaces during that pass.

**Prototype parity:**

- **Specced** — the tree-of-dots + dependency-line visual language itself:
  already covered by `html-prototype/agents-map.html`'s own "Agents Tree"
  Section-drill-down pattern (a generic depiction of connected agent
  nodes fanning out from a Hub), and already implemented live in the real
  app via `layoutAgents.ts`. This story feeds that already-approved
  pattern real Job-tree data for the first time; it does not introduce a
  new visual affordance.
- **Deferred (future refinement, not this story)** — any visual treatment
  that distinguishes a Job-tier node from an Agent-tier node (different
  shape/icon/color/interaction). Not required by the PRD's own Acceptance
  bar; explicitly out of scope (see `## Non-Goals`).
- **Superseded** — none; no part of the prototype's own existing Agents
  Map design is invalidated by this story.

**No other trigger fired beyond trigger-8 above:** `REQ-SB-65` carries no
`<!-- Draft -->` marker in the PRD (it is explicitly "real, not deferred,"
per its own text); no `ESCALATIONS.md` entry was written — this is a
forward, PRD-acknowledged design question awaiting the architect's own
pass, not a backward pipeline step or an out-of-scope event; not
oversized — one data-source mechanism plus one concrete rendering
integration point, kept as one story since both are facets of the same
"make the real pipeline's structure visible" mechanism; no contradictory
PRD inputs — the PRD's own text simply and deliberately leaves the
data-source shape open, restated verbatim in this story's own Context and
gate reasoning.

**What to do next:** this story stays `Draft`/`gate: flagged` — it should
proceed to `/plan-tasks` for the architect's own pass (this is a design
question for the architect to resolve, not a human-operator confirmation
this pass is blocked on, unlike `REQ-SB-64-US-01`'s own two operator-only
open questions). Once the architect records a concrete decision in
`Implementation/Architecture/architecture.md`/`ADR.md` (or explicitly
confirms no new ADR is needed, mirroring `REQ-SB-63-US-01`'s own
precedent), the decomposer locks ACs and tasks against that shape.

---

**Architect resolution (`/plan-tasks` step 1, 2026-08-16) — the open
question above is now decided, not merely leaned toward:**

**Option A, confirmed** — a new, read-only endpoint that inspects the
real, compiled `email_capture_pipeline.py` `StateGraph`'s own structure.
Jobs stay fully non-addressable; `ADR-043` point 6 stays intact, not
reopened. **No new ADR.** Verified directly against the real installed
`langgraph` package (`1.2.11`, `requirements.txt`), not assumed:
`CompiledStateGraph` (what `StateGraph.compile()` returns, already used by
this exact module) is a `langgraph.pregel.Pregel`, and
`Pregel.get_graph(config=None, xray=False)`
(`langgraph/pregel/main.py` → `langgraph/pregel/_draw.py::draw_graph`)
returns a real `langchain_core.runnables.graph.Graph` — `.nodes: dict[str,
Node(id, name, ...)]`, `.edges: list[Edge(source, target, conditional,
data)]` — built by actually walking the compiled graph's own real
trigger/write wiring, a genuine live structural read, not a re-statement
of the `add_node`/`add_edge` calls. `langgraph`/`langchain_core` are both
already-installed, already-imported dependencies of this exact file
(`ADR-015`/`ADR-041` point 5) — this is a new READ call against an
already-compiled object, never a new dependency, tool, or subpackage.

**Full design, recorded in
`Implementation/Architecture/architecture.md` → "Pipeline Job Tree
Visualization — read-only `StateGraph` introspection" (appended directly
after "Email Capture & Threading Pipeline — First Concrete Pipeline"):**

- New `email_capture_pipeline.get_job_tree() -> list[dict]` — calls
  `_GRAPH.get_graph()` on the SAME already-compiled, module-level `_GRAPH`
  singleton `run_email_capture_pipeline` already calls, filters
  `langgraph.constants.START`/`END` (`"__start__"`/`"__end__"`, the
  graph's own synthetic sentinel nodes — never real Jobs), and shapes the
  result into `{"id": str, "name": str, "depends_on": list[str]}` —
  exactly the shape `AgentSummary.depends_on` (`agentsApiClient.ts`) and
  `layoutAgents.ts` already consume. Reads the graph fresh on every call —
  never bakes in a static Job-name list, satisfying Scenario 3.
- New `GET /agents/{agent_id}/jobs` in `agents_router.py` — mirrors the
  existing `GET /agents/{agent_id}/history`/`knowledge-gaps` per-agent
  sub-resource shape (no new top-level `/pipelines` resource; no second
  real Pipeline exists yet to generalize toward). Read-only. For
  `agent_id == "email-capture-pipeline"`, returns
  `email_capture_pipeline.get_job_tree()`'s list, each entry additionally
  carrying `section_id` from the SAME
  `section_registry.get_agent_section("email-capture-pipeline")` lookup
  `GET /agents` already performs, resolved fresh every call (Scenario 4).
  For any other `agent_id`, returns `[]` — honest, never a 404, never
  fabricated.
- Frontend: a new thin adapter (`features/agents-map/`) reshapes each
  fetched Job into an `AgentSummary`-compatible object (`type`/
  `working_mode`/`icon`/`color`/`is_background_agent`/`description`
  inherited from `email-capture-pipeline`'s own already-fetched
  `AgentSummary`, so no new visual affordance is needed), replaces that
  one pipeline `AgentSummary` entry with its Jobs before `layoutAgents()`
  runs. `layoutAgents.ts`'s own `computeAgentDepth`/`assignTreeAngles`/
  `buildDependencyEdges` need ZERO changes — satisfies AC1's "not a new,
  parallel rendering mechanism" bar directly. `agentsApiClient.ts` gains
  one new call, `fetchAgentJobs(agentId)`, mirroring `fetchAgentHistory`.
  **Left open, disclosed, for the decomposer/coder to pick (not itself an
  architectural decision):** whether the frontend fetches `/jobs` only for
  the literal, known `email-capture-pipeline` id (tighter match to this
  story's own single-Pipeline scope bound) or for every returned agent,
  merging whichever responses are non-empty (fully generic, no hardcoded
  id, marginally more network chatter) — both are real, honest,
  non-fabricating options.

**Alternatives Considered (full reasoning in `architecture.md`):** Option
B (a genuine per-Job `agent_registry` entry) — rejected, reopens `ADR-043`
point 6 for no functional gain Option A doesn't already provide, and would
force every `GET /agents` consumer (chat, actions, Working Mode, the
Detail panel) to defensively distinguish a real Agent from a
registry-shaped Job. A brand-new top-level `/pipelines` router — rejected,
no second real Pipeline exists yet to generalize toward. Hand-deriving the
Job list from `_build_graph`'s own source (a hardcoded name list) instead
of the real introspection API — rejected outright, directly contradicts
Scenario 3's "never fabricated, never hardcoded" bar.

**Architecture scope:** §"Pipeline Job Tree Visualization — read-only
`StateGraph` introspection" and §"Email Capture & Threading Pipeline —
First Concrete Pipeline" (`Implementation/Architecture/architecture.md`) —
the coder is bounded by these two sections; `ADR-043` and `ADR-041` for the
taxonomy/module-boundary context neither section reopens.

**Gate stays `flagged`, trigger-1 (material assumption) — not trigger-3:**
no ADR was created or changed; the concrete endpoint route, response
shape, and frontend merge strategy were genuinely undecided by the
story/PRD (both explicitly deferred "for the architect to confirm") and
this pass designed them. The decomposer proceeds regardless — this flag
does not halt the stage; a `REVIEW-QUEUE.md` entry has been written for
human confirmation alongside the decomposer's own task breakdown.

---

**Decomposer pass (`/plan-tasks` step 2, 2026-08-16) — ACs locked, tasks
written, story advances to `Ready`:**

All 5 untagged Gherkin scenarios tightened for buildability and locked as
`REQ-SB-65-US-01-AC-01` through `AC-05` (tags on the line after each
scenario's closing fence, above). None left `locked: false` — every
scenario had a concrete, observable, DOM/data-level outcome to verify
against the architect's confirmed Option A design; no ambiguity or
unverifiable criterion surfaced this pass.

**Two tasks written, built directly against the architect's confirmed
concrete design** (`architecture.md` → "Pipeline Job Tree Visualization"):

- `REQ-SB-65-US-01-T01` (backend, `depends_on: []`) —
  `email_capture_pipeline.get_job_tree()` (real `_GRAPH.get_graph()`
  introspection, START/END-filtered, never hardcoded) + new
  `GET /agents/{agent_id}/jobs` (mirrors the existing
  `/agents/{agent_id}/history` per-agent sub-resource shape; 404s for a
  genuinely unknown agent id, `[]` for any other real agent, the real Job
  tree + fresh `section_id` for `email-capture-pipeline`). Covers
  AC-02/03/04/05.
- `REQ-SB-65-US-01-T02` (frontend, `depends_on: [REQ-SB-65-US-01-T01]`) —
  `fetchAgentJobs()` + a new, pure adapter that replaces the single
  `email-capture-pipeline` `AgentSummary` with one entry per real Job
  before `layoutAgents()` runs; `layoutAgents.ts` itself untouched. Covers
  AC-01/02/05.

**The architect's one disclosed, non-architectural sub-choice — resolved
by the decomposer, not left further open:** whether the frontend fetches
`/jobs` only for the known `email-capture-pipeline` id, or for every
returned agent. `T02` fetches ONLY for the known id — tighter match to
the story's own explicit single-Pipeline scope bound (Scenario 5), avoids
network chatter with zero present functional gain (no second real
Pipeline exists yet to generalize toward). Logged in `T02`'s own
Context/Notes as a disclosed task-scoping judgement call, not a silent
pick.

**Dependency graph:** `T01 → T02`, a single linear chain, acyclic. No
other story's tasks are touched by either `depends_on` edge (both new
tasks; nothing pre-existing referenced them).

---

**Product-owner pass (`/plan-sprints`, 2026-08-16) — grouped into
`SPRINT-051`:** single-story sprint, `T01`→`T02` linear chain, no sibling
`Ready`, `sprint: ""` story existed to batch alongside it (`REQ-SB-64-US-01`
checked and confirmed `Draft`, excluded). `gate: clear` for this pass —
advances `Draft → Ready` sprint status; the story's own trigger-1 flag stays
as a standing breadcrumb, unchanged. Full reasoning:
`Implementation/Sprints/SPRINT-051-pipeline-job-tree-visualization.md`.

**Definition-of-Done gate re-checked:** every locked AC (`AC-01`..`AC-05`)
has at least one AC-ID-tagged manual verification step in `T01`'s and/or
`T02`'s own `## Tests` block — confirmed by direct cross-reference, not
assumed. `depends_on` is acyclic (a 2-node linear chain). Story `status`
therefore advances `Draft → Ready`; both task files are written at
`status: Ready` in lockstep (never left `Draft` under a `Ready` story,
per this pipeline's own stall-avoidance rule).

**`gate: flagged` stays set, trigger-1 only** — the architect's concrete
endpoint/response-shape/frontend-merge design (and this pass's own
resolution of the one disclosed sub-choice) still awaits human
confirmation per the existing `REVIEW-QUEUE.md` entry; per this project's
own established `REQ-SB-54-US-01`/`REQ-SB-55-US-01`/`REQ-SB-63-US-01`
precedent, a standing trigger-1 flag does not block `status` from
advancing to `Ready` — it is a breadcrumb for human review alongside the
now-locked ACs and tasks, not a build blocker.

---

**Coder pass (`T01`/`T02` build, 2026-08-16) — `T01` `Done`, `T02`
`Blocked`, story `status` downgraded `Ready → Blocked`:**

`T01` (backend Job-tree data source) built and verified `Done`, no
deviations — all 4 of its own locked ACs (`AC-02`-`AC-05`) pass live
against the real, compiled `email_capture_pipeline.py` `StateGraph`.

`T02` (frontend splice) built exactly per the architect's confirmed
design and the decomposer's own task spec — `agentsApiClient.ts`'s new
`fetchAgentJobs()`, a new pure `pipelineJobTreeAdapter.ts`, and
`AgentsMapPage.tsx`'s wiring, `layoutAgents.ts` itself untouched. Live
verification against real backend data (an isolated Node harness running
the actual, unmodified `spliceEmailCapturePipelineJobTree()` +
`layoutAgents()` functions against real `GET /agents`/`GET
/agents/email-capture-pipeline/jobs`/`GET /sections` responses) found a
genuine, previously-unrecognized contradiction: the real
`email-capture-pipeline` agent is `is_background_agent: true`, and
`layoutAgents.ts`'s own already-shipped filter (`REQ-SB-51-US-01`)
excludes every Background Agent from the Agents Map ring entirely — it
was moved to `CrawlersPage.tsx` a prior sprint ago. This story's own
Scenario 1 premise ("the single opaque `email-capture-pipeline` node it
renders today") is factually false against the current, real codebase —
there is no node on the Agents Map to replace today. Inheriting
`is_background_agent` verbatim onto the spliced Job entries (this task's
own explicit, locked Constraint) therefore makes every Job invisible too,
directly failing locked `AC-01`/`AC-02` (confirmed: Data Gathering
Section's own `mapAgents` comes back empty, `dependencyEdges` comes back
empty) even though the adapter's own output is otherwise byte-correct and
`AC-05` genuinely passes. Full trigger/finding/candidate-fix:
`ESCALATIONS.md` → `ESC-038`; open item: `REVIEW-QUEUE.md`.
`T02` marked `Blocked`, not `Done` — its own already-written code is not
reverted, it is very likely reusable once the `is_background_agent`
question is resolved. Story `status` downgraded `Ready → Blocked` since
not every task is `Done`. `SPRINT-051` correspondingly stays `In
Progress`, not `Done` — see the sprint file's own Notes.

---

**Coder pass (`T02` resume, 2026-08-16) — ESC-038 resolved, `T02` rebuilt
and re-verified `Done`, story `status` `Blocked → Done`:**

Operator decision recorded in `ESCALATIONS.md` → `ESC-038` (Resolved):
"Jobs always render, regardless of parent's flag." `T02`'s own
`pipelineJobTreeAdapter.ts` changed so every spliced Job `AgentSummary`
entry gets `is_background_agent: false` hardcoded, never inherited from
the parent `email-capture-pipeline` entry — every other inherited field
stays verbatim, and `email-capture-pipeline`'s own real registry flag is
untouched (still `true`, still on `CrawlersPage.tsx`). Re-verified against
real backend data (Vite SSR-loaded, unmodified `spliceEmailCapturePipelineJobTree()`
+ `layoutAgents()`, no live-server networking): `AC-01` (Data Gathering
Section's `mapAgents` now holds 6 distinct Job nodes, correctly inheriting
`type`/`icon`/`color`/`working_mode`), `AC-02` (5 real dependency edges,
`classify`/`thread_match_merge` each with 2 outgoing edges), `AC-05`
(every other Section unaffected), and the empty-`/jobs` regression case
all PASS. `npx tsc -b` shows zero new errors. Full re-verification
writeup: `T02`'s own Implementation Log ("Resume pass, 2026-08-16"
section). `T02` moved `Blocked → Done`; every task in this story is now
`Done`; story `status` moves `Blocked → Done`. `gate` stays `flagged` —
the pre-existing trigger-1 breadcrumb (architect's designed concrete
endpoint/response-shape/frontend-merge design, still awaiting human
confirmation) is unchanged by this resolution, and a second, distinct flag
is now added for the sprint's own retro-harvest (`SPRINT-051`'s drafted
Retrospective awaiting human propagation into `Implementation/Learnings.md`)
— both named in this story's own `gate_reason` above, not conflated.
Live-browser confirmation of the rendered pixels was explicitly out of
scope for this resume pass — deferred to a separate pass with browser
tooling available.
