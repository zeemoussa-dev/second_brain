"""RegistryLoader -- walks the real data/ tree (REQ-SB-80) into an
in-memory Registry, and reports staged progress the whole time so a
frontend BootScreen never has to guess what's happening.

Storage location: `<settings.second_brain_data_path>/data/` -- the same
app-database root every other persisted store already uses
(vault_writer.py's own state store), just organized as a real folder
tree instead of another flat JSON file. Independent of settings.vault_path
since the System settings page (2026-08-27) -- defaults to
`<vault>/.second-brain/` for a fresh install, relocatable from there.

Fail-loud (operator: "Fail Loud so I can fix or remove") -- the first
invalid file anywhere in the tree stops that boot attempt: `state`
flips to "failed" with the exact file + reason, and the previously
loaded Registry (if any) is left untouched rather than being replaced
by a half-built one.

Hot-reload (operator: "the Hot Reload is needed if we will productize
this, but again think consalidation and how can we reuse still") --
`boot_and_watch()` calls the SAME `boot()` used for cold start on every
detected change, never a second parsing/validation path. Detection is a
plain poll (max mtime across the tree) rather than a new file-watcher
dependency -- this codebase has no existing precedent for one, and a
2-second poll is more than fast enough for a personal, single-user app.
"""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from app.business import system_health
from app.config import settings
from app.data_access.registry.errors import RegistryLoadError
from app.data_access.registry.schemas import (
    Agent,
    AgentConfig,
    AgentVisual,
    ProviderConfig,
    Registry,
    SectionConfig,
    Skill,
    SkillConfig,
    SkillVisual,
    Tool,
    ToolConfig,
)

_STAGES = [
    "checking_hermes",
    "loading_sections",
    "loading_agents",
    "loading_skills",
    "loading_providers",
]
_POLL_SECONDS = 2.0

_registry: Registry | None = None
_status: dict = {
    "mode": "cold_boot",
    "state": "booting",  # "booting" | "ready" | "failed"
    "current_stage": None,
    "stages": [{"id": s, "status": "pending"} for s in _STAGES],
    "hermes_reachable": None,
    "error": None,
    "loaded_at": None,
}
_last_seen_fingerprint: str | None = None


def data_root() -> Path:
    return settings.second_brain_data_path / "data"


def get_registry() -> Registry | None:
    return _registry


def agent_data_dir(agent_id: str) -> Path | None:
    """The real on-disk folder for this agent's own data/ files
    (`Agent-config.json`/`Agent-visual.json`/`soul.md`), or None if it
    hasn't been migrated into the tree yet. Centralizes the
    Section-vs-Background placement lookup so a business-layer store that
    wants to dual-write one of an agent's own files (e.g.
    agent_visual_registry.py's icon/color) doesn't have to re-derive it."""
    agent = get_registry().agents.get(agent_id) if get_registry() else None
    if agent is None:
        return None
    if agent.section_id is None:
        return data_root() / "Background" / "Agents" / agent_id
    return data_root() / "Sections" / agent.section_id / "Agents" / agent_id


def get_boot_status() -> dict:
    return json.loads(json.dumps(_status))  # cheap deep copy, status is JSON-safe


def _set_stage(stage_id: str, status: str) -> None:
    _status["current_stage"] = stage_id if status == "in_progress" else _status["current_stage"]
    for entry in _status["stages"]:
        if entry["id"] == stage_id:
            entry["status"] = status


def _reset_status(mode: str) -> None:
    _status["mode"] = mode
    _status["state"] = "booting"
    _status["current_stage"] = None
    _status["stages"] = [{"id": s, "status": "pending"} for s in _STAGES]
    _status["error"] = None


def _require_json(path: Path) -> dict:
    if not path.is_file():
        raise RegistryLoadError(path, "file not found")
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RegistryLoadError(path, f"invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise RegistryLoadError(path, "expected a JSON object")
    return parsed


def _require_field(obj: dict, key: str, path: Path):
    if key not in obj or obj[key] in (None, ""):
        raise RegistryLoadError(path, f"missing required field '{key}'")
    return obj[key]


def _load_sections() -> dict[str, SectionConfig]:
    sections: dict[str, SectionConfig] = {}
    sections_root = data_root() / "Sections"
    if not sections_root.is_dir():
        return sections
    for section_dir in sorted(p for p in sections_root.iterdir() if p.is_dir()):
        section_json = section_dir / "Section.json"
        raw = _require_json(section_json)
        section_id = str(_require_field(raw, "id", section_json))
        sections[section_id] = SectionConfig(
            id=section_id,
            name=str(_require_field(raw, "name", section_json)),
            icon=raw.get("icon"),
            color=raw.get("color"),
            subtitle=raw.get("subtitle"),
            description=raw.get("description"),
        )
    return sections


def _load_one_agent(agent_dir: Path, section_id: str | None) -> Agent:
    config_path = agent_dir / "Agent-config.json"
    visual_path = agent_dir / "Agent-visual.json"
    soul_path = agent_dir / "soul.md"

    config_raw = _require_json(config_path)
    agent_id = str(_require_field(config_raw, "id", config_path))
    agent_type = str(_require_field(config_raw, "type", config_path))
    if agent_type not in ("worker", "producer", "expert"):
        raise RegistryLoadError(config_path, f"'type' must be worker/producer/expert, got '{agent_type}'")

    visual_raw = _require_json(visual_path)

    if not soul_path.is_file():
        raise RegistryLoadError(soul_path, "file not found")
    soul = soul_path.read_text(encoding="utf-8").strip()
    if not soul:
        raise RegistryLoadError(soul_path, "soul.md is empty")

    return Agent(
        config=AgentConfig(
            id=agent_id,
            name=str(_require_field(config_raw, "name", config_path)),
            type=agent_type,
            is_background_agent=bool(config_raw.get("is_background_agent", False)),
            depends_on=list(config_raw.get("depends_on", [])),
            provider_id=config_raw.get("provider_id"),
            skill_ids=list(config_raw.get("skill_ids", [])),
        ),
        visual=AgentVisual(icon=visual_raw.get("icon"), color=visual_raw.get("color")),
        soul=soul,
        section_id=section_id,
    )


def _load_agents(sections: dict[str, SectionConfig]) -> dict[str, Agent]:
    agents: dict[str, Agent] = {}
    sections_root = data_root() / "Sections"
    if sections_root.is_dir():
        for section_dir in sorted(p for p in sections_root.iterdir() if p.is_dir()):
            section_json = section_dir / "Section.json"
            section_id = str(_require_json(section_json)["id"])
            agents_root = section_dir / "Agents"
            if not agents_root.is_dir():
                continue
            for agent_dir in sorted(p for p in agents_root.iterdir() if p.is_dir()):
                agent = _load_one_agent(agent_dir, section_id)
                agents[agent.config.id] = agent

    background_root = data_root() / "Background" / "Agents"
    if background_root.is_dir():
        for agent_dir in sorted(p for p in background_root.iterdir() if p.is_dir()):
            agent = _load_one_agent(agent_dir, None)
            agents[agent.config.id] = agent
    return agents


def _load_tools() -> dict[str, Tool]:
    tools: dict[str, Tool] = {}
    tools_root = data_root() / "Tools"
    if not tools_root.is_dir():
        return tools
    for tool_dir in sorted(p for p in tools_root.iterdir() if p.is_dir()):
        tool_json = tool_dir / "Tool.json"
        raw = _require_json(tool_json)
        tool_id = str(_require_field(raw, "id", tool_json))
        tool = Tool(
            config=ToolConfig(
                id=tool_id,
                name=str(_require_field(raw, "name", tool_json)),
                description=str(raw.get("description") or ""),
                icon=raw.get("icon"),
            )
        )
        skills_root = tool_dir / "Skills"
        if skills_root.is_dir():
            for skill_dir in sorted(p for p in skills_root.iterdir() if p.is_dir()):
                skill_json = skill_dir / "Skill.json"
                skill_visual_json = skill_dir / "Skill-visual.json"
                skill_raw = _require_json(skill_json)
                skill_visual_raw = _require_json(skill_visual_json)
                skill_id = str(_require_field(skill_raw, "id", skill_json))
                tool.skills[skill_id] = Skill(
                    config=SkillConfig(
                        id=skill_id,
                        name=str(_require_field(skill_raw, "name", skill_json)),
                        description=str(skill_raw.get("description") or ""),
                        category=str(skill_raw.get("category") or ""),
                        mutates=bool(skill_raw.get("mutates", True)),
                    ),
                    visual=SkillVisual(icon=skill_visual_raw.get("icon")),
                    tool_id=tool_id,
                )
        tools[tool_id] = tool
    return tools


def _load_providers() -> dict[str, ProviderConfig]:
    providers: dict[str, ProviderConfig] = {}
    providers_root = data_root() / "Providers"
    if not providers_root.is_dir():
        return providers
    for provider_dir in sorted(p for p in providers_root.iterdir() if p.is_dir()):
        provider_json = provider_dir / "Provider.json"
        raw = _require_json(provider_json)
        provider_id = str(_require_field(raw, "id", provider_json))
        providers[provider_id] = ProviderConfig(
            id=provider_id,
            name=str(_require_field(raw, "name", provider_json)),
            endpoint=str(raw.get("endpoint") or ""),
            credential=str(raw.get("credential") or ""),
            model=str(raw.get("model") or ""),
        )
    return providers


def _tree_fingerprint() -> str:
    """Cheap change-detection for the poll-based hot-reload loop -- the
    sorted (relative path, mtime) list of every file under data/. Good
    enough for a single-user local app; not a content hash, so a save
    that rewrites identical bytes still triggers a harmless reload."""
    root = data_root()
    if not root.is_dir():
        return "absent"
    entries = sorted(
        (str(p.relative_to(root)), p.stat().st_mtime) for p in root.rglob("*") if p.is_file()
    )
    return json.dumps(entries)


async def boot(mode: str = "cold_boot") -> None:
    """Runs every stage in order, updating `_status` as it goes. Never
    raises out to the caller -- a fire-and-forget asyncio.create_task
    (main.py's own established pattern for startup work, e.g.
    vault_indexing.rebuild_index) would otherwise just log an unretrieved
    exception and leave `_status` stuck mid-boot forever."""
    global _registry, _last_seen_fingerprint
    _reset_status(mode)
    try:
        _set_stage("checking_hermes", "in_progress")
        reachable = await asyncio.to_thread(system_health.mcp_mount_reachable)
        _status["hermes_reachable"] = reachable
        _set_stage("checking_hermes", "done")

        _set_stage("loading_sections", "in_progress")
        sections = await asyncio.to_thread(_load_sections)
        _set_stage("loading_sections", "done")

        _set_stage("loading_agents", "in_progress")
        agents = await asyncio.to_thread(_load_agents, sections)
        _set_stage("loading_agents", "done")

        _set_stage("loading_skills", "in_progress")
        tools = await asyncio.to_thread(_load_tools)
        _set_stage("loading_skills", "done")

        _set_stage("loading_providers", "in_progress")
        providers = await asyncio.to_thread(_load_providers)
        _set_stage("loading_providers", "done")

        _registry = Registry(sections=sections, agents=agents, tools=tools, providers=providers)
        _status["state"] = "ready"
        _status["loaded_at"] = time.time()
        _last_seen_fingerprint = _tree_fingerprint()
    except RegistryLoadError as exc:
        current = _status["current_stage"]
        if current is not None:
            _set_stage(current, "failed")
        _status["state"] = "failed"
        _status["error"] = {"file": str(exc.file), "message": exc.message}


async def watch_and_reload() -> None:
    """Runs forever -- reuses `boot()` unchanged for every reload, per the
    operator's own "think consalidation, how can we reuse" instruction.
    Only starts polling after the initial cold boot (whatever its
    outcome) so this never overlaps with the first `boot()` call."""
    global _last_seen_fingerprint
    while True:
        await asyncio.sleep(_POLL_SECONDS)
        fingerprint = await asyncio.to_thread(_tree_fingerprint)
        if fingerprint != _last_seen_fingerprint:
            await boot(mode="hot_reload")


async def boot_and_watch() -> None:
    await boot(mode="cold_boot")
    await watch_and_reload()
