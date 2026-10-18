---
id: REQ-SB-95-US-04
title: Workflow as the seventh artifact kind — the operator documents how a kind of request is handled
requirement_ids: [REQ-SB-95]
requirement_section: "REQ-SB-95: An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution"
phase: P2
status: In Progress
gate: clear
gate_reason: "RESOLVED operator confirmed ADR-034, 2026-10-17 — was: trigger-3 (ADR-034 created — a Workflow is run step-by-step by the framework against a run record, not recited into the agent's context)"
sprint: SPRINT-089
created: 2026-10-16
updated: 2026-10-18  # coder: T04 Blocked on ESC-077 with AC-04/AC-05/AC-07 all verified (12 AC-tagged tests; the seventh kind is live across all six business/logic/artifact_*.py modules, incl. the import conflict gate per ESC-076) — the block is a Done task's test that used `workflow` as its unsupported-kind example; T07 waits on T04, T05 unaffected. T03 Done (AC-01, AC-02 verified over the HTTP surface) — T05 and T07 unblocked. T02 Done (AC-02, AC-06; ESC-075 Resolved). T01 Done (AC-01, AC-07)
---

# REQ-SB-95-US-04 — Workflow as the seventh artifact kind — the operator documents how a kind of request is handled

## Story

**As a** Second Brain operator
**I want** to document, as a real artifact, the ordered steps an agent should
take when a particular kind of request arrives — which steps need my
confirmation and what gets reported back
**So that** multi-action intents follow the handling I decided on, rather than
whatever the model improvises that day

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-95* — the third **What is wanted**
  bullet: "Workflows, as a first-class artifact kind. An intent with multiple
  actions: how the agent should behave when a particular kind of request arrives
  — the ordered steps, which need confirmation, what is reported back.
  **Documented by the operator, not inferred by the model.**" The requirement's
  own motivating example is the operator's "Give me the list of Actions Assigned
  to my Team and send it to me by Mail" — one intent, several actions.
- **Architecture is already settled — `ADR-032`** (Accepted 2026-10-16, pending a
  human look): `Workflow` becomes the **seventh artifact kind** at
  `<DATA_PATH>/data/Workflows/<id>/Workflow.json`; "Each step references an
  Action id, so the editor cannot produce a workflow pointing at an action that
  does not exist — **invalid by construction rather than by review**". `ADR-032`
  also decides explicitly that **`Pipeline` is left exactly as it is**: "A
  Workflow is intent-triggered, a Pipeline is time-triggered. They may converge
  later... and that is not worth rebuilding a working thing for now."
- **Sibling stories.** Fourth of `REQ-SB-95`'s five, and the one that depends on
  the most: it is meaningless without `US-02`'s Action catalogue (steps reference
  Action ids) and it reaches agents through `US-03`'s publication seam. It is
  kept separate because it is genuinely additive — the three motivating requests
  in the PRD are served by `US-01`, `US-03` and `US-05`, while Workflows are what
  make the multi-action one repeatable.
- **Grounded against the real code, not guessed.** `Pipeline` already exists as a
  step-based artifact with `depends_on` edges describing a scheduled Hermes cron
  job (`business/core/pipelines/`), and `artifacts_inventory.py` composes exactly
  five Managers today (its header states "these are the only 5"). The `Index`
  precedent (2026-09-06) is the measured template for adding a kind across
  inventory, export, import and the dependency resolver.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: The operator documents a multi-action intent as a Workflow

```gherkin
Given this install has a real Actions catalogue
When the operator saves a Workflow with an id, the kind of request it handles,
    an ordered list of steps each naming a catalogued Action, a per-step
    confirmation flag, and what is reported back
Then the Workflow is stored for this install at
    <DATA_PATH>/data/Workflows/<id>/Workflow.json
  And reopening it returns the same steps in the same order, with the same
    per-step confirmation flags and the same report definition, nothing dropped
    or duplicated
```
<!-- AC-ID: REQ-SB-95-US-04-AC-01 -->

### Scenario 2: A Workflow cannot reference an action that does not exist

```gherkin
Given the operator is saving a Workflow
When a step names an action id that is not in the catalogue
Then the save is refused, naming which step and which unknown action id, and
    nothing is written
  And an existing Workflow updated the same way is left unchanged on disk
  And the step editor offers only real catalogued Actions fetched from the live
    catalogue, so the invalid state is not reachable through the screen
```
<!-- AC-ID: REQ-SB-95-US-04-AC-02 -->

### Scenario 3: A matching request is handled by the documented Workflow

```gherkin
Given a published Workflow for a particular kind of request
When a run of that Workflow is started by a request of that kind
Then the framework hands back exactly one next step at a time, in the documented
    order, and refuses to advance until the current step's outcome is recorded
  And a step marked as needing confirmation pauses the run at an
    awaiting_confirmation Action-call record until the operator answers
  And the report back is composed from the recorded step outcomes, so a failed
    step is never reported as done
  And the run record holds every documented step and no step that is not in the
    Workflow
```
<!-- AC-ID: REQ-SB-95-US-04-AC-03 -->

### Scenario 4: Workflows appear in the artifact inventory as a seventh kind

```gherkin
Given this install has real Workflows
When the artifact inventory is read and the operator opens Settings → Artifacts
Then the Workflows are listed under their own "workflow" kind alongside skill,
    template, agent, pipeline, index and action
  And every pre-existing kind returns exactly the entries it returned before the
    seventh kind existed
```
<!-- AC-ID: REQ-SB-95-US-04-AC-04 -->

### Scenario 5: An exported Workflow carries the Actions its steps reference

```gherkin
Given a Workflow whose steps reference catalogued Actions
When the operator exports that Workflow as part of a portable bundle
Then the same dependency closure that already pulls an Agent's Skills in
    resolves every Action its steps name into the bundle, recursing into those
    Actions' own implementation Skills, under explicitly-named payload folders
  And importing that bundle onto another install produces a Workflow whose every
    step resolves there too
```
<!-- AC-ID: REQ-SB-95-US-04-AC-05 -->

### Scenario 6: Removing an Action a Workflow depends on cannot silently break it

```gherkin
Given a catalogued Action named by a step of an existing Workflow
When deletion of that Action is attempted
Then the operator is told which Workflows reference it and the Action is not
    deleted
  And no Workflow is left holding a step that points at nothing
  And an Action no Workflow references deletes normally
```
<!-- AC-ID: REQ-SB-95-US-04-AC-06 -->

### Scenario 7: Existing scheduled Pipelines are untouched

```gherkin
Given this install has real, running Pipelines on their Hermes cron schedules
When Workflow is added as the seventh artifact kind
Then every existing Pipeline keeps its own id, steps, schedule and behaviour,
    and PipelineManager and the Pipeline store are unchanged
  And no Pipeline is converted into, replaced by, or re-labelled as a Workflow
```
<!-- AC-ID: REQ-SB-95-US-04-AC-07 -->

## Affected Screens

- **New** `src/frontend/src/pages/SettingsWorkflowsPage.tsx` (name indicative) —
  the Workflows catalogue and the editor for one Workflow: the intent it handles,
  an ordered list of steps each picking a real catalogued Action, a
  per-step confirmation toggle, and what is reported. Reuses the live approved
  `.item-list`/`.item-row` list shape and `.input`/`.btn`/`Save changes` form
  conventions.
- `src/frontend/src/pages/SettingsPage.tsx` — one more card in the live
  `SETTINGS_SECTIONS` grid (or a shared Actions & Workflows entry — the
  architect's call).
- `src/frontend/src/pages/SettingsArtifactsPage.tsx` — the cross-kind inventory
  gains a seventh kind (Scenario 4); no new visual pattern.
- `html-prototype/settings.html` — **not** the design authority (see Notes →
  Prototype parity).

## Dependencies

- **Blocked by:** `REQ-SB-95-US-02` — steps reference Action ids, so the Action
  kind must exist first. `REQ-SB-95-US-03` — Scenario 3 needs the publication
  seam and the confirmation path that story builds.
- **Related to:** `REQ-SB-85-US-02`/`US-03` (export/import machinery Scenario 5
  extends); `REQ-SB-21-US-01` (Working Modes / approvals, the likely home of
  per-step confirmation).
- **External:** none new.

## Constraints

- **`<DATA_PATH>/data/Workflows/<id>/Workflow.json`** — instance data in the data
  path, edited in the app, never the repository (`ADR-032`).
- **Invalid by construction, not by review** (`ADR-032`) — referential integrity
  with the Action catalogue is enforced at save and at delete, not by a later
  audit.
- **`Pipeline` is left exactly as it is** (`ADR-032`). No convergence work, no
  migration, no shared store.
- **One Manager is the sole gateway** onto Workflow data, raw I/O in
  `data_access/` only — the standing backend layering rule.
- **Documented by the operator, not inferred by the model** — nothing in this
  story generates, suggests or auto-derives a Workflow from observed behaviour.
- **No pre-existing artifact kind changes behaviour.**

## Implementation Tasks

Final split, owned by the decomposer (2026-10-16). `depends_on` holds task ids;
cross-story edges point at `REQ-SB-95-US-02` and `US-03` tasks.

| ID | Type | Task | ACs covered | depends_on | Task File |
|---|---|---|---|---|---|
| REQ-SB-95-US-04-T01 | backend | `Workflow` entity + `WorkflowManager` + data access over `<DATA_PATH>/data/Workflows/<id>/Workflow.json` | AC-01, AC-07 | US-02-T01 | `../Tasks/REQ-SB-95-US-04-T01-workflow-entity-manager-data-access.md` |
| REQ-SB-95-US-04-T02 | backend | Referential integrity with the Action catalogue — save-time step validation and delete-time reverse lookup | AC-02, AC-06 | T01, US-02-T03 | `../Tasks/REQ-SB-95-US-04-T02-referential-integrity-with-the-action-catalogue.md` |
| REQ-SB-95-US-04-T03 | backend | Workflows CRUD API (`app/api/workflows_router.py`) | AC-01, AC-02 | T02 | `../Tasks/REQ-SB-95-US-04-T03-workflows-crud-api.md` |
| REQ-SB-95-US-04-T04 | backend | Seventh kind in inventory, dependency resolver, export, import, secret scan | AC-04, AC-05, AC-07 | T01, US-02-T04 | `../Tasks/REQ-SB-95-US-04-T04-seventh-kind-inventory-export-import-resolver.md` |
| REQ-SB-95-US-04-T05 | backend | Workflow runs — the run record, one-step-at-a-time routes, per-step confirmation, the composed report | AC-03 | T03, US-03-T04 | `../Tasks/REQ-SB-95-US-04-T05-workflow-run-record-and-routes.md` |
| REQ-SB-95-US-04-T06 | backend | Publish Workflows into agent context and handle a matching request end-to-end | AC-03 | T05, US-03-T01 | `../Tasks/REQ-SB-95-US-04-T06-publish-workflows-and-handle-a-matching-request.md` |
| REQ-SB-95-US-04-T07 | frontend | Workflows catalogue + ordered-step editor page, Settings card, route, seventh Artifacts tab | AC-01, AC-02, AC-04, AC-06 | T03, T04, US-02-T06 | `../Tasks/REQ-SB-95-US-04-T07-workflows-catalogue-screen.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **The Action catalogue itself** — `REQ-SB-95-US-02`.
- **Catalogue publication and the validating call gate** — `REQ-SB-95-US-03`;
  this story consumes both.
- **Converging Workflow and Pipeline** (`ADR-032` defers it explicitly).
- **Scheduling a Workflow.** A Workflow is intent-triggered; a time-triggered
  thing is a Pipeline.
- **Branching, loops, or conditional steps.** The PRD asks for ordered steps;
  control flow beyond order is not in scope.
- **Inferring or suggesting Workflows from the operator's history.**

## Notes

**Prototype parity (`html-prototype/settings.html` is the only prototype screen
in scope):**

- Settings landing navigation — **Superseded**: the real `SettingsPage.tsx`
  icon-card grid replaced the prototype's flat card stack on 2026-08-27; the new
  card reuses the live approved grid.
- Workflows list rows — **Specced** (Scenarios 1, 4) on the already-approved
  `.item-list`/`.item-row` family.
- The ordered-step editor (add/reorder steps, each picking a catalogued Action,
  per-step confirmation toggle) — **Specced functional-first** (Scenarios 1, 2).
  Reordering a list is the one interaction with no exact approved precedent; it
  is to be built plainly with existing controls rather than a bespoke
  drag-and-drop system, following the operator's own 2026-08-31 precedent
  (recorded in `REQ-SB-85-US-01`'s `gate_reason`, applied again on `REQ-SB-78`):
  functional-first, visual pass afterwards. If the human disagrees,
  `/design REQ-SB-95` before `/plan-tasks` is the cheap correction.
- Per-step confirmation at run time — **Specced if reused**
  (`html-prototype/my-day-approvals.html`, Scenario 3), as-is; the architect
  decides at `/plan-tasks` whether it routes through the existing Pending
  Approvals surface.

**Architect pointers for `/plan-tasks` (context, not decisions):**

- `PipelineManager` is the closest existing step-based artifact and the obvious
  shape reference — but `ADR-032` forbids sharing its store or changing it.
- Scenario 6's delete-time reverse lookup is a new edge between two of this
  requirement's own kinds; `artifact_export.py`'s existing dependency closure is
  the precedent for how dependencies between kinds are already expressed.

**Architecture scope (bounds the decomposer/coder):**
`Implementation/Architecture/architecture.md` → §An Agent Acts From a Published
Catalogue (`REQ-SB-95`) → **§Workflow — the Seventh Artifact Kind**,
**§Workflow Runs — Ordered by the Framework**, **§Adding a Kind — the Measured
Touch Points**. Read-only context: §The Action Call Gate and §Confirmation and
the Action-Call Ledger (`US-03` builds both; every Workflow step goes through
them unchanged). ADRs in force: `ADR-032` (kind, store, step-references-Action,
Pipeline untouched), `ADR-033` (the call gate each step uses), **`ADR-034`**
(this story's run model), `ADR-013`/`ADR-015` (export/import machinery).

**Architect pass 2026-10-16 — what was decided for this story:**

- **Scenario 3 is enforced, not instructed (`ADR-034`).** Publication tells the
  agent which Workflows exist and when each applies; the framework runs one
  against a run record at `<DATA_PATH>/data/WorkflowRuns/<run_id>.json`, handing
  back exactly ONE next step at a time and refusing to advance until the current
  step's outcome is recorded. "In order", "no skipped step", "no invented step"
  and "reports what the Workflow says is reported" become properties of the run
  record instead of promises by the model. Reciting the steps into agent context
  and trusting the model was considered and rejected — it is the prompt-only
  grounding `ADR-032` already rejected, one level up.
- **Per-step confirmation reuses `ADR-033`'s mechanism unchanged** — a marked
  step opens an `awaiting_confirmation` Action-call record and the run pauses
  there, visibly. It does NOT route through
  `html-prototype/my-day-approvals.html`: that subsystem's router is archived and
  absent from the repo (see `US-03`'s notes for the evidence).
- **A `skill` step is authorised, not performed, by the app** — same single-use
  grant as any Action call; the runner performs it in its own profile.
- **Scenario 6's reverse lookup runs one direction only** — a Workflow step names
  an Action; an Action knows nothing about Workflows. Deletion asks the Workflow
  side and reports referencing Workflows before removing anything. Same
  one-directional discipline `MEMORY.md` records for Skill-needs-Template.
- `ActionCalls/` and `WorkflowRuns/` are instance data, excluded from artifact
  export alongside the Operator Profile — a run is not a capability.
- `PipelineManager` is reference shape only: not shared, not extended, not
  migrated (Scenario 7 locks that in).

**Decomposer pass 2026-10-16 — AC locking and the task split:**

- Seven ACs locked, `REQ-SB-95-US-04-AC-01` … `AC-07`, one per analyst
  scenario. `AC-03` was rewritten against `ADR-034`'s run model: "in order", "no
  skipped step", "no invented step" and "reports what the Workflow says" are
  now assertions about the **run record**, which is what makes them verifiable
  at all — as prose about model behaviour they were promises nobody could check.
- `AC-07` is deliberately asserted twice (`T01` — nothing imported from or
  written into Pipelines; `T04` — Pipeline entries byte-identical before and
  after the seventh kind), because the shared-module task is where the real risk
  of disturbing Pipelines lives.
- Seven tasks, `T01`–`T07`, one more than the story's indicative six: the
  architect's run model (`ADR-034`) separates *running* a Workflow (`T05`) from
  *telling an agent it exists* (`T06`), and folding them together would not fit
  one working session. Chain: `US-02-T01 → T01 → {T02 → T03 → T05 → T06, T04}`,
  with the frontend `T07` on `T03`+`T04`+`US-02-T06`.
- Backend ACs get AC-tagged automated tests (`pytest tests/<file>.py` from
  `src/backend`), extending the `tests/test_index_artifact_kind.py` precedent
  for the add-a-kind work. The frontend declares no test runner (CLAUDE.md), so
  `T07`'s steps are structural DOM checks; reordering is built plainly, and no
  visual-polish AC was locked.
- Gate left as the architect set it (trigger 3, `ADR-034`) — no additional
  trigger fired in this pass. No `ESCALATIONS.md` entry; no new
  `REVIEW-QUEUE.md` item (the open `REQ-SB-95-US-04` entry already asks for the
  `ADR-034` review this split is built on).

**Audit breadcrumb:**

gate: flagged 2026-10-16 (architect) — trigger 3: `ADR-034` created, deciding how
a matching request is actually handled. No `ESCALATIONS.md` entry; nothing
contradicts `ADR-032` (which left the run model open), the PRD or `MEMORY.md`.
The prior analyst breadcrumb below remains accurate.

gate: clear 2026-10-16 — no triggers fired. No material assumption (every AC
restates the PRD's Workflow bullet or `ADR-032`'s decisions; representation and
run-time surface are left to the architect by writing behavioural ACs); the
requirement is finalised in the PRD with no `<!-- Draft -->` marker; no ADR
created or changed by this pass; no `ESCALATIONS.md` entry; not oversized
(~6 tasks, M) — the five-way split exists to keep it that way; no contradictory
inputs (`ADR-032` pre-empts the obvious Workflow-vs-Pipeline contradiction by
deciding Pipeline is untouched, and Scenario 7 locks that in); no second
equally-valid scoping.
