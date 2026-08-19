---
id: REQ-SB-43-US-01-T06
title: my_day.py/my_day_router.py — list_calendar_items projection gains a "stem" field (the note identity the Cockpit route needs)
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

# REQ-SB-43-US-01-T06 — `my_day.list_calendar_items` gains `"stem"`

## Parent Story

- Story: [[REQ-SB-43-US-01]] — `../UserStories/REQ-SB-43-US-01-meeting-cockpit-expert-assisted-workspace.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-43 *Meeting Cockpit — Expert-Assisted Meeting Workspace*

---

## Objective

`my_day.list_calendar_items`'s own projection currently returns `{"subject", "start", "customer"}` — no stable identity a frontend row can key a click-through route on (the existing `MyDayCalendarPage.tsx` even uses the array `index` as its React `key`, confirmed by direct reading). Add a `"stem"` field (the note's own filename stem — the same identity `vault_indexing`/the Cockpit router already key on) so a meeting row can link to `/meeting-cockpit/:stem`.

---

## Starting State → End State

**Before / Inputs:** `my_day.py::list_calendar_items` iterates `vault_writer.list_notes_in_kind_folder("Meetings")` (a list of `Path`s), builds `{"subject", "start", "customer"}` per note, discarding the path.

**After / Outputs:**
```python
def list_calendar_items(day: str | None = None) -> list[dict]:
    range_start, range_end = _resolve_day_bounds(day)
    items = []
    for path in vault_writer.list_notes_in_kind_folder("Meetings"):
        frontmatter, _ = vault_writer.read_note(path)
        start = frontmatter.get("start", "")
        if not _within_window(start, range_start, range_end):
            continue
        items.append({
            "subject": frontmatter.get("subject", ""),
            "start": start,
            "customer": _customer_or_null(frontmatter),
            "stem": path.stem,
        })
    items.sort(key=lambda item: item["start"])
    return items
```

---

## Files to Modify

- `src/backend/app/business/my_day.py` — add `"stem": path.stem` to `list_calendar_items`'s own appended dict, additive only.

---

## Constraints

- ADDITIVE field only — `"subject"`/`"start"`/`"customer"` keys, sort order, and window-filtering logic are byte-for-byte unchanged.
- Does NOT touch `list_email_items`, `list_todo_items`, or `summary` — this task is scoped to `list_calendar_items` only (`REQ-SB-44-US-01`'s own task adds the equivalent `list_email_items` field).
- `my_day_router.py`'s `GET /my-day/calendar` needs NO code change — it already returns `my_day.list_calendar_items(...)`'s own dict list verbatim.

---

## Tests

**Manual verification steps** (Python shell, backend `.venv`, `PYTHONPATH=.`; requires at least one real Meeting note inside the current 7-day window):
1. **[REQ-SB-43-US-01-AC-01]** `my_day.list_calendar_items()` — confirm every returned item now has a real, non-empty `"stem"` field matching that Meeting note's own real filename stem (spot-check against `vault_writer.list_notes_in_kind_folder("Meetings")`'s own real `Path.stem` for the same note).
2. Non-AC smoke check: confirm `"subject"`/`"start"`/`"customer"` values are unchanged from before this task (same real data, one more key added, nothing altered).
3. Real HTTP smoke check (dev server, backend `.venv`): `GET /my-day/calendar` — confirm the JSON response's items each carry `"stem"`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `list_calendar_items` returns a real `"stem"` per item, additive
- [ ] Every other existing field/behavior of `list_calendar_items` unchanged
- [ ] `list_email_items`/`list_todo_items`/`summary` unmodified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- `list_email_items`'s own equivalent field — `REQ-SB-44-US-01`'s own task.
- Any frontend change — `T09`.

---

## Context / Notes

`REQ-SB-44-US-01`'s own task mirrors this exact change for `list_email_items` — read this task's own real, as-built diff first if building that one later, for shape consistency.

---

## Implementation Log

Implemented exactly as spec'd — one additive `"stem": path.stem` line in
`list_calendar_items`. Read the real, current file first; matched the task's
own sample byte-for-byte.

**Manual verification (real `.venv`, real vault; found and killed a stray
dev-server process on port 8001 serving stale pre-`SPRINT-040` code — started a
fresh, explicitly-controlled instance, per this project's own established
specific-PID-kill-and-restart protocol; this fresh instance is reused for the
rest of this sprint's HTTP-level verification):**
1. **AC-01:** `list_calendar_items()` — all 25 real items in-window each carry a real, non-empty `"stem"` matching `vault_writer.list_notes_in_kind_folder("Meetings")`'s own real `Path.stem` for the same note (spot-checked, asserted programmatically). Confirmed.
2. Non-AC: `"subject"`/`"start"`/`"customer"` values unchanged (same real data, one key added). Confirmed by direct inspection.
3. Real HTTP smoke check: `GET http://127.0.0.1:8001/my-day/calendar` → every JSON item carries `"stem"`. Confirmed.

gate: clear 2026-08-14 — no triggers fired (mechanical, additive-only field).
