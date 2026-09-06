"""SkillManager -- the sole gateway onto Skill data (mirrors Section/
Agent/.../Tool Manager's own "one real gateway" rule).

A Skill's real CONTENT (SKILL.md + scripts/) lives in the checked-in
"skills template repo" -- business/core/skills/catalog/<tool>/<slug>/
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

import re
import yaml
from datetime import datetime, timezone

from app.business.core.skills.skill import Skill
from app.business.core.templates.template_manager import TemplateManager
from app.business.core.tools.tool_manager import ToolManager
from app.business.hermes.client import get_client
from app.config import settings
from app.data_access import skills as skills_data
from app.data_access import tools as tools_data

_JARVIS_TOOL_ID = "jarvis"


_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


class SkillPreconditionError(Exception):
    """A Skill's declared requirements are not satisfied on this install, so
    deploying it would put something in Hermes that fails only when it runs."""


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
            # Was a silent no-op: the bare slug never resolved to a real
            # deployed folder. See _push_to_profile.
            current_md = skills_data.read_skill_md(skill_id) or ""
            current_scripts = skills_data.list_scripts(skill_id)
            for profile_id in skill.deployed_to:
                self._push_to_profile(skill, profile_id, current_md, current_scripts)

        old_tool_id = skill.tool_id or _JARVIS_TOOL_ID
        if tool_id is not None and tool_id != old_tool_id:
            tools_data.move_skill_entry(old_tool_id, tool_id, skill_id)
            skill.tool_id = tool_id

        skill.updated_at = datetime.now(timezone.utc).isoformat()
        self._write_meta(skill)
        return skill

    def _all_profile_ids(self) -> list[str]:
        """Every real Hermes profile, "default" included -- profiles.get_all()
        enumerates named profiles only."""
        named = [agent.id for agent in get_client().profiles.get_all()]
        return ["default"] + [p for p in named if p != "default"]

    def forget_deployment(self, profile_id: str) -> list[str]:
        """Drops `profile_id` from every Skill's `deployed_to`. Returns the
        Skills changed.

        Called when a profile is deleted: the record describes something that
        no longer exists, and a stale one made a delete-and-reinstall come
        back with no Skills at all (BUG-056)."""
        changed: list[str] = []
        for skill in self.get_all():
            if profile_id not in skill.deployed_to:
                continue
            skill.deployed_to = [p for p in skill.deployed_to if p != profile_id]
            skill.updated_at = datetime.now(timezone.utc).isoformat()
            self._write_meta(skill)
            changed.append(skill.id)
        if changed:
            self.publish_section_access_map()
        return changed

    def reconcile_deployed_to(self, *, dry_run: bool = True) -> dict:
        """Sets each Skill's `deployed_to` to what is ACTUALLY on disk.

        Deliberately narrower than sync_from_hermes: it imports nothing and
        touches no content. It answers one question -- which profiles really
        have this Skill -- and records the answer.

        Matches on SLUG, not "<category>/<slug>". sync_from_hermes filters by
        a category allowlist, and after the 2026-09-06 regrouping by Tool
        that allowlist ("vault"/"outlook"/"pricing") no longer matches where
        the deployed copies actually sit (their old categories), so it would
        now miss every one of them.

        Why this is needed at all: `deployed_to` had drifted badly under-set
        -- `summarize-and-tag-files` recorded 1 deployment while 40 profiles
        carried it. Anything keyed off deployed_to was therefore blind to
        most of reality, including the drift check itself.
        """
        client = get_client()
        by_profile = {
            profile_id: {s.slug for s in client.skills.get_all(profile_id)}
            for profile_id in self._all_profile_ids()
        }
        changes: dict[str, dict] = {}
        for skill in self.get_all():
            actual = sorted(p for p, slugs in by_profile.items() if skill.id in slugs)
            recorded = sorted(skill.deployed_to)
            if actual == recorded:
                continue
            changes[skill.id] = {
                "added": [p for p in actual if p not in recorded],
                "removed": [p for p in recorded if p not in actual],
                "was": len(recorded), "now": len(actual),
            }
            if not dry_run:
                skill.deployed_to = actual
                skill.updated_at = datetime.now(timezone.utc).isoformat()
                self._write_meta(skill)
        if changes and not dry_run:
            self.publish_section_access_map()
        return changes

    def _push_to_profile(
        self, skill: Skill, profile_id: str, skill_md: str, scripts: dict[str, str]
    ) -> str:
        """Puts this Skill's current content into one profile and returns
        what happened: "created" | "updated" | "moved".

        Two things this has to get right, both of which were wrong before:

        1. Hermes keys a deployed skill by "<category>/<slug>", while ours
           is the bare slug. `SkillManager.update()` passed the bare slug
           to `HermesSkills.update()`, whose `_skill_dir` partitions on "/"
           -- so it resolved to a folder that does not exist, returned None,
           and the re-push to every deployed profile was a SILENT NO-OP.
           That is how a deployed copy drifts from the catalog unnoticed.

        2. The catalog was regrouped by Tool on 2026-09-06, so a deployed
           copy can still sit under its old category folder. Writing the
           new location without removing the old one would leave Hermes
           seeing the same Skill twice, under two categories.
        """
        client = get_client()
        existing = next(
            (s for s in client.skills.get_all(profile_id) if s.slug == skill.id), None
        )
        if existing is None:
            client.skills.create(profile_id, skill.category, skill.id, skill_md, scripts)
            return "created"
        if existing.category != skill.category:
            client.skills.create(profile_id, skill.category, skill.id, skill_md, scripts)
            client.skills.delete(profile_id, existing.id)
            return "moved"
        client.skills.update(profile_id, existing.id, skill_md_content=skill_md, scripts=scripts)
        return "updated"

    def redeploy(self, skill_id: str) -> dict[str, str]:
        """Pushes current catalog content to every profile this Skill is
        already deployed to. profile_id -> what happened."""
        skill = self.get_by_id(skill_id)
        if skill is None:
            return {}
        problems = self.validate_declared_writes(skill_id)
        if problems:
            raise SkillPreconditionError(f"{skill_id!r} cannot be deployed -- " + "; ".join(problems))
        skill_md = skills_data.read_skill_md(skill_id) or ""
        scripts = skills_data.list_scripts(skill_id)
        skills_data.deploy_shared_managers(settings.hermes_home_path)
        return {
            profile_id: self._push_to_profile(skill, profile_id, skill_md, scripts)
            for profile_id in skill.deployed_to
        }

    def _declared_writes(self, skill_id: str) -> list[dict]:
        """This Skill's own `writes:` frontmatter -- which of its Actions
        write which sections of which Master Template. Malformed entries are
        skipped rather than crashing the whole map; a Skill that declares
        nothing simply grants nothing."""
        skill_md = skills_data.read_skill_md(skill_id) or ""
        match = _FRONTMATTER_RE.match(skill_md)
        if not match:
            return []
        try:
            parsed = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            return []
        declared = (parsed or {}).get("writes") if isinstance(parsed, dict) else None
        if not isinstance(declared, list):
            return []
        entries = []
        for entry in declared:
            if not isinstance(entry, dict):
                continue
            action = entry.get("action")
            template = entry.get("template")
            sections = entry.get("sections")
            if isinstance(action, str) and isinstance(template, str) and isinstance(sections, list):
                entries.append({
                    "action": action, "template": template,
                    "requires": entry.get("requires"),
                    "sections": [s for s in sections if isinstance(s, str)],
                })
        return entries

    def build_section_access_map(self) -> dict:
        """template -> section -> [action, ...], derived from what the
        DEPLOYED Skills declare.

        This replaces `allowed_callers` inside Template.json. That was a
        reverse edge: it made the vault's own structure depend on the
        capability layer, contradicting the dependency resolver's own "a
        Template has no further real dependencies of its own". An Entity
        Template is a vault structure; it should not know which Skills
        exist.

        Derived, never authored, which is what makes it correct by
        construction: it cannot name an Action that is not actually
        deployed, and it cannot go stale against a renamed script the way a
        hand-maintained list in Template.json silently did.

        Only Skills with at least one real deployment target contribute --
        a Skill sitting in the catalog undeployed grants nothing.
        """
        access: dict[str, dict[str, list[str]]] = {}
        for skill in self.get_all():
            if not skill.deployed_to:
                continue
            for entry in self._declared_writes(skill.id):
                template = access.setdefault(entry["template"], {})
                for section in entry["sections"]:
                    callers = template.setdefault(section, [])
                    if entry["action"] not in callers:
                        callers.append(entry["action"])
        for sections in access.values():
            for callers in sections.values():
                callers.sort()
        return access

    def validate_declared_writes(self, skill_id: str) -> list[str]:
        """Every reason this Skill's `writes:` cannot be honoured, empty if
        it can. Checks the intersection the model rests on: a Skill may
        write section S of Template T only if it DECLARES T.S and T marks S
        `machine_write`.

        This is what `allowed_callers` could never do. It was an
        unvalidated string inside Template.json, so renaming a script
        silently locked the writer out -- the section simply stopped being
        writable, with no error anywhere. Declared on the Skill and checked
        against the real Template, a mismatch is caught before deployment
        instead of at 3am inside a cron worker.
        """
        problems: list[str] = []
        for entry in self._declared_writes(skill_id):
            template = TemplateManager().get_by_id(entry["template"])
            if template is None:
                problems.append(
                    f"{entry['action']}: no Master Template {entry['template']!r} on this install"
                )
                continue
            required = entry.get("requires")
            if isinstance(required, int) and required != template.version:
                # EXACT match, not ">=". These are major CONTENT versions: a
                # bump means a section was removed or renamed, so an older
                # Skill is not merely behind, it is wrong. ">=" would let a
                # Skill written for v1 pass against a v2 that dropped the
                # very section it writes -- the failure this exists to catch.
                problems.append(
                    f"{entry['action']}: needs {entry['template']!r} v{required}, "
                    f"install has v{template.version}"
                )
                continue
            by_name = {section.name: section for section in template.sections}
            for section_name in entry["sections"]:
                section = by_name.get(section_name)
                if section is None:
                    problems.append(
                        f"{entry['action']}: template {entry['template']!r} has no section {section_name!r}"
                    )
                elif section.access != "machine_write":
                    problems.append(
                        f"{entry['action']}: section {section_name!r} of {entry['template']!r} "
                        f"is {section.access!r}, not machine_write"
                    )
        return problems

    def _frontmatter(self, skill_id: str) -> dict:
        """This Skill's own SKILL.md frontmatter, {} if absent or malformed."""
        match = _FRONTMATTER_RE.match(skills_data.read_skill_md(skill_id) or "")
        if not match:
            return {}
        try:
            parsed = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def check_deployment_drift(self) -> list[dict]:
        """For every Skill, for every profile it claims to be deployed to:
        is what is RUNNING still what we ship?

        Nothing could answer that before, and the cost was concrete. Six of
        our own Skills sat mis-filed under the catch-all `jarvis` Tool
        because Hermes had become the de-facto source of truth; the index
        engine ran `rglob` for weeks after the fix landed in a different
        copy; 228 stale copies of vault_manager.py ran across 41 profiles.
        Each of those is this same question, left unasked.

        Statuses, most to least serious:
          missing   -- deployed_to claims it, the profile does not have it
          stale     -- deployed version differs from the catalog's
          modified  -- same version, different content (edited in place --
                       worse than stale: the version claims it is current)
          current   -- byte-identical
        """
        client = get_client()
        # One filesystem listing per PROFILE, not per skill-profile pair:
        # this is O(skills x profiles) and each listing globs a real tree.
        deployed_by_profile: dict[str, dict] = {}

        def deployed_skills(profile_id: str) -> dict:
            if profile_id not in deployed_by_profile:
                deployed_by_profile[profile_id] = {
                    s.slug: s for s in client.skills.get_all(profile_id)
                }
            return deployed_by_profile[profile_id]

        report: list[dict] = []
        for skill in self.get_all():
            catalog_md = skills_data.read_skill_md(skill.id) or ""
            catalog_version = str(self._frontmatter(skill.id).get("version", ""))
            for profile_id in skill.deployed_to:
                # Match on SLUG, not "<category>/<slug>". Hermes keys a
                # deployed skill by the folder it landed in, and ours moved
                # when the catalog was regrouped by Tool (2026-09-06), so a
                # deployed copy still sits under its old category. The slug
                # is the stable identity on both sides.
                deployed = deployed_skills(profile_id).get(skill.id)
                deployed_md = (
                    client.skills.read(profile_id, deployed.id) if deployed is not None else None
                )
                if deployed is None or deployed_md is None:
                    status, deployed_version = "missing", None
                elif deployed_md == catalog_md:
                    status, deployed_version = "current", deployed.version
                elif deployed.version != catalog_version:
                    status, deployed_version = "stale", deployed.version
                else:
                    status, deployed_version = "modified", deployed.version
                report.append({
                    "skill_id": skill.id, "profile_id": profile_id, "status": status,
                    "catalog_version": catalog_version, "deployed_version": deployed_version,
                })
        return report

    def publish_section_access_map(self) -> dict:
        """Rebuilds and persists the derived write map. Called on every
        deploy/undeploy, not once: the map is a projection of which Skills
        are deployed, so it has to be recomputed whenever that changes --
        which is exactly what a hand-maintained allowed_callers list in
        Template.json could never do."""
        mapping = self.build_section_access_map()
        skills_data.write_section_access_map(mapping)
        return mapping

    def deploy(self, skill_id: str, profile_id: str) -> Skill | None:
        """Pushes this Skill's current real content to one more real
        Hermes profile.

        Refreshes the install's shared managers first (idempotent, one
        small copy) and does NOT bundle vault_manager.py into the Skill.
        A local copy would silently WIN over the shared one -- sys.path[0]
        is the script's own directory -- so bundling it is what let 228
        stale copies run across 41 profiles while canonical moved on.

        This requires PYTHONPATH to point at the shared directory, which
        `setup_wizard.sync_settings_to_hermes` writes into Hermes' .env
        and which takes effect on the next gateway restart.
        """
        skill = self.get_by_id(skill_id)
        if skill is None or profile_id in skill.deployed_to:
            return skill
        problems = self.validate_declared_writes(skill_id)
        if problems:
            raise SkillPreconditionError(
                f"{skill_id!r} cannot be deployed -- " + "; ".join(problems)
            )
        skill_md = skills_data.read_skill_md(skill_id) or ""
        scripts = skills_data.list_scripts(skill_id)
        skills_data.deploy_shared_managers(settings.hermes_home_path)
        get_client().skills.create(profile_id, skill.category, skill_id, skill_md, scripts)
        skill.deployed_to.append(profile_id)
        skill.updated_at = datetime.now(timezone.utc).isoformat()
        self._write_meta(skill)
        self.publish_section_access_map()
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
            self.publish_section_access_map()
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
