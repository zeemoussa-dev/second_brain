"""Shapes Hermes' real Agent/Skill definitions (app/hermes/definitions.py,
ADR-003) into the Agents Map frontend's existing AgentSummary/AgentDetail/
SkillSummary contract (2026-08-22, operator-directed retrofit of
features/agents-map/ -- "Retrofit agents-map itself").

Deliberately kept OUT of app/hermes/definitions.py/business/hermes/
definitions.py, which stay a pure, honest mirror of what Hermes itself
reports (ADR-003) -- everything below is Second Brain's OWN presentation
decision about how to visualize that data in a UI built for a different,
richer, now-retired agent model, not something Hermes reports.

Real per-agent Type/working_mode, operator's own explicit call
(2026-08-22): "Core is a pipeline, every step in the core is a worker,
File Agent and Notes Agents are Producers, no Experts Yet" -- Primary
(the WhatsApp router) and opp-manager (a pipeline-like Opportunity flow)
are `worker`; notes-manager/files-manager (they PRODUCE captured
artifacts into the vault) are `producer`. `working_mode` is `autonomous`
for all four (operator: "All the same mode" -> autonomous) -- none of
today's real agents are mid-task-supervised the way the old model's
`supervised` was meant.

"No Experts Yet" stopped being true 2026-08-24 (operator: "We need to
change the type of Agents that Are Experts to be Experts instead of
Workers as well") -- every domain-knowledge specialist in the Compass
and Azure families (the hub agent itself plus its own narrower
specialists) is real `type: "expert"` now, matching `AgentType`'s own
long-since-built `'expert'` value on the frontend (AgentDetailPanel's
own "gaps" tab, CreateAgentWizardModal's own Expert-creation flow) --
built ahead of any real data ever using it. `opp-manager`/`notes-
manager`/`files-manager` stay `worker`/`producer`: they're pipeline-
style capture/action agents, not domain-knowledge specialists, a
different real category the operator drew this same line around
originally.

Fields with no honest Hermes equivalent (settings, keywords, scope,
guardrails, color, depends_on, branch_target_agent_id) are left empty/
null rather than fabricated -- never invented data standing in for
something Hermes doesn't actually report.

**2026-08-25 (REQ-SB-80):** Type/Section/depends_on/is_background_agent/
display_name -- every one of these Second-Brain-OWN presentation
decisions above -- moved OFF the hand-maintained hardcoded dicts that
used to live in this file and onto the real `data/` tree
(`app/data_access/registry/loader.py`'s `RegistryLoader`): every agent
added used to mean a hand-edit here; now it means a real file under
`<vault>/.second-brain/data/Sections/<Section>/Agents/<agent>/
Agent.json` (2026-08-28: one merged file, was Agent-config.json +
Agent-visual.json). An agent not yet present in the Registry (not yet
migrated, or the Registry hasn't finished booting) falls through to the
exact same defaults the old dicts' own `.get(agent_id, default)` calls
always used -- worker / Data Gatherer / no deps / not background / the
raw Hermes name -- so this is a storage change, not a behavior change,
for anything not yet in the tree. `agent_visual_registry`/`_visual`
below is UNCHANGED -- icon/color stays a separately CRUD-editable store
(VisualPicker's own live edit path), not yet folded into this same
push/pull loop.

**2026-08-28:** `list_agent_summaries`/`get_agent_detail`'s real-agent
composition (everything this file used to derive by hand from the
Registry -- type/section/depends_on/is_background_agent/display_name)
now delegates to `AgentManager` (`business/core/agents/agent_manager.py`)
instead of re-deriving it here a second time; `_registry_agent` below
survives only for `list_agent_skill_summaries`' own skill-id lookup,
which has no AgentManager equivalent yet. Pipelines stay this file's own
concern (AgentManager deliberately doesn't cover them), so `_visual`/
`_short_excerpt`/`_pipeline_to_summary` are unchanged.
"""
from __future__ import annotations

import re

from app.business import agent_visual_registry
from app.business.core.agents.agent_manager import AgentManager
from app.business.core.agents.agent_presentation import to_detail_dict, to_summary_dict
from app.business.core.pipelines.pipeline_manager import PipelineManager
from app.business.core.sections.section_manager import SectionManager
from app.business.hermes.client import get_client
from app.data_access.registry import loader as registry_loader
from app.data_access.registry.schemas import Agent as RegistryAgent

_WORKING_MODE = "autonomous"
_section_manager = SectionManager()
_pipeline_manager = PipelineManager()
_agent_manager = AgentManager()


def _registry_agent(agent_id: str) -> RegistryAgent | None:
    """The real Registry entry for this agent, or None if it hasn't been
    migrated into the data/ tree yet (or the RegistryLoader hasn't
    finished its first successful boot) -- every caller below treats
    None exactly like the old dicts' own "key absent" case."""
    registry = registry_loader.get_registry()
    if registry is None:
        return None
    return registry.agents.get(agent_id)


def _short_excerpt(text: str, max_len: int = 140) -> str:
    """Same real-first-sentence convention as app/hermes/definitions.py's own
    _first_sentence -- duplicated rather than cross-imported (this vault's
    own established pattern for small helpers, ADR-002), since a Pipeline's
    own description is Second Brain's data, not Hermes'."""
    text = (text or "").strip()
    if not text:
        return ""
    match = re.match(r"^(.*?[.!?])(\s|$)", text, re.DOTALL)
    sentence = match.group(1).strip() if match else text
    if len(sentence) > max_len:
        sentence = sentence[:max_len].rsplit(" ", 1)[0].rstrip(".,;:") + "…"
    return sentence


def _visual(agent_id: str, default_icon: str) -> tuple[str, str | None]:
    """Real per-agent icon/color override (2026-08-22, operator: "it
    should be writing data to the Json File as this is Second Brain View
    only Part no need to update hermes") -- agent_visual_registry.py is
    genuinely Hermes-independent (a plain agent_id -> {icon, color} JSON
    map, `.second-brain/agent_visuals.json`, untouched from the old
    architecture since it never depended on agent_registry.py's own
    records), so it needs zero changes to serve Hermes agent ids too.
    Falls back to the Hermes-derived default icon / no color when no
    override has ever been set for this agent."""
    override = agent_visual_registry.get_agent_visual(agent_id)
    return override.get("icon") or default_icon, override.get("color")


def update_agent_visual(agent_id: str, icon: str | None, color: str | None) -> dict | None:
    agent_visual_registry.set_agent_visual(agent_id, icon=icon, color=color)
    return get_agent_detail(agent_id)


def _registry_skill_catalog() -> dict[str, dict]:
    """id -> SkillSummary dict, from the RegistryLoader's real Tools/Skills
    catalog (REQ-SB-80) -- REPLACES the old app/hermes/definitions-derived
    version, which mirrored EVERY skill physically present under a
    profile's skills/ dir (~80 generic bundled ones every cloned profile
    carries -- apple-notes, imessage, github-*, etc, none of them
    relevant to this product) and set `tool` to the raw Hermes category
    folder name (e.g. "knowledge-base"), which never matched
    SkillsTree.tsx's own `SKILLS_TREE_TOOL_ORDER` ('Outlook'/'Vault'/
    'Web'/'Compass') -- confirmed live, 2026-08-25: every skill silently
    failed to render in any group, the whole Skills panel was empty for
    every agent. This catalog is deliberately small and curated (only
    the real Skills this app actually built), and `tool` is the owning
    Tool's own real display name, so it matches SkillsTree.tsx exactly."""
    registry = registry_loader.get_registry()
    if registry is None:
        return {}
    catalog: dict[str, dict] = {}
    for tool in registry.tools.values():
        for skill in tool.skills.values():
            catalog[skill.config.id] = {
                "id": skill.config.id,
                "name": skill.config.name,
                "description": skill.config.description,
                "tool": tool.config.name,
                "mutates": skill.config.mutates,
            }
    return catalog


def _pipeline_to_summary(pipeline) -> dict:
    """A Pipeline renders as ONE ordinary `worker` node on the map until
    the frontend's own pipelineJobTreeAdapter splices it into its real
    Step nodes (GET /agents/{id}/jobs) -- is_background_agent is False so
    it's actually visible on the ring beforehand, mirroring how
    email-capture-pipeline worked before this Pipeline replaced it."""
    icon, color = _visual(pipeline.id, "conveyor_belt")
    return {
        "id": pipeline.id,
        "name": pipeline.name,
        "type": "worker",
        "section_id": pipeline.section_id,
        "is_background_agent": False,
        "icon": icon,
        "color": color,
        "description": _short_excerpt(pipeline.description) or None,
        "working_mode": _WORKING_MODE,
        "depends_on": [],
        "branch_target_agent_id": None,
    }


def list_pipeline_refs() -> list[dict]:
    """Every real Pipeline's own {id, name} -- lets the frontend discover
    which /agents entries need their own /jobs fetch+splice, without
    guessing from AgentSummary's own icon/type fields."""
    return [{"id": p.id, "name": p.name} for p in _pipeline_manager.get_all()]


def list_agent_summaries() -> list[dict]:
    """Every real, addressable Agent (via AgentManager, same composition
    `agents_router.py`'s own `GET /agents` uses) plus every Pipeline, in
    one flat roster -- Cockpit's own @mention resolution
    (`business/cockpit/chat_turn.py`) and moderator routing
    (`business/cockpit/moderator.py`) need both kinds together (a
    question can route to a Pipeline just like any worker). Hub agents
    excluded (2026-08-28), same reasoning as the map: a Hub isn't a real
    addressable expert/worker, it's the Section's own entry point, so it
    was never a real candidate for @mention or routing either."""
    return [to_summary_dict(a) for a in _agent_manager.get_all(exclude_types=["hub"])] + list_pipeline_summaries()


def list_pipeline_summaries() -> list[dict]:
    """Just the Pipeline-shaped half of list_agent_summaries() above --
    AgentManager (business/core/agents/) does NOT cover Pipelines (a
    separate concept, deliberately not folded in yet), so
    agents_router.py composes real agents via AgentManager plus this for
    the map's own Pipeline nodes."""
    return [_pipeline_to_summary(p) for p in _pipeline_manager.get_all()]


def get_pipeline_job_tree(pipeline_id: str) -> list[dict] | None:
    """JobTreeEntry[]-shaped: one entry per real Step, `depends_on`
    referencing sibling Step ids directly (no pipeline-id prefix needed --
    scoped to one Pipeline's own job-tree fetch, same as the original
    email-capture-pipeline Job ids were bare)."""
    pipeline = _pipeline_manager.get_by_id(pipeline_id)
    if pipeline is None:
        return None
    return [
        {
            "id": step.id, "name": step.name, "depends_on": step.depends_on,
            "section_id": pipeline.section_id, "type": step.type,
        }
        for step in pipeline.steps
    ]


def get_agent_detail(agent_id: str) -> dict | None:
    pipeline = _pipeline_manager.get_by_id(agent_id)
    if pipeline is not None:
        section = _section_manager.get_by_id(pipeline.section_id)
        icon, color = _visual(pipeline.id, "conveyor_belt")
        return {
            "id": pipeline.id,
            "name": pipeline.name,
            "type": "worker",
            "settings": [],
            "capabilities": [],
            "section_id": pipeline.section_id,
            "section_name": section.name if section is not None else pipeline.section_id,
            "provider_id": None,
            "provider_name": None,
            "provider_available": True,
            "keywords": [],
            "working_mode": _WORKING_MODE,
            "scope": [],
            "is_background_agent": False,
            "icon": icon,
            "color": color,
            "description": _short_excerpt(pipeline.description) or None,
            "prompt": pipeline.description or None,
            "guardrails": "",
        }
    agent = _agent_manager.get_by_id(agent_id)
    if agent is None:
        return None
    return to_detail_dict(agent)


def list_all_skill_summaries() -> list[dict]:
    return list(_registry_skill_catalog().values())


def list_agent_skill_summaries(agent_id: str) -> list[dict] | None:
    """The agent's own real `skill_ids` (Agent.json), resolved
    against the curated Registry catalog -- 404 (`None`) only when the
    agent doesn't exist in Hermes at all; an agent that exists but has no
    distinctive Skill of its own (most of them, honestly) gets `[]`, not
    the old ~80-entry generic bundled-catalog dump."""
    if get_client().profiles.find_by_id(agent_id) is None:
        return None
    registry_agent = _registry_agent(agent_id)
    if registry_agent is None:
        return []
    catalog = _registry_skill_catalog()
    return [catalog[skill_id] for skill_id in registry_agent.config.skill_ids if skill_id in catalog]
