---
id: REQ-SB-36-US-01-T06
title: mcp_client.py — new load_agent_tools(agent_id), removes load_vault_query_tools; graph.py call-site edit
parent_story: REQ-SB-36-US-01
requirement_id: REQ-SB-36
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-022 created) — carried from the parent story; the human reviews ADR-022 alongside this task breakdown. Decomposer-owned finding: a real same-call-site collision risk with REQ-SB-20-US-01-T05, resolved via a cross-story depends_on edge, not a new ADR — see ## Context/Notes. Unaffected by the mid-build Provider-resolution correction recorded on T04/T05 (ESC-019) -- this task's own scope (mcp_client.py/graph.py) was not touched by that correction."
phase: P1
depends_on: [REQ-SB-36-US-01-T04, REQ-SB-20-US-01-T05]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-36-US-01-T06 — `mcp_client.py`'s access-control tool-binding gap fix

## Parent Story

- Story: [[REQ-SB-36-US-01]] — `../UserStories/REQ-SB-36-US-01-web-research-skill.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-36 *Agent Knowledge Bootstrapping via Delegated Research*

---

## Cross-story dependency — a real sequencing finding, not an ADR change

This task depends on `REQ-SB-20-US-01-T05` (a different story's task, `status: Ready`) because both tasks edit the exact same `app/business/agent_orchestration/graph.py::run_agent_conversation` call site (`asyncio.run(mcp_client.load_vault_query_tools())`). Building this task first, or independently, risks silently overwriting whichever change lands second — the exact antipattern `MEMORY.md`'s own `REQ-SB-26-US-01-T03` Pattern entry names ("compose the new change around the REAL current file, never overwrite it with the stale sample"). **Do not start this task until `REQ-SB-20-US-01-T05` is `Done`** — read that task's own real, already-landed code (not this task's own sample below, which is written against `T05`'s own documented "After" shape) before editing `graph.py`.

---

## Objective

Close the live-discovered access-control gap `ADR-022` point 6 names: `mcp_client.load_vault_query_tools()` returns every tool on the shared MCP server with no per-agent filtering, meaning any agent's ordinary chat turn could already reach `skill_tools.py`'s catalog (including the now-real `web_research`) regardless of `skill_registry.has_skill_access`. Add `mcp_client.load_agent_tools(agent_id) -> list`, filtering by `has_skill_access`; wire `graph.py::run_agent_conversation` to call it in place of the old function.

---

## Starting State → End State

**Before / Inputs:**
- `T04` has landed `skill_tools.SKILLS` with `"web-research"` as a real, working skill.
- `REQ-SB-20-US-01-T05` has landed (real, current `graph.py`) — by that task's own documented "After" state, `run_agent_conversation`'s tools line reads `tools = list(asyncio.run(mcp_client.load_vault_query_tools())) + [request_cross_section_help]`.
- `mcp_client.py` has one function, `load_vault_query_tools()`, no filtering.

**After / Outputs:**
- `mcp_client.py` gains `load_agent_tools(agent_id: str) -> list` — fetches the full server tool list, then keeps a tool unconditionally if its name is not a `skill_tools.SKILLS` key (the vault-query tools stay always-available), and keeps a skill-catalog tool only if `skill_registry.has_skill_access(agent_id, skill_id)` is `True`. `load_vault_query_tools()` itself is removed (no other caller, once this task's own edit lands).
- `graph.py::run_agent_conversation` calls `mcp_client.load_agent_tools(agent_id)` in place of `mcp_client.load_vault_query_tools()`, composed around whatever `REQ-SB-20-US-01-T05`'s own real `request_cross_section_help`-extended tools line actually looks like at build time (not this task's own necessarily-stale sample).

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/mcp_client.py`:
  ```python
  from app.business import skill_registry, skill_tools


  async def load_agent_tools(agent_id: str) -> list:
      """Filters the shared MCP server's full tool list per-agent
      (ADR-022 point 6) -- the four core vault-query tools stay always
      available; a skill-catalog tool (skill_tools.SKILLS) is only
      included when skill_registry.has_skill_access(agent_id, skill_id)
      is True. Replaces load_vault_query_tools() as this module's one
      public entry point -- reuses has_skill_access exactly as
      skill_registry.py's own docstring already anticipated, not a new
      enforcement concept."""
      all_tools = await _MCP_CLIENT.get_tools()
      return [
          t for t in all_tools
          if t.name not in skill_tools.SKILLS or skill_registry.has_skill_access(agent_id, t.name)
      ]
  ```
  (`load_vault_query_tools` removed in full — confirm, by direct grep, that no other caller of that name remains before deleting it.)
- `src/backend/app/business/agent_orchestration/graph.py` — one call-site edit inside `run_agent_conversation`, composed around the REAL current file (read it fresh at build time — do not trust this task's own sample below if `REQ-SB-20-US-01-T05`'s real landed code differs):
  ```python
      tools = list(await mcp_client.load_agent_tools(agent_id)) + [request_cross_section_help]
  ```
  (Note: `load_agent_tools` is `async def` — if the real current call site still wraps the old function in `asyncio.run(...)` rather than a genuine `await`, per `MEMORY.md`'s own standing async-graph-node Constraint this whole chain must already be `async def` end-to-end by the time this task builds, REQ-SB-25-US-01 having already fixed that; use a real `await`, never re-introduce a nested `asyncio.run()`.)

---

## Constraints

- Inherits from parent story and `ADR-022` point 6.
- `load_agent_tools` must keep every non-skill-catalog tool (the four core vault-query tools) unconditionally — never gate them.
- A skill-catalog tool is gated by `skill_registry.has_skill_access(agent_id, skill_id)` exactly — reuse this existing function, do not reimplement access checking here.
- `request_cross_section_help` (bound directly in `run_agent_conversation`'s own tools list, never registered on `mcp_server.py`/loaded via `mcp_client.py`, per `ADR-017` point 7) must remain unaffected by this filtering — it is added to the tools list separately, outside `load_agent_tools`'s own return value.
- Must compose around `graph.py`'s REAL current file at build time, not a stale sample — per `MEMORY.md`'s own standing Pattern for this exact class of finding.
- Must preserve `MEMORY.md`'s own standing async-graph-node Constraint — `load_agent_tools` and its call site must be genuinely `async def`/`await`, never a nested `asyncio.run()`.

---

## Tests

<!-- No locked AC is tagged directly to this task -- AC-02's own locked
text (an ungranted agent's invocation is refused) is already fully
covered by T05's own direct REST/skill_registry-layer verification. This
task additionally closes the SAME gate for the conversational chat path,
forward-looking correctness per ADR-022 point 6, verified by a non-AC
smoke check -- mirrors REQ-SB-21-US-01-T02's own precedent for a task
with no AC-tagged step of its own. -->

**Manual verification steps:**
1. Non-AC smoke check: confirm, by direct grep across `src/backend`, that `load_vault_query_tools` has zero remaining callers/references after this edit.
2. Non-AC smoke check: in a Python shell against the backend `.venv`, call `await mcp_client.load_agent_tools("todo-capture")` for an agent with NO skill access granted. Confirm the returned tool list includes the four core vault-query tools but does NOT include `"web-research"`/`"diagram-understanding"` by name.
3. Non-AC smoke check: `skill_registry.grant_skill_access("todo-capture", "web-research")`, then re-call `await mcp_client.load_agent_tools("todo-capture")`. Confirm `"web-research"` is now present in the returned list. `skill_registry.revoke_skill_access("todo-capture", "web-research")` to clean up.
4. Non-AC smoke check: confirm `run_agent_conversation("email-capture", "What kinds of notes exist in my vault right now?", [])` (a message with no plausible reason to trigger any skill or Hub-routing tool) still returns `{"reply": <non-empty string>}` exactly as `REQ-SB-25-US-01-T07`'s/`REQ-SB-20-US-01-T05`'s own smoke checks already confirmed — proving this task's tool-binding edit does not disturb the existing non-tool-calling conversational path.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `load_agent_tools(agent_id)` correctly gates every `skill_tools.SKILLS` entry by `has_skill_access`, never gates the four core vault-query tools
- [x] `load_vault_query_tools` is fully removed, zero remaining callers
- [x] `graph.py`'s call site is composed around the REAL current file (confirmed fresh at build time), not a stale sample
- [x] The existing non-tool-calling conversational smoke check still passes unchanged
- [x] The whole chain stays genuinely `async def`/`await` — no nested `asyncio.run()` reintroduced
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `request_cross_section_help`'s own binding/routing logic — `REQ-SB-20-US-01-T05`'s own scope, reused as-is.
- `model_factory.py` — untouched.
- Binding `web_research` into the conversational tool loop as a *feature* (general "ask your agent to search the web" chat wiring) — explicitly out of scope per the parent story's own Non-Goals; this task closes an access-control gap only, it does not add new conversational capability.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-022` created at `/plan-tasks` step 1) — the human reviews `ADR-022` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Why this task depends on a different story's task (`REQ-SB-20-US-01-T05`):** `ADR-022` point 6 was written describing `load_vault_query_tools()` as having "no other caller" once removed — true only in isolation. `REQ-SB-20-US-01-T05` (a sibling story, `Ready`, unbuilt at decomposition time) *also* edits this exact same call site, extending the tools list with `request_cross_section_help`. Building either task without accounting for the other risks one silently overwriting the other's real, landed change. This decomposer pass added the `depends_on` edge to prevent that — a scope-internal sequencing correction, not a new architectural decision, so it is not itself a MUST-FLAG trigger (recorded in the parent story's own `## Notes` for full reasoning).

---

## Implementation Log

Confirmed `REQ-SB-20-US-01-T05` was `Done` before starting, then read the
REAL current `graph.py` (not this task's own sample) — it matched this
task's own documented "After" baseline exactly (`tools =
list(await mcp_client.load_vault_query_tools()) + [request_cross_section_help]`),
so no further reconciliation was needed beyond the one straightforward
edit. Built exactly per spec: `mcp_client.py` gained `load_agent_tools(
agent_id) -> list` (filters the shared server's tool list — a tool is
always kept unless its name is a `skill_tools.SKILLS` key, in which case
it's kept only if `skill_registry.has_skill_access(agent_id, t.name)` is
`True`); `load_vault_query_tools` removed in full, confirmed by direct
grep — zero remaining callers anywhere in `src/backend` (only
`mcp_client.py`'s own docstring mentions the old name, as a comment, not a
call). `graph.py`'s one call site now reads `tools = list(await
mcp_client.load_agent_tools(agent_id)) + [request_cross_section_help]`.

**No AC-ID tagged to this task** (per its own Tests note — `AC-02`'s
locked text is already fully covered by `T05`'s own direct REST-layer
verification; this task closes the same gap for the conversational path
as forward-looking correctness). All 4 non-AC manual verification steps
performed:

1. Grep confirmed zero remaining callers of `load_vault_query_tools`.
2/3. **A genuine environmental blocker was hit and worked around with an
   equivalent, still-real verification technique, not skipped:** this
   project's own documented MCP-loopback port (`8001`, hardcoded in
   `mcp_client.py`, per `ADR-015`) was held by an unkillable "ghost" TCP
   listener — confirmed via `Get-NetTCPConnection`/`Get-Process`/`tasklist`/
   `wmic`/.NET `Process.GetProcessById`, all agreeing the port is
   `LISTEN`-owned by a PID that does not exist in any enumerable process
   table on this host (no admin rights available to investigate further
   via `netstat -anob`). Since a live round trip against THIS exact port
   is structurally required for these two steps (`mcp_client._MCP_CLIENT`
   is hardcoded to it, out of this task's own scope to change) and the
   stale listener serves genuinely OLD code (confirmed: its own `/skills`
   response lists only `diagram-understanding`, missing this story's own
   new `web-research` entry), a live round trip against it would produce
   a MISLEADING result (the new skill would appear "always filtered out"
   regardless of grant status — a false negative from stale infrastructure,
   not a real code check). Instead, verified the REAL, unmodified
   `load_agent_tools` function directly via an in-process monkeypatch of
   `_MCP_CLIENT.get_tools` (the established "in-process monkeypatch of a
   real, already-loaded dependency" Pattern, `MEMORY.md`/`Learnings.md` →
   `SPRINT-018`) returning a synthetic tool list including
   `web-research`/`diagram-understanding` plus 4 vault-query-shaped names:
   confirmed the returned list for an agent with NO skill access excluded
   both skill-catalog tools but kept all 4 vault-query names; after
   granting `web-research` access, the returned list correctly included
   it (`diagram-understanding` still excluded); cleanly reverted the
   monkeypatch. This exercises the real function body's real filtering
   logic end-to-end, just not through a live network round trip against
   the specific stuck port.
4. **Verified live, for real, against the actual live port `8001`** (this
   step doesn't depend on the NEW `web-research` registration being
   present there, only on the ordinary non-tool-calling path still
   working, so the stale-but-functioning ghost listener is a valid real
   peer for it): `await run_agent_conversation("email-capture", "What
   kinds of notes exist in my vault right now?", [])` — real MCP round
   trip succeeded (`200 OK` from the loopback `/mcp` mount), a real tool
   call was made (the model chose to look up vault note kinds), a real
   Compass completion (`200 OK`) produced the final reply:
   `{'reply': 'The current note kinds in your vault are:\n- Customers\n-
   Emails\n- Files\n- Guides\n- Meetings\n- Newsletters\n- Notifications\n-
   Partners\n- People', 'extracted_facts': [...]}` — a real, non-empty
   string, confirming this task's own `load_agent_tools` call-site edit
   introduced no regression to the existing conversational path.

The whole chain stayed genuinely `async def`/`await` throughout — no
nested `asyncio.run()` reintroduced (confirmed by code inspection; the
live smoke check in step 4 is itself direct proof the async chain works
end-to-end without the historical self-connection failure `MEMORY.md`
already documents for the nested-event-loop antipattern).

**Flagged, not silently left unresolved:** port `8001`'s own unkillable
ghost listener is recorded in `REVIEW-QUEUE.md` for a human restart/reboot
before a future session needs a genuinely fresh live MCP round trip on
that exact port.
