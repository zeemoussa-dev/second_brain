---
id: SPRINT-039
title: Real-time agent activity pulses — SSE-pushed glow, Hub-routed traveling pulse, pending-approval highlight
status: Ready                      # Draft | Ready | In Progress | Blocked | Done
gate: clear                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: ""                    # the MUST-FLAG trigger that fired, when gate: flagged
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~8 tasks, L"      # effort estimate; checked vs actual in retro
created: 2026-08-14
started: ""                        # YYYY-MM-DD when status → In Progress
completed: ""                      # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-039 — Real-time agent activity pulses

## Sprint Goal

Build `REQ-SB-42-US-01` end to end per `ADR-035`: the ephemeral in-memory
`agent_presence.py` registry, instrumentation at the five real dispatch
call sites (capture/Skill, chat, the two Hub-routing hops, pending-approval),
a new `GET /agent-presence/stream` SSE endpoint, and both Agents Map
surfaces (overview + Section drill-down) rendering the per-agent glow, the
traveling pulse, and the steady pending-approval highlight in real time.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-42-US-01` is the only story
  here. Confirmed independent of `REQ-SB-43-US-01`/`REQ-SB-44-US-01` (this
  same `/plan-sprints` batch's other two stories) by reading its own task
  table directly: every `depends_on` edge is internal to this story
  (`T01 → {T02, T03, T04, T05} → T06 → {T07, T08}`), no cross-story edge to
  either sibling story or to any other Ready, ungrouped story.
- **Why NOT combined with `REQ-SB-43-US-01`** (same phase, same batch): no
  shared architecture scope (`ADR-035` vs. `ADR-036`), no shared file
  surface, no `depends_on` edge either direction. Combining two unrelated
  8/9-task stories would produce a ~17-task sprint, well past this
  project's own observed sizing ceiling (`Implementation/Learnings.md`'s
  largest matched precedent is `SPRINT-021`, 9 tasks/L, estimated-vs-actual
  matched exactly). Kept standalone — bundling unrelated stories purely for
  task-count convenience is not a grouping this project's own sprint
  history uses (see `SPRINT-029`'s identical reasoning for a same-batch,
  unrelated story).
- **Sizing estimate:** ~8 tasks, L. `T01` (registry module, the
  foundation) → `T02`/`T03`/`T04` (independently parallel-buildable
  dispatch-site instrumentation once `T01` lands) and `T05` (the SSE
  endpoint, also depends only on `T01`) → `T06` (frontend `EventSource`
  wrapper) → `T07`/`T08` (overview and drill-down rendering, independently
  parallel-buildable once `T06` lands, jointly owning the bulk of the
  locked ACs — Scenarios 1-6 and 8 — at the screen level). This sizing sits
  just under this project's own largest confirmed-accurate precedent
  (`SPRINT-021`, 9 tasks/L) — not oversized by calibration, kept as one
  story per the story's own "no independent value alone" test (the
  per-agent glow and the Hub-routed traveling pulse share one underlying
  data source).

---

## Stories in Scope

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-42-US-01](../UserStories/REQ-SB-42-US-01-real-time-agent-activity-pulses.md) | Real-time per-agent activity pulses and Hub-routed traveling pulses on the Agents Map overview and Section drill-down, pushed over a real-time channel | P1 | Ready |

**Tasks in scope** (dependency order): `T01` (`agent_presence.py` registry,
`depends_on: []`) → `T02`/`T03`/`T04` (capture+skill+chat instrumentation;
Hub-routed traveling-pulse instrumentation; pending-approval broadcast,
each `depends_on: [T01]`) and `T05` (`GET /agent-presence/stream` SSE
endpoint, `depends_on: [T01]`) → `T06` (frontend `EventSource` client,
`depends_on: [T05]`) → `T07`/`T08` (overview rendering; Section drill-down
rendering, each `depends_on: [T06]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None. This story's own two Done prerequisites
  (`REQ-SB-20-US-01` — Hub routing; `REQ-SB-21-US-01` — pending approvals)
  are already `Done`; no sprint-level edge is needed for already-completed
  work.

---

## Out of Scope

- `REQ-SB-43-US-01`, `REQ-SB-44-US-01` — this same `/plan-sprints` batch's
  other two stories; no dependency relationship to this story (see
  `SPRINT-040`/`SPRINT-041`).

---

## Definition of Done

- [ ] Every story in scope has status `Done`
- [ ] All story-level Definitions of Done satisfied
- [ ] `BACKLOG.md` updated — every affected row reflects current status
- [ ] `architecture.md` updated if the sprint changed an architectural fact
- [ ] Any new ADRs recorded in `ADR.md` with status `Accepted`
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended
- [ ] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

### Sizing accuracy

- **Estimated:** ~8 tasks, L — **Actual:** _(fill in at retro)_

### What worked

-

### What didn't work

-

### Patterns to carry forward

-

### Antipatterns to avoid

-

### Open follow-ups

-

---

## Notes

**Sprint assembled 2026-08-14 (`/plan-sprints`).** `REQ-SB-42-US-01`'s own
`ADR-035` (Server-Sent Events transport, ephemeral in-memory registry) was
approved 2026-08-14; this story enters `/plan-sprints` fully `Ready`,
`gate: clear`.

**Gate: `gate: clear` 2026-08-14.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — the standalone grouping is
read directly off the decomposer's own recorded `depends_on` graph (fully
internal to this story), not guessed; (2) `REQ-SB-42` is not
`<!-- Draft -->`/unfinalised; (3) product-owner does not write ADRs —
`ADR-035` was already reviewed and approved before this pass; (4) no new
`ESCALATIONS.md` entry; (5) not oversized (8 tasks, L, under this project's
own largest confirmed-accurate precedent of 9 tasks/L); not a blocked
story; no cross-sprint dependency introduced (none exists); (6) N/A
(coder-only trigger); (7) no contradictory inputs; (8) not genuinely
ambiguous — confirmed no dependency or shared-architecture-scope overlap
with either other story in this same batch, so no combined-sprint option
was genuinely equally valid. Advances `Draft → Ready`.
