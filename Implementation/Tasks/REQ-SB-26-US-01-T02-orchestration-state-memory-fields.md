---
id: REQ-SB-26-US-01-T02
title: agent_orchestration/state.py — AgentConversationState gains memory / extracted_facts fields (additive only)
parent_story: REQ-SB-26-US-01
requirement_id: REQ-SB-26
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-25-US-01-T02]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-26-US-01-T02 — `agent_orchestration/state.py` gains `memory`/`extracted_facts`

## Parent Story

- Story: [[REQ-SB-26-US-01]] — `../UserStories/REQ-SB-26-US-01-agent-memory.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-26 *Agent Memory*

---

## Objective

Add the two new, purely additive fields `ADR-016`'s Consequences section
names — `memory: list[dict]` (input) and `extracted_facts: list[str]`
(output) — to `AgentConversationState`, so `T03`'s two new graph nodes have
somewhere on state to read/write.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-25-US-01-T02` has landed — `app/business/agent_orchestration/state.py`
  exists with `AgentConversationState` holding `agent_id`/`messages`/
  `model`/`tools`/`reply`/`error`.

**After / Outputs:**
- `AgentConversationState` gains `memory: list[dict]` and
  `extracted_facts: list[str]` — every existing field unchanged (no field
  removed or renamed, per `ADR-016`'s own "additive-only" Consequence).

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/state.py` — extend the
  `AgentConversationState` TypedDict (leave `history_entries_to_messages`
  and every other line untouched):
  ```python
  class AgentConversationState(TypedDict):
      agent_id: str
      messages: list[BaseMessage]
      model: BaseChatModel | None
      tools: list
      reply: str | None
      error: str | None
      memory: list[dict]
      extracted_facts: list[str]
  ```
  Also update the module's own docstring to note the extension, e.g.
  append a sentence: `"REQ-SB-26/ADR-016 additively extends this state with
  memory (input, stored facts folded in by retrieve_memory) and
  extracted_facts (output, produced by extract_memory) -- see graph.py."`

---

## Constraints

- Inherits from parent story: additive only — do not remove, rename, or
  change the type of `agent_id`/`messages`/`model`/`tools`/`reply`/`error`.
- `history_entries_to_messages` itself is untouched — this task only
  extends the `TypedDict`, per `ADR-016`'s own scoping (it does not touch
  the history-to-message mapping).
- No LangGraph `StateGraph`/node code here — that's `T03` (`graph.py`).
- Must not import `app.api.*` or `app.data_access.*` — same constraint the
  original `state.py` task (`REQ-SB-25-US-01-T02`) already established.

---

## Tests

<!-- This task has no locked AC of its own — state.py is an internal
building block with no directly observable HTTP outcome by itself; every
locked AC is verified end-to-end in T04 once the full chain is wired. This
task's own verification is a non-AC smoke check. -->

**Manual verification steps:**
1. Non-AC smoke check: in a throwaway interpreter against `src/backend`'s
   `.venv`, `from app.business.agent_orchestration.state import
   AgentConversationState` and confirm
   `AgentConversationState.__annotations__` contains all eight keys:
   `agent_id`, `messages`, `model`, `tools`, `reply`, `error`, `memory`,
   `extracted_facts` — confirming the extension is additive, not a
   replacement.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `AgentConversationState` gains `memory: list[dict]` and
      `extracted_facts: list[str]`
- [x] All six pre-existing fields (`agent_id`/`messages`/`model`/`tools`/
      `reply`/`error`) unchanged in name and type
- [x] `history_entries_to_messages` byte-for-byte unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `graph.py` node changes and `run_agent_conversation`'s signature — `T03`.
- `vault_writer.py` primitives — `T01`.
- `agents_router.py` — `T04`.

---

## Context / Notes

Kept as its own task (rather than folded into `T03`) so the state-schema
change and the graph-node/entry-point wiring are each independently
reviewable diffs — mirrors `REQ-SB-25-US-01`'s own `T02`/`T07` split
between `state.py` and `graph.py`.

---

## Implementation Log

**2026-08-12 — coder.** Extended `AgentConversationState` in
`src/backend/app/business/agent_orchestration/state.py` with `memory:
list[dict]` and `extracted_facts: list[str]`, plus the module docstring
sentence — verbatim per this task's own `## Files to Modify` code block,
no deviation. `history_entries_to_messages` untouched.

**Non-AC smoke check (pass):** `AgentConversationState.__annotations__`
confirmed to contain all eight keys (`agent_id`, `messages`, `model`,
`tools`, `reply`, `error`, `memory`, `extracted_facts`) — additive
extension confirmed, no field removed/renamed.

`status: Ready → Done`.

`gate: clear 2026-08-12` — no MUST-FLAG trigger fired: implemented exactly
per the task's own literal code sample, no deviation, no assumption.
