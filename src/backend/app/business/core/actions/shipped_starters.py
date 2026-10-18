"""The starter Actions the framework itself ships (`ADR-032` allows
shipped starters; REQ-SB-95-US-03-T05 ships the first one).

Source, not data: these are version-controlled files that ship with the
product, the exact shape `business/core/templates/masters/` already has
for Entity Templates. `ActionManager.seed_shipped_starters()` installs
any this install does not already have, and never overwrites one.

**Why the read lives here and not in `data_access/actions.py`.** Every
raw read of INSTALL data still goes through that module -- nothing here
touches `<DATA_PATH>`. What this reads is bundled source sitting beside
the Manager that ships it, the same category as `action.py`'s own
`UI_FEATURE_KEYS`, which is already a bundled constant declared in the
business layer. `data_access/templates.py` holds the equivalent reader
for Master Templates, so a human who prefers the symmetry can move these
two functions there unchanged -- it was kept beside the starters it reads
because this task's scope is this directory (see its Implementation Log).
"""
from __future__ import annotations

import json
from pathlib import Path

_SHIPPED_STARTERS_DIR = Path(__file__).resolve().parent / "starters"


def list_shipped_starter_ids() -> list[str]:
    """Every starter Action that ships with the product. Empty (never an
    exception) if the directory is missing, so a checkout without it
    seeds nothing rather than failing app startup -- the same degradation
    `list_shipped_master_ids()` already chose."""
    if not _SHIPPED_STARTERS_DIR.is_dir():
        return []
    return sorted(
        path.name for path in _SHIPPED_STARTERS_DIR.iterdir()
        if path.is_dir() and (path / "Action.json").is_file()
    )


def read_shipped_starter_json(action_id: str) -> dict:
    """Raw parsed JSON for one shipped starter. Raises the same way
    `read_action_json` does -- a shipped Action that will not parse is a
    build defect and must not be swallowed."""
    path = _SHIPPED_STARTERS_DIR / action_id / "Action.json"
    if not path.is_file():
        raise FileNotFoundError(f"No shipped starter Action for {action_id!r}")
    return json.loads(path.read_text(encoding="utf-8"))
