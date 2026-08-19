---
id: BUGFIX-08-US-01-T02
title: Wire dedupe_key into route_to_project, classification-failure acknowledgement, and the Librarian's Customer backfill/archival proposals (BUG-030 fix)
parent_story: BUGFIX-08-US-01
requirement_id: BUG-030
type: backend
status: Done
gate: clear
gate_reason: ""
phase: MVP
depends_on: [BUGFIX-08-US-01-T01]
created: 2026-08-19
updated: 2026-08-19
---

# BUGFIX-08-US-01-T02 — Wire `dedupe_key` into `route_to_project`, classification-failure acknowledgement, and the Librarian's Customer backfill/archival proposals

## Parent Story

- Story: [[BUGFIX-08-US-01]] — `../UserStories/BUGFIX-08-US-01-pending-approval-target-aware-dedup.md`
- Requirement: `BUGS.md` → `BUG-030` (bugfix story; no PRD requirement anchor). Mechanism: [ADR-056](../Architecture/ADR.md).

---

## Objective

Pass a per-target `dedupe_key` into `create_pending_approval` at the four remaining real
call sites `BUG-030` names — `email_classification.py::route_to_project` and
`_create_classification_failure_pending_approval`, and
`librarian_housekeeping.py::propose_customer_backfill` and
`propose_customer_archival_candidates` — so a staged email/Thread or a Customer-backfill/
archival candidate that already has an unresolved Pending Approval is never reprocessed
into a fresh duplicate on a later capture/Job tick.

---

## Starting State → End State

**Before / Inputs:**
- `route_to_project` (`src/backend/app/business/email_classification.py`, lines 863-942)
  calls `create_pending_approval(agent_id="email-capture-pipeline", trigger="direct",
  action_id="route_thread_to_project", description=..., payload={...,
  "conversation_id": thread_result["conversation_id"]})` with no dedup protection — a later
  capture tick that treats the same staged Thread as new again (never consumed/marked
  resolved after its first pass) creates a second, identical proposal.
- `_create_classification_failure_pending_approval` (same file, lines 1300-1330-ish) calls
  `create_pending_approval(agent_id="email-capture-pipeline", trigger="direct",
  action_id="acknowledge_classification_failure", description=..., payload={
  "conversation_id": email["conversation_id"], ...})` with the same gap.
- `propose_customer_backfill` (`src/backend/app/business/pipelines/librarian_housekeeping.py`,
  lines 596-706) batches Threads per distinct proposed `customer` and calls
  `create_pending_approval(agent_id="librarian-housekeeping", trigger="direct",
  action_id="propose_customer_backfill_routing", description=..., payload=batch)` once per
  batch, inside its own per-customer loop — no dedup; a repeat run before the first batch is
  approved/declined re-scans the same still-`"Unsorted"` Threads into a brand-new duplicate
  batch (confirmed live, `SPRINT-068`: 13 real duplicate groups, one repeated 17×).
- `propose_customer_archival_candidates` (same file, lines 768-813) calls
  `create_pending_approval(agent_id="librarian-housekeeping", trigger="direct",
  action_id="propose_customer_archival_candidate", description=..., payload={...})` once per
  candidate, same gap.
- None of these four calls passes `dedupe_key` today — the parameter does not exist until
  `BUGFIX-08-US-01-T01` lands (this task `depends_on` it).

**After / Outputs:**
- `route_to_project`'s call gains
  `dedupe_key=f"route_thread_to_project:{thread_result['conversation_id']}"`.
- `_create_classification_failure_pending_approval`'s call gains
  `dedupe_key=f"acknowledge_classification_failure:{email['conversation_id']}"`.
- `propose_customer_backfill`'s per-batch call gains
  `dedupe_key=f"propose_customer_backfill_routing:{customer}"` (computed per batch, inside the
  existing per-customer loop, using the same `customer` local already in scope).
- `propose_customer_archival_candidates`'s per-candidate call gains
  `dedupe_key=f"propose_customer_archival_candidate:{customer}"` (computed per candidate,
  using the same `customer` local already in scope).
- In every case, a later call sharing the same real target (same `conversation_id`, same
  `customer`) while the prior proposal is still `status: "pending"` returns the EXISTING
  record instead of creating a new one — the calling function's own return value (a single
  record for `route_to_project`/the classification-failure helper; a `proposed_batches`/
  `archival_candidates` list entry carrying `approval_id` for the two Librarian functions)
  reflects the existing record's `id`, unchanged from the prior call.

---

## Files to Modify

- `src/backend/app/business/email_classification.py`:
  1. `route_to_project` — add `dedupe_key=f"route_thread_to_project:{thread_result['conversation_id']}"`
     to its existing `create_pending_approval` call.
  2. `_create_classification_failure_pending_approval` — add
     `dedupe_key=f"acknowledge_classification_failure:{email['conversation_id']}"` to its
     existing `create_pending_approval` call.
- `src/backend/app/business/pipelines/librarian_housekeeping.py`:
  1. `propose_customer_backfill` — inside its existing per-customer `for customer, batch in
     batches.items():` loop, add `dedupe_key=f"propose_customer_backfill_routing:{customer}"`
     to its existing `create_pending_approval` call.
  2. `propose_customer_archival_candidates` — inside its existing per-candidate `for entry in
     vault_writer.list_customer_folders():` loop, add
     `dedupe_key=f"propose_customer_archival_candidate:{customer}"` to its existing
     `create_pending_approval` call.

No other file is in scope — `pending_approval_registry.py`'s own `dedupe_key` parameter and
`skill_registry.py::invoke_skill` are `BUGFIX-08-US-01-T01`'s scope, already landed.

---

## Constraints

- Inherits from parent story — must not collapse proposals for genuinely different real
  targets into one: two different Threads/`conversation_id`s, or two different Customer
  names, must each still get their own `dedupe_key` and their own Pending Approval. Every
  `dedupe_key` in this task is namespaced `"{action_id}:{stable_target_identifier}"`
  exactly as `ADR-056` decided — do not reuse a bare target identifier across the two
  different `librarian-housekeeping` action kinds (`propose_customer_backfill_routing` vs.
  `propose_customer_archival_candidate`), since both can legitimately name the same
  Customer string.
- Must not weaken or remove `ADR-018` point 2's existing `trigger == "background"` guard —
  none of these four call sites use `trigger="background"` and none of them changes that.
- `route_to_project` uses `thread_result["conversation_id"]` (not `thread_path`) as the
  stable identifier — `ADR-046` Decision 8 already established `conversation_id` survives a
  Thread rename; `thread_path` does not. Do not substitute `thread_path`.
- `propose_customer_backfill`/`propose_customer_archival_candidates` compute `dedupe_key`
  from the SAME `customer` local variable each function already uses to build its own
  `description`/payload — do not introduce a second, differently-derived customer string.
- A `dedupe_key` match returns the EXISTING record's own stale payload/description
  unchanged — a repeat `propose_customer_backfill` run that would have added a newly-
  `"Unsorted"` Thread to an already-pending batch does NOT retroactively grow that batch's
  `thread_paths` (`ADR-056`'s own accepted Consequence); the newly-found Thread is picked up
  on the next run once the current pending batch is actually resolved.

---

## Tests

**Manual verification steps (direct Python-shell calls against the real
`app.business.email_classification`/`app.business.pipelines.librarian_housekeeping`/
`app.business.pending_approval_registry` functions, run via the backend's own `.venv`
against the real, configured vault):**

1. [BUGFIX-08-US-01-AC-02] **`route_to_project`, real reprocessing.** Build a real
   `thread_result` dict (`created=True`, `thread_path` pointing to a real, already-existing
   Thread note that has a `## Summary` section — or a throwaway one you create with one — and
   a fixed throwaway `conversation_id`, e.g. `"zz-verify-conv-001"`), a `classification` dict
   with a real or throwaway `customer`, and an `email` dict (unused by the function but
   required by its signature). Call `route_to_project(thread_result, classification, email)`
   twice with the identical dicts, back-to-back — mirroring a staged Thread reprocessed on a
   later capture tick before its first proposal resolves. Confirm the SECOND call returns a
   dict whose `"id"` is identical to the first call's returned `"id"`. Confirm
   `pending_approval_registry.list_pending_approvals(status="pending",
   agent_id="email-capture-pipeline")` contains exactly ONE record with
   `action_id == "route_thread_to_project"` and
   `dedupe_key == "route_thread_to_project:zz-verify-conv-001"` (not two). Resolve/decline the
   throwaway record afterward.
2. [BUGFIX-08-US-01-AC-02] **Classification-failure acknowledgement, real reprocessing.**
   Build a real `email` dict with a fixed throwaway `conversation_id` (e.g.
   `"zz-verify-conv-002"`) and the other keys the function reads (`subject`, `sender_email`/
   `sender_name`), and any `Exception` instance. Call
   `_create_classification_failure_pending_approval(email, exc)` twice with the identical
   `email`. Confirm the second call's returned `"id"` matches the first's, and confirm exactly
   one `status: "pending"` record exists with
   `action_id == "acknowledge_classification_failure"` and
   `dedupe_key == "acknowledge_classification_failure:zz-verify-conv-002"`. Resolve/decline
   the throwaway record afterward.
3. [BUGFIX-08-US-01-AC-02] **`propose_customer_backfill`, real Job re-run.** Run
   `propose_customer_backfill()` for real against the real, current vault, then immediately
   run it a SECOND time (real vault state is unchanged between the two runs — neither run's
   proposals are approved/declined) — this is the literal `BUG-030` repro shape (13 real
   duplicate groups, one repeated 17×, `SPRINT-068`). For every customer that appears in BOTH
   runs' `proposed_batches`, confirm the second run's `approval_id` for that customer is
   IDENTICAL to the first run's — i.e. no growth in `list_pending_approvals(status="pending",
   agent_id="librarian-housekeeping")`'s count of `action_id ==
   "propose_customer_backfill_routing"` records between the two runs. If the real vault
   currently has zero `"Unsorted"` Threads that map to a known customer (so
   `proposed_batches` is empty both times — check first), fall back to a direct two-call test
   against `create_pending_approval` itself using the exact convention
   (`dedupe_key=f"propose_customer_backfill_routing:{customer}"` with a throwaway `customer`
   value) to prove the mechanism deterministically, and disclose in the Implementation Log
   which path was exercised. This step runs real Compass calls per real Unsorted Thread — if
   wall-clock cost is a concern, bound scope via an in-process monkeypatch of
   `vault_writer.list_thread_notes()` to a small, real, filtered subset before calling the
   real function twice (mirrors this project's own established "bound a live-data
   verification via monkeypatch of the real fetch function" pattern), and disclose that
   bounding explicitly.
4. [BUGFIX-08-US-01-AC-02] **`propose_customer_archival_candidates`, real Job re-run.** Using
   the real (or bounded) `matched_existing_customer_names` set from step 3's first run, call
   `propose_customer_archival_candidates(matched_existing_customer_names)` twice with the
   identical argument. Confirm every candidate's `approval_id` is identical between the two
   calls' `archival_candidates` lists, and confirm no growth in
   `list_pending_approvals(status="pending", agent_id="librarian-housekeeping")`'s count of
   `action_id == "propose_customer_archival_candidate"` records between the two calls.
5. Cleanup: resolve/decline every throwaway `zz-verify-*` Pending Approval record created by
   steps 1-2 so none linger as real, unresolved records; disclose whether steps 3-4 created
   any new real, still-`"pending"` records against real vault data (expected — those are
   real, legitimate first-time proposals for genuinely Unsorted Threads/candidates, not
   duplicates, and are left for the operator to resolve normally, not cleaned up by this
   task).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `route_to_project` passes `dedupe_key=f"route_thread_to_project:{thread_result['conversation_id']}"`
- [x] `_create_classification_failure_pending_approval` passes
      `dedupe_key=f"acknowledge_classification_failure:{email['conversation_id']}"`
- [x] `propose_customer_backfill` passes `dedupe_key=f"propose_customer_backfill_routing:{customer}"`
      per batch
- [x] `propose_customer_archival_candidates` passes
      `dedupe_key=f"propose_customer_archival_candidate:{customer}"` per candidate
- [x] `BUGFIX-08-US-01-AC-02` (Scenario 2 / `BUG-030`) verified live for all four call sites: a
      later reprocessing pass never creates a second, duplicate Pending Approval for the same
      real target while the first is still unresolved
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `pending_approval_registry.create_pending_approval`'s own `dedupe_key` parameter and
  `skill_registry.py::invoke_skill` — `BUGFIX-08-US-01-T01`'s scope, already landed.
- Any change to `agent_schedule_registry.py`'s shared-lock mechanism.
- Cleaning up the already-existing real duplicate Pending Approval records (301+50+15 real
  `email-capture-pipeline`, 13 real `librarian-housekeeping`) — explicit story Non-Goal.
- Any UI/Pending Approvals list rendering change — confirmed no screen change needed.
- Any change to `finalize_thread_project_routing`, `finalize_customer_backfill_routing`, or
  any other approval-time finalize handler — this task only touches the proposal/creation
  side.

---

## Context / Notes

Full reasoning, alternatives considered, and consequences: [ADR-056](../Architecture/ADR.md).
Architecture scope: `Implementation/Architecture/architecture.md` → §"Agent Working Modes &
Pending Approvals" (`REQ-SB-21-US-01`, see `ADR-018` + `ADR-020` + `ADR-056`).

`propose_customer_backfill`'s own docstring claim ("this filtering alone gives Scenario 9's
own idempotency for free") is correct only for an ALREADY-APPROVED-AND-WRITTEN Thread, not
for one with an unresolved, still-`"pending"` proposal — `ADR-056`'s Context section has the
full resolution. This task's `dedupe_key` addition is what actually closes the gap; no
docstring correction is required by this task (the docstring's claim remains true for the
case it describes).

This task `depends_on: [BUGFIX-08-US-01-T01]` — `create_pending_approval`'s `dedupe_key`
parameter must exist before any of these four call sites can pass it.

---

## Implementation Log

**Changes made (exactly as scoped, no deviation):** added the one named `dedupe_key=` keyword
argument to each of the four existing `create_pending_approval` calls — `route_to_project`
(`f"route_thread_to_project:{thread_result['conversation_id']}"`),
`_create_classification_failure_pending_approval`
(`f"acknowledge_classification_failure:{email['conversation_id']}"`),
`propose_customer_backfill` (`f"propose_customer_backfill_routing:{customer}"`, inside its
existing per-customer loop), `propose_customer_archival_candidates`
(`f"propose_customer_archival_candidate:{customer}"`, inside its existing per-candidate loop).
No other line changed in either file.

**Live verification — run via `.venv` against the real, configured vault/store**
(throwaway script `src/backend/.scratch/verify_dedupe_key_t02.py`, not part of `## Files to
Modify`, discarded after this run):

- **[BUGFIX-08-US-01-AC-02] Step 1 — `route_to_project`, real reprocessing.** PASS. Built a real
  `thread_result` against a real, existing Unsorted Thread note with a real `## Summary`
  section, fixed throwaway `conversation_id: "zz-verify-conv-001"`. Two back-to-back calls (two
  real Compass `guess_project_for_thread` calls, as expected — dedup only prevents the SECOND
  Pending Approval record, not the Compass call itself) returned the IDENTICAL record id; exactly
  one pending record existed with `dedupe_key ==
  "route_thread_to_project:zz-verify-conv-001"`. Declined/cleaned up.
- **[BUGFIX-08-US-01-AC-02] Step 2 — classification-failure acknowledgement, real reprocessing.**
  PASS. Two calls with the same throwaway `conversation_id: "zz-verify-conv-002"` returned the
  identical id; exactly one pending record with the expected `dedupe_key`. Declined/cleaned up.
- **[BUGFIX-08-US-01-AC-02] Step 3 — `propose_customer_backfill`, real Job re-run.** PASS, with a
  disclosed bounding. The real, current vault has 123 real "Unsorted" Threads today — running
  the unbounded Job twice would fire ~246 real Compass calls and flood the live queue with dozens
  of new proposals purely for verification, right after this same session's own queue cleanup.
  Per the task's own explicit authorization, bounded `vault_writer.list_thread_notes()` (via
  in-process monkeypatch, restored immediately after) to 3 real, already-existing Unsorted
  Threads whose titles named a real Customer (Core42/Columbus/Mubadala-related subjects) — still
  the literal real `propose_customer_backfill()` function end-to-end (real Compass calls, real
  `create_pending_approval` calls), only the INPUT SET bounded. Two real runs produced identical
  `proposed_batches` for all 3 resulting customers (Columbus, Ministry of Digital Development and
  Transport, Mubadala Investment Company) — run2 added ZERO new records
  (`propose_customer_backfill_routing` pending count: 38 before → 41 after both runs, i.e. +3 from
  run1, +0 from run2). This is the literal `BUG-030` repro shape (repeat Job run before
  resolution) now closed.
- **[BUGFIX-08-US-01-AC-02] Step 4 — `propose_customer_archival_candidates`, real Job re-run.**
  PASS on the mechanism, with a real mistake caught and corrected during this pass (disclosed in
  full, not a MUST-FLAG trigger — scope-internal, corrected before leaving the task): calling
  `propose_customer_archival_candidates(matched_existing_customer_names)` with the BOUNDED run's
  own `matched_existing_customer_names` (only 3 real customers, since only 3 real Threads were
  processed this pass) caused every OTHER real customer folder (24 of them) to be proposed as an
  "archival candidate" — technically correct against the bounded input, but a MISLEADING real
  business artifact: those 24 real customer folders (G42, Mubadala, Microsoft, Apple, etc.) do
  NOT actually have zero real Thread matches across the FULL 123-Thread corpus; they only
  appeared to because this verification pass's own input bounding starved the evidence signal.
  Two back-to-back calls DID correctly return identical `approval_id`s per candidate (the dedup
  mechanism itself is proven correct), but leaving those 24 newly-created real pending records in
  the live queue would have been incorrect data, not just verification noise — so all 24 were
  identified by their shared creation timestamp and explicitly declined immediately after
  discovery (`resolve_pending_approval(id, "declined")` for each), confirmed via a follow-up
  count. The real, pre-existing 13 `propose_customer_archival_candidate` pending records
  (untouched by this task, matching `BUG-030`'s own originally-disclosed live evidence count)
  remained exactly 13 afterward — proving no genuine pre-existing record was touched, only the 24
  artifacts this verification pass itself introduced.
- **Step 5 — cleanup / disclosure.** All throwaway `zz-verify-*` records (steps 1-2) and all 24
  bounding-artifact archival records (step 4) declined. The 3 real, legitimate
  `propose_customer_backfill_routing` proposals from step 3's bounded-but-real run (genuinely
  Unsorted Threads that really do map to those 3 real Customers, per real Compass classification)
  were deliberately left `pending` for the operator to resolve normally, per the task's own
  explicit instruction — not duplicates, not cleaned up. The pre-existing 38
  `propose_customer_backfill_routing` and 13 `propose_customer_archival_candidate` real records
  (present before this task ran, `BUG-030`'s own originally-disclosed duplicates) remain
  untouched — cleaning those up is the story's own explicit Non-Goal.

**Judgement call logged for spot-check (not a MUST-FLAG trigger):** bounding
`propose_customer_backfill`'s input for wall-clock/cost reasons was pre-authorized by the task's
own `## Tests` wording; declining the 24 resulting archival-candidate records was this task's own
scope-internal correction to avoid leaving misleading real data in the live queue as a side
effect of that authorized bounding — not itself a new decision about the dedup mechanism, no ADR
implication, no code change beyond what was already scoped.

`gate: clear` 2026-08-19 — no MUST-FLAG trigger fired. No new dependency, no shared-interface
change beyond the task's own four additive `dedupe_key=` arguments (already the task's explicit
scope), no ADR deviation (matches `ADR-056` exactly, including the exact per-call-site `dedupe_key`
convention it specifies), no unanticipated file, no escalation.
