"""Raw data access for VaultManager's own index-filtering config
(ADR-003's own api -> business -> data_access layering) --
second_brain_data_path/index_config.json. Zero business interpretation
here (no per-folder default) -- that's VaultManager's own job.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import settings


def _config_path() -> Path:
    return settings.second_brain_data_path / "index_config.json"


def load_raw() -> dict | None:
    """None if the store has never been written yet, or its own file is
    unreadable/malformed -- the caller decides what that means, not this
    module."""
    path = _config_path()
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_raw(data: dict) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
