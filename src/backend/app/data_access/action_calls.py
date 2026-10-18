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

Beside the records sits `_claims/<call_id>.json`, written by
`claim_call_once()` -- the one primitive that makes a single-use grant
single-use (REQ-SB-95-US-03-T03). It is a subdirectory rather than a
sibling `<call_id>.claim` so the ledger itself keeps its one-file-per-
call shape and `list_call_ids()` keeps returning call ids only.

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
_CLAIMS_DIRNAME = "_claims"


def _action_calls_root() -> Path:
    return settings.second_brain_data_path.joinpath(*_ACTION_CALLS_SUBPATH)


def _claims_root() -> Path:
    """Derived from `_action_calls_root()` rather than from `settings`
    directly, so a test (or an install) that moves the ledger moves its
    claims with it -- a claim that stayed behind in the real data path
    would let a single-use grant be spent twice."""
    return _action_calls_root() / _CLAIMS_DIRNAME


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


def claim_file(call_id: str) -> Path:
    return _claims_root() / f"{call_id}.json"


def claim_call_once(call_id: str, claim: dict) -> bool:
    """Marks one call id claimed, and answers whether THIS caller is the
    one that marked it. True exactly once per call id, ever.

    The exclusivity is the filesystem's, not a read-then-write of the
    call record: `open(..., "x")` fails if the file already exists, in
    one indivisible operation, so two callers racing on the same id
    cannot both be told yes. A read-modify-write over
    `<call_id>.json` could, and the whole point of a single-use grant
    is that it cannot be spent twice.

    WHAT a claim means is business (`business/logic/action_invocation.py`
    spends a skill grant with it, and confirmation spends its own with
    the same primitive) -- this file only guarantees that exactly one
    caller gets it. `claim` is written beside the marker purely so the
    operator can read who took it and when.

    In `_claims/`, a subdirectory, so the ledger proper keeps its
    documented one-`.json`-per-call shape and `list_call_ids()` -- which
    skips directories -- keeps returning call ids and nothing else.
    """
    path = claim_file(call_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(claim, handle, indent=2)
    except FileExistsError:
        return False
    return True


def read_claim_json(call_id: str) -> dict | None:
    """What was written when this call id was claimed, or None if it
    never was. Never raises for an unclaimed id: "nobody has claimed it"
    is an ordinary answer here, not a missing file."""
    path = claim_file(call_id)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
