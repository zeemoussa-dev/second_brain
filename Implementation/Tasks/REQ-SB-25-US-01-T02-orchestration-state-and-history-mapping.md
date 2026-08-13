---
id: REQ-SB-25-US-01-T02
title: agent_orchestration package skeleton + state.py — graph state schema and history-to-messages mapping
parent_story: REQ-SB-25-US-01
requirement_id: REQ-SB-25
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-25-US-01-T01]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-25-US-01-T02 — `agent_orchestration` package skeleton + `state.py`

## Parent Story

- Story: [[REQ-SB-25-US-01]] — `../UserStories/REQ-SB-25-US-01-real-conversational-agent-chat.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-25 *Real Conversational Agent Chat*

---

## Objective

Create the new `app/business/agent_orchestration/` sub-package (`ADR-015`
point 3 — the first sub-package under `business/`) and its `state.py`
module: the graph's state schema, plus the history-to-LangChain-message
mapping settled in `architecture.md`'s 2026-08-12 Addendum.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed — `langgraph`/`langchain-openai`/`mcp`/
  `langchain-mcp-adapters` are installed and importable in `.venv`.
- No `app/business/agent_orchestration/` directory exists yet.

**After / Outputs:**
- `app/business/agent_orchestration/__init__.py` exists (package marker;
  empty this task — `T07` adds the `run_agent_conversation` re-export once
  `graph.py` defines it).
- `app/business/agent_orchestration/state.py` exists: the
  `AgentConversationState` TypedDict, and
  `history_entries_to_messages(agent_name, agent_type, history) ->
  list[BaseMessage]`.

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/__init__.py` (new, empty —
  package marker only).

- `src/backend/app/business/agent_orchestration/state.py` (new):
  ```python
  """The LangGraph conversation graph's state schema (ADR-015 point 3),
  and the mapping from this project's own existing agent_communication_
  history.json shape into the graph's replayed LangChain message list
  (architecture.md's 2026-08-12 Addendum — REQ-SB-25-US-01
  architecture-scoping confirmation)."""
  from typing import TypedDict

  from langchain_core.language_models import BaseChatModel
  from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage


  class AgentConversationState(TypedDict):
      agent_id: str
      messages: list[BaseMessage]
      model: BaseChatModel | None
      tools: list
      reply: str | None
      error: str | None


  def history_entries_to_messages(
      agent_name: str, agent_type: str, history: list[dict]
  ) -> list[BaseMessage]:
      """Maps agent_communication_history.json's existing entry shape
      ({"kind": "chat_user" | "chat_agent" | "run_event", "text": str,
      "timestamp": iso8601}) into the graph's replayed message list:
      "chat_user" -> HumanMessage, "chat_agent" -> AIMessage. "run_event"
      entries are deliberately excluded -- they are action-trigger audit-log
      entries (ADR-011/REQ-SB-13-US-01's own shape), not conversational
      turns, and presenting one to the model as something the user or agent
      "said" would be actively misleading. One minimal SystemMessage is
      prepended from the agent's own registry name/type -- no longer
      instruction/persona prompt is asked for by this story's acceptance
      text. No history window/truncation this pass -- the full list is
      replayed on every call (a token-budget concern is REQ-SB-24's own
      separate scope)."""
      messages: list[BaseMessage] = [
          SystemMessage(
              content=(
                  f"You are the {agent_name} agent for the user's personal "
                  "Second Brain knowledge base."
              )
          )
      ]
      for entry in history:
          if entry["kind"] == "chat_user":
              messages.append(HumanMessage(content=entry["text"]))
          elif entry["kind"] == "chat_agent":
              messages.append(AIMessage(content=entry["text"]))
          # "run_event" entries are intentionally excluded — see docstring.
      return messages
  ```

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (`ADR-003`) — this module is pure business-layer logic, no HTTP concerns,
  no direct file I/O (history is passed in as an already-loaded
  `list[dict]`, not read from disk here).
- `agent_type` is accepted as a parameter but deliberately unused in the
  `SystemMessage` text this pass (only `agent_name` appears) — kept in the
  signature since `architecture.md`'s Addendum names both `name`/`type` as
  the sourced fields, leaving room for a future pass to enrich the prompt
  without a signature change; do not remove the parameter.
- Must not import `app.api.*` or `app.data_access.*` — this is a pure,
  framework-composition module over already-provided inputs.
- No LangGraph `StateGraph`/model/tool code here — that's `T07` (`graph.py`).

---

## Tests

<!-- This task has no locked AC of its own — state.py is an internal
building block with no directly observable HTTP/user-facing outcome by
itself; every locked AC is verified end-to-end in T08 once the full chain
is wired. Its own verification is a non-AC smoke check. -->

**Manual verification steps:**
1. Non-AC smoke check: in a throwaway interpreter against `src/backend`'s
   `.venv` (`.venv\Scripts\python.exe`, `PYTHONPATH` set so `app` imports
   resolve), call
   `history_entries_to_messages("Email Capture", "worker", [{"kind":
   "chat_user", "text": "hello", "timestamp": "2026-01-01T00:00:00Z"},
   {"kind": "chat_agent", "text": "hi there", "timestamp":
   "2026-01-01T00:00:01Z"}, {"kind": "run_event", "text": "Done — 0
   email(s) filed.", "timestamp": "2026-01-01T00:00:02Z"}])`. Confirm the
   returned list has exactly 3 messages: a `SystemMessage` first
   (containing "Email Capture"), then a `HumanMessage("hello")`, then an
   `AIMessage("hi there")` — confirming the `run_event` entry was excluded
   and ordering was preserved.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `app/business/agent_orchestration/__init__.py` exists (empty this task)
- [x] `AgentConversationState` TypedDict matches the shape above
- [x] `history_entries_to_messages` maps `"chat_user"`→`HumanMessage`,
      `"chat_agent"`→`AIMessage`, excludes `"run_event"` entries, and
      prepends exactly one `SystemMessage` sourced from `agent_name`
- [x] No file outside this task's own new files modified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `model_factory.py` — `T03`.
- `mcp_client.py` — `T06`.
- `graph.py` and the `__init__.py` re-export of `run_agent_conversation` —
  `T07`.
- Reading `agent_communication_history.json` from disk — that stays
  `vault_writer.load_agent_history`, called by the router (`T08`), not by
  this module.

---

## Context / Notes

This task's `history_entries_to_messages` implements exactly the mapping
`architecture.md`'s 2026-08-12 Addendum settles — do not re-derive or
deviate from it (e.g. do not add a truncation window, do not include
`run_event` entries, do not invent a longer persona prompt).

---

## Implementation Log

**2026-08-12 — Done.** Created `app/business/agent_orchestration/__init__.py`
(empty, package marker) and `state.py` verbatim per the task's own `##
Files to Modify` code.

**Non-AC smoke check (this task carries no locked AC of its own):** ran
`history_entries_to_messages("Email Capture", "worker", [...])` with the
task's own exact fixture (a `chat_user`, a `chat_agent`, then a
`run_event` entry) against the real `.venv`. Observed: a list of exactly 3
messages — `SystemMessage("You are the Email Capture agent for the user's
personal Second Brain knowledge base.")`, `HumanMessage("hello")`,
`AIMessage("hi there")` — the `run_event` entry correctly excluded,
ordering preserved. PASS, matches the task's own expected outcome exactly.

No assumption, deviation, or escalation. No new decision/pattern/constraint
— this task implements `architecture.md`'s already-settled Addendum
verbatim. `gate: clear` 2026-08-12.
