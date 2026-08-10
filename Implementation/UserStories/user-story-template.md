---
id: REQ-X.Y-US-NN
title: <short, action-oriented story title>
requirement_ids: [REQ-X.Y]
requirement_section: "<PRD heading>"
phase: MVP
status: Draft
gate: clear
gate_reason: ""
sprint: ""
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# REQ-X.Y-US-NN — <Story Title>

## Story

**As a** <type of user>
**I want** <capability>
**So that** <benefit / outcome>

## Context

- PRD: `Documentation/PRD.md` → *<section heading>*
- Related: [[REQ-X.Y-US-NN]]

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: <short scenario name>
```gherkin
Given <initial context / preconditions>
  And <additional precondition>
When <user action or system event>
Then <observable outcome>
  And <additional outcome>
```

### Scenario 2: <short scenario name>

```gherkin
Given <…>
When <…>
Then <…>
```

## Affected Screens

<!-- Prototype files this story touches (under `html-prototype/`). State what
changes in each. If backend-only, write "None — backend only". -->

- `html-prototype/<screen>.html` — <what changes here>

## Dependencies

- **Blocked by:** [[REQ-X.Y-US-NN]] — <reason>
- **Related to:** [[REQ-X.Y-US-NN]] — <reason>
- **External:** <e.g., API key provisioned, tech stack decided>

## Constraints

- <Constraint 1 — limit on HOW this is built>
- <Constraint 2>

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-X.Y-US-NN-T01 | backend | <short description> | `src/backend/...` | [T01](../Tasks/REQ-X.Y-US-NN-T01-<slug>.md) |
| REQ-X.Y-US-NN-T02 | frontend | <short description> | `src/frontend/...` | [T02](../Tasks/REQ-X.Y-US-NN-T02-<slug>.md) |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- <Thing this story intentionally excludes>
- <Behaviour deferred to a later phase / story>

## Notes

<!-- Open questions, design considerations, risks, prototype parity checklist. -->
