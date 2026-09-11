"""graph_calendar_lib.py -- Microsoft Graph replacement for outlook_lib.py's
calendar read.

Same public surface and the same event record, so `list_recent_meetings.py`
needs no change beyond its import line:

    OutlookUnavailable  (alias of GraphUnavailable)
    list_calendar_events(days_back, days_ahead, limit) -> list[dict]

Why Graph and not COM: the agent runs as one account and reads a mailbox
belonging to another. Outlook desktop cannot do that without a mail profile for
the target, and this host has none -- the same reason email capture moved.
Verified live 2026-09-10: the delegated token already in use reads the target's
calendar (3 calendars, 766 events in a 90-day window). No new consent and no new
Exchange grant were needed -- `Calendars.Read`/`Calendars.Read.Shared` were
consented alongside Mail, and Full Access on the mailbox covers its calendar.

Auth, retries and the corporate-middlebox handling are NOT reimplemented here --
they are imported from the email Skill's own `graph_lib`, which owns the single
delegated refresh-token flow. Two copies of that would be two things to
re-authorize.

**`calendarView`, deliberately, not `/events`.** `/events` returns a recurring
series as ONE master item; `calendarView` expands it into real occurrences over
the window, which is exactly the shape the Meeting template wants (one file per
occurrence) and what COM's `IncludeRecurrences = True` produced.

TRAP CARRIED OVER FROM THE COM PATH: `start`/`end` are formatted to match
`str(item.Start)`'s own shape, because the dedup key downstream is computed in
vault_lib from `subject` + `start` as plain strings. A differently-formatted
timestamp does not error -- it silently produces a second copy of a meeting
already captured.
"""
from __future__ import annotations

import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

# The email Skill owns the delegated token flow -- one refresh token, one place
# to re-authorize. Importing it beats carrying a second copy.
#
# Two layouts have to work, and they differ: in the REPO a Skill is
# `catalog/<tool>/<skill>/scripts/`, while a DEPLOYED Skill is flattened to
# `profiles/<agent>/skills/<tool>/<skill>/` with the scripts sitting directly
# in it. Both are tried, and a failure says which paths were checked rather
# than surfacing a bare ModuleNotFoundError.
#
# TODO (after the current backfill): the honest fix is to lift the delegated
# token flow into `skills/managers/` -- the shared-engine location that is
# already deployed onto PYTHONPATH -- so neither Skill reaches into the other.
# Not done now because `graph_lib` is being executed continuously by a running
# 3-month capture, and a broken import there stops the whole pull.
_HERE = Path(__file__).resolve()
_CANDIDATES = [
    _HERE.parents[3] / "m365" / "email-thread-capture" / "scripts",  # repo
    _HERE.parents[2] / "m365" / "email-thread-capture",              # deployed
]
for _candidate in _CANDIDATES:
    if (_candidate / "graph_lib.py").is_file() and str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))
        break

try:
    import graph_lib  # noqa: E402
except ModuleNotFoundError as exc:                       # pragma: no cover
    raise ModuleNotFoundError(
        "graph_calendar_lib needs the email Skill's graph_lib for delegated "
        "Graph auth, and could not find it. Looked in: "
        + "; ".join(str(c) for c in _CANDIDATES)
        + ". Deploy `email-thread-capture` to the same profile as this Skill."
    ) from exc

GraphUnavailable = graph_lib.GraphUnavailable
OutlookUnavailable = GraphUnavailable

_GRAPH = "https://graph.microsoft.com/v1.0"

# `str(item.Start)` on the COM path yields "2026-09-10 16:00:00+00:00".
# vault_lib dedupes on subject + this string, so the format is a contract.
_COM_STAMP = "%Y-%m-%d %H:%M:%S+00:00"

_TEAMS_LINK = re.compile(r"https://teams\.microsoft\.com/l/meetup-join/[^\s\"'<>]+", re.I)
_DIAL_IN = re.compile(r"(?:\+\d[\d\s\-\(\)]{7,}\d)")

_SELECT = ",".join((
    "id", "subject", "start", "end", "location", "organizer", "attendees",
    "isCancelled", "isAllDay", "type", "seriesMasterId", "onlineMeeting", "body",
))


def _mailbox() -> str:
    mailbox = (os.environ.get("SECOND_BRAIN_SELF_EMAIL")
               or os.environ.get("SELF_EMAIL") or "").strip()
    if not mailbox:
        raise GraphUnavailable(
            "SECOND_BRAIN_SELF_EMAIL is not set -- a delegated Graph read "
            "addresses a NAMED mailbox (/users/<address>/calendarView)."
        )
    return mailbox


def _to_com_stamp(value: str) -> str:
    """Graph's ISO datetime -> the shape str(item.Start) produced.

    Returns "" for an unparseable value rather than guessing: a wrong stamp
    would silently become a different dedup key and duplicate the meeting."""
    if not value:
        return ""
    raw = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime(_COM_STAMP)


def _attendee_records(event: dict, organizer_email: str) -> list[dict]:
    """Real human attendees only.

    Mirrors the COM path's own exclusions: never the organizer, and never a
    resource (a booked meeting room is not a person and must not become a
    Person note). department/job_title/company_name stay blank -- Graph does
    not carry them on an event, and filling them would need User.Read.All,
    which this deployment deliberately does not request."""
    records: list[dict] = []
    for attendee in event.get("attendees") or []:
        if (attendee.get("type") or "").lower() == "resource":
            continue
        address = ((attendee.get("emailAddress") or {}).get("address") or "").strip()
        if not address or address.lower() == organizer_email.lower():
            continue
        records.append({
            "name": ((attendee.get("emailAddress") or {}).get("name") or "").strip() or address,
            # `email`, NOT `address`. outlook_lib emitted
            # {"name":..., "email":...} and ingest_meeting.py filters on
            # `a.get("email")` -- an `address` key is silently dropped, which
            # is exactly what happened on the first run: 55 meetings captured
            # with zero attendees linked and no error anywhere.
            "email": address,
            "department": "",
            "job_title": "",
            "company_name": "",
        })
    return records


def _teams_link(event: dict, body_text: str) -> str:
    """Graph gives the join URL structurally; the body regex is the fallback
    for a meeting created outside Teams' own integration."""
    joined = ((event.get("onlineMeeting") or {}).get("joinUrl") or "").strip()
    if joined:
        return joined
    found = _TEAMS_LINK.search(body_text or "")
    return found.group(0) if found else ""


def _dial_in(body_text: str) -> str:
    found = _DIAL_IN.search(body_text or "")
    return found.group(0).strip() if found else ""


def list_calendar_events(days_back: int = 7, days_ahead: int = 14, limit: int = 100) -> list[dict]:
    """Events in [now - days_back, now + days_ahead], recurring series expanded
    into real occurrences, newest first, trimmed to `limit`."""
    mailbox = _mailbox()
    token = graph_lib._access_token()
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=max(0, days_back))).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = (now + timedelta(days=max(0, days_ahead))).strftime("%Y-%m-%dT%H:%M:%SZ")

    params = urllib.parse.urlencode({
        "startDateTime": start,
        "endDateTime": end,
        "$select": _SELECT,
        # Page size, NOT the total. Graph caps calendarView at 999 per page and
        # returns the rest behind @odata.nextLink -- followed below, because a
        # 90-day window here holds ~766 events and a single unpaged request
        # would silently return a prefix. A capture that quietly stops early is
        # the failure mode this codebase keeps paying for.
        "$top": "250",
        "$orderby": "start/dateTime desc",
    }, safe="$,:/() ")
    url = f"{_GRAPH}/users/{urllib.parse.quote(mailbox)}/calendarView?{params}"

    # Prefer UTC so every returned dateTime is directly comparable; without it
    # Graph answers in the mailbox's own timezone and the stamps drift.
    # Built here rather than through a graph_lib helper: this Skill has to work
    # against whatever graph_lib is ALREADY DEPLOYED, and adding a helper there
    # would mean redeploying the email Skill -- which is executing a multi-day
    # capture. `_urlopen_retrying` is the primitive that matters (it carries the
    # corporate-middlebox retry) and it has always been there.
    headers = {
        "Authorization": f"Bearer {token}",
        # Without this Graph answers in the mailbox's own timezone and the
        # stamps drift against the dedup key.
        "Prefer": 'outlook.timezone="UTC"',
    }
    events: list[dict] = []
    pages = 0
    while url and len(events) < limit and pages < 40:
        payload = graph_lib._urlopen_retrying(urllib.request.Request(url, headers=headers))
        events.extend(payload.get("value") or [])
        url = payload.get("@odata.nextLink")
        pages += 1

    results: list[dict] = []
    for event in events:
        if event.get("isCancelled"):
            continue
        organizer_email = ((event.get("organizer") or {}).get("emailAddress") or {}).get("address", "") or ""
        organizer_name = ((event.get("organizer") or {}).get("emailAddress") or {}).get("name", "") or organizer_email
        body_text = ((event.get("body") or {}).get("content") or "")
        occurrence = (event.get("type") or "").lower() in ("occurrence", "exception")
        results.append({
            "id": event.get("id") or "",
            "subject": event.get("subject") or "",
            "start": _to_com_stamp(((event.get("start") or {}).get("dateTime") or "")),
            "end": _to_com_stamp(((event.get("end") or {}).get("dateTime") or "")),
            "location": ((event.get("location") or {}).get("displayName") or "").strip(),
            "organizer": organizer_name,
            "attendees": _attendee_records(event, organizer_email),
            # COM derived this from the appointment's own conversation linkage;
            # Graph exposes no equivalent on an event, and the downstream
            # thread link is a separate, deliberate matching pass
            # (link_meeting_to_thread.py) rather than a field carried here.
            "conversation_id": "",
            "is_recurring": occurrence,
            "series_id": event.get("seriesMasterId") or "",
            "teams_link": _teams_link(event, body_text),
            "dial_in": _dial_in(body_text),
        })
        if len(results) >= limit:
            break
    return results
