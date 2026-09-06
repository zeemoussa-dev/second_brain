from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BlueprintAgent:
    id: str
    name: str
    type: str  # "worker" | "producer" | "expert" | "hub"
    skill_ids: list[str] = field(default_factory=list)
    icon: str | None = None
    color: str | None = None
    model: str | None = None
    reasoning_effort: str | None = None
    clone_from: str = "default"
    soul: str | None = None  # relative path within the Blueprint
    # A PEER is reachable from the Primary profile: installing it appends
    # `primary_routing_snippet` to this machine's Primary SOUL.md, which is
    # what makes Primary relay to it at all. Without that the Agent exists,
    # runs, and is simply never reached.
    peer: bool = False
    primary_routing_snippet: str | None = None


@dataclass
class Blueprint:
    id: str
    name: str
    description: str
    # The Blueprint FORMAT itself.
    schema_version: int
    # This Blueprint's own content -- bump when the Section's shape changes.
    version: int
    section_name: str
    section_icon: str | None = None
    section_color: str | None = None
    agents: list[BlueprintAgent] = field(default_factory=list)
    # Set only when the Blueprint failed to parse -- still returned rather
    # than silently dropped, so a broken Blueprint is visible in the library
    # instead of invisible.
    error: str | None = None

    @property
    def skill_ids(self) -> list[str]:
        """Every Skill this Blueprint needs, across all its Agents."""
        return sorted({skill for agent in self.agents for skill in agent.skill_ids})
