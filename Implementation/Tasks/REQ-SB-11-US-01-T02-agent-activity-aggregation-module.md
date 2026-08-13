---
id: REQ-SB-11-US-01-T02
title: New app/business/agent_activity.py — cross-agent activity log aggregation + outlook_com.py::check_reachable()
parent_story: REQ-SB-11-US-01
requirement_id: REQ-SB-11
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
sprint: "SPRINT-027"
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-11-US-01-T02 — New `app/business/agent_activity.py`

## Parent Story

- Story: [[REQ-SB-11-US-01]] — `../UserStories/REQ-SB-11-US-01-agent-activity-and-error-observability.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-11 *Agent Activity & Error Observability*

---

## Objective

Add a new, read-only aggregation module composing every configured
agent's `"run_event"`/`"run_error"` history entries into one
chronological, cross-agent activity log, plus one new lightweight Outlook
COM reachability check — no new persisted state, no dependency on `T01`
(reads whatever history entries exist generically, by `kind`, not
hardcoded to today's two capture agents).

---

## Starting State → End State

**Before / Inputs:**
- `app/business/agent_registry.py::list_agents()` (`Done`) returns
  `[{"id", "name", "type"}, ...]` for every known agent.
- `app/business/agent_registry.py::get_agent(agent_id)` (`Done`).
- `app/data_access/vault_writer.py::load_agent_history(agent_id)` (`Done`)
  returns that agent's own chronological `list[dict]`
  (`{"kind", "text", "timestamp"[, "pending_approval_id"]}`).
- `app/data_access/outlook_com.py::_connect_namespace()` (`Done`) — the
  mechanism every existing Outlook read already uses; raises
  `OutlookUnavailable` on failure.

**After / Outputs:**
- `app/data_access/outlook_com.py` gains one new public function,
  `check_reachable() -> dict`.
- `app/business/agent_activity.py` exists, exposing
  `get_agent_activity() -> dict` as its one public entry point.

---

## Files to Modify

- `src/backend/app/data_access/outlook_com.py` — add, near
  `_connect_namespace`:

  ```python
  def check_reachable() -> dict:
      """One new, lightweight, real (but local, zero-external-cost)
      reachability check (REQ-SB-11) -- attempts the exact same
      Dispatch("Outlook.Application")/GetNamespace("MAPI") connection
      _connect_namespace() already makes for every real read, purely to
      report whether Outlook desktop is currently reachable. Never raises
      past its own body -- an OutlookUnavailable failure is caught and
      reported honestly, with the real underlying message, never a
      fabricated True."""
      pythoncom.CoInitialize()
      try:
          _connect_namespace()
          return {"reachable": True, "detail": None}
      except OutlookUnavailable as exc:
          return {"reachable": False, "detail": str(exc)}
  ```

  (Placed alongside `_connect_namespace`/the other module-level functions;
  `pythoncom`/`OutlookUnavailable` are already imported/defined in this
  file — no new import.)

- `src/backend/app/business/agent_activity.py` (new):

  ```python
  """Read-only aggregation of Second Brain's own background-agent-run
  history for the Agent Activity view (REQ-SB-11-US-01) -- writes no new
  persisted state at all, composes only already-existing signals from
  agent_registry and vault_writer, plus one local Outlook COM
  reachability check. Recompute fresh on every call -- no caching
  (Scenario 7).

  Scope: "run_event" (success) and "run_error" (failure) history-entry
  kinds only -- "chat_user"/"chat_agent"/"proposal" entries are excluded,
  per the story's own Constraints (they are surfaced elsewhere: each
  agent's own Communication History panel, and Pending Approvals,
  respectively).
  """
  from app.business import agent_registry
  from app.data_access import outlook_com, vault_writer

  _ACTIVITY_KINDS = {"run_event", "run_error"}


  def list_activity_log() -> list[dict]:
      """Every "run_event"/"run_error" entry across every known agent
      (agent_registry.list_agents() -- generic by agent id, not
      hardcoded to today's two capture agents, so a future capture
      agent's entries appear automatically), newest first."""
      entries: list[dict] = []
      for agent in agent_registry.list_agents():
          for entry in vault_writer.load_agent_history(agent["id"]):
              if entry["kind"] not in _ACTIVITY_KINDS:
                  continue
              entries.append({
                  "agent_id": agent["id"],
                  "agent_name": agent["name"],
                  "kind": entry["kind"],
                  "text": entry["text"],
                  "timestamp": entry["timestamp"],
              })
      entries.sort(key=lambda entry: entry["timestamp"], reverse=True)
      return entries


  def get_agent_activity() -> dict:
      return {
          "activity_log": list_activity_log(),
          "outlook_channel": outlook_com.check_reachable(),
      }
  ```

---

## Constraints

- Inherits from parent story: `business/` layer only — no HTTP framework
  import, no direct filesystem access of its own (reads
  `vault_writer.load_agent_history()`, never the file directly).
- **No new persisted state file** — this module writes nothing to
  `.second-brain/`.
- **Scope: `"run_event"`/`"run_error"` kinds only** — `"chat_user"`/
  `"chat_agent"`/`"proposal"` entries must never appear in
  `list_activity_log()`'s output.
- `check_reachable()` must never raise past its own body — any
  `OutlookUnavailable` (or, per `_connect_namespace`'s own `except
  Exception` wrapping, effectively any underlying COM failure) is caught
  and reported as `{"reachable": False, "detail": <message>}`, never left
  to propagate and 500 the whole `/agent-activity` endpoint.
- `agent_registry.py`/`vault_writer.py` are **not modified** beyond the
  one new `outlook_com.check_reachable()` addition — this module composes
  existing public functions only.
- `get_agent_activity()` must recompute fresh on every call — no
  module-level caching.
- Sort order is newest-first by `timestamp` (matching the approved
  prototype).

---

## Tests

<!-- No locked AC of its own -- this module has no HTTP surface yet
(that's T03) and no screen renders it yet (that's T04). Non-AC smoke
checks here, mirroring REQ-SB-31-US-01-T02's own identical split. -->

**Manual verification steps** (throwaway interpreter against
`src/backend`'s `.venv`; Outlook desktop running for the "reachable"
check, closed/unreachable for the other):

1. Non-AC smoke check: with the real vault's existing
   `agent_communication_history.json` (containing at least one
   `"chat_user"`/`"chat_agent"`/`"proposal"` entry from prior stories, and
   — once `T01` has run at least once — at least one `"run_event"`/
   `"run_error"` entry), call `agent_activity.list_activity_log()`
   directly. Confirm every returned entry's `kind` is `"run_event"` or
   `"run_error"` only (no chat/proposal entries leak through), each entry
   carries `agent_name` resolved correctly, and the list is sorted
   newest-first by `timestamp`.
2. Non-AC smoke check: with Outlook desktop running and reachable, call
   `outlook_com.check_reachable()` directly. Confirm
   `{"reachable": True, "detail": None}`.
3. Non-AC smoke check: with Outlook desktop closed (or otherwise
   unreachable), call `outlook_com.check_reachable()` directly. Confirm
   `{"reachable": False, "detail": <a real message containing "couldn't
   connect to Outlook">}`, no exception raised.
4. Non-AC smoke check: call `agent_activity.get_agent_activity()` with no
   history entries yet (a fresh/empty `agent_communication_history.json`,
   or before any agent has ever run) — confirm `activity_log: []`, no
   fabricated entry, no exception.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `get_agent_activity()` returns `{"activity_log", "outlook_channel"}`,
      recomputed fresh on every call
- [x] `list_activity_log()` includes only `"run_event"`/`"run_error"`-kind
      entries, across every agent returned by `agent_registry.list_agents()`,
      sorted newest-first
- [x] `outlook_com.check_reachable()` returns `{"reachable": True,
      "detail": None}` when Outlook is reachable, or `{"reachable": False,
      "detail": <real error message>}` on failure — never raises
- [x] No new `.second-brain/` state file written by this module
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `app/api/agent_activity_router.py` — `T03`.
- Any frontend page/component — `T04`.
- The `email_classification.py` honest-failure-recording fix — `T01`, no
  dependency either way (this module reads whatever history entries
  already exist, generically, regardless of whether `T01` has landed).
- Any staleness/pass-fail judgment beyond the raw `kind`/`text`/
  `timestamp` fields.

---

## Context / Notes

`agent_registry.list_agents()` already returns every known agent
(`email-capture`, `meeting-capture`, `todo-capture`, `people-producer`,
`vault-qa`) — this module deliberately iterates all of them rather than
hardcoding the two capture agents, so a future `todo-capture`
(`REQ-SB-09`) or any other capture agent's entries appear automatically
once it starts writing `"run_event"`/`"run_error"` entries, with zero
change to this file.

`check_reachable()` is sited in `outlook_com.py` (`data_access`), not
composed ad hoc by reaching into `outlook_com._connect_namespace` from
`agent_activity.py` — every other Outlook COM mechanic (`pythoncom.
CoInitialize()`, the `Dispatch`/`GetNamespace` calls, and the honest
failure-message construction) already lives there.

---

## Implementation Log

**Built 2026-08-13** exactly per the task's own sample — both files
compiled cleanly, no deviation needed. Added `finally:
pythoncom.CoUninitialize()` to `check_reachable()` (not in the task's own
literal sample) — a scope-internal judgment call (logged for human
spot-check, not an escalation): every other real Outlook COM function in
this file (`list_recent_mail`, `list_calendar_events`) pairs
`CoInitialize()`/`CoUninitialize()` in a `try/finally`; omitting it here
would leave this one function alone leaking COM apartment state on
repeated calls, with no locked Constraint requiring the omission.

**Manual verification — all real, live, against the real vault/Outlook:**

1. **`list_activity_log()` filtering/sorting (Tests step 1):** the real
   `agent_communication_history.json` (140 real `"run_event"` entries,
   plus 44 `"chat_user"`/37 `"chat_agent"`/11 `"proposal"` real entries
   confirmed present via direct inspection) produced a `list_activity_log()`
   output containing **only** `"run_event"`/`"run_error"` entries — zero
   chat/proposal leakage, confirmed by counting kinds in both the raw file
   and the function's own output. Sorted newest-first (confirmed:
   `meeting-capture`'s later timestamp precedes `email-capture`'s earlier
   one in the real output). Each entry's `agent_name` resolved correctly
   (`"Meeting Capture"`, `"Email Capture"`, etc.). PASS.
2. **`check_reachable()` reachable (Tests step 2):** with Outlook desktop
   running, direct call returned `{"reachable": True, "detail": None}`.
   PASS.
3. **`check_reachable()` unreachable (Tests step 3):** physically closing
   Outlook (`Stop-Process`) did **not** produce a genuine unreachable
   state on this machine — Windows COM `Dispatch("Outlook.Application")`
   silently auto-relaunches Outlook.exe (confirmed live: Outlook's own
   process `StartTime` advanced immediately after the kill). Per this
   project's own established "in-process monkeypatch of a real,
   already-loaded dependency to induce a failure condition" pattern
   (`Learnings.md`, `SPRINT-018`), `outlook_com._connect_namespace` was
   monkeypatched in-process to raise a real `OutlookUnavailable`;
   `check_reachable()` correctly returned `{"reachable": False, "detail":
   "INDUCED-VERIFY: ..."}`, never raising past its own body, and reverted
   to `{"reachable": True, "detail": None}` immediately after the
   monkeypatch was removed — no caching, no stuck state. PASS.
4. **`get_agent_activity()` empty state (Tests step 4):** with the real
   `agent_communication_history.json` moved aside, `get_agent_activity()`
   returned `{"activity_log": [], "outlook_channel": {"reachable": True,
   "detail": None}}` — no exception, no fabricated entry. Confirmed both
   via a direct call and via the live `GET /agent-activity` endpoint (T03)
   reflecting the same state with no caching. File restored immediately
   after. PASS.

`gate: clear` 2026-08-13 — no MUST-FLAG trigger fired: the
`CoUninitialize()` addition is a scope-internal judgment call matching
this file's own existing convention, not a new assumption; the physical-
vs-monkeypatch substitution for step 3 is the same disclosed,
already-established technique this project's own Learnings document, not
a weakened check.
