---
id: REQ-SB-82-US-02-T01
title: Register research-agent under the Librarian Section in Second Brain's presentation layer
parent_story: REQ-SB-82-US-02
requirement_id: REQ-SB-82
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-08-25
updated: 2026-08-25
---

# REQ-SB-82-US-02-T01 — Register research-agent under the Librarian Section in Second Brain's presentation layer

## Parent Story

- Story: [[REQ-SB-82-US-02]] — `../UserStories/REQ-SB-82-US-02-research-agent-librarian-section.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Register `research-agent`'s type (`expert`) and Section (`Librarian`) in
Second Brain's own Hermes-presentation adapter, the same pattern
`notes-manager`/`files-manager` already use, so Second Brain's own Agents
Map UI places and types it correctly once the real Hermes profile exists.

---

## Starting State → End State

**Before / Inputs:**
- `agents_map_adapter.py`'s `_AGENT_TYPE`/`_AGENT_SECTION` dicts have no
  entry for `research-agent`.

**After / Outputs:**
- `_AGENT_TYPE["research-agent"] = "expert"`
- `_AGENT_SECTION["research-agent"] = "Librarian"`

---

## Files to Modify

- `src/backend/app/business/hermes/agents_map_adapter.py`

---

## Constraints

- Inherits from parent story.
- Follow the exact same dict-entry pattern already used for every other
  agent id in `_AGENT_TYPE`/`_AGENT_SECTION` — no new registration
  mechanism.
- This task is Second Brain's OWN presentation-layer concern only — it has
  no effect on whether the real, live `research-agent` Hermes profile
  exists or behaves correctly (see `T02` and this story's own Notes on the
  live-profile provisioning gap). An agent id absent from Hermes'
  own real reported agents renders nothing regardless of this dict entry
  (`_to_summary` only iterates `hermes_definitions.list_agents()`'s real
  output) — this entry is inert (but correct, ready) until that real
  profile exists.

---

## Tests

**Manual verification steps:**
1. In a Python shell, monkeypatch `hermes_definitions.list_agents()` (or
   `get_agent`) to include a stub `HermesAgent(id="research-agent", ...)`
   (the closest-to-real substitute technique this project already uses for
   an agent not yet live) and call `agents_map_adapter.list_agent_summaries()`.
   Expect the `research-agent` entry has `type: "expert"` and resolves to
   the real `"Librarian"` Section id (via `_agent_section_id`/
   `_section_id_by_name`).
2. Confirm no other agent's `_AGENT_TYPE`/`_AGENT_SECTION` entry changed.

**Automated tests:** `n/a — test tooling pending (only src/backend/tests/test_health_check.py exists today)`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `_AGENT_TYPE["research-agent"] = "expert"` added
- [x] `_AGENT_SECTION["research-agent"] = "Librarian"` added
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a -- no new decision/pattern/constraint emerged; this is a direct, same-shape extension of the already-documented `_AGENT_TYPE`/`_AGENT_SECTION` pattern)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Creating the real, live `research-agent` Hermes profile itself (`T02`).
- The `research-kb-writer` Skill (`T02`).

---

## Context / Notes

`ADR-008` is the authoritative design reference. This task carries no
AC-tagged verification step of its own — none of this story's 5 locked
Scenarios assert anything about Second Brain's own Agents Map UI; they are
all covered by `T02`. This task exists purely so the presentation layer is
ready the moment the real profile is provisioned.

---

## Implementation Log

**2026-08-25, coder pass.** Added the two dict entries exactly per this
task's own End State, in `src/backend/app/business/hermes/
agents_map_adapter.py`:
- `_AGENT_TYPE["research-agent"] = "expert"`
- `_AGENT_SECTION["research-agent"] = "Librarian"`

Each addition carries a short explanatory comment (`REQ-SB-82-US-02`,
`ADR-008`, 2026-08-25), matching this file's own established per-entry
comment convention. No other line in either dict was touched.
`_AGENT_DISPLAY_NAME` was deliberately NOT touched -- not named in this
task's own Files to Modify / End State / Acceptance Criteria, and an
absent entry there already falls through to the raw agent id by
construction (same as every other agent before its own display-name
entry was added), so nothing is broken by leaving it out; adding one
would have been unrequested scope.

**Test step 1 (Python-shell monkeypatch, in-process):** wrote a throwaway
script (deleted after the run, not part of `## Files to Modify`) that
monkeypatched `hermes_definitions.list_agents()` to append a stub
`HermesAgent(id="research-agent", ...)` alongside the real agents, then
called `agents_map_adapter.list_agent_summaries()`. Observed:
- `research-agent` entry: `type == "expert"` -- **True**
- `research-agent` entry: `section_id` == `_section_id_by_name("Librarian")`'s
  own independently-resolved real Section id (`"librarian"`) -- **True**
Real command: `.venv/Scripts/python.exe .scratch/verify_research_agent_registration.py`
from `src/backend`. Real output:
```
research-agent type: expert
research-agent section_id: librarian
Librarian section_id (independently resolved): librarian
type == 'expert': True
section_id matches Librarian: True
no other agent's type/section changed: True
```

**Test step 2 (no other agent's entry changed):** the same script snapshotted
every OTHER agent id's `(_agent_type, _agent_section_name)` before and
after the monkeypatch/call and diffed them -- byte-identical (`True`,
above).

**Extra live confirmation beyond the task's own named Tests (per the
launching instruction to restart the backend and confirm live, since this
task touches `agents_map_adapter.py`):** the pre-existing `uvicorn --reload`
dev instance on port 8001 was killed by specific PID (both the reloader
and its worker), per this project's own established specific-PID-kill
protocol. A fresh, non-`--reload` instance could not be rebound to 8001 --
`netstat`/`Get-NetTCPConnection` both continued reporting a `LISTEN` owner
PID that `Get-Process`/`Get-CimInstance`/`tasklist` all independently agree
does not exist (a genuinely orphaned Windows TCP listener, not a caching
artifact -- confirmed via 3 independent enumeration tools, ~25s of waiting).
Per this project's own antipattern precedent ("don't keep trying the same
approach when multiple tools agree a PID doesn't exist"), pivoted to an
alternate port (`8010`) rather than continuing to fight it: started a
clean, non-`--reload` instance there, confirmed it booted with zero errors,
then hit the REAL, live `GET /agents` endpoint directly:
- `research-agent` is correctly **absent** from the real response (22
  real agents/pipelines listed, no `research-agent` -- exactly the
  documented, expected "inert until the real Hermes profile exists" state
  this task's own Constraints describe; Hermes has no such profile yet,
  that's `T02`'s job).
- Spot-checked `notes-manager`/`files-manager` (Librarian, `producer`),
  `masdar-expert`/`adnoc-expert`/`taqa-expert` (Customer, `expert`),
  `azure-calculator` (Technology, `expert`), `opp-manager` (Sales,
  `worker`) via the real HTTP response -- every `type`/`section_id`
  matched their pre-existing values exactly, confirming the live server
  (not just the in-process check) shows zero regression to any other
  agent.
Stopped the temporary verification instance (port 8010) afterward,
cleanly. **Disclosed, not silently left:** port 8001's own orphaned OS-level
listener could not be cleared by any means available in this session (no
reboot performed, out of this task's own scope) -- the project's normal
dev backend is currently NOT reachable on 8001 as a result of this
investigation. This is an environmental/OS anomaly discovered while
restarting an already-running server, not caused by this task's own two-line
code change, and does not affect any locked-AC verification above (the
live confirmation succeeded via the alternate port). Flagged in the
coder's closing report for the human's awareness; not written as a formal
`ESCALATIONS.md`/`REVIEW-QUEUE.md` entry since it is not a scope/decision
blocker for this task or the pipeline.

**Scope note:** this task carries no story-level `AC-ID`-tagged
verification step of its own (see `## Context / Notes` above -- all 5 of
`REQ-SB-82-US-02`'s locked ACs are covered by `T02`, which provisions the
real Hermes profile). This task's own 4-item local checklist above is
what was verified. `research-agent` remains genuinely absent from
Hermes' real reported agents until `T02` provisions the real profile --
this task's registration is correct and ready, but inert, exactly as
its own Constraints describe.

gate: clear 2026-08-25 -- no MUST-FLAG trigger fired (no assumption
needed, no ADR/interface change, no new dependency, both dict entries
match the task's own literal End State exactly, both manual Tests steps
passed against real code -- in-process AND live HTTP).
