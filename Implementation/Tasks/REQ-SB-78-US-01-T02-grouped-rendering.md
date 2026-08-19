---
id: REQ-SB-78-US-01-T02
title: Grouped, color-coded rendering in MyDayApprovalsPage.tsx
parent_story: REQ-SB-78-US-01
requirement_id: REQ-SB-78
type: frontend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-78-US-01-T01]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-78-US-01-T02 — Grouped, color-coded rendering

## Parent Story

- Story: [[REQ-SB-78-US-01]] — `../UserStories/REQ-SB-78-US-01-pending-approvals-grouped-color-coded-review.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-78 *Pending Approvals — Grouped, Color-Coded Review*
- Architecture: `Implementation/Architecture/architecture.md` → "Pending Approvals — Grouped, Color-Coded Review" § "Empty-group suppression / catch-all rendering (Scenarios 3/4)"

---

## Objective

Wrap `MyDayApprovalsPage.tsx`'s existing flat `.item-list` render loop in `[data-group-key]`-tagged sections, keyed by `action_id` (via `T01`'s `pendingApprovalGroups.ts`), suppressing empty groups and routing unmapped items into the `Other` catch-all — every existing per-item card (including the Company Review 5-way control) renders unchanged inside its own group.

---

## Starting State → End State

**Before / Inputs:**
- `MyDayApprovalsPage.tsx` renders `items.map(...)` as one flat `.item-list` of `.item-row` elements, branching per-item on `item.action_id === COMPANY_REVIEW_ACTION_ID`.
- `T01` has added `pendingApprovalGroups.ts`.

**After / Outputs:**
- The render loop groups the already-fetched `items` array by `resolveGroup(item.action_id).key` (or equivalent), producing an ordered list of `{key, label, colorClass, items}` groups.
- Groups with `items.length === 0` are never rendered (Scenario 3) — the grouping step itself only ever produces non-empty groups, by construction (only iterate `items` that exist).
- Each rendered group is a section carrying `data-group-key={group.key}` and a `group-color-N`/`group-color-other` class (from `T01`), with a visible label heading (`group.label`).
- Every item inside a group renders EXACTLY the same per-item markup as today (`.item-row`, `item-row-title`/`item-row-meta`, the `CompanyReviewDecisionControl` branch for `propose_company_review` items) — this task changes only the WRAPPING structure, never the per-item card's own internals.
- The existing empty-state branch (`items && items.length === 0`) is preserved completely unchanged — it renders BEFORE any grouping logic runs (an early return / conditional branch), so Scenario 7 (empty state) needs no new code path.

---

## Files to Modify

- `src/frontend/src/pages/MyDayApprovalsPage.tsx` — grouping wrapper around the existing render loop.

---

## Constraints

- Inherits from parent story.
- **Never replace or restructure any existing per-item card's own internals** — the `CompanyReviewDecisionControl` branch and the plain Approve/Decline branch must render byte-identical output to today, just nested one level deeper inside a group section.
- **Empty-group suppression by construction** — never render a group whose own `items` array is empty; never a hardcoded static group list independent of real data.
- **The `Other` catch-all is the ONE fallback** for every unmapped/null `action_id` — never a second, silent fallback.
- **The empty-state branch (zero pending approvals at all) is untouched** — renders before/instead of any grouping chrome, exactly as today.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-78-US-01-AC-01]` Render the page with 2+ real pending approvals of different `action_id`s. Expect 2+ distinct `[data-group-key="..."]` section elements, each containing only its own matching items — never one flat `.item-list` at the top level.
2. `[REQ-SB-78-US-01-AC-02]` Confirm each rendered `[data-group-key]` section carries a DIFFERENT `group-color-N`/`group-color-other` class from every other currently-rendered group.
3. `[REQ-SB-78-US-01-AC-03]` Seed data with an `action_id` known to `KNOWN_GROUPS` that currently has ZERO pending items. Confirm no `[data-group-key]` section for it renders.
4. `[REQ-SB-78-US-01-AC-04]` Seed a pending approval with an `action_id` not in `KNOWN_GROUPS` (or `null`). Confirm it renders inside `[data-group-key="other"]`, never dropped.
5. `[REQ-SB-78-US-01-AC-05]` Render with a real `propose_company_review` record. Confirm `[data-testid="company-review-decision"]` (or its affiliate/merge picker variants) still renders and functions, nested inside `[data-group-key="propose_company_review"]`.
6. `[REQ-SB-78-US-01-AC-07]` Render with zero pending approvals. Confirm the existing empty-state markup renders exactly as before, with zero `[data-group-key]` elements present.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `[REQ-SB-78-US-01-AC-01]` Grouped-by-`action_id` rendering confirmed live
- [ ] `[REQ-SB-78-US-01-AC-02]` Distinct color class per rendered group confirmed live
- [ ] `[REQ-SB-78-US-01-AC-03]` Empty groups never rendered
- [ ] `[REQ-SB-78-US-01-AC-04]` Unmapped/null `action_id` renders in the `Other` catch-all
- [ ] `[REQ-SB-78-US-01-AC-05]` Company Review 5-way control unchanged inside its own group
- [ ] `[REQ-SB-78-US-01-AC-07]` Empty state unaffected
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The bulk-approve control — `T03`.
- Any backend change.

---

## Context / Notes

Read `T01`'s own real `pendingApprovalGroups.ts` before starting — group by `resolveGroup(item.action_id).key` (or the module's own equivalent exported shape), not a re-derived inline copy of the same logic.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
