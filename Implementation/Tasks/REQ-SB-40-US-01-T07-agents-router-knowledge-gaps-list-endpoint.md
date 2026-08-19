---
id: REQ-SB-40-US-01-T07
title: agents_router.py — GET /agents/{agent_id}/knowledge-gaps
parent_story: REQ-SB-40-US-01
requirement_id: REQ-SB-40
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-032 created) — carried from the parent story; the human reviews ADR-032 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-40-US-01-T02]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-40-US-01-T07 — `GET /agents/{agent_id}/knowledge-gaps`

## Parent Story

- Story: [[REQ-SB-40-US-01]] — `../UserStories/REQ-SB-40-US-01-agent-knowledge-gap-tracking-and-expert-readiness.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-40 *Agent Knowledge-Gap Tracking & Expert Readiness*

---

## Objective

Add `GET /agents/{agent_id}/knowledge-gaps`, mirroring the existing `/history`/`/skills` per-agent sub-resource convention (`ADR-032` point 5) — returns `{"gaps": [...], "open_count": int}`, the read side `T08`'s own Knowledge gaps tab renders directly.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed `knowledge_gap_tracking.list_agent_gaps`/`count_open_gaps`.
- Real current `agents_router.py`'s own `/history` sub-resource endpoint (the convention to mirror, verbatim):
  ```python
  @router.get("/{agent_id}/history")
  def get_history(agent_id: str) -> list[dict]:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")
      return vault_writer.load_agent_history(agent_id)
  ```

**After / Outputs:**
- `agents_router.py` gains `GET /agents/{agent_id}/knowledge-gaps`, placed after `get_history`, returning every recorded gap for that agent (open and closed — a full, ordinary read, no filtering by default) plus the current `open_count`.

---

## Files to Modify

- `src/backend/app/api/agents_router.py`:
  - (`knowledge_gap_tracking` is already imported by `T05`/`T06` if either landed first in the real build order; if this task lands first, add `knowledge_gap_tracking` to the existing `from app.business import (...)` block.)
  - Add the endpoint, placed after `get_history`:
    ```python
    @router.get("/{agent_id}/knowledge-gaps")
    def get_knowledge_gaps(agent_id: str) -> dict:
        agent = agent_registry.get_agent(agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail="Unknown agent")
        return {
            "gaps": knowledge_gap_tracking.list_agent_gaps(agent_id),
            "open_count": knowledge_gap_tracking.count_open_gaps(agent_id),
        }
    ```

---

## Constraints

- Inherits from parent story.
- Read-only — no state mutation.
- Returns every gap for the agent (both `"open"` and `"closed"`), never filtered server-side by default — mirrors `/history`'s own "return the full record, let the client render what it needs" convention; `T08`'s own UI decides what to show/hide.
- `open_count` must always equal `len([g for g in gaps if g["status"] == "open"])` — computed via `knowledge_gap_tracking.count_open_gaps`, never a client-side recomputation the UI would have to keep in sync.
- Do not modify `get_history`, `get_agent`, or any other existing endpoint.

---

## Tests

**Manual verification steps:**

1. **[REQ-SB-40-US-01-AC-02]** In a Python shell / real HTTP call against the backend `.venv`. Starting from a clean state, record two real gaps for `vault-qa` (`knowledge_gap_tracking.record_gap("vault-qa", "question A", "topic A")`, `record_gap("vault-qa", "question B", "topic B")`). Call `GET /agents/vault-qa/knowledge-gaps`. Confirm the response's `gaps` list contains exactly these 2 records (real `question`/`topic`/`status="open"` fields present), and `open_count` is `2`. Close one gap (`knowledge_gap_tracking.close_gap(<id>, "human_provided")`). Re-call the same endpoint — confirm `gaps` still contains both records (the closed one now `status="closed"`), and `open_count` is now `1` — a real, live-recomputed value, not stale.
2. Non-AC smoke check: `GET /agents/todo-capture/knowledge-gaps` (an agent with zero recorded gaps — real starting state) — confirm `{"gaps": [], "open_count": 0}`, not a 404 or an error.
3. Non-AC smoke check: `GET /agents/does-not-exist/knowledge-gaps` — confirm `404`.
4. Clean-up: `vault_writer.save_knowledge_gaps_state({"gaps": []})`, restoring a clean starting state before `T08`'s own verification begins.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-02** (Scenario 2, backend half) — the endpoint returns the agent's own gaps and a real, live `open_count`
- [ ] An agent with zero gaps returns `{"gaps": [], "open_count": 0}`, never a 404
- [ ] An unknown `agent_id` returns `404`
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The two closing-path `POST` endpoints — `T05`/`T06`'s own scope.
- `AgentDetailPanel.tsx` — `T08`'s own scope.
- Any pagination/sorting beyond the natural insertion order already stored — not asked for by this story's own Acceptance text.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-032` created at `/plan-tasks` step 1) — the human reviews `ADR-032` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Shared-file coordination:** `agents_router.py` is also touched by `T05`/`T06` (both add sibling `POST` endpoints under the same `/{agent_id}/knowledge-gaps/...` prefix) — whichever of `T05`/`T06`/`T07` lands first in the real build order adds the `knowledge_gap_tracking` import; the others simply confirm it is already present rather than re-adding it (avoids a duplicate-import diff).

---

## Implementation Log

Added `GET /{agent_id}/knowledge-gaps` to `agents_router.py`, placed after `get_history` (the `knowledge_gap_tracking` import was already present, added by `T05`). No other endpoint touched.

**[REQ-SB-40-US-01-AC-02, backend half] — verified live**: recorded 2 real gaps for `vault-qa`. `GET /agents/vault-qa/knowledge-gaps` returned both real records (`question`/`topic`/`status="open"` present) and `open_count: 2`. Closed one gap directly; re-called the same endpoint — both records still present (the closed one now `status="closed"`), `open_count` live-recomputed to `1`, no staleness. PASS.

Non-AC smoke checks: `GET /agents/todo-capture/knowledge-gaps` (zero real gaps) returned `{"gaps": [], "open_count": 0}`, not a `404`. `GET /agents/does-not-exist/knowledge-gaps` returned `404`.

Cleaned up before T08.

gate: flagged (carried, trigger-3). No new trigger fired.

status: Done
