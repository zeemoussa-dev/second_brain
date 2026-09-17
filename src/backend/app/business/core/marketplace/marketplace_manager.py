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
from app.business.core.templates.template_manager import TemplateManager
from app.data_access import marketplace as marketplace_data
from app.data_access import plugins as plugins_data
from app.data_access import skills as skills_data

_VERSION = re.compile(r"^\d+\.\d+\.\d+$")
_HELD_OPEN_HINT = (
    "Something is holding its files open -- for example a sync client such as OneDrive, "
    "or an editor. Try again once it has let go."
)


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
            "templates": {"install": [], "keep": []},
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
        templates = self._package_templates(plugin_id, version, problems)
        template_manager = TemplateManager()
        result["templates"] = {
            "install": [template_id for template_id in templates if not template_manager.has_template(template_id)],
            "keep": [template_id for template_id in templates if template_manager.has_template(template_id)],
        }

        result["ok"] = not problems
        return result

    def install(self, plugin_id: str, version: str) -> dict:
        """Installs one published version, replacing any other installed version
        of the same plugin. Re-runs preflight itself and changes nothing when it
        fails -- it never trusts a preview the client may be holding.

        The installed version is never destroyed before the new one is in place
        (`BUG-065`): the package is copied into a work folder first, the
        installed pieces are moved aside whole, the new pieces moved in, and
        only then is the old version deleted, as far as the OS allows. A failure
        before the swap completes puts everything back."""
        check = self.preflight(plugin_id, version)
        if not check["ok"]:
            return self._not_installed(plugin_id, version, check["problems"])

        try:
            targets = marketplace_data.install_targets(plugin_id)
            marketplace_data.sweep_work_folders(plugin_id)
            staged = marketplace_data.stage_package(plugin_id, version)
        except OSError as exc:
            return self._not_installed(plugin_id, version, [f"the package could not be copied into this install: {exc}"])

        moved_aside: dict[str, Path] = {}
        placed: list[str] = []
        try:
            for part, target in targets.items():
                aside = marketplace_data.move_aside(target)
                if aside is not None:
                    moved_aside[part] = aside
            for part, source in staged.items():
                if source is not None:
                    marketplace_data.move_into_place(source, targets[part])
                    placed.append(part)
        except OSError as exc:
            self._put_back(targets, staged, moved_aside, placed)
            return self._not_installed(plugin_id, version, [
                f"the installed version could not be replaced, so nothing was changed: {exc}. "
                f"{_HELD_OPEN_HINT}"
            ])

        record = plugins_data.read_installed_record() or {"plugins": []}
        record["plugins"] = [
            entry for entry in record.get("plugins") or []
            if not (isinstance(entry, dict) and entry.get("id") == plugin_id)
        ]
        templates = self._package_templates(plugin_id, version, [])
        record["plugins"].append({
            "id": plugin_id,
            "version": version,
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "owned": [str(targets[part]) for part in placed],
            "templates": sorted(templates),
        })
        plugins_data.write_installed_record(record)
        leftovers = [path for aside in moved_aside.values() for path in marketplace_data.discard_tree(aside)]
        installed_templates, kept_templates, template_problems = self._install_templates(templates)
        return {
            "installed": True, "plugin_id": plugin_id, "version": version, "replaced": check["replaces"],
            "owned": {part: (str(targets[part]) if part in placed else None) for part in targets},
            "templates": {"installed": installed_templates, "kept": kept_templates},
            "leftovers": leftovers, "restart_required": True, "problems": template_problems,
        }

    # -- uninstall ----------------------------------------------------------------

    def uninstall(self, plugin_id: str) -> dict:
        """Removes exactly what the ownership record says this plugin owns, and
        its record entry. Notes the plugin wrote into the vault stay: they are
        the operator's data, not the plugin's.

        A recorded path outside the two folders a plugin can own is never
        deleted -- the ownership record is a file on disk, and a tampered or
        corrupted one must not be able to point a delete at anything else.

        Every owned piece is moved aside before anything is deleted, so when one
        cannot be moved the rest are put back and nothing changes (`BUG-065`)."""
        record = plugins_data.read_installed_record() or {"plugins": []}
        entries = record.get("plugins") or []
        matching = [entry for entry in entries if isinstance(entry, dict) and entry.get("id") == plugin_id]
        if not matching:
            return {"uninstalled": False, "plugin_id": plugin_id, "in_use": False, "reason": f"{plugin_id} is not installed"}

        allowed_roots = [root for root in (plugins_data.plugins_root(), marketplace_data.frontend_plugins_root()) if root]
        to_remove: list[Path] = []
        refused: list[str] = []
        for entry in matching:
            for path in entry.get("owned") or []:
                if any(_is_within(Path(path), root) and Path(path).resolve() != root.resolve() for root in allowed_roots):
                    to_remove.append(Path(path))
                else:
                    refused.append(path)

        marketplace_data.sweep_work_folders(plugin_id)
        moved_aside: list[tuple[Path, Path]] = []
        try:
            for path in to_remove:
                aside = marketplace_data.move_aside(path)
                if aside is not None:
                    moved_aside.append((path, aside))
        except OSError as exc:
            for path, aside in reversed(moved_aside):
                try:
                    marketplace_data.move_into_place(aside, path)
                except OSError:
                    pass
            return {
                "uninstalled": False, "plugin_id": plugin_id, "in_use": True,
                "reason": f"{plugin_id} could not be removed, so nothing was changed: {exc}. {_HELD_OPEN_HINT}",
            }

        record["plugins"] = [entry for entry in entries if entry not in matching]
        plugins_data.write_installed_record(record)
        leftovers = [path for _, aside in moved_aside for path in marketplace_data.discard_tree(aside)]
        return {
            "uninstalled": True, "plugin_id": plugin_id, "removed": [str(path) for path, _ in moved_aside],
            "refused_outside_plugin_folders": refused, "leftovers": leftovers,
            # Notes written against these Templates stay in the vault, so the
            # Templates stay too; the operator removes one deliberately.
            "templates_left_in_place": sorted({t for entry in matching for t in entry.get("templates") or []}),
            "restart_required": True, "reason": None,
        }

    # -- internals ------------------------------------------------------------------

    def _package_templates(self, plugin_id: str, version: str, problems: list[str]) -> dict[str, dict]:
        """The package's valid Templates; every invalid one is named in `problems`."""
        try:
            templates = marketplace_data.read_package_templates(plugin_id, version)
        except (OSError, ValueError) as exc:
            problems.append(f"the package's Templates cannot be read: {exc}")
            return {}
        valid: dict[str, dict] = {}
        template_manager = TemplateManager()
        for template_id, data in templates.items():
            if not is_valid_plugin_id(template_id):
                problems.append(f"Template folder {template_id!r} is not a valid Template id")
            elif not isinstance(data, dict):
                problems.append(f"Template {template_id!r} is not a JSON object")
            elif "id" in data and data["id"] != template_id:
                problems.append(f"Template {template_id!r} declares id {data['id']!r}")
            elif reason := template_manager.validate_template(template_id, data):
                problems.append(f"Template {template_id!r} is not valid on this framework: {reason}")
            else:
                valid[template_id] = data
        return valid

    def _install_templates(self, templates: dict[str, dict]) -> tuple[list[str], list[str], list[str]]:
        """Writes each Template this install does not have and adopts the
        rest as they are. Returns (installed, kept, problems); a Template that
        cannot be written does not undo the install -- it is reported."""
        installed, kept, problems = [], [], []
        template_manager = TemplateManager()
        for template_id, data in templates.items():
            try:
                if template_manager.install_if_missing(template_id, data):
                    installed.append(template_id)
                else:
                    kept.append(template_id)
            except OSError as exc:
                problems.append(f"Template {template_id!r} could not be written: {exc}")
        return installed, kept, problems

    def _not_installed(self, plugin_id: str, version: str, problems: list[str]) -> dict:
        return {"installed": False, "plugin_id": plugin_id, "version": version, "problems": list(problems)}

    def _put_back(self, targets: dict[str, Path], staged: dict[str, Path | None],
                  moved_aside: dict[str, Path], placed: list[str]) -> None:
        """Undoes a swap that failed part-way: takes out what was moved in, returns
        what was moved aside, and deletes the staging copy."""
        for part in placed:
            marketplace_data.discard_tree(targets[part])
        for part, aside in moved_aside.items():
            try:
                marketplace_data.move_into_place(aside, targets[part])
            except OSError:
                pass
        for source in staged.values():
            if source is not None:
                marketplace_data.discard_tree(source)

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
