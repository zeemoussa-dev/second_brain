"""Viewing and editing an existing Template from Settings > Artifacts (2026-09-22).

An edit takes effect on the next Skill run -- the engine reads Template.json at
write time -- so nothing reaches disk unless it is a Template this framework
can use, and an edit never creates or renames one."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.business.core.templates.template_manager import TemplateManager
from app.data_access import templates as templates_data
from app.main import app

client = TestClient(app)


@pytest.fixture()
def install(tmp_path, monkeypatch) -> Path:
    root = tmp_path / "data" / "Templates"
    root.mkdir(parents=True)
    monkeypatch.setattr(templates_data, "templates_root", lambda: root)
    TemplateManager().seed_shipped_masters()
    return root


def _on_disk(root: Path, template_id: str) -> dict:
    return json.loads((root / template_id / "Template.json").read_text(encoding="utf-8"))


def test_a_template_is_read_exactly_as_on_disk(install: Path) -> None:
    response = client.get("/vault/templates/thread")

    assert response.status_code == 200
    assert response.json() == {"id": "thread", "json": _on_disk(install, "thread")}


def test_an_unknown_template_is_a_404(install: Path) -> None:
    assert client.get("/vault/templates/nope").status_code == 404
    assert client.put("/vault/templates/nope", json={"json": {"id": "nope"}}).status_code == 404
    assert not (install / "nope").exists()


def test_an_edit_is_saved_and_read_back(install: Path) -> None:
    edited = _on_disk(install, "thread")
    edited["root"]["sections"].append({"name": "Follow-ups", "access": "machine_write"})

    response = client.put("/vault/templates/thread", json={"json": edited})

    assert response.status_code == 200
    assert _on_disk(install, "thread") == edited
    assert "Follow-ups" in [section["name"] for section in response.json()["template"]["sections"]]


def test_a_template_the_framework_cannot_use_is_refused_and_nothing_is_written(install: Path) -> None:
    before = _on_disk(install, "thread")
    broken = json.loads(json.dumps(before))
    broken["root"]["sections"] = [{"title": "no name field"}]

    response = client.put("/vault/templates/thread", json={"json": broken})

    assert response.status_code == 422
    assert response.json()["detail"]
    assert _on_disk(install, "thread") == before


def test_an_edit_cannot_rename_a_template(install: Path) -> None:
    before = _on_disk(install, "thread")
    renamed = dict(before, id="thread-2")

    response = client.put("/vault/templates/thread", json={"json": renamed})

    assert response.status_code == 422
    assert "cannot be changed" in response.json()["detail"]
    assert _on_disk(install, "thread") == before
    assert not (install / "thread-2").exists()


@pytest.mark.parametrize("newline, trailing", [("\r\n", True), ("\r\n", False), ("\n", True), ("\n", False)])
def test_saving_keeps_the_files_own_line_endings_and_final_newline(install: Path, newline, trailing) -> None:
    """Found live: saving the `note` Template unchanged rewrote its bytes. Every
    Template on that install was CRLF, most with a final newline, in a synced
    folder -- so any edit became a whole-file diff."""
    path = install / "thread" / "Template.json"
    data = _on_disk(install, "thread")
    original = (json.dumps(data, indent=2) + ("\n" if trailing else "")).replace("\n", newline).encode("utf-8")
    path.write_bytes(original)

    assert client.put("/vault/templates/thread", json={"json": data}).status_code == 200
    assert path.read_bytes() == original


def test_a_template_that_no_longer_parses_is_reported_not_hidden(install: Path) -> None:
    (install / "thread" / "Template.json").write_text("{ not json", encoding="utf-8")

    response = client.get("/vault/templates/thread")

    assert response.status_code == 422
    assert "does not parse" in response.json()["detail"]
