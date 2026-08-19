---
id: REQ-SB-39-US-01-T03
title: skills_router.py — invoke endpoint passes trigger="direct" (server-hardcoded)
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

# REQ-SB-39-US-01-T03 — skills_router.py — `trigger="direct"`

## Parent Story

- Story: [[REQ-SB-39-US-01]] — `../UserStories/REQ-SB-39-US-01-unify-capabilities-model-and-read-only-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-39 *Unify Agent Capabilities Under Skills*

---

## Objective

Update `POST /agents/{agent_id}/skills/{skill_id}/invoke`'s call to
`skill_registry.invoke_skill` to satisfy `T02`'s new required `trigger`
parameter — hardcoded server-side to `"direct"`, never accepted from the
client request body (`ADR-028` point 2).

---

## Starting State → End State

**Before / Inputs:**
- `result = skill_registry.invoke_skill(agent_id, skill_id, args)` — no
  `trigger` argument (now fails per `T02`'s breaking signature change).

**After / Outputs:**
- `result = skill_registry.invoke_skill(agent_id, skill_id, args,
  trigger="direct")` — the literal string `"direct"`, never derived from
  `InvokeSkillBody`.

---

## Files to Modify

- `src/backend/app/api/skills_router.py` — the `invoke_skill` route
  handler's call to `skill_registry.invoke_skill`.

---

## Constraints

- Inherits from parent story and `ADR-028` point 2.
- `trigger="direct"` must be a hardcoded literal at the call site — do NOT
  add a `trigger` field to `InvokeSkillBody`; a caller must never be able
  to set it via the JSON request body (mirrors `POST /agents/{agent_id}/
  actions/{action_id}`'s own hardcoded `trigger="direct"`, and this
  codebase's standing "never trust a caller-supplied trust-level value"
  posture).
- No other behavior of this endpoint changes — the existing 404
  (`unknown_skill`) / 403 (`refused`) / pass-through-200 mapping stays
  identical.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-39-US-01-AC-02] Real HTTP (or direct FastAPI `TestClient`) call:
   grant a skill to an agent (e.g. `web-research` to any agent), then
   `POST /agents/{agent_id}/skills/web-research/invoke` — confirm a `200`
   with the expected result shape, proving the endpoint still round-trips
   correctly now that `trigger` is a required argument supplied by this
   task's own change.
2. Non-AC smoke check: confirm `InvokeSkillBody`'s schema has no `trigger`
   field — `POST .../invoke` with a body of `{"trigger": "chat"}` has zero
   effect on the resolved trigger value (still `"direct"` server-side,
   confirmed by inspecting the call `skill_registry.invoke_skill` actually
   receives, e.g. via a temporary print/breakpoint or a monkeypatched stub
   during this smoke check, reverted afterward).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `invoke_skill` call updated to pass `trigger="direct"`, hardcoded
      server-side
- [ ] `InvokeSkillBody` gains no `trigger` field
- [ ] 404 (`unknown_skill`) / 403 (`refused`) mapping unchanged
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any other endpoint in this router (`list_skills`, `list_agent_skills`,
  `grant_skill`, `revoke_skill` are all unaffected by `T02`'s signature
  change and are not touched here).

---

## Context / Notes

None beyond `ADR-028` point 2's own second bullet.

---

## Implementation Log

**2026-08-13 — Built and verified live** (same worktree setup as `T01`).

Changed the one line: `skill_registry.invoke_skill(agent_id, skill_id,
args, trigger="direct")` — hardcoded literal, `InvokeSkillBody` untouched
(still just `query: str | None = None`).

**AC-02:** Real HTTP round-trip via FastAPI `TestClient` against the real,
unmodified app — granted `web-research` to `vault-qa` (already granted in
real state; effectively a no-op), `POST /agents/vault-qa/skills/
web-research/invoke` with `{"query": "test query"}` → `200`, body
`{"available": False, "message": "This skill is not yet available — no
real handler has been built for it."}` — the expected shape. **PASS.**

Non-AC smoke check: `InvokeSkillBody.model_fields.keys()` → `{'query'}`
only, no `trigger` field. **PASS.**

Non-AC smoke check: in-process monkeypatch of
`skills_router_module.skill_registry.invoke_skill` (spy wrapper, delegates
to the real function, reverted immediately after) — `POST .../invoke`
with body `{"query": "test", "trigger": "chat"}` → the real
`skill_registry.invoke_skill` call was observed to receive `trigger=
"direct"` regardless of the client-supplied `"trigger": "chat"` JSON
field — confirms the client cannot override the server-hardcoded value.
**PASS.** Reverted the monkeypatch immediately after; `vault-qa`'s
`web-research` grant round-tripped (revoke + re-grant) back to its exact
original real state, confirmed via `.second-brain/agent_skills.json`
byte-identical to before this task's own live calls.

404 (`unknown_skill`) / 403 (`refused`) mapping — unchanged code path,
not touched by this edit.

gate: clear 2026-08-13 — no new MUST-FLAG trigger.
