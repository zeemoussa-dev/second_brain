---
id: REQ-SB-39-US-01
title: Unify agent capabilities under Skills — the capability model, plus migrating every existing read-only Action to a Skill
requirement_ids: [REQ-SB-39]
requirement_section: "REQ-SB-39: Unify Agent Capabilities Under Skills"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-028 created), carried through to Done — /plan-tasks step 1 (architect): the two mechanism-level open questions (mutates shape for Skills; invoke_skill's trigger concept) were resolved directly by the operator, relayed to the architect, not re-derived; the operator separately decided to skip the /design pass for this batch (REQ-SB-28/29/37/38/39/40/41) and build directly, clearing the net-new-design-needed blocker. Both original unclear-requirement/net-new-design-needed reasons are resolved; ADR-028 review remains open (trigger 3). Additionally, the coder pass (2026-08-13) flagged 3 scope-internal task-level items for human spot-check (T05's recursion-guard fix, T07's result-shape bug fix + honest reply-wording-changed finding on the operator's own highest-risk regression check, T09's Node.js-absent environment gap) — see REVIEW-QUEUE.md for all 4 pointers together. All 7 locked ACs verified live; nothing blocked."
sprint: SPRINT-030
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-39-US-01 — Unify agent capabilities under Skills — the capability model, plus migrating every existing read-only Action to a Skill

## Story

**As a** Second Brain user
**I want** every read-only agent capability that exists today as a hardcoded
Action (`view_last_run`, `ask_question`, `view_channel_status`) to become a
Skill, granted and revoked through the exact same mechanism `REQ-SB-27`
already built for `web-research` and `diagram-understanding`
**So that** there is one consistent way to see and configure what any
agent — existing or newly created — can do, instead of two separate,
differently-shaped capability systems (a hardcoded `agent_registry.py`
`actions` list and a persisted Skills grant)

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-39: Unify Agent Capabilities Under
  Skills*. **Acceptance:** "Every capability any agent has — including every
  capability that exists today as a hardcoded Action — is represented and
  invoked as a Skill; granting or revoking an agent's capabilities uses one
  consistent mechanism regardless of agent type or when the agent was
  created; a mutating Skill's invocation still honors the agent's own
  working mode (Autonomous/Supervised/Manual) the same way a mutating Action
  does today."

- **PRD breadcrumb (2026-08-13, operator-directed), cited in full, not
  re-decided here:** raised in direct response to `REQ-SB-37`'s own "can a
  user-created agent define custom actions?" open question — "We have no
  Custom Action, we need to Convert those Custom Actions to Skills. Example,
  Read Mail is a Skill under Outlook COM Tool we need to have that in our
  tool set." Confirmed, when asked how far this should go: **"Everything,
  including existing shipped agents"** — not just new wizard-created agents.
  The breadcrumb itself names this "a genuine architecture reversal, not a
  wizard feature," flagged explicitly to the operator as such before the
  requirement was written and confirmed as the intended scope. It touches
  `ADR-011` point 2's own action-definition shape and every already-shipped
  story that added or relied on an Action.

- **This story is one half of a two-story split of REQ-SB-39** (analyst
  decision, recorded in full at `ESCALATIONS.md` → `ESC-029`, not guessed
  silently). The PRD's own single Acceptance text describes one end state,
  but splitting the delivery in two lets the safety-critical half (extending
  the working-mode gate to Skills) land atomically with the mutating-Action
  migration it protects, rather than forcing the whole reversal through one
  oversized story. **This story (`US-01`) covers only the capability model
  itself plus every currently *read-only* Action** — migrating these
  requires no change to the working-mode gate at all, since a read-only
  capability is never gated under any working mode today (`ADR-020` point 2
  gates Supervised only on `mutates: True`). `REQ-SB-39-US-02` covers the
  gate extension and the mutating-Action migration together, so a mutating
  capability is never observably ungated even transiently.

- **Resolved here, by direct, live inspection of the real code (not a
  guess):** `app/business/agent_registry.py`'s static `AGENTS` catalog
  today declares 7 agents carrying a combined 14 action entries across 7
  distinct action ids. Of those, **3 distinct ids are `"mutates": False`**
  (read-only, in this story's scope): `view_last_run` (email-capture,
  meeting-capture, todo-capture, people-producer), `ask_question`
  (vault-qa), `view_channel_status` (vault-qa). The remaining 4 distinct ids
  (`run_capture_now`, `pause_schedule`, `rebuild_person_note`,
  `build_knowledge`) are `"mutates": True` — out of scope here, covered by
  `REQ-SB-39-US-02`. `vault-filing-expert` already carries zero actions
  today (nothing to migrate for it).

- **Resolved here, by direct inspection of `app/business/skill_registry.py`
  / `app/api/skills_router.py` (not a guess):** `invoke_skill(agent_id,
  skill_id, args)` and its `POST /agents/{agent_id}/skills/{skill_id}/
  invoke` endpoint check only `has_skill_access` (grant/revoke) today —
  **there is no working-mode check anywhere in that path.** This is exactly
  right for this story's own read-only-only scope (a read-only capability
  needs no gate under any mode), but confirms this codebase has never
  exercised a mutating capability through the Skills invocation path before
  — a real, load-bearing fact `REQ-SB-39-US-02` must design around, not
  assumed here.

- **A genuine gap found while resolving this story, not silently carried
  forward:** `REQ-SB-27-US-01` (Skills Repository, `Done`) shipped **zero
  UI** — confirmed by direct inspection of `html-prototype/` (no `skill`/
  `Skill` text anywhere except one unrelated mention in `agents-map.html`'s
  Meeting Capture description) and `src/frontend/src` (no match at all).
  Today's only agent-capability UI is the "Available actions" panel on
  `agents-map.html`'s agent detail side panel — a static button list
  rendered directly from `agent_registry.py`'s hardcoded `actions` array,
  with no grant/revoke affordance and no awareness of Skills at all. The
  PRD's own phrase "using the surfaces those requirements already built"
  (echoed from `REQ-SB-37`'s own Acceptance text) is **not factually true
  for Skills today** — the *API* mechanism exists (`GET/POST/DELETE
  /agents/{agent_id}/skills/...`), but no screen anywhere calls it. See the
  flag below.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A migrated read-only capability appears in the Skills Repository

```gherkin
Given the vault-qa agent's ask_question and view_channel_status capabilities,
    and every worker/producer agent's view_last_run capability, existed as
    hardcoded Actions before this change
When the Skills Repository catalog (skill_tools.SKILLS) is inspected after
    this change
Then ask_question, view_channel_status, and view_last_run each appear as a
    registered Skill entry, each carrying a "mutates": false classification
  And each already-shipped agent that previously carried the Action
    (email-capture, meeting-capture, todo-capture, people-producer for
    view_last_run; vault-qa for ask_question and view_channel_status) has
    the equivalent Skill grant recorded for it, not just the mechanism
    existing for a hypothetical future agent
```
<!-- AC-ID: REQ-SB-39-US-01-AC-01 -->

### Scenario 2: Granting or revoking a migrated capability uses the exact same mechanism as any other Skill

```gherkin
Given a migrated read-only capability (e.g. view_last_run) is now a
    registered Skill
When the user grants or revokes it for an agent, via the existing
    POST/DELETE /agents/{agent_id}/skills/{skill_id} endpoints (or the
    equivalent UI control)
Then the grant or revoke succeeds through the exact same
    skill_registry.grant_skill_access / revoke_skill_access mechanism
    already used for web-research or diagram-understanding
  And no separate, hardcoded-Actions-specific grant/revoke configuration
    path exists for this capability
```
<!-- AC-ID: REQ-SB-39-US-01-AC-02 -->

### Scenario 3: Invoking a migrated read-only capability produces the same observable result as before migration

```gherkin
Given the vault-qa agent's ask_question capability is now dispatched via
    skill_registry.invoke_skill instead of agents_router._invoke_action
When the user invokes it, whether via a matched chat phrase or a direct
    POST /agents/{agent_id}/actions/{action_id} call
Then the reply is the same honest "not yet available" response the
    capability produced before this migration (no real handler existed for
    it before, and none is added by this migration)
  And no change in behaviour is observable to the user
```
<!-- AC-ID: REQ-SB-39-US-01-AC-03 -->

### Scenario 4: Existing chat trigger phrases still work after migration

```gherkin
Given an agent's existing trigger phrase (e.g. "view last run" for
    email-capture) was wired to a hardcoded Action before this migration
When the user sends that exact same chat message after migration
Then agent_chat.handle_chat_message still matches the same trigger phrase
    to the same capability id
  And agents_router.py's dispatch routes it to
    skill_registry.invoke_skill(agent_id, id, args=None, trigger="chat")
    instead of _invoke_action, with the reply unchanged from before
    migration
```
<!-- AC-ID: REQ-SB-39-US-01-AC-04 -->

### Scenario 5: A newly created agent can be granted a migrated capability the same way an existing agent can

```gherkin
Given an agent that has never carried a migrated capability as either an
    Action or a Skill (e.g. a newly wizard-created agent, or
    vault-filing-expert, which carries zero actions today)
When the user grants it a migrated capability (e.g. view_last_run) via the
    Skills grant mechanism
Then the agent gains that capability
  And invoking it produces the identical result an already-shipped agent
    with the same capability granted produces
```
<!-- AC-ID: REQ-SB-39-US-01-AC-05 -->

### Scenario 6: An agent without a granted capability is honestly refused, never fabricated

```gherkin
Given an agent has not been granted a particular migrated capability
When the user, or a matched chat message, attempts to invoke it
Then skill_registry.invoke_skill returns a "refused" result and the agent
    honestly reports it does not have access to that capability
  And no run_event history entry is recorded, and nothing is fabricated as
    if the capability had succeeded
```
<!-- AC-ID: REQ-SB-39-US-01-AC-06 -->

### Scenario 7: Every capability an agent currently has, whether legacy-Action-shaped or already a Skill, is visible in one place

```gherkin
Given an agent has a mix of capabilities — some migrated from a hardcoded
    Action, some already a pre-existing Skill (e.g. web-research)
When the user requests GET /agents/{agent_id}, or views that agent's own
    capability list in its detail panel
Then the response's "capabilities" list (skill_registry.
    list_agent_capabilities) includes every capability the agent currently
    has access to, combining both kinds into one unified list
  And no "actions" key or separate "Actions"/"Skills" grouping is present
    anywhere in the response or the rendered panel
```
<!-- AC-ID: REQ-SB-39-US-01-AC-07 -->

## Affected Screens

- `html-prototype/agents-map.html` — the agent detail side panel's
  "Available actions" block needs to become a unified capability list
  (Scenario 7), sourced from Skills grants rather than `agent_registry.py`'s
  hardcoded array, with a real grant/revoke affordance (Scenario 2). **No
  such surface exists in the approved prototype today** — see the flag
  below; a `/design` pass is required before this can be built with
  confidence.

## Dependencies

- **Blocked by (all satisfied already):** `REQ-SB-21-US-01` (Working Modes,
  Done — `ADR-020`'s `mutates` concept this story's scope boundary is
  defined against, even though this story itself changes no gate logic),
  `REQ-SB-27-US-01` (Skills Repository, Done — plumbing only; this story
  reuses its grant/revoke mechanism, not just its registry shape).
- **Blocks:** `REQ-SB-39-US-02` (the mutating-Action migration + gate
  extension composes on top of this story's own unified capability model —
  must land after this story, not before or alongside it).
- **Blocks:** `REQ-SB-37-US-02` (Agent Creation Wizard — Worker flow) and
  `REQ-SB-37-US-03` (Agent Creation Wizard — Producer flow) — corrected
  2026-08-13 from the earlier stale reference to `REQ-SB-37-US-01`, which
  was split into three per-type stories the same day; only the Worker/
  Producer flows are Skills-based by the operator's own direction and
  cannot be fully built until this unification lands (named explicitly in
  `REQ-SB-37`'s own PRD breadcrumb). `REQ-SB-37-US-01` (the Expert flow) is
  NOT blocked by this story — see that story's own Context.
- **Related to, not modified by this story:** `app/business/
  agent_orchestration/mcp_client.py::load_agent_tools` — the in-app chat's
  own tool-calling loop already filters the shared MCP tool list per-agent
  via `skill_registry.has_skill_access` (`ADR-022` point 6); migrating a
  read-only Action to a registered `@mcp.tool()` Skill composes with this
  mechanism directly, no separate change needed for that path.
- **External:** none new.

## Constraints

- **Read-only capabilities only** — a currently `"mutates": True` Action
  must not be migrated by this story (see `REQ-SB-39-US-02`); migrating it
  here, ahead of the gate extension, would create exactly the transient
  ungated window this two-story split exists to prevent.
- Migrating a capability to a Skill must not change its observable behavior
  for any already-shipped agent (Scenarios 3/4) — this is a refactor of
  *where* the capability is declared and dispatched from, not a behavior
  change.
- Every already-existing chat trigger phrase for a migrated capability must
  keep working unchanged (Scenario 4) — whether the underlying chat funnel
  (`ADR-011`) dispatches into the Skills mechanism internally, or is itself
  restructured, is a mechanism decision left to `/plan-tasks`, not resolved
  here.
- `vault-filing-expert` carries zero actions today — nothing to migrate for
  it; it is unaffected by this story.

## Implementation Tasks

| Task | Title | Depends on |
|---|---|---|
| [[REQ-SB-39-US-01-T01]] | `skill_tools.py` — `mutates` field on all 5 catalog entries + 3 new honest-unavailable stub Skill handlers | — |
| [[REQ-SB-39-US-01-T02]] | `skill_registry.py` — `invoke_skill` gains required `trigger` param; `_SKILL_HANDLERS` gains 3 new entries | T01 |
| [[REQ-SB-39-US-01-T03]] | `skills_router.py` — invoke endpoint passes `trigger="direct"` (server-hardcoded) | T02 |
| [[REQ-SB-39-US-01-T04]] | `knowledge_bootstrap.py` — existing `invoke_skill` call gains `trigger="hub_routed"` | T02 |
| [[REQ-SB-39-US-01-T05]] | `skill_registry.py` — one-time migration-grant retrofit seed for the 4 real already-shipped agents | T01, T02 |
| [[REQ-SB-39-US-01-T06]] | `skill_registry.py` — new `list_agent_capabilities(agent_id)` aggregator (Actions + Skills, unified) | T01, T02 |
| [[REQ-SB-39-US-01-T07]] | `agents_router.py` — `trigger_action`/`chat()` dispatch fork to `skill_registry.invoke_skill` for migrated ids | T01, T02, T05 |
| [[REQ-SB-39-US-01-T08]] | `agents_router.py` — `get_agent()` response `"actions"` → `"capabilities"` | T06, T07 |
| [[REQ-SB-39-US-01-T09]] | `AgentDetailPanel.tsx` — unified capability list with real grant/revoke control; new `skillsApiClient.ts` | T08 |

## Definition of Done

- [x] All acceptance-criteria scenarios pass — `AC-01`..`AC-07` all
      verified live; see each task's own Implementation Log (`T01`..`T09`)
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, manual-mode verification (no test-stack ADR yet)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Migrating any currently-mutating Action** (`run_capture_now`,
  `pause_schedule`, `rebuild_person_note`, `build_knowledge`) — deferred to
  `REQ-SB-39-US-02`, which lands the working-mode gate extension in the same
  pass so a mutating capability is never ungated even transiently.
- **Extending the working-mode gate to Skills at all** — this story's own
  scope needs no gate change (every capability it touches is read-only,
  never gated under any mode today); the gate-extension design itself is
  `REQ-SB-39-US-02`'s job.
- **Designing or building the concrete Skills grant/revoke UI** — flagged as
  net-new-design-needed (see Notes); this story's Acceptance Criteria are
  written at the mechanism/observable-behavior level and do not presume a
  specific screen shape.
- **Restructuring `ADR-011`'s chat keyword-match funnel itself** — whether
  it stays Action-shaped and calls into the Skills mechanism internally, or
  is itself rebuilt to dispatch to Skills directly, is left to `/plan-tasks`
  (see Constraints).
- **`REQ-SB-37`'s own Worker/Producer wizard Skill-grant flow** — that
  story's own scope; this story only makes the underlying mechanism ready
  for it.

## Notes

**Prototype parity (agents-map.html):**

- Agent detail side panel Settings tab (Section/Provider/Keywords/
  Working-mode rows) — **Specced elsewhere, unaffected** — this story does
  not touch this block.
- Agent detail side panel "Available actions" block — **Superseded, net-new
  design needed.** Today it is a static button list rendered directly from
  `agent_registry.py`'s hardcoded `actions` array, with no grant/revoke
  affordance and zero Skills awareness. This story's own Scenario 7 requires
  it (or a successor surface) to become a unified capability list, sourced
  from Skills grants, with a real grant/revoke control — **no approved
  prototype screen shows this today.** A `/design` pass is required before
  `/plan-tasks` can lock tasks against a UI shape no one has approved.
- Agent detail side panel Chat/Communication-history tabs — **Specced
  elsewhere, unaffected.**
- No `html-prototype/` screen anywhere has a standalone Skills Repository
  browsing surface (a list of all registered Skills, independent of any one
  agent) — `REQ-SB-27-US-01` never built one; this story does not build one
  either, only the per-agent grant/revoke/invocation-observable-behavior
  half.

**Why this is flagged, not cleared (`ESCALATIONS.md` → `ESC-029`):**

1. **Genuine architecture reversal** — the PRD breadcrumb itself names this
   explicitly, confirmed by the operator as intended scope before the
   requirement was written.
2. **Mechanism-level questions left open by the PRD's own breadcrumb** —
   whether the `ADR-011` chat keyword-match funnel needs restructuring to
   dispatch to Skills, and migration ordering/mechanics — both explicitly
   named "left to `/spec`/`/plan-tasks`," not guessed here.
3. **Net-new-design-needed** — no `html-prototype/` screen has any Skills
   grant/revoke affordance anywhere, and `REQ-SB-27-US-01` shipped zero UI;
   today's "Available actions" panel cannot show a migrated capability
   without a real design pass.

`ESCALATIONS.md` → `ESC-029` records the full reversal (covering both
`REQ-SB-39-US-01` and `REQ-SB-39-US-02`) in detail. A `REVIEW-QUEUE.md`
entry recommends the concrete next steps for both stories together.

**Update, 2026-08-13 (`/plan-tasks` step 1 — architect).** Both original
blockers are resolved, not re-derived here: (1) the operator made the two
mechanism-level decisions directly and relayed them for architecture
record — `mutates` is a static per-Skill boolean on the Skill's own
catalog entry, mirroring `ADR-020`'s Action shape exactly; `invoke_skill`
gains an explicit `trigger: Literal["chat","direct","hub_routed"]`
parameter, mirroring `_invoke_action`'s shape, threaded through every
real call site but not yet branched on (`REQ-SB-39-US-02`'s own job);
`ADR-011`'s chat funnel is NOT rebuilt — only its dispatch step changes,
once a phrase matches a migrated capability it now calls `invoke_skill(
..., trigger="chat")` instead of `_invoke_action(..., trigger="chat")`.
(2) The operator separately decided to skip the `/design` pass for this
entire batch of work (`REQ-SB-28/29/37/38/39/40/41`,
`REVIEW-QUEUE.md` 2026-08-13 update) and build directly, matching the
established Section/Provider/Keywords/Working-mode kv-list row pattern —
no fresh prototype screen gates this build. A new ADR,
[ADR-028](../Architecture/ADR.md), records the full mechanism
(`skill_tools.SKILLS` gains `mutates`; `skill_registry.invoke_skill`
gains `trigger`; the funnel's dispatch fork; a one-time migration seed;
the `list_agent_capabilities` unification) — MUST-FLAG trigger 3 fires
(ADR created), so `gate:` stays `flagged`, but per
`Implementation/Pipeline.md` this does **not** halt `/plan-tasks` — the
decomposer proceeds so the human reviews `ADR-028` and the resulting tasks
together in one pass. See `REVIEW-QUEUE.md` for the pointer.

**Architecture scope for the decomposer/coder (bounded by
[ADR-028](../Architecture/ADR.md) and `architecture.md`'s "Amendment —
unified capability model, phase 1: read-only Actions migrated to Skills
(REQ-SB-39-US-01, see ADR-028)" section, under "Skills Repository —
registration & per-agent access"):**

- `src/backend/app/business/skill_tools.py` — add `"mutates": bool` to
  all 5 catalog entries (both existing + the 3 new); add 3 new zero-arg
  `@mcp_server.tool()` stub handlers (`view_last_run`, `ask_question`,
  `view_channel_status`), each unconditionally honest-unavailable.
- `src/backend/app/business/skill_registry.py` — `invoke_skill` gains the
  required `trigger` parameter; `_SKILL_HANDLERS` gains 3 new entries;
  new `list_agent_capabilities(agent_id)` aggregator; the one-time
  migration-grant seed (a small literal id→agent-list mapping) folded
  into `_load_state()`, framed explicitly as a bounded historical
  backfill, not a general self-healing default.
- `src/backend/app/api/skills_router.py` — the invoke endpoint's
  `invoke_skill(...)` call gains `trigger="direct"` (server-hardcoded,
  never client-supplied).
- `src/backend/app/api/agents_router.py` — `trigger_action`/`chat()`
  dispatch: route a matched/requested id that is a `skill_tools.SKILLS`
  member to `skill_registry.invoke_skill(...)` instead of
  `_invoke_action(...)`; a small result-shape translation into the
  existing `{"status","message"}` envelope; `get_agent()`'s response
  changes `"actions"` → `"capabilities"` (sourced from
  `list_agent_capabilities`).
- `src/backend/app/business/agent_orchestration/knowledge_bootstrap.py`
  — its existing `invoke_skill(...)` call gains `trigger="hub_routed"`.
- **Explicitly NOT modified — do not edit:** `src/backend/app/business/
  agent_registry.py` (the 3 migrated ids' entries stay exactly as they
  are, per ADR-028 point 3's "minimal blast radius" decision) and
  `src/backend/app/business/agent_chat.py` (the chat funnel's matching
  logic is unchanged).
- **Explicit retrofit task required, not just the mechanism build:** a
  concrete task must exist for the one-time migration-grant seed
  (`skill_registry.py`'s change, above) actually running and being
  verified against the 4 real agents (`email-capture`, `meeting-capture`,
  `todo-capture`, `people-producer`, `vault-qa`) — the operator's own
  directive ("Everything, including existing shipped agents") is not
  satisfied by building the new mechanism alone; the decomposer must not
  fold this into "mechanism plumbing" and drop it.
- Frontend: `src/frontend/src/features/agents-map/AgentDetailPanel.tsx`
  (unify the "Available actions" block into a capability list with a
  real grant/revoke control) + a new `skillsApiClient.ts` (mirrors
  `settingsApiClient.ts`'s thin fetch-wrapper shape), reusing the
  already-existing `GET /skills` / `GET,POST,DELETE /agents/{agent_id}/
  skills[/{id}]` endpoints — no new endpoint needed for grant/revoke.

Architecture scope: §"Skills Repository — registration & per-agent
access" (including its "Amendment — unified capability model, phase 1"
subsection) in `architecture.md`; [ADR-011](../Architecture/ADR.md),
[ADR-020](../Architecture/ADR.md), [ADR-022](../Architecture/ADR.md), and
[ADR-028](../Architecture/ADR.md) (new) in `ADR.md`.

gate: flagged 2026-08-13, gate_reason: trigger-3 (`ADR-028` created) — see
frontmatter and the Update above. `REQ-SB-39` itself is finalised PRD text
(no `<!-- Draft -->` marker); the flag is solely the ADR-creation trigger,
not an unresolved requirement or design gap.

**Update, 2026-08-13 (`/plan-tasks` step 2 — decomposer).** All 7
Gherkin scenarios tightened for buildability and locked as
`REQ-SB-39-US-01-AC-01` … `AC-07` (all locked; none marked
`locked: false`). 9 tasks written at the flat root, `T01`–`T09`,
`depends_on` acyclic (see the `## Implementation Tasks` table above):
`T01`–`T02` land the `mutates`/`trigger` mechanism shapes; `T03`/`T04`
update the 2 pre-existing real `invoke_skill` call sites; `T05` is the
explicit migration-grant retrofit seed (kept as its own task, not folded
into mechanism plumbing, per this story's own Notes); `T06` adds the
`list_agent_capabilities` aggregator; `T07` is the `agents_router.py`
dispatch fork (Scenarios 3/4/5/6); `T08` changes `get_agent()`'s response
shape (Scenario 7); `T09` is a frontend task.

**On `T09` (frontend) — a real, deliberate decomposer call, not a silent
default:** the architect's own Architecture-scope list under this story's
`## Notes` names `AgentDetailPanel.tsx` + a new `skillsApiClient.ts` as
real files to modify, and the `REVIEW-QUEUE.md` entry for this story
records the operator's same-day decision to skip `/design REQ-SB-39` and
"build directly, matching the established Section/Provider/Keywords/
Working-mode kv-list row pattern." This resolves, in the architect's
favour, an apparent tension against this story's own `## Non-Goals`
("Designing or building the concrete Skills grant/revoke UI" — written
before that same-day operator decision). Both locked ACs that touch this
surface (`AC-02`, `AC-07`) are still written and independently verifiable
at the mechanism/API level (`T03`, `T08`) — `T09`'s own Tests are
supplementary structural checks, not the sole path to either AC passing;
this preserves the Non-Goals' own "ACs do not presume a specific screen
shape" framing while still building the real screen surface the
architecture scope now names. Flagged here explicitly for the same human
pass already reviewing `ADR-028`, in case the operator intended the UI
build to wait for `REQ-SB-39-US-02` or a later story instead.

**Gate stays `flagged` — unchanged, not a new trigger.** Per
`Implementation/Pipeline.md`'s "leave the flag set" rule for an
ADR-creation trigger (trigger-3, already recorded by the architect this
pass), the decomposer does not clear it — this is the same open
`ADR-028` review, not a second flag. `status: Draft → Ready` — every AC is
locked, every locked AC has at least one AC-tagged verification step
across `T01`–`T09` (`AC-01`: `T01`, `T02`, `T05`; `AC-02`: `T01`, `T03`,
`T09`; `AC-03`–`AC-06`: `T07`; `AC-07`: `T06`, `T08`, `T09`), and
`depends_on` is acyclic. All 9 tasks are written directly at
`status: Ready` (lockstep with the story), `gate: clear` (no task-level
MUST-FLAG trigger fired independently of the story's own inherited
`ADR-028` flag).
