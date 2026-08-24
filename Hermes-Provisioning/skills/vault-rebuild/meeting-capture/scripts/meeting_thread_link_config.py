"""Real, accessible config for the meeting-to-Thread linking fallback
heuristic (mirrors the source project's own
app/business/meeting_thread_link_config.py) -- the attendee-overlap
floor, the 1:1 carve-out toggle, and the date-proximity window are never
Python constants; they live in a JSON file under the vault's own
`.second-brain/` state directory, self-healing to these defaults on
first read. Composed alongside link_meeting_to_thread.py, never baked
into it.
"""
from __future__ import annotations

import json
from pathlib import Path

_STATE_DIR = ".second-brain"
_CONFIG_FILE = "meeting_thread_link_config.json"

_DEFAULT_CONFIG = {
    "attendee_overlap_floor": 2,
    "one_on_one_carve_out_enabled": True,
    "date_proximity_days": 7,
}


def _config_path(vault_path: Path) -> Path:
    return vault_path / _STATE_DIR / _CONFIG_FILE


def load_config(vault_path: Path) -> dict:
    """Never returns a record missing any of the three keys -- an
    already-saved config file created before a future key was added
    would otherwise silently miss it; each missing key is seeded to its
    own default and persisted back."""
    path = _config_path(vault_path)
    if not path.exists():
        config = dict(_DEFAULT_CONFIG)
        save_config(vault_path, config)
        return config
    config = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for key, default_value in _DEFAULT_CONFIG.items():
        if key not in config:
            config[key] = default_value
            changed = True
    if changed:
        save_config(vault_path, config)
    return config


def save_config(vault_path: Path, config: dict) -> None:
    path = _config_path(vault_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
