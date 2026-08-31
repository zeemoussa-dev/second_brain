"""Per-artifact id-conflict detection against THIS (target) machine's own
real current state (`REQ-SB-85-US-03-T02`) -- consumed by the import
preview/orchestrator (`T05`) once a bundle's manifest has been parsed by
`sbf_archive.read_archive` (`T01`).

Pure read-only check, zero business decisions made here: this module only
answers "does this id already exist on this machine today," never how to
resolve a conflict (overwrite/skip/keep-both is the operator's own explicit,
per-artifact choice, applied by `T05`, never by this module).
"""
from __future__ import annotations

from app.business.core.agents.agent_manager import AgentManager
from app.business.core.pipelines.pipeline_manager import PipelineManager
from app.business.core.skills.skill_manager import SkillManager
from app.business.core.templates.template_manager import TemplateManager

# Real Manager per manifest `kind` -- every kind an `.sbf` bundle's own
# manifest can name, matching `sbf_archive`/`artifact_export`'s own 4-kind
# vocabulary. A `kind` outside this set is a real defect in the manifest/
# caller, never silently treated as "no conflict."
_MANAGER_BY_KIND: dict[str, type] = {
    "skill": SkillManager,
    "template": TemplateManager,
    "agent": AgentManager,
    "pipeline": PipelineManager,
}


def detect_conflicts(artifacts: list[dict]) -> list[dict]:
    """Returns `artifacts`, each entry's own dict augmented with
    `"conflicts": bool` -- `True` iff the target machine's own matching-kind
    Manager's `get_by_id(id)` returns non-`None` today. Every artifact is
    checked independently against a freshly-constructed Manager instance,
    never short-circuited or batched -- an earlier conflict never skips a
    later artifact's own real check."""
    checked_artifacts: list[dict] = []
    for entry in artifacts:
        kind = entry.get("kind")
        manager_class = _MANAGER_BY_KIND.get(kind)
        if manager_class is None:
            raise ValueError(f"unrecognized artifact kind {kind!r} -- expected one of {sorted(_MANAGER_BY_KIND)}")

        artifact_id = entry.get("id")
        existing = manager_class().get_by_id(artifact_id)
        checked_artifacts.append({**entry, "conflicts": existing is not None})

    return checked_artifacts
