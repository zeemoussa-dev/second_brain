---
id: REQ-SB-39-US-01-T05
title: skill_registry.py — one-time migration-grant retrofit seed for the 4 real already-shipped agents
parent_story: REQ-SB-39-US-01
requirement_id: REQ-SB-39
type: backend
status: Done
gate: flagged
gate_reason: "scope-internal judgement call — a necessary recursion fix inside skill_registry.py, spot-check requested"
phase: P1
depends_on: [REQ-SB-39-US-01-T01, REQ-SB-39-US-01-T02]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-39-US-01-T05 — skill_registry.py — migration-grant retrofit seed

## Parent Story

- Story: [[REQ-SB-39-US-01]] — `../UserStories/REQ-SB-39-US-01-unify-capabilities-model-and-read-only-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-39 *Unify Agent Capabilities Under Skills*

---

## Objective

**This is the explicit retrofit task the operator's own directive
("Everything, including existing shipped agents") requires — it must
exist as its own task, not be folded into `T01`/`T02`'s mechanism
plumbing (`ADR-028` point 5, and the parent story's own `## Notes`).** Add
a one-time, explicitly-scoped migration-grant seed inside
`skill_registry._load_state()` that grants the 4 real, already-shipped
agents that carried the equivalent Action before this migration the
matching Skill access.

---

## Starting State → End State

**Before / Inputs:**
- `_load_state()` only initializes `{"assignments": {}}` on first-ever
  load; nothing seeds any grant.
- The 4 real agents (`email-capture`, `meeting-capture`, `todo-capture`,
  `people-producer`, `vault-qa`) have zero Skill grants for
  `view_last_run`/`ask_question`/`view_channel_status` even though they
  carried the equivalent Action before this migration.

**After / Outputs:**
- A small, literal mapping —
  ```python
  _MIGRATION_GRANT_SEED = {
      "view_last_run": ["email-capture", "meeting-capture", "todo-capture", "people-producer"],
      "ask_question": ["vault-qa"],
      "view_channel_status": ["vault-qa"],
  }
  ```
  — is applied inside `_load_state()`, granting each `(skill_id,
  agent_id)` pair via the existing, already-idempotent
  `grant_skill_access` ("only append if not already granted").
- After the first `_load_state()` call following this change, the 4 real
  agents show the equivalent Skill grant in
  `.second-brain/agent_skills.json`.

---

## Files to Modify

- `src/backend/app/business/skill_registry.py` — `_load_state()`.

---

## Constraints

- Inherits from parent story and `ADR-028` point 5.
- The mapping is a **small, literal, hardcoded dict** — exactly the 3
  already-migrated ids to exactly the 4 named agents. This is a **bounded,
  one-time historical migration backfill**, NOT a general self-healing
  default-assignment mechanism — it must NOT grow to cover any future
  Skill without its own new, explicit mapping entry and its own new ADR
  (`ADR-028`'s own Alternatives-Considered explicitly rejects a blanket
  self-heal here).
- Must be idempotent — calling `_load_state()` repeatedly must never
  create duplicate entries in any agent's granted-skills array.
- Must reuse `grant_skill_access(agent_id, skill_id)` itself (not hand-roll
  the append logic), so its existing unknown-agent/unknown-skill guards
  apply uniformly.
- `compass-expert` and `vault-filing-expert` are explicitly NOT part of
  this mapping — they never carried these Action ids; do not add them.
- Must NOT modify `skill_tools.py` or `agent_registry.py`.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-39-US-01-AC-01] Delete `.second-brain/agent_skills.json` if it
   exists (clean slate). Call `skill_registry.list_agent_skills(
   "email-capture")` — confirm it includes `"view_last_run"` **without any
   explicit grant call having been made in this test**. Repeat for
   `"meeting-capture"`, `"todo-capture"`, `"people-producer"` — same
   result. Call `skill_registry.list_agent_skills("vault-qa")` — confirm
   it includes both `"ask_question"` and `"view_channel_status"`. This
   confirms the 4 real, already-shipped agents are genuinely retrofitted,
   not just theoretically grantable.
2. [REQ-SB-39-US-01-AC-01] Idempotency: call `list_agent_skills` (or any
   function that triggers `_load_state()`) a second time — inspect
   `.second-brain/agent_skills.json` directly and confirm no duplicate
   entries appear in any agent's assignments array.
3. Non-AC smoke check: confirm `compass-expert` and `vault-filing-expert`
   have NOT been granted any of the 3 migrated ids by this seed — proves
   the mapping is exactly scoped, not a blanket grant.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] The literal `_MIGRATION_GRANT_SEED` mapping is folded into
      `_load_state()`, applied via `grant_skill_access`
- [ ] Idempotent — no duplicate grants on repeated `_load_state()` calls
- [ ] Exactly scoped to the 4 named agents / 3 named ids — no other
      agent/skill affected
- [ ] `skill_tools.py` / `agent_registry.py` not modified
- [ ] `MEMORY.md` updated — this is exactly the kind of new decision/
      pattern `MEMORY.md` should record (a one-time migration-seed pattern
      distinct from self-healing defaults)
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any future Skill's grant defaults — explicitly not generalized.
- `list_agent_capabilities` (`T06`).
- `agents_router.py`'s dispatch fork (`T07`).

---

## Context / Notes

**Known, accepted consequence, not a defect:** because this seed reuses
`grant_skill_access`'s own idempotent "append if not already granted"
check inside `_load_state()` (which runs on every read, not just the very
first one), a real operator who later explicitly revokes one of these 3
migrated ids from one of the 4 named agents via the ordinary Skills
grant/revoke mechanism (`T03`) will find it silently re-granted on the
next `_load_state()` call. This is the literal behavior `ADR-028` point 5
directs ("idempotently granting each pair... reusing `grant_skill_access`'s
own already-idempotent behavior") and its Consequences section frames as
"a one-time, observable state change... idempotent thereafter" — do not
add a stricter one-time-only guard beyond what's written here; if this
wrinkle is later judged undesirable, that is a follow-up ADR decision, not
a silent addition to this task's own scope.

---

## Implementation Log

**2026-08-13 — Built and verified live** (same worktree setup as `T01`).

**Scope-internal judgement call, flagged for spot-check (not an
escalation — stays inside this task's own single file, no new
dependency/interface/ADR):** literally implementing "`_load_state()` seeds
by calling the existing `grant_skill_access(agent_id, skill_id)`" as
written would **infinite-recurse** — `grant_skill_access`'s own existing
body calls `_load_state()` internally, so the moment `_load_state()`'s new
seed loop calls `grant_skill_access`, that call re-enters `_load_state()`,
which runs the seed loop again, calling `grant_skill_access` again,
forever (a real stack-overflow crash, not a style nit — confirmed by
reasoning through the call graph before running it, not discovered by
crashing). Fixed with a minimal, backward-compatible internal seam:
`grant_skill_access` gained one new keyword-only parameter,
`_preloaded_state: dict | None = None` — when omitted (every real
external caller: `skills_router.py`'s grant endpoint, any other future
caller), behavior is byte-identical to before (loads state itself); the
migration seed loop is the only caller that passes `_preloaded_state`,
reusing the exact same idempotent "only append if not already granted"
logic without re-entering `_load_state()`. This still satisfies the
Constraint's own wording ("must reuse `grant_skill_access(agent_id,
skill_id)` itself, not hand-roll the append logic") — the append logic
itself is not duplicated anywhere; only a recursion guard was added.

**AC-01** (the 4 real agents are genuinely retrofitted, not just
theoretically grantable): backed up the real `.second-brain/
agent_skills.json` content (`{"todo-capture": [], "vault-qa":
["web-research"], "email-capture": []}` — real state, `vault-qa`'s
`web-research` grant is genuine pre-existing user data, not test debris),
then deleted the file for a genuine clean-slate test per this task's own
Test step 1. `skill_registry.list_agent_skills(agent_id)` for
`email-capture`/`meeting-capture`/`todo-capture`/`people-producer` each
returned `["view_last_run"]` with **zero explicit grant calls made in the
test**; `list_agent_skills("vault-qa")` returned `["ask_question",
"view_channel_status"]`. Inspected `.second-brain/agent_skills.json`
directly afterward — confirms the seed genuinely wrote real state, not
just an in-memory result. **PASS.**

**AC-01 (idempotency):** called `list_agent_skills` 3 more times (each
triggers a fresh `_load_state()`) — re-inspected the file: no duplicate
entries in any agent's assignments array, byte-identical between calls.
**PASS.**

Non-AC smoke check: `list_agent_skills("compass-expert")` and
`list_agent_skills("vault-filing-expert")` both returned `[]` — confirms
the mapping is exactly scoped, not a blanket grant. **PASS.**

**Real-data restoration:** re-granted `vault-qa`'s real, genuine
pre-existing `web-research` access (`grant_skill_access("vault-qa",
"web-research")`, idempotent) after the clean-slate test — this is a real
fact that predates this migration and is outside the 3-id/4-agent seed
mapping, so it needed restoring, unlike the seed grants themselves (which
are the intended, permanent, real production outcome of this task, not
test debris to revert). Final real `.second-brain/agent_skills.json`
state, confirmed by direct read: `email-capture: ["view_last_run"]`,
`meeting-capture: ["view_last_run"]`, `todo-capture: ["view_last_run"]`,
`people-producer: ["view_last_run"]`, `vault-qa: ["ask_question",
"view_channel_status", "web-research"]` — exactly the 4 named agents,
exactly the 3 named ids, `web-research` preserved.

`skill_tools.py` / `agent_registry.py` — confirmed untouched.

gate: flagged 2026-08-13 — the recursion-guard fix above, for human
spot-check (per Pipeline.md's "scope-internal judgement calls... make the
task `gate: flagged`" rule); not an `ESCALATIONS.md`-level event (no new
dependency, no shared-interface change visible to any other file, no ADR
deviation — the seam is additive/opt-in and every other real caller is
unaffected).
