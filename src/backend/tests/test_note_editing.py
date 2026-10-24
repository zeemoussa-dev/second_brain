"""Editing a note from the app (operator, 2026-10-24: "a way to edit the text
in place like you do in apps instead of Having a Textbox and a Button").

The two guards ARE the feature. A vault that only this app wrote could save
blindly; this one is written continuously by Hermes agents, and the API shows a
converted body for captured email, so a naive save destroys either an agent's
enrichment or the original message.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.business.core.vault.vault_manager import (
    NoteChangedError,
    NoteNotEditableError,
    VaultManager,
)
from app.config import settings
from app.data_access import vault_writer

_NOTE = """---
type: "note"
subject: "Renewal thinking"
tags: ["customer/masdar"]
---

## Summary

The renewal lands in March.
"""


@pytest.fixture
def vault(monkeypatch, tmp_path) -> Path:
    """A vault of one note, indexed."""
    root = tmp_path / "vault"
    (root / "Work" / "Notes").mkdir(parents=True)
    note = root / "Work" / "Notes" / "renewal-thinking.md"
    note.write_text(_NOTE, encoding="utf-8")
    monkeypatch.setattr(settings, "vault_path", root)
    VaultManager().rebuild_index()
    return note


def test_an_edit_reaches_the_file(vault) -> None:
    manager = VaultManager()
    opened = manager.get_note_detail("renewal-thinking")

    manager.update_note_body("renewal-thinking", "## Summary\n\nMoved to April.\n", opened["version"])

    assert "Moved to April." in vault.read_text(encoding="utf-8")


def test_the_frontmatter_survives_byte_for_byte(vault) -> None:
    """Re-serialising the parsed frontmatter would reorder keys, requote
    values and drop anything the parser does not understand -- on notes that
    agents write and read back."""
    manager = VaultManager()
    opened = manager.get_note_detail("renewal-thinking")

    manager.update_note_body("renewal-thinking", "nothing much\n", opened["version"])

    written = vault.read_text(encoding="utf-8")
    assert written.startswith('---\ntype: "note"\nsubject: "Renewal thinking"\ntags: ["customer/masdar"]\n---\n')


def test_a_note_an_agent_rewrote_meanwhile_is_not_overwritten(vault) -> None:
    """The case this install actually hits: Hermes wrote 230 notes in one
    burst this morning. The save is refused and the file keeps what the agent
    put there -- the operator's text is still in their browser."""
    manager = VaultManager()
    opened = manager.get_note_detail("renewal-thinking")

    vault.write_text(_NOTE.replace("March", "an agent wrote this"), encoding="utf-8")

    with pytest.raises(NoteChangedError):
        manager.update_note_body("renewal-thinking", "my version\n", opened["version"])

    assert "an agent wrote this" in vault.read_text(encoding="utf-8")
    assert "my version" not in vault.read_text(encoding="utf-8")


def test_saving_twice_in_a_row_works(vault) -> None:
    """The version the save ANSWERS with is the one the next save sends, or
    typing a second sentence would refuse itself."""
    manager = VaultManager()
    opened = manager.get_note_detail("renewal-thinking")

    first = manager.update_note_body("renewal-thinking", "one\n", opened["version"])
    second = manager.update_note_body("renewal-thinking", "two\n", first["version"])

    assert second["ok"] is True
    assert vault.read_text(encoding="utf-8").endswith("two\n")


def test_a_captured_html_body_refuses_to_be_edited(monkeypatch, tmp_path) -> None:
    """A captured email keeps the original HTML on disk and the API converts
    it on the way out, so what is on screen is a rendering. Writing that back
    would replace the message with a picture of itself."""
    root = tmp_path / "vault"
    (root / "Work" / "Emails").mkdir(parents=True)
    note = root / "Work" / "Emails" / "an-email.md"
    note.write_text(
        '---\ntype: "email"\nsubject: "An email"\nbody_type: "html"\n---\n\n<p>Hello <b>there</b></p>\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "vault_path", root)
    manager = VaultManager()
    manager.rebuild_index()
    opened = manager.get_note_detail("an-email")

    assert opened["editable"] is False
    with pytest.raises(NoteNotEditableError):
        manager.update_note_body("an-email", "rewritten", opened["version"])

    assert "<b>there</b>" in note.read_text(encoding="utf-8")


def test_the_note_knows_its_own_version(vault) -> None:
    """Content, not mtime: this vault sits in OneDrive, whose sync client
    rewrites timestamps, and a version that changes when nothing was edited
    refuses saves nobody conflicted on."""
    manager = VaultManager()
    first = manager.get_note_detail("renewal-thinking")["version"]

    Path(vault).touch()

    assert manager.get_note_detail("renewal-thinking")["version"] == first


def test_links_added_while_editing_are_indexed_at_once(vault) -> None:
    """The note's own entry is rebuilt on save, so a wikilink typed just now
    resolves immediately rather than after the next full index rebuild."""
    manager = VaultManager()
    opened = manager.get_note_detail("renewal-thinking")

    manager.update_note_body(
        "renewal-thinking", "See [[Masdar]] about it.\n", opened["version"]
    )

    entry = manager.get_index()["renewal-thinking"]
    assert "Masdar" in entry["outgoing_wikilinks"]
