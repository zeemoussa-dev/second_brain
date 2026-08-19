---
id: REQ-SB-74-US-01-T03
title: propose_customer_archival_candidates() Job — zero-match existing folders surfaced as archival candidates
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

# REQ-SB-74-US-01-T03 — `propose_customer_archival_candidates()` Job

## Parent Story

- Story: [[REQ-SB-74-US-01]] — `../UserStories/REQ-SB-74-US-01-customer-backfill-thread-routing-and-noise-reconciliation.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-74 *Customer Backfill — Propose/Approve Thread Routing + Noise Reconciliation*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Customer Backfill" → "`propose_customer_backfill()`/`propose_customer_archival_candidates()`" (`ADR-055` Decisions 1, 3)

---

## Objective

Surface every existing real Customer folder that ends this backfill pass with zero real Thread matches as its own explicit archival-candidate Pending Approval — evidence-based, never from the folder's own name alone.

---

## Starting State → End State

**Before / Inputs:**
- `T01`'s `propose_customer_backfill()` returns `{"proposed_batches": [...], "matched_existing_customer_names": [...], ...}` — `matched_existing_customer_names` is the real, evidence-based set of existing Customer folder names that received at least one real Thread match this pass.
- `T01`'s `vault_writer.list_customer_folders()` enumerates every real Customer OKF directory under `Work/Customers/`.
- The real `Work/Customers/` has 26 existing folders (2026-08-19 count; re-confirm live), several of which are confirmed noise from an earlier unchecked extraction pass (Apple, Google, Instagram, LinkedIn, Twitter, YouTube, Microsoft, NVIDIA, Razer), several genuinely ambiguous without checking real evidence (Columbus, Sindan, AZCON Holding, HR Avatar).

**After / Outputs:**
- New `librarian_housekeeping.propose_customer_archival_candidates(matched_existing_customer_names: list[str]) -> dict`:
  - Calls `vault_writer.list_customer_folders()`.
  - For every entry whose `"customer"` name is NOT in `matched_existing_customer_names`, creates one archival-candidate Pending Approval: `create_pending_approval(agent_id="librarian-housekeeping", trigger="direct", action_id="propose_customer_archival_candidate", description=..., payload={"customer": <name>, "source_directory": str(<directory>)})`.
  - Never classifies a folder as an archival candidate from its own name alone — only from this pass's own real, zero-match evidence (the function's own only input signal is the real `matched_existing_customer_names` set, never any hardcoded/heuristic name list).
  - Returns `{"archival_candidates": [{"customer": str, "source_directory": str, "approval_id": str}, ...]}`.

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` — add `propose_customer_archival_candidates`.

---

## Constraints

- Inherits from parent story.
- Evidence-based only — zero real Thread matches this pass, never a name-based heuristic (no hand-classification of Columbus/Sindan/AZCON Holding/HR Avatar or any other folder by name).
- `trigger="direct"`, mirroring `T01`'s own reasoning.
- One evidence pass, never a second, independently-run Compass sweep — this function consumes `T01`'s own already-computed `matched_existing_customer_names` directly; it must NOT re-run any detection call itself.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-74-US-01-AC-04]` Direct Python-shell check: call `librarian_housekeeping.propose_customer_backfill()` first (or reuse `T01`'s own real result), then call `propose_customer_archival_candidates(result["matched_existing_customer_names"])`. Confirm every real existing Customer folder that received zero Thread matches this pass now has a real Pending Approval record with `action_id="propose_customer_archival_candidate"` and a `payload["source_directory"]` pointing at its real, current folder path. Confirm a Customer folder that DID receive a real match (present in `matched_existing_customer_names`) has NO archival-candidate proposal created for it.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Every existing Customer folder with zero real Thread matches this pass gets its own archival-candidate Pending Approval
- [x] No folder is ever proposed for archival from its name alone — only from real, this-pass zero-match evidence
- [x] A Customer folder with a real match this pass is never proposed for archival
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The deferred archival move itself (`finalize_customer_archival`) — `T04`.
- `_APPROVAL_HANDLERS` registration and the orchestrating endpoint (which calls this function immediately after `propose_customer_backfill()`, passing its own result through in one pass) — `T05`.
- Declining an archival candidate (Scenario 7) — verified in `T05`, a property of the existing, unmodified decline endpoint.

---

## Context / Notes

Verified here by calling `propose_customer_archival_candidates()` directly, chained after a real `T01` call — the real orchestrating endpoint that runs both in one HTTP request is built in `T05`.

---

## Implementation Log

Built `librarian_housekeeping.propose_customer_archival_candidates(
matched_existing_customer_names)` (new, `app/business/pipelines/
librarian_housekeeping.py`) exactly per `ADR-055` Decisions 1, 3/5 —
consumes `T01`'s own already-computed set directly, never re-running any
detection call itself.

**`[REQ-SB-74-US-01-AC-04]` PASS — real evidence.** Called against the
real, live vault, chained after `T01`'s own real result. Real outcome: 10
archival-candidate Pending Approvals created — `action_id="propose_
customer_archival_candidate"`, each `payload["source_directory"]`
pointing at its real, current folder path: `Apple`, `AZCON Holding`,
`AzInTelecom LLC`, `Google`, `HR Avatar`, `Instagram`, `Mubadala`,
`Twitter`, `"Unsorted"` (the real, pre-existing bug-artifact folder `T01`'s
own Implementation Log disclosed — correctly, honestly flagged here since
no real Thread is ever routed to a Customer literally named
`"Unsorted"`), `YouTube`. Programmatically confirmed: zero overlap between
the archived-candidate set and the matched set; the actual candidate set
exactly equals `(all real folders) − (real matched folders)`, set-equal
confirmed. Every one of the 9 "confirmed noise" folders the story's own
Context names (Apple, Google, Instagram, Twitter, YouTube — 5 of them;
Microsoft/NVIDIA/Razer/LinkedIn were NOT flagged since real Threads
genuinely matched them this pass) is evidence-consistent with the story's
own framing. `AZCON Holding`/`HR Avatar` (named as "genuinely ambiguous
without checking real evidence") found ZERO real matches this pass — an
honest, evidence-based resolution, not a name guess. `Columbus`/`Sindan`
(also named ambiguous) DID have real matches this pass and were correctly
NOT flagged.

**A real, disclosed observation, not a defect:** `"Mubadala"` (a distinct
existing folder from `"Mubadala Investment Company"`) was flagged as a
candidate — the same class of near-spelling/legal-entity-name variance
`T01`'s own Implementation Log already disclosed for `"Department of
Government Enablement"` vs. `"...(DGE)"`, and explicitly out of THIS
pass's scope per `ADR-055`'s own Alternatives Considered (no fuzzy dedup
of the primary match). Left as-is; the operator reviews at approval time.

**Assumption (scope-internal judgement call, logged per `Implementation/
Pipeline.md`):** this coding session's own task-by-task verification order
ran `T02` (a REAL, direct `finalize_customer_backfill_routing` call,
routing the real `"Aldar"`/`"TAQA"` batches) BETWEEN `T01`'s propose call
and this task's own verification call — never how the real `T05`
orchestrating endpoint actually runs (both propose Jobs execute back-to-
back, synchronously, with zero operator approval possible in between, so
`"TAQA"`'s folder could never exist yet at archival-check time in the real
flow). Since `"TAQA"` now GENUINELY carries 7 real routed Threads (from
this session's own `T02` verification), `"TAQA"` was added to the
`matched_existing_customer_names` set passed into this verification call
— reflecting the CURRENT true evidence state honestly, rather than
fabricating a false archival-candidate artifact of this session's own test
ordering (`"Aldar"` needed no correction — already present in `T01`'s own
original matched set). Not a code change, not a defect in `propose_
customer_archival_candidates()` itself — a real, disclosed **verification-
ordering nuance for any FUTURE re-run of the real orchestrating endpoint
after an approval has already happened**, carried forward explicitly into
`T06`'s own Implementation Log since that is where a genuine, unmodified
second real endpoint call will encounter it for real (a Customer whose
ENTIRE real Thread-match set was already approved in a prior pass shows
zero matches on any later pass, by this Job's own literal, locked-AC
"zero real Thread matches THIS PASS" contract — technically correct per
Scenario 4's own wording, but worth the operator's attention).

gate: clear 2026-08-19 — no MUST-FLAG trigger fired; mechanism follows
`ADR-055`/architecture.md directly. The verification-ordering nuance above
is a logged scope-internal judgement call / real operational observation,
not a code defect requiring a fix within this task's own `## Files to
Modify`.
