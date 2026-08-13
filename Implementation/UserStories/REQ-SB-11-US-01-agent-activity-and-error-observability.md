---
id: REQ-SB-11-US-01
title: Chronological background-agent-run activity log, per-communication-channel status, and the honest-failure-recording fix that makes error outcomes visible at all
requirement_ids: [REQ-SB-11]
requirement_section: "REQ-SB-11: Agent Activity & Error Observability"
phase: P1
status: Done
gate: clear
gate_reason: "Resolved 2026-08-13 — the operator delegated ESC-025's placement decision to the orchestrating agent ('make the call yourself, using sane defaults'), which decided a new top-level nav page (not a section grafted onto System Health) — a chronological log has a different shape/interaction model than System Health's current-snapshot status board, mirroring this project's own established 'log/history over time' vs. 'status right now' distinction (My Day's day-navigator precedent), and matching System Health's own precedent of getting its own dedicated nav item rather than being folded into an existing page. ESC-025 flipped to Resolved. /design REQ-SB-11 must still run before /plan-tasks (genuinely net-new UI, no prototype exists yet) — a sequencing dependency, not a gating decision, per the same reasoning REQ-SB-31-US-01 used for its own identical situation."
sprint: "SPRINT-027"
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-11-US-01 — Chronological background-agent-run activity log, per-communication-channel status, and the honest-failure-recording fix that makes error outcomes visible at all

## Story

**As a** Second Brain user
**I want** to see a chronological list of what background agent runs have
happened — email, meeting, and (once built) to-do capture — with whether
each succeeded or failed, plus whether Outlook is currently reachable
**So that** a real capture failure is visible in the UI itself instead of
only discoverable by symptom-chasing (a note that never appeared, a stale
capture timestamp) or digging through server logs

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-11: Agent Activity & Error
  Observability* — "The user can see, from Second Brain's own UI, what
  background agent runs have happened (email/meeting/task/people capture
  and any future recurring job) — whether each succeeded or failed — and
  the current status of communication channels (e.g. whether the
  Hermes-wrapped Outlook skill is currently reachable)." Acceptance: "The
  UI shows a chronological list of background agent runs with outcome
  (success, or error with detail) and a current status indicator per
  communication channel."
- **Related, not overlapping — `REQ-SB-31-US-01` (System Health View,
  `Done`, `SPRINT-019`).** That story's own Context/Notes explicitly named
  this exact distinction and flagged it for whichever of the two was
  specced second — this pass: System Health is a **current-snapshot
  status board** ("is each piece healthy right now" — MCP mount,
  per-agent Provider availability, last capture run's completion
  timestamp), while REQ-SB-11 is a **history/log** shape (every run, with
  its own recorded outcome, in chronological order) plus one net-new
  check System Health does not cover at all (per-communication-channel
  reachability — System Health checks the MCP mount and Providers, never
  Outlook). This story does **not** duplicate or rebuild any of System
  Health's three existing checks — it is additive, a second page/section
  reusing the same "read already-recorded/already-computed signals, plus
  one lightweight in-process live check" philosophy that story
  established, applied to a different shape of data.
- **Real data read directly, not assumed, per this pass's brief:**
  - `app/data_access/vault_writer.py::append_agent_history_entry`/
    `load_agent_history` — a single `.second-brain/
    agent_communication_history.json`, keyed by `agent_id`, each entry
    `{"kind", "text", "timestamp"[, "pending_approval_id"]}`. `kind` is
    one of `"chat_user"` (a user chat message), `"chat_agent"` (an agent
    chat reply), `"run_event"` (a background job outcome or a
    chat-triggered action result), or `"proposal"` (a Supervised-mode
    pending-approval card). This file is **already** the closest thing to
    "background agent run history" in this codebase — but it is
    incomplete for REQ-SB-11's purpose in two concrete, confirmed ways
    (see below), and it also mixes in chat traffic that REQ-SB-11's own
    acceptance text ("background agent runs... succeeded or failed") does
    not ask this story to surface.
  - `app/business/email_classification.py::run_capture_and_record_completion`
    — read directly: on Autonomous mode, **email-capture** writes a
    `"run_event"` entry on every completed run ("Capture run completed —
    N email(s) filed"). **Meeting-capture does not** — its Autonomous
    branch calls `run_capture_for_agent("meeting-capture")` with **no**
    history entry at all, per the function's own comment ("meeting-
    capture's Autonomous branch likewise still just calls its capture
    step with no new history entry, preserving today's exact no-entry
    behaviour"). **Confirmed gap 1: not every background capture agent's
    successful run is even recorded today** — a chronological list built
    directly off today's data would silently omit every meeting-capture
    run.
  - **Confirmed gap 2 — no failure/error outcome is ever recorded,
    anywhere, for any capture pipeline.** `classify_recent_emails` and
    `classify_recent_meetings` each have narrow, **per-item** error
    handling (e.g. a single email's `CompassError` is caught and appended
    to that function's own return list with an `"error"` key) — but
    neither function's own **top-level** entry point is wrapped in a
    `try`/`except`. An exception that escapes per-item handling (e.g.
    `outlook_com.OutlookUnavailable` if Outlook desktop isn't running —
    the exact failure mode `BUG-007`/`BUG-008` already document as real,
    currently `Open` risks) propagates all the way up through
    `run_capture_and_record_completion` and `capture_scheduler.
    run_capture_if_idle`'s `asyncio.to_thread` call, with **zero** history
    entry ever written — the run simply vanishes, untraced, the same
    "crash gap" shape `REQ-SB-31-US-01`'s Scenario 8 already found and
    fixed for the real-time chat path (`graph.py::run_agent_conversation`,
    `ADR-015`'s honest-failure-funnel pattern). **This story cannot honor
    its own literal acceptance text — "outcome (success, or error with
    detail)" — without closing this gap first**; it is not optional
    scope, it is the acceptance text's own explicit "error with detail"
    half.
  - `app/business/agent_orchestration/state.py` — its own docstring
    already documents that `"run_event"` entries are deliberately
    excluded from the chat-message reconstruction path (they aren't
    `HumanMessage`/`AIMessage` turns) — confirming `"run_event"` is
    already understood, in this codebase's own code, as the "background
    job" shape distinct from conversational turns. This story's
    cross-agent aggregation reads exactly this shape.
  - `app/data_access/outlook_com.py::_connect_namespace` — the exact
    mechanism every existing Outlook read (mail, calendar) already uses
    to reach the desktop COM session, raising `OutlookUnavailable` on
    failure. **No caller anywhere today invokes this purely to check
    reachability** — every existing call is bundled inside a real
    fetch. This story needs one new, lightweight, real (but local,
    zero-external-cost) check — attempt the same
    `Dispatch("Outlook.Application")` → `GetNamespace("MAPI")` connection
    and report reachable/unreachable — mirroring `REQ-SB-31-US-01`'s own
    "one new lightweight in-process check, reusing an already-proven
    connection mechanism" precedent for its `GET /mcp` check.
  - **What "communication channel" honestly means today.** The PRD's own
    example — "the Hermes-wrapped Outlook skill" — describes a Hermes
    integration that **does not exist anywhere in this codebase yet**
    (confirmed by the concurrent `/spec REQ-SB-03/04/05` pass this same
    session — no live Hermes connection exists; see `ESCALATIONS.md` →
    `ESC-023`, `Open`). Every existing Outlook read (mail, calendar, and
    this session's proposed to-do read) reaches Outlook **directly** via
    desktop COM, not through Hermes. This story reports **direct Outlook
    COM reachability**, described honestly as such — not as a
    "Hermes-wrapped" channel, which would misrepresent what is actually
    being checked. If/when Hermes integration ships, that would be a
    later story's own amendment to this one channel's underlying
    mechanism, not a reason to delay this story.
- **No `html-prototype/` screen covers any part of this today —
  confirmed by direct inspection**, the same way `REQ-SB-31-US-01`
  confirmed its own net-new status before design: `index.html`'s sidebar,
  `agents-map.html`, `my-day.html` and its four drill-downs,
  `settings.html`, and the newly-`Done` `system-health.html` — none shows
  a chronological cross-agent run list or a per-channel status indicator.
  `REQ-SB-13-US-01`'s per-agent Communication History panel
  (`agents-map.html`'s side panel) is the closest existing surface, but
  it is explicitly **per-agent**, opened by selecting one agent at a
  time — not the cross-agent, "everything that ran recently" view this
  requirement's acceptance text describes. **This is genuinely new UI.**
- **Placement — resolved 2026-08-13: a new top-level nav page.** This
  story originally flagged two live candidates with no PRD text or
  established precedent favoring either — (a) a new top-level nav page,
  mirroring `REQ-SB-31-US-01`'s own resolved precedent, or (b) an added
  section on the already-approved System Health page. The operator
  delegated the call to the orchestrating agent, which decided **(a) — a
  new top-level nav page**, not a section grafted onto System Health.
  **Reasoning:** `REQ-SB-31-US-01` (System Health) was deliberately built
  as a current-snapshot status board with its own dedicated nav item
  specifically because a chronological log has a different shape/
  interaction model than a snapshot board — this project already treats
  "log/history over time" as a distinct UI pattern from "status right
  now" (My Day's own day-navigator precedent draws exactly this
  distinction elsewhere). Crowding a chronological, potentially
  long-scrolling activity log into System Health's own page would
  contradict that page's own designed purpose. This also matches the
  precedent that System Health itself just got its own new nav page
  rather than being folded into Settings. See `## Notes` for the full
  resolution record; `ESCALATIONS.md` → `ESC-025` is now `Resolved`.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. Scenarios describe the required behaviour; placement is resolved
(a new top-level nav page, see Context) but its visual shape awaits
/design REQ-SB-11 — these scenarios do not depend on that visual shape. Scope: run_event-kind
(success) and the new error-kind (failure) entries only — chat_user/
chat_agent turns and Supervised-mode "proposal" entries are explicitly
excluded (see Constraints/Non-Goals), since the PRD's own acceptance text is
about completed background runs, not conversation traffic or in-flight
approval requests already surfaced elsewhere (REQ-SB-21's Pending Approvals). -->

### Scenario 1: The activity log shows a completed background run, in chronological order

```gherkin
Given one or more background capture runs (email, meeting, or — once built —
    to-do) have completed
When the user views the agent activity log
Then each completed run is listed with which agent ran, when, and its
    outcome
  And the runs are shown in chronological order
```
<!-- AC-ID: REQ-SB-11-US-01-AC-01 -->

### Scenario 2: A failed background run appears with its error detail, not silently dropped

```gherkin
Given a background capture run fails partway through (e.g. Outlook is
    unreachable, or an unexpected exception occurs outside the pipeline's
    existing per-item error handling)
When the scheduled run fails
Then the failure is recorded as a run outcome — not silently lost — with
    an honest error detail describing what went wrong
  And the user viewing the agent activity log sees this run listed as
    failed, with its error detail visible
```
<!-- AC-ID: REQ-SB-11-US-01-AC-02 -->

### Scenario 3: Every configured background capture agent's runs appear, not only some of them

```gherkin
Given more than one background capture agent is configured (e.g. email
    capture and meeting capture)
When each completes a scheduled run
Then a run entry is recorded and shown for every one of them — no
    configured capture agent's successful runs are silently omitted from
    the log
```
<!-- AC-ID: REQ-SB-11-US-01-AC-03 -->

### Scenario 4: A communication channel's current status is shown as reachable

```gherkin
Given Outlook desktop is running and reachable via its existing COM
    connection mechanism
When the user views the agent activity view
Then the Outlook communication channel is shown as reachable
```
<!-- AC-ID: REQ-SB-11-US-01-AC-04 -->

### Scenario 5: A communication channel's current status is shown as unreachable

```gherkin
Given Outlook desktop is not running, or its COM connection cannot be
    established
When the user views the agent activity view
Then the Outlook communication channel is shown as unreachable
  And this is visibly distinguished from the reachable state
```
<!-- AC-ID: REQ-SB-11-US-01-AC-05 -->

### Scenario 6: No background runs have happened yet

```gherkin
Given no background capture agent has completed a run yet
When the user views the agent activity log
Then the view honestly shows that no runs have happened yet
  And it does not fabricate a run entry or show a misleadingly-empty
    "everything is fine" default
```
<!-- AC-ID: REQ-SB-11-US-01-AC-06 -->

### Scenario 7: Reopening the view reflects current state, not a stale snapshot

```gherkin
Given the user previously viewed the agent activity view
  And a new background run has completed, or a communication channel's
    reachability has changed, since that view was loaded
When the user reopens or refreshes the view
Then the view reflects the current, freshly-read state
  And it does not display a cached result from the earlier page load
```
<!-- AC-ID: REQ-SB-11-US-01-AC-07 -->

## Affected Screens

- **New top-level nav page (name/visual shape TBD) — resolved placement,
  2026-08-13 (Context).** Not a Settings section, not an added section on
  the System Health page. **No `html-prototype/` screen exists for it
  yet — this remains genuinely net-new UI.** `/design REQ-SB-11` must
  still run, to produce an approved prototype for the decomposer/
  architect to work from, **before `/plan-tasks`** — this story's
  `gate: clear` reflects that this story's own open questions are
  resolved, not that a prototype now exists; `/design` is a sequencing
  dependency, not a pipeline gate on this story itself (the identical
  reasoning `REQ-SB-31-US-01` used for its own equivalent situation).

## Dependencies

- **Blocked by:** none in the hard sense for the backend halves — the
  underlying `agent_communication_history.json` mechanism
  (`REQ-SB-13-US-01`, `Done`) and both existing capture pipelines
  (`REQ-SB-07-US-01`/`REQ-SB-08-US-01`, `Done`) already exist. The
  frontend half is blocked on a placement decision + `/design REQ-SB-11`
  (see Context/Notes).
- **Related to:** `REQ-SB-31-US-01` (`Done`) — the current-snapshot
  counterpart this story is explicitly scoped alongside, not duplicating
  (see Context).
- **Related to:** `REQ-SB-13-US-01` (`Done`) — this story's cross-agent
  aggregation reads the same `agent_communication_history.json` that
  story's per-agent panel already reads/writes; no changes needed to that
  story's own code, and its per-agent panel is unaffected/unchanged by
  this story.
- **Related to:** `REQ-SB-07-US-01`/`REQ-SB-08-US-01` (both `Done`) — this
  story fixes the honest-failure-recording gap inside their own
  orchestration functions (`email_classification.py`,
  `meeting_classification.py`); see Constraints.
- **Related to:** `REQ-SB-09` (To-Do Task Capture Pipeline, specced this
  same session, not yet built) — once built, a `todo-capture` agent's
  `run_event`/error entries will appear in this story's activity log
  automatically, since the aggregation mechanism reads by agent id
  generically rather than hardcoding today's two capture agents. Not a
  build dependency in either direction.
- **Related to:** `REQ-SB-21-US-01` (`Done`) — Supervised-mode
  `"proposal"` entries are intentionally excluded from this story's
  activity log (Constraints); they remain visible via that story's own
  Pending Approvals surface, not duplicated here.
- **External:** none new — the one new check (Outlook COM reachability)
  reuses the already-established connection mechanism
  `app/data_access/outlook_com.py` already has for mail/calendar; no new
  external system, credential, or dependency.

## Constraints

- **Scope: `run_event`-kind (success) and a new error-kind (failure)
  entries only.** `chat_user`/`chat_agent` conversational turns and
  `proposal` (Supervised pending-approval) entries are explicitly
  excluded from this story's activity log — grounded directly in the
  PRD's own "background agent runs... succeeded or failed" framing, and
  in the fact that pending proposals are already surfaced via
  `REQ-SB-21`'s Pending Approvals surface. Do not duplicate that surface
  here.
- **Must close the two confirmed recording gaps in Context before the
  acceptance text can be honestly satisfied:** (1) meeting-capture (and
  any future capture pipeline) must write a `run_event` entry on a
  successful Autonomous run, the same way email-capture already does —
  no configured capture agent's successful runs may be silently omitted
  (Scenario 3); (2) each capture pipeline's own top-level orchestration
  function must apply the same honest-failure-funnel pattern
  `REQ-SB-31-US-01`'s Scenario 8 already established for the chat path
  (`graph.py`, `ADR-015`) — an exception that escapes today's per-item
  handling must be recorded as a failed run with error detail, not left
  to vanish untraced (Scenario 2). The exact new `kind` value (e.g. a new
  `"run_error"` alongside the existing `"run_event"`/`"chat_user"`/
  `"chat_agent"`/`"proposal"` set, vs. an `"outcome"` field added to the
  existing `"run_event"` shape) is an implementation detail left to
  `/plan-tasks`.
- **Scope of the failure-recording fix is limited to each capture
  pipeline's own top-level entry point** (`email_classification.py`,
  `meeting_classification.py`) — mirroring `REQ-SB-31-US-01`'s own
  explicit non-goal of building general exception-catching/logging
  middleware for the ASGI application as a whole. This story does not
  add general error-logging infrastructure beyond these named,
  concretely-identified capture entry points.
- **The Outlook-reachability check is one new, lightweight, real,
  in-process check** — no new external round-trip, no new credential, no
  polling loop; reuses `outlook_com.py`'s already-established connection
  mechanism, the same "reuse existing signals/mechanisms, one cheap new
  check" precedent `REQ-SB-31-US-01` already established for its own
  `GET /mcp` check.
- **Communication channel is reported as direct Outlook COM
  reachability, honestly described as such** — not "Hermes-wrapped" (see
  Context; Hermes has no live connection in this codebase yet).
- **No fabricated data.** An empty activity log or an unreachable channel
  must be shown honestly, never as a silently-passing default
  (Scenario 6).
- Each check/list must reflect current state on every view/refresh, not a
  cached snapshot from an earlier load (Scenario 7) — mirroring
  `REQ-SB-22-US-01`'s/`REQ-SB-31-US-01`'s own "recomputes fresh, never
  cached" precedent.
- Must respect the `api → business → data_access` layer boundary
  (ADR-003).
- **Placement is resolved (a new top-level nav page)** — see Context/
  Notes; `/design REQ-SB-11` must still run, to produce the approved
  prototype, before `/plan-tasks` (a sequencing dependency, not a further
  gating decision).

## Implementation Tasks

| Task | Title | Depends on | AC(s) covered |
|---|---|---|---|
| [REQ-SB-11-US-01-T01](../Tasks/REQ-SB-11-US-01-T01-capture-pipeline-honest-failure-recording.md) | Honest-failure-recording fix — meeting-capture success-entry parity + per-step honest-failure-funnel, `email_classification.py` only | — | (non-AC smoke checks; AC-01/02/03 verified end-to-end in T04) |
| [REQ-SB-11-US-01-T02](../Tasks/REQ-SB-11-US-01-T02-agent-activity-aggregation-module.md) | `app/business/agent_activity.py` read-only aggregation module + `outlook_com.py::check_reachable()` | — | (non-AC smoke checks) |
| [REQ-SB-11-US-01-T03](../Tasks/REQ-SB-11-US-01-T03-agent-activity-router.md) | `app/api/agent_activity_router.py`, `GET /agent-activity` | T02 | (non-AC smoke check) |
| [REQ-SB-11-US-01-T04](../Tasks/REQ-SB-11-US-01-T04-agent-activity-page.md) | `AgentActivityPage.tsx` + nav wiring | T03, REQ-SB-12-US-01-T01 | AC-01..AC-07 |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, no test tooling exists yet; manual verification performed and recorded per task
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **A real Hermes-wrapped channel status** — Hermes has no live
  connection anywhere in this codebase yet (see Context, `ESC-023`); this
  story checks direct Outlook COM reachability only, honestly described
  as such. A later story can extend this channel's mechanism once Hermes
  integration ships.
- **`REQ-SB-31-US-01`'s own three existing checks** (MCP mount, per-agent
  Provider availability, last capture run) — not duplicated or rebuilt;
  System Health remains the current-snapshot surface for those.
- **Alerting/notifications** on a detected failure — not asked for by the
  PRD's acceptance text; this is a view the user checks.
- **Auto-refresh/polling** beyond recomputing fresh on each view open or
  manual refresh (Scenario 7) — no background polling interval is
  specified or built.
- **General exception-catching/logging middleware for the ASGI
  application as a whole** — this story closes only the two
  concretely-identified capture-pipeline gaps named in Constraints; a
  general logging/observability layer is separate, larger follow-on
  work, mirroring `REQ-SB-31-US-01`'s own identical non-goal.
- **Retrofitting/reconstructing run outcomes that were never recorded
  before this story shipped** — the activity log only shows runs
  recorded from this story's own fix forward; no attempt is made to
  recover history that was silently lost before the recording gap was
  closed.
- **Chat traffic (`chat_user`/`chat_agent`) and Supervised-mode
  `proposal` entries** — explicitly excluded from this list (see
  Constraints); the former remains `REQ-SB-13`'s own per-agent
  Communication History, the latter remains `REQ-SB-21`'s own Pending
  Approvals surface.

## Notes

**Prototype parity:** N/A — genuinely new UI; no `html-prototype/` screen
covers any region of this requirement (confirmed by direct inspection of
every existing screen, per Context). Scenarios 1-7 above enumerate every
region the new nav page must show once `/design REQ-SB-11` produces an
approved prototype: the chronological run list (success and error
outcomes), the Outlook channel status indicator, and the empty state.

**Why this was originally flagged (`net-new-design-needed` +
MUST-FLAG trigger 8):**

1. **`net-new-design-needed`.** No approved prototype screen shows a
   chronological cross-agent activity log or a per-channel status
   indicator — confirmed by direct inspection, not assumed. This
   requires a `/design` pass before `/plan-tasks` can proceed on the
   frontend half (still true — see Resolution record below).
2. **Trigger 8 — placement was genuinely unclear, with no PRD text or
   precedent favoring one option.** Two live candidates (Context): a new
   top-level nav page (mirroring `REQ-SB-31-US-01`'s own resolved
   precedent), or an added section on the already-`Done` System Health
   page. Both were equally consistent with this project's existing
   patterns at the time; picking one silently would have been exactly
   the kind of guess the analyst is required to flag rather than make,
   especially since `REQ-SB-31-US-01`'s own Notes explicitly asked for
   this exact human decision when REQ-SB-11 was eventually specced.

No other trigger fired: REQ-SB-11 is finalized PRD text (no `<!--
Draft -->` marker); no ADR was created or changed by this pass (n/a to
the analyst — the honest-failure-recording fix and the new aggregation
module both extend already-`Accepted` patterns, `ADR-015`'s
honest-failure-funnel and `ADR-003`'s read-only-aggregation-module
shape, the same way `REQ-SB-31-US-01`'s own architect pass found "no new
ADR" for a structurally identical extension — left for the architect to
confirm at `/plan-tasks`, not asserted here); the story is not oversized
(4 tasks, the same shape `REQ-SB-31-US-01` used: one fix task, one
aggregation module, one router, one frontend page); no contradictory PRD
inputs exist.

**Resolution record (2026-08-13).** The operator delegated the placement
decision to the orchestrating agent directly ("make the call yourself,
using sane defaults") rather than answering it personally. The
orchestrating agent decided **(a) — a new top-level nav page**, not an
added System Health section, reasoning: `REQ-SB-31-US-01` (System
Health) was deliberately built as a current-snapshot status board with
its own dedicated nav item specifically because a chronological log has
a different shape/interaction model than a snapshot board — this project
already treats "log/history over time" as a distinct UI pattern from
"status right now" (My Day's own day-navigator precedent draws this same
distinction elsewhere). Crowding a chronological, potentially
long-scrolling activity log into System Health's own page would
contradict that page's own designed purpose; this also matches the
precedent that System Health itself just got its own new nav page
rather than being folded into Settings.

`ESCALATIONS.md` → `ESC-025` is flipped to `Resolved`, naming this
story's own updated `## Context`/`## Notes` as the resolving artefact.
`gate:` reset to `clear` — this story's own open questions are resolved,
but `/design REQ-SB-11` must still run (genuinely net-new UI, no
prototype exists yet) before `/plan-tasks` — a sequencing dependency,
not a further gating decision, per the identical reasoning
`REQ-SB-31-US-01` used for its own equivalent situation. The
recording-completeness fix (finding 2 in `ESC-025`, meeting-capture
success-entry parity + the honest-failure-funnel extension) was never a
decision-blocker and remains scoped into this story's own Constraints/
`T01` regardless of the placement outcome.

**What to do:** run `/design REQ-SB-11` to produce the approved prototype
for the new top-level nav page (Scenarios 1-7 above define every region
it must show), then `/plan-tasks REQ-SB-11`.

---

**Architect pass (2026-08-13, `/plan-tasks` step 1).** `/design REQ-SB-11`
already ran and its prototype (`html-prototype/agent-activity.html`) is
live-verified and approved (`REVIEW-QUEUE.md`). **No new ADR.** The
honest-failure-recording fix applies `ADR-015`'s already-`Accepted`
call-site honest-failure-funnel pattern to a second orchestration
function (`email_classification.py::run_capture_and_record_completion`,
this file only — `meeting_classification.py` itself needs no change; see
architecture.md for why), the same "extends, does not reopen" shape
`REQ-SB-31-US-01`'s own Scenario-8 fix already used on the same function
family. The new backend surface (`app/business/agent_activity.py`,
`app/api/agent_activity_router.py`) is a **read-only aggregation module
writing no new persisted state at all** — the same shape
`app/business/system_health.py` (`REQ-SB-31-US-01`) and
`app/business/my_day.py` (`REQ-SB-12-US-02`) already established, composing
`agent_registry.list_agents()`/`vault_writer.load_agent_history()`
(both already `Done`) as-is, plus one new local Outlook COM reachability
check (`outlook_com.py::check_reachable()`) reusing the module's own
already-proven `_connect_namespace()` mechanism — no new tool, framework,
storage mechanism, or trust-surface decision. The new frontend page/
route/nav-item is an ordinary application of `ADR-010`'s already-`Accepted`
routing/styling/component conventions — zero new CSS (composed entirely
from already-ported `.log-list`/`.log-item`/`.badge*`/`.kv-list`/
`.empty-state` classes, per the approved prototype's own header note). The
new `"run_error"` history-entry `kind` value is additive to the existing
enum, the same "grow the set, don't redefine it" shape `ADR-018` point 7
already used for `"proposal"` — confirmed by direct reading that neither
existing consumer of `kind` (`state.py::history_entries_to_messages`,
`AgentDetailPanel.tsx`'s Communication History tab) needs any change to
handle it safely. Full reasoning and every new file/function named:
`Implementation/Architecture/architecture.md` → "Agent Activity & Error
Observability (REQ-SB-11-US-01)".

**Architecture scope (bounds the decomposer/coder):** `architecture.md` →
"Agent Activity & Error Observability (REQ-SB-11-US-01)", plus the
already-`Accepted` conventions it extends without reopening — "Frontend
Application Architecture" (`ADR-010` routing/styling/component
conventions), "In-App Agent Orchestration (LangGraph) & Shared MCP Server"
(`ADR-015`, for the `email_classification.py` fix only), "System Health
View" (the read-only-aggregation-module shape this story's own
`agent_activity.py` mirrors). Concrete files this bounds the decomposer/
coder to: `src/backend/app/business/email_classification.py` (the
honest-failure-recording fix only — the two named capture-step call sites,
no other change; `meeting_classification.py` is explicitly NOT in scope),
`src/backend/app/data_access/outlook_com.py` (new `check_reachable()`
function only), `src/backend/app/business/agent_activity.py` (new),
`src/backend/app/api/agent_activity_router.py` (new),
`src/backend/app/main.py` (router registration only),
`src/frontend/src/pages/AgentActivityPage.tsx` (new),
`src/frontend/src/features/agent-activity/client.ts` (new),
`src/frontend/src/App.tsx` (new route only), `src/frontend/src/
components/shell/Sidebar.tsx` (new nav item only).

`gate: clear` 2026-08-13 — no ADR triggered, no material assumption made
(every mechanism decision above is a direct, same-shape extension of
already-`Accepted` structural decisions, grounded in direct reading of the
real current code — the fix-site clarification and the
`record_capture_run_completed()` preservation decision are both
considered, reasoned design choices recorded above and in
architecture.md, not guesses among equally-valid options), no
contradiction with any Accepted ADR/PRD/`MEMORY.md` constraint. Ready for
the decomposer.

**Decomposer pass (2026-08-13, `/plan-tasks` step 2).** All 7 scenarios
locked as `REQ-SB-11-US-01-AC-01`..`AC-07` (sequential — every scenario's
Given/When/Then was already buildable as written, only trailing AC-ID tags
were added). Four tasks created at the flat root
(`Implementation/Tasks/`): `T01` (backend, the honest-failure-recording
fix in `email_classification.py`, no dependency — independent of the new
activity-page surface, can be built first), `T02` (backend,
`agent_activity.py` aggregation module + `outlook_com.check_reachable()`,
no dependency — mirrors `T01`/`T02`'s own independence in
`REQ-SB-31-US-01`), `T03` (backend, `agent_activity_router.py`,
`depends_on: [T02]`), `T04` (frontend, `AgentActivityPage.tsx` + nav
wiring, `depends_on: [T03, REQ-SB-12-US-01-T01]` — the latter a
task-level edge since `T04` literally edits `App.tsx`/`Sidebar.tsx`,
mirroring `REQ-SB-31-US-01-T04`'s/`REQ-SB-12-US-02-T04`'s own identical
dependency shape on the same task). `depends_on` is acyclic: `T02 → T03 →
T04`; `T01` stands alone.

Every locked AC has at least one AC-tagged manual verification step:
`AC-01`-`AC-07` (every "when the user views the agent activity
log/view" scenario) in `T04` — per the "user-observable outcome"
placement rule already established by `REQ-SB-31-US-01`, tagged steps live
on the frontend page task that actually renders what `T01`/`T02`/`T03`'s
backend produces/returns; `T01`-`T03` carry non-AC-tagged live-call/
live-induced-failure smoke checks instead, mirroring `REQ-SB-31-US-01`'s
own identical `T01`-`T03` split (that story tagged its one backend-only,
no-screen scenario, `AC-08`, directly in `T01` — this story has no
equivalent backend-only scenario, since even the failure-recording fix's
own observable outcome, per Scenario 2's own wording, is "the user viewing
the agent activity log sees this run listed as failed," a screen-level
outcome, not a backend-only one).

No MUST-FLAG trigger fired this pass: no material assumption (every
mechanism decision traces to an already-`Accepted` pattern or a
considered, reasoned extension recorded in architecture.md), no
`Draft`/unfinalised requirement relied on, no ADR created/changed, no
`ESCALATIONS.md` entry written, no oversized decomposition (each task is a
single-file-family, one-sitting unit — `T01` touches exactly one file), no
contradictory inputs, every locked AC has a verifiable tagged step, and
the task breakdown/dependency structure has no genuine ambiguity (the same
read-only-aggregation → router → page shape `REQ-SB-31-US-01`/
`REQ-SB-12-US-02` already established, applied here). `status: Ready`,
`gate: clear`. Eligible for `/plan-sprints`.

---

**Coder pass (2026-08-13, `/implement-sprint SPRINT-027`).** All 4 tasks
built and verified live end-to-end, `status: Done`. `T01`'s fix was
composed directly around the REAL current `email_classification.py`
(SPRINT-025 had landed an unconditional `vault_indexing.rebuild_index()`
call between `/plan-tasks` and this build — preserved, unconditional,
placed ahead of the newly-gated `record_capture_run_completed()` call).
All 7 locked ACs (`AC-01`..`AC-07`) verified with real, live data — real
Outlook/vault capture runs, a real induced email-capture failure
(in-process monkeypatch, this project's own established technique), and
a real, screenshot-confirmed Outlook-unreachable state (achieved via a
temporary, port-identical, immediately-reverted backend swap with
`outlook_com._connect_namespace` monkeypatched — physically closing
Outlook does not stay unreachable on this machine, since Windows COM
auto-relaunches it on the next `Dispatch()` call, a real live finding not
anticipated by this task's own Tests block). Real browser screenshots
(OS-installed Edge headless mode, no visual-harness/CDP tool was
available to this Coder instance) confirm every region against the
approved prototype. Full verification detail, including every screenshot
filename and the exact monkeypatch technique used per AC: each task's own
Implementation Log under `Implementation/Tasks/REQ-SB-11-US-01-T01`..
`T04`. No `ESCALATIONS.md`/`REVIEW-QUEUE.md` entry — no MUST-FLAG trigger
fired; two scope-internal judgment calls (the `vault_indexing.
rebuild_index()` placement in `T01`, and `check_reachable()`'s added
`CoUninitialize()` in `T02`) are logged in their own tasks' Implementation
Logs for human spot-check, per the standing "scope-internal judgement
calls are not escalations" rule. `gate: clear`.
