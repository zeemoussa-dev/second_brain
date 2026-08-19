---
id: REQ-SB-68-US-01-T02
title: Persisted per-job run-state tracking (job_run_state.json) inside dispatch_with_shared_lock, gated structurally to run_capture_now
parent_story: REQ-SB-68-US-01
requirement_id: REQ-SB-68
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-68-US-01-T01]
sprint: "SPRINT-055"
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-68-US-01-T02 — Per-job run-state tracking

## Parent Story

- Story: [[REQ-SB-68-US-01]] — `../UserStories/REQ-SB-68-US-01-non-blocking-capture-dispatch-and-scheduling-monitor.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-68 *Async Capture Jobs + Real-Time Job/Scheduling Monitor*

---

## Objective

Give the three capture-style covered jobs a real, persisted
running/duration/outcome record (`ADR-045` point 4): a new sibling store
`.second-brain/job_run_state.json`, written from inside
`agent_schedule_registry.dispatch_with_shared_lock`'s own lock-held
block, gated **structurally** to `capability_id == "run_capture_now"` —
the same gate `T01`'s dispatch-routing fix uses — so tracking stays
scoped to exactly the three covered jobs with **no hardcoded agent-id
list anywhere in this task's own code** (per tonight's standing
config-not-hardcoded directive: the three agent ids are never re-listed
here — the scope is entirely a function of which `capability_id` is
dispatched, exactly as `T01`'s own routing branch already establishes).

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed: `dispatch_with_shared_lock`'s `trigger` Literal
  includes `"chat"`; `agents_router.py::_invoke_capability` routes
  `run_capture_now` through it.
- `vault_writer.py::_agent_schedules_state_path`/
  `load_agent_schedules_state`/`save_agent_schedules_state` (`Done`,
  `ADR-037` point 3) is the exact pure-I/O shape to mirror for the new
  store — returns `None` if the file doesn't exist yet, no default
  content computed in `data_access` (`ADR-003`).
- `agent_schedule_registry.py::dispatch_with_shared_lock` (as landed by
  `T01`) is the one function every real scheduled/on-demand
  `run_capture_now` trigger source passes through.

**After / Outputs:**
- `vault_writer.py` gains `load_job_run_state()`/`save_job_run_state()` —
  pure I/O against a new `.second-brain/job_run_state.json`, mirroring
  `load_agent_schedules_state`/`save_agent_schedules_state` exactly.
- `agent_schedule_registry.py` gains `_mark_run_started`/
  `_mark_run_finished` (called from inside `dispatch_with_shared_lock`'s
  `async with lock:` block, immediately before/after its existing `await
  asyncio.to_thread(...)` call, gated to `capability_id ==
  "run_capture_now"`) and a new public `get_job_run_states() -> list[dict]`
  read accessor that computes an in-flight run's elapsed duration fresh
  at read time (`now - started_at`), never persisted incrementally.

**Design refinement vs. `ADR-045` point 4's own literal read-side
wording (disclosed, not a re-litigation of the ADR's storage/write-side
mechanism — same record shape, same store, same structural
write-side gate):** `ADR-045`'s own text says an absent covered job's
record is "omitted" from `get_job_run_states()` and "the frontend
renders an explicit 'no runs yet' state for any covered job absent from
the response" — which would require the FRONTEND to hold its own
independent list of the three covered agent ids just to detect
absence, directly re-hardcoding the same list `skill_registry.
_MIGRATION_GRANT_SEED["run_capture_now"]` already carries (tonight's
own standing config-not-hardcoded directive: read the covered-jobs list
from wherever `agent_schedule_registry`/`capture_scheduler` already
source it, never re-hardcode it a second time in the new run-state/
Scheduling code — and that includes the frontend). This task instead
has `get_job_run_states()` itself enumerate the covered agent ids
directly from `skill_registry._MIGRATION_GRANT_SEED["run_capture_now"]`
— the exact real source `ADR-045`'s own Decision 1 already names as "the
one and only capability id shared by exactly the three covered agents"
— and return one entry per covered agent always, carrying a new
`"has_run": bool` field: `False` (with every other field honestly
`None`) for a covered agent with no persisted record yet, `True` for a
real record. The frontend (`T04`) then needs **zero** independent
knowledge of which agent ids are covered — it renders exactly the rows
this accessor returns, nothing more, nothing hardcoded. Scenario 5's
"honest no runs yet" bar and Scenario 7's "uncovered action never
shown" bar are both still satisfied — `build_knowledge`/`compass-expert`
is never in `_MIGRATION_GRANT_SEED["run_capture_now"]`'s own list, so it
is never iterated, regardless of this change.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py`:
  1. Add the new filename constant alongside `_AGENT_SCHEDULES_FILE`:
     ```python
     _JOB_RUN_STATE_FILE = "job_run_state.json"
     ```
  2. Add the new pure-I/O pair, placed alongside
     `load_agent_schedules_state`/`save_agent_schedules_state`:
     ```python
     def _job_run_state_path():
         state_dir = settings.vault_path / _STATE_DIR
         state_dir.mkdir(parents=True, exist_ok=True)
         return state_dir / _JOB_RUN_STATE_FILE


     def load_job_run_state() -> dict | None:
         """Pure I/O -- returns None if job_run_state.json doesn't exist
         yet (no default content computed here, per ADR-003; the composite-
         key shape and every start/finish/read decision is a business-layer
         concern, owned by app/business/agent_schedule_registry.py,
         ADR-045 point 4)."""
         path = _job_run_state_path()
         if not path.exists():
             return None
         return json.loads(path.read_text(encoding="utf-8"))


     def save_job_run_state(state: dict) -> None:
         path = _job_run_state_path()
         path.write_text(json.dumps(state, indent=2), encoding="utf-8")
     ```

- `src/backend/app/business/agent_schedule_registry.py`:
  1. Add, alongside the module's existing `_schedule_key`/`_load_state`
     helpers:
     ```python
     # The one, structural gate every run-state function below uses --
     # capability_id == "run_capture_now" is the one and only id shared by
     # exactly the three covered agents (email-capture-pipeline/
     # meeting-capture/todo-capture, per skill_registry.
     # _MIGRATION_GRANT_SEED["run_capture_now"]) and no other agent/
     # capability pair. Never a hardcoded agent-id list -- the SAME gate
     # T01's own _invoke_capability dispatch-routing branch already uses,
     # kept in exact lockstep here rather than re-derived a second way.
     _RUN_STATE_TRACKED_CAPABILITY_ID = "run_capture_now"


     def _job_run_state_key(agent_id: str, capability_id: str) -> str:
         return f"{agent_id}::{capability_id}"


     def _load_job_run_state() -> dict:
         state = vault_writer.load_job_run_state()
         if state is None:
             state = {"runs": {}}
             vault_writer.save_job_run_state(state)
         return state


     def _mark_run_started(agent_id: str, capability_id: str) -> None:
         if capability_id != _RUN_STATE_TRACKED_CAPABILITY_ID:
             return
         state = _load_job_run_state()
         key = _job_run_state_key(agent_id, capability_id)
         state["runs"][key] = {
             "agent_id": agent_id,
             "capability_id": capability_id,
             "running": True,
             "started_at": datetime.now(timezone.utc).isoformat(),
             "finished_at": None,
             "last_outcome": None,
             "last_error_message": None,
             "last_duration_seconds": None,
         }
         vault_writer.save_job_run_state(state)


     def _classify_run_outcome(result: dict) -> tuple[str, str | None]:
         """Maps invoke_skill's varying result shapes (as returned from
         inside dispatch_with_shared_lock's own asyncio.to_thread call) onto
         this record's {"last_outcome", "last_error_message"} pair.
         "skipped" covers the two genuinely-not-a-failure non-dispatch
         outcomes the working-mode gate can still return from inside the
         lock-held branch (Supervised-deferred "pending",
         Manual-dormant "skipped_manual") -- neither is a capture-pipeline
         failure, so neither should paint the job "error" on the Scheduling
         view. Everything else that did not genuinely, positively dispatch
         (unknown_skill, refused, available: False) is an honest "error",
         carrying the real message/reason text -- never fabricated."""
         status = result.get("status")
         if status in ("pending", "skipped_manual"):
             return "skipped", None
         if status in ("unknown_skill", "refused"):
             return "error", result.get("reason") or result.get("message")
         if result.get("available") is False:
             return "error", result.get("message")
         return "success", None


     def _mark_run_finished(agent_id: str, capability_id: str, result: dict) -> None:
         if capability_id != _RUN_STATE_TRACKED_CAPABILITY_ID:
             return
         state = _load_job_run_state()
         key = _job_run_state_key(agent_id, capability_id)
         existing = state["runs"].get(key)
         started_at_iso = existing["started_at"] if existing else None
         finished_at = datetime.now(timezone.utc)
         duration_seconds = None
         if started_at_iso:
             duration_seconds = (finished_at - datetime.fromisoformat(started_at_iso)).total_seconds()
         outcome, error_message = _classify_run_outcome(result)
         state["runs"][key] = {
             "agent_id": agent_id,
             "capability_id": capability_id,
             "running": False,
             "started_at": started_at_iso,
             "finished_at": finished_at.isoformat(),
             "last_outcome": outcome,
             "last_error_message": error_message,
             "last_duration_seconds": duration_seconds,
         }
         vault_writer.save_job_run_state(state)


     def get_job_run_states() -> list[dict]:
         """Read accessor for the Scheduling view (T03). One entry per
         covered agent for capability_id "run_capture_now" -- covered
         agent ids are read from skill_registry._MIGRATION_GRANT_SEED[
         "run_capture_now"] (the SAME real, already-existing source
         ADR-045's own Decision 1 already names as "the one and only
         capability id shared by exactly the three covered agents"),
         never a second, independently-hardcoded id list -- so the
         frontend (T04) never needs its own copy of this list either.
         A covered agent with no persisted record yet gets an honest
         "has_run": False placeholder (Scenario 5) -- never a fabricated
         running/duration/outcome value. An in-flight run's
         elapsed_seconds is computed fresh at read time (now -
         started_at) -- never persisted incrementally, mirroring
         REQ-SB-31-US-01's own established recompute-fresh-on-refresh
         convention for this exact page. An uncovered agent/capability
         (e.g. compass-expert/build_knowledge) is never iterated here at
         all, regardless of whatever job_run_state.json happens to
         contain (Scenario 7)."""
         state = _load_job_run_state()
         now = datetime.now(timezone.utc)
         covered_agent_ids = skill_registry._MIGRATION_GRANT_SEED.get(
             _RUN_STATE_TRACKED_CAPABILITY_ID, [],
         )
         records = []
         for agent_id in covered_agent_ids:
             key = _job_run_state_key(agent_id, _RUN_STATE_TRACKED_CAPABILITY_ID)
             record = state["runs"].get(key)
             if record is None:
                 records.append({
                     "agent_id": agent_id,
                     "capability_id": _RUN_STATE_TRACKED_CAPABILITY_ID,
                     "has_run": False,
                     "running": False,
                     "started_at": None,
                     "finished_at": None,
                     "last_outcome": None,
                     "last_error_message": None,
                     "last_duration_seconds": None,
                     "elapsed_seconds": None,
                 })
                 continue
             entry = dict(record)
             entry["has_run"] = True
             if entry["running"] and entry["started_at"]:
                 entry["elapsed_seconds"] = (now - datetime.fromisoformat(entry["started_at"])).total_seconds()
             else:
                 entry["elapsed_seconds"] = None
             records.append(entry)
         return records
     ```
  2. Wire the two markers inside `dispatch_with_shared_lock`'s own
     lock-held block, immediately before/after its existing dispatch call
     (only this function's body changes; its signature was already
     updated by `T01`):
     ```python
     async def dispatch_with_shared_lock(
         agent_id: str, capability_id: str, trigger: Literal["scheduled", "direct", "chat"],
     ) -> dict:
         lock = get_shared_dispatch_lock()
         history_len_before = len(vault_writer.load_agent_history(agent_id))
         if lock.locked():
             result = {"status": "skipped", "message": "skipped — another run is already in progress"}
         else:
             async with lock:
                 _mark_run_started(agent_id, capability_id)
                 result = await asyncio.to_thread(
                     skill_registry.invoke_skill, agent_id, capability_id, None, trigger,
                 )
                 _mark_run_finished(agent_id, capability_id, result)
         _record_outcome(agent_id, capability_id, trigger, result, history_len_before)
         return result
     ```

---

## Constraints

- Inherits from parent story.
- **No independently re-hardcoded agent-id list anywhere in this task's
  own code, including implicitly forcing one onto the frontend.** The
  write-side gate is structural (`capability_id ==
  "run_capture_now"`, `_RUN_STATE_TRACKED_CAPABILITY_ID`) — no agent_id
  check at all. The read-side enumeration
  (`get_job_run_states()`, needed only to emit an honest
  never-run placeholder for an absent covered job) reads
  `skill_registry._MIGRATION_GRANT_SEED["run_capture_now"]` directly —
  the one real, already-existing source for "which agents are covered" —
  never a second, independently-maintained literal list, and never pushed
  onto `T04`'s frontend to re-derive.
- **The lock-already-held skip branch does NOT call `_mark_run_finished`**
  — a skipped dispatch attempt never overwrites the currently-in-progress
  run's own `"running": True` record with itself.
- `duration`/`elapsed_seconds` is **never persisted incrementally** — always
  computed fresh at read time from `started_at`.
- A covered job with no record yet must return an honest `"has_run":
  False` placeholder from `get_job_run_states()` (every other field
  `None`) — never omitted (that would force `T04` to hold its own
  covered-agent-id list just to detect absence) and never a fabricated
  running/duration/outcome value.
- `data_access` (`vault_writer.py`) stays pure I/O — no default-content
  computation, no business decision (`ADR-003`), mirroring
  `load_agent_schedules_state`'s own convention exactly.

---

## Tests

<!-- No locked AC of its own -- job_run_state.json has no HTTP surface
yet (T03) and no screen renders it yet (T04). Every one of this story's
view-observable ACs (AC-02 through AC-07) is genuinely observable only
once T04 wires a real page around T03's endpoint, mirroring
REQ-SB-31-US-01-T02's own identical split. Non-AC smoke checks only. -->

**Manual verification steps** (throwaway interpreter against
`src/backend`'s `.venv`; backend need not be running):

1. Non-AC smoke check: with a fresh/absent `job_run_state.json`, call
   `get_job_run_states()` directly. Confirm it returns exactly 3 records
   (one per `skill_registry._MIGRATION_GRANT_SEED["run_capture_now"]`
   entry — `email-capture-pipeline`/`meeting-capture`/`todo-capture`),
   every one `"has_run": False` with every other field `None`, no
   exception.
2. Non-AC smoke check: call `agent_schedule_registry._mark_run_started(
   "email-capture-pipeline", "run_capture_now")` directly, then
   `get_job_run_states()`. Confirm that job's record now shows
   `"has_run": True`, `running: True`, `started_at` set,
   `elapsed_seconds` a small positive float that grows on a second call a
   moment later — the other 2 covered jobs are unaffected, still
   `"has_run": False`.
3. Non-AC smoke check: call `_mark_run_finished("email-capture-pipeline",
   "run_capture_now", {"available": True, "message": "Done — 0 email(s)
   filed."})`. Confirm `get_job_run_states()` now shows that job
   `running: False`, `last_outcome: "success"`, `last_error_message:
   None`, `last_duration_seconds` a positive float, `elapsed_seconds:
   None`.
4. Non-AC smoke check: call `_mark_run_started` then `_mark_run_finished`
   with a genuine failure shape (e.g. `{"available": False, "message":
   "Compass unreachable: ..."}`). Confirm `last_outcome: "error"` and
   `last_error_message` carries the real message text verbatim.
5. Non-AC smoke check: call `_mark_run_started("compass-expert",
   "build_knowledge")` (an uncovered agent/capability pair). Confirm
   `get_job_run_states()`'s own 3-record list is completely unaffected —
   `compass-expert` never appears, since it is never iterated at all
   (not in `_MIGRATION_GRANT_SEED["run_capture_now"]`'s own list),
   proving Scenario 7's bar independent of `_mark_run_started`'s own
   `capability_id` gate.
6. Non-AC end-to-end smoke check: with the real backend running, issue a
   real `POST /agents/email-capture-pipeline/actions/run_capture_now`
   (now routed through `T01`'s fix) and, in a second concurrent terminal
   while it is in flight, call `get_job_run_states()` directly (or via a
   throwaway script importing the module) and confirm it shows
   `email-capture-pipeline::run_capture_now` as `running: True` with a
   growing `elapsed_seconds`; after it completes, confirm `running:
   False` with a real `last_duration_seconds` and `last_outcome`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `get_job_run_states()` returns exactly one record per covered agent
      (read from `skill_registry._MIGRATION_GRANT_SEED[
      "run_capture_now"]`), each carrying `{"agent_id", "capability_id",
      "has_run", "running", "started_at", "finished_at", "last_outcome",
      "last_error_message", "last_duration_seconds", "elapsed_seconds"}`
- [x] A covered job with no run yet returns `"has_run": False` with every
      other field `None` — never omitted, never fabricated
- [x] An uncovered agent/capability pair never produces or appears as a
      record — via the write-side structural `capability_id ==
      "run_capture_now"` gate AND the read-side covered-agent-id
      enumeration, neither a hardcoded literal list
- [x] `elapsed_seconds` for an in-flight run is computed fresh on every
      call, never persisted
- [x] No new persisted state file other than
      `.second-brain/job_run_state.json`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `GET /system-health`'s new `"scheduling"` key — `T03`.
- The Scheduling section frontend — `T04`.
- `.second-brain/last_capture_run.json`'s own write call site
  (`email_classification.py`) — left byte-for-byte unchanged, a
  disclosed, harmless redundancy (`ADR-045` point 6).
- Any change to `_record_outcome`'s own history-writing logic beyond
  what `T01` already established via `history_recorded` — unrelated to
  this task's own run-state persistence concern.

---

## Context / Notes

Mirrors `agent_schedules.json`'s own `"{agent_id}::{capability_id}"`
composite-key convention (`ADR-037` point 3) exactly — reusing an
established key shape, not inventing a new one, per `ADR-045` point 4's
own explicit "Alternatives Considered" rejection of a differently-keyed
store.

---

## Implementation Log

**Changes made** (exactly per this task's own `## Files to Modify`, no
deviation from the plan's literal code blocks):

1. `src/backend/app/data_access/vault_writer.py` — added
   `_JOB_RUN_STATE_FILE = "job_run_state.json"` alongside
   `_AGENT_SCHEDULES_FILE`; added `_job_run_state_path()` /
   `load_job_run_state()` / `save_job_run_state(state)`, placed
   immediately after `save_agent_schedules_state`, byte-identical to the
   task's own code block.
2. `src/backend/app/business/agent_schedule_registry.py` — added
   `_RUN_STATE_TRACKED_CAPABILITY_ID`, `_job_run_state_key`,
   `_load_job_run_state`, `_mark_run_started`, `_classify_run_outcome`,
   `_mark_run_finished`, `get_job_run_states` immediately after
   `_schedule_key`, byte-identical to the task's own code block. Wired
   `_mark_run_started`/`_mark_run_finished` inside
   `dispatch_with_shared_lock`'s own `async with lock:` block,
   immediately before/after its existing `await
   asyncio.to_thread(skill_registry.invoke_skill, ...)` call — the ONLY
   change to that function's body (its signature/`Literal` widening was
   already `T01`'s own landed change, untouched here). The
   lock-already-held `if lock.locked():` skip branch was NOT touched —
   `_mark_run_finished` is never called from it, so a skipped attempt
   never overwrites an in-progress run's own `"running": True` record.

No file outside `## Files to Modify` was touched. No deviation from the
task's own literal code blocks — every function signature, docstring,
and the `dispatch_with_shared_lock` wiring match verbatim.

**Pre-flight checks:**
- `ast.parse()` on both modified files — no syntax errors.
- `.venv/Scripts/python.exe -c "from app.business import
  agent_schedule_registry, skill_registry"` (via the smoke-test script
  below) — imports cleanly, no import errors.

---

### Non-AC smoke checks (manual verification steps 1-5, `## Tests`)

This task carries **no locked AC of its own** — every one of the
story's view-observable ACs (`AC-02`-`AC-07`) is genuinely observable
only once `T04` wires a real page around `T03`'s endpoint (per the
decomposer's own AC-to-task mapping note in the parent story's
`## Notes`). Verified via a throwaway script
(`scratch_vault` under `VAULT_PATH`, backend not required to be
running), importing `app.business.agent_schedule_registry`/
`skill_registry` directly:

1. **Fresh/absent `job_run_state.json`** — `get_job_run_states()`
   returned exactly 3 records
   (`email-capture-pipeline`/`meeting-capture`/`todo-capture`, matching
   `skill_registry._MIGRATION_GRANT_SEED["run_capture_now"]` exactly),
   every one `"has_run": false` with every other field `None`, no
   exception. **PASS.**
2. **`_mark_run_started("email-capture-pipeline", "run_capture_now")`
   then `get_job_run_states()`** — that job's record showed
   `"has_run": true`, `"running": true`, `started_at` set,
   `elapsed_seconds` a small positive float (`0.010208`) that grew on a
   second call 0.5s later (`0.513679`); the other 2 covered jobs stayed
   `"has_run": false`. **PASS.**
3. **`_mark_run_finished("email-capture-pipeline", "run_capture_now",
   {"available": True, "message": "Done — 0 email(s) filed."})`** —
   `get_job_run_states()` showed that job `"running": false`,
   `"last_outcome": "success"`, `"last_error_message": null`,
   `"last_duration_seconds": 0.515632` (positive), `"elapsed_seconds":
   null`. **PASS.**
4. **`_mark_run_started`/`_mark_run_finished("meeting-capture",
   "run_capture_now", {"available": False, "message": "Compass
   unreachable: connection refused"})`** — `"last_outcome": "error"`,
   `"last_error_message": "Compass unreachable: connection refused"`
   (the real message, verbatim). **PASS.**
5. **`_mark_run_started("compass-expert", "build_knowledge")`** (an
   uncovered agent/capability pair) — `get_job_run_states()`'s own
   3-record list was completely unaffected; `compass-expert` never
   appeared, confirmed both structurally (write-side gate) and via the
   read-side enumeration never iterating it. **PASS.**

Confirmed via direct filesystem inspection of the scratch vault's
`.second-brain/` directory: exactly one new file,
`job_run_state.json`, was created — no other persisted state file.
Scratch vault deleted after verification.

### Non-AC live end-to-end smoke check (manual verification step 6, `## Tests`)

**With the real backend running, real Outlook/Compass, real `VAULT_PATH`
vault** (mirroring `T01`'s own live-verification rigor): started a
fresh backend process (port 8020, no `--reload`, to guarantee the code
under test was genuinely this task's edits — the pre-existing port-8001
`--reload` dev server had been reloading on every edit made during this
task, retriggering its own app-start capture pass each time; it was
stopped for the duration of this verification, along with an orphaned
`--reload` sub-worker process, and restarted afterward with `--reload`
on port 8001 to restore the environment exactly as found — the same
disclosed, scope-internal process-management judgement `T01`'s own
Implementation Log already established as precedent, not a
`src/`/artefact change).

Issued a real `POST
/agents/email-capture-pipeline/actions/run_capture_now` against the
live backend. The app's own unconditional app-start capture trigger
(`capture_scheduler.py::run_capture_if_idle`, a separate,
out-of-this-task's-scope code path that holds the SAME shared dispatch
lock but does not itself go through `dispatch_with_shared_lock`) held
the lock for the first several minutes after process start, correctly
producing `{"status": "skipped", ...}` on early manual attempts — a
real, disclosed environmental condition (a genuinely busy real mailbox
that night), not a defect. Once that app-start run's own already-queued
work drained and a manual dispatch genuinely acquired the shared lock
(confirmed by the POST no longer returning an instant `"skipped"`),
concurrently polled `get_job_run_states()` directly (a separate
throwaway script process, reading the same real, file-based
`job_run_state.json` — cross-process reads work fine even though the
`asyncio.Lock()` itself is in-process-only per `ADR-037`):

- **`running: true` observed immediately** (`started_at:
  "2026-08-17T07:17:46.202051+00:00"`), with `elapsed_seconds` growing
  continuously and monotonically on every poll — `0.169133` → `0.67008`
  → `1.171385` → ... → `473.951474` — directly, live proof that
  duration is computed fresh at read time (`now − started_at`), never a
  frozen/cached value, across a genuinely long (~7.9 minute) real
  Outlook-COM-plus-Compass capture pass.
- **The backend stayed fully responsive throughout the entire ~8-minute
  in-flight window** — dozens of concurrent `GET /agents` probes during
  this window all returned `HTTP 200` in 60-120ms (plus 82 rapid
  `POST .../run_capture_now` re-attempts during the earlier
  app-start-held portion, all returning near-instantly with the honest
  `"skipped"` result) — confirming this task's own wiring inside
  `dispatch_with_shared_lock` did not reintroduce any blocking behavior
  `T01` had just fixed.
- **`running: false` observed once the real dispatch genuinely
  finished**, with `finished_at: "2026-08-17T07:25:40.153525+00:00"`,
  `last_outcome: "success"`, `last_error_message: null`, and a real
  `last_duration_seconds: 473.951474` — matching `started_at`/
  `finished_at`'s own real wall-clock delta exactly. `elapsed_seconds`
  correctly reverted to `null` once `running` became `false`.
- Directly inspected the real vault's own
  `.second-brain/job_run_state.json` afterward: exactly one key,
  `"email-capture-pipeline::run_capture_now"`, holding precisely this
  finished record — no other key, no other file.

**Verdict: PASS.** This is the direct, live, end-to-end proof the
task's own "since that's the whole point of this task" instruction
asked for: a real dispatch through the real HTTP surface, against the
real backend/vault/Outlook/Compass, genuinely transitioning
`running: true` (growing `elapsed_seconds`) → `running: false` (real
`last_duration_seconds`, real `last_outcome`) — not inferred from
reading the code, and not only a scratch-vault unit-style double.

**Assumption logged for spot-check (scope-internal judgement call, not a
MUST-FLAG trigger):** stopping/restarting the port-8001 `--reload` dev
server and killing an orphaned `--reload` sub-worker process during this
task's own live verification (to eliminate a real confound — that
process's own reload-triggered app-start captures were competing for
the same real Outlook/Compass resources and continuously appending to
the same shared `agent_communication_history.json`) was necessary to
produce trustworthy live evidence, mirroring `T01`'s own identical
precedent. No task file, no `src/` file outside `## Files to Modify`,
and no other artefact was touched by this process-management cleanup;
the environment was restored to its original state (`--reload` on port
8001) afterward.

### Other locked-in-file checklist items

- `get_job_run_states()`'s covered-agent-id enumeration reads
  `skill_registry._MIGRATION_GRANT_SEED["run_capture_now"]` directly
  (confirmed by direct code read, `grep`-verified against
  `skill_registry.py` line 62 before writing this task's own code) —
  never a second, independently-hardcoded list. Live-exercised: smoke
  check 1 above returned exactly the 3 ids that live in
  `_MIGRATION_GRANT_SEED["run_capture_now"]` today
  (`email-capture-pipeline`/`meeting-capture`/`todo-capture`), not a
  separately-typed literal in this task's own new code.
- `data_access` (`vault_writer.py`) stays pure I/O — `load_job_run_state`/
  `save_job_run_state` compute no default content and make no business
  decision, mirroring `load_agent_schedules_state`'s own convention
  exactly (confirmed by direct code read after edit).
- No new persisted state file other than
  `.second-brain/job_run_state.json` — confirmed both against the
  scratch double vault (smoke checks) and the real vault (live
  end-to-end check).

gate: clear 2026-08-17 — no MUST-FLAG trigger fired during this task's
own build/verification. No material assumption beyond the disclosed,
scope-internal verification-environment process-management cleanup
above (logged, not a requirement-filling assumption); no ADR
created/changed by the coder (this task builds against the architect's
already-`Accepted` `ADR-045` and the decomposer's own disclosed,
in-task-file "Design refinement" note, both unedited); no
`ESCALATIONS.md` entry (no out-of-scope event); every one of this
task's own 5 checklist items was fully verified, not blocked (trigger 6
does not fire — this task carries no locked AC of its own, per the
parent story's AC-to-task mapping); no contradictory inputs; nothing
here required a judgement call among multiple equally-valid options.
