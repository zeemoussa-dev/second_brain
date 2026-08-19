---
id: REQ-SB-37-US-02
title: Agent Creation Wizard — the Worker-type flow (Skills, Vault Scope, Section)
requirement_ids: [REQ-SB-37]
requirement_section: "REQ-SB-37: Agent Creation Wizard"
phase: P1
status: Done
gate: clear
gate_reason: ""
sprint: SPRINT-034
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-37-US-02 — Agent Creation Wizard — the Worker-type flow

## Story

**As a** Second Brain user
**I want** to create a new Worker-type agent from within the app — giving
it Skills (its tools), a Vault Scope, and a Section — without editing
source code
**So that** I can add a new automation/capture-style agent through the
wizard, the same way I can already create an Expert or (once built) a
Producer, instead of needing a code change every time

## Context

- **New sibling of `REQ-SB-37-US-01`**, created by this same re-spec pass
  as part of a three-way split of the rewritten `REQ-SB-37: Agent Creation
  Wizard`. See `REQ-SB-37-US-01`'s own Context for the full split rationale
  and `ESCALATIONS.md` → `ESC-020`'s follow-up note.

- PRD: `Documentation/PRD.md` → *REQ-SB-37: Agent Creation Wizard* —
  "a **Worker** is configured with Skills (its tools), a Vault Scope, and a
  Section." **Acceptance (the Worker-relevant clause):** "the user can
  create a new agent from within the app... via a wizard whose fields
  depend on the chosen Type (Worker: Skills + Vault Scope + Section...)."

- **PRD breadcrumb (2026-08-13, operator-directed), cited verbatim, not
  re-decided here:** "1. Workers Need tools Mainly a Scope of work and
  Section they add data to." Clarified further in the same exchange: Worker
  "tools" = Skills, not custom hardcoded actions — "We have no Custom
  Action, we need to Convert those Custom Actions to Skills. Example, Read
  Mail is a Skill under Outlook COM Tool we need to have that in our tool
  set." This is the exact statement that forced `REQ-SB-39` (Unify Agent
  Capabilities Under Skills) into existence.

- **Why this story is hard-blocked on BOTH halves of `REQ-SB-39`, not
  just one (resolved here, by direct cross-check, not a guess):** a
  Worker's real value comes from the kind of capability today's codebase
  still calls an "Action" — `run_capture_now` (email/meeting/todo capture
  pipelines), `pause_schedule`, `rebuild_person_note` — all classified
  `"mutates": True` and out of scope for `REQ-SB-39-US-01` (which migrates
  only the 3 read-only Action ids). A Worker wizard whose "Skills" step
  could only offer today's narrower, largely read-only Skills catalog
  (`web-research`, `diagram-understanding`, plus `REQ-SB-39-US-01`'s
  read-only migrations) would misrepresent what a Worker actually is per
  the PRD's own framing ("tools" = the real automation work, not just
  read-only lookups). The Worker wizard's Skills step therefore cannot be
  meaningfully written until `REQ-SB-39-US-02` (the mutating-Action
  migration + working-mode gate extension) also lands — both
  `REQ-SB-39-US-01` and `REQ-SB-39-US-02` are hard prerequisites, matching
  both of those stories' own Dependencies sections ("Blocks:
  `REQ-SB-37-US-02`... Worker/Producer wizard flows are Skills-based and
  cannot be fully built until both halves of `REQ-SB-39` land" — corrected
  to this story's ID as part of `REQ-SB-37-US-01`'s own housekeeping edit).

- **What this means concretely for today's dual Actions/Skills system
  (directly answering the question the split raised, not guessing):** no,
  the Worker wizard's Skills step cannot be honestly written against
  today's system. Presenting a Skills picker that only lists the narrow,
  mostly-read-only Skills catalog that exists before `REQ-SB-39` lands
  would either (a) silently omit the very capabilities that make a Worker
  useful (capture, rebuild, pause/resume), misleading the user about what
  their new Worker can do, or (b) require a second, parallel "grant a
  legacy Action" mechanism alongside the Skills picker — exactly the
  two-systems outcome `REQ-SB-39` exists to eliminate. Neither is
  acceptable; this story's Acceptance Criteria are written assuming
  `REQ-SB-39`'s unified catalog already exists, and this story cannot
  progress to `/plan-tasks` until it does.

- **Vault Scope — the second hard dependency (resolved here, by direct
  read of `REQ-SB-29-US-01`, not a guess):** that story's own `gate:` is
  `clear` (the retrieval-mechanism question was resolved 2026-08-12), but
  its `status:` is still `Draft` — no Vault-scope field exists anywhere
  today, on any surface, in code or in `html-prototype/`. A Worker wizard
  step that asks the user to "assign a Vault Scope" needs that field to
  exist first. This story does not duplicate or race ahead of
  `REQ-SB-29-US-01`'s own assignment mechanism; it reuses it once built.

- **Resolved here, by direct code inspection (not a guess):** Worker is
  one of the three existing agent-type values, matching the Agents Map's
  Worker ring.

## Acceptance Criteria

<!-- Decomposer pass, 2026-08-13: analyst's untagged Gherkin tightened for
buildability and locked with sequential AC-IDs (REQ-SB-37-US-02-AC-01..06).
All 6 ACs are locked (no non-locked exception used). -->

### Scenario 1: Selecting the Worker type shows Worker-specific fields

```gherkin
Given the user is on the wizard's type-selection step (REQ-SB-37-US-01)
When the user selects the Worker type
Then the wizard shows exactly three fields: Skills (grantable tools, from
    the unified Skills catalog), a Vault Scope, and a Section
  And it does not show Expert's Domain field or Producer's Purpose/
    output-action fields anywhere in the mounted step
```
<!-- AC-ID: REQ-SB-37-US-02-AC-01 -->

### Scenario 2: Creating a Worker agent with Skills, a Vault Scope, and a Section

```gherkin
Given the user is on the Worker-type wizard step
  And at least one Skill is registered in the unified Skills catalog
    (REQ-SB-39)
When the user enters a name, grants one or more Skills, assigns a Vault
    Scope, selects a Section, and submits
Then a new Worker-type agent is created with that name, those exact Skill
    grants, that Vault Scope, and that Section
  And no source-code change was required to create it
```
<!-- AC-ID: REQ-SB-37-US-02-AC-02 -->

### Scenario 3: The new Worker agent appears immediately on the Agents Map

```gherkin
Given the user has just created a Worker agent
When the user views the Agents Map
Then the new agent appears alongside existing agents, in its assigned
    Section and on the Worker ring
  And no reload or restart of the app is required for it to appear
```
<!-- AC-ID: REQ-SB-37-US-02-AC-03 -->

### Scenario 4: Creating a Worker agent without a required field is rejected honestly

```gherkin
Given the user is on the Worker-type wizard step
When the user submits without providing a name, without granting at least
    one Skill, without assigning a Vault Scope, or without selecting a
    Section
Then the agent is not created and no create/grant/assignment call is issued
  And the user sees a clear, honest message naming every missing field
  And no partial or broken agent appears anywhere, including the Agents Map
```
<!-- AC-ID: REQ-SB-37-US-02-AC-04 -->

### Scenario 5: A newly created Worker agent's granted Skills behave identically to an existing agent's

```gherkin
Given the user has created a Worker agent with a mutating Skill granted
    (e.g. a migrated run_capture_now)
When that Skill is invoked, whether by the user or a matched chat message
Then it honors the new agent's own working mode exactly as it would for an
    existing, already-shipped agent with the same Skill granted
```
<!-- AC-ID: REQ-SB-37-US-02-AC-05 -->

### Scenario 6: A newly created Worker agent works like any other agent afterward

```gherkin
Given the user has created a Worker agent
When the user opens that agent's Chat and Communication History tabs
Then both work the same way they already do for an existing, built-in
    agent — no second-class/read-only distinction anywhere in either
```
<!-- AC-ID: REQ-SB-37-US-02-AC-06 -->

## Affected Screens

- `html-prototype/agents-map.html` — needs the Worker-type wizard step
  (Skills picker + Vault Scope field + Section picker). **No approved
  prototype coverage anywhere** — neither a Skills grant/revoke affordance
  (also missing for `REQ-SB-39-US-01`) nor a Vault Scope field (also
  missing for `REQ-SB-29-US-01`) exist in any screen today. A `/design`
  pass is required, and is most efficient once those two prerequisite
  stories have their own screens designed, so this step can reuse them
  rather than invent parallel ones.

## Dependencies

- **Hard prerequisite:** `REQ-SB-37-US-01` — this story extends that
  story's own wizard shell/type-selector; it is not designed or built in
  isolation.
- **Hard prerequisite (both, not either):** `REQ-SB-39-US-01` and
  `REQ-SB-39-US-02` — the Worker wizard's Skills step needs the fully
  unified capability catalog, including migrated mutating capabilities and
  the extended working-mode gate (see Context).
- **Hard prerequisite:** `REQ-SB-29-US-01` (Vault Scope) — its `gate:` is
  `clear` but its `status:` is `Draft`; no Vault-scope assignment surface
  exists yet anywhere for this wizard step to reuse.
- **Not blocked by (already satisfied):** `REQ-SB-18-US-01` (Section,
  Done), `REQ-SB-21-US-01` (Working mode, Done — the gate Scenario 5
  relies on).
- **External:** none new.

## Constraints

- Skills granted at creation must use the exact same grant mechanism
  `REQ-SB-39`'s unified model establishes for any other agent — no
  parallel, Worker-specific capability mechanism.
- Vault Scope assignment at creation must use the exact same mechanism
  `REQ-SB-29-US-01` establishes for an existing agent's Settings surface —
  no parallel, wizard-only scope-assignment mechanism.
- This story does not progress to `/plan-tasks` until `REQ-SB-39-US-01`,
  `REQ-SB-39-US-02`, and `REQ-SB-29-US-01` are all `Ready` or `Done` — see
  Context's "what this means concretely" note.

## Implementation Tasks

| Task | Title | Depends On |
|---|---|---|
| [[REQ-SB-37-US-02-T01]] | `agents_router.py` — `POST /agents` `type` check extended to accept `"worker"` | `REQ-SB-37-US-01-T03`, `REQ-SB-39-US-02-T03` |
| [[REQ-SB-37-US-02-T02]] | `CreateAgentWizard.tsx` — new Worker step (Skills multi-select + Vault Scope field + Section picker), three-call sequence, client-side validate-before-any-call | `REQ-SB-37-US-02-T01`, `REQ-SB-37-US-01-T04`, `REQ-SB-39-US-01-T09`, `REQ-SB-39-US-02-T03`, `REQ-SB-29-US-01-T05` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Expert-type and Producer-type wizard flows** — `REQ-SB-37-US-01` and
  `REQ-SB-37-US-03` respectively.
- **Building `REQ-SB-39`'s own unified capability model, or `REQ-SB-29`'s
  own Vault Scope mechanism** — this story only consumes both once built;
  it does not build or accelerate either.
- **Any gating/approval step on agent creation itself** — not built here.

## Notes

**Prototype parity (agents-map.html):** no region of the approved
prototype covers a Worker wizard step, a Skills grant/revoke affordance, or
a Vault Scope field — **all net-new design needed**, most efficiently
sequenced after `REQ-SB-39-US-01`'s and `REQ-SB-29-US-01`'s own `/design`
passes so this step reuses their eventual screens.

**Why this is flagged, not cleared:**

1. **Genuine cross-story dependency** — hard-blocked on three separate,
   currently-unbuilt stories (`REQ-SB-39-US-01`, `REQ-SB-39-US-02`,
   `REQ-SB-29-US-01`), a `Pipeline.md` MUST-FLAG trigger in its own right
   (cross-sprint/cross-story dependency, trigger 5/7).
2. **Net-new-design-needed** across multiple prerequisite surfaces.

This story is intentionally NOT written to progress past `Draft` until its
prerequisites land — it exists now so the wizard's full shape is on record
and `REQ-SB-37-US-01` can correctly reference it, not because it is ready
to be planned.

gate: flagged 2026-08-13, gate_reason: new-dependency (hard-blocked on
`REQ-SB-39-US-01` + `REQ-SB-39-US-02` + `REQ-SB-29-US-01`, none of which are
built) + net-new-design-needed. `REQ-SB-37` itself is finalised PRD text —
the flag is entirely about unbuilt prerequisites and missing prototype
coverage, not about the requirement's own finalization state.

**Architect pass, 2026-08-13 (`/plan-tasks` step 1) — all three hard
prerequisites now `Ready`, planning proceeds.** `REQ-SB-39-US-01`,
`REQ-SB-39-US-02`, `REQ-SB-29-US-01`, and `REQ-SB-37-US-01` are all
`status: Ready` with real, drafted task files as of this pass (confirmed
by direct read of each story's frontmatter, not assumed) — the blocker
this story's own flag named is resolved. Actual code for those four
stories is not yet built (`Done`); that is `/implement-sprint`'s own
build-order concern via `depends_on` task edges, not a `/plan-tasks`
blocker — matching this project's own established "status is the single
source of truth, not code-in-place" rule.

**No new ADR — confirmed additive composition, not a new architectural
question.** Direct code inspection (not the plan-only task text) of
`app/api/agents_router.py`, `app/business/skill_registry.py`/
`skill_tools.py`, `app/api/skills_router.py`, and `app/business/
section_registry.py` confirms the three mechanisms this story composes are
real, decided, and stable: `ADR-030`'s `create_agent`/`POST /agents`
shape (not yet coded, but its task files — `REQ-SB-37-US-01-T02`/`T03` —
fully specify it); the unified Skills grant surface (`ADR-028`/`ADR-029`,
`POST`/`DELETE /agents/{agent_id}/skills/{skill_id}`, already real code
today); and `REQ-SB-29-US-01`'s own additive `PATCH /agents/{agent_id}`
`scope` field (architect-recorded, not yet coded). Composing three
already-decided mechanisms into one wizard flow, and deciding the call
**sequencing** between them, is not itself a new structural/tooling
decision — see `architecture.md` → "Amendment — Worker-type flow" for the
full reasoning, including the one genuine judgment call this pass made and
the alternative it explicitly rejected (draft/staged agent record vs.
sequential calls against an already-live `agent_id`).

**Net-new-design-needed — already resolved batch-wide, not re-decided
here.** The operator's own direction to skip `/design` for this entire
batch (`REQ-SB-28/29/37/38/39/40/41`, `REVIEW-QUEUE.md` 2026-08-13 update;
also the basis `REQ-SB-37-US-01`'s and `REQ-SB-39-US-01`'s own architect
passes already relied on) covers `REQ-SB-37` in full, including this
story. The coder is bounded instead to matching already-built row/control
patterns exactly (`AgentDetailPanel.tsx`'s Section `<select>`/Keywords
free-text row, `REQ-SB-39-US-01`'s Skills grant/revoke control) — no fresh
prototype screen gates this build.

**Architecture scope:** `Implementation/Architecture/architecture.md` →
"Agent Creation Wizard — entry point, type selector, Expert-type flow
(REQ-SB-37-US-01, ADR-030)" → "Amendment — Worker-type flow (REQ-SB-37-US-02,
no new ADR)" (the subsection directly below the Expert-type flow's own
breakdown). The coder is bounded to:
- `app/api/agents_router.py` — `POST /agents`'s `type` check extended to
  accept `"worker"` alongside `"expert"`; `domain` becomes optional,
  required only for Expert; a Worker is created via
  `agent_registry.create_agent(name, "worker", settings=[])`. No other
  handler in this file changes.
- No change to `app/business/agent_registry.py`, `skill_registry.py`,
  `skill_tools.py`, `skills_router.py`, `section_registry.py`, or
  `scope_registry.py` themselves — this story consumes each unmodified,
  exactly as `REQ-SB-37-US-01`'s own Expert flow consumes `section_registry`
  unmodified.
- `src/frontend/src/features/agents-map/CreateAgentWizard.tsx` — a new
  Worker step (`step` state gains `'worker'`), reusing the Expert step's
  Section `<select>` verbatim, a new Skills multi-select (`GET /skills`),
  and a new Vault Scope free-text/comma-separated field mirroring the
  Keywords row. Client-side validation (name + ≥1 Skill + non-empty scope
  + a Section, all present before any call fires) mirrors
  `REQ-SB-37-US-01-T04`'s own AC-07 precedent exactly — no new validation
  pattern invented.
- Call sequence the wizard's Worker step issues, in order: `POST /agents`
  → one `POST /agents/{agent_id}/skills/{skill_id}` per selected Skill →
  one combined `PATCH /agents/{agent_id}` carrying both `section_id` and
  `scope` together (a single call, not two).
- `agentsApiClient.ts` — `createAgent`'s `type` union gains `'worker'`; no
  other client function changes (`updateAgentAssignment` and the Skills
  grant call are already additive/`Done`).

`gate: clear` 2026-08-13 — no ADR trigger fired (confirmed additive
composition of three already-`Accepted`/already-established mechanisms,
reasoning above), no material assumption beyond ordinary sequencing/
shape-matching against already-established precedent (`ADR-030` point 6's
sequential-call pattern; `REQ-SB-37-US-01-T04`'s client-validate-before-
any-call pattern), no contradiction of any `Accepted` ADR/PRD/`MEMORY.md`
constraint found (the draft/staged-record alternative was considered and
explicitly rejected as being in tension with `MEMORY.md`'s no-staging-layer
posture, not adopted). Hands off to the decomposer.

**Decomposer pass, 2026-08-13 (`/plan-tasks` step 2).** All 6 analyst
scenarios tightened for buildability and locked as
`REQ-SB-37-US-02-AC-01`..`AC-06` — no non-locked exception used. Two flat-
root task files created: `REQ-SB-37-US-02-T01` (backend — `POST /agents`
`type` check extended to accept `"worker"`, `domain` optional, per the
architect's own code block) and `REQ-SB-37-US-02-T02` (frontend — the
Worker step inside `CreateAgentWizard.tsx`, the three-call sequence, and
client-side validate-before-any-call). `depends_on` wired to REAL task IDs
(read directly, not assumed) from every cross-story prerequisite named in
the architect's own composition: `REQ-SB-37-US-01-T03`/`T04` (the base
`POST /agents` endpoint and wizard shell this story extends);
`REQ-SB-39-US-01-T09` (`skillsApiClient.ts` — `fetchSkills`/
`grantAgentSkill`, reused verbatim, no new Skills fetch/grant client code
written by this story) and `REQ-SB-39-US-02-T03` (the 4 mutating Skills —
including `run_capture_now` — actually land in the catalog; Scenario 5's
own Given clause names a migrated mutating Skill explicitly, so this edge
is load-bearing for verification, not just code composition);
`REQ-SB-29-US-01-T05` (`agentsApiClient.ts`'s `scope` field/body-type
extension — the literal TS surface `T02`'s combined `PATCH` call needs;
`T05`'s own `depends_on` already covers `REQ-SB-29-US-01-T03`'s backend
field transitively, so it is not separately re-listed here). Zero cycles —
verified by direct inspection of every named task's own `depends_on`.

AC → verification mapping (every locked AC has ≥1 tagged step): `AC-01`
(structural — exact 3-field set, no Expert/Producer fields) and `AC-04`
(honest multi-field rejection, no call fires) are UI-specific (their own
Given clause requires the wizard step itself) — tagged in `T02` only,
mirroring `REQ-SB-37-US-01-T04`'s AC-02/AC-07 placement precedent.
`AC-02` (the full name+Skills+Scope+Section submit flow) also requires the
wizard UI — tagged in `T02`. `AC-03`/`AC-05`/`AC-06`'s own Given clauses
only require "a Worker agent has just been created" (not specifically
"via the wizard") — verified backend-layer-first in `T01`, against the
real `POST /agents` mechanism the wizard itself calls, mirroring
`REQ-SB-37-US-01-T03`'s AC-04/05/06/08 placement precedent exactly.

**No MUST-FLAG trigger fired this pass** — no material assumption beyond
ordinary AC-to-task placement precedent already established twice in this
same story family; no `Draft`/unfinalised requirement relied on (all 4
prerequisite stories are `Ready` with real task files, confirmed by direct
read); no ADR created/changed at this step (architect's own `gate: clear`
stands); no `ESCALATIONS.md` entry needed; no oversized task (2 tasks, XS/S,
matches the 2-task `REQ-SB-37-US-01`-sibling shape); every locked AC has a
tagged verification step and is verifiable (all 6 map to a real, observable
HTTP/DOM outcome); no contradictory inputs; no genuinely unclear or
multiple-equally-valid breakdown — the task split (one backend type-check
extension, one frontend wizard step) is the only reasonable cut, matching
`REQ-SB-37-US-01`'s own T03/T04 backend/frontend split.

`status: Draft → Ready`, `gate: clear` 2026-08-13 — nothing written to
`REVIEW-QUEUE.md` or `ESCALATIONS.md` this pass.

**Coder pass, 2026-08-14 (`/implement-sprint SPRINT-034`).** Both tasks
(`T01`, `T02`) built and verified live end-to-end against all 6 locked
ACs — see each task's own Implementation Log for full detail. A real
Worker agent (`ops-helper`) was created end-to-end through the actual
wizard UI, with two granted Skills (one read-only, one migrated mutating),
a Vault Scope, and a Section, and independently confirmed via `GET
/agents/ops-helper` + `GET /agents/ops-helper/skills` to match the UI's
own claimed outcome exactly. `status: Ready → Done`, `gate: clear`.
