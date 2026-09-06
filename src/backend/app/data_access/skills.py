"""Raw data access for Skill CONTENT -- the catalog at
business/core/skills/catalog/<tool>/<slug>/{SKILL.md, scripts/*}, the
canonical source SkillManager authors into and deploys FROM. Distinct
from a live Hermes profile's own deployed copy (app.hermes.skills.
HermesSkills) and from a Skill's Registry metadata (data_access/tools.py).
Zero business interpretation here -- tool grouping, deployment targets,
and sync/import behaviour are all SkillManager's job.

Moved here 2026-09-06 from Hermes-Provisioning/skills/, a folder held
outside the checkout, which meant `GET /skills` silently returned `[]`
whenever it was absent -- an empty Skills list read as "no Skills exist"
rather than "the source is not here". Skills are backend-owned framework
content and now live with the rest of it.

The grouping folder is the **Tool** (vault / outlook / pricing), not the
old free-form category. It is derived from what each Skill actually
depends on, not from the Registry's own grouping, which had six of our
own Skills mis-filed under the catch-all `jarvis` Tool.

`vault_manager.py` is deliberately NOT stored per skill. One canonical
copy lives in ../managers/ and is materialised into each profile at
deploy time -- the repo previously carried 12 copies of it plus 4 more
elsewhere, in 5 different versions.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.config import settings

_SKILLS_ROOT = Path(__file__).resolve().parents[1] / "business" / "core" / "skills" / "catalog"
_MANAGERS_ROOT = Path(__file__).resolve().parents[1] / "business" / "core" / "skills" / "managers"


def managers_root() -> Path:
    """Shared libraries materialised into a skill's own folder at deploy
    time rather than duplicated into it in the repo."""
    return _MANAGERS_ROOT


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

def read_manager_source(filename: str) -> str:
    """One shared library's canonical source, for materialising into a
    skill at deploy time. Raises if absent -- a skill that imports a
    manager we cannot supply must fail loudly, not deploy half-formed."""
    path = _MANAGERS_ROOT / filename
    if not path.is_file():
        raise FileNotFoundError(f"No shared manager named {filename!r}")
    return path.read_text(encoding="utf-8")

def shared_managers_target(hermes_home: Path) -> Path:
    """Where the ONE shared copy of each manager lives on a real install.

    Skills import these as plain siblings (`from vault_manager import ...`),
    which works because this directory is on PYTHONPATH -- Hermes APPENDS a
    configured PYTHONPATH to its own rather than replacing it
    (cron/scheduler.py, gateway/run.py), and the gateway mutates os.environ
    globally, so both `--no-agent --script` cron jobs and agent-invoked
    Skills inherit it. Verified live 2026-09-06 on both paths.
    """
    return hermes_home / "managers"


def deploy_shared_managers(hermes_home: Path) -> list[str]:
    """Copies every canonical manager into the install's shared directory,
    always overwriting. Returns the filenames written.

    Idempotent and cheap, so callers run it on every deploy rather than
    once: that is what makes staleness impossible. The install previously
    carried 228 copies of vault_manager.py across 41 profiles, ALL of them
    an older version than canonical, and nothing noticed because a local
    copy silently wins over PYTHONPATH (sys.path[0] is the script's own
    directory)."""
    target = shared_managers_target(hermes_home)
    target.mkdir(parents=True, exist_ok=True)
    written = []
    for source in sorted(_MANAGERS_ROOT.glob("*.py")):
        # Test scaffolding is not payload. conftest.py in particular would
        # be picked up by any pytest run rooted at the install and change
        # sys.path there.
        if source.name == "conftest.py" or source.name.startswith("test_"):
            continue
        shutil.copyfile(source, target / source.name)
        written.append(source.name)
    return written

_SECTION_ACCESS_FILENAME = "section_access.json"


def write_section_access_map(mapping: dict) -> Path:
    """Persists the derived per-Action write map where the shared
    vault_manager reads it: <data>/data/section_access.json. Raw write of
    exactly what it is given -- SkillManager derives and owns the shape."""
    path = settings.second_brain_data_path / "data" / _SECTION_ACCESS_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(mapping, indent=2, sort_keys=True), encoding="utf-8")
    return path
