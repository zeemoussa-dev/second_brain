---
id: REQ-SB-47-US-01
title: Per-Agent Scheduler — Schedule tab (configure/edit/remove/run-now/run history) generalized across agents/capabilities, built together with REQ-SB-45's shared Outlook-COM serialization
requirement_ids: [REQ-SB-47, REQ-SB-45]
requirement_section: "REQ-SB-47: Per-Agent Scheduler (built together with REQ-SB-45: Shared Serialization for Scheduled Background Jobs, per REQ-SB-45's own 2026-08-14 'Activated' breadcrumb and operator-confirmed merge)"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-037 created — Per-Agent Scheduler + shared Outlook-COM dispatch lock, extends ADR-005/ADR-029). Architect pass resolved both the shared-lock's real location (relocated to a new app/business/agent_schedule_registry.py, mirroring ADR-029's own precedent — no business→scheduling import edge) and the new invoke_skill `\"scheduled\"` trigger's composition with ADR-029's gate. Per the operator's own relayed scoping decisions (see ## Notes), the shared lock is explicitly in-process only (the SPRINT-030 two-process collision stays a disclosed, out-of-scope operational-hygiene risk) and meeting-capture/todo-capture's run_capture_now stays the existing honest not-available stub. Net-new-design-needed (no Schedule tab prototype coverage) remains open independent of this ADR — a /design pass or explicit operator sign-off to skip one is still recommended before the coder builds the frontend. See REVIEW-QUEUE.md and ESC-033."
sprint: "SPRINT-045"
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-47-US-01 — Per-Agent Scheduler + Shared Outlook-COM Serialization

## Story

**As a** Second Brain user
**I want** a Schedule tab on an agent's detail panel where I can configure a
recurring schedule targeting one of that agent's own granted, schedulable
capabilities, see that agent's real run history, edit or remove an existing
schedule, and trigger an immediate on-demand run — with the guarantee that no
two Outlook-COM-touching runs (scheduled, on-demand, across any agent) ever
execute concurrently against the same Outlook/Compass session
**So that** I can manage per-agent automation trustworthily from one place,
instead of being limited to today's single hardcoded hourly email-capture
job with no UI and no visible run history, and without risking the exact
kind of silent double-run collision a real live verification session already
hit once

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-47: Per-Agent Scheduler* and *REQ-SB-45:
  Shared Serialization for Scheduled Background Jobs*. Per REQ-SB-45's own
  "Update, 2026-08-14 — Activated" breadcrumb: "`REQ-SB-47` (Per-Agent
  Scheduler) introduces exactly that second real caller — the operator
  confirmed building this requirement's shared lock as part of `REQ-SB-47`'s
  own work, rather than continuing to defer it." REQ-SB-47's own breadcrumb
  states the identical merge from its own side: "this is exactly the second
  real caller `REQ-SB-45`'s shared-lock generalization needs — operator-
  confirmed 2026-08-14: build `REQ-SB-45` as part of this requirement's own
  work, not as a separate later pass." This story is that single merged
  piece of work, anchored on `REQ-SB-47` for its story ID per the analyst's
  own task-level instruction, `requirement_ids: [REQ-SB-47, REQ-SB-45]`.

- **What the real code actually does today (read directly, not assumed from
  the PRD's own abstraction):**
  - `app/scheduling/capture_scheduler.py` wires exactly **one** APScheduler
    job (`hourly_capture`, `IntervalTrigger(hours=1)`) plus one unconditional
    app-start trigger, both funneled through `run_capture_if_idle`, guarded
    by one module-level `_capture_run_lock = asyncio.Lock()` that only
    prevents this one job from overlapping *itself* (app-start run vs.
    hourly-boundary run) — confirmed by direct reading, matching REQ-SB-45's
    own breadcrumb characterization exactly.
  - `run_capture_if_idle` calls `email_classification.
    run_capture_and_record_completion`, which — despite its name — is **not**
    single-agent. It is a "blob tick" that sequentially drives THREE
    independently-working-mode-gated capture steps every time it runs:
    `email-capture`, then `meeting-capture` (REQ-SB-08), then `todo-capture`
    (REQ-SB-09), each wrapped in its own try/except and each independently
    checking `working_mode_registry.get_agent_working_mode(<agent>)`
    (Autonomous runs it and writes a `run_event`/`run_error`; Supervised
    creates a `trigger="background"` pending-approval instead; Manual stays
    dormant with no history entry at all). `capture_scheduler.py` itself
    "requires zero changes since it already treats this function as an
    opaque unit" (the function's own docstring). This is the single most
    important real-code fact this story's design must reconcile: **today's
    one hardcoded job is already secretly multi-agent**, not the
    single-agent job the PRD's "today only `email-capture` has any real
    scheduling at all" framing implies.
  - `app/business/agent_activity.py` (REQ-SB-11, Done) already aggregates
    every agent's `"run_event"`/`"run_error"` history entries
    (`vault_writer.load_agent_history`, agent-id-keyed, chronological,
    recomputed fresh on every call, no caching) into one cross-agent Agent
    Activity view. `vault_writer.append_agent_history_entry(agent_id, kind,
    text, pending_approval_id=None)` is the one write path every real
    caller already uses (the blob tick, `agents_router.py`'s dispatch/chat
    paths, `pending_approvals_router.py`'s Approve endpoint,
    `knowledge_bootstrap.py`). `kind` is an untyped `str` and `text` is free
    text — both are wide enough to carry "which capability ran" without any
    schema change.
  - `app/business/skill_registry.py`'s `invoke_skill(agent_id, skill_id,
    args, trigger: Literal["chat", "direct", "hub_routed"])` is the ONE
    real gated dispatch path every real caller (the direct-invoke router,
    `agents_router.py`'s dispatch fork, `knowledge_bootstrap.py`'s
    Hub-routed call) already passes through (ADR-029 point 1) — Manual mode
    only special-cases `trigger == "hub_routed"`; Supervised mode gates on
    `skill["mutates"]`, regardless of trigger.
  - `app/business/skill_tools.py`'s `SKILLS` catalog carries exactly 4
    `"mutates": True` migrated ids (`run_capture_now`, `pause_schedule`,
    `rebuild_person_note`, `build_knowledge`) — but their REAL handlers are
    far less complete than "4 real candidates" implies, confirmed by direct
    reading, not assumed:
    - `run_capture_now(agent_id)` is real **only** for `agent_id ==
      "email-capture"` (calls `email_classification.
      run_capture_and_record_completion` — the same blob the hourly job
      already calls); every other agent, **including `meeting-capture` and
      `todo-capture`, whose own real capture logic exists and already runs
      correctly inside the background blob tick**, gets the honest
      `{"available": False, ...}` stub on this on-demand path (their real
      logic was "wired to the BACKGROUND scheduler only, never this
      on-demand path" — the handler's own docstring, confirmed).
    - `build_knowledge(agent_id)` is real for `compass-expert` (delegates to
      `knowledge_bootstrap.bootstrap_agent_knowledge`).
    - `pause_schedule()` and `rebuild_person_note()` have **zero** real
      handler for any agent today — both always return the honest
      not-available stub, unconditionally.
  - ADR-029's own gate lives *inside* `invoke_skill` precisely because it is
    the one function every real call site already passes through
    unconditionally, avoiding an `ADR-003` layering violation a
    `business`-layer caller (`knowledge_bootstrap.py`) would otherwise hit
    reaching into `api/agents_router.py`. This precedent matters directly for
    where this story's shared lock and "run now" dispatch must live (see
    Notes).

- **Real-code grounding is why this story is written at the behavioral level
  and leaves several concrete mechanism choices to the architect (flagged),
  rather than the analyst quietly picking one** — the four "genuinely open"
  design questions the task brief asked to be resolved with a sane default
  where reasonably possible are addressed below; two resolve cleanly, two
  surface genuine architecture-level forks that are named in full in
  `## Notes` and flagged rather than guessed (Pipeline.md MUST-FLAG trigger
  1/8).

  1. **Schedule-definition shape — resolved: interval only (a numeric value
     + minutes/hours unit per agent-capability pair), not a cron
     expression.** This is the simplest buildable generalization of the
     only real precedent that exists (`IntervalTrigger(hours=1)`, ADR-005),
     nothing in either requirement's PRD text asks for cron-level
     expressiveness, and REQ-SB-45's own breadcrumb explicitly favors
     "the right-sized fix... mirroring `_capture_run_lock`'s own
     already-proven shape rather than introducing new machinery" — the same
     right-sizing logic extends naturally to the schedule shape itself.
     Disclosed as a material assumption (MUST-FLAG trigger 1) since the PRD
     does not explicitly rule out something richer — a human should confirm
     interval-only is sufficient before task-level design commits to it.

  2. **Which capabilities are schedulable — resolved with a real, disclosed
     gap: any Skill currently granted to the target agent with `"mutates":
     True`** (today's 4: `run_capture_now`, `pause_schedule`,
     `rebuild_person_note`, `build_knowledge`) is offered in the Schedule
     tab's capability picker; a read-only Skill (e.g. `ask_question`,
     `web-research`) is never offered — scheduling "answer a question" on a
     recurring basis has no sensible recurring-job meaning, matching the
     brief's own framing. Whether a specific (agent, capability) pair
     currently resolves to a REAL handler or an honest not-available stub
     is **not** re-litigated by a new readiness flag — a scheduled/run-now
     tick for a stub capability simply produces the same honest
     "not available" outcome `invoke_skill`'s dispatch already produces
     today for a direct click, recorded to run history exactly like any
     other outcome. This reuses an existing, already-proven honest-failure
     pattern rather than inventing new capability-readiness metadata — a
     sane default, not flagged on its own.

     **Genuinely ambiguous, flagged:** `meeting-capture`'s and
     `todo-capture`'s `run_capture_now` are stubs on this on-demand path
     TODAY even though their real capture logic already runs correctly
     every hour via the background blob tick — so a naive generalization
     would let the user configure a working-looking schedule UI for, say,
     `meeting-capture`'s "Run Capture Now" that would honestly, but
     unhelpfully, report "not available" on every tick, which is a strictly
     worse experience than today's blob tick that already really runs
     meeting-capture. Whether this story should (a) ship the generalized
     mechanism with this gap honestly disclosed (a known, named limitation,
     not a regression — meeting/todo-capture keep running via today's blob
     tick regardless, they just can't ALSO be independently scheduled
     through the new UI yet), or (b) also wire real per-agent on-demand
     handlers for meeting-capture/todo-capture as part of this same story
     (which would mean splitting or duplicating logic out of the blob tick —
     materially larger scope than "generalize the scheduling mechanism") is
     a genuine, consequential scope fork with two defensible answers. Not
     guessed here — flagged for the architect/human (see Notes).

  3. **Run history — resolved: reuse `REQ-SB-11`'s existing Agent Activity
     log directly, unchanged in shape.** Confirmed sufficient by reading
     the real code (not assumed): entries already carry `agent_id` (which
     agent), `timestamp` (when), `kind` (`run_event`/`run_error` = success/
     failure), and a free-text `text` this story extends to also name which
     capability ran (e.g. `"Scheduled run — Run Capture Now — completed, 3
     email(s) filed"` / `"Run now — Run Capture Now — not available"`). No
     new parallel store, no schema change to `vault_writer.
     append_agent_history_entry`. Sane default — not flagged.

  4. **The shared lock (REQ-SB-45) — resolved with two real forks, both
     flagged, not guessed:**
     - **Location:** generalize `capture_scheduler.py`'s own module
       (extended to own N configured per-agent-capability jobs, not
       duplicated into a new parallel module) — mirrors REQ-SB-45's own
       explicit "mirroring `_capture_run_lock`'s own already-proven shape"
       instruction, and every real trigger source today already funnels
       through this module. But "run now" is a `business`-layer dispatch
       (`skill_registry.invoke_skill` → `_dispatch_skill`) that would need
       to acquire this SAME lock before running — a new `business →
       scheduling` dependency this codebase has never had (today
       `scheduling` depends on `business`, one-directional, ADR-005 point
       5). This is the exact class of layering question ADR-029 itself had
       to resolve for the working-mode gate (see Context) — flagged for the
       architect to resolve the same way: either accept the new dependency
       edge, or relocate the lock to a place both layers can reach without
       violating `ADR-003`.
     - **Cross-process scope:** REQ-SB-45's own breadcrumb names its
       motivating real evidence explicitly — `SPRINT-030`'s own live
       verification session "accidentally ran two full capture passes
       concurrently (two backend processes racing on the same live Outlook/
       Compass calls) after a coder mistakenly started two server
       instances." That collision was **two separate OS processes**, each
       with its own independent Python interpreter and therefore its own
       independent `asyncio.Lock` object — a generalized **in-process**
       lock, no matter how correctly it covers every job type within one
       process, **cannot** prevent that specific collision; only a
       cross-process-safe mechanism (e.g., a lock file on disk under
       `.second-brain/`, checked/created before any Outlook-COM-touching
       dispatch starts, consistent with this project's established
       JSON-file/no-DB approach) actually would. Whether REQ-SB-45's own
       Acceptance text ("only one actually runs... across all of them") is
       meant to reach this cross-process case, or is understood more
       narrowly as "across job TYPES within one running process" (leaving
       "don't start two server instances" as an operational-discipline
       matter, not a code fix), is genuinely undecided by the PRD text —
       the two readings require materially different implementations. Not
       guessed here — flagged, and Scenario 7 below is deliberately written
       at the OBSERVABLE-property level (no two COM-touching runs ever
       overlap, regardless of origin) rather than committing to one
       mechanism, so the decomposer/architect can lock its AC against
       whichever mechanism the architect resolves.

  - **Working-mode-gate composition (ADR-029) — resolved, disclosed, real
    code change, flagged for its own ADR touch:** add a new `"scheduled"`
    trigger literal to `invoke_skill`'s `Literal["chat", "direct",
    "hub_routed"]` (→ adds `"scheduled"`) for fully-automatic ticks with no
    user presently in the loop — this mirrors the semantic the blob tick's
    own bespoke `trigger="background"` pending-approval calls already use
    (a real, already-shipped literal, just not one `invoke_skill` itself
    currently accepts), generalized into the one real gated dispatch path
    instead of staying a one-off. Manual mode gains one new branch —
    `mode == "manual" and trigger == "scheduled"` → skip silently, no
    history entry — mirroring the blob tick's own existing per-capture-type
    "Manual stays dormant this tick" precedent exactly, now generalized to
    any scheduled capability rather than re-implemented per capture type.
    On-demand "**run now**" reuses the **existing** `"direct"` literal
    unchanged — a user is presently, explicitly clicking a button, and
    Manual mode already lets `"direct"` calls through today (Manual blocks
    *automatic*/hub-routed action, not an explicit user request) — so no new
    literal or gate branch is needed for run-now. This is a real change to
    `invoke_skill`'s signature and gate body — composes with `ADR-029`,
    needs the architect's sign-off before the decomposer locks any AC that
    depends on it. Flagged.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: Configuring a new recurring schedule for an agent's capability

```gherkin
Given the user opens an agent's detail panel for an agent that has at least
    one granted, mutating capability (e.g. email-capture's "Run Capture Now")
When the user opens the agent's Schedule tab, selects that capability, sets
    a recurring interval (a numeric value plus a minutes/hours unit), and
    saves
Then a recurring schedule is created for that agent-capability pair
  And the Schedule tab shows the schedule as active, showing the capability
    and the configured interval
```
<!-- AC-ID: REQ-SB-47-US-01-AC-01 -->

### Scenario 2: Only the agent's own granted, mutating capabilities are offered as schedulable

```gherkin
Given the user is configuring a new schedule on an agent's Schedule tab
Then the capability picker lists only capabilities currently granted to that
    agent that are classified as mutating
  And a read-only capability (e.g. "Ask a Question", "View Channel Status")
    never appears in the picker
  And a capability not granted to this agent never appears in the picker
```
<!-- AC-ID: REQ-SB-47-US-01-AC-02 -->

### Scenario 3: Viewing that agent's real run history on the Schedule tab

```gherkin
Given an agent has one or more real run-history entries already recorded
    (from a prior scheduled tick, a prior run-now, or any other real run)
When the user opens that agent's Schedule tab
Then the user sees that agent's own real run history — timestamp, which
    capability ran, and whether it succeeded or failed — reflecting the same
    underlying history REQ-SB-11's Agent Activity view already shows, not a
    separate or fabricated list
```
<!-- AC-ID: REQ-SB-47-US-01-AC-03 -->

### Scenario 4: Editing an existing schedule

```gherkin
Given an agent already has an active schedule configured
When the user changes its interval, or the capability it targets, on the
    Schedule tab and saves
Then the schedule updates in place — the same (agent, prior-capability)
    entry is replaced, not duplicated
  And the next tick reflects the newly-saved interval/capability, with no
    backend restart required — the previous configuration no longer applies
```
<!-- AC-ID: REQ-SB-47-US-01-AC-04 -->

### Scenario 5: Removing a schedule

```gherkin
Given an agent has an active schedule configured
When the user removes it from the Schedule tab
Then no further scheduled ticks occur for that agent's removed schedule,
    with no backend restart required
  And "Run now" remains available for that agent's capabilities regardless —
    removing a schedule does not disable on-demand runs
```
<!-- AC-ID: REQ-SB-47-US-01-AC-05 -->

### Scenario 6: Triggering an immediate on-demand run ("run now")

```gherkin
Given the user is on an agent's Schedule tab, with or without an active
    schedule configured
When the user clicks "Run now" for one of that agent's schedulable
    capabilities
Then that capability runs for that agent immediately
  And the resulting outcome — success, honest failure, or honest
    "not available" — is recorded to that agent's run history and visible on
    the Schedule tab
```
<!-- AC-ID: REQ-SB-47-US-01-AC-06 -->

### Scenario 7: No two Outlook-COM-touching runs ever execute concurrently, across any agent or trigger source (the shared-lock property — REQ-SB-45)

```gherkin
Given two different agents each have an eligible Outlook-COM-touching run
    that would otherwise be ready to start at effectively the same moment —
    for example, one agent's scheduled tick becoming due at the same instant
    the user clicks "Run now" for a different agent's capability
When both become eligible to run at the same time, within the same running
    backend process
Then only one of them actually executes against Outlook/Compass at a time
  And the other is skipped — recorded honestly (e.g. "skipped — another run
    is already in progress") — rather than starting and running concurrently
    against the same COM resource
  And at no point do the two runs' real dispatch calls overlap in time —
    this property is guaranteed for any two dispatches racing within one
    live backend process (the shared, in-process dispatch lock); two
    independently-running backend processes racing against the same real
    Outlook/Compass session, as happened live during this project's own
    SPRINT-030 verification session, is a disclosed, deliberately
    out-of-scope operational-hygiene risk this in-process mechanism does not
    address (see the story's own Notes/ADR-037)
```
<!-- AC-ID: REQ-SB-47-US-01-AC-07 -->

### Scenario 8: A Manual-mode agent's scheduled tick stays dormant, but "run now" still works

```gherkin
Given an agent's own working mode is set to Manual
  And that agent has an active schedule configured for one of its
    capabilities
When the scheduled tick for that agent becomes due
Then the scheduled run is skipped silently — no run executes and no history
    entry is recorded, mirroring this agent's own existing Manual-mode
    "stays dormant" behavior for background ticks
When the user instead clicks "Run now" for that same agent and capability
Then the run executes immediately regardless of the agent's Manual mode,
    since the user is directly and presently requesting it
```
<!-- AC-ID: REQ-SB-47-US-01-AC-08 -->

### Scenario 9: Scheduling a capability the agent doesn't have, or a non-mutating capability, is refused

```gherkin
Given the user attempts to configure a schedule targeting a capability the
    agent has not been granted, or a capability that is not classified as
    mutating
When the user tries to save the schedule
Then the schedule is refused with a clear, honest message explaining why
  And no schedule is created
```
<!-- AC-ID: REQ-SB-47-US-01-AC-09 -->

## Affected Screens

- `html-prototype/agents-map.html` — the agent detail `.side-panel-agent`
  block needs a new "Schedule" tab/section (configure/edit/remove/run-now/
  run-history), alongside its existing Settings/Chat/History-equivalent
  sections. **No approved prototype coverage exists anywhere for this** — see
  Notes → Prototype parity.

## Dependencies

- **Related to, not blocked by:** `REQ-SB-46` (Agent Creation Wizard
  Redesign, `Draft`, flagged) — its own Step 4 "Schedule" Trigger choice
  already anticipates this story's Schedule tab as where real schedule
  configuration happens post-creation (recorded there only as intent). This
  story does not depend on `REQ-SB-46` shipping first, and does not change
  anything `REQ-SB-46-US-01` already specced.
- **Composes with, unchanged:** `REQ-SB-11` (Agent Activity & Error
  Observability, `Done`) — this story's run-history requirement reuses its
  existing `run_event`/`run_error` log directly (see Context point 3); no
  change to `app/business/agent_activity.py` or its own `Done` story's ACs.
- **Composes with, extends:** `REQ-SB-39-US-02` / `ADR-029` (Skills working-
  mode gate, `Done`) — this story's "run now"/scheduled-tick dispatch is
  designed to route through the SAME `invoke_skill` gate every other trigger
  already uses, adding one new `trigger` literal (see Context's own
  Working-mode-gate composition point). This is an extension, not a
  reopening — `REQ-SB-39-US-02`'s own locked ACs are untouched.
- **External:** a `/design` pass on the new Schedule tab is strongly
  recommended before `/plan-tasks` commits to a concrete layout (see
  `gate_reason`), but per this project's own established precedent
  (`REQ-SB-46-US-01`'s identical framing), it is not a hard blocker — the
  pipeline may proceed to `/plan-tasks` with this story `gate: flagged`.

## Constraints

- The shared serialization mechanism must not become a full task-queue or
  message broker — REQ-SB-45's own PRD text explicitly forbids this
  ("Explicitly NOT a full task-queue/broker... a queue would be
  disproportionate new infrastructure for a single-user local app"). Any
  resolution the architect picks must stay JSON-file/in-process-appropriate,
  mirroring `_capture_run_lock`'s own proven shape as closely as the
  resolved cross-process question (Context point 4) allows.
- A scheduled or on-demand run for a capability with no real handler today
  (`pause_schedule`, `rebuild_person_note`, and `run_capture_now` for any
  agent other than `email-capture`) must return the SAME honest
  "not available" outcome `invoke_skill`'s dispatch already returns for a
  direct click — never a fabricated success, and never a silent crash.
- Today's existing hourly blob tick (`email-capture` + `meeting-capture` +
  `todo-capture`, `capture_scheduler.py`) must not silently stop running, or
  silently double-run alongside a newly-configured per-agent schedule for
  one of those same three agents, as a side effect of this story's
  generalization — the architect's `/plan-tasks` pass must explicitly
  resolve how the existing blob tick and any new per-agent schedule for the
  same agent coexist (this is part of the flagged scope in Context point 2).
- No two Outlook-COM-touching runs may ever be observably concurrent,
  regardless of trigger source or originating process (Scenario 7) — this is
  the one property this entire story exists to guarantee and must not be
  weakened by any task-level implementation choice.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| `REQ-SB-47-US-01-T01` | backend | `invoke_skill` — new `"scheduled"` trigger + Manual-mode silent-skip branch | `app/business/skill_registry.py` | `Implementation/Tasks/REQ-SB-47-US-01-T01-invoke-skill-scheduled-trigger.md` |
| `REQ-SB-47-US-01-T02` | backend | New `agent_schedule_registry.py` — schedule CRUD + shared dispatch lock + live-scheduler seam | `app/business/agent_schedule_registry.py`, `app/data_access/vault_writer.py` | `Implementation/Tasks/REQ-SB-47-US-01-T02-agent-schedule-registry.md` |
| `REQ-SB-47-US-01-T03` | backend | `capture_scheduler.py` generalization — publish live scheduler, register per-schedule jobs, swap to shared lock | `app/scheduling/capture_scheduler.py` | `Implementation/Tasks/REQ-SB-47-US-01-T03-capture-scheduler-generalization.md` |
| `REQ-SB-47-US-01-T04` | backend | New `agent_schedules_router.py` — `GET`/`POST`/`PATCH`/`DELETE` schedule CRUD | `app/api/agent_schedules_router.py`, `app/main.py` | `Implementation/Tasks/REQ-SB-47-US-01-T04-schedule-crud-endpoints.md` |
| `REQ-SB-47-US-01-T05` | backend | `POST .../run-now` endpoint through the shared dispatch lock | `app/api/agent_schedules_router.py` | `Implementation/Tasks/REQ-SB-47-US-01-T05-run-now-endpoint.md` |
| `REQ-SB-47-US-01-T06` | frontend | New Schedule tab on `AgentDetailPanel.tsx` (configure/edit/remove/run-now/run history) | `AgentDetailPanel.tsx`, `agentSchedulesApiClient.ts`, `skillsApiClient.ts` | `Implementation/Tasks/REQ-SB-47-US-01-T06-frontend-schedule-tab.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **A full cron-style schedule expression** — interval-only (Context point 1)
  is this story's resolved scope; a richer expression language is deferred
  unless the human redirects this at review.
- **Building real, non-stub handlers for `pause_schedule` and
  `rebuild_person_note`** — both stay honest "not available" stubs; this
  story generalizes the SCHEDULING mechanism, it does not complete
  `REQ-SB-39-US-02`'s own still-open handler gaps for these two ids.
- **Whether meeting-capture/todo-capture's `run_capture_now` gets a real
  on-demand handler** — genuinely open, flagged in Context point 2, not
  decided here.
- **A full task-queue/broker, retry policy, or persisted job history beyond
  reusing REQ-SB-11's existing log** — explicitly out of scope per REQ-SB-45's
  own PRD text (Constraints).
- **REQ-SB-46's own wizard Step 4 Schedule-trigger UI** — that story's own
  scope (recording intent only); this story is what its placeholder message
  points to, not the other way around.

## Notes

**Prototype parity (agents-map.html's agent detail `.side-panel-agent`
block):**

- Settings / Chat / History-equivalent sections — **out of scope for this
  story**, already real and shipped in `AgentDetailPanel.tsx`'s own `tabs`
  (`overview`, `chat`, `history`, `settings`, `gaps`); this story adds a new
  tab alongside them without touching their own existing content.
- **Schedule tab (configure schedule, capability picker, interval, run
  history, edit, remove, run-now) — net-new design needed.** Confirmed by
  direct inspection: `html-prototype/agents-map.html`'s `.side-panel-agent`
  blocks (lines ~2341 onward) carry Settings/Actions/Chat/History-equivalent
  sections only; no tab-bar control pattern, no schedule-configuration
  control (interval picker, capability picker), and no run-history list
  presentation exist anywhere in the prototype today. `REQ-SB-46-US-01`'s
  own prior, independent finding ("no popup-modal/step-bar/FAB pattern
  exists anywhere") corroborates that this general area of the prototype has
  not yet received a design pass for any of these newer, richer agent-detail
  interactions.

**Why this is flagged, not cleared:**

1. **Architecture-decision-needed (Pipeline.md MUST-FLAG trigger 3/8, via
   the architect's own future ADR touch)** — the shared lock's real
   location (a new `business → scheduling` dependency edge, or a
   relocation, mirroring ADR-029's own precedent reasoning), its
   cross-process scope (in-process `asyncio.Lock` generalization vs. a
   cross-process lock-file mechanism — the two readings materially differ
   and only one actually catches the literal SPRINT-030 collision REQ-SB-45
   cites as its own motivating evidence), and the new `"scheduled"` trigger
   literal's composition with `ADR-029`'s gate are all real, disclosed
   architecture forks, not resolvable at this behavioral-spec level. See
   Context point 4 and the Working-mode-gate composition point in full.
2. **Genuinely ambiguous scope fork (trigger 8)** — whether
   meeting-capture/todo-capture's `run_capture_now` on-demand stub gets a
   real handler as part of this same story, or stays a disclosed, known gap
   (Context point 2).
3. **Net-new-design-needed** — no Schedule tab pattern exists anywhere in
   `html-prototype/` today (Prototype parity, above). Recommend running
   `/design REQ-SB-47` before `/plan-tasks` commits to a concrete layout.
4. **Material assumption (trigger 1)** — interval-only scheduling (Context
   point 1) is a disclosed, reasoned default, not PRD-stated; a human should
   confirm it before task-level design commits to it.

Both requirements' PRD text is itself finalized (no `<!-- Draft -->` marker
on either `REQ-SB-45` or `REQ-SB-47`) — this flag is about the real
architecture/design gaps above, not about either requirement's own
finalization state. An `ESCALATIONS.md` entry (`ESC-033`) records this in
full for the permanent log.

`gate: flagged` 2026-08-14, `gate_reason`: see frontmatter (architecture-
decision-needed + net-new-design-needed).

**Architect pass (2026-08-14):**

Wrote `ADR-037` (new — extends `ADR-005`, `ADR-029`, reopens neither). Full
reasoning: `Implementation/Architecture/ADR.md` → `ADR-037`;
`Implementation/Architecture/architecture.md` → "Per-Agent Scheduler &
Shared Outlook-COM Dispatch Lock".

**Operator-relayed scoping decisions, recorded here (not re-derived by the
architect):**

- **The shared lock is scoped in-process only.** It protects the real,
  normal operating case — multiple scheduled agents/capabilities running
  within ONE live server process. "Two separate backend processes racing
  against the same vault" (the literal mechanism behind `SPRINT-030`'s own
  motivating collision) is treated as a known, separate, already-
  partially-documented operational-hygiene risk (`MEMORY.md`'s/
  `Implementation/Learnings.md`'s existing "check for/confirm what a stray
  already-running dev-server process is actually serving before live
  verification" guidance, reconfirmed across `SPRINT-019`/`021`/`022`/
  `029`/`031`) — not something this requirement's application code must
  solve via a cross-process mechanism (e.g. a lock file). Consistent with
  `REQ-SB-45`'s own PRD text explicitly rejecting a full queue/broker as
  disproportionate infrastructure for a single-user local app — a
  cross-process file-lock, with its own stale-lock/crash-recovery problem
  to solve, would be a step in that same disproportionate direction for a
  collision class this project already mitigates operationally. This is a
  genuine, deliberate non-solving of part of what the literal `SPRINT-030`
  collision demonstrated — disclosed, not silently narrowed. Full
  reasoning: `ADR-037`'s Context/Alternatives Considered.
- **`meeting-capture`'s/`todo-capture`'s `run_capture_now` stays the
  existing honest "not available" stub for this pass** — mirroring the
  already-established real/honest-unavailable split from `REQ-SB-39-US-02`.
  Wiring real on-demand handlers for those two capabilities is legitimate
  future work, not required to satisfy this requirement's own Acceptance
  text, which needs the SCHEDULING MECHANISM to be real and generalized,
  not every capability's handler to be real. Both capabilities remain
  schedulable through the new picker (any granted `"mutates": True`
  Skill) — a tick or run-now against either always produces the same
  honest "not available" outcome the direct/chat path already produces
  today, recorded to run history like any other outcome.

**Architecture scope:** §Per-Agent Scheduler & Shared Outlook-COM Dispatch
Lock (`Implementation/Architecture/architecture.md`) — the coder is bounded
to: `app/business/agent_schedule_registry.py` (new — schedule CRUD, the
live-scheduler reference, the shared dispatch lock), `app/data_access/
vault_writer.py` (new `load_agent_schedules_state`/
`save_agent_schedules_state` primitives only), `app/scheduling/
capture_scheduler.py` (surgical edit — remove `_capture_run_lock`, acquire
`agent_schedule_registry.get_shared_dispatch_lock()` instead; extend
`build_scheduler()`/`lifespan()` per the section's own design; the existing
hardcoded `hourly_capture` job and `email_classification.py`'s own
background gate stay unmodified), `app/business/skill_registry.py`
(`invoke_skill`'s new `"scheduled"` trigger literal + Manual-mode branch
only — no other gate logic changes), `app/api/agent_schedules_router.py`
(new), `app/main.py` (router registration), and the frontend's new
Schedule tab on `AgentDetailPanel.tsx` (5th tab, alongside `overview`/
`chat`/`history`/`settings`/`gaps`) plus a new/extended
`agentSchedulesApiClient.ts`. `skill_tools.py`'s `SKILLS` catalog and its 4
migrated handlers are explicitly OUT of this scope — unchanged, per the
operator-relayed stub-behavior decision above. `email_classification.py`'s
own background gate (`ADR-018`/`ADR-020`) is explicitly OUT of scope —
unmodified.

**Still open, independent of this ADR:** the net-new Schedule-tab UI
layout has no approved prototype coverage anywhere in `html-prototype/`
today (confirmed by direct inspection, per this story's own earlier
Notes) — a `/design` pass or an explicit operator sign-off to skip one
remains recommended before the coder builds the frontend half of this
story's scope; not resolved by this architecture pass.

Handing off to the decomposer with `gate: flagged` (trigger 3, ADR-037) —
per Pipeline.md, this does not halt `/plan-tasks`; the decomposer proceeds
so the human reviews the ADR and the resulting tasks together in one pass.
See `REVIEW-QUEUE.md`.

**Decomposer pass (2026-08-14):**

Locked all 9 scenarios as `REQ-SB-47-US-01-AC-01` through `-AC-09` (minor
buildability tightening only — Scenario 1 now names the settled interval
shape (numeric value + minutes/hours unit); Scenario 4/7 now name "no
restart required"/"within the same running backend process" explicitly,
matching `ADR-037`'s own resolved scope — no scenario's observable intent
changed). Created 6 flat-root tasks
(`REQ-SB-47-US-01-T01`…`T06`), one linear `depends_on` chain
(`T01→T02→T03→T04→T05→T06`, acyclic): `T01` (skill_registry's new
`"scheduled"` trigger), `T02` (`agent_schedule_registry.py` — CRUD +
shared lock + live-scheduler seam), `T03` (`capture_scheduler.py`
generalization), `T04` (schedule CRUD router), `T05` (run-now endpoint,
same router file), `T06` (frontend Schedule tab). Every locked AC has at
least one AC-tagged manual verification step across these tasks (several
are intentionally split `partial` across two-three tasks — registry-level,
HTTP-level, and/or UI-level — mirroring `REQ-SB-51-US-01`'s own
recently-landed split-verification precedent for the same class of
registry+router pattern). `AC-07`'s shared-lock property gets its own
dedicated concurrent-dispatch verification step in `T02` (function level)
and a second, real-HTTP-layer confirmation in `T05` — this story's single
highest-risk guarantee, treated as load-bearing per
`Implementation/Learnings.md`'s `SPRINT-031` precedent, not a formality.

Story advances `Draft → Ready`; all 6 tasks written directly at
`status: Ready` (lockstep, per Pipeline.md). `gate` stays `flagged` —
trigger 3 (`ADR-037`, architect-created this pass) is carried forward
unchanged; the decomposer introduced no new MUST-FLAG trigger of its own
(no new material assumption, no contradictory input, no unresolvable
verification gap — the interval-only shape and both architecture forks
were already resolved and disclosed upstream). The human reviews `ADR-037`
and this task breakdown together in one pass, per the story's own
architect-pass framing above. See `REVIEW-QUEUE.md` (unchanged entry,
still open) and `ESC-033` (unchanged, architect-authored).

**Coder pass (2026-08-14, `SPRINT-045`):**

All 6 tasks built and verified live, `T01` → `T06`, in dependency order.
All 9 locked ACs (`AC-01` through `AC-09`) verified with real evidence — no
locked AC blocked. Highlights:

- `AC-07` (the shared-lock property, this story's own single highest-risk
  guarantee) confirmed TWICE, independently: an in-process
  `asyncio.gather` call with explicit start/end timing markers around a
  temporarily-monkeypatched `invoke_skill` (`T02`) proved zero overlap
  between two real dispatches for different agents; separately, a genuine
  real-world race at the HTTP layer (`T05`) — a concurrent `run-now` call
  for a second agent, issued while `email-capture`'s own real, multi-minute
  Outlook-COM blob tick was genuinely in flight — was honestly skipped and
  recorded, reconfirming the same property from a second, unplanned, fully
  real angle.
- `AC-08` (Manual-mode scheduled dormancy vs. run-now) confirmed at both
  the function layer (`T01`) and the HTTP layer (`T05`) — a scheduled tick
  silently records zero history under Manual mode; run-now for the same
  agent/capability produces the byte-identical outcome regardless of mode.
- A real, live-discovered duplicate-history-entry defect in
  `dispatch_with_shared_lock`'s own generic outcome-recording (surfaced by
  actually running the real composed call graph, not trusted from this
  ADR's own illustrative text alone) was found and fixed in-scope during
  `T02` — see that task's own Implementation Log for the full root-cause
  and fix.
- The Schedule tab (`T06`) shipped without a `/design` pass — per this
  story's own already-disclosed, non-blocking flag — verified live via a
  real CDP session (creation/edit/remove/run-now/capability-scoping/
  run-history-parity all confirmed against the real running frontend +
  backend) and visually spot-checked via a real screenshot; still awaiting
  the human's own retroactive design/prototype sign-off (see
  `REVIEW-QUEUE.md`'s updated entry).

`status: Ready → Done`. `gate` stays `flagged` — the original `ADR-037`
review request is now joined by a narrowed, updated ask (retroactive
Schedule-tab layout sign-off); see the updated `REVIEW-QUEUE.md` entry and
each task's own Implementation Log for full detail. `ESC-033` is
unaffected (architect-authored, not resolved or reopened by this coder
pass).
