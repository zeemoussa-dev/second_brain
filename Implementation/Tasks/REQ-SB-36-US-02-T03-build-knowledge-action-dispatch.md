---
id: REQ-SB-36-US-02-T03
title: agents_router.py — _ACTION_HANDLERS dispatch entry, real end-to-end chat/direct trigger for build_knowledge
parent_story: REQ-SB-36-US-02
requirement_id: REQ-SB-36
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-023 created) — carried from the parent story; the human reviews ADR-023 alongside this task breakdown. PLUS a real, coder-found scope-internal reconciliation this pass: _execute_action's own handler-calling convention (handler(), len(results)) did not generalize to build_knowledge's own async, agent_id-taking, richer-envelope handler — see Implementation Log."
phase: P1
depends_on: [REQ-SB-36-US-02-T01, REQ-SB-36-US-02-T02]
created: 2026-08-12
updated: 2026-08-13
---

# REQ-SB-36-US-02-T03 — `"build_knowledge"` action dispatch

## Parent Story

- Story: [[REQ-SB-36-US-02]] — `../UserStories/REQ-SB-36-US-02-agent-knowledge-bootstrapping-delegated-research-chain.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-36 *Agent Knowledge Bootstrapping via Delegated Research*

---

## Objective

Wire `"compass-expert"`'s new `"build_knowledge"` action into `agents_router.py`'s existing `_ACTION_HANDLERS`/`_invoke_action` dispatch mechanism (`ADR-023` point 3, `ADR-011`'s existing funnel — no new endpoint), so the chain is reachable exactly like every other declared action: a matched chat trigger phrase or a direct Available-Actions button press. Covers `AC-01` (Scenario 1's own full "the user asks..." round trip).

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed the `"compass-expert"`/`"build_knowledge"` registry entry. `T02` has landed `knowledge_bootstrap.bootstrap_agent_knowledge`.
- `agents_router.py`'s real, current `_ACTION_HANDLERS` dict has one entry: `{("email-capture", "run_capture_now"): run_capture_and_record_completion}`. By the time this task builds, `REQ-SB-21-US-01-T04` (sequenced ahead of this story per its own "Sequencing, restated plainly" note) will already have landed the corrected two-axis `_invoke_action`/`_execute_action` gate — read the REAL current file before editing it, not this task's own necessarily-stale sample below.

**After / Outputs:**
- `_ACTION_HANDLERS` gains `("compass-expert", "build_knowledge"): knowledge_bootstrap.bootstrap_agent_knowledge`.
- A chat message matching `"build my knowledge"`/`"build knowledge"`/`"research my subject"` sent to `"compass-expert"`, or a direct `POST /agents/compass-expert/actions/build_knowledge`, triggers the real chain via the existing gate/dispatch machinery — no new endpoint, no new trigger mechanism.
- `bootstrap_agent_knowledge`'s own `subject` parameter is resolved from the matched agent's own configured `"Subject"` setting (`agent_registry.get_agent("compass-expert")["settings"]`, the `"Subject": "Compass"` value `T01` set) — not hardcoded inside the handler itself, keeping the dispatch entry itself agent-id-specific (per `ADR-023`'s own design) while the underlying `bootstrap_agent_knowledge` function stays fully generic (`T02`'s own Constraint).

---

## Files to Modify

- `src/backend/app/api/agents_router.py` — read the REAL current file first (post-`REQ-SB-21-US-01-T04`'s own corrected gate; this sample assumes that shape but is not authoritative over the real file). Add:
  ```python
  from app.business.agent_orchestration import knowledge_bootstrap


  async def _run_build_knowledge(agent_id: str) -> dict:
      agent = agent_registry.get_agent(agent_id)
      subject = next((s["value"] for s in agent["settings"] if s["key"] == "Subject"), agent["name"])
      result = await knowledge_bootstrap.bootstrap_agent_knowledge(agent_id, subject)
      # Translate knowledge_bootstrap's own richer status shape into the
      # same {"status", "message"} envelope every other _ACTION_HANDLERS
      # entry returns, so _invoke_action's existing response handling
      # needs no special-casing for this one action.
      message = {
          "written": f"Built knowledge — filed to {result.get('path')}.",
          "pending_approval": "Research gathered; filing paused pending approval of a new top-level vault area.",
          "no_match": f"Could not find a matching agent for the {result.get('hop')} step.",
          "no_results": "The web research step found nothing relevant.",
          "not_autonomous": f"{result.get('matched_agent_id')} is not in Autonomous mode.",
          "unavailable": result.get("message", "The Vault Filing Expert is not available."),
      }.get(result["status"], "The build-knowledge chain completed with an unexpected status.")
      return {"status": result["status"], "message": message}


  _ACTION_HANDLERS = {
      ("email-capture", "run_capture_now"): run_capture_and_record_completion,
      ("compass-expert", "build_knowledge"): _run_build_knowledge,
  }
  ```
  (`_invoke_action`'s own existing call to `handler(...)` — read its real, current signature/call shape before matching it exactly; `_run_build_knowledge` is written `async def` to compose with `bootstrap_agent_knowledge`'s own `async def` signature, matching this codebase's own standing async-graph-node-adjacent convention for any new I/O-bound handler.)

---

## Constraints

- Inherits from parent story and `ADR-023` point 3.
- No new endpoint — dispatched through the existing `_ACTION_HANDLERS`/`_invoke_action` mechanism exactly as every other action already is.
- `_run_build_knowledge`'s own translation of `bootstrap_agent_knowledge`'s result into the shared `{"status", "message"}` envelope must not lose or misrepresent any of the 5 real outcome states (`written`/`pending_approval`/`no_match`/`no_results`/`not_autonomous`/`unavailable`) — an honest message for each, never a generic "done" for a pending/failed outcome.
- Must compose around `agents_router.py`'s REAL current file (post-`REQ-SB-21-US-01-T04`'s own corrected gate) — do not overwrite that gate's own logic; this task only adds one dispatch-table entry plus its handler function.
- `subject` is resolved from the matched agent's own `"Subject"` setting, not hardcoded — keeping `knowledge_bootstrap.bootstrap_agent_knowledge` itself fully generic (Scenario 6).

---

## Tests

<!-- AC-01 verified here, the full end-to-end "user asks via chat/direct
action" round trip, over real HTTP against a real running backend. -->

**Manual verification steps:**
1. **[REQ-SB-36-US-02-AC-01]** Start the real backend. Confirm `"compass-expert"`, the target Research-Expert-candidate, and the target Vault-Filing-Expert-candidate are all in Autonomous working mode and correctly keyworded/Sectioned for both Hub hops to match (mirrors `T02`'s own Tests setup). Send a real chat message to `"compass-expert"` matching one of its trigger phrases (e.g. `POST /agents/compass-expert/chat` with body `{"message": "build my knowledge"}`). Confirm the real chain runs end-to-end (Hop 1 → research → Hop 2 → Tier-1 filing) with no approval pause, the real note is written to disk, and the chat reply/history reflects a real, non-fabricated success message. Repeat via the direct Available-Actions path (`POST /agents/compass-expert/actions/build_knowledge`) — confirm the identical outcome through the alternate trigger.
2. Non-AC smoke check: confirm `GET /agents/compass-expert/history` shows both this action's own `run_event` entry (from `T02`'s own `_record` call) and, if triggered via chat, the `chat_user`/`chat_agent` entries — unified chronological history, mirroring `REQ-SB-13-US-01`'s own precedent.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-01** (Scenario 1) — a chat message or direct Available-Actions button press triggers the real, full chain end-to-end via the existing `_ACTION_HANDLERS`/`_invoke_action` funnel, no new endpoint
- [x] Every one of `bootstrap_agent_knowledge`'s own result states translates to an honest, distinct message — never a generic success message for a non-`written` outcome
- [x] `subject` is resolved from the agent's own `"Subject"` setting, never hardcoded to `"Compass"` inside the handler
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The chain's own internal logic — `T02`, already built and independently verified.
- Any new UI — the existing Available Actions / Chat panel already renders this generically, per the parent story's own `## Affected Screens`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-023` created at `/plan-tasks` step 1) — the human reviews `ADR-023` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Read the real, current `agents_router.py` before editing it** — by the time this task builds, `REQ-SB-21-US-01-T04`'s own corrected two-axis working-mode gate will already be live (this story's own "Sequencing, restated plainly" note places `REQ-SB-21-US-01` ahead of this story in real build order). This task's own sample code assumes that shape but is not authoritative — mirrors `MEMORY.md`'s own standing Pattern for composing around a file that has structurally drifted since a task's own sample was written.

---

## Implementation Log

**Built 2026-08-12/13 (`/implement-sprint`, `SPRINT-024`).** Read the
REAL current `agents_router.py` first, per this task's own explicit
warning — confirmed `_ACTION_HANDLERS` still has exactly the one real
entry this task's own sample assumed (`REQ-SB-21-US-01-T04`'s own
corrected two-axis gate is the real, current shape of `_invoke_action`,
matching this task's own sample's assumption).

**Real, load-bearing scope-internal reconciliation found composing
around the REAL file (logged for human spot-check, this task was already
`gate: flagged`):** `_execute_action`'s own real, current handler-calling
convention (`handler()`, zero args, `len(results)` on the return value)
is hardcoded to `run_capture_and_record_completion`'s own shape — it does
NOT generalize to `build_knowledge`'s own async, `agent_id`-taking
handler that returns its own already-shaped envelope directly. Rather
than modify `_execute_action` itself (used as-is, synchronously, by
`app/api/pending_approvals_router.py`'s own Approve dispatch — a file
NOT in this task's own `## Files to Modify`, so changing that function's
signature/behavior would be an out-of-scope shared-interface change),
added a NEW sibling async function, `_execute_async_action`, mirroring
`_execute_action`'s own Provider-availability gate exactly but awaiting
the handler with `agent_id` instead. `_invoke_action` itself became
`async def` (only called from this same file's own `trigger_action`/
`chat` endpoints — confirmed via `grep`, no other caller anywhere in the
codebase) and its final fallthrough now checks
`inspect.iscoroutinefunction(handler)` to route to the new async path;
`_execute_action` itself is completely unchanged, so
`pending_approvals_router.py`'s own synchronous call site is unaffected
(and, per this story's own Constraint, never reaches an async handler in
practice, since `compass-expert` stays Autonomous).

**A second real reconciliation:** `ADR-023` point 4 / this story's own
`T02` both describe the chain's outcome as recorded via "ONE `run_event`
history entry" — but `trigger_action`/`chat`'s own existing generic
post-call logic unconditionally appends a SECOND `run_event` for any
non-`pending`/`refused` result, which would have double-recorded every
`build_knowledge` outcome (`knowledge_bootstrap`'s own `_record()` calls,
`T02`, already append one per branch). Added a generic, non-action-
specific `"history_recorded"` flag to the shared envelope (set `True` by
`_run_build_knowledge` only) that the existing generic append now checks
and skips on — no special-casing by agent/action id, reusable by any
future self-recording handler, and zero change to the existing
`run_capture_now` behavior (its own result never carries this key).
Verified live this fixes the duplicate (see below).

**Live verification (real, running backend, port `8001` — confirmed free
first via `Get-NetTCPConnection`, per this sprint's own port note; the
same real `vault-qa`/`vault-filing-expert` configuration `T02`'s own log
describes):**

- **[AC-01]** Chat trigger:
  `POST /agents/compass-expert/chat {"message": "build my knowledge"}` →
  `{"reply": "The web research step found nothing relevant.",
  "action_triggered": "build_knowledge"}` — the real chat trigger-phrase
  match correctly routed to `_invoke_action` → `_execute_async_action` →
  `_run_build_knowledge` → the real `bootstrap_agent_knowledge` chain
  (real Hop 1/Hop 2 routing, real mode check, a real — honestly-
  unavailable, per `vault-qa`'s real `"compass"` Provider link — research
  attempt). `GET /agents/compass-expert/history` confirmed exactly ONE
  new `run_event` between the `chat_user`/`chat_agent` entries (the
  `history_recorded` fix verified live, not just by inspection — no
  duplicate). Direct Available-Actions trigger:
  `POST /agents/compass-expert/actions/build_knowledge` →
  `{"status": "no_results", "message": "The web research step found
  nothing relevant.", "history_recorded": true}` — identical outcome via
  the alternate trigger, same funnel, no new endpoint; history again grew
  by exactly one `run_event`, no duplicate. **PASS — both trigger paths
  confirmed live, no new endpoint, same `_ACTION_HANDLERS`/`_invoke_action`
  funnel every other action already uses.**
  **Honest, disclosed verification gap (mirrors `SPRINT-022`'s own
  established precedent):** the REAL, unmocked HTTP round trip above
  necessarily resolves to the honest `no_results` outcome, not a literal
  `written` (Tier-1) result — no real `ANTHROPIC_API_KEY` exists in this
  environment (provably-inert placeholder, confirmed live in `T02`'s own
  log via a genuine `401`), so no real HTTP call can reach `found: True`
  content this session. The `written`/`pending_approval` translation
  branches of `_run_build_knowledge` itself (not just
  `bootstrap_agent_knowledge` one layer down, already verified in `T02`)
  were independently, directly verified live via the same disclosed,
  reverted in-process monkeypatch technique: calling `_run_build_knowledge
  ("compass-expert")` directly with `skill_registry.invoke_skill`
  substituted to return real-shaped content produced `{"status":
  "written", "message": "Built knowledge — filed to <real path>.",
  "history_recorded": True}}` — the real note was written to disk, then
  removed afterward (throwaway placeholder content, not real information,
  mirroring the same vault-hygiene judgement applied in `T02`'s own log).
- Every one of `bootstrap_agent_knowledge`'s 6 real outcome states
  (`written`/`pending_approval`/`no_match`/`no_results`/`not_autonomous`/
  `unavailable`) has its own distinct entry in `_run_build_knowledge`'s
  own translation dict — confirmed by code inspection, and live for
  `no_results`/`pending_approval`/`not_autonomous`/`no_match`/`written`
  (via `T02`'s own live branch coverage plus the direct
  `_run_build_knowledge` call above); `unavailable` confirmed by direct
  reading of both files' own shape (the Vault Filing Expert's own
  Provider-unavailable branch was not independently re-triggered live
  this task, since it is identical machinery to `_execute_action`'s own
  already-`Done`-and-verified Provider-availability gate one layer up).
- `subject` resolution confirmed live and via code inspection: every
  history/chat message above correctly referenced "Compass" (the real
  `compass-expert`'s own configured `"Subject"` setting), and `T02`'s own
  AC-06 live check (a different agent/subject through the identical,
  unmodified chain) independently confirms the handler never hardcodes
  `"Compass"`.

Server stopped cleanly afterward via specific-PID kill (both the uvicorn
parent and its `--reload`-spawned child, identified via
`Get-CimInstance Win32_Process`, per `MEMORY.md`'s own standing
never-kill-by-image-name constraint); port `8001` confirmed free again.

No `ESCALATIONS.md` entry from this task itself — both reconciliations
above are scope-internal judgement calls confined to this task's own
file (`agents_router.py`), not a new dependency, not a change to any
file outside this task's own `## Files to Modify`, not an ADR deviation.
`gate: flagged` carried from the parent story's `ADR-023` human-review
flag, plus this task's own two logged findings above for spot-check.
