---
id: REQ-SB-39-US-02-T01
title: skill_registry.py — invoke_skill gains the two-axis working-mode gate; _dispatch_skill extracted as the ungated fallthrough primitive
parent_story: REQ-SB-39-US-02
requirement_id: REQ-SB-39
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-39-US-01-T01, REQ-SB-39-US-01-T02]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-39-US-02-T01 — `skill_registry.py` — two-axis gate + `_dispatch_skill`

## Parent Story

- Story: [[REQ-SB-39-US-02]] — `../UserStories/REQ-SB-39-US-02-unify-capabilities-working-mode-gate-and-mutating-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-39 *Unify Agent Capabilities Under Skills*

---

## Objective

Insert `ADR-020`'s own two-axis working-mode check into `invoke_skill` —
between the existing `has_skill_access` check and dispatch — keyed off
`skill_tools.SKILLS[skill_id]["mutates"]` and the new `trigger` parameter
(`REQ-SB-39-US-01-T02`). A Supervised + mutating invocation creates a
Pending Approval via `pending_approval_registry.create_pending_approval`,
storing `skill_id` in the existing `action_id` field and the invocation's
own `args` in the existing `payload` field. Extract the pre-gate dispatch
body into a new, raw, ungated `_dispatch_skill(agent_id, skill_id, args)`
primitive that the gate's own fallthrough calls (`ADR-029` points 2/3).

---

## Starting State → End State

**Before / Inputs** (the real shape after `REQ-SB-39-US-01-T02`, before this task):
```python
def invoke_skill(agent_id: str, skill_id: str, args: dict | None, trigger: str) -> dict:
    if skill_id not in skill_tools.SKILLS:
        return {"status": "unknown_skill"}
    if not has_skill_access(agent_id, skill_id):
        return {"status": "refused", "reason": "Agent does not have access to this skill."}
    handler = _SKILL_HANDLERS[skill_id]
    call_args = dict(args) if args else {}
    if "agent_id" in inspect.signature(handler).parameters:
        call_args["agent_id"] = agent_id
    if call_args:
        return handler(**call_args)
    return handler()
```
`trigger` is accepted but not yet branched on anywhere (`ADR-028` point 1).

**After / Outputs:**
```python
def _dispatch_skill(agent_id: str, skill_id: str, args: dict | None = None) -> dict:
    """Raw, ungated dispatch -- the exact pre-ADR-029 body of invoke_skill,
    extracted unchanged. Called both by invoke_skill's own post-gate
    fallthrough and by pending_approvals_router.py's Approve endpoint
    (T02), which deliberately bypasses the gate on Approve -- the
    approval itself is the authorization; re-entering the gate would
    find the agent still Supervised and defer forever (ADR-018 point 6,
    mirrored one layer over)."""
    handler = _SKILL_HANDLERS[skill_id]
    call_args = dict(args) if args else {}
    if "agent_id" in inspect.signature(handler).parameters:
        call_args["agent_id"] = agent_id
    if call_args:
        return handler(**call_args)
    return handler()


def invoke_skill(agent_id: str, skill_id: str, args: dict | None, trigger: str) -> dict:
    """... (existing docstring, plus:) Gained the two-axis working-mode
    gate (ADR-029 point 2), inserted AFTER the access check (so an
    agent never granted a skill is still refused before any pending
    record could be created) and BEFORE dispatch."""
    if skill_id not in skill_tools.SKILLS:
        return {"status": "unknown_skill"}
    if not has_skill_access(agent_id, skill_id):
        return {"status": "refused", "reason": "Agent does not have access to this skill."}

    mode = working_mode_registry.get_agent_working_mode(agent_id)

    if mode == "manual" and trigger == "hub_routed":
        return {
            "status": "refused",
            "reason": "This agent is in Manual mode — it does not act on another agent's request.",
        }

    mutates = skill_tools.SKILLS[skill_id].get("mutates", True)

    if mode == "supervised" and mutates:
        skill = skill_tools.SKILLS[skill_id]
        agent = agent_registry.get_agent(agent_id)
        agent_name = agent["name"] if agent else agent_id
        approval = pending_approval_registry.create_pending_approval(
            agent_id=agent_id,
            trigger=trigger,
            action_id=skill_id,
            description=f"{skill['name']} ({agent_name})",
            payload=args,
        )
        message = f"Proposed — {skill['name']}. Awaiting your approval."
        vault_writer.append_agent_history_entry(
            agent_id, "proposal", message, pending_approval_id=approval["id"],
        )
        return {"status": "pending", "message": message, "pending_approval_id": approval["id"]}

    return _dispatch_skill(agent_id, skill_id, args)
```

---

## Files to Modify

- `src/backend/app/business/skill_registry.py` — add `pending_approval_registry`,
  `working_mode_registry` imports; extract `_dispatch_skill`; add the gate
  inside `invoke_skill`.

---

## Constraints

- Inherits from parent story and `ADR-029` points 1–3.
- `_dispatch_skill`'s own body is byte-identical to `invoke_skill`'s
  pre-this-task dispatch logic (handler lookup, `agent_id` injection) —
  extracted, not rewritten.
- The `unknown_skill` / `refused`(access) checks stay exactly where they
  are, unchanged, BEFORE the new gate — access-grant is a genuinely
  different, prior axis from working mode (`ADR-029` point 2).
- The Manual+`hub_routed` refusal reuses the field name `"reason"` (not
  `"message"`) — `invoke_skill`'s own existing access-refused shape
  already uses `"reason"`, so `skills_router.py`'s existing
  `result.get("reason", ...)` 403-mapping needs no change and this task
  does not touch `skills_router.py`.
- `create_pending_approval` is called with `action_id=skill_id` (reusing
  the existing generic field, `ADR-021` point 5's own precedent) and
  `payload=args` (so Approve, `T02`, can replay them) — do NOT add a new
  `skill_id`-named field to the pending-approval record shape.
- The Supervised+mutating branch appends the same `"proposal"`
  history-entry kind `_invoke_action` already appends (`ADR-018`) — reuse
  `vault_writer.append_agent_history_entry` exactly as shown.
- Do NOT modify `skill_tools.py`, `agent_registry.py`, `agent_chat.py`,
  `agents_router.py`, or `knowledge_bootstrap.py` — this task's only file
  is `skill_registry.py`.
- `invoke_skill`'s signature is unchanged (`agent_id, skill_id, args,
  trigger`) — every existing caller continues to compile unchanged.

---

## Tests

**No real mutating Skill exists in the catalog yet at this point in the
build order** (migration is `T03`, which `depends_on` this task per
`ADR-029` point 8's atomicity discipline) — verify the gate mechanism
itself using a temporary, in-process monkeypatched synthetic mutating
skill, reverted after (established technique, `Implementation/
Learnings.md` 2026-08-12 SPRINT-018: "in-process monkeypatch of a real,
already-loaded dependency to induce a [state], instead of editing a file
outside the task's own scope").

**Manual verification steps:**
1. Setup (all steps, reverted at the end): python shell —
   `skill_tools.SKILLS["_test-mutating"] = {"id": "_test-mutating", "name": "Test Mutating", "mutates": True}`;
   `skill_registry._SKILL_HANDLERS["_test-mutating"] = lambda: {"available": True, "message": "ran"}`;
   `skill_registry.grant_skill_access("email-capture", "_test-mutating")`.
2. [REQ-SB-39-US-02-AC-01] `working_mode_registry.set_agent_working_mode("email-capture", "supervised")`;
   call `skill_registry.invoke_skill("email-capture", "_test-mutating", args=None, trigger="direct")`
   — confirm `{"status": "pending", "message": "Proposed — Test Mutating. Awaiting your approval.", "pending_approval_id": <id>}`;
   confirm `pending_approval_registry.get_pending_approval(<id>)` shows
   `action_id == "_test-mutating"`; confirm `vault_writer.load_agent_history("email-capture")`
   gained a new `"proposal"` entry naming "Test Mutating" and "awaiting
   your approval".
3. [REQ-SB-39-US-02-AC-03] `working_mode_registry.set_agent_working_mode("email-capture", "manual")`;
   call `invoke_skill("email-capture", "_test-mutating", args=None, trigger="hub_routed")`
   — confirm `{"status": "refused", "reason": "This agent is in Manual mode — it does not act on another agent's request."}`;
   confirm no new pending-approval record and no new history entry were created.
4. [REQ-SB-39-US-02-AC-04] Still Manual: `invoke_skill("email-capture", "_test-mutating", args=None, trigger="direct")`
   — confirm it executes immediately (`{"available": True, "message": "ran"}`
   from the stub handler, not a "pending"/"refused" shape). Then set
   `working_mode_registry.set_agent_working_mode("email-capture", "autonomous")`
   and call it again with `trigger="hub_routed"` — confirm it also
   executes immediately (Autonomous ignores trigger entirely).
5. [REQ-SB-39-US-02-AC-05] With `email-capture` back to `"supervised"`:
   grant the already-real, read-only `"web-research"` skill to
   `email-capture` too; call `invoke_skill("email-capture", "web-research", {"query": "x"}, trigger="direct")`
   — confirm it executes immediately (no pending record) — proves a
   read-only sibling is ungated regardless of the agent's own mutating
   skill's gating. Immediately re-invoke `"_test-mutating"` under the
   same Supervised mode — confirm it is STILL gated (a second "pending"
   result) — the two skills' gating is independent. Revoke `web-research`
   from `email-capture` afterward.
6. [REQ-SB-39-US-02-AC-08] Via the direct skill-invocation endpoint
   (`POST /agents/email-capture/skills/_test-mutating/invoke`, or the
   equivalent direct call into `skills_router.invoke_skill`) under
   Supervised mode — confirm the SAME `{"status": "pending", ...}` shape
   is returned (never an unconditional execution) — proves Scenario 8:
   the direct endpoint is never a bypass, by construction (it calls
   `skill_registry.invoke_skill` which now always gates).
7. Cleanup: `skill_registry.revoke_skill_access("email-capture", "_test-mutating")`;
   delete the `_test-mutating` entries from `skill_tools.SKILLS` and
   `skill_registry._SKILL_HANDLERS`; `working_mode_registry.set_agent_working_mode("email-capture", "autonomous")`
   (restore the real pre-test working mode).
8. Non-AC smoke check: `invoke_skill("email-capture", "unknown-id", args=None, trigger="direct")`
   — confirm `{"status": "unknown_skill"}`, unaffected by this task's own
   new gate code (still checked first).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `invoke_skill` gains the two-axis gate (Manual+hub_routed refuses;
      Supervised+mutating creates a pending approval; everything else
      falls through) inserted after the access check
- [ ] `_dispatch_skill(agent_id, skill_id, args)` extracted as a raw,
      ungated primitive, byte-identical pre-gate dispatch body
- [ ] `create_pending_approval` called with `action_id=skill_id`,
      `payload=args`; a `"proposal"` history entry appended
- [ ] `invoke_skill`'s signature unchanged; every existing caller compiles
      unchanged
- [ ] No file other than `skill_registry.py` modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Pending-Approvals Approve-endpoint branch that calls
  `_dispatch_skill` (`T02`).
- Migrating the 4 mutating Action ids into `skill_tools.SKILLS` (`T03`).
- The retrofit grant seed (`T04`).
- Any change to `skills_router.py`, `agents_router.py`, or
  `knowledge_bootstrap.py` — none of the 3 real callers need edits; this
  gate is reached automatically by all of them the moment it exists,
  which is the whole point of centralizing it here (`ADR-029` point 1).

---

## Context / Notes

**Atomicity (`ADR-029` point 8):** this task must land, and be verified,
BEFORE `T03`'s migration — `depends_on` encodes this. Until `T03` lands,
no real mutating Skill exists in the catalog, so this task's own gate is
inert in production (never yet exercised by a real caller with a real
mutating skill) but fully real and correct code, verified here via a
synthetic skill per the Tests above — the same "prove the mechanism
before the real data exists" approach `REQ-SB-39-US-01`'s own tasks did
not need (their read-only migration had no ordering hazard).

---

## Implementation Log

**2026-08-14 — Built and verified live** (direct Python-shell verification
against the real `.venv`, `PYTHONPATH=.` — no HTTP server needed for
`AC-01`/`AC-03`/`AC-04`/`AC-05`; `AC-08` exercised `skills_router.
invoke_skill` directly, the real function the HTTP endpoint calls
unmodified, per this project's own established "skip the HTTP layer when
it isn't load-bearing" pattern).

`skill_registry.py` gained the `pending_approval_registry`/
`working_mode_registry` imports, the two-axis gate inside `invoke_skill`
(inserted after the existing access check), and `_dispatch_skill`
extracted byte-identical from `invoke_skill`'s own pre-gate dispatch body.
No other file touched.

Setup/cleanup used the synthetic `_test-mutating` skill technique named in
this task's own Tests block, fully reverted after (confirmed post-hoc:
`_test-mutating` absent from `skill_tools.SKILLS`/`skill_registry.
_SKILL_HANDLERS`, `email-capture`'s working mode restored to its real
pre-test `"autonomous"`, `email-capture`'s real skill grants back to just
`view_last_run`). The 3 pending-approval records this test's own repeated
Supervised invocations created (`_test-mutating` has no real place to
resolve to once its `SKILLS`/handler entries are removed) were declined
directly via `pending_approval_registry.resolve_pending_approval` as an
extra cleanup step beyond this task's own named Cleanup list — avoids
leaving stray unresolvable pending records as debris (the exact class of
issue `SPRINT-021`'s own Learnings antipattern entry names).

- **[REQ-SB-39-US-02-AC-01]** Supervised + mutating → `{"status": "pending",
  "message": "Proposed — Test Mutating. Awaiting your approval.",
  "pending_approval_id": ...}`; the resolved pending record's own
  `action_id == "_test-mutating"`; a new `"proposal"`-kind history entry
  (`vault_writer.load_agent_history`'s own `"text"` field, not `"message"`
  — a test-script check bug on my own first pass, not a code defect;
  confirmed directly by reading the real appended entry) naming "Test
  Mutating" and "Awaiting your approval." **PASS.**
- **[REQ-SB-39-US-02-AC-03]** Manual + `trigger="hub_routed"` →
  `{"status": "refused", "reason": "This agent is in Manual mode — it
  does not act on another agent's request."}`; zero new pending-approval
  records, zero new history entries (both counted before/after). **PASS.**
- **[REQ-SB-39-US-02-AC-04]** Manual + `trigger="direct"` → executes
  immediately (`{"available": True, "message": "ran"}` from the stub
  handler, not a pending/refused shape); Autonomous + `trigger="hub_routed"`
  → also executes immediately (Autonomous ignores trigger entirely).
  **PASS.**
- **[REQ-SB-39-US-02-AC-05]** Supervised, `web-research` (real read-only
  skill) granted alongside `_test-mutating` → `web-research` executes
  immediately (no pending record — its own real body honestly reports
  unavailable since `email-capture` has no real `web-research`-backing
  Provider linked, but the KEY proof is `status != "pending"`, confirmed);
  immediately re-invoking `_test-mutating` under the same Supervised mode
  → still gated (a second `"pending"` result) — the two skills' gating is
  independently correct. `web-research` revoked from `email-capture`
  afterward (it was never previously granted to this agent). **PASS.**
- **[REQ-SB-39-US-02-AC-08]** Called `skills_router.invoke_skill(
  "email-capture", "_test-mutating", None)` directly — the real function
  `POST /agents/{agent_id}/skills/{skill_id}/invoke` calls unmodified —
  under Supervised mode → the SAME `{"status": "pending", ...}` shape,
  never an unconditional execution. Proves Scenario 8 by construction (the
  endpoint calls `skill_registry.invoke_skill`, which now always gates).
  **PASS.**
- Non-AC smoke check: `invoke_skill("email-capture", "unknown-id", ...)`
  → `{"status": "unknown_skill"}`, unaffected by the new gate code (still
  checked first). **PASS.**

All locked ACs this task owns (`AC-01`, `AC-03`, `AC-04`, `AC-05`, `AC-08`)
verified live. `invoke_skill`'s signature unchanged (confirmed by direct
diff — only its docstring and body grew); every existing caller
(`skills_router.py`, `agents_router.py::_invoke_capability`,
`knowledge_bootstrap.py`) compiles/imports unchanged (confirmed via `python
-c "import app.main"`-equivalent module import with no error, run as part
of this same verification session). No file other than `skill_registry.py`
modified.

gate: clear 2026-08-14 — no new MUST-FLAG trigger fired during this task's
own build (no new assumption, no ADR change, no escalation, all locked ACs
verified, no ambiguity). The parent story's own `gate: flagged` (ADR-029
creation, already recorded by the architect/decomposer) is a separate,
already-disclosed breadcrumb this task does not need to re-raise.
