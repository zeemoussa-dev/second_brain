---
id: SPRINT-001
title: Scheduled recurring email capture (hourly + app-start + catch-up)
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: ""                    # the MUST-FLAG trigger that fired, when gate: flagged
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~4 tasks, S"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-10
started: "2026-08-10"               # YYYY-MM-DD when status → In Progress
completed: "2026-08-10"             # YYYY-MM-DD when status → Done
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

# SPRINT-001 — Scheduled recurring email capture (hourly + app-start + catch-up)

## Sprint Goal

Stand up REQ-SB-07's automatic capture scheduling (hourly APScheduler job,
unconditional app-start trigger, missed-run catch-up, and a shared
concurrency guard) on top of the existing manually-triggered email-capture
pipeline.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single-story sprint — `REQ-SB-07-US-01` is the only
  `Ready`, ungrouped story in the project right now. Its four tasks
  (`T01`→`T02`→`T03`→`T04`) form one strict linear `depends_on` chain
  (last-run persistence → business-layer wrapper → concurrency guard →
  scheduler/lifespan wiring) implementing a single cohesive capability
  against one ADR (ADR-005), so there is no partition question to make —
  they cannot be split across sprints without introducing an artificial
  cross-sprint dependency edge in the middle of an acyclic chain that
  clearly belongs together as one unit of work.
- **Sizing estimate:** ~4 tasks, S (small). All four are single-file-or-
  single-package backend changes (`data_access/vault_writer.py`
  additions; one `business/` function; one new `scheduling/` package;
  lifespan wiring in `main.py` + `requirements.txt`), each already scoped
  tightly enough by the decomposer to fit comfortably in one working
  session. **No sizing precedent exists yet** — this is the first sprint
  ever created in this project, so there is no prior actual-vs-estimate
  history in `Implementation/Learnings.md` to calibrate against (its one
  entry is a book-reference note explicitly flagged as not sprint-retro
  history). This estimate is a first-principles judgement call based on
  task count and scope, not a calibrated one; the retro at the end of this
  sprint will be the first real data point for future sizing.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-001 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-07-US-01](../UserStories/REQ-SB-07-US-01-scheduled-recurring-capture.md) | Scheduled recurring capture with app-start and missed-run catch-up | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None — first sprint in the project.
- The story itself carries `gate: flagged` (ADR-005 pending human review,
  logged in `REVIEW-QUEUE.md` under `REQ-SB-07-US-01`, dated 2026-08-10).
  That flag is orthogonal to this sprint's grouping decision (which is
  unambiguous — only one eligible story exists) and does not block
  `/plan-sprints` from grouping it; it does mean a human should clear the
  ADR-005 review before `/implement-sprint` starts building against this
  sprint, per the pipeline's normal flagged-item handling. No new
  REVIEW-QUEUE or ESCALATIONS entry was written by this pass — the
  existing one is left as-is.

---

## Out of Scope

- REQ-SB-08 (Meetings Capture Pipeline) and REQ-SB-09 (To-Do Task Capture
  Pipeline) — both not yet specced; they are expected to reuse this
  sprint's scheduler later, per the story's own Non-Goals, but are not
  part of this sprint.
- REQ-SB-11 (Agent Activity & Error Observability) — the future UI over
  capture-run history; not specced, not part of this sprint.
- Any change to the existing manual `POST /poc/classify-emails` endpoint —
  explicitly untouched by every task in this sprint.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — Tech Stack, Source Layout, Local Development (architect pass)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — ADR-005
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

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S, zero rework or splitting
  — **Takeaway:** matched exactly. First real data point for this project's
  sizing (the estimate itself was explicitly flagged as a first-principles
  guess with no precedent to calibrate against — it held up here, but one
  sprint is not enough to trust the calibration yet).

### What worked

- **Decomposer writing literal code in task files, not just prose specs** —
  every task's `## Files to Modify` contained the exact function/code to
  add. The coder's job on each task was closer to "implement exactly this,
  then verify" than "figure out how to satisfy this AC" — fast, low
  ambiguity, no scope drift across 4 tasks and 3 different agents.
- **Verifying against the real live integration instead of mocks** — every
  task's manual verification ran against the actual running Outlook desktop
  and the real Compass API, catching real behavior (timing, actual note
  writes, actual scheduler registration) rather than mocked approximations.
  Cheap here because the integration already existed and worked from the
  earlier POC.
- **`gate: flagged` not blocking forward pipeline progress** — the architect
  flagged the story for ADR-005 review, but the decomposer, product-owner,
  and (once the operator approved) the coder all proceeded without the flag
  stalling anything. Worked exactly as `Implementation/Pipeline.md` designs
  it: gate is a "a human should look" signal, not a hard blocker.
- **Strict linear `depends_on` chain** (T01→T02→T03→T04) made the build
  loop trivial — no scheduling/ordering decisions, no fan-out to reason
  about.

### What didn't work

- **`BACKLOG.md`'s Story Status cell drifted from the story file's actual
  `status:`** after the decomposer's pass (cell stayed `Draft` while the
  story was already `Ready`) — caught and fixed manually, but nothing in
  the pipeline currently guarantees that column stays in sync outside of
  the specific checkpoints each role's contract names. Worth a process
  note, not a code fix.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Literal code in decomposer-authored tasks** — when the architecture is
  concrete enough (an ADR with real function signatures), have the
  decomposer write the actual code into the task, not just a description of
  what's needed. Cuts coder ambiguity and rework to near zero.
- **Verify against the real integration when it's cheap and already
  working** — don't build mocks/stubs for a manual-verification-mode task
  if the real dependency (Outlook, Compass, the vault) is already reachable
  and low-cost to exercise once per task.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Assuming `BACKLOG.md`'s Story/Sprint Status cells auto-stay in sync** —
  they don't, outside the specific moments each role's contract updates
  them. Spot-check `BACKLOG.md` against the actual story/sprint `status:`
  values at sprint wrap, don't just trust the last agent's report.

### Open follow-ups

- REQ-SB-08 (Meetings) and REQ-SB-09 (Tasks) are expected to reuse
  `app/scheduling/`'s scheduler — generalizing it (currently hardcoded to
  the one email capture job) is real, not-yet-scoped work for those
  stories' own `/plan-tasks` passes, not decided here.
- Every dev-server restart now fires a real capture run (see `MEMORY.md`)
  — worth revisiting once more scheduled pipelines exist, since the
  side-effect cost (API calls, potential vault writes) compounds per
  pipeline per restart.

---

## Notes

gate: clear 2026-08-10 — no triggers fired for the grouping decision itself:
only one `Ready`, ungrouped story exists (`REQ-SB-07-US-01`), so the
partition is unambiguous (no equally-valid alternative grouping), it is not
oversized (4 small tasks against one ADR), it is not blocked (its own tasks
are all `status: Ready`), and no cross-sprint dependency was introduced
(`depends_on_sprints: []`, single-phase P1, single story). Advanced
`Draft → Ready`. This does not clear the story's own pre-existing
`gate: flagged` (ADR-005 review) — that flag is the decomposer/architect's
concern, not a grouping-ambiguity flag, and is left untouched in
`REVIEW-QUEUE.md`.

---

**Sprint wrap (2026-08-10):** All 4 tasks across the sprint's one story
`Done`, all 5 locked ACs verified live, nothing blocked. `status: Done`,
`completed: 2026-08-10`. `gate: flagged` (not clear) per this role's
sprint-wrap contract — the Retrospective above is a **draft**; a human
should skim it and propagate "Patterns to carry forward" / "Antipatterns to
avoid" into `Implementation/Learnings.md` (this sprint's own coder does not
write Learnings.md directly).
