"""graph_lib.py -- Microsoft Graph replacement for outlook_lib.py.

Same public surface, same record shape, no Outlook and no COM: this is a
drop-in for machines where Outlook desktop is not an option (no mail profile
configured, or the mailbox belongs to a DIFFERENT account than the one the
agent runs as -- both true of the CBO agent host, which runs as
cbo-agent01@core42.ai and reads sherif.tawfik@core42.ai).

Public surface, matching outlook_lib.py exactly so `list_recent_emails.py`
needs no change beyond its import line:

    GraphUnavailable          (also exported as OutlookUnavailable)
    list_recent_mail(limit, since, before) -> list[dict]

Auth: app-only (client credentials). Reads GRAPH_TENANT_ID / GRAPH_CLIENT_ID /
GRAPH_CLIENT_SECRET from the environment, which Hermes' own .env supplies to
every Skill subprocess. App-only is deliberate over delegated: a cron run has
no human present to complete an interactive sign-in or refresh a token. The
tenant grant MUST be narrowed by an Application Access Policy scoped to the
one mailbox -- app-only Mail.Read is otherwise tenant-wide.

stdlib only (urllib), matching this Skill's own "stdlib plus pywin32" rule --
Graph is plain HTTPS and needs no SDK.

TWO REAL CONTRACT TRAPS, both load-bearing:

1. `received` MUST be formatted "%Y-%m-%d %H:%M:%S.%f+00:00" -- a SPACE
   separator, not ISO's "T". run_delta_capture.py compares watermarks as
   plain STRINGS, and "T" (0x54) sorts higher than " " (0x20), so an
   isoformat() value would make every same-day message look OLDER than the
   watermark and be silently skipped forever. Graph returns ISO with a "T";
   `_iso_to_outlook_stamp` is the conversion and is not optional.

2. Sender department/job_title/company_name are NOT on a Graph message. The
   directory would supply them but that needs User.Read.All, which this
   deployment deliberately does not request (operator, 2026-09-04: "We can
   extract those from the Signature if found if not skip"). They are parsed
   from the message signature on a best-effort basis and left "" when absent
   -- ingest_email.py already reads them with `.get(...) or ""`, so an empty
   value degrades to an unenriched Person note rather than an error.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone

# Kept identical to outlook_lib.py -- these bound what a Thread note and its
# message children can grow to, and changing one here alone would make the two
# capture paths silently disagree about what "too big" means.
_MAX_BODY_CHARS = 50_000
_MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024

_GRAPH = "https://graph.microsoft.com/v1.0"
_AUTHORITY = "https://login.microsoftonline.com"
_TIMEOUT_SECONDS = 60

# The exact shape str(item.ReceivedTime) produces on the Outlook path. See
# trap 1 in the module docstring -- this is a wire-format contract with
# run_delta_capture.py, not a display choice.
_OUTLOOK_STAMP = "%Y-%m-%d %H:%M:%S.%f+00:00"


class GraphUnavailable(Exception):
    pass

# ── the corporate TLS middlebox ───────────────────────────────────────

# Real, recorded behaviour on this network (MEMORY.md): "the first request
# over a cold connection is reliably reset by the corporate TLS middlebox;
# the immediate retry succeeds." It surfaces as a TRANSPORT error, not an
# HTTP status -- [WinError 10054], or an SSL "UNEXPECTED_EOF_WHILE_READING"
# when the cut lands mid-handshake. Without this retry the FIRST call of
# every cold cron run fails, which for a capture means the run reports a
# failure and writes nothing.
#
# Only transport errors are retried. An HTTPError is a real answer from the
# other end -- a 401 or 403 must surface immediately, never be re-attempted
# as though it were a network blip.
_RETRY_ATTEMPTS = 3
_RETRY_BACKOFF_SECONDS = 1.5


def _urlopen_retrying(request, *, read_bytes: bool = False):
    last: Exception | None = None
    for attempt in range(_RETRY_ATTEMPTS):
        try:
            with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
                raw = response.read()
            return raw if read_bytes else json.loads(raw)
        except urllib.error.HTTPError:
            raise                      # a real answer; never retry
        except Exception as exc:       # transport-level: reset, EOF, timeout
            last = exc
            if attempt < _RETRY_ATTEMPTS - 1:
                time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))
    raise GraphUnavailable(
        f"transport failure after {_RETRY_ATTEMPTS} attempts (corporate TLS "
        f"middlebox resets a cold connection; retries did not recover): {last}"
    )



# `list_recent_emails.py` imports the Outlook name. Aliased rather than
# renamed so this module is a true drop-in and the failure it raises still
# means the same thing to every existing caller.
OutlookUnavailable = GraphUnavailable


# ── formatting ────────────────────────────────────────────────────────

def _iso_to_outlook_stamp(value: str) -> str:
    """Graph's ISO-8601 `receivedDateTime` -> Outlook's own str() shape.

    Returns "" for a missing/unparseable value rather than guessing a time:
    a wrong timestamp would be compared against the watermark as though it
    were real, and could skip a message permanently."""
    if not value:
        return ""
    raw = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime(_OUTLOOK_STAMP)


def _outlook_stamp_to_graph_filter(value: str) -> str:
    """The inverse, for $filter -- Graph will not accept the space form."""
    if not value:
        return ""
    try:
        parsed = datetime.strptime(value, _OUTLOOK_STAMP)
    except ValueError:
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── signature parsing (trap 2) ────────────────────────────────────────

# Deliberately conservative. A false positive writes a wrong job title onto a
# real Person note, which is worse than leaving it blank -- so these only fire
# on an explicit label, never on positional guessing ("the line under the
# name is probably the title").
_LABELLED = {
    "sender_job_title": re.compile(r"^\s*(?:title|job title|position|role)\s*[:|-]\s*(.+)$", re.I),
    "sender_department": re.compile(r"^\s*(?:department|dept|division|team)\s*[:|-]\s*(.+)$", re.I),
    "sender_company_name": re.compile(r"^\s*(?:company|organisation|organization|employer)\s*[:|-]\s*(.+)$", re.I),
}


def parse_signature_fields(body: str) -> dict:
    """Best-effort department / job title / company from a signature block.

    Only the last ~25 lines are considered -- a signature lives at the foot of
    a message, and scanning the whole body would happily read a quoted
    signature from an earlier reply in the chain and attribute it to THIS
    sender."""
    found = {"sender_department": "", "sender_job_title": "", "sender_company_name": ""}
    if not body:
        return found
    for line in [l for l in body.splitlines() if l.strip()][-25:]:
        for field, pattern in _LABELLED.items():
            if found[field]:
                continue
            match = pattern.match(line)
            if match:
                found[field] = match.group(1).strip()[:200]
    return found


# ── HTTP ──────────────────────────────────────────────────────────────

def _require_env(name: str) -> str:
    value = (os.environ.get(name) or "").strip()
    if not value:
        raise GraphUnavailable(
            f"{name} is not set. app-only Graph auth needs GRAPH_TENANT_ID, "
            "GRAPH_CLIENT_ID and GRAPH_CLIENT_SECRET in Hermes' own .env."
        )
    return value


def _access_token() -> str:
    tenant = _require_env("GRAPH_TENANT_ID")
    payload = urllib.parse.urlencode({
        "client_id": _require_env("GRAPH_CLIENT_ID"),
        "client_secret": _require_env("GRAPH_CLIENT_SECRET"),
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }).encode()
    request = urllib.request.Request(f"{_AUTHORITY}/{tenant}/oauth2/v2.0/token", data=payload)
    try:
        token = _urlopen_retrying(request).get("access_token", "")
    except GraphUnavailable:
        raise
    except Exception as exc:  # urllib raises a wide family; all mean "no token"
        raise GraphUnavailable(f"could not obtain a Graph token: {exc}") from exc
    if not token:
        raise GraphUnavailable("Graph returned no access_token")
    return token


def _get(url: str, token: str) -> dict:
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        return _urlopen_retrying(request)
    except GraphUnavailable:
        raise
    except Exception as exc:
        raise GraphUnavailable(f"Graph request failed ({url}): {exc}") from exc


def _get_bytes(url: str, token: str) -> bytes:
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        return _urlopen_retrying(request, read_bytes=True)
    except GraphUnavailable:
        raise
    except Exception as exc:
        raise GraphUnavailable(f"Graph attachment fetch failed ({url}): {exc}") from exc


# ── transforms (pure -- these are what the fixtures exercise) ──────────

def _recipients(message: dict) -> list[dict]:
    """Graph's to/cc lists -> outlook_lib's recipient records.

    department/job_title/company_name are always "" here: they are not on a
    message, and unlike the SENDER there is no signature to mine for a
    recipient. outlook_lib emits the same empty triple for its own
    non-Exchange recipients, so this matches rather than diverges."""
    out: list[dict] = []
    for kind, key in (("to", "toRecipients"), ("cc", "ccRecipients")):
        for entry in message.get(key) or []:
            address = (entry.get("emailAddress") or {})
            out.append({
                "name": address.get("name") or "",
                "email": (address.get("address") or "").lower(),
                "type": kind,
                "department": "",
                "job_title": "",
                "company_name": "",
            })
    return out


def _attachment_records(attachments: list[dict], fetch=None) -> list[dict]:
    """Graph attachment objects -> outlook_lib's attachment records.

    Mirrors outlook_lib's own oversize rule: anything past
    _MAX_ATTACHMENT_BYTES is RECORDED with `temp_path: None` rather than
    dropped, so a Thread still shows that the file existed. Inline images
    (`isInline`) are skipped, matching the Outlook path, which excludes
    embedded signature logos from a message's real attachment list."""
    results: list[dict] = []
    for attachment in attachments or []:
        if attachment.get("isInline"):
            continue
        filename = attachment.get("name") or "attachment"
        size = int(attachment.get("size") or 0)
        if size > _MAX_ATTACHMENT_BYTES or fetch is None:
            results.append({"filename": filename, "temp_path": None, "size": size})
            continue
        content = fetch(attachment)
        if content is None:
            results.append({"filename": filename, "temp_path": None, "size": size})
            continue
        temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}-{filename}")
        with open(temp_path, "wb") as handle:
            handle.write(content)
        results.append({"filename": filename, "temp_path": temp_path, "size": size})
    return results


def message_to_record(message: dict, direction: str, attachments: list[dict] | None = None) -> dict:
    """One Graph message -> one outlook_lib-shaped record.

    Pure: no network, no environment. This is the function the fixtures
    exercise, because it is where every field-mapping mistake would live."""
    body_content = ((message.get("body") or {}).get("content")
                    or message.get("bodyPreview") or "")
    body = body_content.strip()[:_MAX_BODY_CHARS]
    sender = ((message.get("from") or message.get("sender") or {}).get("emailAddress") or {})
    signature = parse_signature_fields(body)
    return {
        "id": message.get("id") or "",
        "subject": message.get("subject") or "",
        "sender_name": sender.get("name") or "",
        "sender_email": (sender.get("address") or "").lower(),
        "sender_department": signature["sender_department"],
        "sender_job_title": signature["sender_job_title"],
        "sender_company_name": signature["sender_company_name"],
        "received": _iso_to_outlook_stamp(message.get("receivedDateTime") or ""),
        "body": body,
        "attachments": attachments if attachments is not None else [],
        "conversation_id": message.get("conversationId") or "",
        "recipients": _recipients(message),
        "direction": direction,
    }


# ── the public call ───────────────────────────────────────────────────

_SELECT = "id,subject,from,sender,toRecipients,ccRecipients,receivedDateTime,conversationId,body,hasAttachments"


def _folder_url(mailbox: str, folder: str, limit: int, since: str | None, before: str | None) -> str:
    clauses = []
    since_filter = _outlook_stamp_to_graph_filter(since or "")
    before_filter = _outlook_stamp_to_graph_filter(before or "")
    if since_filter:
        clauses.append(f"receivedDateTime gt {since_filter}")
    if before_filter:
        clauses.append(f"receivedDateTime lt {before_filter}")
    params = {
        "$select": _SELECT,
        "$top": str(max(1, int(limit))),
        "$orderby": "receivedDateTime desc",
    }
    if clauses:
        params["$filter"] = " and ".join(clauses)
    return (f"{_GRAPH}/users/{urllib.parse.quote(mailbox)}/mailFolders/{folder}/messages"
            f"?{urllib.parse.urlencode(params, safe='$,() ')}")


def list_recent_mail(limit: int = 10, since: str | None = None, before: str | None = None) -> list[dict]:
    """Inbox + Sent, merged newest-first and trimmed to `limit`.

    Queries each folder for up to `limit` on its own before merging, exactly
    as outlook_lib does: the real mix between received and sent in any given
    window is unknown ahead of time, so trimming per-folder first would
    silently favour whichever side happened to be busier."""
    mailbox = (os.environ.get("SECOND_BRAIN_SELF_EMAIL") or os.environ.get("SELF_EMAIL") or "").strip()
    if not mailbox:
        raise GraphUnavailable(
            "SECOND_BRAIN_SELF_EMAIL is not set -- app-only Graph reads a NAMED "
            "mailbox (/users/<address>/messages); there is no 'me' without a signed-in user."
        )
    token = _access_token()
    merged: list[dict] = []
    for folder, direction in (("inbox", "received"), ("sentitems", "sent")):
        payload = _get(_folder_url(mailbox, folder, limit, since, before), token)
        for message in payload.get("value") or []:
            attachments: list[dict] = []
            if message.get("hasAttachments"):
                listing = _get(
                    f"{_GRAPH}/users/{urllib.parse.quote(mailbox)}/messages/"
                    f"{urllib.parse.quote(message['id'])}/attachments",
                    token,
                )
                attachments = _attachment_records(
                    listing.get("value") or [],
                    fetch=lambda a: (_get_bytes(
                        f"{_GRAPH}/users/{urllib.parse.quote(mailbox)}/messages/"
                        f"{urllib.parse.quote(message['id'])}/attachments/"
                        f"{urllib.parse.quote(a['id'])}/$value", token)
                        if a.get("id") else None),
                )
            merged.append(message_to_record(message, direction, attachments))
    merged.sort(key=lambda record: record["received"], reverse=True)
    return merged[:limit]
