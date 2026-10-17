"""Plugin-contributed Actions (REQ-SB-95-US-02-T05, AC-06, ADR-022).

One catalogue: an installed plugin registers Actions through the
`app.plugin_api` facade and they appear beside the install's own, each
attributed to the plugin that contributed it. Nothing about them is
stored, which is the whole point -- uninstalling the plugin removes its
Actions by construction rather than by a cleanup step that could fail,
and the install's own Actions cannot be touched by any of it.

The plugin is a real one written into a temporary App Database Folder,
the technique tests/test_plugin_host.py already uses, so registration
goes through the real loader and the real facade rather than a stand-in
for them. Writes are recorded exactly as tests/test_action_resolution.py
records them, so "nothing was written" is an assertion and not an
absence of evidence.
"""
import json
import textwrap
from pathlib import Path

import pytest

from app import plugin_api
from app.business.core.actions import action_manager as action_manager_module
from app.business.core.actions.action_manager import (
    ActionManager,
    PluginContributedActionIsReadOnlyError,
)
from app.business.core.plugins import plugin_manager as plugin_manager_module
from app.business.core.plugins.plugin_manager import PluginManager
from app.config import settings
from app.data_access import actions as actions_data

A_PLUGIN_ROUTE = ("GET", "/plugins/reporter/report")
A_REAL_FEATURE_KEY = "/settings/artifacts"

_REPORTING_BACKEND = '''
def register(api):
    api.register_action(
        "reporter-weekly",
        description="Build this week's report",
        inputs=[{"name": "week", "type": "string", "required": True}],
        allowed_callers=["*"],
        needs_confirmation=True,
        implementation={"http": {"method": "GET", "path": "/plugins/reporter/report"}},
    )
    api.register_action(
        "reporter-monthly",
        description="Build this month's report",
        implementation={"ui": {"feature_key": "/settings/artifacts"}},
    )
'''


@pytest.fixture(autouse=True)
def leaves_no_loaded_plugin_behind(monkeypatch):
    """`load_all()` writes module-level state that outlives one test, the
    way VaultManager's index does. Restored here so a plugin installed in
    a temporary folder can never be seen by a later test whose settings
    point back at the real install."""
    monkeypatch.setattr(plugin_manager_module, "_plugin_actions", list(plugin_manager_module._plugin_actions))
    monkeypatch.setattr(plugin_manager_module, "_load_report", list(plugin_manager_module._load_report))


@pytest.fixture()
def data_path(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path)
    return tmp_path


@pytest.fixture()
def resolvable(monkeypatch):
    """The live resolution sources, replaced by ones this test controls --
    what is deployed and mounted on the machine running the suite is
    instance state, not a fact about plugin-contributed Actions."""
    monkeypatch.setattr(action_manager_module, "deployed_skill_ids", set)
    monkeypatch.setattr(action_manager_module, "app_route_table", lambda: {A_PLUGIN_ROUTE})
    monkeypatch.setattr(action_manager_module, "UI_FEATURE_KEYS", (A_REAL_FEATURE_KEY,))


@pytest.fixture()
def writes(monkeypatch) -> dict:
    """Every write that reached the Actions store, by id. The real write
    still happens, so a stored Action is a real file in the temporary
    data folder and not a fixture's idea of one."""
    recorded: dict = {}
    real_write = actions_data.write_action_json
    real_delete = actions_data.delete_action_definition

    def record_write(action_id, data):
        recorded[action_id] = data
        real_write(action_id, data)

    def record_delete(action_id):
        recorded.setdefault("deleted", []).append(action_id)
        real_delete(action_id)

    monkeypatch.setattr(actions_data, "write_action_json", record_write)
    monkeypatch.setattr(actions_data, "delete_action_definition", record_delete)
    return recorded


def install(data_path: Path, plugin_id: str, backend: str) -> None:
    folder = data_path / "plugins" / plugin_id
    (folder / "backend").mkdir(parents=True)
    (folder / "plugin.json").write_text(json.dumps({
        "id": plugin_id, "name": plugin_id.title(), "version": "0.1.0",
        "framework_api": plugin_api.FRAMEWORK_API, "requires": [],
    }), encoding="utf-8")
    (folder / "backend" / "__init__.py").write_text(textwrap.dedent(backend), encoding="utf-8")
    write_record(data_path, [{"id": plugin_id, "version": "0.1.0"}])


def write_record(data_path: Path, entries: list[dict]) -> None:
    record_path = data_path / "plugins" / "installed.json"
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps({"plugins": entries}), encoding="utf-8")


def uninstall(data_path: Path, plugin_id: str) -> None:
    """What an uninstall leaves behind for the host: an ownership record
    that no longer names the plugin, and the next load."""
    write_record(data_path, [])
    PluginManager().load_all()


def save_an_own_action(action_id: str = "own-export"):
    return ActionManager().create(
        action_id,
        description="The install's own Action",
        inputs=[{"name": "scope", "type": "string", "required": False}],
        allowed_callers=["cbo"],
        implementation={"ui": {"feature_key": A_REAL_FEATURE_KEY}},
    )


def catalogue_by_id() -> dict:
    return {action.id: action for action in ActionManager().get_all()}


# -- one catalogue, attributed ---------------------------------------------------


def test_a_plugins_actions_join_the_installs_own_in_one_catalogue(data_path, resolvable, writes):
    """[REQ-SB-95-US-02-AC-06]"""
    install(data_path, "reporter", _REPORTING_BACKEND)
    save_an_own_action()

    PluginManager().load_all()
    catalogue = catalogue_by_id()

    assert sorted(catalogue) == ["own-export", "reporter-monthly", "reporter-weekly"]
    assert catalogue["reporter-weekly"].plugin_id == "reporter"
    assert catalogue["reporter-monthly"].plugin_id == "reporter"
    # A stored Action carries no attribution at all, rather than an empty
    # one: "contributed by nobody" and "contributed by ''" must not read
    # back as the same thing to the screen that shows the credit.
    assert not hasattr(catalogue["own-export"], "plugin_id")


def test_a_contributed_action_keeps_the_fields_the_plugin_declared(data_path, resolvable):
    """[REQ-SB-95-US-02-AC-06]"""
    install(data_path, "reporter", _REPORTING_BACKEND)

    PluginManager().load_all()
    weekly = catalogue_by_id()["reporter-weekly"]

    assert weekly.description == "Build this week's report"
    assert [(entry.name, entry.required) for entry in weekly.inputs] == [("week", True)]
    assert weekly.allowed_callers == ["*"]
    assert weekly.needs_confirmation is True
    assert (weekly.implementation.kind, weekly.implementation.path) == ("http", "/plugins/reporter/report")


def test_a_contributed_action_resolves_against_the_plugins_own_mounted_route(data_path, resolvable):
    """[REQ-SB-95-US-02-AC-06]"""
    install(data_path, "reporter", _REPORTING_BACKEND)

    PluginManager().load_all()
    status_by_id = {entry["action_id"]: entry for entry in ActionManager().resolution_report()}

    assert status_by_id["reporter-weekly"]["status"] == "resolves"
    assert status_by_id["reporter-monthly"]["status"] == "resolves"


# -- composed at read time, never stored -----------------------------------------


def test_no_contributed_action_is_ever_written_to_the_actions_store(data_path, resolvable, writes):
    """[REQ-SB-95-US-02-AC-06]"""
    install(data_path, "reporter", _REPORTING_BACKEND)
    save_an_own_action()

    PluginManager().load_all()
    ActionManager().get_all()

    assert sorted(writes) == ["own-export"]
    assert not actions_data.action_file("reporter-weekly").exists()
    assert not actions_data.action_file("reporter-monthly").exists()
    assert sorted(actions_data.list_action_ids()) == ["own-export"]


def test_uninstalling_the_plugin_takes_its_actions_and_leaves_the_installs_own(data_path, resolvable, writes):
    """[REQ-SB-95-US-02-AC-06]"""
    install(data_path, "reporter", _REPORTING_BACKEND)
    save_an_own_action()
    PluginManager().load_all()
    own_before = catalogue_by_id()["own-export"]
    stored_bytes_before = actions_data.action_file("own-export").read_bytes()

    uninstall(data_path, "reporter")
    catalogue = catalogue_by_id()

    assert sorted(catalogue) == ["own-export"]
    assert catalogue["own-export"] == own_before
    assert actions_data.action_file("own-export").read_bytes() == stored_bytes_before


# -- read-only on every write path -----------------------------------------------


def test_a_contributed_action_cannot_be_updated_or_deleted(data_path, resolvable, writes):
    """[REQ-SB-95-US-02-AC-06]"""
    install(data_path, "reporter", _REPORTING_BACKEND)
    PluginManager().load_all()

    with pytest.raises(PluginContributedActionIsReadOnlyError) as updated:
        ActionManager().update("reporter-weekly", description="mine now")
    with pytest.raises(PluginContributedActionIsReadOnlyError) as deleted:
        ActionManager().delete("reporter-weekly")

    for refusal in (updated, deleted):
        assert "reporter" in str(refusal.value)
    assert writes == {}
    assert catalogue_by_id()["reporter-weekly"].description == "Build this week's report"


def test_the_installs_own_action_is_still_writable_while_a_plugin_contributes(data_path, resolvable, writes):
    """[REQ-SB-95-US-02-AC-06]"""
    install(data_path, "reporter", _REPORTING_BACKEND)
    save_an_own_action()
    PluginManager().load_all()

    ActionManager().update("own-export", description="edited")

    assert catalogue_by_id()["own-export"].description == "edited"
    assert ActionManager().delete("own-export") == {"deleted": True}


# -- collisions -------------------------------------------------------------------


def test_a_plugin_cannot_shadow_an_action_the_install_already_stores(data_path, resolvable, writes):
    """[REQ-SB-95-US-02-AC-06]"""
    install(data_path, "reporter", '''
def register(api):
    api.register_action("own-export", description="the plugin's version",
                        implementation={"ui": {"feature_key": "/settings/artifacts"}})
''')
    save_an_own_action()
    PluginManager().load_all()

    catalogue = catalogue_by_id()

    assert len(catalogue) == 1
    assert catalogue["own-export"].description == "The install's own Action"
    assert not hasattr(catalogue["own-export"], "plugin_id")


def test_registering_one_id_twice_disables_the_plugin_rather_than_guessing(data_path, resolvable):
    install(data_path, "reporter", '''
def register(api):
    api.register_action("twice", implementation={"ui": {"feature_key": "/settings/artifacts"}})
    api.register_action("twice", implementation={"ui": {"feature_key": "/settings/artifacts"}})
''')

    PluginManager().load_all()

    [plugin] = PluginManager().get_load_report()
    assert plugin.status == "disabled"
    assert ActionManager().get_all() == []


def test_a_plugin_that_fails_after_registering_contributes_no_action(data_path, resolvable):
    install(data_path, "reporter", '''
def register(api):
    api.register_action("half-registered", implementation={"ui": {"feature_key": "/settings/artifacts"}})
    raise RuntimeError("fails after registering an action")
''')

    PluginManager().load_all()

    assert PluginManager().get_actions() == []
    assert ActionManager().get_all() == []
