"""Raw data access for the Marketplace (`ADR-022`, `REQ-SB-91` Phase 4) -- the
framework's own `src/marketplace/<plugin-id>/<version>/` packages, and copying
one package's pieces into an install. Zero business interpretation here: no
compatibility check, no ownership decisions, no id rules -- that is
MarketplaceManager's job.

A package holds `plugin.json`, `backend/` (the plugin's Python package) and
`ui/` (its screens). Installing copies `plugin.json` and `backend/` into the
install's config folder, where the backend plugin host loads them, and `ui/`
into the frontend's `src/plugins/<plugin-id>/`, where build-time composition
picks it up.

Both roots resolve from this file's own location, not from settings: the
Marketplace and the frontend source are part of the framework checkout, not
per-install data.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.data_access import plugins as plugins_data

_SRC_ROOT = Path(__file__).resolve().parents[3]
_MARKETPLACE_ROOT = _SRC_ROOT / "marketplace"
_FRONTEND_PLUGINS_ROOT = _SRC_ROOT / "frontend" / "src" / "plugins"

_MANIFEST_FILENAME = "plugin.json"
_BACKEND_DIRECTORY_NAME = "backend"
_UI_DIRECTORY_NAME = "ui"
_NEVER_COPIED = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "node_modules")


def marketplace_root() -> Path:
    return _MARKETPLACE_ROOT


def frontend_plugins_root() -> Path:
    return _FRONTEND_PLUGINS_ROOT


def list_package_versions() -> dict[str, list[str]]:
    """Every published package: plugin id -> the version folders that hold a
    `plugin.json`. Empty, never an exception, when there is no Marketplace."""
    root = marketplace_root()
    if not root.is_dir():
        return {}
    packages: dict[str, list[str]] = {}
    for plugin_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        versions = [v.name for v in plugin_dir.iterdir() if v.is_dir() and (v / _MANIFEST_FILENAME).is_file()]
        if versions:
            packages[plugin_dir.name] = versions
    return packages


def has_package(plugin_id: str, version: str) -> bool:
    return (marketplace_root() / plugin_id / version / _MANIFEST_FILENAME).is_file()


def read_package_manifest(plugin_id: str, version: str) -> dict:
    """Raises FileNotFoundError / json.JSONDecodeError."""
    path = marketplace_root() / plugin_id / version / _MANIFEST_FILENAME
    return json.loads(path.read_text(encoding="utf-8"))


def copy_package_into_install(plugin_id: str, version: str) -> dict[str, str | None]:
    """Copies one package's pieces into this install and returns where each
    landed: `{"backend": <path>, "ui": <path or None>}`. Raises if either
    target already exists -- replacing an installed plugin is an uninstall
    followed by an install, decided by the Manager, never an in-place merge
    that could leave a previous version's files behind."""
    source = marketplace_root() / plugin_id / version
    plugins_root = plugins_data.plugins_root()
    if plugins_root is None:
        raise FileNotFoundError("No App Database Folder is configured")

    backend_target = plugins_root / plugin_id
    ui_target = frontend_plugins_root() / plugin_id
    for target in (backend_target, ui_target):
        if target.exists():
            raise FileExistsError(f"{target} already exists")

    backend_target.mkdir(parents=True)
    shutil.copy2(source / _MANIFEST_FILENAME, backend_target / _MANIFEST_FILENAME)
    if (source / _BACKEND_DIRECTORY_NAME).is_dir():
        shutil.copytree(source / _BACKEND_DIRECTORY_NAME, backend_target / _BACKEND_DIRECTORY_NAME, ignore=_NEVER_COPIED)

    copied_ui = None
    if (source / _UI_DIRECTORY_NAME).is_dir():
        ui_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source / _UI_DIRECTORY_NAME, ui_target, ignore=_NEVER_COPIED)
        copied_ui = str(ui_target)

    return {"backend": str(backend_target), "ui": copied_ui}


def remove_tree(path: str) -> bool:
    """True when something was removed. False for a path that is already gone."""
    target = Path(path)
    if not target.exists():
        return False
    shutil.rmtree(target)
    return True
