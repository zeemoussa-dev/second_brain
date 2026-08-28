"""SkillManager -- the sole gateway onto Skill data (mirrors Section/
Agent/.../Tool Manager's own "one real gateway" rule).

A Skill's real CONTENT (SKILL.md + scripts/) lives in the checked-in
"skills template repo" -- Hermes-Provisioning/skills/<category>/<slug>/
(data_access/skills.py) -- our own canonical copy, per operator (2026-
08-28): "we do a copy for all Skills inside our System". Its real
METADATA (name/description/tool grouping/deployment list/mutates/origin)
lives in the Registry's Tools/<tool>/Skills/<slug>/{Skill.json,
Skill-visual.json} (data_access/tools.py) -- the same tree RegistryLoader
already reads for the Agents Map Skills panel, so writing there keeps
that panel current for free.

Deployment is 1:many from our side (a Skill's `deployed_to` lists every
real Hermes profile it's pushed to) but each individual push/pull is a
1:1 call against a single profile's own skills/ folder, via
app.hermes.skills.HermesSkills -- confirmed operator convention (2026-
08-28: "Our store is 1:many hermes is 1:1").

sync_from_hermes() is the real drift-catcher a cron job calls: sweeps
every real Hermes profile (app.hermes.profiles.HermesProfiles) for
skills under an already-known category (data_access.skills.
list_categories() -- our own real, human-editable allowlist; a category
only exists there once a human has actually put a skill under it, so
this can never accidentally ingest Hermes' own ~80 bundled third-party
hub skills living under unrelated categories like apple/github/creative
-- confirmed operator convention, 2026-08-28: "category allowlist...
everything else is ignored as third-party noise"). A skill already
known just gets its deployed_to reconciled; a genuinely new one (new
slug, known category) has its content pulled in and is filed under the
catch-all "jarvis" Tool for a human to re-assign once they've looked at
it (operator: "skills that are generated with hermes will go under a
tool called jarvis")."""
from __future__ import annotations

from datetime import datetime, timezone

from app.business.core.skills.skill import Skill
from app.business.core.tools.tool_manager import ToolManager
from app.business.hermes.client import get_client
from app.data_access import skills as skills_data
from app.data_access import tools as tools_data

_JARVIS_TOOL_ID = "jarvis"


class SkillManager:
    def _to_skill(self, skill_id: str, category: str) -> Skill:
        tool_id = tools_data.find_tool_id_for_skill(skill_id)
        meta = (tools_data.read_skill_entry(tool_id, skill_id) if tool_id else None) or {}
        visual = tools_data.read_skill_visual(tool_id, skill_id) if tool_id else {}
        return Skill(
            id=skill_id,
            name=meta.get("name") or skill_id,
            description=meta.get("description") or "",
            category=category,
            tool_id=tool_id,
            mutates=meta.get("mutates", True),
            origin=meta.get("origin", "second-brain"),
            deployed_to=list(meta.get("deployed_to") or []),
            icon=visual.get("icon") or "bolt",
            created_at=meta.get("created_at", ""),
            updated_at=meta.get("updated_at"),
        )

    def get_all(self) -> list[Skill]:
        skills: list[Skill] = []
        for skill_id in skills_data.list_skill_ids():
            category = skills_data.category_of(skill_id)
            if category is not None:
                skills.append(self._to_skill(skill_id, category))
        return skills

    def get_by_id(self, skill_id: str) -> Skill | None:
        category = skills_data.category_of(skill_id)
        if category is None:
            return None
        return self._to_skill(skill_id, category)

    def _write_meta(self, skill: Skill) -> None:
        tool_id = skill.tool_id or _JARVIS_TOOL_ID
        if tool_id == _JARVIS_TOOL_ID:
            self._ensure_jarvis_tool()
        tools_data.write_skill_entry(
            tool_id, skill.id,
            {
                "id": skill.id, "name": skill.name, "description": skill.description,
                "category": skill.category, "mutates": skill.mutates, "origin": skill.origin,
                "deployed_to": skill.deployed_to, "created_at": skill.created_at,
                "updated_at": skill.updated_at,
            },
            {"icon": skill.icon},
        )

    def _ensure_jarvis_tool(self) -> None:
        if ToolManager().get_by_id(_JARVIS_TOOL_ID) is None:
            ToolManager().create(
                _JARVIS_TOOL_ID, name="Jarvis",
                description="Skills Hermes/an agent generated on its own -- synced in, not yet triaged onto a real Tool.",
            )

    def create(
        self, category: str, skill_id: str, name: str, description: str, skill_md_content: str, *,
        tool_id: str, scripts: dict[str, str] | None = None, deploy_to: list[str] | None = None,
        mutates: bool = True, icon: str = "bolt",
    ) -> Skill:
        """Writes the canonical template-repo copy, files its Registry
        metadata under `tool_id`, then pushes to every profile in
        `deploy_to`."""
        now = datetime.now(timezone.utc).isoformat()
        skills_data.write_skill_md(category, skill_id, skill_md_content)
        for rel_path, content in (scripts or {}).items():
            skills_data.write_script(category, skill_id, rel_path, content)

        client = get_client()
        deployed: list[str] = []
        for profile_id in (deploy_to or []):
            client.skills.create(profile_id, category, skill_id, skill_md_content, scripts)
            deployed.append(profile_id)

        skill = Skill(
            id=skill_id, name=name, description=description, category=category,
            tool_id=tool_id, mutates=mutates, origin="second-brain", deployed_to=deployed,
            icon=icon, created_at=now, updated_at=None,
        )
        self._write_meta(skill)
        return skill

    def update(
        self, skill_id: str, *, name: str | None = None, description: str | None = None,
        skill_md_content: str | None = None, scripts: dict[str, str] | None = None,
        tool_id: str | None = None, mutates: bool | None = None, icon: str | None = None,
    ) -> Skill | None:
        """`None` (omitted) = leave unchanged, same convention every
        other Manager's own update() uses. Content changes (SKILL.md/
        scripts) re-push to every profile already in deployed_to."""
        skill = self.get_by_id(skill_id)
        if skill is None:
            return None

        if name is not None:
            skill.name = name
        if description is not None:
            skill.description = description
        if mutates is not None:
            skill.mutates = mutates
        if icon is not None:
            skill.icon = icon

        if skill_md_content is not None:
            skills_data.write_skill_md(skill.category, skill_id, skill_md_content)
        for rel_path, content in (scripts or {}).items():
            skills_data.write_script(skill.category, skill_id, rel_path, content)

        if skill_md_content is not None or scripts:
            client = get_client()
            for profile_id in skill.deployed_to:
                client.skills.update(profile_id, skill_id, skill_md_content=skill_md_content, scripts=scripts)

        old_tool_id = skill.tool_id or _JARVIS_TOOL_ID
        if tool_id is not None and tool_id != old_tool_id:
            tools_data.move_skill_entry(old_tool_id, tool_id, skill_id)
            skill.tool_id = tool_id

        skill.updated_at = datetime.now(timezone.utc).isoformat()
        self._write_meta(skill)
        return skill

    def deploy(self, skill_id: str, profile_id: str) -> Skill | None:
        """Pushes this Skill's current real content to one more real
        Hermes profile."""
        skill = self.get_by_id(skill_id)
        if skill is None or profile_id in skill.deployed_to:
            return skill
        skill_md = skills_data.read_skill_md(skill_id) or ""
        scripts = skills_data.list_scripts(skill_id)
        get_client().skills.create(profile_id, skill.category, skill_id, skill_md, scripts)
        skill.deployed_to.append(profile_id)
        skill.updated_at = datetime.now(timezone.utc).isoformat()
        self._write_meta(skill)
        return skill

    def undeploy(self, skill_id: str, profile_id: str) -> Skill | None:
        """Removes this Skill from one real Hermes profile without
        touching the canonical template-repo copy."""
        skill = self.get_by_id(skill_id)
        if skill is None:
            return None
        if profile_id in skill.deployed_to:
            get_client().skills.delete(profile_id, skill_id)
            skill.deployed_to.remove(profile_id)
            skill.updated_at = datetime.now(timezone.utc).isoformat()
            self._write_meta(skill)
        return skill

    def delete(self, skill_id: str) -> dict:
        """Removes this Skill from every real profile it's deployed to,
        then its canonical template-repo copy and Registry metadata."""
        skill = self.get_by_id(skill_id)
        if skill is None:
            return {"deleted": False}
        client = get_client()
        for profile_id in skill.deployed_to:
            client.skills.delete(profile_id, skill_id)
        skills_data.delete_skill_dir(skill_id)
        tools_data.delete_skill_entry(skill.tool_id or _JARVIS_TOOL_ID, skill_id)
        return {"deleted": True}

    def sync_from_hermes(self) -> dict:
        """Sweeps every real Hermes profile for skills under an already-
        known category and reconciles deployed_to; a genuinely new skill
        (new slug, known category) has its content pulled into the
        template repo and is filed under the catch-all "jarvis" Tool.
        Categories no human has ever put a skill under -- Hermes' own
        bundled third-party hub skills included -- are never touched."""
        known_categories = set(skills_data.list_categories())
        known_skill_ids = set(skills_data.list_skill_ids())
        client = get_client()
        imported: list[str] = []
        reconciled: list[str] = []

        for profile in client.profiles.get_all():
            for hermes_skill in client.skills.get_all(profile.id):
                if hermes_skill.category not in known_categories:
                    continue
                slug = hermes_skill.slug  # HermesSkill.id is "<category>/<slug>"; ours is the plain slug

                if slug in known_skill_ids:
                    skill = self.get_by_id(slug)
                    if skill is not None and profile.id not in skill.deployed_to:
                        skill.deployed_to.append(profile.id)
                        skill.updated_at = datetime.now(timezone.utc).isoformat()
                        self._write_meta(skill)
                        reconciled.append(f"{slug} <- {profile.id}")
                    continue

                skill_md = client.skills.read(profile.id, hermes_skill.id) or ""
                skills_data.write_skill_md(hermes_skill.category, slug, skill_md)
                now = datetime.now(timezone.utc).isoformat()
                skill = Skill(
                    id=slug, name=hermes_skill.name, description=hermes_skill.description,
                    category=hermes_skill.category, tool_id=_JARVIS_TOOL_ID, mutates=True,
                    origin="jarvis", deployed_to=[profile.id], icon="bolt",
                    created_at=now, updated_at=None,
                )
                self._write_meta(skill)
                known_skill_ids.add(slug)
                imported.append(slug)

        return {"imported": imported, "reconciled": reconciled}
