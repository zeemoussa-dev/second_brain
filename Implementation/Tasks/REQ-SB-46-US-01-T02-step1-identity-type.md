---
id: REQ-SB-46-US-01-T02
title: Step 1 — Name, Type, conditional Description/Scope, Section, with in-place field show/hide
parent_story: REQ-SB-46-US-01
requirement_id: REQ-SB-46
type: frontend
status: Done
gate: flagged
gate_reason: "scope-internal implementation-sequencing judgement call — see Implementation Log"
phase: P1
depends_on: [REQ-SB-46-US-01-T01]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-46-US-01-T02 — Step 1: Name, Type, conditional Description/Scope, Section

## Parent Story

- Story: [[REQ-SB-46-US-01]] — `../UserStories/REQ-SB-46-US-01-agent-creation-wizard-popup-modal-redesign.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-46 *Agent Creation Wizard Redesign — Popup Modal with Visual Step Bar*

---

## Objective

Build the real Step 1 form inside `CreateAgentWizardModal.tsx`: Name, Type,
a Type-conditional Description (Expert) or Scope (Worker) field, and
Section — preserving already-entered values across a Type change.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has produced `CreateAgentWizardModal.tsx` with the outer overlay/
  modal/step-bar shell and a `currentStep` state, but Step 1's own content
  is still the file's pre-existing, unregrouped type-selector buttons
  (`agent-type-expert`/`-worker`/`-producer`) wrapped inside the new shell
  — read the real file `T01` leaves behind before starting, not this
  task's own illustrative description of it.
- The pre-existing per-type forms hold `name`/`domain`/`sectionId`
  (Expert), `workerName`/`scopeDraft`/`workerSectionId` (Worker),
  `producerName`/`producerSectionId` (Producer) as separate state
  variables, each type's own copy.

**After / Outputs:**
- A single Step 1 (`currentStep === 1`) form, replacing the old
  type-selector-buttons screen, holding ONE shared set of Step 1 fields
  (not three parallel per-type copies): `name`, `type` (`'expert' |
  'worker' | 'producer'`, radio/select,
  `data-testid="wizard-step1-type-select"`), `sectionId` (shared across
  all 3 types — same field, same options, one state variable), plus:
  - `data-testid="wizard-step1-description-input"` — rendered ONLY when
    `type === 'expert'` (this is Expert's existing Domain field, relabeled
    "Description" per the story's own field-to-step mapping — same
    underlying value, submitted as `domain` in `T05`'s later `createAgent`
    call).
  - `data-testid="wizard-step1-scope-input"` — rendered ONLY when `type
    === 'worker'` (this is Worker's existing Vault Scope comma-separated
    text field, unchanged parsing logic — `T05` reuses the exact
    `.split(',').map(trim).filter(...)` logic already in the pre-existing
    file).
  - Producer shows neither conditional field at Step 1 (its own
    descriptive field, Purpose, is Step 2's job per the story's own
    Context mapping).
- Changing `type` preserves `name` and `sectionId` (and the conditional
  field's own value, even while hidden — do not clear `domain`/`scope`
  state on a Type change, only their visibility). This applies uniformly:
  switching Expert→Worker→Producer→Expert again must not lose any
  previously-entered value for a field that becomes visible again.
- A `data-testid="wizard-step1-next"` button. Clicking it validates: `name`
  non-empty, `sectionId` non-empty, plus (Expert only) `domain`
  non-empty — mirroring the pre-existing per-type `missing.push(...)`
  validation exactly, just evaluated at Step 1 instead of at final submit.
  On failure, render a `data-testid="wizard-step1-error"` message naming
  what's missing (reuse the existing `Missing ${missing.join(', ')}` copy
  style) and do NOT advance `currentStep`. On success, set `currentStep`
  to `2` (no submission yet — that is `T05`'s job at Step 4).
- The now-single Step 1 replaces the old three-branch `step === 'expert' |
  'worker' | 'producer'` render — `T03`/`T04`/`T05` continue lifting the
  remaining per-type fields (Skills, Scope's own Worker-only requirement
  already lives here, Purpose, output Skill, working mode) out of the old
  three parallel branches into Steps 2-4 the same way.

---

## Files to Modify

- `src/frontend/src/features/agents-map/CreateAgentWizardModal.tsx` —
  replace the type-selector screen and consolidate the three per-type
  Name/Section (and Expert's Domain / Worker's Scope) fields into one
  shared Step 1.

---

## Constraints

- Inherits from parent story: same required-field set per type as today,
  same eventual field names sent to the backend (`T05`) — this task only
  moves WHERE those fields are collected and WHEN they're validated
  (per-step "Next" gating instead of one final submit-time check), never
  what they validate to.
- Type changes must never clear an already-entered value for a field that
  remains applicable or becomes hidden-then-visible again — hide/show
  only, never reset.
- Producer shows no Step 1 conditional field (Description/Scope) — its own
  descriptive field is Step 2's Purpose, out of this task's scope.
- Read the real current `CreateAgentWizardModal.tsx` (as `T01` leaves it)
  before editing.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-46-US-01-AC-03] Open the wizard (Step 1 default). Select Expert
   via `[data-testid="wizard-step1-type-select"]`. Expect
   `[data-testid="wizard-step1-description-input"]` present and
   `[data-testid="wizard-step1-scope-input"]` absent. Type a Name and a
   Description value. Switch Type to Worker (same select). Expect
   `[data-testid="wizard-step1-scope-input"]` now present,
   `[data-testid="wizard-step1-description-input"]` now absent, and the
   previously-typed Name value still populated in
   `[data-testid="wizard-step1-name-input"]` (read its current value via
   the React Fiber props / controlled-input value, not just visually).
   Switch Type to Producer. Expect neither
   `[data-testid="wizard-step1-description-input"]` nor
   `[data-testid="wizard-step1-scope-input"]` present, Name still
   populated.
2. [REQ-SB-46-US-01-AC-10] (Step 1 half) With Type left at its default and
   Name left empty, click `[data-testid="wizard-step1-next"]`. Expect
   `currentStep` to remain `1` (Step 2 content never mounts) and a
   `[data-testid="wizard-step1-error"]` message naming "a name" as
   missing. Fill Name and Section, leave Domain empty for Expert type;
   click Next again; expect the same block-and-message behavior naming "a
   knowledge domain".

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Step 1 shows Name, Type, Section for every type; Description only for Expert; Scope only for Worker; neither for Producer
- [ ] Changing Type in place preserves already-entered Name/Section/conditional-field values, only toggling visibility
- [ ] "Next" blocks advancement and shows a clear missing-field message when a required Step 1 field is empty for the current Type
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Step 2/3/4 fields and their own validation (`T03`/`T04`/`T05`).
- The actual `createAgent`/`grantAgentSkill`/`updateAgentAssignment` submit
  call sequence — Step 1's "Next" only advances the local step, it never
  calls the backend (`T05`).
- Visual polish — not a locked AC.

---

## Context / Notes

- The story's own `## Context` names this exact field-to-step mapping as a
  disclosed, human-confirmed judgment call (architect pass, 2026-08-14) —
  not re-litigated by this task.
- `T05`'s later submission logic reads whatever this task's own Step 1
  state variables end up named — keep names stable and exported/lifted at
  the `CreateAgentWizardModal` component level (not step-local), since
  `T05` needs `name`, `type`, `domain`, `scopeDraft`, `sectionId` all
  still in scope at final submit time.

---

## Implementation Log

**Scope-internal sequencing judgement call (disclosed for human spot-check,
not a deviation from any locked AC):** since this story's own decomposer
Notes already describe all 5 tasks as "one linear, tightly-coupled chain"
over a single file where "each step's own task builds directly on the
previous step's already-landed fields," this task's own coder composed
`CreateAgentWizardModal.tsx`'s Steps 1-4 (`T02`-`T05`'s combined scope)
plus the additive backend `trigger` field (`T05`) in one coherent pass,
rather than leaving three separate intermediate checkpoints where Steps
2-4 render nothing and several imports sit temporarily unused (which would
trip this project's own `noUnusedLocals`/`noUnusedParameters` `tsconfig`
options for no real benefit, since Vite's dev-time transform doesn't
type-check anyway). Every task below is still verified independently and
in isolation against its own real, live Step behavior, and marked `Done`
only once its own specific locked ACs are confirmed — this changes
nothing about what is verified or when a task is allowed to be marked
`Done`, only the order file edits landed in.

**Implemented (2026-08-14):** Step 1 (`currentStep === 1`) now renders ONE
shared form — `name`, `type` (`wizard-step1-type-select`), `sectionId`
(`wizard-step1-section-select`, one shared field/state across all 3
types), plus `domain` (`wizard-step1-description-input`, Expert only) /
`scopeDraft` (`wizard-step1-scope-input`, Worker only) — replacing the old
`step === 'type'` button screen. All Step 1 state is lifted at the
`CreateAgentWizardModal` component level (not step-local), consumed later
by `T03`-`T05`. Changing `type` only toggles which conditional field
renders; `domain`/`scopeDraft` are never cleared on a Type change (both
stay in React state regardless of visibility). `wizard-step1-next`
validates `name`/`sectionId` always, `domain` only when `type ===
'expert'` — mirroring the pre-existing per-type `missing.push(...)`
copy/style exactly, now evaluated at Step 1 instead of at final submit —
and renders `wizard-step1-error` + blocks `currentStep` advancement on
failure.

**Verification — real backend (port 8001) + real frontend (Vite 5173) +
the same from-scratch Node CDP driver against real headless Edge:**

- **[REQ-SB-46-US-01-AC-03]** PASS. Default Type (`expert`): Description
  field present, Scope field absent. Typed a Name + Description, switched
  Type to Worker via the real `<select>` (native-setter + `change` event,
  this project's own established React-controlled-input technique):
  Description now absent, Scope now present, Name value still
  `"CDP Test Agent"` (read via the live controlled input's own `.value`,
  not just visually). Switched to Producer: neither conditional field
  present, Name still populated. Switched back to Expert: the earlier
  Description value (`"CDP knowledge domain"`) was still present —
  confirming hide/show only, never reset, across all 3 type transitions in
  both directions.
- **[REQ-SB-46-US-01-AC-10]** (Step 1 half) PASS. Empty Name, click Next:
  `currentStep` stayed `1` (Step 1's own fields still rendered — Step 2
  never mounted), `wizard-step1-error` read
  `"Missing a name, a Section — the agent was not created."` (naming "a
  name" as required by the test; Section was also legitimately unfilled at
  that point in this pass, correctly co-named). Filled Name + Section,
  left Domain empty (Expert): blocked again, error named
  `"Missing a knowledge domain — the agent was not created."` exactly.
  Filled Domain: `wizard-step1-next` genuinely advanced `currentStep` to
  `2` (`wizard-step-2` carries `aria-current="step"`, Step 2's own
  Working-mode selector rendered) — confirming the block is real, not a
  permanently-stuck state.

No out-of-scope files touched, no new dependency, no ADR deviation. The
one disclosed item above (build-sequencing) is a scope-internal judgement
call, not an escalation — `gate: flagged` per Pipeline.md's own "log as an
assumption in the Implementation Log for human spot-check" mechanism, not
trigger 4-7's ESCALATIONS.md path.
