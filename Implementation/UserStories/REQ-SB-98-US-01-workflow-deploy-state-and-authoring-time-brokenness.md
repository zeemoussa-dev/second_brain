---
id: REQ-SB-98-US-01
title: A Workflow that says whether it is runnable — per-step failure handling, deploy state, and brokenness at authoring time
requirement_ids: [REQ-SB-98]
requirement_section: "REQ-SB-98: Author a Workflow in the UI, and Deploy It"
phase: P2
status: Draft
gate: flagged
gate_reason: "trigger-8 (two equally-valid scopings: REQ-SB-98's 'UI to create workflows' is already fully specced, decomposed and sprint-planned as REQ-SB-95-US-04 / SPRINT-089, which is Ready and parked behind two unfinished sprints — so the honest answer to the operator's request is sequencing, not new spec; this story covers only the three pieces genuinely beyond US-04, and the human should confirm that reading rather than have it chosen for them at /plan-tasks)"
sprint: ""
created: 2026-10-17
updated: 2026-10-17
---

# REQ-SB-98-US-01 — A Workflow that says whether it is runnable — per-step failure handling, deploy state, and brokenness at authoring time

## Story

**As a** Second Brain operator
**I want** a Workflow to tell me, while I am writing it, whether it can actually
run — including what happens when one of its steps fails
**So that** a Workflow stops being a document that looks ready and discovers at run
time that one of its steps is an Action no agent can perform

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-98* — raised 2026-10-17 by the operator:
  "I want a UI to Create workflows and Make Sure a Workflow is Deployed". Finding 1
  (the kind is specified and unbuilt), Finding 2 ("its deployment question is
  `REQ-SB-96`'s"), and the **What is wanted** bullets: the editor including "say
  what happens when a step fails"; the same deploy state and honesty as an Action;
  and a Workflow whose steps include an unperformable Action shown as broken **at
  authoring time, not at run time**.
- **Overlap with `REQ-SB-95-US-04`, and why this is a new story rather than an edit
  to it.** The Workflow editor the operator asked for is **already specced,
  already decomposed and already sprint-planned**:
  - `REQ-SB-95-US-04` is `status: Ready`, seven locked ACs, seven tasks, grouped
    into `SPRINT-089`.
  - Its `AC-01` covers authoring a Workflow end to end (id, the kind of request it
    handles, ordered steps each naming a catalogued Action, per-step confirmation,
    what is reported back). Its `AC-02` covers the step editor offering only real
    catalogued Actions. `T07` is the catalogue + ordered-step editor screen.
  - `SPRINT-089` carries `depends_on_sprints: [SPRINT-087, SPRINT-088]`, neither
    finished — which is the real reason the operator cannot author a Workflow
    today. **That is sequencing, not missing specification.**
  Editing a `Ready`, fully-decomposed story would discard the decomposer's locked
  ACs and the product-owner's partition, and specs are append-only (Pipeline hard
  rule 1). So this story adds only what `REQ-SB-95-US-04` genuinely does not do.
- **The three genuine gaps**, checked against `REQ-SB-95-US-04`'s locked ACs:
  1. **Per-step failure handling.** `US-04` has per-step *confirmation* and a
     composed report, and `ADR-034`'s run record refuses to advance until a step's
     outcome is recorded — but nothing anywhere lets the operator *say* what should
     happen when a step fails. The PRD asks for it explicitly.
  2. **Deploy state per Workflow.** `US-04` never asks whether a Workflow is live
     and runnable; the PRD asks for "the same deploy state and the same honesty
     about it as an Action".
  3. **Brokenness at authoring time.** `US-04`'s `AC-02` validates only that a
     step's Action **exists in the catalogue**. The PRD asks for the stronger
     check: a step naming an Action **no agent can perform** is broken when it is
     written, not when it is run. That is `REQ-SB-97-US-01`'s per-agent
     performability verdict, lifted one level up.
- **`ADR-032`/`ADR-034` already bound the shape.** A Workflow lives at
  `<DATA_PATH>/data/Workflows/<id>/Workflow.json`; each step references an Action
  id so the editor "cannot produce a workflow pointing at an action that does not
  exist — invalid by construction rather than by review"; and the framework runs a
  Workflow against a run record, one step at a time. This story extends those
  decisions; it does not reopen them.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: The Workflow's screen says whether it is runnable, and what is stopping it

```gherkin
Given a Workflow whose steps reference catalogued Actions
When the operator opens it
Then the screen states whether this Workflow is runnable right now
  And a Workflow that is not runnable names every step that is stopping it, the
    Action that step references and the reason that Action cannot be performed
  And a Workflow every step of which can be performed says so explicitly
```

### Scenario 2: A step naming an Action no agent can perform is broken while it is being written

```gherkin
Given the operator is authoring a Workflow
When a step names a catalogued Action that exists but that no allowed agent can
    actually perform
Then that step is shown as broken at authoring time, before any run
  And the reason given is the same per-agent reason the Action's own screen gives
  And a step whose Action every allowed agent can perform shows no such warning
```

### Scenario 3: A broken Workflow cannot be saved as ready

```gherkin
Given a Workflow with at least one step whose Action cannot be performed
When the operator saves it
Then it is not recorded as ready or deployed
  And its stored state says it is incomplete, naming the step responsible
  And the operator can still save the work in progress rather than losing it
  And making the offending step performable and re-saving records it as ready
    without any other edit
```

### Scenario 4: The operator says what happens when a step fails

```gherkin
Given the operator is authoring a Workflow
When a step is given its failure handling — stop the run and report, or carry on
    to the next step
Then the choice is stored with that step and returned unchanged when the Workflow
    is reopened
  And a step saved without an explicit choice takes the documented default rather
    than being left undefined
```

### Scenario 5: A run honours the failure handling that was documented

```gherkin
Given a Workflow whose second step is documented as stop-and-report on failure
When a run reaches that step and the step fails
Then the run stops there, no later step is started, and the report names the step
    that failed and why
  And a run of a Workflow whose failing step is documented as carry-on continues to
    the next step, and the report records that step as failed rather than as done
  And in both cases the run record holds the real outcome of every step attempted
```

### Scenario 6: Runnability is current because it is never stored

```gherkin
Given a Workflow reported as runnable
When the Skill behind one of its steps' Actions is undeployed from the relevant
    profile
Then the next read reports that Workflow as not runnable, naming the step
  And no stale runnable verdict is served from anything written into Workflow.json
  And restoring the deployment restores the runnable verdict with no edit to the
    Workflow
```

### Scenario 7: An unreadable install does not become a verdict

```gherkin
Given the Hermes install cannot be read
When a Workflow's runnability is read
Then the screen says the answer is unknown, and why
  And no Workflow is reported as runnable on the strength of an unread install
```

## Affected Screens

- `src/frontend/src/pages/SettingsWorkflowsPage.tsx` (name indicative — **created
  by `REQ-SB-95-US-04-T07`, not by this story**) — the Workflow editor gains a
  per-step failure-handling control (Scenario 4), a per-step broken marker with its
  reason (Scenario 2), and a Workflow-level runnable/not-runnable state with the
  unknown case (Scenarios 1, 3, 7). The Workflows list gains the same state as a
  badge.
- `html-prototype/settings.html` — **not** the design authority (see Notes →
  Prototype parity).

## Dependencies

- **Blocked by:**
  - `REQ-SB-95-US-04` — the Workflow kind, its store, its editor and `ADR-034`'s
    run record. There is nothing to extend until `SPRINT-089` lands, and
    `SPRINT-089` itself waits on `SPRINT-087` and `SPRINT-088`.
  - `REQ-SB-97-US-01` — Scenarios 1, 2, 3 and 6 are that story's per-agent
    performability verdict, aggregated over a Workflow's steps. Computing it a
    second way here is the duplicated-logic failure `REQ-SB-96` exists to stop.
- **Related to:** `REQ-SB-96-US-01` (the per-profile truth both verdicts rest on),
  `REQ-SB-96-US-02` (deploying the missing Skill is how a broken step is fixed),
  `REQ-SB-95-US-03` (the call gate each step passes through at run time).
- **External:** a real Hermes install with more than one profile.

## Constraints

- **Do not reopen `ADR-032` or `ADR-034`.** The store, the step-references-an-Action
  rule, and the framework-runs-the-workflow run model stand; this story adds fields
  and verdicts within them.
- **Do not weaken `REQ-SB-95-US-04`'s locked ACs.** `AC-02`'s refusal of an unknown
  action id stays a refusal; this story's brokenness is a *different and weaker*
  condition (the Action exists but cannot be performed) and must not be collapsed
  into it — an operator must still be able to save work in progress.
- **Never stored, always computed** — runnability is a function of deployment
  state elsewhere, so a stored verdict is wrong from the moment it is written.
  Only the operator's *documented intent* (failure handling) is persisted.
- **One source of deployment truth** — `REQ-SB-96-US-01`'s comparison, through
  `REQ-SB-97-US-01`'s per-Action verdict. Never `deployed_to`.
- **Ordered steps only.** `REQ-SB-95-US-04` excludes branching, loops and
  conditional steps; "carry on after a failure" is failure handling, not a branch,
  and nothing here introduces control flow beyond order.
- **`Pipeline` is untouched** (`ADR-032`).
- **One Manager is the sole gateway**; raw I/O stays in `data_access/`.

## Implementation Tasks

<!-- Owned by the decomposer at /plan-tasks. -->

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **The Workflow editor, its store, its inventory/export entries, its delete
  protection and its run model** — all `REQ-SB-95-US-04`, `SPRINT-089`. REQ-SB-98's
  "a UI to create workflows" is that sprint finishing, not a second editor.
- **Deploying anything** — `REQ-SB-96-US-02` owns the deploy operation; this story
  reports state and never writes into the install.
- **Retrying, resuming or rolling back a failed run.** Failure *handling* here is
  the documented stop-or-continue choice, nothing more.
- **Branching, conditional steps or loops** (already excluded by
  `REQ-SB-95-US-04`).
- **Scheduling a Workflow** — a time-triggered thing is a Pipeline (`ADR-032`).
- **Inferring a Workflow, or suggesting repairs to a broken one.**

## Notes

**Prototype parity (`html-prototype/settings.html` is the only prototype screen in
scope):**

- Settings landing navigation — **Superseded**: the real `SettingsPage.tsx`
  icon-card grid replaced the prototype's flat card stack on 2026-08-27.
- Workflows list and ordered-step editor regions — **Specced elsewhere**:
  `REQ-SB-95-US-04` owns them, with its own parity note on the same screen. This
  story adds one control per step, one marker per step, and one state badge.
- The per-step failure-handling control and the runnable/not-runnable state —
  **Specced functional-first** (Scenarios 1–4), on already-approved `.input`/
  `.btn`/badge controls, under the operator's 2026-08-31 functional-first
  precedent (recorded in `REQ-SB-85-US-01`'s `gate_reason`). If the human
  disagrees, `/design REQ-SB-98` before `/plan-tasks` is the cheap correction.

**Architect pointers for `/plan-tasks` (context, not decisions):**

- Whether failure handling is a per-step enum on `Workflow.json` or a workflow-level
  default with per-step override is open; every AC here asserts behaviour only.
- Scenario 5 is a property of `ADR-034`'s run record — the same reason
  `REQ-SB-95-US-04`'s `AC-03` was rewritten against it: as prose about model
  behaviour it would be unverifiable.
- Scenario 3's "incomplete" state is deliberately not named as a field; note that
  `REQ-SB-95-US-04` has no readiness concept at all today, so this is the first one.
- The aggregation in Scenario 1 is over an allowed-caller set that belongs to each
  *Action* (`allowed_callers`, `ADR-033`), not to the Workflow — whether a Workflow
  acquires its own caller set is a real question and is not assumed here.

**Audit breadcrumb:**

gate: flagged 2026-10-17 — trigger 8 (two equally-valid scopings against the
`Ready`, fully-decomposed `REQ-SB-95-US-04`/`SPRINT-089`; this story took the
narrower one, and the operator's actual request is answered mostly by finishing
`SPRINT-087` → `SPRINT-088` → `SPRINT-089`). `REQ-SB-98` is finalised in the PRD
with no `<!-- Draft -->` marker; no ADR created or changed by this pass; no new
`ESCALATIONS.md` entry; not oversized.
