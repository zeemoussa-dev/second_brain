"""CLI entry point: fetch one bounded page of recent Outlook emails.

Usage:
    python list_recent_emails.py --limit 50 [--since ISO] [--before ISO]

Prints a JSON array of email dicts to stdout, one per email:
{id, subject, sender_name, sender_email, sender_department,
 sender_job_title, sender_company_name, received, body,
 attachments: [{filename, temp_path, size}], conversation_id,
 recipients: [{name, email, department, job_title, company_name}, ...]}

The department/job_title/company_name fields (2026-08-21) come from
Outlook's own GetExchangeUser() GAL lookup -- populated only for
internal, Exchange-resolved senders/recipients; blank for anyone
external (no GAL entry to read).

`attachments[].temp_path` points at a real file on disk holding that
attachment's raw bytes (None if it was too large to save) -- pass it
straight through to capture_attachments.py, which reads and deletes it.
Fetch-only: no vault write, no side effect besides the Outlook read and
the temp files it saves for real attachments.
"""
from __future__ import annotations

import argparse
import json
import sys

from outlook_lib import OutlookUnavailable, list_recent_mail

# A real email body/subject can carry a Unicode character (found live,
# 2026-08-24: U+202F NARROW NO-BREAK SPACE, a real typographic space
# some senders' own signatures use) that Windows' default console
# codepage (cp1252, not UTF-8) can't encode -- printing the JSON output
# without this crashed the WHOLE capture run on that one email, a
# pre-existing bug this surfaced while verifying the Sent Mail fix
# below, not caused by it (any Inbox email with the same character
# would have hit it too).
sys.stdout.reconfigure(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--since", default=None)
    parser.add_argument("--before", default=None)
    args = parser.parse_args()

    try:
        emails = list_recent_mail(limit=args.limit, since=args.since, before=args.before)
    except OutlookUnavailable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(emails, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
