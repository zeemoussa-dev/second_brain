"""Reads mail via Outlook's own desktop COM automation — rides the
already-authenticated session Outlook has open on this laptop. No Azure app
registration, no OAuth, no admin consent: this only works while Outlook
desktop is running here (per MEMORY.md's Hermes integration-sourcing
constraint — Graph API is blocked by company policy).

Ported from agentic-map's services/gateway/outlook_com.py (see that repo's
ADR-0018 for the full rationale). Second Brain only needs the read path for
this POC — write actions (compose/send/archive/label) were intentionally not
ported; add them here if a future requirement needs them.
"""
from __future__ import annotations

import os
import re
import tempfile
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta

import pythoncom
import win32com.client

_MAX_BODY_CHARS = 50_000
_MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024
_OL_FOLDER_INBOX = 6

# Outlook's well-known Calendar default folder (OlDefaultFolders.
# olFolderCalendar) — ported from agentic-map's outlook_com.py precedent
# (ADR-008), this codebase's first calendar-read capability.
_OL_FOLDER_CALENDAR = 9

# Outlook's well-known Tasks default folder (OlDefaultFolders.
# olFolderTasks) — this codebase's first Outlook Tasks-folder read
# capability (REQ-SB-09, ADR-027). Reachable via the identical
# GetDefaultFolder mechanism mail/calendar already use.
_OL_FOLDER_TASKS = 13

# OlTaskStatus: olTaskNotStarted=0, olTaskInProgress=1,
# olTaskComplete=2, olTaskWaiting=3, olTaskDeferred=4. Mapped down to
# the resolved schema's three-value status (ADR-027 point 2) by
# _map_task_status, below — never passed through raw.
_OL_TASK_STATUS_IN_PROGRESS = 1

# Outlook's own "no due date set" sentinel for TaskItem.DueDate —
# TaskItem.DueDate is never a true COM null; an unset due date reads
# back as this fixed placeholder date (a standard, documented Outlook
# convention). _normalize_task_due_date (below) detects this and
# returns None instead of the sentinel string, which is what makes
# the resolved schema's "due (if set); omitted if none is set"
# possible at all. Live-COM latitude: corrected against this real
# Outlook installation's own str(pywintypes.Time) rendering
# ("4501-01-01 00:00:00+00:00", an ISO-shaped string, not the
# originally-guessed "1/1/4501" US-locale-shaped one) — logged in
# REQ-SB-09-US-01-T01's own Implementation Log as a scope-internal
# implementation detail, not an escalation, the same latitude
# REQ-SB-08-US-01-T01 was given for its own Restrict syntax.
_OL_TASK_NO_DUE_DATE_SENTINEL_PREFIX = "4501-01-01"

# OlMeetingRecipientType: olOrganizer=0, olRequired=1, olOptional=2,
# olResource=3 — attendee resolution (below) includes only 1 and 2, merging
# "required" (To) and "optional" (Cc) into one flat list per ADR-008 (the
# resolved Meetings schema makes no required/optional distinction). The
# organizer (0) and any booked room/resource (3) are not real person
# attendees and are excluded.
_OL_MEETING_RECIPIENT_REQUIRED = 1
_OL_MEETING_RECIPIENT_OPTIONAL = 2

# MAPI PidTagAttachContentId — set when an attachment is referenced inline via
# cid: in the HTML body (a signature logo, a pasted-in-body image), not sent
# as a real file. agentic-map's own outlook_com.py explicitly punted on this
# ("no reliable COM flag... everything gets extracted the same way") because
# its use case (mining signature blocks) wants the images; Second Brain's
# customer-knowledge use case doesn't, so this diverges from that precedent
# rather than blindly copying it.
_PR_ATTACH_CONTENT_ID = "http://schemas.microsoft.com/mapi/proptag/0x3712001F"

# Outlook's own auto-generated filename pattern for pasted/inline images —
# a fallback for cases where PR_ATTACH_CONTENT_ID isn't set but the file is
# still clearly inline art, not a shared document.
_INLINE_IMAGE_FILENAME = re.compile(r"^image\d{3,4}\.(png|jpe?g|gif|bmp)$", re.IGNORECASE)
# Found live 2026-08-10: a recurring "thumbnail_emailsignature_new-02_<guid>.jpg"
# attachment (a corporate signature graphic) didn't match the imageNNN pattern
# above and slipped through — this catches filenames that name themselves as
# signature/logo/thumbnail art regardless of the exact naming scheme.
_INLINE_IMAGE_KEYWORD = re.compile(
    r"(signature|thumbnail|logo)", re.IGNORECASE
)
_IMAGE_EXTENSION = re.compile(r"\.(png|jpe?g|gif|bmp)$", re.IGNORECASE)

# Transient teams_link/dial_in extraction (REQ-SB-71-US-03-T01, ADR-048
# Decision 5) -- live-confirmed regex shapes against this real Outlook
# installation's own Teams-meeting invite footer format: a "Join: <url>
# <safelinks-wrapped-url>" line (the plain URL always precedes the
# safelinks redirect, so capturing up to the first whitespace/`<` yields
# the clean, real join link) and a "<tel:+<digits>,,<conference-id>#>"
# machine-readable phone reference inside the "Dial in by phone" block.
# Both are best-effort, honest-empty-string-on-no-match -- a non-Teams
# invite (Zoom, in-person, no conferencing at all) simply yields "" for
# one or both fields, never a crash or a fabricated value. The raw body
# string these are extracted from is NEVER itself returned by
# list_calendar_events -- see that function's own docstring.
_TEAMS_JOIN_LINK_PATTERN = re.compile(r"Join:\s*(https?://\S+)")
_TEAMS_LINK_FALLBACK_PATTERN = re.compile(r"(https://teams\.microsoft\.com/\S+)")
_DIAL_IN_TEL_PATTERN = re.compile(r"<tel:([^>]+)>")


def _extract_teams_link(raw_body: str) -> str:
    match = _TEAMS_JOIN_LINK_PATTERN.search(raw_body)
    if match:
        return match.group(1)
    match = _TEAMS_LINK_FALLBACK_PATTERN.search(raw_body)
    return match.group(1) if match else ""


def _extract_dial_in(raw_body: str) -> str:
    match = _DIAL_IN_TEL_PATTERN.search(raw_body)
    return match.group(1) if match else ""


# Real meeting invites/responses land in the Inbox with this MessageClass
# family — they aren't mail and are excluded here entirely (Meeting notes are
# separate future scope; see Implementation/Plans/2026-08-10-vault-taxonomy-
# draft.md). Plain mail (including automated notifications like file-share
# alerts) is always "IPM.Note" — Outlook has no separate class for those, so
# distinguishing a real email from a notification is Compass's job, not
# Outlook's (see app/data_access/compass_client.py's `kind` classification).
_MEETING_MESSAGE_CLASS_PREFIX = "IPM.Schedule.Meeting"


class OutlookUnavailable(Exception):
    """Outlook isn't running, or COM automation failed to connect."""


def _connect_namespace():
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        return outlook.GetNamespace("MAPI")
    except Exception as exc:
        raise OutlookUnavailable(f"couldn't connect to Outlook — is it running? ({exc})") from exc


def check_reachable() -> dict:
    """One new, lightweight, real (but local, zero-external-cost)
    reachability check (REQ-SB-11) -- attempts the exact same
    Dispatch("Outlook.Application")/GetNamespace("MAPI") connection
    _connect_namespace() already makes for every real read, purely to
    report whether Outlook desktop is currently reachable. Never raises
    past its own body -- an OutlookUnavailable failure is caught and
    reported honestly, with the real underlying message, never a
    fabricated True."""
    pythoncom.CoInitialize()
    try:
        _connect_namespace()
        return {"reachable": True, "detail": None}
    except OutlookUnavailable as exc:
        return {"reachable": False, "detail": str(exc)}
    finally:
        pythoncom.CoUninitialize()


def _resolve_sender(item) -> tuple[str, str]:
    name = getattr(item, "SenderName", "") or ""
    try:
        addr = item.SenderEmailAddress or ""
        if (item.SenderEmailType or "") == "EX":
            try:
                exch_user = item.Sender.GetExchangeUser()
                if exch_user:
                    addr = exch_user.PrimarySmtpAddress or addr
            except Exception:
                pass
    except Exception:
        addr = ""
    return name, addr


def _is_inline_attachment(att, html_body: str) -> bool:
    """BUG-017 fix, 2026-08-17: a non-empty PR_ATTACH_CONTENT_ID alone is
    NOT proof an attachment is genuinely inline -- some sending mail
    systems stamp a Content-ID on ordinary, real, standalone attachments
    too (confirmed live: a real 4.96MB PDF, legitimately attached, had
    its own Content-ID and was silently dropped by the old "any
    Content-ID means inline" logic before ever reaching the capture
    pipeline). The correct signal is whether that Content-ID is actually
    REFERENCED inline in the message's own HTML body via a `cid:` URL
    (e.g. `<img src="cid:...">`) -- that's what "inline" means. A
    Content-ID that exists but is never referenced falls through to the
    filename-based heuristics below, same as an attachment with no
    Content-ID at all."""
    try:
        content_id = att.PropertyAccessor.GetProperty(_PR_ATTACH_CONTENT_ID)
        if content_id:
            cid = content_id.strip("<>")
            if cid and f"cid:{cid}" in (html_body or ""):
                return True
    except Exception:
        pass
    filename = (att.FileName or "").strip()
    if _INLINE_IMAGE_FILENAME.match(filename):
        return True
    return bool(_INLINE_IMAGE_KEYWORD.search(filename) and _IMAGE_EXTENSION.search(filename))


def _extract_attachments(item) -> list[dict]:
    """Same technique as agentic-map's outlook_com.py: COM's Attachment object
    has no in-memory byte access, so each one is saved to a temp file, read,
    then deleted immediately — nothing persists on disk past this call.
    Best-effort per attachment; one unreadable file doesn't lose the others.
    Inline signature/body images are skipped entirely — see
    _is_inline_attachment's docstring for why this diverges from agentic-map's
    own precedent of keeping everything."""
    results: list[dict] = []
    try:
        attachments = item.Attachments
        count = attachments.Count
    except Exception:
        return results
    html_body = ""
    try:
        html_body = item.HTMLBody or ""
    except Exception:
        pass
    for i in range(1, count + 1):
        try:
            att = attachments.Item(i)
            if _is_inline_attachment(att, html_body):
                continue
            filename = att.FileName or f"attachment_{i}"
            tmp_path = os.path.join(tempfile.gettempdir(), f"second_brain_att_{uuid.uuid4().hex}_{filename}")
            att.SaveAsFile(tmp_path)
            try:
                with open(tmp_path, "rb") as f:
                    content = f.read()
            finally:
                os.remove(tmp_path)
            results.append({
                "filename": filename,
                "content": content if len(content) <= _MAX_ATTACHMENT_BYTES else None,
                "size": len(content),
            })
        except Exception:
            continue
    return results


def list_recent_mail(
    limit: int = 10,
    unread_only: bool = False,
    on_item_fetched: Callable[[dict], None] | None = None,
    since: str | None = None,
    before: str | None = None,
) -> list[dict]:
    """on_item_fetched (ADR-046 Decision 2, REQ-SB-69-US-01-T02) is an
    optional, additive callback fired once per item, immediately after
    that item's own dict is fully resolved (sender/attachments/
    recipients) -- inside this loop, before continuing to the next item,
    never buffered until the whole loop returns. This is what makes
    email_pull.py::pull_and_stage_emails' own staging genuinely
    live-updating/resumable: a stall/exception on a LATER item still
    leaves every already-fetched item durably staged via the callback
    that already fired for it. Every existing caller that passes nothing
    (classify_recent_emails, email_poc_router.py's POC endpoint) sees
    zero behavior change -- this parameter is purely additive.

    `since`/`before` (2026-08-20, additive) -- ISO 8601 datetime strings;
    when given, only items received at/after `since` and/or before
    `before` are considered, via `items.Restrict()` (server/COM-side
    filtering, matching this same file's own `list_upcoming_meetings`
    precedent for date-range filtering -- never a Python-side loop-break,
    which would still walk every older item just to discard it). Combines
    with `limit` as an independent cap -- whichever is hit first stops the
    loop. `before` is what makes a full historical walk possible: page
    backward through time by repeatedly calling with `before` set to the
    oldest `received` timestamp seen in the previous page (an agent-driven
    cron job, not a loop inside this function -- this function itself
    stays one bounded page, per the Bulk data principle)."""
    pythoncom.CoInitialize()
    try:
        ns = _connect_namespace()
        inbox = ns.GetDefaultFolder(_OL_FOLDER_INBOX)
        items = inbox.Items
        items.Sort("[ReceivedTime]", True)
        restrictions = []
        if since is not None:
            since_dt = datetime.fromisoformat(since)
            restrictions.append(f"[ReceivedTime] >= '{since_dt.strftime('%m/%d/%Y %H:%M %p')}'")
        if before is not None:
            before_dt = datetime.fromisoformat(before)
            restrictions.append(f"[ReceivedTime] < '{before_dt.strftime('%m/%d/%Y %H:%M %p')}'")
        if restrictions:
            items = items.Restrict(" AND ".join(restrictions))
        results: list[dict] = []
        for item in items:
            if unread_only and not getattr(item, "UnRead", False):
                continue
            try:
                message_class = getattr(item, "MessageClass", "") or ""
                if message_class.startswith(_MEETING_MESSAGE_CLASS_PREFIX):
                    continue
                name, addr = _resolve_sender(item)
                fetched_item = {
                    "id": item.EntryID,
                    "subject": item.Subject or "",
                    "sender_name": name,
                    "sender_email": addr,
                    "received": str(item.ReceivedTime),
                    "body": (item.Body or "").strip()[:_MAX_BODY_CHARS],
                    "attachments": _extract_attachments(item),
                    "conversation_id": getattr(item, "ConversationID", None) or "",
                    "recipients": resolve_mail_recipients(item),
                }
                results.append(fetched_item)
                if on_item_fetched is not None:
                    on_item_fetched(fetched_item)
            except Exception:
                continue  # skip malformed/non-mail items
            if len(results) >= limit:
                break
        return results
    finally:
        pythoncom.CoUninitialize()


def _resolve_attendees(item) -> list[dict]:
    """Resolves item.Recipients into structured {"name", "email"} pairs,
    merging required (To) and optional (Cc) attendees into one flat list
    (ADR-008) — the resolved Meetings schema's Attendees line makes no
    required/optional distinction. Excludes the organizer (Type 0) and any
    resource recipient (Type 3, e.g. a booked meeting room) — neither is a
    real person attendee. Internal Exchange recipients resolve to their
    real SMTP address via GetExchangeUser() (same technique _resolve_sender
    already uses for mail); external recipients fall back to
    recipient.Address as-is. Best-effort per recipient — one unresolvable
    entry doesn't lose the others."""
    attendees: list[dict] = []
    try:
        recipients = item.Recipients
        count = recipients.Count
    except Exception:
        return attendees
    for i in range(1, count + 1):
        try:
            recipient = recipients.Item(i)
            if recipient.Type not in (
                _OL_MEETING_RECIPIENT_REQUIRED,
                _OL_MEETING_RECIPIENT_OPTIONAL,
            ):
                continue
            name = recipient.Name or ""
            address = recipient.Address or ""
            try:
                exch_user = recipient.AddressEntry.GetExchangeUser()
                if exch_user:
                    address = exch_user.PrimarySmtpAddress or address
            except Exception:
                pass
            attendees.append({"name": name, "email": address})
        except Exception:
            continue
    return attendees


def resolve_mail_recipients(item) -> list[dict]:
    """Public generalization of _resolve_attendees (ADR-036 point 7) --
    a MailItem exposes the identical .Recipients collection shape/type
    values (olTo=1/olCC=2) a meeting AppointmentItem does, confirmed by
    direct reading of _resolve_attendees above (it reads only
    .Recipients/.Type/.Name/.Address/.AddressEntry -- nothing meeting-
    specific). Merges To + CC into one flat list, same "no required/
    optional distinction" precedent ADR-008 already established for
    meetings. _resolve_attendees itself stays private and unmodified --
    this is a new, additive public sibling, not a rename."""
    return _resolve_attendees(item)


def _resolve_conversation_id(item) -> str:
    """Safely resolves an item's own ConversationID to a real string, or
    "" for BOTH an absent property AND a present-but-COM-inaccessible/
    non-string one -- e.g. an IncludeRecurrences-expanded recurring-
    occurrence item, whose ConversationID attribute resolves to a
    non-string bound-method object rather than raising on access itself
    (ESC-040, live-confirmed 2026-08-17: 40.5% of a real sampled
    calendar window, all recurring-occurrence items). Deliberately NOT
    list_recent_mail's own `getattr(item, "ConversationID", None) or ""`
    pattern -- that pattern's `or ""` only filters a falsy value, and a
    bound-method object is truthy, so it would silently pass the broken
    value through as if it were a real conversation id. The try/except
    guards the attribute read itself; the isinstance check guards
    against the known non-string-but-truthy failure mode."""
    try:
        value = item.ConversationID
    except Exception:
        return ""
    return value if isinstance(value, str) else ""


def list_calendar_events(days_back: int = 7, days_ahead: int = 14, limit: int = 50) -> list[dict]:
    """New calendar-read function (ADR-008) — ports agentic-map's
    list_upcoming_events/list_calendar_since COM mechanics
    (GetDefaultFolder(9), IncludeRecurrences = True) into this codebase's
    list_recent_mail-shaped conventions. The sync window is a single
    bounded date range centred on "now" — [now - days_back, now +
    days_ahead] — rather than either of agentic-map's two narrower
    semantics alone (ADR-008's Alternatives Considered explains why).
    IncludeRecurrences = True is what expands a recurring series into
    individual occurrence items. The dedup key (ADR-019) is computed
    downstream in vault_writer.py from this function's own `subject` and
    `start` fields — a hash of the two, not any Outlook-provided identity
    field. Both `EntryID` (ADR-008) and `GlobalAppointmentID` (ADR-013)
    were tried and live-confirmed non-unique across a real recurring
    series' expanded occurrences (ESC-002, ESC-012); `id` (EntryID) is
    still returned here for informational purposes and the legacy-path
    lookup only — it is never itself the dedup key. `conversation_id`
    (REQ-SB-56-US-01-T01) is the third per-item COM identity/relationship
    property live-confirmed unreliable on the exact same recurring-
    occurrence fraction of this installation's calendar (ESC-040) —
    resolved via `_resolve_conversation_id`, never the naive
    `getattr(...) or ""` pattern, so a broken value degrades to `""`
    instead of a truthy garbage object.

    `is_recurring`/`series_id` (REQ-SB-71-US-03-T01, ADR-048 Decision 5)
    are the one-time-vs-recurring split's own new fields: `IsRecurring`
    (a genuine, direct boolean COM property, unlike the three unreliable
    identity fields above) and `GlobalAppointmentID` (ADR-013) — this
    time used ONLY as a series key (constant across every occurrence of a
    series, the exact property ADR-013/ESC-012 already live-confirmed and
    rejected as a per-OCCURRENCE dedup key), never as a per-occurrence
    identifier. `teams_link`/`dial_in` are extracted TRANSIENTLY from
    `item.Body` via `_extract_teams_link`/`_extract_dial_in` — the raw
    body string itself is read into a local variable only, never placed
    into this function's own returned dict, never reaching any caller,
    business-layer code, or disk (the deliberate, operator-authorized
    "raw calendar invite content is dropped entirely, never archived"
    exception to this project's own archive-not-delete discipline)."""
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


def _map_task_status(item) -> str:
    """Three-value business rule (ADR-027 point 2), not a raw
    pass-through of Outlook's own five-value OlTaskStatus enum.
    item.Complete is authoritative and checked first, independent of
    Status — Scenario 5's own "status field honestly reflects that
    it is complete" requires this even if Status itself reads
    stale. Falls back to In Progress only for the one Outlook status
    value that means that; every other remaining value (NotStarted,
    Waiting, Deferred) maps to "Not Started"."""
    try:
        if bool(getattr(item, "Complete", False)):
            return "Completed"
    except Exception:
        pass
    try:
        if item.Status == _OL_TASK_STATUS_IN_PROGRESS:
            return "In Progress"
    except Exception:
        pass
    return "Not Started"


def _normalize_task_due_date(item) -> str | None:
    """TaskItem.DueDate is never a true null in COM -- an unset due
    date reads back as Outlook's own fixed sentinel date rather than
    None. Returns None (not the sentinel string) when detected --
    this defensive guard is what makes the resolved schema's "due
    (if set); omitted if none is set" possible at all, not optional
    polish (ADR-027 point 1)."""
    try:
        due = item.DueDate
    except Exception:
        return None
    if due is None:
        return None
    due_str = str(due)
    if due_str.startswith(_OL_TASK_NO_DUE_DATE_SENTINEL_PREFIX):
        return None
    return due_str


def list_outlook_tasks(limit: int = 100) -> list[dict]:
    """New Tasks-folder read function (REQ-SB-09, ADR-027).
    ns.GetDefaultFolder(13) -- no date-window parameters, unlike
    list_calendar_events -- a task has no natural "occurs near now"
    framing; an undated or far-future-due task is still relevant
    until completed. No IncludeRecurrences-equivalent property exists
    on the Tasks folder's Items collection at all (a structural fact
    about the Outlook Object Model, not an empirical claim about this
    mailbox) -- a recurring Outlook Task shows as a single live item
    at a time, unlike Calendar's occurrence-expansion mechanism.
    id (EntryID) is returned for informational purposes and as the
    dedup/top-up lookup key vault_writer.py's task_note_index
    consults (ADR-027 point 3) -- it is never itself a recomputed
    filename disambiguator the way Calendar's EntryID/
    GlobalAppointmentID attempts were (ESC-002, ESC-012); the
    structural reason those don't apply to Tasks is exactly the
    missing IncludeRecurrences-equivalent noted above."""
    pythoncom.CoInitialize()
    try:
        ns = _connect_namespace()
        tasks_folder = ns.GetDefaultFolder(_OL_FOLDER_TASKS)
        items = tasks_folder.Items
        results: list[dict] = []
        for item in items:
            try:
                results.append({
                    "id": item.EntryID,
                    "subject": item.Subject or "",
                    "due": _normalize_task_due_date(item),
                    "status": _map_task_status(item),
                    "body": (getattr(item, "Body", "") or "").strip()[:_MAX_BODY_CHARS],
                })
            except Exception:
                continue  # skip malformed/non-task items
            if len(results) >= limit:
                break
        return results
    finally:
        pythoncom.CoUninitialize()
