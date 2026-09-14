"""MarketplaceManager -- the sole gateway onto installing and uninstalling
plugins (`ADR-022`, `REQ-SB-91` Phase 4). Decides whether a published package
may be installed and records what an install owns; raw file I/O lives in
`data_access/marketplace.py` and `data_access/plugins.py`.

Install and uninstall change files on disk only. A plugin's backend is loaded
at startup, so both report `restart_required`; its screens appear as soon as
the frontend picks up `src/plugins/`.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from app import plugin_api
from app.business.core.plugins.plugin_manager import is_valid_plugin_id
from app.data_access import marketplace as marketplace_data
from app.data_access import plugins as plugins_data
from app.data_access import skills as skills_data

_VERSION = re.compile(r"^\d+\.\d+\.\d+$")


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


class MarketplaceManager:
    # -- reading ---------------------------------------------------------------

    def get_all(self) -> list[dict]:
        """Every published plugin with its versions, newest first, and what is
        installed. A version whose manifest cannot be read is listed carrying
        `error` rather than dropped: a broken package the operator cannot see
        is worse than one that fails loudly."""
        installed = self._installed_versions()
        catalog = []
        for plugin_id, versions in marketplace_data.list_package_versions().items():
            ordered = sorted((v for v in versions if _VERSION.match(v)), key=_version_key, reverse=True)
            packages = []
            for version in ordered:
                try:
                    manifest = marketplace_data.read_package_manifest(plugin_id, version)
                except (OSError, ValueError) as exc:
                    packages.append({"version": version, "error": f"plugin.json cannot be read: {exc}"})
                    continue
                packages.append({
                    "version": version,
                    "name": str(manifest.get("name") or plugin_id),
                    "description": str(manifest.get("description") or ""),
                    "framework_api": manifest.get("framework_api"),
                    "requires": [str(item) for item in manifest.get("requires") or []],
                    "compatible": manifest.get("framework_api") == plugin_api.FRAMEWORK_API,
                    "error": None,
                })
            if packages:
                catalog.append({
                    "id": plugin_id,
                    "installed_version": installed.get(plugin_id),
                    "packages": packages,
                })
        return catalog

    def has_package(self, plugin_id: str, version: str) -> bool:
        return is_valid_plugin_id(plugin_id) and bool(_VERSION.match(version)) and marketplace_data.has_package(plugin_id, version)

    def is_installed(self, plugin_id: str) -> bool:
        return plugin_id in self._installed_versions()

    # -- install ----------------------------------------------------------------

    def preflight(self, plugin_id: str, version: str) -> dict:
        """What installing would do, and everything that would stop it. Changes
        nothing."""
        installed_version = self._installed_versions().get(plugin_id)
        result = {
            "plugin_id": plugin_id, "version": version, "ok": False, "problems": [],
            "installed_version": installed_version,
            "replaces": installed_version if installed_version and installed_version != version else None,
        }
        problems: list[str] = result["problems"]

        if not self.has_package(plugin_id, version):
            problems.append(f"no published package {plugin_id} {version}")
            return result
        try:
            manifest = marketplace_data.read_package_manifest(plugin_id, version)
        except (OSError, ValueError) as exc:
            problems.append(f"plugin.json cannot be read: {exc}")
            return result

        if manifest.get("id") != plugin_id:
            problems.append(f"plugin.json declares id {manifest.get('id')!r}, but it is published as {plugin_id!r}")
        if manifest.get("version") != version:
            problems.append(f"plugin.json declares version {manifest.get('version')!r}, but it is published as {version!r}")
        if manifest.get("framework_api") != plugin_api.FRAMEWORK_API:
            problems.append(
                f"built for framework API {manifest.get('framework_api')!r}; this framework provides "
                f"API {plugin_api.FRAMEWORK_API}"
            )
        if installed_version == version:
            problems.append(f"{plugin_id} {version} is already installed")
        problems.extend(self._unmet_requirements(plugin_id, manifest))

        result["ok"] = not problems
        return result

    def install(self, plugin_id: str, version: str) -> dict:
        """Installs one published version, replacing any other installed version
        of the same plugin. Re-runs preflight itself and changes nothing when it
        fails -- it never trusts a preview the client may be holding."""
        check = self.preflight(plugin_id, version)
        if not check["ok"]:
            return {"installed": False, "plugin_id": plugin_id, "version": version, "problems": check["problems"]}

        if check["replaces"]:
            removal = self.uninstall(plugin_id)
            if not removal["uninstalled"]:
                return {"installed": False, "plugin_id": plugin_id, "version": version,
                        "problems": [f"the installed {check['replaces']} could not be removed: {removal['reason']}"]}

        owned = marketplace_data.copy_package_into_install(plugin_id, version)
        record = plugins_data.read_installed_record() or {"plugins": []}
        record.setdefault("plugins", []).append({
            "id": plugin_id,
            "version": version,
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "owned": [path for path in owned.values() if path],
        })
        plugins_data.write_installed_record(record)
        return {
            "installed": True, "plugin_id": plugin_id, "version": version,
            "replaced": check["replaces"], "owned": owned, "restart_required": True, "problems": [],
        }

    # -- uninstall ----------------------------------------------------------------

    def uninstall(self, plugin_id: str) -> dict:
        """Removes exactly what the ownership record says this plugin owns, and
        its record entry. Notes the plugin wrote into the vault stay: they are
        the operator's data, not the plugin's.

        A recorded path outside the two folders a plugin can own is never
        deleted -- the ownership record is a file on disk, and a tampered or
        corrupted one must not be able to point a delete at anything else."""
        record = plugins_data.read_installed_record() or {"plugins": []}
        entries = record.get("plugins") or []
        matching = [entry for entry in entries if isinstance(entry, dict) and entry.get("id") == plugin_id]
        if not matching:
            return {"uninstalled": False, "plugin_id": plugin_id, "reason": f"{plugin_id} is not installed"}

        allowed_roots = [root for root in (plugins_data.plugins_root(), marketplace_data.frontend_plugins_root()) if root]
        removed, refused = [], []
        for entry in matching:
            for path in entry.get("owned") or []:
                if any(_is_within(Path(path), root) and Path(path).resolve() != root.resolve() for root in allowed_roots):
                    if marketplace_data.remove_tree(path):
                        removed.append(path)
                else:
                    refused.append(path)

        record["plugins"] = [entry for entry in entries if entry not in matching]
        plugins_data.write_installed_record(record)
        return {
            "uninstalled": True, "plugin_id": plugin_id, "removed": removed,
            "refused_outside_plugin_folders": refused, "restart_required": True, "reason": None,
        }

    # -- internals ------------------------------------------------------------------

    def _installed_versions(self) -> dict[str, str]:
        try:
            record = plugins_data.read_installed_record() or {}
        except (OSError, ValueError):
            return {}
        return {
            str(entry.get("id")): str(entry.get("version") or "")
            for entry in record.get("plugins") or [] if isinstance(entry, dict) and entry.get("id")
        }

    def _unmet_requirements(self, plugin_id: str, manifest: dict) -> list[str]:
        """Each requirement names a Tool or an installed plugin; `a|b` is met by
        either. A plugin replacing its own older version does not count as
        installed for this purpose."""
        present = set(skills_data.list_categories()) | (set(self._installed_versions()) - {plugin_id})
        unmet = []
        for requirement in manifest.get("requires") or []:
            alternatives = [option.strip() for option in str(requirement).split("|") if option.strip()]
            if alternatives and not present.intersection(alternatives):
                unmet.append(f"requires {' or '.join(alternatives)}, which this install does not have")
        return unmet
