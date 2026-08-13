---
id: REQ-SB-21-US-01
title: Per-agent working mode (Autonomous / Supervised / Manual), set on the Agent Settings surface, gating both chat-triggered and background-pipeline actions
requirement_ids: [REQ-SB-21]
requirement_section: "REQ-SB-21: Agent Working Modes"
phase: P1
status: Done
gate: clear
gate_reason: "Built and verified live 2026-08-12 (coder, /implement-sprint SPRINT-021) — all 9 tasks Done, all 8 locked ACs (AC-01..AC-08) verified live against the real backend/frontend/vault/Outlook/Compass. gate stays flagged — T07 logged two scope-internal judgement calls for human spot-check (a CSS file ported verbatim into agent-panel.css though not named in T07's own Files to Modify; a live-discovered unhandled-promise-rejection fix) — not a blocker; see REVIEW-QUEUE.md and each task's own Implementation Log. ADR-020's own human review (this entry's prior gate_reason) is resolved by this build — ESCALATIONS.md -> ESC-013 closed."
sprint: SPRINT-021
created: 2026-08-11
updated: 2026-08-12
---

# REQ-SB-21-US-01 — Per-agent working mode (Autonomous / Supervised / Manual), set on the Agent Settings surface, gating both chat-triggered and background-pipeline actions

## Story

**As a** Second Brain user
**I want** to choose, per agent, whether it acts independently
(Autonomous), asks for my approval before acting (Supervised), or stays
dormant until I explicitly ask it to do something (Manual)
**So that** I control how much trust I extend to each agent individually,
instead of every agent always acting on its own the moment it has
something to do

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-21: Agent Working Modes* — "Every
  agent has one of three working modes, chosen by the user: Autonomous
  (acts independently, no approval needed), Supervised (proposes an action
  and waits for the user's approval before taking it — human in the loop),
  and Manual (stays dormant and only acts when the user explicitly asks it
  to do something)." Acceptance: "Every agent has an assigned working mode
  (Autonomous, Supervised, or Manual), visible and changeable by the user;
  an Autonomous agent takes its actions without asking; a Supervised agent
  proposes an action and waits for explicit user approval before taking it;
  a Manual agent takes no action of its own until the user explicitly
  requests one."
- **PRD breadcrumb (2026-08-11, operator-authored, cited verbatim, NOT
  re-decided here):** "Mode names proposed by Claude ('Autonomous'/
  'Supervised'/'Manual'), mapping directly to the operator's own 'Fully
  Autonomous'/'Need Approval before Taking an action (Human in the
  loop)'/'Doesn't work till I ask it to do a task') and not objected to.
  Genuinely open, not decided here: where working mode is set..., what
  'propose an action and wait for approval' looks like concretely for a
  background capture pipeline (REQ-SB-07/08/09) versus a chat-triggered
  action (REQ-SB-13) — these may need different UI treatment — and the
  default mode for existing and newly-added agents. Left to `/spec`, not
  guessed here."
- **Resolved here, by safe precedent (not a guess):** working mode is set
  per-agent on the Agent Settings surface (`AgentDetailPanel.tsx`, built by
  the already-`Done` `REQ-SB-13-US-01`), the same `kv-list` surface that
  will carry `REQ-SB-18-US-01`'s Section picker and `REQ-SB-19-US-01`'s
  Provider picker — a working-mode `<select>` follows the identical,
  already-established pattern. This story does not need `REQ-SB-18-US-01`/
  `REQ-SB-19-US-01` to be `Done` first, since the panel itself already
  exists (`REQ-SB-13-US-01`, `Done`) and a mode picker is an independent
  field on it, not dependent on Section/Provider.
- **Resolved 2026-08-11, operator-confirmed:**
  1. **Default working mode: Autonomous.** Behavior-preserving — no agent
     regresses from today's defacto behavior (scheduled/app-start
     pipelines run unconditionally, chat-triggered actions execute
     immediately, per `ADR-011`) unless the user explicitly switches it to
     Supervised or Manual. Same posture `REQ-SB-19-US-01` used for Compass
     staying every agent's default Provider.
  2. **The Supervised background-pipeline approval gets a real, dedicated
     surface, built now** — a lightweight Pending Approvals area (e.g. on
     My Day or Settings) listing proposed actions awaiting approval,
     needed for Supervised mode to mean anything for a background pipeline
     with no chat window open at trigger time. Not deferred to REQ-SB-11
     (Observability, not yet started). Exact placement/shape is a
     `/design` question (see Notes), not decided here — only that it gets
     built in this pass, not later.
- **Corrected 2026-08-12, operator-authorized (`ESCALATIONS.md` → `ESC-013`)
  — supersedes the architect's own `ADR-018` judgement call, caught before
  any code exists:** `ADR-018` (`/plan-tasks` step 1, 2026-08-12) built two
  assumptions of its own, never operator-confirmed: (1) Supervised gates
  the entire action uniformly by *trigger source* — chat/direct-triggered
  and background-triggered alike — regardless of whether the action reads
  or writes; (2) Manual differs from Supervised only on the
  background/scheduled trigger, treating a matched chat message or
  Available-Actions button press as "the user explicitly asking,"
  resolvable identically to Autonomous. Asked to confirm this reading, the
  operator gave materially different, authoritative semantics directly:
  - **Manual:** "Can't Pull unless I asked him to... No Agent can Trigger
    an Action" — only a *direct human* ask counts as "asked." A
    scheduled/background trigger does not run it (`ADR-018` already got
    this part right) — and **neither does another agent's Hub-routed
    request** (`ADR-017`, `REQ-SB-20`), a trigger source `ADR-018` never
    considered as a gate input at all, since the two ADRs were written in
    the same session and never reconciled against each other.
  - **Supervised:** "It is running — but some writing or modifying needs
    my approval" — the agent operates and responds normally/immediately
    for read-only/query actions; **only actions that write or modify
    something (the vault, an external system) require approval first,
    regardless of what triggered them** (chat, direct button, or
    background). This replaces `ADR-018`'s trigger-source gate with a gate
    on the action's own read/write nature — a genuinely different axis,
    not a parameter tweak.
  - **Autonomous:** unchanged — runs everything itself immediately, no
    approval ever needed.
  This means `app/business/agent_registry.py`'s existing action
  definitions need a new read-only-vs-mutating classification per action —
  a real, new architectural concept (see Constraints below) left for
  `/plan-tasks` to design, not designed here. The Acceptance Criteria below
  are rewritten to this corrected semantics. `ADR-018` itself is not
  edited (stays `Accepted`, per hard rule 1) — a new superseding ADR is
  expected at the next `/plan-tasks` pass. Full record: `## Notes` below
  and `ESCALATIONS.md` → `ESC-013`.
- **Precedent surfaces this story attaches to (all already `Done`):**
  `REQ-SB-13-US-01` built the Agent Settings detail panel
  (`AgentDetailPanel.tsx`) this story adds a working-mode picker to, and
  the chat action-triggering funnel (`app/api/agents_router.py::
  _invoke_action`, `ADR-011`) a Supervised agent's chat-triggered gate must
  hook into. `REQ-SB-07-US-01`/`REQ-SB-08-US-01` built the scheduled/
  app-start capture pipelines (`app/business/capture_scheduler.py` and its
  callers) a Supervised agent's background-pipeline gate must hook into.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. Re-specced 2026-08-12 (ESCALATIONS.md -> ESC-013) around the
operator's own corrected semantics: Supervised gates by the action's own
read-only-vs-mutating nature, not by what triggered it; Manual additionally
excludes another agent's Hub-routed request, not just a background/scheduled
trigger. These scenarios require agent_registry.py's action definitions to
carry a new read-only-vs-mutating classification per action — a real, new
architectural concept left for /plan-tasks to design, not designed here. They
deliberately do not assert a specific default mode value or a specific
background-pipeline approval UI mechanism — both left open, see Context
above. -->

### Scenario 1: An agent's working mode is visible and changeable

```gherkin
Given the user is viewing an agent's Agent Settings surface
When the user views that agent's settings
Then the agent's current working mode (Autonomous, Supervised, or Manual)
    is shown in a working-mode picker
When the user selects a different working mode from the picker
Then the agent's working mode updates to the newly selected one, persisted
    server-side
```
<!-- AC-ID: REQ-SB-21-US-01-AC-01 -->

### Scenario 2: An Autonomous agent takes its actions without asking

```gherkin
Given an agent's working mode is Autonomous
When that agent has an action to take, whether triggered by a matched
    chat message, a direct Available Actions button press, its own
    background/scheduled pipeline trigger, or another agent's Hub-routed
    request
Then the agent takes the action directly, without creating a pending
    approval or asking for approval first
```
<!-- AC-ID: REQ-SB-21-US-01-AC-02 -->

### Scenario 3: A Supervised agent's write/mutating action proposes and waits for approval, regardless of trigger source

```gherkin
Given an agent's working mode is Supervised
  And it has an action classified as writing or modifying something (the
    vault, an external system) — not read-only
When that action is triggered — whether by a matched chat message, a
    direct Available Actions button press, or the agent's own
    background/scheduled pipeline trigger
Then the agent proposes the action and describes what it would do, shown
    as a pending-approval card
  And the action is not taken until the user explicitly approves it
When the user approves the proposed action
Then the agent takes the action
```
<!-- AC-ID: REQ-SB-21-US-01-AC-03 -->

### Scenario 3b: A Supervised agent's proposed write/mutating action is not approved

```gherkin
Given an agent's working mode is Supervised, and it has a write/mutating
    action proposal pending the user's approval, whatever triggered it
When the user declines the proposed action instead of approving it
Then the action is never taken, and the proposal is recorded as declined
```
<!-- AC-ID: REQ-SB-21-US-01-AC-04 -->

### Scenario 4: A Supervised agent's read-only action proceeds immediately, regardless of trigger source

```gherkin
Given an agent's working mode is Supervised
  And it has an action classified as read-only/query — it does not write
    or modify anything
When that action is triggered — whether by a matched chat message, a
    direct Available Actions button press, or the agent's own
    background/scheduled pipeline trigger
Then the agent takes the action directly, without creating a pending
    approval or waiting for approval first — identical to how an
    Autonomous agent would handle it
```
<!-- AC-ID: REQ-SB-21-US-01-AC-05 -->

### Scenario 5: A Manual agent takes no action of its own until explicitly asked by a human directly

```gherkin
Given an agent's working mode is Manual
When that agent's own background/scheduled pipeline trigger point is
    reached
Then the agent takes no action and records no pending approval
When the user explicitly asks the agent to perform a specific task, via a
    matched chat message or a direct Available Actions button press
Then the agent performs that task immediately, whether the action is
    read-only or write/mutating
```
<!-- AC-ID: REQ-SB-21-US-01-AC-06 -->

### Scenario 5b: A Manual agent is not triggered by another agent's Hub-routed request

```gherkin
Given an agent's working mode is Manual
When another agent's Hub-routed request (REQ-SB-20) identifies this agent
    as a candidate that could help with something
Then this agent takes no action of its own and records no pending
    approval — only a direct human ask (a matched chat message or an
    Available Actions button press) counts as the user "explicitly
    asking"; no agent can trigger an action on a Manual-mode agent
```
<!-- AC-ID: REQ-SB-21-US-01-AC-07 -->

### Scenario 6: Every agent has exactly one working mode assigned at all times

```gherkin
Given any existing agent, or a newly added agent
When the user views that agent's Agent Settings surface
Then the agent has exactly one of the three working modes assigned — it
    is never shown with no mode set
```
<!-- AC-ID: REQ-SB-21-US-01-AC-08 -->

## Affected Screens

- `html-prototype/agents-map.html` — the agent detail side panel's Settings
  block needs a new working-mode field/picker. Not present in the approved
  prototype; no design authority exists for its visual shape. The panel's
  chat thread needs a way to render a pending, awaiting-approval proposal
  distinct from a normal message — also not present. No screen anywhere in
  the prototype has any pending-approval affordance for a background
  pipeline's proposed action — see Notes.

## Dependencies

- **Blocked by:** `REQ-SB-12-US-01` (`Done`) — the Settings/Agents Map app
  shell this story's picker is added within. Satisfied.
- **Blocked by:** `REQ-SB-13-US-01` (`Done`) — the Agent Settings detail
  panel this story adds a working-mode picker to, and the chat/action
  funnel this story's Supervised gate wraps, must exist first. Satisfied.
- **Related to:** `REQ-SB-07-US-01`, `REQ-SB-08-US-01` (both `Done`) — the
  real scheduled/app-start background pipelines this story's Supervised/
  Manual gates must hook into for their background-trigger scenarios.
- **Related to:** `ADR-011` — the existing chat action-triggering funnel
  (`agents_router.py::_invoke_action`) this story's Supervised/Manual gate
  for chat-triggered actions is a strong candidate to hook into; exact
  mechanism left to `/plan-tasks`.
- **Related to:** `REQ-SB-18-US-01`/`REQ-SB-19-US-01` — share the same
  Agent Settings surface `kv-list` pattern this story's mode picker follows
  (not a build dependency; the panel itself already exists via
  `REQ-SB-13-US-01`).
- **External:** none new.

## Constraints

- Every agent must have exactly one working mode assigned at all times —
  never unset/null. **Default value: Autonomous** (operator-resolved,
  2026-08-11), for both existing and newly-added agents.
- **Autonomous behavior must exactly match today's defacto behavior** — no
  regression for any agent whose mode is (or defaults to) Autonomous, the
  same "no change in behaviour unless the user explicitly changes it"
  posture `REQ-SB-19-US-01` established for Compass remaining the default
  Provider.
- **Supervised gating is decided by the action's own read-only-vs-mutating
  nature, not by trigger source** (corrected 2026-08-12, `ESC-013` —
  supersedes this constraint's prior trigger-source framing). A read-only/
  query action proceeds immediately regardless of what triggered it; a
  write/mutating action always proposes-and-waits, regardless of what
  triggered it (chat, direct button, or background/scheduled). This
  requires `app/business/agent_registry.py`'s action definitions to carry
  a new, real read-only-vs-mutating classification per action — a genuine
  new architectural concept, not a parameter tweak. Left for `/plan-tasks`
  to design (a superseding ADR over `ADR-018`); not designed here.
- **Manual mode only executes on a direct human ask** (corrected
  2026-08-12, `ESC-013`) — a matched chat message or an Available Actions
  button press. Neither a background/scheduled pipeline trigger, nor
  another agent's Hub-routed request (`REQ-SB-20`), counts as "asked." No
  agent can trigger an action on a Manual-mode agent.
- **A real Pending Approvals surface is in scope for this pass**
  (operator-resolved, 2026-08-11 — not deferred to REQ-SB-11). Its exact
  placement/shape needs its own `/design` pass; the decision to build it
  now, rather than defer, is final.

## Implementation Tasks

**Current table (2026-08-12, decomposer pass — re-derived against `ADR-020`'s
corrected two-axis gate, resolving `ESCALATIONS.md` → `ESC-017`).** `T01`,
`T02`, `T03`, `T06`, `T07`, `T08` are `ADR-018` points 1/2/6/7/8's own
unedited design — confirmed still correct against `ADR-020` and reused with
only AC-number renumbering (no logic change). `T04` is rewritten in place
around `ADR-020`'s corrected gate (its own pre-correction spec is kept,
unedited, at the bottom of its file, mirroring `REQ-SB-08-US-01-T06`'s own
`ADR-013`→`ADR-019` precedent). `T05` needed no logic change at all — `ADR-020`
point 4 confirms the background-pipeline gate's outcome is unaffected by the
correction, by construction. One new task, `T09`, covers `ADR-020` point 1's
own new scope (`agent_registry.py`'s `mutates` classification + `get_action`
helper), which no `T01`-`T08` task ever touched.

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-21-US-01-T01 | backend | `agent_working_modes.json`/`agent_pending_approvals.json` load/save primitives + `append_agent_history_entry` `pending_approval_id` widen | `data_access/vault_writer.py` | `REQ-SB-21-US-01-T01-working-modes-pending-approvals-vault-writer-primitives.md` |
| REQ-SB-21-US-01-T02 | backend | New `working_mode_registry.py` — self-healing default `"autonomous"`, get/set | `business/working_mode_registry.py` | `REQ-SB-21-US-01-T02-working-mode-registry.md` |
| REQ-SB-21-US-01-T03 | backend | New `pending_approval_registry.py` — CRUD + background-trigger idempotency guard | `business/pending_approval_registry.py` | `REQ-SB-21-US-01-T03-pending-approval-registry.md` |
| REQ-SB-21-US-01-T09 | backend | `agent_registry.py` — new `"mutates": bool` field on every action definition + new `get_action(agent_id, action_id)` helper (`ADR-020` point 1) | `business/agent_registry.py` | `REQ-SB-21-US-01-T09-agent-registry-mutates-classification.md` |
| REQ-SB-21-US-01-T04 | backend | `_invoke_action`/`_execute_action` split — **corrected two-axis gate** (`ADR-020` point 2: Supervised gates on `mutates`, Manual gates on `trigger` incl. new `"hub_routed"`), merged `working_mode` field, `PATCH` `working_mode` | `api/agents_router.py` | `REQ-SB-21-US-01-T04-agents-router-working-mode-gate.md` |
| REQ-SB-21-US-01-T05 | backend | Background-pipeline gate inside `run_capture_and_record_completion`, new `run_capture_for_agent` helper (unchanged design, `ADR-020` point 4) | `business/email_classification.py` | `REQ-SB-21-US-01-T05-background-pipeline-working-mode-gate.md` |
| REQ-SB-21-US-01-T06 | backend | New `pending_approvals_router.py` — list/get/approve/decline | `api/pending_approvals_router.py`, `main.py` | `REQ-SB-21-US-01-T06-pending-approvals-router.md` |
| REQ-SB-21-US-01-T07 | frontend | Working-mode picker kv-row + `.chat-proposal` history-kind rendering with live Approve/Decline | `features/agents-map/AgentDetailPanel.tsx`, `agentsApiClient.ts`, new `pendingApprovalsApiClient.ts` | `REQ-SB-21-US-01-T07-agent-detail-panel-working-mode-and-proposal-card.md` |
| REQ-SB-21-US-01-T08 | frontend | New `MyDayApprovalsPage.tsx` (`/my-day/approvals`) + `MyDayPage.tsx` new card | `pages/MyDayApprovalsPage.tsx`, `App.tsx`, `pages/MyDayPage.tsx` | `REQ-SB-21-US-01-T08-my-day-approvals-page.md` |

`depends_on` graph (acyclic): `T01: []`, `T02: [T01]`, `T03: [T01]`,
`T09: []`, `T04: [T02, T03, T09]`, `T05: [T02, T03]`, `T06: [T03, T04, T05]`,
`T07: [T04, T06]`, `T08: [T06, T07]`.

---

**Superseded, pre-correction table (2026-08-12, `ESC-013`) — kept for
history, not deleted; do NOT build against this table.** Produced by the
decomposer against `ADR-018`'s now-superseded trigger-source gating design
(in particular `T04`/`T05`'s framing of "chat/direct gate" vs.
"background-pipeline gate" as the split, rather than a read-vs-write gate
applied uniformly). Superseded in full by the current table above.

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-21-US-01-T01 | backend | `agent_working_modes.json`/`agent_pending_approvals.json` load/save primitives + `append_agent_history_entry` `pending_approval_id` widen | `data_access/vault_writer.py` | `REQ-SB-21-US-01-T01-working-modes-pending-approvals-vault-writer-primitives.md` |
| REQ-SB-21-US-01-T02 | backend | New `working_mode_registry.py` — self-healing default `"autonomous"`, get/set | `business/working_mode_registry.py` | `REQ-SB-21-US-01-T02-working-mode-registry.md` |
| REQ-SB-21-US-01-T03 | backend | New `pending_approval_registry.py` — CRUD + background-trigger idempotency guard | `business/pending_approval_registry.py` | `REQ-SB-21-US-01-T03-pending-approval-registry.md` |
| REQ-SB-21-US-01-T04 | backend | `_invoke_action`/`_execute_action` split (chat/direct gate), merged `working_mode` field, `PATCH` `working_mode` | `api/agents_router.py` | `REQ-SB-21-US-01-T04-agents-router-working-mode-gate.md` |
| REQ-SB-21-US-01-T05 | backend | Background-pipeline gate inside `run_capture_and_record_completion`, new `run_capture_for_agent` helper | `business/email_classification.py` | `REQ-SB-21-US-01-T05-background-pipeline-working-mode-gate.md` |
| REQ-SB-21-US-01-T06 | backend | New `pending_approvals_router.py` — list/get/approve/decline | `api/pending_approvals_router.py`, `main.py` | `REQ-SB-21-US-01-T06-pending-approvals-router.md` |
| REQ-SB-21-US-01-T07 | frontend | Working-mode picker kv-row + `.chat-proposal` history-kind rendering with live Approve/Decline | `features/agents-map/AgentDetailPanel.tsx`, `agentsApiClient.ts`, new `pendingApprovalsApiClient.ts` | `REQ-SB-21-US-01-T07-agent-detail-panel-working-mode-and-proposal-card.md` |
| REQ-SB-21-US-01-T08 | frontend | New `MyDayApprovalsPage.tsx` (`/my-day/approvals`) + `MyDayPage.tsx` new card | `pages/MyDayApprovalsPage.tsx`, `App.tsx`, `pages/MyDayPage.tsx` | `REQ-SB-21-US-01-T08-my-day-approvals-page.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **A full approval-queue/notification system beyond a lightweight Pending
  Approvals surface** — a minimal list-and-approve/decline surface is in
  scope (operator-resolved); richer features (filtering, batch actions,
  notifications) are not gold-plated here.
- **Automatic expiry, retry, or reminder behaviour for a pending Supervised
  proposal** — not addressed by the PRD's acceptance text; out of scope
  this pass.
- **Any change to Hermes's own concept of agent autonomy/modes** (if any
  exists on Hermes's side) — this is Second Brain's own concept.
- **Fine-grained, per-action mode overrides** (e.g. one action Autonomous,
  another Supervised, on the same agent) — the PRD is explicit that the
  mode is per-agent, not per-action.

## Notes

**Prototype parity (agents-map.html):**

- `agents-map.html`'s side panel Settings block (`kv-list`) — needs a new
  working-mode field/picker row — **not covered by the approved
  prototype.**
- `agents-map.html`'s side panel Chat block — needs a way to render a
  pending, awaiting-approval proposal, distinct from a normal
  message/reply — **not covered by the approved prototype** (the existing
  prototype's chat is a non-functional demo with no proposal/approval
  concept at all).
- `agents-map.html`'s side panel Available Actions block — **N/A**, not
  touched by this story beyond the same Supervised gate a direct
  Available-Actions button press should presumably also go through (not
  explicitly named in the PRD's acceptance text, which speaks only to
  "chat-triggered" vs. "background pipeline" — worth confirming alongside
  the other flagged questions, but not itself blocking, since the direct
  Available-Actions path already funnels through the same
  `_invoke_action` mechanism the chat path uses per `ADR-011`).
- No screen anywhere in `html-prototype/` (including `my-day.html` and its
  drilldowns) has any pending-approval affordance for a background
  pipeline's proposed action — **not covered by the approved prototype.**
  This needs its own `/design` pass once the mechanism question below is
  resolved.

**Resolved 2026-08-11, operator-confirmed (`ESC-005` closed on both
points):**

1. Default working mode → Autonomous, behavior-preserving.
2. Supervised background-pipeline approval → gets a real Pending Approvals
   surface, built now, not deferred to REQ-SB-11.

**Still open — `/design` needed** for the mode picker, the chat's
pending-approval rendering, and the new Pending Approvals surface — none
have prototype coverage.

**Scoping decision (why this stays ONE story):** applying this project's
standing "no independent value alone" test — a mode picker with no
enforcement behind it has no value, and Autonomous/Supervised/Manual
enforcement with no way to set the mode has no value either. Kept as one
story, matching the PRD's own single-requirement framing.

gate: flagged 2026-08-11 — both originally-open product decisions (default
mode value; Supervised background-pipeline approval UI timing) are now
operator-resolved (see above); the remaining trigger is net-new-design
(`/design` pending for three screen regions). See `REVIEW-QUEUE.md`.

**Design — approved 2026-08-12 (operator, live-verified in browser).**
The Working-mode picker row (Agent Settings, all 5 agents), Meeting
Capture's Chat `.chat-proposal` card with its Pending/Approved/Declined
state-switcher, and the Pending Approvals surface (My Day's 5th card +
`html-prototype/my-day-approvals.html`, both example proposals plus an
empty "queue caught up" state) are all built and confirmed live in
`html-prototype/agents-map.html`/`my-day.html`/`my-day-approvals.html` —
see `REVIEW-QUEUE.md`'s "Prototype update: agents-map.html, my-day.html,
my-day-approvals.html" entry. This clears the net-new-design trigger; the
story's `gate` was reset to `clear` and it was handed to `/plan-tasks`.

**Architecture pass (2026-08-12, `/plan-tasks` step 1 — architect):**
`ADR-018` written (new, appended to `Implementation/Architecture/ADR.md`
— numbered `018`, not `017`, since `REQ-SB-20-US-01`'s own concurrent
architect pass claimed `ADR-017` for its Hub-routing mechanism first; no
collision, no content lost) — resolves this story's own explicitly-
deferred mechanism questions. Read as direct current-source precedent:
`app/business/agent_registry.py`, `app/api/agents_router.py`
(`_invoke_action`/`chat`), `app/business/section_registry.py`/
`provider_registry.py` (`ADR-014`), `app/scheduling/capture_scheduler.py`
and `app/business/email_classification.py::run_capture_and_record_
completion` (`ADR-005`/`ADR-008` point 4). Concretely: two new sibling
`.second-brain/` state files (`agent_working_modes.json`,
`agent_pending_approvals.json`), two new business modules
(`working_mode_registry.py` — the per-agent mode property, self-healing
default `"autonomous"`; `pending_approval_registry.py` — the Pending
Approvals workflow record, its own concern, kept separate from working
mode itself). `agents_router.py::_invoke_action` is split into a gate
(checks working mode) and `_execute_action` (today's unconditional
dispatch, renamed) — Supervised short-circuits into a pending-approval
record for **both** the chat-triggered and the direct Available-Actions-
button path (the story's own flagged "should the button go through the
same gate" question: yes, same shared `ADR-011` funnel, same gate).
**Manual vs. Supervised resolved:** for a chat/direct trigger, Manual
executes immediately, identical to Autonomous — a trigger-phrase match or
button click *is* "the user explicitly asking," the only such mechanism
this codebase has (no NLU exists, `ADR-007`/`ADR-011`); the two modes
differ only on the **background/scheduled** trigger, where Manual skips
silently (no record) and Supervised proposes-and-waits. The background
gate lives as two explicit per-agent checks directly inside
`email_classification.py::run_capture_and_record_completion` — zero
changes to `capture_scheduler.py` itself (extends, does not reopen,
`ADR-005`/`ADR-008` point 4). New `app/api/pending_approvals_router.py`
(`GET`/`POST /pending-approvals...`) — Approve executes the deferred
action directly (bypassing the gate, since re-entering it would defer
forever); Decline discards, no action taken. Full reasoning, every
alternative considered, and every consequence: `ADR-018` in
`Implementation/Architecture/ADR.md`. Also updated:
`Implementation/Architecture/architecture.md` → new "Agent Working Modes
& Pending Approvals" subsection (under "My Day & Agent Panel APIs"),
`Last reviewed` footer.

**Architecture scope (bounds the decomposer's task breakdown and the
coder's file access for this story):**
- Backend: `src/backend/app/data_access/vault_writer.py` (new
  `load_working_modes_state`/`save_working_modes_state` and
  `load_pending_approvals_state`/`save_pending_approvals_state`
  primitives only); `src/backend/app/business/working_mode_registry.py`
  (new); `src/backend/app/business/pending_approval_registry.py` (new);
  `src/backend/app/api/pending_approvals_router.py` (new);
  `src/backend/app/api/agents_router.py` (the `_invoke_action`/
  `_execute_action` split and gate, the `trigger` parameter on
  `trigger_action`/`chat`, the merged `working_mode` field on `GET
  /agents`/`GET /agents/{agent_id}`, the `working_mode` portion of `PATCH
  /agents/{agent_id}`, the new `"proposal"` history-entry kind);
  `src/backend/app/business/email_classification.py` (the per-agent
  background gate inside `run_capture_and_record_completion`, the new
  `run_capture_for_agent` helper — **not** `classify_recent_emails` or any
  other existing function/line); `src/backend/app/main.py` (register
  `pending_approvals_router`). `app/scheduling/capture_scheduler.py`,
  `app/business/agent_registry.py`, `app/business/agent_chat.py`,
  `app/business/meeting_classification.py`, `app/business/my_day.py`,
  `app/api/my_day_router.py` are explicitly **out of scope** — none are
  modified by this story.
- Frontend: `src/frontend/src/features/agents-map/AgentDetailPanel.tsx`
  (new Working-mode `<select>` kv-row; `.chat-proposal` card rendering
  for `"proposal"`-kind history entries with Approve/Decline);
  `src/frontend/src/features/agents-map/agentsApiClient.ts` (the
  `working_mode` portion of `updateAgentAssignment`); new
  `src/frontend/src/features/agents-map/pendingApprovalsApiClient.ts`;
  new `src/frontend/src/pages/MyDayApprovalsPage.tsx` (route
  `/my-day/approvals`); `src/frontend/src/App.tsx` (new route);
  `src/frontend/src/pages/MyDayPage.tsx` (new 5th `SECTIONS` entry/card).
- Architecture doc sections the coder is bounded by: `architecture.md` →
  "My Day & Agent Panel APIs" → "Agent Working Modes & Pending Approvals"
  (full mechanism) and "Agent Sections & LLM Providers" (the precedent
  pattern it extends), plus `ADR-018` in full.

Per the architect's own MUST-FLAG trigger 3 (creating/changing an ADR)
**and** trigger 1 (a material assumption — the Manual-vs-Supervised
chat-trigger distinction, `ADR-018` point 5, resolving the story's own
Scenario 5 ambiguity): `gate: flagged`,
`gate_reason: trigger-3 (ADR-018 created)`. The decomposer still runs in
this same `/plan-tasks` pass, per `Implementation/Pipeline.md`'s "do NOT
halt the stage" rule — the human reviews `ADR-018` and the resulting
tasks together in one pass. A `REVIEW-QUEUE.md` pointer has been added.

**Decomposition pass (2026-08-12, `/plan-tasks` step 2 — decomposer).**
All 7 untagged Gherkin scenarios tightened for buildability (wording
only — no scenario weakened, omitted, or deleted) and locked as
`REQ-SB-21-US-01-AC-01` through `AC-07`, each carrying its trailing
`<!-- AC-ID: ... -->` tag. 8 tasks created at the flat `Implementation/
Tasks/` root (`T01`–`T08`, table above), covering every architecture-
scope file: the two new state files' `vault_writer.py` primitives
(`T01`), the two new registry modules (`T02`/`T03`), the
`_invoke_action`/`_execute_action` chat/direct gate split (`T04`), the
background-pipeline gate inside `email_classification.py` (`T05`), the
new `pending_approvals_router.py` (`T06`), and both frontend surfaces —
the Agent Settings picker + `.chat-proposal` card (`T07`) and the
standalone `/my-day/approvals` page (`T08`). `depends_on` wires
registries before the gates that read them, both gates before the router
that resolves against them, and frontend after its own backend
counterpart — acyclic (`T01`→`T02`/`T03`→`T04`/`T05`→`T06`→`T07`→`T08`).
Every locked AC has at least one AC-tagged manual verification step (`T04`/
`T05` carry `AC-02`/`AC-03`(partial)/`AC-05`/`AC-06` at the backend layer;
`T06` carries `AC-04`; `T07` carries `AC-01`/`AC-03`(full round trip)/
`AC-07` at the live UI layer; `T08` carries `AC-05`'s frontend half) — no
locked AC without a tagged step, hard rule 4 satisfied. No new material
assumption introduced by this decomposition pass beyond the one the
architect already flagged (`ADR-018` point 5) — every implementation
choice made while writing the 8 tasks (e.g. rendering the `.chat-proposal`
card inside the panel's persisted Communication History section rather
than the ephemeral Chat thread; preserving meeting-capture's own
no-history-entry Autonomous behaviour unchanged) is a bounded,
architecture-internal judgement call, not a product-level gap-fill, and
is recorded in each task's own Context/Notes rather than raising a new
flag. `status: Draft → Ready`; all 8 new tasks written directly at
`status: Ready` (lockstep with the story). **`gate` intentionally left
`flagged`, `gate_reason` unchanged** — this decomposer did not itself
trigger a new flag and does not clear a flag it did not set; the human
still reviews `ADR-018` and this task breakdown together per the note
above.

**Re-spec pass (2026-08-12, analyst — resolves `ESCALATIONS.md` →
`ESC-013`).** Before either `T01`-`T08` above were ever built (the human
review of `ADR-018` above was still open), the operator reviewed `ADR-018`
directly and corrected it — the story is reset `Ready → Draft` and
re-specced here, per hard rule 1 (specs are append-only for `Done`
stories only; this story never shipped, so an in-place re-spec is not a
violation, same precedent as `ESC-009`'s `REQ-SB-23-US-01` re-spec).
**What changed, concretely:**
- **Scenario 3** (was "chat-triggered action proposes and waits") is
  rewritten as "a write/mutating action proposes and waits, regardless of
  trigger source" — merging in what was Scenario 4's background-trigger
  case, since both now share one gate (the action's own nature), not two
  separate trigger-keyed scenarios.
- **Scenario 3b** (declined proposal) reworded to speak of a write/
  mutating action's proposal generically, not a "chat- or direct-
  triggered" one specifically — substance unchanged (declining still
  means the action is never taken).
- **Scenario 4** (was "background-pipeline action also waits") is
  **replaced** with a new scenario: "a Supervised agent's read-only action
  proceeds immediately, regardless of trigger source" — the corrected
  semantics' other half, with no direct predecessor in the prior scenario
  set (the prior set never described a read-only action's behaviour under
  Supervised at all).
- **Scenario 5** (Manual, background trigger) reworded only to note "read-
  only or write/mutating" is now irrelevant to a direct human ask —
  substance (no background action; immediate action on direct ask)
  unchanged.
- **Scenario 5b** is new: "a Manual agent is not triggered by another
  agent's Hub-routed request" — directly encodes the operator's own "No
  Agent can Trigger an Action" correction, a trigger source `ADR-018`
  never considered.
- All 7 prior `<!-- AC-ID: ... -->` tags removed — this story is `Draft`
  again; the decomposer re-locks fresh AC-IDs at the next `/plan-tasks`
  pass, per the analyst's own "do NOT add AC-IDs" rule.
- Context/Constraints updated in place to record the correction plainly
  (see the new 2026-08-12 Context bullet and the two corrected Constraints
  bullets above) rather than silently patched.
- The existing `T01`-`T08` Implementation Tasks table/task files are left
  in place (not deleted) but flagged stale — see the note directly above
  that table.
**What did NOT change:** Scenarios 1, 2, and 6 (mode visibility/
changeability, Autonomous behaviour, exactly-one-mode-always) are
unaffected by this correction and are carried forward as-is (untagged).
The Pending Approvals surface, its prototype (approved 2026-08-12), and
the default-Autonomous/Pending-Approvals-in-scope-now resolutions from
`ESC-005` are all unaffected — this correction is scoped to the
Manual/Supervised gating semantics only.
**Not this analyst's job, left for the next `/plan-tasks` pass:** designing
the actual read-only-vs-mutating classification mechanism on
`agent_registry.py`'s action definitions (a new architectural concept —
whether it's a new field per action, a derived rule, or something else),
and writing the superseding ADR over `ADR-018` that will carry that
design. `ADR-018` itself stays `Accepted`, unedited.
**Gate: `gate: clear`, 2026-08-12.** No MUST-FLAG trigger fires for this
analyst pass itself: no material assumption was made (the operator gave
the corrected semantics directly, verbatim, quoted above); REQ-SB-21 is
not `<!-- Draft -->`/unfinalised in the PRD; no ADR was created or edited
by this pass (that is next `/plan-tasks` pass's job); no
`ESCALATIONS.md` entry was newly opened by this pass (it resolves an
already-open one, `ESC-013`); the story is not oversized; no contradictory
inputs exist; and there is exactly one correct interpretation of the
operator's own directly-quoted words, not multiple equally-valid ones.
`status:` stays `Draft` — advancing to `Ready` is the decomposer's call at
the next `/plan-tasks` pass, not this analyst's.

**Architecture pass (2026-08-12, `/plan-tasks` step 1 — architect,
resolves `ESCALATIONS.md` → `ESC-013`).** New ADR, `ADR-020`
(`Implementation/Architecture/ADR.md`), supersedes `ADR-018` Decision
points 3 (the chat/direct-action gate) and 5 (the Manual-vs-Supervised
reasoning) **only** — every other part of `ADR-018` (the two new
`.second-brain/` state files and their registry modules, the
`uuid`-based pending-approval id, the Approve/Decline endpoints calling
`_execute_action`/`run_capture_for_agent` directly, the `"proposal"`
history-entry kind, the background-pipeline gate inside
`email_classification.py::run_capture_and_record_completion` untouching
`capture_scheduler.py`) is confirmed correct and reused unmodified.
`ADR-018` itself is not edited (stays `Accepted`, per hard rule 1) — its
`Status:` line is updated to `Superseded by ADR-020 (points 3 and 5
only)` with an append-only note, mirroring `ADR-013`'s own "points 1 and
2 only" precedent.

**Concretely, what `ADR-020` designs:**
- **New `"mutates": bool` field on every action definition in
  `app/business/agent_registry.py`'s static `AGENTS` catalog** (still
  fully hardcoded, `ADR-011` point 2 unaffected), plus a new
  `agent_registry.get_action(agent_id, action_id) -> dict | None` lookup
  helper. Read the real current action definitions (not guessed from
  names alone) to classify: `run_capture_now` (email-capture,
  meeting-capture, todo-capture) and `rebuild_person_note`
  (people-producer) → `True` (write to the vault); `pause_schedule`
  (email-capture, meeting-capture, todo-capture) → `True` (a
  control-plane state mutation, even though it has no real handler yet —
  classified conservatively as a write, not read-only); `view_last_run`
  (all four worker/producer agents), `ask_question` and
  `view_channel_status` (vault-qa, whose own declared settings say
  "Write access: Read-only here") → `False`. An action id the gate cannot
  resolve defaults **fail-safe to `True`** — never silently treated as
  safe to auto-run.
- **`agents_router.py::_invoke_action`'s gate now checks BOTH axes**,
  replacing `ADR-018` point 3's single trigger-source switch: (1)
  **Supervised** gates on the resolved action's own `mutates` flag — a
  mutating action always proposes-and-waits, a read-only action proceeds
  immediately, **regardless of `trigger`** (chat, direct, or hub_routed);
  (2) **Manual** gates on trigger source only — `"chat"`/`"direct"`
  (a direct human ask) always executes immediately regardless of the
  action's nature (unchanged from `ADR-018` point 5's conclusion), but a
  new `"hub_routed"` trigger value (alongside the existing
  `"chat"`/`"direct"`/`"background"`, added to both `_invoke_action`'s
  parameter and `agent_pending_approvals.json`'s `trigger` enum) always
  refuses — satisfying Scenario 5b's "no agent can trigger an action on a
  Manual-mode agent." Recorded explicitly as **currently a no-op gate,
  not dead code**: `ADR-017`'s already-built Hub-routing node never
  itself invokes a target agent's action today (confirmed by the
  operator's own `ESC-013` mid-pass correction — "It can be Offered but
  it doesn't execute"), so no call site produces `trigger="hub_routed"`
  yet; this is forward-looking correctness for the day a future story
  adds real cross-agent action invocation.
- **`ADR-018` point 4 (the background-pipeline gate) needs no structural
  change** — both real background-triggered steps (email-capture's,
  meeting-capture's) are always `"mutates": True` actions today, so the
  corrected mutates-based Supervised rule and the original trigger-based
  rule produce the identical outcome for the background trigger by
  construction. The behavioural change this ADR introduces is real but
  confined entirely to the chat/direct funnel: a Supervised agent's
  read-only action (`view_last_run`, `ask_question`,
  `view_channel_status`) now executes immediately instead of always
  proposing, which `ADR-018`'s uniform trigger-source gate got wrong.

`Implementation/Architecture/architecture.md` → "Agent Working Modes &
Pending Approvals" is updated in place (a living doc, not append-only) to
describe this corrected mechanism directly — the new `mutates` field and
`get_action` helper, the corrected two-axis `_invoke_action` gate, the
corrected Manual-vs-Supervised bullet, the unchanged background gate, and
the extended `trigger` enum — plus its `Last reviewed` footer.

**Architecture scope (bounds the decomposer's task breakdown and the
coder's file access for this story — supersedes the prior architecture-
pass's scope list only where it names `_invoke_action`'s gate design or
the Manual-vs-Supervised reasoning; every other file/module named there
is unchanged and still in scope):**
- Backend: `src/backend/app/business/agent_registry.py` (new
  `"mutates": bool` field on every action dict; new `get_action(agent_id,
  action_id)` helper — **no other change** to this file: it stays fully
  static/hardcoded, no new mutable state); `src/backend/app/data_access/
  vault_writer.py` (the `load_working_modes_state`/`save_working_modes_
  state` and `load_pending_approvals_state`/`save_pending_approvals_
  state` primitives only, per `ADR-018`, unchanged by `ADR-020`);
  `src/backend/app/business/working_mode_registry.py` (new, per
  `ADR-018`); `src/backend/app/business/pending_approval_registry.py`
  (new, per `ADR-018`; its `agent_pending_approvals.json` schema's
  `trigger` field gains the `"hub_routed"` enum value per `ADR-020`);
  `src/backend/app/api/pending_approvals_router.py` (new, per `ADR-018`);
  `src/backend/app/api/agents_router.py` (the `_invoke_action`/
  `_execute_action` split and **corrected two-axis gate** per `ADR-020`
  — supersedes the prior pass's "chat/direct gate" framing; the `trigger`
  parameter on `trigger_action`/`chat` is now `"chat" | "direct" |
  "hub_routed"`, not `"direct" | "chat"`; the merged `working_mode` field
  on `GET /agents`/`GET /agents/{agent_id}`, the `working_mode` portion of
  `PATCH /agents/{agent_id}`, the new `"proposal"` history-entry kind —
  all unchanged, per `ADR-018`); `src/backend/app/business/
  email_classification.py` (the per-agent background gate inside
  `run_capture_and_record_completion`, the new `run_capture_for_agent`
  helper, per `ADR-018` point 4 — **structurally unchanged** by `ADR-020`,
  see above — **not** `classify_recent_emails` or any other existing
  function/line); `src/backend/app/main.py` (register
  `pending_approvals_router`). `app/scheduling/capture_scheduler.py`,
  `app/business/agent_chat.py`, `app/business/meeting_classification.py`,
  `app/business/my_day.py`, `app/api/my_day_router.py` remain explicitly
  **out of scope** — none are modified by this story.
- Frontend: unchanged from the prior architecture pass —
  `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` (Working-
  mode `<select>` kv-row; `.chat-proposal` card rendering for
  `"proposal"`-kind history entries with Approve/Decline);
  `src/frontend/src/features/agents-map/agentsApiClient.ts` (the
  `working_mode` portion of `updateAgentAssignment`); new
  `src/frontend/src/features/agents-map/pendingApprovalsApiClient.ts`;
  new `src/frontend/src/pages/MyDayApprovalsPage.tsx` (route
  `/my-day/approvals`); `src/frontend/src/App.tsx` (new route);
  `src/frontend/src/pages/MyDayPage.tsx` (new 5th `SECTIONS` entry/card).
  None of `ADR-020`'s corrections touch the frontend surface directly —
  the `.chat-proposal` card renders whatever `"proposal"`-kind history
  entry either gate produces, unchanged shape.
- Architecture doc sections the coder is bounded by: `architecture.md` →
  "My Day & Agent Panel APIs" → "Agent Working Modes & Pending Approvals"
  (full corrected mechanism) and "Agent Sections & LLM Providers" (the
  precedent pattern it extends), plus `ADR-018` **and** `ADR-020` in
  full — `ADR-018`'s points 1/2/4/6/7/8 and `ADR-020`'s corrected points 3
  analog/5 analog together form the complete, current design; neither
  ADR alone is sufficient.

Per the architect's own MUST-FLAG trigger 3 (creating/changing an ADR —
`ADR-020` created, `ADR-018`'s `Status:` line updated to record partial
supersession): `gate: flagged`, `gate_reason: trigger-3 (ADR-020 created;
ADR-018 points 3/5 superseded)`. The decomposer still runs in this same
`/plan-tasks` pass, per `Implementation/Pipeline.md`'s "do NOT halt the
stage" rule — the human reviews `ADR-020` and the resulting re-derived
tasks together in one pass. A `REVIEW-QUEUE.md` pointer has been added.
`ESCALATIONS.md` → `ESC-013` is now fully resolved by this pass (both its
"re-spec both stories" and "superseding ADR" resolution steps are
complete).

**Architecture + decomposition pass (2026-08-12, `/plan-tasks` — resolves
`ESCALATIONS.md` → `ESC-017`).** Triggered by `ESC-017`: two concurrent
stories' own `## Dependencies` sections (`REQ-SB-35-US-01`, `REQ-SB-36-US-02`)
wrongly asserted this story's `ADR-020` mechanism was "Done." Direct
inspection this pass confirmed `ESC-017`'s own finding is accurate: this
story was still `status: Draft`, `gate: flagged`, its decomposer had not
re-run since `ADR-020` corrected `ADR-018`, and — checked directly against
`src/backend/app/` — **zero** of its code exists (no
`pending_approval_registry.py`, no `working_mode_registry.py`, no
`pending_approvals_router.py`; `agents_router.py` has no working-mode gate,
no `trigger` parameter, no `mutates` handling of any kind).

**Architect step — no new ADR.** `ADR-018` (points 1, 2, 4, 6, 7, 8) and
`ADR-020` (the corrected points 3/5 analog, including the concrete
`"mutates": bool` classification table, the `get_action` helper design, the
two-axis `_invoke_action` gate, and the extended `"hub_routed"` trigger
enum) already fully specify the concrete registry/router/gate shape this
pass needed to decompose into tasks — this pass is pure implementation-task
derivation against an already-`Accepted` design, not a new architectural
decision. No ADR created or edited. `architecture.md`'s "Agent Working
Modes & Pending Approvals" section was checked directly and already
describes `ADR-020`'s corrected mechanism in full (the `mutates` field, the
`get_action` helper, the corrected two-axis gate, the unchanged background
gate, the extended trigger enum) — no update needed; `Last reviewed` footer
left untouched.

**Decomposer step.** All 8 untagged Gherkin scenarios (now 8, not 7 —
Scenario 4 and Scenario 5b are net-new from the 2026-08-12 re-spec) tightened
for buildability (wording only) and locked as `REQ-SB-21-US-01-AC-01` through
`AC-08`, each carrying its trailing `<!-- AC-ID: ... -->` tag:
`AC-01`=Scenario 1, `AC-02`=Scenario 2, `AC-03`=Scenario 3 (now the merged
"any trigger, including background" mutating-action-proposes scenario —
supersedes the old `AC-03`+`AC-05` split), `AC-04`=Scenario 3b, `AC-05`=
Scenario 4 (**new** — Supervised read-only proceeds immediately), `AC-06`=
Scenario 5, `AC-07`=Scenario 5b (**new** — Manual excludes Hub-routed),
`AC-08`=Scenario 6 (was `AC-07` in the stale table).

Re-derived the task breakdown against `ADR-020`, per this story's own
already-recorded note:
- **`T01`/`T02`/`T03`** (the two new `.second-brain/` state files' `vault_writer.py`
  primitives, `working_mode_registry.py`, `pending_approval_registry.py`) —
  unaffected by `ADR-020` (it supersedes only `ADR-018` points 3/5, not 1/2)
  — re-confirmed correct as originally written, reused **unchanged**.
- **New `T09`** (`agent_registry.py`'s `"mutates": bool` field + `get_action`
  helper, `ADR-020` point 1) — genuinely new scope no `T01`-`T08` task ever
  covered; `depends_on: []` (a static-catalog addition, same independence as
  `T01`-`T03`).
- **`T04` rewritten in place** around `ADR-020`'s corrected two-axis gate
  (`_invoke_action`'s Manual+`hub_routed`-refuses / Supervised+`mutates`-gates
  logic), now depending on `T09` in addition to `T02`/`T03`. **A real,
  material finding surfaced while rewriting this task, not a guess:**
  `src/backend/app/api/agents_router.py`'s real, current file has
  structurally drifted from the original `T04`'s own stale code sample —
  `chat` is now `async def` and calls `await agent_orchestration.
  run_agent_conversation(...)` with real memory-loading/fact-extraction
  (`REQ-SB-25-US-01`/`REQ-SB-26-US-01`, both shipped in `SPRINT-014`/`015`,
  after the original `T01`-`T08` decomposition), none of which the original
  `T04` sample knew about. The rewritten `T04` composes the corrected gate
  around the REAL current file (preserving the async chat/memory logic
  byte-for-byte) rather than overwriting it with the stale sample — the
  exact antipattern `MEMORY.md`'s own `REQ-SB-26-US-01-T03` Pattern entry
  already names. The prior `ADR-018`-only spec is kept, unedited, at the
  bottom of `T04`'s own file as an honest record, mirroring
  `REQ-SB-08-US-01-T06`'s own `ADR-013`→`ADR-019` precedent.
- **`T05` needed no rewrite at all** — `ADR-020` point 4 confirms the
  background-pipeline gate's observable outcome is unaffected by the
  correction (both real background-triggered steps are unconditionally
  mutating today). Only its AC-tag references were renumbered
  (`AC-05`(old)→`AC-03`(new, background half of the merged scenario)).
- **`T06`/`T07`/`T08`** — unchanged in design (the Approve/Decline router,
  the Agent Settings picker + `.chat-proposal` card, the standalone Pending
  Approvals page are all `ADR-018`-governed concerns `ADR-020` does not
  touch); only AC-tag references renumbered where the underlying scenario
  shifted number (`T07`'s old `AC-07`→new `AC-08`; `T08`'s old `AC-05`→new
  `AC-03`).

`depends_on` graph across all 9 tasks (acyclic): `T01: []`, `T02: [T01]`,
`T03: [T01]`, `T09: []`, `T04: [T02, T03, T09]`, `T05: [T02, T03]`,
`T06: [T03, T04, T05]`, `T07: [T04, T06]`, `T08: [T06, T07]`. Every locked
AC has at least one AC-tagged manual verification step — `AC-02`/`AC-03`
(partial)/`AC-05`/`AC-06`(partial)/`AC-07` live at the backend layer across
`T04`/`T05`; `AC-04` in `T06`; `AC-01`/`AC-03`(full round trip)/`AC-08` at
the live UI layer in `T07`; `AC-03`(background/frontend half) in `T08` — no
locked AC without a tagged step, hard rule 4 satisfied. `status: Draft →
Ready`; all 9 tasks written directly at `status: Ready` (lockstep with the
story). **`gate` intentionally left `flagged`, `gate_reason` updated to
note the decomposer has now run** — this decomposer does not itself trigger
a new flag and does not clear a flag it did not set (the architect's own
`ADR-020`-creation flag); the human still needs to review `ADR-020` and
this now-complete task breakdown together before `/implement-sprint` builds
it. `REVIEW-QUEUE.md`'s existing `ADR-020` review entry and its `ESC-017`
entry are both updated to point at this now-complete decomposition.

**For `REQ-SB-35-US-01`'s Tier-2 approval path and `REQ-SB-36-US-02`'s
Autonomous-mode check (both blocked on this story per `ESC-017`) — the real
task IDs to wire `depends_on` onto, once those two stories' own next
decomposer pass runs:**
- `REQ-SB-36-US-02`'s Autonomous-mode check needs
  `working_mode_registry.get_agent_working_mode(...)` → depend on
  **`REQ-SB-21-US-01-T02`**.
- `REQ-SB-35-US-01`'s Tier 2 (and `REQ-SB-36-US-02`'s own Tier-2 resolution,
  per `ADR-023`) needs the full Pending-Approvals workflow store (create/
  list/resolve) and its HTTP surface → depend on **`REQ-SB-21-US-01-T03`**
  (`pending_approval_registry.py`) **and `REQ-SB-21-US-01-T06`**
  (`pending_approvals_router.py`, since `ADR-021`'s own Tier-2 design adds a
  `payload` field and a new `_APPROVAL_HANDLERS` dispatch table onto this
  router's existing Approve endpoint).
- If either story's own gate logic needs the corrected two-axis
  chat/direct-action gate itself (not just the underlying stores) → depend
  on **`REQ-SB-21-US-01-T04`** (the gate) and, transitively, **`T09`** (the
  `mutates` classification `T04` reads).
These are still `Draft`/`gate: flagged` at this pass's own edit — this
story's tasks are `Ready` but not yet built; `/implement-sprint` has not run
against them. `ESC-017` stays `Open` until `REQ-SB-21-US-01` itself reaches
`Done` and the follow-up decomposer pass on `REQ-SB-35-US-01`/
`REQ-SB-36-US-02` actually replaces their placeholder `depends_on: []` with
these real IDs.

**Coder pass (2026-08-12, `/implement-sprint SPRINT-021`) — built and
verified live end to end.** All 9 tasks (`T01`-`T09`) built in
dependency order (`T01`→`T09` independently, `T02`/`T03` next, then
`T04`/`T05`, `T06`, `T07`, `T08`) and marked `Done`, each with its own
Implementation Log detailing what was built and every live verification
step performed. All 8 locked ACs verified live against the real running
backend (`uvicorn`, a second instance on port 8002 — see below), real
frontend (`npm run dev` via Vite, headless-Chrome-via-CDP per this
project's established Learnings pattern), the real vault, and real
Outlook/Compass integration (several genuine capture runs triggered
throughout verification, each deliberate and logged):

- **AC-01** (mode visible/changeable, persisted) — confirmed via the
  real Agent Settings picker, including a full page reload.
- **AC-02** (Autonomous always executes) — confirmed for chat, direct,
  and background triggers, byte-identical to pre-story behaviour.
- **AC-03** (Supervised mutating action proposes+waits, any trigger) —
  confirmed for chat/direct (`T04`), background (`T05`), and the full
  live UI round trip including a real Approve click (`T07`/`T08`).
- **AC-04** (declined proposal never executes) — confirmed via the real
  `POST /pending-approvals/{id}/decline` endpoint and the live UI.
- **AC-05** (Supervised read-only proceeds immediately) — confirmed:
  `view_last_run` executed immediately while Supervised, no pending
  record created.
- **AC-06** (Manual == Autonomous for a direct human ask, background
  skips silently) — confirmed for both mutating and read-only actions
  on a direct/chat trigger, and for the background trigger.
- **AC-07** (Manual refuses `hub_routed`) — confirmed via a direct
  Python-shell call to `_invoke_action(..., trigger="hub_routed")` (no
  real HTTP call site produces this trigger yet, per `ADR-020`'s own
  Context) — refused outright while Manual, executed immediately once
  reset to Autonomous.
- **AC-08** (always exactly one mode assigned) — confirmed on
  `vault-qa`, an agent never explicitly reassigned this session.

**Two real, in-scope findings surfaced during live verification, not
silently patched:**
1. `T04`'s own file-drift note (async chat/memory logic,
   `REQ-SB-25`/`REQ-SB-26`) proved only half the real story — the real
   `agents_router.py` had *also* grown `SPRINT-020`'s own `keywords`
   support (import, field, response key), landed after this story's
   tasks were authored and not named in any task's own "Before" state.
   Composed around the REAL current file throughout, preserving both
   the async chat/memory logic and the keywords support byte-for-byte —
   the same "never overwrite with a stale sample" pattern this session
   already applied twice elsewhere (`MEMORY.md`'s own `REQ-SB-26-US-01-T03`
   Pattern entry, and `SPRINT-020`'s own `graph.py`/`agents_router.py`
   drift). `T06`'s `main.py` sample and `T08`'s `MyDayPage.tsx`/
   `AgentDetailPanel.tsx` samples were each similarly stale relative to
   sibling stories' own intervening work (`skills_router`/
   `system_health_router`/`mcp_server` registrations;
   `REQ-SB-22-US-01`'s rolling-7-day-window navigator) — composed
   around the real files in every case, never overwritten.
2. `T07`'s own live console-error check surfaced a real defect: a
   `"proposal"`-kind history entry with an unresolvable
   `pending_approval_id` (leftover debris from `T01`'s own explicitly
   "no cleanup needed" throwaway smoke-check entry) produced an
   unhandled promise rejection once `T07`'s new rendering logic
   started resolving every such entry's live status. Fixed with a
   `.catch(() => {})` on that fetch chain, and the one stale entry was
   pruned from the real vault state. See `T01`/`T07`'s own
   Implementation Logs.

**Environment finding, not a code defect (recorded for the record):**
this session's usual backend dev port (8001) was found already bound
by a `--reload` process that predated this session; `Get-Process`/
`taskkill` both reported that PID as not existing, yet the OS
continued to report it as the listening socket's owner — an apparent
stale-listener condition on this specific host, not the documented
"surviving reloader child" antipattern (`MEMORY.md`). A second,
independent `uvicorn` instance on port 8002 was used for all live
verification instead of force-fighting an unkillable handle; both
instances converged on the same edited code (the 8001 instance's own
`--reload` picked up the same file changes independently), so no
incorrect-code risk existed, only a brief window of two concurrent
scheduler ticks against the same vault. Both dev processes (8002
`uvicorn`, Vite, the headless-Chrome debug instance) were stopped
cleanly at the end of this session; the pre-existing 8001 process was
left untouched (not owned by this session, could not be killed).

**Final vault/agent state confirmed clean at hand-off:** both
`email-capture` and `meeting-capture` reset to `"autonomous"` (the
default); zero pending approvals remain (`GET /pending-approvals` →
`[]`); every real Outlook/Compass side effect triggered during
verification is a genuine, already-filed vault note (deliberate, not
a defect).

`status: Ready → Done`. `gate` stays `flagged` — two scope-internal
judgement calls (above and in `T07`'s own Implementation Log) are
logged for human spot-check, not escalations. `REVIEW-QUEUE.md` and
`ESCALATIONS.md` → `ESC-013` updated accordingly. `SPRINT-021` itself
is set `Done` alongside this story (its own retrospective drafted
separately).
