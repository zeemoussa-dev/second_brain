---
id: SPRINT-031
title: Extend the working-mode gate to Skills + migrate mutating Actions
status: Done
gate: flagged
gate_reason: "retro-harvest + a live-discovered, disclosed finding (unrelated stray dev-server process), see REVIEW-QUEUE.md"
phase: P1
depends_on_sprints: [SPRINT-030]
sizing_estimate: "~4 tasks, S"
created: 2026-08-13
started: "2026-08-14"
completed: "2026-08-14"
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-031 — Extend the working-mode gate to Skills + migrate mutating Actions

## Sprint Goal

Extend the existing Autonomous/Supervised/Manual working-mode approval gate
to cover `invoke_skill`, and migrate every existing mutating Action onto the
unified Skills model, preserving today's real/honest-unavailable split
exactly.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-39-US-02` is the only story
  here. Its 4 tasks form one straight internal chain (`T01 → T02 → T03 → T04`)
  plus a hard cross-story dependency on `REQ-SB-39-US-01`: `T01`
  (`depends_on: [REQ-SB-39-US-01-T01, REQ-SB-39-US-01-T02]`), `T03`
  (same two edges), `T04` (`depends_on: [..., REQ-SB-39-US-01-T05]`).
- **Why NOT merged into `SPRINT-030`:** would produce a 13-task sprint, past
  every prior sprint's own `L` ceiling (9 tasks, `SPRINT-021`); both stories
  also share the same two files (`skill_registry.py`, `skill_tools.py`), so
  keeping this pass in its own sprint (ordered after `SPRINT-030` via
  `depends_on_sprints`) minimizes same-sprint file-collision risk rather than
  stacking two full passes over the same files into one working context.
- **Sizing estimate:** ~4 tasks, S.

---

## Stories in Scope

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-39-US-02](../UserStories/REQ-SB-39-US-02-unify-capabilities-working-mode-gate-and-mutating-migration.md) | Extend the working-mode approval gate to Skills, and migrate every existing mutating Action to a Skill | P1 | Ready |

**Tasks in scope** (dependency order): `T01` (skill_registry.py two-axis
gate + `_dispatch_skill` primitive, `depends_on: [REQ-SB-39-US-01-T01,
REQ-SB-39-US-01-T02]`) → `T02` (pending_approvals_router.py skill branch,
`depends_on: [T01]`) → `T03` (migrate the 4 mutating Actions to Skills,
`depends_on: [T01, T02, REQ-SB-39-US-01-T01, REQ-SB-39-US-01-T02]`) → `T04`
(migration-grant retrofit seed, `depends_on: [T03, REQ-SB-39-US-01-T05]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-030` (`REQ-SB-39-US-01` must be `Done`
  first — every task here has a real cross-story edge into it).

---

## Out of Scope

- The capability model + read-only migration itself (`SPRINT-030`).
- Every downstream story that composes with this one (`REQ-SB-37-US-02/03`)
  — scheduled in their own sprints, ordered after this one.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (no change needed this sprint — already updated at `/plan-tasks` step 1 per `ADR-029`)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (`ADR-029`, already recorded at `/plan-tasks`; not re-touched by the coder)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md`

---

## Retrospective

### Sizing accuracy

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S in code volume/task
  count (matched exactly, no task split/dropped/merged), but the real
  verification cost was well outside the "S" envelope — one single manual
  test step (a real, unattended, on-demand `run_capture_now` invocation
  against a large real Meetings backlog) took several real-world hours of
  wall-clock time to complete, dominating the entire sprint's build time.

### What worked

- **Splitting the operator's own single highest-risk check out of the
  long real-capture round trip, and verifying it independently first** —
  the gate check (`Supervised` + a real migrated mutating Skill → Pending
  Approval, not immediate execution) happens strictly BEFORE any handler
  dispatch, so it was provable in 0.008s against a different agent
  (`meeting-capture`) without waiting on the much slower, already-in-flight
  real capture test for `email-capture`. This produced a fast, clean,
  unambiguous confirmation of the sprint's single most safety-critical
  property long before the slower end-to-end test finished, and meant the
  sprint's real risk was never actually blocked on the slow verification.
- **Composing evidence from already-independently-proven mechanisms
  instead of re-proving everything from scratch every time** — `T02`'s
  own synthetic-skill test already proved the Approve→`_dispatch_skill`
  dispatch is generic (a plain dict lookup by `skill_id` string, zero
  per-skill branching); `T03` only needed to prove the REAL
  `run_capture_now` handler itself behaves correctly, not re-verify the
  generic dispatch mechanism a second time.
- **Live CPU-accumulation + active-TCP-connection checks as a genuine
  "still working, not hung" control**, reconfirmed a further time
  (`SPRINT-021`/`022`/`027`'s own precedent) — used repeatedly across a
  multi-hour real background run to distinguish real, bounded progress
  from a true hang, without ever needing to kill and restart.
- **Backing up, then restoring, real production state (`agent_skills.json`)
  around a deliberate clean-slate test** — the exact `REQ-SB-39-US-01-T05`
  protocol reused unchanged a second time, including correctly identifying
  which grants were real, pre-existing production data (`vault-qa`'s
  `web-research`) vs. which were the task's own intended, permanent output
  (the 4 new seed grants) — no real data was lost.

### What didn't work

- **No advance sizing signal existed for "this task's own mandated live
  verification step will run against a real, much-larger-than-expected
  historical backlog"** — `T03`'s own Tests block correctly named "confirm
  it runs the REAL capture pipeline" as a manual step, but nothing in the
  task, story, or sprint sizing anticipated that the real vault's Meetings
  backlog (processed on-demand for apparently the first time outside the
  app-start scheduler) would take several real-world hours, not the
  ~90s–7min range this project's own prior Learnings entries had already
  documented for a scheduled tick. `SPRINT-021`'s "assume multi-minute
  latency" guidance held for order-of-magnitude but not for this specific,
  much larger case.

### Patterns to carry forward

- **Independently test an operator-named "single highest-risk check" as
  its own small, fast, isolated probe FIRST, using a different agent/
  input than any slower, already-planned end-to-end test** — de-risks the
  sprint's own most safety-critical property immediately, without making
  its confirmation depend on a much slower real-world call succeeding or
  completing in any particular timeframe.
- **When a task's own Tests block names "the real pipeline" as a manual
  verification step and the real pipeline's own scope is unbounded (no
  `limit` parameter, processes an entire real historical backlog), budget
  session time for a potentially multi-hour real run up front** — start it
  backgrounded immediately, verify liveness periodically via CPU/network
  checks rather than blind waiting, and use the wait time productively
  (build the next task's code, run independent probes that don't touch the
  same shared state).

### Antipatterns to avoid

- **Assuming an "S"-sized task's own real-world verification cost scales
  with its code volume** — this sprint's actual code diff was genuinely
  small (a gate insertion, a dispatch-table extension, 4 new stub/real
  handlers, a dict extension), but one single mandated live check
  dominated the sprint's real wall-clock cost by orders of magnitude. Flag
  this explicitly in future sizing estimates whenever a task's own Tests
  block names an unbounded, on-demand real-pipeline invocation as its
  verification method.
- **Not proactively checking for a stray, already-running dev-server
  process sharing the same real vault/working-mode state BEFORE starting
  a live Supervised-mode test** — this project's own `SPRINT-022`/
  `SPRINT-028`/`SPRINT-029` Learnings entries already establish "a shared
  dev vault can carry real concurrent-session drift"; this sprint's own
  live test window collided with a real, unattended background-scheduler
  tick from a stray process that had been running since before the
  session started. A quick `Get-NetTCPConnection -LocalPort 8000,8001` at
  the START of live verification (not discovered mid-test as a surprising
  extra pending-approval record) would have surfaced this proactively.

### Open follow-ups

- **Human decision needed on the real, still-`pending` `background`-
  triggered `email-capture` proposal** left in the queue by the
  live-discovered stray dev-server tick (approve or decline — both are
  safe; see `REVIEW-QUEUE.md`).
- **Human decision needed on whether to stop the stray dev-server process**
  found listening on `localhost:8000` (real, unattended, already-running
  production-identical code — not a bug, but worth a deliberate decision).
- **Consider a sizing-estimate convention** for any future task whose
  Tests block names an unbounded, on-demand full-pipeline real invocation
  as its verification method — flag it explicitly as a wall-clock-risk
  item distinct from code-volume sizing, so a future sprint's own
  real-time budget accounts for it up front rather than being discovered
  live.

---

## Notes

**Sprint assembled 2026-08-13 (`/plan-sprints`).** `depends_on_sprints:
[SPRINT-030]` is a direct mirror of real task-level `depends_on` edges
already recorded by the decomposer — not an invented dependency.

**Gate: `gate: clear` 2026-08-13.** No MUST-FLAG trigger fires: (1) no
material assumption; (2) `REQ-SB-39` is finalized PRD text; (3) product-owner
does not write ADRs; (4) no new `ESCALATIONS.md` entry; (5) not oversized (4
tasks, S); not a blocked story; the one cross-sprint dependency recorded here
mirrors the decomposer's own real task edges exactly, not a fresh dependency
this pass had to invent; (6) N/A; (7) no contradictory inputs; (8) not
ambiguous — the only genuine choice (merge into `SPRINT-030` vs. split) was
resolved against this project's own established sizing ceiling, not a coin
flip. Advances `Draft → Ready`.

**Update, 2026-08-14 (`/implement-sprint SPRINT-031` — coder).** All 4
tasks built and verified live in dependency order (`T01 → T02 → T03 →
T04`); all 8 locked ACs across the sprint's one story confirmed. The
operator's own explicitly-named single highest-risk check (a real
migrated mutating Skill under Supervised mode creates a real Pending
Approval, never executing immediately) confirmed live. `status: Ready →
Done`; `gate: flagged` — retro-harvest (standard) plus one live-discovered,
disclosed finding (an unrelated, already-running stray dev-server process
independently created its own real background-triggered pending-approval
record during live testing; not a defect in this sprint's own code — see
`REVIEW-QUEUE.md` and `REQ-SB-39-US-02-T03`'s own Implementation Log).
Nothing about this finding weakens or contradicts any locked AC.
