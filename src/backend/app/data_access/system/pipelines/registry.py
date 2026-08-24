"""Loads every real Pipeline definition (*.json, one file per pipeline) in
this directory (2026-08-22). Pure I/O, no caching -- editing a pipeline's
own .json file takes effect on the next read, same "always current"
principle as hermes_definitions.py (ADR-003), for the same reason: a
stale, drifted copy of a definition is worse than reading the real file
every time.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.data_access.system.pipelines.schema import Pipeline, PipelineStep

_DEFINITIONS_DIR = Path(__file__).parent


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
    return [
        _load_pipeline(path)
        for path in sorted(_DEFINITIONS_DIR.glob("*.json"))
    ]


def get_pipeline(pipeline_id: str) -> Pipeline | None:
    for pipeline in list_pipelines():
        if pipeline.id == pipeline_id:
            return pipeline
    return None
