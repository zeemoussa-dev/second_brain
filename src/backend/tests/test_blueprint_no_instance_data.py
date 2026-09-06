"""A shipped Blueprint must never carry one machine's paths.

BUG-051: the librarian souls hard-coded the harvesting operator's absolute
vault path. install() copies a soul verbatim into each Hermes profile, so
every install got it, and the agents wrote into a vault that was not theirs.
It failed loudly on the reporting machine only because that path was not
writable -- on a host where a similarly-named one exists, the agent writes
real notes into the wrong vault and reports success.
"""
from pathlib import Path

import pytest

from app.business.core.blueprints.blueprint_manager import BlueprintManager, _ABSOLUTE_PATH
from app.config import settings
from app.data_access import blueprints as blueprints_data

_LIBRARY = Path(__file__).resolve().parents[1] / "app" / "business" / "core" / "blueprints" / "library"


@pytest.mark.parametrize("path", sorted(_LIBRARY.glob("*/agents/*.md")), ids=lambda p: p.name)
def test_no_shipped_blueprint_asset_carries_an_absolute_path(path: Path) -> None:
    """The check that would have caught this before it shipped."""
    assert not _ABSOLUTE_PATH.search(path.read_text(encoding="utf-8")), (
        f"{path.name} carries a literal absolute path -- use <OPERATOR_VAULT>"
    )


def test_the_placeholder_resolves_to_this_installs_own_vault() -> None:
    soul = blueprints_data.read_blueprint_asset("librarian", "agents/notes-manager.soul.md")

    assert "<OPERATOR_VAULT>" in soul, "the shipped soul must stay machine-neutral"
    resolved = BlueprintManager()._resolve_placeholders(soul)
    assert str(settings.vault_path) in resolved
    assert "<OPERATOR_VAULT>" not in resolved


def test_preflight_refuses_a_soul_carrying_a_literal_path(monkeypatch) -> None:
    """Belt and braces: even if such a soul is authored, install must refuse
    rather than write one machine's paths into another's agents."""
    monkeypatch.setattr(
        blueprints_data, "read_blueprint_asset",
        lambda bid, rel: "Vault path: " + "C:" + chr(92) + "Users" + chr(92) + "someone",
    )

    result = BlueprintManager().preflight("librarian")

    assert result["ok"] is False
    assert any("literal absolute path" in p for p in result["problems"])
