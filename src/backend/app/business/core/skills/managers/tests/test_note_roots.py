"""The vault's note roots are configured, not compiled in.

Operator, 2026-10-29, deploying a second install for personal use:
"Indexes for example Uses Work as Hardcoded Path and I can't Use the Vault
Writer if I don't have Work folder ... What if the whole Vault is Work or
all the Vault is Personal". A vault may now hold several roots side by
side (Work/ and Personal/), one root under any name, or none at all.

Two properties matter more than the parsing, and both are asserted here:

  * an install that sets NOTHING behaves exactly as it did -- which the
    rest of this directory's tests already prove, since every one of them
    asserts a real `Work/` path and none of them sets the variable;
  * a note_name round-trips. `note_name_for` derives a name from a path and
    `create` resolves a name to a path, and a child of a Personal note must
    not land in Work/.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parent.parent / "vault_manager.py"
_spec = importlib.util.spec_from_file_location("vault_manager", _MODULE_PATH)
vm = importlib.util.module_from_spec(_spec)
sys.modules["vault_manager"] = vm
_spec.loader.exec_module(vm)


@pytest.fixture
def vault(tmp_path: Path, monkeypatch) -> Path:
    """A scratch vault with one template, and NO roots configured -- each
    test sets what it is testing, so a leaked value cannot make another
    test pass."""
    monkeypatch.delenv("VAULT_NOTES_ROOTS", raising=False)
    template = tmp_path / ".second-brain" / "data" / "Templates" / "kb-doc" / "Template.json"
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text(json.dumps({
        "id": "kb-doc",
        "on_missing": "create",
        "root": {
            "on_existing_title": "update_section",
            "frontmatter_defaults": {"type": "KBDoc"},
            "sections": [{"name": "Summary", "access": "machine_write"}],
        },
    }), encoding="utf-8")
    return tmp_path


# -- what the setting parses to ------------------------------------------

def test_the_default_root_is_work_when_nothing_is_set(vault):
    assert vm.note_roots() == ("Work",)


def test_several_roots_keep_their_order(vault, monkeypatch):
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "Work,Personal")
    assert vm.note_roots() == ("Work", "Personal")


def test_surrounding_whitespace_and_slashes_are_not_part_of_a_root_name(vault, monkeypatch):
    monkeypatch.setenv("VAULT_NOTES_ROOTS", " Work/ , /Personal ")
    assert vm.note_roots() == ("Work", "Personal")


def test_an_empty_setting_means_the_vault_itself_is_the_root(vault, monkeypatch):
    # Not the same as unset: unset is "nobody chose", empty is the real
    # choice a vault that is entirely one thing makes.
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "")
    assert vm.note_roots() == ("",)


# -- how a note_name resolves -------------------------------------------

def test_a_bare_note_name_resolves_under_the_first_root(vault, monkeypatch):
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "Work,Personal")
    assert vm._notes_root(vault, "Threads") == vault / "Work" / "Threads"


def test_a_note_name_that_names_a_root_is_used_as_it_stands(vault, monkeypatch):
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "Work,Personal")
    assert vm._notes_root(vault, "Personal/Journal") == vault / "Personal" / "Journal"


def test_a_root_is_recognised_whatever_its_case(vault, monkeypatch):
    # Windows paths are case-insensitive, and the segment is matched before
    # sanitising -- a root called "My Notes" must still match itself.
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "Work,Personal")
    assert vm._notes_root(vault, "personal/Journal") == vault / "personal" / "Journal"


def test_a_folder_sharing_a_root_s_name_is_not_mistaken_for_one(vault, monkeypatch):
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "Work")
    # "Personal" is not a configured root here, so it is an ordinary folder
    # under the only one there is.
    assert vm._notes_root(vault, "Personal/Journal") == vault / "Work" / "Personal" / "Journal"


def test_with_no_root_at_all_a_note_name_hangs_off_the_vault(vault, monkeypatch):
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "")
    assert vm._notes_root(vault, "Journal") == vault / "Journal"


# -- and what that means for real writes --------------------------------

def test_create_writes_into_the_root_the_note_name_names(vault, monkeypatch):
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "Work,Personal")
    template = vm.load_template(vault, "kb-doc")
    result = vm.create(vault, template, note_name="Personal/Journal", title="Monday", sections={"Summary": "s"})
    assert Path(result["path"]).parent == vault / "Personal" / "Journal"


def test_create_still_writes_to_work_for_a_caller_that_names_no_root(vault, monkeypatch):
    # Every shipped capture script passes a bare name. This is the
    # assertion that says they did not change behaviour.
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "Work,Personal")
    template = vm.load_template(vault, "kb-doc")
    result = vm.create(vault, template, note_name="Threads", title="A thread", sections={"Summary": "s"})
    assert Path(result["path"]).parent == vault / "Work" / "Threads"


def test_a_vault_with_no_work_folder_can_still_be_written_to(vault, monkeypatch):
    """The operator's actual report: no Work folder, so nothing could be
    written at all."""
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "Personal")
    template = vm.load_template(vault, "kb-doc")
    result = vm.create(vault, template, note_name="Journal", title="Monday", sections={"Summary": "s"})
    assert result["created"] is True
    assert Path(result["path"]).parent == vault / "Personal" / "Journal"
    assert not (vault / "Work").exists()


def test_a_note_name_round_trips_through_the_path_it_produced(vault, monkeypatch):
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "Work,Personal")
    template = vm.load_template(vault, "kb-doc")
    result = vm.create(vault, template, note_name="Personal/Journal", title="Monday", sections={"Summary": "s"})

    derived = vm.note_name_for(vault, Path(result["path"]).parent)
    assert derived == "Personal/Journal"
    # And resolving the derived name lands back where it came from: this is
    # what keeps a child of a Personal note out of Work/.
    assert vm._notes_root(vault, derived) == Path(result["path"]).parent


def test_an_unscoped_find_reaches_every_root(vault, monkeypatch):
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "Work,Personal")
    template = vm.load_template(vault, "kb-doc")
    personal = vm.create(vault, template, note_name="Personal/Journal", title="Monday", sections={"Summary": "s"})

    # note_name omitted: before roots were configurable this searched the
    # one root there was, and searching only the primary now would make a
    # personal note look deleted rather than out of scope.
    assert vm.find_by_id(vault, personal["id"]) == Path(personal["path"])


def test_a_scoped_find_does_not_cross_into_another_root(vault, monkeypatch):
    monkeypatch.setenv("VAULT_NOTES_ROOTS", "Work,Personal")
    template = vm.load_template(vault, "kb-doc")
    personal = vm.create(vault, template, note_name="Personal/Journal", title="Monday", sections={"Summary": "s"})

    assert vm.find_by_id(vault, personal["id"], note_name="Work/Journal") is None
