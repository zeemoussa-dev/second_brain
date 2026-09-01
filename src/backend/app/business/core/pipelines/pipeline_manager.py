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

Pipelines are still primarily hand-edited JSON files -- `get_all()`/
`get_by_id()` remain this module's own everyday path. `import_pipeline`
(ADR-015) is a real, but narrowly-scoped, write path added ONLY to support
REQ-SB-85-US-03's own import provisioning (deploying a bundled Pipeline
artifact onto a target machine) -- not a general Pipelines authoring UI;
no other create/update/delete method exists.

`cron_job_id`/`cron_profile_id` (2026-08-28) link a Pipeline to the real
Hermes cron job behind it -- composed live via `HermesCron`, the same
"never a stale local copy" principle vault-search/build_vault_index.py
etc. already use. Confirmed live, not assumed: not every real cron job
lives on the shared default/root profile -- `meeting-capture-recurring`
runs under `meeting-prep-agent`'s own cron, invisible to a default-only
lookup, which is why `HermesCron` itself gained profile scoping
alongside this.

Raw I/O (2026-08-28 layering correction, operator: "Managers understand
Entities, Data Access understands stores... I/O always happens in Data
Access") lives in `data_access/pipelines.py` -- this file holds zero raw
file calls, only entity-shaping and cron composition. Fixed after the
fact (found in passing while building IndexManager's own cron
composition, which reads the same pattern this file established) --
not part of the original SectionManager/AgentManager/VaultManager
retrofit, which was scoped to those three only.
"""
from __future__ import annotations

from app.business.core.pipelines.pipeline import Pipeline, PipelineStep
from app.business.core.sections.section_manager import SectionManager
from app.business.hermes.client import get_client
from app.data_access import pipelines as pipelines_data

_FALLBACK_SECTION_NAME = "Data Gatherer"


class PipelineManager:
    def __init__(self) -> None:
        self._section_manager = SectionManager()

    def _section_id_by_name(self, name: str) -> str:
        for section in self._section_manager.get_all():
            if section.name == name:
                return section.id
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

    def _to_pipeline(self, pipeline_id: str, data: dict) -> Pipeline:
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
        pipelines = []
        for pipeline_id in pipelines_data.list_pipeline_ids():
            try:
                data = pipelines_data.read_pipeline_json(pipeline_id)
            except (OSError, ValueError):
                continue
            pipelines.append(self._to_pipeline(pipeline_id, data))
        return pipelines

    def get_by_id(self, pipeline_id: str) -> Pipeline | None:
        try:
            data = pipelines_data.read_pipeline_json(pipeline_id)
        except (OSError, ValueError):
            return None
        return self._to_pipeline(pipeline_id, data)

    def get_implementing_skill_id(self, pipeline_id: str) -> str | None:
        """The real Skill id (bare slug) this Pipeline's own cron job
        actually runs -- BUG-041's fix. `PipelineStep.id` (e.g.
        "fetch-meetings") carries no Agent/Skill linkage at all (it only
        drives the Job Tree visualization), so the ONE real path from a
        Pipeline to the Skill that implements it is `cron_job_id`/
        `cron_profile_id` -> the real Hermes cron job -> that job's own
        `skill` field. Confirmed live across multiple real jobs this field
        is inconsistent in shape -- sometimes a bare slug ("meeting-capture"),
        sometimes Hermes' own raw "<category>/<slug>" form
        ("knowledge-base/azure-kb-writer") -- normalized here via the same
        "take the last `/`-segment" convention `AgentManager`/
        `artifact_dependency_resolver.py` already use for `Agent.skill_ids`.
        Returns None when `cron_job_id` is unset, the job can't be found, or
        the job has no `skill` (some real jobs -- git-sync, index rebuilds --
        aren't Skill-backed at all)."""
        pipeline = self.get_by_id(pipeline_id)
        if pipeline is None or pipeline.cron_job_id is None:
            return None
        job = next(
            (j for j in get_client().cron.list_cron_jobs(pipeline.cron_profile_id) if j.name == pipeline.cron_job_id),
            None,
        )
        if job is None or not job.skill:
            return None
        return job.skill.rsplit("/", 1)[-1]

    def import_pipeline(self, pipeline_id: str, data: dict) -> Pipeline:
        """Real, narrowly-scoped write path for import provisioning only
        (ADR-015). Validates `data` by round-tripping it through the
        EXISTING `_to_pipeline` parser first -- the same shape-check the
        read side already performs -- so a malformed shape raises and is
        never written to disk. Only once that succeeds is the raw JSON
        persisted via `pipelines_data.write_pipeline_json`, then
        read back via `get_by_id` (read-your-own-write), the same
        convention `TemplateManager.import_template` uses."""
        self._to_pipeline(pipeline_id, data)
        pipelines_data.write_pipeline_json(pipeline_id, data)
        return self.get_by_id(pipeline_id)
