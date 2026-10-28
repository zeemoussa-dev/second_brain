"""This process serves the built UI in production (2026-10-28).

A production box has no Vite and no second service: the UI is a folder of
static files served from here, which puts the app and its API on ONE port and
ONE origin -- removing the CORS surface and the cross-origin cookie question
rather than configuring around them.

The whole of this file is about the seam between that and the default-deny
guard: the shell must be downloadable by someone who cannot yet sign in, and
nothing else may come with it.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import frontend_dist
from app.main import app

client = TestClient(app)

_AS_A_BROWSER = {"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}


@pytest.fixture(autouse=True)
def _built_ui_present():
    """Every test here needs a real `dist/`. A checkout that has never run a
    frontend build has none, and these are then skipped rather than failing:
    the absence is the documented development state, not a fault."""
    if frontend_dist.frontend_shell() is None:
        pytest.skip("no built frontend in this checkout (src/frontend/dist)")


@pytest.fixture
def signed_out(monkeypatch):
    """The suite signs every request in as an Admin by default; these tests
    are about the person who has NOT signed in yet."""
    from app.api import auth_guard

    monkeypatch.setattr(auth_guard._AuthenticationReader, "identity_for", lambda self, request: None)
    monkeypatch.setattr(auth_guard._AuthenticationReader, "agent_caller_for", lambda self, request: None)


def test_the_sign_in_page_can_be_downloaded_by_someone_signed_out(signed_out) -> None:
    """A sign-in screen that cannot be downloaded is a locked door with the
    handle on the inside."""
    response = client.get("/", headers=_AS_A_BROWSER)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<!doctype html>" in response.text.lower()


def test_the_bundle_and_its_assets_are_downloadable_signed_out(signed_out) -> None:
    """The shell is useless without the code it loads."""
    bundle = next(frontend_dist.DIST.joinpath("assets").glob("*.js"))

    response = client.get(f"/assets/{bundle.name}")

    assert response.status_code == 200
    assert len(response.content) > 0


def test_a_deep_link_reloads_into_the_app_not_a_json_refusal(signed_out) -> None:
    """Reloading on `/browse/<note>` with no session should put the sign-in
    screen on screen. A page of `{"detail": ...}` is what it used to do."""
    response = client.get("/browse/01%20Mandate", headers=_AS_A_BROWSER)

    assert response.status_code == 200
    assert "<!doctype html>" in response.text.lower()


def test_an_api_path_asked_for_as_html_runs_nothing(signed_out) -> None:
    """The dangerous half of the rule above. Serving the shell to a browser
    navigation must not become a way to call the API without an account: the
    request is refused by the middleware and never reaches its route, so what
    comes back is the shell, never the endpoint's data."""
    response = client.get("/vault-search/notes", headers=_AS_A_BROWSER)

    assert "<!doctype html>" in response.text.lower()
    assert '"notes"' not in response.text
    assert '"total"' not in response.text


def test_an_api_call_is_still_refused_as_json(signed_out) -> None:
    """`fetch` asks for data and is told no, in the shape the client parses."""
    response = client.get("/vault-search/notes")

    assert response.status_code == 401
    assert response.json()["reason"] == "not_authenticated"


def test_the_ui_never_serves_a_file_outside_itself(signed_out) -> None:
    """The catch-all resolves the path and checks it is inside `dist/` before
    serving: `/../../.env` is a request this process would otherwise be glad
    to answer."""
    for attempt in ("/../.env", "/../../.env", "/..%2f..%2f.env", "/assets/../../../.env"):
        response = client.get(attempt, headers=_AS_A_BROWSER)

        assert "SECOND_BRAIN_DATA_PATH" not in response.text, f"{attempt} served a real file"
        assert "COMPASS_API_KEY" not in response.text, f"{attempt} served a real file"


def test_health_is_still_json_not_the_shell() -> None:
    """Tooling with no account reads this, and the catch-all sits at
    `/{path}` -- mounted last so it cannot shadow a real route."""
    response = client.get("/health")

    assert response.json()["status"] == "ok"


def test_a_route_registered_after_startup_is_not_shadowed() -> None:
    """The bug the first version of this shipped with.

    It served the UI from `@app.get("/{path:path}")` registered at import, and
    FastAPI matches in registration order -- so every route added LATER
    returned the UI instead of itself. Plugin routers are added later, by the
    plugin host at install time, which on a production box would have
    presented as "all my plugins' endpoints return the web page".

    The fallback is a 404 handler now: it runs only after routing has failed,
    so there is nothing for it to shadow.
    """
    from fastapi import APIRouter

    late = APIRouter()

    @late.get("/a-plugin-added-me-later")
    def added_after_the_ui_was_mounted() -> dict:
        return {"mounted": "late"}

    app.include_router(late)

    response = client.get("/a-plugin-added-me-later")

    assert response.status_code == 200
    assert response.json() == {"mounted": "late"}


def test_a_missing_api_resource_is_still_a_404_for_a_data_caller() -> None:
    """Only a request that names `text/html` gets the shell. A note that does
    not exist must still be a 404 to the code asking for it."""
    response = client.get("/vault-search/notes/no-such-note-exists-here")

    assert response.status_code == 404


def test_a_routes_own_404_message_survives() -> None:
    """Registering a handler for 404 replaces FastAPI's for EVERY 404 in the
    app. The first version returned a flat "Not Found", which turned "no
    workflow run '0000…beef'" into nothing a caller could act on -- two
    workflow tests caught it. The route's own words are kept."""
    response = client.post("/workflows/runs/0000000000000000000000000000beef/next-step")

    assert response.status_code == 404
    assert "0000000000000000000000000000beef" in response.json()["detail"]
