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


def _resolve_day_bounds(day: str | None) -> tuple[str, str]:
    """Resolves the (start, end) date-string bounds a list function should
    filter against: the full 7-day window when `day` is None (existing
    REQ-SB-22-US-01 behavior, unchanged), or that single day (start == end
    == day) when a specific day is requested for the new day-navigator.
    `day` is trusted to already be a real 'YYYY-MM-DD' string within the
    current window — the router validates that, this function does not
    re-derive "today" or re-clamp, so a fresh call always reflects
    whatever the caller asked for."""
    if day is None:
        return _compute_window()
    return day, day


def list_email_items(day: str | None = None) -> list[dict]:
    """[{"subject", "sender", "customer", "received"}] for notes under
    Work/Emails/ whose `received` date falls inside the current 7-day
    window (Scenarios 1, 3, 5), or inside just `day` when provided (the
    My Day day-navigator). `received` is now surfaced for the first
    time — an existing captured frontmatter field the projection
    previously omitted, not a new data source."""
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
        })
    items.sort(key=lambda item: item["received"])
    return items


def list_calendar_items(day: str | None = None) -> list[dict]:
    """[{"subject", "start", "customer"}] for notes under Work/Meetings/
    whose `start` date falls inside the current 7-day window (Scenarios
    2, 3, 5), or inside just `day` when provided (the My Day
    day-navigator). Response shape unchanged from REQ-SB-12-US-02 —
    Calendar already surfaced `start`."""
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
        })
    items.sort(key=lambda item: item["start"])
    return items


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


def summary(day: str | None = None) -> dict:
    """{"emails": {"count"}, "calendar": {"count"}, "todo": {"count": 0},
    "window": {"start", "end"}} — internally unchanged (still len() over
    list_email_items()/list_calendar_items()), but now naturally windowed
    since both list functions are (Scenario 5), or narrowed to just `day`
    when provided. `window` is always the full 7-day range regardless of
    `day` — it describes what the day-navigator may pick from, not what
    was just counted — so the frontend can always render the full
    available range alongside whichever single day is currently selected.
    todo.count now reflects real list_todo_items() data — unwindowed
    (unlike emails/calendar), since a Task has no natural "occurred
    near now" framing (REQ-SB-09, ADR-027)."""
    window_start, window_end = _compute_window()
    return {
        "emails": {"count": len(list_email_items(day))},
        "calendar": {"count": len(list_calendar_items(day))},
        "todo": {"count": len(list_todo_items())},
        "window": {"start": window_start, "end": window_end},
    }
