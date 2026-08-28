"""Raw data access for Skill CONTENT -- Hermes-Provisioning/skills/
<category>/<slug>/{SKILL.md, scripts/*} -- the checked-in "skills
template repo" (operator, 2026-08-28: "we do a copy for all Skills
inside our System"), the canonical source SkillManager authors into and
deploys FROM. Distinct from a live Hermes profile's own deployed copy
(app.hermes.skills.HermesSkills) and from a Skill's Registry metadata
(data_access/tools.py). Zero business interpretation here -- tool
grouping, deployment targets, and sync/import behaviour are all
SkillManager's job.
"""
from __future__ import annotations

import shutil
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SKILLS_ROOT = _REPO_ROOT / "Hermes-Provisioning" / "skills"


def list_categories() -> list[str]:
    """Every real category folder that already exists -- doubles as
    sync_from_hermes' own trusted-category allowlist (operator,
    2026-08-28: "category allowlist... a human adds [a category] to the
    list later" -- adding one here IS that, since it's a real folder a
    human creates, not a separate config value)."""
    if not _SKILLS_ROOT.is_dir():
        return []
    return sorted(p.name for p in _SKILLS_ROOT.iterdir() if p.is_dir())


def _find_skill_dir(skill_id: str) -> Path | None:
    if not _SKILLS_ROOT.is_dir():
        return None
    for category_dir in _SKILLS_ROOT.iterdir():
        if not category_dir.is_dir():
            continue
        candidate = category_dir / skill_id
        if (candidate / "SKILL.md").is_file():
            return candidate
    return None


def list_skill_ids() -> list[str]:
    """Every real skill slug with a SKILL.md, across every category --
    slugs are globally unique (matches Agent.json's own skill_ids
    convention, confirmed live 2026-08-28)."""
    if not _SKILLS_ROOT.is_dir():
        return []
    return sorted(
        p.name
        for category_dir in _SKILLS_ROOT.iterdir() if category_dir.is_dir()
        for p in category_dir.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()
    )


def category_of(skill_id: str) -> str | None:
    skill_dir = _find_skill_dir(skill_id)
    return skill_dir.parent.name if skill_dir else None


def read_skill_md(skill_id: str) -> str | None:
    skill_dir = _find_skill_dir(skill_id)
    if skill_dir is None:
        return None
    try:
        return (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    except OSError:
        return None


def write_skill_md(category: str, skill_id: str, content: str) -> None:
    skill_dir = _SKILLS_ROOT / category / skill_id
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")


def list_scripts(skill_id: str) -> dict[str, str]:
    """{relative script path -> content}, skipping __pycache__."""
    skill_dir = _find_skill_dir(skill_id)
    if skill_dir is None:
        return {}
    scripts_root = skill_dir / "scripts"
    if not scripts_root.is_dir():
        return {}
    out: dict[str, str] = {}
    for path in scripts_root.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            rel = str(path.relative_to(scripts_root))
            try:
                out[rel] = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
    return out


def write_script(category: str, skill_id: str, rel_path: str, content: str) -> None:
    path = _SKILLS_ROOT / category / skill_id / "scripts" / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def delete_skill_dir(skill_id: str) -> None:
    skill_dir = _find_skill_dir(skill_id)
    if skill_dir is not None:
        shutil.rmtree(skill_dir, ignore_errors=True)
