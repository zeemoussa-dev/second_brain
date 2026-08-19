---
id: REQ-SB-65-US-01-T02
title: Splice the real Job tree into the Agents Map's Data Gathering rendering — reuse layoutAgents.ts verbatim
parent_story: REQ-SB-65-US-01
requirement_id: REQ-SB-65
type: frontend
status: Done
gate: flagged
gate_reason: "trigger-1 (material assumption, carried from the parent story's architect pass — the concrete frontend merge/adapter strategy was designed, not spec'd by the PRD/story) — standing breadcrumb, unchanged by this task's own build. ESC-038's contradiction is RESOLVED — operator decision 2026-08-16: spliced Job entries always render regardless of the parent pipeline's own Background Agent flag ('Jobs always render, regardless of parent's flag'). is_background_agent is now hardcoded false on every spliced Job entry, not inherited verbatim — implemented and re-verified this pass, all locked ACs pass. See ESCALATIONS.md ESC-038 (Resolved) and REVIEW-QUEUE.md."
phase: P1
depends_on: [REQ-SB-65-US-01-T01]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-65-US-01-T02 — Splice the real Job tree into the Agents Map's Data Gathering rendering

## Parent Story

- Story: [[REQ-SB-65-US-01]] — `../UserStories/REQ-SB-65-US-01-email-capture-pipeline-job-tree-visualization.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-65 *Pipeline Job Visualization — the Email Capture Pipeline's Real, Running Internals Rendered as a Tree on the Agents Map*

---

## Objective

Fetch `T01`'s new `GET /agents/email-capture-pipeline/jobs` for the one, literally
known `email-capture-pipeline` id, reshape each returned Job into an
`AgentSummary`-compatible object (inheriting `type`/`working_mode`/`icon`/`color`/
`description` from the already-fetched `email-capture-pipeline` `AgentSummary`;
`is_background_agent` hardcoded `false` per the ESC-038 resolution — Jobs always
render on the ring regardless of the parent pipeline's own Background Agent
status), and splice those Job entries into the `AgentSummary[]` list handed
to `layoutAgents()` in place of the single `email-capture-pipeline` entry — with
ZERO changes to `layoutAgents.ts` itself.

---

## Starting State → End State

**Before / Inputs:**
- `agentsApiClient.ts`'s `AgentSummary` interface already has
  `depends_on: string[]` / `branch_target_agent_id: string | null` — populated
  today with honest `[]`/`null` defaults for every real agent (`agents_router.py`'s
  `list_agents()`), never yet fed a real multi-node tree.
- `layoutAgents.ts`'s `layoutAgents(agents, sectionList)` already computes
  `computeAgentDepth`/`assignTreeAngles`/`buildDependencyEdges` generically over
  any `AgentSummary[]` whose `depends_on` is real — confirmed by direct reading
  this pass, needs no change to consume Job-shaped entries.
- `AgentsMapPage.tsx`'s `refreshAgents()` currently does
  `Promise.all([fetchAgentList(), fetchSections()])` then
  `layoutAgents(agentList, sectionList)` directly — no Job-tree fetch exists yet.
- `T01`'s new `GET /agents/{agent_id}/jobs` returns `{"id", "name", "depends_on",
  "section_id"}[]` for `email-capture-pipeline`, `[]` for any other agent.

**After / Outputs:**
- `agentsApiClient.ts` gains a `JobTreeEntry` interface (`id`/`name`/`depends_on`/
  `section_id`) and `fetchAgentJobs(agentId: string): Promise<JobTreeEntry[]>`,
  mirroring `fetchAgentHistory`'s own shape.
- A new thin adapter (module inside `features/agents-map/`) exports a function
  that takes the full fetched `AgentSummary[]` plus the fetched `JobTreeEntry[]`
  for `email-capture-pipeline`, and returns a NEW `AgentSummary[]`: if the Job list
  is non-empty and an `email-capture-pipeline` entry is found in the input, that
  one entry is removed and replaced with one `AgentSummary` per Job (`id`/`name`/
  `depends_on` from the Job entry; `section_id` from the Job entry, falling back to
  the original pipeline agent's own `section_id` if the Job's own is `null`;
  `type`/`working_mode`/`icon`/`color`/`is_background_agent`/`description` all
  copied verbatim from the original `email-capture-pipeline` `AgentSummary`;
  `branch_target_agent_id: null`). If the Job list is empty (fetch failed, or no
  Jobs exist yet), the input `AgentSummary[]` is returned completely unchanged.
- `AgentsMapPage.tsx`'s `refreshAgents()` fetches `fetchAgentJobs('email-capture-pipeline')`
  alongside the existing two calls, runs the adapter over the result, and hands
  the ADAPTED list to `layoutAgents()` — `layoutAgents.ts` itself is untouched.

---

## Files to Modify

- `src/frontend/src/features/agents-map/agentsApiClient.ts` — add `JobTreeEntry`
  interface + `fetchAgentJobs(agentId)`.
- `src/frontend/src/features/agents-map/` — add one new adapter module (e.g.
  `pipelineJobTreeAdapter.ts`) exporting the merge function described above.
- `src/frontend/src/pages/AgentsMapPage.tsx` — wire the new fetch + adapter call
  into `refreshAgents()`, ahead of the existing `layoutAgents(agentList,
  sectionList)` call.

---

## Constraints

- Inherits from parent story: Jobs stay fully non-addressable — no new CSS class,
  no new visual affordance, no click-to-open-detail behavior distinct from what
  the Map already does for a non-clickable structural node (`type`/`working_mode`/
  `icon`/`color`/`description` are all INHERITED from the original
  `email-capture-pipeline` `AgentSummary`, never independently set).
- **RESOLVED 2026-08-16, supersedes the original verbatim-inheritance design
  (ESC-038):** `is_background_agent` is set `false` on every spliced Job entry —
  NOT inherited from the original `email-capture-pipeline` `AgentSummary`. Operator
  decision: the Job tree always renders on the Agents Map ring regardless of the
  parent pipeline's own Background Agent status. `email-capture-pipeline` itself
  keeps its own `is_background_agent: true` flag unchanged (still appears on
  `CrawlersPage.tsx` as today) — this is scoped ONLY to the synthetic, spliced Job
  `AgentSummary` entries the adapter produces, not a change to the real agent's own
  registry flag.
- `layoutAgents.ts` (`computeAgentDepth`/`assignTreeAngles`/`buildDependencyEdges`/
  `layoutAgents`/`layoutSectionDrilldown`) must receive ZERO changes — this task's
  entire mechanism is feeding it an already-shaped `AgentSummary[]` (AC-01's own
  "not a new, parallel rendering mechanism" bar).
- The adapter fetches `/jobs` ONLY for the one, literally-known
  `email-capture-pipeline` id — not for every returned agent (the decomposer's own
  resolution of the architect's disclosed open sub-choice; see Context/Notes for
  the reasoning).
- The adapter must be a pure function (input `AgentSummary[]` + `JobTreeEntry[]` →
  output `AgentSummary[]`), independently callable/testable without a live fetch —
  no network call inside the adapter itself; `fetchAgentJobs` stays a separate,
  thin API-client call.
- Every OTHER real agent in the input list (any agent whose id is not
  `email-capture-pipeline`) must pass through the adapter completely unchanged —
  no other Section's rendering may be affected (Scenario 5).
- If the `/jobs` fetch fails or returns `[]`, the Map must degrade to exactly
  today's existing single-`email-capture-pipeline`-node behavior — never a blank
  Section, never a thrown error that breaks the whole Map's `catch` fallback.
- Must not change `AgentSummary`'s own existing field shapes (`depends_on`/
  `branch_target_agent_id` stay exactly as `T01`'s parent story left them for every
  non-adapted agent).

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-65-US-01-AC-01]** Call the adapter with a real fetched `AgentSummary[]`
   (containing the real `email-capture-pipeline` entry) and a real fetched
   `T01` `/jobs` response — confirm the returned list no longer contains the single
   `email-capture-pipeline` entry, and instead contains 6 Job-derived entries (ids
   matching the 6 real Job ids). Feed that adapted list into the REAL
   `layoutAgents()` — confirm the Data Gathering Section's own `mapAgents` now
   contains 6 distinct nodes instead of 1, and every one of them carries the SAME
   `type`/`icon`/`color`/`working_mode` the original `email-capture-pipeline` agent
   had (confirming no new visual affordance was introduced).
2. **[REQ-SB-65-US-01-AC-02]** Using that same adapted list, confirm the real
   `layoutAgents()`'s returned `dependencyEdges` contains a distinct edge for
   `classify→summarize_attachment`, `classify→detect_recurring_pattern`,
   `summarize_attachment→thread_match_merge`, `thread_match_merge→consult_librarian`,
   and `thread_match_merge→route_to_project` — confirm `classify` has 2 outgoing
   edges and `thread_match_merge` has 2 outgoing edges (the real two fork points),
   not 1 each — the shape is never flattened into a single chain.
3. **[REQ-SB-65-US-01-AC-05]** Call the adapter with a real fetched `AgentSummary[]`
   containing agents from at least one OTHER real Section alongside
   `email-capture-pipeline` — confirm every non-`email-capture-pipeline` entry in
   the adapter's output is reference-/value-identical to its own input entry.
   Confirm `layoutAgents()`'s returned `sections`/`mapAgents` for every OTHER
   Section, run against the adapted list, are identical to running `layoutAgents()`
   on the UN-adapted list restricted to those other Sections' agents — no other
   Section's rendering changes.
4. Regression: call the adapter with an EMPTY `JobTreeEntry[]` (simulating a failed
   or empty `/jobs` fetch) — confirm the returned `AgentSummary[]` is unchanged
   from the input, and `layoutAgents()` still renders the single, today's-existing
   `email-capture-pipeline` node with no error thrown.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `fetchAgentJobs(agentId)` added to `agentsApiClient.ts`, mirroring
      `fetchAgentHistory`'s own shape
- [x] A new, pure adapter function replaces the single `email-capture-pipeline`
      `AgentSummary` with one entry per real fetched Job, inheriting
      `type`/`working_mode`/`icon`/`color`/`description` from the original
      entry (`is_background_agent` hardcoded `false` per the ESC-038
      resolution, NOT inherited — see updated `## Constraints`)
- [x] `AgentsMapPage.tsx` fetches `/jobs` only for the known
      `email-capture-pipeline` id and feeds the adapted list into `layoutAgents()`
- [x] `layoutAgents.ts` itself receives zero code changes
- [x] Every other Section's own rendering is unaffected (adapter passes non-target
      agents through unchanged)
- [x] An empty/failed `/jobs` fetch degrades to today's existing single-node
      behavior, never a broken Map
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `layoutAgents.ts`'s own math (`computeAgentDepth`/
  `assignTreeAngles`/`buildDependencyEdges`/`layoutSectionDrilldown`).
- A visually distinct Job-node design (different shape/icon/color than an Agent
  dot) — explicit Non-Goal of the parent story.
- Fetching `/jobs` for every returned agent (the generic, fully-open variant of
  the architect's disclosed sub-choice) — not chosen this pass; see Context/Notes.
- `CrawlersPage.tsx` — fetches `fetchAgentList()`/`fetchSections()` but never
  calls `layoutAgents()` (a Crawler is never placed on the Map's ring); untouched
  by this task.
- Any Pipeline other than Email Capture ever being adapted — scope-bounded to
  `email-capture-pipeline` only (Scenario 5).

---

## Context / Notes

Full reasoning: `Implementation/Architecture/architecture.md` → "Pipeline Job Tree
Visualization — read-only `StateGraph` introspection" (Frontend integration
bullet). Also read `Implementation/Architecture/ADR.md` → `ADR-043`/`ADR-041` for
the taxonomy/non-addressability context this task must not violate.

**Decomposer resolution of the architect's disclosed open sub-choice (fetch
`/jobs` only for `email-capture-pipeline` vs. for every returned agent):** this
task fetches `/jobs` ONLY for the literal, known `email-capture-pipeline` id —
tighter match to the parent story's own explicit single-Pipeline scope bound
(Scenario 5), and avoids the marginally increased network chatter the fully
generic variant would add against today's small agent count for zero present
functional gain (no second real Pipeline exists yet to generalize toward,
mirroring `ADR-041`'s own repeated "prove one real thing before generalizing"
sequencing). Not itself an architectural decision — a task-scoping judgement call,
disclosed here per this codebase's own established "reconcile and log, don't
silently pick" precedent (`Learnings.md`, `SPRINT-049`).

Compose around the REAL current `agentsApiClient.ts`/`layoutAgents.ts`/
`AgentsMapPage.tsx` as they actually exist today — do not assume exact
variable/function names from this task's own illustrative prose without reading
the real files first.

**Real cross-task dependency, not a placeholder:** this task cannot be built until
`T01`'s `GET /agents/{agent_id}/jobs` exists as a real, running endpoint — if the
coder reaches this task before `T01` lands, treat it as genuinely blocked, not as
license to improvise a divergent response shape.

**Gate stays `flagged`, trigger-1** — carried from the parent story's architect
pass (the concrete frontend merge/adapter strategy was designed at `/plan-tasks`).
A `REVIEW-QUEUE.md` entry already exists for human confirmation; it does not block
this task's build. See the parent story's own `## Notes` and `REVIEW-QUEUE.md`.

---

## Implementation Log

**Built exactly as designed, no deviations in the code itself:**
- `agentsApiClient.ts` gained `JobTreeEntry` (`id`/`name`/`depends_on`/
  `section_id`) and `fetchAgentJobs(agentId)`, mirroring `fetchAgentHistory`'s
  own one-line shape.
- New `pipelineJobTreeAdapter.ts` — `spliceEmailCapturePipelineJobTree(agents,
  jobs)`: pure function, no network call; empty `jobs` or no
  `email-capture-pipeline` entry in `agents` returns `agents` unchanged
  (reference-identical); otherwise removes that one entry and replaces it
  with one `AgentSummary` per Job, `id`/`name`/`depends_on` from the Job,
  `section_id` from the Job falling back to the original agent's own,
  `type`/`working_mode`/`icon`/`color`/`is_background_agent`/`description`
  copied verbatim from the original `email-capture-pipeline` `AgentSummary`,
  `branch_target_agent_id: null`.
- `AgentsMapPage.tsx`'s `refreshAgents()` now fetches
  `fetchAgentJobs('email-capture-pipeline')` alongside the existing two
  calls (caught locally with `.catch(() => [])` so a failed `/jobs` fetch
  degrades gracefully instead of tripping the whole-map blank-state
  `.catch()`), runs the adapter, and hands the adapted list to
  `layoutAgents()`. `layoutAgents.ts` received zero changes (confirmed by
  `git status` before/after — untouched).
- `npx tsc -b` (run via the project's bundled `tools/node/node.exe`, since
  `node`/`npx` are not on this shell's `PATH`) — zero new errors from any of
  the 3 files this task touched; the 6 pre-existing `TS7053` errors in
  `AgentNode.tsx`/`AgentsMapCanvas.tsx`/`SectionDrilldown.tsx`/
  `SectionHub.tsx` predate this session (already `M` in `git status` at
  session start) and are out of this task's `## Files to Modify`.

**Environment finding, not a code defect (documented here + `MEMORY.md`):**
the long-running dev backend on port 8001 (`tools/run-backend.cmd`) could
not be hot-reloaded to pick up `T01`'s already-`Done` `/jobs` route — its
`uvicorn.exe --reload` child process is invisible to `Get-Process`/
`tasklist`/`taskkill` by its own PID (only killable via its `cmd.exe`
wrapper's PID, found via `Get-CimInstance Win32_Process | Where
CommandLine -match 'run-backend'`); even after killing that wrapper, the
port kept answering stale (pre-`T01`) responses for several attempts,
apparently from an orphaned worker process still holding the socket after
its own supervisor died (`taskkill /F /T` on the wrapper PID eventually
cleared it). Confirmed the real code is correct throughout via
`fastapi.testclient.TestClient` (mirroring `T01`'s own established
verification method for this exact codebase) — `GET
/agents/email-capture-pipeline/jobs` returns the real 6-entry tree,
`fork/merge` shape exactly as `T01`'s own Implementation Log recorded.

**Live verification — real backend data, real frontend functions, isolated
Node harness (no live-server networking involved, given the above):** wrote
a throwaway harness (`scratchpad/verify/`, not part of this task's `Files
to Modify`, discarded after use) that imports the REAL, unmodified
`spliceEmailCapturePipelineJobTree()` and `layoutAgents()` source (compiled
via the project's own local `typescript` package) and runs them against
REAL `GET /agents`/`GET /agents/email-capture-pipeline/jobs`/`GET
/sections` JSON captured via `TestClient`.

- **[REQ-SB-65-US-01-AC-01] FAIL (partial).** The adapter's own output is
  correct: input 7 agents -> adapted 12 (email-capture-pipeline removed,
  6 Jobs added), `email-capture-pipeline` absent from the result, all 6
  real Job ids present, every Job entry's `type`/`icon`/`color`/
  `working_mode`/`is_background_agent`/`description` verified identical to
  the original `email-capture-pipeline` `AgentSummary` (byte-equal
  comparison). BUT feeding that adapted list into the REAL `layoutAgents()`
  produced **0** nodes in the Data Gathering Section's own `mapAgents`
  (not 6) — see root cause below. AC-01's own "the Data Gathering
  Section's own mapAgents now contains 6 distinct nodes" bar is not met.
- **[REQ-SB-65-US-01-AC-02] FAIL.** `dependencyEdges` came back empty
  (`[]`) — `buildDependencyEdges()` is built from `mapAgents`, which is
  empty for the reason above, so no edges of any shape can exist. None of
  the 5 expected real edges (`classify->summarize_attachment`,
  `classify->detect_recurring_pattern`, `summarize_attachment->
  thread_match_merge`, `thread_match_merge->consult_librarian`,
  `thread_match_merge->route_to_project`) are present; `classify`'s/
  `thread_match_merge`'s own outgoing-edge counts are both 0, not 2.
- **[REQ-SB-65-US-01-AC-05] PASS.** Every non-`email-capture-pipeline`
  agent in the adapter's output is JSON-identical to its own input entry.
  `layoutAgents()`'s own `mapAgents` for every OTHER Section (`technical`,
  `productivity`, `customers`, `sales`), run against the adapted list, are
  identical to running `layoutAgents()` on the un-adapted list restricted
  to those Sections — confirmed no other Section's rendering changed.
- **Regression test (Tests item #4, not itself a locked AC-ID) — also
  failed, and independently confirms the same root cause:** calling the
  adapter with an empty `JobTreeEntry[]` correctly returns the input
  `AgentSummary[]` completely unchanged (reference-identical, `===` true).
  But running `layoutAgents()` on that unchanged list shows the Data
  Gathering Section's `mapAgents` was ALREADY 0 (not 1) even before any of
  this task's own changes — `email-capture-pipeline` itself does not
  render as a node on the Agents Map today, contradicting the premise this
  whole task (and its parent story's Scenario 1) was built against.

**Root cause (see `ESCALATIONS.md` ESC-038 for the full writeup):** the
real `email-capture-pipeline` agent is `is_background_agent: true` (real
`GET /agents` response). `layoutAgents.ts`'s own already-shipped filter
(`REQ-SB-51-US-01`, confirmed by reading its current, real, UNMODIFIED
source) excludes every Background Agent from `mapAgents`/the ring
entirely — Background Agents were moved to the separate `CrawlersPage.tsx`
a prior sprint ago (confirmed by that file's own comment: "`
AgentsMapCanvas.tsx`'s own now-removed 'Background Agents' card"). This
task's own Constraint required `is_background_agent` to be copied verbatim
onto every spliced Job entry — which the adapter correctly does — but that
verbatim inheritance is what makes every Job invisible too, the same way
the aggregate pipeline agent already is. This task's own Constraint
("`layoutAgents.ts` must receive ZERO changes") forbids fixing this by
touching the filter; the same task's own Constraint ("`is_background_agent`
... copied verbatim") forbids fixing this by not inheriting the field —
these two instructions are now in direct, unresolvable tension with each
other and with locked `AC-01`/`AC-02`. Not a coder judgement call: any
unilateral choice here either silently weakens a locked AC or silently
overrides an explicit, decomposer-authored Constraint — both forbidden.
Escalated per protocol; task marked `Blocked`, not `Done`. **The code
built this pass (`agentsApiClient.ts`/`pipelineJobTreeAdapter.ts`/
`AgentsMapPage.tsx` wiring) is NOT being reverted** — it is correct per
the task's own current spec and is very likely reusable as-is once the
one-line `is_background_agent` question is resolved (see
`REVIEW-QUEUE.md`'s own candidate fix); only the task's own `status`
reflects that it cannot be verified `Done` yet.

**Live-browser verification not performed, disclosed:** this task's own
launching brief asked for live-browser confirmation in addition to the
task's own manual `## Tests` steps. Not performed, for two independent,
disclosed reasons: (1) no browser-automation tool is available in this
session to literally observe rendered pixels; (2) it would not have been
informative regardless — the isolated-harness verification above runs the
exact same, real, unmodified `layoutAgents()`/adapter functions the
browser's own React tree calls, and conclusively shows 0 nodes render for
Data Gathering under the current design, a data-level fact a screenshot
cannot contradict. The dev backend on port 8001 also could not be
restarted to actually serve `T01`'s route during this session (see the
Environment finding above), so a live-browser check against it would have
exercised stale pre-`T01` backend responses, not this task's own real
code path, and would not have added evidence either way.

---

**Resume pass, 2026-08-16 — ESC-038 resolved, task rebuilt/re-verified,
`Blocked → Done`:**

**The fix, applied exactly per the operator resolution recorded in this
task's own frontmatter/`## Constraints`:** in
`pipelineJobTreeAdapter.ts::spliceEmailCapturePipelineJobTree`, the
`is_background_agent` field on each spliced Job `AgentSummary` entry
changed from `pipelineAgent.is_background_agent` (verbatim inheritance) to
a hardcoded `false`. No other field, and no other file, touched — every
other inherited field (`type`/`section_id` fallback/`icon`/`color`/
`description`/`working_mode`) stays exactly as the prior pass built it.
`email-capture-pipeline`'s own real `GET /agents` entry (fetched via
`fetchAgentList()`) is untouched — still `is_background_agent: true`,
still renders on `CrawlersPage.tsx` as today; this change only affects the
synthetic Job entries this adapter produces.

**Re-verification technique — same isolated-harness approach as the prior
pass, refined:** real backend data captured via `fastapi.testclient.TestClient`
(`GET /agents` → 7 agents, `GET /agents/email-capture-pipeline/jobs` → 6
real Job entries, `GET /sections` → 5 sections) written to a throwaway
fixtures file. Rather than a plain Node/tsc transpile (which cannot run
`agentsApiClient.ts`/`layoutAgents.ts` as-is — both modules transitively
load `src/api/client.ts` and `agentsApiClient.ts`'s own
`ATTACHMENT_BASE_URL`, both of which reference `import.meta.env` at module
top level; a plain CommonJS/Node transpile has no `import.meta.env` and
throws before any function can even be called), this pass used Vite's own
SSR module loader (`vite.createServer({ appType: 'custom',
server: { middlewareMode: true } })` + `server.ssrLoadModule(...)`) — the
exact same TypeScript-to-JS compilation and `import.meta.env` resolution
the real app's own dev server performs, but invoked directly from a
throwaway Node script with zero HTTP requests against any running
dev-server port. Loaded the REAL, unmodified
`pipelineJobTreeAdapter.ts::spliceEmailCapturePipelineJobTree` and
`layoutAgents.ts::layoutAgents` this way and ran them against the real
captured fixtures. Harness lived at
`src/frontend/.verify-scratch/harness.mjs` — NOT part of this task's
`## Files to Modify`, deleted after use; fixtures file deleted after use
too.

- **[REQ-SB-65-US-01-AC-01] PASS.** Adapter output: 12 entries (7 input
  agents − 1 `email-capture-pipeline` + 6 Jobs), `email-capture-pipeline`
  absent, all 6 real Job ids present (`classify`, `summarize_attachment`,
  `detect_recurring_pattern`, `thread_match_merge`, `route_to_project`,
  `consult_librarian`). Every Job entry's `type`/`icon`/`color`/
  `working_mode`/`description` byte-identical to the original
  `email-capture-pipeline` `AgentSummary`; every Job entry's
  `is_background_agent` is `false` (the fix), confirmed distinct from the
  real `email-capture-pipeline` fixture entry's own `is_background_agent:
  true` (confirming the parent's own real flag is unaffected). Fed into
  the REAL `layoutAgents()`: the Data Gathering Section's own `mapAgents`
  now contains exactly **6** distinct nodes (`classify`,
  `consult_librarian`, `detect_recurring_pattern`, `route_to_project`,
  `summarize_attachment`, `thread_match_merge`) — was 0 before this fix.
- **[REQ-SB-65-US-01-AC-02] PASS.** `layoutAgents()`'s own
  `dependencyEdges`, filtered to the Data Gathering section, contains
  exactly the 5 expected real edges: `classify->summarize_attachment`,
  `classify->detect_recurring_pattern`,
  `summarize_attachment->thread_match_merge`,
  `thread_match_merge->consult_librarian`,
  `thread_match_merge->route_to_project`. Outgoing-edge counts:
  `classify` → 2, `thread_match_merge` → 2, `summarize_attachment` → 1 —
  the real two fork points each show 2 outgoing edges, never flattened
  into a single chain.
- **[REQ-SB-65-US-01-AC-05] PASS (re-confirmed).** Every non-
  `email-capture-pipeline` agent in the adapter's output is
  JSON-identical to its own input entry. `layoutAgents()`'s own
  `mapAgents` for every OTHER Section (`technical`: 1 agent,
  `productivity`: 3 agents, `customers`: 0, `sales`: 0), run against the
  adapted list, are identical (`JSON.stringify` equality) to running
  `layoutAgents()` on the un-adapted list restricted to those Sections —
  no other Section's rendering changed.
- **Regression test (Tests item #4) — PASS.** Calling the adapter with an
  empty `JobTreeEntry[]` returns the input `AgentSummary[]`
  reference-identical (`===` true, confirmed directly, not just
  value-equal). Running `layoutAgents()` on that unchanged list shows the
  Data Gathering Section's own `mapAgents` at 0 nodes — the SAME as the
  pre-existing baseline this exact regression check found in the prior
  pass (before any of this task's changes, `email-capture-pipeline`
  itself already didn't render as a node, since it is itself a
  Background Agent) — confirmed unchanged from today's existing
  behavior, not a new regression; no error thrown.

**`npx tsc -b` (via the project's bundled `tools/node/node.exe`) —
re-run this pass:** the same 6 pre-existing `TS7053` errors in
`AgentNode.tsx`/`AgentsMapCanvas.tsx`/`SectionDrilldown.tsx`/
`SectionHub.tsx` as the prior pass (all outside this task's own `## Files
to Modify`, pre-existing before this session). Zero new errors from
`pipelineJobTreeAdapter.ts` or any of this task's own touched files.
Confirmed via `git status` that `layoutAgents.ts` shows no diff
attributable to this task (its `M` status in the wider repo predates this
session, part of other in-flight uncommitted work) — this task's own
change is isolated to `pipelineJobTreeAdapter.ts` (new, untracked file).

**Outcome:** all 5 locked ACs (`AC-01` through `AC-05`) now verified —
`AC-03`/`AC-04` were `T01`'s own (already `Done`); `AC-01`/`AC-02`/`AC-05`
are this task's own, all now PASS. Task moved `Blocked → Done`.
Live-browser confirmation of the rendered pixels was explicitly out of
scope for this resume pass (per the launching brief) — deferred to a
separate pass with browser tooling available; the data-level verification
above is conclusive for what the real, unmodified rendering functions
produce, independent of that.
