"""Three reports about state the app reads back from Hermes or writes into it.
"""
from pathlib import Path

from app.business.core.blueprints.blueprint_manager import BlueprintManager
from app.hermes.profiles import _is_real_profile

NL = chr(10)


def test_a_tombstoned_profile_is_not_an_agent(tmp_path: Path) -> None:
    """BUG-053: `hermes profile delete` TOMBSTONES rather than erases -- it
    moves the directory to `profiles/.deleted/<name>`. Enumerating every
    directory made `.deleted` itself an Agent, id and name both `.deleted`,
    after the first deletion an install ever performs."""
    (tmp_path / ".deleted").mkdir()
    (tmp_path / "notes-manager").mkdir()
    (tmp_path / "notes.md").write_text("x", encoding="utf-8")

    real = sorted(p.name for p in tmp_path.iterdir() if _is_real_profile(p))

    assert real == ["notes-manager"]


def _soul(tmp_path: Path, text: str, monkeypatch):
    (tmp_path / "SOUL.md").write_text(text, encoding="utf-8")

    class _S:
        hermes_home_path = tmp_path
    monkeypatch.setattr("app.config.settings", _S)
    return tmp_path / "SOUL.md"


def test_the_peer_heading_migrates_above_blocks_written_before_the_fix(tmp_path, monkeypatch) -> None:
    """BUG-055: appending the heading at the end was right for a fresh SOUL
    and wrong for one already wired by the pre-fix code -- which is every
    install the BUG-052 fix was written for. It produced a heading announcing
    peers with nothing under it, and the bullets still orphaned above."""
    path = _soul(tmp_path, (
        "Tone paragraph." + NL * 2
        + "<!-- BEGIN PRIMARY ROUTING: notes-manager -->" + NL
        + "- notes bullet" + NL
        + "<!-- END PRIMARY ROUTING: notes-manager -->" + NL
    ), monkeypatch)

    assert BlueprintManager()._ensure_peer_section() is True

    text = path.read_text(encoding="utf-8")
    assert text.index("## Your peer agents") < text.index("BEGIN PRIMARY ROUTING")
    assert "- notes bullet" in text, "the existing bullet must survive the migration"


def test_a_fresh_soul_gets_the_heading_appended(tmp_path, monkeypatch) -> None:
    path = _soul(tmp_path, "Tone paragraph." + NL, monkeypatch)

    assert BlueprintManager()._ensure_peer_section() is True
    assert "## Your peer agents" in path.read_text(encoding="utf-8")


def test_ensuring_the_section_twice_changes_nothing(tmp_path, monkeypatch) -> None:
    """It runs on every install; a second pass must not stack headings."""
    path = _soul(tmp_path, "Tone paragraph." + NL, monkeypatch)
    BlueprintManager()._ensure_peer_section()
    once = path.read_text(encoding="utf-8")

    assert BlueprintManager()._ensure_peer_section() is False
    assert path.read_text(encoding="utf-8") == once
