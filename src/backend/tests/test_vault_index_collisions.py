"""BUG-076 -- the index used to keep one note per file name, so a note could hide another.

Obsidian allows the same name in different folders. A meeting and its own invitation
email are captured with the same name, so the meeting vanished from every reader --
My Day listed four of the day's five meetings. 100 notes across 19 names collide on
the reporting install; 3 of them were meetings.

Two rules are checked: nothing is lost, and the by-stem lookup answers the same way
every rebuild."""
import pytest

from app.business.core.vault import vault_manager as module
from app.business.core.vault.vault_manager import VaultManager
from app.config import settings

MEETING = "Work/Meetings/2026-09-22-Masdar-Core42/2026-09-22-Masdar-Core42.md"
MESSAGE = "Work/Threads/2026-09-21 Masdar-Core42/messages/2026-09-22-Masdar-Core42.md"
OTHER = "Work/Notes/Standalone.md"


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "vault_path", tmp_path)
    written = []
    for relative, note_type in ((MEETING, "Meeting"), (MESSAGE, "RawMessage"), (OTHER, "Note")):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'---\ntype: "{note_type}"\n---\n\nbody\n', encoding="utf-8")
        written.append(path)
    # The walk order is what used to decide the winner, so hand them over in the
    # order that made the meeting lose.
    monkeypatch.setattr(module.vault_writer, "list_all_note_paths", lambda: [
        tmp_path / MEETING, tmp_path / MESSAGE, tmp_path / OTHER,
    ])
    return tmp_path


def test_no_note_is_lost_to_a_shared_name(vault):
    manager = VaultManager()
    manager.rebuild_index()

    entries = manager.get_entries()

    assert len(entries) == 3
    assert sorted(entry["frontmatter"]["type"] for entry in entries) == ["Meeting", "Note", "RawMessage"]


def test_the_subject_note_wins_the_name(vault):
    """The meeting's folder is named after it; the message sits inside a Thread's
    folder. The subject note is the one a wikilink or a URL means."""
    manager = VaultManager()
    manager.rebuild_index()

    entry = manager.get_index()["2026-09-22-Masdar-Core42"]

    assert entry["frontmatter"]["type"] == "Meeting"


def test_the_winner_does_not_depend_on_walk_order(vault, monkeypatch):
    manager = VaultManager()
    manager.rebuild_index()
    first = manager.get_index()["2026-09-22-Masdar-Core42"]["path"]

    monkeypatch.setattr(module.vault_writer, "list_all_note_paths", lambda: [
        vault / MESSAGE, vault / OTHER, vault / MEETING,
    ])
    manager.rebuild_index()

    assert manager.get_index()["2026-09-22-Masdar-Core42"]["path"] == first


def test_counting_notes_counts_the_hidden_one_too(vault):
    """`get_overview` and the tag counts read every note, not the deduped map --
    the shape of the original defect, where a whole note simply did not exist to
    anything that iterated."""
    manager = VaultManager()
    manager.rebuild_index()

    assert manager.get_overview().total_notes == 3
    assert len(manager.get_index()) == 2


def test_the_plugin_api_offers_both_views(vault):
    from app import plugin_api

    VaultManager().rebuild_index()
    api = plugin_api.VaultApi()

    assert len(api.entries()) == 3
    assert len(api.index()) == 2
    assert api.index()["2026-09-22-Masdar-Core42"]["frontmatter"]["type"] == "Meeting"
