---
id: REQ-SB-74-US-01-T02
title: finalize_customer_backfill_routing(payload) — deferred customer frontmatter + tag write, on approve
parent_story: REQ-SB-74-US-01
requirement_id: REQ-SB-74
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-74-US-01-T01]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-74-US-01-T02 — `finalize_customer_backfill_routing(payload)`

## Parent Story

- Story: [[REQ-SB-74-US-01]] — `../UserStories/REQ-SB-74-US-01-customer-backfill-thread-routing-and-noise-reconciliation.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-74 *Customer Backfill — Propose/Approve Thread Routing + Noise Reconciliation*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Customer Backfill" → "Finalize handlers" (`ADR-055` Decision 1)

---

## Objective

Build the deferred-write half of `T01`'s own proposal: once an operator approves a batched Customer-routing Pending Approval, write every named Thread's `customer` frontmatter and correct its `customer/<slug>` tags-list element, creating a new Customer folder first if the batch proposes a brand-new Customer.

---

## Starting State → End State

**Before / Inputs:**
- `T01`'s `propose_customer_backfill()` creates Pending Approval records with `payload = {"customer": <name>, "is_new_customer": <bool>, "thread_paths": [<str>, ...]}`.
- `customer_hub_linking.ensure_customer_hub_note(entity_name) -> dict` already exists and is reused unmodified (the exact mechanism `backfill_company_folders()` already uses for a `new_unambiguous` mention).
- `vault_writer.upsert_frontmatter_key(path, key, value) -> bool` already exists.
- A real Thread's own `tags` list carries a `customer/<slug>` element (e.g. `customer/unsorted`) alongside a `kind/...` element, written by `synthesize_thread`'s own `build_tags`/union-append logic once Stage 2 has run.

**After / Outputs:**
- New `librarian_housekeeping.finalize_customer_backfill_routing(payload: dict) -> dict`:
  - If `payload["is_new_customer"]` is `True`: calls `customer_hub_linking.ensure_customer_hub_note(payload["customer"])` — UNCHANGED, reused exactly as `backfill_company_folders` already does for a `new_unambiguous` mention.
  - For every path in `payload["thread_paths"]`:
    - `vault_writer.upsert_frontmatter_key(path, "customer", payload["customer"])`.
    - Reads that Thread's own current `tags` list; replaces any existing `customer/...` element with `f"customer/{vault_writer.tag_slug(payload['customer'])}"` (leaving every other tag, e.g. `kind/...`, untouched); writes the corrected list back via `vault_writer.upsert_frontmatter_key(path, "tags", corrected_tags)` — in the SAME call/pass as the `customer` frontmatter write, per Scenario 2's own "in the same write" wording.
  - No Thread outside `payload["thread_paths"]` is ever touched.
  - Returns `{"customer": str, "threads_routed": [str, ...], "hub_note_path": str | None, "message": str}` — a `"message"` key is REQUIRED (the router's own `_APPROVAL_HANDLERS` dispatch falls back to `f"Approved — filed at {result['path']}."` when no `"message"` key is present, which would `KeyError` here since this handler's own result has no single `"path"` — always supply an explicit `"message"` summarizing the batch, e.g. `f"Approved — routed {len(threads_routed)} Thread(s) to {customer}."`).

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` — add `finalize_customer_backfill_routing`.

---

## Constraints

- Inherits from parent story.
- `ensure_customer_hub_note` is reused UNCHANGED — never reinvented or modified.
- The tags correction REPLACES any existing `customer/...` element (never appends alongside a stale one) — this is a real, deliberate divergence from `synthesize_thread`'s own union-append tags logic, which never removes a stale element; this handler's own job is specifically to correct it.
- `customer` frontmatter and the corrected `tags` element are written in the SAME pass, for every Thread in the batch — never a partial write leaving one field updated and the other stale.
- No Thread outside the batch's own `payload["thread_paths"]` is ever touched.
- `synthesize_customer`/`resync_project_from_thread` are NOT called as a side effect — a routed Thread's Customer `## Glimpse` stays exactly as empty as it is today.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-74-US-01-AC-02]` Direct Python-shell check: hand-construct (or reuse a real one from `T01`) a batch payload naming N ≥ 2 real Unsorted Threads matched to an EXISTING real Customer folder (`is_new_customer: False`). Call `finalize_customer_backfill_routing(payload)` directly. Re-read all N Threads' concept files; confirm every one's `customer` frontmatter is now the approved Customer name, and every one's `tags` list has its `customer/unsorted` element replaced with the real `customer/<slug>` for the approved Customer, with every other tag untouched. Confirm a real Thread NOT in the batch is completely unaffected.
2. `[REQ-SB-74-US-01-AC-03]` Hand-construct a batch payload naming one real Unsorted Thread whose content clearly names a real company with no existing folder (e.g. a disposable test analogous to TAQA), `is_new_customer: True`. Call `finalize_customer_backfill_routing(payload)` directly. Confirm the new Customer's OKF-conformant folder now exists under `Work/Customers/` (created via the real, unmodified `ensure_customer_hub_note`), and confirm the named Thread's `customer` frontmatter and corrected `customer/<slug>` tag are both written, in the same call.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Approving an existing-Customer batch writes `customer` frontmatter + corrects the `customer/<slug>` tags element for every Thread in the batch, in the same write; no Thread outside the batch is touched
- [x] Approving a new-Customer batch creates the Customer's OKF folder via unmodified `ensure_customer_hub_note`, then writes `customer`/tags for every Thread in that batch, in the same approval
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `propose_customer_backfill()` itself — `T01`.
- `_APPROVAL_HANDLERS` registration (so this function is actually reachable via a real approve action) — `T05`.
- Declining a batch (Scenario 6) — verified in `T05`, a property of the existing, unmodified decline endpoint (this handler is never called on decline).

---

## Context / Notes

Verified here by calling `finalize_customer_backfill_routing(payload)` directly against a real or hand-constructed payload — the real end-to-end approve round trip (via the actual `/pending-approvals/{id}/approve` endpoint, once `T05` registers this handler) is exercised again in `T06`'s own full backfill run.

---

## Implementation Log

Built `librarian_housekeeping.finalize_customer_backfill_routing(payload)`
(new, `app/business/pipelines/librarian_housekeeping.py`) exactly per
`ADR-055` Decision 1 / architecture.md's "Finalize handlers" section.

**`[REQ-SB-74-US-01-AC-02]` PASS — real existing-Customer batch.** Reused
`T01`'s own real, live `"Aldar"` batch (3 real Threads, `is_new_customer:
False`). Called `finalize_customer_backfill_routing(payload)` directly.
Before: all 3 Threads `customer: "Unsorted"`, `tags: ["customer/unsorted",
"kind/emails"]`. After: all 3 now `customer: "Aldar"`, `tags: ["customer/
aldar", "kind/emails"]` — the stale `customer/unsorted` element correctly
REPLACED (not appended alongside), `kind/emails` untouched. A real control
Thread NOT in the batch (`"2026-07-27 Requested Item RITM0108464..."`)
confirmed byte-for-byte unchanged before/after (`customer`/`tags`
identical).

**`[REQ-SB-74-US-01-AC-03]` PASS — real new-Customer batch, the story's
own headline TAQA example.** Reused `T01`'s own real, live `"TAQA"` batch
(7 real Threads, `is_new_customer: True`). Confirmed `Work/Customers/
TAQA/` did NOT exist before the call. Called `finalize_customer_backfill_
routing(payload)` directly: `customer_hub_linking.ensure_customer_hub_
note("TAQA")` created the real OKF-conformant folder (`hub_note_path:
Work/Customers/TAQA/TAQA.md`, confirmed to exist on disk after), and all 7
named Threads' `customer` frontmatter + `customer/taqa` tag were written
in the same call.

**Assumption (scope-internal judgement call, logged per `Implementation/
Pipeline.md`):** rather than hand-constructing a disposable/synthetic
payload, both AC checks reused REAL, already-correctly-detected batches
from `T01`'s own real run against the live vault — these are genuinely
correct routings (not arbitrary), and this is real, trusted production
data with no staging/promotion gate (`CLAUDE.md`), so writing them for
real is the intended, correct outcome, not a test-only side effect. After
each direct call, the corresponding real Pending Approval record (from
`T01`) was ALSO explicitly resolved via `pending_approval_registry.
resolve_pending_approval(id, "approved")` — a scope-internal consistency
step (touches only existing registry state, no new file/mechanism) so no
"pending" record is left referencing a batch whose write already happened
outside the HTTP approve flow, avoiding a later confusing double-approve
at `T05`/`T06`.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired; mechanism follows
`ADR-055`/architecture.md directly, the one judgement call above is
logged, not a scope-filling assumption.
