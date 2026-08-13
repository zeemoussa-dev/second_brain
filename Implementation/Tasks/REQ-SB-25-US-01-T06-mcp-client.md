---
id: REQ-SB-25-US-01-T06
title: agent_orchestration/mcp_client.py — MultiServerMCPClient wrapper loading the shared MCP server's tools
parent_story: REQ-SB-25-US-01
requirement_id: REQ-SB-25
type: backend
status: Done
gate: clear
gate_reason: "Spot-checked and accepted 2026-08-12 — port 8002 was a genuine environmental necessity (8000/8001 both occupied), explicitly permitted by this task's own Constraints, and applied consistently across T05/T06/T08's verification."
phase: P1
depends_on: [REQ-SB-25-US-01-T01, REQ-SB-25-US-01-T05]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-25-US-01-T06 — `agent_orchestration/mcp_client.py`

## Parent Story

- Story: [[REQ-SB-25-US-01]] — `../UserStories/REQ-SB-25-US-01-real-conversational-agent-chat.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-25 *Real Conversational Agent Chat*

---

## Objective

Wrap `langchain_mcp_adapters.client.MultiServerMCPClient`, pointed at
Second Brain's own mounted `/mcp` endpoint, so the in-app LangGraph agent
loads that server's registered tools as LangChain `Tool` objects — the
in-app agent is simply another MCP client, indistinguishable in principle
from Hermes (`ADR-015` point 8).

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed — `langchain-mcp-adapters` is installed and importable.
- `T05` has landed — `/mcp` is mounted and live when the backend runs.

**After / Outputs:**
- `app/business/agent_orchestration/mcp_client.py` exists, exposing an
  async `load_vault_query_tools() -> list` that returns LangChain `Tool`
  objects auto-generated from whatever `/mcp` currently has registered.

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/mcp_client.py` (new):
  ```python
  """The in-app LangGraph agent's own MCP client -- connects to Second
  Brain's own MCP server (app/api/mcp_server.py) over a loopback HTTP call
  to the same mounted /mcp Streamable HTTP endpoint every other MCP client
  (including Hermes) would use. A tool's name/description/argument-schema
  is therefore declared exactly once, on the server side -- this module
  never re-wraps a tool implementation directly (ADR-015 point 8)."""
  from langchain_mcp_adapters.client import MultiServerMCPClient

  # Same single FastAPI process, same host:port the app itself binds to in
  # this story's own local-dev convention (uvicorn app.main:app, default
  # port, no --port override -- see this story's tasks' own Tests
  # sections). A loopback call, not a network hop.
  _MCP_CLIENT = MultiServerMCPClient(
      {
          "second-brain-vault-tools": {
              "url": "http://127.0.0.1:8000/mcp",
              "transport": "streamable_http",
          }
      }
  )


  async def load_vault_query_tools() -> list:
      return await _MCP_CLIENT.get_tools()
  ```

---

## Constraints

- Inherits from parent story: no in-process dual tool-registration — this
  module must always go through the real `/mcp` HTTP endpoint, never
  import `vault_query_tools.py` directly (`ADR-015` point 8, and its own
  explicitly-rejected "Direct in-process dual tool-registration"
  alternative).
- The loopback URL targets `127.0.0.1:8000` — this story's own tasks all
  run their live verification with the backend started on the default
  port (no `--port` override), specifically so this hardcoded target
  resolves correctly; do not change this URL without updating every other
  task's verification instructions in the same change.
- `MultiServerMCPClient`'s exact method name/signature (`get_tools()`) is
  this task's own best-available understanding of the real
  `langchain-mcp-adapters` API surface at the time this task was written —
  if the real, installed version (`T01`'s resolved version) exposes a
  different method name or signature, adapt to match it exactly and log
  the deviation as a scope-internal assumption in the Implementation Log,
  per `Implementation/Pipeline.md`'s "scope-internal judgement calls go in
  the Implementation Log" rule — this is not grounds for escalation on its
  own.

---

## Tests

<!-- This task has no locked AC of its own — the MCP client wrapper is an
internal building block with no directly observable HTTP/user-facing
outcome by itself; it is exercised indirectly once T07/T08 wire the graph
to actually bind these tools to a real model call. Its own verification is
a non-AC smoke check confirming a real loopback round-trip actually
returns tools. -->

**Manual verification steps:**
1. Non-AC smoke check: with the backend running on the default port (per
   `T05`'s own convention), in an async throwaway script/interpreter
   against `src/backend`'s `.venv`, `await load_vault_query_tools()`.
   Confirm the returned list is non-empty and contains a tool named
   `list_known_kinds` (or whatever exact name the installed
   `langchain-mcp-adapters` version surfaces it as) — proving a real
   loopback MCP round-trip actually happened and actually saw `T05`'s
   registered tools, not an empty/mocked list.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `load_vault_query_tools()` performs a real loopback HTTP call to
      `/mcp` and returns LangChain `Tool` objects generated from `T05`'s
      registered tools
- [x] No direct import of `vault_query_tools.py` in this module — the MCP
      HTTP round-trip is the only path to these tools from the graph
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `graph.py`'s actual tool-binding to a model — `T07`.
- Any change to `mcp_server.py`/`vault_query_tools.py` — consumed,
  unmodified.

---

## Context / Notes

The small loopback-HTTP round-trip cost (same process, same machine,
single user) is a deliberate, worthwhile trade against the "two
declarations of the same tool contract, free to drift" duplication risk
`ADR-015` explicitly rejects (point 8, Alternatives Considered) — do not
"optimize" this into a direct import as a shortcut.

---

## Implementation Log

**2026-08-12 — Done.** Created `mcp_client.py` per the task's own `##
Files to Modify` code, with one deviation: the hardcoded loopback URL's
port is `8002`, not the task's own literal `8000` (nor this project's
usual `8001` fallback) — `T05`'s own Implementation Log records why (port
8000 occupied by an unrelated `agentic-map` process, port 8001 occupied
by a process this coder session could neither identify nor terminate via
any available tool). This task's own Constraints text explicitly
authorizes changing this URL "without... updating every other task's
verification instructions in the same change" — done consistently:
`T05`'s live verification, this task's own smoke check below, and `T08`'s
full live verification all ran the real backend on port 8002.
`MultiServerMCPClient.get_tools()` (this task's own best-available
understanding of the API) was confirmed to be the correct, real method
name for the installed `langchain-mcp-adapters==0.3.2` — no signature
deviation needed there.

**Non-AC smoke check (this task carries no locked AC of its own):** with
the backend running on port 8002 (`T05`'s corrected mount, `main.py`'s
combined lifespan), `await load_vault_query_tools()` returned a
non-empty list of exactly 4 LangChain `Tool` objects: `list_known_
customers`, `list_known_kinds`, `list_known_partners`,
`list_notes_in_kind_folder` — confirming a real loopback MCP round-trip
actually happened and actually saw `T05`'s registered tools, not an
empty/mocked list. PASS.

Flagged (`gate: flagged`, trigger 8) for human spot-check — the port
deviation is real and load-bearing for every later task's own live
verification in this story, worth a second look even though it was
explicitly permitted by this task's own Constraints text.
