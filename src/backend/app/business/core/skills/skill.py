from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Skill:
    id: str  # the real slug -- globally unique across every category
             # (matches Agent.json's own skill_ids convention)
    name: str
    description: str
    category: str  # the real Hermes-Provisioning/skills/<category> folder this lives under
    tool_id: str | None = None  # the owning Tool grouping; None until assigned
    mutates: bool = True
    origin: str = "second-brain"  # "second-brain" (authored here) | "jarvis" (synced in, unattributed)
    deployed_to: list[str] = field(default_factory=list)  # real Hermes profile ids this is currently pushed to
    icon: str = "bolt"
    created_at: str = ""
    updated_at: str | None = None
