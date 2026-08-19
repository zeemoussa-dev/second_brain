---
id: REQ-SB-40-US-01-T02
title: app/business/knowledge_gap_tracking.py — record_gap/close_gap/list_agent_gaps/count_open_gaps
parent_story: REQ-SB-40-US-01
requirement_id: REQ-SB-40
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-032 created) — carried from the parent story; the human reviews ADR-032 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-40-US-01-T01]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-40-US-01-T02 — `knowledge_gap_tracking.py` business module

## Parent Story

- Story: [[REQ-SB-40-US-01]] — `../UserStories/REQ-SB-40-US-01-agent-knowledge-gap-tracking-and-expert-readiness.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-40 *Agent Knowledge-Gap Tracking & Expert Readiness*

---

## Objective

Add a new `app/business/knowledge_gap_tracking.py` module — composed the same way `skill_registry.py` composes `skill_tools.py` (`ADR-032` point 2) — exposing `record_gap`, `close_gap`, `list_agent_gaps`, and `count_open_gaps`: the one shared read/write core every other task in this story (`T04`–`T07`) calls into. This is the task that makes `AC-05` (the declining open-gap count) a real, directly-verifiable property.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed `vault_writer.load_knowledge_gaps_state()`/`save_knowledge_gaps_state()`.
- `skill_registry.py`'s own `_load_state()` pattern (real current file, verbatim) is the shape to mirror:
  ```python
  def _load_state() -> dict:
      state = vault_writer.load_skills_state()
      if state is None:
          state = {"assignments": {}}
          vault_writer.save_skills_state(state)
      return state
  ```

**After / Outputs:**
- New file `src/backend/app/business/knowledge_gap_tracking.py`, exposing:
  - `record_gap(agent_id: str, question: str, topic: str) -> dict` — appends a new gap (`id = uuid.uuid4().hex[:12]`, `status="open"`, `created_at=<now, iso8601>`, `closed_at=None`, `resolution=None`), persists, returns the created record.
  - `close_gap(gap_id: str, resolution: str) -> bool` — finds the gap by id; if found and still `"open"`, sets `status="closed"`, `closed_at=<now, iso8601>`, `resolution=resolution`, persists, returns `True`; returns `False` if the gap is unknown or already closed (idempotent no-op, mirrors `revoke_skill_access`'s own idempotent-return-True-on-no-op shape — here `False` since "already closed" is a meaningfully different outcome a caller needs to distinguish from a fresh close, unlike a plain revoke).
  - `list_agent_gaps(agent_id: str, status: str | None = None) -> list[dict]` — every gap for `agent_id`, optionally filtered by `status` (`"open"`/`"closed"`).
  - `count_open_gaps(agent_id: str) -> int` — `len(list_agent_gaps(agent_id, status="open"))`.

---

## Files to Modify

- `src/backend/app/business/knowledge_gap_tracking.py` (new file):
  ```python
  """Agent knowledge-gap tracking (ADR-032) -- the shared read/write core
  every closing path (T05's human-answer path, T06's delegated-research
  path) and the graph.py detection node (T04) compose. Mirrors
  skill_registry.py's own "one dedicated business module + one dedicated
  .second-brain/<concern>.json file, pure I/O in vault_writer, business
  rules here" pattern (ADR-032 point 2) -- never folded into
  agent_activity.py, whose own _ACTIVITY_KINDS scope stays
  background-run-only (that story's own Constraints)."""
  import uuid
  from datetime import datetime, timezone

  from app.data_access import vault_writer


  def _load_state() -> dict:
      state = vault_writer.load_knowledge_gaps_state()
      if state is None:
          state = {"gaps": []}
          vault_writer.save_knowledge_gaps_state(state)
      return state


  def record_gap(agent_id: str, question: str, topic: str) -> dict:
      """id is uuid.uuid4().hex[:12] -- the same synthetic-id precedent
      ADR-018 point 2 already established for a workflow record with no
      natural vault-derived identity (a gap is born from a conversation
      turn, not a vault fact)."""
      state = _load_state()
      record = {
          "id": uuid.uuid4().hex[:12],
          "agent_id": agent_id,
          "question": question,
          "topic": topic,
          "status": "open",
          "created_at": datetime.now(timezone.utc).isoformat(),
          "closed_at": None,
          "resolution": None,
      }
      state["gaps"].append(record)
      vault_writer.save_knowledge_gaps_state(state)
      return record


  def close_gap(gap_id: str, resolution: str) -> bool:
      """Returns False if gap_id is unknown or already closed -- a
      caller-meaningful distinction (T06's honest-no-results path, AC-07,
      must never call this at all for a "no_results" outcome; T05/T06's
      own "closed once, not twice" idempotency relies on this False
      return rather than silently succeeding a second time)."""
      state = _load_state()
      for gap in state["gaps"]:
          if gap["id"] == gap_id and gap["status"] == "open":
              gap["status"] = "closed"
              gap["closed_at"] = datetime.now(timezone.utc).isoformat()
              gap["resolution"] = resolution
              vault_writer.save_knowledge_gaps_state(state)
              return True
      return False


  def list_agent_gaps(agent_id: str, status: str | None = None) -> list[dict]:
      state = _load_state()
      gaps = [gap for gap in state["gaps"] if gap["agent_id"] == agent_id]
      if status is not None:
          gaps = [gap for gap in gaps if gap["status"] == status]
      return gaps


  def count_open_gaps(agent_id: str) -> int:
      return len(list_agent_gaps(agent_id, status="open"))
  ```

---

## Constraints

- Inherits from parent story.
- No correctness-verification/approval step inside `close_gap` beyond what its caller (`T05`/`T06`) already arranged before calling it — this module trusts its caller's own `resolution` argument once filing/research has genuinely completed (`ADR-032` point 3, mirrors `MEMORY.md`'s standing no-staging-gate posture); it does not itself call `vault_filing_expert`/`knowledge_bootstrap`.
- `record_gap`'s `question` parameter must always be the caller-supplied real question text — this module does not itself decide what counts as "the real originating `HumanMessage`" (that is `T04`'s own responsibility, per `ADR-032` point 1's "never trust the model's own topic argument for the durable question text").
- Whole-state read-modify-write on every call (no in-process caching) — mirrors `skill_registry.py`'s own identical shape; acceptable at this project's current single-process, low-concurrency scale, same posture already accepted for every sibling `.second-brain/*.json` store.
- Do not modify `skill_registry.py`, `agent_activity.py`, or any other existing business module.

---

## Tests

<!-- AC-05 (the declining open-gap count) is a property of THIS module's
own record_gap/close_gap/count_open_gaps composition and is fully,
directly verifiable here without any live model/HTTP call -- the closing
PATHS themselves (human-answer vs. research) are T05/T06's own scope. -->

**Manual verification steps:**

1. **[REQ-SB-40-US-01-AC-05]** In a Python shell against the backend `.venv` (real configured `vault_path`, starting from a clean `agent_knowledge_gaps.json` — see `T01`'s own clean-up step). Call `knowledge_gap_tracking.record_gap("vault-qa", "What is our Q3 pricing model?", "Q3 pricing")` twice (two distinct gaps). Confirm `knowledge_gap_tracking.count_open_gaps("vault-qa")` returns `2`. Call `knowledge_gap_tracking.close_gap(<first gap's id>, "human_provided")` — confirm it returns `True`. Confirm `count_open_gaps("vault-qa")` now returns `1` — the open-gap count visibly declined by exactly one real `close_gap` call, not a manually-decremented counter. Close the second gap (`resolution="research"`) — confirm `count_open_gaps("vault-qa")` returns `0`.
2. Non-AC smoke check: call `knowledge_gap_tracking.close_gap("nonexistent-id", "human_provided")` — confirm it returns `False` (no exception, no state mutation). Call `close_gap` a second time on an already-closed gap id from step 1 — confirm it also returns `False` (idempotent — does not re-close or overwrite `closed_at`/`resolution`).
3. Non-AC smoke check: call `knowledge_gap_tracking.list_agent_gaps("vault-qa")` — confirm both gaps are present with `status="closed"`, `resolution` set to what was passed, and `closed_at` a real ISO-8601 timestamp. Call `list_agent_gaps("vault-qa", status="open")` — confirm it returns `[]`.
4. Clean-up: `vault_writer.save_knowledge_gaps_state({"gaps": []})`, restoring a clean starting state before `T04`'s own verification begins.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-05** (Scenario 5, backend half) — `count_open_gaps` visibly declines by exactly one for each real `close_gap` call; a fresh Expert agent with no gaps recorded returns `0`
- [ ] `record_gap` creates a record with a unique `id`, `status="open"`, `closed_at=None`, `resolution=None`
- [ ] `close_gap` returns `False` (no-op) for an unknown or already-closed gap id, `True` and mutates state only for a real open gap
- [ ] `list_agent_gaps`/`count_open_gaps` scope strictly to `agent_id`, never leaking another agent's gaps
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Calling `vault_filing_expert`/`knowledge_bootstrap` — `T05`/`T06`'s own scope; this module only records the outcome once its caller decides to close a gap.
- Any HTTP endpoint — `T07`/`T05`/`T06`'s own scope (`agents_router.py`).
- The `record_knowledge_gap` bound tool / graph node — `T04`'s own scope; this module is called BY that node, not the reverse.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-032` created at `/plan-tasks` step 1) — the human reviews `ADR-032` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Why `close_gap` returns `False` rather than raising on an unknown/already-closed id:** mirrors this module's own sibling precedent (`skill_registry.grant_skill_access`/`revoke_skill_access` both return booleans, never raise, for a caller-supplied unknown id) — `T05`/`T06`'s own endpoints translate a `False` into an honest HTTP error, not a raw 500.

---

## Implementation Log

Created `app/business/knowledge_gap_tracking.py` exactly as spec'd: `_load_state`, `record_gap`, `close_gap`, `list_agent_gaps`, `count_open_gaps`, mirroring `skill_registry.py`'s own `_load_state()` shape.

**[REQ-SB-40-US-01-AC-05] — verified live**, backend module only (no HTTP/model call needed): against a clean `agent_knowledge_gaps.json`, `record_gap("vault-qa", ...)` called twice produced `count_open_gaps("vault-qa") == 2`. `close_gap(<first id>, "human_provided")` returned `True`; `count_open_gaps` dropped to `1`. Closing the second gap (`resolution="research"`) dropped the count to `0` — a real, observed decline driven purely by real `close_gap` calls, not a manually decremented counter. PASS.

Non-AC smoke checks, all observed exactly as spec'd: `close_gap` on an unknown id and on an already-closed id both returned `False` with no state mutation (idempotent). `list_agent_gaps("vault-qa")` showed both records `closed` with the correct `resolution`/`closed_at`; `list_agent_gaps("vault-qa", status="open")` returned `[]`.

Cleaned up (`save_knowledge_gaps_state({"gaps": []})`) before T04's own verification began.

gate: flagged (carried, trigger-3). No new trigger fired.

status: Done
