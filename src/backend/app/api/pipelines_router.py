"""Pipeline HTTP surface -- extracted out of agents_router.py (2026-08-30,
operator: "Don;t you think we should have pipeline router instead of the
agent one?"). `pipelines_router` had been living inside agents_router.py
since 2026-08-22 (a different entity's router file) only because that's
where the FIRST route (list-only /pipelines) happened to get added; now
that Pipelines are getting a real detail route (and the rest of the
Pipeline feature on top of it), this follows the same one-router-per-
entity-per-file convention every other real entity here already uses
(sections_router.py, index_router.py, tools_router.py)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.business.core.pipelines.pipeline import Pipeline
from app.business.core.pipelines.pipeline_manager import PipelineManager
from app.business.hermes import agents_map_adapter

router = APIRouter(prefix="/pipelines")
_pipeline_manager = PipelineManager()


@router.get("")
def list_pipelines() -> list[dict]:
    return agents_map_adapter.list_pipeline_refs()


@router.get("/{pipeline_id}")
def get_pipeline(pipeline_id: str) -> Pipeline:
    # GET /agents/{id} already partially handles a pipeline id
    # (agents_map_adapter.get_agent_detail's own pipeline branch), but
    # that dict is Agent-detail-shaped (missing tools/depends_on/
    # preferred_index_ids the frontend AgentDetail type requires, and
    # missing cron status/steps entirely) -- reusing it for a real
    # Pipeline Detail Panel would mean either a broken frontend type or
    # a panel with no cron/step info, so this is a genuinely separate,
    # correctly-shaped route instead. Same "thin wrapper, one business
    # call, return the real dataclass" convention as GET /sections and
    # GET /indexes -- no presentation-module indirection needed.
    pipeline = _pipeline_manager.get_by_id(pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail=f"Unknown pipeline: {pipeline_id!r}")
    return pipeline
