"""Raw data access for Workflow definitions (ADR-003's own api ->
business -> data_access layering) -- second_brain_data_path/data/
Workflows/<id>/Workflow.json, the store ADR-032 fixes for the seventh
artifact kind.

Zero business interpretation here: no defaulting of steps/report, no
minting of step ids, and in particular NO check that a step names a
catalogued Action -- that referential rule is WorkflowManager's own
(ADR-034: save-time validation, one direction only), and enforcing it
here would make a refusal depend on which door the write came through.

Mirrors data_access/actions.py function for function, which mirrors
data_access/indexes.py -- the measured precedent for adding a kind
(ADR-019, 2026-09-06).

Nothing here touches the Pipeline store at
second_brain_data_path/pipelines/ (ADR-032: Pipeline is left exactly as
it is). A Workflow is intent-triggered and file-per-id in its own
folder; a Pipeline is time-triggered and a flat <id>.json. Separate
roots, separate shapes, no migration.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.config import settings

_WORKFLOWS_SUBPATH = ("data", "Workflows")


def _workflows_root() -> Path:
    return settings.second_brain_data_path.joinpath(*_WORKFLOWS_SUBPATH)


def workflow_file(workflow_id: str) -> Path:
    return _workflows_root() / workflow_id / "Workflow.json"


def list_workflow_ids() -> list[str]:
    root = _workflows_root()
    if not root.exists():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and (p / "Workflow.json").is_file())


def read_workflow_json(workflow_id: str) -> dict:
    """Raises FileNotFoundError if the id doesn't exist, json.JSONDecodeError
    if the file doesn't parse -- never swallows either."""
    path = workflow_file(workflow_id)
    if not path.is_file():
        raise FileNotFoundError(f"No Workflow.json for {workflow_id!r}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_workflow_json(workflow_id: str, data: dict) -> None:
    """Writes `data` exactly as given. JSON preserves list order, so the
    operator's documented step order is a property of the file itself --
    nothing downstream has to re-sort it, and nothing here may re-order
    it."""
    path = workflow_file(workflow_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def delete_workflow_definition(workflow_id: str) -> None:
    """Removes this Workflow's own definition folder. A Workflow owns no
    Action and no run: the Actions its steps name belong to the
    catalogue and outlive it, and its runs are their own records under
    WorkflowRuns/, so deleting the definition must never reach either.
    """
    workflow_dir = _workflows_root() / workflow_id
    if workflow_dir.is_dir():
        shutil.rmtree(workflow_dir, ignore_errors=True)
