---
id: REQ-SB-51-US-01-T01
title: Background Agent registry module + JSON persistence (self-healing default, 3-agent backfill)
parent_story: REQ-SB-51-US-01
requirement_id: REQ-SB-51
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-51-US-01-T01 — Background Agent registry module + JSON persistence

## Parent Story

- Story: [[REQ-SB-51-US-01]] — `../UserStories/REQ-SB-51-US-01-background-agents-excluded-from-addressing.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-51 *Background Agents — Excluded from Inter-Agent Addressing, Displayed Separately*

---

## Objective

Add the persisted `is_background_agent` concern: a new `app/business/background_agent_registry.py` module mirroring `working_mode_registry.py`'s exact shape (self-healing default folded into `_load_state()`), backed by a new `vault_writer.py`-owned `.second-brain/agent_background_flags.json` sibling store, with a literal 3-agent exception set (`email-capture`, `meeting-capture`, `todo-capture`) self-healing to `True` and every other agent self-healing to `False`.

---

## Starting State → End State

**Before / Inputs:**
- No `is_background_agent` concept exists anywhere in the backend.
- `app/business/working_mode_registry.py` is the real, shipped precedent this task mirrors exactly (self-healing default inside `_load_state()`, no separate seed step).
- `app/data_access/vault_writer.py` already owns the equivalent `load_working_modes_state`/`save_working_modes_state` pair (lines ~1180-1199) and the `_AGENT_WORKING_MODES_FILE` constant (line 27) this task's own additions sit alongside.

**After / Outputs:**
- `app/business/background_agent_registry.py` exists, exporting `get_is_background_agent(agent_id) -> bool` and `set_is_background_agent(agent_id, is_background_agent) -> None`.
- `app/data_access/vault_writer.py` gains `_AGENT_BACKGROUND_FLAGS_FILE = "agent_background_flags.json"` plus `load_background_agent_flags_state()`/`save_background_agent_flags_state()`, mirroring the working-modes pair's exact shape.
- A fresh vault with no `agent_background_flags.json` self-heals on first read: `email-capture`, `meeting-capture`, `todo-capture` resolve `True`; every other known agent resolves `False`.

---

## Files to Modify

- `src/backend/app/business/background_agent_registry.py` — new file.
- `src/backend/app/data_access/vault_writer.py` — add the `_AGENT_BACKGROUND_FLAGS_FILE` constant (alongside the other `_AGENT_*_FILE` constants, ~line 27) and the `_background_agent_flags_state_path()`/`load_background_agent_flags_state()`/`save_background_agent_flags_state()` trio (alongside the working-modes trio, ~line 1180).

---

## Constraints

- Inherits from parent story.
- Mirror `working_mode_registry.py`'s exact shape (self-healing default inside `_load_state()`, no separate `_seed_state()`) — do not invent a different persistence pattern.
- `vault_writer.py`'s new functions are pure I/O only (per its own file-header convention, `ADR-003`) — the self-healing default/exception-set logic belongs in `background_agent_registry.py`, never in `vault_writer.py`.
- Do not modify `app/business/agent_registry.py` (`ADR-011` point 2 — agent identity/type/actions stay hardcoded; this is composed alongside it, not inside it).
- `set_is_background_agent` performs no agent-existence validation of its own — the caller (`T02`'s `PATCH /agents/{agent_id}`) already 404s on an unknown `agent_id` before any setter is reached, matching `working_mode_registry.set_agent_working_mode`'s own division of responsibility.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-51-US-01-AC-02] In a Python shell (`src/backend`), with a vault that has no `agent_background_flags.json` yet (or after deleting it from the real `VAULT_PATH`'s `.second-brain/` dir), call `background_agent_registry.get_is_background_agent("email-capture")`, `("meeting-capture")`, `("todo-capture")` — expect `True` for all three, with no manual step required. Confirm `.second-brain/agent_background_flags.json` now exists with those three assignments `true`. Then confirm the already-`Done` `run_capture_and_record_completion` handler (`app/business/email_classification.py`) is unmodified and still callable/importable exactly as before this task (no signature change, no new required argument) — this task touches no capture-pipeline file.
2. [REQ-SB-51-US-01-AC-09, partial] Call `background_agent_registry.get_is_background_agent("vault-qa")` (or any non-capture agent) on the same fresh state — expect `False`. Call `set_is_background_agent("vault-qa", True)` then `get_is_background_agent("vault-qa")` — expect `True`, confirming a live, uncached write/read round trip at the registry layer (no restart required). Call `set_is_background_agent("vault-qa", False)` to restore prior state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `background_agent_registry.get_is_background_agent()` resolves `True` for `email-capture`/`meeting-capture`/`todo-capture` and `False` for every other known agent, with no manual backfill step required on a fresh vault.
- [ ] `background_agent_registry.set_is_background_agent()` persists a live write that a subsequent `get_is_background_agent()` call reflects immediately, no caching lag.
- [ ] `vault_writer.py`'s new I/O pair is pure I/O (no default-computation logic), matching its own file-header convention.
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint.
- [ ] `CHANGELOG.md` entry appended.

---

## Out of Scope

- The `GET`/`PATCH /agents` HTTP surface (`T02`).
- The Hub-routing exclusion check (`T03`).
- Any frontend change (`T04`-`T06`).

---

## Context / Notes

Real code to mirror exactly: `src/backend/app/business/working_mode_registry.py` (all 51 lines) and `src/backend/app/data_access/vault_writer.py` lines 1180-1199 (`_working_modes_state_path`/`load_working_modes_state`/`save_working_modes_state`). The only deviation: `_load_state()`'s default-computation reads `agent["id"] in _DEFAULT_BACKGROUND_AGENT_IDS` instead of a single fixed constant.

---

## Implementation Log

Built `app/business/background_agent_registry.py` (new) mirroring
`working_mode_registry.py`'s exact shape — `_load_state()` self-heals
every known agent into `assignments`, defaulting `True` for the literal
`_DEFAULT_BACKGROUND_AGENT_IDS = {"email-capture", "meeting-capture",
"todo-capture"}` set and `False` for every other agent. Added
`vault_writer._AGENT_BACKGROUND_FLAGS_FILE`/`_background_agent_flags_state_path`/
`load_background_agent_flags_state`/`save_background_agent_flags_state`
(pure I/O, no default-computation logic), alongside the working-modes
trio. No changes to `agent_registry.py` (ADR-011 point 2 respected).

**[REQ-SB-51-US-01-AC-02] Verified live** (real Python shell,
`src/backend`, real `VAULT_PATH` — confirmed no pre-existing
`agent_background_flags.json` before this run): `get_is_background_agent`
for `email-capture`/`meeting-capture`/`todo-capture` all resolved `True`
with zero manual step; `.second-brain/agent_background_flags.json` was
created and confirmed to contain `true` for all three, `false` for every
other known agent (including newly-created CDP-test agents from prior
sprints, correctly self-healed). Confirmed `email_classification.
run_capture_and_record_completion`'s signature is byte-identical
(`(limit: int = 10) -> list[dict]`) — this task touched no
capture-pipeline file. PASS.

**[REQ-SB-51-US-01-AC-09, partial] Verified live:** `get_is_background_agent("vault-qa")`
resolved `False` on the same fresh state; `set_is_background_agent("vault-qa", True)`
then an immediate `get_is_background_agent("vault-qa")` read back `True`
(live, uncached round trip, no restart); `set_is_background_agent("vault-qa", False)`
restored prior state, confirmed by a final read. PASS.

Assumption logged for spot-check (scope-internal, not an escalation):
`set_is_background_agent` returns `None` (no boolean return value),
matching the story's own Objective text exactly (`-> None`) rather than
`working_mode_registry.set_agent_working_mode`'s `-> bool` (which
signals an invalid-enum rejection that has no equivalent for a plain
boolean field, per this task's own Constraints) — deliberate, not a
drift.

gate: clear 2026-08-14 — no triggers fired (mirrors an already-Accepted
pattern exactly, no ADR touched, no material assumption beyond the
task's own Context/Notes, both locked ACs verified live).
