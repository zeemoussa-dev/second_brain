---
id: REQ-SB-39-US-01-T04
title: knowledge_bootstrap.py — existing invoke_skill call gains trigger="hub_routed"
parent_story: REQ-SB-39-US-01
requirement_id: REQ-SB-39
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-39-US-01-T02]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-39-US-01-T04 — knowledge_bootstrap.py — `trigger="hub_routed"`

## Parent Story

- Story: [[REQ-SB-39-US-01]] — `../UserStories/REQ-SB-39-US-01-unify-capabilities-model-and-read-only-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-39 *Unify Agent Capabilities Under Skills*

---

## Objective

Update `knowledge_bootstrap.py`'s existing `skill_registry.invoke_skill(
research_expert_id, "web-research", {"query": subject})` call to satisfy
`T02`'s new required `trigger` parameter, passing `trigger="hub_routed"` —
the first real call site on either the Actions or Skills path to ever pass
this value (`ADR-028` point 2).

---

## Starting State → End State

**Before / Inputs:**
- `research_result = skill_registry.invoke_skill(research_expert_id,
  "web-research", {"query": subject})` — no `trigger` argument (now fails
  per `T02`'s breaking signature change).

**After / Outputs:**
- `research_result = skill_registry.invoke_skill(research_expert_id,
  "web-research", {"query": subject}, trigger="hub_routed")`.
- The surrounding `try/except` (the honest-failure funnel for a real
  external Anthropic-API failure) is unchanged — only the call's own
  arguments change.

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/knowledge_bootstrap.py` —
  the one existing `skill_registry.invoke_skill(...)` call.

---

## Constraints

- Inherits from parent story and `ADR-028` point 2's third bullet.
- `trigger="hub_routed"` — this call is itself the product of `ADR-017`'s
  Hub-routing match (hop1), the same semantic `ADR-020` point 3 already
  reserved `"hub_routed"` for on the Actions side.
- The existing `try/except Exception` around this call must remain
  unchanged — only the call's own keyword arguments change; do not alter
  the honest-failure-reporting behavior it already implements.
- Must NOT otherwise touch this file's branching/logic (hop1/hop2
  resolution, the `_record` calls, the return-status shapes).

---

## Tests

**Manual verification steps:**
1. Non-AC smoke check: python shell — call `skill_registry.invoke_skill(
   "vault-qa", "web-research", {"query": "test"}, trigger="hub_routed")`
   directly (any agent granted `web-research` works for this smoke
   check) — confirm it dispatches without a `TypeError` and returns the
   same result shape `web_research`'s own handler already produces
   (unchanged from before this task).
2. Non-AC smoke check: read the diff — confirm the only change in this
   file is the added `trigger="hub_routed"` keyword argument on the
   existing call; the `try/except` block and every other line are
   byte-identical to before.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] The existing `invoke_skill` call site gains `trigger="hub_routed"`
- [ ] No other logic in this file changes
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any other part of `knowledge_bootstrap.py`'s own bootstrap chain
  (hop1/hop2 resolution, `_record`, the Vault Filing Expert hand-off).

---

## Context / Notes

This call invokes `"web-research"`, not one of the 3 migrated read-only
ids this story's own Scenarios describe — no locked AC is tagged directly
to this task; its own Tests are non-AC smoke checks confirming the
required-`trigger`-parameter change doesn't regress this already-working
call site.

---

## Implementation Log

**2026-08-13 — Built and verified live** (same worktree setup as `T01`).

Added `trigger="hub_routed"` to the one existing call, no other change.
`git diff --stat` confirms exactly 1 line changed in this file.

Non-AC smoke check: `skill_registry.invoke_skill("vault-qa", "web-research",
{"query": "test"}, trigger="hub_routed")` (real, granted agent) — dispatched
with no `TypeError`, returned `web_research`'s own real, unchanged
honest-unavailable result shape (`vault-qa` is not currently linked to the
`anthropic-claude` Provider, so this is the same result this handler
already produced before this task, per `web_research`'s own Provider-
resolution logic — unrelated to this task's change). **PASS.**

Non-AC smoke check: `try/except` block and every other line confirmed
byte-identical to before via `git diff` (1 insertion, 1 deletion — the
one line gaining the keyword argument). **PASS.**

gate: clear 2026-08-13 — no new MUST-FLAG trigger.
