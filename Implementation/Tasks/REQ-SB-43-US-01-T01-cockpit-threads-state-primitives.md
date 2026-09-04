---
id: REQ-SB-43-US-01-T01
title: vault_writer.py — load_cockpit_threads_state/save_cockpit_threads_state primitives (new .second-brain/cockpit_threads.json)
parent_story: REQ-SB-43-US-01
requirement_id: REQ-SB-43
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-43-US-01-T01 — `vault_writer.py` cockpit-threads state primitives

## Parent Story

- Story: [[REQ-SB-43-US-01]] — `../UserStories/REQ-SB-43-US-01-meeting-cockpit-expert-assisted-workspace.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-43 *Meeting Cockpit — Expert-Assisted Meeting Workspace*

---

## Objective

Add the pure-I/O `load_cockpit_threads_state`/`save_cockpit_threads_state` pair to `vault_writer.py`, mirroring `load_pending_approvals_state`/`save_pending_approvals_state`'s own exact shape — the new `.second-brain/cockpit_threads.json` this codebase's first multi-party (not per-agent) conversation store (`ADR-036` point 1).

---

## Starting State → End State

**Before / Inputs:** `vault_writer.py`'s `_STATE_DIR = ".second-brain"`; `_pending_approvals_state_path()`/`load_pending_approvals_state()`/`save_pending_approvals_state()` are the closest existing precedent (a flat, single-file JSON blob under `.second-brain/`).

**After / Outputs:**
```python
_COCKPIT_THREADS_FILE = "cockpit_threads.json"


def _cockpit_threads_state_path():
    state_dir = settings.vault_path / _STATE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / _COCKPIT_THREADS_FILE


def load_cockpit_threads_state() -> dict | None:
    """Pure I/O -- returns None if cockpit_threads.json doesn't exist yet
    (ADR-003; the empty-dict seed is app/business/cockpit/threads.py's own
    concern, mirroring load_pending_approvals_state's precedent)."""
    path = _cockpit_threads_state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_cockpit_threads_state(state: dict) -> None:
    path = _cockpit_threads_state_path()
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
```

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add `_COCKPIT_THREADS_FILE`, `_cockpit_threads_state_path`, `load_cockpit_threads_state`, `save_cockpit_threads_state`, placed alongside the existing `_pending_approvals_state_path`/`load_pending_approvals_state`/`save_pending_approvals_state` trio. Additive only.

---

## Constraints

- Byte-for-byte mirrors `load_pending_approvals_state`/`save_pending_approvals_state`'s own shape (pure I/O, `None` when absent, no business-logic default/seed here).
- Does not touch any existing function in `vault_writer.py`.
- `json`/`Path` imports are already present in this file (confirmed — used by the existing pending-approvals pair) — no new import needed.

---

## Tests

**Manual verification steps** (Python shell, backend `.venv`, `PYTHONPATH=.`; delete any leftover `.second-brain/cockpit_threads.json` first):
1. Non-AC smoke check: `vault_writer.load_cockpit_threads_state()` → `None` (file doesn't exist yet).
2. Non-AC smoke check: `vault_writer.save_cockpit_threads_state({"meeting:test-stem": {"messages": [], "brought_in_agent_ids": []}})`. Confirm `.second-brain/cockpit_threads.json` now exists on disk with that exact content (real JSON, indent=2).
3. Non-AC smoke check: `vault_writer.load_cockpit_threads_state()` → the same dict just saved.
4. Clean-up: delete `.second-brain/cockpit_threads.json`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `load_cockpit_threads_state` returns `None` when the file doesn't exist, else the parsed JSON dict
- [ ] `save_cockpit_threads_state` writes real, re-readable JSON under `.second-brain/cockpit_threads.json`
- [ ] No existing `vault_writer.py` function modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The multi-party thread business logic (empty-dict seeding, message composition, per-Expert history-building) — `T02`.

---

## Context / Notes

Full mechanism/reasoning: `ADR-036` point 1. This is the third `.second-brain/` flat-file-JSON state module (after working modes, pending approvals) — no new convention, exact precedent reuse.

---

## Implementation Log

Implemented exactly as spec'd: `_COCKPIT_THREADS_FILE = "cockpit_threads.json"` added
to `vault_writer.py`'s file-constant block, plus `_cockpit_threads_state_path`/
`load_cockpit_threads_state`/`save_cockpit_threads_state`, placed immediately after
`save_pending_approvals_state` (byte-for-byte mirror of that trio's shape). No
existing function touched.

**Manual verification (real `.venv`, real configured vault
`<OPERATOR_VAULT_OLD>`), all steps observed as expected:**
1. `load_cockpit_threads_state()` → `None` (file absent). Confirmed.
2. `save_cockpit_threads_state({...})` → real file written at
   `.second-brain/cockpit_threads.json`, indent=2, exact content. Confirmed.
3. `load_cockpit_threads_state()` → same dict round-tripped. Confirmed.
4. Cleanup: file deleted, confirmed absent afterward.

No locked AC on this task (supports all, per the story's Implementation Tasks table)
— all 3 task-level Acceptance Criteria (not story AC-IDs) verified directly above.

gate: clear 2026-08-14 — no triggers fired (no ADR change, no assumption, no
contradiction; mechanical, byte-for-byte precedent mirror).
