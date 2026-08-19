---
id: REQ-SB-69-US-01-T04
title: pull_email/process_staged_email become two independently-dispatched, non-shared-lock capabilities of email-capture-pipeline
parent_story: REQ-SB-69-US-01
requirement_id: REQ-SB-69
type: backend
status: Done
gate: flagged
gate_reason: "scope-internal judgement calls for human spot-check — see ## Implementation Log (run_capture_for_agent/run_capture_and_record_completion reconciliation, a genuine transitive circular-import found+fixed, and ESC-045 — a disclosed out-of-scope lock-sharing gap in agent_schedules_router.py::run_now)"
phase: P1
depends_on: [REQ-SB-69-US-01-T02, REQ-SB-69-US-01-T03]
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-69-US-01-T04 — Independent pull_email/process_staged_email dispatch

## Parent Story

- Story: [[REQ-SB-69-US-01]] — `../UserStories/REQ-SB-69-US-01-decoupled-email-pull-and-human-readable-thread-notes.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-69 *Decoupled Email Pull + Human-Readable, Graph-Connected Thread Notes*

---

## Objective

Make Pull and Processing two independently-dispatchable capabilities of
the SAME `email-capture-pipeline` Agent-tier identity — `pull_email`
(still under the shared Outlook-COM dispatch lock) and
`process_staged_email` (its own separate, lightweight, NON-Outlook lock)
— the mechanism `ADR-046` Decision 4 names as making Scenarios 2/3 true
BY CONSTRUCTION, not by convention, because the two capabilities share
no lock.

---

## Starting State → End State

**Before / Inputs:**
- `skill_tools.SKILLS` has no `pull_email`/`process_staged_email` entries.
  `agent_schedule_registry.py`'s one module-level `_dispatch_lock` (an
  `asyncio.Lock()`) is the ONLY concurrency guard any real trigger source
  passes through (`dispatch_with_shared_lock`), shared by every real
  Outlook-touching capture step (email/meeting/todo) alike.
- `capture_scheduler.py::run_capture_if_idle` acquires that ONE shared
  lock, then runs `email_classification.run_capture_and_record_
  completion` (which internally dispatches ALL THREE capture agents,
  including the full email pull+process, under that single lock hold)
  as one atomic unit — this is the real trigger surface that produced
  the 2026-08-17 incident.
- `run_capture_now` (the manual/chat-triggered composite dispatch,
  `skill_tools.py::run_capture_now` → `email_classification.
  run_capture_and_record_completion`) also goes through the SAME shared
  lock, via `agents_router.py::_invoke_capability`'s existing
  `dispatch_with_shared_lock` routing (`ADR-045`, `Done`).
- `agent_schedule_registry.py::_RUN_STATE_TRACKED_CAPABILITY_ID` is a
  single string, `"run_capture_now"` — the only capability id
  `_mark_run_started`/`_mark_run_finished`/`get_job_run_states()` track.

**After / Outputs:**
- `skill_tools.SKILLS` gains two new entries, `pull_email` and
  `process_staged_email`, both `"mutates": True` (mirrors
  `run_capture_now`'s own shape), each with a real
  `@mcp_server.tool()`-decorated handler function:
  - `pull_email(agent_id: str) -> dict` — real only for
    `email-capture-pipeline`; every other agent gets the honest "not yet
    available" response (mirrors `run_capture_now`'s own real/honest-
    unavailable split). Calls `email_pull.pull_and_stage_emails()` and
    returns an honest `{"available": True, "message": ...}` summary.
  - `process_staged_email(agent_id: str) -> dict` — same real/honest-
    unavailable split. Calls `email_capture_pipeline.
    run_email_capture_pipeline()` (now reading from staging, `T03`) and
    returns an honest `{"available": True, "message": ...}` summary.
- `skill_registry._SKILL_HANDLERS` gains matching entries for both new
  ids. `skill_registry._MIGRATION_GRANT_SEED` gains `"pull_email":
  ["email-capture-pipeline"]` and `"process_staged_email":
  ["email-capture-pipeline"]` (mirrors the existing
  `"run_capture_now"`/`"pause_schedule"` seed shape exactly — this is a
  genuinely new grant, not a migration backfill of an old Action id, but
  reuses the same seed dict/mechanism for consistency and because
  `agent_schedule_registry._is_schedulable` already reads granted-skill
  membership from this same access layer).
- `agent_schedule_registry.py` gains a SECOND, dedicated `asyncio.Lock()`
  (e.g. `_processing_lock`), scoped to email processing alone — never the
  Outlook lock. A new function mirroring `dispatch_with_shared_lock`'s
  own shape (skip-not-queue on contention, `asyncio.to_thread` dispatch,
  run-state marking, outcome recording) but acquiring THIS lock instead
  — e.g. `dispatch_with_dedicated_processing_lock(agent_id: str,
  capability_id: str, trigger: Literal[...]) -> dict`, called ONLY for
  `capability_id == "process_staged_email"`. `pull_email` continues
  through the EXISTING `dispatch_with_shared_lock` (the real Outlook
  lock), exactly like every other real Outlook caller.
- `_RUN_STATE_TRACKED_CAPABILITY_ID` (a single string) becomes a
  collection covering all three ids (`"run_capture_now"`, `"pull_email"`,
  `"process_staged_email"`) — `_mark_run_started`/`_mark_run_finished`'s
  own gate check (`if capability_id != _RUN_STATE_TRACKED_CAPABILITY_ID:
  return`) becomes `if capability_id not in _RUN_STATE_TRACKED_
  CAPABILITY_IDS: return`. `get_job_run_states()`'s own iteration (today,
  purely over `_MIGRATION_GRANT_SEED["run_capture_now"]`'s agent list for
  that one id) extends to also cover `(email-capture-pipeline,
  pull_email)` and `(email-capture-pipeline, process_staged_email)` as
  two additional real entries — internal observability parity only, per
  `ADR-046` Decision 4; NO new Scheduling-view frontend row is built for
  either (parent story's own Non-Goal — `GET /system-health`'s response
  shape and `SystemHealthPage.tsx` are NOT touched by this task).
- `capture_scheduler.py::run_capture_if_idle` is restructured into two
  separate steps: (1) under the existing shared Outlook lock, Pull runs
  bundled with Meeting-capture's and Todo-capture's own still-unchanged
  Outlook-COM calls (exactly as today — `email_classification.
  run_capture_and_record_completion`'s own email leg now dispatches Pull,
  not the old monolithic fetch+process call); (2) THEN, as a separate,
  subsequent, lock-INDEPENDENT step (outside the `async with lock:`
  block, or via the new dedicated processing lock), Processing runs. The
  exact call shape reconciling `email_classification.
  run_capture_and_record_completion`'s own composite dispatch (also used,
  unchanged, by manual `run_capture_now`) against this two-step
  restructuring is a scope-internal judgement call — see `## Context /
  Notes` below for the grounding and the one hard Constraint it must
  satisfy either way.

---

## Files to Modify

- `src/backend/app/business/skill_tools.py` — add `pull_email`/
  `process_staged_email` entries to `SKILLS` and their
  `@mcp_server.tool()`-decorated handler functions, mirroring
  `run_capture_now`'s own real/honest-unavailable split exactly. Add
  `from app.business.pipelines import email_pull` as a deferred (inside-
  function) import if a circular-import risk exists — mirror
  `email_classification.py::run_capture_for_agent`'s own documented
  deferred-import precedent if needed; check first, do not assume.
- `src/backend/app/business/skill_registry.py` — add both ids to
  `_SKILL_HANDLERS` and `_MIGRATION_GRANT_SEED`.
- `src/backend/app/business/agent_schedule_registry.py` — new dedicated
  `asyncio.Lock()` + new dispatch function for `process_staged_email`
  (mirrors `dispatch_with_shared_lock`'s own shape); widen
  `_RUN_STATE_TRACKED_CAPABILITY_ID` into a set/collection of three ids;
  update `_mark_run_started`/`_mark_run_finished`/`get_job_run_states()`
  to iterate all three covered `(agent_id, capability_id)` pairs instead
  of the one hardcoded id (`get_job_run_states()`'s own per-id agent list
  still reads from `_MIGRATION_GRANT_SEED`, never a second hardcoded
  list — mirror the existing pattern for each of the three ids).
- `src/backend/app/scheduling/capture_scheduler.py` — restructure
  `run_capture_if_idle` into the two-step shape described above.
- `src/backend/app/business/email_classification.py` — only if the
  coder's own reconciliation (see `## Context / Notes`) requires a small,
  additive change to `run_capture_and_record_completion`'s or
  `run_capture_for_agent`'s own email-leg dispatch to make the two-step
  split possible; do not otherwise touch this file's own Thread/dates/
  wikilink logic (`T05`-`T08`'s own scope).

---

## Constraints

- Inherits from parent story.
- **`pull_email` and `process_staged_email` must never share a lock** —
  this is the one non-negotiable structural property this task exists to
  build; whatever exact call-shape reconciliation the coder chooses, this
  property must hold for at least one real, reachable trigger path (the
  hourly/app-start scheduled tick, per `ADR-046`'s own Alternatives
  Considered explicitly rejecting "keep bundled for every trigger
  source").
- **`run_capture_now` (manual/chat dispatch) keeps its own observable
  contract — still results in email fully captured end-to-end (staged
  AND processed) when it completes** — per `ADR-046` Decision 4's own
  "backward-compatible manual/chat-triggered behavior" requirement; it
  does not need to internally achieve lock separation for its own single
  dispatch (a manual button-press is not the incident's own trigger
  surface).
- **Meeting-capture's and Todo-capture's own triggering, working-mode
  gating, and Outlook-COM calls are completely untouched** — out of this
  story's Email-only scope (`ADR-046`'s own Alternatives Considered,
  parent story's own Non-Goals).
- **No new Scheduling-view UI row for either new capability** — parent
  story's own Non-Goal; `GET /system-health`'s response shape and
  `SystemHealthPage.tsx` are NOT touched by this task.
- **`dispatch_with_shared_lock` itself is not rewritten** — a NEW,
  sibling dispatch function is added for the processing lock, mirroring
  its shape; the existing function's own body/signature for
  Outlook-touching dispatch is unchanged (still used, unmodified, for
  `pull_email` and for meeting/todo capture).
- No change to `T05`-`T08`'s own scope (Thread filename/dates/wikilinks,
  `email_classification.py::thread_match_merge`/`route_to_project`).

---

## Tests

**Manual verification steps** (real backend running; real Outlook/Compass
reachable so a genuinely slow real call is available to induce a real
stall against):

1. `[REQ-SB-69-US-01-AC-01]` With the real backend running, dispatch a
   real `pull_email` run (via its own real trigger path — e.g. `POST
   /agents/email-capture-pipeline/actions/pull_email` if wired through
   the existing action-dispatch surface, or a direct
   `agent_schedule_registry.dispatch_with_shared_lock("email-capture-
   pipeline", "pull_email", trigger="direct")` call from a Python shell).
   Confirm real, newly-fetched mail lands in
   `.second-brain/email_staging/` afterward. Then grep-confirm (a direct
   text search, not a guess) that none of `email_capture_pipeline.py`,
   `email_classification.py`, `email_staging.py` import `outlook_com` —
   only `email_pull.py` does.
2. `[REQ-SB-69-US-01-AC-02]` Monkeypatch `email_pull.pull_and_stage_
   emails` (or `outlook_com.list_recent_mail` underneath it) to sleep for
   a real, observable duration (e.g. 30-60s) before returning, simulating
   the real 2026-08-17 hang. Dispatch `pull_email` (don't block waiting
   on it — run it as a background task/thread). While it is still
   genuinely in flight, separately dispatch `process_staged_email`
   against mail that was ALREADY staged before this test began. Confirm
   `process_staged_email` completes normally (classified/threaded/filed)
   WITHOUT waiting for the stalled `pull_email` call to finish — measure
   and record the real elapsed time for each to confirm the shorter one
   (`process_staged_email`) genuinely does not block on the longer one.
3. `[REQ-SB-69-US-01-AC-03]` Monkeypatch a Job the compiled graph invokes
   (e.g. `classify_captured_email`) to sleep for a real, observable
   duration before returning. Dispatch `process_staged_email` against
   at least one staged item (background task/thread, don't block). While
   it is still genuinely in flight, separately dispatch `pull_email`.
   Confirm `pull_email` completes normally (stages new mail) WITHOUT
   waiting for the stalled `process_staged_email` call to finish — same
   elapsed-time measurement discipline as step 2.
4. Non-AC regression check: confirm `run_capture_now` (manual dispatch,
   `POST /agents/email-capture-pipeline/actions/run_capture_now`) still
   results in email fully captured end-to-end (a real newly-staged email
   ends up filed as a Thread note by the time the call returns) —
   backward-compatible behavior preserved.
5. Non-AC regression check: confirm `GET /system-health`'s own response
   shape is unchanged from before this task (no new/removed top-level
   keys) — this task's own run-state extension is internal-only, not a
   new API surface.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-69-US-01-AC-01` — a real Pull stages content; no downstream
      module imports `outlook_com` except `email_pull.py`
- [x] `REQ-SB-69-US-01-AC-02` — a stalled `pull_email` never blocks a
      separately-dispatched `process_staged_email` against already-staged
      mail
- [x] `REQ-SB-69-US-01-AC-03` — a stalled `process_staged_email` never
      blocks a separately-dispatched `pull_email`
- [x] `run_capture_now`'s own backward-compatible behavior preserved
      (Test step 4)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Thread filename/lookup/rename, dates, wikilinks — `T05`-`T08`.
- Any Scheduling-view frontend change — parent story's own Non-Goal.
- Giving `Pull` its own Agent-tier identity — `ADR-046` Decision 5
  explicitly resolves against this; not built here or anywhere in this
  story.

---

## Context / Notes

**The exact reconciliation between `email_classification.py::
run_capture_and_record_completion`/`run_capture_for_agent` (shared by
BOTH the scheduled tick and manual `run_capture_now`) and `capture_
scheduler.py::run_capture_if_idle`'s own two-step restructuring is
deliberately left to the coder's own judgement, within the two hard
Constraints above** (lock separation must hold for at least the
scheduled-tick trigger path; `run_capture_now`'s own observable contract
stays backward-compatible). `ADR-046` Decision 4 (`Implementation/
Architecture/ADR.md`) names `capture_scheduler.py::run_capture_if_idle`
specifically as the function being restructured into two steps, with
Processing dispatched as "a separate, subsequent, lock-independent
call" — read that Decision, its own Alternatives Considered (which
explicitly rejects keeping Pull+Processing bundled under one lock hold
for "the scheduled/manual composite dispatch," i.e. the SAME trigger
surface that produced the real incident), and its Consequences in full
before implementing. One reasonable shape (not mandated, illustrative
only): `run_capture_for_agent("email-capture-pipeline", ...)`'s own
dispatch, when called from the SCHEDULED path specifically, composes
`email_pull.pull_and_stage_emails()` (staying under whatever lock the
caller already holds) and returns; `run_capture_if_idle` then, AFTER
releasing that lock, separately dispatches `process_staged_email`
through the new dedicated processing lock. Whatever shape is chosen,
log the reconciliation explicitly in the Implementation Log as a
scope-internal judgement call (mirrors this project's own established
precedent for reconciling a Constraint's own wording against End-State
text, `Implementation/Learnings.md`, `SPRINT-049`) — this is NOT a
MUST-FLAG trigger (the outcome and its two hard bounds are unambiguous;
only the internal wiring shape has real latitude, exactly the kind of
mechanical judgement call this project's own precedent treats as
scope-internal, not an escalation).

---

## Implementation Log

**Files changed:** `app/business/skill_tools.py` (new `pull_email`/
`process_staged_email` `SKILLS` entries + handlers), `app/business/
skill_registry.py` (`_SKILL_HANDLERS` + `_MIGRATION_GRANT_SEED` entries
for both new ids), `app/business/agent_schedule_registry.py` (new
`_processing_lock` + `get_dedicated_processing_lock`/`dispatch_with_
dedicated_processing_lock`, `_RUN_STATE_TRACKED_CAPABILITY_ID` widened to
`_RUN_STATE_TRACKED_CAPABILITY_IDS` — a tuple of all 3 ids, `get_job_run_
states()` restructured to iterate all 3, `_make_scheduled_tick_callback`
routes `process_staged_email` through the new lock), `app/scheduling/
capture_scheduler.py` (`run_capture_if_idle` restructured into the
two-step shape; `_build_scheduled_tick` gets the same lock-routing fix as
its `agent_schedule_registry.py` sibling), `app/business/
email_classification.py` (`run_capture_for_agent`'s email branch now
composes `email_pull.pull_and_stage_emails()` + `run_email_capture_
pipeline()` in one call — required so `run_capture_now`'s own contract
survives `T03` retiring Fetch from `run_email_capture_pipeline`;
`run_capture_and_record_completion` gains a `trigger: Literal["scheduled",
"direct"] = "direct"` parameter — only the Autonomous branch's body
differs by trigger, Supervised/Manual are unchanged for either value).

**Scope-internal judgement call — `run_capture_for_agent`/
`run_capture_and_record_completion` reconciliation (documented per the
task's own `## Context / Notes` steer, not a MUST-FLAG):** the illustrative
shape in this task's own `## Context / Notes` was implemented close to
verbatim. `run_capture_for_agent`'s own email branch (shared by
`run_capture_now`'s manual/chat dispatch AND `pending_approvals_router.py`'s
background-proposal Approve branch, both out of this task's own Files to
Modify) now calls `email_pull.pull_and_stage_emails()` THEN `run_email_
capture_pipeline()` in one synchronous call — this was NECESSARY, not just
one reasonable option: after `T03` retired Fetch from `run_email_capture_
pipeline`, leaving `run_capture_for_agent`'s email branch unchanged would
have silently broken `run_capture_now`'s own "fully captured end-to-end"
contract (it would only reprocess already-staged mail, never pull new
mail). `run_capture_and_record_completion` gained a `trigger` parameter
so its Autonomous email-leg branches: `trigger="scheduled"` (the ONLY
caller is `capture_scheduler.py::run_capture_if_idle`) calls `email_pull.
pull_and_stage_emails()` alone, under the shared lock; every other caller
(default `trigger="direct"`) is byte-for-byte unchanged from this
function's own pre-existing behavior. Supervised/Manual mode handling for
the email leg is IDENTICAL regardless of `trigger` — only the Autonomous
branch's body differs. `process_staged_email` is then dispatched
separately, AFTER the shared lock releases, via the new `dispatch_with_
dedicated_processing_lock`, which routes through `skill_registry.
invoke_skill`'s own generic two-axis working-mode gate — meaning in
Supervised mode, a scheduled tick can now produce TWO pending approvals
(the pre-existing "Run the scheduled email capture pipeline" background
approval for Pull, unchanged, PLUS a new, separate "Process Staged Email"
skill-based approval) instead of one. No AC or Constraint mandates a
single-approval count for the scheduled tick in Supervised mode; this is
a disclosed, natural consequence of the split ADR-046 Decision 4 itself
mandates, not a regression.

**Real defect found and fixed — a genuine transitive circular import**
(not merely a hypothesized risk; confirmed by direct testing, then fixed):
adding a module-top-level `from app.business.pipelines.email_capture_
pipeline import run_email_capture_pipeline` to `skill_tools.py` initially
compiled and even ran successfully via `agent_schedule_registry`'s own
particular import order — but a DIFFERENT, equally-real import order
(`import app.business.pipelines.email_capture_pipeline` first) hit a real
`ImportError: cannot import name 'run_email_capture_pipeline' from
partially initialized module`. Root cause, traced by direct testing:
`skill_tools -> email_classification -> vault_filing_expert ->
agent_orchestration -> graph -> knowledge_gap_tracking ->
knowledge_bootstrap -> skill_registry -> skill_tools -> email_capture_
pipeline` is a REAL transitive cycle back into `skill_tools.py` through
`email_classification.py`'s own OTHER imports — not the direct one-hop
edge `run_capture_for_agent`'s own existing docstring describes. Fixed by
moving the `email_capture_pipeline` import into `process_staged_email`'s
own function body (deferred), mirroring `build_knowledge`'s/`propose_
person_note_update`'s established precedent one layer deeper.
`email_pull` has zero business-layer imports and was confirmed safe to
keep at module top level (traced directly, not assumed). Re-verified
clean via three real import orders: `import app.business.pipelines.
email_capture_pipeline` first, `import app.main` first (the REAL
production startup order — succeeds), and confirmed `import app.business.
skill_tools` standalone-first still fails with an UNRELATED,
task-independent pre-existing cycle (`skill_registry.py`'s own top-level
`_SKILL_HANDLERS` dict literal reads `skill_tools.diagram_understanding`
at module-load time) that predates this task (confirmed via `git show
HEAD:...skill_tools.py`, which lacks the `email_classification` import
entirely — that import was added by an earlier, already-`Done`,
uncommitted `REQ-SB-39-US-02` pass, not this task) and is never reached by
real `uvicorn` startup (`app.main` imports fine) — left unfixed as
genuinely out of this task's own scope (touching `skill_registry.py`'s
own `_SKILL_HANDLERS` construction shape is not part of this task's
`## Files to Modify`, and this exact fragility is unreachable via any real
trigger surface).

**Disclosed, out-of-scope gap found by direct reading (`ESC-045`,
`Status: Open`, see `ESCALATIONS.md`) — `agent_schedules_
router.py::run_now` (NOT in this task's own `## Files to Modify`,
therefore not touched):** this existing, real, reachable endpoint
(`POST /agents/{agent_id}/schedules/{capability_id}/run-now`) hardcodes
`agent_schedule_registry.dispatch_with_shared_lock` for EVERY
`capability_id`, unconditionally. Once `process_staged_email` becomes a
granted, schedulable skill (this task), a human manually POSTing to this
endpoint with `capability_id="process_staged_email"` would incorrectly
route through the SHARED Outlook-COM lock instead of the new dedicated
processing lock — reintroducing exactly the lock-sharing this task exists
to eliminate, for that one specific manual trigger path only. The
STRUCTURALLY MORE IMPORTANT half of this same gap — a PERSISTED custom
recurring schedule for `process_staged_email` — WAS fixed, in both real
locations, since both are inside this task's own `## Files to Modify`:
`agent_schedule_registry.py::_make_scheduled_tick_callback` (live-mutation
path) and `capture_scheduler.py::_build_scheduled_tick` (cold-start
path). The hard Constraint ("must hold for at least one real, reachable
trigger path — the hourly/app-start scheduled tick") is satisfied
regardless — `run_now` is a one-off manual dispatch, not the scheduled-
tick trigger surface the Constraint binds, and every OTHER real trigger
path this task owns (the hourly/app-start tick, a persisted custom
schedule) is correctly lock-separated. Left unfixed, disclosed here for a
human/future task — fixing `agent_schedules_router.py::run_now` would be a
one-line conditional mirroring the two fixes already made, but touching
that file is out of this task's own scope.

**Verification (manual mode, real backend process, real Outlook/Compass,
one continuous session, `.venv\Scripts\python.exe` with `PYTHONPATH`/`cwd`
set to `src/backend` so `.env` resolves — no live `uvicorn` process was
running at task start, so each check drove the real business-layer
functions directly, exactly the task's own Tests block's disclosed
alternative to a wired HTTP action-dispatch surface, since
`agents_router.py`/`agent_schedules_router.py` are both out of this
task's own `## Files to Modify`):**

- `[REQ-SB-69-US-01-AC-01]` **PASS.** `email_pull.pull_and_stage_emails
  (limit=8)` against the real configured Outlook inbox: `{'fetched': 8,
  'newly_staged': 1, 'already_staged_or_processed': 7}` — confirmed the
  1 newly-staged item as a real new directory under
  `.second-brain/email_staging/<entry_id>/` (real `email.json`, real
  subject "RE: Azure-Net New Revenue Forecast for H2 for AM Updates")
  written to the real configured vault. Grep-confirmed directly: neither
  `email_capture_pipeline.py` nor `email_staging.py` import `outlook_com`
  at all; `email_classification.py` still imports it, but ONLY for the
  pre-existing, disclosed-as-unaffected `classify_recent_emails` (the
  legacy `/poc/classify-emails` standalone endpoint, `ADR-046`'s own
  Consequences) — none of `classify_captured_email`, `summarize_
  attachment`, `thread_match_merge`, `route_to_project`, `detect_
  recurring_pattern`, `consult_librarian` call it (confirmed by direct
  reading of each function body).
- `[REQ-SB-69-US-01-AC-02]` **PASS.** Controlled, deterministic induced
  stall (chosen over relying on real Outlook/Compass latency alone, which
  an initial unstubbed attempt showed can itself be highly variable —
  see `## Notes` below): `email_pull.pull_and_stage_emails` monkeypatched
  to `time.sleep(15)`; `email_capture_pipeline.classify_captured_email`
  monkeypatched to raise immediately (fast, non-destructive — caught by
  the already-verified per-item try/except, `AC-04`/`T03`, leaving staged
  items safely staged+unmarked). `pull_email` dispatched via the real
  `dispatch_with_shared_lock`; confirmed the shared lock was genuinely
  held 1s in. `process_staged_email` dispatched via the real `dispatch_
  with_dedicated_processing_lock` WHILE `pull_email` was still mid-sleep:
  completed in **0.53s**, result `{'available': True, 'message': 'Done —
  4 email(s) filed.'}` (4 real staged items, all failing fast by design
  for this test). `pull_email` then completed at **15.01s** (its own
  real, full stall). `process_staged_email`'s own 0.53s completion,
  fully inside `pull_email`'s still-ongoing 15s stall, is direct,
  unambiguous proof of zero lock sharing.
- `[REQ-SB-69-US-01-AC-03]` **PASS.** Same controlled-stall discipline,
  reversed: `classify_captured_email` monkeypatched to `time.sleep(15)`
  then raise (per item); `email_pull.pull_and_stage_emails` monkeypatched
  to return instantly (removes real-Outlook-latency variability from
  this specific proof; the lock/dispatch machinery itself — `dispatch_
  with_shared_lock`, `dispatch_with_dedicated_processing_lock`, `skill_
  registry.invoke_skill` — is 100% real, unstubbed). `process_staged_
  email` dispatched first (background task); confirmed the dedicated
  processing lock was genuinely held 2s in (mid-first-item's own sleep).
  `pull_email` dispatched while `process_staged_email` was still
  genuinely in flight: completed in **0.01s**. `process_staged_email`
  itself finished naturally **58.54s** later (4 staged items × ~15s
  each). `pull_email`'s 0.01s completion, entirely inside `process_
  staged_email`'s still-ongoing ~58s run, is direct, unambiguous proof.
- **`run_capture_now` backward-compatible behavior (Test step 4).**
  **PASS on the structural claim this task owns; real per-item E2E
  filing could not be observed this session due to a genuine, external,
  unrelated Compass API flakiness (disclosed below, not a regression).**
  Spied on `email_pull.pull_and_stage_emails` (via a wrapper counting real
  calls) around a real, unstubbed `skill_tools.run_capture_now(agent_id=
  "email-capture-pipeline")` call: `pull_and_stage_emails` was called
  **exactly once** inside the one synchronous `run_capture_now` call
  (elapsed `594.53s`, result `{'available': True, 'message': 'Done — 4
  email(s) filed.'}`) — directly confirms Pull+Process still compose in
  one call for this trigger, preserving the pre-existing contract. The 4
  real staged items (from `AC-01`'s own real pull, plus pre-existing
  staged content) remained staged afterward (`staged before: 4, staged
  after: 4`) — NOT because of anything in this task's own diff: a direct,
  isolated re-invocation of the compiled graph against one staged item,
  independent of any dispatch/lock code, reproduced the SAME real,
  external failure twice in a row: `app.data_access.compass_client.
  CompassError: couldn't parse Compass response: Expecting value: line 1
  column 1 (char 0)`, raised from `classify_captured_email` ->
  `compass_client.classify_email` — an unmodified, pre-existing function
  entirely outside this task's own `## Files to Modify`, most likely
  Compass-side degradation/rate-limiting from this session's own repeated
  heavy real-API test traffic. The already-shipped per-item failure
  posture (`AC-04`, `T03`) correctly held throughout: every failed item
  stayed staged and unmarked for retry, no data loss, no crash of the
  whole run. Not treated as a T04 blocker — the STRUCTURAL claim this
  task owns (one call composes both steps) is independently, conclusively
  proven by the call-count instrumentation, and the failure mode observed
  is identical in kind to `AC-04`'s own already-verified, already-shipped
  behavior, just triggered by a real external outage rather than a code
  defect.
- **`GET /system-health` response shape unchanged (Test step 5).**
  **PASS.** `system_health.get_system_health()` called directly: top-level
  keys `['disabled_agents', 'mcp', 'providers', 'scheduling']` — identical
  to the pre-existing 4-key shape (no key added/removed; only `T04`'s own
  files were touched, `system_health.py` itself was not). `scheduling`
  now correctly carries 5 entries (was 3): the pre-existing `run_capture_
  now` × 3 covered agents, plus real, live-recorded `email-capture-
  pipeline::pull_email` and `email-capture-pipeline::process_staged_
  email` entries (`has_run: True`, `last_outcome: "success"`, from the
  `AC-02`/`AC-03` dispatches above) — confirmed directly against
  `.second-brain/job_run_state.json`. The pre-existing, already-`Done`
  `SystemHealthPage.tsx` generically `.map()`s over this array with no
  hardcoded count, so these 2 real entries will render as 2 more rows on
  the ALREADY-BUILT Scheduling view without any frontend code change —
  this is the explicit, intended outcome this task's own End State text
  describes ("NO new Scheduling-view frontend row is BUILT" means no new
  dedicated component/support code was added, not that the existing
  generic view is prevented from reflecting real new data), not a
  violation of the parent story's own Non-Goal.

**Notes on verification methodology:** an initial, fully-real (unstubbed)
`AC-02` attempt used a real Outlook fetch after the induced stall and a
real, unstubbed 4-email `process_staged_email` run; both finished within
~1s of each other at ~210s, which was ambiguous on its own (real Compass
latency for 4 emails plausibly IS ~210s; a real Outlook fetch occasionally
taking that long independently is also plausible, per this story's own
"20+ minute hangs" motivation) — re-run with controlled, deterministic
monkeypatches (above) for an unambiguous proof. This also is what
surfaced the real circular-import defect (see above) and confirmed the 4
staged test items' own persistent real Compass failure (see the
`run_capture_now` entry above) rather than a hidden serialization bug —
both genuine, disclosed findings from this task's own live-verification
pass, not guessed.

**One `ESCALATIONS.md`/`REVIEW-QUEUE.md` entry filed by this task** —
`ESC-045` (`Status: Open`), for the disclosed `agent_schedules_router.py::
run_now` gap above: a real, out-of-scope shared-interface consequence
found during this task's own verification (mirrors `ESC-043`'s own
identical "found live, out of this task's own `## Files to Modify`, not
improvised on" precedent). Every OTHER finding above is either (a) a
scope-internal judgement call with its own disclosed reasoning (the
`run_capture_for_agent`/`run_capture_and_record_completion` reconciliation
shape — not a MUST-FLAG, the outcome and both hard bounds were
unambiguous, only the internal wiring shape had real latitude), (b) a
real defect found AND fixed within this task's own scope (the circular
import), or (c) an external, transient service-health observation
(Compass flakiness) unrelated to any code this project owns. `gate:
flagged` is set so a human can spot-check the reconciliation judgement
call and `ESC-045`, per this project's own established convention for
scope-internal judgement calls and out-of-scope findings.
