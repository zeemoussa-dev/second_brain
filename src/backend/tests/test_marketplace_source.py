"""Installing a plugin from where it lives (`REQ-SB-92`): a folder on this
machine, or a git repository at a ref -- so a plugin never has to be published
into the framework's own tree to be installable.

The git tests clone a real repository created in a temp folder, so cloning is
genuinely exercised without a network. Only the screen build is stubbed: it runs
a real `npm run build`, which belongs to the gate's own test, not to every one.
"""
import json
import subprocess
import textwrap

import pytest

from app import plugin_api
from app.business.core.marketplace.marketplace_manager import MarketplaceManager
from app.business.core.plugins import screen_build
from app.business.core.plugins.plugin_manager import PluginManager
from app.config import settings
from app.data_access import marketplace as marketplace_data
from app.data_access import plugin_sources
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

_UI = '''
import type { PluginUi } from '../../pluginHost/types';
const ui: PluginUi = {};
export default ui;
'''


@pytest.fixture()
def roots(tmp_path, monkeypatch):
    config, frontend_plugins = tmp_path / "config", tmp_path / "frontend-plugins"
    monkeypatch.setattr(settings, "second_brain_data_path", config)
    monkeypatch.setattr(marketplace_data, "_MARKETPLACE_ROOT", tmp_path / "marketplace")
    monkeypatch.setattr(marketplace_data, "_FRONTEND_PLUGINS_ROOT", frontend_plugins)
    monkeypatch.setattr(skills_data, "list_categories", lambda: ["graph", "vault"])
    # The build gate has its own test; every other test would otherwise run npm.
    monkeypatch.setattr(screen_build, "build_screens", lambda *args, **kwargs: None)
    return {"config": config, "frontend_plugins": frontend_plugins, "marketplace": tmp_path / "marketplace",
            "tmp": tmp_path}


def write_source(directory, *, plugin_id="action-center", version="1.0.0", framework_api=None,
                 backend=_BACKEND, with_ui=True, templates=None):
    """A plugin repository's working tree."""
    (directory / "backend").mkdir(parents=True, exist_ok=True)
    (directory / "plugin.json").write_text(json.dumps({
        "id": plugin_id, "name": "Action Center", "description": "Actions asked of people.",
        "version": version,
        "framework_api": plugin_api.FRAMEWORK_API if framework_api is None else framework_api,
        "requires": [],
    }), encoding="utf-8")
    (directory / "backend" / "__init__.py").write_text(
        textwrap.dedent(backend).replace("{version}", version), encoding="utf-8")
    if with_ui:
        (directory / "ui").mkdir(exist_ok=True)
        (directory / "ui" / "index.tsx").write_text(textwrap.dedent(_UI), encoding="utf-8")
    for template_id, data in (templates or {}).items():
        folder = directory / "templates" / template_id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "Template.json").write_text(json.dumps(data), encoding="utf-8")
    return directory


def git_repository(directory, **kwargs):
    """A real git repository holding a plugin, on this machine."""
    write_source(directory, **kwargs)
    run = lambda *args: subprocess.run(["git", *args], cwd=directory, capture_output=True, text=True, check=True)
    run("init", "-b", "main")
    run("config", "user.email", "tests@example.invalid")
    run("config", "user.name", "Tests")
    run("add", "-A")
    run("commit", "-m", "the plugin")
    return directory


def installed_record(roots):
    return json.loads((roots["config"] / "plugins" / "installed.json").read_text(encoding="utf-8"))


def publish_package(roots, plugin_id="action-center", version="0.9.0"):
    package = roots["marketplace"] / plugin_id / version
    write_source(package, plugin_id=plugin_id, version=version)
    return package


# -- installing from a folder -------------------------------------------------------


def test_a_plugin_installs_from_a_folder_on_this_machine(roots):
    source = write_source(roots["tmp"] / "repo")

    result = MarketplaceManager().install_from_source("path", str(source))

    assert result["installed"] is True and result["version"] == "1.0.0"
    assert result["source"] == {"kind": "path", "location": str(source)}
    assert (roots["config"] / "plugins" / "action-center" / "backend" / "__init__.py").is_file()
    assert (roots["frontend_plugins"] / "action-center" / "index.tsx").is_file()
    [entry] = installed_record(roots)["plugins"]
    assert entry["source"]["location"] == str(source)
    assert [prefix for prefix, _ in PluginManager().load_all()] == ["/plugins/action-center"]


def test_a_folder_that_is_not_a_plugin_is_refused(roots, tmp_path):
    empty = tmp_path / "not-a-plugin"
    empty.mkdir()

    result = MarketplaceManager().install_from_source("path", str(empty))

    assert result["installed"] is False
    assert any("no plugin.json" in problem for problem in result["problems"])
    assert not (roots["config"] / "plugins" / "action-center").exists()


# -- installing from a git repository -----------------------------------------------


def test_a_plugin_installs_from_a_git_repository_and_records_where_it_came_from(roots):
    repository = git_repository(roots["tmp"] / "sb-plugins-action-center")

    result = MarketplaceManager().install_from_source("git", str(repository), "main")

    assert result["installed"] is True
    source = result["source"]
    assert source["kind"] == "git" and source["ref"] == "main" and len(source["commit"]) == 40
    assert (roots["config"] / "plugins" / "action-center" / "backend" / "__init__.py").is_file()
    assert installed_record(roots)["plugins"][0]["source"]["commit"] == source["commit"]


def test_an_unknown_ref_is_refused_and_nothing_is_installed(roots):
    repository = git_repository(roots["tmp"] / "repo")

    result = MarketplaceManager().install_from_source("git", str(repository), "no-such-branch")

    assert result["installed"] is False
    assert any("not a branch, tag or commit" in problem for problem in result["problems"])
    assert not (roots["config"] / "plugins" / "action-center").exists()


def test_a_clone_leaves_no_temporary_folder_behind(roots, monkeypatch):
    repository = git_repository(roots["tmp"] / "repo")
    discarded = []
    real_discard = plugin_sources.discard
    monkeypatch.setattr(plugin_sources, "discard",
                        lambda directory: (discarded.append(directory), real_discard(directory))[1])

    MarketplaceManager().preflight_source("git", str(repository), "main")

    assert discarded and not any(directory.exists() for directory in discarded)


# -- the three gates ------------------------------------------------------------------


def test_a_plugin_reaching_past_the_plugin_api_is_refused(roots):
    source = write_source(roots["tmp"] / "repo", backend='''
from app.business.core.vault.vault_manager import VaultManager


def register(api):
    pass
''')

    result = MarketplaceManager().install_from_source("path", str(source))

    assert result["installed"] is False
    assert any("may import only `app.plugin_api`" in problem for problem in result["problems"])
    assert not (roots["config"] / "plugins" / "action-center").exists()


def test_a_plugin_built_for_another_framework_api_is_refused(roots):
    source = write_source(roots["tmp"] / "repo", framework_api=plugin_api.FRAMEWORK_API + 1)

    result = MarketplaceManager().install_from_source("path", str(source))

    assert result["installed"] is False
    assert any("this framework provides" in problem for problem in result["problems"])


def test_screens_that_do_not_build_are_refused(roots, monkeypatch):
    monkeypatch.setattr(screen_build, "build_screens", lambda *args, **kwargs: "the screens do not build: TS2307")
    source = write_source(roots["tmp"] / "repo")

    result = MarketplaceManager().install_from_source("path", str(source))

    assert result["installed"] is False
    assert any("do not build" in problem for problem in result["problems"])
    assert not (roots["frontend_plugins"] / "action-center").exists()


# -- updating -------------------------------------------------------------------------


def test_installing_from_a_repository_replaces_a_version_installed_from_the_marketplace(roots):
    publish_package(roots, version="0.9.0")
    MarketplaceManager().install("action-center", "0.9.0")
    repository = git_repository(roots["tmp"] / "repo", version="1.0.0")

    result = MarketplaceManager().install_from_source("git", str(repository), "main")

    assert result["installed"] is True and result["replaced"] == "0.9.0"
    backend = (roots["config"] / "plugins" / "action-center" / "backend" / "__init__.py").read_text(encoding="utf-8")
    assert 'VERSION = "1.0.0"' in backend
    [entry] = installed_record(roots)["plugins"]
    assert entry["version"] == "1.0.0" and entry["source"]["kind"] == "git"


def test_update_pulls_the_recorded_repository_again(roots):
    repository = git_repository(roots["tmp"] / "repo")
    first = MarketplaceManager().install_from_source("git", str(repository), "main")
    write_source(repository, version="1.1.0")
    for args in (["add", "-A"], ["commit", "-m", "a newer plugin"]):
        subprocess.run(["git", *args], cwd=repository, capture_output=True, text=True, check=True)

    result = MarketplaceManager().update_from_source("action-center")

    assert result["installed"] is True and result["version"] == "1.1.0"
    assert result["source"]["commit"] != first["source"]["commit"]
    backend = (roots["config"] / "plugins" / "action-center" / "backend" / "__init__.py").read_text(encoding="utf-8")
    assert 'VERSION = "1.1.0"' in backend


def test_the_same_version_can_be_reinstalled_from_a_moving_branch(roots):
    repository = git_repository(roots["tmp"] / "repo")
    MarketplaceManager().install_from_source("git", str(repository), "main")

    assert MarketplaceManager().install_from_source("git", str(repository), "main")["installed"] is True


# BUG-071: the "already installed" rule compared version strings alone, so a plugin
# installed from a repository could not be put back onto the published package of the
# same version -- the operator had to uninstall it first.
def test_the_published_package_can_replace_a_repository_install_of_the_same_version(roots):
    package = publish_package(roots, version="1.0.0")
    (package / "backend" / "__init__.py").write_text(
        textwrap.dedent(_BACKEND).replace("{version}", "1.0.0") + '\nORIGIN = "package"\n', encoding="utf-8")
    repository = git_repository(roots["tmp"] / "repo", version="1.0.0")
    MarketplaceManager().install_from_source("git", str(repository), "main")

    check = MarketplaceManager().preflight("action-center", "1.0.0")
    result = MarketplaceManager().install("action-center", "1.0.0")

    assert check["ok"] is True and check["replaces"] == "1.0.0"
    assert result["installed"] is True
    backend = (roots["config"] / "plugins" / "action-center" / "backend" / "__init__.py").read_text(encoding="utf-8")
    assert 'ORIGIN = "package"' in backend
    # Its origin is this Marketplace again, so Update has nothing to pull.
    [entry] = installed_record(roots)["plugins"]
    assert entry.get("source") is None
    assert any("has no repository to pull" in problem
               for problem in MarketplaceManager().update_from_source("action-center")["problems"])


def test_a_marketplace_install_of_the_version_already_installed_is_still_refused(roots):
    publish_package(roots, version="1.0.0")
    MarketplaceManager().install("action-center", "1.0.0")

    result = MarketplaceManager().install("action-center", "1.0.0")

    assert result["installed"] is False
    assert any("already installed" in problem for problem in result["problems"])


def test_update_says_so_when_the_plugin_came_from_the_marketplace(roots):
    publish_package(roots, version="0.9.0")
    MarketplaceManager().install("action-center", "0.9.0")

    result = MarketplaceManager().update_from_source("action-center")

    assert result["installed"] is False
    assert any("has no repository to pull" in problem for problem in result["problems"])


def test_update_of_something_not_installed_is_reported(roots):
    assert MarketplaceManager().update_from_source("nothing")["installed"] is False


# -- listing and Templates --------------------------------------------------------------


def test_a_plugin_installed_from_a_repository_is_listed_with_its_source(roots):
    repository = git_repository(roots["tmp"] / "repo")
    MarketplaceManager().install_from_source("git", str(repository), "main")

    [entry] = MarketplaceManager().get_all()

    assert entry["id"] == "action-center" and entry["packages"] == []
    assert entry["installed_version"] == "1.0.0" and entry["source"]["kind"] == "git"


def test_a_sources_templates_are_installed_and_an_existing_one_is_kept(roots):
    existing = roots["config"] / "data" / "Templates" / "task" / "Template.json"
    existing.parent.mkdir(parents=True)
    existing.write_text(json.dumps({"id": "task", "sections": [], "note": "operator edit"}), encoding="utf-8")
    source = write_source(roots["tmp"] / "repo", templates={
        "task": {"id": "task", "sections": []}, "action": {"id": "action", "sections": []},
    })

    result = MarketplaceManager().install_from_source("path", str(source))

    assert result["templates"] == {"installed": ["action"], "kept": ["task"]}
    assert json.loads(existing.read_text(encoding="utf-8"))["note"] == "operator edit"


# -- HTTP -------------------------------------------------------------------------------


def test_the_http_surface_installs_and_updates_from_a_source(roots):
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    repository = git_repository(roots["tmp"] / "repo")
    body = {"kind": "git", "location": str(repository), "ref": "main"}

    assert client.post("/marketplace/source/preflight", json=body).json()["ok"] is True
    assert client.post("/marketplace/source/install", json=body).json()["installed"] is True
    assert client.post("/marketplace/action-center/update").json()["installed"] is True
    assert client.post("/marketplace/nothing/update").status_code == 409
    assert client.post("/marketplace/source/install", json={"kind": "path", "location": "nowhere"}).status_code == 409
