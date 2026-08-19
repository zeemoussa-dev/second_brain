---
id: REQ-SB-78-US-01-T01
title: pendingApprovalGroups.ts lookup table + group-color CSS classes
parent_story: REQ-SB-78-US-01
requirement_id: REQ-SB-78
type: frontend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-78-US-01-T01 — `pendingApprovalGroups.ts` + CSS

## Parent Story

- Story: [[REQ-SB-78-US-01]] — `../UserStories/REQ-SB-78-US-01-pending-approvals-grouped-color-coded-review.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-78 *Pending Approvals — Grouped, Color-Coded Review*
- Architecture: `Implementation/Architecture/architecture.md` → "Pending Approvals — Grouped, Color-Coded Review" §§ "Grouping key", "Label + color"

---

## Objective

Add the new, purely-presentational `pendingApprovalGroups.ts` module (label/color lookup by `action_id`, `Other` catch-all, branching-decision set) and the small set of new `.group-color-N` CSS classes it references — zero backend change.

---

## Starting State → End State

**Before / Inputs:**
- `MyDayApprovalsPage.tsx` has a local `const COMPANY_REVIEW_ACTION_ID = 'propose_company_review'`, no grouping concept.
- `src/frontend/src/styles/tokens.css` has a numbered-variant CSS-custom-property precedent (`--graph-kind-color-1` … `-8`).
- `src/frontend/src/styles/my-day.css` has `.item-list`/`.item-row`.

**After / Outputs:**
- New file `src/frontend/src/features/agents-map/pendingApprovalGroups.ts`:

  ```ts
  export const KNOWN_GROUPS: Record<string, { label: string; colorClass: string }> = {
    propose_company_review:              { label: 'Company Review',         colorClass: 'group-color-1' },
    propose_customer_backfill_routing:   { label: 'Customer Backfill',      colorClass: 'group-color-2' },
    propose_customer_archival_candidate: { label: 'Customer Archival',      colorClass: 'group-color-3' },
    propose_librarian_company_link:      { label: 'Company Link',           colorClass: 'group-color-4' },
    route_thread_to_project:             { label: 'Thread Routing',         colorClass: 'group-color-5' },
    propose_recurring_pipeline:          { label: 'Recurring Pipeline',     colorClass: 'group-color-6' },
    propose_cross_cutting_update:        { label: 'Cross-Cutting Update',   colorClass: 'group-color-7' },
    propose_background_amendment:        { label: 'Background Amendment',   colorClass: 'group-color-8' },
    propose_new_top_level_area:          { label: 'New Top-Level Area',     colorClass: 'group-color-9' },
    hermes_vault_write:                  { label: 'Hermes Write',           colorClass: 'group-color-10' },
    acknowledge_classification_failure:  { label: 'Classification Failure', colorClass: 'group-color-11' },
  };

  export const OTHER_GROUP = { label: 'Other', colorClass: 'group-color-other' };

  export const BRANCHING_DECISION_ACTION_IDS = new Set(['propose_company_review']);

  export function resolveGroup(actionId: string | null): { key: string; label: string; colorClass: string } {
    if (actionId && actionId in KNOWN_GROUPS) {
      return { key: actionId, ...KNOWN_GROUPS[actionId] };
    }
    return { key: 'other', ...OTHER_GROUP };
  }
  ```

  (`resolveGroup`'s exact shape is a scope-internal implementation choice — `T02` may call `KNOWN_GROUPS`/`OTHER_GROUP` directly instead if that reads cleaner; either satisfies this task's own Constraints, as long as the `key`/`label`/`colorClass` triple is derivable per item.)
- `src/frontend/src/styles/tokens.css` — new custom properties, mirroring the existing `--graph-kind-color-N` numbered-variant pattern: `--group-color-1` … `--group-color-11`, `--group-color-other`.
- `src/frontend/src/styles/my-day.css` — new `.pending-approval-group` block establishing a section wrapper, plus `.group-color-1` … `-11`/`.group-color-other` classes each setting a `--group-accent: var(--group-color-N)` custom property the wrapper's own border/heading-accent styles read (mirrors the existing `--node-color`/`--hub-color` per-item CSS-custom-property pattern the Agents Map canvas already uses).

---

## Files to Modify

- `src/frontend/src/features/agents-map/pendingApprovalGroups.ts` — new file.
- `src/frontend/src/styles/tokens.css` — new `--group-color-N` custom properties.
- `src/frontend/src/styles/my-day.css` — new `.pending-approval-group`/`.group-color-N` classes.

---

## Constraints

- Inherits from parent story.
- **No new backend field, no new endpoint** — this task is purely frontend/presentational.
- **Every `action_id` not in `KNOWN_GROUPS` (including `null`) resolves to the ONE `Other` catch-all** — never a second, undocumented fallback path.
- Reuses the existing `--color-accent`-family CSS-custom-property pattern — never a new, unrelated color system.
- `BRANCHING_DECISION_ACTION_IDS` starts as a superset-safe generalization of the existing `COMPANY_REVIEW_ACTION_ID` constant already in `MyDayApprovalsPage.tsx` — `T02`/`T03` reconcile the two (either import this module's own constant in place of the local one, or keep both in sync; `T02` decides).

---

## Tests

**Manual verification steps:**
1. Import `KNOWN_GROUPS`/`OTHER_GROUP`/`BRANCHING_DECISION_ACTION_IDS`/`resolveGroup` from a scratch script or the browser console once the dev server is running; confirm `resolveGroup('propose_company_review')` returns `{key: 'propose_company_review', label: 'Company Review', colorClass: 'group-color-1'}`.
2. Confirm `resolveGroup('some_future_unmapped_action_id')` and `resolveGroup(null)` both return `{key: 'other', ...OTHER_GROUP}`.
3. Confirm `BRANCHING_DECISION_ACTION_IDS.has('propose_company_review')` is `true` and `.has('route_thread_to_project')` is `false`.
4. Confirm the new CSS classes exist in the built stylesheet (inspect via dev server) and each numbered class sets a distinct `--group-accent` value.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `pendingApprovalGroups.ts` exports `KNOWN_GROUPS`/`OTHER_GROUP`/`BRANCHING_DECISION_ACTION_IDS`, every known `action_id` from the architecture's own lookup table present
- [ ] Unmapped/null `action_id` resolves to the one `Other` catch-all
- [ ] New `.group-color-N`/`.group-color-other` CSS classes exist and are visually distinct by custom-property value
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring this module into `MyDayApprovalsPage.tsx`'s own rendering — `T02`/`T03`.
- Any backend change.

---

## Context / Notes

None beyond the architecture reference above.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
