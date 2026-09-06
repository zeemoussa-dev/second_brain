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

import re

from app.business.core.agents.agent_manager import AgentManager
from app.business.core.blueprints.blueprint import Blueprint, BlueprintAgent
from app.business.core.sections.section_manager import SectionManager
from app.business.core.skills.skill_manager import SkillManager
from app.data_access import blueprints as blueprints_data
from app.obsidian.tags import tag_slug

# A drive-letter or UNC path in a SHIPPED asset is always wrong.
# A drive-letter path in a SHIPPED asset is always wrong. Built from
# chr(92) because a lone backslash inside a character class escapes the
# closing bracket and silently makes the class unterminated.
_SEP = "(?:/|" + chr(92) + chr(92) + ")"
_ABSOLUTE_PATH = re.compile("[A-Za-z]:" + _SEP, re.MULTILINE)


class BlueprintManager:
    def _to_blueprint(self, blueprint_id: str, data: dict) -> Blueprint:
        # `suggested_section` is the current key; `section` is the older one
        # that imposed a Section, kept readable so an existing Blueprint file
        # does not silently lose its default.
        section = data.get("suggested_section") or data.get("section") or {}
        return Blueprint(
            id=blueprint_id,
            name=data.get("name") or blueprint_id,
            description=data.get("description") or "",
            schema_version=int(data.get("schema_version", 1)),
            version=int(data.get("version", 1)),
            suggested_section_name=section.get("name") or data.get("name") or blueprint_id,
            suggested_section_icon=section.get("icon"),
            suggested_section_color=section.get("color"),
            agents=[
                BlueprintAgent(
                    id=agent["id"], name=agent.get("name") or agent["id"],
                    type=agent.get("type") or "worker",
                    skill_ids=list(agent.get("skill_ids") or []),
                    icon=agent.get("icon"), color=agent.get("color"),
                    model=agent.get("model"), reasoning_effort=agent.get("reasoning_effort"),
                    clone_from=agent.get("clone_from") or "default",
                    soul=agent.get("soul"),
                    peer=bool(agent.get("peer")),
                    primary_routing_snippet=agent.get("primary_routing_snippet"),
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
                    schema_version=0, version=0, suggested_section_name=blueprint_id, error=str(exc),
                ))
        return found

    def get_by_id(self, blueprint_id: str) -> Blueprint | None:
        try:
            return self._to_blueprint(blueprint_id, blueprints_data.read_blueprint_json(blueprint_id))
        except (OSError, ValueError, TypeError, KeyError):
            return None

    def preflight(self, blueprint_id: str, section_id: str | None = None) -> dict:
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
            if agent.peer and not (agent.primary_routing_snippet or "").strip():
                problems.append(agent.id + ": marked peer but carries no primary_routing_snippet")
            if agent.soul and blueprints_data.read_blueprint_asset(blueprint_id, agent.soul) is None:
                problems.append(agent.id + ": soul file " + repr(agent.soul) + " missing from the Blueprint")
            elif agent.soul:
                asset = blueprints_data.read_blueprint_asset(blueprint_id, agent.soul) or ""
                if _ABSOLUTE_PATH.search(asset):
                    problems.append(
                        agent.id + ": its soul carries a literal absolute path -- a shipped "
                        "Blueprint must use <OPERATOR_VAULT>, or every install writes into "
                        "one machine's folders (BUG-051)"
                    )

        agent_manager = AgentManager()
        section_manager = SectionManager()
        # The operator's choice wins; the Blueprint only suggests (BUG-046).
        target_section_id = section_id or tag_slug(blueprint.suggested_section_name)
        if section_id and section_manager.get_by_id(section_id) is None:
            problems.append("no Section " + repr(section_id) + " on this install")
        return {
            "blueprint_id": blueprint_id,
            "ok": not problems,
            "problems": problems,
            "skills": blueprint.skill_ids,
            "peers": [a.id for a in blueprint.agents if a.peer],
            "templates": sorted(templates),
            # Skills with no writes: declaration -- the Template check could not
            # cover them. Not a failure, but the check is partial, and saying
            # so is the difference between a real guarantee and a false one.
            "unchecked_skills": undeclared,
            "section_id": target_section_id,
            "suggested_section": blueprint.suggested_section_name,
            "available_sections": [
                {"id": s.id, "name": s.name} for s in section_manager.get_all()
            ],
            "already": {
                "section": section_manager.get_by_id(target_section_id) is not None,
                "agents": [a.id for a in blueprint.agents if agent_manager.get_by_id(a.id) is not None],
            },
        }

    # A shipped Blueprint must never carry one machine's paths -- BUG-051:
    # the librarian souls hard-coded the harvesting operator's absolute vault
    # path, install() copied it verbatim into every profile, and the agents
    # wrote into a vault that was not theirs. It failed loudly here only
    # because that path was unwritable; on a host where a similarly-named one
    # exists it would silently misplace real notes.
    _PLACEHOLDERS = {"<OPERATOR_VAULT>": "vault_path", "<OPERATOR_DATA>": "second_brain_data_path"}

    def _resolve_placeholders(self, text: str) -> str:
        """Substitutes this install's own real paths into a Blueprint asset."""
        from app.config import settings
        for token, setting_name in self._PLACEHOLDERS.items():
            text = text.replace(token, str(getattr(settings, setting_name, "") or ""))
        return text

    def _primary_already_describes(self, agent_id: str) -> bool:
        """Whether this machine's Primary SOUL.md already mentions the agent
        outside our own marker block. True for a hand-configured install,
        where appending would duplicate rather than add."""
        from app.config import settings
        soul_path = settings.hermes_home_path / "SOUL.md"
        if not soul_path.is_file():
            return False
        text = soul_path.read_text(encoding="utf-8", errors="replace")
        from app.business.logic import artifact_import
        begin, _ = artifact_import._primary_routing_markers(agent_id)
        return agent_id in text and begin not in text

    # The snippets are authored as list ITEMS, written to sit under a routing
    # section. Hermes' stock SOUL.md has no such section -- it is one
    # paragraph about tone -- so appending them raw left dangling bullets
    # that describe what each agent owns while nothing established that
    # Primary may delegate at all (BUG-052).
    _PEER_HEADING = "## Your peer agents"
    _PEER_LEAD_IN = (
        "You have peer agents. Each owns a domain you do not handle yourself. "
        "When a request belongs to one of them, relay it verbatim using the "
        "command shown and return its reply -- do not attempt the work yourself, "
        "and do not paraphrase the request away."
    )

    def _ensure_peer_section(self) -> bool:
        """Makes sure Primary's SOUL.md has a heading and lead-in for peer
        bullets to live under, ABOVE any that are already there.

        Appending it at the end was right for a fresh SOUL and wrong for one
        that had already been wired by the pre-fix code (BUG-055) -- which is
        every install the BUG-052 fix was written for. It produced a heading
        announcing peers with nothing under it, and the bullets still
        orphaned above: worse than what it replaced, because it now looks
        deliberate.
        """
        from app.config import settings
        soul_path = settings.hermes_home_path / "SOUL.md"
        if not soul_path.is_file():
            return False
        text = soul_path.read_text(encoding="utf-8")
        if self._PEER_HEADING in text:
            return False
        NL = chr(10)
        block = self._PEER_HEADING + NL + NL + self._PEER_LEAD_IN + NL
        marker = "<!-- BEGIN PRIMARY ROUTING:"
        if marker in text:
            # Migration: put the heading above the first block already there,
            # so existing bullets end up underneath it rather than stranded.
            cut = text.index(marker)
            updated = text[:cut].rstrip(NL) + NL + NL + block + NL + text[cut:]
        else:
            updated = text.rstrip(NL) + NL + NL + block
        soul_path.write_text(updated, encoding="utf-8")
        return True

    def _roll_back(self, agent_ids: list[str], section_id: str | None) -> dict:
        """Undoes a partial install. Best-effort by design: a cleanup that
        raises would replace the real error with its own, and the operator
        would never learn why the install failed."""
        undone: dict[str, str] = {}
        for agent_id in reversed(agent_ids):
            try:
                AgentManager().delete(agent_id)
                undone[agent_id] = "removed"
            except Exception as exc:
                undone[agent_id] = "could not remove: " + str(exc)
        if section_id:
            try:
                SectionManager().delete(section_id)
                undone[section_id] = "section removed"
            except Exception as exc:
                undone[section_id] = "could not remove section: " + str(exc)
        return undone

    def install(self, blueprint_id: str, *, section_id: str | None = None, wire_peers: bool = True) -> dict:
        """Creates the Section and its Agents and deploys each Agent's
        declared Skills. Refuses unless preflight passes -- nothing is
        created when a precondition fails, so a refusal never leaves a
        half-built Section behind.

        Idempotent: an existing Section is reused and an existing Agent is
        left alone, but its Skills are still reconciled -- an Agent existing
        does not mean it has what this Blueprint says it should.
        """
        checks = self.preflight(blueprint_id, section_id)
        if not checks["ok"]:
            return {"installed": False, **checks}

        blueprint = self.get_by_id(blueprint_id)
        section_manager = SectionManager()

        # Anything created here is undone if a later step raises (BUG-044).
        # The precondition guarantee only ever covered preconditions; a
        # failure PAST them left the Section behind, and an operator was
        # left with a half-built Section they never asked for.
        created_section_id: str | None = None
        created_agent_ids: list[str] = []

        if section_id:
            section = section_manager.get_by_id(section_id)
        else:
            existing = section_manager.get_by_id(tag_slug(blueprint.suggested_section_name))
            section = existing or section_manager.create(blueprint.suggested_section_name)
            if existing is None:
                created_section_id = section.id
                if blueprint.suggested_section_icon or blueprint.suggested_section_color:
                    section_manager.update(
                        section.id, icon=blueprint.suggested_section_icon,
                        color=blueprint.suggested_section_color,
                    )

        agent_manager = AgentManager()
        agents: dict[str, str] = {}
        skills: dict[str, dict] = {}
        peers: dict[str, str] = {}
        try:
            for spec in blueprint.agents:
                if agent_manager.get_by_id(spec.id) is not None:
                    agents[spec.id] = "already"
                    skills[spec.id] = agent_manager.ensure_skills(spec.id, spec.skill_ids)
                    continue
                soul = blueprints_data.read_blueprint_asset(blueprint_id, spec.soul) if spec.soul else None
                if soul is not None:
                    soul = self._resolve_placeholders(soul)
                agent_manager.create(
                    spec.id, name=spec.name, section_id=section.id, type=spec.type,
                    prompt=soul, skill_ids=spec.skill_ids, clone_from=spec.clone_from,
                )
                created_agent_ids.append(spec.id)
                if spec.icon or spec.color or spec.model or spec.reasoning_effort:
                    agent_manager.update(
                        spec.id, icon=spec.icon, color=spec.color,
                        model=spec.model, reasoning_effort=spec.reasoning_effort,
                    )
                agents[spec.id] = "created"
                skills[spec.id] = dict.fromkeys(spec.skill_ids, "deployed")
        except Exception as exc:
            # Undo in reverse, and never let cleanup mask the real failure:
            # the operator needs the ORIGINAL error, not whatever the tidy-up
            # hit on the way out.
            undone = self._roll_back(created_agent_ids, created_section_id)
            return {
                "installed": False, "blueprint_id": blueprint_id,
                "section_id": section.id if section else None,
                "problems": [type(exc).__name__ + ": " + str(exc)],
                "rolled_back": undone,
            }

        soul_changed = False
        if wire_peers and any(a.peer and a.primary_routing_snippet for a in blueprint.agents):
            # Heading first, so the bullets appended below have something to
            # belong to. Its return is KEPT: adding the heading changes
            # Primary's prompt on its own, and discarding it meant an upgrade
            # install reported no reset needed while a running Primary could
            # not see the change (BUG-055). That cost a real misrouted file
            # upload, fixed by hand.
            soul_changed = self._ensure_peer_section()
        if wire_peers:
            # A peer is only REACHABLE once Primary knows to relay to it.
            # Without this the Agent exists, runs, and is simply never
            # reached -- which looks like a working install and is not.
            # apply_primary_routing_snippet is marker-guarded, so re-running
            # is a no-op and an operator's own edit is never overwritten.
            from app.business.logic import artifact_import
            for spec in blueprint.agents:
                if not spec.peer or not spec.primary_routing_snippet:
                    continue
                try:
                    # apply_primary_routing_snippet is idempotent by MARKER,
                    # not by content -- so on a machine whose Primary SOUL.md
                    # was written by hand it would append a second, duplicate
                    # set of routing instructions for the same agent. Two
                    # descriptions of how to reach one agent is worse than
                    # none: the Primary has to pick. Detect the unmarked
                    # mention and leave it alone.
                    if self._primary_already_describes(spec.id):
                        peers[spec.id] = "already described in Primary (unmarked) -- left alone"
                        continue
                    outcome = artifact_import.apply_primary_routing_snippet(
                        spec.id, spec.primary_routing_snippet,
                    )
                    peers[spec.id] = "wired" if outcome["applied"] else outcome["detail"]
                except FileNotFoundError as exc:
                    # No Primary SOUL.md on this machine. The Section is
                    # still real and usable directly; say so rather than
                    # failing an otherwise-good install.
                    peers[spec.id] = "not wired: " + str(exc)

        return {
            "installed": True, "blueprint_id": blueprint_id, "section_id": section.id,
            "agents": agents, "skills": skills, "peers": peers,
            "templates": checks["templates"], "problems": [],
            # A running Hermes session is given its prompt ONCE and never
            # re-reads it, so a Primary mid-conversation cannot see the peers
            # that were just wired -- which is exactly when the operator
            # tries them. Surfaced rather than assumed (BUG-052).
            # ANY change to Primary's prompt needs the session restarting --
            # a newly wired peer, or just the heading and lead-in appearing.
            "primary_session_reset_required": bool(
                soul_changed or [state for state in peers.values() if state == "wired"]
            ),
        }
