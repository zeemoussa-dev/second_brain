"""Raw data access for installed plugins (`ADR-022`) -- the install's own
`<SECOND_BRAIN_DATA_PATH>/plugins/` folder: the ownership record
`installed.json`, each plugin's `plugin.json`, and loading a plugin's backend
package from disk. Zero business interpretation here: no version gate, no
status, no id rules, no load order -- that is PluginManager's job.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

from app.config import settings

_PLUGINS_DIRECTORY_NAME = "plugins"
_INSTALLED_RECORD_FILENAME = "installed.json"
_MANIFEST_FILENAME = "plugin.json"
_BACKEND_DIRECTORY_NAME = "backend"
_BACKEND_PACKAGE_PREFIX = "sb_plugins_"


def plugins_root() -> Path | None:
    """None before setup has configured an App Database Folder -- there is
    nowhere an installed plugin could be, which is not the same as "none
    installed"."""
    if settings.second_brain_data_path is None:
        return None
    return Path(settings.second_brain_data_path) / _PLUGINS_DIRECTORY_NAME


def read_installed_record() -> dict | None:
    """None when this install has never installed a plugin. A record that
    exists but will not parse raises `json.JSONDecodeError`: a corrupt
    ownership record must be reported, never read as "nothing installed",
    or an uninstall would later leave that plugin's pieces behind."""
    root = plugins_root()
    if root is None:
        return None
    path = root / _INSTALLED_RECORD_FILENAME
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_installed_record(record: dict) -> None:
    """Written to a temporary file and swapped in. A crash mid-write must never
    leave a half-written ownership record: the host reads a corrupt record as
    "load nothing", and an uninstall could no longer find what to remove."""
    root = plugins_root()
    if root is None:
        raise FileNotFoundError("No App Database Folder is configured")
    root.mkdir(parents=True, exist_ok=True)
    temporary = root / (_INSTALLED_RECORD_FILENAME + ".tmp")
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(root / _INSTALLED_RECORD_FILENAME)


def read_manifest(plugin_id: str) -> dict:
    """Raises FileNotFoundError / json.JSONDecodeError."""
    root = plugins_root()
    if root is None:
        raise FileNotFoundError("No App Database Folder is configured")
    return json.loads((root / plugin_id / _MANIFEST_FILENAME).read_text(encoding="utf-8"))


def backend_package_name(plugin_id: str) -> str:
    """The name a plugin's backend is imported under. Derived from the id, so
    two plugins can never collide in `sys.modules`, and prefixed, so the
    import check can tell a plugin package from framework code."""
    return _BACKEND_PACKAGE_PREFIX + "".join(ch if ch.isalnum() else "_" for ch in plugin_id)


def import_backend_package(plugin_id: str) -> ModuleType:
    """Imports `plugins/<id>/backend/` as a real package, so a plugin's own
    modules can import each other relatively (`from . import day_view`).

    Any earlier import of the same package is dropped first, submodules
    included: without that, reloading after an upgrade would silently keep
    running the previous version's modules from `sys.modules`.

    Raises FileNotFoundError when there is no `backend/__init__.py`, and
    otherwise whatever the plugin's own module code raises -- deciding what a
    failure means is the Manager's job, not this function's."""
    root = plugins_root()
    if root is None:
        raise FileNotFoundError("No App Database Folder is configured")
    backend_dir = root / plugin_id / _BACKEND_DIRECTORY_NAME
    init_file = backend_dir / "__init__.py"
    if not init_file.is_file():
        raise FileNotFoundError(f"{plugin_id}: no backend/__init__.py")

    package_name = backend_package_name(plugin_id)
    for loaded in [name for name in sys.modules if name == package_name or name.startswith(package_name + ".")]:
        del sys.modules[loaded]

    spec = importlib.util.spec_from_file_location(
        package_name, init_file, submodule_search_locations=[str(backend_dir)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"{plugin_id}: backend/__init__.py cannot be loaded as a package")
    module = importlib.util.module_from_spec(spec)
    sys.modules[package_name] = module
    # The plugins folder lives in the install's config folder, which may be
    # synced. A sync client holding a plugin's __pycache__ open is what stopped
    # a version from being replaced (BUG-065), and a plugin is small enough to
    # compile at every start.
    wrote_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(package_name, None)
        raise
    finally:
        sys.dont_write_bytecode = wrote_bytecode
    return module
