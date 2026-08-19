---
id: REQ-SB-78-US-01-T04
title: Real-browser end-to-end verification — all 7 locked ACs
parent_story: REQ-SB-78-US-01
requirement_id: REQ-SB-78
type: frontend
status: Ready
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

- [ ] All 7 locked ACs independently re-confirmed live, in a real browser, against the real running app
- [ ] A screenshot/DOM dump of the grouped layout recorded
- [ ] Every disposable test artefact cleaned up and disclosed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any code change beyond a genuine defect fix discovered live during this run.
- Visual/pixel-level polish spot-check against a prototype — no approved prototype exists for this grouping treatment (operator resolved: build directly, restyle later); out of this task's own locked-AC scope.

---

## Context / Notes

Mirrors this project's own established screen-verification discipline (`Implementation/Learnings.md`, `SPRINT-026`/`036`/`038`) — the heaviest task in this story by real-verification effort, not code volume.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
