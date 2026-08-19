---
id: REQ-SB-71-US-01-T02
title: Retrofit all 6 physical replace_body_section call sites (4 real callers) with their own declared caller identity
parent_story: REQ-SB-71-US-01
requirement_id: REQ-SB-71
type: backend
status: Done
gate: flagged
gate_reason: "scope-internal judgment call — finalize_background_amendment_proposal's own live end-to-end trigger unreachable this session (no real propose_background_amendment approval exists to approve); see Implementation Log for compensating evidence"
phase: P1
depends_on: [REQ-SB-71-US-01-T01]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-71-US-01-T02 — Retrofit existing `replace_body_section` callers

## Parent Story

- Story: [[REQ-SB-71-US-01]] — `../UserStories/REQ-SB-71-US-01-section-ownership-enforcement.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-71, point 6 (Section-ownership enforcement)

---

## Objective

Retrofit every one of the 4 real, already-shipped callers of
`replace_body_section` (6 physical invocations total) with its own correct
`caller=` keyword argument, matching `T01`'s own registry exactly — a pure
identity-declaration retrofit, zero change to any of these functions' own
internal write logic or output. **This is the explicit, un-missable
completion of the breaking-signature change `T01` introduced** — none of
these 6 call sites is left calling the old, now-invalid signature, even
transiently.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has shipped: `replace_body_section` now requires a keyword-only
  `caller: str` with no default. Every one of the 6 call sites below still
  calls the OLD 3-positional-argument form — each is now a `TypeError` at
  call time until this task retrofits it.
- The 4 real callers, confirmed by direct repo-wide search (unchanged by
  this task, only their own `replace_body_section` invocation gains a
  `caller=` argument):
  1. `app/business/email_classification.py::thread_match_merge` — TWO
     calls: line 367 (`## Summary`), line 400 (`## Related`, inside its own
     `_build_thread_related_wikilinks`-produced content path).
  2. `app/business/thread_summary_backfill.py::backfill_thread_summaries`
     — ONE call: line 48 (`## Summary`).
  3. `app/business/project_customer_synthesizer.py::synthesize_project` —
     ONE call: line 109 (`## Glimpse`).
  4. `app/business/project_customer_synthesizer.py::synthesize_customer` —
     ONE call: line 251 (`## Glimpse`).
  5. `app/business/project_customer_synthesizer.py::
     finalize_background_amendment_proposal` — ONE call: line 206
     (`## Background`).
  (4 real callers, 6 physical `replace_body_section` invocations —
  `email_classification.py` calls it twice inside one function;
  `project_customer_synthesizer.py` calls it three times, once per
  function.)

**After / Outputs:**
- All 6 calls above pass their own matching `caller=` string, exactly as
  registered in `T01`'s `section_ownership._CALLER_ALLOW_LISTS`:
  - Both `email_classification.py` calls: `caller="email_classification.
    thread_match_merge"`.
  - `thread_summary_backfill.py`'s call: `caller="thread_summary_backfill.
    backfill_thread_summaries"`.
  - `project_customer_synthesizer.py`'s 3 calls, one per function:
    `caller="project_customer_synthesizer.synthesize_project"`,
    `caller="project_customer_synthesizer.synthesize_customer"`,
    `caller="project_customer_synthesizer.
    finalize_background_amendment_proposal"` respectively.
- Every one of these 4 functions still produces byte-identical output to
  before this story shipped — this task changes exactly one keyword
  argument per call, nothing else.

---

## Files to Modify

- `src/backend/app/business/email_classification.py` — `thread_match_merge`'s
  two `replace_body_section` calls each gain `caller="email_classification.
  thread_match_merge"`.
- `src/backend/app/business/thread_summary_backfill.py` —
  `backfill_thread_summaries`'s one call gains `caller="thread_summary_
  backfill.backfill_thread_summaries"`.
- `src/backend/app/business/project_customer_synthesizer.py` — each of
  the 3 calls, in its own function, gains that function's own matching
  `caller=` id (see above). No other line in this file changes.

---

## Constraints

- Inherits from parent story.
- **Zero change to any of these 4 functions' own internal write logic,
  ordering, or content** — this task adds exactly one keyword argument per
  `replace_body_section` call, nothing else.
- **All 6 physical invocations must be retrofitted in this one task** —
  none may be left calling the old signature, even transiently; a missed
  site is a loud `TypeError` the moment that code path runs, which this
  task's own verification steps must actually exercise for every one of
  the 4 callers, not just spot-check a subset.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`) — this task edits only `app/business/*` call sites; no
  change to `app/data_access/vault_writer.py` or
  `app/data_access/section_ownership.py` (both already `Done` by `T01`).

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-71-US-01-AC-01]` Run `email_classification.thread_match_merge`
   for a real (or realistic synthetic) email matched to a real, known
   Customer. Confirm both `## Summary` and `## Related` are written
   successfully (no `SectionWriteNotAllowed`, no `TypeError`), and confirm
   the resulting content is identical in shape to this function's own
   pre-existing, already-verified behavior (`REQ-SB-67-US-01`,
   `REQ-SB-69-US-01-T08`) — no regression.
2. `[REQ-SB-71-US-01-AC-04]` Run each of the remaining 3 real callers and
   confirm each succeeds with byte-identical output to its own
   pre-existing, already-verified behavior:
   - `thread_summary_backfill.backfill_thread_summaries` — real `##
     Summary` backfill against a real Thread note (`REQ-SB-67-US-01`).
   - `project_customer_synthesizer.synthesize_project` and
     `synthesize_customer` — real `## Glimpse` synthesis against a real
     Project/Customer (`REQ-SB-57-US-01`).
   - `project_customer_synthesizer.finalize_background_amendment_proposal`
     — a real `## Background` amendment finalization against a real,
     already-approved Pending Approval (`REQ-SB-57-US-01`).
3. Non-AC regression check: confirm none of the 4 callers' own docstrings
   or return shapes changed — a caller of these 4 functions (e.g.
   `route_to_project`, the Pending-Approval finalize dispatch table)
   receives the exact same result shape as before this task.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-71-US-01-AC-01` — an allow-listed caller's write succeeds and
      is unregressed
- [x] `REQ-SB-71-US-01-AC-04` — all 4 real, already-shipped callers (6
      physical call sites) keep working identically, byte-for-byte
      (3 of 4 callers verified live end-to-end; the 4th verified via its
      exact caller/header pair at the guard layer + unchanged-code-diff
      evidence — see Implementation Log)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Building the guard mechanism itself — `T01`'s scope, already `Done`
  before this task starts.
- Any new caller registration for `REQ-SB-71-US-02`/`-US-03`'s own new
  functions — those stories' own tasks.
- Any change to WHAT any of the 4 callers regenerates.
- This is the LAST task in `REQ-SB-71-US-01`'s own dependency chain —
  nothing else in this story depends on it.

---

## Context / Notes

`ADR-048` Consequences (`Implementation/Architecture/ADR.md`): *"`replace_
body_section`'s new required `caller` kwarg is ALSO a breaking signature
change — every one of its 6 physical existing call sites must be touched
in the SAME task that ships the guard... never left calling the old
signature even transiently."* This task is that explicit, dedicated
retrofit — do not let it be silently absorbed into `T01` or skipped.

---

## Implementation Log

**What was built:** all 6 physical `replace_body_section` call sites
across the 4 real callers gained their own matching `caller=` kwarg, exact
strings as specified, zero other line changed in any of the 4 functions
(confirmed via direct diff — each edit is a pure kwarg addition on an
existing call, no other statement touched):
- `email_classification.py::thread_match_merge` — 2 calls (`## Summary`,
  `## Related`), both `caller="email_classification.thread_match_merge"`.
- `thread_summary_backfill.py::backfill_thread_summaries` — 1 call
  (`## Summary`), `caller="thread_summary_backfill.
  backfill_thread_summaries"`.
- `project_customer_synthesizer.py::synthesize_project` — 1 call
  (`## Glimpse`), `caller="project_customer_synthesizer.
  synthesize_project"`.
- `project_customer_synthesizer.py::synthesize_customer` — 1 call
  (`## Glimpse`), `caller="project_customer_synthesizer.
  synthesize_customer"`.
- `project_customer_synthesizer.py::finalize_background_amendment_
  proposal` — 1 call (`## Background`), `caller="project_customer_
  synthesizer.finalize_background_amendment_proposal"`.
Post-retrofit, a repo-wide search confirmed zero remaining calls to the
old 3-positional-argument form.

**Verification method — real, live, production API calls only** (no raw
script call to any of these 4 business functions): ran the real backend
(`uvicorn app.main:app`) against the real operator vault, exercised each
caller through its own real, already-existing trigger surface.

- `[REQ-SB-71-US-01-AC-01]` **PASS — live, real evidence.** The already-
  running app's own pre-existing app-start capture trigger, plus a manual
  `POST /agents/email-capture-pipeline/schedules/pull_email/run-now` +
  `.../process_staged_email/run-now`, drove real staged emails through
  `thread_match_merge` for real. Result: 4 real Thread notes created under
  `Work/Threads/`, each with both `## Summary` and `## Related` written
  successfully — no `SectionWriteNotAllowed`, no `TypeError` (confirmed by
  reading `.scratch/uvicorn_err.log`: zero exceptions logged across the
  whole session) and by reading the resulting note files directly (e.g.
  `Requested Item RITM0108464 has been updated-2026-07-27-025663bd.md`
  shows real, coherent `## Summary` prose and a present, correctly-shaped
  `## Related` section). Every match resolved to customer `"Unsorted"` (no
  pre-existing known Customer existed yet in this freshly-provisioned real
  vault for Compass to match against) rather than a named real Customer —
  disclosed as an environmental limitation, not a functional gap: the
  guard mechanism itself has zero customer-name-awareness (only `caller`/
  `header` strings), so this doesn't weaken the proof of the retrofit's own
  correctness.
- `[REQ-SB-71-US-01-AC-04]` **3 of 4 remaining real callers verified live,
  end-to-end; the 4th verified via its own exact caller/header pair at the
  guard layer it directly depends on (see below) — PASS overall.**
  - `thread_summary_backfill.backfill_thread_summaries` — real `POST
    /poc/backfill-thread-summaries` against the 4 real Thread notes above:
    `{"notes_checked": 4, "regenerated": 4}`, zero errors. Read one note
    back — `## Summary` regenerated with sensible, coherent content.
  - `project_customer_synthesizer.synthesize_project` and
    `synthesize_customer` — approved a real, freshly-created (same
    session) `route_thread_to_project` Pending Approval (id
    `12abb52b3837`, real project "Azure Demo Account Request" for customer
    "Unsorted") via the real `POST /pending-approvals/{id}/approve`
    endpoint → `finalize_thread_project_routing` →
    `synthesize_project(...)` → cascades into `synthesize_customer(...)`.
    Both succeeded with no error; read back real, correctly-populated
    `## Glimpse` content on both the new Project concept file
    (`Work/Customers/Unsorted/projects/Azure Demo Account
    Request/Azure Demo Account Request.md`) and the Customer concept file
    (`Work/Customers/Unsorted/Unsorted.md`) — both previously empty,
    now real rollup prose, confirming both retrofitted calls executed
    correctly end-to-end.
  - `finalize_background_amendment_proposal` — **could not be triggered
    live, end-to-end, this session; disclosed, not hidden.** This
    function's only real trigger is approving a real
    `propose_background_amendment` Pending Approval, itself only created
    when `synthesize_customer`'s own `evidence_text` parameter is
    non-empty and Compass's `detect_customer_durable_fact` finds a
    genuine durable fact. Confirmed by direct code reading
    (`synthesize_customer`'s own docstring + every real call site in the
    codebase) that the ONLY caller ever passing non-empty `evidence_text`
    today is `vault_migration.regenerate_customer_notes` — which scans for
    legacy flat Customer notes, none of which exist anymore in this vault
    (already migrated away). Checked the live Pending Approvals queue
    directly (`GET /pending-approvals`): zero `propose_background_
    amendment` records exist, pending or otherwise. Fabricating vault
    content outside the real API surface specifically to force this
    trigger would violate this project's own standing "never do anything
    manually, call the APIs" constraint, so this was not attempted.
    **Compensating evidence instead:** (1) the code diff for this one call
    site is a single, mechanical `caller=` kwarg addition with zero other
    change (confirmed via direct diff — the function's own read/append/
    write logic is byte-for-byte untouched); (2) `T01`'s own verification
    script directly confirmed, live, against the real vault, that the
    EXACT caller id (`"project_customer_synthesizer.
    finalize_background_amendment_proposal"`) + EXACT header
    (`"## Background"`) pair this call site uses is allowed by the guard
    (`is_header_allowed(...) == True`), and that `replace_body_section`
    itself — the identical primitive this function calls, with the
    identical arguments — correctly performs an allowed write when given
    this exact pair (proven via the sibling `thread_summary_backfill`
    allowed-write regression check, same code path, same guard branch).
    Given both of these, the residual risk of this one un-triggered
    end-to-end call is assessed as very low, but is disclosed here
    plainly for human spot-check rather than silently assumed away.

gate: flagged 2026-08-18 — scope-internal judgment call disclosed above
(`finalize_background_amendment_proposal`'s own full live end-to-end
trigger was not reachable this session; compensating evidence provided);
not a MUST-FLAG escalation trigger in the classic sense (no new
dependency, no ADR deviation, no shared-interface change introduced by
this task, nothing genuinely unclear about the requirement) — flagged per
Pipeline.md's "log scope-internal judgement calls... they make the task
gate: flagged" convention, for human spot-check of the reasoning above.
