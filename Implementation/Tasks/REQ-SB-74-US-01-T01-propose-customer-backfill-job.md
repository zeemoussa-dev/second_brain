---
id: REQ-SB-74-US-01-T01
title: propose_customer_backfill() Job — Customer-match detection + batched per-Customer proposal grouping
parent_story: REQ-SB-74-US-01
requirement_id: REQ-SB-74
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-74-US-01-T01 — `propose_customer_backfill()` Job

## Parent Story

- Story: [[REQ-SB-74-US-01]] — `../UserStories/REQ-SB-74-US-01-customer-backfill-thread-routing-and-noise-reconciliation.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-74 *Customer Backfill — Propose/Approve Thread Routing + Noise Reconciliation*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Customer Backfill" → "Detection", "`list_customer_folders()`", "`propose_customer_backfill()`/`propose_customer_archival_candidates()`" (`ADR-055` Decisions 1-3)

---

## Objective

Build the detection + proposal-grouping half of the Customer backfill: a new, narrower-sibling Compass call that decides one Thread's own primary Customer; a new real-folder enumeration; and the Job that ties them together into one batched Pending Approval per distinct proposed Customer.

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.list_known_customers()` scans `customer:` frontmatter USAGE across every note — currently near-empty (zero of 137 Threads ever routed).
- No primitive enumerates real Customer FOLDER existence under `Work/Customers/`.
- `compass_client.classify_task(subject, body, known_customers, prompt_override)` is the closest existing sibling shape, but answers a Task-classification question, not "what is this Thread's own primary Customer."
- `pending_approval_registry.create_pending_approval(agent_id, trigger, action_id, description, payload=None) -> dict` already exists, `payload` is an opaque, additive dict (`ADR-021` point 4) — no registry change needed for a multi-target payload.
- `librarian_housekeeping._thread_full_content(messages_dir) -> str` already exists and is reused, unchanged, as the grounding text for the detection call.

**After / Outputs:**
- New `compass_client.detect_customer_for_thread(thread_content: str, known_customers: list[str], prompt_override: str | None = None) -> dict` → `{"customer": str, "confidence": float}` — a narrower sibling of `classify_task` (same prompt TECHNIQUE: reuse an exact known name when it clearly matches, propose a new proper-noun name when it clearly relates to a real company not yet known, answer `"Unsorted"` rather than guess), own prompt TEXT framed around a Thread's full concatenated content. No retry loop (mirrors `classify_task`'s own precedent).
- New `vault_writer.list_customer_folders() -> list[dict]` → `[{"customer": <title>, "slug": <dir name>, "directory": Path}, ...]` for every real Customer OKF directory under `Work/Customers/` — mirrors `list_customer_projects()`'s own "enumerate this directory level, read title from concept file" shape one level up. Returns `[]` if `Work/Customers/` does not exist yet.
- New `librarian_housekeeping.propose_customer_backfill() -> dict`:
  - Iterates every real Thread still `customer: "Unsorted"` (`vault_writer.list_thread_notes()`, reading each concept file's own current `customer` frontmatter — this filtering alone gives Scenario 9's own idempotency for free: an already-routed Thread's `customer` is no longer `"Unsorted"`, so it is never even considered).
  - For each, calls `detect_customer_for_thread(full_content, known_customers=list_customer_folders()'s own "customer" values, ...)`.
  - Groups every non-`"Unsorted"` result into ONE batched Pending Approval per distinct proposed Customer name: `create_pending_approval(agent_id="librarian-housekeeping", trigger="direct", action_id="propose_customer_backfill_routing", description=..., payload={"customer": <name>, "is_new_customer": <bool — True iff <name> is not among the real existing folder names>, "thread_paths": [<str>, ...]})`.
  - A Thread whose detection result is `"Unsorted"` is left out of every batch entirely — no forced guess (Scenario 8).
  - No Thread's `customer` frontmatter or `tags` are written by this function — proposal only, never a silent write (Scenario 1).
  - Returns `{"proposed_batches": [{"customer": str, "is_new_customer": bool, "thread_paths": [str, ...], "approval_id": str}, ...], "matched_existing_customer_names": [str, ...], "left_unsorted": [str, ...]}` (or an equivalent honest, structured summary) — `matched_existing_customer_names` feeds directly into `T03`'s own `propose_customer_archival_candidates`.

---

## Files to Modify

- `src/backend/app/data_access/compass_client.py` — add `detect_customer_for_thread`.
- `src/backend/app/data_access/vault_writer.py` — add `list_customer_folders`.
- `src/backend/app/business/pipelines/librarian_housekeeping.py` — add `propose_customer_backfill`.

---

## Constraints

- Inherits from parent story.
- Never a silent write — this Job only ever creates Pending Approval records; it never touches any Thread's `customer` or `tags`.
- `trigger="direct"`, never `"background"` — one backfill pass can legitimately produce multiple distinct per-Customer batches, which `"background"`'s own idempotency guard would silently collapse (mirrors `_create_librarian_company_link_proposal`'s own established reasoning).
- `known_customers` passed into `detect_customer_for_thread` must be `list_customer_folders()`'s own real folder names, NOT `list_known_customers()` — a real, deliberate distinction (`ADR-055` Decision 3); using the wrong one would silently starve the detection call of the real 26 existing Customer names.
- No Python-side confidence-threshold logic — the honest three-way outcome (existing match / new-Customer proposal / `"Unsorted"`) is the model's own prompted output, mirrored from `classify_email`/`classify_task`'s existing contract.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-74-US-01-AC-01]` Direct Python-shell check against the real vault: call `librarian_housekeeping.propose_customer_backfill()`. Confirm the result groups matched Threads into batches, exactly one Pending Approval per distinct proposed Customer name (check `pending_approval_registry.list_pending_approvals(status="pending")` for the real, newly-created records — each with `action_id="propose_customer_backfill_routing"` and a `payload["thread_paths"]` naming every Thread matched to that same Customer). Confirm NO Thread's own `customer` frontmatter or `tags` were modified by this call (re-read a few matched Threads' concept files directly; still `customer: "Unsorted"`).
2. `[REQ-SB-74-US-01-AC-08]` Among the real Threads processed, identify at least one whose own content genuinely gives no clear Customer signal (or construct a disposable test Thread with deliberately ambiguous/generic content). Confirm it does not appear in any `payload["thread_paths"]` across any created batch, and its own `customer` frontmatter is still `"Unsorted"`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `compass_client.detect_customer_for_thread` returns the honest three-way outcome (exact known name / new proper-noun proposal / `"Unsorted"`)
- [x] `vault_writer.list_customer_folders()` enumerates every real Customer OKF directory under `Work/Customers/`, `[]` if none yet
- [x] `propose_customer_backfill()` creates exactly one batched Pending Approval per distinct proposed Customer, naming every matched Thread's path in its own payload
- [x] No Thread's `customer` frontmatter or `tags` are written by this Job — proposal only
- [x] A Thread with no clear Customer signal is excluded from every batch, stays `"Unsorted"`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The deferred write itself (`finalize_customer_backfill_routing`) — `T02`.
- The archival-candidate Job — `T03`.
- `_APPROVAL_HANDLERS` registration and the HTTP endpoint — `T05`.
- The real full-corpus run + a real approve round trip — `T06`.

---

## Context / Notes

This task can be verified entirely via direct Python-shell calls against the real, configured vault — no HTTP endpoint exists yet (that's `T05`), mirroring `REQ-SB-72-US-01`'s own established "function-level proof before HTTP-level proof" technique.

---

## Implementation Log

Built: `compass_client.detect_customer_for_thread` (new sibling of
`classify_task`, `app/data_access/compass_client.py`); `vault_writer.
list_customer_folders()` (new, `app/data_access/vault_writer.py`, placed
beside `list_customer_projects`); `librarian_housekeeping.
propose_customer_backfill()` (new, `app/business/pipelines/
librarian_housekeeping.py`), all exactly per `ADR-055`.

**Real vault state at run time (2026-08-19, re-confirmed live):** 28
Customer folders under `Work/Customers/` (not 26 — the corpus grew since
the story was written; includes one, real, PRE-EXISTING anomaly: a folder
literally titled `"Unsorted"` with a nested `projects/Azure Demo Account
Request/` — a bug artifact from before this story, not created by this
task's own code. Left untouched, out of this task's own scope; `T03`'s
own evidence-based archival Job will naturally flag it since no real
Thread is ever routed to a Customer named `"Unsorted"` — a correct,
disclosed side-effect of the existing design, not a defect). 132 real
Threads, all `customer: "Unsorted"` before this run.

**`[REQ-SB-74-US-01-AC-01]` PASS.** Ran `propose_customer_backfill()` for
real against the full real corpus (132 Threads, real Compass calls,
577.9s). Result: 26 distinct proposed-Customer batches, 106 Threads
matched in total. Verified directly against `pending_approval_registry.
list_pending_approvals(status="pending")`: exactly 26 real records with
`action_id="propose_customer_backfill_routing"`, one per distinct
Customer, each `payload["thread_paths"]` naming every Thread matched to
that Customer (total 106 across all 26, matching the in-memory result).
Spot-checked 2 real Threads named in a batch — `customer` frontmatter
still `"Unsorted"`, `tags` still `["customer/unsorted", "kind/emails"]`
after the run — confirmed proposal-only, no silent write.

**`[REQ-SB-74-US-01-AC-08]` PASS.** 26 Threads left `"Unsorted"` (no clear
Customer signal). Verified zero overlap between `left_unsorted` and any
batch's own `thread_paths` (programmatic set-intersection, real result:
0). Spot-checked 3 real left-Unsorted Threads — `customer` frontmatter
confirmed still `"Unsorted"`.

**Real, notable outcome — TAQA correctly detected as a new Customer**
(matches the story's own PRD-level example exactly): 7 real Threads
proposed as a NEW Customer `"TAQA"`, `is_new_customer: True` — validates
the "brand-new Customer, no existing folder" path end-to-end at the
propose stage.

**A real, disclosed (not fixed) observation, not a defect in this task's
own code:** two separate new-Customer batches were proposed for what is
very likely the SAME real company — `"Department of Government Enablement"`
(5 Threads) and `"Department of Government Enablement (DGE)"` (1 Thread)
— two independent per-Thread Compass calls produced a spelling/format
variant for a company with no existing folder to anchor an exact-name
match against. This is the SAME class of near-spelling reconciliation
`ADR-055`'s own Alternatives Considered section explicitly rejected
adding to this pass's scope (`_fuzzy_match_known_entity`-style dedup of
the PRIMARY match) — left as-is; the operator reviews both batches at
approval time and can decline/re-route one manually. Not an AC violation
(each batch is independently correct given its own Thread evidence).

**Assumption (scope-internal judgement call, logged per `Implementation/
Pipeline.md`):** `existing_folder_names` passed to `detect_customer_for_
thread` includes the pre-existing `"Unsorted"` folder's own title
verbatim (a real, disclosed pre-existing data anomaly, not filtered) —
harmless by construction, since the function already treats a `"customer"
== "Unsorted"` detection result as "leave Unsorted" regardless of why the
model answered that way.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired for this task's own
build (mechanism follows `ADR-055`/architecture.md directly; the one
scope-internal judgement call above is logged, not an assumption filling
a genuine scope gap).
