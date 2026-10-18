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

import logging
import re

from fastapi import APIRouter

from app import plugin_api
from app.business.core.plugins.plugin import DISABLED, INVALID, LOADED, REFUSED, Plugin
from app.data_access import plugins as plugins_data

PLUGIN_ROUTE_PREFIX = "/plugins"

_logger = logging.getLogger(__name__)

# An id becomes a folder name, a package name and a URL segment. Anything
# looser would let an ownership record point outside the plugins folder
# ("../x") or produce a route prefix nobody can type.
_VALID_PLUGIN_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")



def is_valid_plugin_id(plugin_id: str) -> bool:
    return bool(_VALID_PLUGIN_ID.match(plugin_id))


_load_report: list[Plugin] = []

# What Cockpit asks to fill in a subject's fields (`BUG-063` seam), rebuilt by
# every `load_all` from the plugins that loaded. Only plugins contribute: the
# framework itself knows no business concept to enrich a subject with.
_plugin_subject_enrichers: list[plugin_api.SubjectEnricher] = []
# Cockpit's agent matchers (`BUG-063` seam) and the services plugins offer one
# another, rebuilt the same way.
_plugin_agent_matchers: list[plugin_api.AgentMatcher] = []
_plugin_services: dict[str, object] = {}
_plugin_people_folders: list[str] = []
_plugin_seed_data_files: list[str] = []
# The Actions the loaded plugins contribute to the one catalogue, as the
# definitions they registered -- never entities: what an Action IS belongs
# to ActionManager, which composes these on top of the stored ones when the
# catalogue is read.
_plugin_actions: list[dict] = []
# The tag namespaces the loaded plugins own, by prefix, each holding the
# `plugin_id` that registered it and the callable to ask for its current
# entries -- never the entries themselves (`ADR-037`). Keyed by prefix because
# one namespace has exactly one owner, and keyed state is what lets the second
# claim on a prefix be spotted at all.
_plugin_tag_namespaces: dict[str, dict] = {}


def _one_owner_per_tag_namespace(loaded_apis: list[plugin_api.PluginApi]) -> dict[str, dict]:
    """The registered namespaces, first registration winning its prefix.

    Aggregation is the only place one plugin's registration meets another's,
    so a cross-plugin collision can be seen nowhere else -- and by the time it
    is seen, the plugin that caused it has already imported, registered and
    mounted its routes. Refusing the later claim and logging it naming both
    plugins is therefore the strongest answer available, and it is the right
    one anyway: a prefix changing hands because of install order would be
    worse than a prefix that stays where it was."""
    owned: dict[str, dict] = {}
    for api in loaded_apis:
        for registration in api.tag_namespaces:
            namespace = registration["namespace"]
            owner = owned.get(namespace)
            if owner is not None:
                _logger.warning(
                    "plugin %r claims tag namespace %r, which plugin %r already owns: the later "
                    "registration is refused and %r keeps the namespace",
                    registration["plugin_id"], namespace, owner["plugin_id"], owner["plugin_id"],
                )
                continue
            owned[namespace] = registration
    return owned


class PluginManager:
    def load_all(self) -> list[tuple[str, APIRouter]]:
        """Loads every plugin in the ownership record, in record order, and
        returns the `(prefix, router)` pairs to mount. Never raises for a
        plugin's own failure. The record's order is the install order, so a
        plugin is loaded after anything it was installed on top of.

        `requires` is recorded but not yet enforced: resolving "graph or
        outlook" needs the Marketplace's view of what is installed, which
        arrives with it (`REQ-SB-91` Phase 4)."""
        global _load_report, _plugin_subject_enrichers, _plugin_agent_matchers, _plugin_services
        global _plugin_people_folders, _plugin_seed_data_files, _plugin_actions
        global _plugin_tag_namespaces
        report: list[Plugin] = []
        mounts: list[tuple[str, APIRouter]] = []

        try:
            record = plugins_data.read_installed_record()
        except (OSError, ValueError) as exc:
            _plugin_subject_enrichers, _plugin_agent_matchers, _plugin_services = [], [], {}
            _plugin_people_folders, _plugin_seed_data_files, _plugin_actions = [], [], []
            _plugin_tag_namespaces = {}
            _load_report = [Plugin(
                id="installed.json", name="Installed plugins record", version="",
                framework_api=None, status=INVALID,
                reason=f"the ownership record cannot be read, so no plugin was loaded: {exc}",
            )]
            return []

        seen: set[str] = set()
        loaded_apis: list[plugin_api.PluginApi] = []
        for entry in (record or {}).get("plugins") or []:
            plugin, plugin_mounts = self._load_one(entry, seen, loaded_apis)
            report.append(plugin)
            mounts.extend(plugin_mounts)

        _load_report = report
        _plugin_subject_enrichers = [enricher for api in loaded_apis for enricher in api.subject_enrichers]
        _plugin_agent_matchers = [matcher for api in loaded_apis for matcher in api.agent_matchers]
        _plugin_services = {name: service for api in loaded_apis for name, service in api.services.items()}
        _plugin_people_folders = list(dict.fromkeys(folder for api in loaded_apis for folder in api.people_folders))
        _plugin_seed_data_files = list(dict.fromkeys(path for api in loaded_apis for path in api.seed_data_files))
        _plugin_actions = [action for api in loaded_apis for action in api.actions]
        _plugin_tag_namespaces = _one_owner_per_tag_namespace(loaded_apis)
        return mounts

    def get_load_report(self) -> list[Plugin]:
        return list(_load_report)

    def get_subject_enrichers(self) -> list[plugin_api.SubjectEnricher]:
        """In plugin install order."""
        return list(_plugin_subject_enrichers)

    def get_agent_matchers(self) -> list[plugin_api.AgentMatcher]:
        """In plugin install order."""
        return list(_plugin_agent_matchers)

    def get_service(self, name: str) -> object | None:
        return _plugin_services.get(name)

    def get_people_folders(self) -> list[str]:
        """Vault folders holding People, from every loaded plugin, without duplicates."""
        return list(_plugin_people_folders)

    def get_seed_data_files(self) -> list[str]:
        """Seed data files from every loaded plugin, without duplicates."""
        return list(_plugin_seed_data_files)

    def get_actions(self) -> list[dict]:
        """The Action definitions every loaded plugin registered, in plugin
        install order, each stamped with the `plugin_id` that registered it.
        A plugin that failed contributes none, and an uninstalled one is
        simply absent from the next load -- which is what makes a plugin's
        Actions disappear with it, with nothing stored to clean up."""
        return list(_plugin_actions)

    def get_tag_namespaces(self) -> list[dict]:
        """Every tag namespace the loaded plugins own, in plugin install
        order: its `namespace` prefix, the `plugin_id` that registered it, and
        the `entries` callable to ask for what it currently holds. The
        callable is handed back unasked -- whoever needs the entries calls it
        then, which is the entire reason a namespace is registered as a
        callable rather than as data (`ADR-037`).

        Nothing here gates the tag-keyed index. That index keys every
        `<namespace>/<slug>` tag the vault holds, registered or not; a
        namespace appearing in this list only means a name can now be turned
        into one of those tags."""
        return [dict(registration) for registration in _plugin_tag_namespaces.values()]

    def _load_one(
        self, entry: object, seen: set[str], loaded_apis: list[plugin_api.PluginApi],
    ) -> tuple[Plugin, list[tuple[str, APIRouter]]]:
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
        # Taken only now: whatever a plugin registered before its own
        # `register` raised belongs to a plugin that is disabled.
        loaded_apis.append(api)
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
