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
