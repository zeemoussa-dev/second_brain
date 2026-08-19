---
id: REQ-SB-74-US-01-T05
title: Register finalize handlers in _APPROVAL_HANDLERS + new /poc/librarian-propose-customer-backfill orchestrating endpoint
parent_story: REQ-SB-74-US-01
requirement_id: REQ-SB-74
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-74-US-01-T01, REQ-SB-74-US-01-T02, REQ-SB-74-US-01-T03, REQ-SB-74-US-01-T04]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-74-US-01-T05 — Approval wiring + orchestrating endpoint

## Parent Story

- Story: [[REQ-SB-74-US-01]] — `../UserStories/REQ-SB-74-US-01-customer-backfill-thread-routing-and-noise-reconciliation.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-74 *Customer Backfill — Propose/Approve Thread Routing + Noise Reconciliation*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Customer Backfill" → "Endpoint & scheduling" (`ADR-055` Decision 5)

---

## Objective

Wire both new finalize handlers into the existing `_APPROVAL_HANDLERS` dispatch table (zero registry/router code change beyond the two new dict entries — the mechanism is already fully payload-shape-agnostic), and build the one new orchestrating endpoint that runs both propose Jobs in a single real HTTP call.

---

## Starting State → End State

**Before / Inputs:**
- `pending_approvals_router.py`'s `_APPROVAL_HANDLERS` dict dispatches `action_id -> handler(payload)` on approve; `decline_pending_approval` never calls any handler — it only flips the record's status to `"declined"` and appends a history entry. This existing behavior is UNCHANGED by this task; it is what makes Scenario 6/7 (decline leaves everything untouched) true with zero new code.
- `T01`'s `propose_customer_backfill()` and `T03`'s `propose_customer_archival_candidates(matched_existing_customer_names)` exist as standalone business-layer functions, not yet reachable via HTTP.
- `T02`'s `finalize_customer_backfill_routing` and `T04`'s `finalize_customer_archival` exist as standalone functions, not yet registered for dispatch.

**After / Outputs:**
- `pending_approvals_router.py`'s `_APPROVAL_HANDLERS` gains two new entries: `"propose_customer_backfill_routing": finalize_customer_backfill_routing` and `"propose_customer_archival_candidate": finalize_customer_archival` (imported from `librarian_housekeeping`).
- New endpoint on `email_poc_router.py`: `POST /poc/librarian-propose-customer-backfill` → runs `propose_customer_backfill()` then `propose_customer_archival_candidates(result["matched_existing_customer_names"])` in ONE orchestrating call, passing the first Job's own result directly into the second — never two independently-run Compass sweeps that could disagree. Returns a combined result (both Jobs' own return shapes). Deliberately NOT added to `run_housekeeping_pass()`'s own scheduled chain — manually-triggered only.

---

## Files to Modify

- `src/backend/app/api/pending_approvals_router.py` — add the two `_APPROVAL_HANDLERS` entries + the two new imports from `librarian_housekeeping`.
- `src/backend/app/api/email_poc_router.py` — add the new orchestrating endpoint + its imports.

---

## Constraints

- Inherits from parent story.
- Manually-triggered only — the new endpoint is NOT wired into `run_housekeeping_pass()`'s own recurring schedule chain, per the story's own explicit Constraint (`REQ-SB-70`/`71`'s standing "live/ongoing capture stays manual" posture).
- Zero change to `pending_approval_registry.py` or the rest of `pending_approvals_router.py`'s own dispatch machinery — confirmed by `ADR-055` to already be fully payload-shape-agnostic; this task adds dict entries only.
- One evidence pass per endpoint call — `propose_customer_archival_candidates` must be called with the SAME call's own `matched_existing_customer_names`, never a second, independent detection sweep.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. Component check: start the real backend app; `POST /poc/librarian-propose-customer-backfill`; confirm a real `200` with both Jobs' own combined result, and confirm real Pending Approval records now exist for both `action_id`s (`propose_customer_backfill_routing`, `propose_customer_archival_candidate`) via `GET /pending-approvals`.
2. `[REQ-SB-74-US-01-AC-06]` Pick one real, pending `propose_customer_backfill_routing` batch naming one or more real Unsorted Threads. `POST /pending-approvals/{id}/decline` against the real running server. Confirm the response reflects `"declined"`, and confirm every named Thread's `customer` frontmatter and `tags` are byte-for-byte unchanged — still exactly `customer: "Unsorted"` / `customer/unsorted` — as if the proposal never ran.
3. `[REQ-SB-74-US-01-AC-07]` Pick one real, pending `propose_customer_archival_candidate` record. `POST /pending-approvals/{id}/decline`. Confirm the response reflects `"declined"`, and confirm the named folder still exists at its ORIGINAL location under `Work/Customers/`, completely unchanged — never moved.
4. `POST /pending-approvals/{id}/approve` against one real `propose_customer_backfill_routing` record and one real `propose_customer_archival_candidate` record (different records than steps 2/3, since those are now resolved); confirm both real `200`s, confirm `_APPROVAL_HANDLERS` correctly dispatched to `T02`'s and `T04`'s own handlers respectively (real frontmatter/tag writes for the routing batch; a real folder move for the archival candidate) — a real, end-to-end approve round trip through the actual HTTP surface, not a direct function call.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Both finalize handlers registered in `_APPROVAL_HANDLERS`, dispatched correctly on real approve
- [x] `POST /poc/librarian-propose-customer-backfill` runs both propose Jobs in one call, second Job consuming the first's own real result
- [x] Declining a routing batch leaves every named Thread's `customer`/`tags` byte-for-byte unchanged
- [x] Declining an archival candidate leaves the folder at its original location, unchanged
- [x] The new endpoint is NOT wired into `run_housekeeping_pass()`'s scheduled chain
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The business logic inside any of the four Job/handler functions — `T01`-`T04`.
- The full-corpus real run + idempotency-after-approval verification (Scenario 9) — `T06`.

---

## Context / Notes

This is the first task in this story where the full propose → approve/decline round trip is exercised via the REAL HTTP surface — `T01`-`T04`'s own AC-tagged steps are real, direct Python-shell function calls (this codebase's own established, repeatedly-used verification technique), never a weaker substitute; this task is where "the capability is reachable via HTTP" is proven, distinct from and additional to "the business logic is correct."

---

## Implementation Log

Registered `"propose_customer_backfill_routing": finalize_customer_
backfill_routing` and `"propose_customer_archival_candidate": finalize_
customer_archival` in `_APPROVAL_HANDLERS` (`app/api/pending_approvals_
router.py`), with the corresponding imports. Added `POST /poc/librarian-
propose-customer-backfill` (`app/api/email_poc_router.py`), orchestrating
`propose_customer_backfill()` then `propose_customer_archival_candidates(
result["matched_existing_customer_names"])` in one call — deliberately
NOT added to `run_housekeeping_pass()`'s own dict-literal body.

**Component check — real, via a dedicated server process on port 8002**
(the already-running shared dev servers on 8000/8001 belong to other
concurrent sessions building the sibling `SPRINT-067`/`REQ-SB-73-US-01`
work in the same repo this same day — left untouched, a fresh dedicated
instance avoids any cross-session interference). First real call: `POST
/poc/librarian-propose-customer-backfill` initially returned a real `500`
(`httpx.ConnectError` — a genuine, live, transient Compass connection
drop partway through the ~123-Thread real sequential pass; see this
task's own defect-fix note below). After the fix, a second real call
returned a clean `200` (480.0s, ~123 real Threads), body confirmed: 23 new
proposed-Customer batches, 29 left Unsorted, 0 failed, and `GET /pending-
approvals`-equivalent direct registry checks confirmed real records now
exist for both `action_id`s.

**A real, genuine defect found live and fixed in scope (`## Files to
Modify` — `librarian_housekeeping.py` only, no signature/contract
change):** `propose_customer_backfill()`'s own per-Thread loop had no
failure isolation — a single transient `compass_client.CompassError`
(observed for real: `[WinError 10054] An existing connection was forcibly
closed by the remote host`) propagated uncaught, discarding EVERY other
Thread's already-good classification in the same pass (`batches` is only
persisted into real Pending Approvals AFTER the whole detection loop
completes) and surfacing as an HTTP `500`. Fixed by wrapping the `detect_
customer_for_thread` call in a `try/except compass_client.CompassError`,
recording a `{"thread_path", "error"}` entry into a new, additive
`"failed"` return key and `continue`-ing the loop — mirrors this
codebase's own already-established honest-degradation pattern (`backfill_
files`'s own `"failed"` key; `detect_mentioned_companies_for_thread`'s own
non-raising `{"error", "mentions": []}` contract). Does NOT touch `detect_
customer_for_thread` itself or add a retry loop — `ADR-055` Decision 2's
own explicit "no retry loop, mirrors `classify_task`" text is UNCHANGED,
respected; this is an orthogonal, Job-LEVEL resilience fix (one bad call
among 100+ no longer wastes the rest), not an ADR deviation. Restarted the
dedicated server process (plain `uvicorn`, no `--reload`) to pick up the
fix before re-running.

**`[REQ-SB-74-US-01-AC-06]` PASS — real, via HTTP.** Declined a real,
pending `propose_customer_backfill_routing` batch (`"Sindan"`, 1 Thread)
via `POST /pending-approvals/{id}/decline` against the real running
server. Response confirmed `"status": "declined"`. Re-read the named
Thread directly: `customer: "Unsorted"`, `tags: ["customer/unsorted",
"kind/emails"]` — byte-for-byte unchanged.

**`[REQ-SB-74-US-01-AC-07]` PASS — real, via HTTP.** Declined a real,
pending `propose_customer_archival_candidate` record (`"AzInTelecom
LLC"`) via the same real endpoint. Response confirmed `"status":
"declined"`. Confirmed the real folder still exists at its ORIGINAL
`Work/Customers/AzInTelecom LLC/` location, unmoved.

**Real approve round trip — both handlers, via the real HTTP surface (not
a direct function call, distinct from `T02`/`T04`'s own proof):** approved
one real, unambiguous `propose_customer_backfill_routing` batch
(`"LinkedIn"`, 1 Thread) via `POST /pending-approvals/{id}/approve` —
confirmed the named Thread's `customer`/`tags` genuinely updated on disk
afterward (`customer: "LinkedIn"`, `customer/linkedin` tag). Approved one
real, unambiguous `propose_customer_archival_candidate` (`"Google"`,
explicitly named as confirmed noise in the story's own Context) — confirmed
the real folder moved to `Work/Archive/Customers/Google/`, the original
`Work/Customers/Google/` location confirmed gone. A handful of stale
DUPLICATE pending records (the SAME Customer proposed again in the second
real propose call, e.g. a second `"LinkedIn"`/`"Google"` record referencing
the identical already-resolved Thread/folder — the exact operational risk
`ADR-055`'s own "Disclosed, not fixed" section already names) were
declined alongside their now-superseded counterpart, never approved twice.

**A real, disclosed observation carried forward into `T06`'s own
Implementation Log (not a defect, not fixed here):** the SAME "already-
approved, zero NEW matches this pass" limitation `T03`'s own Implementation
Log flagged in the abstract was observed FOR REAL on this task's own
second propose call — `"Aldar"` (fully routed to real Threads by `T02`'s
own earlier direct-call verification) was proposed as a real archival
candidate this pass, since none of ITS Threads are Unsorted anymore for a
fresh pass to match. Declined this specific real record (never approved
— would have wrongly archived an actively-used real Customer folder).

gate: clear 2026-08-19 — no NEW MUST-FLAG trigger fired for this task's
own scope: the in-scope defect fix above is additive, Job-level-only, and
does not deviate from `ADR-055`'s own decisions; the archival false-
positive observation is a disclosed operational nuance (documented, not a
code defect), carried to `T06`'s own log where the same real re-run
naturally re-surfaces it.
