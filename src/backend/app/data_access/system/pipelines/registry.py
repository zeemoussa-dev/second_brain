"""Loads every real Pipeline definition (*.json, one file per pipeline)
under `<second_brain_data_path>/pipelines/` -- these are real, live-
edited Second Brain Data (Pipelines get added/changed as the real
Hermes cron jobs behind them change), never static source-tree fixtures,
so they live under the app's own data root, not next to this module.
Pure I/O, no caching -- editing a pipeline's own .json file takes effect
on the next read, same "always current" principle as
app/hermes/definitions.py (ADR-003), for the same reason: a stale,
drifted copy of a definition is worse than reading the real file every
time.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import settings
from app.data_access.system.pipelines.schema import Pipeline, PipelineStep


def _definitions_dir() -> Path:
    return settings.second_brain_data_path / "pipelines"


def _load_pipeline(path: Path) -> Pipeline:
    data = json.loads(path.read_text(encoding="utf-8"))
    steps = [
        PipelineStep(
            id=step["id"],
            name=step["name"],
            description=step.get("description", ""),
            depends_on=list(step.get("depends_on") or []),
            type=step.get("type") or "worker",
        )
        for step in data.get("steps", [])
    ]
    return Pipeline(
        id=data["id"],
        name=data.get("name") or data["id"],
        description=data.get("description", ""),
        section=data.get("section", ""),
        steps=steps,
    )


def list_pipelines() -> list[Pipeline]:
    definitions_dir = _definitions_dir()
    if not definitions_dir.is_dir():
        return []
    return [
        _load_pipeline(path)
        for path in sorted(definitions_dir.glob("*.json"))
    ]


def get_pipeline(pipeline_id: str) -> Pipeline | None:
    for pipeline in list_pipelines():
        if pipeline.id == pipeline_id:
            return pipeline
    return None
