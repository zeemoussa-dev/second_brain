---
id: REQ-SB-36-US-02
title: Agent knowledge bootstrapping via delegated research — end-to-end Hub-routed chain (Research Expert to Vault Filing Expert), piloted by the Compass Expert
requirement_ids: [REQ-SB-36]
requirement_section: "REQ-SB-36: Agent Knowledge Bootstrapping via Delegated Research"
phase: P1
status: In Progress
gate: flagged
gate_reason: "Both of this story's own PRE-EXISTING flagged triggers (ADR-023 review; the decomposer's own granular-task-scheduling judgement call) are already Approved/Confirmed per REVIEW-QUEUE.md (2026-08-12 entries) — not reopened here. gate stays flagged solely for NEW coder-level trigger-8 findings from this SPRINT-024 build pass: two scope-internal reconciliations logged in T02/T03's own Implementation Logs (an honest-failure try/except; agents_router.py's dispatch generalized via a new sibling async path). T01/T02/T03 are Done and live-verified; T04 (AC-03) remains Draft/blocked on REQ-SB-29-US-01's own decomposition (ESC-018, still Open) — story stays In Progress, not Done, until T04 can be built."
sprint: SPRINT-024
created: 2026-08-12
updated: 2026-08-13
---

# REQ-SB-36-US-02 — Agent knowledge bootstrapping via delegated research — end-to-end Hub-routed chain (Research Expert to Vault Filing Expert), piloted by the Compass Expert

## Story

**As a** Second Brain user
**I want** to stand up a brand-new, empty Expert agent for a subject I care
about (e.g. Compass) and have it autonomously build its own knowledge —
asking its own Section's Hub for help, which finds a Research Expert to
gather real information, which is then filed into the vault by the Vault
Filing Expert — with no approval needed at any step, except the one case
where the Vault Filing Expert proposes a wholly new top-level vault area
**So that** I can bootstrap a genuinely useful expert agent for a new
subject without manually researching and filing every piece of its
starting knowledge myself, while still keeping a meaningful say over the
rare, structurally bigger decision

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-36: Agent Knowledge Bootstrapping
  via Delegated Research* — "A new agent that starts with no knowledge of
  its assigned subject can build that knowledge by delegating: it asks its
  own Section's Hub for help, which routes (via `REQ-SB-20`'s
  cross-section mechanism) to find a Research Expert; the Research Expert
  gathers information — from documents the user supplies and from its own
  real web research — and hands the result to the Vault Filing Expert
  (`REQ-SB-35`), which decides correct tags/placement per the vault's own
  design methodology — an existing category if one genuinely fits, a new
  one if it doesn't. The whole chain runs end-to-end without requiring
  approval at any step. Once a new agent has been bootstrapped this way,
  more source material can be added later (e.g. a pricing spreadsheet, an
  unreleased-feature document) via file upload (`REQ-SB-28`), following
  the same Vault Filing Expert step." Acceptance: "A newly created, empty
  Expert agent can, without manual intervention, have its own Section's
  Hub route a help request across Sections to find a Research Expert; the
  Research Expert produces real information about the Expert's assigned
  subject (from supplied documents and/or real web research); the result
  is filed into the vault by the Vault Filing Expert with correct
  tags/placement; the entire sequence completes without pausing for
  approval; the resulting vault content is available for the
  newly-expert agent to draw on afterward."
- **PRD breadcrumb (2026-08-12, operator-authored, cited verbatim), the
  worked business example this whole requirement is built from:** "I need
  to build a Compass Expert who in the beginning will be empty in order to
  build data — it needs to talk to the Tech Manager to talk to the
  Managers to find a Research Expert. The Research Expert will go and do
  research for Compass basic info that can make the agent an expert in
  Compass, then ask my Vault Expert to know where it should store the
  info, then store it in the Knowledge Hub with the right tags... more
  info will need to be added from other systems — an Excel file for
  pricing, or new features that are still not public yet."
- **Resolved directly, operator-confirmed, same date:** "Manager" is the
  existing Hub concept (`REQ-SB-18`/`REQ-SB-20`), not a new agent tier —
  this story reuses `REQ-SB-20-US-01`'s own Hub-to-Hub cross-Section
  routing mechanism as-is, no new routing concept.
- **Updated 2026-08-12 — the chain's autonomy is now confirmed two-tier,
  not uniform.** The PRD's own text now states directly: "The whole chain
  runs fully autonomously end-to-end **except the one new-top-level-
  vault-area exception noted in REQ-SB-35** [`REQ-SB-35-US-01`'s own
  Tier-2 approval gate] — the operator reviews the rest of the resulting
  vault content after the fact, not mid-chain." This story's own
  Acceptance Criteria (below) are updated to reflect this: the delegation
  chain (Hub routing → Research Expert) always runs autonomously, and the
  Vault Filing Expert's own placement step is autonomous **unless** it
  determines a genuinely new top-level vault area is needed, in which case
  only that one step pauses (Scenario 2). Every agent in the chain still
  runs in Autonomous working mode (`REQ-SB-21`/`ADR-020`, Done) — the
  Tier-2 pause is a scoped, requirement-level exception applied to one
  action type, not a working-mode change (see `REQ-SB-35-US-01`'s own
  Context for the full reasoning).
- **Resolved 2026-08-12, operator-directed — REQ-SB-35's own
  placement-mechanism fork, inherited here, is now settled ("This is an
  Agent"):** the Vault Filing Expert is a distinct agent, reached via
  `REQ-SB-20`'s Hub routing — this story's own delegation chain (Scenario
  1) composes two Hub-routed hops (Expert → Research Expert, and Research
  Expert → Vault Filing Expert), both using the same, now-uniform
  mechanism, not two different mechanisms.
- **Resolved by direct precedent, not a guess — how a brand-new, empty
  Expert agent actually gets created and assigned:** `app/business/
  agent_registry.py`'s `AGENTS` dict is deliberately, explicitly static
  and hardcoded (`ADR-011` point 2 — "agent identity/type/actions stay
  hardcoded," never made runtime-mutable). Every existing story that
  touches an agent's own configuration (Section, Provider, Keywords,
  Working mode, and Vault Scope once `REQ-SB-29` ships) adds a *mutable
  property* to an already-hardcoded agent identity — none of them creates
  a brand-new agent identity at runtime. Applying this same,
  already-`Accepted` precedent directly: standing up a new Expert agent
  (the Compass Expert pilot) is a **code-level addition** — a new entry
  added to `agent_registry.AGENTS` (deployed as ordinary code, exactly
  like every one of the 5 existing agents), then configured via the
  already-built Settings surface (Section/Keywords/Working-mode/Provider/
  and, once it ships, Vault Scope) exactly like any existing agent — not a
  new runtime "create agent" UI flow.
- **Resolved directly from the PRD's own updated Acceptance text — what
  "the agent is now an expert" concretely means:** "the resulting vault
  content is available for the newly-expert agent to draw on afterward"
  maps directly onto `REQ-SB-29`'s own mechanism (agent-to-tag/folder
  vault scope, plus scope-bounded retrieval). "Expert" status is resolved
  as: the newly-bootstrapped agent has a `REQ-SB-29` vault-scope
  assignment covering wherever the Vault Filing Expert actually filed the
  gathered content, so it can retrieve and use that content on request. No
  separate "completion signal" concept is introduced. Scenario 3 below is
  written to compose with `REQ-SB-29`'s own mechanism, not to assume it
  has already shipped — the same "don't assume a still-unbuilt sibling has
  shipped" technique `REQ-SB-28-US-01` already used for its own `REQ-SB-25`
  dependency.
- **Resolved directly from the PRD's own text — the initial bootstrap does
  not require document supply:** the Acceptance text says "from supplied
  documents *and/or* real web research" (either counts), and the
  requirement's own narrative text frames file-upload-based additional
  material as something added "*later*... via file upload (`REQ-SB-28`),
  following the same Vault Filing Expert step" — explicitly additive/
  later, not a precondition of the initial bootstrap. This story's own
  initial-bootstrap scenario (Scenario 1) is scoped to real web research
  only (via `REQ-SB-36-US-01`'s new skill); document-supplied research is
  explicitly deferred to whenever `REQ-SB-28` ships.
- **Resolved by direct precedent — how the initial bootstrap request is
  triggered.** "Without manual intervention" (the Acceptance text's own
  words) describes what happens *after* the delegation chain starts, not
  that the very first trigger is spontaneous/automatic. Every existing
  action in this codebase is triggered by an explicit user ask (a chat
  trigger phrase or a direct Available-Actions button, per `ADR-011`);
  Autonomous working mode's own definition ("runs on its own... doesn't
  need anything") is about not needing *approval* once running, not about
  self-initiating unprompted. The bootstrap sequence is triggered by the
  user asking the newly created Expert agent to build its knowledge — a
  chat message or a new declared action on that agent — after which the
  chain runs to completion with no further approval needed (Tier-1 case)
  or pauses once at the Vault Filing Expert's own Tier-2 gate (Scenario 2).

## Acceptance Criteria

<!-- Untagged Gherkin — the decomposer authors final wording and assigns
AC-IDs at /plan-tasks. Happy path (the Compass pilot, general-purpose
wording, Tier 1) first, then the Tier-2 exception composed through the
whole chain, then the "draw on afterward" composition with REQ-SB-29, then
honest no-match/no-result edge cases, then a second-subject case proving
this is a general capability, not Compass-specific code. Do NOT add
AC-IDs — the decomposer assigns them at /plan-tasks. -->

### Scenario 1: A newly created, empty Expert agent bootstraps its own knowledge end-to-end, without approval (Tier 1)

```gherkin
Given a newly created Expert agent exists (e.g. the Compass Expert),
    assigned to a Section, with no vault content of its own yet
  And every agent in the delegation chain is in Autonomous working mode
  And the gathered research fits an existing vault category, or at most a
    new tag/subfolder within an existing top-level area (Tier 1, per
    REQ-SB-35-US-01)
When the user asks the newly created Expert agent to build its own
    knowledge (a chat message or a direct action, per this codebase's
    existing action-trigger convention)
Then the request is routed, via cross-Section Hub-to-Hub routing
    (REQ-SB-20-US-01), from the Expert agent's own Section Hub to a
    Research Expert agent
  And the Research Expert gathers real information about the Expert's
    assigned subject via real web research (REQ-SB-36-US-01)
  And the Research Expert hands the gathered result to the Vault Filing
    Expert (REQ-SB-35-US-01), which determines placement/tags per the
    vault's own design methodology and writes it
  And the whole sequence completes without pausing for approval at any
    step
```
<!-- AC-ID: REQ-SB-36-US-02-AC-01 -->

### Scenario 2: The chain pauses only at the one architecturally-exempted step — a new top-level vault area proposal (Tier 2)

```gherkin
Given the delegation chain has run (Hub routing, then the Research
    Expert's real web research have both already completed autonomously)
  And the Vault Filing Expert determines the gathered content requires a
    genuinely new top-level vault area (not an existing one, not a
    smaller tag/subfolder addition)
When the Vault Filing Expert reaches that placement decision
Then only that one step pauses for the operator's explicit approval, per
    REQ-SB-35-US-01's own Tier-2 behavior — every other step in the chain
    has already completed
  And the content is filed, and the new area created, only after the
    operator approves it
```
<!-- AC-ID: REQ-SB-36-US-02-AC-02 -->

### Scenario 3: The newly-expert agent can draw on the filed content afterward

```gherkin
Given the delegation chain in Scenario 1 (or Scenario 2, once approved)
    has completed and real content has been filed into the vault
When the newly-expert agent's own vault scope (REQ-SB-29) is set to cover
    wherever the content was filed
Then the agent can retrieve and use that filed content on request, per
    REQ-SB-29's own retrieval mechanism
```
<!-- AC-ID: REQ-SB-36-US-02-AC-03 -->

### Scenario 4: No agent in any other Section has matching Research Expert keywords

```gherkin
Given the Expert agent's own Section Hub is asked for help
  And no agent in any other Section has keywords matching a research need
When the request is routed
Then the routing decision honestly reports no match, per REQ-SB-20-US-01's
    own existing no-match behavior
  And the delegation chain does not proceed to a fabricated or guessed
    research result
```
<!-- AC-ID: REQ-SB-36-US-02-AC-04 -->

### Scenario 5: A step in the chain honestly reflects failure or uncertainty rather than fabricating a result

```gherkin
Given the delegation chain is in progress (e.g. the Research Expert's web
    search returns nothing relevant, or the Vault Filing Expert cannot
    confidently determine a Tier-1 placement)
When that step completes
Then the chain honestly reflects the failure or uncertainty at that step
    (per REQ-SB-36-US-01 Scenario 3's honest-no-results behavior, and
    REQ-SB-35-US-01 Scenario 6's honest-uncertainty-disclosure behavior)
  And no step fabricates a confident result to keep the chain moving
```
<!-- AC-ID: REQ-SB-36-US-02-AC-05 -->

### Scenario 6: The same chain runs for any newly-bootstrapped Expert agent, not just Compass

```gherkin
Given a different newly created, empty Expert agent exists, assigned a
    different subject
When the user asks that agent to build its own knowledge
Then the same delegation chain (Hub routing, then a Research Expert, then
    the Vault Filing Expert, including its own Tier-1/Tier-2 behavior)
    runs for it, unmodified — confirming this is a general capability,
    not Compass-specific behavior
```
<!-- AC-ID: REQ-SB-36-US-02-AC-06 -->

## Affected Screens

- **None new.** Once the Compass Expert (or any other newly-created Expert
  agent) exists in the registry, its own Settings/Available-Actions/Chat/
  Communication-History surfaces reuse the already-approved
  `html-prototype/agents-map.html` agent detail panel exactly as-is. A new
  "build my knowledge" action on the new agent's own Available Actions
  list uses the same already-approved Available Actions UI shape any
  existing agent's actions already use. Scenario 2's Tier-2 pause reuses
  the already-approved Pending Approvals surface (see
  `REQ-SB-35-US-01`'s own `## Affected Screens`) — no new screen region
  required for this story specifically.

## Dependencies

- **Blocked by:** `REQ-SB-20-US-01` (`status: Ready`, not yet `Done`/
  built) — the Hub-to-Hub cross-Section routing mechanism this chain's
  first hop needs.
- **Blocked by:** `REQ-SB-35-US-01` (`status: Draft`, `gate: clear`, not
  yet `Ready`/built) — the Vault Filing Expert this chain's final hop
  needs, including its own Tier-1/Tier-2 behavior (Scenario 2).
- **Blocked by:** `REQ-SB-36-US-01` (`status: Draft`, `gate: clear`, not
  yet `Ready`/built) — the Research Expert's real web-search capability
  this chain's middle hop needs.
- **Related to, needed for Scenario 3 only:** `REQ-SB-29-US-01` (`Draft`,
  `gate: clear`, not yet `Ready`/built) — the "draw on afterward"
  mechanism; Scenario 3 is written to compose with it once it ships,
  mirroring `REQ-SB-28-US-01`'s own precedent — Scenarios 1/2 (the
  delegation/filing chain itself) do not depend on it.
- **Related to, explicitly deferred:** `REQ-SB-28-US-01` (`Draft`, `gate:
  flagged`) — the later file-upload path for additional source material,
  out of scope for this story's own initial-bootstrap scenario.
- **Satisfied already:** `REQ-SB-18-US-01` (Done) — Sections exist;
  `REQ-SB-21-US-01`/`ADR-020` (Done) — Autonomous working mode and the
  Pending-Approval mechanism Scenario 2 reuses both already exist;
  `REQ-SB-19-US-01` (Done) — Provider CRUD, needed for
  `REQ-SB-36-US-01`'s own real-client work.
- **Related to:** `ADR-011` point 2 — the "agent identity stays hardcoded"
  precedent this story's own "new agent = code-level addition" resolution
  directly reuses.
- **Sequencing note (recorded, not a gate blocker — mirrors
  `REQ-SB-20-US-01`'s own precedent for its then-unmet `REQ-SB-18-US-01`
  dependency):** this story's own real work cannot begin until
  `REQ-SB-20-US-01`, `REQ-SB-35-US-01`, and `REQ-SB-36-US-01` are
  themselves built — a `/plan-sprints`-time sequencing concern
  (`depends_on_sprints`, Pipeline.md hard rule 7), not a reason to keep
  this story's own, already-unambiguous spec `gate: flagged`.
- **External:** none new beyond the stories above.

## Constraints

- Every agent in the delegation chain (the newly-created Expert, the
  Research Expert, and the Vault Filing Expert) must be in Autonomous
  working mode for this specific flow — reuses `REQ-SB-21`/`ADR-020`'s
  existing per-agent setting, no new mechanism.
- Standing up a brand-new Expert agent (e.g. the Compass Expert) is a
  **code-level addition** to `agent_registry.AGENTS` (mirrors `ADR-011`
  point 2's already-`Accepted` "agent identity stays hardcoded"
  precedent) — not a new runtime "create agent" UI flow.
- **The chain is autonomous end-to-end EXCEPT the one Tier-2 exception**
  (a genuinely new top-level vault area, per `REQ-SB-35-US-01`) — any
  honest failure/uncertainty at a Tier-1 step (Scenario 5) is disclosed in
  the result, not itself surfaced as a mid-chain approval gate; only the
  Tier-2 case actually pauses.
- The initial bootstrap's research source is real web research only
  (`REQ-SB-36-US-01`); document-supplied research (`REQ-SB-28`) is
  explicitly later, additive work.
- Reuses `REQ-SB-20-US-01`'s Hub-routing mechanism, `REQ-SB-35-US-01`'s
  placement/tagging/write mechanism (including its own Tier-1/Tier-2
  split), and `REQ-SB-36-US-01`'s web-research skill exactly as those
  stories build them — this story does not reimplement or duplicate any
  of their own mechanisms.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-36-US-02-T01 | backend | New `"compass-expert"` pilot Expert agent entry + `"build_knowledge"` action definition (`mutates: True`, data only) | `business/agent_registry.py` | `REQ-SB-36-US-02-T01-compass-expert-agent-and-build-knowledge-action.md` |
| REQ-SB-36-US-02-T02 | backend | New `knowledge_bootstrap.py` — `bootstrap_agent_knowledge(agent_id, subject)`: Hop 1, Autonomous-mode check, research, Hop 2, Tier-1/Tier-2 filing dispatch, honest failures | `agent_orchestration/knowledge_bootstrap.py` | `REQ-SB-36-US-02-T02-knowledge-bootstrap-orchestration.md` |
| REQ-SB-36-US-02-T03 | backend | `agents_router.py` — `_ACTION_HANDLERS` dispatch entry, real end-to-end chat/direct trigger | `api/agents_router.py` | `REQ-SB-36-US-02-T03-build-knowledge-action-dispatch.md` |
| REQ-SB-36-US-02-T04 | backend | Scenario 3 ("draw on afterward") composition/regression check — **⚠️ BLOCKED, do not start** | none in this story (cross-story composition only) | `REQ-SB-36-US-02-T04-draw-on-afterward-composition-check.md` |

`depends_on` graph (acyclic): `T01: [REQ-SB-21-US-01-T09]`,
`T02: [REQ-SB-36-US-02-T01, REQ-SB-20-US-01-T05, REQ-SB-21-US-01-T02, REQ-SB-36-US-01-T05, REQ-SB-35-US-01-T02, REQ-SB-35-US-01-T03]`,
`T03: [REQ-SB-36-US-02-T01, REQ-SB-36-US-02-T02]`, `T04: []` (deliberately
empty — see `## Notes`, mirrors `ESC-011`'s established "blocked task"
precedent exactly). Six real cross-story edges on `T01`/`T02` alone, all
pointing at real, `status: Ready` task files (no placeholder, no
fabricated id) — `REQ-SB-20-US-01-T05` (Hub routing), `REQ-SB-21-US-01-T02`
(working-mode check) and `-T09` (mutates classification),
`REQ-SB-36-US-01-T05` (skill invocation with args), `REQ-SB-35-US-01-T02`/
`T03` (Tier-1/Tier-2 filing). `T04` is the one exception — see `## Notes`
for why it cannot yet be given a real edge.

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Building the Hub-routing mechanism itself** — `REQ-SB-20-US-01`'s own
  scope.
- **Building the Vault Filing Expert's own placement/tagging/write logic
  and its own Tier-1/Tier-2 behavior** — `REQ-SB-35-US-01`'s own scope.
- **Building the web-research skill itself, or the real Anthropic
  Provider integration behind it** — `REQ-SB-36-US-01`'s own scope.
- **Building/extending vault-scope assignment or retrieval** —
  `REQ-SB-29-US-01`'s own scope; this story's Scenario 3 composes with it,
  does not rebuild it.
- **Document-supplied initial or later research material via file upload**
  — `REQ-SB-28`'s own scope, explicitly deferred.
- **A new runtime "create agent" UI flow** — this story treats new-agent
  creation as a code-level addition (see Constraints), not a product
  feature of its own.
- **Any approval/review UI beyond REQ-SB-35-US-01's own Tier-2 gate** —
  no other mid-chain approval is introduced.

## Notes

**Prototype parity:** not applicable — this story requires no new screen
region (see `## Affected Screens`).

**Why `gate: clear` — re-checked against every MUST-FLAG trigger, not
assumed:**

1. **Material assumptions, made and disclosed, not hidden.**
   New-agent-creation-is-code-level and bootstrap-trigger-is-user-initiated
   are both resolved via direct, singular, unambiguous precedent
   (`ADR-011` point 2; the existing action-trigger convention already used
   by every other action in this codebase) — recorded plainly in Context,
   not silently baked into the Gherkin. This is the same class of
   safe-precedent resolution `REQ-SB-29-US-01` already used without
   counting it as an unresolved assumption.
2. `REQ-SB-36` is not marked `<!-- Draft -->`/unfinalised — it carries a
   "Scope resolved" breadcrumb whose own named sub-questions relevant to
   this story are now resolved.
3. N/A directly (architect/ADR trigger).
4. No new `ESCALATIONS.md` entry from this story itself. `ESC-015`/
   `ESC-016` (opened by this story's own sibling stories) are resolved by
   those stories' own 2026-08-12 updates, which this story's scenarios now
   compose with directly (Scenario 2).
5. **Re-checked deliberately against the cross-sprint-dependency clause,
   not skipped.** This story depends on three other stories that are not
   `Done` yet. Per `REQ-SB-20-US-01`'s own direct, on-point precedent —
   it stayed `gate: flagged` for its own design/ADR reasons while its real
   `Blocked by: REQ-SB-18-US-01 (Ready, NOT yet Done)... Not satisfied yet`
   dependency was recorded plainly in `## Dependencies` without that fact
   alone driving the gate — an ordinary, real, forward `Blocked by`
   dependency on another not-yet-`Done` story is not, by itself, treated
   as the kind of "cross-sprint dependency had to be introduced" this
   project's own established practice reserves for a genuinely blocking
   decomposer/product-owner-level finding (e.g. `REQ-SB-27-US-01`'s own
   `ESC-011`, where a task-level `depends_on` edge literally could not be
   wired to a real task ID that didn't exist yet — a materially different,
   concrete technical blocker, not present here). This story's own spec is
   fully unambiguous; the sequencing itself is `/plan-sprints`'s ordinary
   job (Pipeline.md hard rule 7), recorded as a Note in `##
   Dependencies`, not a reason to keep this story's own gate flagged. Not
   oversized otherwise — comparable in shape to other composition stories
   in this project.
6. N/A (coder trigger).
7. No new contradictory inputs — the contradictions this story previously
   inherited (`ESC-015`/`ESC-016`) are resolved at their own originating
   stories.
8. **No remaining multiple-equally-valid-options fork.** `REQ-SB-35-US-01`'s
   own agent-vs-skill fork, previously inherited here, is now resolved
   (distinct agent, confirmed).

`gate: clear` 2026-08-12. `REVIEW-QUEUE.md`'s combined entry for this
story is updated to reflect resolution. This story is ready for
`/plan-tasks`, sequenced behind `REQ-SB-20-US-01`/`REQ-SB-35-US-01`/
`REQ-SB-36-US-01` actually shipping (a `/plan-sprints`-time concern, not a
gate blocker).

**Scoping decision — why this stays a separate story from
`REQ-SB-36-US-01` (the web-research skill), unchanged from the original
spec pass.** Applying this project's standing "no independent value
alone" test: the web-research skill has real, demonstrable value on its
own (any agent granted access can invoke it), while the end-to-end
delegation chain has no meaningful way to be demonstrated without a
working web-research skill *and* a working Vault Filing Expert *and*
working Hub-to-Hub routing — three genuinely separable capabilities this
story composes, not reimplements.

**Architecture pass (2026-08-12, `/plan-tasks` step 1 — architect).**
`ADR-023` written (new, appended to `Implementation/Architecture/ADR.md`).
**The core finding this pass surfaced, confirmed by direct reading of
`REQ-SB-20-US-01`'s own file, not assumed:** `ADR-017`'s already-real
Hub-routing node only ever *discovers* a candidate agent — "it does not
itself invoke any action on the target agent... no story yet lets a
routed request actually execute anything on its target" (that story's own
words, resolving `ESC-013`). This story is exactly the first to need real
invocation, so `ADR-023` designs it: a new `app/business/agent_
orchestration/knowledge_bootstrap.py::bootstrap_agent_knowledge(agent_id,
subject)` composes, deterministically (not via a second layer of
recursive, model-driven agent-to-agent conversation): Hop 1 —
`graph.route_cross_section_request(agent_id, need_description=...)`
(`ADR-017`, as-is) finds the Research Expert; a working-mode check gates
unattended completion; `skill_registry.invoke_skill(research_expert_id,
"web-research", {"query": subject})` (`ADR-022`) gathers real content;
Hop 2 finds the Vault Filing Expert; `vault_filing_expert.
determine_placement_and_file(...)` (`ADR-021`) files it (Tier 1) or defers
to approval (Tier 2). Triggered via a new `"build_knowledge"` action on a
new pilot Expert agent (e.g. `"compass-expert"`, a plain code-level
`agent_registry.py` addition, per this story's own already-resolved
"code-level addition" Constraint) — dispatched through the existing
`_ACTION_HANDLERS`/`_invoke_action` funnel (`ADR-011`), no new endpoint.
Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-023`;
`architecture.md` → "Delegated knowledge-bootstrap orchestration."

**Two real, load-bearing findings, not silently patched:** this story's
own `## Dependencies` above lists `REQ-SB-21-US-01`/`ADR-020` under
"Satisfied already." Direct inspection during this pass found this
**false** — `REQ-SB-21-US-01` is `status: Draft`, `gate: flagged`, its
decomposer has not re-run since `ADR-020`, and zero of its 8 tasks have
been built (confirmed against the real `src/backend` source tree: no
`working_mode_registry.py`, no `pending_approval_registry.py`, no
`pending_approvals_router.py`). This story's own chain genuinely needs
**both** halves of that unbuilt mechanism — the Autonomous-mode check
(this story's own Constraint) and Tier 2's own resolution (inherited from
`ADR-021`). Recorded as `ESCALATIONS.md` → `ESC-017` (`Open`), plus a
`REVIEW-QUEUE.md` pointer, mirroring `ESC-011`'s own precedent: the
decomposer's own next pass should individually flag whichever task
implements `knowledge_bootstrap.py`'s working-mode check and Tier-2
resolution with `depends_on: []` and an explicit "blocked, do not start"
note, rather than fabricate a task-id reference.

**Architecture scope (bounds the decomposer/coder for this story):**
`Implementation/Architecture/architecture.md` → "Delegated knowledge-
bootstrap orchestration," "Section-Hub cross-Section routing" (for
`route_cross_section_request`, read-only composition), "Vault Filing
Expert" (for `determine_placement_and_file`, read-only composition), and
"Real Anthropic Provider integration & web-research skill" (for
`invoke_skill`, read-only composition). Concretely: `app/business/
agent_orchestration/knowledge_bootstrap.py` (new), `app/business/
agent_registry.py` (one new pilot Expert agent entry + one new
`"build_knowledge"` action definition, data only), `app/api/
agents_router.py`'s `_ACTION_HANDLERS` (one new dispatch entry, no
structural change). `app/business/agent_orchestration/graph.py` (the
`route_cross_section_request` function itself, unmodified — read-only
composition), `app/business/vault_filing_expert.py` and `app/business/
skill_registry.py` (unmodified — read-only composition). This story does
not itself build or modify `REQ-SB-20-US-01`'s routing node,
`REQ-SB-35-US-01`'s placement mechanism, `REQ-SB-36-US-01`'s skill/
Provider mechanism, or `REQ-SB-21-US-01`'s working-mode/Pending-Approvals
mechanism — it composes all four exactly as those stories build them,
per this story's own Constraints. Full reasoning: `Implementation/
Architecture/ADR.md` → `ADR-023`.

**Sequencing, restated plainly:** this story's own real build order is
now `REQ-SB-20-US-01` → `REQ-SB-35-US-01` → `REQ-SB-36-US-01` →
`REQ-SB-21-US-01` → this story — the addition of `REQ-SB-21-US-01` to
that chain (beyond the three already named in this story's own
Dependencies) is this architecture pass's own finding, not a new product
decision; it is a `/plan-sprints`-time `depends_on_sprints` concern once
all four are individually `Ready`, not a reason to re-flag this story's
own spec.

Gate stays `flagged` per this project's own convention — the decomposer
still runs in this same `/plan-tasks` pass (Pipeline.md's "do NOT halt the
stage" rule); the human reviews `ADR-023` and the resulting tasks together.
A `REVIEW-QUEUE.md` pointer has been added.

**Decomposition pass (2026-08-12, `/plan-tasks` step 2 — decomposer).**
All 6 untagged Gherkin scenarios tightened for buildability (wording only)
and locked as `REQ-SB-36-US-02-AC-01` through `AC-06`. 4 tasks created:
`T01` (the new pilot agent + action), `T02` (the orchestration module
itself — `AC-02`, `AC-04`, `AC-05`, `AC-06`), `T03` (the real
chat/direct-trigger dispatch — `AC-01`), and `T04` (`AC-03`, see below).

**`ESC-017`'s own "wire the real ids in" step is now done for this
story's Autonomous-mode-check and Tier-2 halves.** `REQ-SB-21-US-01`'s
own decomposer pass has since run (9 tasks, all `Ready`) and named the
exact ids to use in its own `## Notes`: `T02` for the Autonomous-mode
check (wired onto `T02` here), `T03`/`T06` for Tier 2's own resolution
(composed via `REQ-SB-35-US-01-T02`/`T03`, which themselves depend on
`REQ-SB-21-US-01-T03`/`T06` directly — this story does not need a second,
redundant direct edge onto them, since it only ever calls
`vault_filing_expert.determine_placement_and_file(...)` and never touches
`pending_approval_registry`/`pending_approvals_router` itself, per this
story's own Constraints "does not reimplement or duplicate"). No
placeholder `depends_on: []` remains for this half of `ESC-017`.

**A second, real, currently-unwireable dependency — genuinely new to this
pass, not inherited from `ESC-017` — logged as `ESCALATIONS.md` →
`ESC-018` (new).** `AC-03` (Scenario 3, "the newly-expert agent can draw
on the filed content afterward") composes entirely with `REQ-SB-29-US-01`'s
own vault-scope-assignment/retrieval mechanism — this story's own text is
explicit that Scenarios 1/2 (the delegation/filing chain itself) do not
depend on it, only Scenario 3 does. Direct inspection during this pass
confirmed `REQ-SB-29-US-01` is `status: Draft`, `gate: clear`, and has
**not been decomposed at all** — zero task files exist
(`Implementation/Tasks/REQ-SB-29-US-01-T*.md` — none found), unlike
`REQ-SB-21-US-01` (which this same session's earlier decomposer pass
already ran). There is no real task id anywhere to wire `AC-03`'s own
verification onto. Mirroring `ESC-011`'s established precedent exactly (an
individually-flagged task, `depends_on: []`, a prominent "⚠️ BLOCKED — do
not start" section, not a fabricated task id and not silent omission):
`T04` is created to hold `AC-03`'s own eventual verification, left fully
blocked. `T04` itself has no `Files to Modify` in this story — Scenario 3's
own "When"/"Then" clauses describe `REQ-SB-29`'s own mechanism entirely
(setting vault scope, retrieval), not new code this story builds; `T04`'s
own future work, once `REQ-SB-29-US-01` ships, is a pure regression/
composition check that this story's own filed content (from `T02`/`T03`)
is retrievable through `REQ-SB-29`'s own real mechanism.

**A genuine judgement call, flagged rather than silently resolved either
way (trigger 8):** `ESC-011`'s own precedent (`REQ-SB-27-US-01`) held the
*entire* story at `Draft` because one of its 4 tasks was blocked, even
though that story's own literal `(a)`/`(b)`/`(c)` Ready-criteria were
arguably satisfied (every AC locked, every locked AC tagged, `depends_on`
acyclic). Applying that same full-lockstep choice here would hold back 3
of 4 tasks — including `T01`/`T02`/`T03`, which have real, `Ready`
cross-story dependencies and zero blocking issue of their own — behind one
scenario (`AC-03`) that needs zero new code in *this* story at all. This
decomposer instead advances the **story** to `Ready` (all `(a)`/`(b)`/`(c)`
criteria are genuinely met: `AC-03` is locked, `T04` carries its tagged
step, `depends_on` is acyclic) while individually holding **only `T04`**
at `status: Draft` with its own explicit `gate: flagged` and "⚠️ BLOCKED —
do not start" section — `T01`/`T02`/`T03` are written directly at
`status: Ready` (ordinary lockstep) since none of them is actually
blocked. This diverges from `ESC-011`'s own full-story-Draft choice; the
human should confirm this more granular approach is preferred going
forward (recorded in `REVIEW-QUEUE.md`, not silently adopted as the new
default).

`depends_on` graph across all 4 tasks plus cross-story edges (acyclic):
`T01: [REQ-SB-21-US-01-T09]`,
`T02: [T01, REQ-SB-20-US-01-T05, REQ-SB-21-US-01-T02, REQ-SB-36-US-01-T05, REQ-SB-35-US-01-T02, REQ-SB-35-US-01-T03]`,
`T03: [T01, T02]`, `T04: []`. Every locked AC has at least one AC-tagged
step — `AC-01` in `T03`, `AC-02`/`AC-04`/`AC-05`/`AC-06` in `T02`, `AC-03`
in `T04` (blocked, not yet executable, but a real step exists — hard rule
4's letter is satisfied; its spirit is honestly caveated above). `status:
Draft → Ready`. **`gate` stays `flagged`** — this pass added its own new
triggers (a new `ESCALATIONS.md` entry, a genuine judgement call) on top
of the architect's own unresolved `ADR-023` review; `gate_reason` records
all three. A `REVIEW-QUEUE.md` entry has been added for both the new
`ESC-018` finding and the judgement-call confirmation.

**Build pass (2026-08-12/13, `/implement-sprint`, `SPRINT-024`).**
`T01`/`T02`/`T03` built and verified live end-to-end against the real
backend, real vault, and real Compass Provider — see each task's own
Implementation Log for full detail. `AC-01`/`AC-02`/`AC-04`/`AC-05`/
`AC-06` all verified live. Two real, scope-internal reconciliations found
composing around the real, current dependency code (an honest-failure
`try/except` in `knowledge_bootstrap.py` around a real external-API call
that can raise; `agents_router.py`'s dispatch generalized via a new
sibling async path rather than modifying the existing, externally-relied-
upon `_execute_action`) — both logged in their own task's Implementation
Log, no `ESCALATIONS.md` entry (confined to each task's own file, no new
dependency/interface change visible outside it). `T04`/`AC-03` remain
`Draft`/blocked on `REQ-SB-29-US-01`'s own decomposition — `ESC-018`
stays `Open`. Story stays `status: In Progress` (not `Done`) until `T04`
can be built. `SPRINT-024` itself reaches `Done` per its own Definition
of Done, which deliberately scopes only `T01`-`T03` — see the sprint
file's own Retrospective.
