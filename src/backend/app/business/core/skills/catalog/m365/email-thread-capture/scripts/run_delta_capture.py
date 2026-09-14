"""Single-process orchestrator for the RECURRING, incremental email
capture loop (2026-08-22) -- the delta sibling of run_full_capture.py
(which stays as-is: the proven, one-time, full-history tool). Same
single-`terminal`-call, O(1)-LLM-calls design (see that script's own
module docstring for why), same per-email steps (ingest, link sender,
rename thread, attachments) -- the difference is which mail it walks.

OLDEST FIRST, SAVING AS IT GOES (2026-09-11). It pages FORWARD from its own
persisted watermark -- the `received` time of the last email it captured --
and moves the watermark after every email it writes. The first version paged
backward from "now" and saved the watermark once, at the very end. A backlog
bigger than one run could clear never finished: Hermes killed the run at its
3600s limit, nothing was saved, and the next run started again from the newest
email and got exactly as far. The 18:04 run on 2026-09-11 did that with 2.5
days of mail behind it, and from then on the delta would never have caught up.

So now:
  * a run that is cut off keeps everything it captured, and the next run
    continues from there;
  * it stops itself at --max-minutes (default 50), inside Hermes' hour, so a
    long catch-up reads as progress rather than as a killed, failed run;
  * an email already in the vault -- captured by the backfill, or by a run
    that stopped part-way -- costs a lookup, not four scripts. Its attachments
    still go through capture, which writes only what is missing.

The watermark still never passes an email that was not written: the first
failure freezes it for the rest of the run, and the next run retries from
there (2026-09-04: 54 emails were lost to a watermark that advanced past
failures). The watermark lives in the App Database Folder's
`email_capture_state.json`; missing state seeds a conservative 2-day
lookback rather than a full-history redo or blindly trusting "now".
"""
from __future__ import annotations
import argparse
import os
import sys
import json
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import vault_manager

VAULT_PATH = os.environ.get("SECOND_BRAIN_VAULT_PATH", "")
SCRIPTS_DIR = str(Path(__file__).resolve().parent)

# Fail loudly rather than operate on the wrong folder. This used to default to
# an absolute path that was deleted when the vault moved (2026-09-03), so an
# unset variable meant silently reading and writing a folder that no longer
# existed -- the same class of silent failure that cost 54 emails on
# 2026-09-04. The setup wizard writes SECOND_BRAIN_VAULT_PATH into Hermes' own
# .env, so this should never be unset on a properly provisioned install.
def _require_vault_path() -> str:
    if not VAULT_PATH.strip():
        raise SystemExit(
            "SECOND_BRAIN_VAULT_PATH is not set. Set it in Hermes' own .env "
            "(the Second Brain setup wizard writes it), or pass the vault "
            "path explicitly."
        )
    return VAULT_PATH

LOCALAPPDATA = os.environ.get("LOCALAPPDATA") or os.path.expanduser(r"~\AppData\Local")
SCRATCH_DIR = os.path.join(LOCALAPPDATA, "Temp", "second_brain_capture_cli")
os.makedirs(SCRATCH_DIR, exist_ok=True)
SUMMARY_PATH = os.path.join(SCRATCH_DIR, "email_delta_capture_summary.json")

# Kept only to find and migrate a pre-2026-09-04 state file; the live
# location is vault_manager.data_root() (see _state_path below).
_LEGACY_STATE_DIR = ".second-brain"
STATE_FILE = "email_capture_state.json"
BOOTSTRAP_LOOKBACK_DAYS = 2

PAGE_SIZE = 50
# Inside Hermes' 3600s script limit, with room for the page in flight.
DEFAULT_MAX_MINUTES = 50

PYTHON = sys.executable or "python"

_clock = time.monotonic


def run_script(args: list[str]) -> tuple[int, str, str]:
    # encoding="utf-8" explicit on BOTH sides of this subprocess boundary
    # (list_recent_emails.py's own sys.stdout.reconfigure, 2026-08-24) --
    # `text=True` alone decodes using the OS locale's preferred encoding
    # (cp1252 on this machine, not UTF-8), which would still choke on a
    # real Unicode character in an email subject/body even after the
    # child side was fixed to WRITE utf-8 bytes correctly.
    proc = subprocess.run([PYTHON] + args, cwd=SCRIPTS_DIR, capture_output=True, text=True, encoding="utf-8")
    return proc.returncode, proc.stdout, proc.stderr


def _legacy_state_path() -> Path:
    return Path(VAULT_PATH) / _LEGACY_STATE_DIR / STATE_FILE


def _state_path() -> Path:
    """The watermark now lives under the App Database Folder with every other
    piece of state, instead of in its own island inside the vault.

    Migrates a legacy <vault>/.second-brain/ file on first sight, and the
    legacy file WINS any collision. That direction is deliberate and matters:
    the app's own retired native capture left a stale copy of this same
    filename in the data folder (watermark 2026-09-03, last written by code
    that no longer runs), while the legacy path holds what THIS skill actually
    read and wrote. Preferring the data-folder copy would silently skip every
    email between the two watermarks."""
    live = vault_manager.data_root(Path(VAULT_PATH)) / STATE_FILE
    legacy = _legacy_state_path()
    if legacy.is_file():
        live.parent.mkdir(parents=True, exist_ok=True)
        if live.is_file():
            live.replace(live.with_suffix(live.suffix + ".superseded"))
        legacy.replace(live)
        # Leave the folder itself if anything else is in it; an empty legacy
        # island is just confusing data, so it goes.
        try:
            legacy.parent.rmdir()
        except OSError:
            pass
    return live


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


# ── paging forward ───────────────────────────────────────────────────────

def trim_page(emails: list[dict], limit: int) -> tuple[list[dict], list[dict], bool]:
    """(emails to capture now, oldest first; emails held back; last page?).

    A FULL page holds back its newest second. The next page asks for mail
    strictly newer than the last email captured, so two emails received in the
    same second -- a message and its Sent copy, a reply and a receipt -- must
    never be split across a page boundary, or the second would be skipped.
    Held back, they come first on the next page. A page whose every email
    shares one second cannot hold any back and is captured whole."""
    ordered = sorted(emails, key=lambda email: email.get("received") or "")
    if len(emails) < limit:
        return ordered, [], True
    newest = ordered[-1].get("received") or ""
    kept = [email for email in ordered if (email.get("received") or "") != newest]
    if not kept:
        return ordered, [], False
    return kept, [email for email in ordered if (email.get("received") or "") == newest], False


def advance_points(kept: list[dict], last_is_safe: bool) -> list[bool]:
    """Whether the watermark may move to each email's `received` once it is
    written. Only when the NEXT email is strictly newer: a run stopped between
    two emails of the same second must not record the second one as captured.
    The last email is safe when nothing else can share its second -- the
    listing was exhausted, or a newer second was held back. An email with no
    timestamp never moves it: there is no way to place it in time."""
    points: list[bool] = []
    for index, email in enumerate(kept):
        this = email.get("received") or ""
        following = kept[index + 1].get("received") or "" if index + 1 < len(kept) else None
        if not this:
            points.append(False)
        elif following is None:
            points.append(last_is_safe)
        else:
            points.append(following > this)
    return points


def discard_downloads(emails: list[dict]) -> None:
    """Deletes the attachment files the listing saved for emails this run will
    not capture. capture_attachments.py deletes the ones it reads; these would
    otherwise sit in %TEMP% forever, and are downloaded again next run."""
    for email in emails:
        for attachment in email.get("attachments") or []:
            if attachment.get("temp_path"):
                try:
                    os.remove(attachment["temp_path"])
                except OSError:
                    pass


# ── already in the vault ─────────────────────────────────────────────────

def captured_threads(vault_path: Path) -> dict[str, Path]:
    """Conversation id -> Thread folder, built ONCE per run. ingest_email.py's
    own lookup scans every Thread note when a conversation is not in the
    index -- tolerable once, ruinous for every email of a catch-up."""
    threads: dict[str, Path] = {}
    root = vault_path / "Work" / "Threads"
    if not root.is_dir():
        return threads
    for thread_dir in root.iterdir():
        note = thread_dir / f"{thread_dir.name}.md"
        if not os.path.isfile(vault_manager.long_path(note)):
            continue
        frontmatter, _ = vault_manager.read_note(note)
        for key in ("id", "conversation_id"):
            value = str(frontmatter.get(key) or "").strip()
            if value:
                threads.setdefault(value, thread_dir)
    return threads


def already_captured(threads: dict[str, Path], conversation_id: str, message_id: str) -> Path | None:
    """The message note already carrying this email, or None. Matched on the
    same (conversation_id, message_id) natural key ingest_email.py writes."""
    thread_dir = threads.get(conversation_id or "")
    if thread_dir is None or not message_id:
        return None
    messages = vault_manager.long_path(thread_dir / "messages")
    if not os.path.isdir(messages):
        return None
    for entry in os.scandir(messages):
        if not entry.name.endswith(".md"):
            continue
        frontmatter, _ = vault_manager.read_note(Path(entry.path))
        if (str(frontmatter.get("message_id", "")) == message_id
                and str(frontmatter.get("conversation_id", "")) == conversation_id):
            return thread_dir / "messages" / entry.name
    return None


# ── one email ────────────────────────────────────────────────────────────

def _capture_attachments(email: dict, message_path: str, counts: dict) -> None:
    payload = {
        "conversation_id": email.get("conversation_id"),
        "message_id": email.get("id"),
        "received": email.get("received"),
        "message_path": message_path,
        "attachments": email.get("attachments") or [],
    }
    cap_path = os.path.join(SCRATCH_DIR, f"attach_{email.get('id')}.json")
    with open(cap_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    code, out, err = run_script(["capture_attachments.py", "--vault-path", VAULT_PATH, "--input-file", cap_path])
    if code == 0:
        try:
            counts["attachments_captured"] += len(json.loads(out.strip() or "{}").get("captured", []))
        except Exception:
            pass


def capture_one(email: dict, threads: dict[str, Path], counts: dict, failures: list[dict]) -> bool:
    """Ingest, link the sender, name the Thread, capture attachments. True when
    the email is in the vault afterwards."""
    conversation_id = email.get("conversation_id")
    message_id = email.get("id")
    received = email.get("received")
    subject = email.get("subject")

    existing = already_captured(threads, conversation_id or "", message_id or "")
    if existing is not None:
        counts["already_captured"] += 1
        if email.get("attachments"):
            _capture_attachments(email, str(existing), counts)
        return True

    try:
        sender_name = email.get("sender_name")
        sender_email = email.get("sender_email")
        ingest_payload = {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "received": received,
            "sender_name": sender_name,
            "sender_email": sender_email,
            "subject": subject,
            "body": email.get("body") or "",
            "recipients": email.get("recipients") or [],
            "direction": email.get("direction") or "",
            "sender_department": email.get("sender_department") or "",
            "sender_job_title": email.get("sender_job_title") or "",
            "sender_company_name": email.get("sender_company_name") or "",
        }
        ingest_path = os.path.join(SCRATCH_DIR, f"ingest_{message_id}.json")
        with open(ingest_path, "w", encoding="utf-8") as f:
            json.dump(ingest_payload, f, ensure_ascii=False)
        code, out, err = run_script(["ingest_email.py", "--vault-path", VAULT_PATH, "--input-file", ingest_path])
        written = False
        message_path = None
        # A failed ingest MUST be recorded, not swallowed. Until 2026-09-04 a
        # non-zero exit here was counted as processed and the watermark moved
        # past it -- how 54 real emails were consumed and permanently skipped
        # without a single error surfacing anywhere.
        if code != 0:
            detail = (err or out or "").strip().splitlines()
            failures.append({
                "message_id": message_id, "received": received, "subject": subject,
                "error": detail[-1][:300] if detail else f"ingest_email.py exited {code}",
            })
        else:
            try:
                result = json.loads(out.strip() or "{}")
                if result.get("thread_created"):
                    counts["threads_created"] += 1
                if result.get("message_created"):
                    counts["messages_created"] += 1
                if result.get("skipped_as_noise"):
                    counts["skipped_as_noise"] += 1
                message_path = result.get("message_path")
                written = True
            except Exception as parse_error:
                # An unparsable reply means we cannot tell what was written --
                # treat it as a failure, never as a success.
                failures.append({
                    "message_id": message_id, "received": received, "subject": subject,
                    "error": f"unparsable ingest_email.py output: {parse_error}",
                })

        if sender_email:
            run_script([
                "link_person_to_thread.py",
                "--vault-path", VAULT_PATH,
                "--conversation-id", conversation_id or "",
                "--sender-name", sender_name or "",
                "--sender-email", sender_email,
            ])
        run_script(["rename_thread.py", "--vault-path", VAULT_PATH, "--conversation-id", conversation_id or ""])
        if email.get("attachments") and message_path:
            _capture_attachments(email, message_path, counts)
        return written
    except Exception as ex:
        print(f"email {message_id!r} failed: {ex}")
        failures.append({"message_id": message_id, "received": received, "subject": subject,
                         "error": str(ex)[:300]})
        return False


def _stop(summary: dict) -> int:
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture mail newer than the watermark, oldest first.")
    parser.add_argument("--max-minutes", type=float, default=DEFAULT_MAX_MINUTES,
                        help="Stop cleanly after this long; the next run continues from the watermark.")
    args = parser.parse_args(argv)
    _require_vault_path()
    # No pywin32 check (removed 2026-09-11). The delta reads mail through
    # Graph and never touches COM; the check tried `pip install pywin32` on
    # every run, which Hermes' uv-managed Python refuses, and its note landed
    # in the hourly output. list_recent_emails.py imports graph_lib, not
    # outlook_lib.

    deadline = _clock() + args.max_minutes * 60
    watermark_before = watermark = load_watermark()
    cursor = watermark
    threads = captured_threads(Path(VAULT_PATH))
    counts = {"threads_created": 0, "messages_created": 0, "attachments_captured": 0,
              "skipped_as_noise": 0, "already_captured": 0}
    failures: list[dict] = []
    total_emails = 0
    frozen = False
    stopped_at_time_limit = False
    progress: list[dict] = []
    page_num = 0

    while True:
        if _clock() >= deadline:
            stopped_at_time_limit = True
            break
        page_num += 1
        code, out, err = run_script(["list_recent_emails.py", "--limit", str(PAGE_SIZE),
                                     "--since", cursor, "--oldest-first"])
        if code != 0:
            err_msg = err.strip() or out.strip()
            print(f"PAGE {page_num}: list_recent_emails failed (code {code}): {err_msg}")
            return _stop({"status": "blocked", "reason": err_msg or "list_recent_emails failed",
                          "page": page_num, "processed_emails": total_emails,
                          "watermark_before": watermark_before, "watermark_after": watermark})
        try:
            emails = json.loads(out or "[]")
        except json.JSONDecodeError as e:
            print(f"PAGE {page_num}: JSON decode error: {e}")
            return _stop({"status": "error", "reason": f"JSON decode error on page {page_num}",
                          "raw_first_200": (out or "")[:200],
                          "watermark_before": watermark_before, "watermark_after": watermark})

        kept, held_back, is_final = trim_page(emails, PAGE_SIZE)
        discard_downloads(held_back)
        if not kept:
            break
        points = advance_points(kept, is_final or bool(held_back))
        captured_on_page = 0
        for index, email in enumerate(kept):
            if _clock() >= deadline:
                stopped_at_time_limit = True
                discard_downloads(kept[index:])
                break
            written = capture_one(email, threads, counts, failures)
            total_emails += 1
            captured_on_page += 1
            if not written:
                frozen = True       # nothing after a failure may be passed
            received = email.get("received") or ""
            if written and not frozen and points[index] and received > watermark:
                save_watermark(received)
                watermark = received

        progress.append({"page": page_num, "emails_seen": len(emails), "processed": captured_on_page,
                         "date_range": {"oldest": kept[0].get("received"), "newest": kept[-1].get("received")}})
        print(f"PAGE {page_num} done: seen={len(emails)} processed={captured_on_page} "
              f"watermark={watermark}")
        if stopped_at_time_limit or is_final:
            break
        next_cursor = kept[-1].get("received") or ""
        if not next_cursor or next_cursor <= cursor:
            break           # cannot advance the listing; never loop on one page
        cursor = next_cursor

    if failures:
        status = "complete_with_errors"
    elif stopped_at_time_limit:
        status = "time_limit_reached"
    else:
        status = "complete"
    final = {
        # A distinct status so a run that dropped mail can never again read as
        # a clean "complete" in the cron report.
        "status": status,
        "more_to_capture": stopped_at_time_limit,
        "pages": page_num,
        "watermark_before": watermark_before,
        "watermark_after": watermark,
        "failed_emails": len(failures),
        # Capped: the point is to make the failure visible and diagnosable in
        # the cron output, not to dump a thousand identical tracebacks.
        "failures": failures[:10],
        "total_new_emails": total_emails,
        **counts,
        "progress": progress,
    }
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    print("DELTA CAPTURE COMPLETE")
    print(json.dumps(final))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
