"""Registering a tag namespace through the Plugin API (REQ-SB-95-US-05-T02,
AC-08, ADR-037, ADR-022).

A plugin says "I own the `<prefix>/` tag namespace, and here is the function
to ask for my current entries". The whole point is the FUNCTION: the registry
behind it is edited while the app runs, so a list captured at registration
would be stale by lunchtime and would leave the framework holding a copy of
the plugin's own business data. These tests therefore spend most of their
effort on WHEN the callable is called, not on what it returns.

The plugin is a real one written into a temporary App Database Folder, the
technique tests/test_plugin_host.py and tests/test_plugin_actions.py already
use, so registration goes through the real loader and the real facade. Each
fake plugin records its own calls into a file beside its backend, which makes
"it was not called at load time" an assertion about observed behaviour rather
than an absence of evidence.

Two properties are pinned here that are easy to lose later:

- **Registration decorates; it does not gate.** T01's tag-keyed index keys
  every `<namespace>/<slug>` tag the vault holds, registered or not (AC-07),
  and nothing added here may turn that into an allow-list. Proved
  structurally: the module that builds the index imports nothing from the
  plugin host, so it cannot consult a registry it has no way to reach.
- **`FRAMEWORK_API` moves exactly once for all of REQ-SB-95** -- in whichever
  of `register_action` (US-02) and `register_tag_namespace` (US-05) lands
  last, never twice. Pinned by the last test in this file.
"""
import ast
import json
import logging
import textwrap
from pathlib import Path

import pytest

from app import plugin_api
from app.business.core.plugins import plugin_manager as plugin_manager_module
from app.business.core.plugins.plugin_manager import PluginManager
from app.business.core.vault import vault_manager as vault_manager_module
from app.config import settings

A_NAMESPACE = "widget"

# A value the framework has never seen and could not interpret if it tried.
# `kind` is an opaque pass-through string (ADR-037): it carries a separator
# and punctuation on purpose, so anything that parsed, normalised or
# enumerated it would show up as a changed byte.
AN_OPAQUE_KIND = "a kind nobody enumerated :: 42/x"

AN_ENTRY = {
    "slug": "one",
    "name": "The First One",
    "aliases": ["First", "No. 1"],
    "domains": ["first.example"],
    "hub": "Work/Hubs/The First One.md",
    "kind": AN_OPAQUE_KIND,
}
ANOTHER_ENTRY = {
    "slug": "two",
    "name": "The Second One",
    "aliases": [],
    "domains": [],
    "hub": "Work/Hubs/The Second One.md",
    "kind": AN_OPAQUE_KIND,
}

_RECORDING_BACKEND = '''
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CALLS = HERE / "calls.json"
ENTRIES = HERE / "entries.json"


def register(api):
    def entries():
        asked = json.loads(CALLS.read_text(encoding="utf-8")) if CALLS.is_file() else []
        asked.append("asked")
        CALLS.write_text(json.dumps(asked), encoding="utf-8")
        return json.loads(ENTRIES.read_text(encoding="utf-8"))

    api.register_tag_namespace("widget", entries)
'''

_CLAIMING_BACKEND = '''
def register(api):
    def entries():
        return [{"slug": api.plugin_id, "name": api.plugin_id, "aliases": [],
                 "domains": [], "hub": "", "kind": "whatever"}]

    api.register_tag_namespace("widget", entries)
'''


@pytest.fixture(autouse=True)
def data_path(tmp_path, monkeypatch) -> Path:
    """This file's own App Database Folder. tests/conftest.py sandboxes the
    Hermes install and nothing else, so without this the loader would read the
    operator's real installed plugins -- and the real ones would then be the
    namespaces under assertion."""
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path)
    return tmp_path


@pytest.fixture(autouse=True)
def leaves_no_loaded_plugin_behind(monkeypatch):
    """`load_all()` writes module-level state that outlives one test, the way
    VaultManager's index does. Restored so a plugin installed in a temporary
    folder can never be seen by a later test pointing at the real install."""
    monkeypatch.setattr(plugin_manager_module, "_plugin_tag_namespaces", dict(plugin_manager_module._plugin_tag_namespaces))
    monkeypatch.setattr(plugin_manager_module, "_load_report", list(plugin_manager_module._load_report))


def install(data_path: Path, plugin_id: str, backend: str) -> Path:
    folder = data_path / "plugins" / plugin_id
    (folder / "backend").mkdir(parents=True)
    (folder / "plugin.json").write_text(json.dumps({
        "id": plugin_id, "name": plugin_id.title(), "version": "0.1.0",
        "framework_api": plugin_api.FRAMEWORK_API, "requires": [],
    }), encoding="utf-8")
    (folder / "backend" / "__init__.py").write_text(textwrap.dedent(backend), encoding="utf-8")

    record_path = data_path / "plugins" / "installed.json"
    record = json.loads(record_path.read_text(encoding="utf-8")) if record_path.is_file() else {"plugins": []}
    record["plugins"].append({"id": plugin_id, "version": "0.1.0"})
    record_path.write_text(json.dumps(record), encoding="utf-8")
    return folder


def set_entries(data_path: Path, plugin_id: str, entries: list[dict]) -> None:
    """What the plugin's registry holds at this moment -- rewritten between
    reads the way an operator edits one while the app runs."""
    path = data_path / "plugins" / plugin_id / "backend" / "entries.json"
    path.write_text(json.dumps(entries), encoding="utf-8")


def times_asked(data_path: Path, plugin_id: str) -> int:
    path = data_path / "plugins" / plugin_id / "backend" / "calls.json"
    return len(json.loads(path.read_text(encoding="utf-8"))) if path.is_file() else 0


def registrations() -> list[dict]:
    return PluginManager().get_tag_namespaces()


# -- a callable, stored and attributed, never called at registration -------------


def test_a_registered_namespace_is_attributed_and_its_callable_is_not_asked_until_needed(data_path):
    """[REQ-SB-95-US-05-AC-08]"""
    install(data_path, "first-owner", _RECORDING_BACKEND)
    set_entries(data_path, "first-owner", [AN_ENTRY])

    PluginManager().load_all()

    [registration] = registrations()
    assert registration["namespace"] == A_NAMESPACE
    assert registration["plugin_id"] == "first-owner"
    assert callable(registration["entries"])
    # Loading the plugin ran its `register`, which stored the callable. Asking
    # it anything at that point is what ADR-037 forbids.
    assert times_asked(data_path, "first-owner") == 0

    assert registration["entries"]() == [AN_ENTRY]
    assert times_asked(data_path, "first-owner") == 1


def test_each_read_sees_the_registry_as_it_is_now_not_as_it_was_at_load(data_path):
    """[REQ-SB-95-US-05-AC-08]"""
    install(data_path, "first-owner", _RECORDING_BACKEND)
    set_entries(data_path, "first-owner", [AN_ENTRY])
    PluginManager().load_all()
    [registration] = registrations()

    before = registration["entries"]()
    set_entries(data_path, "first-owner", [AN_ENTRY, ANOTHER_ENTRY])
    after = registration["entries"]()

    assert before == [AN_ENTRY]
    assert after == [AN_ENTRY, ANOTHER_ENTRY]
    assert times_asked(data_path, "first-owner") == 2


def test_a_plugin_that_fails_after_registering_owns_no_namespace(data_path):
    """[REQ-SB-95-US-05-AC-08]"""
    install(data_path, "flaky", '''
def register(api):
    api.register_tag_namespace("widget", lambda: [])
    raise RuntimeError("fails after registering a namespace")
''')

    PluginManager().load_all()

    assert registrations() == []


def test_reloading_does_not_duplicate_a_registered_namespace(data_path):
    """[REQ-SB-95-US-05-AC-08]"""
    install(data_path, "first-owner", _CLAIMING_BACKEND)

    PluginManager().load_all()
    PluginManager().load_all()

    assert len(registrations()) == 1


# -- one namespace, one owner ----------------------------------------------------


def test_a_second_plugin_claiming_the_same_prefix_is_refused_naming_both(data_path, caplog):
    """[REQ-SB-95-US-05-AC-08]"""
    install(data_path, "first-owner", _CLAIMING_BACKEND)
    install(data_path, "late-comer", _CLAIMING_BACKEND)

    with caplog.at_level(logging.WARNING):
        PluginManager().load_all()

    [registration] = registrations()
    assert registration["plugin_id"] == "first-owner"
    assert registration["entries"]()[0]["slug"] == "first-owner"
    refusal = "\n".join(record.getMessage() for record in caplog.records)
    assert "first-owner" in refusal and "late-comer" in refusal and A_NAMESPACE in refusal


def test_one_plugin_claiming_the_same_prefix_twice_is_disabled_rather_than_guessed_at(data_path):
    """[REQ-SB-95-US-05-AC-08]"""
    install(data_path, "first-owner", '''
def register(api):
    api.register_tag_namespace("widget", lambda: [])
    api.register_tag_namespace("widget", lambda: [])
''')

    PluginManager().load_all()

    [plugin] = PluginManager().get_load_report()
    assert plugin.status == "disabled"
    assert registrations() == []


def test_entries_given_as_data_instead_of_a_callable_is_refused(data_path):
    """[REQ-SB-95-US-05-AC-08]"""
    install(data_path, "snapshotter", '''
def register(api):
    api.register_tag_namespace("widget", [{"slug": "one", "name": "The First One"}])
''')

    PluginManager().load_all()

    [plugin] = PluginManager().get_load_report()
    assert plugin.status == "disabled"
    assert "callable" in plugin.reason
    assert registrations() == []


@pytest.mark.parametrize("namespace", ["", "   ", "/", "a/b", "a\\b"])
def test_a_namespace_that_is_not_one_prefix_is_refused(data_path, namespace):
    """[REQ-SB-95-US-05-AC-08]"""
    install(data_path, "confused", f'''
def register(api):
    api.register_tag_namespace({namespace!r}, lambda: [])
''')

    PluginManager().load_all()

    assert PluginManager().get_load_report()[0].status == "disabled"
    assert registrations() == []


def test_a_prefix_registered_with_its_separator_is_the_same_prefix(data_path):
    """[REQ-SB-95-US-05-AC-08]"""
    install(data_path, "first-owner", '''
def register(api):
    api.register_tag_namespace("widget/", lambda: [])
''')

    PluginManager().load_all()

    assert [registration["namespace"] for registration in registrations()] == [A_NAMESPACE]


# -- the facade rule: plain data only, `kind` opaque -----------------------------


def test_only_plain_data_and_one_callable_cross_the_seam(data_path):
    """[REQ-SB-95-US-05-AC-08]"""
    install(data_path, "first-owner", _RECORDING_BACKEND)
    set_entries(data_path, "first-owner", [AN_ENTRY])
    PluginManager().load_all()

    [registration] = registrations()
    [entry] = registration["entries"]()

    assert type(registration["namespace"]) is str and type(registration["plugin_id"]) is str
    assert callable(registration["entries"])
    assert set(registration) == {"namespace", "plugin_id", "entries"}
    # No framework entity class anywhere in the answer: a plugin holding one
    # would break the moment the framework changed a field on it, while its
    # `framework_api` still matched.
    assert type(entry) is dict
    assert all(type(value) in (str, list) for value in entry.values())
    assert all(type(item) is str for value in entry.values() if type(value) is list for item in value)


def test_kind_is_carried_through_byte_identically(data_path):
    """[REQ-SB-95-US-05-AC-08]"""
    install(data_path, "first-owner", _RECORDING_BACKEND)
    set_entries(data_path, "first-owner", [AN_ENTRY])
    PluginManager().load_all()

    [entry] = registrations()[0]["entries"]()

    assert entry["kind"] == AN_OPAQUE_KIND
    # Not merely equal: nothing split it on its separator, trimmed it, cased
    # it or mapped it onto a framework concept.
    assert entry["kind"].encode("utf-8") == AN_OPAQUE_KIND.encode("utf-8")


def test_the_facade_names_no_plugin_and_enumerates_no_kind():
    """[REQ-SB-95-US-05-AC-08]

    ADR-022's CFO test as a check rather than an intention: a framework that
    shipped a list of valid namespaces or kinds would be naming one install's
    business vocabulary."""
    facade = Path(plugin_api.__file__).read_text(encoding="utf-8")
    host = Path(plugin_manager_module.__file__).read_text(encoding="utf-8")
    namespace_code = [
        facade.split("def register_tag_namespace")[1].split("\n    def ")[0],
        host.split("def _one_owner_per_tag_namespace")[1].split("\n\n\n")[0],
        host.split("def get_tag_namespaces")[1].split("\n    def ")[0],
    ]

    for forbidden in ("customer", "partner", "entities"):
        assert not [piece for piece in namespace_code if forbidden in piece.lower()]


# -- registration decorates, it does not gate ------------------------------------


def test_registration_cannot_filter_the_tag_keyed_index(data_path):
    """[REQ-SB-95-US-05-AC-08]

    AC-07 keeps every `<namespace>/<slug>` tag in the vault as a key whether
    or not a plugin claimed its prefix -- true on an install with no plugins
    at all. The way that stays true under a registration mechanism is for the
    module that builds the index to have no way to reach the registry: it
    imports nothing from the plugin host, so there is nothing for an
    allow-list to be consulted through."""
    tree = ast.parse(Path(vault_manager_module.__file__).read_text(encoding="utf-8"))

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
            imported.update(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)

    assert not [name for name in imported if "plugin" in name]
