"""CRUD for Hermes' real Agent (profile) definitions -- profile.yaml/
config.yaml/SOUL.md, read directly off the local install. Every real
call re-reads the actual files, so this can never drift from what
Hermes itself has configured (no local persistence/caching here).

Real layout:
    <home>/                          -- the "default" profile IS the
        SOUL.md                         home dir itself, no profile.yaml
        config.yaml                     of its own
        skills/**/SKILL.md
    <home>/profiles/<name>/          -- every OTHER profile
        SOUL.md
        config.yaml
        profile.yaml                    -- has `description`; absent on
        skills/**/SKILL.md                 "default"

Profile CREATE/DELETE are NOT here -- `hermes profile create --clone`
does real work a plain mkdir can't replicate (copying config.yaml/.env/
SOUL.md/skills from the source profile), so those go through
HermesCLI/HermesClient instead. UPDATE (SOUL.md content, config.yaml
fields) has no CLI equivalent and is genuinely just a file write, so it
lives here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from app.hermes.config import HermesConfig
from app.hermes.skills import HermesSkill, HermesSkills

_PRIMARY_PROFILE_ID = "default"
_SENTENCE_END = re.compile(r"^(.*?[.!?])(\s|$)", re.DOTALL)


@dataclass
class HermesAgent:
    id: str  # profile folder name, "default" for the primary identity
    name: str
    description: str  # full text -- the profile's own real description/SOUL.md excerpt
    short_description: str  # a genuinely SHORT excerpt of `description`, never fabricated
    model: str
    provider: str
    reasoning_effort: str
    is_primary: bool
    skills: list[HermesSkill] = field(default_factory=list)
    icon: str = "smart_toy"
    source: str = "hermes"


def _read_yaml_file(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _first_sentence(text: str, max_len: int = 140) -> str:
    """The real first sentence of `text` -- never fabricated, just a
    genuine excerpt. Falls back to a length-capped prefix if no
    sentence-ending punctuation is found."""
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
    (only "default" today) -- never fabricated, empty if absent."""
    soul_path = profile_dir / "SOUL.md"
    try:
        text = soul_path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    first_paragraph = text.split("\n\n", 1)[0].strip()
    if len(first_paragraph) > max_len:
        first_paragraph = first_paragraph[:max_len].rsplit(" ", 1)[0] + "…"
    return first_paragraph


def _deep_merge(base: dict, patch: dict) -> dict:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


class HermesProfiles:
    def __init__(self, config: HermesConfig, skills: HermesSkills) -> None:
        self._config = config
        self._skills = skills

    def _profile_dir(self, agent_id: str) -> Path:
        home = self._config.home_path
        return home if agent_id == _PRIMARY_PROFILE_ID else home / "profiles" / agent_id

    def _read_agent(self, profile_id: str, profile_dir: Path) -> HermesAgent:
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
            skills=self._skills.get_all(profile_id),
            icon="hub" if is_primary else "smart_toy",
        )

    def get_all(self) -> list[HermesAgent]:
        """Every real profile found on disk -- "default" plus every
        profiles/<name> directory. Returns [] (never raises) if home_path
        doesn't exist, e.g. running somewhere without a local Hermes
        install."""
        home = self._config.home_path
        if not home.is_dir():
            return []
        agents = [self._read_agent(_PRIMARY_PROFILE_ID, home)]
        profiles_root = home / "profiles"
        if profiles_root.is_dir():
            for profile_dir in sorted(p for p in profiles_root.iterdir() if p.is_dir()):
                agents.append(self._read_agent(profile_dir.name, profile_dir))
        return agents

    def find_by_id(self, agent_id: str) -> HermesAgent | None:
        home = self._config.home_path
        if not home.is_dir():
            return None
        profile_dir = self._profile_dir(agent_id)
        if not profile_dir.is_dir():
            return None
        return self._read_agent(agent_id, profile_dir)

    def read_soul(self, agent_id: str) -> str | None:
        """The real, full SOUL.md content -- distinct from find_by_id's
        `description`, which is a short excerpt derived from it (or from
        profile.yaml, when present)."""
        soul_path = self._profile_dir(agent_id) / "SOUL.md"
        try:
            return soul_path.read_text(encoding="utf-8")
        except OSError:
            return None

    def write_soul(self, agent_id: str, content: str) -> None:
        """No CLI equivalent exists for this -- SOUL.md is genuinely
        just a file Hermes reads at session-creation time (MEMORY.md's
        own documented "injected once, never re-read mid-conversation"
        constraint)."""
        profile_dir = self._profile_dir(agent_id)
        profile_dir.mkdir(parents=True, exist_ok=True)
        (profile_dir / "SOUL.md").write_text(content, encoding="utf-8")

    def update(self, agent_id: str, config_patch: dict) -> HermesAgent | None:
        """Deep-merges `config_patch` into the profile's own config.yaml
        (e.g. {"model": {"default": "..."}, "agent": {"reasoning_effort":
        "..."}}) and writes it back. For the one config.yaml-independent
        field with a real CLI command (`description`), use
        HermesClient.describe_profile instead -- that one's real
        auxiliary-LLM `--auto` mode has no file-only equivalent."""
        profile_dir = self._profile_dir(agent_id)
        if not profile_dir.is_dir():
            return None
        config_path = profile_dir / "config.yaml"
        current = _read_yaml_file(config_path)
        merged = _deep_merge(current, config_patch)
        config_path.write_text(yaml.safe_dump(merged, sort_keys=False), encoding="utf-8")
        return self.find_by_id(agent_id)
