---
id: REQ-SB-44-US-01-T02
title: my_day.py/my_day_router.py — list_email_items projection gains a "stem" field (the note identity the Cockpit route needs)
parent_story: REQ-SB-44-US-01
requirement_id: REQ-SB-44
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-44-US-01-T02 — `my_day.list_email_items` gains `"stem"`

## Parent Story

- Story: [[REQ-SB-44-US-01]] — `../UserStories/REQ-SB-44-US-01-inbox-cockpit-expert-assisted-workspace.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-44 *Inbox Cockpit — Expert-Assisted Email Workspace*

---

## Objective

Mirrors `REQ-SB-43-US-01-T06`'s exact change, for `list_email_items` instead of `list_calendar_items` — adds a `"stem"` field so an email row can link to `/inbox-cockpit/:stem`.

---

## Starting State → End State

**Before / Inputs:** `my_day.py::list_email_items` iterates `vault_writer.list_notes_in_kind_folder("Emails")` (a list of `Path`s), builds `{"subject", "sender", "customer", "received"}` per note, discarding the path.

**After / Outputs:**
```python
def list_email_items(day: str | None = None) -> list[dict]:
    range_start, range_end = _resolve_day_bounds(day)
    items = []
    for path in vault_writer.list_notes_in_kind_folder("Emails"):
        frontmatter, _ = vault_writer.read_note(path)
        received = frontmatter.get("received", "")
        if not _within_window(received, range_start, range_end):
            continue
        items.append({
            "subject": frontmatter.get("subject", ""),
            "sender": frontmatter.get("sender", ""),
            "customer": _customer_or_null(frontmatter),
            "received": received,
            "stem": path.stem,
        })
    items.sort(key=lambda item: item["received"])
    return items
```

---

## Files to Modify

- `src/backend/app/business/my_day.py` — add `"stem": path.stem` to `list_email_items`'s own appended dict, additive only.

---

## Constraints

- ADDITIVE field only — every existing key, sort order, and window-filtering logic unchanged.
- Does NOT touch `list_calendar_items` (`REQ-SB-43-US-01-T06`'s own already-built equivalent), `list_todo_items`, or `summary`.
- `my_day_router.py`'s `GET /my-day/emails` needs no code change.

---

## Tests

**Manual verification steps** (Python shell, backend `.venv`, `PYTHONPATH=.`; requires at least one real Email note inside the current 7-day window):
1. **[REQ-SB-44-US-01-AC-01]** `my_day.list_email_items()` — confirm every item now has a real, non-empty `"stem"` matching that Email note's own real filename stem.
2. Non-AC smoke check: confirm `"subject"`/`"sender"`/`"customer"`/`"received"` values are unchanged from before this task.
3. Real HTTP smoke check: `GET /my-day/emails` — confirm the JSON response's items each carry `"stem"`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `list_email_items` returns a real `"stem"` per item, additive
- [x] Every other existing field/behavior unchanged
- [x] `list_calendar_items`/`list_todo_items`/`summary` unmodified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend change — `T06`.

---

## Context / Notes

Mirrors `REQ-SB-43-US-01-T06` exactly — read that task's own real, as-built diff for shape consistency.

---

## Implementation Log

**2026-08-14 — built exactly per the task's own code block, no deviation.** `my_day.py::list_email_items` gained `"stem": path.stem`, additive; the function's own docstring updated to name the new field (a same-function, in-scope comment touch, not a new file). Mirrors `list_calendar_items`'s own already-built `"stem"` field exactly.

**Verification (Python shell, backend `.venv`; real dev server on port 8001):**
- **[AC-01]** `my_day.list_email_items()` against the real vault — 35 real items returned, every one with a real, non-empty `"stem"` matching that Email note's own real filename stem (e.g. `{'subject': 'Re: Workshop slides', ..., 'stem': '2026-08-11-Re- Workshop slides-7A790000'}`). **Pass.**
- Non-AC smoke check: `"subject"`/`"sender"`/`"customer"`/`"received"` values unchanged from before this task (spot-checked against real output). **Pass.**
- Real HTTP smoke check: `GET http://127.0.0.1:8001/my-day/emails` — real `200` JSON response, every item carries `"stem"`. **Pass.**
- Non-AC: `list_calendar_items()` (25 items) / `list_todo_items()` (82 items) confirmed still returning real data, unmodified by this task.

`gate: clear` 2026-08-14 — no MUST-FLAG trigger fired (additive-only change, no deviation from the task's own code sample, all steps verified live against real vault data).
