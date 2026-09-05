"""REQ-SB-80's real data/ tree shape, as plain dataclasses -- a dataclass
per file kind, no validation library, rather than introducing Pydantic
models for file data.

(The convention was originally inherited from `data_access/system/tools/
schema.py`, the abandoned MCP Tool -> Category -> Action layer removed on
2026-09-04. The convention outlived it and is kept deliberately.)
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SectionConfig:
    id: str
    name: str
    icon: str | None
    color: str | None
    subtitle: str | None
    description: str | None


@dataclass
class AgentConfig:
    id: str
    name: str
    type: str  # "worker" | "producer" | "expert" | "hub"
    is_background_agent: bool
    depends_on: list[str] = field(default_factory=list)
    provider_id: str | None = None
    skill_ids: list[str] = field(default_factory=list)
    icon: str | None = None
    color: str | None = None
    # Real Index ids (business/core/index/) this agent should consult
    # first when looking for data in the vault (2026-08-28).
    preferred_index_ids: list[str] = field(default_factory=list)
    # Free-text snippet describing how a Primary/delegating agent should
    # route to THIS agent -- e.g. "route quick, no-decision-needed capture
    # here; relay verbatim: `hermes -p <id> chat -q \"<content>\" -Q`"
    # (2026-09-03, operator: "link the Agent to primary with what you will
    # append"). Second-Brain-owned Registry metadata, same category as
    # icon/color -- never written to Hermes' own SOUL.md automatically;
    # surfaced as a suggestion on Artifacts import (artifact_import.py)
    # for the operator to explicitly apply to the TARGET's own Primary
    # SOUL.md, never silently.
    primary_routing_snippet: str | None = None


@dataclass
class Agent:
    config: AgentConfig
    soul: str  # real prompt/identity text (soul.md contents)
    section_id: str | None  # None for Background/Agents entries


@dataclass
class SkillVisual:
    icon: str | None


@dataclass
class SkillConfig:
    id: str
    name: str
    description: str
    category: str  # the real Hermes skill category folder this came from
    mutates: bool = True  # real vs. read-only capability -- gates schedulability


@dataclass
class Skill:
    config: SkillConfig
    visual: SkillVisual
    tool_id: str


@dataclass
class ToolConfig:
    id: str
    name: str
    description: str
    icon: str | None


@dataclass
class Tool:
    config: ToolConfig
    skills: dict[str, Skill] = field(default_factory=dict)


@dataclass
class ProviderConfig:
    id: str
    name: str
    endpoint: str
    credential: str
    model: str


@dataclass
class Registry:
    """The RegistryLoader's real, in-memory result -- every entity the
    data/ tree held at the moment the loader last finished successfully.
    Not yet wired to any consumer (agents_map_adapter.py etc. keep reading
    their own hardcoded/existing sources for now) -- that migration is a
    separate follow-up pass, not part of this one."""
    sections: dict[str, SectionConfig] = field(default_factory=dict)
    agents: dict[str, Agent] = field(default_factory=dict)
    tools: dict[str, Tool] = field(default_factory=dict)
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
