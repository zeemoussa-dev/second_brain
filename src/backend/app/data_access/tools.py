"""Raw data access for Tool/Skill Registry catalog entries --
second_brain_data_path/data/Tools/<tool_id>/{Tool.json, Skills/<skill_id>/
{Skill.json, Skill-visual.json}} -- the same tree RegistryLoader already
reads for the Agents Map's Skills panel (app/data_access/registry/
loader.py's _load_tools). ToolManager/SkillManager are the only real
writers; RegistryLoader's own hot-reload poll (~2s) picks up changes the
same as every other Registry entity. Zero business interpretation here.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.data_access.registry.loader import data_root


def _tools_root() -> Path:
    return data_root() / "Tools"


def list_tool_ids() -> list[str]:
    root = _tools_root()
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and (p / "Tool.json").is_file())


def read_tool_json(tool_id: str) -> dict | None:
    path = _tools_root() / tool_id / "Tool.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_tool_json(tool_id: str, data: dict) -> None:
    path = _tools_root() / tool_id / "Tool.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def delete_tool_dir(tool_id: str) -> None:
    tool_dir = _tools_root() / tool_id
    if tool_dir.is_dir():
        shutil.rmtree(tool_dir, ignore_errors=True)


def has_skills(tool_id: str) -> bool:
    skills_dir = _tools_root() / tool_id / "Skills"
    return skills_dir.is_dir() and any(skills_dir.iterdir())


def find_tool_id_for_skill(skill_id: str) -> str | None:
    for tool_id in list_tool_ids():
        if (_tools_root() / tool_id / "Skills" / skill_id / "Skill.json").is_file():
            return tool_id
    return None


def read_skill_entry(tool_id: str, skill_id: str) -> dict | None:
    path = _tools_root() / tool_id / "Skills" / skill_id / "Skill.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_skill_visual(tool_id: str, skill_id: str) -> dict:
    path = _tools_root() / tool_id / "Skills" / skill_id / "Skill-visual.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_skill_entry(tool_id: str, skill_id: str, data: dict, visual: dict) -> None:
    skill_dir = _tools_root() / tool_id / "Skills" / skill_id
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "Skill.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    (skill_dir / "Skill-visual.json").write_text(json.dumps(visual, indent=2), encoding="utf-8")


def delete_skill_entry(tool_id: str, skill_id: str) -> None:
    skill_dir = _tools_root() / tool_id / "Skills" / skill_id
    if skill_dir.is_dir():
        shutil.rmtree(skill_dir, ignore_errors=True)


def move_skill_entry(old_tool_id: str, new_tool_id: str, skill_id: str) -> None:
    """Reassigning a Skill's tool_id is a real directory move -- its own
    Skill.json/Skill-visual.json live nested under the owning Tool."""
    data = read_skill_entry(old_tool_id, skill_id) or {}
    visual = read_skill_visual(old_tool_id, skill_id)
    write_skill_entry(new_tool_id, skill_id, data, visual)
    delete_skill_entry(old_tool_id, skill_id)
