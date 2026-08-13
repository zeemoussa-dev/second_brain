---
id: SPRINT-008
title: App shell, Agents Map, and Settings reachability (first frontend build)
status: Done                        # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "retro drafted — human to skim and harvest Learnings.md"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~4 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-11
started: "2026-08-11"               # YYYY-MM-DD when status → In Progress
completed: "2026-08-11"             # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — who drives each transition:
     Draft       → product-owner assembles the sprint. Bidirectional link is written
                   at creation: every story listed here already has sprint: SPRINT-NNN.
     Ready       → product-owner advances Draft→Ready when grouping is CLEAR (gate: clear).
                   Ambiguous, oversized, or blocked grouping stays Draft + gate: flagged.
                   Adding a story to a Ready sprint AUTO-REVERTS it to Draft.
     In Progress → /implement-sprint has started. Coder sets this + records started:.
     Blocked     → external dependency is unmet. Record it under Dependencies.
     Done        → every story is Done and every DoD box is checked. Coder sets this,
                   records completed:, DRAFTS the retrospective, and sets gate: flagged
                   for the human to skim and harvest Learnings.md.
-->

# SPRINT-008 — App shell, Agents Map, and Settings reachability (first frontend build)

## Sprint Goal

Stand up the first real screen of Second Brain's frontend: a persistent,
collapsible navigation shell landing the user on an Agents Map
(Knowledge Base + color-coded configured agents, first/populated states)
with Settings reachable from the same navigation — the foundation every
later frontend story (My Day, the agent chat panel) builds on.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single-story sprint. `REQ-SB-12-US-01` is the only
  `Ready`, ungrouped story this pass touching `src/frontend` — it is the
  **first-ever** frontend build in this codebase (no page exists yet on the
  scaffolded TypeScript/React/Vite stack), a materially different kind of
  work from the other two sprints assembled this pass (SPRINT-006/007,
  both backend/vault-content, zero frontend surface). Its four tasks form
  one dependency chain (`T01` → `{T02, T03}` → `T04`, acyclic) delivering
  one coherent, independently valuable slice (shell + Agents Map +
  Settings-reachability, per the story's own scoping decision) — not
  splittable across sprints without inventing an artificial cross-sprint
  edge through the middle of it (would contradict hard rule 7).
- **Why NOT combined with SPRINT-006/007's stories:** no dependency edge
  exists between this story and any of `REQ-SB-08-US-01`/
  `REQ-SB-16-US-01`/`REQ-SB-17-US-01` (all three are backend/vault-content
  only, touching zero files under `src/frontend`), so there is no
  dependency-graph reason to merge them. Keeping the first frontend build
  in its own sprint also isolates its own real risk: it establishes new
  architectural conventions this pass (`ADR-010` — routing, styling,
  component structure) that no other Ready story this pass depends on or
  needs bundled alongside, and mixing a foundational new-stack build with
  unrelated backend work would blur which sprint's retro the resulting
  frontend-specific learnings (first-ever `react-router`/component-shape
  calibration) belong to.
- **Why NOT combined with `REQ-SB-12-US-02`/`REQ-SB-13-US-01`:** both name
  this story as a dependency, but neither is eligible for `/plan-sprints`
  this pass — `REQ-SB-12-US-02` is `status: Draft` with drafted-but-unlocked
  tasks and no locked ACs (its own Implementation Tasks table still reads
  "TBD"), and `REQ-SB-13-US-01` is `status: Draft` with no task files at
  all yet (only the architect's ADR-011 pass has run). Neither meets this
  role's own input criterion (`status: Ready` AND `sprint: ""`) — this is
  not a grouping ambiguity to flag, simply work not yet ready for this
  stage. They will become eligible once `/plan-tasks` step 2 (the
  decomposer) finishes for each; at that point they should each land in
  their own sprint with `depends_on_sprints: [SPRINT-008]`, since both
  build on this sprint's shell/Agents Map output.
- **Sizing estimate:** ~4 tasks, S (small) — matching this session's
  established `Implementation/Learnings.md`-calibrated precedent
  (SPRINT-001/002/004, all ~4 tasks/S, all landed exactly at estimate with
  zero rework) in raw task count, though this is the first frontend-shaped
  sprint so that precedent's *shape* (data-access primitives → business
  orchestration → downstream wire-ups) doesn't directly transfer — treated
  as a fresh calibration point for "frontend scaffold + one visualization +
  one placeholder page + one end-to-end verification pass" sprints, not
  assumed identical risk to the backend precedent it borrows its task count
  from.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-008 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-12-US-01](../UserStories/REQ-SB-12-US-01-app-shell-agents-map-and-settings.md) | App shell navigation with Agents Map as the default home page, and a reachable Settings page | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- The story's own `## Dependencies` section confirms it is not blocked —
  this is the foundational first story for the frontend application,
  nothing else needs to precede it.
- `T04` (end-to-end verification) runs a real Vite dev server and inspects
  the rendered app via the coder's browser preview tooling — not a
  fixture/mock environment. Not a sprint-blocking dependency, noted here
  for the coder's awareness.
- `ADR-010` (routing, data-fetching, styling, component-structure decisions
  this story's tasks build against) was reviewed and approved by the
  operator 2026-08-11 — not an open blocker.
- **Downstream, not upstream:** `REQ-SB-12-US-02` (My Day dashboard) and
  `REQ-SB-13-US-01` (embedded agent chat panel) both depend on this
  sprint's output once they are decomposed and grouped — recorded here for
  forward awareness, not a blocker on this sprint itself.

---

## Out of Scope

- **The My Day dashboard and its four drill-down pages** — `REQ-SB-12-US-02`,
  a separate story, not yet decomposed/grouped.
- **The agent detail/chat/communication-history side panel** —
  `REQ-SB-13-US-01`, a separate story, not yet decomposed/grouped; Agents
  Map's agent nodes are rendered in this sprint, but clicking one to open a
  detail panel is not built here.
- **Full Settings page content** (vault path editing, Hermes connection
  management) — only reachability is in scope, per the story's own
  Non-Goals.
- **Defining or building support for agent types beyond Worker/Producer/
  Expert**, and **any Hermes integration work** — both explicitly deferred
  per the story's own Non-Goals.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — no change
      needed this pass; the architect's `/plan-tasks` step 1 pass already recorded the
      "Frontend Application Architecture" section this sprint builds against
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-010` confirmed `Accepted`
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S, landed exactly at estimate,
  zero rework, zero blocked tasks — **Takeaway:** the sprint file's own calibration
  note ("fresh calibration point for frontend scaffold + one visualization + one
  placeholder page + one end-to-end verification pass sprints") holds up: this shape
  (foundational scaffold → one bespoke visualization → one thin placeholder →
  one integration/verification pass) is a reusable ~4-task/S template for the next
  frontend-shaped sprint, distinct from the backend "primitives → orchestration →
  wire-up" shape SPRINT-001/002/004 established.

### What worked

- **ADR-010's task-level prescriptiveness paid off directly.** Each task file
  gave near-final TypeScript/JSX/CSS-selector-group content, not just prose intent —
  building against it was close to transcription for the shell/routing/mock-data
  layers, and every hand-verifiable coordinate (all 3 Hub positions, all 5 agent
  positions) matched the prototype's own literal percentages to the third decimal
  once run through `polarToCartesian`. Confirms the prototype-fidelity approach
  (reuse exact class names, exact CSS, a pure geometry function replacing hand-
  derived coordinates) is sound for future visually-bespoke screens.
- **Building a lightweight CDP-based browser driver instead of skipping live
  verification.** No test-stack ADR exists yet and no Playwright/Puppeteer is
  installed, but Node's built-in `WebSocket`/`fetch` plus a locally-launched
  headless Chrome (`--remote-debugging-port`) was enough to drive real clicks,
  read `aria-expanded`/`classList`/`aria-current`, and capture screenshots — with
  zero new project dependencies. This is the difference between "trust the code
  review" and "watch it actually render/click/navigate," which this role's own
  contract requires for screen tasks.
- **Verifying each task's ACs immediately after building it, not batching to the
  end.** T01's shell was confirmed live before T02/T03 were built on top of it,
  so any wiring defect would have been caught at its source, not surfaced later
  as an ambiguous T04 integration failure. T04 then found zero integration
  defects — a real signal the incremental-verification approach worked, not
  just a lucky pass.

### What didn't work

- **The task files' own `## Files to Modify` scoping had two small gaps** (both
  logged as scope-internal assumptions, not escalations): T01 anticipated T02
  adding the `agents-map.css` import to `main.tsx` in prose, but `main.tsx` wasn't
  listed under T02's own `Files to Modify`; and `AgentSection`'s prescribed shape
  (only `hubAngleDeg`) had no field for a section's true angular midpoint, which
  the prototype's `.section-title` positions actually need (they differ for the
  People section, whose Hub is deliberately angle-offset to avoid a collision).
  Neither blocked the build or weakened a locked AC, but a decomposer pass that
  double-checks "does every file this task's own prose says will be touched
  appear in its `Files to Modify` list" would have caught the first gap earlier.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **CDP-over-built-in-WebSocket as this project's zero-dependency browser
  verification tool, until a real test-stack ADR lands** — a ~150-line driver
  script (headless Chrome + Node's native `WebSocket`/`fetch`, no npm install)
  is enough to drive real DOM interaction (clicks, class/attribute inspection,
  screenshots) for manual-mode AC verification on frontend tasks. Reuse this
  for SPRINT-009/010 rather than re-deriving it, until a Playwright/Puppeteer
  ADR formally replaces it.
- **Pin exact dependency versions named in an ADR, don't trust `npm install
  <pkg>` to land on the analyzed major.** `react-router` unpinned resolved to
  `v8.3.0` (released after ADR-010 was written the same day) instead of the
  `v7.x` ADR-010 actually analyzed — caught and corrected by re-installing
  pinned. Any future task installing a dependency an ADR names by major version
  should pin to that major explicitly, not rely on "latest" matching intent.
- **Incremental per-task live verification, not batched-to-the-end.** Verify
  each task's own ACs immediately after building it (not just at a final
  integration task) — surfaces wiring defects at their source and makes a
  dedicated end-to-end task (like this story's `T04`) a genuine regression
  pass with a real chance of finding zero defects, not the first time anything
  gets run.
- **Run `npm run build` (real `tsc -b`), not just `npm run dev`, before
  calling a frontend task `Done`.** The Vite dev server's esbuild-based
  transform strips TypeScript types without fully type-checking, so a real
  compile error (`T01`'s `ApiError` parameter-property constructor tripping
  this project's own pre-existing `erasableSyntaxOnly: true` tsconfig
  setting) rendered and behaved perfectly under `npm run dev` and would
  have shipped invisibly. Caught only because `T04`'s final consistency
  pass ran the actual production build. Add this as a standing step for
  every future frontend task, not just an end-of-story nicety.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **A task's prose (`## Context / Notes`, `## Starting State -> End State`)
  describing a file change that its own `## Files to Modify` list omits** —
  found twice this sprint (T01's `main.tsx` note for T02; no explicit
  `AgentSection` field for the prototype's non-hub-aligned section-title
  angle). Low-cost to avoid at decomposition time by cross-checking every file
  path mentioned in a task's prose actually appears in its own `Files to
  Modify` section.

### Open follow-ups

- **`REQ-SB-12-US-02`** (My Day dashboard) should be sprint-planned with
  `depends_on_sprints: [SPRINT-008]` once its own decomposition (locked
  ACs, `status: Ready`) completes — its drafted task files already exist
  (`T01`–`T05`) but are not yet locked.
- **`REQ-SB-13-US-01`** (embedded agent chat panel) should likewise be
  sprint-planned with `depends_on_sprints: [SPRINT-008]` once
  `/plan-tasks` step 2 (the decomposer) produces its task files — none
  exist yet.

---

## Notes

gate: clear 2026-08-11 — no triggers fired for this grouping decision:
`REQ-SB-12-US-01`'s own dependency graph (`T01` → `{T02, T03}` → `T04`) is
honoured intact, not split across sprints. Not oversized — four tasks
matches this session's established ~4-task precedent exactly. Not blocked
— all four tasks are `status: Ready`, the story itself is `status: Ready`,
and its own `## Dependencies` section confirms it is the foundational
first frontend story with nothing upstream required. No cross-sprint
dependency was introduced (`depends_on_sprints: []`) — `REQ-SB-12-US-02`
and `REQ-SB-13-US-01` both depend on this sprint's output, but neither is
grouped into a sprint yet (both still `status: Draft`, decomposition
incomplete), so no `depends_on_sprints` edge exists to record on *this*
sprint; the edge will instead be recorded on *their* sprint(s) once they
are decomposed and grouped, per hard rule 7's "same sprint or ordered
sprints" requirement (ordered sprints is the only option here, since they
are separate PRD-acceptance-scoped stories, not folded into this one).
Single phase (P1) throughout. The story's `gate: flagged` (trigger-3,
ADR-010 creation) does not block this stage — the operator reviewed and
approved ADR-010 2026-08-11; resetting the story's `gate:` value is not
this role's job. Advanced `Draft → Ready`.

---

**Sprint assembled (2026-08-11):** 1 story, 4 tasks, `status: Ready`,
`gate: clear`. Eligible for `/implement-sprint`.

**Not grouped this pass (not eligible — `status: Draft`, not `Ready`):**
`REQ-SB-12-US-02` (My Day dashboard) and `REQ-SB-13-US-01` (embedded agent
chat panel) both name this sprint's story as a dependency but have not
finished `/plan-tasks` step 2 (decomposition) — see `## Open follow-ups`
above.

---

**Coder pass (`/implement-sprint`), 2026-08-11.** `REQ-SB-12-US-01` built
end-to-end: `T01` (shell/routing scaffold) → `{T02 (Agents Map), T03
(Settings)}` → `T04` (end-to-end verification), all 4 tasks `Done`, all 6
locked ACs verified live against a real `npm run dev` server via a
headless-Chrome CDP driver script (no test-stack ADR exists yet — see the
Retrospective's "What worked" for why this satisfies the pipeline's
manual-verification default and the coder role's "look before Done"
requirement for screen tasks). Zero runtime/AC-blocking defects; `T04`
did find and fix one build-time-only TypeScript error in `T01`'s
`api/client.ts` (`erasableSyntaxOnly` violation from a parameter-property
constructor — `npm run build`/`tsc -b` catches it, the dev server does
not) — a same-file, same-behavior fix per `T04`'s own explicit mandate,
logged in its Implementation Log. Zero blocked tasks, zero
`ESCALATIONS.md` entries. Sprint `status: Ready -> Done`, `completed: 2026-08-11`. Story
`status: Ready -> Done`; its stale `gate: flagged` (from the architect's
ADR-010-creation flag) reset to `clear` since the underlying
`REVIEW-QUEUE.md` entry is already resolved (removed from the live
queue — the operator's approval is recorded in this sprint's own
Dependencies section). `BACKLOG.md` updated (`REQ-SB-12-US-01`/
`SPRINT-008` rows -> `Done`; `REQ-SB-12-US-02`/`SPRINT-009` rows left
untouched, still `Ready`, out of this sprint's scope). This sprint's
`gate` set to `flagged` (`gate_reason`: retro drafted, awaiting human
Learnings.md harvest) per this role's own mandatory sprint-wrap
behaviour — a `REVIEW-QUEUE.md` entry has been added.
