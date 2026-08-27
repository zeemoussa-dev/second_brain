"""Business-layer wrapper over the Hermes library's Profile (Agent) CRUD
-- the only real job here is turning dataclasses into plain dicts for
the API layer (ADR-005 point 5's own router-never-reaches-into-
data_access split)."""
from __future__ import annotations

from dataclasses import asdict

from app.business.hermes.client import get_client


def get_all() -> list[dict]:
    return [asdict(agent) for agent in get_client().profiles.get_all()]


def find_by_id(agent_id: str) -> dict | None:
    agent = get_client().profiles.find_by_id(agent_id)
    return asdict(agent) if agent is not None else None
