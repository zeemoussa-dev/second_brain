---
id: REQ-SB-31-US-01
title: System Health View — backend/MCP mount/Provider availability/last capture run, from already-recorded signals
requirement_ids: [REQ-SB-31]
requirement_section: "REQ-SB-31: System Health View"
phase: P1
status: Done
gate: flagged
gate_reason: "Resolved 2026-08-12 — operator (in chat, via orchestrator) decided all three previously-flagged questions: (1) placement is a new top-level nav page (not a Settings section, not a persistent shell indicator); (2) an agent whose Provider has no real client is shown as Disabled and listed as a Health Issue in the new page, overriding ADR-011 point 3/ADR-014 point 7's 'not a failure' framing scoped to this view only; (3) the run_agent_conversation crash gap is closed in this story (Scenario 8). ESC-014 resolved. `/design REQ-SB-31` ran, prototype approved (REVIEW-QUEUE.md). Architect pass (2026-08-12): no new ADR — system_health.py/system_health_router.py mirror my_day.py's read-only shape (ADR-003), SystemHealthPage.tsx applies ADR-010, the graph.py Scenario 8 fix applies ADR-015's existing honest-failure-funnel pattern. Decomposer pass (2026-08-12): all 8 scenarios locked as AC-01..AC-08, 4 tasks created (T01-T04), depends_on acyclic. gate stays clear — no MUST-FLAG trigger fired this pass."
sprint: "SPRINT-019"
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-31-US-01 — System Health View

## Story

**As a** Second Brain user
**I want** a single visible surface showing whether the backend, the
in-app MCP/agent-orchestration path, each configured LLM Provider, and
the last scheduled capture run are each genuinely working
**So that** a real failure is visible at a glance instead of being
discovered by symptom-chasing through individual features or digging
through raw server logs

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-31: System Health View* — "A
  visible surface showing the operational status of Second Brain's own
  moving pieces — whether the backend is reachable, whether the in-app MCP
  server and LangGraph agent path are actually working (not just that the
  process is running), whether each configured Provider is reachable,
  whether the scheduler's last capture run succeeded — so a real failure is
  visible at a glance instead of discovered by symptom-chasing through
  individual features." Acceptance: "The user can see, without digging
  through server logs or guessing from a feature silently failing, whether
  Second Brain's backend, MCP/agent-orchestration path, configured
  Providers, and last scheduled capture run are each genuinely working —
  not just 'the process is up.'"
- **PRD breadcrumb (2026-08-12, operator-authored, cited verbatim, NOT
  re-decided here):** "Scope resolved 2026-08-12, operator-directed ('we
  need to have a System Health view as we keep on adding Pieces
  everywhere'), prompted directly by a real debugging session the same
  day: a critical, silent chat failure (an orphaned backend worker process
  serving stale code, then a hardcoded stale MCP port, then a
  nested-event-loop self-connection bug) took extensive live investigation
  to even notice, let alone diagnose — nothing in the app itself surfaced
  that anything was wrong. Genuinely open, not decided here: (1) the exact
  set of checks ...; (2) active probing ... vs. passive reporting ...; (3)
  placement (a new nav item/page vs. a Settings section vs. a small
  persistent status indicator in the app shell); (4) whether this also
  captures unhandled backend exceptions going forward ... or is scoped to
  synchronous health checks only this pass. Left to `/spec`."
- **Two real, now-fixed bugs from the same 2026-08-12 debugging session are
  this requirement's own concrete precedent (`MEMORY.md`'s Decisions/
  Constraints, same date), not hypothetical:** (1) an orphaned
  `uvicorn --reload` worker process silently served stale code indefinitely
  after its reloader parent died — no symptom until a fixed bug appeared to
  have "no effect"; (2) a hardcoded stale MCP loopback port (`8002` instead
  of the real `8001`) caused every real chat call to 500 with no
  indication anywhere in the UI that anything was wrong, discovered only
  via direct backend log inspection.
- **Real code read directly, not assumed, to ground the checks below in
  what's actually checkable today:**
  - `app/data_access/vault_writer.py::record_capture_run_completed()`
    writes `.second-brain/last_capture_run.json` as `{"finished_at":
    <iso8601>}` — **only** `finished_at`, no success/failure/error field
    at all. It is called **once, at the very end** of
    `email_classification.run_capture_and_record_completion()`, **after**
    both `classify_recent_emails()` and
    `meeting_classification.classify_recent_meetings()` have already run
    to completion without raising. If either raises, this call is never
    reached — the file simply keeps its prior (older) `finished_at`
    value, or never exists at all if no run has ever completed. There is
    **no per-attempt success/failure record** — only "when did a run last
    fully complete." `load_last_capture_run()` returns `None` if the file
    doesn't exist yet.
  - `app/business/provider_registry.py::has_real_client(provider_id)` is
    a small hardcoded set-membership check (`_REAL_CLIENT_PROVIDER_IDS =
    {"compass"}`), already used by `app/api/agents_router.py::
    get_agent_settings` to compute `"provider_available": bool` on every
    `GET /agents`/`GET /agents/{id}` response (`REQ-SB-19`, `Done`) — a
    Provider with `provider_available: false` (no real client built for
    it) is an **existing, deliberate, honest "not yet available" state**
    (`ADR-014` point 7's own "declared but not yet backed by a real
    handler" pattern), never a defect.
  - `app/api/mcp_server.py` mounts the shared `FastMCP` server at `/mcp`
    in the same process. A bare `GET /mcp` correctly returns `HTTP 406 Not
    Acceptable` when the mount is alive — confirmed live 2026-08-12 during
    the real debugging session this requirement was prompted by, not
    assumed. This is the one check in this story that makes a real (but
    local, in-process, zero-external-cost) HTTP call rather than reading
    already-recorded data.
  - `app/business/agent_orchestration/graph.py::run_agent_conversation`
    (the real chat path, `REQ-SB-25`, `Done` as of today) already funnels
    two of three failure shapes into an honest `{"error": str}` result,
    never a fabricated reply: a Provider with no real client
    (`model_factory.resolve_agent_model` returns `None` →
    `{"error": "<Provider> is not available yet..."}`), and a genuine
    Provider-call failure inside `call_model` (wrapped in `except
    Exception as exc: return {"error": f"The request to this agent's
    Provider failed: {exc}"}` — "honest-failure-reporting funnel," per
    the function's own comment). **The third shape — an unhandled
    exception elsewhere in the same call chain — is NOT yet closed as of
    this reading:** `run_agent_conversation`'s own body (specifically
    `await mcp_client.load_vault_query_tools()` and
    `await _GRAPH.ainvoke(initial_state)`) is not itself wrapped in a
    try/except. An exception raised there (e.g. an MCP client connection
    failure — the exact shape of the second real bug named above) would
    still propagate uncaught through `agents_router.py::chat` to FastAPI's
    default handler, producing a raw, unhandled 500 with no
    `{"error": ...}` funneling and nothing surfaced to the app itself.
    This was a **real, currently-live gap, confirmed by direct reading of
    the current code, not a hypothetical** — it directly informed the PRD
    breadcrumb's own open question (4). **Resolved 2026-08-12 (operator
    decision, in this story — closes ESC-014's second open question):**
    this gap is now closed as part of `REQ-SB-31-US-01` (Scenario 8) —
    both remaining calls (`mcp_client.load_vault_query_tools()`,
    `_GRAPH.ainvoke(initial_state)`) are wrapped in the same
    honest-failure-funnel pattern `call_model` already uses, so an
    unexpected exception there now returns `{"error": ...}` instead of
    propagating as a raw 500. This is a backend robustness fix inside
    `run_agent_conversation` itself, benefiting the chat path directly —
    it is not one of the System Health view's own passive/already-recorded
    checks (see Non-Goals for what remains genuinely out of scope: general
    exception-catching/logging middleware beyond this one call chain).
- **No `html-prototype/` screen shows a System Health surface today —
  confirmed by direct inspection**, not assumed: `html-prototype/
  index.html`'s sidebar (`agents-map.html`, `my-day.html`,
  `settings.html`, the catalog page) has no health/status nav item;
  `html-prototype/settings.html` (Vault/Connections, Sections, Providers
  cards) has no health card; `html-prototype/agents-map.html`/`my-day.html`
  carry no persistent status indicator. This is genuinely new UI — no
  design authority exists yet for its visual shape. **Placement resolved
  2026-08-12 (operator decision, in chat — closes ESC-014's first open
  question):** a new top-level nav item/page, not a Settings section and
  not a persistent shell indicator. `/design REQ-SB-31` must still run to
  produce the approved prototype screen before `/plan-tasks` — see
  Affected Screens.
- **Resolved here, by this project's own consistent preference for reusing
  existing signals over inventing new probing machinery (not a guess —
  the same reasoning basis this codebase already applies repeatedly, e.g.
  `list_notes_in_kind_folder`/`list_known_customers` deriving from the
  vault instead of a hardcoded list):**
  - **Checks, this pass:** backend reachability is implicit (the view
    cannot render at all if the backend is unreachable, so no explicit
    check is designed for it — matching the PRD's own "not just 'the
    process is up'" framing, which is about the *other* checks going
    further than mere reachability); MCP/agent-orchestration path status,
    via the already-proven `GET /mcp` → `406` liveness signal; per-agent
    Provider availability, by reusing the already-computed
    `provider_available`/`has_real_client` signal (`GET /agents`) rolled
    up per distinct Provider — **not** a new round-trip call to any
    external Provider API; last capture run status, by reading
    `.second-brain/last_capture_run.json`'s existing `finished_at`
    timestamp (or its honest absence).
  - **Active probing vs. passive reporting: resolved as passive.** This
    pass surfaces already-recorded/already-computed signals (Provider
    availability, last capture run timestamp) plus one lightweight,
    local, in-process reachability check (`GET /mcp`) that costs nothing
    external and reuses an already-proven signal — it deliberately does
    **not** add a new real round-trip test to any external Provider
    (that would be the "active probing... costing time/API calls"
    alternative the breadcrumb named, and a materially bigger, riskier
    build for a first pass). **Real limitation, recorded honestly, not
    hidden:** a Provider shown "available" means "a real client is
    configured for it" (`has_real_client`), not "verified reachable right
    now" — a Provider whose credentials are configured but whose endpoint
    is currently down would still show as "available" this pass. Likewise,
    the last capture run's status is its **recorded completion time**,
    not an explicit success/failure flag (none exists in the underlying
    data) — a currently-failing run (raising before
    `record_capture_run_completed()` is ever reached) shows up as an
    **increasingly stale timestamp relative to the known hourly schedule**
    (`app/scheduling/capture_scheduler.py`'s `IntervalTrigger(hours=1)`),
    not as an explicit "FAILED" state. No staleness/pass-fail threshold
    judgment is invented this pass (see Non-Goals) — the raw timestamp
    (or "no run has ever completed") is shown as-is, honestly, and the
    user is left to judge freshness themselves.
  - **Distinguishing genuine failure from "not configured yet" — overridden
    for THIS view, 2026-08-12 (operator decision, in chat — closes
    ESC-014's second open question):** the story as originally drafted
    proposed showing a Provider with no real client as a normal, honest
    "not available"/"not configured" state, mirroring the honesty
    convention this codebase already established for actions with no real
    handler (`ADR-011` point 3) and Providers with no real client (`ADR-014`
    point 7). **The operator has overridden that framing specifically for
    the System Health view:** an agent whose selected Provider has no real
    client configured is shown as **Disabled**, and listed as a **Health
    Issue** in the new page (Scenario 3). This is a deliberate, scoped
    override of how *this view* presents the state — it does **not** change
    `ADR-011`/`ADR-014`'s underlying honesty convention itself, and it does
    **not** touch any other screen that already relies on that convention
    (e.g. the Agents Map or per-agent Settings, which the operator's own
    parenthetical "shouldn't be the case in future" suggests is expected to
    remain rare/transitional rather than a normal steady state worth
    softening elsewhere). **Tension worth a human's attention, noted but
    not resolved here (see `## Notes`):** this creates a real inconsistency
    — the exact same underlying state (`provider_available: false`) is now
    "Disabled / Health Issue" on the System Health page but still a neutral
    "not configured" elsewhere (e.g. Agents Map). Whether Agents Map should
    also adopt a "Disabled" badge for consistency is a separate product
    question, not decided or built here — flagged as a Note, not expanded
    into this story's scope.
- **Related, not overlapping — `REQ-SB-11` (Agent Activity & Error
  Observability, also no story yet):** REQ-SB-11's own acceptance text
  ("a chronological list of background agent runs with outcome... and a
  current status indicator per communication channel") describes a
  **history/log** shape — every run, with its own outcome — while this
  story is a **current-snapshot status board** shape — is each moving
  piece healthy *right now*. They likely share some of the same underlying
  data (`last_capture_run.json`, `agent_communication_history.json`) but
  are not the same requirement and this story does not expand into
  REQ-SB-11's own chronological-list scope. Worth a human note for
  whichever of the two is specced/built second, to avoid duplicating
  the same status-board UI twice.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. Scenarios 1-7 describe what is resolved above (passive
reporting of already-recorded/already-computed signals, plus the one
lightweight in-process MCP-mount check, plus the operator-directed
Disabled/Health Issue Provider display) on a new top-level nav page (exact
visual shape left to /design). Scenario 8 closes the separate
run_agent_conversation crash-gap the operator directed into this story's
scope; it is a chat-path backend fix, not a System Health page check. No
staleness/pass-fail judgment on the last capture run timestamp is asserted
(left open, see Non-Goals). -->

### Scenario 1: Viewing System Health when every checked piece is working

```gherkin
Given the backend is reachable, the MCP server mount at /mcp responds with
    its normal "alive" signal, every agent's selected Provider has a real
    client configured, and a capture run has completed recently
When the user opens the System Health view
Then the view shows the MCP/agent-orchestration path as reachable
  And the view shows each configured Provider's availability
  And the view shows when the last capture run completed
  And none of these is shown as a failure
  And no agents are listed as a Health Issue
```
<!-- AC-ID: REQ-SB-31-US-01-AC-01 -->

### Scenario 2: The MCP/agent-orchestration path is shown as unhealthy when the mount is not responding as expected

```gherkin
Given the MCP server mount at /mcp does not respond with its normal
    "alive" signal (e.g. no response, or an unexpected response)
When the user opens or refreshes the System Health view
Then the view shows the MCP/agent-orchestration path as unhealthy
  And this is visibly distinguished from the normal "reachable" state
```
<!-- AC-ID: REQ-SB-31-US-01-AC-02 -->

### Scenario 3: An agent whose Provider has no real client configured is shown as Disabled and listed as a Health Issue

```gherkin
Given an agent's selected Provider has no real client built for it yet
    (provider_available is false)
When the user opens the System Health view
Then that agent is shown as Disabled
  And that agent is listed as a Health Issue in the System Health view
```
<!-- AC-ID: REQ-SB-31-US-01-AC-03 -->

### Scenario 4: An agent whose Provider has a real client configured is shown as available, not a Health Issue

```gherkin
Given an agent's selected Provider has a real client built for it
    (provider_available is true)
When the user opens the System Health view
Then that agent is shown as available (not Disabled)
  And that agent is not listed as a Health Issue
```
<!-- AC-ID: REQ-SB-31-US-01-AC-04 -->

### Scenario 5: The last capture run's completion time is shown from the recorded completion record

```gherkin
Given a capture run has previously completed and
    .second-brain/last_capture_run.json records its completion timestamp
When the user opens the System Health view
Then the view shows when the last capture run completed
```
<!-- AC-ID: REQ-SB-31-US-01-AC-05 -->

### Scenario 6: No capture run has ever completed

```gherkin
Given no capture run has ever completed (last_capture_run.json does not
    exist)
When the user opens the System Health view
Then the view honestly shows that no capture run has completed yet
  And it does not fabricate a completion time or show a misleadingly
    healthy-looking default
```
<!-- AC-ID: REQ-SB-31-US-01-AC-06 -->

### Scenario 7: Reopening the view reflects the current state, not a stale snapshot

```gherkin
Given the user previously opened the System Health view
  And the underlying state of one of the checked pieces has since changed
    (e.g. a Provider that had no real client now has one configured)
When the user reopens or refreshes the System Health view
Then the view reflects the current, freshly-checked state
  And it does not display a cached result from the earlier page load
```
<!-- AC-ID: REQ-SB-31-US-01-AC-07 -->

### Scenario 8: A previously-unhandled exception in the chat path's own tool-loading/graph-invocation step is now honestly reported, not left as a raw 500

```gherkin
Given an agent's selected Provider is available (a real client is
    configured) but an unexpected exception occurs while loading the MCP
    vault-query tools or while running the conversation graph itself —
    outside the two failure shapes already funneled today (Provider not
    configured; a Provider model-call failure inside call_model)
When the user sends a message to that agent
Then the chat response is an honest {"error": ...} result, using the same
    honest-failure-funnel pattern call_model's own Provider-failure path
    already uses
  And no raw, unhandled 500 propagates to the caller
```
<!-- AC-ID: REQ-SB-31-US-01-AC-08 -->

## Affected Screens

- **New top-level nav page (name/visual shape TBD)** — a dedicated System
  Health page, per the operator's 2026-08-12 decision (resolves ESC-014's
  first open question). Not a Settings section, not a persistent app-shell
  indicator. **No `html-prototype/` screen exists for it yet — this remains
  genuinely net-new UI.** `/design REQ-SB-31` must still run, to produce an
  approved prototype for the decomposer/architect to work from, **before
  `/plan-tasks`** — this story's `gate: clear` reflects that this story's
  own open questions are resolved, not that a prototype now exists; the
  `/design` step is a sequencing dependency, not a pipeline gate on this
  story itself.
- Scenario 8 is backend-only (`app/business/agent_orchestration/graph.py`)
  and touches no screen — see Context/Notes.

## Dependencies

- **Related to:** `REQ-SB-11` (Agent Activity & Error Observability) — a
  chronological run-history/log shape, distinct from this story's
  current-snapshot status-board shape; see Context. Not a build
  dependency; no story exists for either yet.
- **Related to:** `REQ-SB-19-US-01` (`Done`) — this story reuses its
  already-shipped `provider_available`/`has_real_client` signal directly,
  no changes needed to that story's own code.
- **Related to:** `REQ-SB-25-US-01` (`Done`) — this story's understanding
  of the chat path's existing honest-failure-funnel (and its one
  currently-open gap) is grounded in that story's real, shipped code; not
  a build dependency, informational only.
- **Related to:** `REQ-SB-07-US-01`/`REQ-SB-08-US-01` (both `Done`) — this
  story reads `last_capture_run.json`, written by the capture pipeline
  those stories built; no changes needed to either.
- **External:** none new.

## Constraints

- **Reuse existing signals only, this pass — no new active Provider
  round-trip probing.** The `GET /mcp` liveness check is the one
  real (but local, zero-external-cost) HTTP call this story adds; Provider
  availability and last-capture-run status are read from already-recorded/
  already-computed data.
- **On the System Health view specifically, an agent whose Provider has no
  real client configured must be shown as Disabled and listed as a Health
  Issue** (Scenario 3) — an operator-directed override of the "not
  configured is not a failure" framing this story originally proposed. This
  override is **scoped to this view only**; it does not change `ADR-011`
  point 3 / `ADR-014` point 7's underlying honesty convention, and it does
  not touch any other screen (e.g. Agents Map, per-agent Settings) that
  currently relies on that convention to show "not configured" as neutral.
- **No fabricated data.** A check that cannot currently be evaluated (e.g.
  no capture run has ever completed) must say so honestly, never silently
  render a healthy-looking default.
- Each check must reflect current state on every view/refresh, not a
  cached snapshot from an earlier load (Scenario 7) — mirroring the
  "recomputes fresh on every call, never cached" precedent already
  established for My Day's rolling window (`REQ-SB-22-US-01`).
- **Scenario 8's fix wraps only the two remaining, concretely-identified
  calls in `run_agent_conversation`'s own body** (`mcp_client.
  load_vault_query_tools()`, `_GRAPH.ainvoke(initial_state)`) in the same
  honest-failure-funnel pattern `call_model` already uses — return
  `{"error": ...}`, never a fabricated reply, never left to propagate as a
  raw 500. This is not new logging/observability infrastructure (see
  Non-Goals).

## Implementation Tasks

| Task | Title | Depends on | AC(s) covered |
|---|---|---|---|
| [REQ-SB-31-US-01-T01](../Tasks/REQ-SB-31-US-01-T01-run-agent-conversation-crash-gap-fix.md) | `run_agent_conversation` crash-gap fix (Scenario 8) | — | AC-08 |
| [REQ-SB-31-US-01-T02](../Tasks/REQ-SB-31-US-01-T02-system-health-aggregation-module.md) | `app/business/system_health.py` read-only aggregation module | — | (non-AC smoke check) |
| [REQ-SB-31-US-01-T03](../Tasks/REQ-SB-31-US-01-T03-system-health-router.md) | `app/api/system_health_router.py`, `GET /system-health` | T02 | (non-AC smoke check) |
| [REQ-SB-31-US-01-T04](../Tasks/REQ-SB-31-US-01-T04-system-health-page.md) | `SystemHealthPage.tsx` + nav wiring | T03, REQ-SB-12-US-01-T01 | AC-01..AC-07 |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, test tooling still pending; manual-mode verification performed and recorded per task
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Active round-trip reachability probing of each configured Provider**
  (making a real test call to verify it's currently reachable, as opposed
  to "has a real client configured") — deferred; the breadcrumb's own
  named alternative to passive reporting, explicitly not built this pass.
- **A staleness/pass-fail threshold judgment on the last capture run's
  timestamp** (e.g. "flag as failed if no run completed in the last N
  hours") — this pass shows the raw recorded timestamp (or its honest
  absence) only; inventing a threshold is left as a possible fast-follow,
  not decided here.
- **General exception-catching/logging middleware for the ASGI app as a
  whole** (e.g. capturing the `ERROR: Exception in ASGI application` shape
  more generally, across every route, for future observability) — this
  story closes only the one concretely-identified gap in
  `run_agent_conversation`'s own body (Scenario 8, per the operator's
  2026-08-12 decision); a general logging/observability layer is separate,
  larger follow-on work, not decided here.
- **Surfacing Scenario 8's crash-gap fix as its own check/region on the
  System Health page itself** — the fix returns an honest `{"error": ...}`
  to the chat caller in the moment, but there is no persisted "last
  unhandled exception" signal for the System Health view's passive
  checks to read (see Constraints — this pass reuses existing recorded
  signals only). Building such a persisted signal (so a past crash remains
  visible on the health page after the fact, not just in that one chat
  response) is a possible fast-follow, not built here.
- **Extending the Disabled/Health Issue display override to other screens**
  (e.g. Agents Map or per-agent Settings showing a "Disabled" badge for
  consistency with the System Health view) — a real tension the operator's
  decision creates (see Context/Notes), but a separate product question;
  not decided or built here.
- **`REQ-SB-11`'s chronological background-run history/log** — a related
  but distinct requirement (see Context); not expanded into this story.
- **Alerting/notifications** (e.g. email or push on a detected failure) —
  not asked for by the PRD's acceptance text; this is a view the user
  checks, not a push mechanism.
- **Auto-refresh/polling** beyond recomputing fresh on each view open or
  manual refresh (Scenario 7) — no background polling interval is
  specified or built.

## Notes

**Prototype parity:** N/A — this is an entirely new top-level page; there
is no existing `html-prototype/` screen with any region to reconcile
against (confirmed by direct inspection of `index.html`'s sidebar,
`settings.html`, `agents-map.html`, `my-day.html`). Scenarios 1-7 above
enumerate every region the new page must show once `/design REQ-SB-31`
produces the approved prototype: MCP/agent-orchestration status, the
Health Issues list (Disabled agents), per-agent Provider availability, last
capture run status, and the "everything healthy" state. **Superseded:**
none — nothing prior exists for this page to supersede.

**Resolution record (2026-08-12) — ESC-014 resolved.** The operator
answered, verbatim, in chat:

1. **Placement** — *"an new nav page"* — resolves ESC-014's first open
   question. Built as a new top-level nav item/page, not a Settings
   section, not a persistent app-shell indicator.
2. **Provider-not-configured display** — *"If I didn't configure a
   provider (Shouldn't be the case in future) report the issue in and show
   the agent as Disabled and Put it as Health Issue in the new Section."*
   — a real correction to this story's own original design (which had
   proposed a neutral "not available"/"not configured" state, mirroring
   `ADR-011` point 3 / `ADR-014` point 7). Overridden for the System
   Health view specifically: shown as **Disabled**, listed as a **Health
   Issue** (Scenario 3). Scoped to this view only — see Context/
   Constraints for why `ADR-011`/`ADR-014`'s underlying convention and
   other screens (Agents Map, agent Settings) are deliberately untouched.
   **Tension flagged for a human's attention, not resolved here:** the
   same underlying state (`provider_available: false`) now reads
   differently depending which screen the user is on — "Disabled / Health
   Issue" here, still neutral "not configured" elsewhere. Whether Agents
   Map should also show a "Disabled" badge for consistency is a separate
   product question (see Non-Goals); not expanded into this story.
3. **Crash-gap scope** — asked as a direct follow-up (since decision 2
   addressed display, not the separate unhandled-exception gap): operator
   selected **"In this story (Recommended)."** Closed here as Scenario 8 —
   `run_agent_conversation`'s own body (`mcp_client.
   load_vault_query_tools()`, `_GRAPH.ainvoke(initial_state)`) is now
   wrapped in the same honest-failure-funnel pattern `call_model` already
   uses, closing the real, currently-live gap confirmed by direct code
   reading (see Context). This is a backend robustness fix inside
   `agent_orchestration/graph.py` that benefits the chat path directly; the
   System Health page itself does not gain a new region for it this pass
   (no persisted "last unhandled exception" signal exists yet to read
   passively — see Non-Goals).

**Why placement no longer needs a flag:** the operator's decision is
unambiguous and requires no further interpretation — a new top-level nav
page, full stop. What remains before `/plan-tasks` is not a gating
decision but a sequencing dependency: `/design REQ-SB-31` must produce the
approved prototype screen first, since no `html-prototype/` screen exists
for this page yet (see Affected Screens).

**Why this doesn't reopen MUST-FLAG trigger 8 (multiple equally-valid
interpretations):** all three decisions came directly from the operator's
own words, not from the analyst choosing among equally-valid options. The
one genuine open-ended judgement call in this re-spec — whether the
Agents-Map-consistency tension needs its own escalation — was resolved as
an **informational Note**, not a blocking flag: it does not create any
ambiguity in *this* story's own scope (the System Health view's behaviour
is fully and unambiguously specified by Scenario 3/4), it only surfaces a
related-but-separate question for a future story to pick up if wanted.

gate: clear 2026-08-12 — no MUST-FLAG trigger fired on this re-spec: no
material assumption was made (all three decisions are the operator's own
verbatim words); REQ-SB-31 remains finalised PRD text; no ADR was
created or changed (the Disabled/Health Issue display change is a UI
presentation decision for one view, not an architectural change — no
tool, framework, or structural boundary shifted); no `ESCALATIONS.md`
entry was newly *written* by this pass (ESC-014, already open, was
resolved in place, its Trigger text left intact per the file's
append-only convention); this story is not oversized (Scenario 8 is a
small, precisely-scoped two-call try/except addition to already-`Done`
code, not a new subsystem); no contradictory inputs exist; no remaining
multiple-equally-valid-option ambiguity (see above). `ESC-014` in
`ESCALATIONS.md` is updated to `Status: Resolved`, naming this story's own
updated Notes as the resolving artefact. The `REVIEW-QUEUE.md` entry for
`REQ-SB-31-US-01` is updated with a resolution note.
`/design REQ-SB-31` still needs to run — genuinely net-new UI, no
`html-prototype/` screen covers any part of it — before `/plan-tasks`;
this is a sequencing dependency, not a reason to keep the gate flagged.

---

**Architect pass (2026-08-12, `/plan-tasks` step 1).** `/design REQ-SB-31`
already ran and its prototype (`html-prototype/system-health.html`) is
live-verified and approved (`REVIEW-QUEUE.md`). **No new ADR.** The new
backend surface (`app/business/system_health.py`, `app/api/
system_health_router.py`) is a **read-only aggregation module writing no
new persisted state at all** — the same shape `app/business/my_day.py`
(`REQ-SB-12-US-02`) already established with its own "No ADR" reasoning,
composing `provider_registry.list_providers()` (`REQ-SB-19-US-01`,
`Done`) and `vault_writer.load_last_capture_run()` (`REQ-SB-07-US-01`,
`Done`) as-is, plus one new local `GET /mcp` loopback call reusing
`mcp_client.py`'s own already-hardcoded `127.0.0.1:8001` convention — no
new tool, framework, storage mechanism, or trust-surface decision. The
new frontend page/route/nav-item is an ordinary application of
`ADR-010`'s already-`Accepted` routing/styling/component conventions —
zero new CSS (composed entirely from already-ported `.card`/`.badge*`/
`.kv-list`/`.item-list`/`.empty-state` classes, per the approved
prototype's own header note). Scenario 8's `graph.py` fix applies
`ADR-015`'s already-established honest-failure-funnel pattern
(`_call_model`'s own `except Exception` shape) to the two remaining
unwrapped calls in the same function — extending, not reopening,
`ADR-015`. Full reasoning and every new file/function named:
`Implementation/Architecture/architecture.md` → "System Health View —
read-only status aggregation + chat-path crash-gap fix (REQ-SB-31-US-01)".

**Architecture scope (bounds the decomposer/coder):** `architecture.md` →
"System Health View — read-only status aggregation + chat-path crash-gap
fix (REQ-SB-31-US-01)", plus the already-`Accepted` conventions it
extends without reopening — "Frontend Application Architecture" (`ADR-010`
routing/styling/component conventions), "In-App Agent Orchestration
(LangGraph) & Shared MCP Server" (`ADR-015`, for the `graph.py` fix only).
Concrete files this bounds the decomposer/coder to:
`src/backend/app/business/agent_orchestration/graph.py` (Scenario 8 fix
only — the two named calls, no other change),
`src/backend/app/business/system_health.py` (new),
`src/backend/app/api/system_health_router.py` (new),
`src/backend/app/main.py` (router registration only),
`src/frontend/src/pages/SystemHealthPage.tsx` (new),
`src/frontend/src/features/system-health/client.ts` (new),
`src/frontend/src/App.tsx` (new route only), `src/frontend/src/
components/shell/Sidebar.tsx` (new nav item only).

`gate: clear` 2026-08-12 — no ADR triggered, no material assumption made
(every mechanism decision above is a direct, same-shape extension of
already-`Accepted` structural decisions or an already-recorded operator
decision), no contradiction with any Accepted ADR/PRD/`MEMORY.md`
constraint. Ready for the decomposer.

**Decomposer pass (2026-08-12, `/plan-tasks` step 2).** All 8 scenarios
locked as `REQ-SB-31-US-01-AC-01`..`AC-08` (sequential, no non-locked
ACs — every scenario's Given/When/Then was already buildable as written,
only trailing AC-ID tags were added). Four tasks created at the flat root
(`Implementation/Tasks/`): `T01` (backend, `graph.py` Scenario 8 fix, no
dependency — independent of the health-page surface, can be built
first), `T02` (backend, `system_health.py` aggregation module, no
dependency), `T03` (backend, `system_health_router.py`, `depends_on:
[T02]`), `T04` (frontend, `SystemHealthPage.tsx` + nav wiring,
`depends_on: [T03, REQ-SB-12-US-01-T01]` — the latter a task-level edge
since `T04` literally edits `App.tsx`/`Sidebar.tsx`, mirroring
`REQ-SB-12-US-02-T04`'s own identical dependency shape on the same task).
`depends_on` is acyclic: `T02 → T03 → T04`; `T01` stands alone.

Every locked AC has at least one AC-tagged manual verification step:
`AC-01`-`AC-07` (all "when the user opens the System Health view"
scenarios) in `T04` — per the "user-observable outcome" placement rule,
tagged steps live on the frontend page task that actually renders what
`T02`/`T03`'s backend returns; `AC-08` (backend-only, no screen involved)
in `T01`, directly observable via a real chat call with no frontend
dependency. `T02`/`T03` carry non-AC-tagged live-call smoke checks
instead, mirroring `REQ-SB-25-US-01-T07`'s and `REQ-SB-12-US-02-T01`-
`T03`'s own identical split.

No MUST-FLAG trigger fired this pass: no material assumption (every
mechanism decision traces to an already-`Accepted` pattern or an
already-recorded operator decision), no `Draft`/unfinalised requirement
relied on, no ADR created/changed, no `ESCALATIONS.md` entry written, no
oversized decomposition (each task is a single-file-family, one-sitting
unit), every locked AC has a verifiable, tagged step, no contradictory
inputs, and the task breakdown/dependency structure has no genuine
ambiguity (the same read-only-aggregation → router → page shape
`REQ-SB-12-US-02` already established, applied here). `status: Ready`,
`gate: clear`. Eligible for `/plan-sprints`.

---

**Coder pass (2026-08-12, `/implement-sprint SPRINT-019`).** All 4 tasks
built and verified live, in dependency order (`T01`/`T02` independent,
then `T03`, then `T04`). All 8 locked ACs (`AC-01`..`AC-08`) pass — real
backend (`.claude/launch.json` → `second-brain-backend`, restarted once
via the standing `MEMORY.md` specific-PID-kill-and-restart protocol after
the shared dev backend was found serving stale code), real frontend dev
server, real headless-Chrome-via-CDP screenshots compared against the
approved prototype (`html-prototype/system-health.html`), real state
changes induced and reverted against the live vault/`.second-brain/`
state files (never mocked). Full verification transcripts and reasoning
are in each task's own `## Implementation Log`
(`Implementation/Tasks/REQ-SB-31-US-01-T01`..`T04`).

One real, live-discovered bug found and fixed **in-scope**, within `T02`'s
own file (`system_health.py`, not touching any other file): the task's
own literal `httpx.get(_MCP_MOUNT_URL, timeout=3.0)` code sample defaults
to `follow_redirects=False`, so it stopped at the real `/mcp` mount's
`307` (`GET /mcp` → `GET /mcp/`) instead of following through to the
`406` "alive" signal the story's own Context describes — as spec'd, the
real "everything healthy" state would have falsely shown MCP as
unreachable. Fixed by adding `follow_redirects=True`; full root-cause
diagnosis in `T02`'s own Implementation Log. Logged as a scope-internal
judgement call (not an escalation) — `T02` is `gate: flagged` for human
spot-check, `REVIEW-QUEUE.md` pointer added.

This story's own `gate: flagged` (inherited from `T02`'s flag, per the
"a flagged task flags its parent story for the human's spot-check pass"
convention) — not a blocker, `status: Done`. `SPRINT-019` is also `Done`
— see its own Retrospective.
