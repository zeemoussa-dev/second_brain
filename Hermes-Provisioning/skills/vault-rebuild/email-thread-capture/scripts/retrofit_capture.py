"""CLI entry point: a reusable, parameterized retrofit/backfill for the
email-thread-capture pipeline -- bulk-backfills the last N real
Inbox+Sent messages through the SAME FULL per-email pipeline
run_full_capture.py's own live loop uses, not a shortcut.

Built to close a real gap found live, 2026-09-02, post-hoc against
REQ-SB-87-US-02-T05's already-Done real 100-message retrofit: that
retrofit called ingest_email.py DIRECTLY, one message at a time, to
prove ingest/dedup/classification correctness -- but never chained the
same per-email follow-up steps run_full_capture.py's own live loop
always calls right after ingest (rename_thread.py, link_person_to_thread.py,
capture_attachments.py when attachments exist). This left several real
Threads stuck on their raw conversation_id folder name with no automatic
retry path (manually remediated once, by hand, that session -- see
MEMORY.md's own Pattern entry). This script is the reusable fix: any
future retrofit against a brand-new vault, or this one again later,
should use THIS script, never a direct ingest_email.py-only driver.

Minimal-code choice, disclosed: this is a THIN SIBLING orchestrator that
reuses run_full_capture.py's own run_script()-style subprocess pattern,
rather than factoring the per-email loop out of run_full_capture.py/
run_delta_capture.py into a shared helper both would import. Chosen
because it is the smaller, lower-risk change -- it touches neither of
those two already-Done, already-verified real per-email loops at all
(zero risk of regressing their own live cron-facing behavior), at the
cost of the per-email step SEQUENCE (not its logic -- each step's own
real work still lives in exactly one place, that script) being mirrored
here rather than imported. If a third caller of this same sequence ever
appears, factor it into a real shared helper at that point.

Usage:
    python retrofit_capture.py --vault-path P [--limit N]

--vault-path: required, the vault to backfill into.
--limit: how many of the most recent real Inbox+Sent messages to pull,
    default 100 -- passed straight through to list_recent_emails.py's
    own `--limit` (a single bounded pull; list_recent_mail's own
    merge-Inbox+Sent/sort-newest-first/trim-to-limit behavior already
    returns exactly the last N real items in ONE call, so this script
    never pages the way run_full_capture.py's own full-history loop
    does).

Processing order is preserved exactly as list_recent_emails.py returns
it (newest-first) -- NOT re-sorted to oldest-first. This matches
run_full_capture.py's own per-email dispatch shape (it never re-sorts a
page before its own for-loop either) and REQ-SB-87-US-02-T05's own real
100-message retrofit precedent ("in order, matching the orchestrators'
own per-email dispatch shape").

For each message, in that order, chains the SAME four real steps
run_full_capture.py's own per-email loop calls, in the same order (2a-2d):
  1. ingest_email.py       -- create Thread (first-sight)/write message.
  2. link_person_to_thread.py -- only when a sender_email is present.
  3. rename_thread.py      -- always (idempotent no-op once already
                               renamed) -- THIS is the exact step T05's
                               own direct-ingest_email.py retrofit
                               skipped, the gap this script exists to
                               close.
  4. capture_attachments.py -- only when the message actually has
                               attachments AND ingest_email.py returned
                               a real message_path.
Dedup is entirely ingest_email.py's own already-established
(conversation_id, message_id) natural-key idempotency -- this script
adds no new dedup logic of its own, so it is safe to re-run against the
same vault/limit more than once.

Prints one final JSON summary to stdout, mirroring run_full_capture.py's
own summary shape:
{"status": "complete", "limit": int, "total_processed": int,
 "already_existing_topped_up": int, "genuinely_new_captured": int,
 "skipped_as_noise": int, "errors": [{"message_id": str, "error": str}, ...]}
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = str(Path(__file__).resolve().parent)
LOCALAPPDATA = os.environ.get("LOCALAPPDATA") or os.path.expanduser(r"~\AppData\Local")
# Deliberately its OWN scratch subfolder, distinct from run_full_capture.py's/
# run_delta_capture.py's "second_brain_capture_cli" -- avoids any real
# filename collision if this retrofit is ever run alongside either live
# cron job (each writes ingest_<message_id>.json/attach_<message_id>.json
# scratch payloads under its own dir).
SCRATCH_DIR = os.path.join(LOCALAPPDATA, "Temp", "second_brain_retrofit_cli")
os.makedirs(SCRATCH_DIR, exist_ok=True)

PYTHON = sys.executable or "python"


def run_script(args: list[str]) -> tuple[int, str, str]:
    """Run a script in SCRIPTS_DIR and return (code, stdout, stderr) --
    same shape/encoding discipline as run_full_capture.py's own
    run_script()."""
    proc = subprocess.run([PYTHON] + args, cwd=SCRIPTS_DIR, capture_output=True, text=True, encoding="utf-8")
    return proc.returncode, proc.stdout, proc.stderr


def retrofit_capture(vault_path: str, limit: int) -> dict:
    total_processed = 0
    already_existing_topped_up = 0
    genuinely_new_captured = 0
    total_skipped_as_noise = 0
    errors: list[dict] = []

    code, out, err = run_script(["list_recent_emails.py", "--limit", str(limit)])
    if code != 0:
        err_msg = err.strip() or out.strip()
        return {
            "status": "blocked",
            "reason": err_msg or "list_recent_emails failed",
            "limit": limit,
            "total_processed": 0,
        }

    try:
        emails = json.loads(out or "[]")
    except json.JSONDecodeError as exc:
        return {
            "status": "error",
            "reason": f"JSON decode error: {exc}",
            "raw_first_200": (out or "")[:200],
            "limit": limit,
        }

    for e in emails:
        conversation_id = e.get("conversation_id")
        message_id = e.get("id")
        try:
            received = e.get("received")
            sender_name = e.get("sender_name")
            sender_email = e.get("sender_email")
            subject = e.get("subject")
            body = e.get("body") or ""
            recipients = e.get("recipients") or []

            # 2a. ingest_email -- same payload shape run_full_capture.py's
            # own per-email loop builds.
            ingest_payload = {
                "conversation_id": conversation_id,
                "message_id": message_id,
                "received": received,
                "sender_name": sender_name,
                "sender_email": sender_email,
                "subject": subject,
                "body": body,
                "recipients": recipients,
                "direction": e.get("direction") or "",
                "sender_department": e.get("sender_department") or "",
                "sender_job_title": e.get("sender_job_title") or "",
                "sender_company_name": e.get("sender_company_name") or "",
            }
            ingest_path = os.path.join(SCRATCH_DIR, f"ingest_{message_id}.json")
            with open(ingest_path, "w", encoding="utf-8") as f:
                json.dump(ingest_payload, f, ensure_ascii=False)
            code, out, err = run_script(["ingest_email.py", "--vault-path", vault_path, "--input-file", ingest_path])
            if code != 0:
                errors.append({"message_id": message_id, "error": (err.strip() or out.strip())[:1000]})
                continue
            result = json.loads(out.strip() or "{}")
            message_path = result.get("message_path")

            if result.get("skipped_as_noise"):
                total_skipped_as_noise += 1
                total_processed += 1
                continue
            if result.get("thread_created"):
                genuinely_new_captured += 1
            else:
                already_existing_topped_up += 1

            # 2b. link sender person.
            if sender_email:
                run_script([
                    "link_person_to_thread.py",
                    "--vault-path", vault_path,
                    "--conversation-id", conversation_id or "",
                    "--sender-name", sender_name or "",
                    "--sender-email", sender_email,
                ])

            # 2c. rename thread -- the exact step a direct-ingest_email.py-
            # only retrofit driver skips; always called here, idempotent
            # no-op once a Thread is already correctly renamed.
            run_script(["rename_thread.py", "--vault-path", vault_path, "--conversation-id", conversation_id or ""])

            # 2d. attachments.
            attachments = e.get("attachments") or []
            if attachments and message_path:
                cap_payload = {
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "received": received,
                    "message_path": message_path,
                    "attachments": attachments,
                }
                cap_path = os.path.join(SCRATCH_DIR, f"attach_{message_id}.json")
                with open(cap_path, "w", encoding="utf-8") as f:
                    json.dump(cap_payload, f, ensure_ascii=False)
                run_script(["capture_attachments.py", "--vault-path", vault_path, "--input-file", cap_path])

            total_processed += 1
        except Exception as exc:
            errors.append({"message_id": message_id, "error": str(exc)})
            total_processed += 1
            continue

    return {
        "status": "complete",
        "limit": limit,
        "total_processed": total_processed,
        "already_existing_topped_up": already_existing_topped_up,
        "genuinely_new_captured": genuinely_new_captured,
        "skipped_as_noise": total_skipped_as_noise,
        "errors": errors,
    }


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    summary = retrofit_capture(args.vault_path, args.limit)
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary.get("status") == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
