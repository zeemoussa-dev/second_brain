"""The Plugin API -- the ONE module a plugin may import from the framework
(`ADR-022`). Everything a plugin can do to or with the framework goes through
here; `scripts/check_plugin_imports.py` rejects a plugin that imports anything
else from `app`.

It is a facade, not a re-export: a plugin gets plain dicts, lists and tuples
back, never a framework entity class. An entity's fields change whenever the
framework needs them to, and a plugin holding the class would break on that
change while its `framework_api` still matched.

v1 is exactly what the first plugin (My Day) uses, and nothing more. A new
capability is added here when a plugin needs one; removing or changing an
existing one is a `FRAMEWORK_API` major bump, after which every installed
plugin built against the old major is refused rather than half-working.
"""
from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter

from app.business.core.agents.agent_manager import AgentManager
from app.business.core.pipelines.pipeline_manager import PipelineManager
from app.business.core.sections.section_manager import SectionManager
from app.business.core.vault.vault_manager import VaultManager
from app.business.hermes.client import get_client
from app.data_access import vault_writer

FRAMEWORK_API = 1

# `enricher(subject_kind, frontmatter, tags) -> {field: value}`. Cockpit calls it
# while composing a view of a note (`BUG-063` seam).
SubjectEnricher = Callable[[str, dict, list[str]], dict]

# `matcher(subject_kind, subject) -> {"experts": [agent_id, ...], "fallback_agent_id": agent_id | None}`,
# where `subject` is `{"stem", "frontmatter", "tags"}`. Cockpit asks it which agents
# to recommend for a conversation about that note, and which agent answers when
# nobody brought in fits (`BUG-063` seam).
AgentMatcher = Callable[[str, dict], dict]


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
