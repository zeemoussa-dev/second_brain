"""The Graph calendar read must produce the record ingest_meeting.py consumes.

Written after a real failure: `_attendee_records` emitted `address` where
outlook_lib emitted `email`, so `ingest_meeting`'s own
`a.get("email")` filter dropped every attendee. 55 meetings were captured with
zero people linked, no error, no warning -- the exact shape of failure this
codebase keeps paying for. So these tests assert the KEYS a consumer reads, not
just that a record comes back.

No network: the Graph payloads are fixtures.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture()
def lib(monkeypatch):
    """graph_calendar_lib imports the email Skill's graph_lib for auth; stub it
    so these run with no token and no network."""
    import types
    stub = types.ModuleType("graph_lib")
    stub.GraphUnavailable = type("GraphUnavailable", (Exception,), {})
    stub._access_token = lambda: "test-token"
    stub._urlopen_retrying = lambda request: {"value": []}
    sys.modules.setdefault("graph_lib", stub)
    import graph_calendar_lib
    return graph_calendar_lib


EVENT = {
    "id": "evt-1",
    "subject": "G42 x MSFT | Monthly ROB",
    "start": {"dateTime": "2026-09-23T09:00:00.0000000", "timeZone": "UTC"},
    "end": {"dateTime": "2026-09-23T10:00:00.0000000", "timeZone": "UTC"},
    "location": {"displayName": "Microsoft Teams Meeting"},
    "organizer": {"emailAddress": {"name": "Sophie G", "address": "sophie@microsoft.com"}},
    "attendees": [
        {"type": "required", "emailAddress": {"name": "Sophie G", "address": "sophie@microsoft.com"}},
        {"type": "required", "emailAddress": {"name": "Real Person", "address": "person@core42.ai"}},
        {"type": "resource", "emailAddress": {"name": "Room 5", "address": "room5@core42.ai"}},
    ],
    "type": "occurrence",
    "seriesMasterId": "series-1",
    "onlineMeeting": {"joinUrl": "https://teams.microsoft.com/l/meetup-join/x"},
    "body": {"content": "Join by phone +442045266162"},
}


def test_attendee_key_is_email_because_that_is_what_ingest_reads(lib):
    """The regression. ingest_meeting.py filters on `a.get("email")`; an
    `address` key is silently dropped and every attendee disappears."""
    records = lib._attendee_records(EVENT, "sophie@microsoft.com")
    assert records, "attendees must survive"
    for record in records:
        assert "email" in record, "ingest_meeting reads `email`, not `address`"
        assert "address" not in record, (
            "an `address` key is the bug this test exists for -- it passes "
            "through the filter as empty and links nobody"
        )


def test_the_full_attendee_record_matches_what_outlook_lib_emitted(lib):
    records = lib._attendee_records(EVENT, "sophie@microsoft.com")
    assert set(records[0]) == {"name", "email", "department", "job_title", "company_name"}


def test_the_organizer_is_not_an_attendee(lib):
    """They are recorded separately; including them double-counts and creates a
    Person link for the person who called the meeting."""
    records = lib._attendee_records(EVENT, "sophie@microsoft.com")
    assert all(r["email"] != "sophie@microsoft.com" for r in records)


def test_a_room_is_not_a_person(lib):
    """A booked meeting room is a resource. Without this it becomes a Person
    note, which pollutes People with furniture."""
    records = lib._attendee_records(EVENT, "sophie@microsoft.com")
    assert all("room5" not in r["email"] for r in records)


def test_start_keeps_the_com_timestamp_format(lib):
    """Half the dedup key downstream. A different FORMAT does not error -- it
    silently produces a second copy of a meeting already captured."""
    import re
    stamp = lib._to_com_stamp("2026-09-23T09:00:00.0000000")
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\+00:00$", stamp), stamp


def test_an_unparseable_time_returns_empty_not_a_guess(lib):
    """A guessed timestamp would become a different dedup key and duplicate the
    meeting; empty is detectable, wrong is not."""
    assert lib._to_com_stamp("not a date") == ""
    assert lib._to_com_stamp("") == ""


def test_teams_link_prefers_the_structural_field_over_the_body(lib):
    assert lib._teams_link(EVENT, "") == "https://teams.microsoft.com/l/meetup-join/x"


def test_teams_link_falls_back_to_the_body(lib):
    """A meeting created outside Teams' integration carries the URL only in the
    body."""
    body = 'Join here https://teams.microsoft.com/l/meetup-join/fallback now'
    assert lib._teams_link({}, body) == "https://teams.microsoft.com/l/meetup-join/fallback"
