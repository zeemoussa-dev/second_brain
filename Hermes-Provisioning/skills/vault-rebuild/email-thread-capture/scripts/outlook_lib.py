"""Self-contained Outlook desktop COM read for the email-thread-capture
Skill (2026-08-21, "fully hosted in Hermes" pivot). Trimmed port of
Second Brain's own app/data_access/outlook_com.py -- only list_recent_mail
and what it needs; list_calendar_events/list_outlook_tasks are not part
of this Skill's own scope, dropped rather than carried along unused.

Rides Outlook desktop's already-authenticated session on this machine --
no Azure app registration, no OAuth. Requires pywin32 (`pip install
pywin32`, see this Skill's own SKILL.md Prerequisites) and Outlook
desktop running here.

One deliberate divergence from the source: _extract_attachments here
SAVES each real attachment to a durable temp file and returns its path
(never deletes it, never reads it into memory) instead of reading bytes
in-process and discarding the temp file immediately. Necessary because
this Skill's five scripts are separate subprocess invocations (the
`terminal` tool, not one shared Python process) -- raw bytes can't cross
that boundary, but a file path can. capture_attachments.py reads the
bytes back from this path and deletes it once written into the vault.
"""
from __future__ import annotations

import os
import re
import tempfile
import uuid
from datetime import datetime

import pythoncom
import win32com.client

_MAX_BODY_CHARS = 50_000
_MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024
_OL_FOLDER_INBOX = 6
# Sent Mail (2026-08-24, operator: "We didn't pull the outbox to the
# threads... I guess its a must") -- a Thread only had the RECEIVED half
# of a real conversation; Mahmoud's own replies/forwards, sitting in
# this folder, were never captured, silently omitted, no error.
# Confirmed live: `ReceivedTime` is populated on a real Sent Item too
# (Outlook sets it close to `SentOn`, not just on Inbox items), so it
# works as the same real sort/restrict field for both folders -- no
# conditional SentOn/ReceivedTime branching needed. Also confirmed live:
# a real Sent Item's own `SenderEmailAddress` comes back as a raw
# Exchange DN string, not a clean SMTP address -- already handled by
# `_resolve_sender()`'s own existing EX-type `GetExchangeUser()`
# resolution below, reused unchanged for this folder too.
_OL_FOLDER_SENT_MAIL = 5
_OL_MEETING_RECIPIENT_REQUIRED = 1
_OL_MEETING_RECIPIENT_OPTIONAL = 2

_PR_ATTACH_CONTENT_ID = "http://schemas.microsoft.com/mapi/proptag/0x3712001F"
_INLINE_IMAGE_FILENAME = re.compile(r"^image\d{3,4}\.(png|jpe?g|gif|bmp)$", re.IGNORECASE)
_INLINE_IMAGE_KEYWORD = re.compile(r"(signature|thumbnail|logo)", re.IGNORECASE)
_IMAGE_EXTENSION = re.compile(r"\.(png|jpe?g|gif|bmp)$", re.IGNORECASE)
_MEETING_MESSAGE_CLASS_PREFIX = "IPM.Schedule.Meeting"

_CAPTURE_TEMP_PREFIX = "second_brain_capture_"


class OutlookUnavailable(Exception):
    """Outlook isn't running, or COM automation failed to connect."""


def _connect_namespace():
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        return outlook.GetNamespace("MAPI")
    except Exception as exc:
        raise OutlookUnavailable(f"couldn't connect to Outlook — is it running? ({exc})") from exc


def _exchange_user_fields(exch_user) -> dict:
    """Best-effort pull of GAL fields off an already-resolved
    ExchangeUser COM object (2026-08-21, operator: "People need more
    fields (Department, Role)"). Each property read is its own try/except
    -- Exchange returns these as empty/None for plenty of real accounts
    (shared mailboxes, distribution-list senders, older objects), and one
    missing field shouldn't blank out the others. Only ever populated for
    EX-type (internal-Exchange-resolved) senders/recipients -- an
    external SMTP contact has no GetExchangeUser() to call in the first
    place, so these stay empty for them, which is correct: we have no
    real GAL data for someone outside the org."""
    fields = {"department": "", "job_title": "", "company_name": ""}
    try:
        fields["department"] = exch_user.Department or ""
    except Exception:
        pass
    try:
        fields["job_title"] = exch_user.JobTitle or ""
    except Exception:
        pass
    try:
        fields["company_name"] = exch_user.CompanyName or ""
    except Exception:
        pass
    return fields


def _resolve_sender(item) -> dict:
    name = getattr(item, "SenderName", "") or ""
    addr = ""
    extra = {"department": "", "job_title": "", "company_name": ""}
    try:
        addr = item.SenderEmailAddress or ""
        if (item.SenderEmailType or "") == "EX":
            try:
                exch_user = item.Sender.GetExchangeUser()
                if exch_user:
                    addr = exch_user.PrimarySmtpAddress or addr
                    extra = _exchange_user_fields(exch_user)
            except Exception:
                pass
    except Exception:
        addr = ""
    return {"name": name, "email": addr, **extra}


def _is_inline_attachment(att, html_body: str) -> bool:
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
    """Saves each real (non-inline) attachment to a durable temp file --
    see module docstring for why this diverges from the source's
    save-read-delete-immediately shape. Returns {"filename", "temp_path",
    "size"} per attachment; an oversized one (over _MAX_ATTACHMENT_BYTES)
    gets "temp_path": None, same "recorded but not written" precedent
    the source establishes."""
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
            tmp_path = os.path.join(
                tempfile.gettempdir(), f"{_CAPTURE_TEMP_PREFIX}{uuid.uuid4().hex}_{filename}"
            )
            att.SaveAsFile(tmp_path)
            size = os.path.getsize(tmp_path)
            if size > _MAX_ATTACHMENT_BYTES:
                os.remove(tmp_path)
                results.append({"filename": filename, "temp_path": None, "size": size})
            else:
                results.append({"filename": filename, "temp_path": tmp_path, "size": size})
        except Exception:
            continue
    return results


def _resolve_attendees(item) -> list[dict]:
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
            # 2026-09-02 (REQ-SB-87-US-02-T06): these two constants are
            # named for Outlook's MEETING-attendee enum but share their
            # real integer values with mail's own olTo=1/olCC=2 -- reads
            # directly off recipient.Type at the COM layer, never
            # re-derived downstream.
            recipient_type = "to" if recipient.Type == _OL_MEETING_RECIPIENT_REQUIRED else "cc"
            name = recipient.Name or ""
            address = recipient.Address or ""
            extra = {"department": "", "job_title": "", "company_name": ""}
            try:
                exch_user = recipient.AddressEntry.GetExchangeUser()
                if exch_user:
                    address = exch_user.PrimarySmtpAddress or address
                    extra = _exchange_user_fields(exch_user)
            except Exception:
                pass
            attendees.append({"name": name, "email": address, "type": recipient_type, **extra})
        except Exception:
            continue
    return attendees


def resolve_mail_recipients(item) -> list[dict]:
    return _resolve_attendees(item)


def _list_folder_mail(
    folder, limit: int, since: str | None, before: str | None, direction: str,
) -> list[dict]:
    """One folder's own real, filtered/restricted read -- extracted so
    `list_recent_mail` can call this identically for Inbox and Sent Mail
    (2026-08-24 fix, see `_OL_FOLDER_SENT_MAIL`'s own comment) rather
    than duplicating the restrict/iterate/filter logic per folder.

    `direction` (2026-09-02, REQ-SB-87-US-02-T06) is stamped by the
    caller from which of the two real folders this call is actually
    querying ("received" for Inbox, "sent" for Sent Mail) -- never
    inferred afterward from sender_email or participant matching."""
    items = folder.Items
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
        try:
            message_class = getattr(item, "MessageClass", "") or ""
            if message_class.startswith(_MEETING_MESSAGE_CLASS_PREFIX):
                continue
            sender = _resolve_sender(item)
            results.append({
                "id": item.EntryID,
                "subject": item.Subject or "",
                "sender_name": sender["name"],
                "sender_email": sender["email"],
                "sender_department": sender["department"],
                "sender_job_title": sender["job_title"],
                "sender_company_name": sender["company_name"],
                "received": str(item.ReceivedTime),
                "body": (item.Body or "").strip()[:_MAX_BODY_CHARS],
                "attachments": _extract_attachments(item),
                "conversation_id": getattr(item, "ConversationID", None) or "",
                "recipients": resolve_mail_recipients(item),
                "direction": direction,
            })
        except Exception:
            continue
        if len(results) >= limit:
            break
    return results


def list_recent_mail(
    limit: int = 10, since: str | None = None, before: str | None = None,
) -> list[dict]:
    pythoncom.CoInitialize()
    try:
        ns = _connect_namespace()
        # Inbox (received) + Sent Mail (Mahmoud's own replies/forwards) --
        # each queried for up to `limit` on its own, since the real mix
        # between the two in any given window is unknown ahead of time;
        # merged and re-sorted below, THEN trimmed to the real `limit`,
        # so a page never silently favors one folder over the other.
        inbox_results = _list_folder_mail(
            ns.GetDefaultFolder(_OL_FOLDER_INBOX), limit, since, before, direction="received",
        )
        sent_results = _list_folder_mail(
            ns.GetDefaultFolder(_OL_FOLDER_SENT_MAIL), limit, since, before, direction="sent",
        )
        merged = sorted(inbox_results + sent_results, key=lambda e: e["received"], reverse=True)
        return merged[:limit]
    finally:
        pythoncom.CoUninitialize()
