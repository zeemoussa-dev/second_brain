"""Raw data access for call-time rules (`REQ-SB-102`) --
`<SECOND_BRAIN_DATA_PATH>/action-rules.json`, in the config folder.

A list, kept in the operator's own order: `evaluate` stops at the first
rule that refuses, so order is meaning here, not presentation. Sorting
it on read would quietly change which reason a refused call reports.

Zero interpretation: no pattern is compiled, no action id is checked
for existing, nothing is evaluated. That is `business/logic/
action_rules.py`.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import settings

_FILENAME = "action-rules.json"


def rules_path() -> Path:
    return settings.second_brain_data_path / _FILENAME


def read_rules() -> list[dict]:
    """An absent file means no rules, which is a normal install. A file
    that does not parse is RAISED: treating a corrupt rules file as "no
    rules" would turn every rule the operator wrote into nothing, which
    is the one failure a rules engine must never have."""
    path = rules_path()
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else data.get("rules", [])


def write_rules(rules: list[dict]) -> None:
    path = rules_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")
