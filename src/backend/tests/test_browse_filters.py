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


def test_a_tag_means_the_branch_under_it(vault) -> None:
    """These tags are paths -- `azure/services/compute` -- 312 of them across
    15 categories. "Show me customer" has to mean the branch, or a category is
    a filter that matches nothing."""
    listed = VaultManager().list_notes(tag="customer")

    assert listed["total"] == 3
    assert {note["title"] for note in listed["notes"]} == {
        "Masdar renewal", "Acme kickoff", "Beta kickoff"
    }


def test_the_boundary_is_a_separator_not_a_character_count(vault) -> None:
    """`customer/mas` must not match `customer/masdar`: a prefix that cuts a
    segment in half is a typo, and matching it would quietly widen a filter."""
    assert VaultManager().list_notes(tag="customer/mas")["total"] == 0
    assert VaultManager().list_notes(tag="customer/masdar")["total"] == 1


def test_the_tag_tree_counts_everything_beneath_a_category(vault) -> None:
    tree = VaultManager().list_tag_tree()["tags"]
    by_path = {node["path"]: node for node in tree}

    assert by_path["customer"]["count"] == 3
    assert {child["name"] for child in by_path["customer"]["children"]} == {
        "masdar", "acme", "beta"
    }
    # The branch with the most in it sorts first: it is the one worth opening.
    assert tree[0]["path"] == "customer"


def test_a_note_tagged_twice_in_one_branch_counts_once_for_it(vault, tmp_path, monkeypatch) -> None:
    """Otherwise a category's count exceeds the number of notes it can show,
    and the first thing an operator does is notice."""
    path = tmp_path / "Two tags.md"
    path.write_text(
        '---\ntype: "Note"\nsubject: "Two tags"\ntags: ["azure/services/compute", '
        '"azure/services/analytics"]\n---\n\nBody.\n',
        encoding="utf-8",
    )
    existing = list(module.vault_writer.list_all_note_paths())
    monkeypatch.setattr(module.vault_writer, "list_all_note_paths", lambda: [*existing, path])
    VaultManager().rebuild_index()

    by_path = {node["path"]: node for node in VaultManager().list_tag_tree()["tags"]}

    assert by_path["azure"]["count"] == 1


def test_the_folder_tree_is_relative_to_the_vault(vault, tmp_path, monkeypatch) -> None:
    """Never the absolute path: that is this machine's business, it changes
    when the vault moves, and no screen should show it."""
    nested = tmp_path / "Work" / "Customers" / "Filed.md"
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_text('---\ntype: "Note"\nsubject: "Filed"\ntags: []\n---\n\nBody.\n', encoding="utf-8")
    existing = list(module.vault_writer.list_all_note_paths())
    monkeypatch.setattr(module.vault_writer, "list_all_note_paths", lambda: [*existing, nested])
    VaultManager().rebuild_index()

    folders = VaultManager().list_folders()["folders"]
    work = next(node for node in folders if node["path"] == "Work")

    assert work["count"] == 1
    assert [child["path"] for child in work["children"]] == ["Work/Customers"]
    assert str(tmp_path) not in str(folders)


def test_filtering_by_folder_narrows_to_it(vault, tmp_path, monkeypatch) -> None:
    nested = tmp_path / "Work" / "Filed.md"
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_text('---\ntype: "Note"\nsubject: "Filed"\ntags: []\n---\n\nBody.\n', encoding="utf-8")
    existing = list(module.vault_writer.list_all_note_paths())
    monkeypatch.setattr(module.vault_writer, "list_all_note_paths", lambda: [*existing, nested])
    VaultManager().rebuild_index()

    listed = VaultManager().list_notes(folder="Work")

    assert [note["title"] for note in listed["notes"]] == ["Filed"]


def test_the_graph_is_scoped_by_the_same_filters_as_the_list(vault) -> None:
    """One filter, two views. A graph showing a different set than the list
    beside it is two screens that disagree."""
    graph = VaultManager().get_graph(kind="Meeting")

    assert graph["total"] == 2
    assert {node["kind"] for node in graph["nodes"]} == {"Meeting"}


def test_the_graph_caps_what_it_draws_and_says_so(vault) -> None:
    """4,300 nodes at once is a cloud, not a graph. The cap has to be
    reported, or a partial graph reads as the whole vault."""
    graph = VaultManager().get_graph(limit=2)

    assert len(graph["nodes"]) == 2
    assert graph["total"] == len(_NOTES)
    assert graph["truncated"] is True


def test_an_unscoped_graph_is_still_the_whole_vault(vault) -> None:
    graph = VaultManager().get_graph()

    assert graph["total"] == len(_NOTES)
    assert graph["truncated"] is False


def test_the_list_says_when_each_note_last_changed(vault) -> None:
    """The browse row shows "3d ago", so the list has to carry the date. Only
    the LIST: it costs a stat per note, which is affordable for a page of
    twenty and not for a graph of hundreds."""
    listed = VaultManager().list_notes()

    assert all(note["modified_at"] for note in listed["notes"])
    assert "T" in listed["notes"][0]["modified_at"], "an ISO timestamp, not a formatted date"


def test_the_graph_is_not_made_to_pay_for_the_date(vault) -> None:
    graph = VaultManager().get_graph()

    assert all("modified_at" not in node for node in graph["nodes"])


def test_a_vanished_note_has_no_date_rather_than_a_fake_one(vault, tmp_path) -> None:
    (tmp_path / "Acme kickoff.md").unlink()

    listed = VaultManager().list_notes()
    gone = next(note for note in listed["notes"] if note["title"] == "Acme kickoff")

    assert gone["modified_at"] is None
