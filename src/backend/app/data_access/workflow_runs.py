"""Raw data access for Workflow run records (ADR-003's own api ->
business -> data_access layering) -- second_brain_data_path/data/
WorkflowRuns/<run_id>.json, the store ADR-034 fixes for what happened
when one Workflow was actually run: the workflow id, the ordered steps,
each step's status and outcome, and the Action-call ids it produced.

Flat file-per-run, like data_access/action_calls.py and NOT
folder-per-id like data_access/workflows.py. The difference is not
cosmetic: a Workflow is a definition that may grow companion files, a
run is one record of one occurrence and there will be very many of
them. Same reason the Action-call ledger is flat.

Zero business interpretation here: no run_id minted, no step status
vocabulary, no rule about which step may be handed out next and no
check that a reported outcome belongs to the current step. All of that
is business/logic/workflow_run.py's own, and enforcing any of it here
would make a refusal depend on which door the write came through.

A run record is instance data and is excluded from artifact export by
construction rather than by a rule (ADR-034, and the same reasoning
artifact_export.py states for ActionCalls/): export exports named
artifact KINDS, and a run is not a kind -- it is what happened once on
THIS install, never a capability another install could be given.

Nothing here deletes a run. An abandoned run stays open and visible
rather than being tidied away (ADR-034's own consequence): a run that
could be removed could also be removed instead of finished, and a
half-finished operation nobody can see is exactly what the run record
exists to prevent.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import settings

_WORKFLOW_RUNS_SUBPATH = ("data", "WorkflowRuns")


def _workflow_runs_root() -> Path:
    return settings.second_brain_data_path.joinpath(*_WORKFLOW_RUNS_SUBPATH)


def run_file(run_id: str) -> Path:
    return _workflow_runs_root() / f"{run_id}.json"


def list_run_ids() -> list[str]:
    root = _workflow_runs_root()
    if not root.exists():
        return []
    return sorted(p.stem for p in root.iterdir() if p.is_file() and p.suffix == ".json")


def read_run_json(run_id: str) -> dict:
    """Raises FileNotFoundError if the id doesn't exist, json.JSONDecodeError
    if the file doesn't parse -- never swallows either. A run whose record
    cannot be read must not read back as a run with no steps."""
    path = run_file(run_id)
    if not path.is_file():
        raise FileNotFoundError(f"No WorkflowRun record for {run_id!r}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_run_json(run_id: str, data: dict) -> None:
    """Writes `data` exactly as given. JSON preserves list order, so the
    documented step order is a property of the file itself -- nothing
    downstream has to re-sort it, and nothing here may re-order it."""
    path = run_file(run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
