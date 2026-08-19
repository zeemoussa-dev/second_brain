---
id: REQ-SB-46-US-01-T03
title: Step 2 — Working-mode selector, plus Producer-only Purpose and output-Skill fields
parent_story: REQ-SB-46-US-01
requirement_id: REQ-SB-46
type: frontend
status: Done
gate: flagged
gate_reason: "scope-internal implementation-sequencing judgement call — see T02's Implementation Log"
phase: P1
depends_on: [REQ-SB-46-US-01-T02]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-46-US-01-T03 — Step 2: Working-mode selector, plus Producer-only Purpose/output-Skill

## Parent Story

- Story: [[REQ-SB-46-US-01]] — `../UserStories/REQ-SB-46-US-01-agent-creation-wizard-popup-modal-redesign.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-46 *Agent Creation Wizard Redesign — Popup Modal with Visual Step Bar*

---

## Objective

Build Step 2 of `CreateAgentWizardModal.tsx`: a Working-mode
(Instructions/Guardrails) selector shown for every type, plus a Purpose
field and single-select output Skill control shown only for Producer.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has produced a working Step 1 that advances to `currentStep === 2`
  on a valid "Next". Step 2 today (pre-this-task) does not exist as its
  own step — the pre-existing file's Producer branch already has
  `purposeDraft`/`outputSkills`/`selectedOutputSkillId` state and a
  `producer-output-skill-list` radio group; this task relocates them into
  Step 2, gated by `type === 'producer'`, rather than writing them from
  scratch.
- `AgentDetail`'s `working_mode: 'autonomous' | 'supervised' | 'manual'`
  and `updateAgentAssignment`'s `working_mode?: string` body param already
  exist and are already wired end-to-end elsewhere (`AgentDetailPanel.tsx`,
  `REQ-SB-21-US-01`, `Done`) — this task only adds a NEW UI surface for
  setting it at creation time; it does not touch the backend.

**After / Outputs:**
- Step 2 (`currentStep === 2`) renders a
  `data-testid="wizard-step2-working-mode-select"` `<select>` with options
  Autonomous/Supervised/Manual, defaulting to `'autonomous'`, for every
  Type.
- When `type === 'producer'` only, Step 2 additionally renders:
  - `data-testid="wizard-step2-purpose-input"` (the existing `purposeDraft`
    textarea, relocated here unchanged).
  - `data-testid="wizard-step2-output-skill-list"`, one
    `data-testid="wizard-step2-output-skill-radio-{skillId}"` radio per
    catalog Skill (the existing `outputSkills`/`selectedOutputSkillId`
    single-select radio group, relocated here unchanged).
- A `data-testid="wizard-step2-back"` button returns to `currentStep = 1`
  without clearing any Step 1 or Step 2 field. A
  `data-testid="wizard-step2-next"` button validates: (Producer only)
  `purposeDraft` non-empty and `selectedOutputSkillId` non-empty — mirrors
  the existing `missing.push('a Purpose')`/`missing.push('an output
  Skill')` checks, now evaluated at Step 2. On failure, render
  `data-testid="wizard-step2-error"` naming what's missing, do not
  advance. On success, set `currentStep = 3`.
- Expert and Worker's Step 2 has only the Working-mode selector — no
  Purpose/output-Skill fields, and "Next" for those two types has no
  Step-2-specific required field to check (the working-mode selector
  always has a valid default, never itself blocking).

---

## Files to Modify

- `src/frontend/src/features/agents-map/CreateAgentWizardModal.tsx` —
  add Step 2 content (Working-mode selector + Producer-conditional
  Purpose/output-Skill), relocating the existing Producer Purpose/output-
  Skill state and markup out of the old single-form Producer branch.

---

## Constraints

- Inherits from parent story: Working-mode is not a new backend field
  (`REQ-SB-21-US-01`, already `Done`) — this task adds no backend call;
  `T05` is what actually sends `working_mode` on the existing
  `updateAgentAssignment` PATCH at final submission.
- Neither Expert nor Worker gets an output/output-destination field at
  Step 2 — only Producer, per the story's own field-to-step mapping.
- Do not clear Step 1 field values when navigating Back from Step 2 to
  Step 1, or Step 2's own values when navigating Back then Next again.
- Read the real current `CreateAgentWizardModal.tsx` (as `T02` leaves it)
  before editing.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-46-US-01-AC-04] Complete Step 1 for an Expert-type agent,
   advance to Step 2. Expect
   `[data-testid="wizard-step2-working-mode-select"]` present, defaulted
   to Autonomous, and zero elements matching
   `[data-testid="wizard-step2-purpose-input"]` or
   `[data-testid="wizard-step2-output-skill-list"]`. Go Back to Step 1,
   change Type to Producer, re-complete Step 1, advance to Step 2 again.
   Expect the same Working-mode selector PLUS
   `[data-testid="wizard-step2-purpose-input"]` and
   `[data-testid="wizard-step2-output-skill-list"]` (with at least one
   `wizard-step2-output-skill-radio-*` row) now present.
2. [REQ-SB-46-US-01-AC-10] (Step 2 half) With a Producer-type agent on
   Step 2, leave Purpose empty, click
   `[data-testid="wizard-step2-next"]`. Expect `currentStep` to remain `2`
   and a `[data-testid="wizard-step2-error"]` naming "a Purpose" as
   missing. Fill Purpose, leave the output Skill unselected, click Next
   again; expect the same block-and-message behavior naming "an output
   Skill".

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Step 2 shows a Working-mode selector (defaulting Autonomous) for every Type
- [ ] Step 2 shows Purpose + single-select output Skill ONLY for Producer
- [ ] "Next" blocks advancement with a clear missing-field message when Producer's Purpose or output Skill is empty
- [ ] Back/Next navigation never clears an already-entered Step 1 or Step 2 value
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Step 3/4 fields (`T04`/`T05`).
- Sending `working_mode` to the backend (`T05`).
- Visual polish — not a locked AC.

---

## Context / Notes

- The story's own `## Context` names Working-mode-as-"Instructions/
  Guardrails" as a disclosed, human-confirmed judgment call (architect
  pass, 2026-08-14) — not re-litigated by this task.
- Keep `purposeDraft`/`selectedOutputSkillId`/the new working-mode state
  lifted at the `CreateAgentWizardModal` component level (not step-local)
  — `T05` needs them in scope at final submit time.

---

## Implementation Log

**Sequencing note:** built together with `T02`/`T04`/`T05` in one coherent
pass over `CreateAgentWizardModal.tsx` — see `T02`'s own Implementation Log
for the full disclosed reasoning (this file's own decomposer Notes already
describe all 5 tasks as one tightly-coupled chain over a single file).
This task is still verified independently, in isolation against its own
real, live Step 2 behavior, below.

**Implemented (2026-08-14):** Step 2 (`currentStep === 2`) renders
`wizard-step2-working-mode-select` (Autonomous/Supervised/Manual,
defaulting `'autonomous'`) for every Type, plus — only when `type ===
'producer'` — the relocated `purposeDraft` textarea
(`wizard-step2-purpose-input`) and the relocated `selectedOutputSkillId`
radio group (`wizard-step2-output-skill-list`, one
`wizard-step2-output-skill-radio-{id}` per catalog Skill, same single
shared `/skills` fetch Step 3 also consumes). `wizard-step2-back` returns
to `currentStep = 1` without clearing any field; `wizard-step2-next`
validates `purposeDraft`/`selectedOutputSkillId` non-empty ONLY for
Producer, rendering `wizard-step2-error` and blocking advancement on
failure, mirroring the pre-existing `missing.push('a Purpose')`/
`missing.push('an output Skill')` copy exactly.

**Verification — real backend/frontend + CDP driver, continuing directly
from `T02`'s own real Step 1 state:**

- **[REQ-SB-46-US-01-AC-04]** PASS. Completed Step 1 as Expert, advanced:
  `wizard-step2-working-mode-select` present, value `"autonomous"`;
  `wizard-step2-purpose-input`/`wizard-step2-output-skill-list` both
  absent. Went Back to Step 1, switched Type to Producer, re-advanced:
  Working-mode selector still present PLUS `wizard-step2-purpose-input`
  and `wizard-step2-output-skill-list` (11 real
  `wizard-step2-output-skill-radio-*` rows, the real `/skills` catalog)
  now present.
- **[REQ-SB-46-US-01-AC-10]** (Step 2 half) PASS. Producer on Step 2,
  empty Purpose, click Next: blocked (`currentStep` stayed `2`),
  `wizard-step2-error` read
  `"Missing a Purpose, an output Skill — the agent was not created."`
  (naming "a Purpose" as required; output Skill was also legitimately
  unfilled at that point, correctly co-named). Filled Purpose, left output
  Skill unselected, clicked Next again: blocked again, error named
  `"Missing an output Skill — the agent was not created."` exactly.
  Selected an output Skill radio and clicked Next again: genuinely
  advanced to Step 3 (`wizard-step3-skills-tree` rendered) — confirming
  the block is real, not permanent.

`gate: flagged` — same disclosed sequencing note as `T02`, not a new
finding.
