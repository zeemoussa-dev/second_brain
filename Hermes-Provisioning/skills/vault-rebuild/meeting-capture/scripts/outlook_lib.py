"""Self-contained Outlook desktop COM read for the meeting-capture Skill
(2026-08-21) -- trimmed port of Second Brain's own
app/data_access/outlook_com.py's calendar half (list_calendar_events and
what it needs), mirroring email-thread-capture's own outlook_lib.py --
one Skill's worth of primitives, duplicated rather than shared, per this
codebase's established "one Skill per task, pull only what you need"
scope decision.

Rides Outlook desktop's already-authenticated session -- no Azure app
registration, no OAuth. Requires pywin32 and Outlook desktop running.
"""
from __future__ import annotations

import re

import pythoncom
import win32com.client
from datetime import datetime, timedelta

_OL_FOLDER_CALENDAR = 9
_OL_MEETING_RECIPIENT_REQUIRED = 1
_OL_MEETING_RECIPIENT_OPTIONAL = 2

_TEAMS_JOIN_LINK_PATTERN = re.compile(r"Join:\s*(https?://\S+)")
_TEAMS_LINK_FALLBACK_PATTERN = re.compile(r"(https://teams\.microsoft\.com/\S+)")
_DIAL_IN_TEL_PATTERN = re.compile(r"<tel:([^>]+)>")


class OutlookUnavailable(Exception):
    """Outlook isn't running, or COM automation failed to connect."""


def _connect_namespace():
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        return outlook.GetNamespace("MAPI")
    except Exception as exc:
        raise OutlookUnavailable(f"couldn't connect to Outlook — is it running? ({exc})") from exc


def _extract_teams_link(raw_body: str) -> str:
    match = _TEAMS_JOIN_LINK_PATTERN.search(raw_body)
    if match:
        return match.group(1)
    match = _TEAMS_LINK_FALLBACK_PATTERN.search(raw_body)
    return match.group(1) if match else ""


def _extract_dial_in(raw_body: str) -> str:
    match = _DIAL_IN_TEL_PATTERN.search(raw_body)
    return match.group(1) if match else ""


def _resolve_attendees(item) -> list[dict]:
    """Resolves item.Recipients into {"name","email","department",
    "job_title","company_name"} -- merges required (To) and optional
    (Cc) into one flat list, no distinction kept (matches email
    capture's own 2026-08-21 GAL-enrichment addition -- see that
    Skill's own outlook_lib.py for why department/job_title/company_name
    are worth carrying: internal-only, best-effort, never guessed).
    Excludes the organizer (Type 0) and any resource recipient (Type 3,
    e.g. a booked meeting room) -- neither is a real person attendee."""
    attendees: list[dict] = []
    try:
        recipients = item.Recipients
        count = recipients.Count
    except Exception:
        return attendees
    for i in range(1, count + 1):
        try:
            recipient = recipients.Item(i)
            if recipient.Type not in (_OL_MEETING_RECIPIENT_REQUIRED, _OL_MEETING_RECIPIENT_OPTIONAL):
                continue
            name = recipient.Name or ""
            address = recipient.Address or ""
            extra = {"department": "", "job_title": "", "company_name": ""}
            try:
                exch_user = recipient.AddressEntry.GetExchangeUser()
                if exch_user:
                    address = exch_user.PrimarySmtpAddress or address
                    try:
                        extra["department"] = exch_user.Department or ""
                    except Exception:
                        pass
                    try:
                        extra["job_title"] = exch_user.JobTitle or ""
                    except Exception:
                        pass
                    try:
                        extra["company_name"] = exch_user.CompanyName or ""
                    except Exception:
                        pass
            except Exception:
                pass
            attendees.append({"name": name, "email": address, **extra})
        except Exception:
            continue
    return attendees


def _resolve_conversation_id(item) -> str:
    """Safely resolves ConversationID to a real string, or "" for both an
    absent property AND a present-but-COM-inaccessible/non-string one --
    a recurring-occurrence item's own ConversationID has been
    live-confirmed (in the source project) to resolve to a non-string
    bound-method object rather than raising on access itself, which a
    plain `getattr(...) or ""` would silently let through as truthy
    garbage. The try/except guards the read; the isinstance check guards
    the known non-string-but-truthy failure mode."""
    try:
        value = item.ConversationID
    except Exception:
        return ""
    return value if isinstance(value, str) else ""


def list_calendar_events(days_back: int = 7, days_ahead: int = 14, limit: int = 100) -> list[dict]:
    """Sync window is a single bounded date range centred on "now" --
    [now - days_back, now + days_ahead]. IncludeRecurrences = True
    expands a recurring series into individual occurrence items. The
    dedup key is computed downstream in vault_lib.py from this
    function's own `subject` and `start` -- never any raw Outlook
    identity field (EntryID/GlobalAppointmentID/ConversationID have all
    been live-confirmed unreliable as per-occurrence identifiers on a
    real recurring series, in the source project's own history).

    `teams_link`/`dial_in` are extracted TRANSIENTLY from item.Body via
    module-level regexes -- the raw body string itself is read into a
    local variable only, never placed into this function's own returned
    dict, matching the source project's own "raw calendar invite is
    noise, not data" stance."""
    pythoncom.CoInitialize()
    try:
        ns = _connect_namespace()
        calendar = ns.GetDefaultFolder(_OL_FOLDER_CALENDAR)
        items = calendar.Items
        items.Sort("[Start]")
        items.IncludeRecurrences = True
        window_start = datetime.now() - timedelta(days=days_back)
        window_end = datetime.now() + timedelta(days=days_ahead)
        restriction = (
            f"[Start] >= '{window_start.strftime('%m/%d/%Y %H:%M %p')}' AND "
            f"[Start] <= '{window_end.strftime('%m/%d/%Y %H:%M %p')}'"
        )
        restricted_items = items.Restrict(restriction)
        results: list[dict] = []
        for item in restricted_items:
            try:
                raw_body = getattr(item, "Body", "") or ""
                results.append({
                    "id": item.EntryID,
                    "subject": item.Subject or "",
                    "start": str(item.Start),
                    "end": str(item.End),
                    "location": getattr(item, "Location", "") or "",
                    "organizer": getattr(item, "Organizer", "") or "",
                    "attendees": _resolve_attendees(item),
                    "conversation_id": _resolve_conversation_id(item),
                    "is_recurring": bool(getattr(item, "IsRecurring", False)),
                    "series_id": getattr(item, "GlobalAppointmentID", None) or "",
                    "teams_link": _extract_teams_link(raw_body),
                    "dial_in": _extract_dial_in(raw_body),
                })
            except Exception:
                continue  # skip malformed/non-appointment items
            if len(results) >= limit:
                break
        return results
    finally:
        pythoncom.CoUninitialize()
