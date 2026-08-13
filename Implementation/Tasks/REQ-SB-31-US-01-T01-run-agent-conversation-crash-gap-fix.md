---
id: REQ-SB-31-US-01-T01
title: Close run_agent_conversation's remaining crash gap — wrap tool-loading/graph-invocation in the honest-failure-funnel
parent_story: REQ-SB-31-US-01
requirement_id: REQ-SB-31
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
sprint: "SPRINT-019"
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-31-US-01-T01 — `run_agent_conversation` crash-gap fix

## Parent Story

- Story: [[REQ-SB-31-US-01]] — `../UserStories/REQ-SB-31-US-01-system-health-view.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-31 *System Health View*

---

## Objective

Close the one remaining, real, currently-live gap in
`run_agent_conversation`'s own body — its `await mcp_client.
load_vault_query_tools()` and `await _GRAPH.ainvoke(initial_state)` calls
are not yet wrapped in the same honest-failure-funnel pattern `_call_model`
(the graph's own node) already uses — so an unexpected exception there
(e.g. an MCP client connection failure) returns an honest `{"error": ...}`
instead of propagating as a raw, unhandled 500.

---

## Starting State → End State

**Before / Inputs:**
- `app/business/agent_orchestration/graph.py::run_agent_conversation`
  already funnels two of three failure shapes into `{"error": ...}`:
  Provider not configured (pre-graph short-circuit), and a genuine
  Provider-call failure inside `_call_model` (`except Exception as exc`).
  Its own outer body (tool-loading, graph invocation) has no try/except.

**After / Outputs:**
- Both remaining calls are wrapped in a `try/except Exception as exc:
  return {"error": f"..."}` block — an unhandled exception there now
  returns an honest error result, never a raw 500.
- No other function, node, or file is touched.

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/graph.py` — inside
  `run_agent_conversation`, replace the unwrapped body from `tools =
  await mcp_client.load_vault_query_tools()` through `result = await
  _GRAPH.ainvoke(initial_state)` with:
  ```python
      try:
          tools = await mcp_client.load_vault_query_tools()

          messages = history_entries_to_messages(agent["name"], agent["type"], history)
          messages.append(HumanMessage(content=message))

          initial_state: AgentConversationState = {
              "agent_id": agent_id,
              "messages": messages,
              "model": model,
              "tools": tools,
              "reply": None,
              "error": None,
              "memory": memory or [],
              "extracted_facts": [],
          }
          result = await _GRAPH.ainvoke(initial_state)
      except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel (REQ-SB-31 Scenario 8); closes the one remaining unwrapped gap in this function's own body, never left to propagate as a raw 500
          return {"error": f"Something went wrong while processing this message: {exc}"}
      if result.get("error"):
          return {"error": result["error"]}
      return {"reply": result["reply"], "extracted_facts": result.get("extracted_facts", [])}
  ```
  Everything above the `try:` (the `agent = agent_registry.get_agent(...)`
  line and the `model is None` short-circuit) is unchanged.

---

## Constraints

- Inherits from parent story.
- **Only these two named calls** (`mcp_client.load_vault_query_tools()`,
  `_GRAPH.ainvoke(initial_state)`) plus the trivial glue code between them
  (message-list construction, `initial_state` assembly — inert Python with
  no external call of its own) are brought inside the `try` block. Do not
  wrap the `model is None` short-circuit above it — that path already
  returns its own honest error and must keep doing so unchanged.
- No new logging/observability infrastructure, no change to any other
  function in `graph.py` (`_call_model`, `_execute_tools`,
  `_extract_memory`, the graph-building code) — this is the one
  concretely-identified gap this story closes, not general exception-
  catching middleware (see the story's own Non-Goals).
- The error message must never fabricate a reply — always
  `{"error": str}`, never a `{"reply": ...}` key on this path.

---

## Tests

<!-- AC-08 is backend-only — no screen involved — so its tagged
verification step lives here directly, per the "user-observable outcome"
placement rule (a real chat call is directly observable without a
frontend dependency). -->

**Manual verification steps** (from `src/backend`, backend running on its
documented port `8001`; issue a real HTTP request via
`Invoke-RestMethod`/`curl` against `POST /agents/{agent_id}/chat`, or call
`run_agent_conversation` directly in a throwaway interpreter):

1. `[REQ-SB-31-US-01-AC-08]` Temporarily force an exception in the wrapped
   block (e.g. monkeypatch `mcp_client.load_vault_query_tools` to raise,
   or temporarily point `mcp_client.py`'s loopback URL at a wrong port so
   the connection itself fails) for an agent whose Provider **is**
   available (a real client configured, so the pre-graph short-circuit is
   not what's being tested). Call `run_agent_conversation(agent_id,
   "hello", [])` (or `POST /agents/{agent_id}/chat`). Confirm the return
   value is `{"error": <a real message containing the underlying
   exception text>}` — not a raised exception, not a raw 500, not a
   fabricated `{"reply": ...}`. Revert the temporary fault injection
   afterward and confirm a normal chat call succeeds again.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-31-US-01-AC-08` — an unexpected exception raised while loading
      MCP vault-query tools or while running the conversation graph itself
      returns `{"error": ...}`, never a raw unhandled 500, for an agent
      whose Provider is otherwise available
- [x] The two pre-existing funneled failure shapes (Provider not
      configured; a Provider-call failure inside `_call_model`) are
      unchanged in behavior and message text
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `system_health.py`/`system_health_router.py`/the frontend
  page — `T02`-`T04`, no dependency either way.
- Any new persisted "last unhandled exception" signal for the System
  Health page to read — the story's own Non-Goals.
- General exception-catching/logging middleware for the ASGI app as a
  whole.

---

## Context / Notes

This task has no dependency on `T02`-`T04` and can be built first or in
parallel — it is a pure backend robustness fix to an already-`Done` chat
path, unrelated to the new System Health surface's own read path.

---

## Implementation Log

**Build (2026-08-12).** `run_agent_conversation`'s outer body wrapped
exactly per spec: `tools = await mcp_client.load_vault_query_tools()`
through `result = await _GRAPH.ainvoke(initial_state)` now inside a
`try/except Exception as exc: return {"error": f"Something went wrong
while processing this message: {exc}"}` block. Nothing above the `try:`
(the `agent = agent_registry.get_agent(...)` line, the `model is None`
short-circuit) was touched.

**Verification — `[REQ-SB-31-US-01-AC-08]` (2026-08-12).** Real code,
real failure, not a code-review claim. Used the in-process-monkeypatch
technique this same project already established and recorded in
`Implementation/Learnings.md` (`REQ-SB-33-US-01-T01`'s own pattern): a
throwaway script (kept only in the session scratchpad, never written
into `src/`) imported the real, unmodified
`app.business.agent_orchestration.graph`/`mcp_client` modules directly,
monkeypatched `mcp_client.load_vault_query_tools` in-process to raise
`RuntimeError("INDUCED-VERIFY-AC-08: simulated MCP client connection
failure")`, then called the real `run_agent_conversation("vault-qa",
"hello", [])` directly — `vault-qa`'s Provider (Compass) is genuinely
available, so this exercises the crash-gap path, not the pre-graph
Provider-short-circuit path.

- **Case A (induced failure):** returned exactly
  `{"error": "Something went wrong while processing this message:
  INDUCED-VERIFY-AC-08: simulated MCP client connection failure"}` — no
  raised exception propagated out of `run_agent_conversation`, no
  `"reply"` key present (never a fabricated reply on this path). **PASS.**
- **Case B (monkeypatch reverted):** re-called the same function with the
  real `mcp_client.load_vault_query_tools` restored — a real Compass call
  completed normally, returning `{"reply": ..., "extracted_facts": [...]}`.
  Confirms the fix does not regress the ordinary, successful chat path.
  **PASS.**
- The two pre-existing funneled failure shapes (Provider-not-configured
  pre-graph short-circuit; the `_call_model` Provider-call-failure
  `except Exception`) were not touched by this diff — confirmed by direct
  inspection of the final file: every line of both paths is byte-identical
  to before this task's edit, both still outside the newly-added `try`
  block. Not re-exercised live (no code change to re-verify), per the
  task's own Acceptance Criteria checklist item.

No monkeypatched file was ever edited or needed reverting — the
throwaway script's own local reference reassignment
(`mcp_client.load_vault_query_tools = ...`) and its `finally:` restore
are both scoped to that one script's process memory only, never touching
`src/`.

**Assumption logged for human spot-check (scope-internal judgement call,
not an escalation):** verified via a standalone throwaway script that
imports the real modules directly (bypassing the shared, already-running
dev backend's own HTTP surface), rather than a live `POST
/agents/vault-qa/chat` call against the shared backend process — this
avoids inducing a real failure inside the shared backend's own live
process (which other concurrent verification could be depending on) and
matches this exact established pattern's own prior precedent
(`REQ-SB-33-US-01-T01`). The real, unmodified `run_agent_conversation`
function is exercised either way; only the transport (in-process call vs.
HTTP round-trip) differs.

**On `BUG-007` (`graph.py::_call_model`'s synchronous blocking
`model.invoke()` call, unconfirmed root cause of a prior dev-backend
hang):** this task's own verification made its real Compass call (Case B,
above) from an isolated, single-purpose script's own event loop, not
through the shared dev backend's own single event loop serving concurrent
requests — so it does not exercise the concurrency condition `BUG-007`
describes, and provides no new confirming or disconfirming evidence
either way. `BUGS.md`/`MEMORY.md` left unchanged for `BUG-007`,
honestly, rather than a speculative update with no real new evidence.

`gate: clear` 2026-08-12 — no MUST-FLAG trigger fired: no material
assumption beyond the scope-internal judgement call logged above, no
`Draft`/unfinalised requirement relied on, no ADR touched, no
`ESCALATIONS.md` entry, not oversized, AC-08 fully verified (not a
verification failure), no contradictory inputs, no genuine ambiguity.
`status: Done`.
