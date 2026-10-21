"""Raw data access for the operator's declared entry points
(`REQ-SB-102`) -- `<SECOND_BRAIN_DATA_PATH>/entry-points.json`, in the
config folder beside the other things this install knows about itself.

A declaration, not a cache of Hermes: it says which agent the operator
MEANT a door to reach. The observed half is derived from traffic and is
never written here, so this file can never drift into claiming to be
the truth -- it is only ever one side of a comparison.

Zero interpretation: no agent id is checked for existing, no duplicate
is refused, nothing is reconciled. `entry_points.py` in the business
layer owns all of that.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import settings

_FILENAME = "entry-points.json"


def entry_points_path() -> Path:
    return settings.second_brain_data_path / _FILENAME


def read_entry_points() -> list[dict]:
    """An absent file is an install that has declared nothing, which is
    a normal state and not an error -- every door still shows, as
    `observed_only`. A file that does not parse IS an error and is
    raised, because silently treating a corrupted declaration as "no
    declarations" would report every door as undeclared and invite the
    operator to declare them all a second time."""
    path = entry_points_path()
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("entry_points", [])


def write_entry_points(entries: list[dict]) -> None:
    path = entry_points_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
