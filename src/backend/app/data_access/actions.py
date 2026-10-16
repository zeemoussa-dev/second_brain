"""Raw data access for Action definitions (ADR-003's own api -> business
-> data_access layering) -- second_brain_data_path/data/Actions/<id>/
Action.json, the store ADR-032 fixes for the sixth artifact kind.

Zero business interpretation here: no defaulting of inputs/
allowed_callers/needs_confirmation, and in particular NO check that the
definition names exactly one implementation -- that cardinality rule is
ActionManager's own, and enforcing it here would make a refusal depend
on which door the write came through.

Mirrors data_access/indexes.py function for function, which is the
measured precedent for adding a kind (ADR-019, 2026-09-06).
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.config import settings

_ACTIONS_SUBPATH = ("data", "Actions")


def _actions_root() -> Path:
    return settings.second_brain_data_path.joinpath(*_ACTIONS_SUBPATH)


def action_file(action_id: str) -> Path:
    return _actions_root() / action_id / "Action.json"


def list_action_ids() -> list[str]:
    root = _actions_root()
    if not root.exists():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and (p / "Action.json").is_file())


def read_action_json(action_id: str) -> dict:
    """Raises FileNotFoundError if the id doesn't exist, json.JSONDecodeError
    if the file doesn't parse -- never swallows either."""
    path = action_file(action_id)
    if not path.is_file():
        raise FileNotFoundError(f"No Action.json for {action_id!r}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_action_json(action_id: str, data: dict) -> None:
    path = action_file(action_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def delete_action_definition(action_id: str) -> None:
    """Removes this Action's own definition folder. An Action owns no
    built output and no deployed script -- whatever its implementation
    points at belongs to that thing, never to the Action, so deleting
    the catalogue entry must never reach it."""
    action_dir = _actions_root() / action_id
    if action_dir.is_dir():
        shutil.rmtree(action_dir, ignore_errors=True)
