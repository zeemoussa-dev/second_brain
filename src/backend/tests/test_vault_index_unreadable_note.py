"""BUG-090 -- one unreadable note emptied the whole index.

`rebuild_index()` built every entry in one comprehension, so a single note that
could not be read (moved by capture between the walk and the read, held by
OneDrive, not UTF-8) raised out of the rebuild. At boot that left the index empty
until the next cron refresh, and My Day read "0 emails" with every email on disk.
"""
from pathlib import Path

from app.business.core.vault import vault_manager as module
from app.business.core.vault.vault_manager import VaultManager
from app.config import settings


def _note(root: Path, name: str) -> Path:
    path = root / "Work" / "Threads" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('---\ntype: "Thread"\n---\n\nbody\n', encoding="utf-8")
    return path


def test_a_vanished_note_is_skipped_and_the_rest_are_indexed(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "vault_path", tmp_path)
    readable = [_note(tmp_path, "First"), _note(tmp_path, "Second")]
    vanished = tmp_path / "Work" / "Threads" / "Moved mid-walk.md"
    monkeypatch.setattr(module.vault_writer, "list_all_note_paths", lambda: [readable[0], vanished, readable[1]])

    VaultManager().rebuild_index()

    assert sorted(entry["stem"] for entry in VaultManager().get_entries()) == ["First", "Second"]


def test_a_note_that_is_not_utf8_is_skipped(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "vault_path", tmp_path)
    readable = _note(tmp_path, "Readable")
    garbled = tmp_path / "Work" / "Threads" / "Garbled.md"
    garbled.write_bytes(b"---\ntype: \"Thread\"\n---\n\n\xff\xfe\xfa")
    monkeypatch.setattr(module.vault_writer, "list_all_note_paths", lambda: [garbled, readable])

    VaultManager().rebuild_index()

    assert [entry["stem"] for entry in VaultManager().get_entries()] == ["Readable"]
