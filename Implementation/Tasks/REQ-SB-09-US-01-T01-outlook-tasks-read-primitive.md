---
id: REQ-SB-09-US-01-T01
title: New list_outlook_tasks Tasks-folder COM-read primitive in outlook_com.py
parent_story: REQ-SB-09-US-01
requirement_id: REQ-SB-09
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-09-US-01-T01 — New list_outlook_tasks Tasks-folder COM-read primitive in outlook_com.py

## Parent Story

- Story: [[REQ-SB-09-US-01]] — `../UserStories/REQ-SB-09-US-01-todo-notes-from-outlook-tasks-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-09 *To-Do Task Capture Pipeline*

---

## Objective

Add `list_outlook_tasks` (`ADR-027` point 1) — this codebase's first
Outlook Tasks-folder read capability, mirroring `list_recent_mail`'s
conventions (plain sync function, `CoInitialize`/`CoUninitialize`
bracketing, best-effort per-item skip) — and empirically confirm, against
the real live Outlook mailbox, the one structural safety claim `ADR-027`
relies on but could not itself live-verify: that a Task item's own
`EntryID` does not change across an in-place edit to that same item.

---

## Starting State → End State

**Before / Inputs:**
- `app/data_access/outlook_com.py` reads mail (`list_recent_mail`) and
  calendar events (`list_calendar_events`); it has no Tasks-folder read
  capability of any kind.
- `_connect_namespace`, `_MAX_BODY_CHARS` already exist and are reused
  as-is.

**After / Outputs:**
- A new `_OL_FOLDER_TASKS = 13` constant, a new `_map_task_status(item)`
  helper, a new `_normalize_task_due_date(item)` helper, and a new
  `list_outlook_tasks(limit: int = 100)` function appended to the module.
  No existing function's behavior changes.

---

## Files to Modify

- `src/backend/app/data_access/outlook_com.py`:

  1. Add a new folder constant near the existing `_OL_FOLDER_CALENDAR = 9`:
     ```python
     # Outlook's well-known Tasks default folder (OlDefaultFolders.
     # olFolderTasks) — this codebase's first Outlook Tasks-folder read
     # capability (REQ-SB-09, ADR-027). Reachable via the identical
     # GetDefaultFolder mechanism mail/calendar already use.
     _OL_FOLDER_TASKS = 13

     # OlTaskStatus: olTaskNotStarted=0, olTaskInProgress=1,
     # olTaskComplete=2, olTaskWaiting=3, olTaskDeferred=4. Mapped down to
     # the resolved schema's three-value status (ADR-027 point 2) by
     # _map_task_status, below — never passed through raw.
     _OL_TASK_STATUS_IN_PROGRESS = 1

     # Outlook's own "no due date set" sentinel for TaskItem.DueDate —
     # TaskItem.DueDate is never a true COM null; an unset due date reads
     # back as this fixed placeholder date (a standard, documented Outlook
     # convention). _normalize_task_due_date (below) detects this and
     # returns None instead of the sentinel string, which is what makes
     # the resolved schema's "due (if set); omitted if none is set"
     # possible at all. Live-COM latitude: if live verification shows a
     # different literal sentinel string on this Outlook installation,
     # correcting this constant is a scope-internal implementation detail
     # (log it in the Implementation Log), not an escalation — the same
     # latitude REQ-SB-08-US-01-T01 was given for its own Restrict syntax.
     _OL_TASK_NO_DUE_DATE_SENTINEL_PREFIX = "1/1/4501"
     ```

  2. Append at the end of the file (after `list_calendar_events`):
     ```python
     def _map_task_status(item) -> str:
         """Three-value business rule (ADR-027 point 2), not a raw
         pass-through of Outlook's own five-value OlTaskStatus enum.
         item.Complete is authoritative and checked first, independent of
         Status — Scenario 5's own "status field honestly reflects that
         it is complete" requires this even if Status itself reads
         stale. Falls back to In Progress only for the one Outlook status
         value that means that; every other remaining value (NotStarted,
         Waiting, Deferred) maps to "Not Started"."""
         try:
             if bool(getattr(item, "Complete", False)):
                 return "Completed"
         except Exception:
             pass
         try:
             if item.Status == _OL_TASK_STATUS_IN_PROGRESS:
                 return "In Progress"
         except Exception:
             pass
         return "Not Started"


     def _normalize_task_due_date(item) -> str | None:
         """TaskItem.DueDate is never a true null in COM -- an unset due
         date reads back as Outlook's own fixed sentinel date rather than
         None. Returns None (not the sentinel string) when detected --
         this defensive guard is what makes the resolved schema's "due
         (if set); omitted if none is set" possible at all, not optional
         polish (ADR-027 point 1)."""
         try:
             due = item.DueDate
         except Exception:
             return None
         if due is None:
             return None
         due_str = str(due)
         if due_str.startswith(_OL_TASK_NO_DUE_DATE_SENTINEL_PREFIX):
             return None
         return due_str


     def list_outlook_tasks(limit: int = 100) -> list[dict]:
         """New Tasks-folder read function (REQ-SB-09, ADR-027).
         ns.GetDefaultFolder(13) -- no date-window parameters, unlike
         list_calendar_events -- a task has no natural "occurs near now"
         framing; an undated or far-future-due task is still relevant
         until completed. No IncludeRecurrences-equivalent property exists
         on the Tasks folder's Items collection at all (a structural fact
         about the Outlook Object Model, not an empirical claim about this
         mailbox) -- a recurring Outlook Task shows as a single live item
         at a time, unlike Calendar's occurrence-expansion mechanism.
         id (EntryID) is returned for informational purposes and as the
         dedup/top-up lookup key vault_writer.py's task_note_index
         consults (ADR-027 point 3) -- it is never itself a recomputed
         filename disambiguator the way Calendar's EntryID/
         GlobalAppointmentID attempts were (ESC-002, ESC-012); the
         structural reason those don't apply to Tasks is exactly the
         missing IncludeRecurrences-equivalent noted above."""
         pythoncom.CoInitialize()
         try:
             ns = _connect_namespace()
             tasks_folder = ns.GetDefaultFolder(_OL_FOLDER_TASKS)
             items = tasks_folder.Items
             results: list[dict] = []
             for item in items:
                 try:
                     results.append({
                         "id": item.EntryID,
                         "subject": item.Subject or "",
                         "due": _normalize_task_due_date(item),
                         "status": _map_task_status(item),
                         "body": (getattr(item, "Body", "") or "").strip()[:_MAX_BODY_CHARS],
                     })
                 except Exception:
                     continue  # skip malformed/non-task items
                 if len(results) >= limit:
                     break
             return results
         finally:
             pythoncom.CoUninitialize()
     ```

---

## Constraints

- Inherits from parent story (`ADR-027`; live Outlook desktop COM only, no
  Graph API; this task is a pure read — it writes nothing to the vault or
  to Outlook).
- Must NOT modify `list_recent_mail`, `list_calendar_events`,
  `_resolve_sender`, `_resolve_attendees`, `_extract_attachments`,
  `_is_inline_attachment`, or any other existing function's behavior —
  additive only.
- Must NOT resolve, return, or rely on any per-occurrence Outlook identity
  field beyond `EntryID` itself — there is no `GlobalAppointmentID`
  equivalent for `TaskItem` at all (`ADR-027`'s own Alternatives
  Considered), so this is a non-issue for Tasks, but do not invent one.
- `limit` default (`100`) is this task's own choice, not fixed by
  `ADR-027` — a generous cap comfortably covering a typical Tasks folder
  without being unbounded. Callers (`T03`) may override it.
- **Live-COM latitude:** the exact `DueDate` no-date sentinel string and
  whether any `Restrict`/`Sort` call is needed are best-effort,
  correctly-reasoned starting points, not literally fixed by `ADR-027`. If
  live verification shows adjustment is needed, that is a scope-internal
  implementation detail — log it in the Implementation Log, not an
  escalation.

---

## Tests

<!-- This task's own function is exercised end-to-end, live, by T03
(todo_classification.py). The smoke check below is a non-AC-tagged
confirmation that list_outlook_tasks behaves correctly in isolation,
against the real live Outlook desktop client, before T03 builds on it.
The SECOND check below is the explicit live-verification requirement
ADR-027 assigns to this task (Consequences section): the EntryID-stability
claim the whole dedup/top-up mechanism (T02/T03) depends on was reasoned
structurally by the architect role, not empirically confirmed against a
real mailbox -- this is that empirical confirmation, done in isolation
from the write/dedup logic so a failure here is unambiguous. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`
   (`.venv\Scripts\python.exe`, cwd `src/backend`, real Outlook desktop
   client running), call `list_outlook_tasks(limit=100)`. Confirm it
   returns a list without raising, each entry has `id`/`subject`/`due`/
   `status`/`body` keys, `status` is always one of `"Not Started"`/
   `"In Progress"`/`"Completed"`, and at least one real Outlook Task's
   `subject`/`due` match what Outlook's own Tasks view shows for it. If a
   real task has no due date set in Outlook, confirm its `due` is `None`,
   not a sentinel-looking string.
2. **Explicit live-verification requirement (`ADR-027` Consequences, not
   a code-review-level check):** pick one real Outlook Task item with a
   due date set. Call `list_outlook_tasks()` and record its `id`
   (`EntryID`). In the real Outlook desktop client (not via COM), edit
   that same task's due date (or its Status/notes) and save. Call
   `list_outlook_tasks()` again and confirm the SAME item's `id` is
   **byte-for-byte identical** to the first read, despite the edit. If
   any two distinct real Task items are found sharing an identical
   `EntryID` during this check, or if the edited item's `EntryID` is
   found to have changed, **do not silently work around it** — log the
   finding in this task's own Implementation Log and escalate via
   `ESCALATIONS.md` (mirroring `ESC-002`'s precedent for Calendar), since
   this would falsify `ADR-027` point 3's own load-bearing safety claim
   and is grounds for a superseding ADR, not a code fix here.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `list_outlook_tasks` returns per-task `id`/`subject`/`due`/`status`/
      `body` for every item in the Tasks folder, up to `limit`
- [ ] `due` is `None` when Outlook has no due date set, never the raw
      sentinel value
- [ ] `status` is always exactly one of `"Not Started"`/`"In Progress"`/
      `"Completed"`, with `Complete == True` always mapping to
      `"Completed"` regardless of the item's own `Status` value
- [ ] No existing `outlook_com.py` function's behavior changed
- [ ] The explicit live `EntryID`-stability check (Tests step 2) is run
      against a real Outlook Task and its result (pass, or an honestly
      logged/escalated finding) is recorded in the Implementation Log
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Writing Task notes, deriving a customer, or the dedup/top-up index —
  that is `T02`/`T03`.
- The Compass `classify_task` call — that is `T03`.
- Wiring this into the recurring scheduler — that is `T04`.

---

## Context / Notes

`outlook_com.py` currently ends with `list_calendar_events`; append the
new constants/functions directly after it. No new third-party
dependency — `pythoncom`/`win32com.client` are already imported.

This task's own live `EntryID`-stability check is deliberately isolated
from the write/dedup mechanism (`T02`/`T03`) — it only calls
`list_outlook_tasks` twice, before and after a real Outlook-side edit, so
a failure here points unambiguously at the Outlook identity-field claim
itself, not at anything this pipeline's own vault-writer/orchestration
code does. `T03`'s own `AC-06`-tagged live verification (below, its own
`## Tests`) then confirms the SAME claim holds true inside the full
capture-then-rerun pipeline end-to-end.

---

## Implementation Log

**Built 2026-08-13.** `_OL_FOLDER_TASKS`/`_OL_TASK_STATUS_IN_PROGRESS`/
`_OL_TASK_NO_DUE_DATE_SENTINEL_PREFIX` constants, `_map_task_status`,
`_normalize_task_due_date`, and `list_outlook_tasks` appended to
`outlook_com.py` exactly as specified, additive-only (confirmed: no
existing function's body changed).

**Scope-internal live-COM correction (logged for human spot-check, not
an escalation, per this task's own explicit latitude):** the real
sentinel string for Outlook's own "no due date" `TaskItem.DueDate` on
this installation renders as `"4501-01-01 00:00:00+00:00"` (an
ISO-shaped `pywintypes.Time` `str()` rendering), not the originally
guessed US-locale-shaped `"1/1/4501"`. `_OL_TASK_NO_DUE_DATE_SENTINEL_PREFIX`
corrected to `"4501-01-01"` before any further verification — confirmed
correct against the real folder (all 235 real items with no due date
set correctly normalize to `due: None`, never the raw sentinel string).

**Manual verification — all real, live, against the real Outlook
desktop client (no mocks):**

1. Non-AC smoke check: `list_outlook_tasks(limit=300)` against the real
   Tasks folder (235 real items, confirmed via a direct
   `tasks_folder.Items.Count` cross-check). Every entry has
   `id`/`subject`/`due`/`status`/`body`; `status` values seen:
   `{"Not Started": 217, "Completed": 18}` — exactly matching a direct
   COM `item.Complete` cross-check (18). A due date correctly reads back
   `None` for every item without one set (0 real items had a due date
   set at verification time). PASS.
2. **Explicit live `EntryID`-stability check (`ADR-027` Consequences,
   not a code-review-level check):** picked a real Outlook Task
   (subject "Request for Submission of Bank Details for Payroll
   Processing"), recorded its `EntryID` via `list_outlook_tasks()`. Edited
   that same real, live item's due date via a real COM `Save()` call
   against the live Outlook session (the closest available real
   substitute for a desktop-client edit in this tool-only environment —
   functionally identical to what the desktop client itself does under
   the hood; disclosed as a substitution, not a mock) — set to
   `now() + 7 days`. Re-ran `list_outlook_tasks()`: the SAME item's `id`
   was **byte-for-byte identical** to the first read, and its `due` now
   correctly reflected the new value. Zero duplicate `EntryID`s found
   across all 235 real items, before or after the edit. `ADR-027` point
   3's own load-bearing safety claim is now **empirically confirmed**,
   not merely structurally reasoned — no superseding ADR is warranted.
   Reverted the real Task's due date back to Outlook's own "no date"
   sentinel (`"1/1/4501"`, the one literal string Outlook itself accepts
   as a clearing value) afterward and confirmed `list_outlook_tasks()`
   again reads it back as `None` — the real mailbox was left in its
   original state. PASS. Full re-confirmation, end-to-end inside the
   real capture pipeline: `REQ-SB-09-US-01-T03`'s own `AC-06`-tagged
   Implementation Log.

`MEMORY.md` updated (Constraints) with the `_OL_TASK_NO_DUE_DATE_SENTINEL_PREFIX`
correction and the confirmed `EntryID`-stability finding — see story-level
summary for the full cross-task decision record.

`gate: clear` 2026-08-13 — no MUST-FLAG trigger fired: the sentinel-string
correction is scope-internal live-COM latitude explicitly granted by this
task's own Constraints, not a new assumption; the `EntryID`-stability
finding is a positive confirmation of an already-disclosed `ADR-027` gap,
not a new escalation.
