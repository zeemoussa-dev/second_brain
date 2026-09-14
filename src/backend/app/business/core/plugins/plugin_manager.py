"""PluginManager -- the sole gateway onto installed plugins (`ADR-022`,
`REQ-SB-91` Phase 1), the same "one real gateway" rule every other Manager
follows. Decides which installed plugins may run and runs them; raw file and
import I/O lives in `data_access/plugins.py`.

Loading is all-or-nothing PER PLUGIN and never for the app: a plugin that is
refused, invalid or broken is recorded with the reason and skipped, and every
other plugin still loads. A second brain whose Marketplace plugin has a bug
must still boot -- otherwise the operator cannot even reach Settings to
uninstall it.

The load report is module-level state, like VaultManager's index: it is
produced once per app start by `load_all()` and read many times by System
Health, from any number of Manager instances.
"""
from __future__ import annotations

import re

from fastapi import APIRouter

from app import plugin_api
from app.business.core.plugins.plugin import DISABLED, INVALID, LOADED, REFUSED, Plugin
from app.data_access import plugins as plugins_data

PLUGIN_ROUTE_PREFIX = "/plugins"

# An id becomes a folder name, a package name and a URL segment. Anything
# looser would let an ownership record point outside the plugins folder
# ("../x") or produce a route prefix nobody can type.
_VALID_PLUGIN_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")

_load_report: list[Plugin] = []


class PluginManager:
    def load_all(self) -> list[tuple[str, APIRouter]]:
        """Loads every plugin in the ownership record, in record order, and
        returns the `(prefix, router)` pairs to mount. Never raises for a
        plugin's own failure. The record's order is the install order, so a
        plugin is loaded after anything it was installed on top of.

        `requires` is recorded but not yet enforced: resolving "graph or
        outlook" needs the Marketplace's view of what is installed, which
        arrives with it (`REQ-SB-91` Phase 4)."""
        global _load_report
        report: list[Plugin] = []
        mounts: list[tuple[str, APIRouter]] = []

        try:
            record = plugins_data.read_installed_record()
        except (OSError, ValueError) as exc:
            _load_report = [Plugin(
                id="installed.json", name="Installed plugins record", version="",
                framework_api=None, status=INVALID,
                reason=f"the ownership record cannot be read, so no plugin was loaded: {exc}",
            )]
            return []

        seen: set[str] = set()
        for entry in (record or {}).get("plugins") or []:
            plugin, plugin_mounts = self._load_one(entry, seen)
            report.append(plugin)
            mounts.extend(plugin_mounts)

        _load_report = report
        return mounts

    def get_load_report(self) -> list[Plugin]:
        return list(_load_report)

    def _load_one(self, entry: object, seen: set[str]) -> tuple[Plugin, list[tuple[str, APIRouter]]]:
        raw_id = str(entry.get("id") or "").strip() if isinstance(entry, dict) else ""
        recorded_version = str(entry.get("version") or "") if isinstance(entry, dict) else ""

        if not _VALID_PLUGIN_ID.match(raw_id):
            return self._rejected(raw_id or "(missing id)", recorded_version, INVALID,
                                  "the installed id is not a valid plugin id"), []
        if raw_id in seen:
            return self._rejected(raw_id, recorded_version, INVALID,
                                  "installed twice in the ownership record; only the first is loaded"), []
        seen.add(raw_id)

        try:
            manifest = plugins_data.read_manifest(raw_id)
        except (OSError, ValueError) as exc:
            return self._rejected(raw_id, recorded_version, INVALID, f"plugin.json cannot be read: {exc}"), []

        plugin = self._to_plugin(raw_id, manifest)
        if manifest.get("id") != raw_id:
            plugin.status = INVALID
            plugin.reason = f"plugin.json declares id {manifest.get('id')!r}, but it is installed as {raw_id!r}"
            return plugin, []

        # Checked BEFORE importing anything: a plugin built against another
        # framework API must not get the chance to run a single line, because
        # the damage a mismatch does happens at import and registration time.
        if plugin.framework_api != plugin_api.FRAMEWORK_API:
            plugin.status = REFUSED
            plugin.reason = (
                f"built for framework API {plugin.framework_api!r}; this framework provides "
                f"API {plugin_api.FRAMEWORK_API}"
            )
            return plugin, []

        api = plugin_api.PluginApi(raw_id)
        try:
            module = plugins_data.import_backend_package(raw_id)
            register = getattr(module, "register", None)
            if not callable(register):
                raise TypeError("backend/__init__.py defines no register(api) function")
            register(api)
        except Exception as exc:
            plugin.status = DISABLED
            plugin.reason = f"{type(exc).__name__}: {exc}"
            return plugin, []

        prefix = f"{PLUGIN_ROUTE_PREFIX}/{raw_id}"
        plugin.status = LOADED
        plugin.routes_prefix = prefix
        return plugin, [(prefix, router) for router in api.routers]

    def _to_plugin(self, plugin_id: str, manifest: dict) -> Plugin:
        framework_api = manifest.get("framework_api")
        return Plugin(
            id=plugin_id,
            name=str(manifest.get("name") or plugin_id),
            version=str(manifest.get("version") or ""),
            framework_api=framework_api if isinstance(framework_api, int) and not isinstance(framework_api, bool) else None,
            requires=[str(item) for item in manifest.get("requires") or []],
        )

    def _rejected(self, plugin_id: str, version: str, status: str, reason: str) -> Plugin:
        return Plugin(id=plugin_id, name=plugin_id, version=version, framework_api=None,
                      status=status, reason=reason)
