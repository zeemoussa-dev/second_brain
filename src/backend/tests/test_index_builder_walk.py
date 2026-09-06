r"""The index build engine's own traversal.

Two live failures on 2026-09-06 came from this walk, not from the Manager
around it: `Path.rglob` aborted a whole top-level folder the moment one
note sat past Windows' 260-char MAX_PATH, and the fix for that (walking
the extended-length `\?\` form) started yielding prefixed paths that no
longer resolved against the plain vault root. These pin both halves.
"""
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "app" / "business" / "core" / "index" / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

import index_builder_lib  # noqa: E402

_EXTENDED_PREFIX = "\\?\\"


def _note(path: Path, *, tags: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Frontmatter list items must be QUOTED -- vault_manager's own parser
    # only matches quoted entries, so `tags: [adnoc]` reads as no tags.
    quoted = ", ".join('"%s"' % tag for tag in tags or [])
    tag_line = "tags: [%s]\n" % quoted if tags else ""
    path.write_text("---\nid: %s\n%s---\n\nbody\n" % (path.stem, tag_line), encoding="utf-8")


@pytest.fixture()
def vault(tmp_path: Path) -> Path:
    work = tmp_path / "Work"
    _note(work / "Customers" / "Adnoc.md")
    _note(work / "Customers" / "Nested" / "Deeper" / "Note.md", tags=["adnoc"])
    _note(work / "Threads" / "Thread-one.md", tags=["adnoc"])
    # Pruned during the walk, never descended into.
    _note(work / "Customers" / "_archive" / "Old.md")
    # Reserved filenames are excluded by name.
    _note(work / "Customers" / "index.md")
    return tmp_path


def test_paths_resolve_against_the_plain_vault_root(vault: Path) -> None:
    """The regression: walking the long-path form yields prefixed paths,
    and every entry's `path` is computed relative to the vault. Get the
    reconstruction wrong and build_index raises ValueError for every note."""
    result = index_builder_lib.build_index(vault)

    paths = [entry["path"] for entry in result["Customers"]]
    assert "Work/Customers/Adnoc.md" in paths
    assert "Work/Customers/Nested/Deeper/Note.md" in paths
    assert all(not p.startswith(_EXTENDED_PREFIX) for p in paths)
    assert all("\\" not in p for p in paths)


def test_underscore_folders_are_pruned_not_merely_filtered(vault: Path) -> None:
    """Pruning is what keeps an unreadable archive from aborting the scan,
    so the archived note must be absent."""
    result = index_builder_lib.build_index(vault)

    assert all("_archive" not in entry["path"] for entry in result["Customers"])


def test_reserved_filenames_are_excluded(vault: Path) -> None:
    result = index_builder_lib.build_index(vault)

    assert all(entry["filename"] != "index.md" for entry in result["Customers"])


def test_depth_limits_recursion_under_each_top_folder(vault: Path) -> None:
    result = index_builder_lib.build_index(vault, depth=0)

    assert [entry["filename"] for entry in result["Customers"]] == ["Adnoc.md"]


def test_a_tag_filter_selects_across_folders(vault: Path) -> None:
    result = index_builder_lib.build_index(vault, tags=["adnoc"])

    assert sorted(result) == ["Customers", "Threads"]
    assert [entry["filename"] for entry in result["Customers"]] == ["Note.md"]


def test_folder_scope_restricts_to_named_top_folders(vault: Path) -> None:
    result = index_builder_lib.build_index(vault, folders=["Threads"])

    assert list(result) == ["Threads"]
