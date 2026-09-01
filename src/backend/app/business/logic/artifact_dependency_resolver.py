"""Cross-artifact dependency-closure resolution (REQ-SB-85-US-02, ADR-013)
-- given an initial (kind, id) selection, resolves and returns the FULL
real dependency closure (an Agent's own Registry `skill_ids`/`depends_on`,
recursed transitively; a Skill's own implicit Template.json coupling; a
Pipeline's own real implementing Skill, recursed the same way as a direct
Skill selection), each with a human-readable reason it was included. Pure
composition over the 4 already-`Done` Managers -- no owned store, no file
write of any kind (`sbf_archive.py`, T04, is the only writer).

BUG-041 fix (2026-09-01): the Pipeline branch previously treated each
`PipelineStep.id` (e.g. "fetch-meetings") as if it were an Agent id and
tried to resolve it via `AgentManager.get_by_id()` -- but `PipelineStep`
carries no real Agent/Skill linkage at all (it exists purely to drive the
Job Tree visualization), so every one of those lookups silently resolved
to `None` and nothing was ever added. Confirmed live: NO Pipeline export
has ever included its real Skill. Fixed via
`PipelineManager.get_implementing_skill_id()` -- the ONE real path from a
Pipeline to its Skill, composed live from `cron_job_id`/`cron_profile_id`
-> the real Hermes cron job -> that job's own `skill` field.

A Skill's own shared-file `scripts/` copies are deliberately NOT added as
separate closure entries -- ADR-013's own Decision text is explicit this is
"disclosure only, not a separate traversal... not re-listing the Skill's
own files as pseudo-artifacts" (T04's archive writer includes that real
content regardless, since it already travels with the Skill's own
payload). Note this narrows the Objective section's own illustrative
depends_via example list (which shows a "shared file: vault_manager.py"
string alongside the others) -- followed the more specific, more detailed
Traversal Rules bullet instead, logged as a scope-internal judgement call
in this task's own Implementation Log.

`data_access.skills.list_scripts`/`read_skill_md` are called directly
(not through SkillManager, which exposes neither as a public getter) --
this task's own Starting State/Inputs section names `list_scripts`
explicitly as an already-real, ready-to-compose input alongside the 4
Managers; both are pure reads (zero writes), the same raw data
SkillManager.deploy() already reads internally via the identical call.

An Agent's own real `skill_ids` (`AgentManager._to_agent`:
`[skill.id for skill in hermes_agent.skills]`) are Hermes' own raw
`"<category>/<slug>"` form -- confirmed live against every real Agent in
this deployment (e.g. `compass-expert.skill_ids ==
['knowledge-base/compass-kb-writer']`) -- never the bare slug
`SkillManager`/`data_access.skills` key everything by (confirmed live:
`SkillManager().get_by_id('knowledge-base/compass-kb-writer')` is `None`;
`SkillManager().get_by_id('compass-kb-writer')` resolves). Normalized here
via the same "HermesSkill.id is category/slug; ours is the plain slug"
convention `SkillManager.sync_from_hermes()` already establishes -- taking
the id's own last `/`-separated segment before treating it as a Skill kind
id, so an Agent's own dependency on a real Skill actually resolves.
"""
from __future__ import annotations

from app.business.core.agents.agent_manager import AgentManager
from app.business.core.pipelines.pipeline_manager import PipelineManager
from app.business.core.skills.skill_manager import SkillManager
from app.business.core.templates.template_manager import TemplateManager
from app.data_access import skills as skills_data

_skill_manager = SkillManager()
_template_manager = TemplateManager()
_agent_manager = AgentManager()
_pipeline_manager = PipelineManager()


def _skill_own_template_matches(skill_id: str, all_template_ids: list[str]) -> list[str]:
    """A static text scan of the Skill's own SKILL.md + every real
    script's content for any real Template id appearing as a literal
    substring -- the disclosed, acceptable v1 heuristic (ADR-013's own
    Consequences: false negatives possible for a non-literal reference;
    never a more sophisticated detector than this)."""
    skill_md = skills_data.read_skill_md(skill_id) or ""
    scripts = skills_data.list_scripts(skill_id)
    haystack = skill_md + "\n" + "\n".join(scripts.values())
    return [template_id for template_id in all_template_ids if template_id and template_id in haystack]


def resolve_closure(selection: list[dict]) -> list[dict]:
    """`selection` is `[{"kind": str, "id": str}, ...]`. Returns one entry
    per resolved artifact: `{"kind", "id", "included_reason": "selected" |
    "dependency", "depends_via"}`. Every original selection entry is
    always present with `included_reason: "selected"`, even when also
    reachable as a dependency of another selected artifact (never
    duplicated -- "selected" wins over "dependency" regardless of visit
    order, since a later "selected" visit of an already-resolved
    dependency upgrades its stored reason in place). An id that doesn't
    resolve against its own kind's Manager is skipped silently -- no
    entry, no exception, no fabricated placeholder -- but every OTHER
    resolvable entry (including the rest of a partially-unresolvable
    selection) is unaffected. Cycle-safe: each (kind, id) pair's own
    dependencies are traversed at most once per call."""
    results: dict[tuple[str, str], dict] = {}
    visited: set[tuple[str, str]] = set()

    def upsert(kind: str, id_: str, reason: str, depends_via: str | None) -> None:
        key = (kind, id_)
        if key not in results:
            results[key] = {"kind": kind, "id": id_, "included_reason": reason, "depends_via": depends_via}
        elif reason == "selected" and results[key]["included_reason"] != "selected":
            results[key]["included_reason"] = "selected"
            results[key]["depends_via"] = None

    def visit(kind: str, id_: str, reason: str, depends_via: str | None) -> None:
        key = (kind, id_)
        if key in visited:
            # Already resolved (or already found unresolvable) earlier in
            # this same call -- a later "selected" visit still upgrades an
            # already-resolved dependency entry in place; an already-
            # unresolvable id (never added to `results`) stays absent.
            if reason == "selected" and key in results:
                upsert(kind, id_, reason, depends_via)
            return
        visited.add(key)

        if kind == "skill":
            skill = _skill_manager.get_by_id(id_)
            if skill is None:
                return
            upsert(kind, id_, reason, depends_via)
            all_template_ids = [template.id for template in _template_manager.get_all()]
            for template_id in _skill_own_template_matches(id_, all_template_ids):
                visit("template", template_id, "dependency", f"skill:{id_} (implicit Template coupling)")
        elif kind == "template":
            template = _template_manager.get_by_id(id_)
            if template is None:
                return
            upsert(kind, id_, reason, depends_via)
            # A Template has no further real dependencies of its own.
        elif kind == "agent":
            agent = _agent_manager.get_by_id(id_)
            if agent is None:
                return
            upsert(kind, id_, reason, depends_via)
            for dep_agent_id in agent.depends_on:
                visit("agent", dep_agent_id, "dependency", f"agent:{id_} (depends_on)")
            for dep_skill_id in agent.skill_ids:
                # Hermes' own raw "<category>/<slug>" form -- normalize to
                # the bare slug SkillManager keys everything by (see
                # module docstring).
                bare_skill_id = dep_skill_id.rsplit("/", 1)[-1]
                visit("skill", bare_skill_id, "dependency", f"agent:{id_} (skill_ids)")
        elif kind == "pipeline":
            pipeline = _pipeline_manager.get_by_id(id_)
            if pipeline is None:
                return
            upsert(kind, id_, reason, depends_via)
            skill_id = _pipeline_manager.get_implementing_skill_id(id_)
            if skill_id:
                visit("skill", skill_id, "dependency", f"pipeline:{id_} (cron job skill)")
        # An unknown `kind` (never produced by the real 4-Manager
        # inventory this selection is sourced from) resolves to nothing,
        # same silent-skip discipline as an unresolvable id.

    for entry in selection:
        visit(entry["kind"], entry["id"], "selected", None)

    return list(results.values())
