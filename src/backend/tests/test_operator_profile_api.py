"""The Operator Profile's two routes -- `REQ-SB-95-US-01-T03`.

Covers the two locked ACs this task owns: `AC-01` (one record, two
routes, no collection surface, and a round trip that returns exactly
what was sent) and `AC-04` (the own address is read-only in the response
and never written by `PUT`).

Every test drives the real, unmodified `app` through `TestClient`, the
way `tests/test_blueprints_api.py` does, against a
`second_brain_data_path` inside pytest's own tmp dir that does not exist
when the test starts. So the suite exercises a genuinely empty install
and can never read or write the operator's real store. Every value below
is fictitious.

The fixture also fills every `REQUIRED_FOR_STARTUP` setting, because
`main.gate_on_setup_mode` answers `503` to every route outside
`/setup`, `/health` and `/boot-status` while the install is
unconfigured: without this the whole file would pass or fail depending
on whether the machine running it happens to have a real `.env`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main_app
from app.business.core.actions.action_manager import app_route_table
from app.config import REQUIRED_FOR_STARTUP, settings

client = TestClient(main_app.app)

OWN_ADDRESS = "operator@example.test"
A_DIFFERENT_ADDRESS = "someone-else@example.test"

A_PROFILE = {
    "name": "Robin Fictional",
    "other_email_addresses": ["robin.alt@example.test", "robin@example.invalid"],
    "timezone": "Etc/UTC",
    "team": [
        {"email": "blue@example.test", "role": "Engineer"},
        {"email": "green@example.test", "role": "Designer"},
        {"email": "amber@example.test", "role": "Analyst"},
    ],
}


@pytest.fixture(autouse=True)
def empty_install(tmp_path, monkeypatch):
    """A data path that does not exist yet -- the fresh-install state,
    and the thing that keeps the real store out of reach."""
    data_path = tmp_path / "second-brain-data"
    for field in REQUIRED_FOR_STARTUP:
        monkeypatch.setattr(settings, field, tmp_path / "vault" if field == "vault_path" else "set")
    monkeypatch.setattr(settings, "second_brain_data_path", data_path)
    monkeypatch.setattr(settings, "self_email", OWN_ADDRESS)
    assert not data_path.exists()
    return data_path


def profile_file(data_path: Path) -> Path:
    return data_path / "data" / "Operator" / "Profile.json"


def stored_bytes(data_path: Path) -> bytes:
    return profile_file(data_path).read_bytes()


def owned_fields(body: dict) -> dict:
    return {field: body[field] for field in ("name", "other_email_addresses", "timezone", "team")}


def test_a_put_then_a_get_returns_exactly_what_was_saved(empty_install):
    """[REQ-SB-95-US-01-AC-01] The "reopening the page shows exactly
    what was saved" clause, proven at the API layer."""
    put_response = client.put("/operator/profile", json=A_PROFILE)
    get_response = client.get("/operator/profile")

    assert (put_response.status_code, get_response.status_code) == (200, 200)
    for body in (put_response.json(), get_response.json()):
        assert owned_fields(body) == A_PROFILE
        assert body["is_configured"] is True

    assert profile_file(empty_install).is_file()
    assert json.loads(stored_bytes(empty_install)) == A_PROFILE


def test_the_resource_offers_exactly_two_routes_and_no_collection_surface(empty_install):
    """[REQ-SB-95-US-01-AC-01] `ADR-032` chose "configuration, not a
    catalogue", and a collection-shaped API is how that decision would
    quietly erode. Asserted over the live app's own route table rather
    than by reading the router, so a route added anywhere -- another
    router, a plugin -- is caught too.

    Read through `app_route_table()` rather than off `app.routes`
    directly: this installed FastAPI keeps an included router as a lazy
    placeholder, so a flat read of `app.routes` sees only the four
    /docs paths and would pass while asserting nothing (measured here
    first, and already documented on that function)."""
    operator_routes = {
        (method, path)
        for method, path in app_route_table()
        if path.startswith("/operator") and method not in {"HEAD", "OPTIONS"}
    }

    assert operator_routes == {("GET", "/operator/profile"), ("PUT", "/operator/profile")}
    # Said again as the three negatives the AC names, so a failure says
    # which property broke rather than only that a set differs.
    assert not [path for method, path in operator_routes if method in {"POST", "DELETE", "PATCH"}]
    assert not [path for method, path in operator_routes if "{" in path]
    assert not [path for method, path in operator_routes if path.rstrip("/").endswith("profiles")]


def test_a_malformed_team_entry_is_refused_and_nothing_is_partially_saved(empty_install):
    """[REQ-SB-95-US-01-AC-01] Missing `email`, and a smuggled copy of a
    person -- refused by name, with the previous record left byte-identical."""
    assert client.put("/operator/profile", json=A_PROFILE).status_code == 200
    before = stored_bytes(empty_install)

    no_email = {**A_PROFILE, "team": [{"email": "blue@example.test", "role": "Engineer"}, {"role": "Designer"}]}
    response = client.put("/operator/profile", json=no_email)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert ["body", "team", 1, "email"] in [error["loc"] for error in errors]

    a_copy_of_a_person = {**A_PROFILE, "team": [{
        "email": "blue@example.test", "role": "Engineer", "name": "Blue Fictional", "title": "Principal Engineer",
    }]}
    response = client.put("/operator/profile", json=a_copy_of_a_person)

    assert response.status_code == 422
    refused_fields = {tuple(error["loc"]) for error in response.json()["detail"]}
    assert ("body", "team", 0, "name") in refused_fields
    assert ("body", "team", 0, "title") in refused_fields

    assert stored_bytes(empty_install) == before
    assert owned_fields(client.get("/operator/profile").json()) == A_PROFILE


def test_the_get_reports_the_own_address_read_only_and_names_its_editor(empty_install):
    """[REQ-SB-95-US-01-AC-04] The response never offers it as an
    editable field; it names where that one is edited."""
    own_address = client.get("/operator/profile").json()["own_address"]

    assert own_address["email"] == OWN_ADDRESS
    assert own_address["read_only"] is True
    assert own_address["setting_key"] == "SELF_EMAIL"
    assert own_address["edited_at"] == "Settings > System"


def test_a_put_that_tries_to_set_the_own_address_is_refused_and_writes_nothing(empty_install):
    """[REQ-SB-95-US-01-AC-04] Refused rather than accepted-and-dropped:
    a `200` is the client's only evidence that what it sent was stored,
    and the Profile page would otherwise show the old value with no
    explanation. Whichever shape it arrives in, `Profile.json` ends up
    holding no copy of either address."""
    assert client.put("/operator/profile", json=A_PROFILE).status_code == 200
    before = stored_bytes(empty_install)

    for payload in (
        {**A_PROFILE, "own_address": {"email": A_DIFFERENT_ADDRESS}},
        {**A_PROFILE, "own_address": A_DIFFERENT_ADDRESS},
        {**A_PROFILE, "self_email": A_DIFFERENT_ADDRESS},
    ):
        response = client.put("/operator/profile", json=payload)

        assert response.status_code == 409
        assert "SELF_EMAIL" in response.json()["detail"]
        assert "Settings > System" in response.json()["detail"]

    # Any OTHER unowned key is refused too, by the request model itself.
    unknown_key = client.put("/operator/profile", json={**A_PROFILE, "email": A_DIFFERENT_ADDRESS})
    assert unknown_key.status_code == 422
    assert ["body", "email"] in [error["loc"] for error in unknown_key.json()["detail"]]

    written = stored_bytes(empty_install)
    assert written == before
    for address in (OWN_ADDRESS, A_DIFFERENT_ADDRESS):
        assert address.encode("utf-8") not in written
    assert b"own_address" not in written and b"self_email" not in written
    assert set(json.loads(written)) == {"name", "other_email_addresses", "timezone", "team"}

    # And the setting is still what the Profile reports, unchanged by
    # anything the refused payloads asked for.
    assert client.get("/operator/profile").json()["own_address"]["email"] == OWN_ADDRESS


def test_a_saved_profile_never_carries_the_own_address_into_the_store(empty_install):
    """[REQ-SB-95-US-01-AC-04] The ordinary save path, byte-checked: the
    mirrored address reaches the response and never the file."""
    body = client.put("/operator/profile", json=A_PROFILE).json()

    assert body["own_address"]["email"] == OWN_ADDRESS
    assert OWN_ADDRESS.encode("utf-8") not in stored_bytes(empty_install)
