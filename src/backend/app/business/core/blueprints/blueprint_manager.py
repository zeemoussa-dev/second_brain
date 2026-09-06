"""BlueprintManager -- the sole gateway onto Blueprints.

A Blueprint is a RECIPE for a Section: its identity, the Agents in it, and
which Skills each Agent should have. Pull one onto a fresh install and that
Section comes up running.

Deliberately not a snapshot. `.sbf` export already carries an Agent as an
opaque `profile.tar.gz` from one machine -- right for MOVING an install,
wrong for a library, because it bakes in one machine's model, keys and
history and cannot be reviewed, diffed or updated without a live machine to
re-export from. A Blueprint declares, and builds anywhere.

Preconditions are checked BEFORE anything is created. Refusing up front is
the point: the alternative is an Agent that installs cleanly and then fails
inside a cron worker at 03:00.

Required Templates are DERIVED, never authored -- they follow from what the
Blueprint's Skills declare in their own `writes:` frontmatter. Authoring
them separately would be a second copy of a fact that can drift, the same
reason `section_access.json` is derived and `allowed_callers` was removed
from `Template.json`.
"""
from __future__ import annotations

from app.business.core.agents.agent_manager import AgentManager
from app.business.core.blueprints.blueprint import Blueprint, BlueprintAgent
from app.business.core.sections.section_manager import SectionManager
from app.business.core.skills.skill_manager import SkillManager
from app.data_access import blueprints as blueprints_data
from app.obsidian.tags import tag_slug


class BlueprintManager:
    def _to_blueprint(self, blueprint_id: str, data: dict) -> Blueprint:
        section = data.get("section") or {}
        return Blueprint(
            id=blueprint_id,
            name=data.get("name") or blueprint_id,
            description=data.get("description") or "",
            schema_version=int(data.get("schema_version", 1)),
            version=int(data.get("version", 1)),
            section_name=section.get("name") or data.get("name") or blueprint_id,
            section_icon=section.get("icon"),
            section_color=section.get("color"),
            agents=[
                BlueprintAgent(
                    id=agent["id"], name=agent.get("name") or agent["id"],
                    type=agent.get("type") or "worker",
                    skill_ids=list(agent.get("skill_ids") or []),
                    icon=agent.get("icon"), color=agent.get("color"),
                    model=agent.get("model"), reasoning_effort=agent.get("reasoning_effort"),
                    clone_from=agent.get("clone_from") or "default",
                    soul=agent.get("soul"),
                )
                for agent in (data.get("agents") or [])
            ],
        )

    def get_all(self) -> list[Blueprint]:
        found: list[Blueprint] = []
        for blueprint_id in blueprints_data.list_blueprint_ids():
            try:
                found.append(self._to_blueprint(blueprint_id, blueprints_data.read_blueprint_json(blueprint_id)))
            except (OSError, ValueError, TypeError, KeyError) as exc:
                found.append(Blueprint(
                    id=blueprint_id, name=blueprint_id, description="",
                    schema_version=0, version=0, section_name=blueprint_id, error=str(exc),
                ))
        return found

    def get_by_id(self, blueprint_id: str) -> Blueprint | None:
        try:
            return self._to_blueprint(blueprint_id, blueprints_data.read_blueprint_json(blueprint_id))
        except (OSError, ValueError, TypeError, KeyError):
            return None

    def preflight(self, blueprint_id: str) -> dict:
        """Everything that would stop this Blueprint installing, without
        creating anything. `ok` is the only thing install() consults.

        Reports what already exists too: installing is idempotent by
        intention, and an operator deserves to know they are topping up an
        existing Section rather than standing up a new one.
        """
        blueprint = self.get_by_id(blueprint_id)
        if blueprint is None:
            return {"blueprint_id": blueprint_id, "ok": False,
                    "problems": ["no Blueprint " + repr(blueprint_id) + " in the library"]}

        skill_manager = SkillManager()
        problems: list[str] = []
        templates: set[str] = set()
        undeclared: list[str] = []

        for skill_id in blueprint.skill_ids:
            skill = skill_manager.get_by_id(skill_id)
            if skill is None:
                problems.append("Skill " + repr(skill_id) + " is not in the catalog")
                continue
            problems.extend(skill_id + ": " + p for p in skill_manager.validate_declared_writes(skill_id))
            declared = skill_manager._declared_writes(skill_id)
            if not declared:
                # The Template closure is only as complete as the Skills'
                # own declarations. A Skill that declares nothing is not
                # checked against any Template -- report it rather than let
                # a partial check read as a clean one.
                undeclared.append(skill_id)
            templates.update(entry["template"] for entry in declared)

        for agent in blueprint.agents:
            if agent.soul and blueprints_data.read_blueprint_asset(blueprint_id, agent.soul) is None:
                problems.append(agent.id + ": soul file " + repr(agent.soul) + " missing from the Blueprint")

        agent_manager = AgentManager()
        section_id = tag_slug(blueprint.section_name)
        return {
            "blueprint_id": blueprint_id,
            "ok": not problems,
            "problems": problems,
            "skills": blueprint.skill_ids,
            "templates": sorted(templates),
            # Skills with no writes: declaration -- the Template check could not
            # cover them. Not a failure, but the check is partial, and saying
            # so is the difference between a real guarantee and a false one.
            "unchecked_skills": undeclared,
            "section_id": section_id,
            "already": {
                "section": SectionManager().get_by_id(section_id) is not None,
                "agents": [a.id for a in blueprint.agents if agent_manager.get_by_id(a.id) is not None],
            },
        }

    def install(self, blueprint_id: str) -> dict:
        """Creates the Section and its Agents and deploys each Agent's
        declared Skills. Refuses unless preflight passes -- nothing is
        created when a precondition fails, so a refusal never leaves a
        half-built Section behind.

        Idempotent: an existing Section is reused and an existing Agent is
        left alone, but its Skills are still reconciled -- an Agent existing
        does not mean it has what this Blueprint says it should.
        """
        checks = self.preflight(blueprint_id)
        if not checks["ok"]:
            return {"installed": False, **checks}

        blueprint = self.get_by_id(blueprint_id)
        section = SectionManager().create(blueprint.section_name)
        if blueprint.section_icon or blueprint.section_color:
            SectionManager().update(section.id, icon=blueprint.section_icon, color=blueprint.section_color)

        agent_manager = AgentManager()
        agents: dict[str, str] = {}
        skills: dict[str, dict] = {}
        for spec in blueprint.agents:
            if agent_manager.get_by_id(spec.id) is not None:
                agents[spec.id] = "already"
                skills[spec.id] = agent_manager.ensure_skills(spec.id, spec.skill_ids)
                continue
            soul = blueprints_data.read_blueprint_asset(blueprint_id, spec.soul) if spec.soul else None
            agent_manager.create(
                spec.id, name=spec.name, section_id=section.id, type=spec.type,
                prompt=soul, skill_ids=spec.skill_ids, clone_from=spec.clone_from,
            )
            if spec.icon or spec.color or spec.model or spec.reasoning_effort:
                agent_manager.update(
                    spec.id, icon=spec.icon, color=spec.color,
                    model=spec.model, reasoning_effort=spec.reasoning_effort,
                )
            agents[spec.id] = "created"
            skills[spec.id] = dict.fromkeys(spec.skill_ids, "deployed")

        return {
            "installed": True, "blueprint_id": blueprint_id, "section_id": section.id,
            "agents": agents, "skills": skills,
            "templates": checks["templates"], "problems": [],
        }
