from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Agent:
    id: str  # = the real Hermes profile folder name, shared key both sides
    name: str
    description: str | None  # Hermes profile.yaml `description`

    type: str  # "worker" | "producer" | "expert" | "hub"
    section_id: str | None
    is_background_agent: bool
    icon: str | None
    color: str | None

    working_mode: str  # "autonomous" | "human_in_loop" -- human_in_loop maps onto Hermes' own real approval.request/respond mechanism (not yet wired -- see AgentManager)
    managed_by: str  # "hermes" today -- room for a non-Hermes agent later

    model: str | None  # Hermes config.yaml model.default
    reasoning_effort: str | None  # Hermes config.yaml agent.reasoning_effort

    # All three compose into ONE real SOUL.md write (not yet built -- the
    # composer/decomposer scheme is separate follow-up work). `prompt`
    # here is the real, full SOUL.md text today, not yet split from
    # guardrails/scope.
    prompt: str | None
    guardrails: str | None
    scope: dict  # {"folders": [...], "tags": [...]}

    skill_ids: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    # Real Index ids (business/core/index/) this agent should consult
    # FIRST when looking for data in the vault -- pure association today
    # (2026-08-28, operator: "Just the association + prompt text"), no
    # dedicated consult-index tool/skill built yet. Woven into the real
    # SOUL.md as guidance text via AgentManager.regenerate_index_guidance_section
    # (explicit, separate call -- same shape as regenerate_specialists_section).
    preferred_index_ids: list[str] = field(default_factory=list)
