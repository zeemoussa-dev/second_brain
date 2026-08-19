---
id: REQ-SB-79-US-01-T01
title: agent_registry.py — retired flag, retire_agent(), list_agents(include_retired)
parent_story: REQ-SB-79-US-01
requirement_id: REQ-SB-79
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-79-US-01-T01 — `agent_registry.py` retire-without-delete primitive

## Parent Story

- Story: [[REQ-SB-79-US-01]] — `../UserStories/REQ-SB-79-US-01-librarian-two-sub-pipelines.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-79 *The Librarian — Two Sub-Pipelines*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Two Sub-Pipelines" § "`agent_registry.py` gains its first 'retire without delete' primitive"; `Implementation/Architecture/ADR.md` → `ADR-058` Decision 2

---

## Objective

Give `agent_registry.py` its first "retire without delete" capability — a CREATED agent (never a `_SEED_AGENTS` entry) can be marked `retired`, `list_agents()` can optionally exclude retired agents, and `get_agent()` stays completely unchanged so every historical record attributed to a retired agent keeps resolving a real, honest name forever.

---

## Starting State → End State

**Before / Inputs:**
- `agent_registry.py` has `get_agent(agent_id)`, `list_agents()` (no args), `get_action(agent_id, action_id)`, `create_agent(name, type, settings=None)`. No rename/delete/retire primitive exists.
- `created_agents` records (the persisted `.second-brain/agents_registry.json` overlay, via `vault_writer.load_agents_registry_state`/`save_agents_registry_state`) are plain `{"name", "type", "settings", "actions"}` dicts, keyed by `agent_id`.

**After / Outputs:**
- Every CREATED agent record gains an additive `retired: bool` key, default `False` — set by `create_agent` at creation time, and back-filled to `False` for any already-existing created-agent record read without the key (so a pre-existing `.second-brain/agents_registry.json` never crashes on a missing key).
- `retire_agent(agent_id: str) -> bool` — sets `retired = True` on a CREATED agent's own record; idempotent no-op (returns `True`) if already retired; returns `False` for an unknown `agent_id` OR a `_SEED_AGENTS` id (a shipped, static agent can never be retired).
- `list_agents(include_retired: bool = False) -> list[dict]` — default excludes any created agent whose `retired` is `True`; every `_SEED_AGENTS` entry is always included (seed agents have no `retired` concept). `include_retired=True` returns every agent, retired or not.
- `get_agent(agent_id)` — **completely unchanged**, no new parameter, always resolves ANY agent regardless of `retired`.

---

## Files to Modify

- `src/backend/app/business/agent_registry.py` — add `retired` to `create_agent`'s own record shape, add `retire_agent`, add the `include_retired` parameter to `list_agents`.

---

## Constraints

- Inherits from parent story.
- **`get_agent()` must not gain a new parameter or change its return shape in any way** — every existing caller (`_resolved()` in `pending_approvals_router.py`, every agent-history-name lookup) must keep working unmodified.
- **`_SEED_AGENTS` entries can never be retired** — `retire_agent` returns `False` for any `agent_id` present in `_SEED_AGENTS`, never raises, never mutates `_SEED_AGENTS` (a plain in-code dict, not persisted state).
- **Idempotent** — calling `retire_agent` on an already-retired agent is a safe no-op, never an error (needed for `T05`'s own "every app start" bootstrap call).
- **Additive only** — no existing `created_agents` record's `name`/`type`/`settings`/`actions` keys change shape.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`) — this task touches only the `business` layer (`vault_writer` read/write calls it already makes, unchanged).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-79-US-01-AC-06]` Create a real test agent via `create_agent("ZZ-Decomposer-T01-Test-Agent", type="worker")`. Confirm its own persisted record carries `retired: False`.
2. Call `retire_agent(<that test agent's id>)`. Confirm it returns `True`, and the persisted record now carries `retired: True`.
3. Call `retire_agent(<the same id>)` again. Confirm it returns `True` (idempotent no-op), not an error.
4. Call `retire_agent("librarian-housekeeping")` before it is a real created agent (should return `False` — it is currently a `_SEED_AGENTS`-shaped... actually confirm: `librarian-housekeeping` is a CREATED agent via `ensure_librarian_agent_and_section`, not a `_SEED_AGENTS` entry — confirm `retire_agent` succeeds on it once it is real). Separately, call `retire_agent("email-capture-pipeline")` (a real `_SEED_AGENTS` id) and confirm it returns `False`, unmodified.
5. `[REQ-SB-79-US-01-AC-01]` Call `list_agents()` (default) after step 2. Confirm the retired test agent from step 1 is NOT in the result. Call `list_agents(include_retired=True)`. Confirm it IS in the result.
6. Call `get_agent(<the retired test agent's id>)`. Confirm it still returns the real record (name, type, settings, actions) — `get_agent` is unaffected by `retired`.
7. Clean up the disposable test agent's own persisted record afterward (or leave it retired/harmless — disclose the choice in the Implementation Log).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `retired: bool` (default `False`) present on every created-agent record
- [ ] `retire_agent()` idempotent; `False` for unknown/`_SEED_AGENTS` ids
- [ ] `list_agents(include_retired=False)` excludes retired created agents by default; `_SEED_AGENTS` entries always included
- [ ] `get_agent()` completely unchanged
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Retiring `librarian-housekeeping` itself — `T05`'s own scope (this task only builds the primitive).
- Any caller of `list_agents()` — none of `agents_router.py`/`agent_activity.py`/`section_registry.py`/etc. need edits here; their own default (no-argument) call already gets the new, correct default-excludes-retired behavior with zero code change on their side.

---

## Context / Notes

Multiple real callers already invoke `agent_registry.list_agents()` with no arguments (`app/api/agents_router.py`, `app/business/agent_activity.py`, `app/business/agent_keywords.py`, `app/business/background_agent_registry.py`, `app/business/provider_registry.py`, `app/business/section_registry.py`, `app/business/system_health.py`, `app/business/working_mode_registry.py`) — confirmed by grep this pass. Every one of them gets the new default (`include_retired=False`) automatically, with zero code change on their own side, since the new parameter is additive with a default. This is the intended, disclosed effect (`ADR-058` Decision 2's own "structurally stops appearing... with ZERO frontend change" framing) — not a gap to fix in this task.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
