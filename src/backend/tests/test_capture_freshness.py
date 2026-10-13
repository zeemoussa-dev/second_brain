"""BUG-085 -- email capture failed for four days while every status said `ok`.

The Graph token was gone, the script exited 2 on its first page, and the
agent-mediated cron job recorded a successful run anyway. What was missing was
not another job status but the honest question: when did a note last arrive.

Read from the vault on purpose -- a pipeline that lies, a Skill that cannot
authenticate and a Hermes that never fired all produce the same answer here.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.business.core.vault import vault_manager as module
from app.business.core.vault.vault_manager import VaultManager
from app.business.logic import capture_freshness, system_health
from app.config import settings

NOW = datetime.now(timezone.utc)


def write(path, note_type, field, stamp):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'---\ntype: "{note_type}"\n{field}: "{stamp}"\n---\n\nbody\n', encoding="utf-8")
    return path


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "vault_path", tmp_path)

    def build(notes):
        paths = [write(tmp_path / relative, note_type, field, stamp)
                 for relative, note_type, field, stamp in notes]
        monkeypatch.setattr(module.vault_writer, "list_all_note_paths", lambda: paths)
        VaultManager().rebuild_index()
        return paths

    return build


def row(rows, capture_id):
    return next(r for r in rows if r["id"] == capture_id)


def test_a_capture_that_stopped_days_ago_reads_stale(vault):
    """The real shape: the newest captured email is four days old while every
    service is up and every job says `ok`."""
    vault([
        ("Work/Threads/T/messages/old.md", "RawMessage", "received",
         (NOW - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S.%f+00:00")),
    ])

    emails = row(capture_freshness.get_capture_freshness(), "emails")

    assert emails["state"] == "stale"
    assert 95 < emails["age_hours"] < 97


def test_a_capture_that_brought_something_in_today_reads_fresh(vault):
    vault([
        ("Work/Threads/T/messages/new.md", "RawMessage", "received",
         (NOW - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S.%f+00:00")),
    ])

    assert row(capture_freshness.get_capture_freshness(), "emails")["state"] == "fresh"


def test_a_meeting_scheduled_for_next_week_does_not_mask_a_stall(vault):
    """A diary runs ahead. If the newest future occurrence counted, a capture
    that stopped a month ago would read fresh all month."""
    vault([
        ("Work/Meetings/old/old.md", "Meeting", "start", (NOW - timedelta(days=30)).isoformat()),
        ("Work/Meetings/future/future.md", "Meeting", "start", (NOW + timedelta(days=7)).isoformat()),
    ])

    meetings = row(capture_freshness.get_capture_freshness(), "meetings")

    assert meetings["state"] == "stale"
    assert meetings["age_hours"] > 700


def test_a_vault_with_no_notes_of_that_kind_is_not_a_failure(vault):
    """A fresh install has captured nothing yet, which is not the same as a
    capture that stopped."""
    vault([("Work/Notes/n.md", "Note", "created", NOW.isoformat())])

    emails = row(capture_freshness.get_capture_freshness(), "emails")

    assert emails["state"] == "nothing"
    assert emails["last_captured_at"] is None


def test_the_capture_stamp_format_the_pipeline_writes_is_understood(vault):
    """Capture writes `2026-10-09 17:11:47.410000+00:00` -- a space, not a `T`.
    A stamp this reader cannot parse would read as "never captured", which is the
    false alarm that gets a check ignored."""
    stamp = (NOW - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S.%f+00:00")
    assert capture_freshness._parsed(stamp) is not None
    assert capture_freshness._parsed("2026-10-09T17:11:47+04:00") is not None
    assert capture_freshness._parsed("not a date") is None
    assert capture_freshness._parsed("") is None


def test_system_health_carries_it_so_a_screen_can_show_it(vault):
    vault([
        ("Work/Threads/T/messages/new.md", "RawMessage", "received",
         (NOW - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S.%f+00:00")),
    ])

    health = system_health.get_system_health()

    assert [c["id"] for c in health["captures"]] == ["emails", "meetings"]
    assert row(health["captures"], "emails")["state"] == "fresh"
