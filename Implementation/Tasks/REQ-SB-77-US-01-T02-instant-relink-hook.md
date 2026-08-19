---
id: REQ-SB-77-US-01-T02
title: Instant re-link trigger — retarget finalize_company_review to call relink_people_for_thread_paths
parent_story: REQ-SB-77-US-01
requirement_id: REQ-SB-77
type: backend
status: Done
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

- [x] `[REQ-SB-77-US-01-AC-06]` Instant trigger half verified live — a real `finalize_company_review` call relinks the affected Person note(s) in the same call
- [x] All 4 existing outcome branches produce unchanged results (pure rename, not a rewrite)
- [x] The unconfirmable-parent honest-failure path still raises before any write and before any relink call
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — none emerged)
- [x] `CHANGELOG.md` entry appended

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

**Built 2026-08-19.** `finalize_company_review`'s existing 4-branch body was renamed in place to `_finalize_company_review_outcome` (pure rename — docstring updated to note the rename and disclose the wrapper, body text of all 4 branches byte-for-byte unchanged). A new, thin public `finalize_company_review(payload) -> dict` wrapper was added directly above it, calling `_finalize_company_review_outcome(payload)` then `people_extraction.relink_people_for_thread_paths(payload["thread_paths"])`, returning the outcome result unchanged — exactly the composition specified in the task's own End-State code block and `architecture.md`.

**Deviation from plan (scope-internal judgement call, logged for spot-check, non-blocking):** the task's own Constraints say "`librarian_housekeeping.py` gains one new import, `from app.business import people_extraction`." Direct reading of the real, current file (per this project's own "always compose around the REAL current file" discipline) found `people_extraction` was **already** imported on the module's existing `from app.business import ...` line — added by `SPRINT-073`/`REQ-SB-79-US-01-T02`'s own sibling work (`run_company_partner_building_pass()` already calls `people_extraction.retrofit_people_from_emails()`). No import line was added or changed; this task's own code change is exactly the rename + the new wrapper function, nothing else.

**Verification (manual mode, real vault, direct Python-shell calls — no HTTP layer needed, matching this task's own Tests block):**
1. `[REQ-SB-77-US-01-AC-06]` Real Thread `Work/Threads/2026-08-13 Recall- Ewec Discussion (Compass - AI) online/...md` (sender `animas.caustro@ewec.ae`, derived company "Ewec", genuinely NOT yet a known Customer/Partner, `customer`/`partner` primary genuinely unset) — snapshotted before. Called `finalize_company_review({"company": "Ewec", "thread_paths": [<path>], "outcome": "customer"})`. Confirmed: (a) the outcome write happened exactly as the Customer branch's own contract (`hub_note_path`, `threads_applied`, `message` — a real new `Work/Customers/Ewec/` OKF directory created, Thread frontmatter `customer: "Ewec"` / `tags: [..., "customer/ewec"]`); (b) the real Person note `Work/People/animas.caustro@ewec.ae.md` gained the real `**Customer:** [[Ewec]]` wikilink as a DIRECT result of this ONE call (confirmed by reading the file immediately after, before any second call) — proving the instant trigger. **PASS.** Both files, plus the newly-created `Work/Customers/Ewec/` directory, were reverted/removed immediately after (byte-for-byte restore of the two pre-existing files from a snapshot; the wholly-new directory deleted outright, since it had zero prior content) — confirmed clean via `Test-Path` returning `False` and a byte-for-byte post-revert read of both files matching the pre-test snapshot exactly.

   (First attempt used the real `2026-07-28 MIC` Thread/`Microsoft` company and found a genuine, disclosed pre-existing behavior of the ALREADY-SHIPPED `_apply_company_to_threads` helper, unrelated to this task's own change: that Thread already had `partner: "Core42"` set as its primary, so applying a NEW `outcome: "customer"` classification took the pre-existing ADDITIVE-tag branch — `customer/microsoft` was added to `tags`, but the primary `customer:` field stayed `"Unsorted"` (by design — a Thread's primary field is single-value, `_apply_company_to_threads`'s own documented contract). Since `list_known_customers()` reads only the primary `customer:` field, not tags, "Microsoft" never became vault-known, so `relink_people_for_thread_paths` correctly found no match and wrote no wikilink — the wrapper fired correctly; the underlying mechanism simply had nothing new to link given this specific Thread's own pre-existing dual-company state. Not a defect in this task's own change (out of scope — `_apply_company_to_threads` is untouched, pre-existing `REQ-SB-76-US-01-T06` code). This first attempt's own writes (the `Work/Customers/Microsoft/` directory, the additive `customer/microsoft` tag on the MIC Thread) were fully reverted before re-attempting with a cleaner candidate Thread. Logged here as a real, disclosed live finding, not silently discarded.)
2. `[REQ-SB-77-US-01-AC-06]` Called `finalize_company_review` with a disposable-test payload — `outcome: "affiliate"`, `parent_name: "CompletelyUnconfirmableParentXYZ123"`, `parent_kind: "customer"` (a name guaranteed not to exist in the real vault), plus a non-existent `thread_paths` entry (irrelevant — the check fires before any Thread is ever touched). Wrapped `people_extraction.relink_people_for_thread_paths` with an in-process call-counting spy (a scoped, reverted monkeypatch, this project's own established failure-induction technique) before the call. Confirmed: `ValueError` raised with the expected "unconfirmable parent entity" message, BEFORE any write; the spy's call count was `0` — `relink_people_for_thread_paths` was never invoked. **PASS**, exactly as the Constraint requires.
3. Spot-checked the Customer branch (step 1 above) and the Partner branch independently: real Thread `Work/Threads/2026-08-13 [ Core42 @UAE ] SimplAI.../...md` (sender `gurpreet.singh@simplai.ai`, company "Simplai", genuinely unmatched), called `finalize_company_review({"company": "Simplai", "thread_paths": [<path>], "outcome": "partner"})`. Confirmed the returned dict shape (`outcome`, `company`, `hub_note_path`, `threads_applied`, `message`) is byte-for-byte identical in SHAPE to the pre-existing, unmodified Partner-branch contract (`hub_note_path` pointed at the real new `Work/Partners/Simplai.md`), and the real Person note gained `**Partner:** [[Simplai]]` as a direct result of this one call. **PASS.** Reverted the same way as step 1 (Thread/Person notes restored from snapshot, the new `Work/Partners/Simplai.md` file deleted). The Affiliate branch's own real write path (steps 1/3 of this task plus `REQ-SB-76-US-01-T09`'s own already-`Done` live verification of the Affiliate/Merge branches) was not independently re-run here beyond the honest-failure path (step 2) — its own body is untouched by this task's rename (confirmed by direct diff: only the `def` line and the docstring's own first sentence changed inside `_finalize_company_review_outcome`, zero changes to any branch's internal logic).

All real vault writes made during this task's own live verification (2 Customer-hub-shaped test classifications, 1 Partner-hub-shaped test classification, their Thread/Person-note side effects) were disposable, clearly-labeled-in-this-log, and fully reverted immediately after each confirmed pass — the real vault's own actual Customer/Partner/Thread/Person state is unchanged from before this task started (confirmed via `git status`-equivalent, byte-for-byte snapshot restores).

**MEMORY.md:** not updated — no new decision/pattern/constraint; the one real live finding (dual-company-Thread additive-tag interaction with `list_known_customers()`) is a pre-existing, already-disclosed property of already-`Done` code (`_apply_company_to_threads`, `list_known_customers`), not new information this task's own change introduced.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired (no new ADR, the one scope-internal judgement call above is disclosed for spot-check not hidden, no new ESCALATIONS entry, not oversized, the locked AC and every Constraint verified live with a real positive result).
