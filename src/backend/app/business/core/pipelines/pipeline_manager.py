"""PipelineManager -- the ONLY door onto Pipeline data (mirrors Section/
AgentManager's own "one real gateway" rule). A Pipeline is Second Brain's
OWN definition of a cron flow's stages (ADR-005) -- real, hand-edited
JSON files under <second_brain_data_path>/pipelines/, never part of the
Hermes mirror or the REQ-SB-80 Registry tree.

Folds in and replaces `data_access/system/pipelines/{registry,schema}.py`
(both deleted) -- registry.py was pure read-only with zero write methods
and exactly one real caller (agents_map_adapter.py), and schema.py's own
Pipeline/PipelineStep dataclasses were an exact duplicate of this
package's own `pipeline.py` shape. The one real difference: `section` on
disk is a plain Section NAME string (e.g. "Data Gatherer") -- resolved
here into the canonical `section_id` every other entity already uses,
via SectionManager, so callers never juggle a raw name again.

Read-only for now -- pipelines are still hand-edited JSON files; no
create/update/delete existed before this and none is built here either,
since that would be new functionality, not a migration of anything that
already worked.

`cron_job_id`/`cron_profile_id` (2026-08-28) link a Pipeline to the real
Hermes cron job behind it -- composed live via `HermesCron`, the same
"never a stale local copy" principle vault-search/build_vault_index.py
etc. already use. Confirmed live, not assumed: not every real cron job
lives on the shared default/root profile -- `meeting-capture-recurring`
runs under `meeting-prep-agent`'s own cron, invisible to a default-only
lookup, which is why `HermesCron` itself gained profile scoping
alongside this.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.business.core.pipelines.pipeline import Pipeline, PipelineStep
from app.business.core.sections.section_manager import SectionManager
from app.business.hermes.client import get_client
from app.config import settings

_FALLBACK_SECTION_NAME = "Data Gatherer"


class PipelineManager:
    def __init__(self) -> None:
        self._section_manager = SectionManager()

    def _definitions_dir(self) -> Path:
        return settings.second_brain_data_path / "pipelines"

    def _section_id_by_name(self, name: str) -> str:
        for section in self._section_manager.get_all():
            if section.name == name:
                return section.id
        # Same idempotent-collapse-on-collision fallback SectionManager's
        # own callers already use -- a Pipeline referencing an unknown/
        # blank Section name still resolves to something real.
        return self._section_manager.create(name or _FALLBACK_SECTION_NAME).id

    def _cron_status(self, cron_job_id: str | None, cron_profile_id: str | None) -> dict:
        if cron_job_id is None:
            return {}
        job = next(
            (j for j in get_client().cron.list_cron_jobs(cron_profile_id) if j.name == cron_job_id),
            None,
        )
        if job is None:
            return {}
        return {
            "cron_enabled": job.enabled,
            "cron_schedule": job.schedule_display,
            "cron_last_run_at": job.last_run_at,
            "cron_next_run_at": job.next_run_at,
            "cron_last_status": job.last_status,
        }

    def _load_pipeline(self, path: Path) -> Pipeline:
        data = json.loads(path.read_text(encoding="utf-8"))
        steps = [
            PipelineStep(
                id=step["id"], name=step["name"],
                description=step.get("description", ""),
                depends_on=list(step.get("depends_on") or []),
                type=step.get("type") or "worker",
            )
            for step in data.get("steps", [])
        ]
        cron_job_id = data.get("cron_job_id")
        cron_profile_id = data.get("cron_profile_id")
        return Pipeline(
            id=data["id"], name=data.get("name") or data["id"],
            description=data.get("description", ""),
            section_id=self._section_id_by_name(data.get("section", "")),
            cron_profile_id=cron_profile_id,
            cron_job_id=cron_job_id,
            steps=steps,
            **self._cron_status(cron_job_id, cron_profile_id),
        )

    def get_all(self) -> list[Pipeline]:
        definitions_dir = self._definitions_dir()
        if not definitions_dir.is_dir():
            return []
        return [self._load_pipeline(path) for path in sorted(definitions_dir.glob("*.json"))]

    def get_by_id(self, pipeline_id: str) -> Pipeline | None:
        return next((p for p in self.get_all() if p.id == pipeline_id), None)
