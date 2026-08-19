---
id: REQ-SB-39-US-02-T02
title: pending_approvals_router.py — Approve endpoint gains a skill_tools.SKILLS-aware branch calling _dispatch_skill directly
parent_story: REQ-SB-39-US-02
requirement_id: REQ-SB-39
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-39-US-02-T01]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-39-US-02-T02 — `pending_approvals_router.py` — skill Approve branch

## Parent Story

- Story: [[REQ-SB-39-US-02]] — `../UserStories/REQ-SB-39-US-02-unify-capabilities-working-mode-gate-and-mutating-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-39 *Unify Agent Capabilities Under Skills*

---

## Objective

Add one new branch to `POST /pending-approvals/{id}/approve`, checked
BEFORE the existing `_APPROVAL_HANDLERS` / generic `_execute_action`
chain: when `record["action_id"]` is a `skill_tools.SKILLS` member,
dispatch via `skill_registry._dispatch_skill` directly — never
`invoke_skill` (re-entering the gate would find the agent still
Supervised and defer forever, `ADR-018` point 6, `ADR-029` point 3).
Without this branch, a pending mutating-Skill approval would silently
fall into the existing `elif record["action_id"] is not None:` branch,
which resolves `_ACTION_HANDLERS.get((agent_id, skill_id))` — never a
match for a skill_id — and incorrectly report "This action is not yet
available." instead of actually running it.

---

## Starting State → End State

**Before / Inputs:**
```python
if record["action_id"] in _APPROVAL_HANDLERS:
    result = _APPROVAL_HANDLERS[record["action_id"]](record["payload"])
    outcome_message = f"Approved — filed at {result['path']}."
elif record["action_id"] is not None:
    result = _execute_action(record["agent_id"], record["action_id"])
    outcome_message = result["message"]
else:
    results = run_capture_for_agent(record["agent_id"])
    outcome_message = f"Approved — background step ran, {len(results)} result(s)."

resolved = pending_approval_registry.resolve_pending_approval(approval_id, "approved")
vault_writer.append_agent_history_entry(record["agent_id"], "run_event", outcome_message)
return _resolved(resolved)
```

**After / Outputs:**
```python
skip_history = False
if record["action_id"] in skill_tools.SKILLS:
    # A migrated mutating Skill's own pending approval (ADR-029 point 4)
    # -- checked FIRST, before _APPROVAL_HANDLERS, since a skill_id can
    # never collide with an _APPROVAL_HANDLERS key but this ordering is
    # the literal one ADR-029 point 4 specifies.
    result = skill_registry._dispatch_skill(record["agent_id"], record["action_id"], record["payload"])
    outcome_message = result.get("message", "Approved.")
    # A handler that already recorded its own run_event internally
    # (build_knowledge's own bootstrap_agent_knowledge chain, T03) signals
    # this the same way _run_build_knowledge's Action-path handler already
    # does (REQ-SB-36-US-02) -- avoids a duplicate entry.
    skip_history = bool(result.get("history_recorded"))
elif record["action_id"] in _APPROVAL_HANDLERS:
    result = _APPROVAL_HANDLERS[record["action_id"]](record["payload"])
    outcome_message = f"Approved — filed at {result['path']}."
elif record["action_id"] is not None:
    result = _execute_action(record["agent_id"], record["action_id"])
    outcome_message = result["message"]
else:
    results = run_capture_for_agent(record["agent_id"])
    outcome_message = f"Approved — background step ran, {len(results)} result(s)."

resolved = pending_approval_registry.resolve_pending_approval(approval_id, "approved")
if not skip_history:
    vault_writer.append_agent_history_entry(record["agent_id"], "run_event", outcome_message)
return _resolved(resolved)
```

---

## Files to Modify

- `src/backend/app/api/pending_approvals_router.py` — add `skill_registry`,
  `skill_tools` imports; add the new branch + `skip_history` guard on the
  Approve endpoint only (`decline_pending_approval` is unaffected).

---

## Constraints

- Inherits from parent story and `ADR-029` point 4.
- The new branch is checked FIRST (before `_APPROVAL_HANDLERS`), matching
  `ADR-029` point 4's own ordering — even though a real collision between
  a skill_id and an `_APPROVAL_HANDLERS` key (`propose_new_top_level_area`,
  `hermes_vault_write`) is not possible today.
- Calls `skill_registry._dispatch_skill` directly — NEVER
  `skill_registry.invoke_skill` — re-entering the gate on Approve would
  find the agent still Supervised and create a second pending record
  instead of ever running (mirrors this file's own existing
  `_execute_action`-not-`_invoke_action` precedent, `ADR-018` point 6).
- `skip_history` defaults `False` for every existing branch (unchanged
  behaviour for `_APPROVAL_HANDLERS`, plain action_id, and background) —
  only the new skill branch can set it `True`, and only when the
  dispatched handler's own result explicitly carries
  `"history_recorded": True` (`T03`'s `build_knowledge` handler is the
  one real case this pass; every other migrated handler omits the key,
  so `skip_history` stays `False` for them, preserving today's
  single-append behaviour).
- `decline_pending_approval` is NOT touched — declining a Skill's pending
  approval already works correctly unmodified (it never dispatches
  anything, `record["action_id"]`'s specific type is irrelevant to it).
- Do NOT modify `agents_router.py`'s own `_invoke_capability` translation
  (`REQ-SB-39-US-01-T07`) — the chat/direct-trigger dispatch path's own
  potential history-recording behaviour for `build_knowledge` specifically
  is out of this task's file scope; see this story's own `## Notes` for
  the disclosed finding.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-39-US-02-AC-02] Setup (reverted at the end, same synthetic
   technique as `T01`): `skill_tools.SKILLS["_test-mutating"] = {"id": "_test-mutating", "name": "Test Mutating", "mutates": True}`;
   `skill_registry._SKILL_HANDLERS["_test-mutating"] = lambda: {"available": True, "message": "ran for real"}`;
   `skill_registry.grant_skill_access("email-capture", "_test-mutating")`;
   `working_mode_registry.set_agent_working_mode("email-capture", "supervised")`.
   Call `skill_registry.invoke_skill("email-capture", "_test-mutating", args=None, trigger="direct")`
   — capture the returned `pending_approval_id`. Then `POST /pending-approvals/{id}/approve`
   (or the equivalent direct call to `approve_pending_approval`) — confirm
   the response's `status == "approved"`; confirm
   `vault_writer.load_agent_history("email-capture")` gained a new
   `run_event` entry with message `"ran for real"` (proving the real
   handler actually ran, not just a status flip); confirm a SECOND call
   to approve the same (now-resolved) id returns `409`.
2. Non-AC smoke check: confirm the `_APPROVAL_HANDLERS`/plain-action_id/
   background branches are byte-unchanged in behaviour — approve an
   existing Vault Filing Expert Tier-2 pending record (or inspect the
   diff directly) and confirm its own `outcome_message`/history-append
   behaviour is identical to before this task.
3. Cleanup: `skill_registry.revoke_skill_access("email-capture", "_test-mutating")`;
   remove the `_test-mutating` entries from `skill_tools.SKILLS` and
   `skill_registry._SKILL_HANDLERS`; restore `email-capture`'s working
   mode to `"autonomous"`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Approve endpoint gains a `skill_tools.SKILLS`-aware branch, checked
      before `_APPROVAL_HANDLERS`, calling `_dispatch_skill` directly
- [ ] `skip_history` guard added; defaults `False`; only the new branch
      can set it `True`, gated on the handler's own `history_recorded` key
- [ ] `_APPROVAL_HANDLERS` / plain action_id / background branches
      unchanged in observable behaviour
- [ ] `decline_pending_approval` not modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The gate/`_dispatch_skill` primitive itself (`T01`, a hard prerequisite).
- Migrating the 4 mutating ids into the catalog (`T03`).
- The retrofit grant seed (`T04`).
- `agents_router.py`'s own chat/direct dispatch-fork translation
  (`REQ-SB-39-US-01-T07`, already built, not reopened here).

---

## Context / Notes

None beyond `ADR-029` point 4's own reasoning and this story's own
`## Notes` on the disclosed `_invoke_capability`/`history_recorded`
wrinkle (out of this task's file scope, tracked there).

---

## Implementation Log

**2026-08-14 — Built and verified live** (direct Python-shell verification
against the real `.venv`; called `pending_approvals_router.
approve_pending_approval` directly — the real function `POST
/pending-approvals/{id}/approve` calls unmodified).

`pending_approvals_router.py` gained `skill_registry`/`skill_tools`
imports and the new `skill_tools.SKILLS`-aware branch (checked first) +
`skip_history` guard, exactly per this task's own Starting/End-State
sample. No other file touched.

- **[REQ-SB-39-US-02-AC-02]** Same synthetic `_test-mutating` setup as
  `T01` (Supervised, granted to `email-capture`). `invoke_skill` returned
  a `pending_approval_id`; `approve_pending_approval(id)` returned
  `status == "approved"`; `vault_writer.load_agent_history("email-capture")`
  gained a new `run_event` entry with `text == "ran for real"` (the real
  synthetic handler's own return message — proves the real handler
  actually ran via `_dispatch_skill`, not just a status flip). A second
  approve call on the same, now-resolved id raised `HTTPException(409,
  "Already approved")`. **PASS.**
- Non-AC smoke check: the `_APPROVAL_HANDLERS` (`propose_new_top_level_area`,
  `hermes_vault_write`) / plain-`action_id` / background branches are
  confirmed unchanged by direct diff inspection — the new skill branch was
  inserted as a new first `if`, `skip_history` defaults `False` and is
  only ever set `True` inside the new branch, so the final
  `if not skip_history: vault_writer.append_agent_history_entry(...)` call
  is behaviourally identical to the prior unconditional call for every
  pre-existing branch. **PASS** (verified by inspection, per this task's
  own Tests block allowance — "or inspect the diff directly").
- `decline_pending_approval` — confirmed untouched by direct diff read (no
  edit made to that function at all).

Cleanup confirmed: `_test-mutating` absent from `skill_tools.SKILLS`/
`skill_registry._SKILL_HANDLERS`; `email-capture`'s working mode restored
to its real pre-test `"autonomous"`; `_test-mutating` revoked from
`email-capture`'s real skill grants.

gate: clear 2026-08-14 — no new MUST-FLAG trigger fired (no new
assumption, no ADR change, no escalation, the one locked AC this task owns
verified, no ambiguity). Parent story's own `gate: flagged` is the
already-disclosed `ADR-029`-creation breadcrumb, not re-raised here.
