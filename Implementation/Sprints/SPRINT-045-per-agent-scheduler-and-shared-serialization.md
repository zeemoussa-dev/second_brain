---
id: SPRINT-045
title: Per-Agent Scheduler — Schedule tab (configure/edit/remove/run-now/run history) + shared Outlook-COM dispatch lock
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "carried from REQ-SB-47-US-01 (ADR-037 human review + retroactive Schedule-tab design sign-off, no /design pass run — see REVIEW-QUEUE.md/ESC-033); plus one in-scope live-discovered-and-fixed defect flagged for spot-check (T02)."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, M"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-14
started: "2026-08-14"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-14"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-045 — Per-Agent Scheduler + Shared Outlook-COM Serialization

## Sprint Goal

Build `REQ-SB-47-US-01` (merged with `REQ-SB-45`) end to end per `ADR-037`:
a new `agent_schedule_registry.py` (schedule CRUD + shared, in-process
Outlook-COM dispatch lock), `capture_scheduler.py`'s generalization to
register per-agent-capability jobs, a new `"scheduled"` `invoke_skill`
trigger, new schedule CRUD + run-now HTTP endpoints, and a new Schedule tab
on the agent detail panel.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-47-US-01` is the only
  story here. Its 6 tasks form one confirmed-acyclic linear chain
  (`T01 → T02 → T03 → T04 → T05 → T06`), with no `depends_on` edge to any
  other Ready, ungrouped story in this batch — confirmed by direct read of
  all 6 task files.
- **Why NOT combined with `REQ-SB-51-US-01`** (the other story in this
  batch touching agent-registry-adjacent files/`AgentDetailPanel.tsx`): no
  shared architecture scope (`ADR-037` vs. ordinary `ADR-014`/`ADR-018`
  application), no `depends_on` edge either direction, and each is
  independently a full M-sized sprint (6 tasks) on its own — combining
  would produce a 12-task sprint spanning two structurally unrelated
  concerns, past this project's own observed sizing ceiling for no
  cohesion benefit.
- **Sizing estimate:** ~6 tasks, M — matches this project's own repeated
  precedent for a registry-module-plus-router-plus-frontend-tab shape.
- **Story-level `gate: flagged` carried, not re-flagged by this sprint:**
  `REQ-SB-47-US-01` itself stays `gate: flagged` (`ADR-037` human review,
  plus a still-open, recommended-but-not-blocking `/design` pass on the
  net-new Schedule tab UI, both already tracked in `REVIEW-QUEUE.md` /
  `ESC-033`). Per `.claude/agents/product-owner.md`'s own closed list of 4
  sprint-level flag triggers, none fired for this grouping decision — the
  single-story partition is unambiguous, not oversized, not blocked, and
  introduces no cross-sprint dependency. `gate: clear`, advance to
  `Ready` — mirrors `SPRINT-040`'s own precedent (a single-story sprint
  built successfully around a story carrying a freshly-written ADR).

---

## Stories in Scope

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-47-US-01](../UserStories/REQ-SB-47-US-01-per-agent-scheduler-and-shared-serialization.md) | Per-Agent Scheduler + Shared Outlook-COM Serialization (also covers REQ-SB-45) | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None
- **Outstanding, human-owned, not resolved by this pass:** `ADR-037`
  itself still needs human review before the coder builds (`ESC-033`,
  `REVIEW-QUEUE.md`); the Schedule tab's own net-new UI layout has no
  approved `html-prototype/` coverage anywhere — a `/design` pass or an
  explicit operator sign-off to skip one remains recommended before `T06`
  (the frontend task) is built, per the story's own architect-pass Notes.
  Not resolved or duplicated here — already tracked at the story level.

---

## Out of Scope

- A full cron-style schedule expression — interval-only is this story's
  resolved scope.
- Real, non-stub handlers for `pause_schedule`/`rebuild_person_note`, or
  for `meeting-capture`/`todo-capture`'s on-demand `run_capture_now` — all
  stay honest "not available" stubs per the operator-relayed scoping
  decision recorded in the story's own Notes.
- A cross-process (multi-server-instance) lock mechanism — the shared
  dispatch lock is explicitly in-process only, per `ADR-037`.
- `REQ-SB-46`'s own wizard Step 4 Schedule-trigger UI.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (already landed by the architect pass; unchanged by the coder)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (`ADR-037`, already `Accepted` from the architect pass)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks, M — matched exactly on
  task count. Real effort skewed heavily toward live verification, not code
  volume: the registry (`T02`) and the frontend (`T06`) were the two
  heaviest tasks, but for different reasons — `T02` because it surfaced and
  required root-causing a real defect, `T06` because a real, unbounded
  Outlook-COM backlog (2 emails, 35 meetings, 100 tasks) happened to be
  in-flight during this session's own live verification, dominating
  wall-clock time by many multiples of the actual code cost (echoes
  `SPRINT-031`'s own "unbounded on-demand real-pipeline invocation" sizing
  risk, reconfirmed a second time here, this time surfacing indirectly via
  an app-start tick rather than a deliberately-triggered on-demand run).

### What worked

- **Running the REAL composed call graph before trusting a task's/ADR's own
  illustrative "record every status except X" description** — surfaced a
  genuine duplicate-history-entry defect in `dispatch_with_shared_lock`
  (two independent self-recording paths — `invoke_skill`'s own
  Supervised-mode "proposal" write, and `run_capture_now`'s own real
  `email-capture` dispatch chain — neither flagged via the
  `"history_recorded"` convention `build_knowledge` alone uses). Fixed
  in-scope with a generic before/after history-length comparison instead
  of hardcoding the two known cases — closes the gap for any current or
  future self-recording handler, not just the two found live. Directly
  extends this project's own repeated `SPRINT-018/019/030` "trust the real
  call graph over the illustrative sample" pattern to an ADR's own
  descriptive text, not just a task's code sample.
- **Confirming the story's own single highest-risk guarantee (the shared
  lock) via two independent techniques** — an in-process `asyncio.gather`
  call with explicit timing markers (deterministic, fast, isolated), AND a
  real, unplanned HTTP-layer race that happened naturally during this same
  session (a concurrent `run-now` call arriving while a real, multi-minute
  blob tick already held the lock). Neither alone would have been as
  convincing; together they proved the property both in a controlled
  setting and under real, uncontrolled production-shaped conditions.
- **A generic, length-based "did this already record itself" check** is a
  reusable pattern beyond this sprint — any future generic outcome-recording
  wrapper composing over a catalog of handlers with inconsistent
  self-recording conventions can use the same technique instead of a
  per-handler flag or hardcoded exclusion list.

### What didn't work

- **`Stop-Process -Name msedge` (the `-Name`/blanket form, not a specific
  PID)** was used once during CDP-session cleanup — killed every Edge
  process on the host, including the operator's own separate, already-open
  regular browser session, not just this sprint's own headless verification
  instance. This exact antipattern was already documented twice before this
  sprint (`SPRINT-026`, `SPRINT-034` — "always use the specific-PID form,
  never `/IM`/`-Name`") and still recurred a third time. Caught immediately,
  self-corrected for the remainder of the session's own cleanup, disclosed
  in `T06`'s Implementation Log and the closing report — no code/data was
  affected, but a real, avoidable operator-facing disruption occurred.
- **A real, unattended app-start capture tick colliding with this
  session's own deliberate live-verification calls** cost real
  investigation time (an apparent "duplicate history" symptom on the FIRST
  live dispatch attempt was actually two genuinely-different real causes
  compounding: the dedup defect above, AND a same-process app-start tick
  racing a separately-issued verification call before the fix landed).
  Restarting the backend mid-session (to load code changes, since this
  project's server was intentionally run without `--reload` this session)
  unconditionally re-triggers the real app-start capture every time —
  worth naming explicitly as a recurring cost specific to this project's
  own `capture_scheduler.py` design, not a one-off.

### Patterns to carry forward

- **Generic length-based self-recording detection** — when a shared,
  catalog-spanning wrapper function needs to add exactly one outcome record
  per real dispatch without double-recording a handler that already
  self-records (flagged or not), compare the target's own history/log
  length immediately before and after the real call, rather than
  maintaining a per-handler exclusion list or trusting a flag convention
  some handlers may not consistently set.
- **Verify a single highest-risk property via two independently-derived
  techniques when the opportunity arises naturally** — a controlled,
  synthetic proof (timing markers) plus an unplanned but genuinely real
  production-shaped race are complementary, not redundant; the second is
  free extra confidence when it happens to occur during otherwise-necessary
  live verification.

### Antipatterns to avoid

- **`Stop-Process -Name <browser>` / `taskkill /IM <browser>.exe` for
  CDP-session cleanup** — third confirmed recurrence of this exact,
  already-documented antipattern in this project. Given it has now recurred
  across three separate sprints despite being named twice already, this
  may warrant a stronger mitigation than a Learnings entry alone (e.g. a
  standing helper script/snippet that always resolves and kills by the
  launched PID tree specifically, so the correct form is the path of least
  resistance, not something to remember each time).
- **Restarting a dev server mid-session without accounting for its own
  unconditional app-start side effect** — when a project's own scheduler
  wiring includes an unconditional real trigger on every startup (this
  project's `capture_scheduler.py`), each restart during live verification
  is not free; budget for it explicitly rather than treating a restart as
  an instant, side-effect-free way to load new code.

### Open follow-ups

- Human review of `ADR-037` (architecture) and a retroactive design/
  prototype sign-off for the shipped Schedule tab (no `/design` pass was
  run for this net-new UI, per the story's own already-disclosed,
  non-blocking flag) — tracked in `REVIEW-QUEUE.md`.
- The in-scope duplicate-history-entry fix (`T02`) is flagged for a human
  spot-check, not because it's believed incorrect, but per this project's
  own standing scope-internal-judgement-call disclosure convention.
