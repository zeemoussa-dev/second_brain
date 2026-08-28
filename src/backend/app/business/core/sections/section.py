from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Section:
    id: str
    name: str
    icon: str | None
    color: str | None
    subtitle: str | None
    description: str | None
    folders: list[str]
    fallback_agent_id: str | None
    agent_ids: list[str]
