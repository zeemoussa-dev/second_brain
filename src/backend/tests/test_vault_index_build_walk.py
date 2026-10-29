r"""The GLOBAL vault index's own traversal -- the deployed one.

`build_vault_index.py` is the script a Hermes cron job runs to build
`index/folders/<folder>.json`, which `vault_manager`'s find_by_id /
find_by_filename / find_in_folder read as their fast path. It had no test
of its own, and that is precisely how it kept the walk the framework's copy
of this engine replaced on 2026-09-06: `rglob` + `is_file()`, where one note
past Windows' 260-character limit silently disappears and an unreadable
subtree abandons the whole top-level folder. A note missing from this index
is a note missing from `find_in_folder`'s listing.

The first test fails against that old walk -- verified by putting it back
and watching it fail, not by assuming.
"""
import json
import os
import sys
from pathlib import Path

import pytest

_APP = Path(__file__).resolve().parents[1] / "app"
_SCRIPTS_DIR = _APP / "business" / "core" / "skills" / "catalog" / "vault" / "vault-index" / "scripts"
_MANAGERS_DIR = _APP / "business" / "core" / "skills" / "managers"
for _path in (_SCRIPTS_DIR, _MANAGERS_DIR):
    sys.path.insert(0, str(_path))

import build_vault_index  # noqa: E402
import vault_manager as vm  # noqa: E402

# Long enough that the note's own full path passes 260 characters once
# pytest's tmp path and a repeated folder name are in front of it -- the
# same shape as a real captured subject line.
LONG_NAME = "2026-09-09 DFS_10014135 - INJAZAT DATA SYSTEMS LLC - Credit Hold and the rest of a real subject line"


def _write(path: Path, note_id: str) -> None:
    os.makedirs(vm.long_path(path.parent), exist_ok=True)
    with open(vm.long_path(path), "w", encoding="utf-8") as handle:
        handle.write('---\nid: "%s"\ntype: "Thread"\n---\n\nbody\n' % note_id)


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.delenv("VAULT_NOTES_ROOTS", raising=False)
    _write(tmp_path / "Work" / "Threads" / "short.md", "short")
    return tmp_path


def test_a_note_past_the_windows_limit_is_indexed(vault):
    """The regression. `is_file()` returns False past MAX_PATH, so the old
    walk dropped exactly the notes this index exists to make findable --
    and dropped them silently, leaving a plausible-looking index."""
    deep = vault / "Work" / "Threads" / LONG_NAME / f"{LONG_NAME}.md"
    _write(deep, "deep")
    assert len(str(deep)) > 260, "the fixture itself must cross the limit"

    folders = build_vault_index.build_index(vault, vault / ".second-brain")

    ids = {entry["id"] for entry in folders["Threads"]}
    assert ids == {"short", "deep"}


def test_an_archived_subtree_is_pruned_not_merely_filtered(vault):
    """`_archive` was always excluded from the RESULT, but rglob still
    descended into it first -- which is where the over-long path lived, so
    the scan died inside a folder the index never wanted."""
    _write(vault / "Work" / "Threads" / "_archive" / LONG_NAME / f"{LONG_NAME}.md", "archived")

    folders = build_vault_index.build_index(vault, vault / ".second-brain")

    assert {entry["id"] for entry in folders["Threads"]} == {"short"}


def test_a_reserved_filename_is_not_a_note(vault):
    _write(vault / "Work" / "Threads" / "index.md", "reserved")

    folders = build_vault_index.build_index(vault, vault / ".second-brain")

    assert {entry["id"] for entry in folders["Threads"]} == {"short"}


# -- the primary root, and the exclusions saved against it ---------------

def test_the_index_is_built_from_the_configured_primary_root(tmp_path, monkeypatch):
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "Personal")
    _write(tmp_path / "Personal" / "Journal" / "monday.md", "monday")
    # A vault with no Work folder at all used to index nothing, so every
    # find fell back to a full scan for ever.
    folders = build_vault_index.build_index(tmp_path, tmp_path / ".second-brain")

    assert list(folders) == ["Journal"]


def test_a_folder_excluded_under_its_old_bare_name_is_still_skipped(vault):
    """Index Filtering saved bare folder names until 2026-10-29 and
    vault-relative ones after it. An exclusion the operator set has to keep
    holding across that, in both directions."""
    data_path = vault / ".second-brain"
    data_path.mkdir(parents=True, exist_ok=True)
    (data_path / "index_config.json").write_text(
        json.dumps({"folders": {"Threads": {"included": False}}}), encoding="utf-8")

    assert build_vault_index.build_index(vault, data_path) == {}


def test_a_folder_excluded_under_its_new_qualified_name_is_skipped(vault):
    data_path = vault / ".second-brain"
    data_path.mkdir(parents=True, exist_ok=True)
    (data_path / "index_config.json").write_text(
        json.dumps({"folders": {"Work/Threads": {"included": False}}}), encoding="utf-8")

    assert build_vault_index.build_index(vault, data_path) == {}


def test_only_one_copy_of_the_index_engine_exists():
    """`catalog/README.md` names this file's own folder as how a duplicated
    engine stayed on the broken walk for weeks. The duplicate is gone; this
    is what tells the next person who adds one."""
    copies = sorted(
        path.relative_to(_APP).as_posix()
        for path in _APP.rglob("index_builder_lib.py")
    )
    assert copies == ["business/core/index/scripts/index_builder_lib.py"]
