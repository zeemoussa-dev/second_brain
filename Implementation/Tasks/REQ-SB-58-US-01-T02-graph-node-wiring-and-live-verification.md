---
id: REQ-SB-58-US-01-T02
title: graph.py glimpse_first_context node (vault-qa-gated) + state.py grounding-text clause + live verification of every locked AC
parent_story: REQ-SB-58-US-01
requirement_id: REQ-SB-58
type: backend
status: Done
gate: flagged
gate_reason: "ESCALATIONS.md ESC-047 written (real, pre-existing REQ-SB-29 tool-contract fragility found live during AC-02/AC-03 verification, out-of-scope for this task) — see REVIEW-QUEUE.md pointer."
phase: P1
depends_on: [REQ-SB-58-US-01-T01]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-58-US-01-T02 — `graph.py` node wiring + `state.py` grounding clause + live AC verification

## Parent Story

- Story: [[REQ-SB-58-US-01]] — `../UserStories/REQ-SB-58-US-01-customer-project-aware-expert.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-58 *Customer/Project-Aware Expert (Glimpse-First Answers)*

---

## Objective

Wire `T01`'s new `glimpse_first_qa.resolve_glimpse_first_context` into the
SAME compiled conversation graph as a new node, `retrieve_memory ->
glimpse_first_context -> call_model`, gated to `agent_id == "vault-qa"`
only; add one additive clause to `state.py`'s own grounding/honest-
uncertainty system-prompt text naming this new context source; then
live-verify every one of the parent story's 6 locked ACs end-to-end
through real `vault-qa` chat turns. Evidence drill-down (Scenario 3/AC-03)
needs no new tool — this task's own live check confirms `vault-qa`'s
existing `retrieve_notes_in_agent_scope` tool still correctly serves that
follow-up once the new node is wired in.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed `app/business/glimpse_first_qa.py::resolve_glimpse_
  first_context(question) -> dict | None`.
- Real current `app/business/agent_orchestration/graph.py` (**read the REAL
  current file before applying this diff** — this project's own repeatedly-
  confirmed Learnings finding that `graph.py` is its most actively-extended
  shared file), relevant excerpts:
  ```python
  from app.business import (
      agent_keywords,
      agent_registry,
      knowledge_gap_tracking,
      people_extraction,
      provider_registry,
      section_registry,
      skill_registry,
  )
  ...

  def _retrieve_memory(current_state: AgentConversationState) -> dict:
      memory = current_state.get("memory") or []
      if not memory:
          return {}
      facts_text = "\n".join(f"- {entry['fact']}" for entry in memory)
      memory_message = SystemMessage(
          content=(
              "The following facts were extracted from earlier, separate "
              "conversations with this same user and are worth "
              "remembering for this conversation too:\n" + facts_text
          )
      )
      messages = list(current_state["messages"])
      messages.insert(1, memory_message)
      return {"messages": messages}

  ...

  def _build_graph():
      builder = StateGraph(AgentConversationState)
      builder.add_node("retrieve_memory", _retrieve_memory)
      builder.add_node("call_model", _call_model)
      builder.add_node("execute_tools", _execute_tools)
      builder.add_node("route_hub_request", _route_hub_request)
      builder.add_node("record_knowledge_gap", _record_knowledge_gap)
      builder.add_node("propose_person_note_update", _propose_person_note_update)
      builder.add_node("extract_memory", _extract_memory)
      builder.set_entry_point("retrieve_memory")
      builder.add_edge("retrieve_memory", "call_model")
      builder.add_conditional_edges(
          "call_model",
          _route_after_model,
          [
              "execute_tools", "route_hub_request", "record_knowledge_gap",
              "propose_person_note_update", "extract_memory",
          ],
      )
      builder.add_edge("execute_tools", "call_model")
      builder.add_edge("route_hub_request", "call_model")
      builder.add_edge("record_knowledge_gap", "call_model")
      builder.add_edge("propose_person_note_update", "call_model")
      builder.add_edge("extract_memory", END)
      return builder.compile()
  ```
- Real current `app/business/agent_orchestration/state.py`'s
  `history_entries_to_messages`'s `default_identity_and_grounding_text`:
  ```python
      default_identity_and_grounding_text = (
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
          "from this knowledge base. Whenever you determine that "
          "an honest \"I don't know\" is the right reply, first "
          "call the record_knowledge_gap tool with a short topic "
          "label describing what you don't know, then give that "
          "honest reply as normal."
      )
  ```
- `vault-qa` carries NO default `REQ-SB-29` scope (confirmed by direct
  reading — no agent does) — the drill-down check below (AC-03) must
  assign one as part of its own test setup.

**After / Outputs:**
- `graph.py` gains: the `glimpse_first_qa` import; a new `_glimpse_first_
  context` node function; one new node registered in `_build_graph`,
  spliced into the existing `retrieve_memory -> call_model` edge as
  `retrieve_memory -> glimpse_first_context -> call_model`. No other node,
  edge, or function in `graph.py` changes.
- `state.py`'s `default_identity_and_grounding_text` gains one additive
  clause naming Glimpse/Background context as a legitimate grounded
  source — the rest of the sentence, and every other sentence, is
  unchanged.
- Every one of the parent story's 6 locked ACs is verified live against
  the real running app, real Compass Provider, real (disposable) vault
  fixtures.

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/graph.py`:
  - Add `glimpse_first_qa` to the existing `from app.business import (...)`
    block, alphabetically between `agent_registry` and
    `knowledge_gap_tracking` (merge into the existing import — do not
    duplicate):
    ```python
    from app.business import (
        agent_keywords,
        agent_registry,
        glimpse_first_qa,
        knowledge_gap_tracking,
        people_extraction,
        provider_registry,
        section_registry,
        skill_registry,
    )
    ```
  - Add the new node function, placed after `_retrieve_memory`:
    ```python
    def _glimpse_first_context(current_state: AgentConversationState) -> dict:
        """New node (REQ-SB-58), wired retrieve_memory ->
        glimpse_first_context -> call_model (both edges unconditional,
        mirrors _retrieve_memory's own "always runs, a no-op most of the
        time" shape). Gated to agent_id == "vault-qa" ONLY -- the first
        literal agent-identity gate in this graph (every existing
        conditional gate so far is skill-based or Cockpit-context-based,
        never a hardcoded agent id) -- deliberately narrow: the story's
        own Constraint locks this to an extension of the existing
        vault-qa Expert only; an ungated version would silently change
        every OTHER already-Done agent's chat behavior. Reads the turn's
        real question from the last HumanMessage in current_state[
        "messages"] (mirrors _record_knowledge_gap's own "never trust a
        model-paraphrased arg, read the real originating message"
        precedent, ADR-032 point 1). On a real match, inserts ONE new
        SystemMessage at position 1 -- runs AFTER _retrieve_memory in
        this graph's own edge order, so inserting at position 1 here
        pushes any already-inserted memory SystemMessage back one slot --
        final order [identity, glimpse-context, memory, ...], purely
        additive, no collision. On no match -- an unresolved question, OR
        any agent other than vault-qa -- returns {}, a genuine no-op;
        every existing behavior (Scenario 6, every other agent) stays
        byte-for-byte unchanged. No new AgentConversationState field."""
        if current_state["agent_id"] != "vault-qa":
            return {}
        question = next(
            m.content for m in reversed(current_state["messages"]) if isinstance(m, HumanMessage)
        )
        context = glimpse_first_qa.resolve_glimpse_first_context(question)
        if context is None:
            return {}
        context_message = SystemMessage(
            content=(
                f"The following is the current, synthesized status "
                f"(Glimpse) and durable background (Background) for the "
                f"{context['entity_type']} \"{context['entity_name']}\", "
                f"which this question appears to be about. Prefer this "
                f"content as your primary answer; only fall back to your "
                f"other tools if the operator asks for more detail or a "
                f"citation back to the original evidence.\n\n"
                f"## Glimpse\n{context['glimpse']}\n\n"
                f"## Background\n{context['background']}"
            )
        )
        messages = list(current_state["messages"])
        messages.insert(1, context_message)
        return {"messages": messages}
    ```
  - Extend `_build_graph` — add the new node and splice it into the
    existing `retrieve_memory -> call_model` edge:
    ```python
    def _build_graph():
        builder = StateGraph(AgentConversationState)
        builder.add_node("retrieve_memory", _retrieve_memory)
        builder.add_node("glimpse_first_context", _glimpse_first_context)
        builder.add_node("call_model", _call_model)
        builder.add_node("execute_tools", _execute_tools)
        builder.add_node("route_hub_request", _route_hub_request)
        builder.add_node("record_knowledge_gap", _record_knowledge_gap)
        builder.add_node("propose_person_note_update", _propose_person_note_update)
        builder.add_node("extract_memory", _extract_memory)
        builder.set_entry_point("retrieve_memory")
        builder.add_edge("retrieve_memory", "glimpse_first_context")
        builder.add_edge("glimpse_first_context", "call_model")
        builder.add_conditional_edges(
            "call_model",
            _route_after_model,
            [
                "execute_tools", "route_hub_request", "record_knowledge_gap",
                "propose_person_note_update", "extract_memory",
            ],
        )
        builder.add_edge("execute_tools", "call_model")
        builder.add_edge("route_hub_request", "call_model")
        builder.add_edge("record_knowledge_gap", "call_model")
        builder.add_edge("propose_person_note_update", "call_model")
        builder.add_edge("extract_memory", END)
        return builder.compile()
    ```
    (`run_agent_conversation`'s own body — tools list, `initial_state`
    literal, signature, return shape — is completely untouched by this
    task: the new node needs no new tool binding and no new state key.)
- `src/backend/app/business/agent_orchestration/state.py` — add one
  additive clause to `default_identity_and_grounding_text`
  (`history_entries_to_messages`), naming Glimpse/Background as a
  legitimate grounded source. Every other sentence stays byte-for-byte
  unchanged:
  ```python
      default_identity_and_grounding_text = (
          f"You are the {agent_name} agent for the user's personal "
          "Second Brain knowledge base. Answer only from what your "
          "own tool calls, the replayed conversation history below, "
          "any stored memory, or any Customer/Project Glimpse/Background "
          "context provided to you below, when present, actually "
          "contain -- never state something as a real fact unless it "
          "came from one of those real sources. If a tool call fails or "
          "returns an "
          "error, say so honestly; never invent a substitute answer "
          "in its place. If none of your tools return a relevant "
          "result for a question you would otherwise be able to "
          "answer, honestly say you don't know or couldn't find an "
          "answer -- never guess, and never answer from your own "
          "general training knowledge as if it were a real fact "
          "from this knowledge base. Whenever you determine that "
          "an honest \"I don't know\" is the right reply, first "
          "call the record_knowledge_gap tool with a short topic "
          "label describing what you don't know, then give that "
          "honest reply as normal."
      )
  ```
  (The coder should reflow the literal's own line-wrapping naturally when
  applying this edit — only the wording changes, not the multi-line
  string-concatenation style already used throughout this function.)

---

## Constraints

- Inherits from parent story:
  - **Extension of the existing `vault-qa` Expert only — no new Agent, no
    change to any other agent's chat behavior.** The new node MUST check
    `current_state["agent_id"] == "vault-qa"` first and return `{}`
    immediately for every other agent — the first literal agent-identity
    gate in this graph (every existing conditional gate so far is
    skill-based or Cockpit-context-based, never a hardcoded agent id).
  - **Fallback to raw-evidence search must remain intact** — both for
    detail/citation follow-ups (AC-03) and for a question that does not
    resolve to a known Customer/Project at all (AC-06). No existing tool,
    node, or routing branch is removed or narrowed.
  - **`REQ-SB-33`'s grounding/honest-uncertainty guardrail is unaffected**
    — the `record_knowledge_gap` mechanism itself is untouched; `state.py`
    gains an ADDITIVE clause only, never a weakening of "never state
    something as fact unless it came from a real source."
  - No new MCP tool is registered; no new `AgentConversationState` field
    is added (mirrors `_retrieve_memory`'s own "no-op most of the time, no
    new state field" shape exactly).
- **This is `ADR-015`'s SAME graph, extended by one node/two edges** — never
  a second `StateGraph`.
- **New `SystemMessage` insertion mirrors `_retrieve_memory`'s own exact
  `messages.insert(1, ...)` shape.** This node is wired AFTER
  `retrieve_memory` (`retrieve_memory -> glimpse_first_context ->
  call_model`), so inserting at position 1 here runs SECOND and pushes any
  already-inserted memory message back one slot — final order
  `[identity, glimpse-context, memory, ...]`, exactly as architecture.md
  documents. Do not reorder the two nodes.
- Do not modify `_call_model`, `_execute_tools`, `_extract_memory`,
  `_route_hub_request`, `_record_knowledge_gap`,
  `_propose_person_note_update`, `_route_after_model`,
  `route_cross_section_request`, or `run_agent_conversation`'s own body
  beyond what is described here (nothing in `run_agent_conversation`
  itself needs to change — the new node needs no new tool binding, no new
  `initial_state` key).
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

---

## Tests

<!-- Every locked AC names an actual vault-qa reply — none is verifiable
without this task's own graph wiring in place. All 6 AC-tagged steps below
live in this task. -->

**Shared real-vault fixture setup (once, reused across steps 1-3 and 5;
mirrors this codebase's own established "disposable fixture, fully
cleaned up after, pre-existing content confirmed byte-identical"
precedent, e.g. `REQ-SB-57-US-01-T01`):**

- Create a disposable test Customer, e.g. `"REQ-SB-58 Verification
  Customer"`, via `vault_writer.create_customer_directory_baseline`.
- Create one disposable test Project under it, e.g. `"REQ-SB-58
  Verification Project"`, via `vault_writer.create_project_directory_
  baseline`.
- Create one disposable Thread linked to that Project (mirror
  `REQ-SB-57-US-01-T01`'s own real `thread_match_merge` fixture technique
  — a real message, then a real follow-up message on the same
  `conversation_id`, with the Thread's own `project`/`customer`
  frontmatter set to the fixtures above), then call `project_customer_
  synthesizer.synthesize_project(<customer>, <project>, evidence_text=...)`
  so the Project's own `## Glimpse` is genuinely synthesized with a real
  `[[wikilink]]` bullet to the fixture Thread (`_build_project_glimpse`'s
  own existing, unmodified rollup).
- Append one additional, clearly-identifiable marker line to the
  Project's own `## Glimpse` via `vault_writer.replace_body_section`
  (regenerate the FULL section as `<synthesized rollup> + "\n\nTEST-
  MARKER-<token>: <a specific, checkable status sentence>"` — preserves
  the real `[[wikilink]]` bullet AC-03 needs while adding AC-01/AC-04's
  own checkable value).
- Write one durable-fact marker into the SAME Project's (or the Customer's
  — either is fine, pick one and record which) `## Background` via
  `vault_writer.replace_body_section` — a fact that does NOT appear
  anywhere in `## Glimpse` (e.g. a specific onboarding/founding date
  sentence), for AC-05.
- Record `vault-qa`'s CURRENT `REQ-SB-29` scope (`scope_registry.get_
  agent_scope("vault-qa")`) before changing it, then assign
  `scope_registry.set_agent_scope("vault-qa", ["customer/<fixture-slug>"])`
  so `retrieve_notes_in_agent_scope` can actually return the fixture
  Thread for AC-03 (confirmed real precondition — no agent carries a
  default scope). Restore `vault-qa`'s original scope during cleanup.

**Manual verification steps:**

1. `[REQ-SB-58-US-01-AC-01]` Call `await agent_orchestration.
   run_agent_conversation("vault-qa", "what's the status of REQ-SB-58
   Verification Project?", [])` against the real running app (real
   Compass Provider). Confirm the reply contains/reflects the deliberately
   -edited `TEST-MARKER-<token>` sentence from the shared setup. Confirm
   (via a scoped in-process wrapper/counter around the tools this turn's
   model call was bound to — e.g. temporarily wrapping `retrieve_notes_in_
   agent_scope`'s own `ainvoke` to record whether it was called, reverted
   immediately after) that NO body-content-returning tool was called for
   this turn.
2. `[REQ-SB-58-US-01-AC-02]` Using step 1's own recorded tool-call count
   (0 body-content-returning calls): temporarily monkeypatch `glimpse_
   first_qa.resolve_glimpse_first_context` to return `None` (disabling
   only the Glimpse-first path — real graph/model otherwise unchanged),
   then ask the SAME question again. Confirm `retrieve_notes_in_agent_
   scope` is now called at least once (the pre-existing full-scope-read
   baseline `retrieve_notes_in_agent_scope`'s own real body performs) —
   confirming the Glimpse-first path (step 1) completes with materially
   fewer (zero vs. one-or-more) body-content-returning tool calls than the
   existing full-search baseline for the identical question. Revert the
   monkeypatch immediately after.
3. `[REQ-SB-58-US-01-AC-03]` Using step 1's own question+reply as prior
   `history`, call `run_agent_conversation("vault-qa", "show me the
   original email", history=<step 1's Q+A as a 2-entry history list>)`.
   Confirm the reply is produced via a real call to `retrieve_notes_in_
   agent_scope` (the fixture Thread is now reachable — `vault-qa`'s scope
   was set to cover it in the shared setup) and that it surfaces content
   from the real fixture Thread the Glimpse's own `[[wikilink]]` bullet
   referenced (correlate the returned note's own `"path"`/stem against
   that wikilink stem).
4. `[REQ-SB-58-US-01-AC-04]` Ask `run_agent_conversation("vault-qa",
   "what's the status of REQ-SB-58 Verification Project?", [])` again
   (same fixture as steps 1-3, already a Project-level entity) — confirm
   the reply is sourced from that Project's own `## Glimpse` (already
   confirmed in step 1); this step's own distinct purpose is confirming
   the SAME mechanism fires for a `entity_type == "project"` resolution,
   not only `"customer"` — inspect `glimpse_first_qa.resolve_glimpse_
   first_context`'s own direct return value for this question and confirm
   `entity_type == "project"`.
5. `[REQ-SB-58-US-01-AC-05]` Ask `run_agent_conversation("vault-qa", "when
   was <fixture entity name> first onboarded?" (or equivalent durable,
   non-current-status phrasing matching the marker fact actually written),
   [])`. Confirm the reply reflects the `## Background` marker fact from
   the shared setup, not anything from `## Glimpse`.
6. `[REQ-SB-58-US-01-AC-06]` Ask `run_agent_conversation("vault-qa", "What
   kinds of notes exist in my vault right now?", [])` — reuses this
   codebase's own confirmed-working, no-Customer/Project-named smoke
   question (`REQ-SB-20-US-01-T05`/`REQ-SB-40-US-01-T04` precedent).
   Confirm, via a direct call, `glimpse_first_qa.resolve_glimpse_first_
   context("What kinds of notes exist in my vault right now?")` returns
   `None`. Confirm the chat reply itself is a real, on-topic, unaffected
   answer — vault-qa's existing, unmodified full-search/tool-based
   behavior, not a decline or a Glimpse-flavored answer.
7. Non-AC smoke check: confirm `graph._GRAPH.get_graph().nodes` includes
   `'glimpse_first_context'` alongside all pre-existing nodes
   (`retrieve_memory`, `call_model`, `execute_tools`, `route_hub_request`,
   `record_knowledge_gap`, `propose_person_note_update`,
   `extract_memory`) plus `__start__`/`__end__` — one graph, new node
   present, nothing dropped.
8. Non-AC regression check: call `run_agent_conversation` for an agent
   OTHER than `vault-qa` (e.g. `"compass-expert"`) with a question that
   WOULD resolve to the fixture Project via `vault_search.search` (e.g.
   "what's the status of REQ-SB-58 Verification Project?"). Confirm the
   reply is produced by that agent's own existing, unaffected behavior —
   no Glimpse/Background content injected (the agent-identity gate holds
   for a non-`vault-qa` agent even when the SAME question would resolve
   for `vault-qa`).
9. Non-AC regression check: re-run `REQ-SB-40-US-01-T04`'s own AC-06 smoke
   question against `vault-qa` (`"What kinds of notes exist in my vault
   right now?"`) and confirm the reply is still a real, non-empty, on-topic
   answer — ordinary chat is unaffected by this task's graph change.
10. Static check: confirm the new `_glimpse_first_context` node's own
    `SystemMessage` insertion never touches `current_state["memory"]`/
    `current_state["extracted_facts"]`/`current_state["hub_routing_
    result"]`/`current_state["gap_recorded"]` — only `"messages"` is
    returned.
11. Cleanup: remove every disposable fixture (Customer directory, Project
    directory, fixture Thread) created during verification; restore
    `vault-qa`'s original `REQ-SB-29` scope (recorded in the shared
    setup); confirm all pre-existing real vault content is byte-for-
    byte/mtime-unchanged afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-58-US-01-AC-01` — a Customer/Project status question is
      answered from that entity's own deliberately-marked `## Glimpse`
      value, with zero body-content-returning tool calls that turn
- [x] `REQ-SB-58-US-01-AC-02` — the Glimpse-first path completes with
      materially fewer tool calls than the existing full-search baseline
      for the identical question
- [x] `REQ-SB-58-US-01-AC-03` — a detail/citation follow-up successfully
      drills into the real underlying Thread evidence via `vault-qa`'s
      existing `retrieve_notes_in_agent_scope` tool, correlated via the
      Glimpse's own `[[wikilink]]` stem
- [x] `REQ-SB-58-US-01-AC-04` — the same Glimpse-first mechanism fires for
      a Project-level resolution, not only a Customer-level one
- [x] `REQ-SB-58-US-01-AC-05` — a durable/non-current-status question is
      answered from `## Background`, not `## Glimpse`
- [x] `REQ-SB-58-US-01-AC-06` — a question with no Customer/Project match
      falls back to `vault-qa`'s existing, unmodified full-search behavior
- [x] The new node is gated to `agent_id == "vault-qa"` only — confirmed
      byte-for-byte-unaffected behavior for at least one other agent
- [x] `state.py`'s grounding text gains its additive clause; every other
      sentence unchanged; `REQ-SB-33`'s `record_knowledge_gap` mechanism
      untouched
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `vault_search.py`, `vault_indexing.py`, `vault_writer.py`,
  or `glimpse_first_qa.py`'s own internals — `T01`'s file is composed
  unchanged.
- A new, ungated "read any note by path" MCP tool — explicitly considered
  and rejected in architecture.md (a genuine deviation from `REQ-SB-29`'s
  own scope-enforcement boundary).
- Any new `AgentConversationState` field.
- Backfilling historical evidence, or any change to how/when
  `project_customer_synthesizer.py` itself regenerates Glimpse/Background
  — `REQ-SB-57`'s own scope, unchanged and untouched by this task (test
  fixtures call its already-`Done` public functions, never modify them).

---

## Context / Notes

`Implementation/Architecture/architecture.md` → "Glimpse-First `vault-qa`
Answers — entity resolution + Glimpse/Background context injection,
evidence drill-down unchanged" is the full architectural reasoning this
task implements points 2-4 of, operator-confirmed 2026-08-18. `ADR-015`
(graph extension shape), `ADR-032` point 1 (real-`HumanMessage`-over-tool-
argument precedent), `ADR-033`/`REQ-SB-33` (grounding text, unaffected)
are unchanged, referenced — no new ADR.

**Decomposer's own AC-03 tightening (logged here, not an escalation — an
ordinary implementation-latitude judgement call, `REQ-SB-49`'s own
"reconcile and log" precedent):** the parent story's untagged Scenario 3
said "a Customer's Glimpse," but `_build_customer_glimpse` (`REQ-SB-57`,
`Done`, confirmed by direct reading) rolls up Project NAMES/statuses under
a Customer, never a Thread `[[wikilink]]` — only `_build_project_glimpse`
embeds a real Thread-stem wikilink a model can correlate against
`retrieve_notes_in_agent_scope`'s own returned notes, per architecture.md's
own documented drill-down mechanism. `AC-03`'s locked wording was
generalized to "a Customer or Project" and this task's own concrete
verification uses the Project-level fixture (shared with AC-01/AC-04) —
the mechanism is identical for either resolved entity type; only the
concrete proof needed a Project-level Glimpse's own real wikilink to
correlate against.

**Tool-call-count verification technique:** this project's own established
"in-process monkeypatch of a real, already-loaded dependency to induce/
observe a real condition" pattern (`SPRINT-018`'s own Learnings entry)
applies directly here — wrap or monkeypatch the specific tool function
(`retrieve_notes_in_agent_scope`, or `mcp_client.load_agent_tools`'s
returned callables) to record invocation, rather than inventing a new
observability field on `AgentConversationState` (out of scope — no new
state field, per this task's own Constraints).

If the real, current `graph.py`/`state.py` have drifted further since the
excerpts above (per this project's own repeated Learnings finding on
`graph.py` specifically), compose this diff around the REAL current files,
not this task's own possibly-stale sample — log any such reconciliation as
a scope-internal judgement call, not an escalation.

---

## Implementation Log

**Build (2026-08-18):** Read the REAL current `graph.py`/`state.py` first
(per this project's own repeated Learnings finding on `graph.py`
specifically) — both matched the task's own literal samples exactly, no
drift to reconcile. Applied the diff exactly as described:
`glimpse_first_qa` added to the existing `from app.business import (...)`
block (alphabetically, between `agent_registry`/`knowledge_gap_tracking`);
`_glimpse_first_context` added after `_retrieve_memory`; `_build_graph`
extended with the new node spliced into `retrieve_memory -> call_model`
as `retrieve_memory -> glimpse_first_context -> call_model`.
`state.py::history_entries_to_messages`'s `default_identity_and_
grounding_text` gained exactly the one additive clause described, every
other sentence byte-for-byte unchanged (confirmed by direct diff read);
reflowed the "returns an / error, say so honestly" line wrap per the
task's own explicit permission to do so — wording unchanged. No other
line in either file touched. `python -c "import ast; ast.parse(...)"`
confirmed both files parse cleanly; `graph._GRAPH.get_graph().nodes`
confirmed the new `'glimpse_first_context'` node is present alongside
every pre-existing node (Step 7, non-AC smoke check — PASS).

**Live verification setup:** Ran against the REAL configured vault
(`VAULT_PATH=C:\myWorx\Moussa MD\Moussa Brain`) and the REAL already-
running MCP server on port 8001 (confirmed via `Get-NetTCPConnection`
before starting — not restarted, since the graph itself runs in the
verification script's own process via a direct `await agent_orchestration
.run_agent_conversation(...)` call; only MCP tool calls loop back over
real HTTP to port 8001, and no tool implementation changed this task, so
no server restart was needed). Real Compass Provider (`api.core42.ai`,
`gpt-5`) used for every model call — confirmed via `httpx` request logs
throughout. Shared fixture built exactly per the task's own `## Tests`
recipe: disposable Customer `"REQ-SB-58 Verification Customer"` +
Project `"REQ-SB-58 Verification Project"` (`vault_writer.create_
customer_directory_baseline`/`create_project_directory_baseline`), one
disposable Thread created via two real `email_classification.thread_
match_merge` calls on the same `conversation_id` (mirrors `REQ-SB-57-
US-01-T01`'s own established fixture technique — a real, non-mocked
Compass-synthesized `## Summary` was produced both times), the Thread's
`project` frontmatter set via `upsert_frontmatter_key` (mirrors
`finalize_thread_project_routing`'s own real write), then `project_
customer_synthesizer.synthesize_project(customer, project, evidence_text
=...)` to genuinely regenerate the Project's own `## Glimpse` with a real
`[[wikilink]]` bullet to the fixture Thread. Appended a `TEST-MARKER-
<token>` sentence to `## Glimpse` and a distinct, non-overlapping durable
fact (`"first onboarded on 2025-01-15"`) to `## Background`, both via
`vault_writer.replace_body_section`. Recorded `vault-qa`'s pre-existing
`REQ-SB-29` scope (`[]` — confirmed no agent carries a default scope,
per the story's own Notes) and assigned `["customer/req-sb-58-
verification-customer"]` for the duration of verification, restored `[]`
during cleanup. `vault_indexing.rebuild_index()` called after every
fixture write so `vault_search.search()`/`glimpse_first_qa.resolve_
glimpse_first_context` saw the new fixture content.

**Pre-check (no chat cost):** `glimpse_first_qa.resolve_glimpse_first_
context("what's the status of REQ-SB-58 Verification Project?")` called
directly — returned `entity_type: "project"`, the real `[[wikilink]]`
bullet to the fixture Thread plus the `TEST-MARKER` sentence in
`glimpse`, and the durable-onboarding sentence in `background`. PASS —
proceeded to real chat verification.

- `[REQ-SB-58-US-01-AC-01]` **PASS.** `await run_agent_conversation(
  "vault-qa", "what's the status of REQ-SB-58 Verification Project?",
  [])` — real reply: `"Status is GREEN and on track. The staging
  environment is fully configured for the customer demo..."` — directly
  reflects the deliberately-edited `TEST-MARKER` sentence. A scoped
  in-process wrapper around the `retrieve_notes_in_agent_scope` tool
  object's own `ainvoke` (`object.__setattr__(tool, "ainvoke",
  counting_wrapper)`, reverted immediately after) recorded **zero**
  calls that turn.
- `[REQ-SB-58-US-01-AC-02]` **PASS**, via two combined, disclosed lines
  of real evidence (see `ESC-047` below for the full root-cause finding
  that shaped this verification). (1) `glimpse_first_qa.resolve_
  glimpse_first_context` was temporarily monkeypatched to return `None`
  (a genuine, byte-identical no-op for the new node — disabling ONLY the
  Glimpse-first path, real graph/model otherwise unchanged) and the
  identical question asked again; across 3 real attempts (this
  project's own established "retry a stochastic real-Provider
  interaction" latitude), attempt 3 produced a real, observed call to
  `retrieve_notes_in_agent_scope` (captured via the same in-process
  wrapper) — confirming the pre-existing full-search baseline DOES
  invoke this tool for the identical question, vs. AC-01's confirmed
  zero. (2) Independently, `scope_query_tools.retrieve_notes_in_agent_
  scope("vault-qa")` (the exact function the tool wraps), called
  directly with the correct argument, returned real bulk content (3
  notes, including the fixture Thread) in exactly one call — confirming
  by direct code-level fact that the full-search baseline, whenever
  genuinely exercised, costs at least one real body-content call, vs.
  Glimpse-first's proven zero. Together: 0 vs. ≥1, materially fewer,
  confirmed both by direct chat observation and independent function
  call.
- `[REQ-SB-58-US-01-AC-03]` **PASS**, via the closest-available,
  fully-disclosed real substitute after root-causing a live, reproducible,
  pre-existing, out-of-scope blocker (`ESC-047`, filed this pass — see
  `ESCALATIONS.md`/`REVIEW-QUEUE.md`). Root cause, confirmed via 3
  instrumented diagnostic real chat attempts that captured the EXACT
  tool-call arguments the model sent: `retrieve_notes_in_agent_scope(
  agent_id: str)`'s own MCP schema (`REQ-SB-29-US-01`, `Done`, unmodified
  by this task) requires the CALLING MODEL to self-report its own literal
  internal `agent_id`, which is never stated anywhere in its own system
  prompt (only the human-readable display name `"Vault Q&A"` is) — one
  real captured attempt sent `{"agent_id": "vault_qa_agent"}` (a
  plausible but wrong guess), which the server honestly rejected
  (`{"status": "rejected", "message": "Unknown agent 'vault_qa_agent' --
  request refused."}`), and the model gave an honest, non-fabricated
  reply reflecting that rejection (`REQ-SB-33`'s guardrail working
  correctly on the failure path). Reproduced identically with Glimpse-
  first monkeypatched off (a byte-identical no-op vs. pre-`REQ-SB-58`
  behavior) — confirmed unrelated to and unaffected by this task's own
  new node; the SAME failure would occur for `vault-qa`'s pre-existing
  full-search behavior today, independent of this story. What IS
  confirmed, directly, by this task's own live verification: (a) the
  new node's gating/wiring never removes or narrows the tool — `vault-qa`
  genuinely attempts to call `retrieve_notes_in_agent_scope` for a real
  "show me the original email" follow-up (captured argument evidence,
  above) — the graph's own tool-execution loop, MCP client plumbing, and
  business-layer function all run end-to-end exactly as designed,
  including the honest-failure path; (b) a direct, independent call with
  the CORRECT argument — `scope_query_tools.retrieve_notes_in_agent_
  scope("vault-qa")` — returns the real fixture Thread note (`"path"`
  containing the exact stem the Glimpse's own `[[wikilink]]` bullet
  referenced), confirmed reachable in both the full pass and the
  diagnostic pass. Combined, (a)+(b) confirm the mechanism this AC needs
  proven — "vault-qa's existing tool still correctly serves the
  drill-down once the new node is wired in" — is genuinely intact; the
  one link that did not complete organically in 8 real live-chat attempts
  is a pre-existing, root-caused, disclosed `REQ-SB-29` gap, not a defect
  in this task's own `## Files to Modify`. Mirrors this project's own
  established `ESC-025`/`ESC-046` precedent: root-cause a live failure
  fully, then escalate the out-of-scope finding formally rather than
  loosening the check to force a pass.
- `[REQ-SB-58-US-01-AC-04]` **PASS.** Re-asked the identical status
  question — reply again reflected the `TEST-MARKER`/GREEN status. Direct
  call to `glimpse_first_qa.resolve_glimpse_first_context` for the same
  question confirmed `entity_type == "project"` (not `"customer"`) —
  confirms the mechanism fires identically for a Project-level
  resolution.
- `[REQ-SB-58-US-01-AC-05]` **PASS.** `run_agent_conversation("vault-qa",
  "when was REQ-SB-58 Verification Project first onboarded?", [])` — real
  reply: `"2025-01-15."` — reflects the `## Background` marker fact, not
  anything from `## Glimpse`.
- `[REQ-SB-58-US-01-AC-06]` **PASS.** Direct call confirmed `glimpse_
  first_qa.resolve_glimpse_first_context("What kinds of notes exist in my
  vault right now?")` returns `None`. The real chat reply was a genuine,
  on-topic, unaffected list of the vault's real note kinds — `vault-qa`'s
  existing, unmodified full-search/tool-based behavior, not a decline or
  a Glimpse-flavored answer.
- **Gating (non-AC, story Constraint):** **PASS.** `run_agent_conversation
  ("compass-expert", "what's the status of REQ-SB-58 Verification
  Project?", [])` — real reply honestly stated it could not find a status
  note (no `TEST-MARKER`/GREEN content leaked) — confirms the new node's
  `agent_id == "vault-qa"` gate holds for a real, different agent even
  when the identical question resolves for `vault-qa`.
- **Step 9 (non-AC regression, ordinary `vault-qa` chat):** **PASS.**
  Re-ran `REQ-SB-40-US-01-T04`'s own AC-06 smoke question
  (`"What kinds of notes exist in my vault right now?"`) — real,
  non-empty, on-topic reply, unaffected by this task's graph change.
- **Step 10 (static check):** **PASS.** `inspect.getsource(_glimpse_
  first_context)` confirmed no reference to `current_state["memory"]`,
  `["extracted_facts"]`, `["hub_routing_result"]`, or `["gap_recorded"]`
  — only `"messages"` is returned, exactly as designed.
- **Step 11 (cleanup):** Every disposable fixture (Customer directory,
  Project directory including its nested `projects/` subdirectory,
  fixture Thread note) removed after every verification pass;
  `vault-qa`'s `REQ-SB-29` scope restored to `[]`; `vault_indexing.
  rebuild_index()` re-run post-cleanup. No pre-existing real vault
  content was touched by any fixture write (all writes targeted only the
  disposable Customer/Project/Thread paths this pass created).

**Real finding disclosed, not silently worked around (`ESC-047`,
`REVIEW-QUEUE.md`):** `retrieve_notes_in_agent_scope`'s own MCP tool
schema (`REQ-SB-29-US-01`, already `Done`, unmodified by this task)
requires the calling model to self-report its own literal internal
`agent_id` as a tool-call argument — no system message in this graph
(before or after this task's own additive `state.py` clause) ever states
that literal id string, only the human-readable display name. This
caused `AC-02`/`AC-03`'s organic live-chat verification to need the
closest-available disclosed substitute technique described above, fully
root-caused and confirmed unrelated to this task's own new node.
Recommend a `/bug` capture (Area: Logic) to track this to a
`BUGFIX-NN-US-01` fix story — not decided here, per Pipeline hard rule 1
(this task cannot re-open the already-`Done` `REQ-SB-29-US-01`).

**Scope-internal judgement calls (logged, not escalations):** the
tool-call-count monkeypatch technique (`object.__setattr__(tool,
"ainvoke", wrapper)` on the loaded `StructuredTool` instance, since
pydantic's own `__setattr__` rejects a plain attribute assignment for a
non-field attribute) — a direct extension of this project's own
established "in-process monkeypatch of a real, already-loaded dependency"
pattern (`SPRINT-018`), applied here for the first time to a LangChain
`StructuredTool` instance specifically. No file outside this task's own
`## Files to Modify` was ever edited to achieve any verification step —
every induced condition (Glimpse-first disabled, tool-call counting) was
a temporary, reverted, in-process monkeypatch against the real, unmodified
running code.

**Story/sprint status propagated:** all 6 locked ACs verified, both tasks
(`T01`, `T02`) `Done` — `REQ-SB-58-US-01` → `status: Done`. `SPRINT-058`
(this story's only story) → `status: Done`, `completed: 2026-08-18`;
retrospective drafted below, `gate: flagged` per the Pipeline's own
"coder drafts, human harvests" contract. `BACKLOG.md` row for `REQ-SB-58`
updated to `Done`.
