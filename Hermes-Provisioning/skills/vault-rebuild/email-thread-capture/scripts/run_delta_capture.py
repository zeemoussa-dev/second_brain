"""Single-process orchestrator for the RECURRING, incremental email
capture loop (2026-08-22) -- the delta sibling of run_full_capture.py
(which stays as-is: the proven, one-time, full-history tool). Same
single-`terminal`-call, O(1)-LLM-calls design (see that script's own
module docstring for why), same per-email steps (ingest, link sender,
rename thread, attachments) -- the only real difference is WHERE the
pagination stops.

Full capture pages backward via `--before` until Outlook returns zero
results (the true start of history). This script pages backward the
same way, but stops as soon as a page's emails are no longer newer than
the last run's own persisted watermark -- so a recurring cron run only
ever re-walks the small sliver of NEW mail since it last ran, not the
whole mailbox. The watermark lives in
`.second-brain/email_capture_state.json` (real, accessible, persisted
state -- never a hardcoded literal), holding the newest `received`
timestamp this script has ever actually captured. Missing state (first
ever delta run) seeds a conservative 2-day lookback rather than either a
full-history redo (full_capture.py already did that once) or blindly
trusting "now" (which could silently miss a real gap since that last
full run).
"""
from __future__ import annotations
import os
import sys
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

VAULT_PATH = os.environ.get("SECOND_BRAIN_VAULT_PATH", r"C:\myWorx\Moussa MD\Moussa Brain")
SCRIPTS_DIR = str(Path(__file__).resolve().parent)
LOCALAPPDATA = os.environ.get("LOCALAPPDATA") or os.path.expanduser(r"~\AppData\Local")
SCRATCH_DIR = os.path.join(LOCALAPPDATA, "Temp", "second_brain_capture_cli")
os.makedirs(SCRATCH_DIR, exist_ok=True)
SUMMARY_PATH = os.path.join(SCRATCH_DIR, "email_delta_capture_summary.json")

STATE_DIR = ".second-brain"
STATE_FILE = "email_capture_state.json"
BOOTSTRAP_LOOKBACK_DAYS = 2

PYTHON = sys.executable or "python"


def ensure_pywin32():
    try:
        import win32com  # type: ignore
        return True, "ok"
    except Exception as e:
        install_cmd = [PYTHON, "-m", "pip", "install", "pywin32"]
        proc = subprocess.run(install_cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            return False, f"pip install pywin32 failed: code={proc.returncode} stderr={proc.stderr.strip()}"
        try:
            import win32com  # type: ignore
            return True, "installed"
        except Exception as e2:
            return False, f"win32com import still failing after install: {e2}"


def run_script(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run([PYTHON] + args, cwd=SCRIPTS_DIR, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def _state_path() -> Path:
    return Path(VAULT_PATH) / STATE_DIR / STATE_FILE


def load_watermark() -> str:
    path = _state_path()
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        watermark = data.get("last_captured_at")
        if watermark:
            return watermark
    # First ever delta run (or a corrupted/empty state file) -- seed a
    # conservative lookback rather than a full-history redo or "now".
    # Formatted to match Outlook's OWN str(item.ReceivedTime) shape
    # exactly (space separator, not ISO's "T") -- watermark comparisons
    # throughout this script are plain string comparisons against real
    # Outlook-formatted `received` values, and "T" (0x54) sorts higher
    # than " " (0x20), so an isoformat()-style fallback would silently
    # treat every same-day real timestamp as "older" than the watermark.
    fallback_dt = datetime.now(timezone.utc) - timedelta(days=BOOTSTRAP_LOOKBACK_DAYS)
    return fallback_dt.strftime("%Y-%m-%d %H:%M:%S.%f+00:00")


def save_watermark(value: str) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"last_captured_at": value}, indent=2), encoding="utf-8")


def main() -> int:
    ok, msg = ensure_pywin32()
    if not ok:
        print(f"FATAL: pywin32 unavailable: {msg}")
        return 3

    watermark = load_watermark()

    total_emails = 0
    total_threads_created = 0
    total_messages_created = 0
    total_attachments_captured = 0

    page_num = 0
    before_ts: str | None = None
    newest_seen: str | None = None
    reached_watermark = False

    progress: list[dict] = []

    while True:
        page_num += 1
        args = ["list_recent_emails.py", "--limit", "50"]
        if before_ts:
            args += ["--before", before_ts]
        code, out, err = run_script(args)
        if code != 0:
            err_msg = err.strip() or out.strip()
            print(f"PAGE {page_num}: list_recent_emails failed (code {code}): {err_msg}")
            summary = {
                "status": "blocked",
                "reason": err_msg or "list_recent_emails failed",
                "page": page_num,
                "processed_emails": total_emails,
            }
            with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            return 2

        try:
            emails = json.loads(out or "[]")
        except json.JSONDecodeError as e:
            print(f"PAGE {page_num}: JSON decode error: {e}")
            summary = {"status": "error", "reason": f"JSON decode error on page {page_num}", "raw_first_200": (out or "")[:200]}
            with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            return 2

        if not emails:
            break  # genuinely no more mail (empty mailbox / true start of history)

        rec_times = [e.get("received") for e in emails if e.get("received")]
        page_oldest = min(rec_times) if rec_times else None
        page_newest = max(rec_times) if rec_times else None
        if newest_seen is None and page_newest:
            newest_seen = page_newest

        # Only emails strictly newer than the watermark are new -- a page
        # can be a mix (the watermark boundary falls inside it), so filter
        # per-email rather than an all-or-nothing page decision.
        new_emails = [e for e in emails if (e.get("received") or "") > watermark]
        if len(new_emails) < len(emails):
            reached_watermark = True  # this page crosses into already-captured territory

        page_processed = 0
        page_threads_created = 0
        page_messages_created = 0
        page_attachments_captured = 0

        for e in new_emails:
            try:
                conversation_id = e.get("conversation_id")
                message_id = e.get("id")
                received = e.get("received")
                sender_name = e.get("sender_name")
                sender_email = e.get("sender_email")
                subject = e.get("subject")
                body = e.get("body") or ""
                recipients = e.get("recipients") or []

                ingest_payload = {
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "received": received,
                    "sender_name": sender_name,
                    "sender_email": sender_email,
                    "subject": subject,
                    "body": body,
                    "recipients": recipients,
                    "sender_department": e.get("sender_department") or "",
                    "sender_job_title": e.get("sender_job_title") or "",
                    "sender_company_name": e.get("sender_company_name") or "",
                }
                ingest_path = os.path.join(SCRATCH_DIR, f"ingest_{message_id}.json")
                with open(ingest_path, "w", encoding="utf-8") as f:
                    json.dump(ingest_payload, f, ensure_ascii=False)
                code, out, err = run_script(["ingest_email.py", "--vault-path", VAULT_PATH, "--input-file", ingest_path])
                message_path = None
                if code == 0:
                    try:
                        result = json.loads(out.strip() or "{}")
                        if result.get("thread_created"):
                            page_threads_created += 1
                        if result.get("message_created"):
                            page_messages_created += 1
                        message_path = result.get("message_path")
                    except Exception:
                        pass

                if sender_email:
                    _ = run_script([
                        "link_person_to_thread.py",
                        "--vault-path", VAULT_PATH,
                        "--conversation-id", conversation_id or "",
                        "--sender-name", sender_name or "",
                        "--sender-email", sender_email,
                    ])

                _ = run_script(["rename_thread.py", "--vault-path", VAULT_PATH, "--conversation-id", conversation_id or ""])

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
                    code, out, err = run_script(["capture_attachments.py", "--vault-path", VAULT_PATH, "--input-file", cap_path])
                    if code == 0:
                        try:
                            r = json.loads(out.strip() or "{}")
                            page_attachments_captured += len(r.get("captured", []))
                        except Exception:
                            pass

                page_processed += 1
                total_emails += 1
            except Exception as ex:
                print(f"PAGE {page_num}: email {e.get('id')!r} failed: {ex}")
                page_processed += 1
                total_emails += 1
                continue

        total_threads_created += page_threads_created
        total_messages_created += page_messages_created
        total_attachments_captured += page_attachments_captured

        progress.append({
            "page": page_num,
            "emails_seen": len(emails),
            "new_emails": len(new_emails),
            "processed": page_processed,
            "threads_created": page_threads_created,
            "messages_created": page_messages_created,
            "attachments_captured": page_attachments_captured,
            "date_range": {"newest": page_newest, "oldest": page_oldest},
        })

        print(f"PAGE {page_num} done: seen={len(emails)} new={len(new_emails)} processed={page_processed} threads+={page_threads_created} messages+={page_messages_created}")

        if reached_watermark:
            break
        before_ts = page_oldest

    if newest_seen and newest_seen > watermark:
        save_watermark(newest_seen)

    final = {
        "status": "complete",
        "pages": page_num,
        "watermark_before": watermark,
        "watermark_after": newest_seen if (newest_seen and newest_seen > watermark) else watermark,
        "total_new_emails": total_emails,
        "threads_created": total_threads_created,
        "messages_created": total_messages_created,
        "attachments_captured": total_attachments_captured,
        "progress": progress,
    }
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    print("DELTA CAPTURE COMPLETE")
    print(json.dumps(final))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
