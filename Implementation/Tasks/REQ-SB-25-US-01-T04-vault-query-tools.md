---
id: REQ-SB-25-US-01-T04
title: vault_query_tools.py — thin business-layer wrappers over existing read-only vault_writer primitives
parent_story: REQ-SB-25-US-01
requirement_id: REQ-SB-25
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-25-US-01-T04 — `app/business/vault_query_tools.py`

## Parent Story

- Story: [[REQ-SB-25-US-01]] — `../UserStories/REQ-SB-25-US-01-real-conversational-agent-chat.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-25 *Real Conversational Agent Chat*

---

## Objective

Add the actual tool *implementations* the new shared MCP server (`T05`)
registers — thin business-layer functions over already-existing read-only
`vault_writer` primitives, per `ADR-015` point 3/11. No new `data_access`
reads, no business rules beyond simple JSON-serializable projection.

---

## Starting State → End State

**Before / Inputs:**
- `app/data_access/vault_writer.py` already has (all `Done`):
  `list_known_customers() -> list[str]`, `list_known_kinds() -> list[str]`,
  `list_known_partners() -> list[str]`,
  `list_notes_in_kind_folder(kind: str) -> list[Path]`.
- No `app/business/vault_query_tools.py` exists yet.

**After / Outputs:**
- `app/business/vault_query_tools.py` exists, exposing four functions with
  identical names, each a thin pass-through (or, for
  `list_notes_in_kind_folder`, a `Path`→`str` projection so the return
  value is JSON-serializable for MCP tool consumption).

---

## Files to Modify

- `src/backend/app/business/vault_query_tools.py` (new):
  ```python
  """Thin business-layer functions over already-existing read-only
  vault_writer primitives -- the tool *implementations* the shared MCP
  server (app/api/mcp_server.py) registers as @mcp.tool()s, consumed both
  by Second Brain's own in-app LangGraph agents (via mcp_client.py) and by
  Hermes's own external orchestration -- one implementation, reused both
  ways (ADR-015 points 3, 8). No new data_access reads; no business rules
  beyond simple projection (ADR-003)."""
  from app.data_access import vault_writer


  def list_known_customers() -> list[str]:
      return vault_writer.list_known_customers()


  def list_known_kinds() -> list[str]:
      return vault_writer.list_known_kinds()


  def list_known_partners() -> list[str]:
      return vault_writer.list_known_partners()


  def list_notes_in_kind_folder(kind: str) -> list[str]:
      """Projects vault_writer's Path objects to plain path strings -- MCP
      tool return values must be JSON-serializable; a Path is not."""
      return [str(path) for path in vault_writer.list_notes_in_kind_folder(kind)]
  ```

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (`ADR-003`) — no new `data_access` functions, no new vault reads beyond
  the four already-existing primitives.
- No dependency on `T01`'s new packages — this module imports only
  `app.data_access.vault_writer`, already present; it can be built and
  verified independently of the LangGraph/MCP install.
- Pure business-layer projection only — do not add filtering, sorting
  beyond what `vault_writer` already returns, or any new parameter beyond
  `list_notes_in_kind_folder`'s existing `kind: str`.

---

## Tests

<!-- This task has no locked AC of its own — these are internal tool
implementations with no directly observable HTTP/user-facing outcome by
themselves (they become observable once T05 registers them on the MCP
server, and once T07/T08's real conversational replies demonstrate the
agent actually used a tool, which none of this story's 5 locked ACs
individually requires — Scenario 1/3 only require "a real, relevant
conversational reply", not "a reply that used a specific tool"). Its own
verification is a non-AC smoke check. -->

**Manual verification steps:**
1. Non-AC smoke check: in a throwaway interpreter against `src/backend`'s
   `.venv` (real configured `vault_path`), call each of the four functions
   directly; confirm each returns the identical value its `vault_writer`
   counterpart returns (for `list_notes_in_kind_folder`, confirm every
   returned item is a plain `str`, not a `Path` instance).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `list_known_customers`/`list_known_kinds`/`list_known_partners` are
      pure pass-throughs to their `vault_writer` counterparts
- [x] `list_notes_in_kind_folder(kind)` returns `list[str]` (path strings),
      never `Path` objects
- [x] No new `data_access` function added; no existing `vault_writer`
      function modified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Registering these functions as `@mcp.tool()`s — `T05`.
- Any new read-only `vault_writer` primitive — none is needed this pass;
  the four existing ones are sufficient (`ADR-015` point 11).

---

## Context / Notes

`ADR-015` point 11 is explicit that these first tools are "illustrative,
not mandated" — they exist so the MCP server (`T05`) and the graph's
tool-binding (`T07`) have at least one real, exercised tool rather than a
purely theoretical registration surface.

---

## Implementation Log

**2026-08-12 — Done.** Created `vault_query_tools.py` verbatim per the
task's own `## Files to Modify` code.

**Non-AC smoke check (this task carries no locked AC of its own):** called
all four functions directly against the real, configured vault. Observed:
`list_known_customers()`/`list_known_kinds()`/`list_known_partners()` each
returned identical values to their `vault_writer` counterparts (20
customers, 9 kinds, 1 partner — `["Microsoft"]`); `list_notes_in_kind_
folder("Emails")` returned 179 entries, every one a plain `str` (confirmed
via `isinstance` check), not a `Path`. PASS.

No assumption, deviation, or escalation. `gate: clear` 2026-08-12.
