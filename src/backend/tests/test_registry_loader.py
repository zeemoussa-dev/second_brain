"""RegistryLoader tests (REQ-SB-80) -- this session built and hand-
verified (curl/browser) a real fail-loud validator, hot-reload, and
Section/Background agent placement resolver with zero automated
regression coverage. Isolated from the real vault via a temp directory
(`_isolated_vault` monkeypatches `settings.second_brain_data_path` --
`data_root()`'s real source since the System settings page decoupled it
from `settings.vault_path`) -- never writes into the operator's real
`.second-brain/data/`. `loader._hermes_reachable` is stubbed too, so
these tests never depend on (or make a real network call to) a live
Hermes gateway.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import pytest

from app.data_access.registry import loader as registry_loader


@pytest.fixture(autouse=True)
def _isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setattr(registry_loader.settings, "vault_path", tmp_path)
    monkeypatch.setattr(registry_loader.settings, "second_brain_data_path", tmp_path / ".second-brain")
    monkeypatch.setattr(registry_loader, "_hermes_reachable", lambda: True)
    # loader.py keeps process-wide module state (_registry/_status/
    # _last_seen_fingerprint), not request-scoped -- reset it so one
    # test's boot outcome can never leak into the next.
    registry_loader._registry = None
    registry_loader._last_seen_fingerprint = None
    registry_loader._status = {
        "mode": "cold_boot", "state": "booting", "current_stage": None,
        "stages": [{"id": s, "status": "pending"} for s in registry_loader._STAGES],
        "hermes_reachable": None, "error": None, "loaded_at": None,
    }
    return tmp_path


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _seed_minimal_valid_tree(vault_root: Path) -> Path:
    data = vault_root / ".second-brain" / "data"
    _write_json(data / "Sections" / "tech" / "Section.json", {"id": "tech", "name": "Technology"})

    section_agent = data / "Sections" / "tech" / "Agents" / "azure-expert"
    _write_json(section_agent / "Agent.json", {
        "id": "azure-expert", "name": "Azure Expert", "type": "expert", "icon": "cloud", "color": None,
    })
    (section_agent / "soul.md").write_text("You are Azure Expert.", encoding="utf-8")

    background_agent = data / "Background" / "Agents" / "default"
    _write_json(background_agent / "Agent.json", {
        "id": "default", "name": "Primary", "type": "worker", "is_background_agent": True,
        "icon": "hub", "color": None,
    })
    (background_agent / "soul.md").write_text("You are Primary.", encoding="utf-8")

    tool_dir = data / "Tools" / "vault"
    _write_json(tool_dir / "Tool.json", {"id": "vault", "name": "Vault"})
    skill_dir = tool_dir / "Skills" / "capture-notes"
    _write_json(skill_dir / "Skill.json", {"id": "capture-notes", "name": "capture-notes", "category": "notes-capture"})
    _write_json(skill_dir / "Skill-visual.json", {"icon": "bolt"})

    _write_json(
        data / "Providers" / "compass" / "Provider.json",
        {"id": "compass", "name": "Compass", "endpoint": "https://x", "credential": "y", "model": "gpt"},
    )
    return data


def test_boot_loads_valid_tree_successfully(_isolated_vault):
    _seed_minimal_valid_tree(_isolated_vault)

    asyncio.run(registry_loader.boot())

    status = registry_loader.get_boot_status()
    assert status["state"] == "ready"
    assert status["error"] is None
    assert all(stage["status"] == "done" for stage in status["stages"])

    registry = registry_loader.get_registry()
    assert set(registry.sections) == {"tech"}
    assert set(registry.agents) == {"azure-expert", "default"}
    assert registry.agents["azure-expert"].section_id == "tech"
    assert registry.agents["default"].section_id is None
    assert registry.agents["default"].config.is_background_agent is True
    assert registry.tools["vault"].skills["capture-notes"].config.mutates is True
    assert registry.providers["compass"].model == "gpt"


def test_boot_succeeds_on_completely_empty_tree(_isolated_vault):
    asyncio.run(registry_loader.boot())

    status = registry_loader.get_boot_status()
    assert status["state"] == "ready"
    registry = registry_loader.get_registry()
    assert registry.sections == {}
    assert registry.agents == {}


def test_boot_fails_loud_on_missing_required_field(_isolated_vault):
    data = _seed_minimal_valid_tree(_isolated_vault)
    agent_config = data / "Sections" / "tech" / "Agents" / "azure-expert" / "Agent.json"
    _write_json(agent_config, {"id": "azure-expert", "type": "expert"})  # no "name"

    asyncio.run(registry_loader.boot())

    status = registry_loader.get_boot_status()
    assert status["state"] == "failed"
    assert status["error"]["file"] == str(agent_config)
    assert "name" in status["error"]["message"]
    # A failed boot never produces a Registry at all on a cold/empty start.
    assert registry_loader.get_registry() is None


def test_boot_fails_loud_on_invalid_agent_type(_isolated_vault):
    data = _seed_minimal_valid_tree(_isolated_vault)
    agent_config = data / "Sections" / "tech" / "Agents" / "azure-expert" / "Agent.json"
    _write_json(agent_config, {"id": "azure-expert", "name": "Azure Expert", "type": "bogus-type"})

    asyncio.run(registry_loader.boot())

    status = registry_loader.get_boot_status()
    assert status["state"] == "failed"
    assert "bogus-type" in status["error"]["message"]


def test_boot_fails_loud_on_missing_soul_md(_isolated_vault):
    data = _seed_minimal_valid_tree(_isolated_vault)
    (data / "Sections" / "tech" / "Agents" / "azure-expert" / "soul.md").unlink()

    asyncio.run(registry_loader.boot())

    status = registry_loader.get_boot_status()
    assert status["state"] == "failed"
    assert status["error"]["file"].endswith("soul.md")


def test_failed_boot_does_not_replace_previous_good_registry(_isolated_vault):
    data = _seed_minimal_valid_tree(_isolated_vault)
    asyncio.run(registry_loader.boot())
    assert registry_loader.get_boot_status()["state"] == "ready"
    good_registry = registry_loader.get_registry()

    agent_config = data / "Sections" / "tech" / "Agents" / "azure-expert" / "Agent.json"
    _write_json(agent_config, {"id": "azure-expert", "type": "expert"})  # break it
    asyncio.run(registry_loader.boot(mode="hot_reload"))

    assert registry_loader.get_boot_status()["state"] == "failed"
    # The stale-but-good Registry is left exactly as it was -- a broken
    # edit must never blank out an already-working app (operator: "Fail
    # Loud so I can fix or remove", never "take away what was working").
    assert registry_loader.get_registry() is good_registry


def test_agent_data_dir_resolves_section_background_and_unmigrated(_isolated_vault):
    _seed_minimal_valid_tree(_isolated_vault)
    asyncio.run(registry_loader.boot())

    assert registry_loader.agent_data_dir("azure-expert") == registry_loader.data_root() / "Sections" / "tech" / "Agents" / "azure-expert"
    assert registry_loader.agent_data_dir("default") == registry_loader.data_root() / "Background" / "Agents" / "default"
    assert registry_loader.agent_data_dir("never-migrated") is None


def test_tree_fingerprint_changes_when_a_file_is_edited(_isolated_vault):
    data = _seed_minimal_valid_tree(_isolated_vault)
    before = registry_loader._tree_fingerprint()

    agent_config = data / "Sections" / "tech" / "Agents" / "azure-expert" / "Agent.json"
    new_mtime = agent_config.stat().st_mtime + 5  # force a real mtime delta, not timing-dependent
    os.utime(agent_config, (new_mtime, new_mtime))

    after = registry_loader._tree_fingerprint()
    assert before != after
