"""Raw data access for Pipeline definitions (ADR-003's own api ->
business -> data_access layering) -- second_brain_data_path/pipelines/
<id>.json, real hand-edited files. Zero business interpretation here (no
section-name resolution, no cron composition) -- that's PipelineManager's
own job.
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
