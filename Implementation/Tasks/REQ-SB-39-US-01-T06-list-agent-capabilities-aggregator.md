---
id: REQ-SB-39-US-01-T06
title: skill_registry.py — new list_agent_capabilities(agent_id) aggregator (Actions + Skills, unified)
parent_story: REQ-SB-39-US-01
requirement_id: REQ-SB-39
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-39-US-01-T01, REQ-SB-39-US-01-T02]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-39-US-01-T06 — skill_registry.py — `list_agent_capabilities`

## Parent Story

- Story: [[REQ-SB-39-US-01]] — `../UserStories/REQ-SB-39-US-01-unify-capabilities-model-and-read-only-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-39 *Unify Agent Capabilities Under Skills*

---

## Objective

Add `skill_registry.list_agent_capabilities(agent_id) -> list[dict]`,
composing `agent_registry.get_agent(agent_id)["actions"]` (filtered to
exclude any id that is also a `skill_tools.SKILLS` member — i.e. the still
genuinely-real Actions only: `run_capture_now`, `pause_schedule`,
`rebuild_person_note`, `build_knowledge`, agent-dependent) with
`list_agent_skills(agent_id)` (the agent's granted Skills, including the 3
migrated ones), returned as one combined, uniformly-shaped list
(`ADR-028` point 6).

---

## Starting State → End State

**Before / Inputs:**
- No aggregator exists — `agent_registry.py`'s raw `actions` array and
  `skill_registry.list_agent_skills` are two separate, unmerged reads.

**After / Outputs:**
- `skill_registry.list_agent_capabilities(agent_id)` returns one combined
  list: every still-real Action the agent carries (excluding any id also
  present in `skill_tools.SKILLS`, so a migrated id never appears twice)
  plus every Skill currently granted to it (including the 3 migrated
  ones).
- Each returned item shares a uniform shape reconciling Actions'
  `{"id","label"}` with Skills' `{"id","name","description"}` — e.g.
  `{"id": str, "label": str, "kind": "action" | "skill"}` (exact field
  names are this task's own latitude, per `ADR-028` point 6 — document
  whatever shape is chosen below, in Context/Notes).

---

## Files to Modify

- `src/backend/app/business/skill_registry.py` — new
  `list_agent_capabilities(agent_id)` function.

---

## Constraints

- Inherits from parent story and `ADR-028` point 6.
- Placed in `skill_registry.py` (which already imports `agent_registry` —
  a one-directional dependency). Must NOT make `agent_registry.py` import
  `skill_registry` — that layering direction is not used anywhere in this
  project and must not be introduced here.
- Must filter `agent_registry.get_agent(agent_id)["actions"]` to exclude
  any id that is also a `skill_tools.SKILLS` member, so a migrated id
  never appears twice (once via the raw actions array, once via
  `list_agent_skills`).
- Must NOT modify `agent_registry.py` or `skill_tools.py`.
- Returns `[]` (not an error) for a known agent with zero capabilities of
  either kind; propagates whatever `agent_registry.get_agent` returns for
  an unknown agent (this function does not itself validate agent
  existence — callers, e.g. `agents_router.py`'s `get_agent`, already do).

---

## Tests

**Manual verification steps:**
1. [REQ-SB-39-US-01-AC-07] Python shell (run after `T05`'s retrofit seed
   has applied — grant it manually first if testing this task in
   isolation): `skill_registry.list_agent_capabilities("vault-qa")` —
   confirm the result includes `ask_question` and `view_channel_status`
   exactly once each (not duplicated), and confirms `vault-qa` carries no
   still-real Action today (its `agent_registry.py` entry has none).
2. [REQ-SB-39-US-01-AC-07] `skill_registry.list_agent_capabilities(
   "email-capture")` — confirm it includes `view_last_run` (Skill-sourced)
   AND `run_capture_now`, `pause_schedule` (still-real Actions, sourced
   from `agent_registry.py`) together in one combined list, with a
   consistent per-item shape across both kinds.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `list_agent_capabilities(agent_id)` added, combining filtered
      Actions + `list_agent_skills`
- [ ] No duplicate items for a migrated id
- [ ] `agent_registry.py` / `skill_tools.py` not modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- `agents_router.py`'s `get_agent` response change to consume this
  function (`T08`).
- `agents_router.py`'s dispatch fork (`T07`).

---

## Context / Notes

**Chosen shape (implemented):** `{"id": str, "label": str, "kind":
"action" | "skill"}`. Actions map `{"id", "label"}` directly plus
`"kind": "action"`; Skills map their own `"id"`, `"name"` → `"label"`,
plus `"kind": "skill"` (Skills' `"description"` is intentionally dropped
from this aggregate view — still available via `list_skills()`/
`list_agent_skills()` directly if a future consumer needs it). `T08` and
`T09` (frontend) must consume exactly this shape.

---

## Implementation Log

**2026-08-13 — Built and verified live** (same worktree setup as `T01`).

Added `list_agent_capabilities(agent_id)` to `skill_registry.py`, placed
after `invoke_skill` — composes `agent_registry.get_agent(agent_id)
["actions"]` (filtered to exclude any id also in `skill_tools.SKILLS`)
with `list_agent_skills(agent_id)` into the chosen uniform shape (see
Context/Notes above).

**AC-07:** `list_agent_capabilities("vault-qa")` (run post-`T05` retrofit)
→ `[{"id": "ask_question", "label": "Ask a Question", "kind": "skill"},
{"id": "view_channel_status", "label": "View Channel Status", "kind":
"skill"}, {"id": "web-research", "label": "Web Research", "kind":
"skill"}]` — `ask_question`/`view_channel_status` each exactly once, zero
still-real Actions (matches `vault-qa`'s own real `agent_registry.py`
entry, which has none). **PASS.**

**AC-07:** `list_agent_capabilities("email-capture")` →
`run_capture_now`/`pause_schedule` (`kind: "action"`, still-real Actions,
sourced from `agent_registry.py`) together with `view_last_run` (`kind:
"skill"`, Skill-sourced) in one combined list, consistent shape across
both kinds. **PASS.**

`agent_registry.py` / `skill_tools.py` — confirmed untouched.

gate: clear 2026-08-13 — no new MUST-FLAG trigger.
