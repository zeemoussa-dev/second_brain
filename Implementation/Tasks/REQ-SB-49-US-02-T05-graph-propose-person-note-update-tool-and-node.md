---
id: REQ-SB-49-US-02-T05
title: graph.py — conditionally-bound propose_person_note_update tool + _propose_person_note_update node + name-keyed resolver + Cockpit-thread-ref threading
parent_story: REQ-SB-49-US-02
requirement_id: REQ-SB-49
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-038 created) — carried from the parent story; the human reviews ADR-038 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-49-US-02-T02, REQ-SB-49-US-02-T03]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-49-US-02-T05 — `graph.py`'s `propose_person_note_update` Tool + Node

## Parent Story

- Story: [[REQ-SB-49-US-02]] — `../UserStories/REQ-SB-49-US-02-cockpit-person-mention-proposed-note-edit.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-49 *Cockpit @Mentions*

---

## Objective

Extend `graph.py`'s SAME compiled `StateGraph` with a third interceptable bound tool, `propose_person_note_update(person_name, instruction)` — this graph's FIRST **conditionally**-bound tool (`ADR-038` point 2), bound only when `skill_registry.has_skill_access(agent_id, "propose_person_note_update")` is true. Add a new, read-only, name-keyed `people_extraction.find_person_note_by_name` resolver (sibling of `find_existing_person_note`). Thread a new, optional Cockpit-thread reference (`cockpit_subject_kind`/`cockpit_subject_note_stem`) additively through `AgentConversationState` and `run_agent_conversation`'s own signature, sourced from `threads.send_user_message`, so the node's own `invoke_skill` call can pass it into the Skill's `args`.

---

## Starting State → End State

**Before / Inputs:**
- Real, current `graph.py` already has two bound-tool interceptions (`request_cross_section_help`/`route_hub_request`, `record_knowledge_gap`/`_record_knowledge_gap`) — both bound UNCONDITIONALLY in `run_agent_conversation`'s own `tools` list (full real file already read in full for this decomposer pass; **read the REAL current file again immediately before editing** — this is this project's most actively-extended shared file, per repeated prior-sprint Learnings findings).
- `state.py`'s `AgentConversationState` has no Cockpit-thread-ref fields yet.
- `people_extraction.py` has `find_existing_person_note(email)` (email-keyed) but no name-keyed sibling.
- `threads.py::send_user_message` calls `agent_orchestration.run_agent_conversation(agent_id, message_text, history, memory)` — 4 positional args, no thread-ref.
- `T02` has landed the `propose_person_note_update` Skill/handler; `T03` has landed the `"cockpit_mention"` trigger literal.

**After / Outputs:**
- `graph.py` gains: the `propose_person_note_update` tool definition; the `_propose_person_note_update` node; one more `_route_after_model` branch; the node wired into `_build_graph`; `run_agent_conversation`'s tools list CONDITIONALLY extended; two new optional params on `run_agent_conversation` threaded into `initial_state`.
- `state.py`'s `AgentConversationState` gains `cockpit_subject_kind: str | None`, `cockpit_subject_note_stem: str | None`.
- `people_extraction.py` gains `find_person_note_by_name(person_name) -> dict | None`.
- `threads.py::send_user_message`'s own `run_agent_conversation` call passes `cockpit_subject_kind=subject_kind, cockpit_subject_note_stem=subject_note_stem`.
- `agents_router.py`'s own one-on-one `run_agent_conversation` call site is UNCHANGED (both new params default `None`) — a `people-producer` chatted with one-on-one outside any Cockpit still gets the tool bound (per `has_skill_access` alone, `ADR-038` point 2's own literal wording), but the node's own subject refs are `None` there, so `T02`'s handler returns its documented `{"status": "unavailable", ...}` honest refusal rather than crashing or fabricating a thread.

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/state.py` — extend `AgentConversationState` with two new keys, placed after `gap_recorded`:
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
      cockpit_subject_kind: str | None
      cockpit_subject_note_stem: str | None
  ```
  (No other line of `state.py` changes — `history_entries_to_messages` is untouched.)
- `src/backend/app/business/people_extraction.py` — add one new function, placed immediately after `find_existing_person_note`:
  ```python
  def find_person_note_by_name(person_name: str) -> dict | None:
      """Read-only, name-keyed sibling of find_existing_person_note
      (ADR-038 point 4) -- resolves an @PersonName mention (e.g.
      "AhmedMoussa" or "Ahmed Moussa") against every real Person note's
      own frontmatter "name" field, by case-insensitive,
      whitespace-stripped equality. Scans vault_indexing.get_index() for
      entries with frontmatter.get("type") == "Person" -- NEVER creates a
      note, never guesses at the nearest-sounding name (Scenario 4).
      Returns {"note_path": str, "name": str} or None."""
      normalized_target = re.sub(r"\s+", "", person_name).lower()
      for entry in vault_indexing.get_index().values():
          frontmatter = entry["frontmatter"]
          if frontmatter.get("type") != "Person":
              continue
          candidate_name = frontmatter.get("name") or ""
          if re.sub(r"\s+", "", candidate_name).lower() == normalized_target:
              return {"note_path": entry["path"], "name": candidate_name}
      return None
  ```
  Add imports at module top: `import re` and `from app.business import vault_indexing` (merge into the existing `from app.business import customer_hub_linking, partner_hub_linking` line's sibling imports — add as its own new `from app.business import vault_indexing` line if a merged single-line import would conflict with existing style; either is acceptable, do not duplicate an import of the same module twice).
- `src/backend/app/business/cockpit/threads.py` — the ONE line inside `send_user_message`:
  ```python
      result = await agent_orchestration.run_agent_conversation(
          agent_id, message_text, history, memory,
          cockpit_subject_kind=subject_kind, cockpit_subject_note_stem=subject_note_stem,
      )
  ```
  (Every other line of `send_user_message`, and every other function in `threads.py`, is left unchanged — `T01`'s own `save_thread` addition is a separate, additive function.)
- `src/backend/app/business/agent_orchestration/graph.py`:
  - Add imports: `from app.business import (agent_keywords, agent_registry, knowledge_gap_tracking, people_extraction, provider_registry, section_registry, skill_registry)` (merge `people_extraction` and `skill_registry` into the existing import block — do not duplicate).
  - Add the new tool definition, placed immediately after `record_knowledge_gap`:
    ```python
    @tool
    def propose_person_note_update(person_name: str, instruction: str) -> str:
        """Call this when a person-directed Cockpit instruction names a
        real person and describes a specific change to make to their
        Person note (e.g. "@AhmedMoussa is leaving for Core42, update his
        note"). person_name: the mentioned person's name, as written (e.g.
        "Ahmed Moussa" or "AhmedMoussa"). instruction: the specific change
        to propose, in your own words. Only call this once you have
        identified a REAL, SPECIFIC change to propose -- a bare mention
        with no discernible instruction must never trigger this tool.

        Deliberately NOT registered on the shared MCP server, mirroring
        request_cross_section_help/record_knowledge_gap (ADR-017 point 7,
        ADR-032 point 1) -- bound directly to this graph's own model call
        only, and ONLY when the calling agent has a real
        skill_registry.has_skill_access grant for the
        "propose_person_note_update" Skill (ADR-038 point 2 -- this
        graph's first CONDITIONALLY bound tool). This function's own body
        is never actually invoked -- the graph's conditional edge (see
        _route_after_model, below) intercepts every call to this tool and
        routes to the _propose_person_note_update node instead, which
        resolves the real Person note read-only first, then dispatches
        through skill_registry.invoke_skill's full working-mode gate
        (ADR-038 point 4)."""
        raise NotImplementedError(
            "propose_person_note_update is intercepted by the "
            "_propose_person_note_update graph node -- this function body "
            "is never actually invoked."
        )
    ```
  - Add the node, placed after `_record_knowledge_gap`:
    ```python
    def _propose_person_note_update(current_state: AgentConversationState) -> dict:
        last_message = current_state["messages"][-1]
        tool_call = next(
            tc for tc in last_message.tool_calls if tc["name"] == "propose_person_note_update"
        )
        person_name = tool_call["args"]["person_name"]
        instruction = tool_call["args"]["instruction"]
        match = people_extraction.find_person_note_by_name(person_name)
        if match is None:
            # No gate involvement at all -- an honest "not found" reply,
            # never a fabricated match, never a created note (Scenario 4,
            # ADR-038 point 4).
            tool_message = ToolMessage(
                content=json.dumps({
                    "found": False,
                    "message": f"No matching Person note found for {person_name}.",
                }),
                tool_call_id=tool_call["id"],
            )
            return {"messages": current_state["messages"] + [tool_message]}
        result = skill_registry.invoke_skill(
            current_state["agent_id"],
            "propose_person_note_update",
            args={
                "note_path": match["note_path"],
                "person_name": match["name"],
                "instruction": instruction,
                "subject_kind": current_state.get("cockpit_subject_kind"),
                "subject_note_stem": current_state.get("cockpit_subject_note_stem"),
            },
            trigger="cockpit_mention",
        )
        tool_message = ToolMessage(content=json.dumps(result), tool_call_id=tool_call["id"])
        return {"messages": current_state["messages"] + [tool_message]}
    ```
  - Extend `_route_after_model` with one more branch, checked AFTER the existing `record_knowledge_gap` check:
    ```python
    def _route_after_model(current_state: AgentConversationState) -> str:
        if current_state.get("error") is not None or current_state.get("reply") is not None:
            return "extract_memory"
        last_message = current_state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", None) or []
        if any(tc["name"] == "request_cross_section_help" for tc in tool_calls):
            return "route_hub_request"
        if any(tc["name"] == "record_knowledge_gap" for tc in tool_calls):
            return "record_knowledge_gap"
        if any(tc["name"] == "propose_person_note_update" for tc in tool_calls):
            # Intercepted BEFORE the generic execute_tools node, exactly
            # like the two existing bound tools above -- see
            # propose_person_note_update's own NotImplementedError body.
            return "propose_person_note_update"
        return "execute_tools"
    ```
  - Extend `_build_graph`: add `builder.add_node("propose_person_note_update", _propose_person_note_update)`, add `"propose_person_note_update"` to the conditional-edges destination list, add `builder.add_edge("propose_person_note_update", "call_model")`.
  - Extend `run_agent_conversation`'s own signature/body:
    ```python
    async def run_agent_conversation(
        agent_id: str,
        message: str,
        history: list[dict],
        memory: list[dict] | None = None,
        cockpit_subject_kind: str | None = None,
        cockpit_subject_note_stem: str | None = None,
    ) -> dict:
        ...
        tools = list(await mcp_client.load_agent_tools(agent_id)) + [
            request_cross_section_help,
            record_knowledge_gap,
        ]
        if skill_registry.has_skill_access(agent_id, "propose_person_note_update"):
            tools.append(propose_person_note_update)
        ...
        initial_state: AgentConversationState = {
            "agent_id": agent_id,
            "messages": messages,
            "model": model,
            "tools": tools,
            "reply": None,
            "error": None,
            "memory": memory or [],
            "extracted_facts": [],
            "hub_routing_result": None,
            "gap_recorded": None,
            "cockpit_subject_kind": cockpit_subject_kind,
            "cockpit_subject_note_stem": cockpit_subject_note_stem,
        }
        ...
    ```
    (Only the signature line, the `tools` block, and the `initial_state` literal change — every other line of `run_agent_conversation`, including its `try/except`/error-handling shape, stays byte-for-byte unchanged.)

---

## Constraints

- Inherits from parent story.
- `propose_person_note_update` must NOT be registered on `app/api/mcp_server.py` and must NOT be loaded via `mcp_client.py` — bound directly in `run_agent_conversation`'s own `tools` list only, CONDITIONALLY (the one deliberate structural difference from its two unconditionally-bound siblings, `ADR-038` point 2).
- `_propose_person_note_update` must call `people_extraction.find_person_note_by_name` READ-ONLY first — a real match is the ONLY condition under which `skill_registry.invoke_skill` is ever called; no match means no gate involvement of any kind.
- `trigger="cockpit_mention"` on the one `invoke_skill` call this node makes — never `"chat"`/`"direct"`/`"hub_routed"`.
- If the model's own `tool_calls` list contains more than one of `request_cross_section_help`/`record_knowledge_gap`/`propose_person_note_update` in the same turn, only the FIRST-checked branch fires (existing, accepted `ADR-017`/`ADR-032` limitation, extended unchanged to a third tool — not grounds for new logic this task).
- `cockpit_subject_kind`/`cockpit_subject_note_stem` are additive, default-`None` — `agents_router.py`'s own one-on-one `run_agent_conversation` call site must NOT be edited by this task (its call omits both new params, correctly defaulting to `None`).
- `_call_model`'s pre-existing exception handling, tool-round-count guard, and Provider-unavailable short-circuit must be preserved unchanged. Do not modify `_retrieve_memory`, `_execute_tools`, `_extract_memory`, `route_cross_section_request`, `_route_hub_request`, or `_record_knowledge_gap`.
- `run_agent_conversation`'s own return shape (`{"reply": str, "extracted_facts": list[str]}` / `{"error": str}`) is unchanged.

---

## Tests

<!-- AC-01 (full end-to-end propose flow), AC-04 (honest no-match), and
AC-05 (bare mention -> no proposal) all need a real, live model call
(this project's own established technique for this graph's tool-
interception mechanism, REQ-SB-40-US-01-T04's own precedent) -- no mock. -->

**Manual verification steps:**

1. **[REQ-SB-49-US-02-AC-01]** In a Python shell against the backend `.venv` (real vault, real Provider, `people-producer` granted `propose_person_note_update` — confirmed via `T02`). Ensure `people-producer` is in Manual or Autonomous mode. Pick a real, existing Person note (e.g. "Ahmed Moussa"); read and record its current body. Call `await agent_orchestration.run_agent_conversation("people-producer", "Ahmed Moussa is leaving the company and going to Core42, please update his note", [], cockpit_subject_kind="email", cockpit_subject_note_stem="<a real captured email note stem>")`. Confirm the reply text references a proposed update reflecting the instruction (not a generic non-answer). Re-read the same Person note — confirm its body is BYTE-FOR-BYTE unchanged from the recorded value (the edit is a proposal only, never applied as a side effect of the chat reply itself). Confirm (via `person_note_proposals.list_pending_proposals("email", "<that stem>")`) a new pending proposal exists naming that person/instruction. Clean up via `person_note_proposals.discard_proposal(...)` afterward.
2. **[REQ-SB-49-US-02-AC-04]** Call `await agent_orchestration.run_agent_conversation("people-producer", "Please update @SomeoneWithNoRealNote's record", [], cockpit_subject_kind="email", cockpit_subject_note_stem="<same or another real stem>")`, where "SomeoneWithNoRealNote" matches no real Person note's `name`. Confirm the reply honestly states no matching Person note was found (not a fabricated match, not an error). Confirm no new Person note was created (list `Work/People/` before/after, or reuse `vault_indexing.get_index()`'s own count) and no new pending proposal was recorded for this call.
3. **[REQ-SB-49-US-02-AC-05]** Call `await agent_orchestration.run_agent_conversation("people-producer", "Just chatting about Ahmed Moussa, no specific change needed right now", [], cockpit_subject_kind="email", cockpit_subject_note_stem="<same stem>")` — a real mention with no discernible instruction. Confirm the reply is conversational (the agent may mention Ahmed Moussa) and confirm NO new pending proposal was recorded for this call (`list_pending_proposals` count unchanged from immediately before) — a bare mention alone must never produce a proposal.
4. Non-AC smoke check: confirm `graph._GRAPH.get_graph().nodes` includes `'propose_person_note_update'` alongside all 6 pre-existing nodes (`retrieve_memory`, `call_model`, `execute_tools`, `route_hub_request`, `record_knowledge_gap`, `extract_memory`) plus `__start__`/`__end__`.
5. Static check: confirm `propose_person_note_update` (the graph-bound tool) appears only in `graph.py` across the entire `src/backend/app` tree — never registered on `mcp_server.py`, never loaded via `mcp_client.py` (this is a distinct symbol from `T02`'s `skill_tools.propose_person_note_update` handler of the same name — both are expected to exist, in different modules, by design, per `ADR-038`'s own point 4).
6. Conditional-binding check: confirm `await agent_orchestration.run_agent_conversation("<a real agent WITHOUT propose_person_note_update access, e.g. vault-qa>", "Ahmed Moussa is leaving, update his note", [])` does NOT attempt to call the tool (the model has no such tool bound to choose from) — the reply is ordinary conversational/tool-less text, never a proposal, confirming the conditional bind actually gates on `has_skill_access`.
7. Non-Cockpit context check (the disclosed scope note in the parent story): call `await agent_orchestration.run_agent_conversation("people-producer", "Ahmed Moussa is leaving, update his note", [])` — **no** `cockpit_subject_kind`/`cockpit_subject_note_stem` passed (mirrors `agents_router.py`'s own one-on-one call site). Confirm this does not crash — the reply reflects `T02`'s own honest `"unavailable"` refusal message, never a silent write, never an unhandled exception.
8. Regression check: confirm ordinary chat (a question the model can answer without any tool call) still works unaffected on `vault-qa` (unrelated agent) via the real `POST /agents/{id}/chat` HTTP endpoint, not just the direct function call above.
9. Clean-up: `person_note_proposals.discard_proposal(...)` for any leftover pending proposal from steps above; confirm the real Person note(s) used are left in their original, unmodified state.

**Automated tests:** `n/a — no backend test runner scaffolded yet (no pytest suite exists under src/backend as of this task)`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-01** (Scenario 1) — a real chat instruction naming a real person produces a real proposal reflecting the instruction; the real Person note is unmodified at that point
- [ ] **AC-04** (Scenario 4) — an unmatched name produces an honest "not found" reply; no note created, no proposal produced
- [ ] **AC-05** (Scenario 5) — a bare mention with no discernible instruction produces no proposal
- [ ] `propose_person_note_update` is this graph's first CONDITIONALLY bound tool — bound only when `has_skill_access` is true, confirmed live against both a granted and a non-granted agent
- [ ] `_build_graph` compiles with the new node/branch/loop-back edge on the SAME `StateGraph` — no second graph, no pre-existing node/edge removed
- [ ] `run_agent_conversation`'s public return shape unchanged; the two new params are additive/optional, `agents_router.py`'s own call site left unedited
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Full non-Cockpit support for this capability (a real proposal store for a one-on-one chat context) — explicitly out of this story's scope; step 7 above only confirms the honest, non-crashing refusal, not a new mechanism.
- The confirm/discard endpoints/UI — `T01`/`T06`'s scope.
- The `_dispatch_skill(already_approved=...)` seam and Approve-endpoint wiring — `T04`'s scope (this task's own default-`False` fallthrough is sufficient for `AC-01`/`AC-04`/`AC-05`).
- The "both tool calls in one turn" edge case beyond the existing `if`/`elif`-shaped single-interception behavior — an accepted, pre-existing limitation, not built further this pass.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-038` created at `/plan-tasks` step 1, carried) — the human reviews `ADR-038` and the task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Read the REAL current `graph.py` first — this is this project's most actively-extended shared file** (Learnings, `SPRINT-020`/`SPRINT-030`/`REQ-SB-40-US-01-T04` all found real drift on this exact file between a task's own sample and the real current state by build time). Compose this diff around whatever the real current file actually contains — if a sibling story has landed further additive changes since this task was authored, reconcile against those, log the reconciliation as a scope-internal judgement call, not an escalation.

**Non-Cockpit refusal design (disclosed, not a locked-AC gap):** `run_agent_conversation` is called from two real sites — `threads.py::send_user_message` (Cockpit, this task threads the new params through) and `agents_router.py::chat` (one-on-one, deliberately left unedited). Because `ADR-038`'s own conditional-binding rule (point 2) keys on `has_skill_access` alone, not calling context, `people-producer` chatted with one-on-one outside any Cockpit would still get this tool bound and could still trigger this node — with `cockpit_subject_kind`/`cockpit_subject_note_stem` both `None`. `T02`'s handler already resolves this honestly (`{"status": "unavailable", ...}`, never a crash, never a silent write) — this task's own step 7 confirms that live. Every one of this story's 6 locked ACs is Cockpit-scoped, so this is a disclosed, narrowly-scoped limitation, not a gap in this task's own coverage — a future story could extend real non-Cockpit support if ever needed.

---

## Implementation Log

Read the REAL current `graph.py`/`state.py`/`people_extraction.py`/
`threads.py` first (all four already carried `REQ-SB-40`/`REQ-SB-51`-era
additive changes beyond this task's own illustrative samples — e.g.
`_route_hub_request`/`_record_knowledge_gap` already both real, `graph.py`
already importing `agent_keywords`/`section_registry`/etc.). Composed this
task's diff directly around the real files: `propose_person_note_update`
bound tool (`@tool`, `NotImplementedError` body, mirrors
`record_knowledge_gap`), `_propose_person_note_update` node (read-only
`find_person_note_by_name` first; a real match dispatches through
`skill_registry.invoke_skill(..., trigger="cockpit_mention")`; no match →
honest `ToolMessage`, no gate involvement), one more `_route_after_model`
branch, `_build_graph` extended (new node + conditional-edge destination +
loop-back edge), `run_agent_conversation`'s signature/`tools`
list/`initial_state` extended additively (`cockpit_subject_kind`/
`cockpit_subject_note_stem`, both default `None`). `state.py` gained the
two new optional keys. `people_extraction.py` gained
`find_person_note_by_name` (case-insensitive, whitespace-stripped,
`type == "Person"` scan over `vault_indexing.get_index()`). `threads.py`'s
`send_user_message` now passes the two new kwargs through to
`run_agent_conversation` (in addition to this task's own save-race fix,
logged on `T01`'s Implementation Log since it lives in the same file/
function `T01` also touches).

**Verification — real live model calls (`await
agent_orchestration.run_agent_conversation(...)`) against the real backend
`.venv`, real vault, real Compass Provider, real `people-producer` agent
(Manual mode), using a real Person note ("Mahmoud Moussa",
`Work/People/<operator>@core42.ai.md`) and a real captured email note
stem as the Cockpit-thread ref:**
- **AC-01** — PASS: `"Mahmoud Moussa is leaving the company and going to
  Core42, please update his note"` produced a real reply proposing the
  update; the Person note resolved was confirmed byte-for-byte unchanged
  immediately after the reply; `person_note_proposals.
  list_pending_proposals(...)` confirmed a new real pending proposal
  naming Mahmoud Moussa existed. (Note: the vault has TWO real Person
  notes independently named "Mahmoud Moussa" —
  `<operator>@core42.ai.md` and `<operator-email>.md`; the
  resolver's own first-match scan order isn't guaranteed across runs —
  a pre-existing real vault data-quality condition, not a defect in this
  task's own resolver, which correctly finds *a* real match and never
  fabricates one. Disclosed for spot-check, not a locked-AC gap — no
  Scenario in this story asserts disambiguation behavior for two
  identically-named Person notes.)
- **AC-04** — PASS: a deliberately non-existent name produced an honest
  "couldn't find a matching Person note" reply; no new pending proposal
  recorded.
- **AC-05** — PASS: a bare mention with no discernible instruction
  produced a conversational reply; no new pending proposal recorded.
- Conditional-binding check — PASS: `vault-qa` (no
  `propose_person_note_update` grant) never triggers this tool — its
  reply used its own, unrelated, generic vault-query tool instead
  (confirmed by reply content: it listed real note paths via its own
  ordinary MCP tool, never echoed this Skill's own proposal/
  not-found/unavailable wording).
- Non-Cockpit context check — PASS: calling `run_agent_conversation`
  without `cockpit_subject_kind`/`cockpit_subject_note_stem` (mirrors
  `agents_router.py`'s real one-on-one call site) produced `T02`'s own
  honest `"unavailable"` refusal message, no crash, no silent write.
- Graph node registration — PASS: `_GRAPH.get_graph().nodes` includes
  `propose_person_note_update` alongside all pre-existing nodes.
- Static check — PASS: the graph-bound `propose_person_note_update`
  symbol appears only in `graph.py` (never on `mcp_server.py`/
  `mcp_client.py`) — a distinct symbol from `T02`'s
  `skill_tools.propose_person_note_update` handler, by design.
- Regression check — PASS: ordinary chat on `vault-qa` still works
  unaffected via the real `POST /agents/{id}/chat` endpoint.

**Real, live-discovered defect found and fixed in-scope during this
task's own live verification (full writeup on `T01`'s Implementation
Log, since the fix lands in `threads.py`, a file `T01` also owns):** a
save race in `send_user_message` clobbered a mid-loop-created pending
proposal with a stale in-memory `thread` copy. Fixed before AC-01/`T06`
could be verified through the real Cockpit chat end-to-end; independently
re-confirmed AC-01 both via direct function call (before the frontend
round trip) and via the real running frontend (`T06`'s own verification).

gate: flagged (carried, trigger-3 — `ADR-038`) 2026-08-14 — no NEW
coder-owned trigger fired beyond the disclosed duplicate-Person-note-name
observation (a pre-existing real vault data condition, not a build
defect) and the `T01`-filed save-race fix (scope-internal, same-story,
same-file); no `ESCALATIONS.md` entry; AC-01/AC-04/AC-05 all verified
live with real model calls and a real, observed outcome.
