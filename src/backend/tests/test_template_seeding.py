"""Seeding the shipped Master Templates onto an install.

Before 2026-09-06 nothing shipped Entity Templates and nothing seeded
them, so a fresh install had no vault structure at all and every capture
Skill would have failed on a missing template.

Two properties matter and are easy to get wrong in opposite directions:
a fresh install must end up with the full set, and an install that has
already been running must never have an operator's own edits reverted by
a boot that quietly re-installs the shipped copy over them.
"""
import json
from pathlib import Path

import pytest

from app.business.core.templates.template_manager import TemplateManager
from app.data_access import templates as templates_data


@pytest.fixture()
def install(tmp_path, monkeypatch) -> Path:
    """An empty App Database Folder standing in for a fresh install."""
    root = tmp_path / "data" / "Templates"
    root.mkdir(parents=True)
    monkeypatch.setattr(templates_data, "templates_root", lambda: root)
    return root


def _written(root: Path, template_id: str) -> dict:
    return json.loads((root / template_id / "Template.json").read_text(encoding="utf-8"))


def test_a_fresh_install_gets_the_whole_shipped_set(install: Path) -> None:
    result = TemplateManager().seed_shipped_masters()

    assert result["kept"] == []
    assert set(result["seeded"]) == set(templates_data.list_shipped_master_ids())
    assert "thread" in result["seeded"]
    assert sorted(p.name for p in install.iterdir()) == sorted(result["seeded"])


def test_seeded_templates_parse_with_real_content(install: Path) -> None:
    """Seeding something the reader cannot understand would just move the
    empty-template bug onto fresh installs."""
    TemplateManager().seed_shipped_masters()

    thread = TemplateManager().get_by_id("thread")
    assert thread is not None
    assert thread.schema_version == 2
    assert [s.name for s in thread.sections][:2] == ["Summary", "Personal Notes"]


def test_an_operator_edit_is_never_overwritten(install: Path) -> None:
    """The property that matters most: this runs on EVERY boot. Overwriting
    would silently revert local changes on every restart."""
    edited = {"id": "thread", "schema_version": 2, "root": {"sections": [{"name": "My Own Section"}]}}
    templates_data.write_template_json("thread", edited)

    result = TemplateManager().seed_shipped_masters()

    assert "thread" in result["kept"]
    assert "thread" not in result["seeded"]
    assert _written(install, "thread") == edited


def test_seeding_is_idempotent(install: Path) -> None:
    first = TemplateManager().seed_shipped_masters()
    second = TemplateManager().seed_shipped_masters()

    assert second["seeded"] == []
    assert sorted(second["kept"]) == sorted(first["seeded"])


def test_a_partially_seeded_install_gets_only_what_it_lacks(install: Path) -> None:
    """The real upgrade case: an install predating a newly added template."""
    TemplateManager().seed_shipped_masters()
    (install / "thread" / "Template.json").unlink()
    (install / "thread").rmdir()

    result = TemplateManager().seed_shipped_masters()

    assert result["seeded"] == ["thread"]


def test_a_missing_shipped_directory_seeds_nothing_rather_than_raising(install, monkeypatch) -> None:
    """A checkout without the masters directory must degrade to a no-op, not
    take app startup down with it."""
    monkeypatch.setattr(templates_data, "list_shipped_master_ids", lambda: [])

    assert TemplateManager().seed_shipped_masters() == {"seeded": [], "kept": []}
