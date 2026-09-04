---
id: REQ-SB-69-US-01-T03
title: email_capture_pipeline.py reads from email_staging instead of calling outlook_com; per-item failure isolation spans the staging boundary
parent_story: REQ-SB-69-US-01
requirement_id: REQ-SB-69
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-69-US-01-T01]
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-69-US-01-T03 — Pipeline reads from staging

## Parent Story

- Story: [[REQ-SB-69-US-01]] — `../UserStories/REQ-SB-69-US-01-decoupled-email-pull-and-human-readable-thread-notes.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-69 *Decoupled Email Pull + Human-Readable, Graph-Connected Thread Notes*

---

## Objective

Restructure `run_email_capture_pipeline` to read its per-item input from
`email_staging.list_staged_emails()` instead of calling `outlook_com.
list_recent_mail` itself, dropping the `outlook_com` import entirely
(`ADR-046` Decision 3) — the compiled `Classify`→`Thread-Match/Merge`→
`Route-to-Project` DAG (`ADR-043` points 1/3/4) stays structurally
unchanged. Preserve the per-item failure posture across the new staging
boundary (Scenario 4): a failed item stays staged and unmarked; every
other staged item in the same run is still processed normally.

---

## Starting State → End State

**Before / Inputs:**
- `run_email_capture_pipeline(limit: int = 10) -> list[dict]`
  (`app/business/pipelines/email_capture_pipeline.py`, lines 256-316):
  first line `emails = outlook_com.list_recent_mail(limit=limit)`, then
  `already_processed = vault_writer.load_processed_email_ids()`, then
  loops over `emails`, skipping already-processed ids, invoking the
  compiled graph once per new email, catching any per-email exception
  (leaving that email unmarked so a later run retries it), and calling
  `vault_writer.mark_email_processed(email["id"])` only on success.
- `email_capture_pipeline.py` imports `outlook_com` at module top level
  (`from app.data_access import outlook_com, vault_writer`).

**After / Outputs:**
- `run_email_capture_pipeline`'s own first two lines become: `emails =
  email_staging.list_staged_emails()` and `already_processed =
  vault_writer.load_processed_email_ids()` (unchanged second check —
  still consulted here, per `ADR-043` point 2's already-established "a
  second, independent consult at processing time" contract, even though
  `T02`'s `pull_and_stage_emails` already pre-filtered once at Pull
  time — this is deliberate defense-in-depth, not redundant dead logic:
  a staged item could in principle have been marked processed by an
  earlier, different run between when it was staged and when this run
  picks it up).
- On success, BOTH `email_staging.remove_staged_email(email["id"])` AND
  `vault_writer.mark_email_processed(email["id"])` are called (order
  does not matter functionally, but call both). On a per-item failure
  (the existing `except Exception` branch), NEITHER is called — the item
  stays staged AND unmarked, so a later run retries it, mirroring the
  per-email try/except+continue posture `ADR-043` point 1 already
  established, now spanning the staging boundary too (Scenario 4).
- `email_capture_pipeline.py` drops its `outlook_com` import entirely;
  gains `from app.data_access import email_staging` (alongside its
  existing `vault_writer` import). The module's own docstring's
  `Fetch`-era text (lines 13-19) is updated to describe reading from
  staging instead of being the pre-graph `Fetch` step itself — a
  documentation-only change, no behavior implication.
- `get_job_tree()` and the compiled graph itself (`_build_graph`,
  `_GRAPH`, every node/edge) are completely untouched — this task only
  changes `run_email_capture_pipeline`'s own input source and its
  success/failure bookkeeping calls.

---

## Files to Modify

- `src/backend/app/business/pipelines/email_capture_pipeline.py`:
  - Replace `from app.data_access import outlook_com, vault_writer` with
    `from app.data_access import email_staging, vault_writer`.
  - In `run_email_capture_pipeline`, replace `emails =
    outlook_com.list_recent_mail(limit=limit)` with `emails =
    email_staging.list_staged_emails()` — `limit` is no longer meaningful
    here (Pull's own `limit` parameter, `T02`, now bounds what gets
    staged in the first place); keep the `limit: int = 10` parameter on
    the function signature for backward call-site compatibility (every
    real caller — `run_capture_for_agent`, `T04`'s new
    `process_staged_email` handler — may still pass it, it is simply
    unused by this function's own body now) or, if judged cleaner,
    remove it and update the one real call site
    (`email_classification.py::run_capture_for_agent`) accordingly —
    coder's own scope-internal judgement call, log whichever is chosen.
  - On the success path (after `vault_writer.mark_email_processed(
    email["id"])`), add `email_staging.remove_staged_email(email["id"])`.
  - On the failure path (inside the existing `except Exception as exc:`
    block), make no change — neither `mark_email_processed` nor
    `remove_staged_email` is called there today or after this edit.
  - Update the module's own top-of-file docstring (lines 13-19) to
    describe `run_email_capture_pipeline` reading from
    `email_staging.list_staged_emails()` instead of being a pre-graph
    `Fetch` batch step that calls `outlook_com` — documentation text
    only.

---

## Constraints

- Inherits from parent story.
- **The compiled graph itself (`_build_graph`/`_GRAPH`/every node/edge/
  routing function) is completely unchanged** — this task only touches
  `run_email_capture_pipeline`'s own pre-graph bookkeeping.
- **`email_capture_pipeline.py` must not import `outlook_com` after this
  task** — the parent story's own hard Constraint; `email_pull.py`
  (`T02`) is the sole remaining importer in the email path.
- **Neither `mark_email_processed` nor `remove_staged_email` is ever
  called for a failed item** — this is the exact mechanism Scenario 4
  needs; a partial call (only one of the two) would leave an
  inconsistent state (e.g. marked processed but still staged, silently
  hiding a failure from a future retry).
- **`already_processed`/`mark_email_processed` themselves are unchanged**
  (`vault_writer.py`) — this task never edits `vault_writer.py`.
- No change to `app/business/email_classification.py` in this task
  (`run_capture_for_agent`'s own call site, if it needs a `limit`
  signature update, is this task's own scope only if the coder chooses
  to drop the parameter — otherwise leave `email_classification.py`
  untouched).

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-69-US-01-AC-04]` Stage at least three real (or realistic
   synthetic) emails via `email_staging.stage_email` directly (no real
   Outlook pull needed for this check). Monkeypatch
   `classify_captured_email` (or another Job the graph invokes) so it
   raises a real exception for exactly ONE of the three staged emails
   (e.g. matched by subject), leaving the other two to succeed normally.
   Call `run_email_capture_pipeline()`. Confirm: (a) the failed email's
   own `.second-brain/email_staging/<id>/` directory still exists
   afterward AND its `id` is NOT present in
   `vault_writer.load_processed_email_ids()`; (b) both OTHER emails'
   staged directories are gone (`remove_staged_email` fired) AND both
   `id`s ARE present in `load_processed_email_ids()`; (c) the function's
   own returned `results` list contains an honest `{"subject":...,
   "error":...}` entry for the failed one and normal success entries for
   the other two — mirroring `run_email_capture_pipeline`'s own
   already-documented per-email failure-reporting shape.
2. Re-run `run_email_capture_pipeline()` a second time immediately (no
   new staging in between). Confirm the previously-failed email is
   picked up again (still present in `list_staged_emails()`) and, with
   the monkeypatch now removed/restored, completes successfully this
   time — confirming the retry path genuinely works, not just that the
   item was left alone.
3. Non-AC regression check: confirm `email_capture_pipeline.py`'s own
   top-level imports no longer include `outlook_com` (a direct code
   read/grep), and confirm the module still imports and compiles cleanly
   (`python -c "import app.business.pipelines.email_capture_pipeline"`).
4. Non-AC regression check: confirm `get_job_tree()`'s own returned node/
   edge shape is byte-identical to before this task (same 6 Job ids, same
   `depends_on` edges) — the compiled graph itself is untouched.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-69-US-01-AC-04` — a per-item processing failure leaves that
      item staged and unmarked; every other staged item in the same run
      still succeeds normally
- [x] `email_capture_pipeline.py` no longer imports `outlook_com`
- [x] The compiled graph (`get_job_tree()`) is unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint — not
      warranted (see `## Implementation Log`): this task is a direct, mechanical
      build of `ADR-046` Decision 3, no new decision/pattern/constraint beyond what
      the ADR already recorded
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Pull step itself (`email_pull.py`, the `on_item_fetched` callback)
  — `T02` (already `depends_on` here, but this task never calls it).
- Independent-dispatch capability wiring — `T04`.
- Thread filename/dates/wikilinks — `T05`-`T08`.

---

## Context / Notes

`ADR-046` Decision 3 (`Implementation/Architecture/ADR.md`) is the full
architectural reasoning for this restructuring, including why
`already_processed`/`mark_email_processed` stay a real, deliberate
SECOND check rather than being folded away now that `T02` already
pre-filters once at Pull time.

---

## Implementation Log

**Built as designed, no deviations from `## Starting State → End State`.**
`src/backend/app/business/pipelines/email_capture_pipeline.py`:
- `from app.data_access import outlook_com, vault_writer` replaced with
  `from app.data_access import email_staging, vault_writer` — the module
  no longer imports `outlook_com` at all (confirmed by direct grep, Test
  step 3).
- `run_email_capture_pipeline`'s first line is now `emails =
  email_staging.list_staged_emails()`; `already_processed =
  vault_writer.load_processed_email_ids()` kept as the unchanged second,
  independent check.
- On success: `email_staging.remove_staged_email(email["id"])` added
  immediately after the existing `vault_writer.mark_email_processed(
  email["id"])` call. On the existing `except Exception as exc:` failure
  branch: no change — neither is called, so a failed item stays staged
  and unmarked.
- Module docstring (top-of-file) and `run_email_capture_pipeline`'s own
  docstring updated to describe reading from `email_staging.
  list_staged_emails()` instead of being the pre-graph `Fetch` step
  itself — documentation-only, no behavior implication.
- `_build_graph`/`_GRAPH`/`get_job_tree` untouched — zero lines changed
  in that region of the file.

**Scope-internal judgement calls (logged per `Implementation/Pipeline.md`
hard rule 5, not MUST-FLAG triggers):**

1. **Kept the `limit: int = 10` parameter on `run_email_capture_pipeline`'s
   own signature, unused by the function body.** The task's own Files-to-
   Modify text explicitly offered either choice. Removing it would require
   editing `email_classification.py::run_capture_for_agent` (the one real
   call site) — that file is out of this task's own `## Files to Modify`
   by default, and `T02`'s coder is concurrently touching adjacent parts
   of the same email path; keeping the parameter (dead but harmless)
   avoids any risk of touching a file outside this task's scope or
   conflicting with concurrent work, at zero cost since Pull's own
   `limit` (`T02`) now bounds what gets staged in the first place.
2. **Verification (below) monkeypatched every Job function the compiled
   graph invokes (`classify_captured_email`, `thread_match_merge`,
   `route_to_project`, `detect_recurring_pattern`, `consult_librarian`),
   not only `classify_captured_email`, for all three staged emails —
   with exactly one fake raising for the targeted email.** T03's own diff
   never touches any Job's internal logic (that's `REQ-SB-55-US-01`,
   already `Done` and separately verified); what T03's own diff changes
   is purely the staging-boundary bookkeeping in
   `run_email_capture_pipeline`'s per-item loop. Routing all three
   synthetic, clearly-namespaced test emails through the REAL,
   unmonkeypatched Jobs would have made real Compass API calls and
   written real Thread/Customer-hub content into the live, real personal
   vault this project points at (`ensure_customer_hub_note` on whatever
   customer a real LLM call guessed for disposable test content,
   `route_to_project` creating a real Pending Approval, etc.) — a real
   risk to production vault data for zero additional confidence in THIS
   task's own diff. Deterministic fakes exercise the exact real code path
   under test (the REAL `_GRAPH.invoke`, the REAL `email_staging`/
   `vault_writer` calls) while keeping the test side-effect-free outside
   the staging/processed-ids boundary this task actually changed.

**`REQ-SB-69-US-01-AC-04` — verified live, PASS (all 16 checks passed, 0
failed).** Real verification against the real, configured backend venv
(`src/backend/.venv`) and the real, configured vault
(`VAULT_PATH=<OPERATOR_VAULT_OLD>`), per this task's own
`## Tests` steps 1-2, run directly via a one-off Python script (no live
`T02` Pull needed — three synthetic, clearly-namespaced staged emails
were created directly via `email_staging.stage_email`, per this task's
own steer that `T02`'s own Pull mechanism may not yet be wired when this
runs):
- **(a)** After run 1: the deliberately-failed email's own
  `.second-brain/email_staging/<id>/` directory still existed, and its
  `id` was NOT present in `vault_writer.load_processed_email_ids()` —
  PASS.
- **(b)** After run 1: both other emails' staged directories were gone
  (`remove_staged_email` fired) and both ids WERE present in
  `load_processed_email_ids()` — PASS.
- **(c)** The function's own returned `results` list contained exactly
  one honest `{"subject":..., "error":...}` entry (for the failed email)
  and exactly two normal success entries (for the other two) — PASS.
- **Test step 2 (retry):** re-ran `run_email_capture_pipeline()` a second
  time immediately, with the classify fake no longer raising for any id.
  The previously-failed email was still present in `list_staged_emails()`
  going into run 2, and completed successfully this time — its staged
  directory was removed and its id marked processed, with zero errors in
  the run-2 results for this batch — PASS. Confirms the retry path
  genuinely works, not just that the failed item was left alone.
- **Test step 3 (non-AC regression):** direct grep of
  `email_capture_pipeline.py`'s own top-level imports confirms no
  `outlook_com` reference remains as an import; `python -c "import
  app.business.pipelines.email_capture_pipeline"` (via the real venv)
  imports and compiles cleanly — PASS.
- **Test step 4 (non-AC regression):** `get_job_tree()` was called before
  and after this change; both returns are the same 6 Job ids
  (`classify`, `summarize_attachment`, `thread_match_merge`,
  `route_to_project`, `detect_recurring_pattern`, `consult_librarian`)
  with the same `depends_on` edges — the compiled graph is byte-identical
  in shape — PASS.

**Cleanup:** every artefact this verification created was removed —
`remove_staged_email` called for all three synthetic ids in a `finally`
block (idempotent even for the two already removed by the pipeline
itself), and `processed_email_ids.json` was rewritten back to exactly its
pre-run contents (the two synthetic ids added during the run were
excluded). Confirmed directly afterward: no `TEST-T03-*` entries remain
under `.second-brain/email_staging/` or in `processed_email_ids.json` —
the real vault carries no leftover test state, mirroring `T01`'s own
disclosed cleanup discipline. The pre-existing real staged directories
under `.second-brain/email_staging/` (three real GUID-named entries,
presumably `T02`'s own concurrent work) were left completely untouched.

**`REQ-SB-69-US-01-AC-01` (Scenario 1's structural half — "no downstream
`outlook_com` import") is NOT owned by this task** — the story's own
`## Decomposer Pass` AC → task mapping table places `AC-01` on `T04`
("the first task that `depends_on` both [`T02`,`T03`], guaranteeing both
halves are real by the time this is checked"). This task's own Test step
3 above independently re-confirms the `email_capture_pipeline.py`-half of
that structural check (no `outlook_com` import in this file) as a
non-AC regression check, per this task's own `## Tests` block — the
full Scenario-1 integration check spanning `T02`+`T03` together is
deferred to `T04`, as the story's own mapping table specifies.

gate: clear 2026-08-17 — no MUST-FLAG trigger fired: no material
assumption filling a genuine gap (both judgement calls above are
grounded, disclosed, scope-internal choices explicitly offered or implied
by this task's own text, not guesses among equally-valid readings with no
basis); no ADR/architecture change (this task builds directly against the
already-`Accepted` `ADR-046`); no `ESCALATIONS.md` entry; task not
oversized; the one locked AC this task owns (`AC-04`) was verified
directly and passed, with real on-disk evidence and full cleanup.
