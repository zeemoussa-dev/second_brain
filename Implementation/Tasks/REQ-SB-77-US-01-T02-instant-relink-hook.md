---
id: REQ-SB-77-US-01-T02
title: Instant re-link trigger — retarget finalize_company_review to call relink_people_for_thread_paths
parent_story: REQ-SB-77-US-01
requirement_id: REQ-SB-77
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-77-US-01-T01]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-77-US-01-T02 — Instant re-link trigger (Scenario 6a)

## Parent Story

- Story: [[REQ-SB-77-US-01]] — `../UserStories/REQ-SB-77-US-01-people-notes-linked-to-company-partner-note.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-77 *People Notes Linked to Their Real Company/Partner Note*
- Architecture: `Implementation/Architecture/architecture.md` → "People Notes Retroactively Linked to Company/Partner" § "Two real trigger points (Scenario 6)"

---

## Objective

Make every real Customer/Partner/Affiliate/Merge company-status change (`REQ-SB-76-US-01`'s own `finalize_company_review`) immediately re-link every affected Person note, with zero behavior change to any of the four existing outcome branches.

---

## Starting State → End State

**Before / Inputs:**
- `librarian_housekeeping.finalize_company_review(payload) -> dict` (`Done`, `REQ-SB-76-US-01-T06`) has one public body with 4 branches (Customer/Partner/Affiliate/Merge), all reading `payload["thread_paths"]`.
- `T01` has added `people_extraction.relink_people_for_thread_paths(thread_paths)`.

**After / Outputs:**
- `finalize_company_review`'s own existing 4-branch body is renamed in place to a private `_finalize_company_review_outcome(payload) -> dict` — **zero behavior change to any branch**.
- A new, thin public `finalize_company_review(payload) -> dict` wrapper composes it:

  ```python
  def finalize_company_review(payload: dict) -> dict:
      result = _finalize_company_review_outcome(payload)
      people_extraction.relink_people_for_thread_paths(payload["thread_paths"])
      return result
  ```

- `librarian_housekeeping.py` gains one new import, `from app.business import people_extraction` (business-to-business composition — reuses this module's own already-established "intentional, permitted horizontal call within the business layer, not an `ADR-003` boundary violation" precedent a second time).
- The existing "raises before any write" honest-failure contract is preserved by construction — a raise inside `_finalize_company_review_outcome` propagates straight through the wrapper before the relink call ever runs.

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` — rename `finalize_company_review`'s existing body to `_finalize_company_review_outcome`, add the new thin public `finalize_company_review` wrapper, add the `people_extraction` import.

---

## Constraints

- Inherits from parent story.
- **Zero behavior change to any of the 4 existing branches** — `_finalize_company_review_outcome`'s own body must be a pure rename, not a rewrite.
- **ONE relink call, not four** — `payload["thread_paths"]` is identical across all four outcomes; the wrapper calls `relink_people_for_thread_paths` exactly once, after `_finalize_company_review_outcome` returns.
- A raise from `_finalize_company_review_outcome` (the unconfirmable-`parent_name` honest-failure path, `REQ-SB-76-US-01-AC` coverage) must propagate through the wrapper unchanged — the relink call must never run before a successful outcome write, and a relink failure must never mask the outcome's own real result.
- `pending_approvals_router.py`'s own `_APPROVAL_HANDLERS["propose_company_review"] = finalize_company_review` registration needs zero change — the wrapper's own public signature (`payload: dict -> dict`) is identical to the function it replaces.
- No new linking primitive — `relink_people_for_thread_paths` (`T01`) is reused verbatim.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-77-US-01-AC-06]` Call `finalize_company_review(...)` with a real or disposable-test `"outcome": "customer"` payload for a company whose Threads reference at least one real Person note not yet linked to that company. Confirm the outcome's own real write happens exactly as before (Customer OKF folder / Thread frontmatter), AND confirm that Person note gains its real `**Customer:**` wikilink as a direct result of this ONE call — proving the instant trigger half of Scenario 6.
2. Confirm the honest-failure path is unaffected: call with an unconfirmable `parent_name` (Affiliate/Merge outcome). Confirm it raises before any write (identical to `REQ-SB-76-US-01-T06`'s own already-proven behavior) and that `relink_people_for_thread_paths` is never invoked.
3. Confirm all 4 branches (Customer/Partner/Affiliate/Merge) still produce byte-identical outcome results to before this change — spot-check at least the Customer and Partner branches directly.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `[REQ-SB-77-US-01-AC-06]` Instant trigger half verified live — a real `finalize_company_review` call relinks the affected Person note(s) in the same call
- [ ] All 4 existing outcome branches produce unchanged results (pure rename, not a rewrite)
- [ ] The unconfirmable-parent honest-failure path still raises before any write and before any relink call
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The scheduled self-heal trigger — `T03`/`REQ-SB-79-US-01-T02`.
- Any change to `_APPROVAL_HANDLERS` registration — the public function's signature is unchanged.
- Any change to `propose_company_review` or any branch's own internal logic.

---

## Context / Notes

`REQ-SB-76-US-01` may or may not be `Done` at build time — `finalize_company_review` already exists in the codebase today regardless (per this story's own `## Context`), so this task has no real dependency on `REQ-SB-76-US-01`'s own story status.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
