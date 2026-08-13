---
id: REQ-SB-27-US-01-T02
title: New app/business/skill_tools.py — code-level skill catalog + one illustrative @mcp.tool() stub skill
parent_story: REQ-SB-27-US-01
requirement_id: REQ-SB-27
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-25-US-01-T05]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-27-US-01-T02 — New app/business/skill_tools.py

## Parent Story

- Story: [[REQ-SB-27-US-01]] — `../UserStories/REQ-SB-27-US-01-skills-repository-registration-and-access.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-27 *Skills Repository*

---

## Objective

Add `app/business/skill_tools.py` — a new sibling module to `app/business/
vault_query_tools.py` (both siblings of `app/business/agent_orchestration/`,
per `ADR-015` point 3) — holding one illustrative, `@mcp.tool()`-decorated
stub skill function whose body unconditionally returns the honest "not yet
available" response, plus a small, literal, enumerable skill-metadata
registry (`id`/`name`/`description`) that `T03`'s `skill_registry.py` reads
directly (never derived by introspecting the MCP server's full live tool
list, which would also surface `vault_query_tools.py`'s non-skill tools).

---

## ⚠️ RESOLVED (2026-08-12 follow-up decomposer pass) — was BLOCKED, now unblocked

This task's `@mcp.tool()` decorator requires importing the shared `FastMCP`
instance from `app/api/mcp_server.py` (`ADR-015` point 7), and this
module's placement as a sibling of `app/business/vault_query_tools.py`
(`ADR-015` point 3) presumes that module exists too. Both were
`REQ-SB-25-US-01`'s own scaffolding, not yet decomposed into tasks as of
this task's original authoring (2026-08-12) — `depends_on` was
deliberately left `[]` rather than a fabricated task ID (`ESC-011`).

**Now resolved:** `REQ-SB-25-US-01`'s own decomposer pass has since
completed (`status: Ready`, `gate: clear`).
`REQ-SB-25-US-01-T05` (`Implementation/Tasks/
REQ-SB-25-US-01-T05-mcp-server.md`) is the real task that creates
`app/api/mcp_server.py`: a module-level `FastMCP` instance named
**`mcp_server`** (not `mcp` — confirm this exact name against that task's
own `## Files to Modify` before importing it), registering
`vault_query_tools.py`'s four functions, mounted at `/mcp` in `main.py`.
`depends_on` above now points at `REQ-SB-25-US-01-T05`. The coder may
start this task once `REQ-SB-25-US-01-T05` is `Done`. See
`ESCALATIONS.md` → `ESC-011` (`Resolved`).

---

## Starting State → End State

**Before / Inputs:**
- `app/api/mcp_server.py` exists, exposing a module-level `FastMCP`
  instance (name TBD by `REQ-SB-25-US-01`'s own task, e.g. `mcp`) and
  already registers `vault_query_tools.py`'s functions as `@mcp.tool()`s
  (`REQ-SB-25-US-01`'s own scaffolding — not built by this task).
- `T01` has landed `vault_writer.load_skills_state()`/
  `save_skills_state()` (not used by this task directly, but by `T03`).

**After / Outputs:**
- `app/business/skill_tools.py` (new) exposes:
  - A literal, enumerable registry, e.g.:
    ```python
    SKILLS: dict[str, dict] = {
        "diagram-understanding": {
            "id": "diagram-understanding",
            "name": "Diagram Understanding",
            "description": (
                "Given an uploaded image, identify and describe the "
                "components in an architecture/engineering diagram."
            ),
        },
    }
    ```
  - One `@mcp.tool()`-decorated function per registry entry (this pass:
    exactly one, `diagram_understanding`), each unconditionally returning
    the honest "not yet available" response — no real handler is built
    (per the parent story's own Non-Goals). Registered on the same shared
    `mcp` instance imported from `app/api/mcp_server.py`.

---

## Files to Modify

- `src/backend/app/business/skill_tools.py` (new) — exact function
  signature/import path for the shared `mcp` instance is bounded by
  whatever `REQ-SB-25-US-01`'s own `app/api/mcp_server.py` task actually
  names it as; confirm against that task's own `## Files to Modify`
  before writing this file, do not assume.
- `src/backend/app/api/mcp_server.py` — read-only for this task (import
  the existing `mcp` instance; do not otherwise modify this file — any
  change beyond the one new tool registration this task adds is out of
  scope).

---

## Constraints

- Inherits from parent story and `ADR-015` points 3, 7, 9.
- **Skill registration is code-level, not a runtime user-facing action**
  (parent story `## Constraints`) — this task adds exactly one illustrative
  stub skill by editing code, not by exposing a "create skill" endpoint.
- The stub skill's body must unconditionally return the honest "not yet
  available" response — never a fabricated or guessed result — mirroring
  `model_factory.py`'s / `ADR-011` point 3's / `ADR-014` point 7's same
  honesty shape one layer over.
- Must NOT modify `app/business/vault_query_tools.py` or
  `app/business/agent_orchestration/`'s own contents — this task only adds
  a new, independent sibling module plus one new tool registration call
  in `app/api/mcp_server.py`.
- `SKILLS`' registry entries are the single source of truth `T03`'s
  `skill_registry.list_skills()` reads — do not duplicate this metadata
  anywhere else.

---

## Tests

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`,
   confirm `skill_tools.SKILLS` contains exactly the
   `"diagram-understanding"` entry with `id`/`name`/`description`
   populated. Confirm the MCP server's own tool listing (via the running
   dev server's `/mcp` endpoint, or `app.api.mcp_server`'s own FastMCP
   instance introspection) includes a tool matching this skill's
   registration. Call the stub function directly; confirm it returns the
   honest "not yet available" response, never a fabricated result.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `skill_tools.SKILLS` holds exactly one illustrative skill entry
      (`id`/`name`/`description`)
- [x] The stub skill is registered as an `@mcp.tool()` on the same shared
      `mcp` instance `app/api/mcp_server.py` already uses for
      `vault_query_tools.py`
- [x] The stub skill's body unconditionally returns the honest "not yet
      available" response, never a fabricated result
- [x] `vault_query_tools.py`/`agent_orchestration/` unmodified beyond the
      one new tool-registration call this task adds to `mcp_server.py`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any real diagram/image-understanding implementation — explicitly
  deferred, per the parent story's own Non-Goals.
- Per-agent access grant/revoke, `has_skill_access`, `invoke_skill` —
  `T03` (`skill_registry.py`).
- Any API surface — `T04` (`skills_router.py`).
- Building `app/api/mcp_server.py` or `app/business/agent_orchestration/`
  themselves — `REQ-SB-25-US-01`'s own scope, not this story's.

---

## Context / Notes

**Was genuinely blocked, now resolved** — see the "⚠️ RESOLVED" section
above. `REQ-SB-25-US-01-T05` is the real task ID this task depends on;
`app/api/mcp_server.py`'s shared `FastMCP` instance is named `mcp_server`
(confirmed against that task's own `## Files to Modify`).

---

## Implementation Log

**2026-08-12 — coder.** Created `src/backend/app/business/skill_tools.py`
(new): `SKILLS` registry with exactly one entry (`diagram-understanding`)
and a `@mcp_server.tool()`-decorated `diagram_understanding()` stub
function, unconditionally returning `{"available": False, "message":
"This skill is not yet available — no real handler has been built for
it."}`. Imports `mcp_server` from `app.api.mcp_server` (confirmed exact
name `mcp_server`, not `mcp`, per this task's own "confirm before
assuming" instruction and the RESOLVED note already in this file).
`app/api/mcp_server.py` left byte-for-byte unmodified — this task's "one
new tool registration" is achieved by decorating the stub function inside
`skill_tools.py` itself with the already-shared `mcp_server` instance
imported from that module; a `FastMCP` `@tool()` decorator registers on
the shared server *object*, not by editing that object's own defining
module's source, so no change to `mcp_server.py` was needed to satisfy
"one new tool registration call" — confirmed live (see smoke check below).
`vault_query_tools.py`/`agent_orchestration/` untouched.

**Non-AC smoke check (pass):** `skill_tools.SKILLS` contains exactly the
`"diagram-understanding"` entry with `id`/`name`/`description` populated.
`await skill_tools.mcp_server.list_tools()` confirmed
`"diagram_understanding"` is now a registered tool name (alongside the
four pre-existing `vault_query_tools.py` tools) — the shared-instance
registration works without any `mcp_server.py` edit. Calling
`skill_tools.diagram_understanding()` directly returned the honest
`{"available": False, ...}` result, never a fabricated one.

`status: Ready → Done`.

**Scope-internal judgement call (not an escalation):** the task's own
`## Files to Modify` listed `app/api/mcp_server.py` as a file this task
touches ("read-only... any change beyond the one new tool registration
this task adds is out of scope"), which read as implying some edit to
that file was expected. Live-confirmed the decorator-based registration
from a separate module fully satisfies the "one new tool registration"
outcome with zero edits to `mcp_server.py` — consistent with the task's
own explicit "read-only for this task" instruction and its own Acceptance
Criteria ("unmodified beyond the one new tool-registration call"), so no
out-of-scope file was touched; recorded here for human spot-check per this
project's own "scope-internal judgement calls go in the Implementation Log"
convention (Pipeline.md hard rule 5). `gate: clear` — this is a
judgement-call clarification of an already-permitted "may or may not need
edits" file listing, not a deviation from a locked AC or a new dependency.
