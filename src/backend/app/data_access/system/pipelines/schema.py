"""Pipeline / Step schema (2026-08-22).

A Pipeline is one real, Hermes-run cron flow, broken into its own real
Steps (operator: "We have 4 Steps Each Step will be Converted a worker...
Write down the details in the Json Definition With Depends on to Render
Correctly") -- Second Brain's OWN definition of what a cron job's stages
are and how they depend on each other, not something Hermes itself
reports (Hermes only knows about the one Skill it ran, not this
breakdown). Genuinely independent data, same footing as Provider/Tool
(data_access/system/), not part of the Hermes mirror (ADR-003).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PipelineStep:
    id: str
    name: str
    description: str
    depends_on: list[str] = field(default_factory=list)
    # "worker" (default) or "producer" -- operator, 2026-08-22, corrected
    # same day: "The link should be to the last node the one that writes
    # the data to the KB those are the ones that actually bring the data
    # in the vault" -- NOT the entry point that merely fetches raw
    # external data (that was this comment's first, wrong version). Per
    # step, not per pipeline: the terminal step (the sink -- nothing else
    # depends on it) is the one that actually performs the real vault
    # write, so it alone is the Producer; every step before it, including
    # the raw Outlook fetch, only moves/transforms data that isn't in the
    # vault yet, and stays a worker.
    type: str = "worker"


@dataclass
class Pipeline:
    id: str
    name: str
    description: str
    section: str  # real Section name (section_registry), e.g. "Data Gatherer"
    steps: list[PipelineStep] = field(default_factory=list)
