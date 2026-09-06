"""The /blueprints HTTP surface.

preflight and install are separate on purpose: preflight creates NOTHING, so
the Settings card can show exactly what would happen -- and what would stop
it -- before the operator commits.
"""
from fastapi.testclient import TestClient

import app.main as main_app
from app.business.core.blueprints.blueprint_manager import BlueprintManager

client = TestClient(main_app.app)


def test_listing_returns_the_shipped_blueprints() -> None:
    response = client.get("/blueprints")

    assert response.status_code == 200
    assert "notes-capture" in [b["id"] for b in response.json()]


def test_preflight_creates_nothing_and_reports_peers() -> None:
    response = client.get("/blueprints/notes-capture/preflight")
    body = response.json()

    assert response.status_code == 200
    assert body["ok"] is True
    assert body["peers"] == ["notes-manager"]
    assert body["templates"] == ["note"]
    # The Section is a suggestion the operator can override (BUG-046).
    assert body["suggested_section"] == "Librarian"
    assert isinstance(body["available_sections"], list)


def test_an_unknown_blueprint_is_404_on_both_endpoints() -> None:
    assert client.get("/blueprints/nope/preflight").status_code == 404
    assert client.post("/blueprints/nope/install").status_code == 404


def test_a_blueprint_that_cannot_install_is_409_not_500(monkeypatch) -> None:
    """A refused install is a real answer about a real Blueprint, and the
    card needs its `problems` to show. It must not surface as a crash."""
    monkeypatch.setattr(
        BlueprintManager, "install",
        lambda self, bid, section_id=None, wire_peers=True: {"installed": False, "problems": ["Skill 'x' is not in the catalog"]},
    )

    response = client.post("/blueprints/notes-capture/install")

    assert response.status_code == 409
    assert "not in the catalog" in str(response.json()["detail"]["problems"])


def test_an_existing_but_unsatisfiable_blueprint_is_200_not_404(monkeypatch) -> None:
    """404 means "no such Blueprint". One that exists but cannot install is a
    200 carrying ok:false -- conflating the two would tell the operator the
    Blueprint is missing when it is merely blocked."""
    monkeypatch.setattr(
        BlueprintManager, "preflight",
        lambda self, bid, section_id=None: {"blueprint_id": bid, "ok": False, "problems": ["template 'file' missing"]},
    )

    response = client.get("/blueprints/notes-capture/preflight")

    assert response.status_code == 200
    assert response.json()["ok"] is False


def test_peers_can_be_installed_without_touching_primary(monkeypatch) -> None:
    """wire_peers=false exists because appending to Primary's SOUL.md changes
    how the operator's own assistant behaves -- that should be refusable."""
    seen = {}
    monkeypatch.setattr(
        BlueprintManager, "install",
        lambda self, bid, section_id=None, wire_peers=True: seen.setdefault("wire_peers", wire_peers) or {"installed": True},
    )

    client.post("/blueprints/notes-capture/install?wire_peers=false")

    assert seen["wire_peers"] is False
