---
id: REQ-SB-37-US-03-T01
title: skill_tools.py / skill_registry.py — write-to-vault-draft placeholder output Skill (mutates: True)
parent_story: REQ-SB-37-US-03
requirement_id: REQ-SB-37
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-031 created at /plan-tasks step 1) — carried forward, does not halt"
phase: P1
depends_on: [REQ-SB-39-US-01-T01, REQ-SB-39-US-01-T02, REQ-SB-39-US-02-T01]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-37-US-03-T01 — `skill_tools.py`/`skill_registry.py` — `write-to-vault-draft` placeholder Skill

## Parent Story

- Story: [[REQ-SB-37-US-03]] — `../UserStories/REQ-SB-37-US-03-agent-creation-producer-flow.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-37 *Agent Creation Wizard*

---

## Objective

Seed one minimal placeholder output Skill, `write-to-vault-draft`, into
`skill_tools.SKILLS` (`"mutates": True`) with a new zero-arg,
unconditionally honest-unavailable `@mcp_server.tool()` stub, registered in
`skill_registry.py`'s `_SKILL_HANDLERS` — per `ADR-031` point 2. Without
this, the Producer wizard's own output-Skill-grant step (`T02`/`T03`) has
nothing real, selectable, and honestly-labeled to grant or verify against.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-39-US-01-T01`/`T02` have landed `"mutates": bool` on every
  catalog entry and the `_SKILL_HANDLERS` dispatch-table pattern.
- `REQ-SB-39-US-02-T01` has landed `invoke_skill`'s two-axis working-mode
  gate (Manual+`hub_routed` refuses; Supervised+`mutates` defers to a
  Pending Approval; everything else falls through to `_dispatch_skill`),
  keyed off `skill_tools.SKILLS[skill_id]["mutates"]` — this task's own new
  entry is the first agent-facing, genuinely mutating catalog entry that is
  NOT one of `REQ-SB-39-US-02-T03`'s 4 migrated Actions; it must be gated
  by that same, already-real mechanism with zero new gating code.
- No `write-to-vault-draft` (or any other output/destination-shaped) entry
  exists anywhere in `skill_tools.SKILLS` today — confirmed by direct
  reading of the real catalog (`ADR-031`'s own Context).

**After / Outputs:**
- `skill_tools.SKILLS` gains one new entry, `"write-to-vault-draft"`, with
  `"mutates": True`.
- A new zero-arg `@mcp_server.tool()` function, `write_to_vault_draft`,
  unconditionally returns the same honest-unavailable shape every other
  stub Skill in this catalog returns.
- `skill_registry._SKILL_HANDLERS` gains the matching
  `"write-to-vault-draft": skill_tools.write_to_vault_draft` entry.

---

## Files to Modify

- `src/backend/app/business/skill_tools.py` — add the new `SKILLS` entry +
  stub function, alongside the existing entries (read the REAL current
  file first — by the time this task builds, `REQ-SB-39-US-01-T01` and
  `REQ-SB-39-US-02-T03` may already have grown the catalog from 2 to 9
  entries; this task adds the 10th):
  ```python
  "write-to-vault-draft": {
      "id": "write-to-vault-draft",
      "name": "Write to Vault (Draft)",
      "description": (
          "Given a Producer agent's own generated output, write it into "
          "the vault as a new draft note. Not yet available — no real "
          "write handler has been built for it (REQ-SB-37-US-03's own "
          "Non-Goals)."
      ),
      "mutates": True,
  },
  ```
  ```python
  @mcp_server.tool()
  def write_to_vault_draft() -> dict:
      """Given a Producer agent's own generated output, write it into the
      vault as a new draft note. Not yet available — no real write handler
      has been built for it (REQ-SB-37-US-03's own Non-Goals, ADR-031 point
      2). This stub always returns an honest "not available" response,
      never a fabricated or guessed result — mirrors
      diagram_understanding's exact honest-unavailable shape."""
      return {
          "available": False,
          "message": "This skill is not yet available — no real handler has been built for it.",
      }
  ```

- `src/backend/app/business/skill_registry.py` — add the matching
  `_SKILL_HANDLERS` entry (read the REAL current file first — by build
  time it may already carry 9 entries from `REQ-SB-39-US-01-T02`/
  `REQ-SB-39-US-02-T03`; this task adds the 10th, same local-dict pattern):
  ```python
  "write-to-vault-draft": skill_tools.write_to_vault_draft,
  ```

---

## Constraints

- Inherits from parent story and `ADR-031` point 2.
- The id MUST be exactly `write-to-vault-draft` (kebab-case, matching the
  existing hand-authored-Skill naming convention `diagram-understanding`/
  `web-research` use — NOT the underscore Action-id convention
  `REQ-SB-39-US-01`/`-US-02` reuse for their own *migrated* ids) — this is
  a brand-new Skill, not a migrated Action.
- `"mutates"` MUST be `True` — the only entry in the catalog besides the 4
  migrated mutating Actions to be `True`; never left to default/omitted.
- The handler is a zero-arg function, unconditionally honest-unavailable —
  no real write logic, no per-agent branching, mirrors
  `diagram_understanding`'s own existing body exactly.
- Do NOT design or implement any real write-to-vault behaviour — that is
  explicitly out of scope (the parent story's own Non-Goals / `ADR-031`
  point 2).
- Do NOT modify `agent_registry.py` or `agents_router.py` — the Producer
  `type` branch that grants/uses this Skill is `T02`'s own job.
- Do NOT modify the gate logic inside `invoke_skill` itself
  (`REQ-SB-39-US-02-T01`'s own scope) — this task only adds a catalog
  entry + handler; the existing gate reads `"mutates"` with zero
  special-casing.

---

## Tests

<!-- Pure catalog/dispatch-layer primitive, one below every locked AC's
own user/API-observable outcome — no locked AC is tagged here directly,
mirroring REQ-SB-37-US-01-T02's own precedent. Every locked AC that
touches this Skill is verified downstream, in T02/T03. -->

**Manual verification steps** (Python shell, from `src/backend`, backend
`.venv` active):

1. Non-AC smoke check: `from app.business import skill_tools`. Confirm
   `skill_tools.SKILLS["write-to-vault-draft"]` exists, with `"mutates":
   True` and non-empty `"name"`/`"description"`.
2. Non-AC smoke check: call `skill_tools.write_to_vault_draft()` directly —
   confirm it returns exactly `{"available": False, "message": "This
   skill is not yet available — no real handler has been built for it."}`
   — the same honest-unavailable shape as `skill_tools.
   diagram_understanding()`, never a fabricated result.
3. Non-AC smoke check: `from app.business import skill_registry`; call
   `skill_registry.grant_skill_access("people-producer",
   "write-to-vault-draft")` — confirm `True` (the pre-existing, unmodified
   `grant_skill_access` mechanism already works for the new id with zero
   special-casing). Ensure `people-producer`'s own working mode is
   `"autonomous"` (`working_mode_registry.set_agent_working_mode(
   "people-producer", "autonomous")` if needed), then call
   `skill_registry.invoke_skill("people-producer", "write-to-vault-draft",
   args=None, trigger="direct")` — confirm it dispatches to the new stub
   and returns the same honest-unavailable shape as step 2.
4. Non-AC smoke check (gate compatibility — confirms `ADR-031`'s own claim
   that this Skill is "gated by the working-mode two-axis check ADR-029
   already built, no new gating code needed"): `working_mode_registry.
   set_agent_working_mode("people-producer", "supervised")`; call
   `invoke_skill("people-producer", "write-to-vault-draft", args=None,
   trigger="direct")` again — confirm `{"status": "pending", ...}` (a real
   deferral, the same shape any other granted mutating Skill gets under
   Supervised mode), NOT an immediate stub call. Set the working mode back
   to `"autonomous"`, invoke once more — confirm it now executes
   immediately and returns the honest-unavailable shape again.
5. Clean-up: `skill_registry.revoke_skill_access("people-producer",
   "write-to-vault-draft")`; confirm `working_mode_registry.
   set_agent_working_mode("people-producer", "autonomous")` (restore the
   real pre-test working mode). Delete any pending-approval record created
   in step 4 if `pending_approval_registry` persisted one.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `SKILLS` gains a new entry, `"write-to-vault-draft"`, with
      `"mutates": True`
- [ ] A new zero-arg `@mcp_server.tool()` stub function is registered,
      unconditionally honest-unavailable, mirroring
      `diagram_understanding`'s exact body
- [ ] `_SKILL_HANDLERS` gains the matching entry
- [ ] A Supervised-mode invocation of this Skill defers via the existing
      two-axis gate, exactly like any other granted mutating Skill
- [ ] No file other than `skill_tools.py`/`skill_registry.py` modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- A real write-to-vault handler — not built this pass, honest stub only.
- `agents_router.py`'s own `POST /agents` `"producer"` type branch — `T02`.
- The wizard's own output-Skill single-select UI — `T03`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-031` created at
`/plan-tasks` step 1) — the human reviews `ADR-031` and this task
breakdown together; the pipeline does not halt, so this task proceeds to
`Ready` alongside the rest of the story.

Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-031` point 2;
`Implementation/Architecture/architecture.md` → "Amendment —
Producer-type flow (REQ-SB-37-US-03, ADR-031)". Read `skill_tools.py`'s
and `skill_registry.py`'s REAL current files before editing (not a stale
copy) — reconcile this task's own code sample against them if anything
has drifted since this task was written.

---

## Implementation Log

**2026-08-14, coder.** Read the REAL current `skill_tools.py`/
`skill_registry.py` first — the catalog had grown to 9 entries (as the
task's own Notes anticipated), matching the task's own diff target
exactly. Added the 10th `SKILLS` entry (`write-to-vault-draft`,
`mutates: True`), the matching zero-arg `@mcp_server.tool()` stub
(byte-identical honest-unavailable body to `diagram_understanding`), and
the matching `_SKILL_HANDLERS` entry — all per the task's own code
sample, no reconciliation needed beyond the entry count.

**Verification (Python shell, `.venv\Scripts\python.exe`, from
`src/backend`):**

- Non-AC smoke: `skill_tools.SKILLS["write-to-vault-draft"]` exists,
  `mutates: True`, non-empty `name`/`description`.
- Non-AC smoke: `write_to_vault_draft()` returns exactly `{"available":
  False, "message": "This skill is not yet available — no real handler
  has been built for it."}` — confirmed byte-identical to
  `diagram_understanding()`'s own return value.
- Non-AC smoke: `grant_skill_access("people-producer",
  "write-to-vault-draft")` → `True` with zero special-casing;
  `invoke_skill(..., trigger="direct")` under Autonomous → dispatches to
  the new stub, same honest-unavailable shape.
- **Gate-compatibility check (this task's own highest-value proof) —
  PASS.** Set `people-producer` Supervised, invoked again →
  `{"status": "pending", "message": "Proposed — Write to Vault (Draft).
  Awaiting your approval.", "pending_approval_id": "3919778c8c69"}` — a
  real deferral via the already-real two-axis gate, zero new gating code.
  Set back to Autonomous, invoked once more → executed immediately,
  honest-unavailable shape again.
- Cleanup: revoked the test grant, restored `people-producer`'s working
  mode to Autonomous, declined the one real pending-approval record this
  test created.

**No file other than `skill_tools.py`/`skill_registry.py` modified.**

`ADR-031` point 2's own claim ("gated by the working-mode two-axis check
`ADR-029` already built, no new gating code needed") is confirmed live,
not just architecturally asserted.

gate stays flagged (trigger-3, `ADR-031`, carried forward — human review
of the ADR + this task's own breakdown, not a build blocker) — no new
MUST-FLAG trigger fired this pass.
