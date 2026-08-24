"""Reads Hermes' own real Agent (profile) and Skill definitions directly
from its local install (2026-08-22 -- operator's own explicit choice: read
live from Hermes' own files rather than a synced copy or its `hermes
serve` API, which today only exposes session/status data, not full
definitions).

Deliberately a display-only mirror, not a data-access layer Second Brain
owns (ADR-001's own "not ours to own" principle for Hermes/LangGraph data)
-- there is no local persistence here, every call re-reads the real files,
so this can never drift from what Hermes itself actually has configured.

Real layout (confirmed live, 2026-08-22, against this machine's own
install):
    <hermes_home>/                          -- the "default" profile IS
        SOUL.md                                the home dir itself, no
        config.yaml                            profile.yaml of its own
        skills/**/SKILL.md
    <hermes_home>/profiles/<name>/          -- every OTHER profile
        SOUL.md
        config.yaml
        profile.yaml                           -- has `description`;
        skills/**/SKILL.md                     absent on "default"

`_disabled-*` archive folders (skills moved off a profile so it can't use
them -- see MEMORY.md's own "removing a write-capable Skill from Primary"
entries) are siblings of `skills/`, not nested inside it, so the
`skills/**/SKILL.md` glob below naturally excludes them without any
special-case filtering.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from app.config import settings

_FRONTMATTER_BLOCK = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_PRIMARY_PROFILE_ID = "default"


@dataclass
class HermesSkill:
    id: str  # "<category>/<name>", e.g. "company-review/track-opportunities"
    name: str
    description: str
    version: str
    category: str
    icon: str = "bolt"
    source: str = "hermes"


@dataclass
class HermesAgent:
    id: str  # profile folder name, "default" for Primary
    name: str
    description: str  # full text -- the profile's own real description/SOUL.md excerpt
    # 2026-08-22 -- a genuinely SHORT excerpt of `description` above (its
    # own first real sentence, never fabricated), for contexts that need a
    # one-line summary rather than the full prompt-length text (map hover
    # card, Overview's own Description row). Operator: the hover card
    # showing the full text "should be description not the full prompt".
    short_description: str
    model: str
    provider: str
    reasoning_effort: str
    is_primary: bool
    skills: list[HermesSkill] = field(default_factory=list)
    icon: str = "smart_toy"
    source: str = "hermes"


def _read_frontmatter(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    match = _FRONTMATTER_BLOCK.match(text)
    if not match:
        return {}
    try:
        parsed = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _read_yaml_file(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


_SENTENCE_END = re.compile(r"^(.*?[.!?])(\s|$)", re.DOTALL)


def _first_sentence(text: str, max_len: int = 140) -> str:
    """The real first sentence of `text` -- never fabricated, just a
    genuine excerpt of the same real description/SOUL.md text. Falls back
    to a length-capped prefix if no sentence-ending punctuation is found
    (e.g. a description that's already a single short phrase)."""
    text = text.strip()
    if not text:
        return ""
    match = _SENTENCE_END.match(text)
    sentence = match.group(1).strip() if match else text
    if len(sentence) > max_len:
        sentence = sentence[:max_len].rsplit(" ", 1)[0].rstrip(".,;:") + "…"
    return sentence


def _soul_excerpt(profile_dir: Path, max_len: int = 280) -> str:
    """First real paragraph of SOUL.md, for profiles with no profile.yaml
    (only "default"/Primary today) -- never fabricated, empty if absent."""
    soul_path = profile_dir / "SOUL.md"
    try:
        text = soul_path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    first_paragraph = text.split("\n\n", 1)[0].strip()
    if len(first_paragraph) > max_len:
        first_paragraph = first_paragraph[:max_len].rsplit(" ", 1)[0] + "…"
    return first_paragraph


def _read_skills(profile_dir: Path) -> list[HermesSkill]:
    skills_root = profile_dir / "skills"
    if not skills_root.is_dir():
        return []
    skills: list[HermesSkill] = []
    for skill_md in sorted(skills_root.glob("*/*/SKILL.md")):
        frontmatter = _read_frontmatter(skill_md)
        category = skill_md.parent.parent.name
        slug = skill_md.parent.name
        skills.append(
            HermesSkill(
                id=f"{category}/{slug}",
                name=str(frontmatter.get("name") or slug),
                description=str(frontmatter.get("description") or ""),
                version=str(frontmatter.get("version") or ""),
                category=category,
            )
        )
    return skills


def _read_agent(profile_id: str, profile_dir: Path) -> HermesAgent:
    is_primary = profile_id == _PRIMARY_PROFILE_ID
    profile_meta = _read_yaml_file(profile_dir / "profile.yaml")
    description = str(profile_meta.get("description") or "").strip()
    if not description:
        description = _soul_excerpt(profile_dir) if is_primary else ""

    config = _read_yaml_file(profile_dir / "config.yaml")
    model_section = config.get("model") or {}
    model = str(model_section.get("default") or "")
    provider = str(model_section.get("provider") or "")
    reasoning_effort = str((config.get("agent") or {}).get("reasoning_effort") or "medium")

    return HermesAgent(
        id=profile_id,
        name="Primary" if is_primary else profile_id,
        description=description,
        short_description=_first_sentence(description),
        model=model,
        provider=provider,
        reasoning_effort=reasoning_effort,
        is_primary=is_primary,
        skills=_read_skills(profile_dir),
        icon="hub" if is_primary else "smart_toy",
    )


def list_agents() -> list[HermesAgent]:
    """Every real profile found on disk -- "default" (Primary) plus every
    profiles/<name> directory. Returns [] (never raises) if hermes_home_path
    doesn't exist on this machine, e.g. running the backend somewhere
    without a local Hermes install."""
    home = settings.hermes_home_path
    if not home.is_dir():
        return []

    agents = [_read_agent(_PRIMARY_PROFILE_ID, home)]
    profiles_root = home / "profiles"
    if profiles_root.is_dir():
        for profile_dir in sorted(p for p in profiles_root.iterdir() if p.is_dir()):
            agents.append(_read_agent(profile_dir.name, profile_dir))
    return agents


def get_agent(agent_id: str) -> HermesAgent | None:
    home = settings.hermes_home_path
    if not home.is_dir():
        return None
    profile_dir = home if agent_id == _PRIMARY_PROFILE_ID else home / "profiles" / agent_id
    if not profile_dir.is_dir():
        return None
    return _read_agent(agent_id, profile_dir)
