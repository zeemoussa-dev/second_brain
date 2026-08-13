---
id: REQ-SB-36-US-02-T04
title: "⚠️ BLOCKED — Scenario 3 (draw on afterward) composition/regression check"
parent_story: REQ-SB-36-US-02
requirement_id: REQ-SB-36
type: backend
status: Draft
gate: flagged
gate_reason: "Individually flagged, mirroring ESC-011's own precedent exactly. Blocked on REQ-SB-29-US-01, which has not been decomposed at all (status: Draft, zero task files exist) — no real task id exists anywhere to depend on. Logged as ESCALATIONS.md -> ESC-018 (new). Do not start until REQ-SB-29-US-01 has shipped its own vault-scope-assignment/retrieval mechanism and a follow-up decomposer pass replaces this depends_on: [] with the real task id."
phase: P1
depends_on: []
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-36-US-02-T04 — ⚠️ BLOCKED — Scenario 3 composition/regression check

## ⚠️ BLOCKED — DO NOT START

This task cannot be built or verified until `REQ-SB-29-US-01` (Agent-to-Tag/Folder Scoping) ships its own real vault-scope-assignment/retrieval mechanism. As of this decomposition pass, `REQ-SB-29-US-01` is `status: Draft`, `gate: clear`, and **has not been decomposed into tasks at all** — zero `REQ-SB-29-US-01-T*.md` files exist anywhere in `Implementation/Tasks/` (confirmed by direct glob at decomposition time). There is no real task id to depend on, unlike `REQ-SB-21-US-01` (whose own decomposer pass has already run this same session). `depends_on: []` here is a deliberate, honest placeholder — never fabricate a task id that does not exist, mirroring `ESC-011`'s own established precedent (`REQ-SB-27-US-01-T02`) exactly.

**Resolving this block:** once `REQ-SB-29-US-01` reaches `status: Ready` (its own decomposer pass has run and produced real task ids for its vault-scope-assignment/retrieval mechanism), a follow-up decomposer pass on this story replaces this task's own `depends_on: []` with the real id(s), and this task's own `status`/`gate` are reset to ordinary lockstep with the rest of this story. See `ESCALATIONS.md` → `ESC-018`.

---

## Parent Story

- Story: [[REQ-SB-36-US-02]] — `../UserStories/REQ-SB-36-US-02-agent-knowledge-bootstrapping-delegated-research-chain.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-36 *Agent Knowledge Bootstrapping via Delegated Research*

---

## Objective

Once `REQ-SB-29-US-01` ships, confirm that content this story's own chain (`T02`/`T03`) files into the vault is genuinely retrievable by the newly-expert agent through `REQ-SB-29`'s own real vault-scope-assignment/retrieval mechanism — a pure cross-story composition/regression check, not new code owned by this story.

---

## Starting State → End State

**Before / Inputs:**
- `T02`/`T03` have landed and are `Done` — real content has been filed into the vault by a real `bootstrap_agent_knowledge` chain run.
- `REQ-SB-29-US-01`'s own real vault-scope-assignment mechanism exists (its own task ids, TBD).

**After / Outputs:**
- A recorded, real confirmation that assigning the newly-expert agent's vault scope (via `REQ-SB-29`'s own real mechanism) to cover wherever `T02`/`T03`'s own chain filed content makes that content genuinely retrievable by the agent on request.

---

## Files to Modify

<!-- None owned by this story. Scenario 3's own "When"/"Then" clauses
describe REQ-SB-29's own mechanism entirely (setting vault scope,
retrieval) -- this story's own chain (T02/T03) needs zero further code
change for this scenario to hold true, once REQ-SB-29 exists. This task
exists purely to hold AC-03's own eventual verification step, per
ESC-011's own established precedent for a genuinely blocked locked AC. -->

- None in this story. (If, once `REQ-SB-29-US-01` ships, its own real retrieval mechanism turns out to need something concrete from this story's own filed content shape that isn't already present — e.g. a specific frontmatter field — that would be a new, real finding to escalate at that time, not assumed here.)

---

## Constraints

- Inherits from parent story.
- This task adds no new code to this story — it is a verification-only, cross-story composition check.
- Do not fabricate a `depends_on` edge to make this task appear unblocked — leave `depends_on: []` until `REQ-SB-29-US-01` has a real, `Ready` task id.

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-36-US-02-AC-03]** _(Blocked — cannot be executed until `REQ-SB-29-US-01` ships.)_ Once real: run `T02`'s own Scenario-1-shaped chain (or reuse its own already-filed content), assign the newly-expert agent's vault scope (via `REQ-SB-29`'s own real mechanism) to cover the folder/tag the content was filed under, then confirm — via `REQ-SB-29`'s own real retrieval mechanism — that the agent can retrieve and use that filed content on request.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-03** (Scenario 3) — _blocked, not yet verifiable_ — filed content is retrievable by the newly-expert agent through `REQ-SB-29`'s own real mechanism
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (once unblocked)
- [ ] `CHANGELOG.md` entry appended (once unblocked)

---

## Out of Scope

- Building `REQ-SB-29-US-01`'s own vault-scope-assignment/retrieval mechanism — that story's own scope entirely.
- Any change to `T02`/`T03`'s own filing chain — reused exactly as built, no rework anticipated.

---

## Context / Notes

**Gating note:** this task is individually flagged (`gate: flagged`, its own `status: Draft`, diverging from the rest of this story's own `status: Ready` lockstep) — see the parent story's own `## Notes` for the full judgement-call reasoning (this decomposer chose to advance the story overall rather than hold all 4 tasks back over this one scenario, mirroring but not identically replicating `ESC-011`'s own full-story-Draft precedent — flagged in `REVIEW-QUEUE.md` for human confirmation).

**A new `ESCALATIONS.md` entry, `ESC-018`, records this finding** — a real, currently-unwireable cross-story dependency discovered during this decomposer pass, not inherited from the architect's own `ESC-017` finding (which concerned `REQ-SB-21-US-01`, already resolved with real task ids for this story's other three tasks).

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any
deviations from the plan, observed verification outcomes keyed by AC-ID.
Not applicable until this task is unblocked.)_
