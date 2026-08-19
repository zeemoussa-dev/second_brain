---
id: REQ-SB-39-US-02-T03
title: skill_tools.py / skill_registry.py — the 4 mutating Action ids become SKILLS entries + handlers, preserving today's real/honest-unavailable split exactly
parent_story: REQ-SB-39-US-02
requirement_id: REQ-SB-39
type: backend
status: Done
gate: flagged
gate_reason: "live-discovered finding during verification — a pre-existing, real background-scheduler pending-approval record was created by an unrelated, already-running dev-server process during this task's own live test window; disclosed, not silently resolved"
phase: P1
depends_on: [REQ-SB-39-US-02-T01, REQ-SB-39-US-02-T02, REQ-SB-39-US-01-T01, REQ-SB-39-US-01-T02]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-39-US-02-T03 — migrate the 4 mutating Action ids to Skills

## Parent Story

- Story: [[REQ-SB-39-US-02]] — `../UserStories/REQ-SB-39-US-02-unify-capabilities-working-mode-gate-and-mutating-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-39 *Unify Agent Capabilities Under Skills*

---

## Objective

Add `run_capture_now`, `pause_schedule`, `rebuild_person_note`, and
`build_knowledge` to `skill_tools.SKILLS` (each `"mutates": True`), with
one new `@mcp_server.tool()` handler each, wired into
`skill_registry._SKILL_HANDLERS`. Preserves EXACTLY today's real/honest-
unavailable split (`ADR-029` point 5, confirmed by direct code
inspection, not guessed) — no new real behavior is built by this pass.

**This task must land on top of `T01` (the gate) — never independently**
(`ADR-029` point 8's atomicity discipline): the moment these 4 ids join
`SKILLS`, they become real, invocable, mutating Skills; if the gate did
not already exist, they would be invocable completely ungated. `depends_on`
encodes this.

---

## Starting State → End State

**Before / Inputs:**
- `skill_tools.SKILLS` has 5 entries (`diagram-understanding`,
  `web-research`, `view_last_run`, `ask_question`, `view_channel_status`),
  all `"mutates": False`.
- `_ACTION_HANDLERS` (`agents_router.py`, untouched by this task) wires a
  real handler to only 2 of the 4 mutating ids' agent pairs:
  `("email-capture", "run_capture_now")` →
  `run_capture_and_record_completion`; `("compass-expert",
  "build_knowledge")` → `_run_build_knowledge` (→
  `knowledge_bootstrap.bootstrap_agent_knowledge`). The other 5 real
  (agent, action) pairs — `meeting-capture`'s/`todo-capture`'s own
  `run_capture_now`, all 3 agents' `pause_schedule`, `people-producer`'s
  `rebuild_person_note` — have no wired handler and return an honest "not
  yet available" today.

**After / Outputs:**
- `skill_tools.SKILLS` grows from 5 to 9 entries; the 4 new entries all
  carry `"mutates": True`.
- 4 new `@mcp_server.tool()` handlers in `skill_tools.py`:
  - `run_capture_now(agent_id: str) -> dict` — agent-agnostic catalog
    entry (one entry, not one per agent — mirrors `web_research`'s own
    agent_id-resolves-real-backend pattern). Real for `email-capture`
    only (calls `email_classification.run_capture_and_record_completion`);
    honest-unavailable for every other agent (`meeting-capture`,
    `todo-capture` included) — the exact real/stub split preserved, NOT
    newly wired for meeting/todo-capture even though their own real
    classification logic exists (it is real and used by the BACKGROUND
    scheduler only, `ADR-018` point 4, never wired to this on-demand
    path — wiring it here would be new behavior this task's own
    Constraint forbids).
  - `pause_schedule() -> dict` — unconditional honest-unavailable stub
    (no real handler exists for this id on any agent today).
  - `rebuild_person_note() -> dict` — unconditional honest-unavailable
    stub (same reason).
  - `build_knowledge(agent_id: str) -> dict` — real handler, calls through
    to `knowledge_bootstrap.bootstrap_agent_knowledge(agent_id, subject)`,
    reusing `agents_router.py::_run_build_knowledge`'s own Subject-
    resolution and status→message translation, reshaped into this
    module's `{"available", "message"}` handler-return convention. See
    `## Context / Notes` for the two real, load-bearing wiring subtleties
    this handler must account for (async bridging, a deferred import to
    avoid a circular import) — neither is guesswork; both are necessary
    for this handler to work at all, not stylistic choices.
- `skill_registry._SKILL_HANDLERS` grows to 9 entries, mapping the 4 new
  ids to the 4 new `skill_tools` functions.
- `agent_registry.py`'s per-agent action arrays for these 4 ids are
  unedited (vestigial, chat-funnel-matching only, `ADR-029` point 6) — no
  file outside this task's own 2 files is touched.

---

## Files to Modify

- `src/backend/app/business/skill_tools.py` — 4 new `SKILLS` entries + 4
  new `@mcp_server.tool()` functions; new top-level imports
  `agent_registry`, `email_classification`; stdlib `asyncio`,
  `concurrent.futures`.
- `src/backend/app/business/skill_registry.py` — `_SKILL_HANDLERS` gains
  4 new entries.

---

## Constraints

- Inherits from parent story and `ADR-029` points 5/6.
- Every one of the 4 new `SKILLS` entries MUST carry `"mutates": True` —
  this is what makes `T01`'s gate defer them under Supervised mode; a
  missing/wrong value here silently defeats the entire story.
- `run_capture_now`'s handler MUST branch on the injected `agent_id` and
  return the honest-unavailable shape for every agent except
  `email-capture` — do NOT call `meeting_classification.
  classify_recent_meetings` / `todo_classification.classify_recent_todos`
  from this handler; that would be new real on-demand behavior neither
  `ADR-029` nor this story's own Constraint ("a gating/declaration
  refactor, not a rewrite") authorizes.
- `pause_schedule` / `rebuild_person_note` are unconditional stubs — no
  per-agent branching, no real logic, identical honest-unavailable shape
  to `diagram_understanding`'s existing body.
- `build_knowledge`'s handler MUST NOT import
  `app.business.agent_orchestration.knowledge_bootstrap` at module level
  — `skill_registry.py` imports `skill_tools`, and `knowledge_bootstrap.py`
  imports `skill_registry` (its own existing Hub-routed `invoke_skill`
  call); a module-level import here would create a real circular import
  (`skill_tools → knowledge_bootstrap → skill_registry → skill_tools`).
  Import it INSIDE the handler function body instead (a standard,
  deferred-import fix — both modules are already fully loaded by the time
  the handler actually runs).
- `build_knowledge`'s handler MUST NOT call `asyncio.run(...)` directly —
  a real caller of this handler (`agents_router.py`'s own async
  `trigger_action`/`chat()` routes, via the already-built
  `skill_tools.SKILLS` membership dispatch fork, `REQ-SB-39-US-01-T07`)
  may already be executing inside FastAPI's own active event loop, and
  `asyncio.run()` raises `RuntimeError: cannot be called from a running
  event loop` in that real case. Drive the coroutine to completion from a
  dedicated, single-use thread instead (`concurrent.futures.
  ThreadPoolExecutor(max_workers=1).submit(asyncio.run, coro).result()`)
  — safe regardless of the calling thread's own event-loop state. See
  `## Context / Notes` for why this is necessary, not a stylistic choice.
- `build_knowledge`'s handler returns `"history_recorded": True` in its
  result dict (mirrors `_run_build_knowledge`'s own identical flag,
  `REQ-SB-36-US-02`) — `bootstrap_agent_knowledge` already records
  exactly one real `run_event`/`proposal` entry itself, internally, in
  every branch; `T02`'s own Approve-branch `skip_history` guard reads
  this flag. `run_capture_now` / `pause_schedule` / `rebuild_person_note`
  do NOT set this flag — none of their own call paths self-record.
- Do NOT modify `agent_registry.py`, `agent_chat.py`, `agents_router.py`,
  `knowledge_bootstrap.py`, or `pending_approvals_router.py` in this task.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-39-US-02-AC-06] Python shell: confirm `skill_tools.SKILLS` has
   9 keys total, all 4 new ones (`run_capture_now`, `pause_schedule`,
   `rebuild_person_note`, `build_knowledge`) present with `"mutates":
   True`. Grant `run_capture_now` to `email-capture` directly
   (`skill_registry.grant_skill_access`); with `email-capture` in
   Autonomous mode, call `skill_registry.invoke_skill("email-capture",
   "run_capture_now", args=None, trigger="direct")` — confirm it runs the
   REAL capture pipeline (a non-fabricated `{"available": True, "message":
   "Done — N email(s) filed."}}`, `N` matching what a direct
   `email_classification.run_capture_and_record_completion()` call
   produces independently). Set `email-capture` to Supervised, invoke
   again, confirm `{"status": "pending", ...}`; approve the resulting
   pending-approval id (`T02`'s new branch) — confirm the SAME real
   capture pipeline actually ran (a new real `run_event` history entry
   naming files captured, not a "not yet available" message). Revoke
   afterward and restore Autonomous mode.
2. [REQ-SB-39-US-02-AC-06] Grant `run_capture_now` to `meeting-capture`
   directly — invoke it — confirm the honest-unavailable shape (`{
   "available": False, "message": "This skill is not yet available — no
   real handler has been built for it."}`), proving the real/stub split
   by agent, not by id, matches today's `_ACTION_HANDLERS` exactly.
   Revoke afterward. Repeat briefly for `pause_schedule` (any agent) and
   `rebuild_person_note` (`people-producer`) — both unconditionally
   honest-unavailable regardless of agent.
3. [REQ-SB-39-US-02-AC-06] Grant `build_knowledge` to `compass-expert`
   directly; with `compass-expert` in Autonomous mode (its own standing
   real-world convention), invoke it via `skill_registry.invoke_skill(
   "compass-expert", "build_knowledge", args=None, trigger="direct")`
   from WITHIN an async context that mirrors the real chat/direct caller
   (e.g. run this specific check via a small `asyncio` test harness that
   itself already has a running loop, or directly exercise it through the
   real `POST /agents/compass-expert/actions/build_knowledge` HTTP route
   once the server is up — that route is itself `async def`) — confirm
   NO `RuntimeError` about a running event loop, and confirm the result
   dict's own `status`/message field mirrors `_run_build_knowledge`'s own
   real result shape (a `written`/`no_match`/`no_results`/`not_autonomous`/
   `unavailable` outcome, translated into this module's `{"available":
   True, "message": ...}` convention) — proving the thread-bridge
   technique is genuinely safe under the real caller's own async context,
   not just in a bare, loop-free python shell. Revoke afterward.
4. [REQ-SB-39-US-02-AC-07] `POST /agents/email-capture/skills/
   run_capture_now` (the standard grant endpoint) then `DELETE` the same
   — confirm identical `{"granted": True}` / `{"revoked": True}` responses
   to any pre-existing Skill, e.g. `web-research` — proving no separate,
   mutating-Skill-specific grant/revoke surface exists.
5. Non-AC smoke check: confirm `agent_registry.AGENTS["email-capture"]
   ["actions"]` still lists `run_capture_now`/`pause_schedule` unchanged
   (vestigial, `ADR-029` point 6) — this task does not touch that file.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `SKILLS` grows from 5 to 9 entries; all 4 new entries carry
      `"mutates": True`
- [ ] `run_capture_now` real only for `email-capture`; honest-unavailable
      for every other agent (no new behavior for meeting/todo-capture)
- [ ] `pause_schedule` / `rebuild_person_note` unconditional
      honest-unavailable stubs
- [ ] `build_knowledge` real handler calls through to
      `bootstrap_agent_knowledge`, via a deferred import (no circular
      import) and a thread-bridge (no running-event-loop crash), and sets
      `"history_recorded": True`
- [ ] `_SKILL_HANDLERS` gains exactly 4 new entries
- [ ] `agent_registry.py` / `agent_chat.py` / `agents_router.py` /
      `knowledge_bootstrap.py` / `pending_approvals_router.py` not modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The gate itself (`T01`) and the Approve-endpoint branch (`T02`) — both
  hard prerequisites, not built here.
- The retrofit grant seed for the 5 real agents (`T04`).
- Building real handler behavior for the 5 currently-unwired (agent,
  action) pairs — explicitly rejected by `ADR-029`'s own Alternatives
  Considered.
- Any change to `agents_router.py`'s own dispatch fork — already handles
  these 4 ids automatically via the existing `id in skill_tools.SKILLS`
  membership check (`ADR-029` point 6).

---

## Context / Notes

**Two real wiring subtleties `ADR-029` names as a destination
("call through to the same real functions") without addressing the
mechanics — both resolved here, not guessed, and both load-bearing:**

1. **Circular import.** `skill_registry.py` imports `skill_tools` at
   module load time; `knowledge_bootstrap.py` imports `skill_registry`
   at module load time (its own existing Hub-routed `invoke_skill` call).
   A module-level `from app.business.agent_orchestration import
   knowledge_bootstrap` inside `skill_tools.py` would complete the cycle
   and fail at import time. Resolved via a deferred (function-body)
   import inside `build_knowledge` itself — a standard, safe fix; by the
   time the handler is actually called, both modules have already
   finished loading.
2. **Sync/async boundary.** `bootstrap_agent_knowledge` is genuinely
   `async def` (to match ITS OWN caller's async signature,
   `knowledge_bootstrap.py`'s own module docstring), even though every
   call inside its own body is synchronous. `invoke_skill`/
   `_dispatch_skill`'s own dispatch contract, by contrast, is synchronous
   end-to-end — and this is relied on, as such, by a caller OUTSIDE this
   task's own file scope: `knowledge_bootstrap.py`'s own existing
   Hub-routed call to `invoke_skill` states explicitly, in its own
   module docstring, that "no `await` appears inside this function's own
   body" because every composed call (including `invoke_skill`) is
   synchronous. Making `invoke_skill` itself `async def` to natively
   support this one handler would force edits to `skills_router.py`,
   `agents_router.py`, AND `knowledge_bootstrap.py` — all 3 outside this
   story's own named file scope. The thread-bridge in the Constraints
   above resolves this without touching any of those 3 files.

**Disclosed, known wrinkle NOT fixed by this task (tracked in the parent
story's own `## Notes`, not blocking):** `build_knowledge` invoked via
the chat/direct-trigger dispatch fork (`agents_router.py`'s own
`_invoke_capability` helper, `REQ-SB-39-US-01-T07`) will append a SECOND,
generic history entry on top of `bootstrap_agent_knowledge`'s own
internal one — `_invoke_capability`'s existing result-shape translation
does not forward the `"history_recorded"` key through to
`trigger_action`/`chat()`'s own post-dispatch history-append check, and
fixing that requires editing `agents_router.py`, outside this story's
own named scope. Low real-world severity today: `compass-expert` carries
a standing "stays Autonomous" convention (`REQ-SB-36-US-02`'s own
`_execute_async_action` docstring), and Autonomous mode's own chat/direct
behaviour is unaffected by this story either way (a cosmetic duplicate
history line, not a security/approval-bypass issue) — see the story's
own `## Notes` for the full disclosure and the suggested one-line
fast-follow.

---

## Implementation Log

**2026-08-13/14 — Built and verified live** against the real `.venv`,
real Outlook COM, real Compass Provider, and the real vault. `skill_tools.py`
gained the 4 new `SKILLS` entries (all `"mutates": True`) and 4 new
`@mcp_server.tool()` handlers (`run_capture_now`, `pause_schedule`,
`rebuild_person_note`, `build_knowledge`), plus the new top-level
`agent_registry`/`email_classification`/`asyncio`/`concurrent.futures`
imports. `skill_registry._SKILL_HANDLERS` gained the matching 4 entries.
No other file touched. `SKILLS`/`_SKILL_HANDLERS` both confirmed to hold
exactly 9 entries after the change.

- **[REQ-SB-39-US-02-AC-06] Real `run_capture_now` for `email-capture`
  (Autonomous, then Supervised + Approve):** granted directly, Autonomous
  mode, invoked — the REAL Outlook/Compass capture pipeline ran (100+ real
  `POST https://api.core42.ai/v1/chat/completions` calls observed live,
  confirmed via `Get-NetTCPConnection`/CPU-accumulation liveness checks
  throughout a genuinely long real run — this session's vault had a large
  real backlog, mostly Meetings, not previously processed on-demand;
  `Work/Meetings/` grew from 40 to 56 real notes during this run),
  completing with the exact real result shape `{"available": True,
  "message": "Done — 0 email(s) filed."}` (0 new emails; the backlog was
  in Meetings, which the same function also processes per its own
  existing docstring, unmodified by this task). Set Supervised, invoked
  again — `{"status": "pending", "pending_approval_id": ...}`, confirming
  the real Skill defers exactly like the synthetic one did in `T01`.
  Approved via `pending_approvals_router.approve_pending_approval` (`T02`'s
  new branch) — `status: "approved"`, and a new real `run_event` history
  entry `"Done — 0 email(s) filed."` appended, confirming `_dispatch_skill`
  genuinely re-ran the real handler on Approve, not a fabricated status
  flip. **PASS.**
- **[REQ-SB-39-US-02-AC-06] Honest-unavailable split, confirmed real:**
  `run_capture_now` granted+invoked for `meeting-capture` →
  `{"available": False, "message": "This skill is not yet available — no
  real handler has been built for it."}` — proves the real/stub split is
  by AGENT, not by id (matches `_ACTION_HANDLERS`'s own pre-migration
  shape exactly; meeting-capture's own real classification logic was
  deliberately NOT wired to this on-demand path, per this task's own
  Constraint). `pause_schedule` (any agent) and `rebuild_person_note`
  (`people-producer`) both confirmed unconditionally honest-unavailable.
  **PASS.**
- **[REQ-SB-39-US-02-AC-06] `build_knowledge` real handler, thread-bridge
  proven under a genuinely active event loop:** granted to
  `compass-expert` (Autonomous, its own standing convention), invoked from
  INSIDE a running `asyncio.run(...)` coroutine (mirroring the real
  `agents_router.py` async-route caller shape) — no `RuntimeError`
  ("cannot be called from a running event loop") raised; result
  `{"available": true, "message": "The web research step found nothing
  relevant.", "history_recorded": true}` — the real chain ran end-to-end
  (Hub routing twice, the real `web-research` skill honestly reporting
  unavailable since `compass-expert` is linked to the `"compass"`
  Provider, not `"anthropic-claude"`), matching
  `_run_build_knowledge`'s own identical status→message translation for
  the `no_results` branch exactly. **PASS.**
- **[REQ-SB-39-US-02-AC-07]** `POST /agents/email-capture/skills/
  run_capture_now` (via direct `skills_router.grant_skill`/`revoke_skill`
  calls) then the same for `web-research` — identical `{"granted": True}`
  / `{"revoked": True}` shapes for both a mutating and a read-only skill.
  **PASS.**
- Non-AC smoke check: `agent_registry.AGENTS["email-capture"]["actions"]`
  confirmed unchanged (`run_capture_now`, `view_last_run`,
  `pause_schedule` still present, vestigial). **PASS.**

**Highest-risk property, independently and separately confirmed
(operator-directed, real-caller-agnostic of the long Autonomous run
above):** invoking the REAL migrated `run_capture_now` Skill for
`meeting-capture` under Supervised mode returned `{"status": "pending",
...}` in **0.008 seconds**, with zero Outlook/Compass calls made — proves
the gate check happens strictly BEFORE any real handler dispatch, for the
real migrated Skill, not only the synthetic one. A real `pending_approval`
record was created (`action_id == "run_capture_now"`, `status ==
"pending"`), then declined as cleanup.

**Live-discovered finding, disclosed not silently resolved (this
task's own `gate: flagged` reason):** during the Supervised leg of the
`email-capture` test above, a SECOND, unrelated pending-approval record
(`action_id: None`, `trigger: "background"`, description "Run the
scheduled email-capture step — checks the inbox for new mail and files it
into the vault.") appeared in the real vault state. This is the
PRE-EXISTING, unmodified-by-this-sprint background-scheduler gate inside
`email_classification.py` (`ADR-018` point 4) — not this story's own
Skill gate, not a file this task touched. Root cause: a real, already-
running dev-server process from an earlier/separate session was found
still alive on `localhost:8000` (`Get-NetTCPConnection -LocalPort 8000`
resolved a real listening PID, already observed at high accumulated CPU
time at the very start of this task before any of my own work began) —
its own real, unattended hourly capture-scheduler tick independently fired
against the same real vault while `email-capture` happened to be briefly
`Supervised` during my own test window, a genuine timing coincidence, not
caused by any code this task wrote. **Not resolved (approved/declined) by
me** — it is a real, correctly-gated, legitimate proposal (exactly what
Supervised mode is supposed to produce) that a human should see and act on
directly, not something a coder should silently discard or approve on
their behalf. Left `pending` in the real queue for human review. Confirms
this project's own established "a shared dev vault can carry real
concurrent-session drift" antipattern (`SPRINT-029`) a further time — see
final report / `REVIEW-QUEUE.md`.

**Migration-grant retrofit note:** because `skill_registry._load_state()`
re-applies `_MIGRATION_GRANT_SEED` (which by the time of this task's own
testing already included `T04`'s own 4 new entries, built immediately
after this task to avoid a second full round of live verification) on
every read, the extensive live testing above already exercised — and
implicitly cross-confirmed — `T04`'s own retrofit seed as a side effect
(email-capture/meeting-capture/todo-capture correctly showing
`run_capture_now`+`pause_schedule`, people-producer showing
`rebuild_person_note`, compass-expert showing `build_knowledge`, all with
zero explicit grant calls). `T04`'s own Implementation Log below still
records its own dedicated, deliberate clean-slate verification pass.

gate: flagged 2026-08-14 — the live-discovered stray-dev-server finding
above, for human awareness (not a defect in this task's own code, no file
outside this task's own `## Files to Modify` was touched to investigate
it — purely read-only inspection via `Get-NetTCPConnection`/
`pending_approval_registry.get_pending_approval`).
