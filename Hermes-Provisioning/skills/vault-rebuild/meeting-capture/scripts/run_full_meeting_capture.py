"""Single-process orchestrator for the full meeting-capture loop
(2026-08-21) -- mirrors email-thread-capture's own run_full_capture.py:
one background `terminal` process runs the whole per-event loop directly,
instead of burning one LLM round-trip per script call per event.

Unlike email capture, the calendar fetch is a single bounded window
(days_back/days_ahead), not a paginated full-history pull -- one
list_recent_meetings.py call covers the whole run, no cursor loop needed.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

VAULT_PATH = os.environ.get("SECOND_BRAIN_VAULT_PATH", r"C:\myWorx\Moussa MD\Moussa Brain")
SELF_EMAIL = os.environ.get("SECOND_BRAIN_SELF_EMAIL", "")
SCRIPTS_DIR = str(Path(__file__).resolve().parent)
LOCALAPPDATA = os.environ.get("LOCALAPPDATA") or os.path.expanduser(r"~\AppData\Local")
SCRATCH_DIR = os.path.join(LOCALAPPDATA, "Temp", "second_brain_meeting_capture_cli")
os.makedirs(SCRATCH_DIR, exist_ok=True)
SUMMARY_PATH = os.path.join(SCRATCH_DIR, "meeting_capture_summary.json")

PYTHON = sys.executable or "python"


def run_script(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run([PYTHON] + args, cwd=SCRIPTS_DIR, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def main() -> int:
    days_back = int(os.environ.get("SECOND_BRAIN_MEETING_DAYS_BACK", "7"))
    days_ahead = int(os.environ.get("SECOND_BRAIN_MEETING_DAYS_AHEAD", "14"))

    code, out, err = run_script([
        "list_recent_meetings.py", "--days-back", str(days_back), "--days-ahead", str(days_ahead), "--limit", "200",
    ])
    if code != 0:
        err_msg = err.strip() or out.strip()
        print(f"list_recent_meetings failed (code {code}): {err_msg}")
        summary = {"status": "blocked", "reason": err_msg or "list_recent_meetings failed"}
        with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        return 2

    try:
        events = json.loads(out or "[]")
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        summary = {"status": "error", "reason": "JSON decode error", "raw_first_200": (out or "")[:200]}
        with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        return 2

    total_processed = 0
    total_series_created = 0
    total_one_time_created = 0
    total_occurrences_created = 0
    total_attendees_linked = 0
    total_threads_linked = 0
    errors: list[str] = []

    for event in events:
        try:
            ingest_path = os.path.join(SCRATCH_DIR, f"ingest_{event['id']}.json")
            with open(ingest_path, "w", encoding="utf-8") as f:
                json.dump(event, f, ensure_ascii=False)
            args = ["ingest_meeting.py", "--vault-path", VAULT_PATH, "--input-file", ingest_path]
            if SELF_EMAIL:
                args += ["--self-email", SELF_EMAIL]
            code, out, err = run_script(args)
            if code != 0:
                errors.append(f"{event.get('subject')!r}: {err.strip()[:300]}")
                total_processed += 1
                continue
            result = json.loads(out.strip() or "{}")
            if result.get("series_created"):
                total_series_created += 1
            if result.get("created"):
                total_one_time_created += 1
            if result.get("occurrence_created"):
                total_occurrences_created += 1
            total_attendees_linked += result.get("attendees_linked", 0)
            if result.get("thread_linked_to"):
                total_threads_linked += 1
            total_processed += 1
        except Exception as ex:
            errors.append(f"{event.get('subject')!r}: {ex}")
            total_processed += 1
            continue

    final = {
        "status": "complete",
        "events_in_window": len(events),
        "processed": total_processed,
        "series_created": total_series_created,
        "one_time_meetings_created": total_one_time_created,
        "occurrences_created": total_occurrences_created,
        "attendees_linked": total_attendees_linked,
        "threads_linked": total_threads_linked,
        "errors": errors,
    }
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    print("MEETING CAPTURE COMPLETE")
    print(json.dumps(final))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
