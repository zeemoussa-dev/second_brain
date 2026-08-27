"""One-off migration (REQ-SB-80) -- seeds the real data/ tree
(`<vault>/.second-brain/data/`) from every source that today holds this
information: hermes_definitions.py (reads Hermes' real profile files
directly), agent_visual_registry.py, section_registry.py,
provider_registry.py, and the handful of real, product-relevant Skill
SKILL.md files under Hermes' install (NOT its whole generic bundled
catalog -- see this script's own SKILL_SOURCES below, confirmed live
against this machine's real install, 2026-08-25).

Run once, by hand, from src/backend:
    .venv\\Scripts\\python.exe scripts\\migrate_to_data_layer.py

Idempotent -- safe to re-run; each file is fully overwritten from the
current live source data, never merged with a previous run's output.

**2026-08-25 update:** agents_map_adapter.py's own Type/Section/
depends_on/is_background_agent/display_name helpers are now themselves
Registry-backed (they read the very data/ tree this script writes), not
the hardcoded dicts they used to be. Calling them here is still correct
and still idempotent for an agent ALREADY migrated (reads back its own
real value, rewrites the same thing) -- but for a genuinely NEW Hermes
agent never migrated before, they now return the same bare defaults an
unmigrated agent falls through to at read time anyway (worker / Data
Gatherer / no deps / not background / raw Hermes name), same as if this
script were never run for it. This script is no longer a "regenerate
correct placement from hardcoded ground truth" tool -- that ground truth
now lives in the data/ tree itself, edited directly (or, later, through
a real UI) rather than regenerated.
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.business import agent_visual_registry, provider_registry, section_registry
from app.business.hermes import agents_map_adapter as adapter
from app.config import settings
from app.data_access import hermes_definitions
from app.data_access.registry import loader as registry_loader
from app.data_access.system.tools import registry as tools_registry

DATA_ROOT = settings.vault_path / ".second-brain" / "data"

# Only the real, deliberate, product-relevant Skills this app actually
# built and uses -- NOT Hermes' generic bundled catalog every cloned
# profile carries by default (apple/*, creative/*, github/*, mlops/*,
# productivity/* etc. -- confirmed live, 2026-08-25: present under every
# single profile, referenced by none of their real SOUL.md prompts).
# (category_folder, slug, tool_id) -- category/slug is the real path
# under Hermes' skills/ (profile-level or shared), tool_id is which of
# our 4 real Tools it belongs under (REQ-SB-80's locked decision).
SKILL_SOURCES = [
    ("knowledge-base", "azure-kb-writer", "vault"),
    ("knowledge-base", "compass-kb-writer", "vault"),
    ("librarian", "person-lookup", "vault"),
    ("librarian", "research-kb-writer", "vault"),
    ("notes-capture", "capture-notes", "vault"),
    ("notes-capture", "capture-files", "vault"),
    ("company-review", "track-opportunities", "vault"),
    ("company-review", "summarize-and-tag-files", "vault"),
    ("company-review", "summarize-and-tag-threads", "vault"),
    ("pricing", "azure-cost-calculator", "vault"),
    ("sales", "macc-forecast-generator", "vault"),
]

# Per-agent distinctive skill_ids -- only the deliberate add-on each real
# agent has beyond the generic bundled catalog (found by direct
# inspection of each profile's skills/ dir, 2026-08-25). An agent absent
# here has no distinctive Skill of its own yet.
AGENT_SKILL_IDS: dict[str, list[str]] = {
    "azure-calculator": ["azure-cost-calculator"],
    "opp-manager": ["track-opportunities"],
    "notes-manager": ["capture-notes"],
    "files-manager": ["capture-files", "summarize-and-tag-files"],
    "research-agent": ["research-kb-writer"],
    "meeting-prep-agent": ["person-lookup"],
    "macc-expert": ["macc-forecast-generator"],
    "azure-expert": ["azure-kb-writer", "summarize-and-tag-threads"],
    "compass-expert": ["compass-kb-writer"],
}

_FRONTMATTER_BLOCK = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _skill_md_path(category: str, slug: str) -> Path | None:
    shared = settings.hermes_home_path / "skills" / category / slug / "SKILL.md"
    if shared.is_file():
        return shared
    profiles_root = settings.hermes_home_path / "profiles"
    if profiles_root.is_dir():
        for profile_dir in profiles_root.iterdir():
            candidate = profile_dir / "skills" / category / slug / "SKILL.md"
            if candidate.is_file():
                return candidate
    return None


def _read_frontmatter(path: Path) -> dict:
    import yaml
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_BLOCK.match(text)
    if not match:
        return {}
    parsed = yaml.safe_load(match.group(1))
    return parsed if isinstance(parsed, dict) else {}


def migrate_sections() -> None:
    count = 0
    for section in section_registry.list_sections():
        _write_json(
            DATA_ROOT / "Sections" / section["id"] / "Section.json",
            {
                "id": section["id"],
                "name": section["name"],
                "icon": section["icon"],
                "color": section["color"],
                "subtitle": section["subtitle"],
                "description": section["description"],
            },
        )
        count += 1
    print(f"Sections: {count}")


def migrate_agents() -> None:
    count = 0
    for hermes_agent in hermes_definitions.list_agents():
        agent_id = hermes_agent.id
        is_background = adapter._is_background_agent(agent_id)
        agent_config = {
            "id": agent_id,
            "name": adapter._agent_display_name(agent_id, hermes_agent.name),
            "type": adapter._agent_type(agent_id),
            "is_background_agent": is_background,
            "depends_on": adapter._agent_depends_on(agent_id),
            "provider_id": (provider_registry.get_agent_provider(agent_id) or {}).get("id"),
            "skill_ids": AGENT_SKILL_IDS.get(agent_id, []),
        }
        icon, color = adapter._visual(agent_id, hermes_agent.icon)
        agent_visual = {"icon": icon, "color": color}

        profile_dir = (
            settings.hermes_home_path
            if agent_id == "default"
            else settings.hermes_home_path / "profiles" / agent_id
        )
        soul_path = profile_dir / "SOUL.md"
        soul_text = soul_path.read_text(encoding="utf-8") if soul_path.is_file() else (
            hermes_agent.description or f"# {agent_config['name']}\n\n(no real SOUL.md found on this machine)\n"
        )

        if is_background:
            agent_root = DATA_ROOT / "Background" / "Agents" / agent_id
        else:
            section_id = adapter._agent_section_id(agent_id)
            agent_root = DATA_ROOT / "Sections" / section_id / "Agents" / agent_id

        _write_json(agent_root / "Agent-config.json", agent_config)
        _write_json(agent_root / "Agent-visual.json", agent_visual)
        _write_text(agent_root / "soul.md", soul_text)
        count += 1
    print(f"Agents: {count}")


def migrate_tools_and_skills() -> None:
    tool_defs = [
        {"id": "outlook", "name": "Outlook", "description": "Real Outlook email capture, over local desktop Outlook via COM automation.", "icon": "mail"},
        {"id": "vault", "name": "Vault", "description": "Skills that write directly into the Obsidian vault -- the mechanical, deterministic KB-write paths every Expert/Producer agent calls once it has real content worth keeping.", "icon": "folder_open"},
        {"id": "web", "name": "Web", "description": "Real, live web research, via the invoking agent's own linked Provider's server-side web-search capability.", "icon": "public"},
        {"id": "compass", "name": "Compass", "description": "Compass-specific capabilities. No dedicated Skill yet -- reserved for when one exists.", "icon": "explore"},
    ]
    for tool in tool_defs:
        _write_json(DATA_ROOT / "Tools" / tool["id"] / "Tool.json", tool)

    # Outlook's own real Skill: gather_emails, sourced from the already-real
    # data_access/system/tools/registry.json (a genuine Second-Brain-native
    # Tool/Action, not a Hermes-mirrored SKILL.md).
    for tool in tools_registry.load_tools_registry():
        if tool.id != "outlook":
            continue
        for category in tool.categories:
            for action in category.actions:
                _write_json(
                    DATA_ROOT / "Tools" / "outlook" / "Skills" / action.id / "Skill.json",
                    {"id": action.id, "name": action.name, "description": action.description, "category": category.id},
                )
                _write_json(
                    DATA_ROOT / "Tools" / "outlook" / "Skills" / action.id / "Skill-visual.json",
                    {"icon": action.icon},
                )

    skill_count = 1  # gather_emails, written above
    for category, slug, tool_id in SKILL_SOURCES:
        skill_md = _skill_md_path(category, slug)
        if skill_md is None:
            print(f"  SKIP {category}/{slug} -- SKILL.md not found on this machine")
            continue
        frontmatter = _read_frontmatter(skill_md)
        _write_json(
            DATA_ROOT / "Tools" / tool_id / "Skills" / slug / "Skill.json",
            {
                "id": slug,
                "name": str(frontmatter.get("name") or slug),
                "description": str(frontmatter.get("description") or ""),
                "category": category,
            },
        )
        _write_json(
            DATA_ROOT / "Tools" / tool_id / "Skills" / slug / "Skill-visual.json",
            {"icon": "bolt"},
        )
        skill_count += 1

    # web-search: a real, Second-Brain-native Skill (business/skill_tools.py),
    # not a Hermes-mirrored SKILL.md -- description copied verbatim from its
    # own real registration text there.
    _write_json(
        DATA_ROOT / "Tools" / "web" / "Skills" / "web-search" / "Skill.json",
        {
            "id": "web-search",
            "name": "Web Search",
            "description": (
                "Given a research subject or query, gather real, current information "
                "from the web -- using the invoking agent's own linked Provider's real "
                "web-search capability (Anthropic Claude's own server-side web-search "
                "tool, today)."
            ),
            "category": "second-brain-native",
            # Read-only (skill_tools.py's own real "mutates": False) --
            # the one Skill in this catalog that doesn't write anything,
            # so the only one that should never show up as schedulable.
            "mutates": False,
        },
    )
    _write_json(DATA_ROOT / "Tools" / "web" / "Skills" / "web-search" / "Skill-visual.json", {"icon": "public"})
    skill_count += 1

    print(f"Tools: {len(tool_defs)}, Skills: {skill_count}")


def migrate_providers() -> None:
    count = 0
    for provider in provider_registry.list_providers():
        full = provider_registry.get_provider(provider["id"])
        _write_json(
            DATA_ROOT / "Providers" / provider["id"] / "Provider.json",
            {
                "id": full["id"],
                "name": full["name"],
                "endpoint": full["endpoint"],
                "credential": full["credential"],
                "model": full["model"],
            },
        )
        count += 1
    print(f"Providers: {count}")


if __name__ == "__main__":
    print(f"Migrating into {DATA_ROOT}")
    # agents_map_adapter's Type/Section/depends_on/is_background_agent/
    # display_name helpers now read the RegistryLoader's in-memory
    # Registry (2026-08-25) -- which only exists after boot() has run in
    # THIS process. Without this, every one of those helpers would see an
    # empty Registry and fall through to bare defaults, silently
    # overwriting every already-correct placement on disk with "worker /
    # Data Gatherer / no deps / not background" on a re-run. Booting here
    # first makes this script genuinely idempotent, matching its own
    # module docstring above.
    asyncio.run(registry_loader.boot())
    boot_status = registry_loader.get_boot_status()
    if boot_status["state"] == "failed":
        # Refuse to proceed -- migrate_agents() below would otherwise see
        # an empty Registry and overwrite every already-correct real
        # placement on disk with bare defaults (see the comment above).
        raise SystemExit(f"RegistryLoader boot failed, aborting migration: {boot_status['error']}")
    migrate_sections()
    migrate_agents()
    migrate_tools_and_skills()
    migrate_providers()
    print("Done.")
