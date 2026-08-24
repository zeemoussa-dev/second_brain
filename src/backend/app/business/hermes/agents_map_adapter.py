"""Shapes Hermes' real Agent/Skill definitions (hermes_definitions.py,
ADR-003) into the Agents Map frontend's existing AgentSummary/AgentDetail/
SkillSummary contract (2026-08-22, operator-directed retrofit of
features/agents-map/ -- "Retrofit agents-map itself").

Deliberately kept OUT of hermes_definitions.py/business/hermes/
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
"""
from __future__ import annotations

import re

from app.business import agent_visual_registry, section_registry
from app.data_access import hermes_definitions
from app.data_access.system.pipelines import registry as pipeline_registry

_AGENT_TYPE: dict[str, str] = {
    "default": "worker",
    "opp-manager": "worker",
    "notes-manager": "producer",
    "files-manager": "producer",
    "compass-expert": "expert",
    "compass-pricing-expert": "expert",
    "compass-solutions": "expert",
    "compass-models-expert": "expert",
    "azure-expert": "expert",
    "azure-services-expert": "expert",
    "azure-enterprise-architect": "expert",
    "azure-data-architect": "expert",
    "azure-infra-architect": "expert",
    "azure-calculator": "expert",
    "macc-expert": "expert",
}
_WORKING_MODE = "autonomous"
_SECTION_NAME = "Data Gatherer"

# Real per-agent Section override (2026-08-23, operator: "more the Azure
# Calculator to Technology Section... Opp Manager to Sales, and Notes and
# file Manager to Liberian") -- every individual Hermes-mirrored agent
# used to land in ONE hardcoded Section (_SECTION_NAME below) regardless
# of what it actually does; this is the first real per-agent placement.
# Deliberately a plain dict here (not routed through section_registry's
# own persisted `assignments`, ADR-014) -- that store is scoped to the
# now-fully-retired Second-Brain-native agent model (agent_registry.py's
# own 2026-08-22 emptying) and was never wired to read for Hermes agent
# ids; this dict is this adapter's own equivalent of _AGENT_TYPE above,
# same shape, same reasoning. An agent id absent here (e.g. "default"/
# Primary) falls through to _SECTION_NAME, i.e. Data Gatherer -- the
# operator's own explicit fallback ("bring the rest... to the Data
# Gathering"), true by construction rather than needing its own entry.
_AGENT_SECTION: dict[str, str] = {
    "azure-calculator": "Technology",
    "opp-manager": "Sales",
    "notes-manager": "Librarian",
    "files-manager": "Librarian",
    "compass-expert": "Technology",
    "compass-pricing-expert": "Technology",
    "compass-solutions": "Technology",
    "compass-models-expert": "Technology",
    "azure-expert": "Technology",
    "azure-services-expert": "Technology",
    "azure-enterprise-architect": "Technology",
    "azure-data-architect": "Technology",
    "azure-infra-architect": "Technology",
    "macc-expert": "Sales",
}

# Real agent-to-agent dependency edges (2026-08-24, operator: "We will
# have Compass Expert Depends on 3 Other Agents") -- the first REAL use
# of `AgentSummary.depends_on` for individual (non-Pipeline) agents;
# layoutAgents.ts's own tree-layout/dependency-line rendering already
# exists and works generically off this field (confirmed by reading it
# directly -- it was never Pipeline-specific, just never fed real data
# for a plain agent before now). Each of Compass Expert's own 3
# specialists depends ON it (matches DependencyEdge's own real
# direction -- `fromAgentId` a `depends_on` predecessor -> `toAgentId`
# the dependent successor that receives from it -- the same direction a
# Pipeline step's own `depends_on` already uses), so Compass Expert
# renders as the tree's real root with its own 3 children fanning out
# under it, all within the Technology Section above.
_AGENT_DEPENDS_ON: dict[str, list[str]] = {
    "compass-pricing-expert": ["compass-expert"],
    "compass-solutions": ["compass-expert"],
    "compass-models-expert": ["compass-expert"],
    # Azure Expert family (2026-08-24, operator: "We will build now Azure
    # Expert Agent, He will have many Agents under it") -- a THREE-level
    # chain, one level deeper than Compass's own 2-level family:
    # azure-expert -> {azure-services-expert, azure-enterprise-architect,
    # azure-calculator} -> azure-enterprise-architect's own further
    # {azure-data-architect, azure-infra-architect}. azure-calculator
    # itself moved here from being independently, directly reachable (see
    # its own SOUL.md) to a plain dependent, the same reachability shape
    # compass-pricing-expert already has under compass-expert.
    "azure-services-expert": ["azure-expert"],
    "azure-enterprise-architect": ["azure-expert"],
    "azure-calculator": ["azure-expert"],
    "azure-data-architect": ["azure-enterprise-architect"],
    "azure-infra-architect": ["azure-enterprise-architect"],
}

# Real per-agent background override (2026-08-24, operator: "move the
# Primary Chat to be Background Agent... Create a new Tab we call Chat
# where we can Chat with this Agent since it talks to everything") --
# Primary is the one agent general-purpose enough to warrant its own
# always-available top-level Chat tab (ChatPage.tsx) rather than living
# behind the map's per-Section AgentDetailPanel; moving it out of the
# map ring here is what makes that new surface its real, primary way to
# be reached, instead of a second, redundant path to the same chat.
# `is_background_agent: true` fully excludes an agent from
# layoutAgents.ts's own addressableAgents filter (2026-08-22, see the
# comment on `_to_summary` below) -- Primary becomes unreachable via the
# map ring entirely, by design, not merely de-emphasized.
_BACKGROUND_AGENTS: frozenset[str] = frozenset({"default"})


def _is_background_agent(agent_id: str) -> bool:
    return agent_id in _BACKGROUND_AGENTS


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


def _agent_section_name(agent_id: str) -> str:
    return _AGENT_SECTION.get(agent_id, _SECTION_NAME)


def _agent_section_id(agent_id: str) -> str:
    return _section_id_by_name(_agent_section_name(agent_id))


def _agent_type(agent_id: str) -> str:
    return _AGENT_TYPE.get(agent_id, "worker")


def _agent_depends_on(agent_id: str) -> list[str]:
    return _AGENT_DEPENDS_ON.get(agent_id, [])


def _short_excerpt(text: str, max_len: int = 140) -> str:
    """Same real-first-sentence convention as hermes_definitions.py's own
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


def _to_summary(agent: hermes_definitions.HermesAgent, section_id: str) -> dict:
    icon, color = _visual(agent.id, agent.icon)
    return {
        "id": agent.id,
        "name": agent.name,
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


def _skill_to_capability(skill: hermes_definitions.HermesSkill) -> dict:
    return {"id": skill.id, "label": skill.name, "kind": "skill", "tool": skill.category}


def _skill_to_summary(skill: hermes_definitions.HermesSkill) -> dict:
    # "mutates" is an honest true for every real Hermes Skill mirrored here
    # today -- each one (track-opportunities, capture-notes, capture-files,
    # summarize-and-tag-files, the document-extraction skills) genuinely
    # writes to the vault or an external system; there is no read-only
    # Hermes Skill in this mirror yet to contrast it against.
    return {"id": skill.id, "name": skill.name, "description": skill.description, "tool": skill.category, "mutates": True}


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
        _to_summary(agent, _agent_section_id(agent.id)) for agent in hermes_definitions.list_agents()
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
    agent = hermes_definitions.get_agent(agent_id)
    if agent is None:
        return None
    section_name = _agent_section_name(agent.id)
    section_id = _section_id_by_name(section_name)
    icon, color = _visual(agent.id, agent.icon)
    return {
        "id": agent.id,
        "name": agent.name,
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
    seen: dict[str, dict] = {}
    for agent in hermes_definitions.list_agents():
        for skill in agent.skills:
            seen.setdefault(skill.id, _skill_to_summary(skill))
    return list(seen.values())


def list_agent_skill_summaries(agent_id: str) -> list[dict] | None:
    agent = hermes_definitions.get_agent(agent_id)
    if agent is None:
        return None
    return [_skill_to_summary(s) for s in agent.skills]
