---
id: REQ-SB-41-US-01-T01
title: agent_registry.py — backfill 7 shipped agents with a real Purpose settings entry
parent_story: REQ-SB-41-US-01
requirement_id: REQ-SB-41
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-033 created) — carried from the parent story; the human reviews ADR-033 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: []
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-41-US-01-T01 — `agent_registry.py` Purpose backfill

## Parent Story

- Story: [[REQ-SB-41-US-01]] — `../UserStories/REQ-SB-41-US-01-agent-overview-surface.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-41 *Agent Overview Surface*

---

## Objective

Backfill all 7 shipped agents (`email-capture`, `meeting-capture`, `todo-capture`, `people-producer`, `vault-qa`, `vault-filing-expert`, `compass-expert`) with one real, authored `{"key": "Purpose", "value": "..."}` settings entry each — a static seed-data edit only, per `ADR-033` point 3a — so `T02`'s Overview Purpose region has a real, non-fabricated sentence to show for every already-shipped agent.

---

## Starting State → End State

**Before / Inputs:**
- `src/backend/app/business/agent_registry.py`'s real current top-level dict — **read the real current file before editing; do not assume its name.** As of this task's own writing it is `AGENTS: dict[str, dict]` (7 entries, unrenamed). `REQ-SB-37-US-01-T02` (a sibling, already-`Ready` task on a different story) may rename it to `_SEED_AGENTS` before this task lands, per `ADR-030`. Either way, this task's own diff is the same: append one additive `{"key": "Purpose", ...}` entry to each of the 7 entries' existing `settings` list, whatever the enclosing dict is currently called. Do not rename the dict yourself if it hasn't been renamed yet — that rename is `REQ-SB-37-US-01-T02`'s own scope, not this task's.
- None of the 7 entries currently carries a `"Purpose"` or `"Domain"` key (confirmed directly — `ADR-033`'s own Context).

**After / Outputs:**
- Each of the 7 seed agents' `settings` list gains exactly one new trailing entry: `{"key": "Purpose", "value": "<one line>"}`. No existing settings row edited, reordered, or removed. No other file changes — `GET /agents/{agent_id}` already returns the full `settings` array unmodified, so this backfill is visible to `T02`'s Overview with zero API changes.

---

## Files to Modify

- `src/backend/app/business/agent_registry.py` — append one entry to the end of each of the 7 entries' existing `settings` list (verbatim draft copy, `ADR-033` point 3a — final wording is this task's own copy-editing latitude, but must preserve the same factual content):
  - `email-capture` → `{"key": "Purpose", "value": "Automatically captures incoming Outlook emails into the vault on an hourly schedule, classified by customer."}`
  - `meeting-capture` → `{"key": "Purpose", "value": "Automatically captures Outlook Calendar meetings into the vault on an hourly schedule, classified by customer and deduplicated across reruns."}`
  - `todo-capture` → `{"key": "Purpose", "value": "Automatically captures Outlook Tasks into the vault on an hourly schedule."}`
  - `people-producer` → `{"key": "Purpose", "value": "Builds and maintains a person note for every new email sender or meeting attendee, preserving any user-added content."}`
  - `vault-qa` → `{"key": "Purpose", "value": "Answers questions about the vault's contents, grounded in the indexed vault; reachable from this panel and Hermes channels."}`
  - `vault-filing-expert` → `{"key": "Purpose", "value": "Decides where new vault content belongs using the Second Brain filing methodology, pausing for approval when a new top-level area is needed."}`
  - `compass-expert` → `{"key": "Purpose", "value": "A subject-matter expert on Compass, built from delegated research rather than pre-loaded knowledge."}`

---

## Constraints

- Inherits from parent story and `ADR-033` point 3 in full.
- **Additive only** — append one entry per agent's existing `settings` list; do not edit, reorder, or remove any existing settings row (e.g. `compass-expert`'s existing `"Vault scope"` settings row stays exactly as-is — this task does not touch it, and does not conflate it with the real `scope` field `REQ-SB-29-US-01` adds elsewhere).
- **Does not touch `create_agent`, `POST /agents`, or any runtime agent-creation call path** — this is a one-time backfill of the 7 static seed entries only. Must not modify or reopen `REQ-SB-37-US-02-T01`'s already-`Ready`, already-locked "Worker's `create_agent` call MUST pass `settings=[]`" constraint (out of scope, a different task on a different story).
- Do not rename the top-level dict, add a new field to the agent record shape, or touch `get_agent`/`list_agents`/`get_action`/`create_agent` (if present) — this task changes seed data only.
- Do not touch any file other than `agent_registry.py`.

---

## Tests

<!-- Pure static-seed-data layer, one below every locked AC's own
user/API-observable outcome — no locked AC is tagged here directly,
mirroring REQ-SB-29-US-01-T03's own precedent ("Scenario 1/2's full
verification lives in T05... the steps below are non-AC smoke checks").
AC-02 (Scenario 2, Purpose) is verified at the observable UI layer in T02,
which reads this task's real backfilled data. -->

**Manual verification steps** (Python shell, from `src/backend`, backend `.venv` active):

1. Non-AC smoke check: `from app.business import agent_registry` — call `agent_registry.get_agent("vault-qa")`. Confirm its `settings` list now contains a `{"key": "Purpose", "value": "Answers questions about the vault's contents, grounded in the indexed vault; reachable from this panel and Hermes channels."}` entry (or this task's own copy-edited equivalent, same factual content), appended after the pre-existing `Grounding`/`Reachable via`/`Write access` rows (still present, unchanged, in their original order).
2. Non-AC smoke check: repeat step 1 for the remaining 6 agents (`email-capture`, `meeting-capture`, `todo-capture`, `people-producer`, `vault-filing-expert`, `compass-expert`) — confirm each carries exactly one new trailing `"Purpose"` entry, and every pre-existing settings row for that agent is unchanged in content and order.
3. Non-AC smoke check: `agent_registry.list_agents()` — confirm it still returns exactly 7 agents (or 7 seed + any already-created agents, if `REQ-SB-37-US-01`'s create path has landed by build time), in unchanged order, each with the same `{"id", "name", "type"}` shape as before this task — `list_agents()`'s own summary shape does not surface `settings`, so this backfill is invisible there by design.
4. Non-AC smoke check: real HTTP — start the backend (`.venv\Scripts\uvicorn app.main:app --reload --port 8001`), `GET /agents/compass-expert`. Confirm the response's `settings` array includes the new `Purpose` entry alongside the pre-existing rows, with no other field changed.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] All 7 shipped agents (`email-capture`, `meeting-capture`, `todo-capture`, `people-producer`, `vault-qa`, `vault-filing-expert`, `compass-expert`) carry exactly one new, appended `{"key": "Purpose", "value": ...}` settings entry
- [x] No existing settings row (for any of the 7 agents) is edited, reordered, or removed
- [x] `create_agent`/`POST /agents` and `REQ-SB-37-US-02-T01`'s locked Worker `settings=[]` constraint are untouched
- [x] `get_agent`/`list_agents`/`get_action`'s call signatures and return shapes are unchanged
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint — n/a, no new decision/pattern/constraint emerged (backfill composes `ADR-033`'s already-recorded decision)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend change — `T02`'s own scope.
- Renaming `AGENTS`/`_SEED_AGENTS`, or any other structural change to `agent_registry.py` — `REQ-SB-37-US-01-T02`'s own scope, a different story; if it has already landed by the time this task builds, compose around its real current shape rather than reverting it.
- A Purpose/Domain entry for any agent created after this pass via the wizard — `ADR-033` point 3b's own resolution is that such an agent shows the honest "No stated purpose recorded" state instead; this task only backfills the 7 already-shipped agents.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-033` created at `/plan-tasks` step 1) — the human reviews `ADR-033` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Why no hard `depends_on` on `REQ-SB-37-US-01-T02`:** that task renames `AGENTS` → `_SEED_AGENTS` as part of a larger seed-plus-persisted-overlay rewrite, but this task's own diff (append one entry per existing agent's `settings` list) is identical either way — the dict's name is not load-bearing for this task's own instructions. Read the real current file first, exactly as this project's own established convention requires, and append accordingly.

Full reasoning for the 7 backfill lines and the decision to backfill rather than leave an honest empty state: `Implementation/Architecture/ADR.md` → `ADR-033` point 3 and its own Alternatives Considered.

---

## Implementation Log

Read the REAL current `agent_registry.py` first — confirmed the top-level dict is already named `_SEED_AGENTS` (renamed ahead of this task by `REQ-SB-37-US-01-T02`, per this task's own anticipated either-way instruction), 7 entries, none carrying a `Purpose`/`Domain` key. Appended exactly one trailing `{"key": "Purpose", "value": "..."}` entry to each of the 7 entries' existing `settings` list, verbatim from `ADR-033` point 3a's draft copy (no copy-editing changes made — the draft lines were already clear and factually accurate). No existing settings row edited, reordered, or removed. `create_agent`/`get_agent`/`list_agents`/`get_action` untouched.

**Verification** (Python shell + real HTTP, backend `.venv`, matching this task's own `## Tests` steps 1–4):

- **Step 1/2 (non-AC smoke check)** — `agent_registry.get_agent(...)` for all 7 agents: each carries exactly one new trailing `"Purpose"` entry; every pre-existing settings row is unchanged in content and order (confirmed by direct dump of each agent's `settings` list). PASS.
- **Step 3 (non-AC smoke check)** — `agent_registry.list_agents()` returns exactly 7 agents, same `{"id", "name", "type"}` shape and order as before this task; `settings` (and therefore this backfill) is invisible in the summary shape, as designed. PASS.
- **Step 4 (non-AC smoke check)** — started the real backend (`.venv\Scripts\uvicorn app.main:app --reload --port 8001`), `GET /agents/compass-expert` — response's `settings` array includes the new `Purpose` entry alongside all pre-existing rows (`Subject`/`Starting knowledge`/`Vault scope`), unchanged. PASS.

No AC is tagged directly to this task (`AC-02`'s own real user/API-observable verification lives in `T02`, per this project's own established "verify at the observable layer" precedent) — `T02`'s own live verification (see its Implementation Log) confirms this backfilled data renders correctly on the Overview tab for `vault-qa`, `todo-capture`, and `people-producer`.

gate: flagged (carried, trigger-3). No new trigger fired.

status: Done
