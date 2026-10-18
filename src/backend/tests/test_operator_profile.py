"""The Operator Profile singleton -- `REQ-SB-95-US-01-T01`.

Covers the three locked ACs this task owns: `AC-01` (one record, one
Manager, one store, no catalogue surface), `AC-03` (a team entry is
membership, not a copy of a person) and `AC-04` (the operator's own
address is mirrored from the `SELF_EMAIL` setting and never written).

Every test runs against a `second_brain_data_path` inside pytest's own
tmp dir that does not exist when the test starts, so the suite exercises
a genuinely empty install and can never read or write the operator's
real store. Every value below is fictitious.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import app.config
from app.business import setup_wizard, system_settings
from app.business.core.operator import operator_profile_manager as manager_module
from app.business.core.operator.operator_profile_manager import OperatorProfileManager
from app.config import settings
from app.data_access import operator_profile as operator_profile_data
from app.data_access import vault_writer

OWN_ADDRESS = "operator@example.test"

A_PROFILE = {
    "name": "Robin Fictional",
    "other_email_addresses": ["robin.alt@example.test", "robin@example.invalid"],
    "timezone": "Etc/UTC",
    "team": [
        {"email": "blue@example.test", "role": "Engineer"},
        {"email": "green@example.test", "role": "Designer"},
        {"email": "amber@example.test", "role": "Analyst"},
    ],
}


@pytest.fixture(autouse=True)
def empty_install(tmp_path, monkeypatch):
    """A data path that does not exist yet -- the fresh-install state,
    and the thing that keeps the real store out of reach."""
    data_path = tmp_path / "second-brain-data"
    monkeypatch.setattr(settings, "second_brain_data_path", data_path)
    monkeypatch.setattr(settings, "self_email", OWN_ADDRESS)
    assert not data_path.exists()
    return data_path


def stored_json(data_path: Path) -> dict:
    return json.loads((data_path / "data" / "Operator" / "Profile.json").read_text(encoding="utf-8"))


def test_an_install_that_never_saved_reads_back_as_unconfigured(empty_install):
    """Not an invented empty record that looks configured. `T02`'s
    `AC-05` block tells those two apart with exactly this flag."""
    profile = OperatorProfileManager().get()

    assert profile.is_configured is False
    assert (profile.name, profile.other_email_addresses, profile.timezone, profile.team) == ("", [], "", [])


def test_the_profile_is_one_record_at_one_path_and_reads_back_as_saved(empty_install):
    """[REQ-SB-95-US-01-AC-01]"""
    saved = OperatorProfileManager().save(A_PROFILE)

    expected_path = (empty_install / "data" / "Operator" / "Profile.json").resolve()
    assert operator_profile_data.profile_path().resolve() == expected_path
    assert expected_path.is_file()

    for profile in (saved, OperatorProfileManager().get()):
        assert profile.is_configured is True
        assert profile.name == A_PROFILE["name"]
        assert profile.other_email_addresses == A_PROFILE["other_email_addresses"]
        assert profile.timezone == A_PROFILE["timezone"]
        assert [(member.email, member.role) for member in profile.team] == [
            (entry["email"], entry["role"]) for entry in A_PROFILE["team"]
        ]


def test_the_manager_is_a_singleton_and_a_second_save_replaces_the_one_record(empty_install):
    """[REQ-SB-95-US-01-AC-01]"""
    public_surface = {name for name in dir(OperatorProfileManager) if not name.startswith("_")}
    assert public_surface == {"get", "save"}

    for method_name in ("get", "save"):
        parameters = set(inspect.signature(getattr(OperatorProfileManager, method_name)).parameters)
        assert not parameters & {"id", "profile_id", "operator_id"}

    OperatorProfileManager().save(A_PROFILE)
    OperatorProfileManager().save({**A_PROFILE, "name": "Sam Fictional"})

    operator_dir = empty_install / "data" / "Operator"
    assert [path.name for path in sorted(operator_dir.rglob("*")) if path.is_file()] == ["Profile.json"]
    assert OperatorProfileManager().get().name == "Sam Fictional"


def test_a_team_entry_holds_an_email_and_a_role_and_nothing_else(empty_install):
    """[REQ-SB-95-US-01-AC-03]"""
    OperatorProfileManager().save({
        "team": [{
            "email": "blue@example.test",
            "role": "Engineer",
            "name": "Blue Fictional",
            "title": "Principal Engineer",
            "description": "a second copy of a person",
        }],
    })

    stored_entry = stored_json(empty_install)["team"][0]
    assert set(stored_entry) == {"email", "role"}
    assert stored_entry == {"email": "blue@example.test", "role": "Engineer"}

    team = OperatorProfileManager().get().team
    assert [(member.email, member.role) for member in team] == [("blue@example.test", "Engineer")]


def test_the_stored_email_is_what_reaches_the_real_person_note(empty_install, tmp_path, monkeypatch):
    """[REQ-SB-95-US-01-AC-03] Membership works because the email is
    returned unchanged and the vault files a Person note by it."""
    vault = tmp_path / "vault"
    note = vault / "Work" / "Customers" / "Acme" / "People" / "blue@example.test.md"
    note.parent.mkdir(parents=True)
    note.write_text('---\ntype: "Person"\nname: "Blue Fictional"\n---\n', encoding="utf-8")
    monkeypatch.setattr(vault_writer, "settings", SimpleNamespace(vault_path=vault))

    OperatorProfileManager().save({"team": [{"email": "blue@example.test", "role": "Engineer"}]})
    member = OperatorProfileManager().get().team[0]

    assert vault_writer.find_person_note_path(member.email, ["Work/Customers"]) == note


def test_the_own_address_is_mirrored_from_the_setting_and_marked_read_only(empty_install):
    """[REQ-SB-95-US-01-AC-04]"""
    own_address = OperatorProfileManager().get().own_address

    assert own_address.email == OWN_ADDRESS
    assert own_address.read_only is True
    assert own_address.setting_key == "SELF_EMAIL"
    assert own_address.edited_at == "Settings > System"


def test_no_copy_of_the_own_address_is_ever_written(empty_install):
    """[REQ-SB-95-US-01-AC-04]"""
    OperatorProfileManager().save({
        **A_PROFILE,
        "own_address": {"email": OWN_ADDRESS},
        "self_email": OWN_ADDRESS,
        "email": OWN_ADDRESS,
    })

    written = (empty_install / "data" / "Operator" / "Profile.json").read_bytes()
    assert OWN_ADDRESS.encode("utf-8") not in written
    assert b"self_email" not in written and b"own_address" not in written
    assert set(stored_json(empty_install)) == {"name", "other_email_addresses", "timezone", "team"}


def test_saving_the_profile_leaves_the_self_email_setting_entirely_alone(empty_install, monkeypatch):
    """[REQ-SB-95-US-01-AC-04] The regression clause of `ADR-038`: the
    setting stays exactly as it is, and the Profile path never syncs it."""
    syncs: list[tuple] = []
    monkeypatch.setattr(setup_wizard, "sync_settings_to_hermes", lambda *args, **kwargs: syncs.append((args, kwargs)))

    OperatorProfileManager().save(A_PROFILE)

    assert syncs == []
    # A module-attribute spy cannot see a `from ... import` binding, so
    # pin the absence of the import itself too.
    for module in (manager_module, operator_profile_data):
        source_lines = Path(module.__file__).read_text(encoding="utf-8").splitlines()
        imports = [line for line in source_lines if line.startswith(("import ", "from ", "    import ", "    from "))]
        assert not [line for line in imports if "setup_wizard" in line]

    assert "self_email" in app.config.REQUIRED_FOR_STARTUP
    assert "self_email" in system_settings._FIELDS
    assert system_settings._FIELDS["self_email"]["env_key"] == "SELF_EMAIL"


def test_changing_the_setting_changes_what_the_profile_returns_with_no_save(empty_install, monkeypatch):
    """[REQ-SB-95-US-01-AC-04]"""
    OperatorProfileManager().save(A_PROFILE)
    assert OperatorProfileManager().get().own_address.email == OWN_ADDRESS

    monkeypatch.setattr(settings, "self_email", "moved@example.test")

    assert OperatorProfileManager().get().own_address.email == "moved@example.test"
    assert stored_json(empty_install)["name"] == A_PROFILE["name"]
