---
id: REQ-SB-07-US-01
title: Scheduled recurring capture with app-start and missed-run catch-up
requirement_ids: [REQ-SB-07]
requirement_section: "REQ-SB-07: Scheduled Recurring Agent Capture"
phase: P1
status: Done
gate: clear
gate_reason: ""
sprint: "SPRINT-001"
created: 2026-08-10
updated: 2026-08-10
---

# REQ-SB-07-US-01 — Scheduled recurring capture with app-start and missed-run catch-up

## Story

**As a** Second Brain user running the app on my own laptop
**I want** the email capture pipeline to run automatically on an hourly schedule
and once whenever the app starts, catching up on any run it missed while my
laptop was off or asleep
**So that** my vault stays current without me having to remember to trigger
capture manually, even though the app isn't a persistent, always-on server

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-07: Scheduled Recurring Agent Capture*
- Precedent cited in the PRD entry: agentic-map's REQ-069 (scheduler catches up
  on any cron/skill_cron job missed while the laptop was off, firing it once on
  wake) — same underlying personal-laptop-hosted-scheduler problem, tool swap
  only; no further detail borrowed beyond what the PRD entry itself states.
- This story generalizes the existing manually-triggered email-classification
  POC (`POST /poc/classify-emails`, see `MEMORY.md` 2026-08-10 entry) into an
  automatically-scheduled capture run. The underlying capture logic itself
  (Outlook fetch → Compass classification → vault write) is
  `app/business/email_classification.py::classify_recent_emails` and is
  **unchanged** by this story — only *how and when* it gets invoked changes.
- Per `MEMORY.md`'s Hermes constraint: Hermes is an external dependency this
  project does not build code for. The recurring/catch-up scheduler is owned
  and triggered by Second Brain's own backend; Hermes remains the channel/skill
  layer the capture step runs through (as it already does for the Outlook
  fetch), not something this story designs the internals of.
- REQ-SB-08 (Meetings) and REQ-SB-09 (Tasks) both reference "the recurring
  schedule from REQ-SB-07" — this story is the first to stand that schedule up,
  wired to the one pipeline that exists today (email). Generalizing the
  scheduler to run additional pipelines is left for those stories' own
  `/plan-tasks` work, not decided here.
- No `html-prototype/` screen applies — this is a backend-only capability with
  no user-facing surface. REQ-SB-11 (Agent Activity & Error Observability) is
  the future story that will surface run history/status in the UI; that UI is
  explicitly out of scope here (see Non-Goals).

## Acceptance Criteria

<!-- Locked by the decomposer at /plan-tasks (2026-08-10) against ADR-005's
concrete mechanism (APScheduler AsyncIOScheduler + IntervalTrigger(hours=1),
coalesce=True, misfire_grace_time=None, max_instances=1; an unconditional
app-start trigger; one shared concurrency guard; last-run state in
`.second-brain/last_capture_run.json`). Wording tightened for buildability
against that mechanism; intent unchanged from the analyst's draft. -->

### Scenario 1: Hourly automatic capture run

```gherkin
Given the Second Brain backend process has been running for over an hour
  And no capture run is currently in progress (the shared scheduling
    concurrency guard is free)
When the APScheduler hourly interval job's trigger elapses
Then a capture run fires automatically, with no manual trigger required
  And the run executes the same Outlook-fetch → classify → vault-write
    pipeline the manual `POST /poc/classify-emails` endpoint already
    performs (`app/business/email_classification.py::classify_recent_emails`)
  And the last-successful-run record (`.second-brain/last_capture_run.json`)
    is updated once the run completes
```
<!-- AC-ID: REQ-SB-07-US-01-AC-01 -->

### Scenario 2: Immediate capture run on app start

```gherkin
Given the Second Brain backend process is starting up
When FastAPI's `lifespan` startup phase completes
Then a capture run fires once immediately, without waiting for the next
    hourly boundary
  And the hourly APScheduler job continues on its own interval from that
    point (the next automatic run is roughly one hour later, not
    immediately again)
```
<!-- AC-ID: REQ-SB-07-US-01-AC-02 -->

### Scenario 3: Catch-up for a run missed while the laptop was off or asleep

```gherkin
Given the last successful capture run finished more than one hour ago
  And one or more scheduled hourly runs were missed because the laptop was
    off or asleep during that window
When the app is next running and reaches its next scheduling opportunity
    (either the app-start trigger firing on a full restart, or
    APScheduler's own coalesced-misfire handling firing on wake from sleep
    under a still-live process)
Then a capture run fires once to catch up
  And it is not skipped or deferred until the next regular hourly slot
  And exactly one catch-up run fires regardless of how many hourly slots
    were missed during the gap (per the PRD acceptance text: a missed run
    "fires once on the next opportunity")
```
<!-- AC-ID: REQ-SB-07-US-01-AC-03 -->

### Scenario 4: No duplicate run when a capture is already in progress

```gherkin
Given a capture run is currently in progress (started by either the hourly
    schedule, the app-start trigger, or a missed-run catch-up), holding the
    shared scheduling concurrency guard
When another trigger (hourly boundary elapsing, or a second app-start event)
    occurs before the in-progress run finishes
Then the new trigger finds the guard held and is skipped immediately rather
    than starting a second, overlapping run, and rather than queuing/waiting
    for the guard to free up
  And the in-progress run is left to complete uninterrupted
  And the skip does not count as, or get treated as, a missed run requiring
    its own catch-up
```
<!-- AC-ID: REQ-SB-07-US-01-AC-04 -->

### Scenario 5: App restarted shortly after its own previous run

```gherkin
Given the app was restarted (e.g. after a crash or manual relaunch) less than
    one hour after its own last successful capture run
When FastAPI's `lifespan` startup phase completes
Then the app-start trigger still fires one immediate capture run, per
    Scenario 2 / AC-02 — app start always runs once, unconditionally,
    independent of how recently the last run completed
```
<!-- AC-ID: REQ-SB-07-US-01-AC-05 -->

## Affected Screens

None — backend only. No `html-prototype/` screen exists or is needed for this
capability; see `## Notes` for why no prototype-parity checklist applies.

## Dependencies

- **Blocked by:** none — the underlying capture pipeline
  (`app/business/email_classification.py`) already exists and works, validated
  by the POC (see `MEMORY.md`).
- **Related to:** REQ-SB-08 (Meetings Capture Pipeline) and REQ-SB-09 (To-Do
  Task Capture Pipeline), both of which will run on this same recurring
  schedule once their own stories are specced — not part of this story.
- **External:** none new. The Hermes-wrapped Outlook skill this pipeline
  already depends on (per `MEMORY.md`'s Hermes integration-sourcing
  constraint) is unchanged by this story.

## Constraints

- Hermes is an external dependency this project does not build code for — the
  scheduler (timing, hourly cadence, app-start trigger, catch-up, concurrency
  guard) is Second Brain's own backend responsibility, not Hermes's.
- Must respect the `api → business → data_access` layer boundary (ADR-003) —
  the scheduler orchestrates by calling into `business/`, the same way the
  existing `/poc/classify-emails` router does; it does not reach into
  `data_access` directly.
- Second Brain runs on the user's own laptop, not a persistent server — the
  scheduling/catch-up mechanism must not assume the process is always running
  or that wall-clock time between runs is contiguous.
- The exact scheduling mechanism (library/approach used to implement hourly
  cadence, app-start hook, and missed-run detection) is an architecture-level
  decision for `/plan-tasks`, not decided in this story.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-07-US-01-T01 | backend | Persist the last-successful-capture-run record | `src/backend/app/data_access/vault_writer.py` | [T01](../Tasks/REQ-SB-07-US-01-T01-last-run-persistence.md) |
| REQ-SB-07-US-01-T02 | backend | Wrap the capture pipeline with last-run bookkeeping | `src/backend/app/business/email_classification.py` | [T02](../Tasks/REQ-SB-07-US-01-T02-capture-run-and-record.md) |
| REQ-SB-07-US-01-T03 | backend | New `app/scheduling/` package: shared concurrency guard | `src/backend/app/scheduling/` | [T03](../Tasks/REQ-SB-07-US-01-T03-scheduling-concurrency-guard.md) |
| REQ-SB-07-US-01-T04 | backend | Wire APScheduler hourly job + app-start trigger into FastAPI `lifespan` | `src/backend/app/scheduling/capture_scheduler.py`, `src/backend/app/main.py`, `src/backend/requirements.txt` | [T04](../Tasks/REQ-SB-07-US-01-T04-scheduler-lifespan-wiring.md) |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, manual-verification mode still in effect project-wide
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- Meetings capture (REQ-SB-08) and To-Do task capture (REQ-SB-09) — those are
  separate, not-yet-specced stories that will plug into this same recurring
  schedule later.
- Any UI for viewing capture run history, status, or errors — that is
  REQ-SB-11 (Agent Activity & Error Observability), a distinct future story.
- Changing or removing the existing manual trigger endpoint
  (`POST /poc/classify-emails`) — it continues to exist unchanged; this story
  only adds automatic triggering alongside it.
- Deduplication of vault notes across repeated/overlapping runs — that is
  already handled by the existing capture pipeline's own logic (EntryID-based
  uniqueness, per `MEMORY.md`) and is not re-specified here.
- Configurability of the hourly cadence (e.g. a user-settable interval) — the
  PRD specifies hourly; making it configurable is not requested.

## Notes

gate: clear 2026-08-10 — no triggers fired (REQ-SB-07 is finalised in the PRD,
no `<!-- Draft -->` marker; no contradictory inputs; no architecture/ADR
changes made or needed from this role; the "exactly one catch-up run" reading
in Scenario 3 is taken directly from the PRD's own Acceptance text — "fires
once on the next opportunity" — not an added assumption; the exact scheduling
implementation mechanism is correctly left to the architect at `/plan-tasks`,
not a spec-time ambiguity).

**Prototype parity:** not applicable — this story has no screen surface.
`html-prototype/` was checked and contains no screen relevant to a backend
scheduling capability; REQ-SB-11's future observability UI is the eventual
screen that will surface this pipeline's activity, and is explicitly deferred
(see Non-Goals), not omitted by oversight.

---

**Architect pass (2026-08-10):** `gate: flagged`,
`gate_reason: trigger-3 (ADR-005 created)`. Wrote **ADR-005** (In-process
recurring scheduler via APScheduler, plus a new `app/scheduling/` layer) —
see `Implementation/Architecture/ADR.md`. Decision summary: APScheduler
(`AsyncIOScheduler`, `IntervalTrigger(hours=1)`, `coalesce=True`,
`misfire_grace_time=None`, `max_instances=1`) over a hand-rolled asyncio
loop, wired into FastAPI's `lifespan`; the app-start trigger is unconditional
application code (always fires once, doubling as catch-up for a full-restart
gap) rather than an APScheduler job; APScheduler's in-memory misfire/coalesce
handling covers the complementary case of a laptop sleeping under a still-
live process; one shared concurrency guard covers both trigger sources; the
last-run record is a new JSON file under the existing `.second-brain/`
convention (`app/data_access/vault_writer.py`'s territory). A new
`app/scheduling/` package is introduced as a fourth top-level layer, parallel
to `api/`, calling into `business/` only — extends but does not edit
ADR-003. Updated `architecture.md` (§Tech Stack, §Source Layout, §Local
Development). Not an ADR deviation or escalation — no contradiction with any
Accepted ADR, the PRD, or a `MEMORY.md` constraint was found.

**Architecture scope: §Tech Stack, §Source Layout, §Local Development**
(`Implementation/Architecture/architecture.md`) — the decomposer and coder
are bounded by these sections plus ADR-005 for this story.

REVIEW-QUEUE pointer written for ADR-005 (see `REVIEW-QUEUE.md`); the
decomposer runs next regardless, per `Implementation/Pipeline.md`'s trigger-3
handling (ADR review and the resulting tasks land in front of the human
together).

---

**Decomposer pass (2026-08-10):** All 5 scenarios locked as
`REQ-SB-07-US-01-AC-01`..`AC-05` (wording tightened against ADR-005's
concrete mechanism; no scenario intent changed — see the Acceptance Criteria
section for the diff rationale inline). Decomposed into four flat-root task
files, `REQ-SB-07-US-01-T01`..`T04` (see `## Implementation Tasks`), linearly
chained via `depends_on` (`T01 → T02 → T03 → T04`, acyclic): T01 adds
last-run JSON persistence to `data_access/vault_writer.py`; T02 adds a
business-layer wrapper (`run_capture_and_record_completion`) that calls the
existing `classify_recent_emails` unchanged, then records completion — the
manual `POST /poc/classify-emails` endpoint is untouched, per this story's
Non-Goals; T03 stands up the new `app/scheduling/` package with the shared
concurrency guard (`run_capture_if_idle`); T04 wires an APScheduler
`AsyncIOScheduler` hourly job (`IntervalTrigger(hours=1)`, `coalesce=True`,
`misfire_grace_time=None`, `max_instances=1`) plus the unconditional
app-start trigger into `app/main.py`'s `lifespan`, and adds the `apscheduler`
dependency to `requirements.txt`. Every locked AC has at least one AC-tagged
manual verification step in a task's `## Tests` (AC-01 appears in T01, T02,
and T04; AC-04 in T03; AC-02/AC-03/AC-05 in T04) — verification runs in
manual mode per `Implementation/Pipeline.md`'s coder verification-mode
section (no automated test runner wired to this layer yet; `pytest` today
only covers `/health`). `depends_on` is acyclic (a straight T01→T02→T03→T04
chain, no fan-out). Story `status:` advances `Draft → Ready` and all four new
tasks are written at `status: Ready` to match, per the decomposer's
lockstep-status rule.

**`gate:` left `flagged`, unchanged from the architect's pass** —
`gate_reason: trigger-3 (ADR-005 created)` still applies; no new MUST-FLAG
trigger fired during this decomposition pass itself (no material assumption
beyond what ADR-005 already settled, no contradictory inputs, no additional
ADR/ESCALATIONS activity, no oversized task — each of T01–T04 is a
single-file-or-single-package change fitting one working session, every
locked AC is verifiable by an observable manual step, and the task
breakdown followed directly from ADR-005's own numbered decision points
rather than presenting a genuine choice). Per this role's contract, the
architect's flag stays set so the human reviews ADR-005 and these four tasks
together in one pass — the existing `REVIEW-QUEUE.md` entry for
`REQ-SB-07-US-01` has been updated to point at the now-created tasks as well
as the ADR.

---

**Operator review (2026-08-10):** ADR-005 approved as written — no changes
requested. `gate: flagged → clear`; the `REVIEW-QUEUE.md` entry is resolved
and removed. Proceeding straight to `/implement-sprint` for `SPRINT-001`.

---

**Coder pass, all tasks (2026-08-10):** `T01`–`T04` all `status: Done`, all
5 locked ACs verified live against the real backend (Outlook desktop
running, real Compass calls, real vault writes) — see each task's own
`## Implementation Log` for per-AC detail. `status: Done`. All Definition of
Done boxes satisfied: ACs pass, every Implementation Task complete,
Constraints respected (layering, Hermes untouched, no manual-endpoint
changes), `MEMORY.md` updated (dev-server-fires-a-real-capture-run
constraint from T04), `CHANGELOG.md` entries appended per task.
