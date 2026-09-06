"""Raw data access for Blueprints -- the shipped library at
business/core/blueprints/library/<id>/{Blueprint.json, agents/*.soul.md}.

Zero business interpretation here: no precondition checking, no Skill or
Template resolution, no install ordering -- that is BlueprintManager's job.
Resolved from this file's own package layout, not from settings: a Blueprint
is bundled source that ships with the product, not user data.
"""
from __future__ import annotations

import json
from pathlib import Path

_LIBRARY_ROOT = (
    Path(__file__).resolve().parents[1] / "business" / "core" / "blueprints" / "library"
)


def list_blueprint_ids() -> list[str]:
    """Every Blueprint that ships. Empty (never an exception) if the library
    directory is missing, so a checkout without it degrades to "none on
    offer" rather than failing the Settings page."""
    if not _LIBRARY_ROOT.is_dir():
        return []
    return sorted(
        p.name for p in _LIBRARY_ROOT.iterdir()
        if p.is_dir() and (p / "Blueprint.json").is_file()
    )


def read_blueprint_json(blueprint_id: str) -> dict:
    """Raises FileNotFoundError for an unknown id, json.JSONDecodeError if it
    does not parse -- a shipped Blueprint that will not load is a build
    defect and must not be swallowed."""
    path = _LIBRARY_ROOT / blueprint_id / "Blueprint.json"
    if not path.is_file():
        raise FileNotFoundError(f"No Blueprint.json for {blueprint_id!r}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_blueprint_asset(blueprint_id: str, relative_path: str) -> str | None:
    """A file the Blueprint references by relative path (an agent's soul.md).
    None if absent -- a missing soul is a real problem the business layer
    reports, not an exception here.

    Refuses to escape the Blueprint's own directory: the path comes out of a
    JSON file, and a `../` in it would otherwise read anything on disk.
    """
    base = (_LIBRARY_ROOT / blueprint_id).resolve()
    target = (base / relative_path).resolve()
    if not target.is_file() or base not in target.parents:
        return None
    return target.read_text(encoding="utf-8")
