"""CLI entry point: `vault_manager.py`-based replacement for
`ingest_meeting.py` (Implementation/Plans/2026-08-25-vault-writer-
standardization.md's own real test case). Same job -- ensure one calendar
event's Meeting note exists and is topped up, plus bare Person notes +
attendee links + a Thread-link attempt -- but the note itself is resolved/
created/updated by `vault_manager.py`'s real `id`-based `find`/`create`/
`modify_section` instead of `vault_lib.py`'s own directory-name-is-identity
scheme.

Why this exists (real, live, documented bug -- see this Skill's OWN
`vault_lib.py`, `rename_meeting_series_if_needed`'s docstring): a series
first captured before folder-name resolution worked right gets stuck on a
raw Outlook id FOREVER, because identity there IS the folder name, and the
one attempted self-healing rename produced real, repeated duplicate
folders in live testing and was deliberately disabled. `vault_manager.py`'s
identity is frontmatter `id`, never the folder/file name -- there is
nothing to get stuck, because renaming (a title/display change) and
identity (an `id` lookup) are no longer the same operation.

Deliberately narrow: ONLY the Meeting-note resolution/creation/section-
write logic moves to `vault_manager.py`. Person-note creation/dedup,
attendee-linking, and Thread-linking are UNCHANGED, imported from this same
Skill's own `vault_lib.py`/`link_meeting_to_thread.py` -- not part of the
real, reported problem (multiple Meeting-naming schemes), no reason to
touch them.

TEST-PHASE ONLY (2026-08-25): writes under `Notes/Meetings/...`, a real,
separate location from the existing `Work/Meetings/...` tree -- so running
this against real calendar data cannot collide with or overwrite anything
already captured there. Once proven, this becomes the real
`ingest_meeting.py` and `Work/Meetings/` is deleted server-side (explicit
operator authorization), not before.

Usage: identical to ingest_meeting.py's own real contract --
    python ingest_meeting_v2.py --vault-path P --input-file F [--self-email E]
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import link_meeting_to_thread
import vault_lib
import vault_manager as vm

_LINK_PERSON_CALLER = "link_person_to_meeting.link_person_to_meeting"
_MEETING_TEMPLATE_ID = "meeting"
_SERIES_TEMPLATE_ID = "meeting-series"
_NOTE_NAME_ROOT = "Meetings"
_RECURRENCES_SUBFOLDER = "Recurrences"


def _logistics_fields(start: str, end: str, location: str, organizer: str, teams_link: str, dial_in: str) -> dict:
    """Real logistics, stored in FRONTMATTER (operator, 2026-08-25: "I
    need only the meeting link to be Stored in front Matter", not dumped
    as prose into the body) -- matches the real shape ingest_meeting.py's
    own vault_lib.py already used (start/end/location/organizer/
    teams_link/dial_in were always frontmatter fields there). Set once,
    at creation, never overwritten on a later top-up call -- these aren't
    expected to change; a real reschedule is a different real event id."""
    fields: dict = {"start": start, "end": end}
    if location:
        fields["location"] = location
    if organizer:
        fields["organizer"] = organizer
    if teams_link:
        fields["teams_link"] = teams_link
    if dial_in:
        fields["dial_in"] = dial_in
    return fields


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
    logistics = _logistics_fields(start, end, location, organizer, teams_link, dial_in)

    if is_recurring:
        series_id = event["series_id"]
        series_template = vm.load_template(vault_path, _SERIES_TEMPLATE_ID)
        series_path = vm.find_by_id(vault_path, series_id, note_name=_NOTE_NAME_ROOT)
        result["series_created"] = series_path is None
        if series_path is None:
            # `folder_date=start[:10]` -- operator, 2026-08-25: "Last
            # meeting Date so Sort will work" -- seeded with the REAL
            # first-captured occurrence's own date, never "today" (an
            # artifact of whenever this capture happens to run).
            created_series = vm.create(
                vault_path, series_template, note_name=_NOTE_NAME_ROOT, title=subject, note_id=series_id,
                frontmatter={**logistics, "calendar_series_id": series_id}, folder_date=start[:10],
            )
            series_path = Path(created_series["path"])
        else:
            # Every later capture bumps the series folder forward if THIS
            # occurrence is more recent than whatever the folder already
            # encodes -- a no-op otherwise (vm.bump_folder_date's own
            # contract), so re-ingesting old/out-of-order events never
            # moves it backwards.
            series_path = vm.bump_folder_date(vault_path, series_path, start[:10])

        occurrence_template = vm.load_template(vault_path, _MEETING_TEMPLATE_ID)
        # Operator, 2026-08-25: "Meetings --> Series Folder (Name of the
        # Series) --> Recurencies --> Meeting folder --> Meeting MD" --
        # TRUE nesting inside the series' own real, already-resolved
        # folder, derived from series_path itself (own_folder wraps it
        # with a real date prefix, e.g. "2026-08-25-Standup"). Real bug
        # in the earlier version, found from this same correction: a
        # note_name RE-BUILT from `subject` alone (without that date
        # prefix) landed as a SIBLING folder next to the series, not a
        # child of it -- silently wrong nesting, not just a rename ask.
        # .as_posix(), never str() -- Path.relative_to() returns
        # backslash-joined segments on Windows, which vault_manager's own
        # "/"-delimited note_name splitting would then treat as ONE
        # segment containing a literal backslash (itself then slugified
        # into a hyphen) rather than two real path segments. Real bug,
        # caught live: produced "Meetings-2026-08-25-Standup.../
        # Recurrences" (one bogus hyphenated segment + Recurrences)
        # instead of true "Meetings/2026-08-25-Standup.../Recurrences"
        # nesting.
        # vm._NOTES_ROOT, never a literal "Work"/"Notes" here -- this
        # exact mismatch (a hardcoded root drifting from vault_manager's
        # own real one) is what the 2026-08-26 Notes-vs-Work correction
        # was.
        series_folder_note_name = series_path.parent.relative_to(vault_path / vm._NOTES_ROOT).as_posix()
        occurrence_note_name = f"{series_folder_note_name}/{_RECURRENCES_SUBFOLDER}"
        # Real bug, found live 2026-08-27 (operator: "another meeting i
        # have not visible"): `event["id"]` (Outlook's own EntryID) is
        # NOT a reliable per-occurrence identifier for a real recurring
        # series -- confirmed live, a real event today and a real
        # occurrence captured back on 2026-07-16 (same series) came back
        # with the EXACT SAME EntryID from Outlook's own COM API.
        # `outlook_lib.py`'s own module docstring already documents this
        # exact finding ("EntryID/GlobalAppointmentID/ConversationID have
        # all been live-confirmed unreliable as per-occurrence
        # identifiers... in the source project's own history") and the
        # OLD vault_lib.py pipeline already worked around it by deriving
        # its own dedup key from subject+start -- this script's own
        # `vm.find_by_id(event["id"], ...)` silently reintroduced the
        # exact same bug by trusting Outlook's id directly, so EVERY
        # occurrence after the first-ever-captured one was silently
        # treated as "already captured" and never got its own note.
        # Fixed the same way: a synthetic, deterministic per-occurrence
        # key (`series_id` + the occurrence's own real `start`, which a
        # real recurring series can only have once) is the note's real
        # identity here, never the raw Outlook EntryID -- `event["id"]`
        # is still recorded in frontmatter (`calendar_event_id`) for
        # reference, just never used as the lookup/identity key.
        occurrence_key = f"{series_id}-{start}"
        occurrence_path = vm.find_by_id(vault_path, occurrence_key, note_name=occurrence_note_name)
        result["occurrence_created"] = occurrence_path is None
        if occurrence_path is None:
            # Real bug, found live 2026-08-25 processing the full history:
            # `folder_date` was only ever passed for the SERIES, never for
            # the occurrence -- every occurrence defaulted to TODAY's date
            # instead of its own real `start`. Ten real weekly occurrences
            # of the same series, all captured in one batch run, then all
            # collided on the identical "today"-dated folder name, and the
            # collision-retry counters piled up past the path-length
            # budget (which never anticipated retry suffixes being added
            # after its own truncation already ran).
            created_occurrence = vm.create(
                vault_path, occurrence_template, note_name=occurrence_note_name, title=subject, note_id=occurrence_key,
                frontmatter={**logistics, "calendar_event_id": event["id"]}, folder_date=start[:10],
            )
            occurrence_path = Path(created_occurrence["path"])

        wikilink = f"[[{occurrence_path.stem}]]"
        history = vm.get_section_content(series_path, "History")
        if wikilink not in history:
            lines = [line for line in history.splitlines() if line.strip()]
            lines.append(f"- {start[:10]}: {wikilink}")
            # Real bug, found live 2026-08-26 (full history rebuild): no
            # `note_name` here meant find_by_id fell back to scanning the
            # ENTIRE Work/ tree (every note in the vault, not just
            # Meetings/) -- slow, and it hit an inaccessible file under
            # old, unrelated Work/_archive/ content along the way. Scope
            # it to Meetings/, exactly like every other find_by_id call
            # in this file already does.
            vm.modify_section(
                vault_path, series_template, note_id=series_id, section="History", content="\n".join(lines),
                mode="replace", note_name=_NOTE_NAME_ROOT,
            )

        target_note = occurrence_path
        result["meeting_note_path"] = str(occurrence_path)
        result["series_concept_path"] = str(series_path)
    else:
        template = vm.load_template(vault_path, _MEETING_TEMPLATE_ID)
        note_path = vm.find_by_id(vault_path, event["id"], note_name=_NOTE_NAME_ROOT)
        result["created"] = note_path is None
        if note_path is None:
            # Real bug, found live 2026-08-27 (operator: "Now all Meetings
            # folder Showing the 2026-08-26"): this branch never passed
            # `folder_date`, so every ONE-TIME meeting's folder/filename got
            # dated with whatever day the capture script happened to run,
            # not the meeting's own real `start` date -- the exact same bug
            # already found and fixed for the recurring-series/occurrence
            # branches above (see their own comments), just never applied
            # here. A historical backfill run captures meetings spanning
            # weeks/months in one batch, so this silently mis-dated the
            # large majority of one-time meetings to the single day the
            # backfill ran.
            created = vm.create(
                vault_path, template, note_name=_NOTE_NAME_ROOT, title=subject, note_id=event["id"],
                frontmatter={**logistics, "calendar_event_id": event["id"]}, folder_date=start[:10],
            )
            note_path = Path(created["path"])
        target_note = note_path
        result["meeting_note_path"] = str(target_note)

    # Unchanged from ingest_meeting.py -- real, working Person-note /
    # attendee-link / Thread-link logic, not part of the naming-mess
    # problem this test is solving.
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
