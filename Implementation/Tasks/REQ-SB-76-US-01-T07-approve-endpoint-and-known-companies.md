---
id: REQ-SB-76-US-01-T07
title: Approve-endpoint additive decision body + handler registration + GET known-companies
parent_story: REQ-SB-76-US-01
requirement_id: REQ-SB-76
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-76-US-01-T04, REQ-SB-76-US-01-T06]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-76-US-01-T07 — Approve-endpoint decision body + known-companies endpoint

## Parent Story

- Story: [[REQ-SB-76-US-01]] — `../UserStories/REQ-SB-76-US-01-company-review-extract-classify-and-batch-apply.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-76 *Company Review — Extract & Recommend, Customer/Partner/Affiliate Classification, Batch-Apply*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Company Review" (§ "Approve endpoint", § "`GET /pending-approvals/known-companies`"), `Implementation/Architecture/ADR.md` → `ADR-057` Decisions 3, 9

---

## Objective

Give `POST /pending-approvals/{id}/approve` a new, additive, optional `CompanyReviewDecisionBody` request body, merged into the stored payload before dispatch; register `finalize_company_review` in `_APPROVAL_HANDLERS`; add a new `GET /pending-approvals/known-companies` endpoint the frontend (`T08`) will call.

---

## Starting State → End State

**Before / Inputs:**
- `def approve_pending_approval(approval_id: str) -> dict` takes no body at all.
- `_APPROVAL_HANDLERS` has 9 entries, none for `"propose_company_review"`.
- No endpoint exposes `list_customer_folders()`/`list_known_partners()` to the browser.

**After / Outputs:**
- New Pydantic model: `class CompanyReviewDecisionBody(BaseModel): outcome: str; parent_name: str | None = None; parent_kind: str | None = None`.
- `def approve_pending_approval(approval_id: str, decision: CompanyReviewDecisionBody | None = None) -> dict`. Inside the EXISTING `elif record["action_id"] in _APPROVAL_HANDLERS:` branch only: `effective_payload = {**record["payload"], **(decision.model_dump() if decision else {})}`; `result = _APPROVAL_HANDLERS[record["action_id"]](effective_payload)`. Every one of the other 9 registered handlers keeps its exact one-argument signature — `effective_payload == payload` whenever no body is sent, exactly as today.
- `_APPROVAL_HANDLERS["propose_company_review"] = finalize_company_review` (new entry, `T06`'s function).
- `Decline` (`POST /pending-approvals/{id}/decline`) is NOT touched at all.
- New `GET /pending-approvals/known-companies -> {"customers": [<name>, ...], "partners": [<name>, ...]}`, composed from `vault_writer.list_customer_folders()` + `vault_writer.list_known_partners()`.

---

## Files to Modify

- `src/backend/app/api/pending_approvals_router.py` — `CompanyReviewDecisionBody`, `approve_pending_approval`, `_APPROVAL_HANDLERS` registration, new `known-companies` route.

---

## Constraints

- Inherits from parent story.
- Every one of the other 9 registered handlers' one-argument `(payload: dict) -> dict` contract is completely unaffected — no signature change anywhere else.
- `Decline` reuses the existing endpoint verbatim — zero code change to `decline_pending_approval`.
- The new decision body is OPTIONAL (`| None = None`) — every existing caller sending no body keeps working unchanged.
- `known-companies` composes only already-existing, vault-derived enumerations — zero new `vault_writer.py` code.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`) — this router calls `librarian_housekeeping`/`vault_writer` functions, never the reverse.

---

## Tests

**Real vault + real running server. Use a real `propose_company_review` batch created via `T04`'s bounded verification (or create one fresh, bounded, for this task) — do not mass-approve the real, broader Pending Approvals queue as part of this task's own testing.**

**Manual verification steps:**
1. `[REQ-SB-76-US-01-AC-01]` (mechanism half) Confirm, by direct reading of the merged router code, that `_APPROVAL_HANDLERS["propose_company_review"]` is registered and that NO separate `action_id` per outcome was introduced — exactly one Pending Approval record kind offers all five outcomes via the new decision body, never a direct `"route to X"` `action_id`.
2. Create (or reuse) one real, pending `propose_company_review` batch. `POST /pending-approvals/{id}/approve` with a real JSON body `{"outcome": "customer"}` against the real running server; confirm a real `200` and that `finalize_company_review` genuinely ran (cross-check the real Thread/entity writes on disk, mirroring `T06`'s own verification).
3. `POST /pending-approvals/{id}/approve` for an EXISTING, unrelated pending record of a DIFFERENT, already-`Done` `action_id` (e.g. a real or freshly-created `propose_customer_backfill_routing` record) with NO body at all; confirm it behaves byte-for-byte as it did before this task (unaffected — `effective_payload == payload`).
4. `[REQ-SB-76-US-01-AC-07]` `POST /pending-approvals/{id}/decline` against a real, pending `propose_company_review` batch; confirm a real `200`, the record resolves `"declined"`, and every Thread named in its own `payload["thread_paths"]` is confirmed byte-for-byte unchanged on disk (frontmatter, tags, body) — no Customer/Partner entry created for that company.
5. `GET /pending-approvals/known-companies` against the real running server; confirm a real `200` with `{"customers": [...], "partners": [...]}` matching the live vault's own current `list_customer_folders()`/`list_known_partners()` output exactly.
6. Approve/create one more real Customer or Partner via `T06`'s own mechanism, then call `known-companies` again; confirm the new name appears — never baked into a stale snapshot.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `[REQ-SB-76-US-01-AC-01]` mechanism confirmed — one `action_id`, five outcomes via a decision body, never per-outcome `action_id`s
- [x] Real approve round trip verified for the new decision body, dispatching to `finalize_company_review`
- [x] Every other existing `action_id`'s approve behavior confirmed unaffected (no body sent, `effective_payload == payload`)
- [x] `[REQ-SB-76-US-01-AC-07]` Decline verified live — untouched endpoint, real no-op confirmed on disk
- [x] `GET /pending-approvals/known-companies` verified live, fresh (not stale) on every call
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision beyond `ADR-057`)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend change — `T08`.
- `finalize_company_review`'s own internal branch logic — already built, `T06`.

---

## Context / Notes

The router-level merge (`effective_payload = {**record["payload"], **(decision.model_dump() if decision else {})}`) is the ENTIRE new dispatch mechanism — no other of the 8 pre-existing handlers needs touching, per `ADR-057`'s own rejected "change every handler's signature" alternative.

---

## Implementation Log

**2026-08-19, coder.** Added `CompanyReviewDecisionBody` (`outcome: str; parent_name: str | None = None; parent_kind: str | None = None`) and gave `approve_pending_approval` an additive `decision: CompanyReviewDecisionBody | None = None` parameter. Inside the existing `elif record["action_id"] in _APPROVAL_HANDLERS:` branch only, merges `{**record["payload"], **(decision.model_dump() if decision else {})}` before dispatch. Registered `_APPROVAL_HANDLERS["propose_company_review"] = finalize_company_review`. `decline_pending_approval` untouched. New `GET /pending-approvals/known-companies` composes `list_customer_folders()` + `list_known_partners()`.

**Route-ordering fix, disclosed:** the new `known-companies` GET route was initially placed AFTER the existing `GET /{approval_id}` route — FastAPI resolves path-parameter routes in DEFINITION order, so `/known-companies` would have been shadowed (bound to `approval_id="known-companies"`, a 404). Caught before any live test ran (confirmed via a direct `curl` returning `{"detail":"Unknown pending approval"}` instead of the real payload) — moved `known-companies` to register BEFORE `/{approval_id}`, confirmed fixed live afterward. Restarted both real dev backends (ports 8000/8001, launched as genuinely detached `Start-Process`-style processes, not `Bash`-tool-owned — this project's own established restart discipline) after this and every subsequent backend code change in this sprint, since `--reload`'s `WatchFiles` was observed to silently miss a change in this session (a real re-confirmation of `Implementation/Learnings.md`'s own `SPRINT-034`/`SPRINT-035` finding) — moved to non-`--reload` instances, manually restarted after each edit, for the rest of this sprint's own verification.

**Verification — live, real running backend + real vault:**
1. `[REQ-SB-76-US-01-AC-01]` (mechanism) Confirmed by direct reading — `_APPROVAL_HANDLERS["propose_company_review"]` registered once; no per-outcome `action_id` exists anywhere.
2. Real approve round trip: `POST /pending-approvals/7ad370f0ac69/approve` with body `{"outcome":"customer"}` against the real ADNOC batch → real `200`, `finalize_company_review` genuinely ran (cross-checked both named real Threads' `customer`/tags on disk — see `T06`). Same for `POST .../a8b160ff17e6/approve` `{"outcome":"partner"}` (real Core42 batch).
3. Created a fresh, disposable `propose_customer_backfill_routing` record (`customer: "ADNOC", is_new_customer: false, thread_paths: []`) and approved it with NO body → real `200`, dispatched to the existing `finalize_customer_backfill_routing` unaffected (`effective_payload == payload` since `decision` was `None`) — confirms the other 8 registered handlers' one-argument contract is untouched.
4. `[REQ-SB-76-US-01-AC-07]` Declined 9 real `propose_company_review` batches (Microsoft/AMD/Dell/Schneider/Honeywell/EY/SLB/Armada/"G42 In'tl" — genuine vendor-name mentions inside the ADNOC account-plan document, not real Customer/Partner relationships, so Decline was also the correct real business disposition here) via `POST .../{id}/decline` → real `200` each, every one resolved `"declined"`; re-read the shared real Thread's own frontmatter afterward — confirmed byte-for-byte unchanged by any of the 9 declines (only the two earlier real approvals' own tags/customer field were present, nothing from the declined batches).
5. `GET /pending-approvals/known-companies` → real `200`, `{"customers": ["ADNOC","TAQA","Unsorted"], "partners": ["Core42","Presight"]}`, matching `list_customer_folders()`/`list_known_partners()` exactly.
6. Created one further disposable Customer (`ZZ-Decomposer-T07-KnownCompanies-Test`) via `ensure_customer_hub_note`, re-called `known-companies` → the new name appeared immediately (never a stale snapshot); deleted the disposable entity afterward, re-confirmed it disappeared from the list.

`MEMORY.md`: no new decision beyond `ADR-057` (the route-ordering fix and restart discipline are execution notes, not new architectural decisions). `CHANGELOG.md` entry appended.
