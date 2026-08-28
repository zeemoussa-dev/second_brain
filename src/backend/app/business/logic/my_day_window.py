"""Validates the `day` query param My Day's own /summary, /emails, and
/calendar endpoints accept -- moved out of my_day_router.py (2026-08-28,
API layer holds no business logic) since deciding what counts as a valid
`day` is a real business rule (the same 7-day window a user could
actually reach via the day-navigator), not an HTTP concern.
"""
from __future__ import annotations

from app.business import my_day


class DayOutsideWindowError(ValueError):
    def __init__(self, day: str, window_start: str, window_end: str) -> None:
        self.day = day
        self.window_start = window_start
        self.window_end = window_end
        super().__init__(f"day must be within the current window ({window_start} to {window_end})")


def validate_day(day: str | None) -> str | None:
    """A `day` is only meaningful (and only safe to hand to my_day's
    string-prefix date comparisons) if it's a real date inside the
    current 7-day window. Raises DayOutsideWindowError otherwise --
    never a silently-empty result or a window bypass."""
    if day is None:
        return None
    window_start, window_end = my_day.compute_window()
    if not (window_start <= day <= window_end):
        raise DayOutsideWindowError(day, window_start, window_end)
    return day
