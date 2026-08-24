"""Single-process orchestrator for the full email-thread-capture loop
(2026-08-21). Provenance: an earlier cron run improvised this itself, via
`write_file`, to work around burning one LLM round-trip per script call
per email across a full-history pull (thousands of emails x 5 scripts
each) -- running the whole per-email loop as one background `terminal`
process instead turns that into O(1) LLM calls. Adopted here as the
canonical path (see SKILL.md's own "How to Run") after cleanup:

- VAULT_PATH/SCRIPTS_DIR no longer hardcoded to one machine's paths (the
  original had a real bug too: r"C:\\\\myWorx\\..." is a RAW string, so
  the doubled backslashes were literal characters, not escapes -- harmless
  in practice since Windows path parsing tolerates redundant separators,
  but not something to keep around).
- Step "external file links" (extract_file_links) is DISABLED -- it was a
  mechanical domain-match (any sharepoint.com/1drv.ms/etc. URL), not the
  real judgment call capture_file_link.py's own contract requires ("read
  the email body ... if unsure, skip it"). This produced real junk (a
  SharePoint LISTING page or access-request page captured as if it were a
  referenced file, e.g. "AllItems.aspx", "pendingreq.aspx"). Left in the
  code, disabled, rather than deleted -- may be worth a real LLM-judgment
  pass later, just not a mechanical one.
"""
from __future__ import annotations
import os
import sys
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

VAULT_PATH = os.environ.get("SECOND_BRAIN_VAULT_PATH", r"C:\myWorx\Moussa MD\Moussa Brain")
SCRIPTS_DIR = str(Path(__file__).resolve().parent)
LOCALAPPDATA = os.environ.get("LOCALAPPDATA") or os.path.expanduser(r"~\AppData\Local")
SCRATCH_DIR = os.path.join(LOCALAPPDATA, "Temp", "second_brain_capture_cli")
os.makedirs(SCRATCH_DIR, exist_ok=True)
SUMMARY_PATH = os.path.join(SCRATCH_DIR, "email_capture_summary.json")

PYTHON = sys.executable or "python"

# Set to True to re-enable the mechanical file-link heuristic -- see
# module docstring for why this is off by default.
CAPTURE_EXTERNAL_FILE_LINKS = False


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
    """Run a script in SCRIPTS_DIR and return (code, stdout, stderr)."""
    proc = subprocess.run([PYTHON] + args, cwd=SCRIPTS_DIR, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def parse_iso(ts: str) -> datetime:
    # Be forgiving: handle presence/absence of timezone
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        # Fallback: strip timezone
        return datetime.fromisoformat(ts.split("+")[0].split("-") if "+" in ts or "-" in ts else ts)


FILE_LINK_DOMAINS = [
    "sharepoint.com",
    "1drv.ms",
    "onedrive.live.com",
    "drive.google.com",
    "dropbox.com",
    "box.com",
    "wetransfer.com",
    "sharefile.com",
    "files.office.com",
    "my.sharepoint.com",
]


def extract_file_links(text: str, max_links: int = 3) -> list[tuple[str, str]]:
    if not text:
        return []
    urls = re.findall(r"https?://[^\s<>\)\"]+", text)
    out: list[tuple[str, str]] = []
    for u in urls:
        try:
            parsed = urlparse(u)
            domain = parsed.netloc.lower()
            if not any(d in domain for d in FILE_LINK_DOMAINS):
                continue
            label = ""
            # Try filename-like last path segment
            segments = [s for s in parsed.path.split("/") if s]
            if segments:
                label = unquote(segments[-1])
            if not label:
                # Try common query params
                q = parse_qs(parsed.query)
                for key in ("filename", "file", "name", "doc", "id"):
                    if key in q and q[key]:
                        label = unquote(q[key][0])
                        break
            if not label:
                label = domain
            # Keep it short/readable
            if len(label) > 80:
                label = label[:77] + "..."
            out.append((label, u))
            if len(out) >= max_links:
                break
        except Exception:
            continue
    return out


def main() -> int:
    ok, msg = ensure_pywin32()
    if not ok:
        print(f"FATAL: pywin32 unavailable: {msg}")
        return 3

    total_emails = 0
    total_threads_created = 0
    total_messages_created = 0
    total_attachments_captured = 0

    page_num = 0
    before_ts: str | None = None
    oldest_seen: str | None = None
    newest_seen: str | None = None

    progress: list[dict] = []

    while True:
        page_num += 1
        args = ["list_recent_emails.py", "--limit", "50"]
        if before_ts:
            args += ["--before", before_ts]
        code, out, err = run_script(args)
        if code != 0:
            # Likely Outlook not running/signed-in
            err_msg = err.strip() or out.strip()
            print(f"PAGE {page_num}: list_recent_emails failed (code {code}): {err_msg}")
            # Stop the whole pull on Outlook unavailability
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
            # Done
            final = {
                "status": "complete",
                "pages": page_num - 1,
                "total_emails": total_emails,
                "threads_created": total_threads_created,
                "messages_created": total_messages_created,
                "attachments_captured": total_attachments_captured,
                "date_range": {
                    "newest": newest_seen,
                    "oldest": oldest_seen,
                },
                "progress": progress,
            }
            with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
                json.dump(final, f, ensure_ascii=False, indent=2)
            print("CAPTURE COMPLETE")
            print(json.dumps(final))
            return 0

        # Determine page oldest/newest
        rec_times = [e.get("received") for e in emails if e.get("received")]
        page_oldest = min(rec_times) if rec_times else None
        page_newest = max(rec_times) if rec_times else None
        if newest_seen is None and page_newest:
            newest_seen = page_newest
        if page_oldest:
            oldest_seen = page_oldest

        page_processed = 0
        page_threads_created = 0
        page_messages_created = 0
        page_attachments_captured = 0

        for e in emails:
            try:
                conversation_id = e.get("conversation_id")
                message_id = e.get("id")
                received = e.get("received")
                sender_name = e.get("sender_name")
                sender_email = e.get("sender_email")
                subject = e.get("subject")
                body = e.get("body") or ""
                recipients = e.get("recipients") or []

                # 2a. ingest_email
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
                else:
                    # log and continue
                    pass

                # 2b. link sender person
                if sender_email:
                    _ = run_script([
                        "link_person_to_thread.py",
                        "--vault-path", VAULT_PATH,
                        "--conversation-id", conversation_id or "",
                        "--sender-name", sender_name or "",
                        "--sender-email", sender_email,
                    ])

                # 2c. rename thread
                _ = run_script(["rename_thread.py", "--vault-path", VAULT_PATH, "--conversation-id", conversation_id or ""])

                # 2d. attachments
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

                # 2e. external file links -- see module docstring for why
                # this is off by default (mechanical domain-match, not a
                # real judgment call).
                if CAPTURE_EXTERNAL_FILE_LINKS:
                    for label, url in extract_file_links(body):
                        if not message_path:
                            break
                        _ = run_script([
                            "capture_file_link.py",
                            "--vault-path", VAULT_PATH,
                            "--conversation-id", conversation_id or "",
                            "--message-path", message_path,
                            "--received", received or "",
                            "--label", label,
                            "--url", url,
                        ])

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

        # Progress record for this page
        progress.append({
            "page": page_num,
            "emails": len(emails),
            "processed": page_processed,
            "threads_created": page_threads_created,
            "messages_created": page_messages_created,
            "attachments_captured": page_attachments_captured,
            "date_range": {"newest": page_newest, "oldest": page_oldest},
        })

        print(f"PAGE {page_num} done: emails={len(emails)} processed={page_processed} threads+={page_threads_created} messages+={page_messages_created} attachments+={page_attachments_captured} range=[{page_oldest} .. {page_newest}]")
        # Prepare next page
        before_ts = page_oldest


if __name__ == "__main__":
    raise SystemExit(main())
