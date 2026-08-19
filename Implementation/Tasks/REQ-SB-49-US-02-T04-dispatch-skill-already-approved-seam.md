---
id: REQ-SB-49-US-02-T04
title: _dispatch_skill(..., already_approved) seam + Approve-endpoint wiring
parent_story: REQ-SB-49-US-02
requirement_id: REQ-SB-49
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-038 created) — carried from the parent story; the human reviews ADR-038 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-49-US-02-T02]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-49-US-02-T04 — `_dispatch_skill(..., already_approved)` Seam + Approve-Endpoint Wiring

## Parent Story

- Story: [[REQ-SB-49-US-02]] — `../UserStories/REQ-SB-49-US-02-cockpit-person-mention-proposed-note-edit.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-49 *Cockpit @Mentions*

---

## Objective

Give `skill_registry._dispatch_skill` one new, opt-in keyword, `already_approved: bool = False`, forwarded to a handler via the SAME signature-introspection seam that already auto-injects `agent_id` (`ADR-038` point 7) — a no-op for every one of the other 11 existing handlers, none of which declare this parameter. Wire `pending_approvals_router.py`'s Approve branch for a migrated Skill to pass `already_approved=True` explicitly on its one `_dispatch_skill` call site — the ONLY real call site in this codebase that ever passes `True`.

---

## Starting State → End State

**Before / Inputs:**
- `skill_registry._dispatch_skill(agent_id, skill_id, args=None)` — real, current body (confirmed by direct reading):
  ```python
  def _dispatch_skill(agent_id: str, skill_id: str, args: dict | None = None) -> dict:
      handler = _SKILL_HANDLERS[skill_id]
      call_args = dict(args) if args else {}
      if "agent_id" in inspect.signature(handler).parameters:
          call_args["agent_id"] = agent_id
      if call_args:
          return handler(**call_args)
      return handler()
  ```
- `pending_approvals_router.py`'s Approve branch for a migrated Skill (real, current, confirmed by direct reading):
  ```python
  result = skill_registry._dispatch_skill(record["agent_id"], record["action_id"], record["payload"])
  ```
- `T02` has landed `propose_person_note_update`, whose own handler signature declares `already_approved: bool = False`.

**After / Outputs:**
- `_dispatch_skill` gains the `already_approved` parameter and forwards it via the same introspection pattern as `agent_id`.
- The ONE `pending_approvals_router.py` call site above passes `already_approved=True` explicitly.
- `propose_person_note_update`'s handler (`T02`) now genuinely reachable with `already_approved=True` only via a just-approved Supervised Pending Approval — every other of the 11 existing handlers is provably unaffected (none declare the parameter).

---

## Files to Modify

- `src/backend/app/business/skill_registry.py` — extend `_dispatch_skill`:
  ```python
  def _dispatch_skill(
      agent_id: str, skill_id: str, args: dict | None = None, *, already_approved: bool = False,
  ) -> dict:
      """Raw, ungated dispatch -- the exact pre-REQ-SB-39-US-02 body of
      invoke_skill, extracted unchanged (ADR-029 point 3). Called both by
      invoke_skill's own post-gate fallthrough, above, and by
      pending_approvals_router.py's Approve endpoint (REQ-SB-39-US-02-T02),
      which deliberately bypasses the gate on Approve -- the approval
      itself is the authorization; re-entering the gate would find the
      agent still Supervised and defer forever (ADR-018 point 6, mirrored
      one layer over).

      already_approved is a new, keyword-only, opt-in flag (ADR-038 point
      7, REQ-SB-49-US-02) forwarded to a handler via the SAME signature-
      introspection seam that already forwards agent_id -- a no-op for
      every handler that does not declare it (confirmed by direct reading:
      none of the 11 pre-existing handlers declare this parameter).
      pending_approvals_router.py's Approve branch passes True explicitly
      on its one call site (the ONLY real caller that ever does);
      invoke_skill's own Manual/Autonomous fallthrough (below) omits it,
      leaving it at its default False."""
      handler = _SKILL_HANDLERS[skill_id]
      call_args = dict(args) if args else {}
      if "agent_id" in inspect.signature(handler).parameters:
          call_args["agent_id"] = agent_id
      if "already_approved" in inspect.signature(handler).parameters:
          call_args["already_approved"] = already_approved
      if call_args:
          return handler(**call_args)
      return handler()
  ```
  (`invoke_skill`'s own Manual/Autonomous fallthrough line, `return _dispatch_skill(agent_id, skill_id, args)`, is left completely unchanged — it never passes `already_approved`, so the parameter's own default `False` applies there, exactly as `ADR-038` point 7 specifies.)
- `src/backend/app/api/pending_approvals_router.py` — the ONE line inside the `if record["action_id"] in skill_tools.SKILLS:` branch:
  ```python
  result = skill_registry._dispatch_skill(
      record["agent_id"], record["action_id"], record["payload"], already_approved=True,
  )
  ```
  (Every other line of `approve_pending_approval` — the `_APPROVAL_HANDLERS`/`_execute_action`/background-proposal branches, `skip_history`, `resolve_pending_approval`, the history-entry append — is left completely unchanged.)

---

## Constraints

- Inherits from parent story.
- `already_approved` is keyword-only (`*,` before it) and defaults to `False` — no positional-call-site breakage for any of the 11 existing handlers or the 3 existing `_dispatch_skill` callers.
- The ONE explicit `already_approved=True` call site is `pending_approvals_router.py`'s migrated-Skill Approve branch — no other call site (in this task or anywhere else) should ever pass `True`.
- `invoke_skill`'s own gate logic (the two `if` branches, the Supervised+`mutates` Pending-Approval creation) is NOT touched by this task — this task only extends `_dispatch_skill`'s own signature/forwarding.
- Do not alter `_dispatch_skill`'s existing `agent_id`-forwarding line — add the new `already_approved`-forwarding check alongside it, not in place of it.

---

## Tests

<!-- AC-02 (Supervised: Approve -> real write; Decline -> unchanged) is
fully verifiable here directly against invoke_skill/the real Approve
endpoint, without needing T05's graph/LLM layer -- Scenario 2's own
Gherkin describes exactly this call chain. -->

**Manual verification steps:**

1. **[REQ-SB-49-US-02-AC-02]** In a Python shell against the backend `.venv` (real vault, real pending-approval store). Set `people-producer` to Supervised working mode. Pick a real, existing Person note; read and record its current body text. Call `skill_registry.invoke_skill("people-producer", "propose_person_note_update", args={"note_path": "<that note's real path>", "person_name": "<its real name>", "instruction": "test instruction — supervised approve check"}, trigger="cockpit_mention")`. Confirm the return is `{"status": "pending", "pending_approval_id": ..., ...}` (the existing, unmodified `ADR-029` Supervised branch). Confirm the Person note is still byte-for-byte unchanged. Call `POST /pending-approvals/{that id}/approve` (via `TestClient`, no lifespan, or a real running server). Confirm the response resolves `status: "approved"`. Re-read the Person note — confirm its body now ends with a new `- test instruction — supervised approve check` line, written by the `already_approved=True` branch, and confirm this happened "and not before" (the note was unchanged immediately after the `invoke_skill` call, only changed after the explicit Approve).
2. **[REQ-SB-49-US-02-AC-02]** Repeat step 1's `invoke_skill` call once more (fresh instruction text, e.g. "test instruction — supervised decline check") to produce a second real pending approval. Record the Person note's body immediately after this call. Call `POST /pending-approvals/{that id}/decline`. Confirm the response resolves `status: "declined"`. Re-read the Person note — confirm its body is byte-for-byte unchanged from immediately before the decline call (and therefore never gained the "decline check" line at all).
3. Non-AC regression check: confirm a pre-existing migrated mutating Skill's own Approve flow is unaffected — call `invoke_skill(<an agent with rebuild_person_note access>, "rebuild_person_note", None, trigger="direct")` in Supervised mode, confirm it still creates a pending approval and Approve still dispatches correctly (its own handler does not declare `already_approved`, so this task's new forwarding is a provable no-op for it).
4. Static check: grep `src/backend/app` for `already_approved` — confirm it appears only in `skill_registry.py` (`_dispatch_skill`'s signature/forwarding) and `pending_approvals_router.py` (the one explicit `=True` call site) and `skill_tools.py` (`T02`'s handler's own parameter declaration) — never a second, independent introduction.
5. Clean-up: leave both test Person-note edits from steps 1/2 in the vault as a disclosed, harmless artefact (or manually strip the one appended test line from step 1 if a clean state is preferred before the next task's own live verification reuses the same note) — record whichever choice was made in the Implementation Log.

**Automated tests:** `n/a — no backend test runner scaffolded yet (no pytest suite exists under src/backend as of this task)`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-02** (Scenario 2) — Supervised mode: a pending approval is created and the Person note is untouched until Approve; Approve writes the real edit; Decline leaves the note completely unchanged
- [ ] `_dispatch_skill` gains the keyword-only `already_approved: bool = False`, forwarded via signature introspection exactly like `agent_id`
- [ ] `pending_approvals_router.py`'s migrated-Skill Approve branch passes `already_approved=True` on its one call site, no other line changed
- [ ] Every one of the 11 pre-existing `_SKILL_HANDLERS` entries provably unaffected (none declare `already_approved`)
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- `invoke_skill`'s own gate logic (the two `if` branches) — untouched, out of scope for this task.
- The `propose_person_note_update` handler's own body — `T02`'s scope; this task only makes the seam that lets `already_approved` ever reach it as `True`.
- The `"cockpit_mention"` trigger literal itself — `T03`'s scope (this task's own Tests pass it as a plain string regardless).
- The real graph-level flow that produces a Manual/Autonomous `"proposed"` outcome — `T05`'s scope; this task's own Tests exercise the Supervised path only (`AC-02`), which does not need the graph/LLM layer at all.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-038` created at `/plan-tasks` step 1, carried) — the human reviews `ADR-038` and the task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Why `depends_on: [T02]` and not `[T02, T03]`:** this task's own `AC-02` verification calls `invoke_skill(..., trigger="cockpit_mention")` directly — a plain string, not gated by whether `T03`'s `Literal[...]` widening has landed yet (Python does not enforce `Literal` at runtime, confirmed directly in `T03`'s own Context). `T02` is the one real prerequisite: without `propose_person_note_update` registered and handler-declared, there is no real Skill for this seam to exercise at all.

**Read the REAL current `skill_registry.py`/`pending_approvals_router.py` first** — both already read in full for this decomposer pass; re-confirm at build time. This task's diff is additive/narrow: one new parameter + one new forwarding check on `_dispatch_skill`, one call-site edit in `pending_approvals_router.py`. No other function in either file is touched.

---

## Implementation Log

Built exactly as specced: `_dispatch_skill` gained the keyword-only
`already_approved: bool = False`, forwarded via the same
signature-introspection seam that already forwards `agent_id`;
`pending_approvals_router.py`'s one migrated-Skill Approve call site now
passes `already_approved=True` explicitly. No other line of either
function changed.

**Verification — Python shell + a real running server (`http://127.0.0.1:
8001`) for the Approve/Decline HTTP calls, real vault, real
`people-producer` agent set to Supervised mode:**
- **AC-02** — PASS, both branches:
  - Approve: `invoke_skill(..., trigger="cockpit_mention")` in Supervised
    mode returned `{"status": "pending", "pending_approval_id": ...}`;
    the real Person note was confirmed byte-for-byte unchanged
    immediately after (before Approve). `POST /pending-approvals/{id}/
    approve` against the real running server resolved `status:
    "approved"`, and the real Person note was then confirmed to end with
    the approved instruction line — "and not before."
  - Decline: a second real Supervised dispatch produced a second real
    pending approval; `POST /pending-approvals/{id}/decline` resolved
    `status: "declined"`; the real Person note was confirmed
    byte-for-byte unchanged from immediately before the decline call.
- Regression check — PASS: `invoke_skill(<agent with rebuild_person_note
  access>, "rebuild_person_note", None, trigger="direct")` in Supervised
  mode still creates a pending approval and Approve still dispatches
  correctly — `rebuild_person_note`'s own handler does not declare
  `already_approved`, confirming this task's new forwarding is a provable
  no-op for it.
- Static check — PASS: `already_approved` greps to exactly
  `skill_registry.py` (signature/forwarding), `pending_approvals_router.py`
  (the one `=True` call site), and `skill_tools.py` (`T02`'s handler's own
  parameter declaration) — no second, independent introduction.
- Clean-up: the one real write from the Approve-path test was reverted
  (test line stripped, byte-confirmed back to the pre-test body); working
  mode restored afterward.

gate: flagged (carried, trigger-3 — `ADR-038`) 2026-08-14 — no NEW
coder-owned trigger fired (additive, keyword-only, default-`False`
parameter; no gate-logic branch touched; no `ESCALATIONS.md` entry;
AC-02 verified live with a real, observed outcome on both Approve and
Decline).
