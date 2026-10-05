"""BUG-082 -- the backend indexed the vault at boot and never again.

Everything built on the index (browse, search, tags, the graph, My Day, the
Cockpit) showed the vault as it was when the process started, while capture kept
writing: 250 notes invisible after three days of uptime, and an Emails tab reading
empty rather than stale. The `vault-index-rebuild` cron job already runs on a
schedule and already writes a fresh index to disk for the agents -- it just never
told the backend. Now it does.

The trap this pins: `/vault-index/rebuild` FIRES that cron job, so the job calling
it would trigger itself. The job calls `/vault-index/refresh`, which does not.
"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.business.core.vault import vault_manager as module
from app.business.core.vault.vault_manager import VaultManager
from app.business.logic import vault_index_rebuild
from app.config import settings
from app.main import app

_SCRIPTS_DIR = (Path(__file__).resolve().parents[1] / "app" / "business" / "core" / "skills"
                / "catalog" / "vault" / "vault-index" / "scripts")
_MANAGERS_DIR = (Path(__file__).resolve().parents[1] / "app" / "business" / "core" / "skills" / "managers")
for _path in (_SCRIPTS_DIR, _MANAGERS_DIR):
    sys.path.insert(0, str(_path))

import build_vault_index  # noqa: E402

client = TestClient(app)


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "vault_path", tmp_path)
    paths = []
    for name in ("First", "Second"):
        path = tmp_path / "Work" / "Notes" / f"{name}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('---\ntype: "Note"\n---\n\nbody\n', encoding="utf-8")
        paths.append(path)
    monkeypatch.setattr(module.vault_writer, "list_all_note_paths", lambda: list(paths))
    VaultManager().rebuild_index()
    return tmp_path, paths


def test_a_note_written_after_boot_is_indexed_by_a_refresh(vault, monkeypatch):
    tmp_path, paths = vault
    assert len(VaultManager().get_entries()) == 2

    later = tmp_path / "Work" / "Notes" / "Captured while running.md"
    later.write_text('---\ntype: "Note"\n---\n\nbody\n', encoding="utf-8")
    monkeypatch.setattr(module.vault_writer, "list_all_note_paths", lambda: [*paths, later])

    result = vault_index_rebuild.refresh_in_process_index()

    assert result["notes_indexed"] == 3
    assert len(VaultManager().get_entries()) == 3


def test_a_refresh_does_not_trigger_the_cron_job_that_calls_it(vault, monkeypatch):
    """The whole reason there are two endpoints: `/rebuild` fires the
    `vault-index-rebuild` job, so the job calling it would trigger itself."""
    fired = []
    monkeypatch.setattr(vault_index_rebuild, "get_client",
                        lambda: pytest.fail("a refresh must not reach Hermes"))

    result = vault_index_rebuild.refresh_in_process_index()

    assert result["agent_index_rebuild_triggered"] is False
    assert fired == []


def test_the_rebuild_endpoint_still_triggers_the_agent_index(vault, monkeypatch):
    fired = []

    class Cli:
        def run_cron_job(self, job_name, profile_id=None):
            fired.append(job_name)
            return True

    monkeypatch.setattr(vault_index_rebuild, "get_client", lambda: type("C", (), {"cli": Cli()})())

    result = vault_index_rebuild.rebuild_vault_index()

    assert result["agent_index_rebuild_triggered"] is True
    assert fired == ["vault-index-rebuild"]


def test_the_endpoint_answers_with_what_it_indexed(vault):
    response = client.post("/vault-index/refresh")

    assert response.status_code == 200
    assert response.json()["notes_indexed"] == 2
    assert response.json()["agent_index_rebuild_triggered"] is False


# -- the cron job's side ------------------------------------------------------------


def test_the_job_posts_to_the_refresh_endpoint(monkeypatch):
    """Not `/rebuild`: that one would have the job trigger itself."""
    asked = {}

    class Response:
        def read(self):
            return json.dumps({"notes_indexed": 3025}).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    def fake_urlopen(request, timeout=None):
        asked["url"] = request.full_url
        asked["method"] = request.method
        asked["timeout"] = timeout
        return Response()

    monkeypatch.setattr(build_vault_index.urllib.request, "urlopen", fake_urlopen)

    outcome = build_vault_index.notify_backend("http://127.0.0.1:8001")

    assert asked["url"] == "http://127.0.0.1:8001/vault-index/refresh"
    assert asked["method"] == "POST"
    assert outcome == {"notified": True, "backend": {"notes_indexed": 3025}}


def test_a_closed_app_does_not_fail_the_job(monkeypatch):
    """A scheduled run on a machine where the app is not open is the normal case;
    the disk index is written either way."""
    def refuse(_request, timeout=None):
        raise OSError("[WinError 10061] the target machine actively refused it")

    monkeypatch.setattr(build_vault_index.urllib.request, "urlopen", refuse)

    outcome = build_vault_index.notify_backend("http://127.0.0.1:8001")

    assert outcome["notified"] is False
    assert "refused" in outcome["reason"]


def test_an_empty_api_url_skips_the_call(monkeypatch):
    monkeypatch.setattr(build_vault_index.urllib.request, "urlopen",
                        lambda *_args, **_kwargs: pytest.fail("nothing to call"))

    assert build_vault_index.notify_backend("")["notified"] is False
