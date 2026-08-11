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

import pythoncom
import win32com.client

_MAX_BODY_CHARS = 50_000
_MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024
_OL_FOLDER_INBOX = 6

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


def _is_inline_attachment(att) -> bool:
    try:
        content_id = att.PropertyAccessor.GetProperty(_PR_ATTACH_CONTENT_ID)
        if content_id:
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
    for i in range(1, count + 1):
        try:
            att = attachments.Item(i)
            if _is_inline_attachment(att):
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


def list_recent_mail(limit: int = 10, unread_only: bool = False) -> list[dict]:
    pythoncom.CoInitialize()
    try:
        ns = _connect_namespace()
        inbox = ns.GetDefaultFolder(_OL_FOLDER_INBOX)
        items = inbox.Items
        items.Sort("[ReceivedTime]", True)
        results: list[dict] = []
        for item in items:
            if unread_only and not getattr(item, "UnRead", False):
                continue
            try:
                message_class = getattr(item, "MessageClass", "") or ""
                if message_class.startswith(_MEETING_MESSAGE_CLASS_PREFIX):
                    continue
                name, addr = _resolve_sender(item)
                results.append({
                    "id": item.EntryID,
                    "subject": item.Subject or "",
                    "sender_name": name,
                    "sender_email": addr,
                    "received": str(item.ReceivedTime),
                    "body": (item.Body or "").strip()[:_MAX_BODY_CHARS],
                    "attachments": _extract_attachments(item),
                    "conversation_id": getattr(item, "ConversationID", None) or "",
                })
            except Exception:
                continue  # skip malformed/non-mail items
            if len(results) >= limit:
                break
        return results
    finally:
        pythoncom.CoUninitialize()
