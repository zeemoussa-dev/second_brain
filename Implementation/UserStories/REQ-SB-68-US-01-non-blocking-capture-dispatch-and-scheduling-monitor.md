---
id: REQ-SB-68-US-01
title: Non-blocking manual capture dispatch + a real Job/Scheduling monitor on System Health
requirement_ids: [REQ-SB-68]
requirement_section: "REQ-SB-68: Async Capture Jobs + Real-Time Job/Scheduling Monitor"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-045 created) — architect pass, /plan-tasks step 1, 2026-08-17, left flagged through the decomposer pass per Implementation/Pipeline.md (the human reviews ADR-045 and the resulting tasks together in one pass). The earlier net-new-design-needed flag was already resolved clear by direct operator decision (see the 'Operator decision' note near the end of ## Notes); this flag is a separate, later one raised by the architect pass, not a reopening of the design question. Decomposer pass (/plan-tasks step 2, 2026-08-17) locked all 7 ACs, created T01-T04, and advanced status to Ready — no additional MUST-FLAG trigger fired during decomposition itself (see ## Notes)."
sprint: "SPRINT-055"
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-68-US-01 — Non-blocking manual capture dispatch + a real Job/Scheduling monitor on System Health

## Story

**As a** Second Brain operator
**I want** manually triggering a capture job to never freeze the rest of
the app while it runs, and to be able to see — for each of the jobs that
can freeze the app today — whether it's currently running, how long the
current or most recent run took, and whether it succeeded or genuinely
failed (with the real error)
**So that** I never again have to guess whether the backend is stuck,
still working, or silently failing while a capture run is in flight, the
way it did on 2026-08-17 when a manual "Run Capture Now" click froze
every other endpoint for several minutes with zero visibility into what
was happening

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-68: Async Capture Jobs +
  Real-Time Job/Scheduling Monitor*. Two tightly-coupled fixes to the
  same underlying gap: (1) fix `run_capture_now`'s blocking bug — the
  manual "Run Capture Now" action calls its handler directly on the
  asyncio event loop, blocking the ENTIRE backend for the full duration
  of the run; (2) a real Job/Scheduling monitor — today there is no
  visibility into whether a backend capture job is currently running, how
  long it has been running, or whether its last run errored.
- **Raised 2026-08-17, operator-directed, immediately following a live
  incident** (PRD's own HTML comment, cited verbatim): manually
  triggering `run_capture_now` to double-check a low real-Thread count
  caused the whole backend to become unresponsive for several minutes,
  with zero visibility into what was actually happening (running? stuck?
  errored?) from either the API or the UI while it happened.
- **Real code read directly to ground this story, not assumed:**
  - `app/api/agents_router.py::_execute_action` — the dispatch path
    `("email-capture-pipeline", "run_capture_now")` in `_ACTION_HANDLERS`
    resolves to — calls `handler()` **directly, synchronously**, with no
    thread-pool offload (`results = handler()`, line ~129). Its caller,
    `_invoke_action` (async), reaches it via a plain `return
    _execute_action(agent_id, action_id)` — never `await`ed onto a
    thread. Since the underlying handler
    (`email_classification.run_capture_and_record_completion`) does real,
    slow, blocking work (Outlook COM calls, real Compass HTTP calls —
    including, since `REQ-SB-67`, one Compass call per email/Thread
    message), this blocks asyncio's single event loop for the whole
    duration, and FastAPI/uvicorn's default single-worker setup means
    EVERY other in-flight or new request — not just this one — starves
    until it returns. Confirmed live 2026-08-17: a real `curl` to `GET
    /agents` returned nothing until the manually-triggered capture
    finished.
  - Contrast with `app/scheduling/capture_scheduler.py::run_capture_if_idle`
    — the SAME underlying pipeline call
    (`email_classification.run_capture_and_record_completion`), but
    already wrapped in `asyncio.to_thread(...)`. This function's own
    docstring/inline comment documents a near-identical 2026-08-14
    bugfix (`BUG-008`, `BUGS.md`, `Closed`) applied to the app-start
    trigger specifically because an earlier version of this exact same
    class of bug froze all HTTP traffic at startup. The scheduler's own
    hourly/per-agent-schedule ticks never exhibit this bug today; only
    the manual action-dispatch path (`_execute_action`) does, because it
    never received the same fix. **This story applies the same, already-
    proven fix shape to `_execute_action`'s manual-trigger path** — no
    new mechanism, the one this codebase already uses and has already
    verified live twice (`BUG-008`; `capture_scheduler.py`'s hourly tick
    running for weeks with no repeat).
  - `app/business/agent_schedule_registry.py::get_shared_dispatch_lock()`/
    `dispatch_with_shared_lock()` — the scheduler's own concurrency guard,
    a single module-level `asyncio.Lock()` every real scheduled/on-demand
    trigger source is meant to pass through, per its own docstring ("the
    ONE function every real scheduled/on-demand trigger source now passes
    through"). **Confirmed by direct reading: `_execute_action`'s manual-
    trigger path does NOT participate in this lock at all** — it calls
    `handler()` with no lock acquisition of any kind. This means a manual
    "Run Capture Now" click could in principle race a concurrent
    scheduled tick, running two real Outlook COM sessions at once. This
    is real, relevant background for whoever designs the fix at
    `/plan-tasks` — see `## Notes` for why fixing this specific race is
    **not** this story's own primary ask.
  - `.second-brain/last_capture_run.json`
    (`app/data_access/vault_writer.py::record_capture_run_completed`/
    `load_last_capture_run`) is today's only run-state persistence — a
    bare `{"finished_at": <iso8601>}`, written once, only on a fully
    successful tick (no per-attempt record, no running/duration/error
    field of any kind). `GET /agents/{id}/history`
    (`agents_router.py::get_history` → `vault_writer.load_agent_history`)
    only logs simple post-hoc text lines ("Capture run completed — N
    email(s) filed" / "Capture run failed — <exc>"), written **after**
    a run finishes — nothing at all while a run is still in flight, no
    duration field. This story's new run-state tracking composes with/
    extends these existing mechanisms (a persisted started-at/still-
    running/duration/outcome record, read fresh on each Scheduling-view
    load) rather than inventing a third, disconnected one.
  - `Implementation/UserStories/REQ-SB-31-US-01-system-health-view.md`
    (`Done`, `SPRINT-019`) built `src/backend/app/business/
    system_health.py` + `src/backend/app/api/system_health_router.py` +
    `src/frontend/src/pages/SystemHealthPage.tsx` +
    `src/frontend/src/features/system-health/client.ts` — a read-only
    aggregation module → router → page, recomputing fresh on every open/
    refresh, **no auto-polling** (an explicit Non-Goal of that story: "no
    background polling interval is specified or built"). This story's new
    "Scheduling" region is a new section on the **same, already-existing**
    System Health page (`GET /system-health`'s own response shape grows a
    new key; the page grows a new section) — not a new top-level page, no
    new nav item.
- **Two open scope questions the PRD deliberately leaves for `/spec`,
  resolved here with code-grounded reasoning (not a guess between
  equally-valid options — see `## Notes` for why this does not also
  trigger MUST-FLAG-8):**
  1. **Which jobs does the new run-state tracking cover?** Resolved:
     **scoped to the three capture-style jobs `capture_scheduler.py`'s
     own shared dispatch lock already covers today** —
     `email-capture-pipeline`, `meeting-capture`, `todo-capture` (the
     exact three `email_classification.run_capture_and_record_completion`
     already dispatches internally, in one call, gated independently by
     each agent's own working mode). **Not** "every dispatched agent
     action generally" — `_ACTION_HANDLERS` has exactly one other real
     handler today (`compass-expert`/`build_knowledge`), already async
     via `_execute_async_action` and never exposed to the blocking bug
     this story fixes; every other declared action has no real handler
     at all and honestly returns "not yet available"
     (`_execute_action`'s own `handler is None` branch, `ADR-011` point
     3's disclosed honesty convention). Building run-state-tracking
     infrastructure for actions with no real handler would mean tracking
     something that never actually runs — the exact kind of
     speculative/dead surface this codebase's own conventions
     consistently avoid (see `agents_router.py`'s own
     `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE`, "a small, disclosed,
     hand-maintained set" of real facts, never a fabricated blanket
     claim).
  2. **Static or live-updating duration?** Resolved: **recompute fresh on
     open/manual refresh** — the same convention the existing System
     Health page already established for every other check
     (`REQ-SB-31-US-01` Scenario 7/Constraints: "recomputes fresh on
     every call, never cached"; that story's own Non-Goals explicitly
     rule out "auto-refresh/polling beyond recomputing fresh on each view
     open or manual refresh"). A run's elapsed duration is computed at
     **read time** from a persisted `started_at` timestamp (`now −
     started_at`), so it is correct and effectively "live" relative to
     each explicit open/refresh — without inventing a first-ever push/
     WebSocket/polling mechanism this codebase has never built. This
     directly answers the operator's own complaint (no visibility while a
     run is in flight) without a materially bigger, riskier build than
     this project's own established "reuse first, invent last" pattern
     calls for.
- **A pre-existing `REVIEW-QUEUE.md` entry already tracks the raw
  incident this story now formally specs** (`2026-08-17 · Performance/
  architecture finding · run_capture_now blocks the ENTIRE backend`). That
  entry noted "no story currently owns it" — this story is that story;
  the queue entry is left in place (not removed — the fix has not shipped
  yet) with a pointer added to this file. See `## Notes`.
- **A live-code correction to `MEMORY.md`'s own same-night entry:**
  `MEMORY.md`'s `run_capture_now`-blocking Constraint entry (2026-08-17)
  states "the scheduled/automatic hourly runs (`capture_scheduler.py`)
  hit this same blocking behavior every time they fire, but are usually
  fast enough in practice... that it isn't noticeable." **Direct reading
  of the current `capture_scheduler.py::run_capture_if_idle` shows this
  is not accurate as written** — that function already wraps the
  identical pipeline call in `asyncio.to_thread(...)`, which does not
  block the event loop regardless of how long the underlying call takes;
  it is genuinely non-blocking today, not merely "usually fast enough."
  Only the manual `_execute_action` dispatch path lacks this. Flagged
  here for a human to correct the `MEMORY.md` entry's own wording (the
  analyst does not edit `MEMORY.md` directly — out of scope, see
  `## Forbidden` in the analyst's own role bounds).

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A real, manually-triggered capture run no longer blocks the rest of the backend

```gherkin
Given the operator manually triggers "Run Capture Now" for
    email-capture-pipeline (POST /agents/email-capture-pipeline/actions/
    run_capture_now)
  And the underlying capture call is a real, slow, blocking call
    (real Outlook COM access, real Compass HTTP calls)
When that capture run is genuinely still in progress
Then a request to an unrelated endpoint (e.g. GET /agents) responds
    normally and promptly — not delayed until the capture run finishes
  And the capture run itself still completes and returns its usual
    {"status", "message"} result (no change to what the capture does,
    only to how it is dispatched)
```
<!-- AC-ID: REQ-SB-68-US-01-AC-01 -->

### Scenario 2: The Scheduling section shows a covered job as currently running, with its elapsed duration

```gherkin
Given one of the three covered jobs (email-capture-pipeline,
    meeting-capture, todo-capture) has a real run currently in progress
When the user opens or refreshes the Scheduling section on the System
    Health page
Then that job's row shows a "running" state
  And the row shows how long the run has been going so far, computed
    fresh at the moment of that request — not a value frozen from when
    the run started
```
<!-- AC-ID: REQ-SB-68-US-01-AC-02 -->

### Scenario 3: The Scheduling section shows the most recent run's duration and success outcome once it finishes

```gherkin
Given one of the covered jobs' most recent run has finished successfully
When the user opens or refreshes the Scheduling section
Then that job's row shows it is not currently running
  And the row shows how long that most recent run took
  And the row shows its last outcome as a success
```
<!-- AC-ID: REQ-SB-68-US-01-AC-03 -->

### Scenario 4: A genuine failure in the underlying call is surfaced honestly, not hidden behind stale or blank state

```gherkin
Given one of the covered jobs' most recent run failed because a real
    underlying call errored (e.g. Compass was unreachable)
When the user opens or refreshes the Scheduling section
Then that job's row shows its last outcome as a failure
  And the row shows the real error message from that failure
  And the row does not silently keep showing an earlier successful run's
    stale outcome, and is not left blank
```
<!-- AC-ID: REQ-SB-68-US-01-AC-04 -->

### Scenario 5: A covered job that has never run shows an honest "no runs yet" state

```gherkin
Given one of the covered jobs has never been dispatched, manually or on
    a schedule, since job_run_state.json's own run-state tracking was
    introduced
When the user opens the Scheduling section
Then that job's row honestly states it has no recorded run yet
  And no running/duration/outcome value is fabricated for it
```
<!-- AC-ID: REQ-SB-68-US-01-AC-05 -->

### Scenario 6: The existing scheduled-tick behavior remains correctly non-blocking and unregressed

```gherkin
Given the hourly scheduled capture tick (or a per-agent schedule) fires
    and dispatches one of the covered jobs exactly as it does today
When that scheduled tick runs
Then it continues to run off the event loop thread exactly as it does
    today, and does not block any other request
  And its existing skip-if-already-running / non-overlap behavior
    (agent_schedule_registry's shared dispatch lock) is unchanged
  And the Scheduling section correctly reflects that scheduled run's own
    running/duration/outcome state, through the same job_run_state.json
    mechanism a manually-triggered run's state is shown through
```
<!-- AC-ID: REQ-SB-68-US-01-AC-06 -->

### Scenario 7: An agent action outside the three covered jobs is not shown on the Scheduling section

```gherkin
Given an agent action other than the three covered jobs' run_capture_now
    (e.g. compass-expert's build_knowledge) is dispatched
When the user opens the Scheduling section
Then that action's own run is not shown as a row on the Scheduling
    section
  And the Scheduling section still correctly renders the three covered
    jobs' own rows — it is not left broken or empty-looking because of
    the uncovered action
```
<!-- AC-ID: REQ-SB-68-US-01-AC-07 -->

## Affected Screens

- `html-prototype/system-health.html` — grows a new "Scheduling" section
  showing, per covered job (email-capture-pipeline, meeting-capture,
  todo-capture): currently-running state, elapsed/most-recent duration,
  and last outcome (success, or the real error message on failure). This
  region has **no covering prototype today** — see `gate_reason` above
  and `## Notes` → *Prototype parity*. `/design REQ-SB-68` must run to
  produce an approved prototype for this new region before
  `/plan-tasks`.

## Dependencies

- **Related to:** `REQ-SB-31-US-01` (`Done`) — this story extends the
  same System Health page/`GET /system-health` surface that story built;
  no changes needed to that story's own existing regions (Health Issues,
  MCP status, Providers).
- **Related to:** `BUG-008` (`Closed`, `BUGS.md`) — the app-start
  blocking-startup bug this story's own fix shape directly mirrors
  (`asyncio.to_thread`, applied to a different trigger source).
- **Related to:** `ADR-037` / `agent_schedule_registry.py`'s shared
  dispatch lock — this story's run-state tracking is scoped to exactly
  the same three jobs that lock already covers; see `## Notes` for the
  separate, not-fixed-here race-condition risk (`_execute_action` does
  not currently acquire this lock).
- **External:** none new.

## Constraints

- **The async fix must preserve the capture's own existing behavior and
  outcome exactly** — only how `run_capture_now` is dispatched changes
  (moved off the event loop thread), never what it does, what it writes,
  or what history entries it records.
- **Run-state tracking is scoped to the three capture-style jobs already
  covered by `agent_schedule_registry`'s shared dispatch lock**
  (`email-capture-pipeline`, `meeting-capture`, `todo-capture`) — not
  extended to every dispatched agent action. See `## Notes` for the
  reasoning this resolves the PRD's own open scope question 1.
- **No new push/WebSocket/polling mechanism is invented.** The Scheduling
  view recomputes fresh on open/manual refresh, mirroring the System
  Health page's existing convention (`REQ-SB-31-US-01`). Duration for an
  in-flight run is computed at read time from a persisted `started_at`
  timestamp — never incrementally streamed.
- **No fabricated data.** A job with no recorded run must say so
  honestly (Scenario 5); a genuine failure must show the real error
  message (Scenario 4), never a generic/blank placeholder.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Decomposer-authored table (/plan-tasks step 2, 2026-08-17) —
supersedes the analyst's own starting-point table. Corrected per the
architect's grounding correction (ADR-045): the real fix touches
_invoke_capability, not _execute_action. -->

| ID | Type | Task | Files / Area | Depends On | Task File |
|---|---|---|---|---|---|
| REQ-SB-68-US-01-T01 | backend | `agents_router.py::_invoke_capability` becomes `async def`, routes `run_capture_now` through `agent_schedule_registry.dispatch_with_shared_lock` (`ADR-045` point 1-3) | `app/api/agents_router.py`, `app/business/agent_schedule_registry.py` (one-line `Literal` widen only) | — | `../Tasks/REQ-SB-68-US-01-T01-non-blocking-manual-capture-dispatch.md` |
| REQ-SB-68-US-01-T02 | backend | Persisted per-job run-state record (`job_run_state.json`) written from inside `dispatch_with_shared_lock`, gated structurally to `capability_id == "run_capture_now"`, no hardcoded agent-id list (`ADR-045` point 4) | `app/data_access/vault_writer.py`, `app/business/agent_schedule_registry.py` | T01 | `../Tasks/REQ-SB-68-US-01-T02-per-job-run-state-tracking.md` |
| REQ-SB-68-US-01-T03 | backend | Extend `GET /system-health` with the new `"scheduling"` key; retire `"last_capture_run"` (`ADR-045` point 5-6) | `app/business/system_health.py` | T02 | `../Tasks/REQ-SB-68-US-01-T03-scheduling-system-health-extension.md` |
| REQ-SB-68-US-01-T04 | frontend | Replace `SystemHealthPage.tsx`'s "Last capture run" region with a "Scheduling" section, reusing the page's own `item-list`/`item-row` idiom (`ADR-045` point 7; no `/design` pass, operator-directed) | `src/frontend/src/pages/SystemHealthPage.tsx`, `src/frontend/src/features/system-health/client.ts` | T03 | `../Tasks/REQ-SB-68-US-01-T04-scheduling-view-frontend.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists — manual/live-data-trace verification mode until then, per this project's own standing convention)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
      (including the wording correction to the 2026-08-17 "scheduled runs
      also block" Constraint entry noted in `## Context` — closed out by
      `T01`'s own Implementation Log)
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Real-time push/WebSocket-based live-updating duration display** —
  deferred; recompute-on-refresh only (see Constraints and the PRD scope
  question 2 resolution in `## Context`).
- **Run-state tracking for agent actions outside the three capture-style
  jobs already covered by the shared dispatch lock** — see the PRD scope
  question 1 resolution in `## Context`.
- **Closing the separate race-condition risk** where `_execute_action`'s
  manual dispatch does not currently participate in
  `agent_schedule_registry`'s shared dispatch lock, so a manual trigger
  could in principle race a concurrent scheduled tick (two real Outlook
  COM sessions at once). Real and documented (`## Notes`), but explicitly
  **not** this story's own primary ask per the task that raised it —
  left for the architect to decide at `/plan-tasks` whether `T01`'s fix
  should also route through `get_shared_dispatch_lock()`/
  `dispatch_with_shared_lock()`, or whether that's separate follow-up
  work.
- **General ASGI-level exception-catching/logging middleware** — this
  story adds per-job run-state tracking for the three covered jobs only,
  not a general observability layer (mirrors `REQ-SB-31-US-01`'s own
  identical Non-Goal boundary).
- **Alerting/notifications** on a detected failure — this is a view the
  operator checks, not a push mechanism.
- **Historical run-history / chronological log beyond "current or most
  recent run"** — that is `REQ-SB-11`'s separate scope (Agent Activity &
  Error Observability), not expanded into this story, mirroring
  `REQ-SB-31-US-01`'s own precedent for keeping these two shapes distinct.

## Notes

**Prototype parity (`html-prototype/system-health.html`):**

- **"Health Issues" card** — Specced by `REQ-SB-31-US-01` (`Done`);
  untouched by this story.
- **"MCP / Agent-orchestration path" card** — Specced by
  `REQ-SB-31-US-01` (`Done`); untouched by this story.
- **"Providers" card** — Specced by `REQ-SB-31-US-01` (`Done`); untouched
  by this story.
- **"Last capture run" section** (the existing single aggregate
  `finished_at` timestamp) — **Superseded** (reason: this story's new
  per-job "Scheduling" section provides equivalent-and-richer state —
  running/duration/outcome/error for each of the three covered jobs —
  that this single aggregate timestamp region only showed a sliver of
  for `email-capture-pipeline` alone). Whether the old region is replaced
  outright by the new section or the two coexist is a concrete visual
  question left to `/design REQ-SB-68`, since no prototype today shows
  either shape for the new, richer per-job data.
- **New "Scheduling" section** (per-job running/duration/outcome/error
  state for the three covered jobs) — **genuinely new UI region, not
  covered by any existing `html-prototype/` screen** (confirmed by direct
  inspection of `system-health.html` in full, plus a repo-wide search of
  every `html-prototype/*.html` file for "schedul" — the only matches are
  unrelated per-agent recurring-schedule CRUD UI on other screens, not a
  running-jobs monitor). This is the concrete trigger for this story's
  `gate: flagged` — see `gate_reason` above. **Recommend the human run
  `/design REQ-SB-68`** to produce an approved prototype for this region
  before `/plan-tasks` proceeds, mirroring `REQ-SB-31-US-01`'s own
  identical precedent for genuinely new UI on this same page.

**Why the two PRD-deliberate open scope questions don't *also* trigger
MUST-FLAG-8 ("multiple equally-valid options / genuinely unclear")
separately from the net-new-design flag above:** both were resolved with
a single, code/precedent-grounded answer, not a choice among equally
plausible alternatives (see `## Context` for the full reasoning on each):
scope question 1's answer follows directly from what `_ACTION_HANDLERS`
and the shared dispatch lock actually, currently cover — extending
further would mean tracking non-existent handlers, contradicting this
codebase's own repeated "disclose only what's real" convention (`ADR-011`
point 3, `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE`). Scope question 2's
answer follows directly from the exact convention the System Health page
this story extends already established (`REQ-SB-31-US-01`'s own
recompute-fresh-on-refresh Constraint/Non-Goal) — inventing a first-ever
push/polling mechanism for this one region, when the page's every other
region already uses and will continue using refresh-based recompute,
would be the genuinely arbitrary choice, not the resolution taken here.

**The race-condition finding (`_execute_action` bypasses
`agent_schedule_registry`'s shared dispatch lock entirely)** is recorded
in `## Context`/Non-Goals for the architect's attention at `/plan-tasks`
— real, confirmed by direct code reading, but explicitly out of this
story's own primary scope per the task that raised it. Whether `T01`'s
fix should also acquire the shared lock (closing the race as a side
effect) or whether that's separate follow-up work is an architecture
decision, not decided here.

**Existing `REVIEW-QUEUE.md` entry:** `2026-08-17 · Performance/
architecture finding · run_capture_now blocks the ENTIRE backend, not
just its own request` is the raw incident report that prompted `REQ-SB-68`
and, now, this story. It is left in place (not removed — the fix has not
shipped; `REVIEW-QUEUE.md` items are removed only once resolved) with a
pointer to this story added directly beneath it, so the human sees both
together.

**Existing `MEMORY.md` wording correction:** see `## Context`'s final
bullet — the 2026-08-17 Constraint entry's claim that scheduled runs
"hit this same blocking behavior" is not accurate against the current
`capture_scheduler.py::run_capture_if_idle` code (already
`asyncio.to_thread`-wrapped, genuinely non-blocking). Flagged for a human
to correct that entry's wording directly; the analyst does not edit
`MEMORY.md`.

gate: flagged 2026-08-17 — net-new-design-needed (see `gate_reason`
above and *Prototype parity*, this section). No other MUST-FLAG trigger
fired independently: no material assumption was needed beyond the two
PRD-deliberate open questions, both resolved with grounded, single-answer
reasoning (not a guess among equally-valid options — see above); `REQ-SB-68`
is finalised PRD text, not `Draft`; no ADR was created or changed by this
pass (that is the architect's own call to make at `/plan-tasks`, informed
by the race-condition finding above); no `ESCALATIONS.md` entry was
written (this is a forward, in-scope `/spec` pass, not a backward/
out-of-scope event); this story is not oversized (four tasks, the same
shape/size as `REQ-SB-31-US-01`'s own four-task System Health build); no
contradictory PRD inputs exist. A `REVIEW-QUEUE.md` entry has been added
pointing here.

---

**Operator decision, 2026-08-17: `/design` skipped, `gate` reset to
`clear`.** Same standing precedent already set the same night for
`REQ-SB-66`'s Job-Settings UI (operator: "no more designer we will do it
later build the needed ui we will fix it later") — a small, additive
region on an already-existing, already-approved page
(`SystemHealthPage.tsx`), not a net-new screen needing its own
ground-up prototype. `/plan-tasks` may now proceed directly.

---

**Architect pass, 2026-08-17 (`/plan-tasks` step 1) — grounding
correction, decisions, and ADR-045:**

- **A material correction to this story's own `## Context`, found by
  direct re-reading of the REAL current code, not assumed.** This
  story's own Context named `agents_router.py::_execute_action`'s
  `_ACTION_HANDLERS` dispatch as the live blocking call site for manual
  `run_capture_now`. That is not correct as written: both of
  `_ACTION_HANDLERS`'s only two entries (`run_capture_now`,
  `build_knowledge`) are ALSO `skill_tools.SKILLS` members (migrated
  there by `REQ-SB-39-US-02`/`ADR-029` point 5), and every real caller
  that could reach `_execute_action` (`trigger_action`, `chat`,
  `pending_approvals_router.py`'s Approve endpoint) checks `action_id in
  skill_tools.SKILLS` FIRST and branches away before `_execute_action` is
  ever reached, for both ids, always. **`_execute_action`/
  `_ACTION_HANDLERS`/`_run_build_knowledge`/`_execute_async_action` are
  confirmed dead code today** — a real, previously-undisclosed
  housekeeping finding, left unfixed (out of this story's own scope,
  flagged to `REVIEW-QUEUE.md` for a future cleanup story). The
  underlying diagnosis this story's own Context reached — "the manual
  trigger blocks the event loop" — is correct; only the specific
  function was wrong. The REAL manual dispatch path, confirmed by direct
  reading, is `agents_router.py::trigger_action`/`chat` →
  `_invoke_capability` → `skill_registry.invoke_skill` →
  `_dispatch_skill` → `skill_tools.run_capture_now` →
  `email_classification.run_capture_and_record_completion` — fully
  synchronous end-to-end, no thread offload anywhere. This is the path
  the decomposer's tasks must fix; `_execute_action` itself needs no
  change and does NOT need to become `async def` — it is not on the real
  hot path for any of the three covered jobs' manual dispatch.
- **The non-blocking fix's exact shape:** `_invoke_capability` becomes
  `async def`; when `capability_id == "run_capture_now"` it routes
  through `agent_schedule_registry.dispatch_with_shared_lock(agent_id,
  capability_id, trigger=trigger)` (already `asyncio.to_thread`-wrapped,
  `ADR-037`, the exact same proven shape `capture_scheduler.py::
  run_capture_if_idle` uses) instead of calling `skill_registry.
  invoke_skill` directly; every other `capability_id` is unaffected. Both
  real call sites (`trigger_action`, `chat`, both already `async def`)
  add `await`. Full mechanism, every alternative considered:
  [ADR-045](../Architecture/ADR.md).
- **Shared-lock decision: YES, the manual path now joins
  `agent_schedule_registry`'s shared dispatch lock**, closing the
  race-condition risk this story's own `## Non-Goals` left open for the
  architect to decide. This was not a separate, harder add-on — it is
  the SAME function (`dispatch_with_shared_lock`) already being adopted
  for the non-blocking fix; declining to also take the lock would have
  meant deliberately building a second, parallel non-locked wrapper next
  to it for no benefit. A manual "Run Capture Now" click and a concurrent
  scheduled tick targeting the same covered agent now correctly
  skip-not-queue-not-overlap, exactly as `run_capture_if_idle`'s own
  Scenario 4 already does.
- **Run-state persistence: new sibling store
  `.second-brain/job_run_state.json`**, composed via new
  `vault_writer.py` pure-I/O primitives, keyed by the same
  `"{agent_id}::{capability_id}"` composite string `agent_schedules.json`
  already uses. Written from two new `agent_schedule_registry.py`
  functions called inside `dispatch_with_shared_lock`'s own lock-held
  block, gated to `capability_id == "run_capture_now"` (the same
  structural gate the dispatch fix uses — no hardcoded 3-agent-id list
  needed). A new `get_job_run_states()` accessor computes an in-flight
  run's duration fresh at read time, never persisted incrementally.
  `.second-brain/last_capture_run.json` is **superseded for display**
  (its own "last_capture_run" key drops off `GET /system-health`'s
  response) **but left alone for storage** (its own write call site in
  `email_classification.py` is untouched — a harmless, disclosed
  redundancy, not a defect).
- **New endpoint: none — extends the existing `GET /system-health`**
  with a new `"scheduling"` key (API-first, not a raw file, per
  tonight's own standing operator directive). No new router.
- **Where the Scheduling region lives:** replaces
  `SystemHealthPage.tsx`'s existing `<h2>Last capture run</h2>` + card
  region outright, at the same position (immediately after the
  "Providers" card) — not coexisting alongside it (a strictly-subsumed
  smaller sliver of the same signal next to the fuller one is more
  confusing, not less). Reuses the page's own already-established
  `item-list`/`item-row` visual idiom (the "Providers" card immediately
  above it), one row per covered job.
- **ADR decision: yes, a new ADR was needed — `ADR-045`.** This is more
  than "a new sibling-store persistence mechanism" (which alone would not
  need one, mirroring `ADR-011` point 2/`ADR-030`'s already-`Accepted`
  pattern, per `ADR-044`'s own precedent for the same class of judgment
  call) — it also reroutes a real, previously-un-routed dispatch surface
  through `ADR-037`'s own shared-lock mechanism (closing a gap that
  already-`Accepted` ADR itself left open), corrects a material grounding
  error in this story's own Context, and makes a real, disclosed
  "replace, don't coexist" UI-region decision. This project's own history
  consistently ADRs dispatch/gating-mechanism changes of this shape
  (`ADR-011`, `ADR-020`, `ADR-028`, `ADR-029`, `ADR-037`) — this is that
  same class of decision, one step further. Full ADR:
  `Implementation/Architecture/ADR.md` → `ADR-045`.
- **Architecture scope: §Non-Blocking Manual Capture Dispatch +
  Scheduling Monitor (REQ-SB-68-US-01), §Per-Agent Scheduler & Shared
  Outlook-COM Dispatch Lock (REQ-SB-47-US-01, ADR-037), §System Health
  View (REQ-SB-31-US-01)** — the coder is bounded to these three
  `Implementation/Architecture/architecture.md` sections plus `ADR-037`
  and `ADR-045` in full.

`gate: flagged 2026-08-17 — trigger-3 (ADR-045 created)`. The pipeline
does not halt: the decomposer runs next so a human reviews `ADR-045` and
the resulting tasks together in one pass, per `Implementation/
Pipeline.md`. A `REVIEW-QUEUE.md` entry has been added pointing here,
alongside a separate entry for the confirmed-dead-code housekeeping
finding above.

---

**Decomposer pass, 2026-08-17 (`/plan-tasks` step 2) — ACs locked, tasks
created, story advanced to `Ready`:**

- **All 7 scenarios locked as `REQ-SB-68-US-01-AC-01` through `AC-07`**,
  wording lightly tightened for buildability (concrete section/response
  language: "Scheduling section" instead of "Scheduling view", `{"status",
  "message"}` result shape named explicitly in `AC-01`, `job_run_state.json`
  named explicitly in `AC-05`/`AC-06`) — no scenario's own substance
  changed, no AC marked non-locked.
- **Four flat-root tasks created**, `T01` → `T02` → `T03` → `T04`, a
  single linear `depends_on` chain (acyclic): `T01` (backend,
  `agents_router.py::_invoke_capability` + one-line
  `dispatch_with_shared_lock` `Literal` widen) → `T02` (backend,
  `job_run_state.json` persistence inside `dispatch_with_shared_lock`) →
  `T03` (backend, `GET /system-health`'s new `"scheduling"` key) → `T04`
  (frontend, the new Scheduling section). `T01`/`T02` both touch
  `agent_schedule_registry.py`, hence the explicit `depends_on` edge
  between them (sequencing, not a genuine interface dependency) — every
  other edge is a genuine same-response-shape/endpoint dependency.
- **AC-to-task mapping:** `AC-01` (no screen, Scenario 1 names none) is
  verified in `T01` at the backend layer, mirroring
  `REQ-SB-31-US-01-AC-08`'s own identical no-screen precedent. `AC-02`
  through `AC-07` (all "the user opens or refreshes the Scheduling
  section") are verified in `T04`, the only task where they are
  genuinely, fully observable — `T02`/`T03` carry non-AC smoke checks
  only, mirroring `REQ-SB-31-US-01-T02`/`T03`'s own identical split.
- **One disclosed, in-scope design refinement of `ADR-045` point 4's own
  literal read-side wording, not a re-litigation of its write-side
  mechanism/storage/record-shape decisions (see `T02`'s own "Design
  refinement" note for the full reasoning):** `ADR-045`'s text has
  `get_job_run_states()` omit an absent covered job and has the
  *frontend* detect that absence to render "no runs yet" — which would
  require the frontend to hold its own independently-hardcoded
  three-covered-agent-id list, directly in tension with tonight's own
  standing config-not-hardcoded operator directive ("read the
  three-jobs list from wherever `agent_schedule_registry`/
  `capture_scheduler` already source it, not re-hardcoded a second time
  in the new run-state/Scheduling code"). `T02` instead has
  `get_job_run_states()` itself enumerate the covered agent ids from
  `skill_registry._MIGRATION_GRANT_SEED["run_capture_now"]` (the exact
  real source `ADR-045`'s own Decision 1 already names) and return an
  honest `"has_run": False` placeholder for an absent one — same store,
  same write-side structural gate, same record shape, zero client-side
  hardcoding. Not flagged as a further MUST-FLAG trigger: a mechanical,
  same-shape implementation-detail resolution under an already-Accepted
  ADR, not a new architectural decision, an assumption filling a gap, or
  a contradiction.
- **No new MUST-FLAG trigger fired during this decomposition pass
  itself.** No material assumption was needed beyond the design
  refinement above (grounded, not guessed); `REQ-SB-68` is finalised PRD
  text; no ADR was created or changed by this pass (the architect's own
  `ADR-045`, already accounted for in `gate_reason`, above); no
  `ESCALATIONS.md` entry was written; the story is not oversized (four
  tasks, matching `REQ-SB-31-US-01`'s own precedent shape); every locked
  AC has at least one tagged verification step; `depends_on` is acyclic.
  `status:` advances `Draft → Ready`; `gate:` stays `flagged` (per
  `Implementation/Pipeline.md`: an architect-created ADR this run keeps
  the story flagged through the decomposer pass so the human reviews
  `ADR-045` and `T01`-`T04` together) — the `REVIEW-QUEUE.md` entry
  already pointing here from the architect pass now also covers these
  tasks; no new entry needed.
- **Every task file's own `status:` was written `Ready`** (not `Draft`),
  in lockstep with the story's own advance to `Ready`, per
  `Implementation/Pipeline.md`'s "task status moves in lockstep with the
  story" rule.

---

**Product-owner pass (`/plan-sprints`, 2026-08-17) — grouped into
`SPRINT-055`, bundled with `BUGFIX-03-US-01` per explicit operator
instruction ("bundle the bugfix into REQ-SB-68's own sprint rather than
spinning up a separate one for it").** Left to this pass's own default
dependency/complexity partitioning, this story would have landed in its own
single-story sprint (no `depends_on` edge connects either story's tasks to
the other's) — the bundling is a directive followed, not a partition
re-derived. No false `depends_on` edge invented between the two stories.
Task order within the sprint: this story's own `T01→T02→T03→T04` chain
first, `BUGFIX-03-US-01`'s own `T01→T02` chain second (a placement choice,
not a dependency claim — see the sprint's own Grouping Rationale for the
reasoning). `gate: clear` for this pass — advances the sprint's own
`Draft → Ready`; this story's own standing `ADR-045`/trigger-3 flag stays
unchanged, a standing breadcrumb, per this project's own established
`SPRINT-051`/`REQ-SB-65-US-01` precedent. Full reasoning:
`Implementation/Sprints/SPRINT-055-non-blocking-capture-dispatch-and-thread-attachment-fix.md`.

---

**Coder pass, 2026-08-17 — `T01` `Done`.** `AC-01` (the story's only
no-screen AC) verified live against the real running backend, real
Outlook/Compass: a genuinely in-flight manual `run_capture_now` no
longer blocks a concurrent `GET /agents`. Full evidence:
`Implementation/Tasks/REQ-SB-68-US-01-T01-non-blocking-manual-capture-dispatch.md`
→ `## Implementation Log`. Story `status:` advances `Ready → In
Progress` (`T02`-`T04` remain `Ready`, not yet built — out of `T01`'s
own scope). `gate:` stays `flagged` unchanged — the standing
`ADR-045`/trigger-3 flag is a human-review item independent of build
progress, not resolved by any task completing.

---

**Coder pass, 2026-08-17 — `T02` `Done`.** `T02` carries no locked AC of
its own (`AC-02`-`AC-07` are genuinely observable only once `T04` wires
a real page around `T03`'s endpoint, per the decomposer's own
AC-to-task mapping). Persisted per-job run-state tracking
(`.second-brain/job_run_state.json`,
`agent_schedule_registry._mark_run_started`/`_mark_run_finished`/
`get_job_run_states()`) landed exactly per `ADR-045` point 4 and the
decomposer's own disclosed read-side enumeration refinement (covered
agent ids read from `skill_registry._MIGRATION_GRANT_SEED[
"run_capture_now"]`, never re-hardcoded). Verified: 5 non-AC smoke
checks against a `VAULT_PATH`-scratch double vault, PLUS a real
end-to-end live check against the real running backend/Outlook/Compass/
vault — a real manually-triggered `run_capture_now` dispatch was
observed transitioning `job_run_state.json` from `running: true`
(`elapsed_seconds` growing continuously across an ~8-minute real
capture pass) to `running: false` with a real `last_duration_seconds`
(`473.95s`) and `last_outcome: "success"`, while the backend stayed
fully responsive throughout. Full evidence:
`Implementation/Tasks/REQ-SB-68-US-01-T02-per-job-run-state-tracking.md`
→ `## Implementation Log`. Story `status:` stays `In Progress`
(`T03`-`T04` remain `Ready`, not yet built). `gate:` stays `flagged`
unchanged — the standing `ADR-045`/trigger-3 flag is a human-review
item independent of build progress, not resolved by any task
completing.

---

**Coder pass, 2026-08-17 — `T03` left `status: Blocked` (not `Done`) —
its own in-scope code is built exactly per spec, but a real,
pre-existing, unrelated `HTTP 500` on `GET /system-health` (confirmed
live BEFORE any of `T03`'s own changes, root-caused via a real
traceback, not guessed) blocks end-to-end live verification.** Root
cause: `.second-brain/agent_providers.json`'s `"assignments"` map
carries a stale key, `"email-capture"`, orphaned since the already-`Done`
`REQ-SB-55-US-01-T08`/`ADR-043` renamed that agent to
`"email-capture-pipeline"` — `provider_registry.py::_load_state()` only
ever adds new assignments, never prunes stale ones, so
`system_health.py::_providers_with_agent_names()` (built by the
already-`Done` `REQ-SB-31-US-01`) crashes dereferencing the orphaned id.
Both real fix locations (`provider_registry.py`'s own reconciliation
logic; a defensive guard in `_providers_with_agent_names()`) are outside
`T03`'s own `## Files to Modify` and its own explicit `## Out of Scope`
carve-out — escalated rather than patched in place, mirroring
`ESC-012`'s own identical "leave the faithful, already-built code in
place, mark the task `Blocked`" precedent. Confirmed `T03`'s own change
neither causes nor worsens the 500 (identical traceback before and
after; `T03`'s own new `"scheduling"` key is never even reached).
`T03`'s own `get_system_health()` composition logic is verified correct
**in isolation** (direct calls to `agent_schedule_registry.
get_job_run_states()` and `mcp_mount_reachable()` both succeed and
return the expected shape) but not verifiable end-to-end through the
real endpoint until the escalated defect is resolved. Story `status:`
stays `In Progress`; `T04` cannot start (`depends_on: [T03]`, not yet
`Done`). Full evidence: `Implementation/Tasks/
REQ-SB-68-US-01-T03-scheduling-system-health-extension.md` → `##
Implementation Log`; full root-cause write-up: `ESCALATIONS.md` →
`ESC-042`; human decision pointer: `REVIEW-QUEUE.md`.

---

**Coder pass, 2026-08-17 — `T03` `Done`.** Operator decision on
`ESC-042` (Option (a)): `provider_registry.py::_load_state()` now prunes
any `"assignments"` key whose agent id no longer exists in
`agent_registry.list_agents()`, symmetric with that same function's
existing add-missing-assignment loop — applied as `ESC-042`'s own
resolving artefact, not as a change to `T03`'s own `## Files to Modify`
(`system_health.py` needed zero further change). Live-verified against
the real running backend/vault: the stale `"email-capture"` assignment
key was confirmed present, then confirmed pruned automatically on the
next `_load_state()` call (triggered by a real `GET /system-health`).
`GET /system-health` now returns a real `200` with the exact
`{"mcp", "providers", "disabled_agents", "scheduling"}` shape. All 3 of
`T03`'s own non-AC smoke checks passed live, including a real
`running: true` (growing `elapsed_seconds`) → `finished` transition
observed through the actual endpoint. Full evidence: `Implementation/
Tasks/REQ-SB-68-US-01-T03-scheduling-system-health-extension.md` → `##
Implementation Log`; `ESCALATIONS.md` → `ESC-042` (`Status: Resolved`).
Story `status:` stays `In Progress` (`T04` remains to build — not this
task's scope; its own `depends_on: [T03]` is now satisfied). `gate:`
stays `flagged` unchanged — the standing `ADR-045`/trigger-3 flag is a
separate, still-open human-review item, untouched by this resolution.

---

**Coder pass, 2026-08-17 — `T04` `Done`. Story `status:` advances `In
Progress → Done` — all 4 tasks (`T01`-`T04`) now `Done`, all 7 locked ACs
(`AC-01`-`AC-07`) verified.** The new "Scheduling" section (`SystemHealthPage.tsx`,
`system-health/client.ts`) replaces the former "Last capture run" region
outright, same position, per the architect's own locked design.
`AC-02`-`AC-07` all verified against real, live data from the real
running backend/vault/Outlook/Compass: a real in-flight
`email-capture-pipeline` run showed genuinely growing `elapsed_seconds`
(`AC-02`) then a real `580.55s` success (`AC-03`); `meeting-capture`'s
real, honest "not yet available" on-demand result surfaced as a real
failure with its real message, not stale/blank (`AC-04`); `todo-capture`
showed the honest "no runs yet" placeholder before its first dispatch
(`AC-05`); a genuine `trigger="scheduled"` tick (fired by a real,
temporary per-agent schedule against the live `AsyncIOScheduler`, not a
manual HTTP call) correctly updated the Scheduling data through the
identical, trigger-agnostic `dispatch_with_shared_lock` mechanism a
manual run already uses, with concurrent `GET /agents` staying responsive
throughout and a concurrent second dispatch correctly skipped, not
overlapped (`AC-06`); `compass-expert`/`build_knowledge` never appeared
among the 3 covered-job rows (`AC-07`). Every rendering branch was traced
against this real data against the task's own literal, unmodified JSX.
**Disclosed: no browser/screenshot tool was available this session** —
same limitation `REQ-SB-66-US-01-T05`/`T07` already disclosed; verified
instead via `tsc`/`oxlint` clean + exact-code-match + live-data-trace, per
this task's own `## Implementation Log`. The operator's own stated plan
is to perform the live-browser confirmation pass personally. `gate:`
stays `flagged` — the standing `ADR-045`/trigger-3 flag from the
architect pass is a human-review item independent of build completion,
not resolved by the story completing. `BACKLOG.md`'s `REQ-SB-68` row
updated to `Done`. `SPRINT-055` stays `In Progress`
(`BUGFIX-03-US-01`'s own `T01`/`T02` remain outstanding in the same
sprint). Full evidence: `Implementation/Tasks/
REQ-SB-68-US-01-T04-scheduling-view-frontend.md` → `## Implementation
Log`.
