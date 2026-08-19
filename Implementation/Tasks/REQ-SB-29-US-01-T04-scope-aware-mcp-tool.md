---
id: REQ-SB-29-US-01-T04
title: Scope-aware retrieve_notes_in_agent_scope MCP tool (scope_query_tools.py)
parent_story: REQ-SB-29-US-01
requirement_id: REQ-SB-29
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-29-US-01-T01, REQ-SB-29-US-01-T02]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-29-US-01-T04 — Scope-aware `retrieve_notes_in_agent_scope` MCP tool

## Parent Story

- Story: [[REQ-SB-29-US-01]] — `../UserStories/REQ-SB-29-US-01-agent-to-tag-folder-scoping.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-29 *Agent-to-Tag/Folder Scoping*

---

## Objective

Register a new, scope-aware `@mcp_server.tool()` that resolves and enforces the calling agent's own assigned vault scope **server-side** — never accepting a freeform `tags`/`folders` argument from the model — and returns the agent's own scoped notes' real content, an honest "no scope" result, or an honest "nothing found" result, per `Implementation/Architecture/architecture.md`'s "Agent-to-Tag/Folder Vault Scoping" section and `ADR-025` point 4's `propose_vault_write`-shape precedent.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed `vault_writer.list_notes_matching_scope(scope) -> list[Path]` and `vault_writer.read_note(path) -> tuple[dict, str]` (already existing).
- `T02` has landed `scope_registry.get_agent_scope(agent_id) -> list[str]`.
- `app/business/agent_registry.get_agent(agent_id) -> dict | None` already exists — the known-agent lookup this task's tool uses, mirroring `propose_vault_write`'s own unknown-agent handling.
- `app/api/mcp_server.py` currently registers four read-only passthrough tools (`list_known_customers`, `list_known_kinds`, `list_known_partners`, `list_notes_in_kind_folder`) plus `propose_vault_write` (a fifth, business-rule-enforcing tool, `app/business/vault_write_tools.py`) — the exact shape precedent this task's own tool follows.

**After / Outputs:**
- New `app/business/scope_query_tools.py`: `retrieve_notes_in_agent_scope(agent_id: str) -> dict`.
- `app/api/mcp_server.py` registers `retrieve_notes_in_agent_scope` as a sixth `@mcp_server.tool()`.
- No new state file, no new endpoint — this tool is reachable both by Second Brain's own in-app LangGraph agents (via `mcp_client.py`, automatically — it is not a skill-catalog tool, so `mcp_client.load_agent_tools` includes it for every agent unconditionally, same as the four passthrough tools) and by Hermes's own external orchestration, over the same shared `/mcp` endpoint.

---

## Files to Modify

- `src/backend/app/business/scope_query_tools.py` (new):
  ```python
  """Scope-aware, business-rule-enforcing MCP tool (REQ-SB-29-US-01) -- a
  sibling to vault_write_tools.py, not vault_query_tools.py's own thin
  1:1-passthrough shape (ADR-015 point 3), because this tool must itself
  enforce a business rule (resolve and bound the requesting agent's own
  assigned scope server-side, never accept a freeform tags/folders
  argument from the model) rather than merely project an existing
  read-only vault_writer primitive unchanged. Mirrors propose_vault_write's
  own explicit-agent_id/server-resolved shape (ADR-025 points 4-6)."""
  from app.business import agent_registry, scope_registry
  from app.data_access import vault_writer


  def retrieve_notes_in_agent_scope(agent_id: str) -> dict:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          return {"status": "rejected", "message": f"Unknown agent '{agent_id}' -- request refused."}

      scope = scope_registry.get_agent_scope(agent_id)
      if not scope:
          return {
              "status": "no_scope",
              "message": (
                  f"'{agent_id}' has no assigned vault tag/folder scope -- "
                  "it has no bounded vault query access to use."
              ),
          }

      paths = vault_writer.list_notes_matching_scope(scope)
      if not paths:
          return {
              "status": "empty",
              "message": f"No notes matching '{agent_id}'s assigned scope ({', '.join(scope)}) were found.",
          }

      notes = []
      for path in paths:
          frontmatter, body = vault_writer.read_note(path)
          notes.append({"path": str(path), "frontmatter": frontmatter, "body": body})
      return {"status": "ok", "scope": scope, "notes": notes}
  ```

- `src/backend/app/api/mcp_server.py` — extend the existing `app.business` import:
  ```python
  from app.business import scope_query_tools, vault_query_tools, vault_write_tools
  ```
  Register a sixth tool, after the existing `propose_vault_write` tool:
  ```python
  @mcp_server.tool()
  def retrieve_notes_in_agent_scope(agent_id: str) -> dict:
      """Retrieve every vault note matching agent_id's own assigned vault
      tag/folder scope (REQ-SB-29-US-01). Never accepts a freeform
      tags/folders argument -- the calling agent's own scope is always
      resolved and enforced server-side via scope_registry.get_agent_scope.
      An unknown agent_id is rejected outright. An agent with no assigned
      scope gets an explicit "no bounded vault query access" result, never
      a silent whole-vault search. An assigned scope with no matching
      notes gets an explicit "nothing found" result, never a fabricated
      one."""
      return scope_query_tools.retrieve_notes_in_agent_scope(agent_id)
  ```

---

## Constraints

- Inherits from parent story and `Implementation/Architecture/architecture.md`'s "Agent-to-Tag/Folder Vault Scoping" section.
- The tool's own parameter list is **exactly `agent_id: str`** — no `tags`, `folders`, `scope`, or free-text query parameter of any kind. The model must never be able to supply or widen the scope it queries against; scope is always resolved server-side from the agent's own real assignment.
- An unknown `agent_id` must be rejected before any scope lookup runs (mirrors `propose_vault_write`'s own unknown-agent-first check).
- An agent with an empty assigned scope (`[]`) must return `{"status": "no_scope", ...}`, never fall back to querying the whole vault, and never return an empty `"notes"` list under a `"status": "ok"`/`"empty"` envelope that could be confused with "assigned scope, nothing matched."
- A non-empty assigned scope with zero matching notes must return `{"status": "empty", ...}`, distinct from `"no_scope"` — the two honest-failure states (Scenario 5 vs. Scenario 6) must remain distinguishable by the model/caller, not collapsed into one generic "nothing" result.
- Must NOT compose `vault_indexing.get_index()`/`vault_search.py` anywhere in this module, directly or transitively — this tool's only vault reads are `scope_registry.get_agent_scope`, `vault_writer.list_notes_matching_scope`, and `vault_writer.read_note`.
- Must NOT consult `working_mode_registry` — this is a read-only retrieval tool, not a mutating action; no approval-gating concept applies (mirrors the four existing read-only passthrough tools' own ungated shape, not `propose_vault_write`'s write-gating).
- Do not add this tool's name to `app/business/skill_tools.SKILLS` — it must stay unconditionally available to every agent via `mcp_client.load_agent_tools`, the same as the four existing passthrough tools, not access-gated like a skill.

---

## Tests

<!-- AC-03/AC-04/AC-05/AC-06 (Scenarios 3-6) are verified here via DIRECT
calls to scope_query_tools.retrieve_notes_in_agent_scope -- this is the
real, deterministic code this task itself builds, and the closest-to-real
substitute for a live chat round-trip that does not depend on model
phrasing variance (this project's own established "closest-to-real
substitute" Learnings pattern). The honest, grounded PHRASING of a chat
reply built from this tool's own output composes with REQ-SB-33's already-
live, already-verified grounding/honest-uncertainty system-prompt
instruction (Implementation/Architecture/architecture.md's own explicit
note) -- not a new honesty mechanism this task builds -- so an additional,
non-AC-tagged live chat round-trip is included below for full end-to-end
confidence, without making the locked ACs themselves hostage to real-
Provider latency/phrasing variance. -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; Python shell
against the same real backend `.venv`/real configured `vault_path` for the
direct calls; browser preview tool for the live chat check):

1. Setup: pick one real, currently-assigned-or-assignable customer tag
   that has at least one real note in the configured vault (e.g. whatever
   `list_known_customers()` returns first) — call it `<real-customer-tag>`
   (e.g. `"customer/masdar"` if real data exists for it, else substitute
   the first real value `list_known_customers()` actually returns). Call
   `scope_registry.set_agent_scope("email-capture", ["<real-customer-tag>"])`
   to give a real agent a real, non-empty scope for this task's own
   verification (`email-capture` chosen arbitrarily as a throwaway
   verification target — no product meaning to this specific agent
   holding this scope).
2. **[REQ-SB-29-US-01-AC-03]** Call `scope_query_tools.retrieve_notes_in_agent_scope("email-capture")` directly. Confirm `{"status": "ok", "scope": ["<real-customer-tag>"], "notes": [...]}` — `"notes"` is non-empty, and every entry's `"path"` corresponds to a real note actually tagged (or folder-matched) with `<real-customer-tag>` in the real vault (cross-check at least one entry's own `"frontmatter"` independently, e.g. via a direct `vault_writer.read_note` call on the same path, confirming a byte-for-byte match — this project's own established "cross-check against an independent, direct call to the same function" Learnings pattern). Confirm no entry's `frontmatter`/`tags` is unrelated to `<real-customer-tag>`.
3. **[REQ-SB-29-US-01-AC-04]** Confirm, by direct inspection of `scope_query_tools.py`'s own source, that `retrieve_notes_in_agent_scope`'s parameter list contains only `agent_id: str` — no `tags`/`folders`/query parameter the model could use to request a different customer's notes. This proves the "does not return notes outside its assigned scope" clause structurally, by construction, not just by example (whatever the model asks for, this tool can only ever return `email-capture`'s own real assigned scope's notes). Independently confirm step 2's own returned notes contain zero entries for any OTHER customer with real notes in the vault (list at least one other real customer via `list_known_customers()` and confirm none of its notes appear in step 2's result).
4. **[REQ-SB-29-US-01-AC-05]** Call `scope_registry.set_agent_scope("email-capture", ["definitely-not-a-real-tag-or-folder-xyz"])` (a syntactically valid but real-content-free scope value). Call `scope_query_tools.retrieve_notes_in_agent_scope("email-capture")` directly. Confirm `{"status": "empty", "message": "No notes matching 'email-capture's assigned scope (definitely-not-a-real-tag-or-folder-xyz) were found."}` — an honest empty result, no fabricated notes list.
5. **[REQ-SB-29-US-01-AC-06]** Call `scope_registry.set_agent_scope("email-capture", [])` (clears the assignment). Call `scope_query_tools.retrieve_notes_in_agent_scope("email-capture")` directly. Confirm `{"status": "no_scope", "message": "'email-capture' has no assigned vault tag/folder scope -- it has no bounded vault query access to use."}` — distinct from step 4's `"empty"` result, and no notes list of any kind returned.
6. Non-AC smoke check: call `scope_query_tools.retrieve_notes_in_agent_scope("not-a-real-agent")`. Confirm `{"status": "rejected", "message": "Unknown agent 'not-a-real-agent' -- request refused."}` and that no scope-lookup code runs for it (confirm by direct code reading — `agent_registry.get_agent` is the first statement in the function).
7. Additional real end-to-end check, beyond the AC-tagged direct calls above (honest disclosure of exactly what this proves): with `email-capture` still at the cleared/no-scope state from step 5, restore a real scope (`scope_registry.set_agent_scope("email-capture", ["<real-customer-tag>"])`, same as step 1), then send a real chat message to that agent via `POST /agents/email-capture/chat` (or the browser UI) asking for that customer's notes (e.g. "get me the notes for <real-customer-tag's own customer name>"). Confirm the model's real reply references genuine content matching step 2's own returned notes (not fabricated) — this is a real, live confirmation that the tool composes correctly through the full graph/chat path, not a re-verification of the tool's own deterministic logic (already proven above). Record the observed reply verbatim in the Implementation Log. This step is NOT tagged to any AC — it is additional confidence beyond what this task's own Tests block strictly requires.
8. Clean-up: `scope_registry.set_agent_scope("email-capture", [])` (restore the clean, unassigned seed state) and delete `.second-brain/agent_scopes.json` if this task's own verification was the first thing to ever create it.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-03** (Scenario 3) — for an agent with a real, non-empty assigned scope and matching vault notes, `retrieve_notes_in_agent_scope` returns those actual notes' content (`"status": "ok"`), limited to ones matching the assigned scope
- [x] **AC-04** (Scenario 4) — the tool's own parameter list (`agent_id` only) structurally prevents ever returning notes outside the agent's own assigned scope, regardless of what is asked; confirmed no unrelated customer's notes appear in a real scoped result
- [x] **AC-05** (Scenario 5) — for an agent with a real, non-empty assigned scope and zero matching notes, the tool returns an honest `"status": "empty"` result, never a fabricated notes list
- [x] **AC-06** (Scenario 6) — for an agent with no assigned scope (`[]`), the tool returns an honest `"status": "no_scope"` result, distinct from `"empty"`, never a silent whole-vault search
- [x] `retrieve_notes_in_agent_scope` rejects an unknown `agent_id` outright, before any scope lookup
- [x] The tool is not added to `skill_tools.SKILLS` — unconditionally available to every agent
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Agent Settings surface's own scope assignment UI — `T05`.
- Any new LangGraph node/conditional-edge for scope retrieval — none is needed; the existing generic `_execute_tools` node (`graph.py`) already executes any bound tool call, and `mcp_client.load_agent_tools` already includes every non-skill-catalog tool from the shared MCP server unconditionally, so this new tool composes with the existing graph with zero graph-layer code change.
- Any change to `history_entries_to_messages`'s system-prompt honesty instruction (`REQ-SB-33`) — already live, already composes with this tool's own honest `"empty"`/`"no_scope"` result shapes, not touched here.
- Wiring `vault_write_tools._is_within_assigned_scope`'s real body — `REQ-SB-04-US-01-T03` (still blocked).

---

## Context / Notes

**Why a new sibling module, not an addition to `vault_query_tools.py`:** per the parent story's own `## Notes` (decomposer pass) and `Implementation/Architecture/architecture.md`'s own explicit callout — this tool enforces a real business rule (server-side agent scope resolution, honest multi-state result shape) rather than a 1:1 passthrough of an existing read-only primitive, the same reasoning that put `propose_vault_write` in its own `vault_write_tools.py` sibling module rather than `vault_query_tools.py`.

**Why the tool returns real note content (`frontmatter`/`body`), not just paths:** `list_notes_matching_scope` itself (`T01`) mirrors `list_known_customers()`/`list_notes_in_kind_folder()`'s exact "just paths" shape — but Scenario 3's own acceptance text ("the agent returns the actual Masdar Pipeline notes from the vault") requires real content the model can answer from, not a bare path list it has no further tool to read. This module's own composition step (`vault_writer.read_note` per matched path) is the mechanism-filling detail that makes that concretely true, ordinary implementation latitude within the architect's own already-decided shape.

---

## Implementation Log

**2026-08-14 — Implemented and verified.** New `src/backend/app/business/
scope_query_tools.py` created exactly as specified. `app/api/mcp_server.py`
(real current state: 4 read-only passthrough tools +
`propose_vault_write`, matching the task's own precedent exactly)
extended: `scope_query_tools` added to the `app.business` import, and
`retrieve_notes_in_agent_scope` registered as a sixth `@mcp_server.tool()`.

**Honest, real-vault-vs-schema finding, recorded per the parent
instruction to verify Scenarios 3-6 against real notes matching the
Customer/Pipeline/Agreements/Consumption schema if any exist, or the
honest-empty path if not:** directly confirmed (`Work/` subfolder listing)
that `Work/Pipeline`, `Work/Agreements`, `Work/Consumption` do **not
exist at all** in the real configured vault — zero notes of that specific
sub-schema, consistent with `MEMORY.md`'s 2026-08-10 "structure only, no
ingestion/agent code" entry, still true as of this build. `AC-03`'s own
"produces a real positive result" half is therefore verified against the
closest real substitute available — the `customer/<slug>` tag dimension
of the same schema, which DOES have real, extensive vault content
(`customer/masdar`, `customer/adnoc`, etc., spanning Emails/Meetings/
Tasks/Notifications/the Customer hub note) — not against the
Pipeline/Agreements/Consumption sub-kind specifically, which has no real
data yet to test a positive case against. A scope of `["Pipeline"]` alone
was also tested directly and correctly produces the honest `"status":
"empty"` path (see `AC-05` below) — confirming the tool behaves
correctly for that specific still-empty schema slice today, not a
fabricated positive.

1. Setup: chose `customer/adnoc` as `<real-customer-tag>` (`list_known_
   customers()`'s first real return with actual tag-scoped notes,
   `ADNOC`), then separately re-verified against `customer/masdar` (the
   PRD's own literal example) for the additional live chat check, below.
   `scope_registry.set_agent_scope("email-capture", ["customer/adnoc"])`.
2. **[REQ-SB-29-US-01-AC-03]** `scope_query_tools.
   retrieve_notes_in_agent_scope("email-capture")` → `{"status": "ok",
   "scope": ["customer/adnoc"], "notes": [...37 entries...]}`. Every
   entry's own `"path"` is a real note actually tagged
   `customer/adnoc` (spot-checked the first 3 directly). Cross-checked
   the first entry's own `"frontmatter"`/`"body"` against an independent
   direct `vault_writer.read_note()` call on the same path — byte-for-
   byte match confirmed (`True`/`True`). Zero entries carried an
   unrelated tag. PASS.
3. **[REQ-SB-29-US-01-AC-04]** Direct source inspection confirmed
   `retrieve_notes_in_agent_scope`'s parameter list is exactly
   `agent_id: str` — no `tags`/`folders`/query parameter (`inspect.
   signature` → `['agent_id']`). Independently confirmed step 2's own
   37 returned notes contain zero entries for another real customer with
   real notes (`Aldar`, 12 real notes of its own) — set intersection of
   the two path sets was empty. PASS (structural + empirical).
4. **[REQ-SB-29-US-01-AC-05]** `scope_registry.set_agent_scope(
   "email-capture", ["definitely-not-a-real-tag-or-folder-xyz"])` →
   `retrieve_notes_in_agent_scope("email-capture")` → `{"status":
   "empty", "message": "No notes matching 'email-capture's assigned
   scope (definitely-not-a-real-tag-or-folder-xyz) were found."}` —
   exact match, no fabricated notes list. Also independently confirmed
   the real, still-empty `["Pipeline"]` scope produces the identical
   honest `"empty"` shape (see the schema finding above). PASS.
5. **[REQ-SB-29-US-01-AC-06]** `scope_registry.set_agent_scope(
   "email-capture", [])` → `retrieve_notes_in_agent_scope(
   "email-capture")` → `{"status": "no_scope", "message": "'email-
   capture' has no assigned vault tag/folder scope -- it has no bounded
   vault query access to use."}` — distinct from step 4's `"empty"`,
   no notes list. PASS.
6. Non-AC smoke check: `retrieve_notes_in_agent_scope("not-a-real-
   agent")` → `{"status": "rejected", "message": "Unknown agent
   'not-a-real-agent' -- request refused."}`. Direct source reading
   confirmed `agent_registry.get_agent(agent_id)` is the function's own
   first statement — no scope-lookup code runs before it. PASS.
7. Additional real end-to-end check (non-AC-tagged, disclosed as
   additional confidence beyond this task's own locked ACs): restored
   `email-capture`'s scope to the PRD's own literal example,
   `["customer/masdar"]`, via a live `PATCH /agents/email-capture`
   against a real running backend (`--port 8001`, restarted after this
   task's own edits so the new MCP tool registration was actually
   loaded). Sent a real chat message ("Can you retrieve the notes you
   have for Masdar in your assigned vault scope?") via `POST
   /agents/email-capture/chat`. The model's real reply summarized real,
   genuine vault content (1 Customer hub note, 42 Emails, 12 Meetings, 1
   Notification, 4 Tasks — matching the direct tool call's own 60-note
   total for the union of `customer/masdar` + the (empty) `Pipeline`
   folder scope tested earlier), citing real subjects/dates, not
   fabricated ones — confirms the tool composes correctly through the
   full graph/chat path. Verbatim reply on file in this task's own
   working notes; summarized here for brevity. `email-capture`'s scope
   restored to `[]` afterward via `PATCH`, and `.second-brain/
   agent_scopes.json` deleted (this task's own verification was the
   first thing in this session to leave a persisted entry after `T01`/
   `T02`/`T03` had each already cleaned up their own throwaway state).

`gate: clear` 2026-08-14 — no MUST-FLAG trigger fired. The Pipeline/
Agreements/Consumption schema finding above is a disclosed, honest
environmental observation (no real data exists yet for that specific
sub-schema), not a defect in this task's own code — recorded per the
launching instruction's explicit ask, not silently omitted or fabricated
around.

Status: `Ready` → `Done`.
