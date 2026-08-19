---
id: REQ-SB-46-US-01
title: Agent Creation Wizard Redesign — Agents Map FAB entry point, popup modal, visual step bar, reorganized 4-step field groupings
requirement_ids: [REQ-SB-46]
requirement_section: "REQ-SB-46: Agent Creation Wizard Redesign — Popup Modal with Visual Step Bar"
phase: P1
status: Done
gate: flagged
gate_reason: "Coder pass (2026-08-14): all 5 tasks (T01-T05) Done, all 11 locked ACs (AC-01..AC-11) verified live end-to-end via a real CDP-driven headless-Edge session plus direct backend HTTP cross-checks (no mocks) — see each task's own Implementation Log. Story advances to Done. Stays gate: flagged for a human spot-check of the coder's own disclosed scope-internal judgement calls (never escalations): (1) all 4 steps built in one coherent pass rather than as 4 separate non-compiling checkpoints — T02's Implementation Log; (2) Expert's own optional Step-3 Skills selections are granted at submit (a for-loop no-op when none selected, satisfying AC-07's literal 2-call Expert case) rather than silently discarded — T05's Implementation Log. Both are scope-internal per Pipeline.md hard rule 5, not MUST-FLAG triggers 4-8."
sprint: "SPRINT-043"
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-46-US-01 — Agent Creation Wizard Redesign — popup modal, visual step bar, reorganized steps

## Story

**As a** Second Brain user
**I want** to open the Agent Creation Wizard from a floating action button on
the Agents Map, as a popup modal with a visual step-progress bar, with its
fields regrouped into four clearer steps (identity/type, configuration,
tools, and a final summary-plus-trigger-choice) instead of today's
Settings-page inline flow
**So that** creating an agent feels like a modern, guided, visually-clear
wizard reachable from the surface where I actually think about my agents
(the Agents Map), instead of a buried Settings-page `<details>` disclosure

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-46: Agent Creation Wizard Redesign
  — Popup Modal with Visual Step Bar*. Verbatim operator direction cited in
  the PRD's own breadcrumb (2026-08-14): "The Link should be in the
  Agentic Map at the Bottom Right. Click on it open a Pop up wizard with
  the top is Steps Bar (1,2,3,4) A Visual Appealing one."

- **This is a NEW story, not a reopening of `REQ-SB-37-US-01`/`-US-02`/
  `-US-03` (all three `Done`, frozen — Pipeline.md hard rule 1, specs are
  append-only).** Confirmed directly against the real shipped code
  (`src/frontend/src/features/agents-map/CreateAgentWizard.tsx`,
  `src/frontend/src/features/settings/CreateAgentCard.tsx`,
  `src/frontend/src/pages/SettingsPage.tsx`,
  `src/backend/app/api/agents_router.py`'s `POST /agents`): the backend
  `create_agent` mechanism, its per-type field set (Expert: Domain; Worker:
  Skills grant + Vault Scope + Section; Producer: Purpose + single output
  Skill + Section), and the exact multi-call sequence each type's submit
  handler issues (`createAgent` → optional `grantAgentSkill` call(s) →
  `updateAgentAssignment` PATCH) are all real, already-built, and
  unchanged by this story. This story composes/relocates/re-presents that
  mechanism; it does not rebuild it.

- **Entry point moves from Settings to a new Agents Map FAB (PRD-directed,
  not a judgment call).** Today's sole entry point is
  `CreateAgentCard.tsx`'s `+ Create agent` `<details>` disclosure on
  `SettingsPage.tsx`. The PRD text is explicit — "moves from a
  Settings-page entry point to a floating action button at the
  bottom-right of the Agents Map" — so this story treats the Map FAB as
  the **sole** entry point going forward, not an additional one alongside
  Settings (see Scenario 8).

- **No `html-prototype/` coverage anywhere — confirmed by direct
  inspection, not trusted from the PRD breadcrumb's own assertion.**
  Grepped `html-prototype/agents-map.html`, `styles.css`, and `app.js` for
  `modal|dialog|overlay|backdrop|fab|floating|bottom-right` and
  `html-prototype/settings.html` for any Create-agent affordance. The only
  overlay pattern that exists anywhere is the agent detail
  `.side-panel-overlay` (`agents-map.html` line ~2330, `styles.css` line
  ~751) — a **slide-in side panel**, not a centered popup modal, and it
  carries no step-bar concept at all. `settings.html` has zero Create
  Agent affordance (matching `REQ-SB-37-US-01`'s own prior finding — still
  true). A centered popup modal with a 4-step visual progress bar and a
  Map-mounted FAB are both genuinely new visual patterns with no reusable
  approved precedent anywhere in this prototype. Per this role's own
  "Prototype reconciliation" rule, this sets `gate: flagged`,
  `gate_reason: net-new-design-needed` — the human should run `/design` on
  this requirement before `/plan-tasks`, per the recommendation below,
  even though the operator has generally skipped `/design` for
  backend-heavy work this session; a real new interaction shell (popup +
  step bar) is exactly the class of decision that pattern-matching skip
  doesn't cover.

- **Step 1 conditional-field interaction — resolved here, delegated to the
  analyst's own judgment per the brief (a standard wizard pattern, not a
  novel design problem):** when the user changes Type within Step 1, any
  Type-specific field **appears/disappears in place** — the already-entered
  Name and Section values (and any other already-entered Step 1 field) are
  preserved across the Type change, not reset. This applies uniformly to
  both Type-conditional Step 1 fields this story identifies (Scope,
  Worker-only; Description, Expert-only — see next point), not just the
  one the breadcrumb named explicitly, for interaction consistency (one
  conditional-visibility rule, not two different ones for two structurally
  identical cases).

- **Field-to-step mapping — the real, disclosed material assumption this
  story makes (Pipeline.md MUST-FLAG trigger 1), because the PRD's own
  Step 1/2/3 field-bucket wording is generic across all three types while
  the real, already-shipped per-type field set is not:**

  The PRD's Acceptance text names step buckets generically ("Description,"
  "Instructions/Guardrails," "output plus what it does with that output,"
  "Tools/Skills") without saying which of Expert's Domain / Worker's
  Skills+Scope / Producer's Purpose+outputSkill lands in which bucket for
  which type. Reading the PRD breadcrumb's own explicit reassurance — "it
  does not change the underlying per-type field set already built
  (Purpose/Domain, Skills grant, Scope, Section, single output Skill)" —
  as the load-bearing constraint, this story maps the existing fields onto
  the new generic buckets as follows, chosen because it is the only mapping
  under which every existing field appears in exactly one step and no step
  bucket is left structurally empty for every type:

  - **Step 1 "Description"** → Expert's existing **Domain** field, shown
    only when Type = Expert (Worker and Producer show no Step 1
    description-equivalent field — Worker has none today, and Producer's
    descriptive field is Purpose, mapped to Step 2 below since the PRD's
    own Step 2 wording ("the agent's output... what it does with it")
    describes Producer's Purpose-plus-output-Skill pair far more precisely
    than Step 1's "Description" does).
  - **Step 2 "Instructions/Guardrails"** → the agent's **Working mode**
    selector (Autonomous/Supervised/Manual) — already a real, shipped
    `PATCH /agents/{agent_id}` field (`REQ-SB-21-US-01`, Done) that
    functions as the agent's own guardrail (gates its mutating
    capabilities); shown for every type, defaulting to Autonomous exactly
    as it already does today when configured post-creation via
    `AgentDetailPanel.tsx`. No new backend field.
  - **Step 2 "output plus what it does with that output"** → Producer's
    existing **Purpose** (free text) + its existing **single-select output
    Skill**, shown only when Type = Producer. Neither Expert nor Worker has
    an output/output-destination concept in the already-shipped mechanism,
    so neither shows this half of Step 2.
  - **Step 3 "Tools/Skills the agent has access to"** → the existing Skills
    multi-select/grant mechanism (`grantAgentSkill`, agent-agnostic at the
    backend), shown for every type: **required** (≥1) for Worker exactly as
    today; **optional** for Expert and Producer (Producer's own mandatory
    output Skill is already selected in Step 2 — Step 3 here lets a
    Producer optionally grant *additional* Skills at creation time, which
    was already possible post-creation via Settings and is now also
    available inline; this is a backend-safe UI convenience, not a new
    mechanism — `grantAgentSkill` was never type-restricted).
  - **Step 4 "summary review, plus a Trigger choice"** → a read-only recap
    of every field entered across Steps 1-3, plus the new Trigger choice
    (see below), before the same create/grant/assign call sequence already
    shipped fires.

  This mapping is disclosed here in full, not silently guessed — it is a
  genuine judgment call under Pipeline.md MUST-FLAG trigger 1 (material
  assumption to fill a PRD gap) and is named explicitly in `gate_reason`
  and `REVIEW-QUEUE.md` for human confirmation before `/plan-tasks` commits
  task-level design to it.

- **The Trigger concept (Step 4) — resolved conservatively, per the brief's
  own delegation, cross-checked against `REQ-SB-47`'s own still-`Draft`
  PRD text (not that story, which does not yet exist):** Trigger is a
  three-option choice (User / Agent / Schedule) **recorded as agent
  metadata only** — reusing the exact same generic `settings` kv-list
  mechanism `create_agent` already uses for Domain/Purpose (a new
  `{"key": "Trigger", "value": "user"|"agent"|"schedule"}` entry,
  defaulting to `"user"` if the step is skipped or left at its default,
  matching the PRD's own "User... today's default" framing). This story
  does **not** build any of `REQ-SB-47`'s own schedule-configuration
  mechanism — choosing "Schedule" only records the intent and shows an
  honest placeholder message that schedule configuration happens on the
  agent's own Schedule tab once `REQ-SB-47` ships (see Scenario 11). This
  story is not blocked on `REQ-SB-47`'s own completion, and does not
  attempt to build any part of its functionality — consistent with this
  project's own established "honest, disclosed intermediate state, not a
  silently-dropped requirement" pattern (`REQ-SB-37-US-03`'s own
  `write-to-vault-draft` stub precedent).

- **Whether "Agent" as a Trigger choice needs any new data-model
  field beyond the generic Trigger metadata above — resolved here, by
  direct code inspection, not guessed:** no. Every agent is already
  Hub-routable and cockpit-`@mention`-invocable today with no per-agent
  opt-in field anywhere (`REQ-SB-20-US-01`, `REQ-SB-43-US-01`,
  `REQ-SB-44-US-01`, all `Done`, all agent-agnostic by construction —
  confirmed by `REQ-SB-37-US-01`'s own prior finding that
  `history_entries_to_messages`/Hub routing branch on no per-agent
  allow-list). Choosing "Agent" therefore records the same generic Trigger
  metadata value as any other choice and is **purely informational** at
  this story's scope — it does not gate, enable, or restrict anything
  structurally. This mirrors the Schedule choice's own
  "recorded intent, not a new mechanism" resolution, applied consistently
  across all three Trigger values rather than inventing a special case for
  one of them.

- **Why this is kept as ONE story, not a three-way split like
  `REQ-SB-37`'s own precedent:** `REQ-SB-37`'s split existed because
  Worker's and Producer's underlying backend mechanisms were **not yet
  built** at spec time (hard-blocked on `REQ-SB-39`/`REQ-SB-29`). Here, all
  three types' backend mechanisms are already `Done` and identical in
  shape before and after this redesign — this story is a pure
  frontend-composition/relocation exercise (container, entry point,
  step-grouping) plus one small additive metadata field (Trigger). Nothing
  about it is blocked per-type, so splitting would not unblock anything
  and would only fragment the regression-guard scenario across three
  stories.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: Reaching the wizard via the new Agents Map FAB

```gherkin
Given the user is viewing the Agents Map
When the user looks at the bottom-right of the screen
Then a floating action button for creating a new agent is visible there
  And no "+ Create agent" affordance exists anywhere on the Settings page
    anymore
```
<!-- AC-ID: REQ-SB-46-US-01-AC-01 -->

### Scenario 2: The FAB opens a popup modal with a visual step-progress bar

```gherkin
Given the user is viewing the Agents Map
When the user clicks the Create Agent floating action button
Then a popup modal opens, centered over the Agents Map, distinct from the
    existing agent-detail side panel's slide-in overlay
  And the modal's top shows a visual step-progress bar with four steps
    (1, 2, 3, 4), with step 1 shown as the current step
```
<!-- AC-ID: REQ-SB-46-US-01-AC-02 -->

### Scenario 3: Step 1 collects Name, Type, conditionally Description and Scope, and Section

```gherkin
Given the user is on Step 1 of the popup wizard
When the user selects the Expert type
Then Step 1 shows Name, Type, a Description field (Expert's knowledge
    domain), and Section — with no Scope field shown
When the user then changes Type to Worker, without reloading or resetting
    the modal
Then Step 1 now shows Name, Type, a Scope field, and Section — with no
    Description field shown
  And any Name or Section value the user already entered before changing
    Type is preserved, not cleared
When the user then changes Type to Producer
Then Step 1 shows Name, Type, and Section only — with no Description field
    and no Scope field shown
```
<!-- AC-ID: REQ-SB-46-US-01-AC-03 -->

### Scenario 4: Step 2 collects Instructions/Guardrails, plus output fields only for Producer

```gherkin
Given the user has completed Step 1 for an Expert-type agent and advances
    to Step 2
Then Step 2 shows a Working-mode (Instructions/Guardrails) selector
    defaulting to Autonomous
  And Step 2 shows no output/output-destination fields
Given the user instead completed Step 1 for a Producer-type agent
When the user advances to Step 2
Then Step 2 shows the same Working-mode selector, plus a Purpose field and
    a single-select output Skill control
```
<!-- AC-ID: REQ-SB-46-US-01-AC-04 -->

### Scenario 5: Step 3 collects Tools/Skills access, required for Worker, optional otherwise

```gherkin
Given the user has completed Step 2 for a Worker-type agent and advances to
    Step 3
Then Step 3 shows a multi-select list of the agent's grantable Skills
  And at least one Skill must be selected before the user can advance
Given the user instead completed Step 2 for an Expert-type or Producer-type
    agent
When the user advances to Step 3
Then Step 3 shows the same multi-select Skills list, but the user may
    advance with zero Skills selected
```
<!-- AC-ID: REQ-SB-46-US-01-AC-05 -->

### Scenario 6: Step 4 shows a summary and a Trigger choice before creation

```gherkin
Given the user has completed Steps 1-3 for any agent type
When the user advances to Step 4
Then Step 4 shows a read-only summary of every field entered in Steps 1-3
  And a Trigger choice of User, Agent, or Schedule, defaulting to User
  And a final "Create agent" action
```
<!-- AC-ID: REQ-SB-46-US-01-AC-06 -->

### Scenario 7: Creating an agent through the new wizard is functionally identical to today's shipped wizard (regression guard)

```gherkin
Given the user completes the new popup wizard for an Expert-type agent with
    a name, a Description (Domain), and a Section
When the user clicks "Create agent" on Step 4
Then the same backend call sequence today's shipped wizard issues for an
    Expert (POST /agents with type "expert" and a Domain setting, then a
    Section-assignment PATCH) fires, and the resulting agent is
    indistinguishable in shape from one created via today's shipped wizard
Given the user instead completes the wizard for a Worker-type agent with a
    name, at least one granted Skill, a Vault Scope, and a Section
When the user clicks "Create agent"
Then the same backend call sequence today's shipped Worker flow issues
    (POST /agents type "worker", one grant call per selected Skill, a
    combined section+scope PATCH) fires, unchanged in shape
Given the user instead completes the wizard for a Producer-type agent with
    a name, a Purpose, a single output Skill, and a Section
When the user clicks "Create agent"
Then the same backend call sequence today's shipped Producer flow issues
    (POST /agents type "producer" with a Purpose setting, one output-Skill
    grant call, a Section-assignment PATCH) fires, unchanged in shape
  And in every case above the created agent appears immediately on the
    Agents Map, on the correct ring for its type, exactly as it already
    does today
```
<!-- AC-ID: REQ-SB-46-US-01-AC-07 -->

### Scenario 8: Selecting "Schedule" as Trigger records intent without building schedule configuration

```gherkin
Given the user is on Step 4 of the popup wizard
When the user selects "Schedule" as the Trigger and creates the agent
Then the agent is created with Trigger metadata recorded as "Schedule"
  And the user sees an honest message that schedule configuration happens
    on the agent's own Schedule tab once it is available
  And no schedule-configuration UI of any kind opens inline as part of this
    wizard
```
<!-- AC-ID: REQ-SB-46-US-01-AC-08 -->

### Scenario 9: Selecting "Agent" as Trigger is purely informational

```gherkin
Given the user is on Step 4 of the popup wizard
When the user selects "Agent" as the Trigger and creates the agent
Then the agent is created with Trigger metadata recorded as "Agent"
  And the agent is Hub-routable and cockpit-@mention-invocable exactly as
    every other agent already is, with no different behavior than if User
    or Schedule had been chosen instead
```
<!-- AC-ID: REQ-SB-46-US-01-AC-09 -->

### Scenario 10: Submitting any step without a required field is rejected honestly

```gherkin
Given the user is on any step of the popup wizard with a required field for
    the current agent Type left empty (e.g. no name, no Section, a Worker
    with zero granted Skills, a Producer with no output Skill selected)
When the user tries to advance past that step or clicks "Create agent" on
    Step 4
Then the wizard does not advance (or does not create the agent)
  And the user sees a clear, honest message naming what's missing
  And no partial or broken agent appears anywhere, including the Agents Map
```
<!-- AC-ID: REQ-SB-46-US-01-AC-10 -->

### Scenario 11: Closing the modal mid-wizard discards the in-progress draft

```gherkin
Given the user has entered values across one or more steps of the popup
    wizard but has not yet clicked "Create agent"
When the user closes the popup modal
Then no agent is created
  And reopening the wizard afterward starts a fresh, empty Step 1 — the
    discarded draft is not restored
```
<!-- AC-ID: REQ-SB-46-US-01-AC-11 -->

## Affected Screens

- `html-prototype/agents-map.html` — needs a new bottom-right floating
  action button and a new popup-modal-with-step-bar screen (or screens, one
  per step, or one screen with step-conditional regions — a `/design`
  decision). **No approved prototype coverage anywhere** — net-new design
  needed (see Context and Notes → Prototype parity).
- `html-prototype/settings.html` — its (never actually designed —
  `REQ-SB-37-US-01`'s own prior finding) `+ Create agent` affordance is
  retired; no design work needed here since none ever existed for it.

## Dependencies

- **Hard prerequisite (already satisfied, all `Done`):** `REQ-SB-37-US-01`
  (Expert flow + `create_agent`/`POST /agents` mechanism), `REQ-SB-37-US-02`
  (Worker flow), `REQ-SB-37-US-03` (Producer flow) — this story composes
  their already-shipped backend mechanisms unchanged; it does not extend or
  modify any of their frozen files' underlying logic.
- **Not blocked by, explicitly:** `REQ-SB-47` (Per-Agent Scheduler) — the
  Schedule Trigger choice only records intent (see Context); this story
  does not wait on `REQ-SB-47`'s own completion.
- **Related to, not composed with:** `REQ-SB-48` (Skills Grouped by Tool —
  Collapsible Multi-Select Tree with Icons) — Step 3's Skills picker in
  this story reuses today's flat multi-select list (`REQ-SB-39`'s existing
  mechanism); the collapsible-tree-by-Tool presentation is `REQ-SB-48`'s
  own separate scope, layered on afterward without requiring changes here.
- **External:** none new. A `/design` pass on this requirement's popup
  modal + step bar + FAB is strongly recommended before `/plan-tasks` (see
  `gate_reason` and `REVIEW-QUEUE.md`), but is not a hard blocker — the
  pipeline may proceed to `/plan-tasks` with this story `gate: flagged` per
  Pipeline.md's exception-based gating (the architect/human may choose to
  run `/design` first, or accept the coder matching established
  row/control patterns directly, mirroring `REQ-SB-37`'s own precedent of
  skipping `/design` for some passes).

## Constraints

- The resulting created agent must be functionally identical (same backend
  calls, same resulting fields/capabilities) to one created via today's
  shipped wizard, for every one of the three types — this story changes
  presentation and entry point only, never the underlying `create_agent`
  mechanism, its per-type required-field set, or its call sequence.
- No new backend field is introduced except the additive `Trigger` metadata
  entry, stored via `create_agent`'s existing generic `settings` kv-list
  mechanism — no new registry, no new persisted file, no schema change to
  any existing agent record shape.
- The Agents Map FAB is the sole entry point after this story ships — no
  duplicate "+ Create agent" affordance remains on Settings.
- Choosing "Schedule" or "Agent" as Trigger must not attempt to build or
  simulate any part of `REQ-SB-47`'s own schedule-configuration mechanism
  or any new Hub-routing behavior — both are recorded as metadata only.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| `REQ-SB-46-US-01-T01` | frontend | Agents Map FAB + popup modal shell + visual step-bar container; retire Settings entry point | `AgentsMapPage.tsx`, `CreateAgentWizard.tsx` → `CreateAgentWizardModal.tsx` (skeleton), `agents-map.css`, `CreateAgentCard.tsx`, `SettingsPage.tsx` | `Implementation/Tasks/REQ-SB-46-US-01-T01-fab-modal-step-bar.md` |
| `REQ-SB-46-US-01-T02` | frontend | Step 1 — Name/Type/conditional Description-or-Scope/Section, in-place field show/hide | `CreateAgentWizardModal.tsx` | `Implementation/Tasks/REQ-SB-46-US-01-T02-step1-identity-type.md` |
| `REQ-SB-46-US-01-T03` | frontend | Step 2 — Working-mode selector + conditional Producer Purpose/output-Skill fields | `CreateAgentWizardModal.tsx` | `Implementation/Tasks/REQ-SB-46-US-01-T03-step2-guardrails-output.md` |
| `REQ-SB-46-US-01-T04` | frontend | Step 3 — shared `SkillsTree.tsx` in `mode="select"`, required for Worker, optional otherwise | `CreateAgentWizardModal.tsx`, `SkillsTree.tsx` (consumed, cross-story) | `Implementation/Tasks/REQ-SB-46-US-01-T04-step3-skills-tree.md` |
| `REQ-SB-46-US-01-T05` | fullstack | Step 4 — summary + Trigger choice + submit wiring (additive backend `trigger` field); regression-guard verification | `CreateAgentWizardModal.tsx`, `AgentsMapPage.tsx`, `agentsApiClient.ts`, `agents_router.py` | `Implementation/Tasks/REQ-SB-46-US-01-T05-step4-summary-trigger-submit.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **`REQ-SB-47`'s own Schedule tab / schedule-configuration UI** — not
  built here; the Schedule Trigger choice only records intent and shows a
  placeholder message (Scenario 8).
- **`REQ-SB-48`'s own collapsible Tool-grouped Skills tree with icons** —
  Step 3 reuses today's flat Skills multi-select list; the tree/icon
  presentation is that requirement's own separate scope.
- **Any new Hub-routing/mention behavior tied to the "Agent" Trigger
  choice** — purely informational metadata at this story's scope
  (Scenario 9).
- **Changing any of `create_agent`'s existing required-field validation,
  the three types' underlying field sets, or the Skills-grant/Section-
  assignment call mechanism** — this story only reorganizes where those
  same fields and calls are presented and sequenced.
- **Editing an already-created agent's Trigger value after creation** — not
  addressed here; the Trigger field's own post-creation editability (e.g.
  on Settings, or on `REQ-SB-47`'s future Schedule tab) is left open for a
  future story.

## Notes

**Prototype parity (agents-map.html / settings.html):**

- Agents Map bottom-right FAB — **net-new design needed**. No floating
  action button, or any `position: fixed` bottom-right affordance, exists
  anywhere in `agents-map.html` today (confirmed by direct grep).
- Popup modal container with a visual 4-step progress bar — **net-new
  design needed**. The only existing overlay pattern anywhere in
  `html-prototype/` is the agent detail panel's `.side-panel-overlay`
  (slide-in side panel), a structurally different shape (edge-anchored,
  no step concept) from a centered popup modal with a top step bar. No
  step-progress-bar visual pattern exists anywhere in the prototype today.
- Step 1 (Name/Type/conditional Description/conditional Scope/Section),
  Step 2 (Working-mode + conditional Producer output fields), Step 3
  (Skills multi-select), Step 4 (summary + Trigger choice) — **Specced**
  in this story's own Scenarios 3-6, but every one of their underlying
  fields is presented today only as flat inline form rows inside
  `CreateAgentWizard.tsx`'s per-type `<form>` blocks
  (`html-prototype/settings.html` itself never got a matching design pass
  either, per `REQ-SB-37-US-01`'s own prior finding) — so there is no
  prior approved visual treatment to reconcile against for any of the four
  steps' own layout, only the underlying field list this story maps them
  onto.
- Settings page's `+ Create agent` `<details>` disclosure —
  **Superseded** (retired; the Map FAB becomes the sole entry point,
  Scenario 1) — this region of `settings.html` was itself never actually
  designed in the prototype (confirmed above), so there is nothing to
  formally deprecate in the prototype file itself, only in the real
  shipped `SettingsPage.tsx`/`CreateAgentCard.tsx`.

**Why this is flagged, not cleared:**

1. **Net-new-design-needed** (Pipeline.md MUST-FLAG trigger 8 / this role's
   own mandatory prototype-reconciliation rule) — a popup modal with a
   visual step-progress bar and a Map-mounted FAB are both genuinely new
   interaction patterns with zero approved prototype precedent anywhere.
   Recommend running `/design REQ-SB-46` before `/plan-tasks`.
2. **Material assumptions** (trigger 1) — the field-to-step mapping in
   Context (Description → Expert's Domain only; Instructions/Guardrails →
   Working mode; output-and-what-it-does-with-it → Producer's
   Purpose+outputSkill only; Tools/Skills → required-for-Worker/
   optional-otherwise) is a disclosed, reasoned judgment call, not
   something the PRD or its breadcrumb states directly. A human should
   confirm this mapping (or redirect it) before task-level design commits
   to it.

Both are named plainly here and in `REVIEW-QUEUE.md`, not silently decided.
The Step 1 conditional-visibility interaction and the Trigger step's own
recorded-metadata-only scope (both explicitly delegated to the analyst's
own judgment by the brief) are **not** flag reasons — they are resolved,
sane, buildable defaults per the brief's own direction, documented in
Context for traceability.

`gate: flagged` 2026-08-14, `gate_reason: net-new-design-needed` (no popup
modal / step-bar / FAB pattern anywhere in `html-prototype/`) +
unclear-requirement-adjacent material assumptions (the field-to-step
mapping named above). `REQ-SB-46` itself is finalised PRD text (no
`<!-- Draft -->` marker) — the flag is about missing prototype coverage and
a disclosed mapping judgment call, not about the requirement's own
finalization state.

---

**Architect pass (2026-08-14):**

**Operator-relayed decisions, recorded here (not re-derived by the
architect):** (1) skip a formal `/design` pass for this story, matching
this session's established precedent (`REQ-SB-47`/`REQ-SB-48` both skipped
it too) — the coder is directed to build a genuinely polished, visually
appealing step-bar by drawing on this codebase's own existing visual
language (the agent detail side panel's slide-in overlay styling,
`agents-map.css`'s color/spacing tokens), not by inventing a new design
system. This resolves the analyst's `net-new-design-needed` flag. (2) The
analyst's field-to-step mapping (Context, above) is confirmed as final,
not re-litigated.

**The three real composition questions this pass resolved concretely
(this story lands last in its batch, after `REQ-SB-47`/`REQ-SB-48`/
`REQ-SB-51`, all now `Ready` with real, decomposed designs):**

1. **Step 3 (Tools/Skills) and `REQ-SB-48`'s own Skills tree — resolved:
   shared, reusable component, not duplicated.** A new `SkillsTree.tsx`
   (mode-parameterized: `manage` for `AgentDetailPanel.tsx`'s existing
   grant/revoke UI, `select` for this wizard's new checkbox multi-select)
   is originated by `REQ-SB-48-US-01-T02` (which lands first — already
   `Ready` with locked ACs/tasks) and consumed here via a real, decomposer-
   assigned `depends_on: REQ-SB-48-US-01-T02` edge on this story's own
   Step-3 task — this codebase's first cross-story frontend task
   dependency. Full reasoning: `ADR-039` point 2/Alternatives.
2. **Step 4's Trigger choice and `REQ-SB-47`'s now-real Schedule tab —
   confirmed: the story's own already-resolved "records intent only, does
   not build `REQ-SB-47`'s own configuration UI inline" scoping still
   holds.** Composing the real schedule-creation call now would need two
   additional required inputs (capability, interval) this story's own
   locked Step 4 does not collect, and would silently expand this story's
   own AC surface. No architecture change beyond the additive `trigger`
   field already named in this story's own Constraints. Full reasoning:
   `ADR-039` point 3/Alternatives.
3. **`REQ-SB-51`'s `is_background_agent` toggle — fold-in declined,
   deferral stands.** No locked AC in this story names a Background-Agent
   toggle, and this role may not expand a story's scope beyond its own
   Context/Constraints; folding it in now would also add a real,
   avoidable dependency on `REQ-SB-51-US-01`'s own not-yet-`Done` backend
   field. `REQ-SB-51-US-01`'s own "a future story may add this to
   whichever wizard shape is current once `REQ-SB-46` lands" reasoning
   stands, unchanged — revisit as a small, separate future story once both
   this story and `REQ-SB-51-US-01` are `Done`. Full reasoning: `ADR-039`
   point 4/Alternatives.

Wrote `ADR-039` (new — extends `ADR-030`/`ADR-031`, composes with
`REQ-SB-48-US-01`'s own in-flight design, reopens neither). Full reasoning:
`Implementation/Architecture/ADR.md` → `ADR-039`;
`Implementation/Architecture/architecture.md` → "Amendment — Popup Modal
Redesign, shared `SkillsTree.tsx` extraction, Trigger/Background-Agent
composition (REQ-SB-46-US-01, ADR-039)" under "Agent Creation Wizard —
entry point, type selector, Expert-type flow."

**Architecture scope:** §Agent Creation Wizard →
"Amendment — Popup Modal Redesign, shared `SkillsTree.tsx` extraction,
Trigger/Background-Agent composition (REQ-SB-46-US-01, ADR-039)"
(`Implementation/Architecture/architecture.md`) — the coder is bounded to:
`src/frontend/src/features/agents-map/CreateAgentWizardModal.tsx`
(renamed/restructured from `CreateAgentWizard.tsx`), `src/frontend/src/
features/agents-map/SkillsTree.tsx` (new — but only the `mode="select"`
consumption half is this story's own scope; `REQ-SB-48-US-01-T02` owns the
file's origination and its own `mode="manage"` consumer), `src/frontend/
src/pages/AgentsMapPage.tsx` (new `.map-fab` + modal mount), `src/frontend/
src/features/settings/CreateAgentCard.tsx` + `src/frontend/src/pages/
SettingsPage.tsx` (entry point removed), `src/frontend/src/styles/
agents-map.css` (new `.wizard-modal-overlay`/`.wizard-modal`/
`.wizard-step-bar`/`.wizard-step`/`.map-fab` classes, tokens-based, no
`.side-panel-*` reuse), `src/backend/app/api/agents_router.py`
(`CreateAgentBody` gains additive `trigger?: str`; `create_agent` appends
the `Trigger` `settings` entry uniformly), `src/frontend/src/features/
agents-map/agentsApiClient.ts` (`CreateAgentBody` gains additive
`trigger?: string`). Out of scope, explicitly: any `REQ-SB-47` schedule-
configuration UI, any `REQ-SB-51` `is_background_agent` field/toggle,
`REQ-SB-48-US-01-T01`'s backend `"tool"` field work (already that story's
own scope, consumed here read-only).

Handing off to the decomposer with `gate: flagged` (trigger 3, `ADR-039`)
— per Pipeline.md, this does not halt `/plan-tasks`; the decomposer
proceeds so the human reviews the ADR and the resulting tasks together in
one pass, including the new cross-story `depends_on` edge onto
`REQ-SB-48-US-01-T02`. See `REVIEW-QUEUE.md`.

---

**Decomposer pass (2026-08-14):**

All 11 untagged scenarios tightened only trivially (wording already
buildable as written) and locked as `REQ-SB-46-US-01-AC-01` through
`-AC-11`, one tag per scenario, in order. No AC marked `locked: false` —
every scenario has an observable, DOM/HTTP-verifiable outcome.

**Five tasks written**, sequenced to match the real single-file wizard's
own tightly-coupled state (`CreateAgentWizardModal.tsx` carries all step
state, so each step's own task builds directly on the previous step's
already-landed fields):

- `T01` (FAB + modal shell + step-bar container + Settings-entry-point
  retirement) — AC-01, AC-02. The FAB and the modal/step-bar container are
  combined into one task, not split into two as the literal batch listing
  might imply: a FAB alone (one button + one state flag) is far below one
  working-session's atomic-task floor, and it is inseparably coupled to
  the modal it opens — splitting them would only produce an artificial
  intermediate task with a stub modal. This is a scope-internal judgement
  call (Pipeline.md hard rule 5), not a MUST-FLAG trigger — there is one
  sensible answer here, not genuinely multiple equally-valid
  breakdowns — recorded here for traceability, not escalated.
- `T02` (Step 1) — AC-03. `depends_on: [T01]`.
- `T03` (Step 2) — AC-04. `depends_on: [T02]`.
- `T04` (Step 3, shared `SkillsTree.tsx` `mode="select"`) — AC-05.
  `depends_on: [T03, REQ-SB-48-US-01-T02]` — this codebase's first
  cross-story frontend task dependency, exactly as `ADR-039` directs.
- `T05` (Step 4: summary, Trigger choice, submit wiring, additive backend
  `trigger` field, and the Scenario 7 regression-guard walkthrough) —
  AC-06 through AC-11. `depends_on: [T04]`. The regression guard
  (AC-07) and the multi-step validation/discard scenarios (AC-10, AC-11)
  are verified here, not as separate tasks — they test already-built
  behaviour end-to-end rather than requiring new code of their own, and by
  `T05` every prior step's fields genuinely exist to exercise.

**`depends_on` graph:** `T01 ← T02 ← T03 ← T04 ← T05`, plus `T04 ←
REQ-SB-48-US-01-T02` (cross-story, real, already `Ready`). Acyclic,
confirmed by inspection — a single linear chain with one external leaf.

**Confirmed no new backend endpoint** beyond the one additive `trigger?:
str` field on `POST /agents`'s existing `CreateAgentBody` (`T05`) — every
other backend call this story composes (`create_agent`,
`grantAgentSkill`, `updateAgentAssignment`) is `REQ-SB-37`'s own already-
`Done`, unmodified mechanism, confirmed directly against the real
`agents_router.py`/`agentsApiClient.ts`/`CreateAgentWizard.tsx`.

**New finding this pass, not present in the architect's own review-queue
entry:** `REQ-SB-48-US-01-T02`'s own locked `## Files to Modify` gives its
coder real latitude on `SkillsTree.tsx`'s filename and even whether it
becomes a standalone file at all ("a new sibling component file... vs. an
inline implementation is your own latitude"), and its own locked ACs/Tests
describe only the `mode="manage"` behaviour — no `mode` prop is named
anywhere in that task's own text. `ADR-039` and this story's own `T04`
assume a specific, mode-parameterized `SkillsTree.tsx` will exist at a
specific path. This is a real, disclosed gap between what `T04`'s
`depends_on` edge assumes and what the still-unbuilt `T02` is actually
locked to produce — flagged in full in `REVIEW-QUEUE.md`, not silently
assumed away. Trigger 7 (contradictory inputs) — folded into this story's
existing `gate: flagged` state rather than opening a second flag, per
Pipeline.md's "a batch advances clean items, parks flagged ones" model
(this story was already parked on `ADR-039`).

**Status:** `Draft → Ready`. All 11 ACs locked with at least one AC-tagged
verification step each (confirmed by cross-reference against all 5 task
`## Tests` blocks); `depends_on` acyclic. Tasks written at `status: Ready`
in lockstep, per this role's own mandatory behaviour. `gate` stays
`flagged` — the ADR-039 review is still outstanding, unresolved by this
pass; the human reviews `ADR-039`, this story's 5 tasks, and the new
`SkillsTree.tsx` shape-gap finding together in one pass.
