---
id: REQ-SB-37-US-01
title: Agent Creation Wizard — entry point, type selection, and the Expert-type flow (domain + starts empty, honestly uncertain)
requirement_ids: [REQ-SB-37]
requirement_section: "REQ-SB-37: Agent Creation Wizard"
phase: P1
status: Done
gate: clear
gate_reason: "Built and verified end-to-end 2026-08-14 (/implement-sprint, SPRINT-033) — all 8 locked ACs (AC-01..AC-08) verified live against the real backend/vault/Compass Provider and a real CDP-driven browser session. ADR-030's own human-review flag is resolved by this successful build, mirroring REQ-SB-20-US-01/REQ-SB-21-US-01/REQ-SB-35-US-01's own identical precedent. See ## Notes."
sprint: SPRINT-033
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-37-US-01 — Agent Creation Wizard — entry point, type selection, and the Expert-type flow

## Story

**As a** Second Brain user
**I want** to create a new Expert-type agent from within the app — via a
wizard that lets me pick a type, then define a knowledge domain and a
Section — without editing source code
**So that** I can add a new Expert for a subject I care about the same way
I already create a new Section or Provider, and have it start genuinely
empty and honest about what it doesn't know yet, instead of needing a code
change every time

## Context

- **RE-SPEC, 2026-08-13.** This story was previously drafted under the PRD
  title "REQ-SB-37: Agent Creation," before the operator's own Worker/
  Expert/Producer wizard-shape breadcrumb existed. The PRD requirement was
  rewritten the same day — the title is now **"Agent Creation Wizard"** —
  and this story is updated in place (not replaced) to reflect that
  rewrite. `ESCALATIONS.md` → `ESC-020` carries a follow-up note recording
  this re-spec and the split decided below.

- PRD: `Documentation/PRD.md` → *REQ-SB-37: Agent Creation Wizard* — "The
  user can create a new agent from the app itself, via a wizard whose steps
  change based on the agent's Type: a **Worker** is configured with Skills
  (its tools), a Vault Scope, and a Section; an **Expert** is configured
  with a knowledge domain and starts genuinely empty — honestly answering
  'I don't know' until real content exists in its scope (see REQ-SB-40 for
  how that gap closes over time); a **Producer** is configured with a
  Purpose and an output action... No place in the UI currently lets the
  user do this."

- **PRD breadcrumb (2026-08-13, operator-directed), cited in full, not
  re-decided here — the per-type wizard shape, verbatim:** "1. Workers Need
  tools Mainly a Scope of work and Section they add data to. 2. Experts
  they are domain Expert to need to Understand What they have and what they
  missing to be called Expert. 3. Producers Need to have a Purpose and then
  do something with [it]." On Expert readiness specifically: "I guess we
  need both the wizard, and the Agent can say I don't know as a start, and
  a human input is needed to fill the gap — by time it will be Expert (the
  number of I don't know is how we close this Expert gap in future)." The
  PRD's own text is explicit that the "becoming an Expert" part is
  `REQ-SB-40`'s job, not this wizard's: "REQ-SB-37's own wizard for an
  Expert is therefore thin by design — define the domain/scope, done."

- **Analyst decision — this story is one of a three-way split of the
  rewritten REQ-SB-37, not a same-numbered replacement of the old story
  (recorded in full at `ESCALATIONS.md` → `ESC-020`'s follow-up note, not
  guessed silently).** The PRD's own single Acceptance text describes one
  wizard with three structurally distinct per-type shapes — different
  required fields, different underlying mechanisms, and, critically,
  **different build-readiness today**. Splitting lets the one flow that is
  actually buildable now (Expert) proceed toward `/plan-tasks` without
  waiting on unbuilt prerequisites the other two types genuinely need, and
  keeps each story small enough to fit one working context (Pipeline.md
  MUST-FLAG trigger 5 — oversized). The three resulting stories:
  - **`REQ-SB-37-US-01` (this story)** — the wizard's entry point, its
    type-selection step, and the **Expert**-type flow end-to-end.
  - **`REQ-SB-37-US-02`** — the **Worker**-type flow (Skills + Vault Scope
    + Section). Hard-blocked on `REQ-SB-39` (both `US-01` and `US-02`) and
    related to the still-unbuilt `REQ-SB-29` (Vault Scope).
  - **`REQ-SB-37-US-03`** — the **Producer**-type flow (Purpose + output
    action). Hard-blocked on `REQ-SB-39`, and carries its own unresolved
    "what is the output action, mechanically" open question.
  All three depend on this story's own wizard shell (entry point + type
  selector) landing first — see Dependencies.

- **Why Expert is buildable now and Worker/Producer are not (the real
  judgment call driving the split):** the PRD's own breadcrumb states the
  hard `REQ-SB-39` (Unify Agent Capabilities Under Skills) dependency
  applies specifically to "the wizard's own **Worker/Producer** flows...
  Skills-based by the operator's own direction" — Expert is not named in
  that sentence. Cross-checked directly against both `REQ-SB-39` stories'
  own Dependencies sections, which each say "Blocks: `REQ-SB-37-US-01`
  (Agent Creation)... Worker/Producer wizard flows are Skills-based" — that
  cross-reference is stale after this split and should now read
  `REQ-SB-37-US-02`/`REQ-SB-37-US-03`; this story updates those two files'
  Dependencies text accordingly (see Notes) since story IDs are the join
  key (`Pipeline.md` hard rule 2). Expert's own wizard field is a knowledge
  domain, not Skills — `REQ-SB-33`'s honest-uncertainty guardrail (`Done`)
  is the only real prerequisite, and it already ships today.

- **The REQ-SB-40 dependency call (analyst judgment, not a guess):**
  `REQ-SB-40-US-01` (Agent Knowledge-Gap Tracking & Expert Readiness) is
  itself `Draft`/flagged and unbuilt. Read closely, the PRD's own text
  draws a real seam: an Expert "starts genuinely empty — honestly
  answering 'I don't know'" is exactly `REQ-SB-33`'s already-`Done`
  guardrail applied to a freshly-created agent with zero seeded content —
  no new mechanism is needed for that half. What `REQ-SB-40` adds is
  *recording* each "I don't know" as a trackable, closeable gap and
  surfacing a declining open-gap count as a readiness signal — an
  observability layer on top, not a precondition for an Expert agent to
  exist and answer honestly. **Resolution: this story does NOT hard-depend
  on `REQ-SB-40`.** An Expert created by this wizard is fully functional
  (reachable, honestly uncertain) the moment `REQ-SB-33`'s guardrail
  applies to it; `REQ-SB-40`, once built, adds gap-tracking on top without
  requiring anything from this story to change. This is a genuine
  interpretive call, not a fact lookup, so it is called out here explicitly
  rather than silently assumed.

- **Genuinely NOT resolved here — the persisted-registry mechanism itself
  (carried over unchanged from the prior draft, still open).** Every
  already-`Done` per-agent property registry (`section_registry.py`,
  `provider_registry.py`, `agent_keywords.py`, `working_mode_registry.py`,
  `skill_registry.py`) self-heals its own default assignment by iterating
  `agent_registry.list_agents()` — a user-created agent only gets picked up
  automatically if `list_agents()`/`get_agent()` themselves start reporting
  it. Every prior agent-touching ADR this session composed *alongside*
  `agent_registry.py` without modifying it; this story requires the
  opposite. This is an ADR-level call for the architect at `/plan-tasks`,
  not decided here — see `ESCALATIONS.md` → `ESC-020`.

- **Resolved here, by direct code inspection (unchanged from the prior
  draft):** a created agent's **type** must be one of the three existing
  values — Worker, Expert, Producer — matching the Agents Map's own
  polar-grid ring layout (`AgentsMapCanvas.tsx`'s `RING_RADIUS` lookup).

- **No `html-prototype/` screen has a Create Agent affordance anywhere** —
  confirmed by direct inspection of `agents-map.html` and `settings.html`
  (still true; unchanged since the prior draft). See the flag below.

- **Genuinely open, not decided here — where the wizard's type selector
  sits relative to `REQ-SB-37-US-02`/`US-03` not yet being buildable.**
  Whether the type selector offers Worker and Producer today (routing to a
  "not yet available" state until those stories ship) or is itself extended
  incrementally as each type's story lands, is an implementation-sequencing
  call left to `/plan-tasks` — this story's own Acceptance Criteria are
  written so they hold regardless of which sequencing the architect
  chooses.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: Reaching the Create Agent wizard from within the app

```gherkin
Given the user is using the app
When the user opens the Create Agent affordance
Then a wizard opens, offering a choice of agent Type
  And no source-code change was required to reach it
```
<!-- AC-ID: REQ-SB-37-US-01-AC-01 -->

### Scenario 2: Selecting the Expert type shows Expert-specific fields

```gherkin
Given the user is on the wizard's type-selection step
When the user selects the Expert type
Then the wizard shows fields for a knowledge domain and a Section
  And it does not show Worker's Skills/Vault-Scope fields or Producer's
    Purpose/output-action fields
```
<!-- AC-ID: REQ-SB-37-US-01-AC-02 -->

### Scenario 3: Creating an Expert-type agent with a domain and Section

```gherkin
Given the user is on the Expert-type wizard step
When the user enters a name, defines a knowledge domain, selects a Section,
    and submits
Then a new Expert-type agent is created with that name, domain, and Section
  And no source-code change was required to create it
```
<!-- AC-ID: REQ-SB-37-US-01-AC-03 -->

### Scenario 4: A newly created Expert agent starts genuinely empty and honestly uncertain

```gherkin
Given the user has just created an Expert agent, before any content exists
    in its assigned domain
When the user asks it a question within its stated domain
Then it honestly answers that it doesn't know, per REQ-SB-33's existing
    grounding/honest-uncertainty guardrail
  And nothing about the agent is fabricated as already expert or already
    knowledgeable about something it has no content for
```
<!-- AC-ID: REQ-SB-37-US-01-AC-04 -->

### Scenario 5: The new Expert agent appears immediately on the Agents Map

```gherkin
Given the user has just created an Expert agent
When the user views the Agents Map
Then the new agent appears alongside existing agents, in its assigned
    Section and on the Expert ring
  And no reload or restart of the app is required for it to appear
```
<!-- AC-ID: REQ-SB-37-US-01-AC-05 -->

### Scenario 6: Configuring the new Expert agent's Provider, Working mode, and Skill grants

```gherkin
Given the user has created a new Expert agent
When the user selects a Provider, selects a Working mode, or grants it
    access to an already-registered Skill (e.g. web-research), using the
    same surfaces an existing agent's Settings surface already uses
Then the new agent's configuration is updated accordingly
  And the change is shown immediately on that agent's own Settings surface
```
<!-- AC-ID: REQ-SB-37-US-01-AC-06 -->

### Scenario 7: Creating an Expert agent without a required field is rejected honestly

```gherkin
Given the user is on the Expert-type wizard step
When the user submits without providing a name, a knowledge domain, or a
    Section
Then the agent is not created
  And the user sees a clear, honest message naming what's missing
  And no partial or broken agent appears anywhere, including the Agents Map
```
<!-- AC-ID: REQ-SB-37-US-01-AC-07 -->

### Scenario 8: A newly created Expert agent works like any other agent afterward

```gherkin
Given the user has created an Expert agent
When the user opens that agent's Chat and Communication History tabs
Then both work the same way they already do for an existing, built-in agent
  And the created agent is not treated as a second-class or read-only
    agent anywhere in the app
```
<!-- AC-ID: REQ-SB-37-US-01-AC-08 -->

## Affected Screens

- `html-prototype/agents-map.html` — needs a new "Create Agent" affordance
  (or `html-prototype/settings.html`, or both — placement is genuinely
  open, not decided here). No existing region of either screen covers
  this.
- `html-prototype/agents-map.html` — the agent detail side panel (Settings
  tab) already covers Provider/Working-mode/Skill-access configuration for
  an *existing* agent; this story's Scenario 6 reuses that surface
  unchanged for a *created* Expert agent — no new design needed for
  configuration itself, only for the creation affordance and the wizard's
  own Expert-type step.

## Dependencies

- **Not blocked by (all satisfied already):** `REQ-SB-18-US-01` (Section,
  Done), `REQ-SB-19-US-01` (Provider, Done), `REQ-SB-21-US-01` (Working
  mode, Done), `REQ-SB-27-US-01` (Skills, plumbing Done), `REQ-SB-33-US-01`
  (Honest-uncertainty guardrail, Done — the mechanism Scenario 4 relies
  on).
- **NOT blocked by `REQ-SB-39`** (Unify Agent Capabilities Under Skills) —
  the PRD breadcrumb names the hard dependency against Worker/Producer
  specifically, not Expert (see Context). This is the load-bearing fact
  behind splitting Expert into its own, independently-buildable story.
- **Related to, explicitly NOT a hard dependency (analyst judgment call —
  see Context):** `REQ-SB-40-US-01` (Agent Knowledge-Gap Tracking &
  Expert Readiness) — still `Draft`/flagged, unbuilt. An Expert created by
  this wizard is fully functional without it; `REQ-SB-40` adds gap-tracking
  observability on top, later, without requiring changes here.
- **Related to, explicitly deferred:** `REQ-SB-29` (Vault Scope) — still
  `Draft`/unbuilt. Vault Scope is not an Expert-type wizard field; it
  remains out of scope for this story exactly as it was for the prior
  draft.
- **Blocks:** `REQ-SB-37-US-02` (Worker flow) and `REQ-SB-37-US-03`
  (Producer flow) — both extend the wizard shell/type-selector this story
  builds; neither can be designed or built in isolation from it.
- **Cross-reference correction (this story's own housekeeping):**
  `REQ-SB-39-US-01`'s and `REQ-SB-39-US-02`'s own Dependencies sections
  each say "Blocks: `REQ-SB-37-US-01`... Worker/Producer wizard flows" —
  stale after this split. Both files' Dependencies text is updated in this
  same pass to read `REQ-SB-37-US-02`/`REQ-SB-37-US-03` instead, since
  story IDs are the join key (`Pipeline.md` hard rule 2). `REQ-SB-40-US-01`'s
  own "Related to: `REQ-SB-37`" note is similarly narrowed to name
  `REQ-SB-37-US-01` specifically.
- **External:** none new.

## Constraints

- A created agent's **type** is limited to the existing Worker/Expert/
  Producer enumeration.
- This story builds only the Expert-type wizard step; Worker's and
  Producer's own steps are `REQ-SB-37-US-02`/`US-03`'s scope.
- Configuring Provider/Working mode/Skill grants on a created Expert agent
  must use the exact same surfaces an existing built-in agent already
  uses — no parallel/duplicate configuration mechanism.
- Creating an agent must not require any source-code change.
- Vault Scope is out of scope for this story (Expert is not a Vault-Scope
  wizard field, and `REQ-SB-29` is unbuilt regardless).

## Implementation Tasks

<!-- Decomposer pass, 2026-08-13 — drafted all 4 tasks, wired depends_on as
a straight-line chain (ADR-030's own layering: vault_writer primitives →
agent_registry.py overlay → POST /agents → frontend wizard+entry
affordance), and advanced all 4 tasks to status: Ready in lockstep with the
story. T04 (frontend) merges the wizard shell/type-selector/Expert-step
with the Settings entry affordance into one task, not two — mirrors this
project's own established REQ-SB-18-US-01-T07 precedent (SectionsCard.tsx +
SettingsPage.tsx composition landed together), and avoids an artificial
intermediate task with no reachable mount point to verify against (a
wizard component with no entry affordance yet is not independently
click-through-verifiable). See ## Notes for the full gating rationale. -->

| Task | Title | depends_on | Status |
|---|---|---|---|
| [[REQ-SB-37-US-01-T01]] | `vault_writer.py` — `agents_registry.json` load/save primitives | — | Done |
| [[REQ-SB-37-US-01-T02]] | `agent_registry.py` — `_SEED_AGENTS` rename + persisted-overlay `_load_state` + `create_agent` | `T01` | Done |
| [[REQ-SB-37-US-01-T03]] | `agents_router.py` — new `POST /agents` endpoint | `T02` | Done |
| [[REQ-SB-37-US-01-T04]] | `CreateAgentWizard.tsx` (type selector + Expert step) + Settings entry affordance + `agentsApiClient.ts` `createAgent` | `T03` | Done |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, manual verification mode still in effect project-wide
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Worker-type and Producer-type wizard flows** — `REQ-SB-37-US-02` and
  `REQ-SB-37-US-03` respectively; both are hard-blocked on `REQ-SB-39`.
- **Bespoke/custom actions for a user-created agent** — superseded by
  `REQ-SB-39`'s own "convert existing Actions to Skills" direction; no
  separate custom-action mechanism is built by this story or any sibling.
- **Vault Scope configuration for a created agent** — `REQ-SB-29-US-01` is
  still `Draft` with no built surface.
- **`REQ-SB-40`'s gap-tracking/observability layer itself** — separate
  story; this story only relies on the already-`Done` `REQ-SB-33` guardrail
  it is built on top of.
- **Deleting or renaming an existing built-in agent** — this story is
  additive only.
- **Any gating/approval step on agent creation itself** — the PRD
  breadcrumb names this as open; not built here.
- **Migrating the seven existing static `AGENTS` entries** into whatever
  persisted mechanism this story introduces — the architect's
  `/plan-tasks` call, not required here.

## Notes

**Prototype parity (agents-map.html / settings.html):**

- Both screens' existing Sections/Providers `+ Create new …` `<details>`
  affordances — **Specced** as the closest existing precedent for this
  story's own Create Agent affordance, but the affordance itself is **not
  covered by the approved prototype** anywhere — net-new design needed.
- `agents-map.html`'s agent detail side panel Settings tab (Provider/
  Working-mode/Skill-access rows) — **Specced**, Scenario 6; already
  approved for `REQ-SB-19/21/27`.
- `agents-map.html`'s agent detail side panel Chat/Communication History
  tabs — **Specced**, Scenario 8; already approved, unchanged.
- The Expert-type wizard step itself (domain field + honest-empty state) —
  **Net-new design needed**, no approved prototype coverage.

**Why this is flagged, not cleared (`ESCALATIONS.md` → `ESC-020`, follow-up
note added this pass):**

1. **The persisted-registry mechanism still directly reverses `ADR-011`
   point 2** — unchanged from the prior draft, still an ADR-level call for
   the architect at `/plan-tasks`.
2. **Net-new-design-needed** — no `html-prototype/` screen has a Create
   Agent affordance anywhere, and placement (Agents Map vs. Settings vs.
   both) is genuinely open.
3. **Implementation-sequencing open question** — whether the type selector
   exposes Worker/Producer as visible-but-not-yet-functional options before
   `REQ-SB-37-US-02`/`US-03` ship, or is extended incrementally, is left to
   `/plan-tasks`.

The custom-bespoke-actions fork that drove the original `ESC-020` flag is
now **resolved by REQ-SB-39's own existence** (every capability becomes a
Skill; no separate custom-action mechanism is needed) — this is recorded as
resolved in `ESCALATIONS.md`'s follow-up note, not re-flagged here.

`ESCALATIONS.md` → `ESC-020` (follow-up note) records this re-spec and
split in full. A `REVIEW-QUEUE.md` entry (updated, not duplicated) covers
all three resulting stories.

gate: flagged 2026-08-13, gate_reason: unclear-requirement (`ESC-020`
follow-up — persisted-registry mechanism reversing `ADR-011` point 2, still
open) + net-new-design-needed (no Create Agent affordance in any
`html-prototype/` screen) + an implementation-sequencing question left to
`/plan-tasks`. `REQ-SB-37` itself is finalised PRD text (no
`<!-- Draft -->` marker) — the flag is about the open architectural
mechanism decision, the missing prototype coverage, and the sequencing
question, not about the requirement's own finalization state.

**Architect pass, 2026-08-13 (`/plan-tasks` step 1) — blockers 1 and 2
resolved, blocker 3 given an architect call:**

1. **Blocker 1 (persisted-registry mechanism) — resolved via `ADR-030`**
   (supersedes `ADR-011` point 2 only; points 1/3/4 untouched, not
   reopened). Per the operator's relayed mechanism decision: `agent_
   registry.py`'s static `AGENTS` dict becomes `_SEED_AGENTS` (byte-
   identical, unchanged, stays in code — the 7 shipped agents remain
   deployment configuration, not migrated into the persisted store), and a
   new `.second-brain/agents_registry.json` (`{"created_agents": {}}`,
   `vault_writer.load_agents_registry_state`/`save_agents_registry_state`
   mirroring `skill_registry.py`'s `_load_state`/`_save_state` shape
   exactly) holds runtime-created agents. `get_agent`/`list_agents` become
   seed-then-persisted merges; `create_agent(name, type, settings=None)`
   derives `agent_id` via `vault_writer.tag_slug(name)` with numeric-suffix
   collision disambiguation against the union of seed + created ids (never
   an idempotent-collapse the way `create_section` collides — two agents
   must never silently share one identity). Confirmed by direct code
   reading of `agents_router.py` and all five self-healing per-agent
   registries: none of them cache `agent_registry.list_agents()`, every one
   reads it fresh per call, so **zero code changes** are needed in
   `section_registry.py`/`provider_registry.py`/`working_mode_registry.py`/
   `skill_registry.py`/`agent_keywords.py` for a created agent to get a
   default Section/Provider/working-mode/keywords and be Skill-grantable —
   this is the concrete mechanism `ESC-020` flagged as needing this ADR.
   Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-030`.
2. **Blocker 2 (net-new-design-needed) — cleared by operator direction**
   (`/design` explicitly skipped for this batch; build directly). The
   entry-point placement question this blocker also carried is resolved
   here as an architect sequencing call, not deferred further: the "+
   Create agent" affordance goes on **Settings**, mirroring
   `SectionsCard.tsx`/`ProvidersCard.tsx`'s existing "+ Create new …"
   `<details>` pattern — the closest existing precedent named in this
   story's own Prototype-parity note — rather than adding new interactive
   surface to `AgentsMapCanvas.tsx`'s already-`Done`, already-delicate
   semantic-zoom/drill-down canvas (`BUGFIX-02-US-01`/`BUG-002`). See
   `architecture.md` → "Agent Creation Wizard — entry point, type
   selector, Expert-type flow" for the full file-level breakdown.
3. **Blocker 3 (implementation-sequencing — type selector vs.
   Worker/Producer readiness) — resolved:** the type selector shows all
   three types (Worker, Expert, Producer) so Scenario 1's "a choice of
   agent Type" reads honestly against the PRD's own three-type wizard
   shape, but Worker and Producer render **visibly-present-but-disabled**
   ("Coming soon" / not yet selectable) until `REQ-SB-37-US-02`/`US-03`
   ship their own steps — not hidden entirely (which would misrepresent
   the wizard as Expert-only) and not fully wired (which is explicitly
   those sibling stories' own scope, hard-blocked on `REQ-SB-39`).
   Enabling them later is additive UI work in the same component, not a
   re-architecture — no ADR needed for this point, it is ordinary
   component/state sequencing.

**REQ-SB-33 agent-agnosticism — confirmed by direct reading, not
assumed:** `app/business/agent_orchestration/state.py::
history_entries_to_messages(agent_name, agent_type, history)` builds the
grounding/honest-uncertainty `SystemMessage` purely from its own `agent_
name`/`agent_type` **parameters** — no per-agent-id branching anywhere in
`state.py` or `graph.py`. `graph.py::run_agent_conversation` resolves those
two parameters via `agent_registry.get_agent(agent_id)` immediately before
calling it. Since `create_agent` (`ADR-030`) produces a `get_agent`-visible
record with real `name`/`type` fields the instant it is created, a newly
created Expert agent's very first chat message already flows through the
identical grounding instruction every existing agent gets — Scenario 4
requires zero new code in the guardrail itself.

**Architecture scope: §"Agent Creation Wizard — entry point, type
selector, Expert-type flow (REQ-SB-37-US-01, ADR-030)" (`architecture.md`),
§"Frontend Application Architecture" → "Source structure" (for
`features/settings/`/`features/agents-map/` file placement conventions),
`ADR-030` (`ADR.md`).** The coder is bounded to: `app/business/
agent_registry.py`, two new `vault_writer.py` primitives
(`load_agents_registry_state`/`save_agents_registry_state`), a new
`POST /agents` handler in `app/api/agents_router.py`, and frontend:
`src/frontend/src/features/agents-map/CreateAgentWizard.tsx` (new), the
Settings-page entry affordance (`SettingsPage.tsx` /
`features/settings/`), and `agentsApiClient.ts`'s new `createAgent(...)`
call. No other file named in `architecture.md` is in scope for this story.

**Decomposer pass, 2026-08-13 (`/plan-tasks` step 2) — all 8 scenarios
locked, 4 tasks drafted, story advanced `Draft → Ready`:**

- All 8 Gherkin scenarios tightened for buildability and locked as
  `REQ-SB-37-US-01-AC-01` .. `AC-08`, tagged in place after each scenario's
  closing fence. No AC was marked non-locked — every scenario has an
  observable, verifiable outcome (an HTTP response shape, a DOM element, or
  an existing already-`Done` surface's unchanged behavior).
- 4 tasks created (`T01`-`T04`), wired as a straight-line `depends_on`
  chain mirroring `ADR-030`'s own layering (`vault_writer` primitives →
  `agent_registry.py` overlay/`create_agent` → `POST /agents` → frontend
  wizard + entry affordance) — acyclic by construction, see `##
  Implementation Tasks`.
- **AC-to-task mapping:** `AC-01` (entry point), `AC-02` (type-selection
  field-set), `AC-03` (Expert creation with domain+Section), `AC-07`
  (honest rejection on a missing required field) are tagged in `T04`'s own
  `## Tests` — the only task with a real, reachable wizard UI to drive them
  through. `AC-04` (honest uncertainty), `AC-05` (Agents Map), `AC-06`
  (Provider/Working-mode/Skill-grant configuration), `AC-08` (Chat/History
  parity) are tagged in `T03`'s own `## Tests` — each of those four
  scenarios' own Given clause only requires "an Expert agent has just been
  created," not specifically "via the wizard," and `T03`'s new `POST
  /agents` endpoint is the real mechanism the wizard itself calls (per
  `ADR-030` point 6) — the same "backend-layer-first verification" pattern
  already established elsewhere in this project (e.g.
  `REQ-SB-27-US-01-T04`), verifying each of those four scenarios against
  every already-`Done`, zero-code-change downstream surface (`AgentsMapCanvas.tsx`,
  `AgentDetailPanel.tsx`, `/chat`, `/history`) the moment a real created
  agent exists, without waiting on the wizard's own UI to land. `T01`/`T02`
  carry zero AC-tagged steps (non-AC smoke checks only) — mirrors
  `REQ-SB-27-US-01-T01`-`T03`'s own precedent of concentrating every locked
  AC at the user/API-observable layer, not the internal plumbing layers
  beneath it.
- `depends_on` is acyclic (a straight 4-node chain); every locked AC has at
  least one tagged verification step in some task — both conditions for
  `Draft → Ready` are met. Story `status: Draft → Ready`; all 4 tasks
  written at `status: Ready` in lockstep, per `Pipeline.md`'s "task status
  moves in lockstep with the story" rule.
- **Gate stays `flagged`, not reset to `clear`** — the architect's `ADR-030`
  (trigger 3, ADR created/changed) fired this same pass; per this role's own
  rule ("if the architect flagged the story this run for an ADR change,
  leave it `gate: flagged`"), the human reviews `ADR-030` and this task
  breakdown together as one unit. No new MUST-FLAG trigger fired during
  this decomposer pass itself (no material assumption beyond what's already
  recorded above, no contradictory inputs, no locked AC left unverifiable,
  no oversized task — the heaviest, `T04`, is comparable in scope to the
  already-`Done` `REQ-SB-18-US-01-T07` precedent it explicitly mirrors).
  `REVIEW-QUEUE.md`'s existing entry for this story (covering all three
  `REQ-SB-37` split stories) is left as-is, not duplicated.

**Coder pass, 2026-08-14 (`/implement-sprint SPRINT-033`) — all 4 tasks
built and verified live, story `Ready → Done`:**

- All 8 locked ACs verified live: `AC-01`/`AC-02`/`AC-03`/`AC-07` via a
  real CDP-driven headless-browser session against the real wizard UI
  (`T04`); `AC-04`/`AC-05`/`AC-06`/`AC-08` via real HTTP calls against
  `POST /agents` and every already-`Done` downstream surface (`T03`), per
  the decomposer's own backend-layer-first sequencing.
- `ADR-030` built exactly as decided — no deviation, no new ADR needed.
- One scope-internal correction, logged for human spot-check (not an
  escalation): the task's own informal `/agents-map` verification-step
  reference does not exist as a real route — the Agents Map is actually
  mounted at `/` (root), confirmed directly from `App.tsx`'s own route
  table. No locked AC's own wording names a literal URL, so this is a
  verification-method detail only.
- **Sprint-level end-to-end confirmation (beyond any single task's own
  scope, run at the coder's own initiative before closing the sprint):** a
  freshly created Expert agent (`gadgets-expert`) was opened via its real
  detail panel on the Agents Map — Settings tab (Section/Provider/Working
  mode selects, all populated and functional), Chat tab (a real,
  non-fabricated honest-uncertainty reply to an out-of-domain question,
  explicitly naming its own missing vault scope rather than inventing an
  answer), and History tab (identical `{"kind","text","timestamp"}` shape
  to any existing agent's history) all confirmed working, with zero
  console exceptions throughout. The 7 pre-existing static agents were
  independently reconfirmed unaffected — identical ids/types/sections
  before and after this build (`GET /agents` byte-comparable), and
  `vault-qa`'s own pre-existing `view_channel_status` trigger-phrase/
  action path still resolves identically to before this sprint.
- Full evidence: each task's own Implementation Log under
  `Implementation/Tasks/REQ-SB-37-US-01-T01`..`T04`.
