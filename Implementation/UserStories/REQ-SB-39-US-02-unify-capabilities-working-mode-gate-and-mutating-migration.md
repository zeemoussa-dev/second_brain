---
id: REQ-SB-39-US-02
title: Extend the working-mode approval gate to Skills, and migrate every existing mutating Action to a Skill
requirement_ids: [REQ-SB-39]
requirement_section: "REQ-SB-39: Unify Agent Capabilities Under Skills"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-029 created) — /plan-tasks step 1 (architect): the mutates-classification mechanism for Skills was already resolved by ADR-028 (REQ-SB-39-US-01); this pass resolves the remaining open question (whether ADR-020's gate mechanism needs a redesign vs. a direct extension — resolved: the gate moves inside skill_registry.invoke_skill itself, a direct extension of ADR-020's own two-axis logic, not a redesign) and records it as ADR-029. The story remains flagged solely because this pass created ADR-029 (MUST-FLAG trigger 3) — this does NOT halt the decomposer, per Implementation/Pipeline.md. Original oversized/high-risk framing stands as context for the human review, not as a separate unresolved blocker."
sprint: SPRINT-031
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-39-US-02 — Extend the working-mode approval gate to Skills, and migrate every existing mutating Action to a Skill

## Story

**As a** Second Brain user relying on Supervised/Manual working modes to
control which capabilities can act without my direct approval
**I want** every mutating capability — including today's hardcoded mutating
Actions (`run_capture_now`, `pause_schedule`, `rebuild_person_note`,
`build_knowledge`) — to keep honoring my agent's working mode exactly as it
does today, even after that capability becomes a Skill
**So that** unifying the capability model (`REQ-SB-39-US-01`) never weakens
the approval protections I already rely on, for a single day, for a single
agent, for a single capability

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-39: Unify Agent Capabilities Under
  Skills*. **Acceptance (the clause this story exists to satisfy):** "a
  mutating Skill's invocation still honors the agent's own working mode
  (Autonomous/Supervised/Manual) the same way a mutating Action does today."

- **This is the second half of a two-story split of REQ-SB-39** — see
  `REQ-SB-39-US-01`'s own Context and `ESCALATIONS.md` → `ESC-029` for the
  full split rationale. This story covers the two things that must land
  **together, in the same build**: extending the working-mode gate to cover
  Skills, and migrating every currently-mutating Action to a Skill. Landing
  either half without the other would create exactly the outcome this
  requirement exists to prevent — a mutating capability invocable without
  the approval gate that protects it today.

- **Resolved here, by direct, live inspection of the real code (not a
  guess):** two structurally separate gates exist today and this story must
  reconcile with both:
  1. `app/api/agents_router.py::_invoke_action` (`ADR-020`) — the real,
     current two-axis working-mode gate for hardcoded Actions. Resolves
     `mode = working_mode_registry.get_agent_working_mode(agent_id)` and
     `action = agent_registry.get_action(agent_id, action_id)`
     (fail-safe: an unresolvable action's `mutates` defaults to `True`).
     Manual + `trigger == "hub_routed"` refuses outright. Supervised +
     `mutates is True` creates a pending-approval record
     (`pending_approval_registry.create_pending_approval`) and returns
     `{"status": "pending", ...}`. Supervised + `mutates is False` and
     Autonomous (any trigger) and Manual (`"chat"`/`"direct"` trigger) all
     fall straight through to `_execute_action`/`_execute_async_action`.
  2. `app/business/skill_registry.py::invoke_skill` / `app/api/
     skills_router.py`'s `POST /agents/{agent_id}/skills/{skill_id}/invoke`
     — confirmed **completely ungated** today: `invoke_skill` checks only
     `has_skill_access(agent_id, skill_id)` (the grant/revoke concern) before
     dispatching straight to the registered handler. There is no `trigger`
     parameter anywhere on this path at all (unlike `_invoke_action`'s
     `"chat" | "direct" | "hub_routed"`), no working-mode lookup, and no
     pending-approval integration. This is exactly right for `REQ-SB-27`'s
     own narrow, largely read-only skills (`web-research`,
     `diagram-understanding`) — this story is what changes that, for
     mutating Skills only.
  Separately, `app/business/agent_orchestration/mcp_client.py::
  load_agent_tools` (`ADR-022` point 6) already gates the in-app chat's own
  tool-calling loop by `has_skill_access` alone — an access-grant filter,
  not a working-mode gate; it decides which tools an agent's LangGraph
  conversation can even see, not whether a mutating one executes
  immediately vs. proposes-and-waits. This story's own gate extension is a
  distinct, additional layer on top, not a replacement for this filter.

- **Genuinely NOT resolved here — the mutates-classification mechanism for
  Skills.** `ADR-020` point 1's own reasoning classifies `mutates` as "a
  structural fact about what the action's own code does, not a user
  preference," deliberately kept as a static field on
  `agent_registry.py`'s hardcoded action dicts, not a persisted/mutable
  concern. Skills, by contrast, are registered on the shared MCP server
  (`app/business/skill_tools.py`, `ADR-015`) with their own catalog shape
  (`skill_tools.SKILLS`) — which has **no `mutates`-equivalent field
  today.** Whether `mutates` becomes a parallel static field on each
  `@mcp.tool()`-registered Skill's own catalog entry (the most direct
  extension of `ADR-020`'s own precedent, one layer over), or Skills need a
  materially different approval model entirely (e.g. because a single Skill
  could plausibly be invoked with different args that have different
  read/write implications, unlike a fixed-shape Action), is a real
  architecture-level call. The PRD's own breadcrumb names this explicitly:
  "whether `mutates` becomes a per-Skill classification... so `ADR-020`'s
  existing Supervised-mode gate logic can key off Skills with minimal
  redesign, or whether Skills need a materially different approval model" —
  **left to `/spec`/`/plan-tasks`, not decided here.** This story describes
  only the OBSERVABLE BEHAVIOR the gate extension must produce (Scenarios
  below), not the mechanism.

- **Genuinely NOT resolved here — whether `invoke_skill`/its endpoint gains
  a `trigger` concept at all**, and if so, how it's threaded through from
  each real call site (chat, a direct UI trigger, a future Hub-routed
  request) the same way `_invoke_action`'s `trigger` parameter already is.
  Today's `POST /agents/{agent_id}/skills/{skill_id}/invoke` has no such
  parameter anywhere — adding one, and wiring every caller to supply it
  correctly, is real structural work belonging to `/plan-tasks`.

- **Resolved here, by direct code inspection (not a guess):** the 4
  currently-mutating Action ids in scope for migration are `run_capture_now`
  (email-capture, meeting-capture, todo-capture — files new notes),
  `pause_schedule` (same three agents — a control-plane mutation, `ADR-020`
  point 1's own explicit "not read-only by any reasonable reading"
  classification), `rebuild_person_note` (people-producer — overwrites/
  regenerates a Person note), `build_knowledge` (compass-expert —
  `ADR-023`'s async, agent_id-aware, richer-envelope handler, dispatched via
  `_execute_async_action` today, not `_execute_action`). The migrated Skill
  equivalents must each preserve their real, already-shipped handler
  behavior (`run_capture_and_record_completion`, the people-extraction
  rebuild path, `knowledge_bootstrap.bootstrap_agent_knowledge` via
  `_run_build_knowledge`) — this story does not rewrite what any of these
  capabilities actually do, only how they are declared, granted, and gated.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A mutating Skill in Supervised mode still requires approval before executing

```gherkin
Given an agent is in Supervised working mode
  And it has a mutating capability granted as a Skill (e.g. the migrated
    run_capture_now)
When the user, or a matched chat message, or a direct trigger invokes that
    Skill
Then the invocation does not execute immediately
  And a pending-approval record is created, exactly as a mutating Action
    does today
  And the user sees a message naming the proposed capability and that it is
    awaiting approval ("Proposed — {capability name}. Awaiting your
    approval.")
```
<!-- AC-ID: REQ-SB-39-US-02-AC-01 -->

### Scenario 2: Approving a pending mutating Skill invocation executes it

```gherkin
Given a mutating Skill invocation is pending approval
When the user approves it
Then the capability executes
  And the outcome is recorded in the agent's history exactly as an approved
    mutating Action's outcome is recorded today
```
<!-- AC-ID: REQ-SB-39-US-02-AC-02 -->

### Scenario 3: A mutating Skill on a Manual-mode agent is never triggered by another agent's request

```gherkin
Given an agent is in Manual working mode
  And it has a mutating capability granted as a Skill
When another agent's Hub-routed request attempts to invoke that Skill
Then the agent refuses outright
  And no pending-approval record is created
  And no execution occurs
```
<!-- AC-ID: REQ-SB-39-US-02-AC-03 -->

### Scenario 4: A mutating Skill executes immediately under Autonomous mode, or when the user asks directly under Manual mode

```gherkin
Given an agent is in Autonomous mode, or is in Manual mode and the user
    directly asks it via chat or a direct trigger
When the user invokes a granted mutating Skill
Then it executes immediately
  And the outcome is recorded in the agent's history exactly as an
    unapproved-gate mutating Action's outcome is recorded today
```
<!-- AC-ID: REQ-SB-39-US-02-AC-04 -->

### Scenario 5: A read-only Skill on the same agent is never gated by working mode, regardless of what its mutating siblings require

```gherkin
Given an agent has both a read-only capability and a mutating capability,
    each granted as a Skill
  And the agent is in Supervised mode
When the user invokes the read-only capability
Then it executes immediately, without requiring approval
  And the agent's mutating Skill remains gated independently — invoking it
    still requires approval
```
<!-- AC-ID: REQ-SB-39-US-02-AC-05 -->

### Scenario 6: Every existing mutating Action is migrated with zero loss of protection

```gherkin
Given run_capture_now, pause_schedule, rebuild_person_note, and
    build_knowledge all existed as hardcoded mutating Actions before this
    change
When each is inspected after migration
Then each is now a Skill
  And each still honors the same Autonomous/Supervised/Manual gating its
    Action counterpart honored before migration
  And each still performs the same real underlying work it did as an Action
    once approved or executed (e.g. run_capture_now still files the same
    real captured content into the vault)
```
<!-- AC-ID: REQ-SB-39-US-02-AC-06 -->

### Scenario 7: Granting or revoking a mutating Skill uses the exact same mechanism as any other Skill

```gherkin
Given a mutating capability is now a Skill
When the user grants or revokes it for an agent
Then the grant or revoke uses the identical mechanism used for every other
    Skill, read-only or mutating
  And no separate, harder-coded, mutating-Action-specific configuration
    surface remains
```
<!-- AC-ID: REQ-SB-39-US-02-AC-07 -->

### Scenario 8: The direct skill-invocation endpoint is never a bypass around the working-mode gate

```gherkin
Given the existing skill-invocation endpoint (REQ-SB-27) previously invoked
    any granted Skill completely unconditionally
When it is called for a mutating Skill after this change
Then the same working-mode gate applies to it as to every other invocation
    path for that same capability
  And it is never usable as a route around Supervised or Manual protections
```
<!-- AC-ID: REQ-SB-39-US-02-AC-08 -->

## Affected Screens

- `html-prototype/agents-map.html` — the agent detail side panel's
  pending-approval / Chat-proposal pattern (already approved for
  `REQ-SB-21-US-01`) needs to extend to a mutating Skill's own proposal, not
  only a mutating Action's — see Notes. No new visual pattern is expected
  (the existing `.chat-proposal` card is reused), but this needs explicit
  confirmation once `REQ-SB-39-US-01`'s own unified capability-list UI
  exists (this story cannot be designed in isolation from it).
- `html-prototype/my-day-approvals.html` — the Pending Approvals surface
  (already approved for `REQ-SB-21-US-01`) needs to show a mutating Skill's
  own pending-approval record alongside a mutating Action's, using the
  identical card shape — same caveat as above.

## Dependencies

- **Hard prerequisite:** `REQ-SB-39-US-01` — this story's own migrated
  mutating capabilities must land on top of that story's already-unified
  capability model, not before or alongside it.
- **Blocked by (all satisfied already):** `REQ-SB-21-US-01` (Working Modes /
  `ADR-018`/`ADR-020`, Done — the gate this story extends), `REQ-SB-27-US-01`
  (Skills Repository, Done — plumbing only; this story's gate extension
  applies on top of its existing `invoke_skill`/endpoint).
- **Blocks:** `REQ-SB-37-US-02` (Agent Creation Wizard — Worker flow) and
  `REQ-SB-37-US-03` (Agent Creation Wizard — Producer flow) — corrected
  2026-08-13 from the earlier stale reference to `REQ-SB-37-US-01`, which
  was split into three per-type stories the same day; both flows are
  Skills-based and cannot be fully built until both halves of `REQ-SB-39`
  land (named explicitly in `REQ-SB-37`'s own PRD breadcrumb).
  `REQ-SB-37-US-01` (the Expert flow) is NOT blocked by this story — see
  that story's own Context.
- **Related to, unaffected by this story:** `app/business/
  agent_orchestration/mcp_client.py::load_agent_tools` (`ADR-022` point 6) —
  its own access-grant filter (which tools an in-app conversation can see at
  all) is a separate layer from this story's working-mode gate (whether a
  visible, invocable mutating Skill executes immediately or proposes); this
  story does not change that filter.
- **External:** none new.

## Constraints

- **The gate extension and the mutating-Action migration must land together,
  in the same release** — at no point should a mutating capability exist
  that is invocable through any real call site (chat, direct trigger,
  Hub-routed request, or the direct skill-invocation endpoint) without the
  working-mode gate applying to it.
- The `mutates`-classification mechanism for Skills is an architect-level
  decision, not resolved here — this story's Acceptance Criteria describe
  only the OBSERVABLE BEHAVIOR the gate must produce (Scenarios 1-5, 8), not
  which concrete field/structure carries the classification.
- Every migrated mutating capability must preserve its real, already-shipped
  underlying handler behavior unchanged (Scenario 6) — this is a
  gating/declaration refactor, not a rewrite of what any capability
  actually does.
- A read-only Skill's gating must remain entirely independent of any
  mutating Skill the same agent also has (Scenario 5) — migrating mutating
  capabilities must not accidentally widen or narrow the read-only gate
  `REQ-SB-39-US-01` already established.

## Implementation Tasks

| Task | Title | Depends on | Status |
|---|---|---|---|
| [[REQ-SB-39-US-02-T01]] | `skill_registry.py` — two-axis working-mode gate inside `invoke_skill` + `_dispatch_skill` extraction | `REQ-SB-39-US-01-T01`, `REQ-SB-39-US-01-T02` | Done |
| [[REQ-SB-39-US-02-T02]] | `pending_approvals_router.py` — Approve endpoint gains a `skill_tools.SKILLS`-aware branch | `REQ-SB-39-US-02-T01` | Done |
| [[REQ-SB-39-US-02-T03]] | Migrate the 4 mutating Action ids into `skill_tools.SKILLS` + handlers | `REQ-SB-39-US-02-T01`, `REQ-SB-39-US-02-T02`, `REQ-SB-39-US-01-T01`, `REQ-SB-39-US-01-T02` | Done |
| [[REQ-SB-39-US-02-T04]] | Migration-grant retrofit seed for the 5 real agents | `REQ-SB-39-US-02-T03`, `REQ-SB-39-US-01-T05` | Done |

Atomicity (`ADR-029` point 8) is enforced structurally: `T03` (the
migration) `depends_on` `T01` (the gate) directly — the 4 mutating ids
can never land in the catalog without the gate already in place in the
same or an earlier task. `T04` (retrofit) depends on `T03`, so it is
transitively gated the same way.

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Migrating any read-only capability** — already covered by
  `REQ-SB-39-US-01`; this story only migrates the 4 currently-mutating
  Action ids.
- **Designing the `mutates`-for-Skills mechanism itself** — the architect's
  call at `/plan-tasks`, not the analyst's; this story specifies observable
  behavior only.
- **Restructuring `ADR-011`'s chat keyword-match funnel beyond what's needed
  to thread a `trigger` value through to the gate** — any deeper
  restructuring is `REQ-SB-39-US-01`'s own already-flagged open question,
  not duplicated or re-decided here.
- **A generic, per-argument mutates classification for a Skill that could be
  invoked with different read/write implications depending on its args** —
  the PRD breadcrumb names this as a real possibility but does not resolve
  it; this story does not build such a mechanism ahead of an architect
  decision on whether it's even needed.
- **`REQ-SB-37`'s own Worker/Producer wizard Skill-grant flow** — that
  story's own scope; this story only makes both migration halves ready for
  it.

## Notes

**Prototype parity (agents-map.html / my-day-approvals.html):**

- `.chat-proposal` pending-approval card pattern (already approved for
  `REQ-SB-21-US-01`) — **Specced, reused**, Scenario 1; expected to need no
  new visual pattern, only a new source of proposals (mutating Skills
  alongside mutating Actions), but this cannot be confirmed until
  `REQ-SB-39-US-01`'s own unified capability-list UI exists to invoke a
  Skill from in the first place — see the flag below.
- `my-day-approvals.html` Pending Approvals surface (already approved for
  `REQ-SB-21-US-01`) — **Specced, reused**, Scenario 1/2; same caveat as
  above.
- No `html-prototype/` screen shows a mutating Skill's own proposal card
  distinct from a mutating Action's — not expected to need one (the
  existing pattern is generic over "a description string + approve/decline
  controls"), but not yet confirmed against a real design pass.

**Why this is flagged, not cleared (`ESCALATIONS.md` → `ESC-029`):**

1. **Genuine architecture reversal, the safety-critical half** — this story
   extends `ADR-020`'s own working-mode gate, the mechanism this project's
   entire Supervised/Manual trust model depends on, to a code path
   (`invoke_skill`) that was deliberately built ungated for a narrower class
   of capability.
2. **The `mutates`-classification mechanism for Skills is a real,
   unresolved architect-level call**, named explicitly by the PRD's own
   breadcrumb as "left to `/spec`/`/plan-tasks`" — not guessed here.
3. **Whether `invoke_skill`/its endpoint needs a `trigger` concept, and how
   it threads through every real call site**, is real structural work with
   more than one plausible shape.
4. **Depends on `REQ-SB-39-US-01` landing first** — this story cannot be
   designed or built in isolation; its own affected-screens question (does
   the pending-approval UI need any change once Skills, not just Actions,
   can propose?) cannot be answered until that story's own unified
   capability-list UI exists.

`ESCALATIONS.md` → `ESC-029` records the full reversal (covering both
`REQ-SB-39-US-01` and `REQ-SB-39-US-02`) in detail. A `REVIEW-QUEUE.md`
entry recommends the concrete next steps for both stories together.

**Update, 2026-08-13 (`/plan-tasks` step 1 — architect).** `REQ-SB-39-US-01`
landed `Ready` with `ADR-028` (its own gate mechanism shapes —
`skill_tools.SKILLS` gains `mutates`, `invoke_skill` gains `trigger` —
already threaded through every real call site, not yet branched on).
This pass resolves this story's own remaining open architecture questions
and records them as [ADR-029](../Architecture/ADR.md):

- **Where the gate lives:** inside `skill_registry.invoke_skill` itself,
  not mirrored into `agents_router.py` the way `_invoke_action` (`ADR-020`)
  is — the one function all three real call sites (`skills_router.py`'s
  direct invoke endpoint, `agents_router.py`'s dispatch fork,
  `knowledge_bootstrap.py`'s Hub-routed call) already pass through, and the
  only placement that does not force `knowledge_bootstrap.py` (a business
  module) to violate `ADR-003`'s layering to reach it. This directly
  satisfies Scenario 8 (never a bypass) by construction, not by caller
  discipline.
- **How a Supervised mutating Skill invocation creates a Pending
  Approval:** reuses `pending_approval_registry.create_pending_approval`
  unedited, storing `skill_id` in the existing generic `action_id` field
  (the same field `ADR-021` point 5's Tier-2 ids already reuse) and the
  invocation's own `args` in the existing `payload` field. A new,
  ungated `skill_registry._dispatch_skill` primitive (mirrors
  `_execute_action`'s "thin gate wraps unconditional dispatch" split)
  backs both the gate's own post-check fallthrough and a new
  `pending_approvals_router.py` Approve-endpoint branch (Scenario 2).
- **Migration atomicity, concretely defined for a single-process app with
  no staged rollout:** the gate-logic task, the Approve-endpoint task, and
  the 4-id-migration-plus-retrofit task must be `depends_on`-chained
  (migration depends on gate, never the reverse) — a decomposer-level
  task-sequencing discipline, not a code mechanism, since no real deploy
  boundary exists to enforce it technically.
- **Migration preserves exactly today's real/honest-unavailable split —
  confirmed by direct code inspection, not guessed:** `_ACTION_HANDLERS`
  wires a real handler to only 2 of the 4 mutating ids' agent pairs today
  (`("email-capture", "run_capture_now")`, `("compass-expert",
  "build_knowledge")`); the other 5 real pairs (`meeting-capture`/
  `todo-capture`'s own `run_capture_now`, all 3 agents' `pause_schedule`,
  `people-producer`'s `rebuild_person_note`) have no wired handler today
  and already return an honest "not yet available." The migrated Skill
  handlers preserve this split exactly — no new real behavior is built by
  this pass.
- **The 5 real agents needing retrofit** (confirmed by direct reading of
  `agent_registry.py`'s own `AGENTS` catalog — the task's own "4 real
  agents" framing names the 4 action ids, not 4 distinct agents; 3 agents
  share `run_capture_now`+`pause_schedule`, 2 more each carry one distinct
  id): `email-capture`, `meeting-capture`, `todo-capture` (`run_capture_now`
  + `pause_schedule`), `people-producer` (`rebuild_person_note`),
  `compass-expert` (`build_knowledge`).

Full reasoning, every alternative considered, and every consequence:
[ADR-029](../Architecture/ADR.md). Architecture updated: see "Amendment —
unified capability model, phase 2" under "Skills Repository —
registration & per-agent access" in `architecture.md`.

**Architecture scope for the decomposer/coder:** §"Skills Repository —
registration & per-agent access" in `architecture.md` (both its "Amendment
— unified capability model, phase 1" and "Amendment — unified capability
model, phase 2" subsections) + §"Agent Working Modes & Pending Approvals"
(the `_invoke_action`/`_execute_action`/Approve-endpoint precedent this
story's own gate and Approve-branch mirror); [ADR-018](../Architecture/ADR.md),
[ADR-020](../Architecture/ADR.md), [ADR-021](../Architecture/ADR.md) point 5,
[ADR-028](../Architecture/ADR.md), and [ADR-029](../Architecture/ADR.md)
(new) in `ADR.md`. Real files in scope: `src/backend/app/business/
skill_registry.py` (gate logic + `_dispatch_skill`), `src/backend/app/
business/skill_tools.py` (4 new `SKILLS` entries + handlers),
`src/backend/app/api/pending_approvals_router.py` (new Approve branch +
`skill_registry` import) — `agent_registry.py` and `agent_chat.py` stay
unedited, same "leave in place" precedent `ADR-028` point 3 already
established.

gate: flagged 2026-08-13, gate_reason: trigger-3 (`ADR-029` created) — see
frontmatter and the Update above. `REQ-SB-39` itself is finalised PRD text
(no `<!-- Draft -->` marker); the flag is solely the ADR-creation trigger,
not an unresolved requirement or design gap. Does not halt the decomposer —
per `Implementation/Pipeline.md`, the decomposer proceeds so the human
reviews `ADR-029` and the resulting tasks together in one pass.

**Update, 2026-08-13 (`/plan-tasks REQ-SB-39-US-02` step 2 — decomposer).**
All 8 scenarios locked as `AC-01`…`AC-08` (no non-locked ACs — every
scenario is independently, observably verifiable). 4 tasks written
(`T01`–`T04`), `depends_on` acyclic, chained so migration/retrofit can
never land ahead of the gate (`ADR-029` point 8's atomicity discipline
enforced structurally, not just by discipline): `T03` (catalog/handler
migration) `depends_on` `T01` (the gate) directly; `T04` (retrofit)
`depends_on` `T03`. Cross-story edges into `REQ-SB-39-US-01`'s own real
task IDs: `T01` depends on `REQ-SB-39-US-01-T01`/`T02` (the `mutates`
field and `trigger` param this gate reads); `T03` additionally depends on
the same two (the catalog/handler-dict shapes it extends); `T04` depends
on `REQ-SB-39-US-01-T05` (the exact `_MIGRATION_GRANT_SEED` dict it
extends). `status: Draft → Ready`; `gate:` stays `flagged` — unchanged
trigger (still the same `ADR-029`-creation breadcrumb the architect
already recorded above, not a new decomposer-raised trigger).

**Two real, previously-unaddressed wiring gaps found live while building
`T03`, both resolved in-scope, both worth the same human review pass as
`ADR-029` itself (not blocking, but disclosed per Implementation/
Pipeline.md's "reduce attention must never become zero visibility"):**

1. **`build_knowledge`'s real handler needs a sync/async bridge
   `ADR-029` does not name.** `knowledge_bootstrap.bootstrap_agent_knowledge`
   is `async def`; `invoke_skill`/`_dispatch_skill`'s own dispatch
   contract is synchronous end-to-end, and a real caller
   (`agents_router.py`'s own async `trigger_action`/`chat()` routes) may
   already be executing inside FastAPI's own active event loop when this
   handler runs — a plain `asyncio.run()` call would raise
   `RuntimeError: cannot be called from a running event loop` in that
   real case. `T03` resolves this with a dedicated single-use thread
   (`concurrent.futures.ThreadPoolExecutor(...).submit(asyncio.run,
   coro).result()`), safe regardless of the calling thread's own
   event-loop state, entirely inside `skill_tools.py` (in this story's
   own named file scope) — no edit to `knowledge_bootstrap.py`,
   `agents_router.py`, or `skills_router.py` needed.
2. **A genuine circular import** (`skill_tools → knowledge_bootstrap →
   skill_registry → skill_tools`, since `skill_registry.py` already
   imports `skill_tools` and `knowledge_bootstrap.py` already imports
   `skill_registry`) — resolved with a deferred, function-body import of
   `knowledge_bootstrap` inside `build_knowledge`'s own handler, rather
   than at `skill_tools.py`'s module top level.
3. **Disclosed, NOT fixed here (genuinely out of this story's own named
   file scope):** `build_knowledge` invoked via the chat/direct-trigger
   dispatch fork (`agents_router.py`'s own `_invoke_capability` helper,
   already built by `REQ-SB-39-US-01-T07`) will append a second, generic
   history entry on top of `bootstrap_agent_knowledge`'s own internal
   one — `_invoke_capability`'s existing result-shape translation does
   not forward a `"history_recorded"` key through to
   `trigger_action`/`chat()`'s own post-dispatch history-append check.
   `T02`'s own Approve-endpoint branch DOES honor this flag (in scope,
   fixed there). Low real-world severity today — `compass-expert` carries
   a standing "stays Autonomous" convention (`REQ-SB-36-US-02`), so this
   surfaces only as a cosmetic duplicate history line on an Autonomous
   agent's own chat/direct invocation, never a security or
   approval-bypass issue. **Suggested fast-follow (not this story's own
   job):** a one-line addition to `_invoke_capability`'s translated dict
   (`"history_recorded": result.get("history_recorded", False)`) —
   `trigger_action`/`chat()`'s existing check already does the rest.

**What to do now:** review `ADR-029` (already queued) together with `T01`
–`T04` above and the 3 findings just disclosed; approve, or reset this
story's `status:` to `Draft` to redo if any finding needs a different
resolution (in particular, whether the `_invoke_capability` fast-follow
should be pulled into this story's own scope now rather than deferred).
→ `REVIEW-QUEUE.md` (same combined `REQ-SB-39-US-01 + REQ-SB-39-US-02`
entry, updated with this pass).

**Update, 2026-08-14 (`/implement-sprint SPRINT-031` — coder).** All 4
tasks (`T01`–`T04`) built and verified live against the real backend,
real Outlook/Compass, and the real vault. All 8 locked ACs
(`AC-01`…`AC-08`) confirmed live, including the operator-directed
highest-risk check (a real migrated mutating Skill, `run_capture_now`,
under Supervised mode creates a real Pending Approval record in <0.01s
rather than executing immediately) and the full real-capture round trip
(Autonomous execution, Supervised defer, Approve → the same real handler
actually running). `status: Ready → Done`. `gate:` stays `flagged` — the
same already-disclosed `ADR-029`-creation breadcrumb from `/plan-tasks`,
plus one new, purely informational live finding from `T03` (a real,
unrelated, already-running stray dev-server process independently
created its own real background-triggered pending-approval record during
live testing — disclosed, not silently resolved; see `T03`'s own
Implementation Log and the `REVIEW-QUEUE.md` entry). Nothing about this
finding weakens or contradicts any locked AC.
