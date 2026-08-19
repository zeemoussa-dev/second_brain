---
id: REQ-SB-76-US-01-T04
title: propose_company_review() Job — batched-per-company extraction pass + its own endpoint
parent_story: REQ-SB-76-US-01
requirement_id: REQ-SB-76
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-76-US-01-T01]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-76-US-01-T04 — propose_company_review() Job + endpoint

## Parent Story

- Story: [[REQ-SB-76-US-01]] — `../UserStories/REQ-SB-76-US-01-company-review-extract-classify-and-batch-apply.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-76 *Company Review — Extract & Recommend, Customer/Partner/Affiliate Classification, Batch-Apply*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Company Review" (§ "`propose_company_review()`/`finalize_company_review()`"), `Implementation/Architecture/ADR.md` → `ADR-057` Decisions 2, 10

---

## Objective

Add `librarian_housekeeping.propose_company_review()` — iterates every real Thread, calls `T01`'s extraction function once per Thread, skips a mention already covered by an existing `customer/<slug>`/`partner/<slug>` tag on that Thread, and groups every remaining mention into ONE batched, deduplicated Pending Approval per distinct company — plus its own `POST /poc/librarian-propose-company-review` endpoint. Added ALONGSIDE (never replacing) `propose_customer_backfill`.

---

## Starting State → End State

**Before / Inputs:**
- `T01`'s `extract_thread_companies_for_review` exists but is called nowhere.
- `propose_customer_backfill`/`finalize_customer_backfill_routing` remain live, unedited (frozen, `Done`).
- No `action_id="propose_company_review"` Pending Approval kind exists yet.

**After / Outputs:**
- `propose_company_review()` iterates every real Thread via `vault_writer.list_thread_notes()` — **NOT** filtered to `"Unsorted"` only (Scenario 9 needs an already-routed Thread considered too) — calls `extract_thread_companies_for_review` once per Thread against that Thread's full concatenated message content and the live `known_companies` union (`list_customer_folders()` + `list_known_partners()`).
- For each returned company mention: skipped if that Thread's own current `tags` already carries the exact `customer/<slug>`/`partner/<slug>` for that company (per-mention idempotency floor). Every remaining mention groups into ONE batched Pending Approval per distinct company name: `action_id="propose_company_review"`, `trigger="direct"`, `payload={"company": <name>, "thread_paths": [...]}`, `dedupe_key=f"propose_company_review:{company}"`.
- A single transient `CompassError` for one Thread is recorded in a `"failed"` list and skipped — never crashes the whole pass.
- Returns `{"proposed_batches": [...], "failed": [...]}`.
- New `POST /poc/librarian-propose-company-review` endpoint (mirrors the existing `/poc/librarian-*` convention) runs `propose_company_review()`. Deliberately NOT added to `run_housekeeping_pass()`'s scheduled chain.
- No Thread's `customer`/`partner` frontmatter or `tags` are written by this Job — proposal only.

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` — new `propose_company_review()` (place alongside the existing `propose_customer_backfill`, its nearest structural sibling; local `pending_approval_registry` import, mirroring that function's own precedent).
- `src/backend/app/api/email_poc_router.py` — new `POST /poc/librarian-propose-company-review` endpoint (mirrors `librarian_propose_customer_backfill_endpoint`'s own shape).

---

## Constraints

- Inherits from parent story.
- Added ALONGSIDE, never replacing, `propose_customer_backfill`/`finalize_customer_backfill_routing` — both stay live, callable, byte-for-byte unedited.
- `dedupe_key` applied from day one (`ADR-056`'s own convention) — never left for a future bugfix.
- Never a silent write — this Job performs zero frontmatter/tag writes anywhere.
- Manually-triggered only — never wired into `run_housekeeping_pass()`.
- A single Thread's transient extraction failure must never abort the whole pass (mirrors `propose_customer_backfill`'s own `T06`-found honest-failure handling).

---

## Tests

**Real vault, but BOUNDED for this task's own direct verification — do not run this Job against the FULL, unbounded real Thread corpus here** (that full-scale, multi-batch real run, and its own careful review, is `T09`'s explicit mandate; running it twice unbounded here would needlessly pile up duplicate real Pending Approval records ahead of the queue actually being reviewed). Bound this task's own direct-function-call verification via an in-process monkeypatch of `vault_writer.list_thread_notes()` to return a small, hand-picked, real subset of Threads (2-5 real Threads, at least two of which genuinely mention the same real company), mirroring this codebase's own established "bound a live-data verification to a real, filtered subset via in-process monkeypatch of the real fetch function" pattern (`Implementation/Learnings.md`, `SPRINT-028`/`SPRINT-050`).

**Manual verification steps:**
1. `[REQ-SB-76-US-01-AC-01]` With `list_thread_notes()` monkeypatched to the bounded real subset above (chosen so at least 2 real Threads genuinely mention the SAME real company), call `propose_company_review()` directly. Confirm exactly ONE Pending Approval record is created for that company, with `payload["thread_paths"]` naming BOTH real Threads (not just one), `action_id="propose_company_review"` (never `propose_customer_backfill_routing`), and `dedupe_key=f"propose_company_review:{company}"`. Re-read every named Thread's own real `customer`/`tags` frontmatter directly afterward and confirm NONE were written by this call — proposal only.
2. Confirm a Thread whose own current `tags` already carries the exact `customer/<slug>` for a mentioned company is correctly SKIPPED for that company (per-mention idempotency floor) — pick a real already-routed Thread from the bounded subset for this check.
3. Induce a transient `CompassError` for exactly one Thread in the bounded subset (in-process monkeypatch of `compass_client.extract_thread_companies_for_review` for that one call only); confirm it lands in `"failed"` and every OTHER Thread in the same pass still produces its own correct real batch — the whole pass does not abort.
4. `POST /poc/librarian-propose-company-review` against the real running server with the SAME bounded monkeypatch active; confirm a real `200` and a response shape matching the direct-call result above.
5. Confirm `run_housekeeping_pass()`'s own source is unedited — this Job is not part of its scheduled chain.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `[REQ-SB-76-US-01-AC-01]` verified live (bounded) — one batched Pending Approval per company, correct payload, zero writes at propose time
- [x] Per-mention idempotency floor confirmed against a real already-tagged Thread
- [x] A single transient extraction failure does not abort the whole pass
- [x] New endpoint returns a real `200` with the correct shape
- [x] `propose_customer_backfill`/`run_housekeeping_pass()` left unedited
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision beyond `ADR-057`)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The full, unbounded real-corpus run — `T09`'s own explicit scope.
- `finalize_company_review` and the Approve-endpoint wiring — `T06`/`T07`.
- Any change to `propose_customer_backfill`/`propose_customer_archival_candidates`.

---

## Context / Notes

Mirrors `propose_customer_backfill`'s own shape closely (grouping, `dedupe_key`, honest-failure `"failed"` list) — the real difference is the iteration scope (every Thread, not just `"Unsorted"` ones) and the per-mention (not per-Thread) skip check, both required by Scenario 9.

---

## Implementation Log

**2026-08-19, coder.** Added `librarian_housekeeping.propose_company_review()` alongside `propose_customer_backfill` (both now live, unedited). Iterates `vault_writer.list_thread_notes()` (every Thread, not filtered to Unsorted), calls `T01`'s `extract_thread_companies_for_review` once per Thread against the live UNION of `list_customer_folders()` + `list_known_partners()`; skips a mention whose exact `customer/<slug>`/`partner/<slug>` tag is already on that Thread; groups the rest into one batched Pending Approval per company (`action_id="propose_company_review"`, `dedupe_key=f"propose_company_review:{company}"`). A `compass_client.CompassError` for one Thread lands in `"failed"`, the pass continues. New `POST /poc/librarian-propose-company-review` added to `email_poc_router.py`, mirroring the existing `/poc/librarian-*` convention; NOT added to `run_housekeeping_pass()`.

**Verification — bounded, live, real vault:**
1. `[REQ-SB-76-US-01-AC-01]` `vault_writer.list_thread_notes()` monkeypatched to 4 real Threads (2 real, currently-Unsorted, genuinely ADNOC-related Threads; 1 real Thread already routed to `ADNOC`; 1 real boilerplate-only Thread). `propose_company_review()` → exactly ONE `ADNOC` Pending Approval batch naming BOTH real Unsorted Threads (not the already-routed one), `action_id="propose_company_review"`, `dedupe_key="propose_company_review:ADNOC"`. Re-read every named Thread's own frontmatter afterward — byte-for-byte unwritten (proposal only). (This same real pass also genuinely extracted 10 further real companies from the real ADNOC Account Plan document's own substantive content — Core42, Microsoft, AMD, Dell, Schneider, Honeywell, EY, SLB, Armada, "G42 Int'l" — each its own real batched Pending Approval, disclosed below.)
2. The already-routed real Thread was correctly excluded from the `ADNOC` batch — per-mention idempotency floor confirmed against real data.
3. Induced a `CompassError` for the boilerplate Thread (in-process monkeypatch of `extract_thread_companies_for_review` scoped to that one Thread's own content); it landed in `"failed"`, every OTHER Thread in the same bounded pass still produced its own correct batch.
4. `POST /poc/librarian-propose-company-review` (via `fastapi.testclient.TestClient`, same bounded monkeypatch) → real `200`, `dedupe_key` correctly returned the SAME `ADNOC` record (`7ad370f0ac69`) rather than a duplicate — confirms the endpoint drives the exact same Job.
5. `run_housekeeping_pass()`'s own source confirmed unedited by direct reading — this Job's own call is not in its chain.

**Real Pending Approvals produced by this task's own bounded verification (disclosed per the sprint's own constraint):** 11 records — `ADNOC` (2 Threads), `Core42`/`Microsoft`/`AMD`/`Dell`/`Schneider`/`Honeywell`/`EY`/`SLB`/`Armada`/`"G42 In'tl"` (1 Thread each, all the same real ADNOC Account Plan Thread). These were resolved during `T06`/`T07`'s own live verification (see those tasks' own Implementation Logs) — `ADNOC`→Customer and `Core42`→Partner kept as real, correct classifications; the 9 vendor-name mentions declined (genuinely not real Customer/Partner relationships, only vendors cited inside an internal account-plan document) — the queue was left clean of this task's own artefacts by the end of `T07`.

`MEMORY.md`: no new decision beyond `ADR-057`. `CHANGELOG.md` entry appended.
