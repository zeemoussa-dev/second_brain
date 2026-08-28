"""CLI entry point: fetch one bounded window of calendar events.

Usage:
    python list_recent_meetings.py [--days-back 7] [--days-ahead 14] [--limit 100]

Prints a JSON array of event dicts to stdout, one per calendar event:
{id, subject, start, end, location, organizer,
 attendees: [{name, email, department, job_title, company_name}, ...],
 conversation_id, is_recurring, series_id, teams_link, dial_in}

Fetch-only: no vault write, no side effect.
"""
from __future__ import annotations

import argparse
import json
import sys

from outlook_lib import OutlookUnavailable, list_calendar_events

# Same real crash as email-thread-capture's own list_recent_emails.py
# (2026-08-24): a meeting subject/location/attendee name can carry a
# Unicode character Windows' default console codepage (cp1252) can't
# encode; printing the JSON output without this would crash the whole
# capture run on that one event.
sys.stdout.reconfigure(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days-back", type=int, default=7)
    parser.add_argument("--days-ahead", type=int, default=14)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    try:
        events = list_calendar_events(days_back=args.days_back, days_ahead=args.days_ahead, limit=args.limit)
    except OutlookUnavailable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(events, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
