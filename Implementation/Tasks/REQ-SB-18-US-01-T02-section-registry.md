---
id: REQ-SB-18-US-01-T02
title: New app/business/section_registry.py — seeding, self-healing default assignment, CRUD, block-until-empty delete
parent_story: REQ-SB-18-US-01
requirement_id: REQ-SB-18
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-18-US-01-T01]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-18-US-01-T02 — New app/business/section_registry.py

## Parent Story

- Story: [[REQ-SB-18-US-01]] — `../UserStories/REQ-SB-18-US-01-dynamic-agent-sections-and-assignment.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-18 *Dynamic Agent Sections & Agent-to-Section Assignment*

---

## Objective

Add `app/business/section_registry.py`, owning: seeding the starting
5-section set on first read (persisting immediately), self-healing default
assignment for any known agent absent from `assignments`, and Section CRUD
including the block-until-empty delete check (`ADR-014` points 1 and 4) —
composed *alongside*, not inside, `agent_registry.py` (`ADR-011` point 2's
reasoning untouched).

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed `vault_writer.load_sections_state()` /
  `save_sections_state()`.
- `agent_registry.list_agents()` already returns `[{"id","name","type"}]`
  for the 5 known agents (`email-capture`, `meeting-capture`,
  `todo-capture`, `people-producer`, `vault-qa`).

**After / Outputs:**
- `app/business/section_registry.py` (new) exposes: `list_sections()`,
  `create_section(name)`, `rename_section(section_id, name)`,
  `delete_section(section_id) -> {"deleted": bool,
  "blocked_by_agent_ids": [str]}`, `get_agent_section(agent_id)`,
  `set_agent_section(agent_id, section_id) -> bool`.
- On first call to any of the above, `.second-brain/agent_sections.json` is
  seeded with the 5 starting sections (Technical, Sales, Productivity,
  Customers, Products) and every known agent defaulted to `"technical"`,
  persisted immediately.

---

## Files to Modify

- `src/backend/app/business/section_registry.py` (new):
  ```python
  """Sections: a new, persisted, user-mutable concern (ADR-014) — which
  Section an agent belongs to, independent of its Worker/Producer/Expert
  Type. Composed alongside app/business/agent_registry.py, not inside it —
  agent_registry.py itself is not modified (ADR-011 point 2's "agent
  identity/type/actions stay hardcoded" reasoning is untouched).
  """
  from app.business import agent_registry
  from app.data_access import vault_writer

  _STARTING_SECTION_NAMES = ["Technical", "Sales", "Productivity", "Customers", "Products"]


  def _seed_state() -> dict:
      sections = [{"id": vault_writer.tag_slug(name), "name": name} for name in _STARTING_SECTION_NAMES]
      state = {"sections": sections, "assignments": {}}
      vault_writer.save_sections_state(state)
      return state


  def _load_state() -> dict:
      """Seeds the starting 5 sections on first read (persisting
      immediately), then self-heals: any known agent
      (agent_registry.list_agents()) absent from assignments — true for
      every agent on first seed, and for any agent a future story adds
      without a migration step — is assigned to the first section in
      creation order and persisted (ADR-014 point 1)."""
      state = vault_writer.load_sections_state()
      if state is None:
          state = _seed_state()
      if not state["sections"]:
          return state
      default_section_id = state["sections"][0]["id"]
      changed = False
      for agent in agent_registry.list_agents():
          if agent["id"] not in state["assignments"]:
              state["assignments"][agent["id"]] = default_section_id
              changed = True
      if changed:
          vault_writer.save_sections_state(state)
      return state


  def list_sections() -> list[dict]:
      state = _load_state()
      agent_ids_by_section: dict[str, list[str]] = {}
      for agent_id, section_id in state["assignments"].items():
          agent_ids_by_section.setdefault(section_id, []).append(agent_id)
      return [
          {"id": s["id"], "name": s["name"], "agent_ids": agent_ids_by_section.get(s["id"], [])}
          for s in state["sections"]
      ]


  def create_section(name: str) -> dict:
      state = _load_state()
      section_id = vault_writer.tag_slug(name)
      existing = next((s for s in state["sections"] if s["id"] == section_id), None)
      if existing is not None:
          # Same normalized name already exists — return it rather than
          # duplicating (tag_slug collisions collapse to the same section).
          return existing
      section = {"id": section_id, "name": name}
      state["sections"].append(section)
      vault_writer.save_sections_state(state)
      return section


  def rename_section(section_id: str, name: str) -> dict | None:
      """Updates name in place only — section_id (the slug) is fixed at
      creation and never regenerated on rename (ADR-014 point 1), which is
      what makes every existing assignments entry stay correct
      automatically."""
      state = _load_state()
      for section in state["sections"]:
          if section["id"] == section_id:
              section["name"] = name
              vault_writer.save_sections_state(state)
              return section
      return None


  def delete_section(section_id: str) -> dict:
      """Never raises for ordinary control flow — returns a result dict
      (ADR-014 point 4), mirroring the existing _invoke_action/
      trigger_action result-dict convention. The router (T03) translates a
      blocked deletion into HTTP 409."""
      state = _load_state()
      blocked_by_agent_ids = [
          agent_id for agent_id, sid in state["assignments"].items() if sid == section_id
      ]
      if blocked_by_agent_ids:
          return {"deleted": False, "blocked_by_agent_ids": blocked_by_agent_ids}
      state["sections"] = [s for s in state["sections"] if s["id"] != section_id]
      vault_writer.save_sections_state(state)
      return {"deleted": True, "blocked_by_agent_ids": []}


  def get_agent_section(agent_id: str) -> dict | None:
      state = _load_state()
      section_id = state["assignments"].get(agent_id)
      if section_id is None:
          return None
      return next((s for s in state["sections"] if s["id"] == section_id), None)


  def set_agent_section(agent_id: str, section_id: str) -> bool:
      state = _load_state()
      if not any(s["id"] == section_id for s in state["sections"]):
          return False
      state["assignments"][agent_id] = section_id
      vault_writer.save_sections_state(state)
      return True
  ```

---

## Constraints

- Inherits from parent story and `ADR-014` (points 1, 2, 4).
- Must NOT import or modify `agent_chat.py`. May import `agent_registry`
  only (to enumerate known agent ids) — must NOT modify
  `agent_registry.py`.
- `delete_section` must never raise for the ordinary "still in use" case —
  it returns `{"deleted": False, "blocked_by_agent_ids": [...]}`; the
  router layer (`T03`) is the only place a `409` is raised.
- `create_section`/`rename_section` must not regenerate an existing
  section's `id` — only `name` changes on rename.

---

## Tests

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`
   (real `vault_path`, delete any leftover `.second-brain/
   agent_sections.json` from `T01`'s throwaway test first), call
   `list_sections()`. Confirm it returns exactly 5 sections named
   Technical, Sales, Productivity, Customers, Products (ids are
   `tag_slug`s of those names), and that `.second-brain/
   agent_sections.json` now exists with all 5 known agent ids
   (`email-capture`, `meeting-capture`, `todo-capture`,
   `people-producer`, `vault-qa`) present in `assignments`, each mapped
   to `"technical"`.
2. Non-AC smoke check: call `create_section("Operations")`. Confirm
   `list_sections()` now includes it with `agent_ids: []`. Call
   `rename_section(<its id>, "Ops")`. Confirm the same `id` now has
   `name: "Ops"` and any agent previously assigned to it (none, in this
   case) is unaffected.
3. Non-AC smoke check: call `set_agent_section("email-capture",
   "sales")` (an existing section id). Confirm it returns `True` and
   `get_agent_section("email-capture")` now returns the `sales` section.
   Call `set_agent_section("email-capture", "not-a-real-id")`; confirm it
   returns `False` and the previous assignment is unchanged.
4. Non-AC smoke check: call `delete_section("sales")` (now has
   `email-capture` assigned, from step 3). Confirm it returns
   `{"deleted": False, "blocked_by_agent_ids": ["email-capture"]}` and
   `list_sections()` still shows `sales`. Call `set_agent_section
   ("email-capture", "technical")` to unblock, then `delete_section
   ("sales")` again; confirm `{"deleted": True, "blocked_by_agent_ids":
   []}` and `sales` no longer appears in `list_sections()`.
5. Clean up: reset `.second-brain/agent_sections.json` back to a fresh
   seed (delete the file — `T03`'s own verification re-seeds it) so no
   throwaway "Ops"/renamed state leaks into later tasks' verification.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] First read seeds the exact 5 starting sections and self-heals every
      known agent's assignment to the first section in creation order
- [ ] `create_section`/`rename_section` behave per the code above (rename
      never changes `id`)
- [ ] `delete_section` returns a result dict, never raises, blocked when
      `assignments` still references the section
- [ ] `get_agent_section`/`set_agent_section` behave per the code above,
      `set_agent_section` returns `False` for an unknown `section_id`
- [ ] `agent_registry.py` not modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any API surface — `T03` (`sections_router.py`), `T04`
  (`agents_router.py`'s `PATCH /agents/{agent_id}`).
- Provider CRUD — `REQ-SB-19-US-01`'s own `provider_registry.py`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-014` created at
`/plan-tasks` step 1) — the human reviews `ADR-014` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

---

## Implementation Log

**2026-08-11 — Done.** Created `app/business/section_registry.py` matching
the task's own code block verbatim: `_seed_state`/`_load_state`
(seed-then-self-heal), `list_sections`, `create_section`,
`rename_section`, `delete_section` (result-dict, never raises),
`get_agent_section`, `set_agent_section`.

All 4 non-AC smoke checks run live against the real backend `.venv` and
real `vault_path`:
1. First `list_sections()` call seeded exactly 5 sections (Technical,
   Sales, Productivity, Customers, Products) and self-healed all 5 known
   agent ids into `assignments`, each mapped to `"technical"`.
2. `create_section("Operations")` → `agent_ids: []` in `list_sections()`;
   `rename_section(<id>, "Ops")` kept the same `id`, updated `name`.
3. `set_agent_section("email-capture", "sales")` → `True`,
   `get_agent_section` confirmed. `set_agent_section("email-capture",
   "not-a-real-id")` → `False`, prior assignment unchanged.
4. `delete_section("sales")` (still assigned) →
   `{"deleted": False, "blocked_by_agent_ids": ["email-capture"]}`.
   Reassigned to `"technical"`, retried → `{"deleted": True,
   "blocked_by_agent_ids": []}`, `sales` gone from `list_sections()`.

Cleanup: deleted `.second-brain/agent_sections.json` afterward so `T03`
re-seeds from a clean state, per this task's own step 5.

gate: clear 2026-08-11 — no MUST-FLAG trigger fired; implemented exactly
per the task's own literal code block, no assumption needed.
