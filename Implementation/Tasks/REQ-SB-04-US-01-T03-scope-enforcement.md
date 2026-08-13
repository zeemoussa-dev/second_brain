---
id: REQ-SB-04-US-01-T03
title: "⚠️ BLOCKED — real scope enforcement (`_is_within_assigned_scope`), Scenarios 1/2"
parent_story: REQ-SB-04-US-01
requirement_id: REQ-SB-04
type: backend
status: Draft
gate: flagged
gate_reason: "Individually flagged, mirroring ESC-011's/ESC-018's own precedent exactly. Blocked on REQ-SB-29-US-01, which has not been decomposed at all (status: Draft, zero task files exist) — no real task id exists anywhere to depend on. Logged as ESCALATIONS.md -> ESC-026 (new). Do not start until REQ-SB-29-US-01 has shipped its own vault-scope-assignment mechanism and a follow-up decomposer pass replaces this depends_on: [] with the real task id."
phase: P1
depends_on: []
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-04-US-01-T03 — ⚠️ BLOCKED — real scope enforcement

## ⚠️ BLOCKED — DO NOT START

This task cannot be built or verified until `REQ-SB-29-US-01`
(Agent-to-Tag/Folder Scoping) ships its own real vault-scope-assignment
mechanism. As of this decomposition pass, `REQ-SB-29-US-01` is `status:
Draft`, `gate: clear`, and **has not been decomposed into tasks at all** —
zero `REQ-SB-29-US-01-T*.md` files exist anywhere in
`Implementation/Tasks/` (confirmed by direct glob at decomposition time).
There is no real task id to depend on. `depends_on: []` here is a
deliberate, honest placeholder — never fabricate a task id that does not
exist, mirroring `ESC-011`'s/`ESC-018`'s own established precedent
(`REQ-SB-27-US-01-T02`, `REQ-SB-36-US-02-T04`) exactly.

**Resolving this block:** once `REQ-SB-29-US-01` reaches `status: Ready`
(its own decomposer pass has run and produced real task ids for its
vault-scope-assignment mechanism), a follow-up decomposer pass on this
story replaces this task's own `depends_on: []` with the real id(s), and
this task's own `status`/`gate` are reset to ordinary lockstep with the
rest of this story. See `ESCALATIONS.md` → `ESC-026`.

---

## Parent Story

- Story: [[REQ-SB-04-US-01]] — `../UserStories/REQ-SB-04-US-01-agent-vault-write-access.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-04 *Agent Vault Write Access*

---

## Objective

Once `REQ-SB-29-US-01` ships a real per-agent vault-scope registry,
replace `vault_write_tools.py::_is_within_assigned_scope`'s `T02`-built
fail-closed `return False` stub with a real scope-match check against that
registry, so `propose_vault_write` can genuinely accept an in-scope
proposal (Scenario 1) and genuinely reject an out-of-scope one against a
real assigned scope (Scenario 2) — rather than rejecting everything
unconditionally.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed `vault_write_tools.py` with
  `_is_within_assigned_scope` always returning `False`.
- `REQ-SB-29-US-01`'s own real vault-scope-assignment mechanism exists
  (its own task ids, TBD — likely a per-agent scope lookup function this
  task calls, e.g. something shaped like
  `agent_scope_registry.get_agent_scope(agent_id) -> list[str]`, exact
  name/shape decided by that story's own `/plan-tasks` pass, not assumed
  here).

**After / Outputs:**
- `_is_within_assigned_scope(agent_id, subfolder, frontmatter)` calls
  `REQ-SB-29-US-01`'s own real scope-lookup function for `agent_id`, and
  returns `True` only if the proposed `subfolder`/`frontmatter` target
  matches at least one of the agent's assigned tags/folders; `False`
  (unchanged behaviour) for an agent with no assigned scope at all,
  matching `REQ-SB-29-US-01`'s own Scenario 6 ("no assigned scope = no
  bounded access") extended to writes.
- Scenario 1 (`AC-01`) and Scenario 2 (`AC-02`) are, for the first time,
  genuinely live-verifiable end to end through `propose_vault_write`'s
  own real front door.

---

## Files to Modify

<!-- Scoped to vault_write_tools.py's own _is_within_assigned_scope
function -- the exact call this task makes into REQ-SB-29-US-01's own
scope-lookup module/function is decided once that story's real shape
exists, not guessed here. -->

- `src/backend/app/business/vault_write_tools.py` — replace
  `_is_within_assigned_scope`'s stub body with a real call into
  `REQ-SB-29-US-01`'s own scope-lookup mechanism. (If, once
  `REQ-SB-29-US-01` ships, its own real lookup needs something concrete
  from this task's own comparison logic that isn't already anticipated —
  e.g. a specific tag-string normalization — that is a new, real finding
  to escalate at that time, not assumed here.)

---

## Constraints

- Inherits from parent story and `ADR-025` point 6.
- This task adds no new persisted state of its own — it composes
  `REQ-SB-29-US-01`'s own real registry, exactly as built by that story.
- An agent with no assigned scope must still be rejected (fail-closed
  default preserved) — this task changes `_is_within_assigned_scope` from
  "always `False`" to "`False` unless a real matching scope is found,"
  never to "`True` by default."
- Do not fabricate a `depends_on` edge to make this task appear
  unblocked — leave `depends_on: []` until `REQ-SB-29-US-01` has a real,
  `Ready` task id.

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-04-US-01-AC-01]** _(Blocked — cannot be executed until
   `REQ-SB-29-US-01` ships.)_ Once real: assign a known agent (e.g.
   `vault-qa`) a real vault scope (e.g. a `customer/masdar` tag or a
   `Work/Notes/` folder, via `REQ-SB-29`'s own real mechanism), call
   `propose_vault_write` with a target inside that scope, confirm
   `{"status": "pending", ...}` is returned (not rejected), approve it,
   and confirm the resulting note lands in the vault at the proposed
   path with the proposed content.
2. **[REQ-SB-04-US-01-AC-02]** _(Blocked — cannot be executed until
   `REQ-SB-29-US-01` ships.)_ Once real: using the same scoped agent from
   step 1, call `propose_vault_write` with a target **outside** that
   agent's assigned scope. Confirm `{"status": "rejected", ...}` is
   returned, the rejection message clearly names the scope mismatch (not
   a generic/silent failure), and no pending-approval record was created
   and no note was created or modified as a result.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-01** (Scenario 1) — _blocked, not yet verifiable_ — a write
      within an agent's real assigned scope, once confirmed, lands in the
      vault
- [ ] **AC-02** (Scenario 2) — _blocked, not yet verifiable_ — a write
      attempt outside an agent's real assigned scope is rejected, clearly
      communicated, with no pending record and no note created
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (once unblocked)
- [ ] `CHANGELOG.md` entry appended (once unblocked)

---

## Out of Scope

- Building `REQ-SB-29-US-01`'s own vault-scope-assignment mechanism —
  that story's own scope entirely.
- Any change to `T01`/`T02`'s own auth/plumbing — reused exactly as
  built, no rework anticipated.
- AC-03/AC-04 — already fully verified by `T02`, independent of scope.

---

## Context / Notes

**Gating note:** this task is individually flagged (`gate: flagged`, its
own `status: Draft`, diverging from the rest of this story's own `status:
Ready` lockstep) — see the parent story's own `## Notes` for the full
judgement-call reasoning. This mirrors, not just parallels, the exact
precedent the operator already confirmed acceptable
(`REVIEW-QUEUE.md` → `ESC-018` entry, "Approved 2026-08-12 — per-task
blocking (T04 held, T01-T03 proceed) is correct; no reason to hold
buildable work back for one composition check") — applied here to a
2-of-4-ACs split rather than 1-of-6, for the same reason: `T01`/`T02` have
real, satisfiable dependencies and no reason to wait.

**A new `ESCALATIONS.md` entry, `ESC-026`, records this finding** — a
real, currently-unwireable cross-story dependency discovered during this
decomposer pass, the same shape `ESC-018` already established for
`REQ-SB-36-US-02`'s own composition with this identical blocking story
(`REQ-SB-29-US-01`).

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any
deviations from the plan, observed verification outcomes keyed by AC-ID.
Not applicable until this task is unblocked.)_
