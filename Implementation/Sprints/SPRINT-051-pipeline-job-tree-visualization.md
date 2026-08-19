---
id: SPRINT-051
title: Pipeline Job Visualization — Email Capture Pipeline's real Jobs rendered as a tree on the Agents Map
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Two distinct flags: (1) trigger-1, standing breadcrumb — REQ-SB-65-US-01's architect-designed concrete endpoint route/response shape/frontend-merge strategy still awaits human confirmation, see REVIEW-QUEUE.md. (2) Retro-harvest — this sprint's drafted Retrospective below (including ESC-038 as a genuine finding) awaits human propagation into Implementation/Learnings.md. REQ-SB-65-US-01-T02 was blocked (ESC-038) — RESOLVED 2026-08-16, operator decision: spliced Job entries get is_background_agent: false hardcoded, not inherited. T02 rebuilt/re-verified Done; story Done; sprint Done. See ESCALATIONS.md ESC-038 (Resolved) and REVIEW-QUEUE.md."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~2 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-16
started: "2026-08-16"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-16"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-051 — Pipeline Job Visualization — Email Capture Pipeline's real Jobs rendered as a tree on the Agents Map

## Sprint Goal

Render the Email Capture Pipeline's real, compiled `StateGraph` structure as
connected Job tree nodes on the Agents Map's Data Gathering Section, replacing
today's single opaque `email-capture-pipeline` node, via a new read-only
introspection endpoint and a thin frontend adapter that reuses the already-built
`layoutAgents.ts` tree math verbatim.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-65-US-01` is the only `Ready`,
  ungrouped story this pass found. Its 2 tasks are a strict linear chain
  (`T01` backend read-only introspection endpoint, `depends_on: []` → `T02`
  frontend rendering, `depends_on: [REQ-SB-65-US-01-T01]`), acyclic, both within
  one story and one architecture section
  (`architecture.md` → "Pipeline Job Tree Visualization — read-only
  `StateGraph` introspection"). No reason to split a 2-task linear chain across
  sprints, and no sibling `Ready`, ungrouped story exists to combine it with.
- **`REQ-SB-64-US-01` deliberately excluded, confirmed directly from its own
  frontmatter, not assumed:** `status: Draft` (not `Ready`),
  `gate: flagged` — `gate_reason` names two genuinely unresolved open
  questions the operator has not yet answered (whether it retrofits
  `REQ-SB-55`'s already-shipped `consult_librarian` call site, and the
  mechanical shape of Hub-mediation) — see
  `Implementation/UserStories/REQ-SB-64-US-01-section-hub-kb-traffic-gateway.md`
  frontmatter and its own `REVIEW-QUEUE.md` entry. It is not eligible for
  `/plan-sprints` regardless of any topical proximity to `REQ-SB-65-US-01`
  (both touch the Email Capture Pipeline's KB-write path) — status is the
  single source of truth, per this pipeline's own hard rule; a `Draft` story
  is never pulled into a sprint. No other `Ready`, `sprint: ""` story was
  found in `Implementation/UserStories/*.md` this pass.
- **Story-level `gate: flagged` (trigger-1, the architect's designed concrete
  endpoint route/response shape/frontend-merge strategy) is a standing
  breadcrumb, not a build blocker** — per this project's own established
  `REQ-SB-54-US-01`/`SPRINT-048`, `REQ-SB-55-US-01`/`SPRINT-049`, and
  `REQ-SB-63-US-01`/`SPRINT-050` precedent (a `Ready`/`flagged` story is
  fully eligible for `/plan-sprints` and `/implement-sprint`; the flag awaits
  a human look at the architect's designed shape, independent of delivery
  progress). Both `T01` and `T02` are themselves `status: Ready` — nothing
  is `Blocked`.
- **Sizing estimate:** ~2 tasks, S — matches this project's own closest
  sizing analog for a 2-task story (`SPRINT-036`, "~2 tasks, S — Actual: 2
  tasks, S — matched exactly," `Implementation/Learnings.md`) and
  `SPRINT-029`'s identical 2-task/S precedent. `T02` (frontend splice +
  live verification of the real fork/merge/branch shape across 5 locked
  ACs) is expected to be the heavier of the two, mirroring `SPRINT-036`'s
  and `SPRINT-027`'s own repeated finding that a frontend task's real cost
  is live-verification complexity, not code volume.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-051 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-65-US-01](../UserStories/REQ-SB-65-US-01-email-capture-pipeline-job-tree-visualization.md) | Pipeline Job Visualization — render the Email Capture Pipeline's real Jobs as connected tree nodes on the Agents Map | P1 | Done |

**Tasks in scope** (dependency order): `T01` (Read-only Job-tree data source —
`email_capture_pipeline.get_job_tree()` + `GET /agents/{agent_id}/jobs`,
`depends_on: []`) → `T02` (Splice the real Job tree into the Agents Map's Data
Gathering rendering, `depends_on: [REQ-SB-65-US-01-T01]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None. `REQ-SB-65-US-01`'s own `## Dependencies`
  names `REQ-SB-55-US-01` (`Done`, `SPRINT-049`) and `REQ-SB-63-US-01`
  (`Done`, `SPRINT-050`) as the real, compiled pipeline this story
  visualizes — both already `Done` well before this pass, so no
  `depends_on_sprints` ordering edge is needed; neither `T01` nor `T02`
  records a cross-story `depends_on` edge into either sprint's own tasks.
- `REQ-SB-64-US-01` — topically adjacent (both concern the Email Capture
  Pipeline's KB-write path) but genuinely independent: `REQ-SB-65-US-01` is
  read-only visualization of the pipeline's own structure; `REQ-SB-64-US-01`
  would mediate KB-bound writes. Neither story's tasks reference the
  other's. Held out of this sprint per its own `Draft`/`gate: flagged`
  status (see Grouping Rationale) — not a dependency this sprint waits on.

---

## Out of Scope

- `REQ-SB-64-US-01` (Section Hub as KB Traffic Gateway) — `Draft`, two
  unresolved operator open questions; not eligible for `/plan-sprints`
  until the operator answers them and the story is re-run through
  `/plan-tasks`.
- Any Pipeline other than Email Capture (Meeting Capture/`REQ-SB-56`, the
  demo taxonomy's own 150+ generated samples, or any future Pipeline) —
  explicitly out of `REQ-SB-65-US-01`'s own scope (Scenario 5), not
  attempted here.
- The Pipeline Builder / DAG visual authoring UI (`ADR-041` points 5-6) —
  unrelated, separately deferred work.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied (automated tests item stays open pending test tooling, per this project's own standing exception)
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (no change this pass — architecture stayed exactly what the architect designed at `/plan-tasks`)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (none needed — confirmed at `/plan-tasks`)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~2 tasks, S — **Actual:** 2 tasks, S, but `T02` needed a
  real backward detour (`Blocked → ESC-038 → operator decision → rebuilt →
  Done`) mid-flight — **Takeaway:** the task COUNT matched exactly (matching
  `SPRINT-036`/`SPRINT-029`'s own precedent this sprint's own sizing note
  cited), but "S" undercounted the actual verification cost. This sprint
  reconfirms `SPRINT-036`'s/`SPRINT-027`'s already-recorded finding
  ("a frontend task's real cost is live-verification complexity, not code
  volume") one level deeper: here it wasn't just verification complexity,
  it was verification that surfaced a genuine, previously-invisible
  cross-cutting contradiction between two already-`Done` pieces of work
  (`REQ-SB-51-US-01`'s Background Agent ring filter and this task's own
  locked Constraint) that no amount of reading the spec beforehand would
  have caught — only running the real functions against real data did.

### What worked

- Reusing `layoutAgents.ts` verbatim, with a thin adapter feeding it
  already-shaped data, worked exactly as designed — zero changes to that
  module across the whole sprint, confirmed by direct `git status`/diff
  checks both before and after the fix, not just assumed.
- Isolated-harness verification against REAL backend data (via
  `fastapi.testclient.TestClient` for the backend, Vite's own
  `server.ssrLoadModule()` for the frontend) caught a genuine, real defect
  that no amount of code review alone would have — and, once resolved,
  gave a fast, live-server-networking-free way to re-confirm the fix
  without needing a browser.
- The escalate-rather-than-improvise discipline paid off directly: the
  coder had a candidate one-line fix already identified and written up in
  `ESC-038` at block time, but did NOT apply it unilaterally since it
  contradicted the task's own locked Constraint prose word-for-word — the
  operator's actual decision matched that candidate fix exactly, but the
  point is it was the operator's call to make, not the coder's guess to
  apply silently.

### What didn't work

- **The parent story's own Scenario 1 premise was already false against
  the real, current codebase at spec time** — "the single opaque
  `email-capture-pipeline` node it renders today" assumed the aggregate
  pipeline agent currently occupies a ring slot; it does not, and hasn't
  since `REQ-SB-51-US-01` moved every Background Agent off the Agents Map
  ring onto `CrawlersPage.tsx`, a full 14+ sprints before this one. Neither
  `/spec` (analyst) nor `/plan-tasks` (architect/decomposer) caught this —
  both reasoned from the story's own prose, not from directly exercising
  the real, current Agents Map against real backend data before locking
  the ACs. This is the SAME class of gap `MEMORY.md`'s own
  `depends_on`/`branch_target_agent_id` finding from earlier this exact
  day already named: "any frontend field a demo/mock backend populates but
  the real backend doesn't is a live landmine that stays invisible until
  the real backend is actually exercised through that UI path" — here the
  landmine wasn't a missing field, it was a stale assumption about what
  the CURRENT Map already renders, carried forward from before a shipped,
  unrelated-sounding change (`REQ-SB-51-US-01`, Background Agent
  crowding/ring-slot behavior) quietly invalidated it.
- Two of this task's own locked instructions — "`layoutAgents.ts` must
  receive ZERO changes" and "`is_background_agent`... copied verbatim" —
  were in direct, unresolvable tension with each other and with locked
  `AC-01`/`AC-02` once the real data was exercised. Neither the architect
  nor the decomposer could have reasonably foreseen this without the SAME
  live-data check the coder ultimately had to perform to find it —
  reinforcing that "reasoning from prose alone" has a real, recurring
  blind spot in this project specifically around Background-Agent/ring
  visibility interactions.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Check current live rendering state before locking ACs that assume it**
  — when a story's own Acceptance Criteria assume "X currently renders as
  Y" (e.g. "the single opaque node it renders today"), verify that premise
  against the REAL, CURRENT app (not just the story's own prose) at
  `/spec`/`/plan-tasks` time, especially when the premise depends on the
  interaction of two features shipped in different, non-adjacent sprints
  (here: `REQ-SB-51-US-01`'s Background Agent ring filter, shipped many
  sprints before `REQ-SB-65-US-01` was even drafted). A stale premise
  baked into locked ACs surfaces as a live-verification failure much later
  and more expensively than a five-minute manual check would have.
- **Isolated-harness verification via the real framework's own module
  loader, not a plain transpile, when the real source has environment-tied
  top-level code** — Vite's `server.ssrLoadModule()` (SSR mode,
  `middlewareMode: true`, zero live networking) correctly resolves
  `import.meta.env` and other Vite-specific runtime behavior that a plain
  `tsc`/Node CommonJS transpile cannot; reach for it whenever a frontend
  module under isolated verification has a top-level `import.meta`
  reference anywhere in its own import chain (as `agentsApiClient.ts`
  itself and `src/api/client.ts` both do here).

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Locking an AC's premise ("renders as X today") without checking it
  against the live, current app** — a plausible-sounding assumption about
  current rendered state, carried in a story's own Context/Scenario prose
  unchecked through `/spec` and `/plan-tasks`, can silently contradict a
  much earlier, unrelated-sounding shipped change; only live verification
  against real data surfaces the contradiction, and only at build time —
  the most expensive point to find it.

### Open follow-ups

- The story's own standing trigger-1 flag (architect's concrete endpoint
  route/response shape/frontend-merge design) still awaits a human look —
  independent of this sprint's own delivery completion; see
  `REVIEW-QUEUE.md`.
- Live-browser confirmation of the rendered Agents Map pixels (Data
  Gathering Section showing the real 6-node Job tree) was explicitly
  deferred by this pass's own launching brief to a separate pass with
  browser tooling available — not yet performed.

---

## Notes

**Sprint assembled 2026-08-16 (`/plan-sprints`).** `REQ-SB-65-US-01` enters
`/plan-sprints` at `status: Ready`, `gate: flagged` (trigger-1, material
assumption — the architect's designed concrete endpoint/response-shape/
frontend-merge design; a standing breadcrumb, not a blocker per the
established `REQ-SB-54-US-01`/`SPRINT-048`, `REQ-SB-55-US-01`/`SPRINT-049`,
`REQ-SB-63-US-01`/`SPRINT-050` precedent explicitly reconfirmed for this
pass). It is the only `Ready`, `sprint: ""` story found — confirmed by
scanning `Implementation/UserStories/*.md` frontmatter directly.
`REQ-SB-64-US-01` was checked specifically and confirmed `Draft`
(`gate: flagged`, two unresolved operator open questions) — excluded, not
batched.

**Gate: `gate: clear` 2026-08-16.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — the single-story grouping
and the (absent) sequencing are both read directly off the decomposer's own
recorded `depends_on` edges (`T01: []`, `T02: [REQ-SB-65-US-01-T01]`,
confirmed by direct reading, not guessed) and the story's own already-`Done`
upstream dependencies; (2) `REQ-SB-65` is not `<!-- Draft -->`/unfinalised in
the PRD; (3) product-owner does not write ADRs — none was created or
changed by this pass; (4) no new `ESCALATIONS.md` entry; (5) not oversized
(2 tasks, S, matching the `SPRINT-036`/`SPRINT-029` 2-task/S precedent) —
not a blocked story — both tasks are `status: Ready`; no cross-sprint
dependency had to be introduced (`depends_on_sprints: []`, genuinely none
needed); (6) N/A (coder-only trigger); (7) no contradictory inputs; (8) not
genuinely ambiguous — a single story with a strict 2-task linear chain and
no sibling `Ready` story to combine it with has exactly one reasonable
partition. Advances `Draft → Ready`.

**`BACKLOG.md` updated:** `REQ-SB-65` row's Sprint column set to
`SPRINT-051`; a new `SPRINT-051` row appended to the Sprint Status table.

**REVIEW-QUEUE.md:** no new entry written by this pass — the story's own
standing trigger-1 flag (architect's concrete endpoint/response-shape/
frontend-merge design awaiting human confirmation) already has its own
`REVIEW-QUEUE.md` entry, unchanged and unresolved by this pass; see
`REVIEW-QUEUE.md` → "review the architect's concrete endpoint/response-shape/
frontend-merge design" (2026-08-16, `REQ-SB-65-US-01`).

---

**Coder pass (`/implement-sprint`, 2026-08-16) — `status` downgraded
`In Progress → Blocked`:** `T01` built and verified `Done` (all 4 of its
own locked ACs pass live). `T02` built exactly per the architect/
decomposer's own confirmed design, but live verification against real
backend data found the design's own `is_background_agent`-verbatim
inheritance makes every spliced Job entry invisible on the Agents Map
ring — the real `email-capture-pipeline` agent is itself a Background
Agent, already excluded from the ring by `layoutAgents.ts`'s own
already-shipped, unmodified filter (`REQ-SB-51-US-01`). Locked
`AC-01`/`AC-02` fail against real data; `AC-05` passes. Full writeup:
`ESCALATIONS.md` → `ESC-038`; open review item:
`REVIEW-QUEUE.md` → `REQ-SB-65-US-01-T02`. `T02` marked `Blocked`, not
`Done`; the parent story `REQ-SB-65-US-01` downgraded `Ready → Blocked`
since not every task is `Done`; this sprint therefore cannot close —
`status` downgraded `In Progress → Blocked`, `gate: flagged` (a NEW
trigger, additional to the story's own pre-existing standing trigger-1
breadcrumb — both are real and both are named in `gate_reason` above, not
conflated). No Retrospective drafted this pass — the Definition of Done's
own "every story in scope has status Done" bar is not met, and drafting a
retro on a still-blocked sprint would misrepresent it as closed. Retro
drafting resumes once `REQ-SB-65-US-01-T02`'s block is resolved and the
task re-run to `Done`.

---

**Coder pass (`T02` resume, 2026-08-16) — ESC-038 resolved, `T02` rebuilt
and re-verified `Done`, sprint `status` `In Progress → Done`:** operator
decision recorded in `ESCALATIONS.md` → `ESC-038` (Resolved): spliced Job
`AgentSummary` entries get `is_background_agent: false` hardcoded, never
inherited. `T02` rebuilt with that one-line change, re-verified against
real backend data (Vite SSR-loaded, unmodified adapter + `layoutAgents()`,
no live-server networking) — all 5 locked ACs across the story
(`AC-01`-`AC-05`) now pass; `npx tsc -b` shows zero new errors. `T02`
moved `Blocked → Done`; every task in `REQ-SB-65-US-01` is now `Done`;
story `status` moved `Blocked → Done`. Every story in this sprint is now
`Done` — sprint `status` moves `In Progress → Done`, `completed:
2026-08-16`. Retrospective drafted above, factoring in the real ESC-038
detour as a genuine "what didn't work" finding. `gate: flagged` stays
set — two distinct, named flags: (1) the story's own pre-existing standing
trigger-1 breadcrumb (architect's designed concrete shape, still awaiting
human confirmation), unchanged by this resolution; (2) this sprint's own
NEW retro-harvest flag, per the sprint skill contract — the human
propagates the drafted Retrospective's patterns/antipatterns into
`Implementation/Learnings.md`; the coder does not write `Learnings.md`
itself.
