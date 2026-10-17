---
id: REQ-SB-99-US-01-T03
title: HermesCLI reports a failed toolsets read separately from "nothing enabled"
parent_story: REQ-SB-99-US-01
requirement_id: REQ-SB-99
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-10-17
updated: 2026-10-17
---

# REQ-SB-99-US-01-T03 — "Could Not Read" Is Not "Nothing Enabled"

## Parent Story

- Story: [[REQ-SB-99-US-01]] — `../UserStories/REQ-SB-99-US-01-hermes-profile-as-it-really-is.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-99 *See a Hermes Profile As It Really Is — Soul, Skills, Config, Jobs*

---

## Objective

Make the two conditions `cli.list_tools()` currently collapses into one — a
failed `hermes tools list` and a profile with no toolsets enabled —
distinguishable by its callers, without changing any existing caller.

---

## Starting State → End State

**Before / Inputs:**

- `src/backend/app/hermes/cli.py::list_tools(profile_id=None)` (line ~299)
  returns `{}` when `self._run(...)` reports failure **and** `{}` when the
  command succeeded but matched no `_TOOL_LINE_RE` line. Both are the same value
  to every caller.
- `_run()` already returns `(success, stdout-or-stderr text)` and never raises —
  a missing install, a timeout, or an unknown profile are ordinary failures
  here.
- `_profile_args(profile_id)` already handles the `-p` flag; `None`/`"default"`
  mean the root profile.
- There are three existing `list_tools` callers; they must be unaffected.

**After / Outputs:**

- A sibling on `HermesCLI`, e.g.
  `read_tools(profile_id: str | None = None) -> tuple[bool, dict[str, bool], str]`
  — `(succeeded, {toolset: enabled}, message)`, where `message` is `_run()`'s
  own captured text on failure and empty on success. It never raises and never
  fabricates a toolset.
- `list_tools()` delegates to it and returns just the mapping, byte-identical to
  today for every existing caller (`ADR-014`'s same-shape-extension precedent).
- A real success with zero enabled toolsets is `(True, {}, "")`; a failure is
  `(False, {}, "<the real reason>")`.

---

## Files to Modify

- `src/backend/app/hermes/cli.py` — add the sibling, delegate `list_tools()`.
- `src/backend/tests/test_toolsets_read_honesty.py` (new) — the tests below.

---

## Constraints

- Inherits from parent story.
- **Additive, same-shape extension.** `list_tools()` keeps its name, signature
  and return type; its three existing callers are not edited.
- `app/hermes/` stays a portable Hermes client: no `app.config` import, no
  `app.obsidian` import, nothing Second-Brain-aware (`client.py` boundary).
- Parsing is unchanged — the same `_TOOL_LINE_RE` against the same real text.
  Do not invent a `--json` mode; none exists (confirmed against `--help`).
- Never substitute a default or an empty mapping for a failure, anywhere.

---

## Tests

**Automated tests:** `cd src/backend; pytest tests/test_toolsets_read_honesty.py`

Monkeypatch `HermesCLI._run` to return engineered `(success, output)` pairs —
no real subprocess is needed to prove the distinction.

1. `[REQ-SB-99-US-01-AC-03]` With `_run` returning success and real
   `hermes tools list` text (the live 2026-08-29 shape, e.g.
   `"  ✓ enabled  web  🔍 Web Search & Scraping"` plus a `✗ disabled` line and
   an `MCP servers:` line), assert `read_tools("adnoc-expert")` returns
   `succeeded is True` with the correct enabled/disabled mapping, the MCP line
   excluded, and that `list_tools("adnoc-expert")` returns exactly that same
   mapping.
2. `[REQ-SB-99-US-01-AC-06]` With `_run` returning
   `(False, "No real Hermes install found at the configured home path")`, assert
   `read_tools()` returns `succeeded is False`, an empty mapping, and that exact
   message — and that `list_tools()` still returns `{}` for its existing
   callers, unchanged.
3. `[REQ-SB-99-US-01-AC-06]` With `_run` returning success and output that
   matches no toolset line at all, assert `read_tools()` returns
   `succeeded is True` with an empty mapping — the "nothing enabled" case, now
   distinguishable from step 2's failure case by the flag alone.
4. `[REQ-SB-99-US-01-AC-03]` Assert `read_tools("adnoc-expert")` passes the real
   `-p adnoc-expert` argument prefix to `_run`, and `read_tools()` /
   `read_tools("default")` pass none — recorded off the monkeypatched `_run`'s
   received args.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] A failed read and an empty-but-successful read are distinguishable
- [ ] `list_tools()` delegates and is unchanged for its three existing callers
- [ ] The failure carries the real reason text, never a fabricated mapping
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Enabling or disabling toolsets (`enable_tools`/`disable_tools` untouched).
- Calling `read_tools()` from anywhere — `T05` is its first caller.
- Adding a toolsets read to any listing path (`GET /agents`,
  `GET /hermes/agents`) — explicitly forbidden by the story's Constraints and
  `BUG-086`.

---

## Context / Notes

`architecture.md` → **§Honest Absence — Three Different Failures**, third
bullet, and `ADR-043`. This is the one change this story makes to a file it
would otherwise only read, and it is the whole reason Scenario 6's "a failed
toolsets read is reported as a failed read" can be built rather than assumed.

---

## Implementation Log

_(Filled in by the coder.)_
