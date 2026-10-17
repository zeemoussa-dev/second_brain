---
id: REQ-SB-95-US-03-T02
title: The validating call gate — action_invocation.py, POST /actions/{action_id}/call, and the Action-call ledger
parent_story: REQ-SB-95-US-03
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "Six scope-internal judgement calls, all recorded in the Implementation Log and none of them blocking: every gate refusal is ONE status (409) carrying the verdict as a dict detail, including an unknown action id where GET /actions/{id} returns 404; a validated call records the transitional outcome `not_dispatched` rather than one of ADR-033's four values, because T03 owns dispatch; a blank caller_agent_id is refused inside the caller-not-permitted class rather than being admitted by [\"*\"]; a required input supplied as null counts as not supplied; the resolution re-check goes through ActionManager.resolution_report() rather than the private _ResolutionSources; and the tests use fastapi.testclient.TestClient (which IS httpx.ASGITransport behind a sync wrapper) rather than ASGITransport directly, the same call T03 of US-02 made. Spot-check only — no REVIEW-QUEUE entry was added, per that file's standing 2026-09-06 instruction not to refill it with scope-internal judgement-call spot-checks."
phase: P2
depends_on: [REQ-SB-95-US-02-T03]
created: 2026-10-16
updated: 2026-10-18
---

# REQ-SB-95-US-03-T02 — The Validating Call Gate + the Action-Call Ledger

## Parent Story

- Story: [[REQ-SB-95-US-03]] — `../UserStories/REQ-SB-95-US-03-published-catalogue-and-call-enforcement.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Build the one validating door — unknown id, unknown or missing required input,
caller not permitted, implementation no longer resolving — so the refusal comes
from the framework and no prompt text can route around it, with every call
recorded in a ledger.

---

## Starting State → End State

**Before / Inputs:**

- `app/api/actions_router.py` exists with CRUD (`REQ-SB-95-US-02-T03`); there is
  no call route.
- There is no `business/logic/action_invocation.py` and no `ActionCalls` store.
- `business/logic/agent_chat_stream.py` is an SSE relay that *observes*
  `tool.start` / `tool.complete` after the fact — it is **not** an interception
  point and must not be touched by this task (`ADR-033`).

**After / Outputs:**

- `app/data_access/action_calls.py` — raw I/O only over
  `<DATA_PATH>/data/ActionCalls/<call_id>.json`.
- `app/business/logic/action_invocation.py` — the one gate. In order, before any
  dispatch: the action id exists in the live catalogue; the caller's agent id is
  in `allowed_callers` (or `allowed_callers == ["*"]`); every required input is
  supplied and no unknown input is passed; the implementation still resolves.
  Each failure returns a refusal naming the specific cause and writes a
  `refused:<reason>` ledger record.
- `POST /actions/{action_id}/call` on `actions_router.py`, taking the caller's
  agent id and the inputs, returning the gate's verdict.
- Validation completes before dispatch begins — **nothing is half-performed**.
- The gate reads the **live catalogue**, never the published SOUL text.

---

## Files to Modify

- `src/backend/app/data_access/action_calls.py` (new)
- `src/backend/app/business/logic/action_invocation.py` (new)
- `src/backend/app/api/actions_router.py` (the call route)
- `src/backend/tests/test_action_invocation_gate.py` (new)

---

## Constraints

- Inherits from parent story.
- **Enforcement is a gate, not an instruction** (`ADR-032`). No part of this may
  depend on prompt text.
- **No silent fallback and no guessing:** a missing required input is refused by
  name; no default, inferred or substituted value, ever.
- The gate reads the live catalogue — never the published block.
- `agent_chat_stream.py` is not touched by this task.
- Dispatch itself is `T03`; this task validates and, on success, hands off to a
  dispatch seam `T03` fills (a clearly-named not-yet-implemented branch is
  correct here, provided a successful validation does not claim an operation was
  performed).
- The ledger is instance data — excluded from artifact export, never written
  into the repository.

---

## Tests

**Automated tests** — `src/backend/tests/test_action_invocation_gate.py`, run
with `pytest tests/test_action_invocation_gate.py` from `src/backend`, driving
the real app through `httpx.ASGITransport(app=app)` with the Actions and
ActionCalls data access monkeypatched onto a tmp dir.

1. `[REQ-SB-95-US-03-AC-03]` `POST /actions/does-not-exist/call`; assert the
   call is refused, the response names the unknown id, no dispatch seam was
   entered (spy asserts zero calls), and a `refused:` ledger record naming the
   unknown id was written.
2. `[REQ-SB-95-US-03-AC-04]` Call a catalogued Action with a required input
   omitted; assert the refusal names that input by name, that no value was
   substituted anywhere in the recorded inputs, that nothing was dispatched, and
   that the ledger records the refusal.
3. `[REQ-SB-95-US-03-AC-04]` Call the same Action with an input it does not
   declare; assert the refusal names the unknown input rather than silently
   dropping it.
4. `[REQ-SB-95-US-03-AC-07]` Call an Action whose `allowed_callers` is
   `["other-agent"]` as `this-agent`; assert the refusal states this caller may
   not run that action, nothing is dispatched, and the ledger records it. Then
   set `allowed_callers: ["*"]` and assert the same caller is accepted.
5. `[REQ-SB-95-US-03-AC-02]` Call a fully valid, non-confirmation Action with
   every required input; assert validation passes, the ledger record carries the
   caller, the action id and the validated inputs, and the dispatch seam is
   entered exactly once with those validated inputs.
6. `[REQ-SB-95-US-03-AC-02]` Make the implementation stop resolving, then call;
   assert the gate refuses naming what no longer resolves (the second line
   behind `REQ-SB-95-US-02-T02`'s save-time check) and nothing is dispatched.

**Manual verification steps:**

1. `[REQ-SB-95-US-03-AC-03]` With the backend running, `POST
   http://127.0.0.1:8001/actions/not-a-real-action/call` from PowerShell and
   confirm the real refusal body and the real ledger file written under the
   configured data path.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] One gate module refusing all four failure classes, naming each cause
- [x] `POST /actions/{action_id}/call` on the existing Actions router
- [x] Every call outcome recorded in `<DATA_PATH>/data/ActionCalls/<call_id>.json`
- [x] Validation completes before any dispatch; nothing half-performed
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Dispatch by implementation kind — `T03`.
- Confirmation and the single-use grant — `T04`.
- The runner Skill and the agent-facing refusal wording — `T05`.

---

## Context / Notes

`architecture.md` → **§The Action Call Gate** and **§Confirmation and the
Action-Call Ledger**; `ADR-033` decides the surface, the caller identity and why
the in-app chat path cannot be the chokepoint. The trust boundary is loopback
and is stated honestly in `ADR-033`'s Consequences — this task does not sandbox
Hermes and must not claim to.

---

## Implementation Log

**Coder, 2026-10-18 — `Done`.**

### Verification

Baseline measured before the first edit: **481 passed**, 0 failed (`pytest -q`,
`src/backend`, 42.70s). After: **487 passed**, 0 failed (36.39s) — the six new
tests in `tests/test_action_invocation_gate.py` and nothing else moved. Neither
known flake fired. No frontend file was touched, so no `tsc` pass was needed.

**Where this task's writes land, proved BEFORE the suite was run with the new
code (`ESC-072`'s lesson applied).** The gate writes one ledger file per call, at
`settings.second_brain_data_path/data/ActionCalls/<call_id>.json`, and nothing
else. Measured behind a write-intercepting pytest plugin that wrapped
`Path.write_text/write_bytes/open/mkdir/touch/unlink/rename/replace`,
`builtins.open`, `os.replace/rename/remove` and `shutil.rmtree/copyfile/copytree`,
and additionally made `AgentManager.update`, `AgentManager.publish_action_catalogue`,
`HermesProfiles.write_soul` and `HermesProfiles.write_agent_json` raise on entry:

- 45 write calls intercepted across the six tests;
- **every one landed under pytest's own `tmp_path`** (`…/AppData/Local/Temp/pytest-of-<user>/pytest-NNN/…`),
  plus `.pytest_cache` and `\\.\nul`, both pytest's own;
- **zero** writes under the configured data path, zero matching `SOUL`,
  `Agent.json`, `profiles` or the vault;
- **`hermes seams entered: none`.**

That is by construction, not by luck: the gate reads the LIVE catalogue
(`ADR-033`) and never an agent's published text, so no code path here opens a
profile. This file is therefore safe to run on a real install while `T01`'s
publication trigger stays unwired.

| AC-ID | Step | Observed |
|---|---|---|
| `REQ-SB-95-US-03-AC-03` | Automated test 1 — `POST /actions/does-not-exist/call` | **Pass.** 409 with `outcome: "refused:unknown_action"`, `accepted: false`, and the refusal naming the id: *"there is no action 'does-not-exist' in this install's catalogue, so it cannot be called"*. The dispatch spy recorded zero entries. Exactly one ledger file exists, its `call_id` equals the verdict's, and it carries `refused:unknown_action` plus the same sentence naming the unknown id. |
| `REQ-SB-95-US-03-AC-04` | Automated test 2 — a required input omitted | **Pass.** 409, `refused:missing_required_input`, refusal names `'scope'` by name. The ledger record's `inputs` is exactly `{"force": true}` — the string `scope` does not appear anywhere in the recorded inputs, so nothing was defaulted, inferred or substituted. Zero dispatch entries. |
| `REQ-SB-95-US-03-AC-04` | Automated test 3 — an input the Action does not declare | **Pass.** 409, `refused:unknown_input`, refusal names `'recurse'` and says it was not dropped. The ledger records the inputs as the caller sent them (`scope` + `recurse`), so the refusal is checkable against what actually arrived. Zero dispatch entries. |
| `REQ-SB-95-US-03-AC-07` | Automated test 4 — `allowed_callers: ["other-agent"]` called as `this-agent`, then `["*"]` | **Pass.** First call: 409, `refused:caller_not_permitted`, *"agent 'this-agent' may not run action 'refresh-the-index'"*, zero dispatch entries, ledger records the refusal. After `PUT`ting `allowed_callers: ["*"]` — same caller, same inputs — the call is accepted (200) and dispatch is entered once as `this-agent`. The only thing that changed the answer was the catalogue. |
| `REQ-SB-95-US-03-AC-02` | Automated test 5 — a fully valid, non-confirmation Action with every required input | **Pass.** 200, `accepted: true`, `refusal: null`. The dispatch seam was entered **exactly once**, with exactly `{"scope": "Projects", "force": true}`. The single ledger record carries the caller (`cbo-agent`), the action id and those validated inputs under the verdict's own `call_id`. The outcome is `not_dispatched` and the detail says dispatch is not implemented yet — a validated call does **not** claim an operation was performed. |
| `REQ-SB-95-US-03-AC-02` | Automated test 6 — the implementation stops resolving after the save | **Pass.** The Skill resolved at save time and was then undeployed; the call is refused 409 `refused:implementation_does_not_resolve`, naming the skill and *"is not deployed on this install"* — `ActionManager`'s own sentence, so the gate and the catalogue screen cannot disagree. Zero dispatch entries; the ledger records the refusal. |
| `REQ-SB-95-US-03-AC-03` | Manual step 1 — real backend on `127.0.0.1:8001`, real refusal body, real ledger file | **Pass.** `POST /actions/not-a-real-action/call` with `{"caller_agent_id":"cbo-agent","inputs":{}}` returned **409** and verbatim: `{"detail":{"call_id":"78c041cfff5c48989ab50b04f003116d","action_id":"not-a-real-action","caller_agent_id":"cbo-agent","accepted":false,"outcome":"refused:unknown_action","refusal":"there is no action 'not-a-real-action' in this install's catalogue, so it cannot be called","detail":null,"inputs":{}}}`. A real file appeared at `<DATA_PATH>/data/ActionCalls/78c041cfff5c48989ab50b04f003116d.json` holding the same `call_id`, `action_id`, `caller_agent_id`, `outcome`, `refusal` and a `recorded_at` timestamp. (Two earlier probe calls left their own records beside it — real refusals of real calls, left in place: the ledger is an append-only record of what happened, and it is instance data outside the repository.) |

### Judgement calls inside scope (for human spot-check)

1. **Every gate refusal is ONE status — 409 — carrying the whole verdict as a
   dict `detail`, including an unknown action id**, where `GET /actions/{id}`
   returns 404 for the same id. The caller is a runner Skill relaying words to an
   operator: it must reach the refusal sentence, the reason token and the
   `call_id` without first branching on which status arrived, and a refused call
   is not "nothing found" — a real ledger record was created for it. 2xx stays
   reserved for a call that passed the gate, so no client can read a refusal as a
   success. 409 is also already this router's refusal code.
2. **A validated call records `not_dispatched`, which is not one of `ADR-033`'s
   four outcome values.** Dispatch is `T03`. Recording `performed` would be the
   fabricated outcome this story exists to prevent, and recording a refusal would
   be false. The ledger is written **twice** for an accepted call — `validated`
   before the seam is entered, then whatever the seam reports — so a call that
   crashes mid-dispatch leaves a record saying only that it was allowed to
   proceed. `T03` should need to change nothing but the seam's body.
3. **A blank `caller_agent_id` is refused inside the caller-not-permitted class**
   rather than being admitted by `allowed_callers: ["*"]`. The wildcard means
   every agent and an empty string is not an agent; believing it would record a
   call nobody made. This is not a fifth failure class — it is the second one,
   closed.
4. **A required input supplied as `null` counts as not supplied.** Passing it to
   dispatch would hand the operation a value the caller never had, which is the
   substitution `ADR-032` forbids. An empty string is a real value and is left
   alone — the gate refuses what was not asked for, it does not judge what was.
5. **The resolution re-check goes through `ActionManager.resolution_report()`**,
   the Manager's public, never-cached read, rather than reaching into the private
   `_ResolutionSources`. It costs a whole-catalogue pass per call, and buys that
   the gate and the catalogue screen can never disagree about why one Action is
   broken. An Action the report does not cover is treated as broken, never as
   fine — `actions_router.py`'s list already takes that stance.
6. **The tests drive `fastapi.testclient.TestClient`, not `httpx.ASGITransport`
   directly**, as this task's `## Tests` section words it. `TestClient` *is*
   `ASGITransport(app=app)` behind a sync wrapper; no test in this repo uses
   `ASGITransport` directly and thirteen use `TestClient`. Same call
   `REQ-SB-95-US-02-T03` made and recorded.

### Not done here, deliberately

- **Confirmation is untouched** (`T04`). An Action with `needs_confirmation: true`
  is validated like any other today; nothing is performed by anything in this
  task, so no confirmation requirement can currently be bypassed — but `T03`
  fills the dispatch seam, and **`T04` must insert the confirmation check between
  a complete validation and that seam** (the comment marking that spot is in
  `call_action`).
- `agent_chat_stream.py` was not touched (`ADR-033`).
- The ledger is excluded from artifact export **by construction**: `artifact_export.py`
  exports named artifact kinds and a call record is not a kind. No export file was
  edited, and none needed to be.
