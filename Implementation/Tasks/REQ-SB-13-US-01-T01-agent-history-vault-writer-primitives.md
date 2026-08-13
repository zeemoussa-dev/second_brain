---
id: REQ-SB-13-US-01-T01
title: New append_agent_history_entry / load_agent_history primitives, backed by .second-brain/agent_communication_history.json
parent_story: REQ-SB-13-US-01
requirement_id: REQ-SB-13
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-13-US-01-T01 — New agent-history vault_writer primitives

## Parent Story

- Story: [[REQ-SB-13-US-01]] — `../UserStories/REQ-SB-13-US-01-embedded-agent-chat-and-communication-history.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-13 *Embedded Agent Chat & Communication History*

---

## Objective

Add a fourth `.second-brain/` flat-JSON-file state file,
`agent_communication_history.json`, plus its
`append_agent_history_entry(agent_id, kind, text)` /
`load_agent_history(agent_id)` primitives — mirroring
`record_capture_run_completed()`/`load_last_capture_run()`'s exact existing
shape — per `ADR-011`'s persistence decision.

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.py` already has three `.second-brain/` state files:
  `processed_email_ids.json`, `conversation_index.json`,
  `last_capture_run.json`, each with its own `_<name>_path()` helper
  (`state_dir.mkdir(parents=True, exist_ok=True)` + return the file path).

**After / Outputs:**
- A new `_AGENT_HISTORY_FILE = "agent_communication_history.json"` constant,
  a new `_agent_history_path()` helper, and new
  `append_agent_history_entry(agent_id: str, kind: str, text: str) -> None`
  / `load_agent_history(agent_id: str) -> list[dict]` functions appended to
  `vault_writer.py`. No existing function's behavior changes.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py`:

  1. Add the new state-file constant near the existing three:
     ```python
     _AGENT_HISTORY_FILE = "agent_communication_history.json"
     ```

  2. Append at the end of the file (after `load_last_capture_run`):
     ```python
     def _agent_history_path():
         state_dir = settings.vault_path / _STATE_DIR
         state_dir.mkdir(parents=True, exist_ok=True)
         return state_dir / _AGENT_HISTORY_FILE


     def _load_agent_history_index() -> dict[str, list[dict]]:
         path = _agent_history_path()
         if not path.exists():
             return {}
         return json.loads(path.read_text(encoding="utf-8"))


     def append_agent_history_entry(agent_id: str, kind: str, text: str) -> None:
         """Appends one entry to agent_id's chronological history list
         (ADR-011) — kind is "chat_user" | "chat_agent" | "run_event".
         Entries are appended in call order and read back in that same
         order (load_agent_history does not re-sort) — every caller
         (scheduler, app-start, /poc/classify-emails,
         POST /agents/{id}/chat, POST /agents/{id}/actions/{action_id})
         already calls this at the moment the event actually happens, so
         append order already is chronological order."""
         path = _agent_history_path()
         index = _load_agent_history_index()
         index.setdefault(agent_id, []).append({
             "kind": kind,
             "text": text,
             "timestamp": datetime.now(timezone.utc).isoformat(),
         })
         path.write_text(json.dumps(index, indent=2), encoding="utf-8")


     def load_agent_history(agent_id: str) -> list[dict]:
         return _load_agent_history_index().get(agent_id, [])
     ```

---

## Constraints

- Inherits from parent story: `ADR-011`'s persistence decision (one combined
  `.second-brain/agent_communication_history.json`, keyed by `agent_id`, not
  per-agent files or a database).
- Must NOT modify `processed_email_ids.json`/`conversation_index.json`/
  `last_capture_run.json` or any of their existing helper functions —
  additive only.
- `kind` is a free-form string this layer does not validate against an enum
  — callers (`T03`'s `agent_chat.py`, `T04`'s capture-completion hook, `T05`'s
  router) are responsible for passing one of `"chat_user"`/`"chat_agent"`/
  `"run_event"`, per `ADR-011`.
- `load_agent_history` returns entries in append order (chronological, since
  every caller appends at the moment the event happens) — it does not sort
  by `timestamp` itself.

---

## Tests

<!-- Exercised end-to-end, live, by T05's router endpoints, where this
story's locked ACs are tagged. The smoke check below confirms this
primitive pair in isolation first. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv` (cwd
   `src/backend`, real vault configured), call
   `append_agent_history_entry("email-capture", "run_event", "Test entry
   one")`, then `append_agent_history_entry("email-capture", "chat_user",
   "Test entry two")`. Confirm
   `.second-brain/agent_communication_history.json` now exists in the real
   vault and contains an `"email-capture"` key with a 2-entry list, each
   entry having `kind`/`text`/`timestamp` keys, in the order appended.
   Confirm `load_agent_history("email-capture")` returns that same 2-entry
   list. Confirm `load_agent_history("some-other-agent")` returns `[]`.
   **Manually remove the two test entries from the JSON file afterward**
   (or delete the file if it contained nothing else) so this smoke check
   leaves no stray test data behind for `T04`/`T05`'s own verification.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `append_agent_history_entry(agent_id, kind, text)` appends one
      `{"kind", "text", "timestamp"}` entry to `agent_id`'s list in
      `.second-brain/agent_communication_history.json`
- [ ] `load_agent_history(agent_id)` returns that agent's entry list in
      append order, or `[]` for an unknown agent
- [ ] No existing `vault_writer.py` function's behavior changed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Calling these primitives from `email_classification.py` — that is `T04`.
- Calling these primitives from the chat/action-trigger flow — that is `T03`/`T05`.
- Any history read/merge-with-chat logic — that is `T05`/`T08` (frontend).

---

## Context / Notes

`datetime`/`timezone` are already imported in `vault_writer.py` (used by
`record_capture_run_completed`) — no new import needed.

**Gating note:** this story is `gate: flagged` (`ADR-011` created at
`/plan-tasks` step 1) — the human reviews `ADR-011` and this task breakdown
together; the pipeline does not halt (per `Pipeline.md`'s gating contract),
so this task proceeds to `Ready` alongside the rest of the story.

---

## Implementation Log

**2026-08-11, coder pass.** Added `_AGENT_HISTORY_FILE`,
`_agent_history_path()`, `_load_agent_history_index()`,
`append_agent_history_entry()`, `load_agent_history()` to
`app/data_access/vault_writer.py`, appended at the end of the file exactly
per this task's own spec — no existing function touched. `vault_writer.py`
had been concurrently edited on disk since this task was authored (other
in-flight sprints); re-read fresh immediately before editing, confirmed the
only difference from the task's assumed "Before" state was unrelated
Partner-migration functions further up the file — purely additive, no
conflict.

Non-AC smoke check (superseded by a live end-to-end check instead of the
literal isolated-shell steps, since T05's router was built in the same
pass): confirmed via `T05`'s own live `GET /agents/email-capture/history`
smoke check (see `T05`'s Implementation Log) that entries appended by
`append_agent_history_entry` round-trip correctly through
`load_agent_history` in append order, and that an untouched agent
(`meeting-capture`, kept deliberately untriggered — see `T05`'s Log for
why) returns `[]`. This is a stronger, real end-to-end confirmation of the
same contract the isolated shell script would have shown, using the real
vault the whole story is built and verified against; no stray test data
left behind since only real entries were written.

- [x] `append_agent_history_entry(agent_id, kind, text)` appends one entry — confirmed live via T05/T08
- [x] `load_agent_history(agent_id)` returns append order, `[]` for unknown agent — confirmed live
- [x] No existing `vault_writer.py` function's behavior changed — confirmed by diff review
- [x] `MEMORY.md` updated — yes, see Decisions entry for SPRINT-010
- [x] `CHANGELOG.md` entry appended — yes

Assumption (scope-internal, logged for spot-check): substituted the live
end-to-end verification (via T05's router, against the real vault) for the
literal isolated-Python-shell smoke script this task's own `## Tests`
described, since T05 was built in the same pass and exercises the exact
same code path against real data — avoids a redundant, disposable
throwaway test-data write/cleanup cycle against the real vault.
