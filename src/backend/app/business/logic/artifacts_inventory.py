"""Cross-type artifact inventory (REQ-SB-85-US-01) -- composes the seven
Managers (Skill/Template/Agent/Pipeline/Index/Action/Workflow) into one
flat, tagged list. Pure read composition -- no owned store, no
write path -- matches the existing `business/logic/` cross-entity,
no-caching pattern (`section_agents.py`/`cockpit_view.py`/
`system_health.py`; `system_health.py`'s own header comment is this
module's direct precedent). Recomputed fresh on every call by
construction -- every `get_all()` call below is a real, live read, never
cached here or anywhere upstream.

`kind` is always exactly one of "skill"/"template"/"agent"/"pipeline"/
"index"/"action"/"workflow" -- no 8th value is ever produced, since these
are the only 7 Managers composed. Index joined the set on 2026-09-06,
when its own engine became backend-owned code rather than a Skill's
private scripts folder; before that it could not travel in a bundle at
all. Action joined it on 2026-10-16 (`ADR-032`, `REQ-SB-95-US-02`) for
the same reason: a catalogue entry that cannot travel in a bundle is not
an artifact. Workflow joined it on 2026-10-18 (`ADR-032`/`ADR-034`,
`REQ-SB-95-US-04`) for that same reason again -- the operator's
documented handling of a kind of request is as portable as the Actions
it names.
`get_all()` here returns this install's STORED Actions only --
plugin-contributed ones are composed on top at read time by
`REQ-SB-95-US-02-T05` and are never written into the store.

`Pipeline` is composed here exactly as it always was and is NOT what the
new `workflow` kind is built from (`ADR-032`: Pipeline is left exactly as
it is). A Pipeline is time-triggered and keeps its own store, its own
Manager and its own `"pipeline"` rows; a Workflow is intent-triggered and
adds rows beside them. No row ever moves between the two.

`name`/`description` are pulled from each entity's own real
field; `Template` has neither field on its dataclass (confirmed by direct
reading, business/core/templates/template.py) so `name` falls back to
`template.id` and `description` falls back to `template.note_name or ""`.
`Action` carries a real `description` but likewise no `name` (confirmed by
direct reading, business/core/actions/action.py -- an Action's id IS how
the catalogue names it), so its `name` falls back to `action.id` the same
way Template's does. `Workflow` is the same case again (confirmed by
direct reading, business/core/workflows/workflow.py): a real
`description`, no `name`, so its id names it. Its `request_kind` is
deliberately NOT folded into either field -- it is a third, different
fact (what an agent recognises an incoming intent as), and quietly
substituting it for a description the operator left blank would make the
inventory say something the operator never wrote.
A malformed Template (`Template.error` set, per `TemplateManager.get_all()`'s
own honest-list convention) is still included, with `description` replaced
by `f"Error: {template.error}"` instead of being silently dropped."""
from __future__ import annotations

from app.business.core.actions.action_manager import ActionManager
from app.business.core.agents.agent_manager import AgentManager
from app.business.core.index.index_manager import IndexManager
from app.business.core.pipelines.pipeline_manager import PipelineManager
from app.business.core.skills.skill_manager import SkillManager
from app.business.core.templates.template_manager import TemplateManager
from app.business.core.workflows.workflow_manager import WorkflowManager

_skill_manager = SkillManager()
_template_manager = TemplateManager()
_agent_manager = AgentManager()
_pipeline_manager = PipelineManager()
_index_manager = IndexManager()
_action_manager = ActionManager()
_workflow_manager = WorkflowManager()


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
    entries.extend(
        {"kind": "index", "id": index.id, "name": index.name, "description": ""}
        for index in _index_manager.get_all()
    )
    entries.extend(
        {"kind": "action", "id": action.id, "name": action.id, "description": action.description}
        for action in _action_manager.get_all()
    )
    entries.extend(
        {"kind": "workflow", "id": workflow.id, "name": workflow.id, "description": workflow.description}
        for workflow in _workflow_manager.get_all()
    )
    return entries
