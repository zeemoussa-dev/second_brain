---
id: REQ-SB-40-US-01-T03
title: state.py — AgentConversationState.gap_recorded field + record_knowledge_gap system-prompt instruction
parent_story: REQ-SB-40-US-01
requirement_id: REQ-SB-40
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-032 created) — carried from the parent story; the human reviews ADR-032 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: []
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-40-US-01-T03 — `state.py`: `gap_recorded` field + system-prompt instruction

## Parent Story

- Story: [[REQ-SB-40-US-01]] — `../UserStories/REQ-SB-40-US-01-agent-knowledge-gap-tracking-and-expert-readiness.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-40 *Agent Knowledge-Gap Tracking & Expert Readiness*

---

## Objective

Additively extend `AgentConversationState` with `gap_recorded: dict | None` (mirrors `hub_routing_result`'s own addition shape, `ADR-017`), and append ONE more instruction to `history_entries_to_messages`'s existing single `SystemMessage` telling the model to call `record_knowledge_gap` before an honest decline — without touching `REQ-SB-33-US-01`'s own existing locked instruction text (`ADR-032` point 1).

---

## Starting State → End State

**Before / Inputs:** Real current `state.py` (verbatim, relevant excerpt):
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
    hub_routing_result: dict | None
```
and `history_entries_to_messages`'s existing `SystemMessage` content (verbatim, real current file):
```python
        SystemMessage(
            content=(
                f"You are the {agent_name} agent for the user's personal "
                "Second Brain knowledge base. Answer only from what your "
                "own tool calls, the replayed conversation history below, "
                "and any stored memory actually contain -- never state "
                "something as a real fact unless it came from one of "
                "those real sources. If a tool call fails or returns an "
                "error, say so honestly; never invent a substitute answer "
                "in its place. If none of your tools return a relevant "
                "result for a question you would otherwise be able to "
                "answer, honestly say you don't know or couldn't find an "
                "answer -- never guess, and never answer from your own "
                "general training knowledge as if it were a real fact "
                "from this knowledge base."
            )
        )
```

**After / Outputs:**
- `AgentConversationState` gains `gap_recorded: dict | None` (additive, last key).
- The `SystemMessage`'s content string gains ONE appended sentence instructing the model to call `record_knowledge_gap` before producing an honest decline — every existing word of the current instruction stays byte-for-byte unchanged; nothing is removed or reworded.

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/state.py`:
  - Extend `AgentConversationState`:
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
        hub_routing_result: dict | None
        gap_recorded: dict | None
    ```
  - Extend the `SystemMessage` content string in `history_entries_to_messages` — append this sentence immediately after the existing final sentence ("...never answer from your own general training knowledge as if it were a real fact from this knowledge base."), inside the same string literal, still exactly one `SystemMessage`:
    ```python
                "general training knowledge as if it were a real fact "
                "from this knowledge base. Whenever you determine that "
                "an honest \"I don't know\" is the right reply, first "
                "call the record_knowledge_gap tool with a short topic "
                "label describing what you don't know, then give that "
                "honest reply as normal."
    ```
  - Update the module docstring's own running commentary (top of file) to note this additive extension, mirroring how it already documents `ADR-016`'s `memory`/`extracted_facts` and `ADR-017`'s `hub_routing_result` additions — one more sentence, e.g.: `"REQ-SB-40/ADR-032 additively extends this state with gap_recorded (output, produced by graph.py's _record_knowledge_gap node) -- see graph.py."`

---

## Constraints

- Inherits from parent story.
- Must NOT reword, remove, or reorder any existing word of the current `SystemMessage` content — append only, per `ADR-032`'s own "extends, does not reopen, `REQ-SB-33-US-01`'s existing locked ACs" Consequence.
- Still exactly ONE `SystemMessage` — do not add a second one (mirrors the docstring's own explicit "still exactly one SystemMessage, not two" rule already documented for the `REQ-SB-33-US-01` addition).
- `gap_recorded` is additive only — do not remove or rename `hub_routing_result`, `extracted_facts`, or any other existing key.
- Do not modify `history_entries_to_messages`'s function signature, its `"chat_user"`/`"chat_agent"` mapping, or its `"run_event"`-exclusion behavior.

---

## Tests

<!-- This task alone has no independently observable AC-tagged outcome —
"the model calls record_knowledge_gap before an honest decline" is only
observable once T04's node/routing exists to intercept the call. This
task's own Tests block verifies the two mechanical, directly-inspectable
properties it is responsible for; AC-01 is verified end-to-end at T04. -->

**Manual verification steps:**

1. Non-AC smoke check: in a Python shell against the backend `.venv`, import `app.business.agent_orchestration.state` and confirm `AgentConversationState.__annotations__` includes `"gap_recorded"` mapped to `dict | None`, alongside all 9 pre-existing keys (none dropped).
2. Non-AC smoke check: call `state.history_entries_to_messages("Vault Q&A", "expert", [])`. Confirm the result is still a list with exactly one `SystemMessage` (no second one added), and that its `.content` string both (a) still contains the full, byte-for-byte original `REQ-SB-33-US-01` instruction text (e.g. confirm the substring `"never answer from your own general training knowledge as if it were a real fact from this knowledge base."` is present unchanged) and (b) now also contains the new appended sentence (confirm the substring `"call the record_knowledge_gap tool"` is present).
3. Clean-up: none needed — this task modifies only source code, no persisted state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `AgentConversationState` carries a new additive `gap_recorded: dict | None` key; all pre-existing keys unchanged
- [ ] The system prompt's existing `REQ-SB-33-US-01` instruction text is present byte-for-byte, unmodified
- [ ] The system prompt gains exactly one new appended sentence instructing the model to call `record_knowledge_gap` before an honest decline
- [ ] Still exactly one `SystemMessage` produced by `history_entries_to_messages`
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The `record_knowledge_gap` tool definition, the `_record_knowledge_gap` node, and the routing branch that actually intercepts a call to it — `T04`'s scope (`graph.py`).
- `history_entries_to_messages`'s `"chat_user"`/`"chat_agent"`/`"run_event"` mapping logic — untouched.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-032` created at `/plan-tasks` step 1) — the human reviews `ADR-032` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Independent of `T01`/`T02`:** this task touches only `state.py`, not `vault_writer.py`/`knowledge_gap_tracking.py` — it has no `depends_on` edge, and may be built in parallel with `T01`/`T02`; `T04` (which needs both this task's `gap_recorded` field AND `T02`'s `knowledge_gap_tracking.record_gap`) is the join point.

---

## Implementation Log

`state.py`: read the REAL current file first (confirmed byte-for-byte match against the task's own "Before" sample, no drift since the sample was authored). Added `gap_recorded: dict | None` as the new last key on `AgentConversationState`. Appended exactly one sentence to the existing `SystemMessage` content string (never reworded/removed any existing word). Updated the module docstring's running commentary with one more sentence noting the `ADR-032` addition, mirroring the existing `ADR-016`/`ADR-017` commentary pattern already there.

**Verified live** (Python shell, backend `.venv`): `AgentConversationState.__annotations__` now has 10 keys including `"gap_recorded": dict | None`, all 9 pre-existing keys unchanged. `history_entries_to_messages("Vault Q&A", "expert", [])` still returns exactly one `SystemMessage`; its content contains BOTH the original `REQ-SB-33-US-01` instruction text byte-for-byte (`"never answer from your own general training knowledge as if it were a real fact from this knowledge base."` present unmodified) AND the new appended sentence (`"call the record_knowledge_gap tool"` present). PASS on both non-AC smoke checks (no locked AC maps solely to this task — AC-01 is verified end-to-end at T04, per this task's own Tests block).

No `history_entries_to_messages` signature/mapping-logic change.

gate: flagged (carried, trigger-3). No new trigger fired.

status: Done
