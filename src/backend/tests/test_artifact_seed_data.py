"""Seed data files in artifact export/import (Entities plan Phase 2).

Export and import no longer hardcode `Settings/Entities.md`: plugins register
their seed files, and the framework lists Entities.md only until the Entities
plugin does. An import never empties an existing seed file (`BUG-067`).
"""
import pytest

from app.business.core.plugins import plugin_manager as plugin_manager_module
from app.business.logic import artifact_export, artifact_import, artifact_seed_data
from app.config import settings


@pytest.fixture()
def data_path(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path)
    monkeypatch.setattr(plugin_manager_module, "_plugin_seed_data_files", [])
    return tmp_path


def registered(monkeypatch, *files):
    monkeypatch.setattr(plugin_manager_module, "_plugin_seed_data_files", list(files))


def deployed_skills_mention(monkeypatch, *names):
    monkeypatch.setattr(artifact_import, "_skill_content_references_needle",
                        lambda payload, skill_id, needle: needle in names)


def test_the_framework_still_lists_entities_until_the_plugin_registers_it(data_path):
    assert artifact_seed_data.seed_data_files() == {"Settings/Entities.md": "Entities.md"}


def test_plugin_registered_files_are_added_without_duplicates(data_path, monkeypatch):
    registered(monkeypatch, "Settings/Clients.md", "Settings/Entities.md")

    assert artifact_seed_data.seed_data_files() == {
        "Settings/Entities.md": "Entities.md", "Settings/Clients.md": "Clients.md",
    }


def test_import_creates_a_missing_seed_file_empty_when_its_skill_is_deployed(data_path, monkeypatch):
    deployed_skills_mention(monkeypatch, "Entities.md")

    artifact_import._write_seed_data({"seed_data/Settings/Entities.md": b"not empty"}, {"create-companies"})

    assert (data_path / "Settings" / "Entities.md").read_text(encoding="utf-8") == ""


def test_import_never_empties_an_existing_seed_file(data_path, monkeypatch):
    store = data_path / "Settings" / "Entities.md"
    store.parent.mkdir(parents=True)
    store.write_text("### Adnoc\n", encoding="utf-8")
    deployed_skills_mention(monkeypatch, "Entities.md")

    artifact_import._write_seed_data({"seed_data/Settings/Entities.md": b""}, {"create-companies"})

    assert store.read_text(encoding="utf-8") == "### Adnoc\n"


def test_import_skips_a_seed_file_no_deployed_skill_needs(data_path, monkeypatch):
    deployed_skills_mention(monkeypatch)

    artifact_import._write_seed_data({"seed_data/Settings/Entities.md": b""}, {"unrelated-skill"})

    assert not (data_path / "Settings" / "Entities.md").exists()


def test_import_ignores_a_seed_file_nothing_registered(data_path, monkeypatch):
    deployed_skills_mention(monkeypatch, "Anything.md")

    artifact_import._write_seed_data({"seed_data/Settings/Anything.md": b""}, {"some-skill"})

    assert not (data_path / "Settings" / "Anything.md").exists()


def test_import_creates_a_plugin_registered_seed_file(data_path, monkeypatch):
    registered(monkeypatch, "Settings/Clients.md")
    deployed_skills_mention(monkeypatch, "Clients.md")

    artifact_import._write_seed_data({"seed_data/Settings/Clients.md": b""}, {"clients-skill"})

    assert (data_path / "Settings" / "Clients.md").is_file()


def test_export_carries_a_plugin_registered_seed_file_empty_when_a_skill_mentions_it(data_path, monkeypatch):
    registered(monkeypatch, "Settings/Clients.md")
    monkeypatch.setattr(artifact_export, "_closure_references_seed_needle", lambda closure, needle: needle == "Clients.md")
    payload: dict[str, bytes] = {}

    artifact_export._add_seed_data_entries([{"kind": "skill", "id": "clients-skill"}], payload)

    assert payload == {"seed_data/Settings/Clients.md": b""}
