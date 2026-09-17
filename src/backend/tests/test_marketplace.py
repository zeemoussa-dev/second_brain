"""The Marketplace (`ADR-022`, `REQ-SB-91` Phase 4a): installing and
uninstalling published plugin packages.

Every root is redirected into a temporary folder -- the Marketplace, the
install's config folder and the frontend's `src/plugins/` -- so nothing touches
the real checkout or install. The install tests end by loading the plugin
through the real plugin host, which is the point of installing it.
"""
import json
import textwrap
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import plugin_api
from app.business.core.marketplace.marketplace_manager import MarketplaceManager
from app.business.core.plugins.plugin_manager import PluginManager
from app.config import settings
from app.data_access import marketplace as marketplace_data
from app.data_access import plugins as plugins_data
from app.data_access import skills as skills_data

_BACKEND = '''
from fastapi import APIRouter


def register(api):
    router = APIRouter()

    @router.get("/version")
    def version():
        return {"version": VERSION}

    api.register_router(router)


VERSION = "{version}"
'''


@pytest.fixture()
def roots(tmp_path, monkeypatch):
    marketplace = tmp_path / "marketplace"
    config = tmp_path / "config"
    frontend_plugins = tmp_path / "frontend-plugins"
    monkeypatch.setattr(settings, "second_brain_data_path", config)
    monkeypatch.setattr(marketplace_data, "_MARKETPLACE_ROOT", marketplace)
    monkeypatch.setattr(marketplace_data, "_FRONTEND_PLUGINS_ROOT", frontend_plugins)
    monkeypatch.setattr(skills_data, "list_categories", lambda: ["graph", "vault"])
    return {"marketplace": marketplace, "config": config, "frontend_plugins": frontend_plugins}


def publish(roots, plugin_id="my-day", version="1.0.0", *, framework_api=None, requires=None,
            manifest_id=None, manifest_version=None, with_ui=True, templates=None) -> Path:
    package = roots["marketplace"] / plugin_id / version
    (package / "backend").mkdir(parents=True)
    manifest = {
        "id": manifest_id or plugin_id, "name": "My Day", "description": "Your day.",
        "version": manifest_version or version,
        "framework_api": plugin_api.FRAMEWORK_API if framework_api is None else framework_api,
        "requires": requires if requires is not None else ["graph|outlook"],
    }
    (package / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
    (package / "backend" / "__init__.py").write_text(
        textwrap.dedent(_BACKEND).replace("{version}", version), encoding="utf-8")
    if with_ui:
        (package / "ui").mkdir()
        (package / "ui" / "index.tsx").write_text("export default {};\n", encoding="utf-8")
    for template_id, data in (templates or {}).items():
        (package / "templates" / template_id).mkdir(parents=True)
        (package / "templates" / template_id / "Template.json").write_text(json.dumps(data), encoding="utf-8")
    return package


def install_template(roots, template_id: str, data: dict) -> Path:
    """A Template already on the install, as seeding or the operator left it."""
    path = roots["config"] / "data" / "Templates" / template_id / "Template.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


_CLIENT_TEMPLATE = {"id": "client", "version": 1, "sections": []}
_OPERATOR_EDITED_TEMPLATE = {"id": "client", "version": 1, "sections": [], "note": "operator edit"}


def installed_record(roots) -> dict:
    return json.loads((roots["config"] / "plugins" / "installed.json").read_text(encoding="utf-8"))


def work_entries(roots) -> list[str]:
    """What is waiting in the Marketplace's work folders: staging copies and replaced pieces."""
    entries = []
    for root in (roots["config"] / "plugins", roots["frontend_plugins"]):
        work = root / ".marketplace-work"
        if work.is_dir():
            entries.extend(entry.name for entry in work.iterdir())
    return entries


def refuse_to_move(monkeypatch, locked: Path) -> None:
    """Makes one installed piece behave as if something held a file in it open."""
    real_move_aside = marketplace_data.move_aside

    def move_aside(path):
        if Path(path) == locked:
            raise PermissionError(13, "Access is denied", str(path))
        return real_move_aside(path)

    monkeypatch.setattr(marketplace_data, "move_aside", move_aside)


# -- listing and preflight -------------------------------------------------------


def test_the_catalog_lists_versions_newest_first_with_compatibility(roots):
    publish(roots, version="1.0.0")
    publish(roots, version="1.10.0")
    publish(roots, version="1.2.0", framework_api=plugin_api.FRAMEWORK_API + 1)

    [entry] = MarketplaceManager().get_all()

    assert entry["id"] == "my-day"
    assert [p["version"] for p in entry["packages"]] == ["1.10.0", "1.2.0", "1.0.0"]
    assert [p["compatible"] for p in entry["packages"]] == [True, False, True]
    assert entry["installed_version"] is None


def test_preflight_passes_for_a_compatible_package(roots):
    publish(roots)

    check = MarketplaceManager().preflight("my-day", "1.0.0")

    assert check["ok"] is True
    assert check["problems"] == []


@pytest.mark.parametrize("kwargs, expected", [
    ({"framework_api": plugin_api.FRAMEWORK_API + 1}, "framework API"),
    ({"requires": ["outlook"]}, "requires outlook"),
    ({"manifest_id": "someone-else"}, "declares id"),
    ({"manifest_version": "9.9.9"}, "declares version"),
])
def test_preflight_names_what_would_stop_the_install(roots, kwargs, expected):
    publish(roots, **kwargs)

    check = MarketplaceManager().preflight("my-day", "1.0.0")

    assert check["ok"] is False
    assert any(expected in problem for problem in check["problems"])


def test_a_requirement_with_alternatives_is_met_by_either(roots, monkeypatch):
    monkeypatch.setattr(skills_data, "list_categories", lambda: ["outlook"])
    publish(roots, requires=["graph|outlook"])

    assert MarketplaceManager().preflight("my-day", "1.0.0")["ok"] is True


# -- install ------------------------------------------------------------------------


def test_install_places_the_pieces_records_ownership_and_the_host_loads_it(roots):
    publish(roots)

    result = MarketplaceManager().install("my-day", "1.0.0")

    assert result["installed"] is True
    assert result["restart_required"] is True
    assert (roots["config"] / "plugins" / "my-day" / "plugin.json").is_file()
    assert (roots["config"] / "plugins" / "my-day" / "backend" / "__init__.py").is_file()
    assert (roots["frontend_plugins"] / "my-day" / "index.tsx").is_file()
    [entry] = installed_record(roots)["plugins"]
    assert entry["id"] == "my-day" and entry["version"] == "1.0.0"
    assert len(entry["owned"]) == 2

    mounts = PluginManager().load_all()
    assert [prefix for prefix, _ in mounts] == ["/plugins/my-day"]


def test_a_refused_install_writes_nothing(roots):
    publish(roots, framework_api=plugin_api.FRAMEWORK_API + 1)

    result = MarketplaceManager().install("my-day", "1.0.0")

    assert result["installed"] is False
    assert not (roots["config"] / "plugins").exists()
    assert not roots["frontend_plugins"].exists()


def test_installing_another_version_replaces_the_installed_one(roots):
    publish(roots, version="1.0.0")
    publish(roots, version="1.1.0")
    MarketplaceManager().install("my-day", "1.0.0")

    result = MarketplaceManager().install("my-day", "1.1.0")

    assert result["installed"] is True
    assert result["replaced"] == "1.0.0"
    assert [e["version"] for e in installed_record(roots)["plugins"]] == ["1.1.0"]
    backend = (roots["config"] / "plugins" / "my-day" / "backend" / "__init__.py").read_text(encoding="utf-8")
    assert 'VERSION = "1.1.0"' in backend


def test_installing_the_same_version_twice_is_refused(roots):
    publish(roots)
    MarketplaceManager().install("my-day", "1.0.0")

    result = MarketplaceManager().install("my-day", "1.0.0")

    assert result["installed"] is False
    assert any("already installed" in problem for problem in result["problems"])


# BUG-065: replacing a version deleted the installed backend file by file, so a
# __pycache__ held open by OneDrive stopped it half-way -- modules gone, record
# still naming the old version, and a 500.


def test_a_version_that_cannot_be_moved_aside_stays_installed_and_whole(roots, monkeypatch):
    publish(roots, version="1.0.0")
    publish(roots, version="1.1.0")
    MarketplaceManager().install("my-day", "1.0.0")
    # The screens are moved after the backend, so this also puts the backend back.
    refuse_to_move(monkeypatch, roots["frontend_plugins"] / "my-day")

    result = MarketplaceManager().install("my-day", "1.1.0")

    assert result["installed"] is False
    assert any("could not be replaced, so nothing was changed" in problem for problem in result["problems"])
    backend = (roots["config"] / "plugins" / "my-day" / "backend" / "__init__.py").read_text(encoding="utf-8")
    assert 'VERSION = "1.0.0"' in backend
    assert (roots["frontend_plugins"] / "my-day" / "index.tsx").is_file()
    assert [e["version"] for e in installed_record(roots)["plugins"]] == ["1.0.0"]
    assert work_entries(roots) == []
    assert [prefix for prefix, _ in PluginManager().load_all()] == ["/plugins/my-day"]


def test_a_replaced_version_that_cannot_be_deleted_does_not_fail_the_install(roots, monkeypatch):
    publish(roots, version="1.0.0")
    publish(roots, version="1.1.0")
    MarketplaceManager().install("my-day", "1.0.0")
    deleting = {"allowed": False}
    real_rmtree = marketplace_data.shutil.rmtree

    def rmtree(path, *args, **kwargs):
        if deleting["allowed"]:
            return real_rmtree(path, *args, **kwargs)
        return None

    monkeypatch.setattr(marketplace_data.shutil, "rmtree", rmtree)

    result = MarketplaceManager().install("my-day", "1.1.0")

    assert result["installed"] is True
    backend = (roots["config"] / "plugins" / "my-day" / "backend" / "__init__.py").read_text(encoding="utf-8")
    assert 'VERSION = "1.1.0"' in backend
    assert len(result["leftovers"]) == 2 and len(work_entries(roots)) == 2

    deleting["allowed"] = True
    MarketplaceManager().uninstall("my-day")

    assert work_entries(roots) == []


def test_install_repairs_a_plugin_left_with_only_its_bytecode_cache(roots):
    publish(roots, version="1.0.0")
    publish(roots, version="1.1.0")
    MarketplaceManager().install("my-day", "1.0.0")
    backend = roots["config"] / "plugins" / "my-day" / "backend"
    (backend / "__init__.py").unlink()
    (backend / "__pycache__").mkdir(exist_ok=True)
    (backend / "__pycache__" / "__init__.cpython-311.pyc").write_bytes(b"")

    result = MarketplaceManager().install("my-day", "1.1.0")

    assert result["installed"] is True
    assert 'VERSION = "1.1.0"' in (backend / "__init__.py").read_text(encoding="utf-8")
    assert not (backend / "__pycache__").exists()
    assert [prefix for prefix, _ in PluginManager().load_all()] == ["/plugins/my-day"]


def test_the_plugin_host_writes_no_bytecode_into_the_config_folder(roots):
    publish(roots)
    MarketplaceManager().install("my-day", "1.0.0")

    PluginManager().load_all()

    assert list((roots["config"] / "plugins").rglob("__pycache__")) == []


# -- Templates layer (Entities plan Phase 2) ----------------------------------------------


def test_preflight_says_which_templates_it_would_install_and_which_it_keeps(roots):
    publish(roots, templates={"client": _CLIENT_TEMPLATE, "contract": {"id": "contract", "sections": []}})
    install_template(roots, "contract", {"id": "contract", "sections": []})

    check = MarketplaceManager().preflight("my-day", "1.0.0")

    assert check["ok"] is True
    assert check["templates"] == {"install": ["client"], "keep": ["contract"]}


@pytest.mark.parametrize("template_id, data, expected", [
    ("client", {"id": "client", "sections": "not a list"}, "not valid on this framework"),
    ("client", {"id": "someone-else", "sections": []}, "declares id"),
    ("client", ["not", "an", "object"], "not a JSON object"),
    ("Bad_Id", {"sections": []}, "not a valid Template id"),
])
def test_preflight_refuses_a_package_with_an_invalid_template(roots, template_id, data, expected):
    publish(roots, templates={template_id: data})

    check = MarketplaceManager().preflight("my-day", "1.0.0")

    assert check["ok"] is False
    assert any(expected in problem for problem in check["problems"])


def test_install_writes_missing_templates_and_never_overwrites_an_existing_one(roots):
    publish(roots, templates={"client": _CLIENT_TEMPLATE, "contract": {"id": "contract", "sections": []}})
    existing = install_template(roots, "client", _OPERATOR_EDITED_TEMPLATE)

    result = MarketplaceManager().install("my-day", "1.0.0")

    assert result["installed"] is True
    assert result["templates"] == {"installed": ["contract"], "kept": ["client"]}
    assert json.loads(existing.read_text(encoding="utf-8")) == _OPERATOR_EDITED_TEMPLATE
    assert (roots["config"] / "data" / "Templates" / "contract" / "Template.json").is_file()
    assert installed_record(roots)["plugins"][0]["templates"] == ["client", "contract"]


def test_uninstall_leaves_the_templates_in_place(roots):
    publish(roots, templates={"client": _CLIENT_TEMPLATE})
    MarketplaceManager().install("my-day", "1.0.0")

    result = MarketplaceManager().uninstall("my-day")

    assert result["templates_left_in_place"] == ["client"]
    assert (roots["config"] / "data" / "Templates" / "client" / "Template.json").is_file()


# -- uninstall ----------------------------------------------------------------------


def test_uninstall_removes_what_it_owns_and_the_host_no_longer_loads_it(roots):
    publish(roots)
    MarketplaceManager().install("my-day", "1.0.0")

    result = MarketplaceManager().uninstall("my-day")

    assert result["uninstalled"] is True
    assert not (roots["config"] / "plugins" / "my-day").exists()
    assert not (roots["frontend_plugins"] / "my-day").exists()
    assert installed_record(roots)["plugins"] == []
    assert PluginManager().load_all() == []


def test_uninstall_never_deletes_outside_the_plugin_folders(roots, tmp_path):
    publish(roots)
    MarketplaceManager().install("my-day", "1.0.0")
    precious = tmp_path / "precious"
    precious.mkdir()
    (precious / "note.md").write_text("the operator's data", encoding="utf-8")
    record = installed_record(roots)
    record["plugins"][0]["owned"].append(str(precious))
    plugins_data.write_installed_record(record)

    result = MarketplaceManager().uninstall("my-day")

    assert (precious / "note.md").is_file()
    assert str(precious) in result["refused_outside_plugin_folders"]


def test_uninstalling_something_not_installed_is_reported(roots):
    result = MarketplaceManager().uninstall("my-day")

    assert result["uninstalled"] is False


def test_an_uninstall_that_cannot_move_a_piece_aside_changes_nothing(roots, monkeypatch):
    publish(roots)
    MarketplaceManager().install("my-day", "1.0.0")
    refuse_to_move(monkeypatch, roots["frontend_plugins"] / "my-day")

    result = MarketplaceManager().uninstall("my-day")

    assert result["uninstalled"] is False
    assert result["in_use"] is True
    assert (roots["config"] / "plugins" / "my-day" / "backend" / "__init__.py").is_file()
    assert (roots["frontend_plugins"] / "my-day" / "index.tsx").is_file()
    assert [e["id"] for e in installed_record(roots)["plugins"]] == ["my-day"]
    assert work_entries(roots) == []


# -- HTTP ----------------------------------------------------------------------------


def test_the_http_surface_installs_and_uninstalls(roots):
    from app.main import app

    publish(roots)
    client = TestClient(app)

    assert client.get("/marketplace").json()[0]["id"] == "my-day"
    assert client.get("/marketplace/my-day/1.0.0/preflight").json()["ok"] is True
    assert client.get("/marketplace/my-day/9.9.9/preflight").status_code == 404
    assert client.post("/marketplace/my-day/1.0.0/install").json()["installed"] is True
    assert client.post("/marketplace/my-day/1.0.0/install").status_code == 409
    assert client.post("/marketplace/my-day/uninstall").json()["uninstalled"] is True
    assert client.post("/marketplace/my-day/uninstall").status_code == 404
