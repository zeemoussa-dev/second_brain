---
id: REQ-SB-25-US-01-T01
title: Add langgraph/langchain-openai/mcp/langchain-mcp-adapters to requirements.txt and verify a real pip install
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

# REQ-SB-25-US-01-T01 — Add LangGraph/MCP dependencies and verify a real pip install

## Parent Story

- Story: [[REQ-SB-25-US-01]] — `../UserStories/REQ-SB-25-US-01-real-conversational-agent-chat.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-25 *Real Conversational Agent Chat*

---

## Objective

Add the four new packages `ADR-015` names to `requirements.txt` and run a
**real** `pip install` against the backend's own `.venv` to confirm every
package (and its transitive compiled dependencies, chiefly `pydantic-core`)
actually installs on this Windows/`cp314` host — per `ADR-015`'s own
honestly-flagged, explicitly-unverified wheel-availability risk (Decision
point 2). This is a live verification step, not an assumption — every
other task in this story imports at least one of these packages and cannot
be built until this one is real and confirmed.

---

## Starting State → End State

**Before / Inputs:**
- `src/backend/requirements.txt` has 7 lines (`fastapi`, `uvicorn[standard]`,
  `pytest`, `httpx`, `pydantic-settings`, `pywin32`, `apscheduler`) — no
  LangGraph/MCP packages yet.
- `src/backend/.venv` already exists and already runs the current
  dependency set successfully (`ADR-001`).

**After / Outputs:**
- `requirements.txt` gains four new lines.
- `src/backend/.venv` has all four packages (and their transitive
  dependencies) installed and importable.
- The Implementation Log records the exact resolved versions of all four
  packages, and explicitly confirms (or, if it genuinely fails, reports)
  whether every transitive compiled dependency has a working `cp314` wheel.

---

## Files to Modify

- `src/backend/requirements.txt` — append, in this order, directly below
  the existing `apscheduler>=3.10` line:
  ```
  langgraph>=1,<2
  langchain-openai
  mcp
  langchain-mcp-adapters
  ```
  Only `langgraph` gets an explicit version pin — `ADR-015` Decision point 2
  states that pin verbatim (`langgraph>=1,<2`). `ADR-015` does not name an
  explicit major for the other three packages (only their names), so do
  **not** invent an upper-bound pin for them — install them unpinned first,
  per this project's own established "pin what the ADR states; let the real
  install resolve and confirm the rest" pattern (`MEMORY.md` Patterns,
  `react-router`/`ADR-010` precedent). Record whatever versions the real
  install resolves in the Implementation Log; if a later task's own
  `/plan-tasks`-equivalent judgement determines a pin is warranted, that's
  a separate, future decision — not this task's job to pre-empt.

---

## Constraints

- Inherits from parent story: no new external system, no change to any
  existing dependency's version.
- Run the install from `src/backend`, against the real `.venv`
  (`.venv\Scripts\pip.exe install -r requirements.txt`, or
  `.venv\Scripts\pip.exe install langgraph>=1,<2 langchain-openai mcp
  langchain-mcp-adapters` for just the four new lines) — never against any
  system-wide Python.
- **Do not silently work around a missing wheel.** If `pip install` fails
  because a required package has no prebuilt `cp314` wheel and no C/Rust
  build toolchain is available on this host (`ADR-001`/`ADR-002`'s
  no-admin-rights constraint), **stop and report the failure** — per
  `ADR-015` Decision point 2's own instruction, this is "grounds for a
  follow-up decision... not a silent workaround." Do not pin an older
  Python-incompatible version or attempt an unofficial wheel source without
  first escalating.

---

## Tests

<!-- This task has no locked AC of its own — it is pure dependency
infrastructure with no directly observable behavioural outcome; every
locked AC in this story is verified end-to-end once the full chain of
tasks (through T08) lands. Its own verification is a non-AC smoke check. -->

**Manual verification steps:**
1. Non-AC smoke check: from `src/backend`, run the real `pip install`
   against `.venv`. Confirm the command exits with no error. Then, in a
   throwaway interpreter against the same `.venv`
   (`.venv\Scripts\python.exe -c "import langgraph, langchain_openai, mcp,
   langchain_mcp_adapters; print('ok')"`), confirm the import succeeds and
   prints `ok` — proving every package, and every transitive compiled
   dependency it pulls in, is actually importable on this host, not merely
   downloaded.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `requirements.txt` gains exactly the four lines specified above, in
      that order, with only `langgraph` version-pinned
- [x] A real `pip install` against `src/backend/.venv` completes without
      error
- [x] `import langgraph, langchain_openai, mcp, langchain_mcp_adapters`
      succeeds against that same `.venv`
- [x] Exact resolved versions of all four packages recorded in the
      Implementation Log
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Writing any code that imports these packages — every other task in this
  story (`T02`–`T08`).
- Pinning an explicit upper-bound version for `langchain-openai`, `mcp`, or
  `langchain-mcp-adapters` — not directed by `ADR-015`; left as an open,
  future decision if it ever becomes necessary.

---

## Context / Notes

**Why this task exists standalone, ahead of every other task:** `ADR-015`
itself states "no live network/package-index access was available to this
architecture pass" and explicitly defers real verification of the
wheel-availability risk to "the coder task's own real `pip install`... not
assumed here." Every other task in this story (`T02`–`T08`) imports at
least one of these four packages — none of them can be meaningfully built
or verified until this task is `Done`.

If this task's real install genuinely fails on a missing `cp314` wheel,
that is a **blocking** discovery for the whole story, not a scope-internal
judgement call — escalate per `Implementation/Pipeline.md`'s MUST-FLAG
trigger 6/7 rather than improvise a workaround (e.g. downgrading Python,
using an unofficial wheel index).

---

## Implementation Log

**2026-08-12 — Done.** `requirements.txt` gained the four lines exactly as
specified (only `langgraph>=1,<2` pinned). Ran a real
`.venv\Scripts\pip.exe install -r requirements.txt` from `src/backend`
against the real `.venv` — completed successfully, no error (one benign,
non-fatal `WARNING: Failed to remove contents in a temporary directory
'...~ebsockets'` during the `websockets` 17.0.1→15.0.1 downgrade cleanup;
the install itself still reported `Successfully installed ...` for all 42
new/changed packages, and the later `import` check below confirms
`websockets` is fully functional despite the cleanup warning).

Every transitive compiled dependency (`pydantic-core` already proven per
`ADR-015`, plus newly-pulled `cryptography` (`cryptography-50.0.0`,
`cp311-abi3` wheel — forward-compatible with `cp314`), `cffi`, `rpds-py`,
`orjson`, `ormsgpack`, `tiktoken`, `regex`, `xxhash`, `zstandard`,
`uuid-utils`) resolved to a prebuilt Windows wheel — **no missing `cp314`
wheel, no build-from-source requirement, no blocker.** `ADR-015`'s own
honestly-flagged wheel-availability risk (Decision point 2) is now
confirmed clear on this host.

Real import check: `.venv\Scripts\python.exe -c "import langgraph,
langchain_openai, mcp, langchain_mcp_adapters; print('ok')"` → printed
`ok`.

**Exact resolved versions:**
- `langgraph` → `1.2.11` (satisfies the `>=1,<2` pin)
- `langchain-openai` → `1.4.3`
- `mcp` → `1.29.0`
- `langchain-mcp-adapters` → `0.3.2`

**Non-AC smoke check (this task carries no locked AC of its own):** PASS —
both the real install and the real import succeeded, per the task's own
Tests section.

No assumption, deviation, or escalation — install went cleanly per
`ADR-015`'s own best-case expectation. `MEMORY.md` updated (Decisions) —
this is the first real confirmation of the wheel-availability risk
`ADR-015` had explicitly left open, worth recording since three future
stories (`REQ-SB-20`/`26`/`27`) depend on this same install having
succeeded. `gate: clear` 2026-08-12 — no MUST-FLAG trigger fired (no
assumption, no ADR change, no unverifiable AC — this task carries none, no
contradiction, no escalation).
