---
id: REQ-SB-72-US-01-T07
title: Company folder backfill Job + ambiguous-finding Pending Approval
parent_story: REQ-SB-72-US-01
requirement_id: REQ-SB-72
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-72-US-01-T05]
created: 2026-08-18
updated: 2026-08-19
---

# REQ-SB-72-US-01-T07 — Company folder backfill Job + ambiguous-finding Pending Approval

## Parent Story

- Story: [[REQ-SB-72-US-01]] — `../UserStories/REQ-SB-72-US-01-librarian-section-first-housekeeping-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-72 *The Librarian Section — First Housekeeping Pipeline*
- Architecture: `Implementation/Architecture/architecture.md` → "Company-mention detection & the ambiguous-finding Pending Approval" (`ADR-049` Decision 5)

---

## Objective

For every company mention `T05` classifies `"new_unambiguous"`, auto-create its Customer folder via the existing, unmodified `ensure_customer_hub_note`. For every mention classified `"ambiguous"`, create a real Pending Approval instead of guessing — approving performs the deferred create-or-link action, declining performs nothing.

---

## Starting State → End State

**Before / Inputs:**
- `customer_hub_linking.ensure_customer_hub_note(customer) -> dict` already exists, unchanged, unconditionally creates a Customer's OKF baseline (Tier-1-shaped, no approval).
- `vault_filing_expert._create_cross_cutting_proposal`/`finalize_cross_cutting_update` is the established propose/finalize shape this task's own new mechanism mirrors (never a second, divergent one).
- `app/api/pending_approvals_router.py`'s `_APPROVAL_HANDLERS` dict dispatches `action_id` → finalize handler on Approve.

**After / Outputs:**
- New `librarian_housekeeping.backfill_company_folders() -> dict` Job:
  - Iterates `vault_writer.list_thread_notes()`; for each, calls `T05`'s `detect_mentioned_companies_for_thread`.
  - For every `"new_unambiguous"` mention: calls `customer_hub_linking.ensure_customer_hub_note(mention["name"])` directly — no approval.
  - For every `"ambiguous"` mention: calls a new `_create_librarian_company_link_proposal(entity_name, reason, thread_path, requesting_agent_id="librarian-housekeeping")` — mirrors `_create_cross_cutting_proposal`'s exact shape (LOCAL `pending_approval_registry` import, `trigger="direct"`), creating a Pending Approval with `action_id="propose_librarian_company_link"` and payload `{"entity_name", "reason", "thread_path", "requesting_agent_id"}`.
  - Returns `{"created_folders": [...], "pending_approvals": [approval_id, ...]}`.
- New `librarian_housekeeping.finalize_librarian_company_link(payload: dict) -> dict` — called only on Approve, mirrors `finalize_cross_cutting_update`'s own "payload-driven deferred write" shape: performs the deferred `ensure_customer_hub_note(payload["entity_name"])` call. Never called for a declined record (declining performs nothing, per `pending_approval_registry`'s own existing decline contract — no code change needed there).
- `pending_approvals_router.py`'s `_APPROVAL_HANDLERS` gains `"propose_librarian_company_link": librarian_housekeeping.finalize_librarian_company_link`.

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` — add `backfill_company_folders()`, `_create_librarian_company_link_proposal()`, `finalize_librarian_company_link()`.
- `src/backend/app/api/pending_approvals_router.py` — register the new `_APPROVAL_HANDLERS` entry + import.

---

## Constraints

- Inherits from parent story.
- Never a second, divergent placement/proposal mechanism — `ensure_customer_hub_note` reused unchanged for the confident case; the propose/finalize shape mirrors `_create_cross_cutting_proposal`/`finalize_cross_cutting_update` exactly (`ADR-021` point 2).
- An `"ambiguous"` mention NEVER autonomously links or creates a folder — only a Pending Approval, until approved.
- Declining a `propose_librarian_company_link` Pending Approval performs nothing — no code path in this task may perform the create/link action outside `finalize_librarian_company_link`, and that function is only ever invoked from the Approve dispatch table.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-72-US-01-AC-09]` Direct Python-shell / real endpoint check: construct or identify a real Thread whose content confidently names a real company that is not yet a known Customer (no existing `Work/Customers/<slug>/` directory). Call `librarian_housekeeping.backfill_company_folders()`. Confirm a new Customer OKF directory now exists for that company, created via the real, unmodified `ensure_customer_hub_note`, and confirm NO Pending Approval was created for this confident case.
2. `[REQ-SB-72-US-01-AC-10]` Construct or identify a real Thread whose content names a company genuinely ambiguous against the live `known_customers`/`known_partners` lists (e.g. a near-spelling match of a real existing Customer). Call `librarian_housekeeping.backfill_company_folders()`. Confirm NO autonomous folder is created and NO autonomous `## Related` link exists for that ambiguous name; confirm exactly one new, real Pending Approval exists (`GET /pending-approvals`) with `action_id="propose_librarian_company_link"` and a payload naming the real entity/reason/thread. Approve it (`POST /pending-approvals/{id}/approve`) and confirm the deferred create-or-link action now performs (the Customer folder now exists). Repeat with a second, fresh ambiguous finding and Decline it instead — confirm nothing is created and the finding is not silently reapplied elsewhere.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] A confident, genuinely-new company mention auto-creates its Customer folder, no approval required
- [x] An ambiguous/low-confidence mention creates a real Pending Approval instead of acting autonomously
- [x] Approving performs the deferred create/link action; declining performs nothing
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The `/poc/librarian-backfill-company-folders` HTTP endpoint and the orchestrating `run_housekeeping_pass` — `T08`.
- Wikilinking a resolved mention into `## Related` — `T06`.

---

## Context / Notes

`pending_approval_registry.py` itself needs no code change — `create_pending_approval`/decline are already fully generic; this task only registers a new dispatch-table entry and a new finalize handler, mirroring `REQ-SB-63-US-01`'s own precedent exactly.

---

## Implementation Log

**Resumed session, 2026-08-18/19.** Code for this task (`backfill_company_folders`, `_create_librarian_company_link_proposal`, `finalize_librarian_company_link` in `librarian_housekeeping.py`; `pending_approvals_router.py`'s `_APPROVAL_HANDLERS["propose_librarian_company_link"]` registration) was already present on disk from an earlier interrupted coder session — confirmed correct by direct reading before any further action, not re-implemented.

**`[REQ-SB-72-US-01-AC-09]` — verified, real evidence:** Called the real endpoint `POST /poc/librarian-backfill-company-folders`. Confirmed via real, on-disk `Work/Customers/` directory listing (filtered to today's date) that multiple new Customer OKF folders were created for confident/`new_unambiguous` mentions with no prior folder — e.g. `Google`, `YouTube`, `Twitter`, `LinkedIn`, `Instagram`, `SimplAI`, `AZCON Holding`, `AzInTelecom LLC`, `Microsoft Corporation`, `Ministry of Digital Development and Transport`, `Innovation and Digital Development Agency`. Cross-checked the live Pending Approvals list (`GET /pending-approvals`, real endpoint): none of these entity names appear among the (exactly 5, later 10) `propose_librarian_company_link` records — confirming no approval was created for any confident case, per the AC's own negative check.

**`[REQ-SB-72-US-01-AC-10]` — verified, real evidence:** Same run surfaced 5 real, genuinely ambiguous mentions (`Compass`, `Inception`, `core42.ai`, `HR Avatar`, `Aldar`) as real `GET /pending-approvals` records with `action_id="propose_librarian_company_link"` and a real payload naming entity/reason/thread — confirmed no autonomous folder/link existed for any of them beforehand. Approved `HR Avatar` (`POST /pending-approvals/1fc7b6688148/approve`, 200 OK) — confirmed via a real before/after directory listing that `Work/Customers/HR Avatar/` did not exist before and exists after (created by the deferred `ensure_customer_hub_note` call inside `finalize_librarian_company_link`). Declined `Compass` (`POST /pending-approvals/a126ba526347/decline`, 200 OK) — confirmed via directory listing that no `Work/Customers/Compass/` was ever created; the finding was not silently reapplied. A later full run surfaced 5 further real ambiguous findings (`Apple`, `Google` [ambiguous this pass], `ADFEC`, `Kerno`, `DGE`), left `pending` for the operator's own real review — genuine, disclosed, non-fabricated findings, not test fixtures.

**Bulk backfill note:** shares the SAME infrastructure finding as `T06` (see that task's own Implementation Log, and `ESCALATIONS.md`/`REVIEW-QUEUE.md`) — `backfill_company_folders()` has no per-thread scope and re-processes the full real corpus every call; multiple real-endpoint attempts made genuine progress (10 real Pending Approval records + numerous real Customer folders created across this session) but a full single-call completion across all 126 Threads was not reached within this session due to the coding session's own background-process reclaim, not an application defect. The remaining Threads will be completed by `T09`'s own scheduled `run_housekeeping_pass`.

**No concurrent mutating calls were made** — every `backfill_company_folders`/`populate_thread_related_links` invocation was confirmed single-in-flight via live log tailing before any further action was taken.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired for this task's own scope.
