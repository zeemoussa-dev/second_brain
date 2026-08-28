"""Raw write-side I/O for the Registry tree (ADR-003's own api ->
business -> data_access layering) -- sibling to loader.py (which owns
the read side: booting, hot-reload polling, agent_data_dir() lookup for
an agent already known to the loaded Registry). Nothing here interprets
what a Section/Agent record MEANS -- that's SectionManager's/
AgentManager's own job; this module only knows where files for a given
id live on disk and how to write/delete them.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from app.data_access.registry import loader as registry_loader


def agent_dir(agent_id: str, *, section_id: str, is_background_agent: bool) -> Path:
    """The real store-layout convention for where an agent's own
    Agent.json/soul.md live -- Sections/<id>/Agents/<agent>/ normally,
    Background/Agents/<agent>/ for a background agent. A pure formula
    (the target location for a write), distinct from loader.py's own
    agent_data_dir() (a lookup of where an agent ALREADY-loaded into the
    Registry currently lives)."""
    root = registry_loader.data_root()
    if is_background_agent:
        return root / "Background" / "Agents" / agent_id
    return root / "Sections" / section_id / "Agents" / agent_id


def write_agent_files(directory: Path, *, config: dict, soul_text: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "Agent.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    (directory / "soul.md").write_text(soul_text, encoding="utf-8")


def write_section_json(section_id: str, data: dict) -> None:
    path = registry_loader.data_root() / "Sections" / section_id / "Section.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def delete_dir(path: Path | None) -> None:
    """Tolerant of None (nothing to delete) and a non-existent/already-
    gone directory -- the same `is_dir()`-guarded, ignore_errors=True
    shape every real caller already relied on."""
    if path is not None and path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
