---
id: REQ-SB-78-US-01-T02
title: Grouped, color-coded rendering in MyDayApprovalsPage.tsx
parent_story: REQ-SB-78-US-01
requirement_id: REQ-SB-78
type: frontend
status: Done
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

- [x] `[REQ-SB-78-US-01-AC-01]` Grouped-by-`action_id` rendering confirmed live
- [x] `[REQ-SB-78-US-01-AC-02]` Distinct color class per rendered group confirmed live
- [x] `[REQ-SB-78-US-01-AC-03]` Empty groups never rendered
- [x] `[REQ-SB-78-US-01-AC-04]` Unmapped/null `action_id` renders in the `Other` catch-all
- [x] `[REQ-SB-78-US-01-AC-05]` Company Review 5-way control unchanged inside its own group
- [x] `[REQ-SB-78-US-01-AC-07]` Empty state unaffected
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision/pattern/constraint)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The bulk-approve control — `T03`.
- Any backend change.

---

## Context / Notes

Read `T01`'s own real `pendingApprovalGroups.ts` before starting — group by `resolveGroup(item.action_id).key` (or the module's own equivalent exported shape), not a re-derived inline copy of the same logic.

---

## Implementation Log

**2026-08-19, coder.** `MyDayApprovalsPage.tsx` — added a local
`groupPendingApprovals(items)` helper (first-appearance-order grouping via
`T01`'s `resolveGroup`) and wrapped the existing render loop in a
`<section data-group-key={group.key} className={"pending-approval-group " +
group.colorClass}>` per group, with a `.pending-approval-group-heading`
carrying the group's own label. The per-item markup inside each group
(`.item-row`, `CompanyReviewDecisionControl` branch, plain Approve/Decline
branch) is untouched, byte-identical to before — only re-indented one level
deeper. The empty-state branch and its governing `items && items.length >
0` condition are both completely untouched.

**Live verification (real running app: dev server on `http://127.0.0.1:5174`
for this worktree, real backend on `http://127.0.0.1:8000`, real vault
data — headless Edge via CDP, `--remote-debugging-port=9333`, minimal Node
`fetch`+`WebSocket` driver, no new dependency):**

- `[REQ-SB-78-US-01-AC-01]` Real data: 80 pending items across 3 real
  `action_id`s. DOM showed exactly 3 `[data-group-key]` sections
  (`acknowledge_classification_failure`, `propose_cross_cutting_update`,
  `propose_company_review`), zero top-level flat `.item-list`
  (`document.querySelector('.card > .item-list')` → `false`). **Confirmed.**
- `[REQ-SB-78-US-01-AC-02]` Each of the 3 rendered groups carried a
  DIFFERENT `group-color-N` class and a distinct computed `--group-accent`
  value (`group-color-11`/`#64748b`, `group-color-7`/`#0891b2`,
  `group-color-1`/`#c58b5f`). **Confirmed.**
- `[REQ-SB-78-US-01-AC-03]` 8 of the 11 `KNOWN_GROUPS` entries have zero
  real pending items right now (`propose_customer_backfill_routing`,
  `propose_customer_archival_candidate`, `propose_librarian_company_link`,
  `route_thread_to_project`, `propose_recurring_pipeline`,
  `propose_background_amendment`, `propose_new_top_level_area`,
  `hermes_vault_write`) — none of the 3 rendered `[data-group-key]`
  sections named any of them; confirmed by construction (the render loop
  only ever iterates real `items`) and by direct DOM read. **Confirmed.**
- `[REQ-SB-78-US-01-AC-04]` No real record currently has an unmapped
  `action_id`, so seeded one disposable test record via the REAL,
  unmodified `pending_approval_registry.create_pending_approval()`
  function (not a mock, not a raw JSON-file mutation — the same production
  function every internal pipeline calls; there is no public "create
  arbitrary" HTTP endpoint), `action_id=
  "some_future_unmapped_action_id__REQ_SB_78_T02_disposable_test"`,
  `agent_id="librarian-housekeeping"`. Confirmed live via the real
  `GET /pending-approvals` API that it appeared, then confirmed in the DOM
  it rendered inside `[data-group-key="other"]` with class
  `group-color-other` and label "Other". **Cleaned up immediately after**
  via the REAL `POST /pending-approvals/{id}/decline` endpoint (record
  `9b7d953ae5b2`) — never a raw store mutation, per this project's
  archive-not-delete/API-first standing constraint. **Confirmed.**
- `[REQ-SB-78-US-01-AC-05]` The `propose_company_review` group (73 real
  records) rendered `[data-testid="company-review-decision"]` 73 times —
  one per item, matching the real count exactly (no duplication), nested
  inside `[data-group-key="propose_company_review"]`. **Confirmed.**
- `[REQ-SB-78-US-01-AC-07]` Verified via an in-page `window.fetch`
  monkeypatch stub for this one tab session only (established precedent,
  `Implementation/Learnings.md` `SPRINT-026`/`REQ-SB-02-US-01-T04`) —
  stubbed only the `/pending-approvals` list call to return `[]`, leaving
  every other real fetch (including `known-companies`) untouched, rather
  than bulk-declining any of the 80 real records to reach a genuine empty
  state. Confirmed 0 `[data-group-key]` elements, the original empty-state
  icon/copy ("Nothing awaiting approval right now.") rendered exactly as
  before. **Confirmed.**

No live-found defect. Every disposable artefact (one seeded-then-declined
Pending Approval, `9b7d953ae5b2`) disclosed above; zero real records were
mutated beyond that one disposable one.

**Gate: clear 2026-08-19** — no MUST-FLAG trigger: the empty-state
verification technique (fetch-stub rather than a real zero-record state)
and the disposable-record seeding technique (direct real-function call,
since no create-arbitrary HTTP endpoint exists) are both scope-internal,
disclosed judgement calls consistent with this project's own established
Learnings precedents, not new assumptions requiring a flag; `REQ-SB-78` is
not `Draft`; no ADR touched; no `ESCALATIONS.md` entry; not oversized; all
6 locked ACs this task owns independently verified live; no contradictory
inputs; nothing genuinely ambiguous.
