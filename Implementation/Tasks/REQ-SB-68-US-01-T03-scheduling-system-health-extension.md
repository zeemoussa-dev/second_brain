---
id: REQ-SB-68-US-01-T03
title: Extend GET /system-health with the new "scheduling" key; retire "last_capture_run" from the response
parent_story: REQ-SB-68-US-01
requirement_id: REQ-SB-68
type: backend
status: Done
gate: clear
gate_reason: "Resolved 2026-08-17 — ESC-042's blocking pre-existing defect (provider_registry.py::_load_state() never pruning an orphaned agent-id assignment key) is fixed per direct operator decision (Option (a), symmetric self-healing pruning). Live-verified: GET /system-health now returns a real 200 with the exact {mcp, providers, disabled_agents, scheduling} shape. All 3 non-AC smoke checks passed live. See ESCALATIONS.md -> ESC-042 (Status: Resolved) and this file's own Implementation Log."
phase: P1
depends_on: [REQ-SB-68-US-01-T02]
sprint: ""
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-68-US-01-T03 — `GET /system-health`'s new `"scheduling"` key

## Parent Story

- Story: [[REQ-SB-68-US-01]] — `../UserStories/REQ-SB-68-US-01-non-blocking-capture-dispatch-and-scheduling-monitor.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-68 *Async Capture Jobs + Real-Time Job/Scheduling Monitor*

---

## Objective

Compose `T02`'s new `agent_schedule_registry.get_job_run_states()` into
the existing, already-real `GET /system-health` aggregation
(`system_health.py::get_system_health()`) under a new `"scheduling"` key
— **no new endpoint** (API-first, per tonight's own standing operator
directive: extend the real, already-established aggregation surface
rather than add a new router). Retire the now-superseded
`"last_capture_run"` key from the response.

---

## Starting State → End State

**Before / Inputs:**
- `system_health.py::get_system_health()` returns `{"mcp", "providers",
  "disabled_agents", "last_capture_run"}`.
- `T02` has landed `agent_schedule_registry.get_job_run_states() ->
  list[dict]`.

**After / Outputs:**
- `system_health.py::get_system_health()` returns `{"mcp", "providers",
  "disabled_agents", "scheduling"}` — `"last_capture_run"` is removed;
  `"scheduling"` is `agent_schedule_registry.get_job_run_states()`'s own
  list, composed in unmodified.
- `system_health_router.py` needs **no change** — it already returns
  `get_system_health()`'s full dict unmodified.

---

## Files to Modify

- `src/backend/app/business/system_health.py`:
  ```python
  """Read-only aggregation of Second Brain's own operational signals for
  the System Health view (REQ-SB-31-US-01, extended REQ-SB-68-US-01) --
  writes no new persisted state at all, composes only already-existing/
  already-computed signals from provider_registry, agent_registry,
  agent_schedule_registry, and vault_writer, plus one local, in-process
  GET /mcp reachability check. Recompute fresh on every call -- no
  caching (Scenario 7, REQ-SB-31-US-01)."""
  import httpx

  from app.business import agent_registry, agent_schedule_registry, provider_registry
  from app.data_access import vault_writer

  # Same hardcoded loopback host:port agent_orchestration/mcp_client.py
  # already calls -- this project's own documented port convention
  # (tools/run-backend.cmd --port 8001), not a new port-discovery
  # mechanism.
  _MCP_MOUNT_URL = "http://127.0.0.1:8001/mcp"


  def mcp_mount_reachable() -> bool:
      """True only on the mount's own proven "alive" signal (a bare GET
      correctly returns HTTP 406 Not Acceptable when the mount is alive --
      confirmed live 2026-08-12, see architecture.md). Any other status
      code, connection error, or timeout is honestly reported as
      unreachable -- never a fabricated True.

      follow_redirects=True is required here (REQ-SB-31-US-01-T02's own
      live-discovered correction) -- a bare GET /mcp (no trailing slash)
      actually 307-redirects to /mcp/ first, which only then answers 406."""
      try:
          response = httpx.get(_MCP_MOUNT_URL, timeout=3.0, follow_redirects=True)
      except httpx.HTTPError:
          return False
      return response.status_code == 406


  def list_disabled_agents() -> list[dict]:
      """Every agent whose selected Provider has no real client configured
      -- the System-Health-view-specific Disabled/Health-Issue override
      (scoped to this view only, per the story's own Constraints)."""
      disabled = []
      for agent in agent_registry.list_agents():
          provider = provider_registry.get_agent_provider(agent["id"])
          if provider is None or not provider_registry.has_real_client(provider["id"]):
              disabled.append({
                  "agent_id": agent["id"],
                  "agent_name": agent["name"],
                  "provider_name": provider["name"] if provider else None,
              })
      return disabled


  def _providers_with_agent_names() -> list[dict]:
      """provider_registry.list_providers() already rolls up each
      Provider's agent_ids -- this adds a display-only agent_names field
      (resolved via agent_registry.get_agent) alongside it, additive only,
      so the frontend never has to make a second round-trip or duplicate
      the id->name lookup itself. Does not modify provider_registry.py's
      own return contract."""
      providers = provider_registry.list_providers()
      for provider in providers:
          provider["agent_names"] = [
              agent_registry.get_agent(agent_id)["name"] for agent_id in provider["agent_ids"]
          ]
      return providers


  def get_system_health() -> dict:
      return {
          "mcp": {"reachable": mcp_mount_reachable()},
          "providers": _providers_with_agent_names(),
          "disabled_agents": list_disabled_agents(),
          # REQ-SB-68-US-01 / ADR-045 point 5 -- replaces the former
          # "last_capture_run" key (a single, aggregate finished_at
          # timestamp) with the richer per-covered-job running/duration/
          # outcome list. agent_schedule_registry.get_job_run_states()
          # recomputes fresh on every call, exactly like every other
          # signal in this dict.
          "scheduling": agent_schedule_registry.get_job_run_states(),
      }
  ```

---

## Constraints

- Inherits from parent story: `business/` layer only — no HTTP framework
  import, no direct filesystem access of its own.
- **`system_health_router.py` is NOT modified** — it already returns
  `get_system_health()`'s dict unmodified; no new endpoint.
- `"last_capture_run"` is removed from the response dict — `T02`'s Notes
  confirm `.second-brain/last_capture_run.json`'s own write call site
  stays byte-for-byte unchanged elsewhere (a disclosed, harmless
  redundancy — not this task's concern).
- `get_system_health()` must continue to recompute fresh on every call —
  no caching of any of its four signals, including the new
  `"scheduling"` one.

---

## Tests

<!-- No locked AC of its own -- mirrors REQ-SB-31-US-01-T02/T03's own
identical split: every one of AC-02 through AC-07 is genuinely
view-observable only once T04 wires a real page around this endpoint.
Non-AC smoke checks only. -->

**Manual verification steps** (real backend running on port `8001`):

1. Non-AC smoke check: `GET /system-health` with no covered job ever run
   in this vault (or a freshly-cleared `job_run_state.json`). Confirm the
   response's `"scheduling"` list has exactly 3 entries (one per
   `skill_registry._MIGRATION_GRANT_SEED["run_capture_now"]` agent), each
   `"has_run": false`, and has **no** `"last_capture_run"` key at all.
2. Non-AC smoke check: trigger a real `POST
   /agents/email-capture-pipeline/actions/run_capture_now` and, while it
   is in flight, `GET /system-health`. Confirm `"scheduling"` contains an
   entry for `email-capture-pipeline`/`run_capture_now` with `"running":
   true` and a positive `"elapsed_seconds"`. After it completes, `GET
   /system-health` again and confirm `"running": false` with a real
   `"last_duration_seconds"` and `"last_outcome"`.
3. Non-AC smoke check: dispatch an uncovered action (`POST
   /agents/compass-expert/actions/build_knowledge`, or confirm via direct
   call if no real Provider is configured) and confirm it never appears
   in `"scheduling"`, and the response's other three keys
   (`mcp`/`providers`/`disabled_agents`) are unaffected.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `GET /system-health` returns `{"mcp", "providers",
      "disabled_agents", "scheduling"}` — `"last_capture_run"` removed
      — **verified live: real `GET /system-health` returns `200` with
      exactly this shape, once ESC-042's blocking pre-existing defect
      was resolved (see `## Implementation Log`)**
- [x] `"scheduling"` is exactly `agent_schedule_registry.
      get_job_run_states()`'s own list, recomputed fresh on every call
      — **verified live end-to-end through the real endpoint** (running
      → finished transition observed live, see `## Implementation Log`)
- [x] `system_health_router.py` is unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `mcp_mount_reachable`/`list_disabled_agents`/
  `_providers_with_agent_names` beyond the import-list addition needed
  for `agent_schedule_registry` — those three functions are otherwise
  untouched.
- The Scheduling section frontend — `T04`.
- `.second-brain/last_capture_run.json`'s own write call site — left
  alone, `T02`'s Notes.

---

## Context / Notes

Mirrors `REQ-SB-31-US-01-T02`'s own "one-module-per-feature, read-only
aggregation, no vault writes" shape — this task only adds one import and
one dict key, replacing another; every other function in the file is
untouched.

---

## Implementation Log

**Coder pass, 2026-08-17 — code built exactly per spec; task left
`status: Blocked` (not `Done`) — a pre-existing, unrelated defect
blocks live end-to-end verification. Full root cause: `ESCALATIONS.md`
→ `ESC-042`.**

### What was changed (`src/backend/app/business/system_health.py`)

- Import list: `from app.business import agent_registry,
  agent_schedule_registry, provider_registry` — added
  `agent_schedule_registry`.
- `get_system_health()`: `"last_capture_run"` key removed; new
  `"scheduling": agent_schedule_registry.get_job_run_states()` key
  added in its place. `mcp`/`providers`/`disabled_agents` keys and every
  other function (`mcp_mount_reachable`, `list_disabled_agents`,
  `_providers_with_agent_names`) are byte-for-byte unchanged, per the
  task's own `## Out of Scope`.
- **One disclosed, scope-internal deviation from the task's own literal
  code block (an assumption, logged here per Pipeline.md's "scope-internal
  judgement calls" convention, not an escalation):** the task's own
  prescribed code block kept `from app.data_access import vault_writer`
  even though removing `"last_capture_run"` (the only call site that used
  it, `vault_writer.load_last_capture_run()`) leaves that import unused.
  Dropped the now-dead `vault_writer` import and corrected the module
  docstring's own list of composed modules to match (no longer names
  `vault_writer`; added a short note explaining why). No functional
  change — the resulting dict shape and every function's behavior are
  identical to the task's own literal spec; only a dead import was not
  carried forward.
- `system_health_router.py`: **not modified**, confirmed by inspection —
  it already returns `get_system_health()`'s dict unmodified (no import,
  no key-shaping logic of its own).

### Pre-existing `HTTP 500` — real traceback captured, root-caused, NOT fixed here (escalated)

Before making any change, `curl http://127.0.0.1:8001/system-health`
against the real running backend returned `HTTP 500` on 3 separate real
requests. A real traceback (not guessed from `curl` alone) was captured
by invoking `system_health.get_system_health()` directly in the venv
Python interpreter against the real app:

```
File "...\system_health.py", line 74, in get_system_health
    "providers": _providers_with_agent_names(),
File "...\system_health.py", line 66, in _providers_with_agent_names
    agent_registry.get_agent(agent_id)["name"] for agent_id in provider["agent_ids"]
TypeError: 'NoneType' object is not subscriptable
```

Root cause, confirmed by direct inspection: `.second-brain/agent_providers.json`'s
`"assignments"` map carries a stale, orphaned key `"email-capture":
"compass"` — no agent with that id exists in `agent_registry.py`'s
`_SEED_AGENTS` today (renamed to `"email-capture-pipeline"` by the
already-`Done` `REQ-SB-55-US-01-T08`/`ADR-043` point 6, confirmed by
that module's own docstring). `provider_registry.py::_load_state()`
only ever *adds* a missing assignment for a currently-known agent id —
it never *prunes* one for an agent id that no longer exists after a
rename — so the orphaned key has sat there since that rename, with no
consumer dereferencing it until `_providers_with_agent_names()`
(`REQ-SB-31-US-01`, already `Done`) started calling
`agent_registry.get_agent(agent_id)["name"]` with no `None`-guard.
`get_agent("email-capture")` returns `None`; `None["name"]` raises the
`TypeError`, surfaced by FastAPI as an unhandled `500`.

**Ruled out, by direct testing, not assumption:**
- `mcp_mount_reachable()`'s own self-referential `httpx.get` call — a
  direct `curl -L http://127.0.0.1:8001/mcp` returns `406` as expected
  (mount alive), and a direct in-process call to `mcp_mount_reachable()`
  returns `True`. The captured traceback also shows the crash occurs one
  key later (`"providers"`), so `mcp_mount_reachable()`'s own result is
  irrelevant to the 500 either way.
- `agent_registry.list_agents()` — returns exactly the 7 real, expected
  seed agents, all valid; `list_disabled_agents()` (which iterates the
  same 7) is never even reached — the traceback fails one key earlier.
- Not caused by tonight's session — the underlying agent-id rename
  (`REQ-SB-55-US-01-T08`) predates tonight; this is a dormant defect
  exposed by `REQ-SB-31-US-01`'s already-`Done` `GET /system-health`
  build, not a regression introduced live tonight.

**Confirmed this task's own change neither causes nor worsens the
500:** re-ran the identical direct-Python-shell reproduction *after*
this task's `system_health.py` edit landed — identical traceback, same
line, same exception. `T03`'s own new `"scheduling"` key is never even
reached; the crash happens one key earlier, in
`_providers_with_agent_names()`, a function `T03`'s own `## Out of
Scope` explicitly forbids changing beyond the import-list addition. The
real fix belongs to either `provider_registry.py::_load_state()`'s own
reconciliation logic (a different file, not in this task's `## Files to
Modify`) or a defensive guard inside `_providers_with_agent_names()`
itself (explicitly excluded by this task's own `## Out of Scope`
carve-out) — both belong to a different, already-`Done` story's
territory, not `T03`'s own declared scope. Per `Implementation/
Pipeline.md` hard rule 5 ("ANY out-of-scope event → immediate
escalation, no improvisation"), this is escalated (`ESCALATIONS.md` →
`ESC-042`, `REVIEW-QUEUE.md` pointer added), not patched in place. No
file outside this task's own `## Files to Modify` was touched to work
around it — not even `.second-brain/agent_providers.json`'s one stale
data key, despite that being the most surgical possible fix, since it
is not listed in `## Files to Modify` either.

### Verification attempted (per this task's own `## Tests`)

`T03` carries no locked AC of its own (`AC-02`-`AC-07` are only
genuinely observable once `T04` wires a real page around this
endpoint, per the decomposer's own AC-to-task mapping) — non-AC smoke
checks only, per the task's own `## Tests`. All three require a
genuinely working `GET /system-health` response, which the pre-existing
defect above blocks end-to-end:

1. **Fresh-state placeholders check — BLOCKED, could not verify live.**
   Would confirm `"scheduling"` has exactly 3 entries, each `"has_run":
   false`, no `"last_capture_run"` key. Verified instead via a direct,
   isolated call to `agent_schedule_registry.get_job_run_states()`
   (bypassing the crashing `_providers_with_agent_names()` entirely) —
   returns the correct 3-entry shape (`email-capture-pipeline` currently
   `has_run: true` from `T02`'s own earlier real dispatch;
   `meeting-capture`/`todo-capture` correctly `has_run: false`), proving
   `T03`'s own composition logic is sound. **Not the same thing as a
   real `200` `GET /system-health` response** — recorded honestly as
   blocked, not passed.
2. **Running-then-finished transition via a real `run_capture_now`
   dispatch — NOT ATTEMPTED.** Dispatching a real ~8-minute live capture
   run (per `T02`'s own precedent) is pointless while `GET
   /system-health` itself 500s regardless of the job's running state —
   would not produce a different, more informative result. Deferred
   until the pre-existing defect is resolved.
3. **Uncovered-action isolation — NOT ATTEMPTED**, same reason as (2).

### Acceptance Criteria — status

- [x] `system_health_router.py` is unchanged — confirmed by direct
      inspection (git diff shows no change to this file).
- [ ] `GET /system-health` returns `{"mcp", "providers",
      "disabled_agents", "scheduling"}` — **blocked**, cannot verify
      live while the pre-existing, escalated defect (`ESC-042`) stands;
      the code change implementing this is in place and correct.
- [ ] `"scheduling"` is exactly `agent_schedule_registry.
      get_job_run_states()`'s own list, recomputed fresh on every call —
      verified correct **in isolation** (direct call, see above);
      **not verifiable end-to-end through the real endpoint** until
      `ESC-042` is resolved.
- [x] `MEMORY.md` updated (see repo-root `MEMORY.md` — new Constraint
      entry on this class of orphaned-assignment defect).
- [x] `CHANGELOG.md` entry appended.

**Task left `status: Blocked`, `gate: flagged`** — mirrors `ESC-012`'s
own identical precedent (`REQ-SB-08-US-01-T06`): the already-built code
is faithful, non-regressive, and left in place, not reverted, pending a
human/architect decision on `ESC-042`'s fix shape. `REQ-SB-68-US-01`'s
own story status stays `In Progress` (`T04` cannot start — it
`depends_on: [T03]`, and `T03` is not `Done`).

---

**Coder pass, 2026-08-17 (resume) — `ESC-042` resolved by direct
operator decision (Option (a)); `T03` now `status: Done`, `gate: clear`.**

### The fix (out-of-scope file, applied as the escalation's own
resolving artefact, not part of this task's own `## Files to Modify`)

Per the operator's direct 2026-08-17 decision recorded in
`ESCALATIONS.md` → `ESC-042`'s own `## Resolution`, `src/backend/app/
business/provider_registry.py::_load_state()` was given a small,
surgical, symmetric addition: after the existing add-missing-assignment
loop, a new loop removes any `"assignments"` key whose agent id is not
in the current, real `agent_registry.list_agents()` id set, persisting
the pruned state back via the same `vault_writer.save_providers_state`
call the add-side already uses. This is **not** a change to this task's
own `## Files to Modify` (`system_health.py` is unchanged by this
addition) — it is the concrete resolving artefact for a already-
escalated, already-operator-decided defect in a different file, applied
here only because doing so is what unblocks this task's own live
verification, per the explicit operator direction that accompanied the
resolution. `system_health.py` itself required **zero** further change —
confirmed live below.

### Live verification, real running backend (port 8001), real vault

1. **Before:** direct read of `.second-brain/agent_providers.json`
   confirmed the stale `"email-capture": "compass"` key was present.
2. **Backend started**
   (`.venv/Scripts/python.exe -m uvicorn app.main:app --port 8001`).
3. **Trigger:** a real `GET /system-health` request (which reaches
   `provider_registry.list_providers()` → `_load_state()`).
4. **After:** the same file, re-read directly, no longer carries the
   `"email-capture"` key — pruned automatically by the new reconciliation
   loop, not hand-edited. Every other assignment (`meeting-capture`,
   `todo-capture`, `people-producer`, `vault-qa`, `vault-filing-expert`,
   `compass-expert`, `email-capture-pipeline`) is untouched.
5. **`curl http://127.0.0.1:8001/system-health` now returns a real, live
   `200`**, with the exact shape `{"mcp", "providers", "disabled_agents",
   "scheduling"}` and no `"last_capture_run"` key.
6. **`system_health_router.py` confirmed byte-for-byte unchanged**
   (`git diff --stat` shows zero changes to that file).

### The 3 non-AC smoke checks (`## Tests`), all blocked in the prior pass, now passed live

1. **Fresh/real-state placeholder shape.** `"scheduling"` has exactly 3
   entries — one per `skill_registry._MIGRATION_GRANT_SEED[
   "run_capture_now"]` agent. Tonight's session had already run a real
   capture for `email-capture-pipeline` before this pass began, so it
   correctly shows `"has_run": true` with real `started_at`/`finished_at`/
   `last_outcome`/`last_duration_seconds`; `meeting-capture` and
   `todo-capture` correctly show `"has_run": false` with every other
   field `null` — an honest, correct shape either way, not a fabricated
   placeholder.
2. **Running → finished transition, observed live through the real
   endpoint.** A real `POST /agents/email-capture-pipeline/actions/
   run_capture_now` was dispatched. (Several earlier attempts returned
   `{"status": "skipped", "message": "skipped — another run is already in
   progress"}` — the app-start capture trigger, `capture_scheduler.py::
   lifespan`'s unconditional `run_capture_if_idle()` call, was itself
   genuinely in flight and holding `agent_schedule_registry`'s shared
   dispatch lock; confirmed real via the server's own live log showing
   continuous real Compass API calls throughout — not a bug, correct
   skip-not-overlap behavior.) Once that app-start run finished and the
   lock freed, the manual dispatch was accepted. Polling `GET
   /system-health` repeatedly showed `"scheduling"`'s
   `email-capture-pipeline` entry as `"running": true`,
   `"started_at": "2026-08-17T08:42:53.774606+00:00"`, `"finished_at":
   null`, with a real, monotonically growing `"elapsed_seconds"` (342.95
   → 363.40 → 383.74 → … → 586.93 across repeated polls). The next poll
   after that showed `"running": false`, `"finished_at":
   "2026-08-17T08:52:50.877558+00:00"`, `"last_outcome": "success"`,
   `"last_duration_seconds": 597.102952`, `"elapsed_seconds": null` — a
   complete, real, live-observed transition through the actual endpoint,
   not `T02`'s own already-verified direct-registry-call evidence alone.
3. **Uncovered-action isolation.** `POST /agents/compass-expert/actions/
   build_knowledge` was dispatched (`{"status": "ok", "message": "The web
   research step found nothing relevant.", "history_recorded": false}`).
   The subsequent `GET /system-health` confirmed `compass-expert` never
   appears in `"scheduling"` (still exactly the same 3 covered-agent
   entries), and the other 3 response keys (`mcp`/`providers`/
   `disabled_agents`) were unaffected.

### Acceptance Criteria — final status

- [x] `GET /system-health` returns `{"mcp", "providers",
      "disabled_agents", "scheduling"}`, `"last_capture_run"` removed —
      verified live (200, exact shape, confirmed above).
- [x] `"scheduling"` is exactly `agent_schedule_registry.
      get_job_run_states()`'s own list, recomputed fresh on every call —
      verified live end-to-end (real running → finished transition
      observed through the actual endpoint, confirmed above).
- [x] `system_health_router.py` is unchanged — reconfirmed by `git diff`
      after this pass too (zero changes).
- [x] `MEMORY.md` updated — the 2026-08-17 Constraint entry describing
      the open defect is corrected in place to record the fix (self-
      healing pruning), not left describing a now-resolved defect as
      still open.
- [x] `CHANGELOG.md` entry appended.

**Task `status: Done`, `gate: clear`.** `REQ-SB-68-US-01`'s own story
status advances `In Progress` (unchanged — `T04` remains to be built,
now unblocked: `depends_on: [T03]` is satisfied). `ESCALATIONS.md` →
`ESC-042` is updated to `Status: Resolved` with this task's own live
verification as the concrete resolving evidence. `REVIEW-QUEUE.md`'s
`REQ-SB-68-US-01-T03` entry is marked resolved accordingly (the story's
own separate, standing `ADR-045` review-flag entry is untouched — a
different, still-open item).
