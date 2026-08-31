"""Raw data access for Pipeline definitions (ADR-003's own api ->
business -> data_access layering) -- second_brain_data_path/pipelines/
<id>.json, real hand-edited files. Zero business interpretation here (no
section-name resolution, no cron composition) -- that's PipelineManager's
own job. `write_pipeline_json` (ADR-015) is a real, narrowly-scoped write
primitive added for import provisioning only -- same raw-I/O-only
discipline as the read side; PipelineManager still does all shape
validation before ever calling it.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import settings


def _definitions_dir() -> Path:
    return settings.second_brain_data_path / "pipelines"


def list_pipeline_ids() -> list[str]:
    definitions_dir = _definitions_dir()
    if not definitions_dir.is_dir():
        return []
    return sorted(p.stem for p in definitions_dir.glob("*.json"))


def read_pipeline_json(pipeline_id: str) -> dict:
    """Raises FileNotFoundError if the id doesn't exist, json.JSONDecodeError
    if the file doesn't parse -- never swallows either."""
    path = _definitions_dir() / f"{pipeline_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"No pipeline definition for {pipeline_id!r}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_pipeline_json(pipeline_id: str, data: dict) -> None:
    """Raw write of `data` as <pipeline_id>.json, exactly as given -- no
    defaults filled in, no shape validated (PipelineManager's own job,
    same discipline the read side already follows). Creates the
    definitions directory if it doesn't exist yet. Always overwrites
    whatever <pipeline_id>.json is already there -- the caller
    (PipelineManager.import_pipeline) is responsible for only calling
    this once any per-artifact conflict decision has already been made."""
    definitions_dir = _definitions_dir()
    definitions_dir.mkdir(parents=True, exist_ok=True)
    (definitions_dir / f"{pipeline_id}.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )
