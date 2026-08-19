---
id: SPRINT-037
title: Agents Map density clustering
status: Done
gate: flagged
gate_reason: "coder T04 scope-internal judgement call (src/frontend/src/pages/AgentsMapPage.tsx, out of declared task scope) + retro drafted, awaiting human read-through per Pipeline.md's sprint-wrap protocol"
phase: P1
depends_on_sprints: []
sizing_estimate: "~4 tasks, S"
created: 2026-08-13
started: "2026-08-14"
completed: "2026-08-14"
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-037 — Agents Map density clustering

## Sprint Goal

Collapse a crowded Section+Type-ring's overflow agents on the Agents Map
into a single clickable cluster marker with its own drill-down.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-38-US-01` is the only story
  here. Its 4 tasks form one straight chain (`T01`/`T02` independent, `T03`
  depends on `T01`, `T04` depends on `T01`/`T02`/`T03`); verified directly
  against every task file's real frontmatter that none carries a cross-story
  `depends_on` edge.
- **Why NOT bundled with any other independent story in this batch:** pure
  frontend (`layoutAgents.ts`, `agents-map.css`, `AgentsMapCanvas.tsx`), no
  shared file surface or dependency edge with any of the Skills/Agent-
  Creation/Knowledge-Gap chain. Fully independent — can build and ship in
  parallel with every other sprint in this batch.
- **Sizing estimate:** ~4 tasks, S.

---

## Stories in Scope

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-38-US-01](../UserStories/REQ-SB-38-US-01-agents-map-density-clustering.md) | Agents Map Density Clustering — collapse a crowded Section+Type-ring's overflow agents into a clickable cluster marker | P1 | Ready |

**Tasks in scope** (dependency order): `T01` (layoutAgents.ts clustering
grouping, `depends_on: []`), `T02` (agents-map.css cluster marker,
`depends_on: []`) → `T03` (cluster drill-down component, `depends_on:
[T01]`) → `T04` (AgentsMapCanvas.tsx cluster wiring, `depends_on: [T01, T02,
T03]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None.

---

## Out of Scope

- Everything else in this batch — no real relationship.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — n/a, no architectural fact changed this pass (architect's own pass already recorded everything at `/plan-tasks`; coder pass introduced no new tool/framework/structural boundary)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — n/a, no new ADR this sprint
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md`

---

## Retrospective

### Sizing accuracy

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S — task count matched
  exactly; `T04` was correctly the heaviest, not in code volume but in a
  genuine, only-discoverable-at-integration-time gap (see below) plus the
  live-clustering verification needing real test-agent creation/cleanup
  against the real backend.

### What worked

- **Running the task's own literal Tests-block scenarios against the REAL
  code, every time, at every layer** — `layoutAgents()` directly via
  Node's own built-in TS type-stripping (`T01`), the real `ClusterDrilldown`
  component via a real CDP-driven headless browser hitting the real dev
  server (`T03`), and the fully-wired `AgentsMapCanvas` against 8 real
  agents created live through `POST /agents` (`T04`) — caught the `T04`
  full-drilldown gap for real, not hypothetically, before marking anything
  `Done`.
- **`(sectionId, agentType)` grouping structurally guaranteeing Scenario
  4/AC-04** (a cluster marker can never mix Types, by construction, not by
  an added runtime check) held up exactly as the architect's own pass
  predicted — zero extra defensive code needed.
- **Reusing the exact `data-*`/`useState`/`transitionend`-gated-mount
  pattern `BUGFIX-02-US-01` already established for the Section-Hub
  click-to-zoom mechanism**, widened (not duplicated) to also carry a
  cluster's own distinct target id, kept `T04`'s wiring small and low-risk
  despite the added complexity.
- **Creating real, disposable test agents via the app's own live `POST
  /agents` endpoint, then fully reverting the two persisted JSON state
  files afterward** — genuinely exercised 7+ same-ring agents clustering
  live (not simulated), left zero trace once cleaned up (confirmed via a
  fresh `GET /agents`).

### What didn't work

- **The task-authoring pass did not anticipate that `T01`'s own locked
  `mapAgents` reduction would break `SectionDrilldown`'s existing
  full-agent-list dependency** — none of the four tasks' own declared
  `## Files to Modify` listed `src/frontend/src/pages/AgentsMapPage.tsx`,
  yet completing `T04` at all (not just the AC-06 edge case) structurally
  required threading `layout.clusters` (and, for AC-06's own "must not
  narrow" Constraint, a genuinely unreduced agent list) through that page.
  This only became visible at integration time, not from reading any
  single task in isolation.

### Patterns to carry forward

- **When a task's own Objective is only achievable by touching a file one
  layer up the component tree that no task declared, and the fix is a
  mechanical, same-pattern extension of that file's own already-
  established state-then-pass-through shape (zero new business logic, no
  new interface with any consumer outside the one caller) — implement it,
  log it explicitly as a scope-internal judgement call, and flag the
  task's own gate for human spot-check, rather than either silently
  expanding scope unflagged or blocking a fully-specified, already-locked
  story on a plumbing-only gap.** Extends `SPRINT-021`'s own "mechanical,
  zero-judgement port of already-approved design" precedent from a
  same-file CSS port to a one-layer-up prop-threading case. Found live,
  `REQ-SB-38-US-01-T04`.
- **When a locked AC's own Constraint says "must not narrow existing
  behavior," verify that specific claim live BEFORE assuming the
  straightforward wiring is sufficient** — the AC-06 full-drilldown check
  is what surfaced the `mapAgents`-reduction gap concretely; reading the
  code alone made it look like a one-file task.

### Antipatterns to avoid

- **A decomposer's per-task `## Files to Modify` list, even when each
  task's own logic is individually correct and each task passes its own
  named tests in isolation, can still miss a cross-file integration
  consequence of an earlier, already-`Done`, already-frozen task's own
  locked design choice** — worth an explicit "does this task's own change
  alter what data flows through to an unlisted, up-the-tree caller"
  question during future decomposition passes for any task that
  deliberately *reduces* a shared data shape (as `T01` did to `mapAgents`)
  ahead of a later task that *reuses* the old, larger shape (as `T04`'s
  own `SectionDrilldown` reuse did) — not specific to this sprint, likely
  to recur wherever the same "overview shows less than everything, but a
  drill-down still needs everything" shape appears again.

### Open follow-ups

- **Human spot-check the `AgentsMapPage.tsx` judgement call** (`T04`'s own
  Implementation Log + this story's Notes) — confirm the
  `clusters`/`fullAgents` state-and-prop addition is an acceptable
  resolution, or direct a different shape if not.
- Every genuinely-deferred item from the story's own Non-Goals remains
  open and untouched by this sprint: `layoutSectionDrilldown`'s own
  full-360° view staying unclustered even at high counts; live/dynamic
  recount as `REQ-SB-37` Agent Creation matures; a computed
  node-size-vs-arc-length dynamic threshold in place of the fixed
  `VISIBLE_SLOT_CAP = 6`.

---

## Notes

**Sprint assembled 2026-08-13 (`/plan-sprints`).**

**Gate: `gate: clear` 2026-08-13.** No MUST-FLAG trigger fires: (1) no
material assumption — zero cross-story deps confirmed directly off real task
frontmatter; (2) `REQ-SB-38` is finalized PRD text; (3) product-owner does
not write ADRs; (4) no new `ESCALATIONS.md` entry; (5) not oversized (4
tasks, S); not a blocked story; no cross-sprint dependency needed; (6) N/A;
(7) no contradictory inputs; (8) not ambiguous — fully independent, no
genuine alternative grouping exists. Advances `Draft → Ready`.

**Coder pass, 2026-08-14 (`/implement-sprint`).** All 4 tasks built,
live-verified, and marked `Done` in dependency order; the one story in
scope (`REQ-SB-38-US-01`) is `Done`, all 6 locked ACs verified for real.
`gate: flagged` — not for a hard escalation, but because `T04` made one
disclosed scope-internal judgement call (touched
`src/frontend/src/pages/AgentsMapPage.tsx`, outside every task's own
declared `## Files to Modify`, to thread `layout.clusters` and a genuinely
unreduced agent list down to `AgentsMapCanvas` — see `T04`'s own
Implementation Log and this file's own Retrospective for the full
reasoning). Retrospective drafted below per Pipeline.md's sprint-wrap
protocol; awaiting human read-through to propagate into
`Implementation/Learnings.md`.
