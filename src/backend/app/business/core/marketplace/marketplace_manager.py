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
from app.business.core.plugins import import_rules, screen_build
from app.business.core.plugins.plugin_manager import is_valid_plugin_id
from app.business.core.templates.template_manager import TemplateManager
from app.data_access import marketplace as marketplace_data
from app.data_access import plugin_sources
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
                    "source": self._installed_sources().get(plugin_id),
                    "packages": packages,
                })
        # A plugin installed straight from its repository has no published
        # package, so it would otherwise not be listed at all -- and an
        # operator could neither see nor uninstall it (`REQ-SB-92`).
        listed = {entry["id"] for entry in catalog}
        for plugin_id, entry in sorted(self._installed_entries().items()):
            if plugin_id in listed:
                continue
            catalog.append({
                "id": plugin_id,
                "installed_version": str(entry.get("version") or ""),
                "source": entry.get("source"),
                "packages": [],
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

        templates = self._package_templates(plugin_id, version, [])
        return self._place(plugin_id, version, targets, staged, templates,
                           replaced=check["replaces"], source=None)

    # -- install from a repository or folder (`REQ-SB-92`) ---------------------------

    def preflight_source(self, kind: str, location: str, ref: str | None = None) -> dict:
        """What installing this source would do, and everything that would stop
        it. Clones a repository, reads it, and discards the clone; changes
        nothing on the install."""
        fetched = None
        try:
            fetched = plugin_sources.fetch(kind, location, ref)
            return self._check_source(fetched)
        except plugin_sources.SourceError as exc:
            return self._source_result(kind, location, ref, problems=[str(exc)])
        finally:
            self._discard(fetched)

    def install_from_source(self, kind: str, location: str, ref: str | None = None) -> dict:
        """Installs a plugin straight from where it lives -- a repository at a
        ref, or a folder on this machine -- so a plugin never has to be
        published into the framework's own tree to be installable (`REQ-SB-92`).

        The same swap as a published install: nothing installed is destroyed
        before the new pieces are in place."""
        fetched = None
        try:
            fetched = plugin_sources.fetch(kind, location, ref)
            check = self._check_source(fetched)
            if not check["ok"]:
                return self._not_installed(check["plugin_id"], check["version"], check["problems"],
                                           source=check["source"])
            plugin_id, version = check["plugin_id"], check["version"]
            try:
                targets = marketplace_data.install_targets(plugin_id)
                marketplace_data.sweep_work_folders(plugin_id)
                staged = marketplace_data.stage_source(plugin_id, fetched["directory"])
            except OSError as exc:
                return self._not_installed(plugin_id, version,
                                           [f"the plugin could not be copied into this install: {exc}"],
                                           source=check["source"])
            templates = self._source_templates(fetched["directory"], [])
            return self._place(plugin_id, version, targets, staged, templates,
                               replaced=check["replaces"], source=check["source"])
        except plugin_sources.SourceError as exc:
            return self._not_installed(None, None, [str(exc)],
                                       source={"kind": kind, "location": location, "ref": ref})
        finally:
            self._discard(fetched)

    def update_from_source(self, plugin_id: str) -> dict:
        """Re-installs a plugin from the source it was installed from -- the same
        repository and ref, pulled again (`REQ-SB-92`). This is how a plugin is
        upgraded when its repository moves: the ref is usually a branch, so the
        version string can stay put while the code changes.

        A plugin installed from this framework's own Marketplace has no source
        to pull, and is upgraded by installing another published version."""
        entry = self._installed_entries().get(plugin_id)
        if entry is None:
            return self._not_installed(plugin_id, None, [f"{plugin_id} is not installed"])
        source = entry.get("source")
        if not isinstance(source, dict) or not source.get("location"):
            return self._not_installed(plugin_id, str(entry.get("version") or ""), [
                f"{plugin_id} was installed from this framework's Marketplace, which has no repository to pull. "
                "Install a published version, or install it once from its repository to track that instead."
            ])
        return self.install_from_source(source.get("kind", plugin_sources.GIT), source["location"], source.get("ref"))

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

    def _place(self, plugin_id: str, version: str, targets: dict[str, Path],
               staged: dict[str, Path | None], templates: dict[str, dict],
               *, replaced: str | None, source: dict | None) -> dict:
        """The swap every install goes through, whether the plugin came from the
        Marketplace or straight from its repository: move the installed pieces
        aside whole, move the new ones in, record what is owned, then delete the
        old ones (`BUG-065`). A failure before the swap completes puts
        everything back."""
        moved_aside: dict[str, Path] = {}
        placed: list[str] = []
        try:
            for part, target in targets.items():
                aside = marketplace_data.move_aside(target)
                if aside is not None:
                    moved_aside[part] = aside
            for part, staged_part in staged.items():
                if staged_part is not None:
                    marketplace_data.move_into_place(staged_part, targets[part])
                    placed.append(part)
        except OSError as exc:
            self._put_back(targets, staged, moved_aside, placed)
            return self._not_installed(plugin_id, version, [
                f"the installed version could not be replaced, so nothing was changed: {exc}. "
                f"{_HELD_OPEN_HINT}"
            ], source=source)

        record = plugins_data.read_installed_record() or {"plugins": []}
        record["plugins"] = [
            entry for entry in record.get("plugins") or []
            if not (isinstance(entry, dict) and entry.get("id") == plugin_id)
        ]
        entry = {
            "id": plugin_id,
            "version": version,
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "owned": [str(targets[part]) for part in placed],
            "templates": sorted(templates),
        }
        # Where it came from, so an install can say which repository and ref it
        # is running (`REQ-SB-92`). Absent means the framework's own Marketplace.
        if source is not None:
            entry["source"] = source
        record["plugins"].append(entry)
        plugins_data.write_installed_record(record)
        leftovers = [path for aside in moved_aside.values() for path in marketplace_data.discard_tree(aside)]
        installed_templates, kept_templates, template_problems = self._install_templates(templates)
        return {
            "installed": True, "plugin_id": plugin_id, "version": version, "replaced": replaced,
            "owned": {part: (str(targets[part]) if part in placed else None) for part in targets},
            "templates": {"installed": installed_templates, "kept": kept_templates},
            "source": source, "leftovers": leftovers, "restart_required": True, "problems": template_problems,
        }

    def _check_source(self, fetched: dict) -> dict:
        """Everything that would stop this source being installed, in the order
        that costs least: the manifest, then the layout and the import boundary,
        and only when those pass, the build (`REQ-SB-92` -- the three gates)."""
        directory = Path(fetched["directory"])
        source = fetched["source"]
        manifest = plugin_sources.read_manifest(directory)
        plugin_id = str(manifest.get("id") or "")
        version = str(manifest.get("version") or "")
        problems: list[str] = []

        if not is_valid_plugin_id(plugin_id):
            problems.append(f"plugin.json declares id {manifest.get('id')!r}, which is not a valid plugin id")
        if not _VERSION.match(version):
            problems.append(f"plugin.json declares version {manifest.get('version')!r}, which is not x.y.z")
        if manifest.get("framework_api") != plugin_api.FRAMEWORK_API:
            problems.append(
                f"built for framework API {manifest.get('framework_api')!r}; this framework provides "
                f"API {plugin_api.FRAMEWORK_API}"
            )
        if problems:
            return self._source_result(source["kind"], source["location"], source.get("ref"),
                                       problems=problems, plugin_id=plugin_id or None, version=version or None,
                                       source=source)

        backend_dir, ui_dir = directory / "backend", directory / "ui"
        has_templates = (directory / "templates").is_dir()
        if not (backend_dir.is_dir() or ui_dir.is_dir() or has_templates):
            problems.append("the plugin has none of backend/, ui/ or templates/")
        if backend_dir.is_dir() and not (backend_dir / "__init__.py").is_file():
            problems.append("backend/ has no __init__.py defining register(api)")
        if ui_dir.is_dir() and not (ui_dir / "index.tsx").is_file():
            problems.append("ui/ has no index.tsx default-exporting the plugin's screens")
        if backend_dir.is_dir():
            problems.extend(import_rules.check_plugin(backend_dir))
        if ui_dir.is_dir():
            problems.extend(import_rules.check_plugin_ui(ui_dir, plugin_id))
        problems.extend(self._unmet_requirements(plugin_id, manifest))
        templates = self._source_templates(directory, problems)

        if not problems and ui_dir.is_dir():
            failure = screen_build.build_screens(marketplace_data.frontend_root(), plugin_id, ui_dir, purpose="install")
            if failure:
                problems.append(failure)

        installed_version = self._installed_versions().get(plugin_id)
        template_manager = TemplateManager()
        return self._source_result(
            source["kind"], source["location"], source.get("ref"), problems=problems,
            plugin_id=plugin_id, version=version, source=source, installed_version=installed_version,
            templates={
                "install": [t for t in templates if not template_manager.has_template(t)],
                "keep": [t for t in templates if template_manager.has_template(t)],
            },
        )

    def _source_result(self, kind: str, location: str, ref: str | None, *, problems: list[str],
                       plugin_id: str | None = None, version: str | None = None, source: dict | None = None,
                       installed_version: str | None = None, templates: dict | None = None) -> dict:
        return {
            "ok": not problems, "problems": list(problems),
            "plugin_id": plugin_id, "version": version,
            "installed_version": installed_version,
            "replaces": installed_version if installed_version and installed_version != version else None,
            "templates": templates or {"install": [], "keep": []},
            "source": source or {"kind": kind, "location": location, "ref": ref},
        }

    def _discard(self, fetched: dict | None) -> None:
        if fetched is not None and fetched.get("temporary"):
            plugin_sources.discard(fetched["directory"])

    def _source_templates(self, source_dir: Path, problems: list[str]) -> dict[str, dict]:
        """A source folder's valid Templates; every invalid one is named in `problems`."""
        try:
            templates = marketplace_data.read_source_templates(source_dir)
        except (OSError, ValueError) as exc:
            problems.append(f"the plugin's Templates cannot be read: {exc}")
            return {}
        return self._valid_templates(templates, problems)

    def _package_templates(self, plugin_id: str, version: str, problems: list[str]) -> dict[str, dict]:
        """The package's valid Templates; every invalid one is named in `problems`."""
        try:
            templates = marketplace_data.read_package_templates(plugin_id, version)
        except (OSError, ValueError) as exc:
            problems.append(f"the package's Templates cannot be read: {exc}")
            return {}
        return self._valid_templates(templates, problems)

    def _valid_templates(self, templates: dict, problems: list[str]) -> dict[str, dict]:
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

    def _not_installed(self, plugin_id: str | None, version: str | None, problems: list[str],
                       *, source: dict | None = None) -> dict:
        return {"installed": False, "plugin_id": plugin_id, "version": version,
                "source": source, "problems": list(problems)}

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

    def _installed_entries(self) -> dict[str, dict]:
        try:
            record = plugins_data.read_installed_record() or {}
        except (OSError, ValueError):
            return {}
        return {
            str(entry.get("id")): entry
            for entry in record.get("plugins") or [] if isinstance(entry, dict) and entry.get("id")
        }

    def _installed_versions(self) -> dict[str, str]:
        return {plugin_id: str(entry.get("version") or "") for plugin_id, entry in self._installed_entries().items()}

    def _installed_sources(self) -> dict[str, dict | None]:
        """Where each installed plugin came from; None means this framework's own Marketplace."""
        return {plugin_id: entry.get("source") for plugin_id, entry in self._installed_entries().items()}

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
