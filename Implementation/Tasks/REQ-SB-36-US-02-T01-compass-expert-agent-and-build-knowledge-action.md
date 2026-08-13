---
id: REQ-SB-36-US-02-T01
title: New "compass-expert" pilot Expert agent entry + "build_knowledge" action definition
parent_story: REQ-SB-36-US-02
requirement_id: REQ-SB-36
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-023 created) — carried from the parent story; the human reviews ADR-023 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-21-US-01-T09]
created: 2026-08-12
updated: 2026-08-13
---

# REQ-SB-36-US-02-T01 — New `"compass-expert"` pilot agent + `"build_knowledge"` action

## Parent Story

- Story: [[REQ-SB-36-US-02]] — `../UserStories/REQ-SB-36-US-02-agent-knowledge-bootstrapping-delegated-research-chain.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-36 *Agent Knowledge Bootstrapping via Delegated Research*

---

## Objective

Add a new, plain, hardcoded `"compass-expert"` entry to `agent_registry.py`'s static `AGENTS` dict (`ADR-023` point 3, `ADR-011` point 2 unaffected) — the worked pilot example from the PRD's own Compass narrative — declaring one new action, `"build_knowledge"`, classified `"mutates": True` (it writes to the vault via the delegation chain), dispatched through the existing `_ACTION_HANDLERS`/`_invoke_action` funnel.

---

## Starting State → End State

**Before / Inputs:**
- `agent_registry.AGENTS` has 6 entries after `REQ-SB-35-US-01-T01` (including `"vault-filing-expert"`); no `"compass-expert"` entry exists.
- `REQ-SB-21-US-01-T09` has landed `agent_registry.py`'s `"mutates": bool` field convention + `get_action(agent_id, action_id)` helper (already applied to every pre-existing action).

**After / Outputs:**
- `agent_registry.AGENTS["compass-expert"]` exists: `type: "expert"`, one action, `"build_knowledge"`, `"mutates": True`, with real trigger phrases (e.g. `"build my knowledge"`, `"build knowledge"`, `"research my subject"`).
- `section_registry`/`working_mode_registry`/`provider_registry` all self-heal this new agent to their own defaults on first read — no code change needed.

---

## Files to Modify

- `src/backend/app/business/agent_registry.py` — add, inside `AGENTS`:
  ```python
      "compass-expert": {
          "name": "Compass Expert",
          "type": "expert",
          "settings": [
              {"key": "Subject", "value": "Compass"},
              {"key": "Starting knowledge", "value": "None — bootstrapped via delegated research"},
              {"key": "Vault scope", "value": "Not yet assigned (REQ-SB-29)"},
          ],
          "actions": [
              {
                  "id": "build_knowledge",
                  "label": "Build my knowledge",
                  "trigger_phrases": ["build my knowledge", "build knowledge", "research my subject"],
                  "mutates": True,
              },
          ],
      },
  ```
  (This is the general, reusable shape `ADR-023` point 3 names — "any future pilot Expert agent reuses the identical one-line registry addition." A future second pilot agent for a different subject would be an identical, separately-scoped new entry; not built here.)

---

## Constraints

- Inherits from parent story and `ADR-023` point 3.
- `agent_registry.py`'s own shape is unchanged — only one new agent entry, following `REQ-SB-21-US-01-T09`'s already-established `"mutates"` field convention on the new action.
- `"build_knowledge"` MUST be classified `"mutates": True` — it writes to the vault (via the Vault Filing Expert) once the chain completes, per `ADR-020`'s own fail-safe-conservative classification precedent.
- The handler dispatch entry itself (`_ACTION_HANDLERS`) is `T03`'s own scope, not this task's.

---

## Tests

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`, call `agent_registry.get_agent("compass-expert")`. Confirm it returns the new entry with one action, `"build_knowledge"`, `"mutates": True`. Confirm `agent_registry.get_action("compass-expert", "build_knowledge")` (the `REQ-SB-21-US-01-T09` helper) resolves it correctly.
2. Non-AC smoke check: confirm `agent_registry.list_agents()` now includes `"compass-expert"` alongside the other 6 entries, unchanged shape.
3. Non-AC smoke check: confirm `section_registry.get_agent_section("compass-expert")`/`working_mode_registry.get_agent_working_mode("compass-expert")`/`provider_registry.get_agent_provider("compass-expert")` all self-heal to their own real defaults with zero code change needed in any of those modules.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `agent_registry.AGENTS` gains exactly one new entry, `"compass-expert"`, `type: "expert"`, one action `"build_knowledge"` classified `"mutates": True`
- [x] `agent_registry.py`'s own shape is otherwise unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The `_ACTION_HANDLERS` dispatch entry, real chat/direct trigger wiring — `T03`.
- The orchestration logic itself — `T02`.
- Any UI — the existing Agent Settings/Actions/Chat/History panel already renders any registry agent generically.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-023` created at `/plan-tasks` step 1) — the human reviews `ADR-023` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Why this depends on `REQ-SB-21-US-01-T09`:** `T09` establishes the `"mutates": bool` field convention across every existing action; this task's own new action follows that established convention from the start (rather than being added inconsistently before the convention exists elsewhere in the file). Not a hard code dependency (the fail-safe-`True` default in `ADR-020`'s own gate would make this action safe even without the explicit field), but the right sequencing for schema consistency.

---

## Implementation Log

**Built 2026-08-12/13 (`/implement-sprint`, `SPRINT-024`).** Added the
`"compass-expert"` entry to `agent_registry.AGENTS` exactly per this
task's own sample — no other change to `agent_registry.py`. This task
carries no AC-IDs of its own (its 3 Tests steps are all non-AC smoke
checks); verified live against the real backend `.venv`:

1. `agent_registry.get_agent("compass-expert")` returns the new entry —
   `type: "expert"`, one action `"build_knowledge"`,
   `"mutates": True`, trigger phrases `["build my knowledge", "build
   knowledge", "research my subject"]`. `agent_registry.get_action(
   "compass-expert", "build_knowledge")` (the `REQ-SB-21-US-01-T09`
   helper) resolves it correctly. **PASS.**
2. `agent_registry.list_agents()` now returns 7 entries (was 6),
   including `"compass-expert"`, unchanged shape for every other entry.
   **PASS.**
3. `section_registry.get_agent_section("compass-expert")` self-healed to
   `{"id": "technical", "name": "Technical"}` (the first section, no
   assignment existed); `working_mode_registry.get_agent_working_mode(
   "compass-expert")` self-healed to `"autonomous"`;
   `provider_registry.get_agent_provider("compass-expert")` self-healed
   to the real `"compass"` Provider entry — all three with **zero code
   change** to any of those three modules, confirming
   `ADR-011` point 2's "agent identity stays hardcoded, everything else
   self-heals" precedent held for this new agent too. **PASS.**

No assumptions beyond the task's own already-recorded ones (`## Context
/ Notes`). `gate: flagged` unchanged — carried from `ADR-023`'s own open
human-review flag on the parent story; nothing new fired on this task.
