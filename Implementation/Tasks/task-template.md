---
id: REQ-X.Y-US-NN-T<NN>
title: <short, action-oriented task title>
parent_story: REQ-X.Y-US-NN
requirement_id: REQ-X.Y
type: backend
status: Draft
gate: clear
gate_reason: ""
phase: MVP
depends_on: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# REQ-X.Y-US-NN-T<NN> — <Task Title>

## Parent Story

- Story: [[REQ-X.Y-US-NN]] — `../UserStories/REQ-X.Y-US-NN-<slug>.md`
- Requirement: `Documentation/PRD.md` → REQ-X.Y *<section heading>*

---

## Objective

_(One sentence: what this task accomplishes.)_

---

## Starting State → End State

**Before / Inputs:**
- _(state or input 1)_

**After / Outputs:**
- _(state or output 1)_

---

## Files to Modify

<!-- List every file the coder is allowed to touch. -->

- _(file path — what to do)_

---

## Constraints

- Inherits from parent story
- _(task-specific constraint, if any)_

---

## Tests

<!-- Every locked AC from the parent story must appear as at least one numbered
verification step here, prefixed with its AC-ID in square brackets.
A locked AC with no tagged step is a hard failure — the task cannot be Done.

Verification runs in manual mode until the test stack is scaffolded. Once it is,
upgrade to AC-tagged automated tests with the real runner commands.

FRONTEND / SCREEN tasks: verify DOM structure only (jsdom sees no computed CSS,
layout, colour, or :hover states — pure visual polish is not a locked AC and is
spot-checked against the prototype out-of-band). Example structural AC step:
  [REQ-X.Y-US-NN-AC-01] Render the screen; expect a [data-testid="help-button"]
  element present in the sidebar footer. -->

**Manual verification steps:**
1. _([REQ-X.Y-US-NN-AC-01] open <screen>, do <thing>, expect <observable>)_

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] _(criterion 1)_
- [ ] _(criterion 2)_
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- _(out of scope item 1)_

---

## Context / Notes

_(Optional background the coder needs that isn't obvious from the files.)_

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
