"""Cross-type artifact inventory (REQ-SB-85-US-01) -- composes the four
already-`Done` Managers (Skill/Template/Agent/Pipeline, all REQ-SB-80)
into one flat, tagged list. Pure read composition -- no owned store, no
write path -- matches the existing `business/logic/` cross-entity,
no-caching pattern (`section_agents.py`/`cockpit_view.py`/
`system_health.py`; `system_health.py`'s own header comment is this
module's direct precedent). Recomputed fresh on every call by
construction -- every `get_all()` call below is a real, live read, never
cached here or anywhere upstream.

`kind` is always exactly one of "skill"/"template"/"agent"/"pipeline" --
no 5th value is ever produced, since these are the only 4 Managers
composed. `name`/`description` are pulled from each entity's own real
field; `Template` has neither field on its dataclass (confirmed by direct
reading, business/core/templates/template.py) so `name` falls back to
`template.id` and `description` falls back to `template.note_name or ""`.
A malformed Template (`Template.error` set, per `TemplateManager.get_all()`'s
own honest-list convention) is still included, with `description` replaced
by `f"Error: {template.error}"` instead of being silently dropped."""
from __future__ import annotations

from app.business.core.agents.agent_manager import AgentManager
from app.business.core.pipelines.pipeline_manager import PipelineManager
from app.business.core.skills.skill_manager import SkillManager
from app.business.core.templates.template_manager import TemplateManager

_skill_manager = SkillManager()
_template_manager = TemplateManager()
_agent_manager = AgentManager()
_pipeline_manager = PipelineManager()


def _template_entry(template) -> dict:
    description = f"Error: {template.error}" if template.error else (template.note_name or "")
    return {
        "kind": "template",
        "id": template.id,
        "name": template.id,
        "description": description,
    }


def list_all_artifacts() -> list[dict]:
    entries: list[dict] = []
    entries.extend(
        {"kind": "skill", "id": skill.id, "name": skill.name, "description": skill.description}
        for skill in _skill_manager.get_all()
    )
    entries.extend(_template_entry(template) for template in _template_manager.get_all())
    entries.extend(
        {"kind": "agent", "id": agent.id, "name": agent.name, "description": agent.description or ""}
        for agent in _agent_manager.get_all()
    )
    entries.extend(
        {"kind": "pipeline", "id": pipeline.id, "name": pipeline.name, "description": pipeline.description}
        for pipeline in _pipeline_manager.get_all()
    )
    return entries
