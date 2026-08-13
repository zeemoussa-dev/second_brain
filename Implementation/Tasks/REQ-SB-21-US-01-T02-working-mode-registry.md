---
id: REQ-SB-21-US-01-T02
title: New app/business/working_mode_registry.py — self-healing default "autonomous", get/set per-agent working mode
parent_story: REQ-SB-21-US-01
requirement_id: REQ-SB-21
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-21-US-01-T01]
created: 2026-08-12
updated: 2026-08-12
---

**Re-confirmed unchanged, 2026-08-12 (`ADR-020` decomposer pass).** `ADR-020`
supersedes `ADR-018` points 3/5 only — this task's own scope (`ADR-018`
point 1) is untouched; no logic change needed.

# REQ-SB-21-US-01-T02 — New app/business/working_mode_registry.py

## Parent Story

- Story: [[REQ-SB-21-US-01]] — `../UserStories/REQ-SB-21-US-01-agent-working-modes.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-21 *Agent Working Modes*

---

## Objective

Add `app/business/working_mode_registry.py`, owning: self-healing default
(`"autonomous"`) assignment for any known agent absent from
`assignments`, and `get_agent_working_mode`/`set_agent_working_mode`
(`ADR-018` point 1). Unlike `section_registry.py`/`provider_registry.py`,
working mode is a fixed 3-value enum, not a user-created catalog, so
seeding folds directly into `_load_state()` — no separate `_seed_state()`
(`ADR-018` point 1's own deliberate simplification).

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed `vault_writer.load_working_modes_state()`/
  `save_working_modes_state()`.
- `agent_registry.list_agents()` returns the 5 known agents.

**After / Outputs:**
- `app/business/working_mode_registry.py` (new) exposes:
  `VALID_WORKING_MODES` (the fixed 3-value tuple),
  `get_agent_working_mode(agent_id) -> str` (never `None` — always
  resolvable, by construction), `set_agent_working_mode(agent_id, mode)
  -> bool` (`False` if `mode` is not one of the three valid values).
- On first call to either, `.second-brain/agent_working_modes.json` is
  seeded with every known agent defaulted to `"autonomous"`, persisted
  immediately.

---

## Files to Modify

- `src/backend/app/business/working_mode_registry.py` (new):
  ```python
  """Working mode: a new, persisted, user-mutable per-agent concern
  (ADR-018 point 1) — Autonomous | Supervised | Manual, gating both the
  chat/direct-action funnel (app/api/agents_router.py) and the
  background-capture scheduler tick (app/business/email_classification.py).
  Composed alongside app/business/agent_registry.py, not inside it —
  agent_registry.py is not modified (ADR-011 point 2's "agent identity/
  type/actions stay hardcoded" reasoning untouched a second time over).
  Unlike Sections/Providers (ADR-014), this is a fixed 3-value enum, not a
  user-created catalog — no "list of entities" half to this file, only
  the assignment map, so seeding folds directly into _load_state() rather
  than a separate _seed_state() (ADR-018 point 1's own deliberate, minor
  simplification).
  """
  from app.business import agent_registry
  from app.data_access import vault_writer

  VALID_WORKING_MODES = ("autonomous", "supervised", "manual")
  _DEFAULT_WORKING_MODE = "autonomous"


  def _load_state() -> dict:
      state = vault_writer.load_working_modes_state()
      if state is None:
          state = {"assignments": {}}
      changed = False
      for agent in agent_registry.list_agents():
          if agent["id"] not in state["assignments"]:
              state["assignments"][agent["id"]] = _DEFAULT_WORKING_MODE
              changed = True
      if changed:
          vault_writer.save_working_modes_state(state)
      return state


  def get_agent_working_mode(agent_id: str) -> str:
      """Never returns None — any known agent absent from assignments is
      self-healed to the default inside _load_state() before this reads
      it; an unknown agent_id also resolves to the default rather than
      raising, matching get_agent_section's own no-raise style."""
      state = _load_state()
      return state["assignments"].get(agent_id, _DEFAULT_WORKING_MODE)


  def set_agent_working_mode(agent_id: str, mode: str) -> bool:
      if mode not in VALID_WORKING_MODES:
          return False
      state = _load_state()
      state["assignments"][agent_id] = mode
      vault_writer.save_working_modes_state(state)
      return True
  ```

---

## Constraints

- Inherits from parent story and `ADR-018` point 1.
- May import `agent_registry` only (to enumerate known agent ids) — must
  NOT modify `agent_registry.py`.
- `get_agent_working_mode` must never raise and must never return `None`
  or any value outside `VALID_WORKING_MODES`.
- `set_agent_working_mode` must reject (return `False`, not raise or
  silently coerce) any value outside `VALID_WORKING_MODES` — the router
  layer (`T04`) translates a rejected value into `HTTP 400`.

---

## Tests

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`
   (real `vault_path`; delete any leftover
   `.second-brain/agent_working_modes.json` from `T01`'s throwaway test
   first), call `get_agent_working_mode("email-capture")`. Confirm it
   returns `"autonomous"` and `.second-brain/agent_working_modes.json` now
   has all 5 known agent ids in `assignments`, each `"autonomous"`.
2. Non-AC smoke check: call `set_agent_working_mode("email-capture",
   "supervised")`. Confirm it returns `True` and
   `get_agent_working_mode("email-capture")` now returns `"supervised"`.
   Call `set_agent_working_mode("email-capture", "not-a-real-mode")` —
   confirm `False`, assignment unchanged (still `"supervised"`).
3. Clean-up: call `set_agent_working_mode("email-capture", "autonomous")`
   to reset back to the seed default, so no throwaway state leaks into
   later tasks' verification.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] First read seeds every known agent to `"autonomous"` in
      `assignments`, persisted immediately
- [ ] `get_agent_working_mode` never returns `None`/an invalid value
- [ ] `set_agent_working_mode` rejects (returns `False`) any value outside
      `VALID_WORKING_MODES`, applies and persists a valid one
- [ ] `agent_registry.py` not modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any API surface — `T04` (`agents_router.py`'s `PATCH
  /agents/{agent_id}` working-mode portion, the `_invoke_action` gate
  split).
- The background-pipeline gate — `T05`
  (`email_classification.py::run_capture_and_record_completion`).
- Pending-approval workflow records — `T03`
  (`pending_approval_registry.py`).

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-018` created at
`/plan-tasks` step 1) — the human reviews `ADR-018` and this task
breakdown together; the pipeline does not halt, so this task proceeds to
`Ready` alongside the rest of the story.

This task carries no AC-tagged step of its own — `REQ-SB-21-US-01-AC-07`
(every agent always has exactly one mode assigned, self-healed default)
is verified live, on the real Agent Settings panel, in `T07`
(`AgentDetailPanel.tsx`), the same "user-observable outcome" placement
rule `REQ-SB-19-US-01-T02`/`T06` already established for Provider's own
self-healing default.

---

## Implementation Log

**2026-08-12, coder (`/implement-sprint`, `SPRINT-021`).** New
`app/business/working_mode_registry.py` built exactly as specified.

No locked AC of its own — verified via the Tests block's non-AC smoke
checks, live, against the real backend `.venv`/vault:
1. `get_agent_working_mode("email-capture")` on first call returned
   `"autonomous"` and seeded `.second-brain/agent_working_modes.json`
   with all 5 known agents, each `"autonomous"`. PASS.
2. `set_agent_working_mode("email-capture", "supervised")` returned
   `True` and persisted; `set_agent_working_mode("email-capture",
   "not-a-real-mode")` returned `False`, assignment unchanged. PASS.
3. Reset back to `"autonomous"` per the task's own clean-up step.

Later, live end-to-end at `T04`/`T05`/`T06`/`T07`/`T08`'s own
verification passes, this module's `get_agent_working_mode`/
`set_agent_working_mode` were exercised dozens of times against the
real gate and the real Agent Settings picker with no defect.

Gate: `clear` — no MUST-FLAG trigger fired.
