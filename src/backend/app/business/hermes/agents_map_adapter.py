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
Agent-config.json`. An agent not yet present in the Registry (not yet
migrated, or the Registry hasn't finished booting) falls through to the
exact same defaults the old dicts' own `.get(agent_id, default)` calls
always used -- worker / Data Gatherer / no deps / not background / the
raw Hermes name -- so this is a storage change, not a behavior change,
for anything not yet in the tree. `agent_visual_registry`/`_visual`
below is UNCHANGED -- icon/color stays a separately CRUD-editable store
(VisualPicker's own live edit path), not yet folded into this same
push/pull loop.
"""
from __future__ import annotations

import re

from app.business import agent_visual_registry, section_registry
from app.business.hermes.client import HermesAgent, HermesSkill, get_client
from app.data_access.registry import loader as registry_loader
from app.data_access.registry.schemas import Agent as RegistryAgent
from app.data_access.system.pipelines import registry as pipeline_registry

_WORKING_MODE = "autonomous"
_SECTION_NAME = "Data Gatherer"


def _registry_agent(agent_id: str) -> RegistryAgent | None:
    """The real Registry entry for this agent, or None if it hasn't been
    migrated into the data/ tree yet (or the RegistryLoader hasn't
    finished its first successful boot) -- every caller below treats
    None exactly like the old dicts' own "key absent" case."""
    registry = registry_loader.get_registry()
    if registry is None:
        return None
    return registry.agents.get(agent_id)


def _is_background_agent(agent_id: str) -> bool:
    agent = _registry_agent(agent_id)
    return agent.config.is_background_agent if agent is not None else False


def _agent_display_name(agent_id: str, fallback: str) -> str:
    agent = _registry_agent(agent_id)
    return agent.config.name if agent is not None else fallback


def _section_id_by_name(name: str) -> str:
    """A real Section's own id, resolved by name via section_registry
    (ADR-014) -- never a bare string literal, so a rename in Settings can
    never silently desync this mapping."""
    for section in section_registry.list_sections():
        if section["name"] == name:
            return section["id"]
    # First call before section_registry has ever seeded/created this name
    # -- create_section is idempotent-collapse-on-collision, always safe.
    return section_registry.create_section(name)["id"]


def _agent_section(agent_id: str) -> tuple[str, str]:
    """(section_id, section_name) -- from the Registry when this agent has
    been migrated into the data/ tree, else the same Data Gatherer default
    the old _AGENT_SECTION dict always fell back to for an unlisted id."""
    registry_entry = _registry_agent(agent_id)
    if registry_entry is not None and registry_entry.section_id is not None:
        registry = registry_loader.get_registry()
        section = registry.sections.get(registry_entry.section_id) if registry else None
        if section is not None:
            return section.id, section.name
    return _section_id_by_name(_SECTION_NAME), _SECTION_NAME


def _agent_section_id(agent_id: str) -> str:
    return _agent_section(agent_id)[0]


def _agent_type(agent_id: str) -> str:
    agent = _registry_agent(agent_id)
    return agent.config.type if agent is not None else "worker"


def _agent_depends_on(agent_id: str) -> list[str]:
    agent = _registry_agent(agent_id)
    return agent.config.depends_on if agent is not None else []


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


def _to_summary(agent: HermesAgent, section_id: str) -> dict:
    icon, color = _visual(agent.id, agent.icon)
    return {
        "id": agent.id,
        "name": _agent_display_name(agent.id, agent.name),
        "type": _agent_type(agent.id),
        "section_id": section_id,
        # False for every real Hermes agent EXCEPT the ones in
        # _BACKGROUND_AGENTS above (2026-08-22, corrected same day --
        # operator: "We Hided all Agents Panel in UI and Kept it only
        # live for Experts Bring it back for all agents"). The original
        # "specialists run as relayed workers, so they're background" idea
        # had a real side effect nobody wanted: layoutAgents.ts's own
        # addressableAgents filter excludes is_background_agent entries
        # from the map ring ENTIRELY, so opp-manager/notes-manager/
        # files-manager weren't just visually de-emphasized, they were
        # unclickable -- no way to ever open their own AgentDetailPanel.
        # Primary opting back into that same exclusion (2026-08-24) is a
        # deliberate, different reason: it now has its own dedicated
        # Chat tab, not accidental collateral from a shared "specialists
        # are background" rule.
        "is_background_agent": _is_background_agent(agent.id),
        "icon": icon,
        "color": color,
        # SHORT excerpt for the map's own hover card -- operator, 2026-08-22:
        # "it should be description not the full prompt". The full text is
        # `prompt` on AgentDetail (Settings tab / Overview), a separate field.
        "description": agent.short_description or None,
        "working_mode": _WORKING_MODE,
        "depends_on": _agent_depends_on(agent.id),
        "branch_target_agent_id": None,
    }


def _skill_to_capability(skill: HermesSkill) -> dict:
    return {"id": skill.id, "label": skill.name, "kind": "skill", "tool": skill.category}


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
        "section_id": _section_id_by_name(pipeline.section),
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
    return [{"id": p.id, "name": p.name} for p in pipeline_registry.list_pipelines()]


def list_agent_summaries() -> list[dict]:
    summaries = [
        _to_summary(agent, _agent_section_id(agent.id)) for agent in get_client().profiles.get_all()
    ]
    summaries.extend(_pipeline_to_summary(p) for p in pipeline_registry.list_pipelines())
    return summaries


def get_pipeline_job_tree(pipeline_id: str) -> list[dict] | None:
    """JobTreeEntry[]-shaped: one entry per real Step, `depends_on`
    referencing sibling Step ids directly (no pipeline-id prefix needed --
    scoped to one Pipeline's own job-tree fetch, same as the original
    email-capture-pipeline Job ids were bare)."""
    pipeline = pipeline_registry.get_pipeline(pipeline_id)
    if pipeline is None:
        return None
    section_id = _section_id_by_name(pipeline.section)
    return [
        {
            "id": step.id, "name": step.name, "depends_on": step.depends_on,
            "section_id": section_id, "type": step.type,
        }
        for step in pipeline.steps
    ]


def get_agent_detail(agent_id: str) -> dict | None:
    pipeline = pipeline_registry.get_pipeline(agent_id)
    if pipeline is not None:
        section_id = _section_id_by_name(pipeline.section)
        icon, color = _visual(pipeline.id, "conveyor_belt")
        return {
            "id": pipeline.id,
            "name": pipeline.name,
            "type": "worker",
            "settings": [],
            "capabilities": [],
            "section_id": section_id,
            "section_name": pipeline.section,
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
    agent = get_client().profiles.find_by_id(agent_id)
    if agent is None:
        return None
    section_id, section_name = _agent_section(agent.id)
    icon, color = _visual(agent.id, agent.icon)
    return {
        "id": agent.id,
        "name": _agent_display_name(agent.id, agent.name),
        "type": _agent_type(agent.id),
        "settings": [],
        "capabilities": [_skill_to_capability(s) for s in agent.skills],
        "section_id": section_id,
        "section_name": section_name,
        "provider_id": agent.provider or None,
        "provider_name": agent.provider or None,
        "provider_available": True,
        "keywords": [],
        "working_mode": _WORKING_MODE,
        "scope": [],
        "is_background_agent": _is_background_agent(agent.id),
        "icon": icon,
        "color": color,
        "description": agent.short_description or None,
        "prompt": agent.description or None,
        "guardrails": "",
    }


def list_all_skill_summaries() -> list[dict]:
    return list(_registry_skill_catalog().values())


def list_agent_skill_summaries(agent_id: str) -> list[dict] | None:
    """The agent's own real `skill_ids` (Agent-config.json), resolved
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
