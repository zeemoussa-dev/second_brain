"""BUG-079 -- which `[[wikilink]]` targets are real notes is one answer, asked for.

Every surface used to work this out for itself, so a wikilink linked only where
somebody had remembered to: chat, where agents write them constantly, showed the
brackets. The browser cannot hold the index of an install with tens of thousands of
notes, so it asks about the handful of targets a text actually contains.
"""
import pytest
from fastapi.testclient import TestClient

from app.business.core.vault import vault_manager as module
from app.business.core.vault.vault_manager import VaultManager
from app.config import settings
from app.main import app

client = TestClient(app)

NOTES = {
    "Work/Customers/ADNOC/ADNOC.md": "Customer",
    "Work/Meetings/2026-09-22-Masdar-Core42/2026-09-22-Masdar-Core42.md": "Meeting",
}


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "vault_path", tmp_path)
    paths = []
    for relative, note_type in NOTES.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'---\ntype: "{note_type}"\n---\n\nbody\n', encoding="utf-8")
        paths.append(path)
    monkeypatch.setattr(module.vault_writer, "list_all_note_paths", lambda: paths)
    VaultManager().rebuild_index()
    return tmp_path


def test_a_real_note_resolves_and_anything_else_is_absent(vault):
    resolved = VaultManager().resolve_wikilink_targets(["ADNOC", "Not A Note"])

    assert resolved == {"ADNOC": "ADNOC"}


def test_a_target_resolves_however_it_is_cased_or_spaced(vault):
    """Obsidian resolves a wikilink case-insensitively, and an agent writing
    `[[adnoc]]` means the same note as one writing `[[ADNOC]]`. The answer is the
    note's real stem, which is what the link has to be built from."""
    resolved = VaultManager().resolve_wikilink_targets(["adnoc", "  ADNOC  "])

    assert resolved == {"adnoc": "ADNOC", "  ADNOC  ": "ADNOC"}


def test_the_endpoint_answers_for_the_targets_a_text_contains(vault):
    response = client.post(
        "/vault-search/resolve",
        json={"targets": ["2026-09-22-Masdar-Core42", "ADNOC", "Nobody"]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "resolved": {"2026-09-22-Masdar-Core42": "2026-09-22-Masdar-Core42", "ADNOC": "ADNOC"},
    }


def test_asking_about_nothing_is_not_an_error(vault):
    """A text with no wikilinks is the common case; the frontend skips the call,
    but an empty list must not be a 422 for whoever does make it."""
    response = client.post("/vault-search/resolve", json={"targets": []})

    assert response.status_code == 200
    assert response.json() == {"resolved": {}}
