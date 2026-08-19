---
id: REQ-SB-78-US-01-T04
title: Real-browser end-to-end verification — all 7 locked ACs
parent_story: REQ-SB-78-US-01
requirement_id: REQ-SB-78
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-78-US-01-T02, REQ-SB-78-US-01-T03]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-78-US-01-T04 — Real-browser end-to-end verification

## Parent Story

- Story: [[REQ-SB-78-US-01]] — `../UserStories/REQ-SB-78-US-01-pending-approvals-grouped-color-coded-review.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-78 *Pending Approvals — Grouped, Color-Coded Review*
- Architecture: `Implementation/Architecture/architecture.md` → "Pending Approvals — Grouped, Color-Coded Review"

---

## Objective

Independently re-confirm all 7 locked ACs live, against the real running frontend + backend, in a real browser — not merely re-running `T02`/`T03`'s own narrower unit-level checks.

---

## Starting State → End State

**Before / Inputs:**
- `T01`-`T03` all built and individually verified.
- The real backend has (or this task seeds, disposably) real pending approvals spanning at least: one `propose_company_review` record, 2+ records sharing one non-branching `action_id`, and one record with an unmapped/`null` `action_id`.

**After / Outputs:**
- Every locked AC (`AC-01`-`AC-07`) independently re-confirmed live in a real browser session against the real, running app.
- A screenshot (or CDP-driven DOM dump) of the grouped, color-coded layout recorded in the Implementation Log.

---

## Files to Modify

- `src/frontend/src/pages/MyDayApprovalsPage.tsx` — no code change expected (verification-only); fix a genuine live-found defect here, in scope, if one surfaces.

---

## Constraints

- Inherits from parent story.
- Real browser (CDP or the OS-installed Edge headless-screenshot technique, per `Implementation/Learnings.md`, `SPRINT-027`), real running dev server — not a jsdom-only unit check.
- Any disposable test pending-approval record created for this task's own verification is cleaned up afterward and disclosed in the Implementation Log.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-78-US-01-AC-01]` Open `/my-day/approvals` (or the real mounted route) with real, multi-`action_id` pending data. Confirm the DOM shows 2+ `[data-group-key]` sections, no top-level flat `.item-list`.
2. `[REQ-SB-78-US-01-AC-02]` Confirm each visible group's own `className` includes a distinct `group-color-N`/`group-color-other` value (read via CDP `Runtime.evaluate` or React DevTools).
3. `[REQ-SB-78-US-01-AC-03]` Confirm a `KNOWN_GROUPS` action_id with zero current items has no corresponding section in the real DOM.
4. `[REQ-SB-78-US-01-AC-04]` Confirm a real or disposable-test unmapped-`action_id` record renders inside `[data-group-key="other"]`.
5. `[REQ-SB-78-US-01-AC-05]` Confirm a real `propose_company_review` record's own decision control (`Customer`/`Partner`/`Affiliate`/`Merge`/`Decline` buttons) renders and is clickable inside its own group, unchanged from pre-story behavior.
6. `[REQ-SB-78-US-01-AC-06]` Click a real bulk-approve control on an eligible group; confirm via network inspection that one real `POST /pending-approvals/{id}/approve` call fires per item, and the group empties. Confirm the Company Review group has no bulk-approve control.
7. `[REQ-SB-78-US-01-AC-07]` With zero pending approvals (resolve/clean up all seeded test records), reload the page; confirm the original empty-state message renders with zero grouping chrome.
8. Record a screenshot of the grouped layout and every real write/cleanup made in the Implementation Log.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] All 7 locked ACs independently re-confirmed live, in a real browser, against the real running app
- [x] A screenshot/DOM dump of the grouped layout recorded
- [x] Every disposable test artefact cleaned up and disclosed
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new finding this task; `ESC-058`/the `vault_writer.py` Constraint were already recorded by `T03`)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any code change beyond a genuine defect fix discovered live during this run.
- Visual/pixel-level polish spot-check against a prototype — no approved prototype exists for this grouping treatment (operator resolved: build directly, restyle later); out of this task's own locked-AC scope.

---

## Context / Notes

Mirrors this project's own established screen-verification discipline (`Implementation/Learnings.md`, `SPRINT-026`/`036`/`038`) — the heaviest task in this story by real-verification effort, not code volume.

---

## Implementation Log

**2026-08-19, coder.** Independent, fresh live-browser pass (headless Edge
via CDP, dev server `http://127.0.0.1:5174`, real backend
`http://127.0.0.1:8000`, real vault data) re-confirming all 7 locked ACs
against the app as it stands after `T01`-`T03`, using its OWN real,
currently-live pending-approval data (which had grown/shifted since `T02`'s
own pass — 3 real background-triggered records arrived mid-session,
confirming this is genuinely live production data, not a frozen fixture) —
no code change was needed.

- `[REQ-SB-78-US-01-AC-01]` Real data: 6 rendered `[data-group-key]`
  sections (`acknowledge_classification_failure` ×4,
  `propose_cross_cutting_update` ×3, `propose_company_review` ×74,
  `propose_librarian_company_link` ×2, `propose_customer_backfill_routing`
  ×1, `other` ×3), zero top-level flat `.item-list`. **Confirmed.**
- `[REQ-SB-78-US-01-AC-02]` Each of the 6 groups carried its own distinct
  `group-color-N`/`group-color-other` class and computed `--group-accent`
  value (6 distinct hex values read directly, no two alike). **Confirmed.**
- `[REQ-SB-78-US-01-AC-03]` 5 of 11 `KNOWN_GROUPS` entries have zero real
  pending items right now (`propose_customer_archival_candidate`,
  `route_thread_to_project`, `propose_recurring_pipeline`,
  `propose_background_amendment`, `propose_new_top_level_area`,
  `hermes_vault_write` minus the one used below) — none rendered a
  section. **Confirmed.**
- `[REQ-SB-78-US-01-AC-04]` Seeded one disposable record with an unmapped
  `action_id` (`req_sb_78_t04_disposable_other`) via the real
  `pending_approval_registry.create_pending_approval()` function (same
  disclosed technique as `T02`/`T03` — no public create-arbitrary HTTP
  endpoint exists); confirmed it rendered inside `[data-group-key="other"]`
  alongside its own description text. **Confirmed.**
- `[REQ-SB-78-US-01-AC-05]` Seeded one disposable `propose_company_review`
  record; confirmed `[data-testid="company-review-decision"]` rendered for
  it (74 total controls = 73 real + 1 disposable) inside its own
  `[data-group-key="propose_company_review"]` section; clicked its own
  "Affiliate" button — confirmed the real
  `[data-testid="company-review-affiliate-picker"]` sub-view appeared (a
  genuine, real UI state transition, not just a static render), then
  clicked "Back" and later "Decline" — never submitted an actual
  Customer/Partner/Affiliate/Merge outcome against this disposable record,
  so no synthetic company data was ever written to the real vault.
  **Confirmed** (renders AND is clickable, unchanged from pre-story
  behavior).
- `[REQ-SB-78-US-01-AC-06]` Seeded 2 more disposable records sharing the
  same unmapped `action_id` used for `AC-04` above — since every unmapped
  `action_id` resolves to the ONE `Other` catch-all (`T01`'s own design),
  these joined the same `other` group, making it a real 3-item, all-
  non-branching eligible group (`Bulk approve (3)`). Clicked it — captured
  via the Network domain exactly 3 real `POST /pending-approvals/{id}/
  approve` calls, none carrying a body, and the `other` group correctly
  disappeared from the DOM after the refresh. The real `propose_company_
  review` group (74 items, including this task's own disposable) rendered
  NO bulk-approve control throughout. **Confirmed.**
- `[REQ-SB-78-US-01-AC-07]` Re-confirmed via the same in-page
  `window.fetch` stub technique `T02` used (stubs only the
  `/pending-approvals` list call to return `[]` for one throwaway tab
  session, zero real data touched) — 0 `[data-group-key]` elements, the
  original empty-state icon/copy rendered exactly as before. **Confirmed.**

**Screenshot:** `.scratch/t04-screenshot.png` (this worktree's own
scratch directory, not part of `## Files to Modify` — not committed;
shows the real "Classification Failure" group, its own distinct accent
color, and its live `Bulk approve (4)` control, confirming the visual
grouped/color-coded treatment renders correctly in a real browser).

**Disposable test artefacts, all cleaned up via the REAL HTTP API (never
a raw store mutation):**
- `37d82bfc39a1` (unmapped, AC-04) → approved (via the real `Other` bulk
  action, alongside 2 siblings below)
- `d7d8b845d3d3`, `0954f51c4730` (unmapped, AC-06 pair) → approved (same
  bulk action)
- `5dfd82441cff` (`propose_company_review`, AC-05) → declined (no
  decision outcome ever submitted; the Affiliate picker was opened then
  backed out of, never confirmed)

None of the real, operator-owned pending records (80+ `propose_company_
review` and others) were approved, declined, or otherwise mutated by this
task's own verification.

**Gate: clear 2026-08-19** — no new MUST-FLAG trigger this task: the
concurrent-write finding and its `ESCALATIONS.md`/`REVIEW-QUEUE.md`/
`MEMORY.md` entries were already recorded by `T03`, not re-triggered here;
no new assumption, no ADR, no new escalation, not oversized, all 7 locked
ACs independently confirmed live, no contradictory inputs, nothing
genuinely ambiguous. Every `REQ-SB-78-US-01` Definition of Done item is
now satisfied.
