---
id: REQ-SB-38-US-01-T01
title: layoutAgents.ts — VISIBLE_SLOT_CAP + per-(Section x Type-ring) clustering grouping
parent_story: REQ-SB-38-US-01
requirement_id: REQ-SB-38
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-38-US-01-T01 — layoutAgents.ts — VISIBLE_SLOT_CAP + per-(Section x Type-ring) clustering grouping

## Parent Story

- Story: [[REQ-SB-38-US-01]] — `../UserStories/REQ-SB-38-US-01-agents-map-density-clustering.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-38 *Agents Map Density Clustering*

---

## Objective

Add a new `VISIBLE_SLOT_CAP = 6` constant to `layoutAgents.ts`, sibling to
the existing `SECTION_ARC_SPAN_DEG_CAP`/`SECTION_ARC_SPAN_FRACTION`, and
group agents by `(sectionId, agentType)` — not `sectionId` alone — ahead of
the existing fan-out math, so any group with more than 6 agents collapses
its overflow into a single cluster-marker descriptor instead of rendering
every agent individually.

---

## Starting State → End State

**Before / Inputs:**
- `layoutAgents.ts`'s `layoutAgents()` returns `{ sections, mapAgents }`,
  where `mapAgents` fans out every agent in a Section across
  `sectionArcSpanDeg`, regardless of how many share the same Type-ring.
- `polarLayout.ts`'s `RING_RADIUS` already keys an agent's radius to its own
  `type` (`worker`/`expert`/`producer`) — confirmed by direct read: a
  Section's agents only ever visually crowd within one Type-ring, never
  across rings.

**After / Outputs:**
- `layoutAgents()`'s return shape gains a third field (e.g. `clusters:
  ClusterMarker[]`) — one entry per `(sectionId, agentType)` group whose
  agent count exceeds `VISIBLE_SLOT_CAP` (6). Each entry carries at least:
  the section id, the agent type, the fan-slot angle for the marker's own
  position (the group's last fan slot, matching today's existing
  `sectionArcSpanDeg` spacing convention), a count of overflow agents, and
  the list of agent ids the marker represents.
- `mapAgents` no longer includes the overflow agents for a clustered group —
  only the first `VISIBLE_SLOT_CAP - 1` (5) agents of that group (existing
  sort/index order), still rendered exactly as today via `AgentNode`.
- A group at or under `VISIBLE_SLOT_CAP` produces no cluster entry — every
  one of its agents stays in `mapAgents`, unchanged from today's behavior.
- A cluster's marker angle reuses the same `section.hubAngleDeg + offset`
  computation the group's own last fan slot would have used — no new
  angular-placement logic, just a different terminal element for that slot.

---

## Files to Modify

- `src/frontend/src/features/agents-map/layoutAgents.ts` — add
  `VISIBLE_SLOT_CAP`, group `agentsBySection`'s existing per-section list by
  `agent.type` before the existing `sectionAgents.forEach` fan-out loop, cap
  each `(sectionId, type)` group's individually-rendered agents at
  `VISIBLE_SLOT_CAP - 1` when the group exceeds the cap, and emit one
  cluster descriptor per capped group. Export whatever new type(s) the
  cluster descriptor needs (e.g. `ClusterMarker`) alongside the existing
  `SectionSummary`/`AgentMapLayout` exports.

---

## Constraints

- Inherits from parent story: a cluster marker must never represent agents
  of more than one Type (Scenario 4) — grouping by `(sectionId, agentType)`,
  not `sectionId` alone, must guarantee this by construction, not by an
  added runtime check.
- `polarLayout.ts` is read-only reference (`RING_RADIUS`) — no change
  expected or permitted in this task.
- `layoutSectionDrilldown()` (same file) is out of scope for this task —
  untouched, reused as-is by `T03`.
- Do not change `SECTION_ARC_SPAN_DEG_CAP`/`SECTION_ARC_SPAN_FRACTION` or
  the existing per-agent angle computation for non-clustered agents —
  additive change only.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-38-US-01-AC-01] Call `layoutAgents()` with a synthetic
   `AgentSummary[]` containing 15 agents sharing one `section_id` and one
   `type`. Expect `mapAgents` to contain exactly 5 individually-placed
   agents for that `(sectionId, type)` group, and `clusters` to contain
   exactly one entry for that group with `count === 10` and an
   `agentIds`/equivalent list of the remaining 10 agent ids.
2. [REQ-SB-38-US-01-AC-04] Call `layoutAgents()` with a synthetic dataset
   where one Section has 8 `worker`-type agents and 3 `expert`-type agents.
   Expect two independent groups: the `worker` group produces one cluster
   entry (8 > 6) whose `agentIds` are all `worker` agents only; the `expert`
   group (3 <= 6) produces no cluster entry. Confirm no cluster entry's
   `agentIds` ever mixes agents of different `type`.
3. [REQ-SB-38-US-01-AC-05] Call `layoutAgents()` with a synthetic Section
   whose every `(sectionId, type)` group has 6 or fewer agents (e.g. 4
   `worker`, 5 `expert`, 2 `producer`). Expect `clusters` to be empty and
   `mapAgents` to contain every one of those agents individually, matching
   today's pre-clustering output shape.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `VISIBLE_SLOT_CAP = 6` added as a sibling constant to
      `SECTION_ARC_SPAN_DEG_CAP`/`SECTION_ARC_SPAN_FRACTION`
- [x] Agents are grouped by `(sectionId, agentType)`, not `sectionId` alone,
      before the cap is applied
- [x] A group over the cap emits exactly one cluster descriptor (count +
      represented agent ids) and keeps only its first 5 agents in
      `mapAgents`
- [x] A group at or under the cap emits no cluster descriptor and keeps
      every agent in `mapAgents`, unchanged from today
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Rendering the cluster marker in the DOM — `T04`.
- The cluster-scoped drill-down view — `T03`.
- `.map-overflow-marker` CSS — `T02`.

---

## Context / Notes

Foundation task — every other task in this story consumes this function's
new `clusters` output. No dependencies; can start immediately alongside
`T02`. See `Implementation/Architecture/architecture.md` → "Agents Map —
Density Clustering (REQ-SB-38-US-01)" for the full reasoning on why
`(sectionId, agentType)` is the correct grouping key (it structurally
guarantees Scenario 4, not by an added check).

---

## Implementation Log

**2026-08-14 — coder.** Added `VISIBLE_SLOT_CAP = 6` (sibling constant to
`SECTION_ARC_SPAN_DEG_CAP`/`SECTION_ARC_SPAN_FRACTION`). `layoutAgents()`'s
per-section loop now groups `sectionAgents` by `agent.type` into a
`Map<AgentType, AgentSummary[]>` before the fan-out; for a group with
`count > VISIBLE_SLOT_CAP`, only its first `VISIBLE_SLOT_CAP - 1` (5) agents
(existing sort/index order) go into `mapAgents`, and one `ClusterMarker` is
pushed (`count`/`agentIds` = the remaining overflow) at the angle the
group's own last fan slot would have used (same `sectionArcSpanDeg` offset
formula, unchanged — only its `count`/`index` inputs are now scoped to the
`(sectionId, agentType)` group instead of the whole Section, which the
Objective's own "group ahead of the existing fan-out math" instruction
requires; this cannot change visible crowding since different Types render
on different `RING_RADIUS` rings per `polarLayout.ts`, confirmed by direct
read — logged here as a scope-internal judgement call for human spot-check,
not a deviation from a locked AC). A group at/under the cap is unaffected —
every agent still pushed to `mapAgents` individually. New `ClusterMarker`
export (`id`, `sectionId`, `type`, `angleDeg`, `count`, `agentIds`);
`AgentMapLayout` gains a `clusters: ClusterMarker[]` field.
`polarLayout.ts`/`layoutSectionDrilldown()` untouched.

**Verification (manual mode — `n/a: test tooling pending` per Tests
block).** Ran the task's own three literal Tests-block scenarios by
importing the REAL `layoutAgents.ts` directly (Node 24's built-in TS
type-stripping, `node <harness>.mjs`, no transpile/mock step) — script at
`C:\Users\...\scratchpad\verify-layoutAgents-T01.mjs` (throwaway, not
committed):

- **AC-01** (15 same-section/same-type agents): `mapAgents` contained
  exactly 5 individually-placed agents for the group; `clusters` contained
  exactly 1 entry, `count === 10`, `agentIds.length === 10`, zero overlap
  between the 5 visible ids and the 10 clustered ids. **PASS.**
- **AC-04** (8 `worker` + 3 `expert` in one Section): exactly 1 cluster
  entry, `type === 'worker'`, its `agentIds` resolved to a single distinct
  type (`worker`) with zero `expert` ids mixed in; all 3 `expert` agents
  rendered individually (no cluster for that group). **PASS.**
- **AC-05** (4 `worker` + 5 `expert` + 2 `producer`, all `<= 6`): `clusters`
  was empty; `mapAgents` contained all 11 agents individually. **PASS.**

Full real console output captured; all three scenarios matched expectation
exactly on first run, no fix cycle needed.

gate: clear 2026-08-14 — no MUST-FLAG trigger fired. One scope-internal
judgement call logged above (per-group vs. whole-Section `count`/`index`
inputs to the unchanged offset formula) for human spot-check.
