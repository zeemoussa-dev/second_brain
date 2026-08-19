---
id: REQ-SB-65-US-01-T01
title: Read-only Job-tree data source — email_capture_pipeline.get_job_tree() + GET /agents/{agent_id}/jobs
parent_story: REQ-SB-65-US-01
requirement_id: REQ-SB-65
type: backend
status: Done
gate: flagged
gate_reason: "trigger-1 (material assumption) — carried from the parent story's architect pass (the concrete endpoint route/response shape was designed, not spec'd by the PRD/story). No decomposer-owned trigger fired on this task itself. See REVIEW-QUEUE.md."
phase: P1
depends_on: []
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-65-US-01-T01 — Read-only Job-tree data source — `email_capture_pipeline.get_job_tree()` + `GET /agents/{agent_id}/jobs`

## Parent Story

- Story: [[REQ-SB-65-US-01]] — `../UserStories/REQ-SB-65-US-01-email-capture-pipeline-job-tree-visualization.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-65 *Pipeline Job Visualization — the Email Capture Pipeline's Real, Running Internals Rendered as a Tree on the Agents Map*

---

## Objective

Add a new `get_job_tree() -> list[dict]` function to the real, already-compiled
`email_capture_pipeline.py` module that reads the SAME module-level `_GRAPH`
singleton's own `get_graph()` introspection (LangGraph's real `Pregel.get_graph()`
API, confirmed against the installed `langgraph==1.2.11`) and shapes the result
into `{"id", "name", "depends_on"}` entries; expose it read-only via a new
`GET /agents/{agent_id}/jobs` route in `agents_router.py`, mirroring the existing
`GET /agents/{agent_id}/history` per-agent sub-resource shape.

---

## Starting State → End State

**Before / Inputs:**
- `src/backend/app/business/pipelines/email_capture_pipeline.py` (`REQ-SB-55-US-01-T07`,
  `REQ-SB-63-US-01-T02`, both `Done`) has a module-level `_GRAPH = _build_graph()`
  singleton with 6 real graph nodes today (`classify`, `summarize_attachment`,
  `detect_recurring_pattern`, `thread_match_merge`, `route_to_project`,
  `consult_librarian`) — confirmed by direct reading of `_build_graph()` this pass.
  No introspection function exists yet.
- `agents_router.py`'s `list_agents()` (`GET /agents`) currently hardcodes
  `agent["depends_on"] = []` / `agent["branch_target_agent_id"] = None` for every
  real agent, with a comment explicitly noting "no real pipeline-dependency source
  exists yet" — this task is that source, arriving.
- `section_registry.get_agent_section(agent_id)` already returns `{"id": ..., "name": ...}
  | None`, used identically by `list_agents()`/`get_agent()`.

**After / Outputs:**
- `email_capture_pipeline.py` gains `get_job_tree() -> list[dict]`: calls
  `_GRAPH.get_graph()` on the existing `_GRAPH` singleton (never recompiles a
  second graph instance), filters out the graph's own synthetic `START`/`END`
  sentinel nodes (`"__start__"`/`"__end__"`), and returns one `{"id": str, "name":
  str, "depends_on": list[str]}` entry per real Job node — `depends_on` derived
  directly from the real `Graph.edges` (every edge whose `target` is this node
  contributes its `source` to that node's `depends_on`). Reads `_GRAPH.get_graph()`
  fresh on every call — never a static, hardcoded Job-name list.
- `agents_router.py` gains `GET /agents/{agent_id}/jobs`: 404s exactly like
  `/history`/`/knowledge-gaps` when `agent_id` is genuinely unknown
  (`agent_registry.get_agent(agent_id) is None`); for `agent_id ==
  "email-capture-pipeline"`, returns `email_capture_pipeline.get_job_tree()`'s
  list, each entry additionally carrying `section_id` from the SAME
  `section_registry.get_agent_section("email-capture-pipeline")` lookup
  `list_agents()`/`get_agent()` already perform, resolved fresh on every call; for
  any OTHER real, known `agent_id`, returns `[]` — honest, never fabricated.

---

## Files to Modify

- `src/backend/app/business/pipelines/email_capture_pipeline.py` — add
  `get_job_tree()`. Import whatever `langgraph` constant(s) are needed to filter
  the sentinel nodes (e.g. `START` alongside the already-imported `END` from
  `langgraph.graph`, or the literal `"__start__"`/`"__end__"` string ids — confirm
  against the real installed `langgraph.graph`/`langgraph.constants` module before
  choosing).
- `src/backend/app/api/agents_router.py` — add `GET /agents/{agent_id}/jobs`,
  importing `email_capture_pipeline` from `app.business.pipelines`.

---

## Constraints

- Inherits from parent story: Jobs stay fully non-addressable — this endpoint is
  read-only (`GET` only), never creates any Job-tier registry entry, chat surface,
  Working Mode, or Pending-Approval identity (`ADR-043` point 6 stays intact, not
  reopened).
- `get_job_tree()` must call `.get_graph()` on the EXISTING `_GRAPH` module-level
  singleton — never construct or compile a second `StateGraph` instance.
- `get_job_tree()` must never hardcode a static list of Job names/ids anywhere in
  its body — every id/name/depends_on value must be read from `_GRAPH.get_graph()`'s
  own `.nodes`/`.edges` on each call (Scenario 3's "never fabricated, never
  hardcoded" bar — a future Job added/removed/rewired in `_build_graph` must change
  this function's output with zero code change here).
- `GET /agents/{agent_id}/jobs` must never 404 for a real, known, non-pipeline
  `agent_id` — it returns `[]` (Scenario 5's scope bound: only
  `email-capture-pipeline` has a real, populated answer today). It DOES still 404
  for a genuinely unknown `agent_id`, mirroring `/history`/`/knowledge-gaps`'s
  existing convention.
- `section_id` on each returned entry must be resolved via a fresh
  `section_registry.get_agent_section("email-capture-pipeline")` call on every
  request — never cached, never hardcoded to a Section name/id (Scenario 4).
- Must respect the `api → business → data_access` layer boundary (`ADR-003`) —
  `agents_router.py` composes `email_capture_pipeline.get_job_tree()` directly,
  mirroring `list_agents()`'s own existing multi-registry-composition shape.
- Do not modify `_build_graph()`, any existing node function, or
  `run_email_capture_pipeline()` — this task only ADDS `get_job_tree()` as a new,
  sibling read function.
- Do not modify `list_agents()`/`get_agent()`'s own existing `depends_on: []` /
  `branch_target_agent_id: None` defaults for the general `GET /agents` response —
  out of this task's scope (a separate, already-shipped, honest-empty-default
  behavior for every OTHER agent; this task only adds the new per-agent
  sub-resource).

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-65-US-01-AC-02]** Direct call to `email_capture_pipeline.get_job_tree()`
   against the real, already-compiled `_GRAPH` — confirm the returned list has
   exactly 6 entries (`classify`, `summarize_attachment`,
   `detect_recurring_pattern`, `thread_match_merge`, `route_to_project`,
   `consult_librarian`) and that `"__start__"`/`"__end__"` are absent. Confirm
   `classify`'s own `depends_on == []` (the graph's real entry point);
   `summarize_attachment` AND `detect_recurring_pattern` both list `classify` in
   their own `depends_on` (the first, real fork point); `thread_match_merge` lists
   `summarize_attachment` in its own `depends_on` (the real fan-in edge);
   `consult_librarian` AND `route_to_project` both list `thread_match_merge` in
   their own `depends_on` (the second, real fork point) — confirming the actual
   compiled graph's fork/merge/branch shape is captured, not flattened into a
   chain.
2. **[REQ-SB-65-US-01-AC-03]** Read `get_job_tree()`'s own source — confirm it
   contains no hardcoded string literal naming any of the 6 Job ids/names as a
   static list; every id/name/depends_on value traces directly to
   `_GRAPH.get_graph().nodes`/`.edges`. Call `get_job_tree()` twice in the same
   process and confirm both calls independently query `_GRAPH.get_graph()` (not a
   module-level cached result computed once at import time).
3. **[REQ-SB-65-US-01-AC-04]** Call `GET /agents/email-capture-pipeline/jobs`
   (real running backend or FastAPI `TestClient`) — confirm every returned entry's
   `section_id` equals `section_registry.get_agent_section("email-capture-pipeline")`'s
   real, current id. Reassign `email-capture-pipeline`'s Section via the existing
   `PATCH /agents/email-capture-pipeline` `section_id` call, re-fetch `/jobs`, and
   confirm every entry's `section_id` reflects the NEW Section immediately, with
   zero code change — then reassign it back to its original Section.
4. **[REQ-SB-65-US-01-AC-05]** Call `GET /agents/{other_real_agent_id}/jobs` for a
   real, existing non-pipeline agent — confirm it returns `[]` (never a 404, never
   a fabricated tree). Call `GET /agents/does-not-exist/jobs` for a genuinely
   unknown agent id — confirm it 404s, mirroring `/history`/`/knowledge-gaps`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `get_job_tree()` reads `_GRAPH.get_graph()` fresh on every call, filters
      `START`/`END` sentinel nodes, and derives `id`/`name`/`depends_on` purely
      from the real graph's own nodes/edges — no hardcoded Job-name list
- [x] The returned `depends_on` shape correctly reflects both real fork points
      (after `classify`, after `thread_match_merge`) and the real fan-in
      (`summarize_attachment` → `thread_match_merge`)
- [x] `GET /agents/{agent_id}/jobs` mirrors the `/history`/`/knowledge-gaps`
      404-on-unknown-agent convention, returns the real Job tree (with fresh
      `section_id`) for `email-capture-pipeline`, and returns `[]` — never a 404,
      never fabricated — for every other real agent
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend consumption of this endpoint — `T02`.
- Granting Jobs any `agent_registry` entry, chat surface, independent Working
  Mode, or Pending-Approval identity — explicitly out of scope per the parent
  story's own Non-Goals; `ADR-043` point 6 stays fully intact.
- A new top-level `/pipelines` resource — rejected by the architect (see
  `architecture.md`); this task nests under the existing per-agent
  `/agents/{agent_id}/...` convention only.
- Any Pipeline other than Email Capture (`email-capture-pipeline`) ever returning
  a non-empty Job tree — scope-bounded to this one Pipeline (Scenario 5).

---

## Context / Notes

Full reasoning: `Implementation/Architecture/architecture.md` → "Pipeline Job Tree
Visualization — read-only `StateGraph` introspection" (appended directly after
"Email Capture & Threading Pipeline — First Concrete Pipeline"). Also read
`Implementation/Architecture/ADR.md` → `ADR-043` (the module boundary this task's
new function extends, not reopens) and `ADR-041` (the Job-tier non-addressability
default this task's endpoint must not violate).

**Verified, not assumed:** `langgraph` `1.2.11` (`requirements.txt`) is already an
installed, already-imported dependency of this exact module — `CompiledStateGraph`
(what `StateGraph.compile()` returns) is a `langgraph.pregel.Pregel`, and
`Pregel.get_graph(config=None, xray=False)` returns a real
`langchain_core.runnables.graph.Graph` (`.nodes: dict[str, Node]`, `.edges:
list[Edge]`) built by walking the compiled graph's own real trigger/write wiring —
a live structural read, never a re-statement of the `add_node`/`add_edge` calls.
This is a new READ call against an already-compiled object — never a new
dependency, subpackage, or tool.

Compose around the REAL current `email_capture_pipeline.py`/`agents_router.py` as
they actually exist today — do not assume exact variable/node names from this
task's own illustrative prose without reading the real files first (this
codebase's own established "compose around the real current file" precedent,
`Learnings.md`, `SPRINT-020`/`021`/`027`/`048`/`050`).

**Gate stays `flagged`, trigger-1** — carried from the parent story's architect
pass (the concrete endpoint route/response shape was designed at `/plan-tasks`,
not spec'd by the PRD/story). A `REVIEW-QUEUE.md` entry already exists for human
confirmation; it does not block this task's build. See the parent story's own
`## Notes` and `REVIEW-QUEUE.md`.

---

## Implementation Log

**Built as designed, no deviations.** `email_capture_pipeline.py` gained
`get_job_tree()` (imports `START` alongside the already-imported `END` from
`langgraph.graph` — confirmed against the real installed `langgraph==1.2.11`:
`from langgraph.graph import START, END` resolves to `'__start__'`/`'__end__'`).
`agents_router.py` gained `GET /agents/{agent_id}/jobs`, importing
`email_capture_pipeline` from `app.business.pipelines` and composing
`agent_registry.get_agent`/`section_registry.get_agent_section` exactly as
`list_agents()` already does.

Verification was run directly against the real venv
(`src/backend/.venv`) — `python -c` one-off scripts and FastAPI
`TestClient`, not a persisted pytest file (repo has no test suite for this
module yet, per this task's own "Automated tests: n/a — test tooling
pending"). Every script's real output is what's recorded below, not
inferred.

- **[REQ-SB-65-US-01-AC-02]** PASS. Called `email_capture_pipeline.get_job_tree()`
  directly against the real, already-compiled `_GRAPH`. Returned exactly 6
  entries: `classify`, `summarize_attachment`, `thread_match_merge`,
  `route_to_project`, `detect_recurring_pattern`, `consult_librarian` —
  `__start__`/`__end__` absent. Confirmed: `classify.depends_on == []`;
  `summarize_attachment.depends_on == ['classify']`;
  `detect_recurring_pattern.depends_on == ['classify']` (first fork point);
  `thread_match_merge.depends_on == ['summarize_attachment']` (fan-in);
  `consult_librarian.depends_on == ['thread_match_merge']` and
  `route_to_project.depends_on == ['thread_match_merge']` (second fork
  point). Real fork/merge/branch shape captured, not flattened — matches
  the graph's actual compiled wiring, directly inspected via
  `_GRAPH.get_graph().edges` before writing the function (`__start__ ->
  classify`; `classify -> {summarize_attachment, detect_recurring_pattern}`;
  `summarize_attachment -> thread_match_merge`; `thread_match_merge ->
  {consult_librarian, route_to_project}`; `{consult_librarian,
  route_to_project, detect_recurring_pattern} -> __end__`).
- **[REQ-SB-65-US-01-AC-03]** PASS. Read `get_job_tree()`'s own source via
  `inspect.getsource` and searched for each of the 6 Job id/name string
  literals — zero matches; every id/name/depends_on value traces to
  `graph.nodes`/`graph.edges` at call time. Called `get_job_tree()` twice
  in the same process — both calls independently returned the same,
  freshly-computed list (`tree1 == tree2` True, `tree1 is not tree2` True
  — equal in value, distinct objects, confirming no cached singleton
  result is returned).
- **[REQ-SB-65-US-01-AC-04]** PASS. `GET /agents/email-capture-pipeline/jobs`
  via FastAPI `TestClient` returned 200, 6 entries, every entry's
  `section_id == "data-gathering"` — matching
  `section_registry.get_agent_section("email-capture-pipeline")`'s real,
  current id at call time. Reassigned via
  `PATCH /agents/email-capture-pipeline {"section_id": "technical"}`,
  re-fetched `/jobs` — every entry's `section_id` immediately read back as
  `"technical"`, zero code change. Reassigned back to `"data-gathering"`
  and re-verified restored.
- **[REQ-SB-65-US-01-AC-05]** PASS. `GET /agents/meeting-capture/jobs`
  (a real, existing non-pipeline agent) returned `200 []` — never a 404,
  never a fabricated tree. `GET /agents/does-not-exist/jobs` returned
  `404 {"detail": "Unknown agent"}`, mirroring `/history`/`/knowledge-gaps`.

Full backend test suite (`pytest`, `src/backend`) re-run after the change:
1 passed, no regressions.

**Assumption logged for human spot-check (scope-internal judgement call,
not an escalation):** placed the new `GET /agents/{agent_id}/jobs` route
directly above `GET /agents/{agent_id}/knowledge-gaps` in `agents_router.py`
(after `/history`) — purely a file-ordering choice among existing per-agent
sub-resource routes, no behavioral significance.
