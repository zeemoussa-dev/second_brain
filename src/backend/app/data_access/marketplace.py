"""Raw data access for the Marketplace (`ADR-022`, `REQ-SB-91` Phase 4) -- the
framework's own `src/marketplace/<plugin-id>/<version>/` packages, and moving
one package's pieces into and out of an install. Zero business interpretation
here: no compatibility check, no ownership decisions, no id rules -- that is
MarketplaceManager's job.

A package holds `plugin.json`, `backend/` (the plugin's Python package),
`ui/` (its screens) and `templates/<id>/Template.json` (its Templates). An
installed plugin is two pieces: `plugin.json` and `backend/` in the install's
config folder, where the backend plugin host loads them, and `ui/` in the
frontend's `src/plugins/<plugin-id>/`, where build-time composition picks it
up. Templates are not copied here: TemplateManager installs them.

Pieces are never deleted in place (`BUG-065`). A delete that the OS stops
part-way -- a sync client such as OneDrive holding a `__pycache__` open --
leaves a plugin with its modules gone and its folder still there. So a piece
is renamed into a work folder beside it in one step, which either fully
succeeds or changes nothing, and deleted from there as far as the OS allows.

Both roots resolve from this file's own location, not from settings: the
Marketplace and the frontend source are part of the framework checkout, not
per-install data.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import uuid
from pathlib import Path

from app.data_access import plugins as plugins_data

_SRC_ROOT = Path(__file__).resolve().parents[3]
_MARKETPLACE_ROOT = _SRC_ROOT / "marketplace"
_FRONTEND_ROOT = _SRC_ROOT / "frontend"
_FRONTEND_PLUGINS_ROOT = _SRC_ROOT / "frontend" / "src" / "plugins"

_MANIFEST_FILENAME = "plugin.json"
_BACKEND_DIRECTORY_NAME = "backend"
_UI_DIRECTORY_NAME = "ui"
_TEMPLATES_DIRECTORY_NAME = "templates"
_TEMPLATE_FILENAME = "Template.json"
_NEVER_COPIED = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "node_modules")

# Beside the pieces, in the same parent folder, so moving in and out is a
# rename on one volume. The host loads plugins by the ownership record, never by
# scanning folders, and the frontend composes only `src/plugins/*/index.tsx`, so
# nothing in here is ever loaded.
_WORK_DIRECTORY_NAME = ".marketplace-work"
_NAME_SEPARATOR = "--"


def marketplace_root() -> Path:
    return _MARKETPLACE_ROOT


def frontend_plugins_root() -> Path:
    return _FRONTEND_PLUGINS_ROOT


def frontend_root() -> Path:
    """The frontend checkout -- where a plugin's screens are built before it is
    installed, and where they land."""
    return _FRONTEND_ROOT


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


def read_source_templates(source_dir: Path) -> dict[str, object]:
    """{Template id (its folder name): parsed Template.json} for a plugin's
    source -- a published package or a repository checkout. Empty when it ships
    no `templates/`. Raises OSError / json.JSONDecodeError."""
    root = Path(source_dir) / _TEMPLATES_DIRECTORY_NAME
    if not root.is_dir():
        return {}
    return {
        folder.name: json.loads((folder / _TEMPLATE_FILENAME).read_text(encoding="utf-8"))
        for folder in sorted(root.iterdir()) if folder.is_dir()
    }


def read_package_templates(plugin_id: str, version: str) -> dict[str, object]:
    """The published package's Templates."""
    return read_source_templates(marketplace_root() / plugin_id / version)


def install_targets(plugin_id: str) -> dict[str, Path]:
    """Where each piece of an installed plugin lives: `{"backend": ..., "ui": ...}`."""
    plugins_root = plugins_data.plugins_root()
    if plugins_root is None:
        raise FileNotFoundError("No App Database Folder is configured")
    return {"backend": plugins_root / plugin_id, "ui": frontend_plugins_root() / plugin_id}


def _work_path(beside: Path, kind: str, plugin_id: str) -> Path:
    name = _NAME_SEPARATOR.join((kind, plugin_id, uuid.uuid4().hex[:8]))
    return beside.parent / _WORK_DIRECTORY_NAME / name


def stage_package(plugin_id: str, version: str) -> dict[str, Path | None]:
    """Copies a published package into work folders beside where it will be installed."""
    return stage_source(plugin_id, marketplace_root() / plugin_id / version)


def stage_source(plugin_id: str, source_dir: Path) -> dict[str, Path | None]:
    """Copies a plugin's source -- a published package, or a repository checkout
    (`REQ-SB-92`) -- into work folders beside where it will be installed,
    without touching anything installed: `{"backend": <path>, "ui": <path or
    None>}`. A copy that fails removes what it copied and raises."""
    source = Path(source_dir)
    targets = install_targets(plugin_id)
    staged: dict[str, Path | None] = {"backend": None, "ui": None}
    try:
        backend_stage = _work_path(targets["backend"], "staging", plugin_id)
        staged["backend"] = backend_stage
        backend_stage.mkdir(parents=True)
        shutil.copy2(source / _MANIFEST_FILENAME, backend_stage / _MANIFEST_FILENAME)
        if (source / _BACKEND_DIRECTORY_NAME).is_dir():
            shutil.copytree(source / _BACKEND_DIRECTORY_NAME, backend_stage / _BACKEND_DIRECTORY_NAME, ignore=_NEVER_COPIED)
        if (source / _UI_DIRECTORY_NAME).is_dir():
            ui_stage = _work_path(targets["ui"], "staging", plugin_id)
            staged["ui"] = ui_stage
            ui_stage.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source / _UI_DIRECTORY_NAME, ui_stage, ignore=_NEVER_COPIED)
    except OSError:
        for path in staged.values():
            if path is not None:
                discard_tree(path)
        raise
    return staged


def move_aside(path: Path) -> Path | None:
    """Renames an installed piece into its work folder in one step, so it is
    either still wholly in place or wholly out of the way. Returns where it
    went, or None when nothing was there. Raises OSError when the OS refuses,
    typically because something holds a file in it open."""
    path = Path(path)
    if not path.exists():
        return None
    aside = _work_path(path, "replaced", path.name)
    aside.parent.mkdir(parents=True, exist_ok=True)
    path.rename(aside)
    return aside


def move_into_place(source: Path, target: Path) -> None:
    """Raises FileExistsError when something is already at `target`."""
    target = Path(target)
    if target.exists():
        raise FileExistsError(f"{target} already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    Path(source).rename(target)


def discard_tree(path: Path) -> list[str]:
    """Deletes a folder that is already out of the install's way, as far as the
    OS allows. Never raises: whatever cannot be deleted is returned, and swept
    again by the plugin's next install or uninstall."""
    path = Path(path)
    if not path.exists():
        return []

    def retry_writable(function, failed_path, _exc_info):
        try:
            os.chmod(failed_path, stat.S_IWRITE)
            function(failed_path)
        except OSError:
            pass

    shutil.rmtree(path, onerror=retry_writable)
    return [str(path)] if path.exists() else []


def sweep_work_folders(plugin_id: str) -> list[str]:
    """Deletes this plugin's staging copies and replaced pieces that an earlier
    install or uninstall could not. Returns what still cannot be deleted."""
    leftovers: list[str] = []
    for target in install_targets(plugin_id).values():
        work = target.parent / _WORK_DIRECTORY_NAME
        if not work.is_dir():
            continue
        for entry in work.iterdir():
            kind_and_id = entry.name.rsplit(_NAME_SEPARATOR, 1)[0]
            if kind_and_id in (f"staging{_NAME_SEPARATOR}{plugin_id}", f"replaced{_NAME_SEPARATOR}{plugin_id}"):
                leftovers.extend(discard_tree(entry))
    return leftovers
