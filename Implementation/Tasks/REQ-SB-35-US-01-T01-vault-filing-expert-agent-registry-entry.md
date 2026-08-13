---
id: REQ-SB-35-US-01-T01
title: New "vault-filing-expert" registry agent entry + persisted Hub-routing keyword assignment
parent_story: REQ-SB-35-US-01
requirement_id: REQ-SB-35
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-021) carried from the parent story — human still reviews ADR-021 alongside this task breakdown. No new trigger fired during the build itself; all 3 non-AC smoke checks passed live."
phase: P1
depends_on: [REQ-SB-20-US-01-T02]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-35-US-01-T01 — New `"vault-filing-expert"` registry agent entry

## Parent Story

- Story: [[REQ-SB-35-US-01]] — `../UserStories/REQ-SB-35-US-01-vault-filing-expert.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-35 *Vault Filing Expert*

---

## Objective

Add a new, plain, hardcoded `"vault-filing-expert"` entry to `agent_registry.py`'s static `AGENTS` dict (`ADR-021` point 1, `ADR-011` point 2 unaffected — no shape change to `agent_registry.py` itself), then give it a real, persisted set of Hub-routing keywords so `REQ-SB-20-US-01`'s `route_cross_section_request(...)` can actually find it once that story's own routing node lands — the concrete prerequisite `T02`'s Scenario 7 composition and `REQ-SB-36-US-02`'s own Hop 2 both need.

---

## Starting State → End State

**Before / Inputs:**
- `agent_registry.AGENTS` has 5 entries (`email-capture`, `meeting-capture`, `todo-capture`, `people-producer`, `vault-qa`); no `"vault-filing-expert"` entry exists.
- `REQ-SB-20-US-01-T02` has landed `app/business/agent_keywords.py` — `set_agent_keywords(agent_id, keywords: list[str]) -> bool`, `get_agent_keywords(agent_id) -> list[str]` (self-heals any unassigned known agent to `[]`).

**After / Outputs:**
- `agent_registry.AGENTS["vault-filing-expert"]` exists: `{"name": "Vault Filing Expert", "type": "expert", "settings": [...], "actions": []}`. `actions: []` is deliberate — this agent is reached exclusively via direct business-function calls (`vault_filing_expert.determine_placement_and_file`, invoked by whichever orchestration produced the content — `ADR-021` point 1), never via the chat/direct-action `_ACTION_HANDLERS` funnel; it declares no actions of its own.
- `agent_keywords.get_agent_keywords("vault-filing-expert")` returns a real, non-empty, persisted keyword list (not a throwaway test value later reverted) — the standing configuration this agent needs to ever be found by Hub routing in production.
- `section_registry`/`working_mode_registry`/`provider_registry` all self-heal this new agent to their own defaults on first read (first Section, `"autonomous"`, `"compass"` respectively) — no code change needed in any of those modules, confirmed by their own existing self-healing `_load_state()` shape.

---

## Files to Modify

- `src/backend/app/business/agent_registry.py` — add, inside `AGENTS`, alongside the existing 5 entries:
  ```python
      "vault-filing-expert": {
          "name": "Vault Filing Expert",
          "type": "expert",
          "settings": [
              {"key": "Grounding", "value": "Beyond the Second Brain methodology + live vault structure"},
              {"key": "Reachable via", "value": "REQ-SB-20 Hub-to-Hub cross-Section routing only"},
              {"key": "New top-level area", "value": "Pauses for operator approval (Tier 2)"},
          ],
          "actions": [],
      },
  ```
  (Placed as the 6th entry, after `"vault-qa"` — dict insertion order does not affect `list_agents()`'s own output shape, which already returns `id`/`name`/`type` per entry regardless of position.)

---

## Constraints

- Inherits from parent story and `ADR-021` point 1.
- `agent_registry.py`'s own shape is unchanged — no new field, no new key beyond the one new agent entry. `AGENTS` stays fully static/hardcoded (`ADR-011` point 2).
- The keyword assignment step (see Tests) is a real, standing configuration change — not reverted at the end of this task's own verification, unlike a throwaway test fixture.
- Do not modify `section_registry.py`, `working_mode_registry.py`, `provider_registry.py`, or `agent_keywords.py` — this task only adds the new agent entry and calls the already-existing `agent_keywords.set_agent_keywords` once.

---

## Tests

<!-- This task carries no AC-tagged step of its own — Scenario 7
(REQ-SB-35-US-01-AC-07, "other agents consult the Vault Filing Expert via
Hub routing") is verified in T02, once route_cross_section_request
(REQ-SB-20-US-01-T05) exists and can be called against this task's own
real, persisted keyword assignment. Mirrors REQ-SB-21-US-01-T02's own
precedent for a foundational, non-AC-tagged registry task. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`, call `agent_registry.get_agent("vault-filing-expert")`. Confirm it returns the new entry with `"type": "expert"` and `"actions": []`. Confirm `agent_registry.list_agents()` now returns 6 entries, the 5 originals unchanged.
2. Non-AC smoke check: call `agent_keywords.set_agent_keywords("vault-filing-expert", ["filing", "tags", "vault placement", "categorize", "new category"])`. Confirm it returns `True` and `agent_keywords.get_agent_keywords("vault-filing-expert")` returns exactly that list — this is a real, standing assignment (do NOT revert it at the end of this task, unlike a throwaway verification fixture).
3. Non-AC smoke check: confirm `section_registry.get_agent_section("vault-filing-expert")` self-heals to the first known Section (no code change needed — direct confirmation the existing self-healing mechanism covers this new agent id) and `working_mode_registry.get_agent_working_mode("vault-filing-expert")` (once `REQ-SB-21-US-01-T02` has landed) self-heals to `"autonomous"`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `agent_registry.AGENTS` gains exactly one new entry, `"vault-filing-expert"`, `type: "expert"`, `actions: []`
- [x] `agent_registry.py`'s own shape (fields, dict structure) is otherwise unchanged
- [x] `agent_keywords.set_agent_keywords("vault-filing-expert", [...])` is called once, real and persisted, not reverted
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The placement/write logic itself — `T02` (`vault_filing_expert.py`).
- Tier-2 approval resolution — `T03`.
- Any UI — the Agent Settings/Actions/Chat/History panel already renders any registry agent generically (see the parent story's own `## Affected Screens`).

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-021` created at `/plan-tasks` step 1) — the human reviews `ADR-021` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Why `actions: []`, not a declared action:** the Vault Filing Expert's own placement/write capability is reached by direct business-function call (`determine_placement_and_file`), composed by whichever code invoked it (`REQ-SB-36-US-02`'s own orchestration, or a future caller) — never a chat trigger phrase or an Available-Actions button on this agent's own panel. This mirrors `ADR-021`'s own point 3 framing ("this code path never reaches `agents_router.py::_invoke_action`'s funnel at all") one level up: there is no action to declare because there is no human-facing trigger for this agent's own capability.

**Why the keyword assignment happens here, not deferred to a task's own throwaway `Tests`:** unlike a verification fixture that gets set then reverted, this agent's own discoverability via Hub routing is a real, standing product requirement (Scenario 7) — the keywords must actually persist past this task's own build for the capability to work in the running application, not just during this task's own test pass.

---

## Implementation Log

**Built 2026-08-12 (coder, `/implement-sprint`, `SPRINT-023`).** Added the
`"vault-filing-expert"` entry to `agent_registry.AGENTS` verbatim per this
task's own code block (6th entry, `type: "expert"`, `actions: []`).

This task carries no locked AC of its own (per its own `## Tests` note —
`AC-07` is verified in `T02`, once `route_cross_section_request` exists).
All 3 non-AC smoke checks run live against the real backend `.venv`/vault:

1. `agent_registry.get_agent("vault-filing-expert")` → the new entry,
   `type: "expert"`, `actions: []`. `agent_registry.list_agents()` → 6
   entries, the 5 originals unchanged (`email-capture`, `meeting-capture`,
   `todo-capture`, `people-producer`, `vault-qa`, `vault-filing-expert`).
   **PASS.**
2. `agent_keywords.set_agent_keywords("vault-filing-expert", ["filing",
   "tags", "vault placement", "categorize", "new category"])` → returned
   that exact list (not literally `True` — the real, already-`Done`
   `set_agent_keywords` returns the new list itself, per its own real
   code read directly before this task's build; the task's own Tests
   text assumed a bare `True` return, a stale expectation, not a defect —
   logged here as a scope-internal observation, not a deviation from any
   locked AC since this step carries none). `agent_keywords.
   get_agent_keywords("vault-filing-expert")` → the identical list,
   persisted. This is a real, standing assignment — NOT reverted. **PASS.**
3. `section_registry.get_agent_section("vault-filing-expert")` self-healed
   to `{"id": "technical", "name": "Technical"}` (the real seed's first
   Section) with zero code change. `working_mode_registry.
   get_agent_working_mode("vault-filing-expert")` self-healed to
   `"autonomous"` with zero code change (`REQ-SB-21-US-01-T02`, already
   `Done`, confirmed present in the real source tree). **PASS.**

No new dependency, no shared-interface change, no ADR deviation, no
unanticipated file. `gate: flagged` carried unchanged from the parent
story/`ADR-021` (trigger-3) — no new trigger fired by this task's own
build.
