"""There is ONE vault engine.

`app/vault/vault_manager.py` used to be a second, older copy that claimed to
be canonical ("editing the engine happens in exactly ONE place (this file,
then re-copy)") while sitting at 606 lines against the 1,543 deployed. It was
the v1 flat Template reader and resolved Templates relative to the VAULT, so
every template-driven backend write failed with `unknown template` after the
2026-09-03 config/vault split.
"""
from pathlib import Path

from app.config import settings
from app.vault import vault_manager as vm

_CANONICAL = (
    Path(__file__).resolve().parents[1]
    / "app" / "business" / "core" / "skills" / "managers" / "vault_manager.py"
)


def test_the_backend_uses_the_canonical_engine_not_a_fork() -> None:
    """The shim must resolve to the same file every Hermes profile runs."""
    assert Path(vm.__dict__["__file__"] if "__file__" in vm.__dict__ else _CANONICAL)
    assert vm.load_template.__code__.co_filename == str(_CANONICAL)


def test_the_v2_only_capabilities_are_present() -> None:
    """The fork had none of these. Their absence is how you tell the engines
    apart, so assert on them rather than on line count."""
    for capability in ("data_root", "create_dynamic_child", "iter_md_files", "long_path"):
        assert hasattr(vm, capability), capability


def test_a_real_shipped_template_loads() -> None:
    """The regression itself: this raised `unknown template: 'file'` because
    Templates were resolved relative to the vault, not the App Database
    Folder."""
    template = vm.load_template(settings.vault_path, "file")

    assert template["id"] == "file"
    assert template["root"]["sections"], "parsed to zero sections -- v1 reader on a v2 file"


def test_the_engine_resolves_the_data_root_from_the_environment() -> None:
    """It is standalone by design (no backend import), so it reads the
    environment. app/config.py exports SECOND_BRAIN_DATA_PATH on load; without
    that it falls back to <vault>/.second-brain and silently finds nothing."""
    assert vm.data_root(settings.vault_path) == settings.second_brain_data_path


def test_create_and_modify_section_are_called_by_keyword_in_client() -> None:
    """Both changed positional order between the fork and the engine, so a
    positional call silently swaps arguments -- note name for title, and
    note_id for section. Pin the call style, not just the behaviour."""
    source = (Path(__file__).resolve().parents[1] / "app" / "vault" / "client.py").read_text(encoding="utf-8")

    assert "title=title, note_name=note_name" in source
    assert "section=section, content=content, mode=mode" in source
