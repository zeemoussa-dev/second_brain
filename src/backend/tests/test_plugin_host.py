"""Plugin host, backend half (`ADR-022`, `REQ-SB-91` Phase 1).

Every plugin here is written into a temporary App Database Folder, so nothing
touches the real install. The host is exercised through PluginManager and a
bare FastAPI app rather than `app.main`'s lifespan, whose other startup work
(Registry boot, a full vault index rebuild) reads the real vault.
"""
import importlib.util
import json
import textwrap
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import plugin_api
from app.business.core.plugins.plugin_manager import PluginManager
from app.business.logic import system_health
from app.config import settings

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_plugin_imports.py"
_spec = importlib.util.spec_from_file_location("check_plugin_imports", _SCRIPT)
check_plugin_imports = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_plugin_imports)

_WORKING_BACKEND = '''
from fastapi import APIRouter

from . import greeting


def register(api):
    router = APIRouter()

    @router.get("/ping")
    def ping():
        return {"plugin": api.plugin_id, "message": greeting.MESSAGE}

    api.register_router(router)
'''


@pytest.fixture()
def data_path(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path)
    return tmp_path


def install(data_path: Path, plugin_id: str, *, backend: str = _WORKING_BACKEND,
            framework_api=None, manifest_id: str | None = None) -> Path:
    folder = data_path / "plugins" / plugin_id
    (folder / "backend").mkdir(parents=True)
    manifest = {
        "id": manifest_id or plugin_id, "name": plugin_id.title(), "version": "0.1.0",
        "framework_api": plugin_api.FRAMEWORK_API if framework_api is None else framework_api,
        "requires": [],
    }
    (folder / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
    (folder / "backend" / "__init__.py").write_text(textwrap.dedent(backend), encoding="utf-8")
    (folder / "backend" / "greeting.py").write_text('MESSAGE = "pong"\n', encoding="utf-8")
    record_record(data_path, {"id": plugin_id, "version": "0.1.0"})
    return folder


def record_record(data_path: Path, entry: dict) -> None:
    record_path = data_path / "plugins" / "installed.json"
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record = json.loads(record_path.read_text(encoding="utf-8")) if record_path.is_file() else {"plugins": []}
    record["plugins"].append(entry)
    record_path.write_text(json.dumps(record), encoding="utf-8")


def app_with(mounts) -> TestClient:
    app = FastAPI()
    for prefix, router in mounts:
        app.include_router(router, prefix=prefix)
    return TestClient(app)


def report_by_id() -> dict:
    return {plugin.id: plugin for plugin in PluginManager().get_load_report()}


# -- loading -------------------------------------------------------------------


def test_no_plugins_installed_loads_nothing(data_path):
    assert PluginManager().load_all() == []
    assert PluginManager().get_load_report() == []


def test_a_plugin_is_loaded_and_its_routes_are_mounted_under_its_id(data_path):
    install(data_path, "hello")

    client = app_with(PluginManager().load_all())

    # The plugin's own relative import (`from . import greeting`) resolved,
    # which is what lets a real plugin be more than one file.
    assert client.get("/plugins/hello/ping").json() == {"plugin": "hello", "message": "pong"}
    assert report_by_id()["hello"].status == "loaded"
    assert report_by_id()["hello"].routes_prefix == "/plugins/hello"


def test_a_framework_api_mismatch_is_refused_before_any_of_its_code_runs(data_path):
    install(data_path, "old", framework_api=plugin_api.FRAMEWORK_API + 1,
            backend='raise RuntimeError("a refused plugin must never be imported")\n')

    mounts = PluginManager().load_all()

    assert mounts == []
    refused = report_by_id()["old"]
    assert refused.status == "refused"
    assert str(plugin_api.FRAMEWORK_API) in refused.reason


def test_a_plugin_that_fails_is_disabled_and_the_others_still_load(data_path):
    install(data_path, "broken", backend='def register(api):\n    raise ValueError("boom")\n')
    install(data_path, "hello")

    client = app_with(PluginManager().load_all())

    assert report_by_id()["broken"].status == "disabled"
    assert "boom" in report_by_id()["broken"].reason
    assert client.get("/plugins/hello/ping").status_code == 200


def test_a_plugin_without_a_register_function_is_disabled(data_path):
    install(data_path, "empty", backend="VALUE = 1\n")

    PluginManager().load_all()

    assert report_by_id()["empty"].status == "disabled"
    assert "register" in report_by_id()["empty"].reason


def test_an_id_that_could_escape_the_plugins_folder_is_rejected(data_path):
    record_record(data_path, {"id": "../escape", "version": "1"})

    PluginManager().load_all()

    assert report_by_id()["../escape"].status == "invalid"


def test_a_manifest_naming_a_different_id_is_invalid(data_path):
    install(data_path, "hello", manifest_id="someone-else")

    assert PluginManager().load_all() == []
    assert report_by_id()["hello"].status == "invalid"


def test_a_plugin_recorded_twice_loads_once(data_path):
    install(data_path, "hello")
    record_record(data_path, {"id": "hello", "version": "0.1.0"})

    mounts = PluginManager().load_all()

    assert len(mounts) == 1
    statuses = [plugin.status for plugin in PluginManager().get_load_report()]
    assert statuses == ["loaded", "invalid"]


def test_a_corrupt_ownership_record_is_reported_not_read_as_empty(data_path):
    record_path = data_path / "plugins" / "installed.json"
    record_path.parent.mkdir(parents=True)
    record_path.write_text("{ not json", encoding="utf-8")

    assert PluginManager().load_all() == []
    report = PluginManager().get_load_report()
    assert len(report) == 1 and report[0].status == "invalid"


def test_system_health_lists_what_the_host_did(data_path):
    install(data_path, "hello")
    install(data_path, "old", framework_api=plugin_api.FRAMEWORK_API + 1)
    PluginManager().load_all()

    plugins = {p["id"]: p for p in system_health.get_system_health()["plugins"]}

    assert plugins["hello"]["status"] == "loaded"
    assert plugins["old"]["status"] == "refused"
    assert plugins["old"]["reason"]


# -- the import boundary -------------------------------------------------------


def write_module(folder: Path, source: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "module.py"
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    return folder


def test_a_plugin_may_import_the_facade(tmp_path):
    folder = write_module(tmp_path / "ok", """
        from app import plugin_api
        from app.plugin_api import FRAMEWORK_API
        import app.plugin_api
        from . import sibling
        import json
    """)

    assert check_plugin_imports.check_plugin(folder) == []


def test_a_plugin_reaching_past_the_facade_is_rejected(tmp_path):
    folder = write_module(tmp_path / "bad", """
        from app.business.core.vault.vault_manager import VaultManager
        from app import config
    """)

    violations = check_plugin_imports.check_plugin(folder)

    assert len(violations) == 2
    assert "vault_manager" in violations[0]


def test_a_plugin_importing_another_plugin_is_rejected(tmp_path):
    folder = write_module(tmp_path / "bad", "import sb_plugins_entities\n")

    assert len(check_plugin_imports.check_plugin(folder)) == 1


def test_core_importing_a_plugin_is_rejected(tmp_path):
    folder = write_module(tmp_path / "core", "from sb_plugins_my_day import register\n")

    assert len(check_plugin_imports.check_core(folder)) == 1


def test_the_framework_itself_imports_no_plugin():
    app_dir = Path(__file__).resolve().parents[1] / "app"

    assert check_plugin_imports.check_core(app_dir) == []


# -- the Cockpit subject-enricher seam (BUG-063) ---------------------------------


_ENRICHING_BACKEND = '''
def register(api):
    def add_owner(subject_kind, frontmatter, tags):
        return {"owner": f"{subject_kind}:{len(tags)}"}

    api.register_subject_enricher(add_owner)
'''

_FAILS_AFTER_REGISTERING_BACKEND = '''
def register(api):
    api.register_subject_enricher(lambda kind, frontmatter, tags: {"leaked": True})
    raise RuntimeError("fails after registering an enricher")
'''


def test_a_loaded_plugin_contributes_its_subject_enrichers(data_path):
    install(data_path, "owners", backend=_ENRICHING_BACKEND)

    PluginManager().load_all()
    enrichers = PluginManager().get_subject_enrichers()

    assert len(enrichers) == 1
    assert enrichers[0]("meeting", {}, ["a", "b"]) == {"owner": "meeting:2"}


def test_a_plugin_that_fails_after_registering_contributes_no_enricher(data_path):
    install(data_path, "flaky", backend=_FAILS_AFTER_REGISTERING_BACKEND)

    PluginManager().load_all()

    assert report_by_id()["flaky"].status == "disabled"
    assert PluginManager().get_subject_enrichers() == []


_MATCHING_AND_SERVING_BACKEND = '''
def register(api):
    api.register_agent_matcher(lambda kind, subject: {"experts": ["x-expert"]})
    api.provide_service(api.plugin_id + ".lookup", lambda value: value.upper())
'''

_ASKING_BACKEND = '''
from fastapi import APIRouter


def register(api):
    router = APIRouter()

    @router.get("/ask")
    def ask():
        lookup = api.get_service("provider.lookup")
        return {"answer": lookup("hi") if lookup else None}

    api.register_router(router)
'''


def test_a_loaded_plugin_contributes_agent_matchers_and_services(data_path):
    install(data_path, "provider", backend=_MATCHING_AND_SERVING_BACKEND)

    PluginManager().load_all()

    [matcher] = PluginManager().get_agent_matchers()
    assert matcher("email", {}) == {"experts": ["x-expert"]}
    assert PluginManager().get_service("provider.lookup")("hi") == "HI"


def test_a_plugin_reaches_another_plugins_service_whatever_the_install_order(data_path):
    install(data_path, "asker", backend=_ASKING_BACKEND)
    install(data_path, "provider", backend=_MATCHING_AND_SERVING_BACKEND)

    client = app_with(PluginManager().load_all())

    assert client.get("/plugins/asker/ask").json() == {"answer": "HI"}


def test_a_missing_service_is_none_not_an_error(data_path):
    install(data_path, "asker", backend=_ASKING_BACKEND)

    client = app_with(PluginManager().load_all())

    assert client.get("/plugins/asker/ask").json() == {"answer": None}


@pytest.mark.parametrize("name", ["other.lookup", "lookup", "provider.", "providerx.lookup"])
def test_a_service_must_be_named_under_the_plugins_own_id(data_path, name):
    backend = f'''
def register(api):
    api.provide_service({name!r}, object())
'''
    install(data_path, "provider", backend=backend)

    PluginManager().load_all()

    assert report_by_id()["provider"].status == "disabled"
    assert PluginManager().get_service(name) is None


def test_a_plugin_that_fails_after_registering_contributes_no_matcher_or_service(data_path):
    backend = '''
def register(api):
    api.register_agent_matcher(lambda kind, subject: {})
    api.provide_service("flaky.lookup", object())
    raise RuntimeError("fails after registering")
'''
    install(data_path, "flaky", backend=backend)

    PluginManager().load_all()

    assert PluginManager().get_agent_matchers() == []
    assert PluginManager().get_service("flaky.lookup") is None


def test_plugins_register_people_folders_combined_without_duplicates(data_path):
    for plugin_id, folders in (("first", ["Work/Customers", "Work\\\\Partners"]), ("second", ["Work/Partners/"])):
        install(data_path, plugin_id, backend=f'''
def register(api):
    api.register_people_folders({folders!r})
''')

    PluginManager().load_all()

    assert PluginManager().get_people_folders() == ["Work/Customers", "Work/Partners"]


@pytest.mark.parametrize("folder", ["../outside", "/Work/Customers", "C:/Work", ""])
def test_a_people_folder_outside_the_vault_is_refused(data_path, folder):
    install(data_path, "escaper", backend=f'''
def register(api):
    api.register_people_folders([{folder!r}])
''')

    PluginManager().load_all()

    assert report_by_id()["escaper"].status == "disabled"
    assert PluginManager().get_people_folders() == []


def test_a_plugin_registers_its_seed_data_files(data_path):
    install(data_path, "stores", backend='''
def register(api):
    api.register_seed_data_file("Settings/Stores.md")
    api.register_seed_data_file("Settings\\\\Stores.md")
''')

    PluginManager().load_all()

    assert PluginManager().get_seed_data_files() == ["Settings/Stores.md"]


@pytest.mark.parametrize("path", ["../Stores.md", "/etc/passwd", "C:/Stores.md", " "])
def test_a_seed_data_file_outside_the_data_folder_is_refused(data_path, path):
    install(data_path, "escaper", backend=f'''
def register(api):
    api.register_seed_data_file({path!r})
''')

    PluginManager().load_all()

    assert report_by_id()["escaper"].status == "disabled"
    assert PluginManager().get_seed_data_files() == []


_DATA_FILE_BACKEND = '''
from fastapi import APIRouter


def register(api):
    api.register_seed_data_file("Settings/Stores.md")
    router = APIRouter()

    @router.post("/write")
    def write():
        api.data.write_text("Settings/Stores.md", "### Store\\n")
        return {"read": api.data.read_text("Settings/Stores.md")}

    @router.get("/unregistered")
    def unregistered():
        try:
            api.data.read_text("Settings/Entities.md")
        except PermissionError as exc:
            return {"refused": str(exc)}
        return {"refused": None}

    api.register_router(router)
'''


def test_a_plugin_reads_and_writes_only_its_own_registered_data_files(data_path):
    install(data_path, "stores", backend=_DATA_FILE_BACKEND)

    client = app_with(PluginManager().load_all())

    assert client.post("/plugins/stores/write").json() == {"read": "### Store\n"}
    assert (data_path / "Settings" / "Stores.md").read_text(encoding="utf-8") == "### Store\n"
    assert "not a data file this plugin registered" in client.get("/plugins/stores/unregistered").json()["refused"]


def test_reloading_does_not_duplicate_a_plugins_enrichers(data_path):
    install(data_path, "owners", backend=_ENRICHING_BACKEND)

    PluginManager().load_all()
    PluginManager().load_all()

    assert len(PluginManager().get_subject_enrichers()) == 1
