"""Raw data access for Template.json files (ADR-003's own api -> business
-> data_access layering) -- second_brain_data_path/data/Templates/<id>/
Template.json. Zero business interpretation here: no defaults applied,
no error swallowed, no shape validated -- that's TemplateManager's own
job (business/core/templates/template_manager.py), the one real caller.
Pure I/O, no caching: a Template edited on disk takes effect on the very
next read.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import settings

_TEMPLATES_SUBPATH = ("data", "Templates")


def templates_root() -> Path:
    return settings.second_brain_data_path.joinpath(*_TEMPLATES_SUBPATH)


def list_template_ids() -> list[str]:
    """Every real Template directory (one that actually has a
    Template.json), sorted -- a bare, otherwise-empty directory under
    Templates/ is not a Template."""
    root = templates_root()
    if not root.exists():
        return []
    return sorted(
        p.name for p in root.iterdir() if p.is_dir() and (p / "Template.json").is_file()
    )


def read_template_json(template_id: str) -> dict:
    """Raw parsed JSON for one Template, exactly as written on disk --
    no defaults filled in. Raises FileNotFoundError if the id doesn't
    exist, json.JSONDecodeError if the file doesn't parse; never
    swallows either, unlike the business-layer caller which decides what
    a missing/malformed Template means to its own contract."""
    path = templates_root() / template_id / "Template.json"
    if not path.is_file():
        raise FileNotFoundError(f"No Template.json for {template_id!r}")
    return json.loads(path.read_text(encoding="utf-8"))
