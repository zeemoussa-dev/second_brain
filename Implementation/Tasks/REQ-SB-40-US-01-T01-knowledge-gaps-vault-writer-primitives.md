---
id: REQ-SB-40-US-01-T01
title: vault_writer.py — load_knowledge_gaps_state/save_knowledge_gaps_state primitives
parent_story: REQ-SB-40-US-01
requirement_id: REQ-SB-40
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-032 created) — carried from the parent story; the human reviews ADR-032 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: []
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-40-US-01-T01 — `vault_writer.py` knowledge-gaps state primitives

## Parent Story

- Story: [[REQ-SB-40-US-01]] — `../UserStories/REQ-SB-40-US-01-agent-knowledge-gap-tracking-and-expert-readiness.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-40 *Agent Knowledge-Gap Tracking & Expert Readiness*

---

## Objective

Add the tenth `.second-brain/` state file, `agent_knowledge_gaps.json`, plus its pure-I/O `vault_writer.py` primitives — `load_knowledge_gaps_state()`/`save_knowledge_gaps_state(state)` — mirroring `load_skills_state()`/`save_skills_state()`'s exact shape (`ADR-032` point 2), with no default content computed here (`ADR-003`).

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.py` already declares `_STATE_DIR = ".second-brain"` and sibling per-concern filename constants (`_AGENT_SKILLS_FILE`, `_AGENT_KEYWORDS_FILE`, `_AGENT_WORKING_MODES_FILE`, `_AGENT_PENDING_APPROVALS_FILE`), each with its own `_<concern>_path()` private helper and a `load_<concern>_state()`/`save_<concern>_state()` pair. `load_skills_state()`/`save_skills_state()` (real current file, verbatim):
  ```python
  def load_skills_state() -> dict | None:
      """Pure I/O — returns None if agent_skills.json doesn't exist yet (no
      default content is computed here, per ADR-003; explicit-grant-only,
      no self-healing default assignment, is a business-layer decision
      owned by app/business/skill_registry.py)."""
      path = _skills_state_path()
      if not path.exists():
          return None
      return json.loads(path.read_text(encoding="utf-8"))


  def save_skills_state(state: dict) -> None:
      path = _skills_state_path()
      path.write_text(json.dumps(state, indent=2), encoding="utf-8")
  ```

**After / Outputs:**
- `vault_writer.py` gains `_AGENT_KNOWLEDGE_GAPS_FILE = "agent_knowledge_gaps.json"`, `_knowledge_gaps_state_path()`, `load_knowledge_gaps_state() -> dict | None`, `save_knowledge_gaps_state(state: dict) -> None` — same pure-I/O shape as every sibling pair; no other function in this file is touched.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py`:
  - Add the new filename constant alongside the existing sibling constants (near the other `_AGENT_*_FILE` declarations, e.g. after `_AGENT_PENDING_APPROVALS_FILE`):
    ```python
    _AGENT_KNOWLEDGE_GAPS_FILE = "agent_knowledge_gaps.json"
    ```
  - Add the path helper and load/save pair, placed after `save_pending_approvals_state` (or the current file's real, current last per-agent-state-file pair — read the real file first, per this project's own established "compose around the REAL current file" pattern):
    ```python
    def _knowledge_gaps_state_path():
        state_dir = settings.vault_path / _STATE_DIR
        state_dir.mkdir(parents=True, exist_ok=True)
        return state_dir / _AGENT_KNOWLEDGE_GAPS_FILE


    def load_knowledge_gaps_state() -> dict | None:
        """Pure I/O — returns None if agent_knowledge_gaps.json doesn't
        exist yet (no default content is computed here, per ADR-003; the
        {"gaps": []} default shape is a business-layer decision owned by
        app/business/knowledge_gap_tracking.py, mirroring
        skill_registry.py's own _load_state() pattern)."""
        path = _knowledge_gaps_state_path()
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))


    def save_knowledge_gaps_state(state: dict) -> None:
        path = _knowledge_gaps_state_path()
        path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    ```

---

## Constraints

- Inherits from parent story.
- Pure I/O only — no default `{"gaps": []}` content, no gap-shape validation, no id generation here (`ADR-003`'s "no default content computed in `data_access`" rule, confirmed by `load_skills_state`'s own docstring precedent). All of that is `T02`'s (`knowledge_gap_tracking.py`) responsibility.
- Do not modify any other function in `vault_writer.py` — additive only.
- File shape stored is exactly `ADR-032` point 2's own declared schema: `{"gaps": [{"id": str, "agent_id": str, "question": str, "topic": str, "status": "open" | "closed", "created_at": iso8601, "closed_at": iso8601 | null, "resolution": "human_provided" | "research" | null}]}` — this task only persists/loads whatever dict `T02` passes in; it does not itself construct or validate that shape.

---

## Tests

<!-- No locked AC maps solely to this task — it is pure I/O plumbing with
no independently observable behavior of its own beyond "the file
round-trips." AC-01/03/04/05/06/07 are all verified downstream (T02/T04/
T05/T06/T07) via the real persisted file this task creates the read/write
path for. This task's own Tests block therefore verifies the plumbing
directly, not a locked AC. -->

**Manual verification steps:**

1. Non-AC smoke check: in a Python shell against the backend `.venv` (real configured `vault_path`), confirm `vault_writer.load_knowledge_gaps_state()` returns `None` (no file yet — real starting state). Call `vault_writer.save_knowledge_gaps_state({"gaps": [{"id": "abc123", "agent_id": "vault-qa", "question": "test", "topic": "test", "status": "open", "created_at": "2026-08-13T00:00:00", "closed_at": None, "resolution": None}]})`. Confirm `.second-brain/agent_knowledge_gaps.json` now exists in the configured vault directory and its contents match exactly (`json.dumps(state, indent=2)` shape). Call `vault_writer.load_knowledge_gaps_state()` again — confirm it returns the identical dict just saved (real round-trip, not a cached value).
2. Clean-up: delete `.second-brain/agent_knowledge_gaps.json` (or overwrite with `save_knowledge_gaps_state({"gaps": []})`), restoring a clean starting state before `T02`'s own verification begins.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `load_knowledge_gaps_state()` returns `None` when `agent_knowledge_gaps.json` does not exist, and the exact persisted dict when it does
- [ ] `save_knowledge_gaps_state(state)` writes `state` verbatim (via `json.dumps(state, indent=2)`) to `.second-brain/agent_knowledge_gaps.json`, creating `.second-brain/` if needed
- [ ] No other `vault_writer.py` function/constant is modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any default-content computation, gap-shape validation, or id generation — `T02`'s scope (`app/business/knowledge_gap_tracking.py`).
- `agent_activity.py` — untouched (`ADR-032`'s own "not folded into `agent_activity.py`" decision).

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-032` created at `/plan-tasks` step 1) — the human reviews `ADR-032` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Shared-file coordination:** `vault_writer.py` is this project's single most actively-extended shared file (per `Implementation/Learnings.md`'s own repeated finding on this exact file). Read the REAL current file immediately before applying this diff — the exact insertion point (after `save_pending_approvals_state`, or whichever per-agent-state pair is genuinely last in the real current file) may have shifted if a sibling story landed in between.

---

## Implementation Log

Implemented exactly as spec'd: added `_AGENT_KNOWLEDGE_GAPS_FILE`, `_knowledge_gaps_state_path()`, `load_knowledge_gaps_state()`, `save_knowledge_gaps_state()` to `vault_writer.py`, placed after `save_pending_approvals_state` — confirmed that was still the real, current last per-agent-state pair before landing the diff (matched the task's own sample verbatim). No other function/constant touched.

**Verification (non-AC plumbing check, per this task's own Tests block):** ran live against the real configured `vault_path` (`<OPERATOR_VAULT_OLD>`). `load_knowledge_gaps_state()` returned `None` (no file yet). `save_knowledge_gaps_state(...)` with a sample gap record created `.second-brain/agent_knowledge_gaps.json` with the exact `json.dumps(state, indent=2)` shape. `load_knowledge_gaps_state()` re-read returned the identical dict (real round-trip, confirmed via file read). Cleaned up with `save_knowledge_gaps_state({"gaps": []})` before T02 began.

gate: flagged (carried unchanged from parent story — trigger-3, ADR-032). No new decomposer/coder-owned trigger fired on this task itself.

status: Done
