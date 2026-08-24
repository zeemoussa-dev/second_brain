"""CLI entry point: ensure one calendar event's Meeting note exists and
is topped up -- one-time meeting (its own folder, single file) or one
occurrence of a recurring series (series folder + concept note +
occurrences/<occurrence>.md), per the operator's own explicit structure
(2026-08-21): every meeting/series gets a real folder, a recurring
series' folder holds a real file PER OCCURRENCE, never one ever-growing
note. Also ensures a bare Person note + attendee link for every attendee,
and attempts a Thread link via link_meeting_to_thread.py.

Usage:
    python ingest_meeting.py --vault-path P --input-file F [--self-email E]

F is a JSON file (write it with the `write_file` tool before calling):
{
  "id": str, "subject": str, "start": str, "end": str, "location": str,
  "organizer": str, "attendees": [{"name","email","department",
  "job_title","company_name"}, ...], "conversation_id": str,
  "is_recurring": bool, "series_id": str, "teams_link": str, "dial_in": str
}
(the exact shape list_recent_meetings.py returns per event).

--self-email (optional, or the SECOND_BRAIN_SELF_EMAIL env var) excludes
the vault owner's own address from the attendee list -- they are never
captured as their own meeting's own attendee. Real, accessible config,
not a hardcoded literal (mirrors the same discipline
meeting_thread_link_config.py already applies to the thread-linking
thresholds).

Prints {"meeting_note_path", "series_created"/"created", "occurrence_created",
"attendees_linked", "thread_linked_to"}.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import link_meeting_to_thread
import vault_lib

_LINK_PERSON_CALLER = "link_person_to_meeting.link_person_to_meeting"
_LINK_OCCURRENCE_CALLER = "link_occurrence_to_series.link_occurrence_to_series"


def ingest_meeting(vault_path: Path, event: dict, self_email: str) -> dict:
    subject = event["subject"]
    start = event["start"]
    end = event.get("end") or ""
    location = event.get("location") or ""
    organizer = event.get("organizer") or ""
    teams_link = event.get("teams_link") or ""
    dial_in = event.get("dial_in") or ""
    conversation_id = event.get("conversation_id") or ""
    is_recurring = bool(event.get("is_recurring")) and bool(event.get("series_id"))
    attendees = [
        a for a in (event.get("attendees") or [])
        if (a.get("email") or "").strip().lower() != self_email.lower()
    ]

    result: dict = {"attendees_linked": 0}

    if is_recurring:
        series_id = event["series_id"]
        directory = vault_lib.resolve_meeting_directory(vault_path, series_id, is_recurring=True)
        if directory is None:
            directory = vault_lib.meeting_directory_for_new(vault_path, subject, start, True, series_id)
        concept_path = directory / f"{directory.name}.md"
        series_created = not concept_path.exists()
        if series_created:
            vault_lib.create_meeting_note_baseline(concept_path, subject, True, series_id, organizer, teams_link, dial_in)
        result["series_created"] = series_created

        occurrence_path = vault_lib.occurrence_note_path(directory, subject, start, event["id"])
        occurrence_created = not occurrence_path.exists()
        if occurrence_created:
            vault_lib.create_occurrence_note(
                occurrence_path, subject, event["id"], start, end, location, organizer, teams_link, dial_in,
            )
        result["occurrence_created"] = occurrence_created

        vault_lib.link_occurrence_to_series(concept_path, occurrence_path, start[:10], caller=_LINK_OCCURRENCE_CALLER)
        target_note = occurrence_path
        result["meeting_note_path"] = str(occurrence_path)
        result["series_concept_path"] = str(concept_path)
    else:
        # 2026-08-21 bug fix, caught live on this Skill's own first
        # idempotency rerun: going straight to meeting_directory_for_new
        # every call (no resolve-existing-first step) meant an ALREADY
        # captured one-time meeting's own deterministic path always
        # "collided" with itself on the very next rerun -- read as a
        # collision with a DIFFERENT meeting, appending a spurious hash
        # suffix and creating a full duplicate folder every single time
        # (17 real duplicates produced this way before the fix). Mirrors
        # the recurring branch's own already-correct two-step shape:
        # resolve by scanning existing notes' own calendar_event_id
        # first, only computing a fresh path when truly not found.
        directory = vault_lib.resolve_meeting_directory(vault_path, event["id"], is_recurring=False)
        if directory is None:
            directory = vault_lib.meeting_directory_for_new(vault_path, subject, start, False, event["id"])
        concept_path = directory / f"{directory.name}.md"
        created = not concept_path.exists()
        if created:
            vault_lib.create_meeting_note_baseline(concept_path, subject, False, event["id"], organizer, teams_link, dial_in)
        result["created"] = created
        target_note = concept_path
        result["meeting_note_path"] = str(concept_path)

    vault_lib.set_occurrence_logistics(target_note, start, end, location)

    attendee_emails: list[str] = []
    for attendee in attendees:
        email = attendee.get("email") or ""
        name = attendee.get("name") or email or "Unknown Attendee"
        person_result = vault_lib.ensure_bare_person_note(
            vault_path, name, email or None,
            department=attendee.get("department") or "",
            role=attendee.get("job_title") or "",
            company=attendee.get("company_name") or "",
        )
        if person_result is None:
            continue
        attendee_emails.append(email)
        stem = Path(person_result["note_path"]).stem
        if vault_lib.add_attendee_to_frontmatter(target_note, stem):
            result["attendees_linked"] += 1
        vault_lib.link_person_to_meeting(target_note, stem, caller=_LINK_PERSON_CALLER)

    thread_linked_to = link_meeting_to_thread.link_meeting_to_thread(
        vault_path, target_note, conversation_id, start, attendee_emails,
    )
    result["thread_linked_to"] = thread_linked_to

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--self-email", default=None)
    args = parser.parse_args()

    vault_path = Path(args.vault_path)
    self_email = args.self_email or os.environ.get("SECOND_BRAIN_SELF_EMAIL", "")
    event = json.loads(Path(args.input_file).read_text(encoding="utf-8-sig"))
    result = ingest_meeting(vault_path, event, self_email)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
