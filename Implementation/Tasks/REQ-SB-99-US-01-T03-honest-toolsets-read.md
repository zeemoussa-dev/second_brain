---
id: REQ-SB-99-US-01-T03
title: HermesCLI reports a failed toolsets read separately from "nothing enabled"
parent_story: REQ-SB-99-US-01
requirement_id: REQ-SB-99
type: backend
status: Done
gate: flagged
gate_reason: "Optional skim only — four scope-internal judgement calls logged in the Implementation Log (the tuple shape and its empty-string success message, the two cost tests added beyond the four prescribed steps, capturing the real `_hermes_exe` at import time to exercise conftest's second sandbox seam, and `list_tools()` delegating by index). Nothing is blocked; both locked ACs verified."
phase: P2
depends_on: []
created: 2026-10-17
updated: 2026-10-18
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

- [x] A failed read and an empty-but-successful read are distinguishable
- [x] `list_tools()` delegates and is unchanged for its three existing callers
- [x] The failure carries the real reason text, never a fabricated mapping
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      — not updated: nothing new. `ADR-043` already records the decision, and
      `ADR-014`'s same-shape-extension precedent already exists.
- [x] `CHANGELOG.md` entry appended

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

**2026-10-18 — Done.** `HermesCLI.read_tools(profile_id=None) -> tuple[bool,
dict[str, bool], str]` added in `src/backend/app/hermes/cli.py`;
`list_tools()` delegates to it and returns the mapping only. Parsing, the
regex, `_profile_args` and the `_run` call are untouched — the only new
behaviour is that the read's own success survives the return. No caller was
edited (the three existing ones are in `agent_manager.py`, lines 177/241/684).

Commit `e373391` — code + tests. Docs commit follows.

### Verification — automated mode, 10 AC-tagged tests

`cd src/backend; .venv/Scripts/python.exe -m pytest tests/test_toolsets_read_honesty.py -q`
→ **10 passed**. Full suite measured on this checkout before any edit:
**538 passed, 0 failed, 54.4s**; after: **548 passed, 0 failed, 38.2s** (+10,
exactly this file). Neither known flake fired in either run.

- **`REQ-SB-99-US-01-AC-03`** — *the enabled toolsets recorded for that profile
  are among what is shown*. **Pass.**
  `test_a_real_read_reports_what_is_enabled_and_what_is_not` drives the real
  2026-08-29 output shape (two checkmark sections plus an `MCP servers:`
  section) and observes `(True, {"web": True, "shell": False,
  "obsidian": True}, "")` — the disabled toolset present and `False`, the
  `outlook` MCP line excluded because it carries no checkmark.
  `test_list_tools_returns_exactly_what_the_read_found` observes
  `list_tools(profile) == read_tools(profile)[1] == ` that same mapping.
  `test_a_named_profile_is_targeted_and_the_root_profile_is_not` observes the
  recorded argv as exactly `[["-p", "adnoc-expert", "tools", "list"],
  ["tools", "list"], ["tools", "list"]]` for `("adnoc-expert")`, `()` and
  `("default")` — the root profile takes no flag.
- **`REQ-SB-99-US-01-AC-06`** — *a failed toolsets read is reported as a failed
  read, never as "no toolsets are enabled"*. **Pass.**
  `test_a_failed_read_says_so_and_carries_the_real_reason` observes
  `(False, {}, "No real Hermes install found at the configured home path")` —
  the exact captured text, no fabricated toolset.
  `test_nothing_enabled_is_a_successful_read_not_a_failure` observes
  `(True, {}, "")` for output matching no toolset line. The two cases differ in
  the flag alone — their mapping and their `list_tools()` value are both `{}`,
  which is the collapse this task removed.
  `test_the_existing_callers_still_see_an_empty_mapping_on_failure` observes
  `list_tools() == {}` on failure, unchanged from before this task.
  `test_the_sandboxed_install_is_the_honest_failure_path` observes the same
  failure triple produced by conftest's sandbox itself rather than by a stub.

### Cost, pinned by equality

Measured through a recorder substituted for `subprocess.run`, with
`_hermes_exe()` pointed at a path under `tmp_path`:

- **One read = exactly 1 subprocess**, and its argv pinned whole:
  `spawns == [[str(fake_exe), "-p", "adnoc-expert", "tools", "list"]]`.
  `list_tools()` measured separately at the same **1** — delegating did not
  double the existing callers' cost.
- **A failing read = exactly 1 subprocess, never retried:** `returncode 1`
  yields `spawns == [[str(fake_exe), "-p", "adnoc-expert", "tools", "list"]]`
  and `(False, {}, "Error: profile 'adnoc-expert' not found")`.
- `BUG-086` is the named precedent; `T01` and `T02` pinned by equality for the
  same reason and this file follows them.

### No access to the operator's real install

- An autouse fixture refuses **both** `subprocess.run` and `subprocess.Popen`
  for the whole file, so a test that forgot its own seam would fail rather than
  spawn. The two cost tests replace `run` with a recorder after it; every other
  test never reaches `_run`'s body at all.
- conftest's suite-wide sandbox is asserted, not assumed:
  `test_no_test_here_can_see_the_operators_real_install` checks
  `settings.hermes_home_path` does not exist, restores the **real**
  `_hermes_exe` over a `tmp_path` home, and observes
  `shutil.which` asked exactly `["hermes"]` and nothing resolved — the second
  seam this file is obliged to respect, since a sandboxed `HERMES_HOME` alone
  would let `_hermes_exe()` find the real launcher on PATH. Nothing was created
  under the temp home (`tmp_path/bin` absent afterwards).
- Zero reads, zero writes and zero subprocesses against the real install:
  structurally, every path here either stops at `_hermes_exe() -> None` or at a
  recorder, and `app/hermes/cli.py` touches no file of its own.

### Judgement calls (scope-internal — logged, not escalated)

1. **The tuple shape** is the task's own suggested
   `(succeeded, mapping, message)`, with `message` `""` on success rather than
   `None` — one type for the field, and "" reads as "nothing to report" at the
   call site `T05` will write. A dataclass was not introduced for a
   three-field internal return in a portable client module.
2. **`list_tools()` delegates by index** (`return self.read_tools(profile_id)[1]`)
   rather than by unpacking — smallest possible diff on the method three
   callers depend on.
3. **Two cost tests beyond the four prescribed steps.** The `## Tests` block
   prescribes monkeypatching `_run`, which cannot see a subprocess; pinning the
   spawn count by equality needed the `subprocess.run` seam. Added rather than
   substituted — all four prescribed steps are present.
4. **The real `_hermes_exe` is captured at module import time**
   (`_REAL_HERMES_EXE`), before conftest's autouse fixture replaces it, so the
   sandbox's second seam can be demonstrated rather than described. It is used
   in one test, paired with a `shutil.which` that finds nothing, so the real
   launcher is never resolvable there.

Nothing written to `ESCALATIONS.md` or `REVIEW-QUEUE.md`: no new dependency, no
shared-interface change (the extension is additive and no caller moved), no ADR
deviation, no file needed outside `## Files to Modify`, no unclear requirement.
