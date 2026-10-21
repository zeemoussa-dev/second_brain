"""Raw data access for the routing conditions the operator writes onto
each specialist edge (`REQ-SB-102`) --
`<SECOND_BRAIN_DATA_PATH>/routing-conditions.json`.

**This app's annotation, not Hermes' configuration.** The edge itself
(`depends_on`) lives in the Hermes registry and Hermes owns it; the
`when` is the operator's own words about that edge, so it is stored
here. Writing it into the registry would make this app an author of
Hermes' configuration, which `MEMORY.md`'s "Hermes drives, the Registry
only decorates" is exactly about.

Shape: `{parent_agent_id: {child_agent_id: "when to go there"}}`. A
missing parent, or a missing child under one, means nobody has said
when -- which the map reports as a gap rather than inventing a default.

Zero interpretation: no agent id is checked for existing, no condition
is validated, nothing is merged with `depends_on`. That is the
business layer's.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import settings

_FILENAME = "routing-conditions.json"


def routing_conditions_path() -> Path:
    return settings.second_brain_data_path / _FILENAME


def read_all() -> dict[str, dict[str, str]]:
    """An absent file is an install that has annotated nothing -- normal,
    and reported as every edge being unconditioned. A file that does not
    parse is raised rather than swallowed: treating a corrupt file as
    "no conditions" would quietly blank every condition the operator
    wrote and invite them to write them all again."""
    path = routing_conditions_path()
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def write_all(conditions: dict[str, dict[str, str]]) -> None:
    path = routing_conditions_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(conditions, ensure_ascii=False, indent=2), encoding="utf-8")
