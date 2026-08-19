---
id: REQ-SB-76-US-01-T06
title: finalize_company_review() dispatch — Customer/Partner/Affiliate/Merge branches
parent_story: REQ-SB-76-US-01
requirement_id: REQ-SB-76
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-76-US-01-T02, REQ-SB-76-US-01-T03, REQ-SB-76-US-01-T05]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-76-US-01-T06 — `finalize_company_review()` dispatch

## Parent Story

- Story: [[REQ-SB-76-US-01]] — `../UserStories/REQ-SB-76-US-01-company-review-extract-classify-and-batch-apply.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-76 *Company Review — Extract & Recommend, Customer/Partner/Affiliate Classification, Batch-Apply*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Company Review" (§ "`propose_company_review()`/`finalize_company_review()`"), `Implementation/Architecture/ADR.md` → `ADR-057` Decisions 3, 7, 8

---

## Objective

Add `librarian_housekeeping.finalize_company_review(payload) -> dict` — ONE handler, branching internally on `payload["outcome"]` (`"customer" | "partner" | "affiliate" | "merge"`), called only once the operator's decision is merged into the stored payload by the router (`T07`).

---

## Starting State → End State

**Before / Inputs:**
- `T02` has added `affiliate_of` to both entity shapes. `T03` has fixed `migrate_customer_to_partner` and added `retarget_company_references`. `T05` has added `_apply_company_to_threads`.
- No `finalize_company_review` function exists.

**After / Outputs:**
- **Customer** branch: `customer_hub_linking.ensure_customer_hub_note(company)` (UNCHANGED), then `_apply_company_to_threads(thread_paths, company, "customer")`.
- **Partner** branch: `partner_hub_linking.ensure_partner_hub_note(company)` (UNCHANGED), then `_apply_company_to_threads(thread_paths, company, "partner")`.
- **Affiliate** branch: ensures the entity (Customer or Partner, per `payload["parent_kind"]` naming the NEW entity's own kind) exactly as above, then `vault_writer.upsert_frontmatter_key(<entity path>, "affiliate_of", payload["parent_name"])`, then `_apply_company_to_threads`.
- **Merge** branch: validates `parent_name`/`parent_kind` name a real, existing entity (`customer_concept_file_exists`/`hub_note_exists` for Customer, `partner_hub_note_exists` for Partner — raises before any write if not confirmable); `_apply_company_to_threads(thread_paths, parent_name, parent_kind)` routes every batch Thread to the canonical entity; if `company` already has a real prior entity of its own, calls `partner_hub_linking.retarget_company_references(company, <company's own real kind>, parent_name, parent_kind)` to redirect every OTHER vault note's reference, then archives the now-unreferenced duplicate via `vault_writer.move_okf_directory` (OKF-shaped) or `vault_writer.move_note_and_attachments` (legacy-flat-shaped) to `Work/Archive/Customers/` — reusing `finalize_customer_archival`'s own exact call shape as a plain same-module function call. Disclosed, not fixed: a Partner-shaped duplicate is retargeted but not archived (no `Work/Archive/Partners/` root exists).
- A `parent_name` the server cannot independently confirm as a real, existing entity of the claimed `parent_kind` raises BEFORE any write happens — the record stays `"pending"`, never half-applied (existing call order already guarantees this — no new error-handling mechanism needed).

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` — new `finalize_company_review` (place near `finalize_customer_backfill_routing`, its nearest structural sibling).

---

## Constraints

- Inherits from parent story.
- `ensure_customer_hub_note`/`ensure_partner_hub_note`/`link_note_to_partner_hub` are reused UNMODIFIED — this task never edits them.
- `affiliate_of` writes reuse `vault_writer.upsert_frontmatter_key` verbatim — no new write primitive.
- Merge reuses `retarget_company_references` (`T03`) and `finalize_customer_archival`'s own exact call shape (`REQ-SB-74-US-01`, `move_okf_directory`) — NO new move/retag/archival primitive.
- A company is still never both a Customer and a Partner at once (`ADR-009` point 1, untouched) — the Affiliate/Merge branches' own `parent_kind`/entity-kind choices must not violate this.
- Never a silent write — every branch's real write happens only inside this function, called only after the operator's real approval.

---

## Tests

**Real vault. This is the outcome-writing half — use REAL, genuine companies discovered by `T04`'s own real extraction pass wherever a real company/batch is available (a legitimate real classification the operator would want anyway), and clearly-labeled disposable test entities only where no real, low-risk example exists yet (e.g. the Affiliate-of-Partner branch, or a Merge pair, if no real duplicate-name pair is currently pending). Never mass-resolve real, unreviewed Pending Approval records as part of this task's own verification — call `finalize_company_review` DIRECTLY against a hand-constructed or genuinely-approved real payload, one outcome at a time, and record exactly what was written.**

**Manual verification steps:**
1. `[REQ-SB-76-US-01-AC-03]` Customer branch: call `finalize_company_review({"company": "<real or disposable test company>", "thread_paths": [<1-2 real Thread paths>], "outcome": "customer"})`. Confirm the Customer OKF directory is created/confirmed and every named Thread's real `customer` frontmatter + `customer/<slug>` tag are set. Confirm a Thread NOT in `thread_paths` is untouched.
2. `[REQ-SB-76-US-01-AC-04]` Partner branch: same shape, `"outcome": "partner"`. Confirm the Partner hub note is created/confirmed under `Work/Partners/` and every named Thread is linked + tagged `partner/<slug>`.
3. `[REQ-SB-76-US-01-AC-05]` Affiliate-of-Customer: call with `"outcome": "affiliate", "parent_name": "<a real, already-known Customer>", "parent_kind": "customer"`. Confirm the new entity's own Customer OKF concept file carries `affiliate_of` = the real parent's name, and the batch Threads are processed exactly as step 1.
4. `[REQ-SB-76-US-01-AC-06]` Affiliate-of-Partner: same shape, `"parent_kind": "partner"` naming a real, already-known Partner. Confirm the new Partner hub note's `affiliate_of` is set (a real, non-empty value where Partner previously carried none at all) and the batch Threads are processed exactly as step 2.
5. Confirm the honest-failure path: call with a `parent_name` that does NOT resolve to any real, existing entity of the claimed `parent_kind`; confirm it raises before any write, and that no batch Thread was touched.
6. `[REQ-SB-76-US-01-AC-10]` Merge, WITHOUT the duplicate's own prior entity: call with `"outcome": "merge", "parent_name": "<a real, existing canonical entity>", "parent_kind": "customer"|"partner"`, for a `company` that has no entity of its own yet. Confirm every batch Thread is routed to the CANONICAL entity's frontmatter/tag, and no new folder/entity was created for `company`.
7. `[REQ-SB-76-US-01-AC-10]` Merge, WITH the duplicate's own prior real OKF content — the operator's own real Mudala/Mubadala-shaped case: find (or, if none exists yet, create a small, clearly-labeled disposable OKF-shaped duplicate with real placeholder content) a duplicate-name entity with its own real content, then Merge it into a real canonical parent. Confirm: content is genuinely moved into the canonical entity via `retarget_company_references` (every other note's own reference correctly redirected), the duplicate's own now-empty folder is ARCHIVED (moved to `Work/Archive/Customers/`, content preserved) — never deleted, and every batch Thread is routed to the canonical entity.
8. Record every real write made across steps 1-7 explicitly in this task's own Implementation Log (which entities/Threads were touched, real vs. disposable-test).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `[REQ-SB-76-US-01-AC-03]` Customer branch verified live
- [x] `[REQ-SB-76-US-01-AC-04]` Partner branch verified live
- [x] `[REQ-SB-76-US-01-AC-05]` Affiliate-of-Customer verified live, real `affiliate_of` value set
- [x] `[REQ-SB-76-US-01-AC-06]` Affiliate-of-Partner verified live, real `affiliate_of` value set on a shape that previously had none
- [x] `[REQ-SB-76-US-01-AC-10]` Merge verified live in both shapes (no prior duplicate entity; with a real, content-bearing prior duplicate — archived not deleted)
- [x] An unconfirmable `parent_name`/`parent_kind` raises before any write, record stays pending
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision beyond `ADR-057`)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Approve-endpoint decision body/dispatch wiring — `T07`'s own scope (this task only builds the function `T07` registers).
- Provisioning `Work/Archive/Partners/` — disclosed, not fixed.
- The `propose_company_review()` Job itself — `T04`.

---

## Context / Notes

`ADR-057` Decision 3's own call-order guarantee (`_APPROVAL_HANDLERS[...]` runs BEFORE `resolve_pending_approval`) is what makes step 5's honest-failure test meaningful — a raised exception here means the router (unmodified logic) never marks the record resolved.

---

## Implementation Log

**2026-08-19, coder.** Added `librarian_housekeeping.finalize_company_review(payload) -> dict` near `finalize_customer_backfill_routing`, branching on `payload["outcome"]`. Customer/Partner branches call `ensure_customer_hub_note`/`ensure_partner_hub_note` (unmodified) then `_apply_company_to_threads` (`T05`). Affiliate validates the named parent via a new `_known_entity_exists(name, kind)` helper (`customer_concept_file_exists`/`hub_note_exists` for Customer, `partner_hub_note_exists` for Partner — the exact check `ADR-057` Decision 3 names), ensures the NEW entity, sets its `affiliate_of` via the already-existing `vault_writer.upsert_frontmatter_key`, then applies to Threads. Merge validates the parent the same way, applies the canonical entity to every batch Thread FIRST, then — only if the duplicate name already has a real prior entity of its own (a new `_existing_duplicate_shape(company)` helper distinguishing OKF-Customer/legacy-flat-Customer/Partner shapes) — calls `partner_hub_linking.retarget_company_references` (`T03`) to redirect every other note's reference, then archives the duplicate via `vault_writer.move_okf_directory` or `vault_writer.move_note_and_attachments` (matched to its own real shape) to `Work/Archive/Customers/`, reusing `finalize_customer_archival`'s own exact call shape. A Partner-shaped duplicate is retargeted but not archived (no `Work/Archive/Partners/` root — disclosed, not fixed, `ADR-057` Consequences). An unconfirmable `parent_name`/`parent_kind` raises `ValueError` before any write.

**Verification — live, real + disposable data. Customer/Partner branches (AC-03/AC-04) were verified via the REAL Approve endpoint against real `propose_company_review` batches as part of `T07`'s own live verification (same `finalize_company_review` function, dispatched through the router) rather than a second, duplicate direct call here — see `T07`'s own Implementation Log for the real writes; summarized:**
- `[REQ-SB-76-US-01-AC-03]` Real `ADNOC` batch approved with `{"outcome":"customer"}` via `POST /pending-approvals/{id}/approve` → `ensure_customer_hub_note` confirmed the already-existing ADNOC folder, both named real Threads' `customer` frontmatter + `customer/adnoc` tag set.
- `[REQ-SB-76-US-01-AC-04]` Real `Core42` batch approved with `{"outcome":"partner"}` → `ensure_partner_hub_note` confirmed the already-existing Core42 hub note, the named real Thread (already `customer: "ADNOC"` from the step above) took the ADDITIVE path — `partner/core42` tag + `## Related` gained `[[Core42]]`.

**Steps run directly in THIS task (disposable entities, cleaned up afterward — no genuine real Affiliate/Merge relationship was on hand, per this task's own explicit "disposable where no real low-risk example exists" allowance):**
1. `[REQ-SB-76-US-01-AC-05]` Affiliate-of-Customer: `finalize_company_review({"company": "ZZ-Decomposer-T06-Affiliate-Child-Customer", "thread_paths": [<1 disposable test Thread>], "outcome": "affiliate", "parent_name": "ADNOC", "parent_kind": "customer"})` (parent = REAL, already-known ADNOC) → new Customer OKF directory created, its concept file's `affiliate_of` = `"ADNOC"`, the batch Thread processed exactly as the plain-Customer path.
2. `[REQ-SB-76-US-01-AC-06]` Affiliate-of-Partner: same shape, `parent_kind: "partner"`, parent = REAL, already-known `Core42` → new Partner hub note's `affiliate_of` = `"Core42"` (a real, non-empty value where Partner previously carried none at all), batch Thread processed exactly as the plain-Partner path (`partner` field set, `Unsorted` `customer` field left alone).
3. Honest-failure: `parent_name="ZZ-No-Such-Real-Entity"` → raised `ValueError` before any write; no batch Thread touched.
4. `[REQ-SB-76-US-01-AC-10]` Merge, no prior duplicate entity: batch Thread routed straight to `ADNOC`'s own frontmatter/tag; confirmed `customer_concept_file_exists("ZZ-Decomposer-T06-Merge-Duplicate-NoDupe")` stayed `False` — no new folder ever created for the duplicate name.
5. `[REQ-SB-76-US-01-AC-10]` Merge WITH prior real OKF content: created a disposable OKF Customer with real placeholder `## Background` content plus a second note referencing it; Merge into `ADNOC` → the referencing note's own `customer` field/tag/wikilink correctly redirected to ADNOC (via `retarget_company_references`), the duplicate's now-empty OKF directory genuinely ARCHIVED (moved to `Work/Archive/Customers/<slug>/`, `index.md`/`log.md`/`captures.md`/the real placeholder `## Background` content all preserved byte-for-byte) — never deleted.
6. Every disposable artefact from steps 1/2/4/5 deleted afterward (2 disposable Customer/Partner entities, the disposable Merge-duplicate's archived folder, 5 disposable test notes).

`MEMORY.md`: no new decision beyond `ADR-057`. `CHANGELOG.md` entry appended.
