---
id: REQ-SB-76-US-01-T03
title: Fix migrate_customer_to_partner's OKF-directory blind spot; extract the generalized _retag_company_references/retarget_company_references primitive
parent_story: REQ-SB-76-US-01
requirement_id: REQ-SB-76
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-76-US-01-T02]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-76-US-01-T03 — migrate_customer_to_partner OKF fix + generalized retag primitive

## Parent Story

- Story: [[REQ-SB-76-US-01]] — `../UserStories/REQ-SB-76-US-01-company-review-extract-classify-and-batch-apply.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-76 *Company Review — Extract & Recommend, Customer/Partner/Affiliate Classification, Batch-Apply*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Company Review" (§ "`partner_hub_linking._retag_company_references()`/`retarget_company_references()`"), `Implementation/Architecture/ADR.md` → `ADR-057` Decisions 5/6

---

## Objective

Fix `migrate_customer_to_partner`'s real gap (Step 1 never resolves an OKF-directory-shaped Customer's real path, so it silently no-ops), correct Step 2's now-wrong `affiliate_of`-drop line, and extract Step 2's per-note rewrite logic into a new, parameterized `_retag_company_references(old_name, old_kind, new_name, new_kind)` plus a public thin sibling `retarget_company_references` — the Merge outcome's own entry point (`T06`).

---

## Starting State → End State

**Before / Inputs:**
- `migrate_customer_to_partner`'s Step 1: `old_hub_path = vault_writer.hub_note_path(customer_name)` only ever resolves the LEGACY flat path — never moves an OKF-directory-shaped Customer.
- Step 2's per-note scan is hardcoded to a Customer→Partner kind swap, including an `affiliate_of`-drop line that is now WRONG (Partner legitimately carries `affiliate_of` as of `T02`).
- No generalized, parameterized version of the retag scan exists — Merge (`T06`) has nothing to call.

**After / Outputs:**
- Step 1 gains an OKF-directory-first branch (tried BEFORE the legacy-flat check): if `vault_writer.customer_concept_file_exists(customer_name)`, moves the WHOLE OKF directory via `vault_writer.move_okf_directory(vault_writer.customer_directory_paths(customer_name)["directory"], vault_writer.partner_hub_note_path(customer_name).parent)`. Only when the OKF concept file does NOT exist does the existing legacy-flat branch run, unchanged.
- The `remove_frontmatter_key_if_present(path, "affiliate_of")` line is DELETED — an entity's own `affiliate_of` value, real or empty, carries forward untouched.
- A new `_retag_company_references(old_name, old_kind, new_name, new_kind) -> list[dict]` (`old_kind`/`new_kind` ∈ `{"customer", "partner"}`) generalizes Step 2's scan/rewrite from hardcoded Customer→Partner values to the four parameters.
- `migrate_customer_to_partner(customer_name)` becomes a thin wrapper — `_retag_company_references(customer_name, "customer", customer_name, "partner")` plus its own (now-fixed) Step 1 — behaviourally IDENTICAL to today by construction, zero external contract/call-site changes.
- A new public `retarget_company_references(old_name, old_kind, new_name, new_kind) -> list[dict]` is a one-line pass-through to `_retag_company_references` — `T06`'s Merge entry point.

---

## Files to Modify

- `src/backend/app/business/partner_hub_linking.py` — `migrate_customer_to_partner`, new `_retag_company_references`, new `retarget_company_references`.

---

## Constraints

- Inherits from parent story.
- `migrate_customer_to_partner`'s own external contract (signature, return shape `{"hub_note_moved", "hub_note_path", "notes_retagged"}`) is UNCHANGED — every existing call site keeps working with zero edits.
- Reuses `vault_writer.move_okf_directory` verbatim (the exact already-`Accepted` `REQ-SB-74-US-01-T04` primitive) — no new move primitive.
- The generic scan technique and its four per-note rewrite primitives (`rename_frontmatter_key`/`remove_frontmatter_key_if_present`/`swap_tag`/`replace_body_line`) are REUSED, not rewritten — only their hardcoded "Customer"/"Partner" values become parameters.
- Idempotency-by-construction is preserved — a second run of either `migrate_customer_to_partner` or `retarget_company_references` for the same pair makes zero further changes.
- No third move/retag primitive introduced anywhere in this task.

---

## Tests

**Real vault, but scoped to a small, clearly-labeled disposable test Customer/Partner pair for the destructive move/retag steps — never run against a real, currently-in-use Customer/Partner unless the operator has already indicated it should genuinely be migrated.**

**Manual verification steps:**
1. `[REQ-SB-76-US-01-AC-08]` Create a real, disposable, clearly-labeled test Customer (e.g. `"ZZ-Decomposer-OKF-Migrate-Test"`) via `customer_hub_linking.ensure_customer_hub_note` (real OKF directory, not legacy flat), and tag at least one other real disposable note with its `customer/<slug>` tag plus the inline `**Customer:** [[<hub stem>]]` body line. Call `migrate_customer_to_partner` for it; confirm (a) the WHOLE OKF directory genuinely moved to `Work/Partners/<slug>/` with every file's content byte-for-byte preserved (not a silent no-op — `hub_note_moved: True`), and (b) the other tagged note is correctly retagged (`partner/<slug>` tag, relabeled body wikilink).
2. Re-run `migrate_customer_to_partner` for the SAME name a second time; confirm `hub_note_moved: False` (nothing left to move) and `notes_retagged` shows every previously-touched note now `"already_migrated"` (idempotent by construction — zero further changes).
3. Confirm the migrated Partner entry's own `affiliate_of` key (added by `T02`) carries forward with its original value (empty, since the test Customer never had a real one set) — NOT dropped.
4. Call `retarget_company_references("ZZ-Decomposer-Merge-Test-A", "customer", "ZZ-Decomposer-Merge-Test-B", "customer")` against a second, disposable same-kind (Customer→Customer) test pair — confirm the SAME scan/rewrite mechanism correctly handles a same-kind name change (Merge's own shape), not just the kind-changing migration.
5. Clean up every disposable test artefact created in steps 1-4 (archive or delete, clearly test data, never real production entities).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `[REQ-SB-76-US-01-AC-08]` verified live — an OKF-directory-shaped Customer is genuinely migrated (not a no-op), every other referencing note is correctly retagged, and a second run is a true no-op
- [x] `affiliate_of` carries forward untouched through a migration (drop line removed)
- [x] `_retag_company_references`/`retarget_company_references` exist, generalized and verified against a same-kind pair
- [x] `migrate_customer_to_partner`'s own external contract unchanged — zero call-site edits needed
- [x] `MEMORY.md` updated (closes the disclosed `REQ-SB-54-US-01-T04`/`REQ-SB-62` gap — worth a decision/pattern entry)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Merge outcome's own archival step (`T06`'s own scope — this task only builds the retag primitive Merge calls).
- Giving Partner its own native OKF directory shape (`ADR-057`'s own rejected alternative).
- Provisioning `Work/Archive/Partners/` (disclosed gap, not fixed by this story).

---

## Context / Notes

`list_all_note_paths()` is already a recursive scan (confirmed by direct reading, `ADR-057` Context point 5) — Step 2 already discovers the OKF concept file today; the real gap is narrower than "the scan can't see it," it's Step 1's hardcoded legacy-flat path alone. Do not over-fix Step 2 beyond the one `affiliate_of`-drop-line removal.

---

## Implementation Log

**2026-08-19, coder.** Step 1 of `migrate_customer_to_partner` gained an OKF-directory-first branch (`vault_writer.customer_concept_file_exists` → `vault_writer.move_okf_directory`, verbatim reuse of the `REQ-SB-74-US-01-T04` primitive), tried before the existing legacy-flat-path check, which now runs only on a miss. Step 2's per-note rewrite logic was extracted into a new, parameterized `_retag_company_references(old_name, old_kind, new_name, new_kind)` (`old_kind`/`new_kind` ∈ `{"customer","partner"}`), generalizing the hardcoded Customer→Partner field-rename/type-swap/tag-swap/body-line-relabel logic from four literal values to four parameters; the now-wrong `remove_frontmatter_key_if_present(path, "affiliate_of")` line was deleted entirely (Partner now legitimately carries `affiliate_of`, `T02`). A new public `retarget_company_references(old_name, old_kind, new_name, new_kind)` is a one-line pass-through — the Merge outcome's own entry point (`T06`). `migrate_customer_to_partner(customer_name)` is now a thin wrapper — Step 1 (as above) plus `_retag_company_references(customer_name, "customer", customer_name, "partner")` — same external contract/return shape, zero call-site changes.

**Deviation from the task's own literal wording, disclosed:** to avoid a spurious "changed" flag on a same-kind/same-label rewrite (which would break the reused primitive's own idempotency-by-construction discipline for the NEW same-kind Merge path `T06` needs), `_retag_company_references` skips the `type` swap when `old_label == new_label` and skips the `kind/<kind>` tag swap when `old_kind == new_kind` — a scope-internal generalization judgement call, not a functional gap-fill; `migrate_customer_to_partner`'s own always-cross-kind call path is completely unaffected (its own `old_label != new_label`/`old_kind != new_kind` always).

**Verification — all manual, live, against real+disposable data:**
1. `[REQ-SB-76-US-01-AC-08]` Created a real, disposable OKF-directory Customer (`ZZ-Decomposer-OKF-Migrate-Test`) via `customer_hub_linking.ensure_customer_hub_note`; tagged a second disposable note with its `customer/<slug>` tag + inline `**Customer:** [[...]]` wikilink. `migrate_customer_to_partner` → the WHOLE OKF directory genuinely moved to `Work/Partners/<slug>/` (`hub_note_moved: True`, `index.md`/`log.md`/`captures.md` all preserved), the other note correctly retagged (`partner/<slug>` tag, relabeled wikilink, `customer`→`partner` field rename).
2. Re-ran for the same name: `hub_note_moved: False`, `notes_retagged: []`. **Nuance disclosed, not glossed over:** the task's own prose expected `notes_retagged` to show the previously-touched note re-listed as `"already_migrated"`; live behavior is an EMPTY list instead, because after migration neither Signal A (`frontmatter.get("customer")`, now renamed away) nor Signal B (body wikilink, now relabeled) matches that note anymore — so the scan's own leading `if not (matches_frontmatter or matches_body_wikilink): continue` excludes it before the per-note branch that would assign `"already_migrated"` is ever reached. This is INHERITED, frozen behavior from the original `REQ-SB-16` `migrate_customer_to_partner` (its own docstring already documents this exact "excluded on a rerun" mechanism) — confirmed unchanged by this task's generalization, not a new defect. The real invariant the test cares about — "idempotent by construction, zero further changes" — is fully satisfied (`hub_note_moved: False`, no writes of any kind on the second call).
3. Migrated concept file's own `affiliate_of` confirmed `""` (unset originally, carried forward, not dropped).
4. `retarget_company_references("ZZ-Decomposer-Merge-Test-A", "customer", "ZZ-Decomposer-Merge-Test-B", "customer")` against a disposable same-kind pair — the other note referencing A was correctly retagged to B (field value renamed, tag swapped, wikilink relabeled to B's own stem); confirms the generalized primitive handles a same-kind name change (Merge's own shape), not just the kind-changing migration.
5. All disposable test artefacts (2 directories, 2 loose notes) deleted afterward.

No `ADR.md` edit made (architect already recorded the revision in `ADR-009`'s `**Status:**` line). `MEMORY.md` updated (closes the `REQ-SB-54-US-01-T04`/`REQ-SB-62` disclosed gap). `CHANGELOG.md` entry appended.
