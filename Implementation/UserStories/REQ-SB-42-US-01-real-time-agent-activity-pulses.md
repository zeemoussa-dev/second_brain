---
id: REQ-SB-42-US-01
title: Real-time per-agent activity pulses and Hub-routed traveling pulses on the Agents Map overview and Section drill-down, pushed over a real-time channel
requirement_ids: [REQ-SB-42]
requirement_section: "REQ-SB-42: Real-Time Agent Activity Pulses (Agents Map)"
phase: P1
status: Ready
gate: clear
gate_reason: "operator reviewed and approved ADR-035 as-is 2026-08-14 — trigger-3 resolved. Ready for /plan-sprints."
sprint: SPRINT-039
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-42-US-01 — Real-time per-agent activity pulses and Hub-routed traveling pulses on the Agents Map overview and Section drill-down, pushed over a real-time channel

## Story

**As a** Second Brain user
**I want** to see, live, which agents are currently doing something and —
when one agent's request is actually being routed to another — a
traveling pulse between the two specific agents involved
**So that** I can tell at a glance what is actively happening on the
Agents Map right now, instead of only ever seeing a static picture or
having to open an agent's own history after the fact

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-42: Real-Time Agent Activity
  Pulses (Agents Map)* — "Replace the Agents Map's static agent-to-agent
  connections with a live, real-time visualization of what's actually
  happening right now: which agents are currently active, and — when one
  agent's request is actually being routed to another (Hub-to-Hub
  cross-section routing) — a traveling pulse between the two specific
  agents involved." Acceptance: "On both the Agents Map overview and a
  Section's drill-down Agents Tree, an agent visually pulses/glows while
  it is (a) running a capture or Skill, (b) generating a chat reply, or
  (c) engaged in a Hub-routed cross-section request to/from another
  agent — the latter rendered as a traveling pulse along the connecting
  line between the two specific agents. An agent with an open
  pending-approval record renders with a distinct, steady (non-animated)
  highlight instead, so a blocked/waiting agent is never visually
  confused with an actively-working one. Updates arrive via a real-time
  push channel (near-instant, not polling). The existing decorative
  KB↔Hub spoke animation is unaffected — this is a new, additive
  data-driven layer."
- **PRD breadcrumb (2026-08-13, operator-directed, cited verbatim, NOT
  re-decided here):** "instead of a static Agents Connection... show real
  time inter communication between agents like pulses and showing active
  Agents at the moment who is currently running a task (as a Pulse
  Visual)." Clarified via requirements-gathering session, verbatim
  decisions: (1) "active" covers four triggers — running a capture/Skill,
  generating a chat reply, an in-flight Hub-routed cross-section request
  (`REQ-SB-20`, Done), and an open pending-approval record (`REQ-SB-21`,
  Done — Supervised-mode gate); (2) both a per-agent glow (for the first
  three, general "this agent is working" states) and a traveling pulse
  between two specific agents (for the Hub-routed case only) are wanted,
  together; (3) an open pending-approval record renders as a visually
  distinct, steady/non-animated highlight — never confused with the
  animated pulse; (4) surfaces on both the Agents Map overview and a
  Section's drill-down Agents Tree; (5) the existing decorative KB↔Hub
  spoke pulse (`agents-map.html`'s always-on `kb-pulse-dot` animation,
  data-independent) is kept unchanged as ambient texture — this
  requirement is a new, additive, data-driven layer on top, not a
  replacement; (6) real-time means near-instant push, not a polling
  interval — operator explicitly chose push over a 2–5s poll.
- **Genuinely no "is this agent doing something right now" concept exists
  today.** `REQ-SB-11`'s Agent Activity & Error Observability (Done)
  records completed history entries only, written after the fact
  (`vault_writer.append_agent_history_entry`) — there is no live/ephemeral
  in-progress marker written at the start of a real dispatch path (a
  capture run, a Skill invocation, chat generation, a Hub-routed call, a
  pending-approval creation) and cleared at completion. This story's
  backend half needs to introduce that concept from scratch — not
  designed here, left to `/plan-tasks`, since which dispatch call sites
  set/clear it and how it's represented server-side is an architecture
  decision, not a product one.
- **No real-time push transport exists today.** Every existing surface in
  this codebase (`GET /agents`, `GET /agents/{id}/history`, My Day, System
  Health, Vault Search, etc.) is REST/poll-shaped. The operator explicitly
  chose push ("real time means near-instant push, not a polling
  interval") over a 2–5s poll — introducing WebSocket or SSE is a genuine
  new architectural capability the PRD's own context explicitly names as
  "not a small lift... the specific choice between them is an
  architect-level call." Neither is decided here; both scenarios below
  are written to the observable behavior (near-instant push delivery), not
  to a specific transport, so the architect is free to choose either.
- **Depends on two already-`Done` mechanisms this story's activity states
  key off, not new business logic:** `REQ-SB-20-US-01` (Section Hub
  Intelligence & Cross-Section Routing, **Done**) — the Hub-routed
  cross-section request is the one case with two real, named endpoints,
  and its own `route_cross_section_request(...)` result already records
  both hops (`from_section_id`/`matched_section_id`) as explicit fields,
  the natural source for "which two agents does the traveling pulse run
  between." `REQ-SB-21-US-01` (Agent Working Modes, **Done**) — the
  pending-approval record (`pending_approval_registry.py`,
  `agent_pending_approvals.json`) is the existing, already-persisted
  concept this story's "steady, non-animated highlight" state reads.
  Neither story's own behavior changes here — this story only reads their
  existing outputs/state to decide when to render which visual, plus adds
  the genuinely new "in-progress right now" marker for the other three
  activity triggers (capture/Skill run, chat generation) that has no
  existing analog.
- **No `html-prototype/` screen shows this.** `agents-map.html`'s canvas
  (Hub nodes, agent nodes, rings, the existing always-on decorative
  `kb-pulse-dot` spoke animation) has no live/animated per-agent activity
  concept, no traveling-pulse-between-two-agents concept, and no distinct
  steady/pending-approval highlight concept — confirmed by direct
  inspection. The Section drill-down (`BUGFIX-02-US-01`'s semantic-zoom
  view) likewise has no such concept. A `/design` pass is needed before
  this story can proceed past `/plan-tasks` — see the flag below.
- **Exact visual treatment left open, not guessed here** (per the PRD's
  own breadcrumb): glow radius/color for the per-agent "working" state,
  traveling-pulse styling relative to the existing `kb-pulse-dot`, and
  whether the Section drill-down's own Agents Tree needs its own
  connection-line geometry for the Hub-routed traveling-pulse case or can
  reuse the overview's existing spoke/cluster-line geometry. These are
  `/design` and `/plan-tasks` questions, not resolved by this spec.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then
edge cases and error states. Do NOT add AC-IDs — the decomposer assigns them
at /plan-tasks. These scenarios describe only the externally observable
behaviour the PRD's own Acceptance text commits to; they deliberately do not
assert a specific transport (WebSocket vs SSE), a specific "in-progress"
storage mechanism, or a specific visual treatment — all three are left open
per the Context above. -->

### Scenario 1: An agent glows while running a capture or Skill

```gherkin
Given the user is viewing the Agents Map overview or a Section's
    drill-down Agents Tree
When an agent begins running a capture pipeline or a Skill
Then that agent renders with an animated glow/pulse for as long as the
    run is in progress
When the run completes
Then the glow/pulse clears from that agent, near-instantly, without the
    user needing to refresh or re-navigate the page
```

<!-- AC-ID: REQ-SB-42-US-01-AC-01 -->

### Scenario 2: An agent glows while generating a chat reply

```gherkin
Given the user is viewing the Agents Map overview or a Section's
    drill-down Agents Tree
When an agent is generating a chat reply (a real conversational turn is
    in flight)
Then that agent renders with the same animated glow/pulse used for a
    capture/Skill run, for as long as the reply generation is in
    progress
When the reply is delivered
Then the glow/pulse clears from that agent, near-instantly
```

<!-- AC-ID: REQ-SB-42-US-01-AC-02 -->

### Scenario 3: A Hub-routed cross-section request renders a traveling pulse between the two specific agents involved

```gherkin
Given the user is viewing the Agents Map overview or a Section's
    drill-down Agents Tree
When one agent's request is actually routed, via the Hub-to-Hub
    mechanism, to a second, specific agent
Then a traveling pulse animates along the connecting line between
    exactly those two agents — not a generic glow on either agent alone
When the routed request completes
Then the traveling pulse clears, near-instantly
```

<!-- AC-ID: REQ-SB-42-US-01-AC-03 -->

### Scenario 4: An agent with an open pending-approval record renders a distinct, steady, non-animated highlight

```gherkin
Given an agent has an open (unresolved) pending-approval record
When the user is viewing the Agents Map overview or a Section's
    drill-down Agents Tree
Then that agent renders with a steady, non-animated highlight, visually
    distinct from the animated glow/pulse used for an actively-working
    agent
  And this agent is never shown with the animated glow/pulse while its
    pending-approval record remains open, even if it is also otherwise
    idle
When the pending approval is resolved (approved or declined)
Then the steady highlight clears from that agent, near-instantly
```

<!-- AC-ID: REQ-SB-42-US-01-AC-04 -->

### Scenario 5: Multiple agents can be independently active at the same time, each shown correctly

```gherkin
Given two or more agents each independently begin one of the activity
    states above (a capture/Skill run, a chat reply, a Hub-routed
    request, or an open pending approval) at overlapping times
When the user views the Agents Map overview or a Section's drill-down
    Agents Tree
Then each agent's own current activity state renders correctly and
    independently — one agent's glow/pulse/highlight never bleeds onto,
    replaces, or is confused with another agent's own state
```

<!-- AC-ID: REQ-SB-42-US-01-AC-05 -->

### Scenario 6: An idle agent shows no activity indicator

```gherkin
Given an agent is not currently running a capture/Skill, not generating
    a chat reply, not engaged in a Hub-routed request, and has no open
    pending-approval record
When the user views the Agents Map overview or a Section's drill-down
    Agents Tree
Then that agent renders with no activity glow/pulse/highlight of any
    kind
```

<!-- AC-ID: REQ-SB-42-US-01-AC-06 -->

### Scenario 7: Updates arrive via real-time push, not polling

```gherkin
Given the user has the Agents Map overview or a Section's drill-down
    Agents Tree open
When an agent's activity state changes (starts, changes kind, or clears)
Then the change is reflected on the open screen near-instantly, delivered
    over a real-time push channel
  And the user is never required to manually refresh, and the screen does
    not rely on a fixed polling interval to eventually pick up the change
```

<!-- AC-ID: REQ-SB-42-US-01-AC-07 -->

### Scenario 8: The existing decorative KB↔Hub spoke pulse is unaffected

```gherkin
Given the Agents Map overview's existing always-on, data-independent
    KB↔Hub spoke pulse animation (kb-pulse-dot)
When this story's new, additive, data-driven activity layer is present
Then the existing decorative spoke pulse continues to render exactly as
    before, unchanged and unaffected by any agent's activity state
```

<!-- AC-ID: REQ-SB-42-US-01-AC-08 -->

## Affected Screens

- `html-prototype/agents-map.html` — the canvas (Hub nodes, agent nodes,
  rings, existing `kb-pulse-dot` decorative spoke animation) needs a new,
  additive per-agent glow/pulse treatment, a traveling-pulse-along-a-line
  treatment for the Hub-routed case, and a distinct steady/non-animated
  pending-approval highlight. **Not present in the approved prototype in
  any form** — no design authority exists for any of these three visual
  treatments. See the flag below and the Notes' Prototype parity
  subsection.
- The Section drill-down Agents Tree (`BUGFIX-02-US-01`'s semantic-zoom
  view, part of `agents-map.html`'s own live app surface, not a separate
  prototype file) needs the identical treatment, including deciding
  whether it reuses the overview's connection-line geometry for the
  traveling-pulse case or needs its own — left open, see Context.

## Dependencies

- **Blocked by:** `REQ-SB-20-US-01` (Section Hub Intelligence &
  Cross-Section Routing, **Done**) — the Hub-routed cross-section request
  this story's traveling-pulse scenario (Scenario 3) keys off. Satisfied.
- **Blocked by:** `REQ-SB-21-US-01` (Agent Working Modes, **Done**) — the
  pending-approval record this story's steady-highlight scenario
  (Scenario 4) reads. Satisfied.
- **Related to:** `REQ-SB-11-US-01` (Agent Activity & Error Observability,
  **Done**) — records completed history entries only, after the fact;
  this story needs a genuinely new "in progress right now" concept this
  requirement does not provide, not an extension of it.
- **Related to:** `BUGFIX-02-US-01` (Agents Map semantic zoom / drill-down,
  **Done**) — the Section drill-down Agents Tree surface this story's
  scenarios also apply to.
- **External:** a real-time push transport (WebSocket or SSE) does not
  exist in this codebase today — the specific choice is an architect-level
  call, left to `/plan-tasks`, not decided here.

## Constraints

- **"Active" covers exactly four triggers, operator-resolved, not
  reinterpreted:** running a capture/Skill, generating a chat reply, an
  in-flight Hub-routed cross-section request, and an open pending-approval
  record. No other state renders any activity indicator.
- **A Hub-routed cross-section request renders as a traveling pulse
  between the two specific agents involved** — not a generic per-agent
  glow on either side. This is the one case with two real, named
  endpoints, per the operator's own resolution.
- **An open pending-approval record renders as a distinct, steady,
  non-animated highlight** — never the same animated treatment as an
  actively-working agent, and never simultaneously with the animated
  glow/pulse for that same agent.
- **Both the Agents Map overview and a Section's drill-down Agents Tree**
  must show this — not one surface only.
- **The existing decorative KB↔Hub spoke pulse (`kb-pulse-dot`) is kept
  unchanged** — this requirement is additive, never a replacement of that
  existing animation.
- **Real-time means push, not polling** — the operator explicitly chose a
  near-instant push channel over a 2–5s poll interval. The specific
  transport (WebSocket vs SSE) is left to `/plan-tasks`.
- This story cannot be fully specced past `/plan-tasks` until a `/design`
  pass produces an approved visual treatment for all three new elements
  (per-agent glow, traveling pulse, steady pending-approval highlight) on
  both surfaces.

## Implementation Tasks

| Task | Title | Depends on | ACs covered |
|---|---|---|---|
| [[REQ-SB-42-US-01-T01]] | `app/business/agent_presence.py` — in-memory activity/hub-route registry, snapshot, broadcast | — | (supports all) |
| [[REQ-SB-42-US-01-T02]] | Instrument capture/Skill run + chat generation (`email_classification.py`, `skill_registry.py::_dispatch_skill`, `agents_router.py::chat`) | T01 | AC-01, AC-02 |
| [[REQ-SB-42-US-01-T03]] | Instrument the Hub-routed traveling pulse (`knowledge_bootstrap.py`'s two hops) | T01 | AC-03 |
| [[REQ-SB-42-US-01-T04]] | Instrument pending-approval broadcast-only (`pending_approval_registry.py`) | T01 | AC-04 |
| [[REQ-SB-42-US-01-T05]] | `GET /agent-presence/stream` (SSE), registered in `main.py` | T01 | AC-07 |
| [[REQ-SB-42-US-01-T06]] | Frontend `agent-presence/client.ts` (native `EventSource` wrapper) | T05 | (supports AC-07) |
| [[REQ-SB-42-US-01-T07]] | Agents Map overview rendering (glow/pending-approval/traveling pulse, CSS port) | T06 | AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-08 |
| [[REQ-SB-42-US-01-T08]] | Section drill-down rendering (identical treatment + captioned-cluster-line proposal) | T06 | AC-01, AC-02, AC-03, AC-04, AC-05, AC-06 |

Dependency graph: `T01 → {T02, T03, T04, T05} → T06 → {T07, T08}`. `T02`/`T03`/`T04`
are independently parallel-buildable once `T01` lands; `T07`/`T08` are
independently parallel-buildable once `T06` lands. No cycles.

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Any change to `REQ-SB-20`'s own Hub-routing behavior or
  `REQ-SB-21`'s own working-mode/pending-approval behavior** — this story
  only visualizes their existing outputs; neither mechanism's own logic
  changes here.
- **Within-Section (agent-to-agent, same-Section) activity visualization**
  — the PRD's Acceptance text only names the Hub-routed cross-section case
  for the traveling-pulse treatment; `REQ-SB-20-US-01`'s own within-Section
  routing remains out of scope (deferred by that story itself).
- **A general-purpose event/notification system beyond this specific
  visualization** — this story is scoped to the Agents Map's own visual
  activity layer, not a reusable pub/sub mechanism for other surfaces
  (though the architect may choose a transport that happens to be
  reusable — not required here).
- **Historical/replay visualization of past activity** — this is a live,
  present-moment view only; `REQ-SB-11`'s own completed-history surface is
  unchanged and remains the place to look at what already happened.
- **Choosing or building the real-time transport itself in this pass** —
  left entirely to `/plan-tasks` (architect-level call).
- **Designing the exact visual treatment in this pass** — left to
  `/design`.

## Notes

**Prototype parity (agents-map.html):**

- Canvas (Hub nodes, agent nodes, rings, existing always-on decorative
  `kb-pulse-dot` spoke animation) — **Superseded/extended, not covered.**
  The existing decorative pulse is kept unchanged (Scenario 8), but this
  story adds three new visual elements on top of the same canvas — a
  per-agent animated glow/pulse, a traveling pulse along a connecting
  line between two specific agents, and a distinct steady/non-animated
  pending-approval highlight — none of which exist in the approved
  prototype today. **`net-new-design-needed`.**
- Section drill-down Agents Tree (semantic-zoom view, `BUGFIX-02-US-01`)
  — same three elements needed, plus an open question (left to
  `/design`/`/plan-tasks`) on whether the traveling-pulse case reuses the
  overview's own connection-line geometry or needs its own. **Not
  covered by the approved prototype.**
- Side panel (Settings/Actions/Chat/History) — **N/A**, not touched by
  this story; this is a canvas-level visualization concern only.

**Why `gate: flagged`:**

1. No material product-level assumption was made beyond what the PRD's
   own context already resolves verbatim (the four activity triggers, the
   glow-vs-traveling-pulse split, the steady pending-approval highlight,
   both surfaces, the unaffected decorative pulse, push-over-poll) — all
   directly quoted from the operator's own clarifying session, not guessed.
2. `REQ-SB-42` is not marked `<!-- Draft -->`/unfinalised in the PRD.
3. N/A here (architect/ADR trigger) — but `/plan-tasks` should expect a
   real, new architectural decision (the push-transport choice) and a
   likely ADR.
4. No `ESCALATIONS.md` entry was written by this pass.
5. Not oversized — one bounded visualization layer over two already-Done
   mechanisms plus one new "in-progress" concept; kept as one story since
   the per-agent glow and the Hub-routed traveling pulse share the same
   underlying "is this agent doing something right now" data source and
   have no independent value apart from each other (this project's
   standing "no independent value alone" test).
6. N/A (coder trigger).
7. No contradictory PRD inputs found.
8. **The controlling flags, both genuinely live:** `net-new-design-needed`
   (no `html-prototype/` screen shows any of the three new visual
   elements) and the real-time-transport choice being explicitly named by
   the PRD's own context as an architect-level call not yet made. Neither
   is guessed past here.

**What to do next:** run `/design REQ-SB-42` for the per-agent
glow/pulse, the traveling pulse, and the steady pending-approval
highlight on both the Agents Map overview and the Section drill-down;
then `/plan-tasks` (architect) resolves the WebSocket-vs-SSE transport
choice and the new "activity in progress" state concept.

gate: flagged 2026-08-13 — net-new-design-needed (no prototype coverage
for any of the three new visual elements) plus the real-time-transport
choice being an explicit open architect-level call. A `REVIEW-QUEUE.md`
entry has been added.

**Update, 2026-08-14 (`/plan-tasks REQ-SB-42-US-01` step 1 — architect).**
Design already approved (operator, 2026-08-13); this pass resolves the
remaining architect-level open items via a new ADR, per `Implementation/
Pipeline.md`'s MUST-FLAG trigger 3 (ADR created) — `gate:` flips back to
`flagged` accordingly (does not halt the decomposer, which proceeds in the
same `/plan-tasks` pass). Transport: **Server-Sent Events**, not WebSocket
(one-directional push is all this story needs). New ephemeral, in-memory-
only `app/business/agent_presence.py` registry (never `.second-brain/`-
persisted — the PRD's own "ephemeral, not a durable vault-writer concern"
framing, honored literally), instrumented at five real dispatch call sites;
pending-approval state is read live from the existing
`pending_approval_registry`, never duplicated. New `GET
/agent-presence/stream` SSE endpoint. Full reasoning:
`Implementation/Architecture/ADR.md` → `ADR-035`.

**Architecture scope:** §Real-Time Agent Activity Pulses (REQ-SB-42-US-01,
see ADR-035), §In-App Agent Orchestration (LangGraph) & Shared MCP Server
(for `route_cross_section_request`/`run_agent_conversation`/
`_dispatch_skill` call-site context only — unmodified by this story), §Agent
Activity & Error Observability (contrast only — this story does not touch
`agent_activity.py`/`REQ-SB-11`'s own persisted history).

---

**Decomposer pass (`/plan-tasks` step 2, 2026-08-14).** All 8 Gherkin
scenarios tightened (no wording changes beyond the trailing tag — the
analyst's/architect's own text already read as directly buildable against
`ADR-035`'s real module shape) and locked as `REQ-SB-42-US-01-AC-01`..`AC-08`
(`locked: true`, no non-locked exceptions). 8 task files created (`T01`-`T08`,
flat root): `T01` (new `agent_presence.py`), `T02`/`T03`/`T04` (the five real
dispatch call sites `ADR-035` point 3 names, split by file/concern: single-
agent capture+skill+chat; the Hub-routed traveling pulse; pending-approval
broadcast-only), `T05` (the SSE endpoint), `T06` (the frontend `EventSource`
wrapper), `T07`/`T08` (overview and drill-down rendering, sharing one
subscription). `depends_on` wired acyclic: `T01 → {T02, T03, T04, T05} → T06
→ {T07, T08}` — every locked AC has at least one AC-tagged manual
verification step across the task set (`T07`/`T08` jointly own the
page-level Scenarios 1-6, since the parent story's own Constraint requires
BOTH surfaces to show every state independently; `T05` owns AC-07 at the
transport layer, `T07` re-confirms AC-08's regression guard).

Structural note: every locked AC in this story is behavioural (a real,
timed state transition on a real screen), not a pure DOM-structure
assertion — `T07`/`T08`'s own Tests block verifies each one via a real,
induced backend state change plus a real rendered CSS class, per this
project's manual-verification-mode convention; no AC is weakened to a
static/structural-only check.

**No new decomposer-owned MUST-FLAG trigger fired this pass** — every
module/function name, file, and endpoint this decomposition builds against
is `ADR-035`'s own already-made Decision, not a decomposer assumption; the
CSS classes `T07`/`T08` port are copied verbatim from the already-approved
`html-prototype/agents-map.html` design-pass revision, not invented; no
locked AC is unverifiable (every one maps to a real, inspectable outcome —
an SSE `data:` event, a rendered CSS class, an SVG element); `depends_on`
is acyclic; no task exceeds one working session (each is a single file or
a tightly-scoped, mechanically-similar group of call sites). `gate` stays
`flagged` — trigger-3 (`ADR-035` created) is carried unchanged from the
architect pass, per this file's own rule "if the architect flagged the
story this run for an ADR change, leave it `gate: flagged`." No new
`REVIEW-QUEUE.md` entry needed — the architect's own 2026-08-14 entry
already asks the human to review `ADR-035` and the resulting tasks
together, which this pass's 8 task files now make reviewable. No
`ESCALATIONS.md` entry written by this pass. `status:` was already `Ready`
entering this pass (set alongside the architect's own step-1 update); this
pass confirms that status is now fully earned — every AC locked, every
task written and set to `status: Ready` in lockstep, `depends_on` acyclic —
rather than transitioning it.
