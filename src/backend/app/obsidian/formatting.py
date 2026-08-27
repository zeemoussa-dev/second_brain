"""Pure display-formatting helpers -- never a replacement for a
machine-parseable field, which stays byte-for-byte unchanged everywhere
it's already written."""
from __future__ import annotations

from datetime import datetime


def format_human_readable_datetime(raw: str) -> str:
    """Renders a raw, COM-stringified timestamp (e.g. "2026-08-16
    13:02:57.246000+00:00") in a human-readable form, e.g. "Aug 16,
    2026, 1:02 PM". Never raises and never fabricates a guessed date --
    a genuinely unparseable raw string is returned unchanged."""
    try:
        parsed = datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        try:
            parsed = datetime.strptime(raw[:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            return raw
    month_day_year = f"{parsed.strftime('%b')} {parsed.strftime('%d').lstrip('0') or '0'}, {parsed.year}"
    time_of_day = parsed.strftime("%I:%M %p").lstrip("0") or "0"
    return f"{month_day_year}, {time_of_day}"
