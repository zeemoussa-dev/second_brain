---
id: REQ-SB-12-US-02-T02
title: New app/business/my_day.py — read-only summary/emails/calendar aggregation
parent_story: REQ-SB-12-US-02
requirement_id: REQ-SB-12
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-12-US-02-T01]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-12-US-02-T02 — New app/business/my_day.py — read-only summary/emails/calendar aggregation

## Parent Story

- Story: [[REQ-SB-12-US-02]] — `../UserStories/REQ-SB-12-US-02-my-day-dashboard-and-drilldowns.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-12 *Primary Application UI Shell — Agents Map & My Day*

---

## Objective

Add the new read-only `app/business/my_day.py` module: one shared
note-projection helper plus `list_email_items()` / `list_calendar_items()`
and a `summary()` aggregator, all built on `T01`'s
`list_notes_in_kind_folder` — the business-layer aggregation the router (`T03`)
calls.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed `vault_writer.list_notes_in_kind_folder(kind)`.
- `vault_writer.read_note(path)` already parses a note's frontmatter dict
  (existing, used by `list_known_customers()`).

**After / Outputs:**
- `app/business/my_day.py` exists with `list_email_items()`,
  `list_calendar_items()`, and `summary()`, matching
  `architecture.md`'s "My Day dashboard & drill-downs" response shapes
  exactly.

---

## Files to Modify

- `src/backend/app/business/my_day.py` (new):
  ```python
  """Read-only My Day aggregation (REQ-SB-12-US-02) — projects captured
  Email/Meeting notes down to the fields My Day's dashboard and drill-down
  pages need. No writes; api -> business -> data_access layering (ADR-003)."""
  from __future__ import annotations

  from app.data_access import vault_writer

  _UNCLASSIFIED_CUSTOMER = "Unsorted"


  def _customer_or_null(frontmatter: dict) -> str | None:
      """Mirrors list_known_customers()'s existing '!= "Unsorted"' convention
      for "not really classified" (MEMORY.md) rather than inventing a second
      one; the frontend renders None as "unclassified"."""
      customer = frontmatter.get("customer")
      if not customer or customer == _UNCLASSIFIED_CUSTOMER:
          return None
      return customer


  def list_email_items() -> list[dict]:
      """[{"subject", "sender", "customer"}] for every note under
      Work/Emails/ (Scenarios 4, 5)."""
      items = []
      for path in vault_writer.list_notes_in_kind_folder("Emails"):
          frontmatter, _ = vault_writer.read_note(path)
          items.append({
              "subject": frontmatter.get("subject", ""),
              "sender": frontmatter.get("sender", ""),
              "customer": _customer_or_null(frontmatter),
          })
      return items


  def list_calendar_items() -> list[dict]:
      """[{"subject", "start", "customer"}] for every note under
      Work/Meetings/ (Scenarios 6, 7). Resolves to [] today since REQ-SB-08
      hasn't shipped and Work/Meetings/ doesn't exist in the real vault yet
      — list_notes_in_kind_folder already handles that (T01)."""
      items = []
      for path in vault_writer.list_notes_in_kind_folder("Meetings"):
          frontmatter, _ = vault_writer.read_note(path)
          items.append({
              "subject": frontmatter.get("subject", ""),
              "start": frontmatter.get("start", ""),
              "customer": _customer_or_null(frontmatter),
          })
      return items


  def summary() -> dict:
      """{"emails": {"count"}, "calendar": {"count"}, "todo": {"count": 0}}
      (Scenarios 1, 2). todo is always 0 — REQ-SB-09 has no resolved task
      source/kind folder yet (this story's own Non-Goals); guessing one
      would be exactly the material assumption the story declined to make."""
      return {
          "emails": {"count": len(list_email_items())},
          "calendar": {"count": len(list_calendar_items())},
          "todo": {"count": 0},
      }
  ```

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering
  (ADR-003) — this module calls `vault_writer` only, no direct filesystem
  I/O of its own.
- `todo`'s count is hardcoded `0` — do not glob any folder for it (REQ-SB-09's
  task source/kind-folder name is unresolved; not this task's or this
  story's job to guess one, per the story's own Non-Goals).
- `customer` projects to `None` (not the string `"Unsorted"`) using the same
  convention `list_known_customers()` already established — do not invent a
  second "unclassified" sentinel.
- Read-only — no new write path, no new `.second-brain/` state file.

---

## Tests

<!-- Exercised end-to-end, live, by T03's router endpoints, where this
story's locked ACs are tagged. The smoke check below confirms this module in
isolation first. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`
   (cwd `src/backend`, real vault configured), call `my_day.summary()`.
   Confirm it returns `{"emails": {"count": N}, "calendar": {"count": 0},
   "todo": {"count": 0}}` where `N` is a positive integer matching the real
   count of `.md` files under the vault's `Work/Emails/`. Call
   `my_day.list_email_items()`; confirm each entry has `subject`/`sender`/
   `customer` keys, and at least one entry's `subject`/`sender` match a real
   captured email note's frontmatter. Call `my_day.list_calendar_items()`;
   confirm it returns `[]`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `summary()` returns `{"emails": {"count"}, "calendar": {"count"},
      "todo": {"count": 0}}` matching real vault data for emails/calendar
- [x] `list_email_items()` / `list_calendar_items()` project
      `subject`/`sender`(or `start`)/`customer`, with `customer` `null` for
      `"Unsorted"`/absent
- [x] Module only calls `vault_writer` — no direct filesystem I/O
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The `/my-day/*` HTTP endpoints and `app/main.py` router registration —
  that is T03.
- Any `todo` vault read — permanently out of this story's scope (see
  Non-Goals).

---

## Context / Notes

Matches `architecture.md`'s "My Day dashboard & drill-downs
(REQ-SB-12-US-02)" section verbatim — `list_email_items`/
`list_calendar_items` both go through the same shared per-kind-folder
primitive (`T01`), consistent with that section's stated design.

---

## Implementation Log

Implemented exactly as specified — new `app/business/my_day.py` with
`_customer_or_null`, `list_email_items`, `list_calendar_items`, `summary`,
all calling `vault_writer` only.

**Non-AC smoke check (2026-08-11):** `my_day.summary()` returned
`{"emails": {"count": 178}, "calendar": {"count": 39}, "todo": {"count":
0}}` against the real vault. `list_email_items()` sample entry had
`subject`/`sender`/`customer` keys, matching a real captured email's
frontmatter. `list_calendar_items()` returned 39 entries (not `[]` — same
real-vault-state note as `T01`'s Implementation Log: SPRINT-006 landed
concurrently and Meeting notes now exist) with `subject`/`start`/`customer`
keys; `customer: ""` in the real Meeting note frontmatter correctly
projected to `None` via `_customer_or_null`'s falsy-string check.

gate: clear 2026-08-11 — no MUST-FLAG trigger fired.
