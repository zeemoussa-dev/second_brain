"""Raw data access for the Operator Profile (ADR-003's own api ->
business -> data_access layering) -- second_brain_data_path/data/
Operator/Profile.json, the singleton store ADR-032 fixes for it.

Zero business interpretation here: no defaulting of name/timezone/team,
no check that a team entry holds exactly an email and a role, and in
particular NO notion of what "configured" means -- an absent file is
reported as absent and nothing more. Those are OperatorProfileManager's
own, and applying them here would make the answer depend on which door
the read came through.

A SINGLETON, not a catalogue: one path, no id anywhere in this module,
and deliberately no list and no delete. That is the one structural
difference from data_access/actions.py and data_access/indexes.py, which
this otherwise mirrors; the closer precedent for the shape is
data_access/vault_index_config.py, the other single-file store.

This module never reads or writes the operator's own mail address. It
lives in the SELF_EMAIL setting (ADR-038) and the Profile only mirrors
it, so there is nothing here to persist it with.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import settings

_PROFILE_SUBPATH = ("data", "Operator", "Profile.json")


def profile_path() -> Path:
    return settings.second_brain_data_path.joinpath(*_PROFILE_SUBPATH)


def profile_exists() -> bool:
    """Whether this install has ever saved a Profile. The Manager needs
    this to tell "never configured" from "configured and empty" -- two
    states an absent file and an empty record would otherwise collapse
    into one."""
    return profile_path().is_file()


def read_profile_json() -> dict:
    """Raises FileNotFoundError if nothing has been saved yet,
    json.JSONDecodeError if the file doesn't parse -- never swallows
    either, and never substitutes an empty record for a missing one."""
    path = profile_path()
    if not path.is_file():
        raise FileNotFoundError(f"No Operator Profile at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_profile_json(data: dict) -> None:
    """Overwrites the one record. There is no second path to write, so a
    save can only ever replace the singleton."""
    path = profile_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
