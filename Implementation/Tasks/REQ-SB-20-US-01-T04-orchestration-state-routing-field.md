---
id: REQ-SB-20-US-01-T04
title: agent_orchestration/state.py — add hub_routing_result field to AgentConversationState
parent_story: REQ-SB-20-US-01
requirement_id: REQ-SB-20
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-017 created) — carried from the parent story; the human reviews ADR-017 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-25-US-01-T02]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-20-US-01-T04 — `agent_orchestration/state.py` routing-outcome field

## Parent Story

- Story: [[REQ-SB-20-US-01]] — `../UserStories/REQ-SB-20-US-01-section-hub-intelligence-and-cross-section-routing.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-20 *Section Hub Intelligence & Cross-Section Routing*

---

## Objective

Extend `AgentConversationState` (`app/business/agent_orchestration/state.py`, built by `REQ-SB-25-US-01-T02`) with the one new field `ADR-017`'s own Consequences names as expected: a routing-outcome field so `T05`'s new `route_hub_request` node can pass its result back into `call_model`'s replayed turn.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-25-US-01-T02` has landed — `app/business/agent_orchestration/state.py` exists with `AgentConversationState` (verbatim, that task's own code block):
  ```python
  class AgentConversationState(TypedDict):
      agent_id: str
      messages: list[BaseMessage]
      model: BaseChatModel | None
      tools: list
      reply: str | None
      error: str | None
  ```

**After / Outputs:**
- `AgentConversationState` gains one new key: `hub_routing_result: dict | None`.
- `history_entries_to_messages` is **unchanged** — this task touches only the `TypedDict` definition.

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/state.py` — replace the
  `AgentConversationState` definition with:
  ```python
  class AgentConversationState(TypedDict):
      agent_id: str
      messages: list[BaseMessage]
      model: BaseChatModel | None
      tools: list
      reply: str | None
      error: str | None
      hub_routing_result: dict | None
  ```
  Also extend the module's own docstring/comment context minimally, if
  present, to note the field's origin — not required if the existing
  docstring makes no per-field claims (check the real landed file; do not
  invent a docstring rewrite beyond what's needed to add the one field).

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering (`ADR-003`) — this module stays pure business/state-schema logic, no HTTP concerns, no direct file I/O.
- This task adds exactly **one** new key — `hub_routing_result: dict | None`. Do not rename, remove, or change the type of any existing key (`agent_id`/`messages`/`model`/`tools`/`reply`/`error`).
- `history_entries_to_messages` — untouched, byte-for-byte, by this task.
- No LangGraph `StateGraph`/model/tool/node code here — that's `T05` (`graph.py`).
- Every caller that currently constructs an `AgentConversationState` literal (`REQ-SB-25-US-01-T07`'s `run_agent_conversation`) will need `"hub_routing_result": None` added to its own initial-state dict once `T05` extends that function — this task does **not** touch `graph.py` itself, only the `TypedDict` shape it will need to satisfy.

---

## Tests

<!-- This task has no locked AC of its own — a TypedDict field addition has
no directly observable HTTP/user-facing outcome by itself; every locked AC
is verified once T05 actually populates and consumes this field end-to-end.
This task's own verification is a non-AC smoke check, mirroring
REQ-SB-25-US-01-T02's own precedent for the identical shape of task. -->

**Manual verification steps:**
1. Non-AC smoke check: in a throwaway interpreter against `src/backend`'s
   `.venv` (`PYTHONPATH` set so `app` imports resolve), `from
   app.business.agent_orchestration.state import AgentConversationState`;
   confirm `AgentConversationState.__annotations__` (or
   `typing.get_type_hints(AgentConversationState)`) includes a
   `hub_routing_result` key, and that every one of the 6 pre-existing keys
   (`agent_id`/`messages`/`model`/`tools`/`reply`/`error`) is still present
   and unchanged.
2. Non-AC smoke check: confirm `history_entries_to_messages` still behaves
   identically to `REQ-SB-25-US-01-T02`'s own already-verified smoke check
   (same 3-message result for the same input) — proving this task's edit
   did not disturb it.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `AgentConversationState` gains `hub_routing_result: dict | None`
- [x] All pre-existing keys unchanged in name and type (8 keys, not the 6 this task's own "Before" sample assumed — see Implementation Log)
- [x] `history_entries_to_messages` unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `graph.py`'s `route_hub_request` node, the `request_cross_section_help`
  tool, the conditional edge, and updating `run_agent_conversation`'s own
  initial-state literal to include `"hub_routing_result": None` — all `T05`.
- `model_factory.py`, `mcp_client.py` — untouched, not this story's concern.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-017` created at
`/plan-tasks` step 1) — the human reviews `ADR-017` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

**Cross-story dependency:** this task extends `REQ-SB-25-US-01-T02`'s own
landed file — `REQ-SB-25-US-01-T02` is `status: Ready` (not yet `Done`) as
of this decomposition pass; this task's own `depends_on` names it
explicitly so the build loop sequences `REQ-SB-25-US-01-T02` first. `ADR-017`'s
own Consequences anticipated exactly this: "`AgentConversationState`
(`state.py`) is expected to gain whatever routing-outcome field(s) the
eventual task-level design needs... exact field name(s) are ordinary
`/plan-tasks`/task-level latitude." One field (`hub_routing_result`) is
judged sufficient — the routing node's result dict (`matched`/`agent_id`/
`from_section_id`/`matched_section_id`) is stored as one nested value
rather than four flat keys, since nothing outside `T05`'s own node/tool
logic needs to address its sub-fields independently.

---

## Implementation Log

**Built 2026-08-12 (coder).** Composed this task's one-field addition
around the REAL current `state.py`, not the stale 6-key sample — by this
point `REQ-SB-26-US-01`/`ADR-016` had already additively landed `memory:
list[dict]` and `extracted_facts: list[str]`, so the real file carries 8
keys, not the 6 this task's own "Before" code block (written earlier in
the sequence) assumed. Added the one new key,
`hub_routing_result: dict | None`, on top of the real current 8 — same
substance the task specifies (exactly one new key, nothing renamed/
removed), composed against reality per this project's own established
Learnings pattern ("compose the new change around the REAL current file,
never overwrite it with the stale sample"). Logged here as a scope-internal
judgement call, not an escalation — no ADR/interface change, purely
additive. `history_entries_to_messages` untouched, byte-for-byte.

**Live verification (real backend `.venv`):** `typing.get_type_hints
(AgentConversationState)` confirmed `hub_routing_result` present alongside
all 8 pre-existing keys (`agent_id`/`messages`/`model`/`tools`/`reply`/
`error`/`memory`/`extracted_facts`), none renamed/removed/retyped.
`history_entries_to_messages` re-run against the same 3-entry input
`REQ-SB-25-US-01-T02`'s own smoke check used — returned the identical
3-message result (`SystemMessage`, `HumanMessage`, `AIMessage`), confirming
no disturbance. **PASS.**

No locked AC of its own (verified end-to-end once `T05` actually populates/
consumes this field) — non-AC smoke check per this task's own `## Tests`
placement rule, both steps passed.

gate: flagged (carried, `ADR-017` — unresolved by this task itself, per
its own gating note).
