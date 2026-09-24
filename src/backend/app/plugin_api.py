"""The Plugin API -- the ONE module a plugin may import from the framework
(`ADR-022`). Everything a plugin can do to or with the framework goes through
here; `scripts/check_plugin_imports.py` rejects a plugin that imports anything
else from `app`.

It is a facade, not a re-export: a plugin gets plain dicts, lists and tuples
back, never a framework entity class. An entity's fields change whenever the
framework needs them to, and a plugin holding the class would break on that
change while its `framework_api` still matched.

v1 was exactly what the first plugin (My Day) used. v2 adds what the Entities
plugin needs, so the framework can stop knowing its business concepts: Cockpit
agent matchers, services between plugins, People folders, seed data files and
reading/writing them (`api.data`), read access to Expert agents and Sections --
and, in a package, Templates.

v3 lets a plugin contribute a Cockpit TAB, not just a row in its info panel
(`PluginUi.cockpitTabs`, frontend-side). The Cockpit is a generic component for
chatting with agents about a subject; what an email or a meeting IS belongs to
the plugin that understands it (operator, 2026-09-24: "Cockpit is the framework
Peice as Component for Agents to chat its Used inside myDay which understands
Emails and Calendar"). A Thread's own emails is My Day's tab, not a framework
one. A new capability is added here when a plugin needs one. The host loads only
plugins built for its exact `FRAMEWORK_API`, so a plugin that relies on a
capability is never loaded by a framework that lacks it, and every installed
plugin is republished when the version moves.
"""
from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter

from app.business.core.agents.agent_manager import AgentManager
from app.business.core.pipelines.pipeline_manager import PipelineManager
from app.business.core.sections.section_manager import SectionManager
from app.business.core.vault.vault_manager import VaultManager
from app.business.hermes.client import get_client
from app.data_access import seed_data, vault_writer

FRAMEWORK_API = 3

# `enricher(subject_kind, frontmatter, tags) -> {field: value}`. Cockpit calls it
# while composing a view of a note (`BUG-063` seam).
SubjectEnricher = Callable[[str, dict, list[str]], dict]

# `matcher(subject_kind, subject) -> {"experts": [agent_id, ...], "fallback_agent_id": agent_id | None}`,
# where `subject` is `{"stem", "frontmatter", "tags"}`. Cockpit asks it which agents
# to recommend for a conversation about that note, and which agent answers when
# nobody brought in fits (`BUG-063` seam).
AgentMatcher = Callable[[str, dict], dict]


def _relative_path(path: str, what: str) -> str:
    """`path` with `/` separators, or ValueError when it could point outside
    the folder it is relative to."""
    text = str(path or "")
    parts = text.replace("\\", "/").split("/")
    if not text.strip() or text.startswith(("/", "\\")) or ":" in text or ".." in parts:
        raise ValueError(f"{what} {path!r} must be a relative path")
    return "/".join(part for part in parts if part)


class VaultApi:
    def index(self) -> dict[str, dict]:
        """Every indexed note keyed by filename stem, each with `path`, `stem`,
        `frontmatter`, `tags` and its wikilinks. The mapping is a copy, but its
        entries are the framework's live index: treat them as read-only."""
        return dict(VaultManager().get_index())

    def notes_in_kind(self, kind: str) -> list:
        """Paths of the notes in one kind folder under `Work/` (e.g. `Tasks`)."""
        return vault_writer.list_notes_in_kind_folder(kind)

    def read_note(self, path) -> tuple[dict, str]:
        """`(frontmatter, body)` for one note."""
        return vault_writer.read_note(path)


class PipelinesApi:
    def get(self, pipeline_id: str) -> dict | None:
        """The fields a plugin may rely on, or None for an unknown pipeline."""
        pipeline = PipelineManager().get_by_id(pipeline_id)
        if pipeline is None:
            return None
        return {
            "id": pipeline.id,
            "name": pipeline.name,
            "cron_job_id": pipeline.cron_job_id,
            "cron_profile_id": pipeline.cron_profile_id,
        }


class AgentsApi:
    def list_experts(self) -> list[dict]:
        """Every Expert agent: `id`, `name`, `description`, `section_id`."""
        return [
            {"id": agent.id, "name": agent.name, "description": agent.description, "section_id": agent.section_id}
            for agent in AgentManager().get_expert_agents()
        ]


class SectionsApi:
    def get(self, section_id: str) -> dict | None:
        """`id`, `name` and `fallback_agent_id`, or None for an unknown Section."""
        section = SectionManager().get_by_id(section_id)
        if section is None:
            return None
        return {"id": section.id, "name": section.name, "fallback_agent_id": section.fallback_agent_id}


class DataFilesApi:
    """Reads and writes this plugin's own data files under the App Database
    Folder -- only the ones it registered with `register_seed_data_file`, so
    a plugin never reaches the framework's or another plugin's files."""

    def __init__(self, registered_files: list[str]) -> None:
        self._registered_files = registered_files

    def _registered(self, relative_path: str) -> str:
        normalized = _relative_path(relative_path, "data file")
        if normalized not in self._registered_files:
            raise PermissionError(f"{normalized!r} is not a data file this plugin registered")
        return normalized

    def read_text(self, relative_path: str) -> str | None:
        """None when the file does not exist yet."""
        return seed_data.read_text(self._registered(relative_path))

    def write_text(self, relative_path: str, content: str) -> None:
        seed_data.write_text(self._registered(relative_path), content)


class HermesApi:
    def run_cron_job(self, job_name: str, profile_id: str | None = None) -> bool:
        """Fires a Hermes cron job now. Returns once the trigger is sent, not
        when the job finishes."""
        return get_client().cli.run_cron_job(job_name, profile_id)


class PluginApi:
    """What a plugin's `register(api)` receives. One instance per plugin, so
    everything a plugin registers is attributable to that plugin."""

    def __init__(self, plugin_id: str) -> None:
        self.plugin_id = plugin_id
        self.vault = VaultApi()
        self.pipelines = PipelinesApi()
        self.hermes = HermesApi()
        self.agents = AgentsApi()
        self.sections = SectionsApi()
        self.routers: list[APIRouter] = []
        self.subject_enrichers: list[SubjectEnricher] = []
        self.agent_matchers: list[AgentMatcher] = []
        self.services: dict[str, object] = {}
        self.people_folders: list[str] = []
        self.seed_data_files: list[str] = []
        self.data = DataFilesApi(self.seed_data_files)

    def register_router(self, router: APIRouter) -> None:
        """Mounted under `/plugins/<plugin_id>/` once registration succeeds.
        A plugin whose `register` raises has none of its routers mounted."""
        self.routers.append(router)

    def register_subject_enricher(self, enricher: SubjectEnricher) -> None:
        """Lets Cockpit ask this plugin about a note it is showing, instead of
        Cockpit knowing a business concept itself. Cockpit applies a returned
        field only where the note carries no value for it: an enricher fills
        gaps, and never overrides what the note itself says."""
        self.subject_enrichers.append(enricher)

    def register_agent_matcher(self, matcher: AgentMatcher) -> None:
        """Lets Cockpit ask this plugin which agents fit a conversation about a
        note, instead of Cockpit knowing a business concept itself. Returned
        ids that are not registered agents are ignored, and a matcher that
        raises is skipped."""
        self.agent_matchers.append(matcher)

    def register_people_folders(self, folders: list[str]) -> None:
        """Vault folders under which this plugin's notes keep People (e.g.
        `Work/Customers`): Cockpit looks for a Person's note in
        `<folder>/**/People/`, then the flat `Work/People/`. Vault-relative
        paths only; anything that could leave the vault is refused."""
        for folder in folders:
            normalized = _relative_path(folder, "people folder")
            if normalized not in self.people_folders:
                self.people_folders.append(normalized)

    def register_seed_data_file(self, relative_path: str) -> None:
        """A file under the App Database Folder that this plugin's Skills
        need before their first run (e.g. `Settings/Entities.md`). An
        artifact export carries it empty, and an import creates it empty
        when a deployed Skill mentions its name -- never over an existing
        file."""
        normalized = _relative_path(relative_path, "seed data file")
        if normalized not in self.seed_data_files:
            self.seed_data_files.append(normalized)

    def provide_service(self, name: str, implementation: object) -> None:
        """Offers a capability to other plugins by name, so a plugin never
        imports another plugin. The name must be this plugin's id, a dot and
        a name (`entities.customers`), so no plugin can take another's name."""
        prefix = f"{self.plugin_id}."
        if not name.startswith(prefix) or name == prefix:
            raise ValueError(f"service {name!r} must be named '{prefix}<name>'")
        if name in self.services:
            raise ValueError(f"service {name!r} is provided twice")
        self.services[name] = implementation

    def get_service(self, name: str) -> object | None:
        """Another loaded plugin's service, or None when that plugin is not
        installed or did not load. Ask when the service is needed, not in
        `register`: plugins load in install order, so the provider may load
        after the plugin asking."""
        # Imported here: the plugin manager imports this module.
        from app.business.core.plugins.plugin_manager import PluginManager
        return PluginManager().get_service(name)
