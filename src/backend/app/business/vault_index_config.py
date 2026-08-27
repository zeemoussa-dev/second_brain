"""Vault > Index Filtering (Settings, 2026-08-27) -- which top-level
Work/ folders the vault structural indexer
(Hermes-Provisioning/shared/build_vault_index.py,
Implementation/Plans/2026-08-27-vault-index-and-section-agents.md)
actually walks, as real editable config instead of a hardcoded folder
list (operator: "Index Filtering a new settings feature... instead of
Hardcoding files").

Folder discovery reuses vault_indexing.get_overview()'s own live
folder_counts rather than re-scanning the vault a second time. A folder
with no saved preference defaults to included=True -- non-breaking:
Phase 1's own "index every real top-level folder" behavior is exactly
what an empty config already produces.

Storage: settings.second_brain_data_path / "index_config.json" -- a
plain JSON file the standalone indexer script also reads directly (no
backend dependency), same convention as every other `.second-brain/
data/*.json` store.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.business import vault_indexing
from app.config import settings


def _config_path() -> Path:
    return settings.second_brain_data_path / "index_config.json"


def _load_raw() -> dict:
    path = _config_path()
    if not path.exists():
        return {"folders": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"folders": {}}
    data.setdefault("folders", {})
    return data


def _save_raw(data: dict) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_index_config() -> dict:
    """Every real top-level Work/ folder (from the same live folder_counts
    the Vault Overview page already shows), each with its current
    included/excluded state -- True unless explicitly saved otherwise."""
    raw = _load_raw()
    saved_folders = raw["folders"]
    real_folder_names = vault_indexing.get_overview()["folder_counts"].keys()
    return {
        "folders": [
            {
                "name": name,
                "included": saved_folders.get(name, {}).get("included", True),
            }
            for name in sorted(real_folder_names)
        ],
    }


def set_folder_included(folder_name: str, included: bool) -> dict:
    raw = _load_raw()
    raw["folders"].setdefault(folder_name, {})["included"] = included
    _save_raw(raw)
    return get_index_config()
