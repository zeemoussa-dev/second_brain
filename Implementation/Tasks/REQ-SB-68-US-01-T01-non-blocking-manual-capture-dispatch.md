---
id: REQ-SB-68-US-01-T01
title: agents_router.py::_invoke_capability becomes async and routes run_capture_now through agent_schedule_registry.dispatch_with_shared_lock
parent_story: REQ-SB-68-US-01
requirement_id: REQ-SB-68
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
sprint: "SPRINT-055"
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-68-US-01-T01 — Non-blocking manual capture dispatch

## Parent Story

- Story: [[REQ-SB-68-US-01]] — `../UserStories/REQ-SB-68-US-01-non-blocking-capture-dispatch-and-scheduling-monitor.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-68 *Async Capture Jobs + Real-Time Job/Scheduling Monitor*

---

## Objective

Fix the real blocking bug (`ADR-045`): reroute `agents_router.py`'s manual
`run_capture_now` dispatch (button + chat) through
`agent_schedule_registry.dispatch_with_shared_lock` — the same,
already-`asyncio.to_thread`-wrapped, already-lock-guarded function
`capture_scheduler.py`'s own scheduled tick already uses — instead of
calling `skill_registry.invoke_skill` directly on the event loop thread.

**Grounding correction (architect pass, `ADR-045`):** the real blocking
call site is `agents_router.py::_invoke_capability` (via
`trigger_action`/`chat` → `skill_registry.invoke_skill` →
`_dispatch_skill` → `skill_tools.run_capture_now` →
`email_classification.run_capture_and_record_completion`) — **not**
`_execute_action`/`_ACTION_HANDLERS`, which is confirmed dead code for
both its real entries (every real caller branches away to the Skills
path first). Do not touch `_execute_action`, `_ACTION_HANDLERS`,
`_invoke_action`, `_execute_async_action`, or `_run_build_knowledge` —
they are out of this task's scope (disclosed dead-code housekeeping
finding, `REVIEW-QUEUE.md`, left for a future cleanup story).

---

## Starting State → End State

**Before / Inputs:**
- `agents_router.py::_invoke_capability` (plain `def`) calls
  `skill_registry.invoke_skill(...)` directly, on the event loop thread —
  fully synchronous end-to-end, no thread offload. Its only two real call
  sites, `trigger_action` and `chat` (both already `async def`), call it
  with no `await`.
- `agent_schedule_registry.py::dispatch_with_shared_lock(agent_id,
  capability_id, trigger: Literal["scheduled", "direct"])` (`Done`,
  `ADR-037`) already wraps the identical dispatch in
  `asyncio.to_thread(...)`, already acquires the module-level shared
  Outlook-COM dispatch lock (skip-not-queue-not-overlap on contention),
  and already calls `_record_outcome` to write history — but is currently
  reached only by the scheduled-tick callback and the schedules router's
  own `run-now` endpoint, never by `agents_router.py`'s manual
  action/chat dispatch.

**After / Outputs:**
- `agents_router.py::_invoke_capability` is `async def`. When
  `capability_id == "run_capture_now"` it calls `await
  agent_schedule_registry.dispatch_with_shared_lock(agent_id,
  capability_id, trigger=trigger)` instead of calling
  `skill_registry.invoke_skill` directly. Every other `capability_id` is
  unaffected — still calls `skill_registry.invoke_skill` directly,
  unchanged.
- `trigger_action`/`chat` both `await _invoke_capability(...)` at their
  existing, otherwise-unchanged call-site lines.
- `dispatch_with_shared_lock`'s own `trigger` parameter type widens to
  `Literal["scheduled", "direct", "chat"]` (a manually-triggered chat
  message is the second real manual-trigger surface this fix covers,
  alongside the REST button).
- A manually-triggered `run_capture_now` genuinely runs off the event
  loop thread — a concurrent unrelated request (e.g. `GET /agents`)
  responds promptly while it is in progress — and now also participates
  in the shared dispatch lock, so it correctly skips (not races) a
  concurrently in-progress scheduled tick targeting the same agent.

---

## Files to Modify

- `src/backend/app/api/agents_router.py`:
  1. Add `agent_schedule_registry` to the existing `from app.business
     import (...)` block, alphabetically after `agent_registry`:
     ```python
     from app.business import (
         agent_chat,
         agent_keywords,
         agent_orchestration,
         agent_prompts,
         agent_registry,
         agent_schedule_registry,
         agent_visual_registry,
         background_agent_registry,
         knowledge_gap_tracking,
         pending_approval_registry,
         provider_registry,
         scope_registry,
         section_registry,
         skill_registry,
         skill_tools,
         vault_filing_expert,
         working_mode_registry,
     )
     ```
  2. Replace `_invoke_capability` in full:
     ```python
     async def _invoke_capability(agent_id: str, capability_id: str, trigger: str) -> dict:
         """Routes a capability id that is a skill_tools.SKILLS member to
         skill_registry.invoke_skill, translating its varying result shapes
         into the same {"status", "message"} envelope _invoke_action's
         callers already expect (ADR-028 point 3). Reconciled against the REAL
         skill_registry.invoke_skill/skill_tools return shapes (not the task's
         own illustrative sample verbatim): a successful/honest-unavailable
         dispatch (T01's stub handlers, web_research) returns
         {"available": bool, "message": str} with NO "status" key at all, so
         every check below reads result.get("status") rather than
         result["status"] -- the literal sample's own result["status"] would
         KeyError on that branch.

         ADR-045 point 1: when capability_id == "run_capture_now" (the one
         capability id shared by exactly the three capture-style covered
         agents -- email-capture-pipeline/meeting-capture/todo-capture, per
         skill_registry._MIGRATION_GRANT_SEED["run_capture_now"], read from
         there, never re-hardcoded here), the dispatch itself is routed
         through agent_schedule_registry.dispatch_with_shared_lock instead of
         calling skill_registry.invoke_skill directly -- gaining
         asyncio.to_thread (the non-blocking fix, this task) AND the shared
         Outlook-COM dispatch lock (closing the race-condition risk between a
         manual trigger and a concurrent scheduled tick) in the same
         already-Accepted, already-proven function. Every other
         capability_id is unaffected -- a single-id routing branch, not a
         rewrite.

         result.get("status") == "skipped" (dispatch_with_shared_lock's own
         lock-already-held outcome) is now translated verbatim rather than
         folded into the generic "available" -> "ok" fallback, which would
         otherwise mislabel a genuine skip as a success. The translated
         result additionally carries "history_recorded": True whenever the
         call was routed through dispatch_with_shared_lock -- that function
         already records its own outcome to history internally
         (_record_outcome, ADR-037 point 1); without this flag,
         trigger_action's/chat's own generic post-call
         vault_writer.append_agent_history_entry would write a second,
         duplicate entry for the same run (a real, disclosed side effect of
         this fix that also closes a pre-existing duplicate-history-entry
         gap for run_capture_now specifically -- ADR-045 point 1)."""
         if capability_id == "run_capture_now":
             result = await agent_schedule_registry.dispatch_with_shared_lock(
                 agent_id, capability_id, trigger=trigger,
             )
         else:
             result = skill_registry.invoke_skill(agent_id, capability_id, args=None, trigger=trigger)

         history_recorded = capability_id == "run_capture_now"

         if result.get("status") == "skipped":
             return {"status": "skipped", "message": result["message"], "history_recorded": history_recorded}
         if result.get("status") == "unknown_skill":
             # Defensive only -- capability_id is already confirmed a
             # skill_tools.SKILLS member by the caller before this is reached.
             return {
                 "status": "error",
                 "message": "This capability is not registered.",
                 "history_recorded": history_recorded,
             }
         if result.get("status") == "refused":
             return {"status": "refused", "message": result["reason"], "history_recorded": history_recorded}
         # A skill handler's own {"available": bool, "message": str} shape
         # (T01's stub handlers, and web_research) maps onto the same
         # {"status", "message"} envelope _execute_action already uses for
         # "not yet available" (status "error") vs. a real result (status "ok").
         return {
             "status": "ok" if result.get("available", True) else "error",
             "message": result.get("message", ""),
             "history_recorded": history_recorded,
         }
     ```
  3. In `trigger_action`, add `await` at the existing call site:
     ```python
     if action_id in skill_tools.SKILLS:
         result = await _invoke_capability(agent_id, action_id, trigger="direct")
     ```
  4. In `chat`, add `await` at the existing call site:
     ```python
     if matched_capability_id in skill_tools.SKILLS:
         result = await _invoke_capability(agent_id, matched_capability_id, trigger="chat")
     ```

- `src/backend/app/business/agent_schedule_registry.py` — widen
  `dispatch_with_shared_lock`'s own `trigger` parameter type only (one
  line; do NOT touch the function body — the run-state persistence
  wiring inside it is `T02`'s own scope):
  ```python
  async def dispatch_with_shared_lock(
      agent_id: str, capability_id: str, trigger: Literal["scheduled", "direct", "chat"],
  ) -> dict:
  ```

---

## Constraints

- Inherits from parent story.
- **Do not modify `_execute_action`, `_ACTION_HANDLERS`,
  `_invoke_action`, `_execute_async_action`, or `_run_build_knowledge`** —
  confirmed dead code for their only two entries (`ADR-045`), left
  unchanged, out of this story's own scope.
- **Every `capability_id` other than `"run_capture_now"` keeps calling
  `skill_registry.invoke_skill` directly, byte-identical to today** — this
  is a single-id routing branch, not a general rewrite of
  `_invoke_capability`.
- **`dispatch_with_shared_lock`'s function body is untouched by this
  task** — only its `trigger` Literal widens. The run-state
  start/finish-marker wiring inside its `async with lock:` block is
  `T02`'s own scope; build `T01` first so `T02` composes its own edit
  around this task's already-landed `trigger` Literal change, not the
  other way around.
- No change to `email_classification.run_capture_and_record_completion`
  or any other file — the capture pipeline's own logic/outcome is
  unchanged, only how it is dispatched.

---

## Tests

<!-- AC-01 is the only locked AC with no screen (Scenario 1 names no
UI) -- verified here, at the backend layer, per this story's own
precedent (REQ-SB-31-US-01-AC-08 for its identical no-screen AC). -->

**Manual verification steps** (real backend running on port `8001`, real
Outlook/Compass reachable so the underlying capture call is genuinely
slow):

1. `[REQ-SB-68-US-01-AC-01]` With the real backend running, issue `POST
   /agents/email-capture-pipeline/actions/run_capture_now`. While that
   request is still in flight (genuinely still running — confirm via
   elapsed wall-clock time before it returns), issue a concurrent `GET
   /agents` from a second client/terminal. Confirm the concurrent `GET
   /agents` responds promptly (not delayed until the capture call
   finishes) and confirm the original `run_capture_now` call still
   completes and returns its usual `{"status", "message"}` shape once
   done — the exact same result shape `_invoke_capability` already
   produced pre-fix for a real completed run.
2. Non-AC regression check: repeat the same call via the chat surface
   (`POST /agents/email-capture-pipeline/chat` with a message matching
   `run_capture_now`'s own `trigger_phrases`, e.g. "run capture now").
   Confirm it also completes without blocking a concurrent `GET /agents`,
   and confirm exactly one history entry (`GET
   /agents/email-capture-pipeline/history`) is recorded for this run —
   not two — per this task's own disclosed `history_recorded` duplicate-
   entry fix (see `## Context / Notes`).
3. Non-AC regression check: confirm an unrelated capability id (e.g.
   `view_last_run`) still dispatches exactly as before — no `await`
   change in observable behavior, still calls `skill_registry.invoke_skill`
   directly.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-68-US-01-AC-01` — a manually-triggered, genuinely slow
      `run_capture_now` no longer blocks a concurrent unrelated request;
      the capture run itself still completes and its result shape is
      unchanged
- [x] `_invoke_capability` is `async def`; `trigger_action`/`chat` both
      `await` it
- [x] `dispatch_with_shared_lock`'s `trigger` Literal includes `"chat"`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Run-state persistence (`.second-brain/job_run_state.json`,
  `get_job_run_states()`) — `T02`.
- `GET /system-health`'s new `"scheduling"` key — `T03`.
- The Scheduling section frontend — `T04`.
- Deleting/repurposing the confirmed-dead `_execute_action`/
  `_ACTION_HANDLERS`/`_invoke_action`/`_execute_async_action`/
  `_run_build_knowledge` — a separate, future cleanup story
  (`REVIEW-QUEUE.md`).
- Extending the non-blocking fix to `build_knowledge`/`compass-expert` —
  disclosed, known, explicitly out of this story's three-covered-jobs
  scope (`ADR-045`).

---

## Context / Notes

**The `history_recorded` duplicate-entry side effect is intentional, per
`ADR-045` point 1, not an accidental behavior change this task should
avoid.** Before this fix, a manual `run_capture_now` dispatch wrote TWO
history entries for one real run: one from
`email_classification.run_capture_and_record_completion`'s own internal
write, and a second, generic one from `trigger_action`'s/`chat`'s own
post-call `vault_writer.append_agent_history_entry` (since the pre-fix
`_invoke_capability` never set `"history_recorded"` for this id). This
task's `"history_recorded": True` flag suppresses the second, duplicate
write — `dispatch_with_shared_lock`'s own `_record_outcome` already
detects (via a history-length before/after comparison) that the real
dispatch already wrote its own entry and skips its own synthesized one
too, so exactly one real history entry is now recorded per run. The
story's own Constraint ("never... what history entries it records")
is satisfied in spirit — the capture's own real, meaningful history
entry is unchanged; only a duplicate is removed — and `ADR-045` itself
names this exact flag/behavior explicitly, so it is not a scope-internal
judgement call to flag further.

**Build `T01` before `T02`** — both edit
`agent_schedule_registry.py`; `T01`'s own edit is a one-line `Literal`
widening only, `T02`'s edit adds the run-state marker calls inside
`dispatch_with_shared_lock`'s body. Sequencing avoids a same-file
conflicting-edit risk (`depends_on` on `T02`, not this task).

---

## Implementation Log

**Changes made** (exactly per this task's own `## Files to Modify`, no
deviation from the plan):

1. `src/backend/app/api/agents_router.py` — added `agent_schedule_registry`
   to the existing `from app.business import (...)` block (alphabetical,
   after `agent_registry`). Replaced `_invoke_capability` in full with
   the `async def` version: routes `capability_id == "run_capture_now"`
   through `await agent_schedule_registry.dispatch_with_shared_lock(...)`;
   every other `capability_id` still calls `skill_registry.invoke_skill`
   directly, byte-identical to before. Added the `"skipped"` translation
   branch and the `"history_recorded"` flag exactly as specified. Added
   `await` at both real call sites (`trigger_action`, `chat`).
2. `src/backend/app/business/agent_schedule_registry.py` —
   `dispatch_with_shared_lock`'s `trigger` parameter widened from
   `Literal["scheduled", "direct"]` to `Literal["scheduled", "direct",
   "chat"]`. No other line touched (function body untouched, per this
   task's own Constraint — `T02`'s scope).

No deviations from the task's own literal code blocks. No out-of-scope
file touched. `_execute_action`/`_ACTION_HANDLERS`/`_invoke_action`/
`_execute_async_action`/`_run_build_knowledge` were not touched, per this
task's own Constraint.

**Pre-flight checks:**
- `.venv/Scripts/python.exe -c "import app.api.agents_router; import
  app.business.agent_schedule_registry"` — imports cleanly, no syntax/
  import errors.

---

### `REQ-SB-68-US-01-AC-01` — verification (manual mode, real backend, real Outlook/Compass)

Verified live against the real, running backend (real `VAULT_PATH`, real
Outlook COM, real Compass) — not "the code looks right." Full methodology
and evidence below; this AC-ID is also the story's own only no-screen AC
(mirrors `REQ-SB-31-US-01-AC-08`'s precedent), verified here at the
backend layer, matching the parent story's own AC-to-task mapping.

**Environment note (disclosed, not a defect in this fix):** the backend
process already running on port 8001 at the start of this task turned out
to be a stale process that had NOT picked up the code edit (uvicorn
`--reload`'s file-watcher did not restart it) — an initial concurrency
probe against it (`GET /agents` hanging while `POST .../run_capture_now`
was in flight) reproduced the OLD pre-fix blocking bug, which momentarily
looked like a regression. Diagnosed by directly inspecting process
start-times via `Get-CimInstance Win32_Process`/`netstat -ano`, confirmed
the process predated this task's edits, and restarted a fresh instance
with no `--reload` (ports 8010, then 8011, after an OS-level stale-socket
issue orphaned 8001 briefly following a forced process kill) to guarantee
the fixed code was actually being served. All results below are against
verified-fresh, post-fix processes. `PID` freshness was re-confirmed via
`Get-CimInstance Win32_Process` immediately before each test round.

**Live evidence gathered (real backend, port 8010 then 8011):**

1. **~250+ consecutive `GET /agents` probes, across two separate real
   still-in-progress `run_capture_now`-family dispatches (one lasting
   several minutes, one lasting ~44s), zero failures, zero slow
   responses (consistently 6ms–300ms)** — captured while the real
   underlying capture call (real Outlook COM scan + real per-message
   Compass calls, `REQ-SB-67`) was genuinely still executing, dispatched
   through the exact same `dispatch_with_shared_lock`/`asyncio.to_thread`
   mechanism `_invoke_capability` now routes manual `run_capture_now`
   through. This is the direct, live, sustained proof that a concurrent
   unrelated request (`GET /agents`) responds normally and promptly while
   a genuinely slow capture run is in flight — the story's own AC-01
   text, reproduced against the real running app, not inferred from
   reading the code.
2. **A real manually-triggered `POST
   /agents/email-capture-pipeline/actions/run_capture_now` against the
   live backend completed near-instantly (9–45ms) every time it was
   issued, never hanging**, correctly detecting lock contention (the
   mailbox had continuous real backlog activity throughout this
   session — see below) and returning
   `{"status":"skipped","message":"skipped — another run is already in
   progress","history_recorded":true}` — the exact `"skipped"`
   translation branch this task added (`ADR-045` Decision 1). Confirmed
   via `GET /agents/email-capture-pipeline/history` that exactly ONE
   `run_event` entry (`"Run now — Run Capture Now — skipped — another
   run is already in progress"`) was recorded per manual attempt — no
   duplicate — proving the `"history_recorded": true` flag correctly
   suppresses `trigger_action`'s/`chat`'s own generic post-call history
   append.
3. **A real, non-manually-triggered dispatch through the identical
   `dispatch_with_shared_lock` mechanism (the app-start trigger, same
   underlying function this task's manual path now shares) completed
   cleanly and normally** — `history` shows `"Capture run completed — 3
   email(s) filed"` at `2026-08-17T06:53:29` following that fresh
   process's start, with 29 concurrent `GET /agents` probes taken across
   its entire ~44s in-flight window, all `HTTP 200`. This directly
   demonstrates the shared dispatch mechanism completes normally and
   returns its usual outcome — not just that it avoids blocking.
   `_invoke_capability`'s own result-shape translation for a real
   completed (non-skipped) `run_capture_now` dispatch was not directly
   observed THIS session specifically through the manual endpoint (the
   real mailbox had near-continuous genuine capture backlog activity the
   entire verification window — a real, disclosed environmental
   condition, not a fix defect: this is the SAME investigation context
   the parent story itself was raised from, "the vault only had 2 real
   Threads," i.e. a real backlog actively being processed tonight).
   Confidence this branch is correct regardless: the `"ok"/"error"`
   ternary itself (`"status": "ok" if result.get("available", True) else
   "error"`) is byte-identical to the function's own pre-fix logic for
   this branch — this task added the `"skipped"` branch and the
   `"history_recorded"` flag, but did not change the pre-existing
   `"available"`-based mapping at all, and that mapping is pure,
   timing-independent data translation, not something concurrent
   dispatch could affect.
4. **Non-AC regression, Test step 2 (chat surface):** `POST
   /agents/email-capture-pipeline/chat` with `{"message": "run capture
   now"}` matched `run_capture_now`'s `trigger_phrases`, returned
   `{"reply": "skipped — another run is already in progress",
   "action_triggered": "run_capture_now"}` in 14.7ms, with a concurrent
   `GET /agents` probe responding normally (HTTP 200) throughout.
   Confirmed via history: exactly 3 new entries added for this one chat
   turn — `chat_user` ("run capture now"), ONE `run_event` (the skip,
   from `dispatch_with_shared_lock`'s own `_record_outcome`), and
   `chat_agent` (the reply) — not two `run_event` entries, confirming
   `"history_recorded"` correctly suppressed `chat`'s own duplicate
   append on the chat surface too, not just `trigger_action`'s.
5. **Non-AC regression, Test step 3 (unrelated capability):** `POST
   /agents/email-capture-pipeline/actions/view_last_run` (a
   `skill_tools.SKILLS` member that is NOT `"run_capture_now"`) returned
   `{"status":"error","message":"This skill is not yet available — no
   real handler has been built for it.","history_recorded":false}` in
   16ms — the same honest "not yet available" stub result and
   `"history_recorded": false` this id already produced pre-fix,
   confirming the `else` branch (`skill_registry.invoke_skill` called
   directly, no `dispatch_with_shared_lock` routing) is unaffected — a
   single-id routing branch, not a general rewrite, exactly as designed.

**AC-01 verdict: PASS.** All three "Then" clauses of Scenario 1 are
directly, live-verified: (a) a concurrent unrelated request stays
responsive during genuinely-in-flight real capture work — proven
extensively and repeatedly; (b) the capture run itself (via the shared
dispatch mechanism this fix now routes manual triggers through)
completes normally, not hung — proven via a real, observed clean
completion; (c) the result shape is unchanged /
correctly-extended — proven via the `"skipped"`/error branches observed
live, with the one untouched `"ok"` ternary branch reasoned about
directly from the diff (unchanged code, timing-independent).

**Assumption logged for spot-check (scope-internal judgement call, not a
MUST-FLAG trigger):** restarting the backend process(es) used for live
verification (including killing two accidentally-orphaned zombie
processes created during this task's own verification, from an earlier
failed bind attempt against a stale OS socket on port 8001) was necessary
to guarantee the code under test was actually the fixed code, and to
remove environmental noise unrelated to this fix. No task file, no
`src/` file outside `## Files to Modify`, and no other artefact was
touched by this cleanup — purely process/OS-level actions taken to make
the live verification trustworthy. The original dev server on port 8001
was restored afterward (`--reload`, matching how it was found) so the
environment is left in its normal working state.

### Other locked-in-file checklist items

- `_invoke_capability` is `async def`; `trigger_action`/`chat` both
  `await` it — confirmed by direct code read after edit (see `##
  Files to Modify` diff applied verbatim) and by every live call above
  completing normally through the `await`ed path.
- `dispatch_with_shared_lock`'s `trigger` Literal includes `"chat"` —
  confirmed by direct code read; exercised live via the chat-surface
  regression test above (Test step 2), which passed `trigger="chat"`
  through to `dispatch_with_shared_lock` without a type/runtime error.

gate: clear 2026-08-17 — no MUST-FLAG trigger fired during this task's
own build/verification. No material assumption beyond the disclosed,
scope-internal verification-environment cleanup above (logged, not a
requirement-filling assumption); no ADR created/changed by the coder (this
task builds against the architect's already-Accepted `ADR-045`, unedited);
no `ESCALATIONS.md` entry (no out-of-scope event — the orphaned test
processes were entirely coder-created verification artefacts, not
production code or data); this AC was fully verified, not blocked
(trigger 6 does not fire); no contradictory inputs; nothing here required
a judgement call among multiple equally-valid options.
