"""The Cockpit shows the subject note's own Summary section.

Operator, 2026-09-24: "Thread Summary is not loading". It never loaded: the read
model hard-coded `summary: None` as an honest stub, while the
`summarize-and-tag-threads` Skill had been writing a real Summary into the note all
along. This reads that section; it never composes one."""
import os

import pytest

from app.business.logic import cockpit_view
from app.obsidian.notes import long_path

NOTE = """---
type: "Thread"
thread_name: "Data Platform walk-through"
---

## Summary

Set up a Core42 architecture walk-through with Masdar to agree the target state.

## Personal Notes

## Actions
"""


@pytest.fixture()
def note(tmp_path):
    path = tmp_path / "2026-09-17 Data Platform.md"
    path.write_text(NOTE, encoding="utf-8")
    return path


def test_the_notes_summary_section_is_what_the_cockpit_shows(note):
    summary = cockpit_view._note_summary({"path": str(note), "stem": note.stem})

    assert summary.startswith("Set up a Core42 architecture walk-through")
    assert "Personal Notes" not in summary


def test_an_empty_summary_section_reads_as_none_rather_than_blank(tmp_path):
    """A Meeting note carries the same section and nothing writes it yet, so the
    panel must say "no summary yet", not render an empty box."""
    path = tmp_path / "meeting.md"
    path.write_text("---\ntype: \"Meeting\"\n---\n\n## Summary\n\n## Actions\n", encoding="utf-8")

    assert cockpit_view._note_summary({"path": str(path), "stem": "meeting"}) is None


def test_a_note_without_the_section_reads_as_none(tmp_path):
    path = tmp_path / "bare.md"
    path.write_text("---\ntype: \"Thread\"\n---\n\njust a body\n", encoding="utf-8")

    assert cockpit_view._note_summary({"path": str(path), "stem": "bare"}) is None


def test_an_unreadable_note_is_reported_not_raised(tmp_path, caplog):
    """The Cockpit still opens when one note cannot be read."""
    missing = {"path": str(tmp_path / "gone.md"), "stem": "gone"}

    assert cockpit_view._note_summary(missing) is None
    assert "could not read the Summary section" in caplog.text


def test_a_path_past_the_windows_limit_is_still_read(tmp_path):
    """A recurring meeting's note nests deep enough to pass 260 characters, where a
    plain open() fails -- the exact trap that has bitten this vault before."""
    deep = tmp_path
    for _ in range(6):
        deep = deep / ("recurrence-folder-with-a-long-real-world-name-" + "x" * 30)
    path = deep / "note.md"
    assert len(str(path)) > 260
    # Creating it needs the same long-path treatment the reader uses.
    os.makedirs(long_path(deep), exist_ok=True)
    with open(long_path(path), "w", encoding="utf-8") as handle:
        handle.write(NOTE)

    summary = cockpit_view._note_summary({"path": str(path), "stem": "note"})

    assert summary.startswith("Set up a Core42 architecture walk-through")
