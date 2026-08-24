"""Business-layer wrapper over data_access/hermes_definitions.py (2026-08-22
-- view-only mirror of Hermes' real Agent/Skill definitions; see that
module's own docstring for the "why files, not the API" reasoning and
ADR-001's "not ours to own" scoping). Thin by design, same shape as
hermes_status.py's own router-never-reaches-into-data_access split
(ADR-005 point 5) -- the only real job here is turning dataclasses into
plain dicts for the API layer.
"""
from __future__ import annotations

from dataclasses import asdict

from app.data_access import hermes_definitions


def list_agents() -> list[dict]:
    return [asdict(agent) for agent in hermes_definitions.list_agents()]


def get_agent(agent_id: str) -> dict | None:
    agent = hermes_definitions.get_agent(agent_id)
    return asdict(agent) if agent is not None else None
