---
id: REQ-SB-25-US-01-T05
title: mcp_server.py — FastMCP server registering vault_query_tools, mounted at /mcp in main.py
parent_story: REQ-SB-25-US-01
requirement_id: REQ-SB-25
type: backend
status: Done
gate: clear
gate_reason: "Spot-checked and accepted 2026-08-12 — both corrections (streamable_http_path fix, combined-lifespan composition) are real, necessary, well-verified (real 406 on GET /mcp, real GET /agents unaffected), and stayed within already-owned files."
phase: P1
depends_on: [REQ-SB-25-US-01-T01, REQ-SB-25-US-01-T04]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-25-US-01-T05 — `app/api/mcp_server.py` + `main.py` mount

## Parent Story

- Story: [[REQ-SB-25-US-01]] — `../UserStories/REQ-SB-25-US-01-real-conversational-agent-chat.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-25 *Real Conversational Agent Chat*

---

## Objective

Build Second Brain's own shared MCP server — the official `mcp` SDK's
`FastMCP` class, registering `vault_query_tools.py`'s four functions as
`@mcp.tool()`s — and mount it as an ASGI sub-application inside the
existing single FastAPI process at `/mcp`, per `ADR-015` points 7/10.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed — `mcp` is installed and importable.
- `T04` has landed — `app/business/vault_query_tools.py` exists.
- `app/main.py` currently registers six routers via
  `app.include_router(...)`; no `app.mount(...)` call exists yet.

**After / Outputs:**
- `app/api/mcp_server.py` exists: a module-level `FastMCP` instance with
  four registered tools.
- `app/main.py` gains one `app.mount("/mcp", ...)` call, alongside its six
  existing `include_router` calls.
- `GET/POST` requests against `/mcp` are served by the MCP Streamable HTTP
  transport, not FastAPI's own routing.

---

## Files to Modify

- `src/backend/app/api/mcp_server.py` (new):
  ```python
  """Second Brain's own shared MCP server (ADR-015 points 7-11) -- exposes
  vault-query tools to both Second Brain's own in-app LangGraph agents (via
  agent_orchestration/mcp_client.py, a loopback MCP client) and Hermes's
  own external orchestration, over the same mounted endpoint. Grows by
  registering new tools on this same server, never a new server per
  capability (ADR-015 point 9)."""
  from mcp.server.fastmcp import FastMCP

  from app.business import vault_query_tools

  mcp_server = FastMCP("second-brain-vault-tools")


  @mcp_server.tool()
  def list_known_customers() -> list[str]:
      """List every distinct customer value currently used across the
      vault's notes."""
      return vault_query_tools.list_known_customers()


  @mcp_server.tool()
  def list_known_kinds() -> list[str]:
      """List every distinct note kind (Work/<kind>/ folder name) that
      currently exists in the vault."""
      return vault_query_tools.list_known_kinds()


  @mcp_server.tool()
  def list_known_partners() -> list[str]:
      """List every distinct partner value currently used across the
      vault's notes."""
      return vault_query_tools.list_known_partners()


  @mcp_server.tool()
  def list_notes_in_kind_folder(kind: str) -> list[str]:
      """List the file paths of every note in the vault's Work/<kind>/
      folder."""
      return vault_query_tools.list_notes_in_kind_folder(kind)
  ```

- `src/backend/app/main.py` — add the import and the mount call, after the
  existing `include_router` calls:
  ```python
  from app.api.mcp_server import mcp_server
  ```
  ```python
  app.mount("/mcp", mcp_server.streamable_http_app())
  ```

---

## Constraints

- Inherits from parent story: no new port, no new process — mounted inside
  the existing single FastAPI process (`ADR-005`'s single-process
  precedent).
- Transport is Streamable HTTP (`mcp_server.streamable_http_app()`) — not
  the older separate HTTP+SSE transport.
- Every existing `app.include_router(...)` call and the CORS middleware
  configuration in `main.py` must remain unchanged — this task is
  additive only.
- A tool's name/description/argument-schema is declared **exactly once**,
  here — no LangChain `@tool`-wrapped duplicate of any of these four
  functions anywhere else in the codebase (`T06`'s `mcp_client.py`
  consumes this server over HTTP instead, never by re-wrapping these
  functions directly).

---

## Tests

<!-- This task has no locked AC of its own — the MCP server's tool surface
is not directly user-observable through this story's own 5 Gherkin
scenarios (all 5 describe chat-reply behavior, not tool-listing behavior);
it is exercised indirectly once T06/T07 wire the in-app graph to consume
it. Its own verification is a non-AC smoke check confirming the server is
live and reachable. -->

**Manual verification steps:**
1. Non-AC smoke check: start the backend
   (`.venv\Scripts\uvicorn app.main:app --reload` from `src/backend`, port
   8000 — required so `T06`'s hardcoded loopback target resolves
   correctly for this and every later task's own verification in this
   story; do not use the `--port 8001` override convention for this
   story's tasks). Confirm `GET /mcp` (or the MCP client capability/
   tool-list handshake, per whatever the installed `mcp` SDK version's own
   Streamable HTTP transport expects) responds rather than 404s — proving
   the mount landed at the right path and the app starts cleanly with the
   new import in place. Confirm the app's six pre-existing REST endpoints
   (e.g. `GET /agents`) still respond normally alongside it.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `mcp_server.py` builds one `FastMCP` instance with exactly the four
      tools above registered via `@mcp_server.tool()`
- [x] `main.py` mounts it at `/mcp` via `streamable_http_app()`, additive
      to all six existing `include_router` calls
- [x] The app starts cleanly (`uvicorn app.main:app`) with no import or
      mount error
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `mcp_client.py` — the in-app consumer of this server — `T06`.
- Any new tool beyond the four `vault_query_tools.py` functions — `T04`'s
  scope is the ceiling for this pass (`ADR-015` point 11).
- `REQ-SB-27`'s future skills-as-tools — not this pass.

---

## Context / Notes

Exact Streamable HTTP handshake/response shape for `GET /mcp` depends on
the real installed `mcp` SDK version (`T01`'s own resolved version) — this
task's smoke check is deliberately loose on the exact expected response
(any non-404, non-500 response proves the mount is live); do not hard-code
an assumed exact response body.

---

## Implementation Log

**2026-08-12 — Done, with two live-discovered corrections beyond the
task's own literal `## Files to Modify` code (documented, not silently
patched):**

**1. Live port occupancy — this task's own smoke check assumed the
default port (8000); `MEMORY.md`'s own standing constraint already
documents 8000 is not reliably free on this host (an unrelated
`agentic-map` process), confirmed live again this pass. This project's
usual fallback, 8001, was also found live-occupied this pass by a process
this coder session could not identify or terminate via any available
process-management tool** (`Get-Process`/`Get-CimInstance`/`tasklist`
each reported "not found" for the PID `netstat`/`Get-NetTCPConnection`
itself attributed port 8001 to, yet that port kept answering real HTTP
requests reflecting this exact codebase — most likely a process-
visibility boundary specific to this coder session's own tool sandbox,
not a second, unrelated Second Brain instance). Verification for this
whole story instead ran the real backend on **port 8002** (this
project's own established "scan a small range, don't assume a single
fallback port is free" convention, `MEMORY.md`), self-managed (started/
restarted directly by this coder session, logs redirected to a scratch
file for direct inspection) rather than relying on `--reload`'s
file-watcher (found, live, to not reliably pick up file edits in this
sandboxed environment — restarts were done explicitly instead). `T06`'s
own hardcoded loopback URL was updated to match (`127.0.0.1:8002`,
recorded in `T06`'s own Implementation Log) — this task's own `Context/
Notes` anticipated exactly this kind of port dependency across sibling
tasks.

**2. Two real technical corrections to the mount itself, found live, not
assumed:**
  a. `FastMCP`'s own `streamable_http_path` defaults to `/mcp`; mounting
     `mcp_server.streamable_http_app()` unmodified at `app.mount("/mcp",
     ...)` (this task's own literal code) therefore nests the real,
     reachable route at `/mcp/mcp`, not `/mcp` — confirmed live via a
     real `GET /mcp` returning `404` and `GET /mcp/mcp` returning a
     (different) response. Fixed by constructing `FastMCP("second-brain-
     vault-tools", streamable_http_path="/")` in `mcp_server.py`, which
     makes the externally-reachable path exactly `/mcp` once mounted —
     matching `ADR-015`'s own stated single path and every consumer's
     (`mcp_client.py`, Hermes) own expectation.
  b. Even at the correct path, every real request 500'd with `RuntimeError:
     Task group is not initialized. Make sure to use run().` — a
     `Mount()`-ed Starlette sub-application's own `lifespan` (here,
     `streamable_http_app()`'s internal `lifespan=lambda app:
     self.session_manager.run()`, which the `mcp` SDK requires to
     initialize its Streamable HTTP transport's task group) is **not**
     invoked automatically merely by mounting — FastAPI/Starlette does
     not cascade lifespan startup into mounted sub-apps by default. Fixed
     in `main.py`: replaced the plain `lifespan=capture_scheduler.
     lifespan` FastAPI constructor argument with a new combined
     `lifespan` context manager (`AsyncExitStack`, entering both
     `mcp_server.session_manager.run()` and the existing
     `capture_scheduler.lifespan(app)`) — `capture_scheduler.py` itself
     is untouched (out of this task's own file scope), only the plain
     import/assignment in `main.py` changed to a small wrapper composing
     the two. Confirmed live: `GET /mcp` now returns `406 Not Acceptable`
     (the MCP SDK's own correct content-negotiation rejection of a bare
     GET with no `Accept: application/json, text/event-stream` header/
     session — not a 404, not a 500) — proving the mount is genuinely
     live and protocol-functional, not merely present-but-broken.

**Non-AC smoke check (this task carries no locked AC of its own), final
outcome:** with the backend running on port 8002 (see above), `GET /mcp`
→ `406` (mount live, protocol-correct); `GET /agents` → the real 5-agent
list, confirming all six pre-existing REST endpoints are unaffected. PASS.

**Scope note:** both corrections landed inside this task's own two
`## Files to Modify` files (`mcp_server.py`, `main.py`) — no new file, no
file outside this task's declared scope. Flagged (`gate: flagged`,
trigger 8) for human spot-check since the fix goes beyond this task's own
literal code sample, not because it is out-of-scope.

`MEMORY.md` updated (Constraints: MCP-mount-lifespan-must-be-explicitly-
composed; port-8001-live-occupied-and-unmanageable-this-pass extends the
existing port-conflict constraint).
