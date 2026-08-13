---
id: REQ-SB-21-US-01-T01
title: Add agent_working_modes.json / agent_pending_approvals.json load/save primitives to vault_writer.py + widen append_agent_history_entry with an optional pending_approval_id
parent_story: REQ-SB-21-US-01
requirement_id: REQ-SB-21
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-12
updated: 2026-08-12
---

**Re-confirmed unchanged, 2026-08-12 (`ADR-020` decomposer pass).** `ADR-020`
supersedes `ADR-018` points 3/5 only — this task's own scope (`ADR-018`
points 1, 2, 7) is untouched; no AC of its own, no renumbering needed.

# REQ-SB-21-US-01-T01 — Working Modes / Pending Approvals vault_writer.py primitives

## Parent Story

- Story: [[REQ-SB-21-US-01]] — `../UserStories/REQ-SB-21-US-01-agent-working-modes.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-21 *Agent Working Modes*

---

## Objective

Add the paired `load_working_modes_state()`/`save_working_modes_state()`
and `load_pending_approvals_state()`/`save_pending_approvals_state()`
pure-I/O primitives for the eighth and ninth `.second-brain/` state files
(`ADR-018` points 1–2) — no business rules (self-healing default,
idempotency) here, that lives in `T02`/`T03`. Also additively widens the
existing `append_agent_history_entry` with an optional
`pending_approval_id` parameter (`ADR-018` point 7's new `"proposal"`
history-entry kind).

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.py` already carries `load_sections_state`/
  `save_sections_state` and `load_providers_state`/`save_providers_state`
  (`ADR-014`) as the exact shape precedent for the two new pairs this task
  adds.
- `append_agent_history_entry(agent_id: str, kind: str, text: str) -> None`
  exists, called by `agents_router.py` (`chat`, `trigger_action`) and
  `email_classification.py` (`run_capture_and_record_completion`).

**After / Outputs:**
- Four new functions appended to `vault_writer.py`:
  `load_working_modes_state() -> dict | None`,
  `save_working_modes_state(state: dict) -> None`,
  `load_pending_approvals_state() -> dict | None`,
  `save_pending_approvals_state(state: dict) -> None`.
- `append_agent_history_entry` gains an optional
  `pending_approval_id: str | None = None` parameter — every existing
  call site (positional `agent_id, kind, text`) is unaffected; only a
  caller that supplies it (a `"proposal"`-kind entry, `T04`/`T05`) gets a
  `pending_approval_id` key in the stored entry.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add two new constants
  alongside `_AGENT_SECTIONS_FILE`/`_AGENT_PROVIDERS_FILE`:
  ```python
  _AGENT_WORKING_MODES_FILE = "agent_working_modes.json"
  _AGENT_PENDING_APPROVALS_FILE = "agent_pending_approvals.json"
  ```
  Append at the end of the file:
  ```python
  def _working_modes_state_path():
      state_dir = settings.vault_path / _STATE_DIR
      state_dir.mkdir(parents=True, exist_ok=True)
      return state_dir / _AGENT_WORKING_MODES_FILE


  def load_working_modes_state() -> dict | None:
      """Pure I/O — returns None if agent_working_modes.json doesn't exist
      yet (no default content is computed here, per ADR-003; the
      self-healing "autonomous" default is a business-layer decision,
      owned by app/business/working_mode_registry.py, ADR-018 point 1)."""
      path = _working_modes_state_path()
      if not path.exists():
          return None
      return json.loads(path.read_text(encoding="utf-8"))


  def save_working_modes_state(state: dict) -> None:
      path = _working_modes_state_path()
      path.write_text(json.dumps(state, indent=2), encoding="utf-8")


  def _pending_approvals_state_path():
      state_dir = settings.vault_path / _STATE_DIR
      state_dir.mkdir(parents=True, exist_ok=True)
      return state_dir / _AGENT_PENDING_APPROVALS_FILE


  def load_pending_approvals_state() -> dict | None:
      """Pure I/O — returns None if agent_pending_approvals.json doesn't
      exist yet (ADR-003; the empty-list seed and idempotency guard are
      app/business/pending_approval_registry.py's own concern, ADR-018
      point 2)."""
      path = _pending_approvals_state_path()
      if not path.exists():
          return None
      return json.loads(path.read_text(encoding="utf-8"))


  def save_pending_approvals_state(state: dict) -> None:
      path = _pending_approvals_state_path()
      path.write_text(json.dumps(state, indent=2), encoding="utf-8")
  ```
  Replace the existing `append_agent_history_entry` with this additively
  widened version (same function, one new optional parameter):
  ```python
  def append_agent_history_entry(
      agent_id: str, kind: str, text: str, pending_approval_id: str | None = None,
  ) -> None:
      """Appends one entry to agent_id's chronological history list
      (ADR-011) — kind is "chat_user" | "chat_agent" | "run_event" |
      "proposal" (ADR-018 point 7 adds "proposal"). pending_approval_id is
      new and optional, additive — every existing caller (positional
      agent_id/kind/text, no fourth argument) is unaffected; only a
      "proposal"-kind entry supplies it, carrying the pending-approval
      record's own id so the frontend can resolve the card's live
      Pending/Approved/Declined status via GET /pending-approvals/{id}.
      Entries are appended in call order and read back in that same
      order (load_agent_history does not re-sort)."""
      path = _agent_history_path()
      index = _load_agent_history_index()
      entry = {
          "kind": kind,
          "text": text,
          "timestamp": datetime.now(timezone.utc).isoformat(),
      }
      if pending_approval_id is not None:
          entry["pending_approval_id"] = pending_approval_id
      index.setdefault(agent_id, []).append(entry)
      path.write_text(json.dumps(index, indent=2), encoding="utf-8")
  ```

---

## Constraints

- Inherits from parent story: `ADR-018` points 1, 2, and 7's exact file/
  entry shapes — this task does not enforce them (pure I/O for the state
  files; the history-entry widening is a mechanical, additive parameter
  add), enforcement of the *content* shape is `T02`/`T03`'s job.
- This file lives in `data_access/` only — no business rules (seeding,
  self-healing default, idempotency guard) belong here.
- Must NOT change the behavior of any existing call to
  `append_agent_history_entry` that omits the new fourth argument — the
  stored entry dict for those calls must be byte-for-byte identical to
  before this task (no `pending_approval_id` key present at all when not
  supplied, not even `null`).
- Must NOT modify any other existing `vault_writer.py` function.

---

## Tests

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`
   (real `vault_path`), confirm `load_working_modes_state()` and
   `load_pending_approvals_state()` both return `None` when their files
   don't yet exist. Call `save_working_modes_state({"assignments":
   {"test-agent": "autonomous"}})`; confirm the file now exists with that
   exact content, and `load_working_modes_state()` returns it verbatim.
   Call `save_pending_approvals_state({"pending": [{"id": "test123"}]})`;
   confirm the same round-trip. Delete both throwaway files afterward —
   `T02`/`T03`'s own verification will re-seed them.
2. Non-AC smoke check: call `append_agent_history_entry("email-capture",
   "run_event", "smoke check — no pending_approval_id")` (three
   positional args, unchanged call shape). Confirm via
   `load_agent_history("email-capture")` that the newly appended entry
   has exactly the keys `kind`/`text`/`timestamp` — no
   `pending_approval_id` key present at all. Call
   `append_agent_history_entry("email-capture", "proposal", "smoke check
   — with pending_approval_id", pending_approval_id="abc123")`; confirm
   the new entry additionally has `"pending_approval_id": "abc123"`. Both
   throwaway entries are harmless (append-only history, `ADR-011`) — no
   cleanup needed, but note them so `T04`'s live verification isn't
   confused by stray smoke-check entries at the top of history.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `load_working_modes_state()`/`load_pending_approvals_state()` return
      `None` when their file doesn't exist, else the parsed JSON dict
- [ ] `save_working_modes_state(state)`/`save_pending_approvals_state
      (state)` write `state` verbatim as indented JSON
- [ ] `append_agent_history_entry`'s existing 3-positional-argument call
      shape is unaffected — no `pending_approval_id` key when omitted
- [ ] `append_agent_history_entry(..., pending_approval_id=...)` stores
      that value under a `pending_approval_id` key
- [ ] No other existing `vault_writer.py` function's behavior changed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Self-healing default working-mode assignment, `get_agent_working_mode`/
  `set_agent_working_mode` — `T02` (`working_mode_registry.py`).
- Pending-approval CRUD, the background-trigger idempotency guard,
  `create_pending_approval`/`resolve_pending_approval` — `T03`
  (`pending_approval_registry.py`).
- Any API surface — `T04` (`agents_router.py`), `T06`
  (`pending_approvals_router.py`).

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-018` created at
`/plan-tasks` step 1, plus a flagged material assumption on the
Manual-vs-Supervised chat-trigger distinction, `ADR-018` point 5) — the
human reviews `ADR-018` and this task breakdown together; the pipeline
does not halt, so this task proceeds to `Ready` alongside the rest of the
story.

This task carries no AC-tagged step of its own — its two locked-AC
consumers (`T04`'s gate, `T05`'s background gate) verify the
`pending_approval_id` field's real effect live, against the real backend.

---

## Implementation Log

**2026-08-12, coder (`/implement-sprint`, `SPRINT-021`).** Built exactly
as specified — `load_working_modes_state`/`save_working_modes_state`,
`load_pending_approvals_state`/`save_pending_approvals_state` added to
`vault_writer.py`; `append_agent_history_entry` widened with the
optional `pending_approval_id` parameter, additive.

No locked AC of its own (per this task's own Notes) — verified via the
Tests block's non-AC smoke checks, live, against the real backend
`.venv`/vault:
1. `load_working_modes_state()`/`load_pending_approvals_state()` both
   returned `None` before either file existed; `save_*`/`load_*`
   round-tripped `{"assignments": {"test-agent": "autonomous"}}` and
   `{"pending": [{"id": "test123"}]}` verbatim; both throwaway files
   deleted afterward. PASS.
2. `append_agent_history_entry("email-capture", "run_event", "smoke
   check — no pending_approval_id")` produced an entry with exactly
   `kind`/`text`/`timestamp` keys (no `pending_approval_id` at all).
   `append_agent_history_entry("email-capture", "proposal", "...",
   pending_approval_id="abc123")` produced an entry additionally
   carrying `"pending_approval_id": "abc123"`. PASS.

**Live-discovered follow-up (not this task's own fault, recorded for
the record):** the throwaway `"proposal"`-kind smoke-check entry
(`pending_approval_id="abc123"`) left in place per this task's own
"no cleanup needed" note turned out to interact with `T07`'s later
rendering logic — `T07`'s `ProposalCard` fetches every `"proposal"`
entry's live status, and `"abc123"` has no real backend record, so it
produced a real `404`/unhandled-promise-rejection during `T07`'s own
console-error check. Removed directly from the real
`.second-brain/agent_communication_history.json` (one entry pruned,
"email-capture" 135→134) once discovered, and `T07`'s own effect was
hardened with a `.catch(() => {})` so a future unresolvable id degrades
gracefully instead of crashing the console. See `T07`'s own
Implementation Log for the full finding.

Gate: `clear` — no MUST-FLAG trigger fired (no new dependency, no
shared-interface change beyond what the task itself specified, no ADR
deviation, no unanticipated file, no unclear requirement).
