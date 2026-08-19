---
id: REQ-SB-76-US-01-T05
title: _apply_company_to_threads shared helper — primary-write vs. additive-tag-plus-Related branching
parent_story: REQ-SB-76-US-01
requirement_id: REQ-SB-76
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-76-US-01-T05 — `_apply_company_to_threads` shared helper

## Parent Story

- Story: [[REQ-SB-76-US-01]] — `../UserStories/REQ-SB-76-US-01-company-review-extract-classify-and-batch-apply.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-76 *Company Review — Extract & Recommend, Customer/Partner/Affiliate Classification, Batch-Apply*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Company Review" (§ "`_apply_company_to_threads`"), `Implementation/Architecture/ADR.md` → `ADR-057` Decision 8

---

## Objective

Add `librarian_housekeeping._apply_company_to_threads(thread_paths, target_name, target_kind) -> list[str]` — the single shared per-Thread apply helper all four Customer/Partner/Affiliate/Merge finalize outcomes (`T06`) call: writes the PRIMARY `customer`/`partner` field + tag when a Thread's own current state is still unset/`"Unsorted"`, or an ADDITIVE tag + regenerated `## Related` section when it is already set to a different real company (Scenario 9).

---

## Starting State → End State

**Before / Inputs:**
- No shared per-outcome apply helper exists — `finalize_customer_backfill_routing` (a DIFFERENT, `Done`, unrelated function) always writes the primary field unconditionally, with no already-set-vs-unset branch.
- `email_classification.build_thread_related_wikilinks` exists and already accepts `mentioned_companies` (added `REQ-SB-72-US-01-T06`).

**After / Outputs:**
- For each Thread in `thread_paths`, freshly reads its CURRENT `customer`/`partner` frontmatter AT CALL TIME (never trusts a stale snapshot):
  - If still unset/`"Unsorted"`: writes `target_name` to the primary `customer`/`partner` field (matching `target_kind`) plus the `target_kind/<slug>` tag.
  - If already set to a DIFFERENT real company: leaves the primary field byte-for-byte untouched; adds an ADDITIVE `target_kind/<slug>` tag (alongside existing tags); regenerates that Thread's own `## Related` section via `email_classification.build_thread_related_wikilinks` directly, written via `vault_writer.replace_body_section(concept_path, "## Related", ..., caller="librarian_housekeeping.populate_thread_related_links")` — the SAME already-registered `section_ownership.py` caller id.
- Returns the list of Thread paths actually processed.

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` — new `_apply_company_to_threads` (place near `finalize_customer_backfill_routing`, its nearest structural sibling).

---

## Constraints

- Inherits from parent story.
- Reads each Thread's own CURRENT state at call time, never from a payload snapshot taken at propose time — a different Company Review batch could resolve first and change that state in between.
- `customer:`/`partner:` frontmatter stays single-value — the primary-write branch only ever fires when the field is genuinely unset/`"Unsorted"`.
- Reuses `email_classification.build_thread_related_wikilinks` DIRECTLY — never `populate_thread_related_links()` itself (a whole-vault batch Job with no per-Thread entry point; extracting one is an unrelated refactor out of this task's scope).
- Writes `## Related` under the SAME already-registered `librarian_housekeeping.populate_thread_related_links` caller id in `section_ownership.py` — no new registry entry.
- No Thread outside `thread_paths` is ever touched.

---

## Tests

**Real vault — writes real frontmatter/tags/body content to real Threads. Use real, already-`"Unsorted"` Threads for the primary-write branch (a legitimate real classification, not a fabricated one), and pick a real Thread that ALREADY has a genuine primary `customer` set for the additive branch — confirm its identity and current state directly before writing, and re-confirm its untouched primary field afterward.**

**Manual verification steps:**
1. `[REQ-SB-76-US-01-AC-09]` Pick one real Thread whose own current `customer` frontmatter is already set to a real, previously-confirmed company (not `"Unsorted"`). Record its exact current `customer` value and its current `tags`/`## Related` content before this test. Call `_apply_company_to_threads([<that thread path>], "<a different real, known company>", "customer")`. Confirm: (a) that Thread's `customer` frontmatter is byte-for-byte identical to the value recorded before the call; (b) a new `customer/<slug>` (or `partner/<slug>`) tag for the NEW company was added, alongside every pre-existing tag; (c) `## Related` now includes a real wikilink to the new company's own concept file, generated via `build_thread_related_wikilinks`.
2. Pick a real, genuinely `"Unsorted"` Thread. Call `_apply_company_to_threads([<that thread path>], "<a real company>", "customer")`. Confirm the primary `customer` field is now set to that company AND the `customer/<slug>` tag was added (the "primary write" path, Scenarios 3-6/10's own precondition).
3. Confirm no Thread outside the single-element `thread_paths` list passed in either call above was touched.
4. Confirm the `## Related` write in step 1 used the registered `librarian_housekeeping.populate_thread_related_links` caller id (no `SectionWriteNotAllowed` raised, no new `section_ownership.py` entry needed).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `[REQ-SB-76-US-01-AC-09]` verified live — additive tag + `## Related` link, original `customer` field byte-for-byte untouched
- [x] Primary-write branch verified live against a real `"Unsorted"` Thread
- [x] `## Related` write reuses `build_thread_related_wikilinks` + the existing registered caller id, no new `section_ownership.py` entry
- [x] No Thread outside the passed `thread_paths` touched
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision beyond `ADR-057`)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Entity creation/confirmation (`ensure_customer_hub_note`/`ensure_partner_hub_note`) — `T06`'s own scope, called before this helper.
- `affiliate_of` writes — `T06`'s own scope.
- The Merge outcome's own retag/archival step — `T03`/`T06`.

---

## Context / Notes

This helper is deliberately the ONE place Scenario 9's already-set-vs-unset check lives — every one of `T06`'s four outcome branches calls it, so the branch logic is written exactly once.

---

## Implementation Log

**2026-08-19, coder.** Added `librarian_housekeeping._apply_company_to_threads(thread_paths, target_name, target_kind) -> list[str]` near `finalize_customer_backfill_routing`. For each Thread: reads current `customer`/`partner` frontmatter fresh at call time; if both are unset/`"Unsorted"`, writes `target_name` to the primary `target_kind` field AND replaces any existing `customer/...`/`partner/...` tags-list element with the real `target_kind/<slug>` tag (deviation from a first draft that merely appended — corrected to mirror `finalize_customer_backfill_routing`'s own tag-CORRECTION shape, exactly as the architecture text names — see "Deviation" below); otherwise leaves the primary field untouched, adds an ADDITIVE `target_kind/<slug>` tag (never replacing an existing one), and regenerates `## Related` via `email_classification.build_thread_related_wikilinks` directly, written under the already-registered `librarian_housekeeping.populate_thread_related_links` caller id.

**Deviation, disclosed (scope-internal correction, not a functional gap-fill):** the first implementation only ever APPENDED the target tag in both branches. Re-reading `architecture.md`'s own text ("mirroring `finalize_customer_backfill_routing`'s own tag-correction shape") made clear the primary-write branch should REPLACE a stale `customer/unsorted` placeholder tag, not leave it sitting alongside the new real tag. Corrected before any live verification ran against real data.

**Verification — live, real vault, real Threads (writes kept — legitimate real classifications, not fabricated, per this task's own Tests framing):**
1. `[REQ-SB-76-US-01-AC-09]` Real Thread `2026-07-28 Confirmation to Core42 - Insight & Alpha for Aldar` (`customer: "Aldar"`, genuinely also involves Core42 — its own participant is `naima.bikbi@core42.ai`). `_apply_company_to_threads([...], "Core42", "partner")` → `customer` frontmatter unchanged (`"Aldar"`, byte-for-byte), new `partner/core42` tag added alongside the existing `customer/aldar`/`kind/emails` tags, `## Related` regenerated with a new `[[Core42]]` wikilink added to the pre-existing `[[Aldar]]`/`[[naima.bikbi@core42.ai]]` links (no prior link dropped, `build_thread_related_wikilinks` recomputes the Customer/participant links fresh from frontmatter each call). No `SectionWriteNotAllowed` raised — confirms the reused caller id.
2. Real, genuinely-`"Unsorted"` Thread `2026-08-05 Visitor Feedback Request - ADNOC` (participant `systemnotification@adnoc.ae`, `## Related` already named `[[ADNOC]]`). `_apply_company_to_threads([...], "ADNOC", "customer")` → `customer` set to `"ADNOC"`, the stale `customer/unsorted` tag REPLACED by `customer/adnoc` (not left duplicated).
3. Confirmed no Thread outside either single-element `thread_paths` list was touched (snapshotted every other real Thread's own `customer` value before/after both calls — identical).
4. Caller-id reuse confirmed by the absence of any `section_ownership.SectionWriteNotAllowed` exception across both calls.

Both real writes are kept as genuinely correct classifications (Aldar's own thread legitimately also involves Core42; the ADNOC visitor-feedback Thread genuinely belongs to ADNOC) — not reverted.

`MEMORY.md`: no new decision beyond `ADR-057` (the tag-replace-vs-append correction is implementation-conformance to the architecture text, not a new decision). `CHANGELOG.md` entry appended.
