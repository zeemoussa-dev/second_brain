"""Raw data access for the Action-call ledger (ADR-003's own api ->
business -> data_access layering) -- second_brain_data_path/data/
ActionCalls/<call_id>.json, the store ADR-033 fixes for every call
outcome: who called, which Action, the validated inputs, and what
happened.

Flat file-per-call, NOT a folder-per-id like data_access/actions.py: an
Action owns a definition plus whatever else an artifact kind may grow,
while a call record is one immutable-ish fact and there will be very
many of them. `data_access/indexes.py` is still the function-for-function
shape this mirrors; only the path shape differs.

Zero business interpretation here: no call_id minted, no outcome
vocabulary, no validation of who may call what. All of that is
`business/logic/action_invocation.py`'s own, and enforcing any of it
here would make a refusal depend on which door the write came through.

The ledger is instance data and personal (ADR-033's consequences). It is
excluded from artifact export by construction rather than by a rule:
artifact_export.py exports named artifact KINDS, and a call record is
not a kind.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import settings

_ACTION_CALLS_SUBPATH = ("data", "ActionCalls")


def _action_calls_root() -> Path:
    return settings.second_brain_data_path.joinpath(*_ACTION_CALLS_SUBPATH)


def call_file(call_id: str) -> Path:
    return _action_calls_root() / f"{call_id}.json"


def list_call_ids() -> list[str]:
    root = _action_calls_root()
    if not root.exists():
        return []
    return sorted(p.stem for p in root.iterdir() if p.is_file() and p.suffix == ".json")


def read_call_json(call_id: str) -> dict:
    """Raises FileNotFoundError if the id doesn't exist, json.JSONDecodeError
    if the file doesn't parse -- never swallows either."""
    path = call_file(call_id)
    if not path.is_file():
        raise FileNotFoundError(f"No ActionCall record for {call_id!r}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_call_json(call_id: str, data: dict) -> None:
    path = call_file(call_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
