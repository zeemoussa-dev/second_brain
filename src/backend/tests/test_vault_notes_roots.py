"""A vault with no `Work/` folder is a usable vault.

Operator, 2026-10-29, setting up a second install for personal use: the
Index and the vault writer both read a hardcoded `<vault>/Work`, so an
install whose vault had no such folder offered no note kinds, indexed
nothing, and could not write a note -- with nothing on screen to say why.

These tests drive the three surfaces that read the roots: the kind
vocabulary, the whole-vault scan, and the Index builder.
"""
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.data_access import vault_writer
from app.obsidian import notes as obsidian_notes


def note(vault: Path, *parts: str) -> Path:
    path = vault.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('---\ntype: "KBDoc"\ntitle: "A note"\n---\n\nbody\n', encoding="utf-8")
    return path


@pytest.fixture()
def personal_vault(tmp_path, monkeypatch):
    """A vault that has never had a Work folder."""
    note(tmp_path, "Personal", "Journal", "monday.md")
    note(tmp_path, "Personal", "Recipes", "bread.md")
    monkeypatch.setattr(
        vault_writer, "settings",
        SimpleNamespace(vault_path=tmp_path, vault_notes_roots_list=["Personal"]),
    )
    return tmp_path


@pytest.fixture()
def two_root_vault(tmp_path, monkeypatch):
    note(tmp_path, "Work", "Threads", "a-deal.md")
    note(tmp_path, "Work", "Customers", "masdar.md")
    note(tmp_path, "Personal", "Journal", "monday.md")
    note(tmp_path, "Personal", "Threads", "family.md")
    monkeypatch.setattr(
        vault_writer, "settings",
        SimpleNamespace(vault_path=tmp_path, vault_notes_roots_list=["Work", "Personal"]),
    )
    return tmp_path


# -- the kind vocabulary -------------------------------------------------

def test_a_vault_with_no_work_folder_still_has_kinds(personal_vault):
    # The exact failure reported: list_known_kinds() read <vault>/Work,
    # found nothing, and returned [] -- so every screen that offers a kind
    # had an empty list and the writer had no vocabulary.
    assert vault_writer.list_known_kinds() == ["Journal", "Recipes"]


def test_kinds_are_one_vocabulary_across_roots(two_root_vault):
    # Threads exists under both roots and is ONE kind: a kind says what a
    # note is, not which part of the vault it sits in.
    assert vault_writer.list_known_kinds() == ["Customers", "Journal", "Threads"]


def test_an_archived_or_dotted_folder_is_not_a_kind(tmp_path, monkeypatch):
    note(tmp_path, "Personal", "Journal", "monday.md")
    note(tmp_path, "Personal", "_archive", "old.md")
    (tmp_path / "Personal" / ".trash").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        vault_writer, "settings",
        SimpleNamespace(vault_path=tmp_path, vault_notes_roots_list=["Personal"]),
    )
    assert vault_writer.list_known_kinds() == ["Journal"]


# -- the whole-vault scan ------------------------------------------------

def test_the_scan_covers_every_root(two_root_vault):
    found = {path.name for path in vault_writer.list_all_note_paths()}
    assert found == {"a-deal.md", "masdar.md", "monday.md", "family.md"}


def test_one_kind_folder_is_read_from_every_root(two_root_vault):
    found = {path.name for path in vault_writer.list_notes_in_kind_folder("Threads")}
    assert found == {"a-deal.md", "family.md"}


def test_a_blank_root_scans_the_vault_but_not_obsidian_s_own_files(tmp_path):
    note(tmp_path, "Journal", "monday.md")
    note(tmp_path, ".obsidian", "workspace.md")
    note(tmp_path, ".second-brain", "data", "notes.md")
    note(tmp_path, "_archive", "old.md")

    found = {path.name for path in obsidian_notes.list_all_note_paths(tmp_path, [""])}
    # A vault that is entirely one thing needs no folder to say so -- but
    # scanning from the vault root reaches Obsidian's own directory and a
    # config folder kept inside the vault, neither of which is a note.
    assert found == {"monday.md"}


# -- the Index -----------------------------------------------------------

def test_the_index_keys_a_folder_by_the_root_it_is_in(two_root_vault, monkeypatch):
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "Work,Personal")
    from app.business.core.index.scripts import index_builder_lib

    built = index_builder_lib.build_index(two_root_vault)
    # Not "Threads" twice: with two roots a bare key could not say which
    # Threads folder it described, and the second would overwrite the first.
    assert set(built) == {"Work/Threads", "Work/Customers", "Personal/Journal", "Personal/Threads"}


def test_an_index_saved_before_roots_existed_still_selects_its_folder(two_root_vault, monkeypatch):
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "Work,Personal")
    from app.business.core.index.scripts import index_builder_lib

    # A bare folder name is what every Index saved before this change
    # holds, and it keeps meaning "that folder" -- in every root.
    built = index_builder_lib.build_index(two_root_vault, folders=["Threads"])
    assert set(built) == {"Work/Threads", "Personal/Threads"}


def test_an_index_can_scope_to_one_root_s_folder(two_root_vault, monkeypatch):
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "Work,Personal")
    from app.business.core.index.scripts import index_builder_lib

    built = index_builder_lib.build_index(two_root_vault, folders=["Personal/Threads"])
    assert set(built) == {"Personal/Threads"}


# -- the include/exclude state saved before folders carried a root ------

def test_a_folder_excluded_under_its_old_bare_name_stays_excluded():
    """Folders are now named "Work/Threads" where they used to be
    "Threads". Reading only the new key would default every state saved
    before today back to included -- a folder deliberately kept out of the
    index would quietly return to it, which nobody would attribute to a
    rename."""
    from app.business.core.vault.vault_manager import VaultManager

    saved = {"Threads": {"included": False}}
    assert VaultManager._folder_included(saved, "Work/Threads") is False


def test_the_qualified_name_wins_where_both_were_saved():
    from app.business.core.vault.vault_manager import VaultManager

    saved = {"Threads": {"included": False}, "Work/Threads": {"included": True}}
    assert VaultManager._folder_included(saved, "Work/Threads") is True


def test_a_folder_nobody_has_an_opinion_about_is_included():
    from app.business.core.vault.vault_manager import VaultManager

    assert VaultManager._folder_included({}, "Personal/Journal") is True


def test_one_root_s_exclusion_does_not_reach_another_root(personal_vault):
    """The reason the qualified name exists: excluding work Threads must
    not exclude personal Threads."""
    from app.business.core.vault.vault_manager import VaultManager

    saved = {"Work/Threads": {"included": False}}
    assert VaultManager._folder_included(saved, "Personal/Threads") is True


def test_the_index_of_a_vault_with_no_work_folder_is_not_empty(personal_vault, monkeypatch):
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "Personal")
    from app.business.core.index.scripts import index_builder_lib

    built = index_builder_lib.build_index(personal_vault)
    assert set(built) == {"Personal/Journal", "Personal/Recipes"}
