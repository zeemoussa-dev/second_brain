"""Second Brain's own single AgentSummary/AgentDetail dict-shaping for a
real Agent (agent.py) -- built once here (2026-08-28) so agents_router.py
(the Agents Map's own /agents surface) and agents_map_adapter.py
(Cockpit's own mention-resolution/moderator routing, which needs the same
shape for both real agents and Pipelines) never independently re-derive
the same mapping. Previously each kept its own copy: agents_router.py's
own `_to_summary_dict`/`_to_detail_dict`, and agents_map_adapter.py's own
hand-rolled `_to_summary`/`get_agent_detail` real-agent branch composing
straight from Hermes+Registry+visual instead of going through
AgentManager at all.
"""
from __future__ import annotations

from app.business.core.agents.agent import Agent
from app.business.core.sections.section_manager import SectionManager
from app.business.hermes.client import get_client

_section_manager = SectionManager()


def to_summary_dict(agent: Agent) -> dict:
    return {
        "id": agent.id, "name": agent.name, "type": agent.type,
        "section_id": agent.section_id, "is_background_agent": agent.is_background_agent,
        "icon": agent.icon, "color": agent.color, "description": agent.description,
        "working_mode": agent.working_mode, "depends_on": agent.depends_on,
        "branch_target_agent_id": None,
    }


def to_detail_dict(agent: Agent) -> dict:
    hermes_agent = get_client().profiles.find_by_id(agent.id)
    capabilities = [
        {"id": s.id, "label": s.name, "kind": "skill", "tool": s.category}
        for s in (hermes_agent.skills if hermes_agent is not None else [])
    ]
    section = _section_manager.get_by_id(agent.section_id)
    scope = agent.scope or {}
    return {
        "id": agent.id, "name": agent.name, "type": agent.type,
        "settings": [], "capabilities": capabilities,
        "section_id": agent.section_id,
        "section_name": section.name if section is not None else agent.section_id,
        "provider_id": agent.managed_by, "provider_name": agent.managed_by, "provider_available": True,
        "keywords": [], "working_mode": agent.working_mode,
        "scope": list(scope.get("folders", [])) + list(scope.get("tags", [])),
        "is_background_agent": agent.is_background_agent,
        "icon": agent.icon, "color": agent.color, "description": agent.description,
        "prompt": agent.prompt, "guardrails": agent.guardrails or "",
        "tools": agent.tools,
        "depends_on": agent.depends_on,
        "preferred_index_ids": agent.preferred_index_ids,
        "primary_routing_snippet": agent.primary_routing_snippet,
    }
