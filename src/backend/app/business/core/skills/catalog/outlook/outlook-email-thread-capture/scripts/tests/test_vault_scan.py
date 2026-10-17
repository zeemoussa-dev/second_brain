"""The vault scan that MAX_PATH broke.

Found live 2026-09-04. The 2026-09-03 vault move lengthened the vault root
from 32 to 71 characters, which pushed an already-existing archived folder
past Windows' 260-character limit (220 chars before the move, 259 after).
`rglob("*.md")` then raised FileNotFoundError mid-traversal, killing the
whole ingest AFTER the Thread note had been written -- leaving Thread notes
with no messages/ and an empty last_message_at, and 42 emails failing per run.

Two things were wrong and both are covered here: no long-path support, and
`_`-prefixed folders being filtered out of the RESULTS while still being
walked into.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vault_manager  # noqa: E402


def test_underscore_folders_are_not_entered_at_all(tmp_path: Path) -> None:
    """Pruning during the walk, not filtering after it. The distinction is
    the whole fix: an excluded-but-unreadable subtree used to abort the
    entire scan before anything could reject it."""
    (tmp_path / "Threads").mkdir()
    (tmp_path / "Threads" / "keep.md").write_text("x", encoding="utf-8")
    archived = tmp_path / "_archive" / "deep"
    archived.mkdir(parents=True)
    (archived / "skipped.md").write_text("x", encoding="utf-8")

    found = {p.name for p in vault_manager.iter_md_files(tmp_path)}

    assert found == {"keep.md"}


def test_nested_underscore_folder_is_pruned(tmp_path: Path) -> None:
    nested = tmp_path / "Meetings" / "_Archived Duplicates (2026-08-24)"
    nested.mkdir(parents=True)
    (nested / "dupe.md").write_text("x", encoding="utf-8")
    (tmp_path / "Meetings" / "real.md").write_text("x", encoding="utf-8")

    found = {p.name for p in vault_manager.iter_md_files(tmp_path)}

    assert found == {"real.md"}


def test_only_markdown_is_yielded(tmp_path: Path) -> None:
    (tmp_path / "note.md").write_text("x", encoding="utf-8")
    (tmp_path / "desktop.ini").write_text("x", encoding="utf-8")
    (tmp_path / "attachment.pdf").write_text("x", encoding="utf-8")

    assert {p.name for p in vault_manager.iter_md_files(tmp_path)} == {"note.md"}


@pytest.mark.skipif(os.name != "nt", reason="MAX_PATH is a Windows limit")
def test_long_path_carries_the_extended_prefix() -> None:
    resolved = vault_manager.long_path(Path(r"C:\some\vault"))

    assert resolved.startswith("\\\\?\\"), repr(resolved)
    # A single leading backslash is the easy typo, and it fails SILENTLY --
    # os.walk simply yields nothing, which reads exactly like an empty vault.
    assert not resolved.startswith("\\?\\C")


@pytest.mark.skipif(os.name != "nt", reason="MAX_PATH is a Windows limit")
def test_already_prefixed_paths_are_not_double_prefixed() -> None:
    once = vault_manager.long_path(Path(r"C:\some\vault"))

    assert vault_manager.long_path(once) == once


@pytest.mark.skipif(os.name != "nt", reason="MAX_PATH is a Windows limit")
def test_a_file_past_max_path_is_still_found(tmp_path: Path) -> None:
    """The real failure, reproduced: a path over 260 characters that plain
    rglob cannot traverse."""
    deep = tmp_path
    while len(str(deep)) < 250:
        deep = deep / ("d" * 40)
    # Creating the fixture needs the same long-path treatment it is testing --
    # plain mkdir cannot even build a tree this deep.
    os.makedirs(vault_manager.long_path(deep), exist_ok=True)
    target = deep / "buried.md"
    Path(vault_manager.long_path(target)).write_text("x", encoding="utf-8")
    assert len(str(target)) > 260

    found = [p.name for p in vault_manager.iter_md_files(tmp_path)]

    assert "buried.md" in found
