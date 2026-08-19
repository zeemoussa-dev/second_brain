---
id: REQ-SB-76-US-01-T08
title: Company Review decision control — MyDayApprovalsPage.tsx (Customer/Partner/Affiliate/Merge/Decline)
parent_story: REQ-SB-76-US-01
requirement_id: REQ-SB-76
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-76-US-01-T07]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-76-US-01-T08 — Company Review decision control (frontend)

## Parent Story

- Story: [[REQ-SB-76-US-01]] — `../UserStories/REQ-SB-76-US-01-company-review-extract-classify-and-batch-apply.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-76 *Company Review — Extract & Recommend, Customer/Partner/Affiliate Classification, Batch-Apply*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Company Review" (§ "Frontend — `MyDayApprovalsPage.tsx` branches on `action_id`"), `Implementation/Architecture/ADR.md` → `ADR-057` Decision 3 (endpoint), 9 (known-companies)

---

## Objective

`MyDayApprovalsPage.tsx`'s render loop branches on `item.action_id === "propose_company_review"`: render a new 5-way decision control (Customer/Partner/Affiliate/Merge/Decline) in place of the generic Approve/Decline pair, for THIS proposal kind only — built directly, using the app's own existing form/control vocabulary, per the story's own operator override (no `/design` pass).

---

## Starting State → End State

**Before / Inputs:**
- `MyDayApprovalsPage.tsx` renders every item with the same generic `.item-row-actions` Approve/Decline pair, calling `approvePendingApproval(id)`/`declinePendingApproval(id)` with no body.
- `PendingApproval` has no `payload` field typed; `approvePendingApproval` takes no decision argument; no `fetchKnownCompanies` exists.
- `T07`'s real `CompanyReviewDecisionBody`/`GET /pending-approvals/known-companies` endpoints exist.

**After / Outputs:**
- `PendingApproval` gains an additive `payload: Record<string, unknown> | null` field.
- `approvePendingApproval(id: string, decision?: { outcome: string; parent_name?: string; parent_kind?: string }): Promise<PendingApproval>` gains an optional second parameter, POSTed as the JSON body only when supplied — every OTHER existing call site (`handleApprove(id)`, unchanged) keeps sending no body.
- New `fetchKnownCompanies(): Promise<{ customers: string[]; partners: string[] }>` composes `GET /pending-approvals/known-companies`.
- `MyDayApprovalsPage.tsx`'s render loop: `item.action_id === "propose_company_review"` renders a NEW decision-control component — five buttons (Customer/Partner/Affiliate/Merge/Decline); Affiliate reveals a parent picker (from `fetchKnownCompanies()`) plus a Customer-or-Partner kind choice; Merge reveals a parent picker only (no kind choice); Decline reuses `declinePendingApproval(id)` verbatim. Every OTHER `action_id` renders the EXISTING generic pair, completely unchanged.

---

## Files to Modify

- `src/frontend/src/features/agents-map/pendingApprovalsApiClient.ts` — `PendingApproval.payload`, `approvePendingApproval`'s optional `decision` param, new `fetchKnownCompanies`.
- `src/frontend/src/pages/MyDayApprovalsPage.tsx` — the new branch + decision-control component (may be a small new local component in this same file, or a new sibling file under `src/frontend/src/pages/` or `src/frontend/src/features/agents-map/` — coder's own judgement, no existing convention mandates a split).

---

## Constraints

- Inherits from parent story.
- Every OTHER existing proposal kind's own `.item-row-actions` Approve/Decline pair is completely unchanged — this branch is additive, scoped to `action_id === "propose_company_review"` only.
- Decline, for THIS proposal kind too, reuses `declinePendingApproval(id)` verbatim — no new Decline mechanism.
- `fetchKnownCompanies()` is called fresh on every Approvals page load — never baked into a proposal's own stored `payload`, which would go stale the moment ANY other Company Review batch resolves first.
- No `/design` pass — build directly using the app's own existing form/control vocabulary (buttons, selects) per the story's own operator override; a later, separate design pass may restyle it without blocking this story.
- No other new screen or navigation change.

---

## Tests

**Real running frontend + backend, real vault. Drive via a minimal CDP session (or the project's own established Node+`fetch`+`WebSocket` CDP client, `Implementation/Learnings.md` `SPRINT-036`) against a real `propose_company_review` batch — do not fabricate a fake item client-side; use a genuine record from `T04`'s own real extraction pass (or a bounded fresh one created for this test).**

**Manual verification steps:**
1. `[REQ-SB-76-US-01-AC-11]` Load the real Approvals page with at least one real, pending `propose_company_review` item AND at least one real, pending item of a DIFFERENT `action_id` both present. Confirm: the Company Review item renders the new 5-button decision control (Customer/Partner/Affiliate/Merge/Decline) in place of the generic pair; the OTHER item still renders the exact, unchanged generic Approve/Decline pair.
2. `[REQ-SB-76-US-01-AC-11]` Click Affiliate on the Company Review item; confirm a parent-entity picker (populated from a real `GET /pending-approvals/known-companies` call — verify via a `window.fetch` spy that exactly this call fired) plus a Customer-or-Partner kind choice both appear.
3. `[REQ-SB-76-US-01-AC-11]` Click Merge instead; confirm a parent-entity picker appears with NO kind choice.
4. `[REQ-SB-76-US-01-AC-03]` Click Customer (no picker needed); confirm the real `POST /pending-approvals/{id}/approve` fires with body `{"outcome": "customer"}` (verify via the `window.fetch` spy's captured request body) and the item disappears from the pending list on success (list refetches).
5. `[REQ-SB-76-US-01-AC-05]` Pick Affiliate, select a real parent + Customer kind, submit; confirm the real request body carries `{"outcome": "affiliate", "parent_name": "<picked>", "parent_kind": "customer"}`.
6. `[REQ-SB-76-US-01-AC-10]` Pick Merge, select a real parent, submit; confirm the real request body carries `{"outcome": "merge", "parent_name": "<picked>"}` with no `parent_kind` supplied by the UI unless the picker itself also resolves kind (coder's own judgement on the picker's exact shape — confirm whichever shape was built matches what `T06`'s `finalize_company_review` actually expects).
7. Click Decline on a (separate) real Company Review item; confirm `declinePendingApproval(id)` fires with no body — byte-for-byte the same call every other item's Decline button already makes.
8. Confirm a DIFFERENT, pre-existing proposal kind's own Approve/Decline buttons still work exactly as before this task (regression check).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `[REQ-SB-76-US-01-AC-11]` verified live — the new decision control renders only for `propose_company_review`, every other kind unaffected; Affiliate/Merge picker branching confirmed via real DOM presence
- [x] `[REQ-SB-76-US-01-AC-03]`/`[AC-05]`/`[AC-10]` spot-checked live via the UI — the correct real request body reaches the real backend for at least one outcome per branch shape (plain, Affiliate, Merge)
- [x] Decline reuses the existing call verbatim, confirmed live
- [x] Every other existing proposal kind's own controls confirmed unaffected (regression)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision beyond `ADR-057`)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any visual/interaction polish beyond a working, structurally-correct control — a later design pass may restyle (out of this story's own scope, per the operator's override).
- Any other new screen or navigation change.

---

## Context / Notes

`MyDayApprovalsPage.tsx`'s current shape (`src/frontend/src/pages/MyDayApprovalsPage.tsx`) and `pendingApprovalsApiClient.ts`'s current shape (`src/frontend/src/features/agents-map/pendingApprovalsApiClient.ts`) are both small, single-purpose files — read them fresh immediately before editing (this codebase's own established "compose around the REAL current file" discipline), since sibling stories may have landed additive changes in between `/plan-tasks` and this task's own build.

---

## Implementation Log

**2026-08-19, coder.** `PendingApproval` gained `payload?: Record<string, unknown> | null`. `approvePendingApproval(id, decision?)` gained an optional second parameter, POSTed as the JSON body only when supplied (`handleApprove(id)`'s own existing zero-arg call site unchanged). New `fetchKnownCompanies()`. `MyDayApprovalsPage.tsx`'s render loop branches `item.action_id === 'propose_company_review'` to a new local `CompanyReviewDecisionControl` component (kept in the same file — a small, single-purpose component, no existing convention mandates a split); every other `action_id` renders the existing generic `.item-row-actions` pair unchanged. Five buttons (Customer/Partner/Affiliate/Merge/Decline); Affiliate reveals two `<select className="input">`s (parent picker + Customer-or-Partner kind choice); Merge reveals one `<select>` (parent picker only) — the picked option's own list membership (`knownCompanies.customers` vs. `.partners`) resolves `parent_kind` for Merge, so the operator is never asked to choose it separately, and the real request body still carries `parent_kind` (confirmed live, matches what `finalize_company_review` actually reads). `fetchKnownCompanies()` is called once per page load (`useEffect`), never baked into a stored payload. Built directly with the app's own existing `btn`/`btn-primary`/`btn-danger`/`input` vocabulary — no `/design` pass, per the story's own operator override. `tsc -b --noEmit` run — zero new errors introduced (6 pre-existing `CSSProperties` errors in unrelated files, untouched by this task).

**Verification — live, real frontend (Vite dev server, port 5173) + real backend (port 8001) + real vault, driven via a minimal Node native-`fetch`+`WebSocket` CDP client against a headless Edge instance (`--headless=new --remote-debugging-port`), mirroring `Implementation/Learnings.md` `SPRINT-036`'s own established technique (no `puppeteer`/`playwright` dependency):**
1. `[REQ-SB-76-US-01-AC-11]` Loaded `/my-day/approvals` with 4 real, pending `propose_company_review` items (Core42/FAB/Microsoft/Thales — a bounded, freshly-proposed real batch from one further real Thread, `2026-08-04 FW- FAB & Core42 - NDRC Discovery & Workshop`, disclosed below) AND 2 real, pending items of OTHER kinds (`acknowledge_classification_failure`, `propose_cross_cutting_update`, both pre-existing, untouched by this session). DOM query confirmed exactly 4 `[data-testid="company-review-decision"]` regions and exactly 2 generic Approve/Decline rows — real coexistence.
2. Clicked Affiliate on the Core42 item → `[data-testid="company-review-affiliate-picker"]` appeared with 2 real `<select>`s; parent picker's real options were `['', 'ADNOC', 'TAQA', 'Unsorted', 'Core42', 'Presight']` (from a real `GET known-companies` call, confirmed fired via a `Page.addScriptToEvaluateOnNewDocument`-installed `window.fetch` spy).
3. Clicked Merge instead → `[data-testid="company-review-merge-picker"]` appeared with exactly 1 `<select>` (no kind choice).
4. `[REQ-SB-76-US-01-AC-03]` Clicked Customer on the real `FAB` item (a genuine, correct classification — kept) → real `fetch` spy captured `POST .../8e8f1c1924bc/approve` body `{"outcome":"customer"}`; the item disappeared from the list on success (real refetch). Confirmed on disk: `Work/Threads/2026-08-04 FW.../....md` now `customer: "FAB"`, `customer/fab` tag.
5. `[REQ-SB-76-US-01-AC-05]` Created 2 disposable real pending `propose_company_review` records (`ZZ-Decomposer-T08-Affiliate-UI-Test`/`-Merge-UI-Test`, each naming one disposable test Thread) purely for the Affiliate/Merge submit round trips, since no genuine real Affiliate/Merge relationship was available among the real batches (mirrors `T06`'s own identical allowance). Selected `ADNOC` + `customer` kind, clicked Confirm Affiliate → real `POST .../c38e0c3b24af/approve` body `{"outcome":"affiliate","parent_name":"ADNOC","parent_kind":"customer"}`; confirmed on disk: new disposable Customer entity's `affiliate_of: "ADNOC"`, its batch Thread's `customer` set to it.
6. `[REQ-SB-76-US-01-AC-10]` Selected `ADNOC`, clicked Confirm Merge → real `POST .../a0463f1954c3/approve` body `{"outcome":"merge","parent_name":"ADNOC","parent_kind":"customer"}` (the picker's own list-membership resolution supplied `parent_kind` even though Merge shows no separate kind control) — confirmed on disk: batch Thread routed to `ADNOC`, no new folder created for the duplicate name.
7. Clicked Decline on the real `Microsoft` item → real `POST .../0e9e946b6a0b/decline`, no body — byte-for-byte the same call every other item's Decline button already makes.
8. Regression: the 2 OTHER pending items' own `.item-row-actions` HTML confirmed unchanged (`<button class="btn btn-primary">Approve</button><button class="btn btn-danger">Decline</button>`) both before and after all of the above.
9. Cleanup: deleted both disposable test Threads and the disposable Affiliate-Customer entity; approved the real remaining `Core42` batch as Partner and declined the real remaining `Thales` batch (a vendor mention, not a real relationship) via the real API directly, leaving the Pending Approvals queue with zero leftover `propose_company_review` records from this task's own verification.

`MEMORY.md`: no new decision beyond `ADR-057`. `CHANGELOG.md` entry appended.
