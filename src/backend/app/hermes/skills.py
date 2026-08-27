"""CRUD for a Hermes profile's own custom SKILL.md-based skills -- this
app's own product Skills (capture-notes, azure-kb-writer, etc.), never
Hermes' `hermes skills` hub/registry mechanism (that installs THIRD-
PARTY skills from skills.sh/GitHub/etc -- a completely different,
unrelated concept that only shares the word "skill"). No CLI command
exists for authoring one of these -- direct file I/O is the only real
mechanism, matching how every one of this app's own Skills has always
been written.

Real layout:
    <profile_dir>/skills/<category>/<slug>/
        SKILL.md          -- YAML frontmatter (name/description/version)
                              + the real prompt/instructions body
        scripts/*          -- any real supporting script files
"""
from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml

from app.hermes.config import HermesConfig

_FRONTMATTER_BLOCK = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


@dataclass
class HermesSkill:
    id: str  # "<category>/<slug>"
    name: str
    description: str
    version: str
    category: str
    slug: str
    icon: str = "bolt"
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


def _skill_from_md(skill_md: Path) -> HermesSkill:
    frontmatter = _read_frontmatter(skill_md)
    category = skill_md.parent.parent.name
    slug = skill_md.parent.name
    return HermesSkill(
        id=f"{category}/{slug}",
        name=str(frontmatter.get("name") or slug),
        description=str(frontmatter.get("description") or ""),
        version=str(frontmatter.get("version") or ""),
        category=category,
        slug=slug,
    )


class HermesSkills:
    def __init__(self, config: HermesConfig) -> None:
        self._config = config

    def _profile_dir(self, agent_id: str) -> Path:
        home = self._config.home_path
        return home if agent_id == "default" else home / "profiles" / agent_id

    def _skill_dir(self, agent_id: str, skill_id: str) -> Path:
        category, _, slug = skill_id.partition("/")
        return self._profile_dir(agent_id) / "skills" / category / slug

    def get_all(self, agent_id: str) -> list[HermesSkill]:
        """Every real skill for this profile. `_disabled-*` archive
        folders are siblings of `skills/`, not nested inside it, so this
        naturally excludes them without special-case filtering."""
        skills_root = self._profile_dir(agent_id) / "skills"
        if not skills_root.is_dir():
            return []
        return [_skill_from_md(p) for p in sorted(skills_root.glob("*/*/SKILL.md"))]

    def find_by_id(self, agent_id: str, skill_id: str) -> HermesSkill | None:
        skill_md = self._skill_dir(agent_id, skill_id) / "SKILL.md"
        return _skill_from_md(skill_md) if skill_md.is_file() else None

    def read(self, agent_id: str, skill_id: str) -> str | None:
        """The real, full SKILL.md text (frontmatter + prompt body) --
        distinct from find_by_id's parsed-frontmatter-only summary."""
        skill_md = self._skill_dir(agent_id, skill_id) / "SKILL.md"
        try:
            return skill_md.read_text(encoding="utf-8")
        except OSError:
            return None

    def create(
        self, agent_id: str, category: str, slug: str, skill_md_content: str,
        scripts: dict[str, str] | None = None,
    ) -> HermesSkill:
        skill_dir = self._profile_dir(agent_id) / "skills" / category / slug
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")
        for rel_path, content in (scripts or {}).items():
            script_path = skill_dir / rel_path
            script_path.parent.mkdir(parents=True, exist_ok=True)
            script_path.write_text(content, encoding="utf-8")
        return _skill_from_md(skill_dir / "SKILL.md")

    def update(
        self, agent_id: str, skill_id: str, *,
        skill_md_content: str | None = None, scripts: dict[str, str] | None = None,
    ) -> HermesSkill | None:
        skill_dir = self._skill_dir(agent_id, skill_id)
        if not (skill_dir / "SKILL.md").is_file():
            return None
        if skill_md_content is not None:
            (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")
        for rel_path, content in (scripts or {}).items():
            script_path = skill_dir / rel_path
            script_path.parent.mkdir(parents=True, exist_ok=True)
            script_path.write_text(content, encoding="utf-8")
        return _skill_from_md(skill_dir / "SKILL.md")

    def delete(self, agent_id: str, skill_id: str) -> bool:
        """Hard delete -- removes the skill's whole folder from disk."""
        skill_dir = self._skill_dir(agent_id, skill_id)
        if not skill_dir.is_dir():
            return False
        shutil.rmtree(skill_dir)
        return True
