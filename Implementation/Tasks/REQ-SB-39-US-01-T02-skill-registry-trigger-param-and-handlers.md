---
id: REQ-SB-39-US-01-T02
title: skill_registry.py — invoke_skill gains required trigger param; _SKILL_HANDLERS gains 3 new entries
parent_story: REQ-SB-39-US-01
requirement_id: REQ-SB-39
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-39-US-01-T01]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-39-US-01-T02 — skill_registry.py — `trigger` param + 3 new `_SKILL_HANDLERS` entries

## Parent Story

- Story: [[REQ-SB-39-US-01]] — `../UserStories/REQ-SB-39-US-01-unify-capabilities-model-and-read-only-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-39 *Unify Agent Capabilities Under Skills*

---

## Objective

`invoke_skill(agent_id, skill_id, args, trigger)` gains a required,
no-default `trigger: Literal["chat", "direct", "hub_routed"]` parameter —
mirrors `_invoke_action`'s existing shape exactly (`ADR-028` point 2).
`_SKILL_HANDLERS` gains 3 new entries mapping `T01`'s new stub functions.

---

## Starting State → End State

**Before / Inputs:**
- `invoke_skill(agent_id, skill_id, args=None) -> dict` — no `trigger`
  parameter anywhere on this path.
- `_SKILL_HANDLERS = {"diagram-understanding": ..., "web-research": ...}`.

**After / Outputs:**
- `invoke_skill(agent_id, skill_id, args, trigger)` — `trigger` is
  required, no default value; every real caller must pass one explicitly
  (this task changes only the signature — updating the 3 real call sites
  is `T03`/`T04`/`T07`'s own job, not this task's).
- `_SKILL_HANDLERS` grows to 5 entries, adding `"view_last_run":
  skill_tools.view_last_run`, `"ask_question": skill_tools.ask_question`,
  `"view_channel_status": skill_tools.view_channel_status`.
- `trigger` is accepted and threaded through the signature but is **not**
  read/branched on anywhere in `invoke_skill`'s own body this pass
  (`ADR-028` point 1 — `REQ-SB-39-US-02` adds the real two-axis check).

---

## Files to Modify

- `src/backend/app/business/skill_registry.py` — `invoke_skill`'s
  signature + `_SKILL_HANDLERS` dict.

---

## Constraints

- Inherits from parent story and `ADR-028` point 2.
- `trigger: Literal["chat", "direct", "hub_routed"]` gets **no default** —
  a call site that omits it fails loudly at Python's own call boundary, by
  design (mirrors `_invoke_action`'s own "no default, ever" discipline).
- `invoke_skill` must NOT branch on `trigger` or `mutates` anywhere in this
  task — that gating logic is `REQ-SB-39-US-02`'s own scope.
- `_SKILL_HANDLERS` gains exactly 3 new entries mapped to `T01`'s new
  `skill_tools` functions — same local-dict pattern the existing 2 entries
  already use (kept inside `skill_registry.py`, not moved to
  `skill_tools.py`).
- The existing "check `has_skill_access` before dispatch" ordering must be
  preserved unchanged — Scenario 3's honest-unavailable and Scenario 6's
  refusal must stay distinguishable result shapes.
- Do NOT modify `skill_tools.py` or `agent_registry.py` in this task.

---

## Tests

**Manual verification steps:**
1. Non-AC smoke check: python shell — `skill_registry.invoke_skill(
   "email-capture", "view_last_run", args=None, trigger="direct")` **before**
   granting it — confirm `{"status": "refused", "reason": "Agent does not
   have access to this skill."}` (the access check still runs before
   dispatch, unchanged).
2. [REQ-SB-39-US-01-AC-01] `skill_registry.grant_skill_access(
   "email-capture", "view_last_run")`, then re-run the same
   `invoke_skill(..., trigger="direct")` call — confirm it now dispatches
   to `T01`'s new stub handler and returns the honest-unavailable shape
   (`{"available": False, "message": "This skill is not yet available —
   no real handler has been built for it."}`) — confirms `view_last_run`
   is now a genuinely working, registered, invocable Skill.
3. Non-AC smoke check: confirm calling `skill_registry.invoke_skill(
   "email-capture", "view_last_run", args=None)` (omitting `trigger`
   entirely) raises a `TypeError` — proves no default value was
   accidentally left on the parameter.
4. Clean-up: `skill_registry.revoke_skill_access("email-capture",
   "view_last_run")` — leaves state clean so `T05`'s own retrofit
   verification starts from a pre-migration baseline.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `invoke_skill`'s signature gains a required, no-default `trigger:
      Literal["chat","direct","hub_routed"]` parameter
- [ ] `_SKILL_HANDLERS` gains exactly 3 new entries mapped to `T01`'s stub
      functions
- [ ] `invoke_skill` does not branch on `trigger` or `mutates` anywhere in
      this task
- [ ] `has_skill_access` is still checked before dispatch
- [ ] `skill_tools.py` / `agent_registry.py` not modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Updating the 3 real call sites (`skills_router.py` — `T03`;
  `knowledge_bootstrap.py` — `T04`; `agents_router.py` — `T07`).
- The migration-grant retrofit seed (`T05`).
- `list_agent_capabilities` (`T06`).
- Any gating logic that reads `trigger`/`mutates` together
  (`REQ-SB-39-US-02`).

---

## Context / Notes

This is a **breaking signature change** for any existing caller that does
not pass `trigger` — both of today's two real callers
(`skills_router.py`, `knowledge_bootstrap.py`) are updated in `T03`/`T04`,
and `agents_router.py`'s new call sites are added in `T07`. Do not add a
default value to soften this — the point is every real call site fails
loudly if it forgets the update (`ADR-028`'s own Consequences section).

---

## Implementation Log

**2026-08-13 — Built and verified live** (same worktree/`.env`/`.venv`
setup as `T01`'s own Implementation Log — not repeated here).

`invoke_skill`'s signature became `invoke_skill(agent_id: str, skill_id:
str, args: dict | None, trigger: Literal["chat", "direct",
"hub_routed"]) -> dict` — `trigger` required, no default. Left `args`
also without a default (matching the End State code sample's literal
shown signature, `invoke_skill(agent_id, skill_id, args, trigger)`) —
confirmed safe: only 2 real call sites exist codebase-wide today
(`grep`-confirmed: `skills_router.py`, `knowledge_bootstrap.py`), both
already pass `args` positionally, and both are updated in `T03`/`T04`
regardless. `_SKILL_HANDLERS` grew to 5 entries (the 3 new ones mapped to
`T01`'s new `skill_tools` functions).

Non-AC smoke check: `invoke_skill("email-capture", "view_last_run",
args=None, trigger="direct")` **before** granting → `{"status":
"refused", "reason": "Agent does not have access to this skill."}`.
**PASS** — access check still runs before dispatch.

**AC-01** (continuation from `T01` — the new id is a genuinely working,
registered, invocable Skill): granted `view_last_run` to `email-capture`,
re-ran the same call → `{"available": False, "message": "This skill is
not yet available — no real handler has been built for it."}` (exact
byte compare). **PASS.**

Non-AC smoke check: `invoke_skill("email-capture", "view_last_run",
args=None)` (omitting `trigger`) → raised `TypeError: invoke_skill()
missing 1 required positional argument: 'trigger'`. **PASS** — no default
value was accidentally left on the parameter.

Clean-up: `revoke_skill_access("email-capture", "view_last_run")` ran —
state left at the same clean baseline `T01`'s own log confirmed.

`skill_tools.py` / `agent_registry.py` — confirmed untouched.

gate: clear 2026-08-13 — no new MUST-FLAG trigger (story's own inherited
`ADR-028` flag unchanged, not re-raised here).
