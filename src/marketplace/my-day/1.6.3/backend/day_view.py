"""My Day's projections over the vault, built on the Plugin API.

Ported from the framework's `business/my_day.py` (Second Brain `REQ-SB-91`
Phase 5) with its behaviour unchanged. The five framework capabilities it used
directly are now Plugin API calls: `api.vault.entries()`,
`api.vault.notes_in_kind()`, `api.vault.read_note()`, `api.pipelines.get()` and
`api.hermes.run_cron_job()`.

Listing goes through `entries()`, not `index()` (framework API v5, `BUG-076`):
`index()` holds one note per name, and a meeting whose invitation email was
captured under the same name simply was not in it -- My Day showed four of the
day's five meetings. Customers come from the Entities plugin's
`entities.customers` service (1.3.0).
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta
from pathlib import Path

# The two Pipelines whose cron jobs populate My Day's Emails and Calendar, so a
# manual refresh re-runs exactly what the schedule runs (operator, 2026-09-02:
# "the Option to pull stuff manually").
REFRESH_PIPELINE_IDS = ("threads-builder", "meeting-builder")

WINDOW_DAYS_BEFORE = 3
WINDOW_DAYS_AFTER = 3


class DayOutsideWindowError(ValueError):
    def __init__(self, day: str, window_start: str, window_end: str) -> None:
        self.day = day
        self.window_start = window_start
        self.window_end = window_end
        super().__init__(f"day must be within the current window ({window_start} to {window_end})")


def _within_window(date_value: str, window_start: str, window_end: str) -> bool:
    """ISO-8601 date prefixes compare correctly as plain strings, so no parsing
    or timezone conversion is involved. A missing date is outside the window."""
    if not date_value:
        return False
    return window_start <= date_value[:10] <= window_end


def _series_folder_name_for(path_str: str) -> str:
    # Work/Meetings/<series>/occurrences/<occurrence>.md
    return Path(path_str).parent.parent.name


class DayView:
    def __init__(self, api, today: Callable[[], date] | None = None) -> None:
        self._api = api
        # Injectable so the rolling window can be tested on a fixed date; the
        # default reads the clock on every call, so the window advances by itself.
        self._today = today or (lambda: datetime.now().date())

    # -- the window -----------------------------------------------------------------

    def compute_window(self) -> tuple[str, str]:
        today = self._today()
        return (
            (today - timedelta(days=WINDOW_DAYS_BEFORE)).isoformat(),
            (today + timedelta(days=WINDOW_DAYS_AFTER)).isoformat(),
        )

    def validate_day(self, day: str | None) -> str | None:
        """A `day` is only safe to hand to the string-prefix comparisons if it is
        inside the current window; outside it raises, never silently empties."""
        if day is None:
            return None
        window_start, window_end = self.compute_window()
        if not (window_start <= day <= window_end):
            raise DayOutsideWindowError(day, window_start, window_end)
        return day

    def _day_bounds(self, day: str | None) -> tuple[str, str]:
        return self.compute_window() if day is None else (day, day)

    # -- lookups built from the live index --------------------------------------------

    def _customer_resolver(self):
        """`resolve(tags) -> customer name | None` for one listing. Customers
        belong to the Entities plugin (Entities plan Phase 4): without it
        installed, nothing on My Day has a customer, and nothing fails."""
        customers = self._api.get_service("entities.customers")
        if customers is None:
            return lambda tags: None
        lookup = customers.name_by_tag()
        return lambda tags: customers.customer_from_tags(tags, lookup)

    def _latest_sender_by_conversation(self) -> dict[str, str]:
        """A Thread has no single sender, but the Emails screen shows one: the
        sender of the conversation's most recent RawMessage."""
        latest: dict[str, tuple[str, str]] = {}
        for entry in self._api.vault.entries():
            frontmatter = entry["frontmatter"]
            if frontmatter.get("type") != "RawMessage":
                continue
            conversation_id = frontmatter.get("conversation_id")
            if not conversation_id:
                continue
            received = frontmatter.get("received", "")
            current = latest.get(conversation_id)
            if current is None or received > current[0]:
                latest[conversation_id] = (received, frontmatter.get("sender", ""))
        return {conversation_id: sender for conversation_id, (_, sender) in latest.items()}

    def _meeting_series_lookup(self) -> dict[str, dict]:
        """Series folder name -> the series note's frontmatter. A dated occurrence
        carries only logistics; its customer tags live on the series note, which
        is the occurrence's grandparent folder on disk (the series folder name is
        a truncated prefix of `calendar_series_id`, so the ids do not match)."""
        lookup: dict[str, dict] = {}
        for entry in self._api.vault.entries():
            frontmatter = entry["frontmatter"]
            if frontmatter.get("type") != "Meeting" or frontmatter.get("start"):
                continue
            lookup[entry["stem"]] = frontmatter
        return lookup

    # -- what the screens show ----------------------------------------------------------

    def list_email_items(self, day: str | None = None) -> list[dict]:
        range_start, range_end = self._day_bounds(day)
        customer_of = self._customer_resolver()
        sender_lookup = self._latest_sender_by_conversation()
        items = []
        for entry in self._api.vault.entries():
            frontmatter = entry["frontmatter"]
            if frontmatter.get("type") != "Thread":
                continue
            received = frontmatter.get("last_message_at", "")
            if not _within_window(received, range_start, range_end):
                continue
            items.append({
                "subject": frontmatter.get("thread_name", ""),
                "sender": sender_lookup.get(frontmatter.get("conversation_id"), ""),
                "customer": customer_of(entry["tags"]),
                "received": received,
                "stem": entry["stem"],
            })
        items.sort(key=lambda item: item["received"])
        return items

    def list_calendar_items(self, day: str | None = None) -> list[dict]:
        range_start, range_end = self._day_bounds(day)
        customer_of = self._customer_resolver()
        series_lookup = self._meeting_series_lookup()
        items = []
        for entry in self._api.vault.entries():
            frontmatter = entry["frontmatter"]
            if frontmatter.get("type") != "Meeting":
                continue
            start = frontmatter.get("start", "")
            if not start:
                continue  # the series note itself, never an occurrence
            if not _within_window(start, range_start, range_end):
                continue
            series = series_lookup.get(_series_folder_name_for(entry["path"])) or {}
            customer = customer_of(entry["tags"]) or customer_of(series.get("tags") or [])
            items.append({
                "subject": frontmatter.get("subject") or series.get("subject") or entry["stem"],
                "start": start,
                "customer": customer,
                "stem": entry["stem"],
            })
        items.sort(key=lambda item: item["start"])
        return items

    def list_todo_items(self) -> list[dict]:
        """Open tasks. Unlike emails and meetings a task is not windowed: it has
        no natural "near now", so it stays listed until it is completed."""
        items = []
        for path in self._api.vault.notes_in_kind("Tasks"):
            frontmatter, _ = self._api.vault.read_note(path)
            if frontmatter.get("status") == "Completed":
                continue
            items.append({
                "subject": frontmatter.get("subject", ""),
                "customer": frontmatter.get("customer") or None,
                "due": frontmatter.get("due") or None,
            })
        items.sort(key=lambda item: (item["due"] is None, item["due"] or "", item["subject"]))
        return items

    def trigger_refresh(self) -> list[dict]:
        """Fires each refresh Pipeline's own cron job. Returns once the triggers
        are sent, not when capture finishes. A Pipeline with no cron job is
        reported, never skipped silently."""
        results = []
        for pipeline_id in REFRESH_PIPELINE_IDS:
            pipeline = self._api.pipelines.get(pipeline_id)
            if pipeline is None or pipeline.get("cron_job_id") is None:
                results.append({"pipeline_id": pipeline_id, "triggered": False, "detail": "no cron job configured"})
                continue
            triggered = self._api.hermes.run_cron_job(pipeline["cron_job_id"], pipeline.get("cron_profile_id"))
            results.append({
                "pipeline_id": pipeline_id,
                "triggered": triggered,
                "detail": "triggered" if triggered else "Hermes CLI call failed",
            })
        return results

    def summary(self, day: str | None = None) -> dict:
        """Counts for the dashboard. `window` is always the full navigable range,
        whatever `day` is, so the day-navigator can always show it."""
        window_start, window_end = self.compute_window()
        return {
            "emails": {"count": len(self.list_email_items(day))},
            "calendar": {"count": len(self.list_calendar_items(day))},
            "todo": {"count": len(self.list_todo_items())},
            "window": {"start": window_start, "end": window_end},
        }
