---
id: SPRINT-044
title: Background Agents — explicit opt-in flag, excluded from Hub-routing and Cockpit addressing, displayed separately
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "retro-harvest — human to skim retro and propagate patterns to Implementation/Learnings.md"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, M"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-14
started: "2026-08-14"               # YYYY-MM-DD when status → In Progress
completed: "2026-08-14"             # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-044 — Background Agents

## Sprint Goal

Build `REQ-SB-51-US-01` end to end: a new `is_background_agent` flag
(self-healing registry, backfilled for the 3 real capture-pipeline
Workers), excluded from Hub-routing candidacy and the Cockpit's Available
Agents bring-in list, and displayed in a new, separate "Background Agents"
rail on the Agents Map instead of the Section/ring layout — while staying
fully reachable and usable directly by the user.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-51-US-01` is the only
  story here. Its 6 tasks form one confirmed-acyclic dependency graph
  (`T01 → {T02, T03} → T04 → T05 → T06`) with no cross-story `depends_on`
  edge to any other Ready, ungrouped story in this batch — the story's own
  Dependencies section explicitly confirms it is "not blocked by,
  explicitly" `REQ-SB-49-US-01` or `REQ-SB-46`, and composes only with
  already-`Done` surfaces (`REQ-SB-20-US-01`, `REQ-SB-43-US-01`/
  `REQ-SB-44-US-01`, `REQ-SB-38-US-01`).
- **Why NOT combined with `REQ-SB-47-US-01`** (the other story in this
  batch touching agent-registry-adjacent files): no shared architecture
  scope, no `depends_on` edge either direction, and each is independently
  a full M-sized sprint (6 tasks) on its own — combining would produce a
  12-task sprint spanning two structurally unrelated concerns (an
  addressing-exclusion flag vs. a scheduler + shared dispatch lock),
  pushing past this project's own observed sizing ceiling (L ≈ 9 tasks)
  for no cohesion benefit.
- **Sizing estimate:** ~6 tasks, M — matches this project's own repeated
  precedent for a registry-module-plus-two-consumer-layers shape
  (`SPRINT-020`, `SPRINT-022`, `SPRINT-028`, all "~6 tasks, M").

---

## Stories in Scope

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-51-US-01](../UserStories/REQ-SB-51-US-01-background-agents-excluded-from-addressing.md) | Background Agents — explicit opt-in flag, excluded from Hub-routing and Cockpit addressing, displayed separately | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None
- No external blockers. A soft, same-source (not a hard `depends_on`)
  coordination note exists with `REQ-SB-49-US-01` (`SPRINT-046`): both read
  the same `fetchAgentList()`-sourced candidate list, so whichever of the
  two lands second may need a small, same-file follow-on edit to repoint
  its own source at the other's filtered variable — named explicitly in
  both stories' own architecture passes, not a blocking edge, and not
  sequenced via `depends_on_sprints` here since either build order works.

---

## Out of Scope

- Setting `is_background_agent` from the Agent Creation Wizard — deferred
  to a future story once `REQ-SB-46` lands (story's own Non-Goals).
- The Wizard's own Step 4 "Agent" Trigger option — unrelated, independent
  metadata field.
- `REQ-SB-49-US-01`'s own inline `@mention` suggestion UI — this sprint
  only guarantees the shared source it will read from is already filtered.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (no change needed — architect's own Notes already fully described the design at `/plan-tasks`, no drift found)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (none — ordinary CRUD-pattern extension, no new ADR per the architect's own reasoning)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks, M — matched exactly.
  No task was split, dropped, or merged. `T06` (the widest fan-in,
  deliberately last) was correctly the heaviest by real verification
  effort, not code volume — its own `AC-09` full-stack restoration check
  exercised every other task's real, already-built code in one
  continuous live session, as the decomposer's own reasoning predicted.

### What worked

- The 3 real capture-pipeline Workers being backfilled to
  `is_background_agent: True` at `T01` (before any HTTP/frontend work
  existed) meant every later task's own live verification against
  `email-capture`/`meeting-capture`/`todo-capture` needed zero manual
  setup step — the backfill itself was the fixture.
- Mirroring `working_mode_registry.py`'s exact shape one file over
  (self-healing default folded into `_load_state()`, pure-I/O
  `vault_writer.py` pair) meant zero new persistence pattern to design
  or debug — the only real decision was the non-uniform default (a
  literal 3-id exception set vs. one fixed constant), which was already
  named explicitly by the architect.
- Using the real, already-running Vite dev server's own process to
  locate a working `node.exe`/`tsc` (no `npx` on `PATH`, a now
  4th-confirmed instance of this project's own standing antipattern)
  kept a genuine `tsc -b --noEmit` compile check in the loop for every
  frontend task, rather than skipping it.

### What didn't work

- An initial CDP read of the new Background Agents rail, immediately
  after `Page.navigate` with only a fixed ~3s wait, produced a
  false-negative empty rail — the page's own two chained `fetch` calls
  plus `layoutAgents()` computation hadn't resolved yet. A
  `Console`/`Runtime.exceptionThrown` listener confirmed no real error;
  a longer wait (4s+) on the same, otherwise-correct code produced the
  right result on the next attempt. Root cause: an initial page-load
  data-fetch race, not a dispatched-interaction race — a new variant of
  this project's own already-documented "wait after a CDP-dispatched
  state change" precedent (`SPRINT-036`), now confirmed to extend to
  initial mount-time async data loading too.
- A stray, non-`--reload` uvicorn process (from an unrelated earlier
  session) was already listening on port 8001 before this sprint's own
  verification began — killed and replaced with a single,
  explicitly-controlled `--reload` instance per this project's own
  standing anti-stray-process precedent (now confirmed a further,
  Nth time).

### Patterns to carry forward

- **Backfill-before-build** — when a story's own Scenario 2 (or
  equivalent) requires N real, already-shipped entities to already carry
  a new field's non-default value, build that backfill in the very first
  task, before any consuming layer exists. Every later task's live
  verification then gets its fixture data for free, with zero manual
  setup step repeated across 5 more tasks.
- **Wait after ANY CDP page navigation that triggers async data
  fetching, not just after a dispatched interaction** — extends the
  already-documented "wait after a state-changing click" precedent one
  layer earlier, to a page's own mount-time `useEffect`/`fetch` chain.
  A `Console`/`Runtime.exceptionThrown` listener is the fast way to rule
  out a real error before assuming "just needs more time."

### Antipatterns to avoid

- **Trusting a stray dev-server process on the project's own usual
  ports without confirming what it's serving, even briefly** — this is
  now a repeated-Nth-time finding across many prior sprints
  (`SPRINT-021`/`022`/`028`/`029`); still worth naming per-sprint since
  it keeps recurring from genuinely different, unrelated prior sessions,
  not a regression in this project's own code.

### Open follow-ups

- None filed — no `ESCALATIONS.md`/`REVIEW-QUEUE.md` entries this
  sprint (see the story's own Coder-pass Notes for the explicit
  confirmation). The story's own already-named soft coordination note
  with `REQ-SB-49-US-01`/`SPRINT-046` (both reading the same
  `fetchAgentList()`-sourced candidate list) remains live and
  unaffected — `REQ-SB-49-US-01` inherits this sprint's own exclusion
  filter automatically once it ships, per the story's own Constraints;
  no action needed from this sprint's own side regardless of build
  order.
