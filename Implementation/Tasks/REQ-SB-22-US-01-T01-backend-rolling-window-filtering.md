---
id: REQ-SB-22-US-01-T01
title: Backend query-time 7-day window filtering + received field — app/business/my_day.py
parent_story: REQ-SB-22-US-01
requirement_id: REQ-SB-22
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-22-US-01-T01 — Backend query-time 7-day window filtering + received field

## Parent Story

- Story: [[REQ-SB-22-US-01]] — `../UserStories/REQ-SB-22-US-01-my-day-rolling-7-day-window.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-22 *My Day Rolling 7-Day Window*

---

## Objective

Add the first date-range filtering to My Day's read path: `list_email_items()`
and `list_calendar_items()` narrow to a rolling 7-day window (3 days before
today through 3 days after today), computed fresh on every call, and
`list_email_items()` gains the `received` field it currently omits entirely.

---

## Starting State → End State

**Before / Inputs:**
- `app/business/my_day.py` (`REQ-SB-12-US-02`, `Done`) exists with
  `list_email_items()` / `list_calendar_items()` / `summary()`, none of
  which filter by date — every note ever captured under `Work/Emails/` /
  `Work/Meetings/` is returned, unfiltered.
- `list_email_items()`'s projection omits `received` even though the
  underlying note's `received` frontmatter field already exists (written
  by `email_classification.py`).
- `vault_writer.list_notes_in_kind_folder(kind)` / `vault_writer.read_note(path)`
  (both existing, unchanged by this task) supply the raw per-note
  frontmatter this module already reads.

**After / Outputs:**
- `list_email_items()` returns `[{"subject", "sender", "customer",
  "received"}]`, containing only notes whose `received[:10]` falls inside
  the current 7-day window.
- `list_calendar_items()` returns `[{"subject", "start", "customer"}]`
  (shape unchanged), containing only notes whose `start[:10]` falls inside
  the current 7-day window.
- `summary()` is unchanged internally (`len(list_email_items())`/
  `len(list_calendar_items())`) but its counts are now windowed by
  construction, since both list functions are.
- "Today" is recomputed from `datetime.now()` on every call — never cached
  at import/module level — so the window advances automatically as days
  pass with zero extra polling/refresh mechanism.

---

## Files to Modify

- `src/backend/app/business/my_day.py`:
  ```python
  """Read-only My Day aggregation (REQ-SB-12-US-02, extended by
  REQ-SB-22-US-01 for rolling 7-day window date-filtering) — projects
  captured Email/Meeting notes down to the fields My Day's dashboard and
  drill-down pages need. No writes; api -> business -> data_access
  layering (ADR-003)."""
  from __future__ import annotations

  from datetime import datetime, timedelta

  from app.data_access import vault_writer

  _UNCLASSIFIED_CUSTOMER = "Unsorted"
  _WINDOW_DAYS_BEFORE = 3
  _WINDOW_DAYS_AFTER = 3


  def _customer_or_null(frontmatter: dict) -> str | None:
      """Mirrors list_known_customers()'s existing '!= "Unsorted"' convention
      for "not really classified" (MEMORY.md) rather than inventing a second
      one; the frontend renders None as "unclassified"."""
      customer = frontmatter.get("customer")
      if not customer or customer == _UNCLASSIFIED_CUSTOMER:
          return None
      return customer


  def _compute_window() -> tuple[str, str]:
      """Returns (window_start, window_end) as 'YYYY-MM-DD' strings, 3 days
      before through 3 days after the app/server host's current local
      calendar date (REQ-SB-22-US-01 Scenario 4/AC-04). Called fresh on
      every list_email_items()/list_calendar_items() invocation — never
      memoized at module or process level — so the window advances
      automatically as real days pass, and so a live verification pass can
      observe the window shift by monkeypatching this module's `datetime`
      reference rather than waiting for a real day to pass."""
      today = datetime.now().date()
      window_start = today - timedelta(days=_WINDOW_DAYS_BEFORE)
      window_end = today + timedelta(days=_WINDOW_DAYS_AFTER)
      return window_start.isoformat(), window_end.isoformat()


  def _within_window(date_value: str, window_start: str, window_end: str) -> bool:
      """String-compares the note's ISO-8601 date prefix (first 10 chars,
      'YYYY-MM-DD') against the window bounds — ISO date strings sort and
      compare correctly as plain strings, the same received[:10]/start[:10]
      slicing precedent already used in email_classification.py and
      vault_writer.meeting_note_filename_stem(). No datetime.fromisoformat()
      parsing or timezone conversion is introduced. A missing/empty date
      value is treated as outside the window (excluded), not a crash."""
      if not date_value:
          return False
      date_prefix = date_value[:10]
      return window_start <= date_prefix <= window_end


  def list_email_items() -> list[dict]:
      """[{"subject", "sender", "customer", "received"}] for notes under
      Work/Emails/ whose `received` date falls inside the current 7-day
      window (Scenarios 1, 3, 5). `received` is now surfaced for the first
      time — an existing captured frontmatter field the projection
      previously omitted, not a new data source."""
      window_start, window_end = _compute_window()
      items = []
      for path in vault_writer.list_notes_in_kind_folder("Emails"):
          frontmatter, _ = vault_writer.read_note(path)
          received = frontmatter.get("received", "")
          if not _within_window(received, window_start, window_end):
              continue
          items.append({
              "subject": frontmatter.get("subject", ""),
              "sender": frontmatter.get("sender", ""),
              "customer": _customer_or_null(frontmatter),
              "received": received,
          })
      return items


  def list_calendar_items() -> list[dict]:
      """[{"subject", "start", "customer"}] for notes under Work/Meetings/
      whose `start` date falls inside the current 7-day window (Scenarios
      2, 3, 5). Response shape unchanged from REQ-SB-12-US-02 — Calendar
      already surfaced `start`."""
      window_start, window_end = _compute_window()
      items = []
      for path in vault_writer.list_notes_in_kind_folder("Meetings"):
          frontmatter, _ = vault_writer.read_note(path)
          start = frontmatter.get("start", "")
          if not _within_window(start, window_start, window_end):
              continue
          items.append({
              "subject": frontmatter.get("subject", ""),
              "start": start,
              "customer": _customer_or_null(frontmatter),
          })
      return items


  def summary() -> dict:
      """{"emails": {"count"}, "calendar": {"count"}, "todo": {"count": 0}}
      — internally unchanged (still len() over list_email_items()/
      list_calendar_items()), but now naturally windowed since both list
      functions are (Scenario 5). todo stays hardcoded 0 — REQ-SB-09 has
      no resolved task source/kind folder yet, unchanged from
      REQ-SB-12-US-02's own reasoning."""
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
- Filtering happens **backend, query-time, inside this module** — not a
  client-side filter over an already-fetched full list (architect's own
  scope note).
- "Today" comes from `datetime.now()` (naive local host clock, no
  timezone library, no per-user timezone preference) — recomputed on
  every call, never a value cached at import time or stored between
  requests.
- Date comparison uses the `[:10]` ISO-date-string-slice precedent — no
  `datetime.fromisoformat()` parsing or timezone-conversion logic.
- `app/api/my_day_router.py` needs **no changes** — its endpoint
  signatures/response shapes are unchanged (an additive field + a
  narrower result set only); do not touch it in this task.
- `todo`'s count stays hardcoded `0` — do not glob any folder for it.
- `customer` continues to project to `None` (not the string `"Unsorted"`)
  — do not invent a second "unclassified" sentinel.
- Read-only — no new write path, no new `.second-brain/` state file.

---

## Tests

<!-- AC-01, AC-02, AC-05, AC-06 are verified live in T02 (frontend), which
loads the actual drill-down/dashboard pages a user sees. This task holds
the two locked ACs that need direct backend-level manipulation to verify
at all: AC-03 (proving exclusion is real, not merely a rendering choice)
and AC-04 (proving the window recomputes on every call, without waiting a
real day). -->

**Manual verification steps** (in a Python shell against the backend
`.venv`, cwd `src/backend`, real vault configured):

1. **[REQ-SB-22-US-01-AC-03]** Import `app.data_access.vault_writer` and
   `app.business.my_day`. Enumerate the full, unfiltered set of real note
   dates directly: for every path in
   `vault_writer.list_notes_in_kind_folder("Emails")`, read
   `vault_writer.read_note(path)[0].get("received", "")[:10]`; do the same
   for `"Meetings"` with `start`. Compute today's window bounds by calling
   `my_day._compute_window()`. Confirm by direct comparison that (a) at
   least one real note's date falls **outside** `[window_start,
   window_end]`, and (b) that exact note's `subject` does **not** appear
   anywhere in `my_day.list_email_items()` / `list_calendar_items()`'s
   returned list — not present at all, not present-but-flagged. If today's
   real vault happens to have zero notes outside the window for one of the
   two kinds, note that honestly and rely on the other kind's evidence
   (email capture has run for weeks; meeting capture only pulls a bounded
   future range per REQ-SB-08, so at least one of the two kinds is
   expected to have real out-of-window notes).
2. **[REQ-SB-22-US-01-AC-04]** In the same shell, temporarily monkeypatch
   `my_day`'s clock to simulate a later day: define a `FakeDatetime`
   subclass of the real `datetime` whose `now()` classmethod returns a
   fixed value 10 days after the real current time, then set
   `my_day.datetime = FakeDatetime`. Call
   `my_day.list_email_items()`/`list_calendar_items()` again and confirm
   the returned set differs from step 1's real-`"today"` result in the way
   the shifted window predicts (e.g. an item excluded before is now
   included, or vice versa, matching a manual recomputation of the
   10-days-later window bounds against the same raw date list from step
   1). Then revert: `my_day.datetime = datetime` (the real class,
   re-imported or restored from a saved reference), and re-run
   `list_email_items()`/`list_calendar_items()` once more to confirm the
   real, current-day windowed result (matching step 1) is restored
   exactly — mirroring `MEMORY.md`'s established temporary-stub-and-revert
   verification pattern, applied server-side.
3. Non-AC smoke check: confirm `list_email_items()`'s returned dicts each
   have a `received` key (non-empty, matching the corresponding note's
   real `received` frontmatter value) — the new field this task adds.
4. Non-AC smoke check: confirm `summary()`'s `emails.count` /
   `calendar.count` equal `len(list_email_items())` /
   `len(list_calendar_items())` from the same shell session (internal
   consistency, unchanged from `REQ-SB-12-US-02`).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `list_email_items()` returns only notes whose `received[:10]` falls
      inside the current 7-day window, each with a `received` field
- [x] `list_calendar_items()` returns only notes whose `start[:10]` falls
      inside the current 7-day window
- [x] An out-of-window note is excluded entirely from both list functions'
      returned data — not merely flagged (AC-03)
- [x] The window is recomputed from `datetime.now()` on every call — a
      monkeypatched later "today" produces a correspondingly shifted
      result (AC-04)
- [x] `summary()`'s counts stay internally consistent with the windowed
      list functions
- [x] Module only calls `vault_writer` — no direct filesystem I/O
- [x] `app/api/my_day_router.py` left unmodified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `app/api/my_day_router.py` — no changes needed; its endpoint contracts
  are unchanged.
- Any frontend page/component — that is `T02`.
- Timezone-aware "today" computation — explicitly out of scope per the
  parent story's own Non-Goals.
- A user-configurable window size — fixed at 3 days before/after, per the
  parent story's own Non-Goals.

---

## Context / Notes

Matches `architecture.md`'s "My Day & Agent Panel APIs" → "Amendment —
rolling 7-day window date-filtering (REQ-SB-22-US-01)" section verbatim.
`_compute_window()`/`_within_window()` are new private helpers scoped to
this module only — no `vault_writer` change, no new primitive.

---

## Implementation Log

**Coder pass, 2026-08-11.** Implemented `app/business/my_day.py` exactly as
specified in this task's `## Files to Modify` — `_compute_window()`/
`_within_window()` helpers, `received` added to `list_email_items()`'s
projection, both list functions narrowed to the current 3-days-before/
3-days-after window, `summary()` left internally unchanged (still
`len(list_...())`, now naturally windowed). No deviations from the plan.
`app/api/my_day_router.py` was read but not touched (endpoint contracts
unchanged, confirmed by inspection).

All verification run live in a `.venv` Python shell, cwd `src/backend`,
against the real, `.env`-configured vault (real captured Email/Meeting
notes, no fixtures/mocks):

- **[REQ-SB-22-US-01-AC-03]** PASS. `_compute_window()` returned
  `('2026-08-08', '2026-08-14')`. Direct enumeration of the full unfiltered
  vault found 179 real Email notes (158 outside the window) and 39 real
  Meeting notes (22 outside the window — one meeting note also has an
  empty `start` field, correctly treated as outside-window/excluded per
  this task's own "missing date = excluded" rule). Confirmed a real
  out-of-window email subject ("Involuntary Loss of Employment Insurance
  (ILOE)", `received` `2026-07-20`) and a real out-of-window meeting
  subject ("Re: Weekly Forecast l Strategic Clients", empty `start`) are
  each **absent** from `list_email_items()`/`list_calendar_items()`'s
  returned lists — not present, not flagged. `list_email_items()` returned
  21 items, `list_calendar_items()` returned 17, both far fewer than the
  full 179/39 — exclusion is real, not coincidental.
- **[REQ-SB-22-US-01-AC-04]** PASS. Captured the real-`"today"` windowed
  result (21 emails, 17 meetings) plus the raw unfiltered date list, then
  monkeypatched `my_day.datetime` to a `FakeDatetime` subclass whose
  `now()` returns the real time + 10 days. Recomputing the window under
  the fake clock shifted it to `('2026-08-18', '2026-08-24')`, and
  `list_email_items()`/`list_calendar_items()` under the fake clock
  returned 0 emails / 4 meetings — exactly matching a manual
  recomputation of "which raw dates fall in the shifted window" derived
  from the same raw date list captured in step 1 (subject-set equality
  confirmed programmatically, not just counts). Reverted
  `my_day.datetime = datetime` (the real class) and re-ran both list
  functions: window, counts, and the exact set of returned subjects for
  both lists matched the original real-`"today"` result exactly — no
  vault file was ever written or needed, mirroring `MEMORY.md`'s
  established temporary-stub-and-revert verification pattern extended
  server-side.
- **Non-AC smoke check 1** PASS. Every item returned by
  `list_email_items()` has a non-empty `received` key; spot-checked one
  item's `received` value against the real note's raw frontmatter (using
  the exact `received` value + subject as the join key, since 3 real notes
  in the vault happen to share the same subject/sender from a resent
  thread — matching on subject/sender alone was ambiguous, matching on the
  full `received` timestamp was not) — confirmed exact match.
- **Non-AC smoke check 2** PASS. `summary()` returned
  `{"emails": {"count": 21}, "calendar": {"count": 17}, "todo": {"count":
  0}}`, and `emails.count`/`calendar.count` equal
  `len(list_email_items())`/`len(list_calendar_items())` from the same
  session — internally consistent.

**Assumption logged for spot-check (scope-internal, not an escalation):**
the real vault has at least one Meeting note with an empty `start` field
(a data-quality artifact from a prior sprint, unrelated to this task) —
this task's own `_within_window` spec already calls for treating a
missing/empty date as excluded, so no code change was needed, but it's
worth a human spot-check that this particular note's empty `start` isn't
itself a latent capture-pipeline defect worth a separate `/bug`.

`gate: clear` 2026-08-11 — no MUST-FLAG trigger fired: no new dependency,
no shared-interface change (`my_day_router.py` untouched, endpoint
contracts unchanged), no ADR deviation, no unanticipated file, both locked
ACs verified live against real data with exact-match evidence (not just
count deltas). Task `status: Ready -> Done`.
