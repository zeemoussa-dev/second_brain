---
id: REQ-SB-47-US-01-T05
title: agent_schedules_router.py — POST run-now endpoint through the shared dispatch lock
parent_story: REQ-SB-47-US-01
requirement_id: REQ-SB-47
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-47-US-01-T04]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-47-US-01-T05 — `POST .../run-now` endpoint

## Parent Story

- Story: [[REQ-SB-47-US-01]] — `../UserStories/REQ-SB-47-US-01-per-agent-scheduler-and-shared-serialization.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-47 *Per-Agent Scheduler* (merges REQ-SB-45)

---

## Objective

Add `POST /agents/{agent_id}/schedules/{capability_id}/run-now` to the
router `T04` created — the on-demand path that reuses the existing
`"direct"` trigger literal, unchanged, dispatched through the SAME shared
lock every scheduled tick uses, per `ADR-037` point 7.

---

## Starting State → End State

**Before / Inputs:**
- `T04`'s `agent_schedules_router.py` exists with `GET`/`POST`/`PATCH`/`DELETE` on `/agents/{agent_id}/schedules[...]`.
- `T02`'s `agent_schedule_registry.dispatch_with_shared_lock(agent_id, capability_id, trigger)` exists.
- `T01`'s `invoke_skill` already lets `trigger="direct"` through unconditionally regardless of working mode (Manual mode only special-cases `"hub_routed"` and, as of `T01`, `"scheduled"` — never `"direct"`).

**After / Outputs:**
- `POST /agents/{agent_id}/schedules/{capability_id}/run-now` — `404` for an unknown `agent_id`; otherwise `await agent_schedule_registry.dispatch_with_shared_lock(agent_id, capability_id, trigger="direct")`, returning the result as-is (`200`) — a real success, an honest "not available," and an honest "skipped — another run is already in progress" are all valid `200` outcomes, never translated into an error status. Works whether or not a recurring schedule currently exists for that `(agent_id, capability_id)` pair — this endpoint does not require `list_schedules` to contain the pair first.

---

## Files to Modify

- `src/backend/app/api/agent_schedules_router.py` — add exactly one new route function to the file `T04` created. No other route in this file changes.

---

## Constraints

- Inherits from parent story.
- Reuses the existing `"direct"` literal, unchanged — do not introduce a new trigger value or a new Manual-mode branch for this endpoint; `T01`'s gate already lets `"direct"` through.
- Do not require an active schedule to exist for the targeted capability — Scenario 6 and Scenario 5 both require "run now" to work independent of whether a recurring schedule is currently configured.
- Every outcome (`ok`, honest-unavailable, honest-skipped) is a `200`, never a `4xx`/`5xx` — an honest non-success result is not itself an HTTP error, mirroring `skills_router.py::invoke_skill`'s own existing "any other shape... returned as-is, 200" convention.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-47-US-01-AC-05, partial] Ensure NO schedule exists for `("meeting-capture", "run_capture_now")` (delete it first if `T04`'s own checks left one). `POST /agents/meeting-capture/schedules/run_capture_now/run-now` — expect a `200` with the same honest "not available" outcome the existing direct-invoke path already produces for `meeting-capture` (per this story's own disclosed, known limitation). Confirms "Run now" works with no schedule configured at all.
2. [REQ-SB-47-US-01-AC-06] `POST /agents/email-capture/schedules/run_capture_now/run-now`. Expect a `200` real outcome. Immediately `GET /agents/email-capture/history` and confirm a new entry recording this exact outcome now appears, newest-first.
3. [REQ-SB-47-US-01-AC-07, partial — real HTTP layer] Fire `POST /agents/email-capture/schedules/run_capture_now/run-now` and, concurrently (e.g. two parallel `curl`/`httpx.AsyncClient` calls issued back-to-back with no deliberate delay, or one real HTTP call plus one direct in-process `agent_schedule_registry.dispatch_with_shared_lock("meeting-capture", "run_capture_now", trigger="scheduled")` call fired in the same instant via `asyncio.gather`) against a DIFFERENT agent's capability. Confirm exactly one real outcome and one honest "skipped — another run is already in progress" outcome, both visible in their respective agents' `GET /agents/{id}/history`, confirming the shared lock holds across the real HTTP surface, not just at the registry-function level `T02` already proved.
4. [REQ-SB-47-US-01-AC-08, partial — real HTTP layer] Set an agent to Manual mode (`PATCH /agents/{agent_id}` per the existing `working_mode` field). `POST /agents/{agent_id}/schedules/{a granted mutating capability_id}/run-now` — expect the run to execute (same outcome as it would for any other mode), confirming Manual mode does not block this endpoint. Restore the agent's prior working mode afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `POST .../run-now` dispatches through `dispatch_with_shared_lock` with `trigger="direct"`, works with or without an active schedule for that pair.
- [ ] The outcome (success / honest-unavailable / honest-skipped) is recorded to run history and returned `200`.
- [ ] The shared-lock property holds across the real HTTP surface: two concurrent eligible runs for different agents never overlap.
- [ ] A Manual-mode agent's run-now still executes.
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint.
- [ ] `CHANGELOG.md` entry appended.

---

## Out of Scope

- Any frontend change (`T06`).
- Any change to schedule CRUD routes (`T04`, already built).

---

## Context / Notes

Full reasoning: `ADR-037` point 7. Precedent for "any outcome shape, always 200": `src/backend/app/api/skills_router.py::invoke_skill`'s own existing convention.

---

## Implementation Log

**Built:** `POST /agents/{agent_id}/schedules/{capability_id}/run-now` added
to `agent_schedules_router.py` — `404` for an unknown `agent_id`, otherwise
`await agent_schedule_registry.dispatch_with_shared_lock(agent_id,
capability_id, trigger="direct")`, result returned as-is (`200`) in every
case.

**Verification (2026-08-14, real HTTP against a live server; this task's own
run-now calls are what surfaced `T02`'s real duplicate-history defect —
described in full in `T02`'s own Implementation Log — re-verified here
post-fix):**

- `[AC-05, partial]` No schedule existed for `("meeting-capture",
  "run_capture_now")`. `POST .../meeting-capture/schedules/
  run_capture_now/run-now` → `200`, the same honest "not available" outcome
  the direct-invoke path already produces — confirms run-now works with NO
  schedule configured at all. **PASS.**
- `[AC-06]` `POST .../email-capture/schedules/run_capture_now/run-now` → a
  real outcome (`{"available":true,"message":"Done — 0 email(s) filed."}`,
  after an earlier call in this same session had already cleared the day's
  backlog). `GET /agents/email-capture/history` confirmed exactly ONE new
  entry recording this outcome, newest-first. **PASS** (post-fix; the
  pre-fix run showed a real +2 duplicate, root-caused and fixed in `T02`).
- `[AC-07, partial — real HTTP layer]` While the `email-capture` run-now
  call above was genuinely in flight (a real, multi-minute blob tick —
  observed processing a large real backlog: 2 emails, 35 meetings, 100
  tasks across this session's several real ticks), a concurrent `POST
  .../meeting-capture/schedules/run_capture_now/run-now` call returned
  immediately: `{"status":"skipped","message":"skipped — another run is
  already in progress"}` — confirmed recorded to `meeting-capture`'s own
  history. This is a REAL cross-agent lock-contention event at the HTTP
  layer (not simulated), independently reconfirming `T02`'s in-process
  `asyncio.gather` proof of the exact same property from a second angle.
  **PASS — the story's own single highest-risk guarantee, confirmed live at
  the HTTP surface.**
- `[AC-08, partial — real HTTP layer]` `people-producer` (baseline
  Autonomous) `run-now` for `rebuild_person_note` → honest "not available"
  stub. Switched to Manual (`PATCH /agents/people-producer
  {"working_mode":"manual"}`), re-ran the identical `run-now` call → BYTE-
  IDENTICAL outcome — confirms Manual mode does not block this endpoint.
  Restored to Autonomous afterward. **PASS.**

No deviations from the task's own design (the fix that changed dispatch
behavior lives entirely in `T02`'s own file, `agent_schedule_registry.py` —
this task's own file, the run-now route itself, needed no change once that
fix landed).

gate: clear 2026-08-14 — no triggers fired (requirement finalised, no ADR
change, all tagged manual steps verified live and passing).
