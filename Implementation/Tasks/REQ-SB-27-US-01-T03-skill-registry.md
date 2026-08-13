---
id: REQ-SB-27-US-01-T03
title: New app/business/skill_registry.py — per-agent grant/revoke CRUD, has_skill_access, invoke_skill, explicit-grant-only (no self-healing default)
parent_story: REQ-SB-27-US-01
requirement_id: REQ-SB-27
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-27-US-01-T01, REQ-SB-27-US-01-T02]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-27-US-01-T03 — New app/business/skill_registry.py

## Parent Story

- Story: [[REQ-SB-27-US-01]] — `../UserStories/REQ-SB-27-US-01-skills-repository-registration-and-access.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-27 *Skills Repository*

---

## Objective

Add `app/business/skill_registry.py`, owning the new, persisted,
user-mutable per-agent skill-*access* concern (mirrors `section_registry.
py`/`provider_registry.py`'s `ADR-014` shape exactly, one concept over):
`list_skills()`, `list_agent_skills(agent_id)`, `grant_skill_access
(agent_id, skill_id)`, `revoke_skill_access(agent_id, skill_id)`,
`has_skill_access(agent_id, skill_id)`, `invoke_skill(agent_id, skill_id)`.
**Deliberately no self-healing default assignment** — explicit-grant-only
(Scenario 2/`AC-02`'s own model); no agent is auto-granted any skill by
this module.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed `vault_writer.load_skills_state()`/
  `save_skills_state()`.
- `T02` has landed `skill_tools.SKILLS` (the code-level catalog) and its
  one stub `@mcp.tool()` skill function.
- `agent_registry.get_agent(agent_id)` / `list_agents()` already exist
  (used only to validate a known agent id — mirrors `provider_registry.py`'s
  own `agent_registry` import for the same purpose).

**After / Outputs:**
- `app/business/skill_registry.py` (new) exposes:
  ```python
  """Skill access: a new, persisted, user-mutable concern (ADR-014's own
  pattern, one concept over) — which agents may invoke which registered
  skills, independent of a skill's own catalog entry or its actual
  implementation. Composed alongside app/business/skill_tools.py, not
  inside it. Deliberately no self-healing default assignment — an agent
  gets skill access only via an explicit grant (Scenario 2); see the
  parent story's own Non-Goals for the still-open "should some skills
  default to all agents" question this module does not resolve.
  """
  from app.business import agent_registry, skill_tools
  from app.data_access import vault_writer


  def _load_state() -> dict:
      state = vault_writer.load_skills_state()
      if state is None:
          state = {"assignments": {}}
          vault_writer.save_skills_state(state)
      return state


  def list_skills() -> list[dict]:
      return list(skill_tools.SKILLS.values())


  def list_agent_skills(agent_id: str) -> list[dict]:
      state = _load_state()
      granted_ids = state["assignments"].get(agent_id, [])
      return [skill_tools.SKILLS[sid] for sid in granted_ids if sid in skill_tools.SKILLS]


  def has_skill_access(agent_id: str, skill_id: str) -> bool:
      state = _load_state()
      return skill_id in state["assignments"].get(agent_id, [])


  def grant_skill_access(agent_id: str, skill_id: str) -> bool:
      """Returns False (no-op) if agent_id or skill_id is unknown."""
      if agent_registry.get_agent(agent_id) is None or skill_id not in skill_tools.SKILLS:
          return False
      state = _load_state()
      granted = state["assignments"].setdefault(agent_id, [])
      if skill_id not in granted:
          granted.append(skill_id)
          vault_writer.save_skills_state(state)
      return True


  def revoke_skill_access(agent_id: str, skill_id: str) -> bool:
      """Returns False if the agent did not have this skill granted (or
      agent_id is unknown); True once revoked (idempotent — revoking an
      already-ungranted skill for a known agent still returns True, mirrors
      section_registry.py's own idempotent-delete shape)."""
      if agent_registry.get_agent(agent_id) is None:
          return False
      state = _load_state()
      granted = state["assignments"].get(agent_id, [])
      if skill_id in granted:
          granted.remove(skill_id)
          vault_writer.save_skills_state(state)
      return True


  def invoke_skill(agent_id: str, skill_id: str) -> dict:
      """Never raises for ordinary control flow — returns a result dict the
      router (T04) translates into the right HTTP response. Checks access
      before checking whether a real handler exists, so Scenario 3's
      refusal and Scenario 4's honest-unavailable are always distinguishable
      (AC-03 vs AC-04)."""
      if skill_id not in skill_tools.SKILLS:
          return {"status": "unknown_skill"}
      if not has_skill_access(agent_id, skill_id):
          return {"status": "refused", "reason": "Agent does not have access to this skill."}
      return skill_tools.invoke(skill_id)
  ```
  — the exact `skill_tools.invoke(skill_id)` dispatch signature must match
  whatever `T02` actually built (a single dispatcher function, or a
  per-skill function looked up by id); reconcile against `T02`'s own
  `## Files to Modify` before writing this file, do not assume.

---

## Files to Modify

- `src/backend/app/business/skill_registry.py` (new) — per the code block
  above, reconciled against `T02`'s actual `skill_tools.py` shape.

---

## Constraints

- Inherits from parent story and `ADR-014`'s "new persisted concern
  composed alongside a hardcoded registry" pattern, applied to
  `skill_tools.py`'s catalog instead of `agent_registry.py`.
- **No self-healing default assignment** — must NOT auto-grant any skill
  to any agent on first read or anywhere else. This is a hard, deliberate
  divergence from `section_registry.py`/`provider_registry.py`'s own
  self-healing precedent — do not port that behavior over by habit.
- `invoke_skill` must check `has_skill_access` **before** attempting to
  invoke the skill's real (or stub) handler — Scenario 3's refusal and
  Scenario 4's honest-unavailable must always be distinguishable, never
  conflated into one response shape.
- May import `agent_registry` (to validate a known agent id) and
  `skill_tools` (to read the catalog / dispatch invocation) only — must
  NOT modify either module.
- `grant_skill_access`/`revoke_skill_access` must never raise for the
  ordinary "already granted" / "not currently granted" case.

---

## Tests

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`
   (delete any leftover `.second-brain/agent_skills.json` first), call
   `list_skills()`. Confirm it returns exactly the one skill `T02`
   registered. Call `list_agent_skills("email-capture")` — confirm `[]`
   (no self-healing, no default grant).
2. Non-AC smoke check: call `grant_skill_access("email-capture",
   "diagram-understanding")` — confirm `True`, and
   `list_agent_skills("email-capture")` now includes it. Call
   `has_skill_access("email-capture", "diagram-understanding")` — confirm
   `True`. Call `grant_skill_access("not-a-real-agent",
   "diagram-understanding")` — confirm `False`.
3. Non-AC smoke check: call `invoke_skill("email-capture",
   "diagram-understanding")` — confirm the honest "not yet available"
   result (from `skill_tools`'s own stub body), never a fabricated result.
   Call `invoke_skill("meeting-capture", "diagram-understanding")` (an
   agent never granted this skill) — confirm a `"refused"`-shaped result,
   distinct in shape from the honest-unavailable result from the previous
   call.
4. Non-AC smoke check: call `revoke_skill_access("email-capture",
   "diagram-understanding")` — confirm `True`, and
   `list_agent_skills("email-capture")` no longer includes it. Call
   `invoke_skill("email-capture", "diagram-understanding")` again —
   confirm it now returns the same `"refused"`-shaped result as step 3's
   never-granted agent.
5. Clean-up: delete `.second-brain/agent_skills.json` — `T04`'s own
   verification does not depend on any pre-existing state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `list_skills()` reads `skill_tools.SKILLS` directly, never derived
      from the MCP server's live tool list
- [x] `list_agent_skills`/`has_skill_access` return `[]`/`False` for an
      agent with no explicit grant — no self-healing default
- [x] `grant_skill_access`/`revoke_skill_access` behave per the code above
      (idempotent, `False`/no-op for an unknown agent id)
- [x] `invoke_skill` checks access before dispatch — refusal (Scenario 3)
      and honest-unavailable (Scenario 4) are distinguishable result shapes
- [x] `agent_registry.py`/`skill_tools.py` not modified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any API surface — `T04` (`skills_router.py`) translates these result
  shapes into HTTP responses (404/403-or-409-style refusal/200 with an
  honest-unavailable body — exact status codes are `T04`'s own call).
- The skill catalog itself, the stub skill's implementation — `T02`.

---

## Context / Notes

**Was transitively blocked via `depends_on: [T01, T02]`** — `T02` was
itself genuinely blocked pending `REQ-SB-25-US-01`'s own decomposer pass
(see `T02`'s own Context/Notes). Now resolved: `T02`'s `depends_on` is
wired to the real `REQ-SB-25-US-01-T05` (`ESCALATIONS.md` → `ESC-011`,
`Resolved`). This task's own code still has no direct dependency on
`app/api/mcp_server.py` — only on `T02`'s `skill_tools.py` output — and
still cannot start until `T02` is actually built, per its ordinary
`depends_on: [T01, T02]` edge.

---

## Implementation Log

**2026-08-12 — coder.** Created `src/backend/app/business/skill_registry.py`
per this task's own code block verbatim (`list_skills`,
`list_agent_skills`, `has_skill_access`, `grant_skill_access`,
`revoke_skill_access`, `invoke_skill`, no self-healing default).

**Reconciliation this task's own text explicitly asked for:** `T02`'s
real `skill_tools.py` built one `@mcp.tool()`-decorated function per
registry entry (`diagram_understanding`), not a generic `skill_tools.
invoke(skill_id)` dispatcher. `invoke_skill`'s own dispatch is
implemented via a small local `_SKILL_HANDLERS: dict[str, Callable]`
mapping (`{"diagram-understanding": skill_tools.diagram_understanding}`)
kept inside `skill_registry.py` itself — `skill_tools.py` is not in this
task's own `## Files to Modify` and was not touched again. Adding a
future second skill means adding one entry here alongside
`skill_tools.SKILLS`'s own new entry — recorded as a pattern worth
reusing if `skill_tools.py` ever needs a real dispatcher of its own.

**Non-AC smoke checks (all pass, `.second-brain/agent_skills.json`
deleted before starting, per this task's own step 1 instruction):**
1. `list_skills()` returned exactly the one skill `T02` registered;
   `list_agent_skills("email-capture")` returned `[]` (no self-healing).
2. `grant_skill_access("email-capture", "diagram-understanding")` → `True`,
   reflected in `list_agent_skills`; `has_skill_access` → `True`;
   `grant_skill_access("not-a-real-agent", ...)` → `False`.
3. `invoke_skill("email-capture", "diagram-understanding")` → the honest
   `{"available": False, ...}` result; `invoke_skill("meeting-capture",
   "diagram-understanding")` (never granted) → `{"status": "refused",
   ...}` — confirmed distinct shapes.
4. `revoke_skill_access("email-capture", "diagram-understanding")` →
   `True`, no longer in `list_agent_skills`; a further `invoke_skill` call
   now returns the same `"refused"` shape as step 3's never-granted agent.
5. Clean-up: `.second-brain/agent_skills.json` deleted afterward.

`agent_registry.py`/`skill_tools.py` not modified by this task.
`status: Ready → Done`.

`gate: clear 2026-08-12` — the dispatch-table reconciliation above is a
scope-internal judgement call this task's own text explicitly
anticipated ("reconcile against T02's own Files to Modify before writing
this file, do not assume"), not a deviation from a locked AC or an
out-of-scope file touch — no MUST-FLAG trigger fired.
