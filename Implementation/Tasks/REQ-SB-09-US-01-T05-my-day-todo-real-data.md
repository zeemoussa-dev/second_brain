---
id: REQ-SB-09-US-01-T05
title: Real GET /my-day/todo + dashboard count, replacing the hardcoded-0 stub
parent_story: REQ-SB-09-US-01
requirement_id: REQ-SB-09
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-09-US-01-T02, REQ-SB-09-US-01-T03]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-09-US-01-T05 — Real GET /my-day/todo + dashboard count

## Parent Story

- Story: [[REQ-SB-09-US-01]] — `../UserStories/REQ-SB-09-US-01-todo-notes-from-outlook-tasks-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-09 *To-Do Task Capture Pipeline*

---

## Objective

`GET /my-day/todo` moves from "always `[]`, hardcoded, no vault read at
all" to a real read over `Work/Tasks/` notes, and `summary()`'s `todo`
object moves from the hardcoded `{"count": 0}` to a real count — the
architecture.md "To-Do real data" amendment. Same shape as
`REQ-SB-22-US-01`'s/`REQ-SB-30-US-01`'s own amendments: an ordinary
extension of already-`Accepted` `my_day.py` structure, no new endpoint
contract shape (the response shape was already declared by
`REQ-SB-12-US-02`, just previously unpopulated).

---

## Starting State → End State

**Before / Inputs:**
- `my_day.py::summary()` hardcodes `"todo": {"count": 0}`.
- `my_day_router.py::get_todo()` hardcodes `return []`, with no vault read
  at all.
- `T02`/`T03` established the Task-note schema: notes live under
  `Work/Tasks/`, with `subject`/`customer` (absent if no match)/`due`
  (absent if unset)/`status` (`Not Started`/`In Progress`/`Completed`)
  frontmatter fields.
- `vault_writer.list_notes_in_kind_folder(kind)` already exists (used by
  `list_email_items`/`list_calendar_items`) — no new `vault_writer.py`
  primitive is needed for this task.

**After / Outputs:**
- `my_day.py` gains `list_todo_items()`, mirroring
  `list_email_items()`/`list_calendar_items()`'s existing shape:
  `[{"subject", "customer", "due"}]`, filtered to still-open tasks only
  (`status != "Completed"`), with **no date-window filtering** (unlike
  Email/Calendar's rolling 7-day window — a Task has no natural "occurs
  near now" framing, mirroring `list_outlook_tasks`'s own no-date-window
  design).
- `summary()`'s `todo` object becomes `{"count": len(list_todo_items())}`.
- `my_day_router.py::get_todo()` returns `my_day.list_todo_items()`.

---

## Files to Modify

- `src/backend/app/business/my_day.py`:

  1. Append a new function after `list_calendar_items` (before
     `summary`):
     ```python
     def list_todo_items() -> list[dict]:
         """[{"subject", "customer", "due"}] for notes under Work/Tasks/
         whose status is still open (Scenario 8's own "still-open" text) —
         "status" == "Completed" is excluded, not deleted; a completed
         task is still a real, captured Task note (Scenario 5), it is
         simply outside this particular read projection, the same
         "captured but filtered" shape REQ-SB-30-US-01's `important`
         filter already established for Emails. No date-window
         filtering is applied — unlike list_email_items/
         list_calendar_items's rolling 7-day window, a Task has no
         natural "occurred near now" framing (mirroring
         outlook_com.list_outlook_tasks's own no-date-window design,
         ADR-027); a far-future or undated task stays listed until it is
         completed, not until it ages out of a window."""
         items = []
         for path in vault_writer.list_notes_in_kind_folder("Tasks"):
             frontmatter, _ = vault_writer.read_note(path)
             if frontmatter.get("status") == "Completed":
                 continue
             items.append({
                 "subject": frontmatter.get("subject", ""),
                 "customer": _customer_or_null(frontmatter),
                 "due": frontmatter.get("due") or None,
             })
         items.sort(key=lambda item: (item["due"] is None, item["due"] or "", item["subject"]))
         return items
     ```

  2. In `summary()`, replace:
     ```python
         return {
             "emails": {"count": len(list_email_items(day))},
             "calendar": {"count": len(list_calendar_items(day))},
             "todo": {"count": 0},
             "window": {"start": window_start, "end": window_end},
         }
     ```
     with:
     ```python
         return {
             "emails": {"count": len(list_email_items(day))},
             "calendar": {"count": len(list_calendar_items(day))},
             "todo": {"count": len(list_todo_items())},
             "window": {"start": window_start, "end": window_end},
         }
     ```
     Update `summary()`'s own docstring's trailing sentence ("todo stays
     hardcoded 0 — REQ-SB-09 has no resolved task source/kind folder yet")
     to instead note `todo`'s count now reflects real `list_todo_items()`
     data, unwindowed (unlike `emails`/`calendar`), same as the code
     comment update above.

- `src/backend/app/api/my_day_router.py`:
  - Replace:
    ```python
    @router.get("/todo")
    def get_todo() -> list[dict]:
        # Hardcoded [] — REQ-SB-09's task source/kind folder is still
        # unresolved (this story's own Non-Goals); no vault read at all.
        return []
    ```
    with:
    ```python
    @router.get("/todo")
    def get_todo() -> list[dict]:
        return my_day.list_todo_items()
    ```

---

## Constraints

- Inherits from parent story (`ADR-003` layering — `api` → `business` →
  `data_access`; read-only, no writes).
- Must NOT modify `list_email_items`, `list_calendar_items`,
  `_compute_window`, `_within_window`, `_resolve_day_bounds`,
  `_customer_or_null`, `get_summary`/`get_emails`/`get_calendar`, or
  `_validate_day` — additive only.
- `list_todo_items()` takes **no `day` parameter** — unlike
  `list_email_items`/`list_calendar_items`, To-Do has no day-navigator
  windowing (per the architecture.md amendment); do not add one.
- Must reuse `vault_writer.list_notes_in_kind_folder("Tasks")` and
  `vault_writer.read_note` — the same generic primitives Email/Calendar
  already use; no new `vault_writer.py` primitive is needed or permitted
  for this task.
- `GET /my-day/todo`'s response shape stays exactly
  `[{"subject", "customer", "due"}]` — the shape `REQ-SB-12-US-02`
  originally declared; do not add or rename any field.

---

## Tests

<!-- AC-08 (Scenario 8) is a My Day / user-facing scenario, primarily
verified end-to-end in T06 (the frontend task, which needs this endpoint
real to render against). This task's own Tests are non-AC-tagged backend-
layer smoke checks confirming the real data/filtering/response shape is
correct BEFORE T06 writes a line of frontend code against it — this
project's own established "backend-layer-first live verification"
pattern (Implementation/Learnings.md). -->

**Manual verification steps** (against the real live vault; at least one
real Task note from `T03`'s own live verification should already exist —
if not, run `todo_classification.classify_recent_todos()` once first):

1. Non-AC smoke check: in a Python shell, call `my_day.list_todo_items()`.
   Confirm it returns a list of `{"subject", "customer", "due"}` dicts,
   with a real still-open Task note present in the result and a real
   `status: "Completed"` Task note (mark one Complete via `T03`'s own
   pipeline first if none exists yet) genuinely ABSENT from the result.
   Confirm a Task note with no `due` frontmatter key shows `"due": None`
   in the projection (not a missing key, not an empty string), and a
   Task note with no `customer` shows `"customer": None`.
2. Non-AC smoke check: call `my_day.summary()`. Confirm `todo.count`
   matches `len(list_todo_items())` exactly, and that this count is a
   real, non-hardcoded value (i.e., not `0` if at least one real
   still-open Task note exists).
3. Non-AC smoke check: with the dev server running
   (`.venv\Scripts\python.exe -m uvicorn app.main:app --reload` from
   `src/backend`), `GET http://127.0.0.1:8000/my-day/todo` (adjust port
   per `MEMORY.md`'s known port-8000-may-be-occupied constraint). Confirm
   the raw JSON response matches `list_todo_items()`'s own return value
   exactly, and that `GET /my-day/summary`'s `todo.count` field is
   likewise no longer hardcoded `0`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `list_todo_items()` returns `{"subject", "customer", "due"}` for
      every still-open (`status != "Completed"`) note under `Work/Tasks/`,
      with no date-window filtering
- [ ] `summary()`'s `todo.count` reflects `len(list_todo_items())`, no
      longer hardcoded `0`
- [ ] `GET /my-day/todo` returns `list_todo_items()`'s real data
- [ ] No existing `my_day.py`/`my_day_router.py` function's behavior
      changed beyond the two edits above
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The frontend drill-down page's own rendering, badge logic — that is
  `T06`.
- `MyDayPage.tsx`'s dashboard card — already reads `summary.todo.count`
  generically (confirmed by direct reading); needs zero code change once
  this task lands, same "already-correct consumer" precedent
  `REQ-SB-22-US-01` established for `MyDayCalendarPage.tsx`/
  `MyDayPage.tsx`.
- A day-navigator for To-Do — explicitly not built (see Constraints).

---

## Context / Notes

`my_day.py` currently defines `list_email_items`/`list_calendar_items`
directly above `summary()`; insert `list_todo_items` between
`list_calendar_items` and `summary()`, matching the file's own existing
top-to-bottom ordering (Email, Calendar, then the new To-Do function,
then the aggregating `summary()`).

---

## Implementation Log (built 2026-08-13)

Read the real current `my_day.py`/`my_day_router.py` fresh before
editing — already matched this task's own sample exactly (the rolling
7-day-window `day` param on `summary()`/`list_email_items()`/
`list_calendar_items()` from `REQ-SB-22-US-01` was already accounted
for in this task's own literal code). `list_todo_items()` inserted
between `list_calendar_items` and `summary()`; `summary()`'s `todo`
object and its docstring updated; `get_todo()` now delegates to
`my_day.list_todo_items()`. No other line changed.

**Manual verification, all real, live (backend-layer-first, before
`T06`'s frontend code existed):**

1. `my_day.list_todo_items()` returns `{"subject", "customer", "due"}`
   dicts; a real still-open Task note is present, `due`/`customer`
   correctly render `None` (not a missing key, not `""`) when absent.
2. **Completed-task exclusion, dedicated real check:** created a real
   throwaway Outlook Task, marked `Complete = True`, captured it (real,
   bounded pipeline call) — confirmed a real `status: "Completed"` note
   was genuinely written (never skipped, per `AC-05`), then confirmed it
   is genuinely ABSENT from `list_todo_items()`'s own return value
   (82 open items, unchanged before/after — the completed note is
   captured but correctly filtered from this read projection). Cleaned
   up the throwaway Outlook Task/note/index entry afterward.
3. `my_day.summary()`'s `todo.count` matches `len(list_todo_items())`
   exactly and is a real, non-hardcoded value (82, not `0`).
4. Real `GET /my-day/todo` (against the live backend, port 8010) and
   `GET /my-day/summary` both confirmed matching `list_todo_items()`'s
   own real return value exactly — `todo.count: 82`, no longer
   hardcoded `0`.

No existing `my_day.py`/`my_day_router.py` function's behavior changed
beyond the two specified edits (confirmed by direct diff review).

`gate: clear` 2026-08-13 — no MUST-FLAG trigger fired: no assumption, no
ADR change, real file already matched this task's own sample exactly.
