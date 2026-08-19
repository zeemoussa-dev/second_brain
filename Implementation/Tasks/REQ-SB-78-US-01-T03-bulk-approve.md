---
id: REQ-SB-78-US-01-T03
title: Bulk-approve control per eligible group
parent_story: REQ-SB-78-US-01
requirement_id: REQ-SB-78
type: frontend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-78-US-01-T01, REQ-SB-78-US-01-T02]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-78-US-01-T03 — Bulk-approve control per eligible group

## Parent Story

- Story: [[REQ-SB-78-US-01]] — `../UserStories/REQ-SB-78-US-01-pending-approvals-grouped-color-coded-review.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-78 *Pending Approvals — Grouped, Color-Coded Review*
- Architecture: `Implementation/Architecture/architecture.md` → "Pending Approvals — Grouped, Color-Coded Review" § "Bulk-approve eligibility (Scenario 7)"

---

## Objective

Give every rendered group whose items are ALL non-branching-decision a real bulk-approve control that loops the already-existing single-item `approvePendingApproval(id)` call; a group containing any branching-decision item (Company Review) offers no bulk-approve control at all.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed: groups render as `[data-group-key]` sections, each with its own `items` array.
- `approvePendingApproval(id)` (`../features/agents-map/pendingApprovalsApiClient.ts`) already exists — a plain `POST /pending-approvals/{id}/approve` call with no decision body.

**After / Outputs:**
- For each rendered group, compute eligibility: `group.items.every(item => !BRANCHING_DECISION_ACTION_IDS.has(item.action_id))` (correctly covers the heterogeneous `Other` catch-all too, since it's computed per rendered group, not per group key).
- An eligible group's own section header/toolbar gains a `Bulk approve (<N>)` button (`btn btn-primary`, mirroring existing button vocabulary). Clicking it calls `approvePendingApproval(id)` once per item currently in that group (sequential or `Promise.all` — coder's own implementation choice), then refreshes the list once at the end (mirrors `handleApprove`'s own existing `refresh()` call).
- A group containing at least one branching-decision item (`propose_company_review`) renders NO bulk-approve control for that group.

---

## Files to Modify

- `src/frontend/src/pages/MyDayApprovalsPage.tsx` — bulk-approve control + handler, added to `T02`'s own group-section rendering.

---

## Constraints

- Inherits from parent story.
- **Zero new backend endpoint/capability** — loops the ALREADY-EXISTING `approvePendingApproval(id)` verbatim, once per item, mirroring `handleApprove`'s own existing per-item call shape exactly.
- **Eligibility computed PER RENDERED GROUP, not per group key** — a future `Other`-catch-all group that happens to contain a mixed set (some branching, some not) must correctly get NO bulk-approve control, using the same one check as every named group.
- **Refresh once at the end**, not once per item — avoid N redundant re-fetches for an N-item bulk action.
- Never bulk-approve/bulk-decline without an explicit operator click on this task's own new control — no auto-trigger.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-78-US-01-AC-06]` Seed 2+ real pending approvals sharing a non-branching `action_id` (e.g. `route_thread_to_project` or `acknowledge_classification_failure`). Confirm that group renders a `Bulk approve` control. Click it; confirm every item in the group is approved via a real `POST /pending-approvals/{id}/approve` call each (confirm via network inspection: one call per item, no decision body), and the group empties/disappears once the list refreshes.
2. `[REQ-SB-78-US-01-AC-06]` Seed a real `propose_company_review` pending approval. Confirm its own group renders NO bulk-approve control.
3. Seed a group with a mix (if the `Other` catch-all can realistically contain a branching + non-branching mix — construct this case even if synthetic). Confirm the mixed group ALSO gets no bulk-approve control — the per-group, not per-key, computation.
4. Confirm a single-item group still offers bulk-approve if eligible (no "2+ items" gate on rendering the control itself — the Gherkin's own "2+" is about a realistic demonstration, not a hard eligibility floor; disclose if a different reading was taken).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `[REQ-SB-78-US-01-AC-06]` Bulk-approve confirmed live for an eligible group, looping the existing single-item endpoint
- [ ] `[REQ-SB-78-US-01-AC-06]` No bulk-approve control rendered for a group containing any branching-decision item
- [ ] List refreshes once at the end of a bulk action, not once per item
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any new backend endpoint.
- Bulk-decline (not asked for by this story's own Gherkin — Approve only).

---

## Context / Notes

A future new branching-decision `action_id` needs to be added to BOTH `BRANCHING_DECISION_ACTION_IDS` (`T01`) AND `MyDayApprovalsPage.tsx`'s own existing per-item render branch — the same "each new decision control names itself" precedent the Company Review control already established, not a new gap this task introduces.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
