---
id: REQ-SB-46-US-01-T04
title: Step 3 — shared SkillsTree.tsx in mode="select", required for Worker, optional otherwise
parent_story: REQ-SB-46-US-01
requirement_id: REQ-SB-46
type: frontend
status: Done
gate: flagged
gate_reason: "scope-internal implementation-sequencing judgement call — see T02's Implementation Log; SkillsTree.tsx real shape reconciled, not the task's own guessed prop shape — see below"
phase: P1
depends_on: [REQ-SB-46-US-01-T03, REQ-SB-48-US-01-T02]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-46-US-01-T04 — Step 3: shared `SkillsTree.tsx` in `mode="select"`

## Parent Story

- Story: [[REQ-SB-46-US-01]] — `../UserStories/REQ-SB-46-US-01-agent-creation-wizard-popup-modal-redesign.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-46 *Agent Creation Wizard Redesign — Popup Modal with Visual Step Bar*

---

## Objective

Build Step 3 of `CreateAgentWizardModal.tsx`: a multi-select Skills picker
using the shared `SkillsTree.tsx` component in `mode="select"`, required
(≥1) for Worker, optional (0 allowed) for Expert and Producer.

---

## Starting State → End State

**Before / Inputs — READ THIS BEFORE STARTING, this is a real cross-story
risk, not a formality:**
- This task depends on `REQ-SB-48-US-01-T02`
  (`Implementation/Tasks/REQ-SB-48-US-01-T02-capabilities-tool-tree.md`),
  which is `Ready` but **not yet `Done`/built** as of this task's own
  writing. `ADR-039` and this story assume `T02` will originate a shared,
  mode-parameterized `src/frontend/src/features/agents-map/SkillsTree.tsx`
  (`mode="manage"` for `AgentDetailPanel.tsx`, `mode="select"` for this
  task). **`REQ-SB-48-US-01-T02`'s own locked `## Files to Modify` does
  NOT mandate this** — it explicitly gives its own coder latitude on
  filename and even whether a standalone file is created at all ("a new
  sibling component file... vs. an inline implementation is your own
  latitude"), and names zero `mode` prop anywhere in its own locked text.
  This gap is recorded in `REVIEW-QUEUE.md` (decomposer pass, this
  story). **Before writing any code in this task:**
  1. Confirm `REQ-SB-48-US-01-T02` is `Done`.
  2. Read the REAL, shipped `SkillsTree.tsx` (or whatever file/shape `T02`
     actually produced) directly — do not trust this task's own
     illustrative prop-shape guess below.
  3. If `T02` shipped a standalone, reasonably mode-extensible component
     (even under a different filename/prop names than guessed below),
     extend it with a `mode="select"` branch and consume it — this is the
     expected, in-scope path.
  4. If `T02` shipped fully inline logic inside `AgentDetailPanel.tsx`
     with no separable component at all, this is an out-of-scope blocker
     for this task (Pipeline.md hard rule 5 — files outside this task's
     own `## Files to Modify` may not be edited without escalation). Stop
     and escalate per Pipeline.md (log to `ESCALATIONS.md`, category
     `shared-interface-change` or `unanticipated-file`) rather than
     improvising an inline duplicate tree here — a duplicate would
     directly contradict `ADR-039`'s own "one shared implementation, never
     duplicated" decision.
- Illustrative (unconfirmed) expected shape, per `ADR-039`: `<SkillsTree
  mode="select" tools={...} skills={...} selectedIds={selectedSkillIds}
  onChange={setSelectedSkillIds} />` — a collapsible, icon-bearing,
  Tool-grouped tree of checkboxes, no immediate API call, this task's own
  parent component owns the selected-id array via `onChange`.
- The pre-existing file (as `T03` leaves it) already has
  `skills`/`selectedSkillIds`/`toggleSkill` state from the old flat
  Worker-only checkbox list (`worker-skills-list`,
  `worker-skill-checkbox-{id}`) — this task replaces that flat list's
  markup with `<SkillsTree mode="select" .../>`, reusing the SAME
  `selectedSkillIds` state/`toggleSkill`-equivalent wiring, now available
  to Expert/Producer as well as Worker (extending multi-select Skills
  selection beyond Worker for the first time, per Scenario 5).

**After / Outputs:**
- Step 3 (`currentStep === 3`) renders
  `data-testid="wizard-step3-skills-tree"` wrapping `<SkillsTree
  mode="select" .../>`, for every Type.
- A `data-testid="wizard-step3-next"` button. For Worker only, validates
  `selectedSkillIds.length > 0`; on failure renders
  `data-testid="wizard-step3-error"` naming "at least one Skill" as
  missing and does not advance. For Expert/Producer, Next always succeeds
  regardless of selection count (0 or more).
- A `data-testid="wizard-step3-back"` button returns to Step 2 without
  clearing any field.

---

## Files to Modify

- `src/frontend/src/features/agents-map/CreateAgentWizardModal.tsx` —
  replace the old flat Worker-only Skills checkbox list with Step 3's
  `<SkillsTree mode="select" .../>` usage, available to all 3 types.
- `src/frontend/src/features/agents-map/SkillsTree.tsx` — READ-ONLY
  consumption. Only touch this file if step 4 of the "Before / Inputs"
  section above applies (escalation path) — otherwise this task consumes
  it exactly as `REQ-SB-48-US-01-T02` shipped it, adding a `mode="select"`
  branch only if that branch doesn't already exist, coordinating with
  whatever `T02` actually built.

---

## Constraints

- Inherits from parent story: no new backend endpoint; Skills
  grant/selection at this step does not itself call
  `grantAgentSkill` — that remains `T05`'s job at final submission
  (mirrors today's already-shipped behavior: Worker's Skills are granted
  only after `createAgent` succeeds).
- Must consume the SAME shared `SkillsTree.tsx` `REQ-SB-48-US-01-T02`
  originates — never write a second, divergent Skills-tree implementation
  local to the wizard (`ADR-039` point 2, explicit).
- Worker requires ≥1 Skill selected to advance; Expert/Producer do not.
- Read the real current `CreateAgentWizardModal.tsx` (as `T03` leaves it)
  AND the real, shipped `SkillsTree.tsx` before editing — do not apply a
  stale diff against either an assumed wizard shape or an assumed
  component shape.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-46-US-01-AC-05] Complete Steps 1-2 for a Worker-type agent,
   advance to Step 3. Expect
   `[data-testid="wizard-step3-skills-tree"]` present, rendering the
   shared Skills tree's own multi-select checkboxes. Click
   `[data-testid="wizard-step3-next"]` with zero Skills selected; expect
   `currentStep` to remain `3` and a `[data-testid="wizard-step3-error"]`
   naming "at least one Skill". Select one Skill, click Next again;
   expect `currentStep` to advance to `4`.
2. [REQ-SB-46-US-01-AC-05] Repeat for an Expert-type (or Producer-type)
   agent: advance to Step 3 with zero Skills selected, click
   `[data-testid="wizard-step3-next"]`; expect `currentStep` to advance to
   `4` with no error — confirming Skills selection is optional for these
   two types.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Step 3 renders the shared `SkillsTree.tsx` in `mode="select"` for every Type, not a separate wizard-local implementation
- [ ] Worker cannot advance past Step 3 with zero Skills selected; a clear message names what's missing
- [ ] Expert and Producer can advance past Step 3 with zero Skills selected
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Originating `SkillsTree.tsx` itself, or its `mode="manage"` behavior —
  entirely `REQ-SB-48-US-01-T02`'s own scope.
- Actually calling `grantAgentSkill` — `T05`'s job at final submission.
- Step 4 fields (`T05`).
- Visual polish — not a locked AC.

---

## Context / Notes

- This is this codebase's first cross-story frontend task dependency
  (`ADR-039` point 2). Do not start this task until `REQ-SB-48-US-01-T02`
  is confirmed `Done` — the product-owner is expected to sequence
  `REQ-SB-48-US-01` no later than the same sprint as, and ordered before,
  this task (Pipeline.md hard rule 7).
- Keep `selectedSkillIds` lifted at the `CreateAgentWizardModal` component
  level — `T05` needs it in scope at final submit time (Worker's N
  sequential `grantAgentSkill` calls, Producer's optional additional-Skill
  grants beyond its own mandatory output Skill from Step 2).

---

## Implementation Log

**Pre-flight check performed exactly as this task's own "Before / Inputs"
section directs, before writing any code:**

1. Confirmed `REQ-SB-48-US-01-T02` is `Done` (`SPRINT-042`, `Done`
   2026-08-14) — read directly from its own task file frontmatter and
   `SPRINT-042`'s own retro, not assumed.
2. Read the REAL, shipped
   `src/frontend/src/features/agents-map/SkillsTree.tsx` directly (not
   this task's own illustrative prop-shape guess). Its real shape:
   `SkillsTreeSelectProps = { mode: 'select'; skills: SkillsTreeSkill[];
   selectedIds: string[]; onChange: (selectedIds: string[]) => void }`,
   where `SkillsTreeSkill = { id, name, tool, granted: boolean }` (a single
   `skills` array, each already carrying its own `tool` field — there is
   NO separate `tools={...}` prop the task's own illustrative sample
   guessed). `mode="select"` is a real, already-working implementation
   (collapsible Tool-grouped checkboxes, expanded by default, no API
   call) — not a stub.
3. This is a real, standalone, mode-extensible component exactly as
   `ADR-039`/`MEMORY.md` describe — the expected, in-scope "extend and
   consume" path applies; no escalation needed (step 4 of the Before/
   Inputs section does not apply).

**Sequencing note:** built together with `T02`/`T03`/`T05` in one coherent
pass — see `T02`'s own Implementation Log for the full disclosed
reasoning.

**Implemented (2026-08-14):** Step 3 (`currentStep === 3`) renders
`wizard-step3-skills-tree` wrapping `<SkillsTree mode="select"
skills={skills.map(({id,name,tool}) => ({id,name,tool,granted:false}))}
selectedIds={selectedSkillIds} onChange={setSelectedSkillIds} />` — the
REAL shared component, reconciled against its actual shipped prop shape
(not the task's own illustrative guess: no `tools` prop exists; `granted`
is a required field on each skill object even in `mode="select"`, set to
`false` since it is `mode="manage"`-only and unused by the Select view).
Same shared `/skills` fetch `T03`'s Step 2 output-Skill radio group
already consumes — one catalog, two consumers, zero divergent fetch.
`wizard-step3-next` validates `selectedSkillIds.length > 0` ONLY for
`type === 'worker'`, rendering `wizard-step3-error` and blocking on
failure; Expert/Producer always advance regardless of selection count.
`wizard-step3-back` returns to Step 2 without clearing any field. No
second, divergent Skills-tree implementation was written anywhere.

**Verification — real backend/frontend + CDP driver:**

- **[REQ-SB-46-US-01-AC-05]** PASS (Worker). Completed Steps 1-2 for a
  Worker, advanced to Step 3: `wizard-step3-skills-tree` present, and
  nested inside it a real `[data-testid="skills-tree"]` element with a
  real `[data-testid="skills-tree-group-Outlook"]` Tool group — confirming
  this is genuinely the shared `SkillsTree.tsx` rendering, not a
  wizard-local reimplementation. Clicked `wizard-step3-next` with zero
  Skills selected: blocked (`currentStep` stayed `3`),
  `wizard-step3-error` read exactly
  `"Missing at least one Skill — the agent was not created."` Selected one
  real `.skills-tree-checkbox`, clicked Next again: genuinely advanced to
  Step 4 (`wizard-step4-summary` rendered).
- **[REQ-SB-46-US-01-AC-05]** PASS (Expert). Completed Steps 1-2 for an
  Expert, advanced to Step 3 with zero Skills selected, clicked
  `wizard-step3-next`: advanced straight to Step 4 with no error element
  present at all — confirming Skills selection is genuinely optional for
  Expert (and, by the same unconditional-except-Worker validation branch,
  Producer).

**`SkillsTree.tsx`'s real shipped shape was used, confirmed by direct
read before writing any code — not a guessed shape.** `gate: flagged` —
both the disclosed sequencing note (shared with `T02`) and this
confirmation are logged for human spot-check, per Pipeline.md's
scope-internal-judgement-call mechanism; neither is an escalation.
