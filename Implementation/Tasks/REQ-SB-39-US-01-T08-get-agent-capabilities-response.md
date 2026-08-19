---
id: REQ-SB-39-US-01-T08
title: agents_router.py — get_agent() response "actions" -> "capabilities" (sourced from list_agent_capabilities)
parent_story: REQ-SB-39-US-01
requirement_id: REQ-SB-39
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-39-US-01-T06, REQ-SB-39-US-01-T07]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-39-US-01-T08 — agents_router.py — `get_agent()` → `"capabilities"`

## Parent Story

- Story: [[REQ-SB-39-US-01]] — `../UserStories/REQ-SB-39-US-01-unify-capabilities-model-and-read-only-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-39 *Unify Agent Capabilities Under Skills*

---

## Objective

Change `get_agent()`'s response shape from a bare `"actions": [...]`
(sourced directly from `agent_registry.py`'s array) to `"capabilities":
[...]` (sourced from `T06`'s `skill_registry.list_agent_capabilities`) —
the `"actions"` key is **removed**, not kept alongside the new key
(`ADR-028` point 6; Scenario 7's own "no separate Actions section shown
alongside a Skills section").

---

## Starting State → End State

**Before / Inputs:**
```python
"actions": [{"id": a["id"], "label": a["label"]} for a in agent["actions"]],
```

**After / Outputs:**
```python
"capabilities": skill_registry.list_agent_capabilities(agent_id),
```
— `"actions"` is fully removed from the response dict, not left present
alongside `"capabilities"`.

---

## Files to Modify

- `src/backend/app/api/agents_router.py` — `get_agent()`'s response dict.

---

## Constraints

- Inherits from parent story and `ADR-028` point 6.
- `"actions"` key removed entirely — enforced at the response-shape
  level (`"actions" not in response`), not just by convention.
- Sourced from `skill_registry.list_agent_capabilities(agent_id)`, not
  reimplemented inline.
- Every other field in `get_agent()`'s response (`id`, `name`, `type`,
  `settings`, `section_id`, `section_name`, `provider_id`,
  `provider_name`, `provider_available`, `keywords`, `working_mode`)
  unchanged.
- `update_agent_assignment` (`PATCH /agents/{agent_id}`) delegates to
  `get_agent()` for its own response — confirm it picks up the new shape
  automatically, no separate edit needed there.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-39-US-01-AC-07] `GET /agents/vault-qa` (post-retrofit, so it
   carries a mix of migrated Skills) — confirm the response has a
   `"capabilities"` key (not `"actions"`), and it includes every
   capability the agent currently has access to (`ask_question`,
   `view_channel_status`).
2. [REQ-SB-39-US-01-AC-07] Confirm the response has **no `"actions"` key
   at all** — `"actions" not in response.json()` — not just an empty
   list.
3. Non-AC smoke check: `PATCH /agents/vault-qa` with a trivial no-op
   update (e.g. re-set its current `working_mode`) — confirm its own
   response also reflects the `"capabilities"` shape (delegates to
   `get_agent()` correctly, no stale code path left behind).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `get_agent()` response has `"capabilities"` (not `"actions"`)
- [ ] `"actions"` key fully removed
- [ ] `update_agent_assignment`'s response (delegates to `get_agent`)
      reflects the same shape
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The frontend consumer of this response shape (`T09`).

---

## Context / Notes

This is a real, breaking internal interface change — `ADR-028`'s own
Consequences section confirms `AgentDetailPanel.tsx` (`T09`) is the only
real consumer (no external caller, including Hermes, reaches this
endpoint), so changing it in the same pass (rather than an additive/
deprecation period) is safe.

---

## Implementation Log

**2026-08-13 — Built and verified live** (same worktree setup as `T01`).

Replaced `get_agent()`'s `"actions": [...]` line with `"capabilities":
skill_registry.list_agent_capabilities(agent_id)`. `update_agent_
assignment` (`PATCH`) needed zero edit — it already delegates to
`get_agent(agent_id)` for its own response.

**AC-07:** Real HTTP via FastAPI `TestClient` — `GET /agents/vault-qa`
(post-retrofit, mixed migrated-Skill capabilities) → `200`, response has
a `"capabilities"` key including `ask_question`/`view_channel_status`
(plus the pre-existing `web-research` grant). **PASS.**

**AC-07:** `"actions" not in response.json()` — confirmed True, not just
an empty list. **PASS.**

Non-AC smoke check: `PATCH /agents/vault-qa` with a trivial no-op
`working_mode` re-set → its own response also carries `"capabilities"`,
no `"actions"` — confirms `update_agent_assignment` correctly delegates,
no stale code path left behind. **PASS.**

gate: clear 2026-08-13 — no new MUST-FLAG trigger.
