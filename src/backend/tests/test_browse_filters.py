"""Browse & Search can narrow and order a vault (operator, 2026-10-24).

The screen showed a `kind` badge on every row and could not filter on one, and
"what changed lately" was unanswerable: the list was always every note, by
name. These pin the filtering and ordering the screen now offers.
"""
from __future__ import annotations

import os
import time

import pytest

from app.business.core.vault import vault_manager as module
from app.business.core.vault.vault_manager import VaultManager
from app.config import settings

_NOTES = (
    ("Masdar renewal", "Opportunity", ("customer/masdar", "stage/negotiation")),
    ("Acme kickoff", "Meeting", ("customer/acme",)),
    ("Beta kickoff", "Meeting", ("customer/beta",)),
    ("Quarterly plan", "Note", ()),
)


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "vault_path", tmp_path)
    paths = []
    for title, kind, tags in _NOTES:
        path = tmp_path / f"{title}.md"
        # The inline list form this codebase writes and its frontmatter parser
        # recognises -- deliberately not general YAML (app/obsidian/frontmatter.py).
        rendered_tags = "[" + ", ".join(f'"{tag}"' for tag in tags) + "]"
        path.write_text(
            f'---\ntype: "{kind}"\nsubject: "{title}"\ntags: {rendered_tags}\n---\n\n'
            f"Body of {title}.\n",
            encoding="utf-8",
        )
        paths.append(path)
    monkeypatch.setattr(module.vault_writer, "list_all_note_paths", lambda: list(paths))
    VaultManager().rebuild_index()
    return tmp_path, paths


def test_the_kinds_offered_are_the_ones_the_vault_actually_has(vault) -> None:
    """Not a hard-coded list: a Template added tomorrow is a kind the filter
    must offer, and one nobody uses must not clutter it."""
    kinds = VaultManager().list_kinds()["kinds"]

    assert {entry["kind"] for entry in kinds} == {"Opportunity", "Meeting", "Note"}
    # Commonest first, like the tag chips, so the useful filters are nearest.
    assert kinds[0] == {"kind": "Meeting", "count": 2}


def test_filtering_by_kind_returns_only_that_kind(vault) -> None:
    listed = VaultManager().list_notes(kind="Meeting")

    assert listed["total"] == 2
    assert {note["kind"] for note in listed["notes"]} == {"Meeting"}


def test_a_kind_and_a_tag_narrow_together(vault) -> None:
    """Both at once, not either: two filters that ignore each other would show
    a list matching neither of the things the operator clicked."""
    listed = VaultManager().list_notes(kind="Meeting", tag="customer/acme")

    assert [note["title"] for note in listed["notes"]] == ["Acme kickoff"]


def test_a_filter_matching_nothing_is_an_honest_empty_list(vault) -> None:
    listed = VaultManager().list_notes(kind="Invoice")

    assert listed == {"total": 0, "page": 1, "page_size": 20, "notes": []}


def test_sorting_by_name_is_the_default_and_is_stable(vault) -> None:
    titles = [note["title"] for note in VaultManager().list_notes()["notes"]]

    assert titles == sorted(titles)


def test_recently_changed_puts_the_newest_first(vault) -> None:
    """The file's own mtime, because a note's dates live in whatever
    frontmatter its Template happens to define -- the filesystem is the only
    answer that exists for every note."""
    tmp_path, paths = vault
    touched = tmp_path / "Quarterly plan.md"
    future = time.time() + 60
    os.utime(touched, (future, future))

    listed = VaultManager().list_notes(sort="recent")

    assert listed["notes"][0]["title"] == "Quarterly plan"


def test_a_note_that_vanished_still_lists(vault) -> None:
    """A missing file sorts last rather than failing the listing for every
    other note: the index is a snapshot, and the vault moves under it."""
    tmp_path, paths = vault
    (tmp_path / "Acme kickoff.md").unlink()

    listed = VaultManager().list_notes(sort="recent")

    assert listed["total"] == len(_NOTES)
    assert listed["notes"][-1]["title"] == "Acme kickoff"


def test_paging_survives_a_filter(vault) -> None:
    listed = VaultManager().list_notes(kind="Meeting", page=2, page_size=1)

    assert listed["total"] == 2
    assert listed["page"] == 2
    assert len(listed["notes"]) == 1
