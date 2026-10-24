"""Staying signed in (operator, 2026-10-24: "It Expires alot and No Remember
Password so I need to Enter Everything everytime").

The eight-hour rolling session was never what decided how long anyone stayed
signed in. The cookie carrying it had no `max-age`, which makes it a SESSION
cookie: the browser threw it away when it closed, every time, and the server
session it pointed at was left orphaned until it idled out.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.auth_guard import SESSION_COOKIE
from app.business.core.users.user_manager import (
    REMEMBERED_IDLE_TIMEOUT,
    SESSION_IDLE_TIMEOUT,
    UserManager,
)
from app.business.core.users.user import Role
from app.config import settings
from app.data_access import users_db
from app.main import app

client = TestClient(app)

_PASSWORD = "a-long-enough-password"


@pytest.fixture
def account(monkeypatch, tmp_path):
    """One install with one real user, in its own data root."""
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path)
    users = UserManager()
    users.initialise()
    users.create_user("operator", _PASSWORD, Role.ADMIN, "Operator")
    return users


def test_the_session_cookie_outlives_the_browser(account) -> None:
    """The whole bug: with no max-age the browser discards it on close, so
    "signed in for eight hours" meant "signed in until you close the
    window"."""
    response = client.post(
        "/auth/sign-in", json={"username": "operator", "password": _PASSWORD}
    )

    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert "max-age=" in cookie.lower(), f"still a session cookie: {cookie}"


def test_remembering_me_is_a_month_not_eight_hours(account) -> None:
    response = client.post(
        "/auth/sign-in",
        json={"username": "operator", "password": _PASSWORD, "remember": True},
    )

    cookie = response.headers["set-cookie"].lower()
    assert f"max-age={int(REMEMBERED_IDLE_TIMEOUT.total_seconds())}" in cookie


def test_not_remembering_keeps_the_short_window(account) -> None:
    """The default is unchanged for a caller that does not ask."""
    response = client.post(
        "/auth/sign-in",
        json={"username": "operator", "password": _PASSWORD, "remember": False},
    )

    cookie = response.headers["set-cookie"].lower()
    assert f"max-age={int(SESSION_IDLE_TIMEOUT.total_seconds())}" in cookie


def test_a_remembered_session_is_not_demoted_by_its_next_request(account) -> None:
    """The window is read back from the row rather than reset to the default,
    so one request would otherwise cut a month down to eight hours -- the
    exact bug a column-free implementation invites."""
    _, token, window = account.authenticate("operator", _PASSWORD, remember=True)
    assert window == REMEMBERED_IDLE_TIMEOUT

    account.identity_for_token(token)

    session = users_db.read_session(_digest(token))
    remaining = datetime.fromisoformat(session["expires_at"]) - datetime.now(timezone.utc)
    assert remaining > SESSION_IDLE_TIMEOUT * 2, "a remembered session was demoted on use"


def test_an_ordinary_session_still_rolls_eight_hours(account) -> None:
    _, token, window = account.authenticate("operator", _PASSWORD)
    assert window == SESSION_IDLE_TIMEOUT

    account.identity_for_token(token)

    session = users_db.read_session(_digest(token))
    remaining = datetime.fromisoformat(session["expires_at"]) - datetime.now(timezone.utc)
    assert timedelta(hours=7) < remaining <= SESSION_IDLE_TIMEOUT


def test_signing_out_still_ends_it_immediately(account) -> None:
    """Remembering is a longer leash, not a weaker lock."""
    _, token, _ = account.authenticate("operator", _PASSWORD, remember=True)

    account.sign_out(token)

    assert account.identity_for_token(token) is None


def test_the_first_admin_is_remembered(account, monkeypatch, tmp_path) -> None:
    """The person who just set the install up is the one least served by
    being asked again in eight hours."""
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path / "fresh")
    response = client.post(
        "/auth/bootstrap",
        json={"username": "founder", "password": _PASSWORD, "display_name": "Founder"},
    )

    assert response.status_code == 200
    cookie = response.headers["set-cookie"].lower()
    assert f"max-age={int(REMEMBERED_IDLE_TIMEOUT.total_seconds())}" in cookie


def test_the_cookie_stays_httponly_and_lax(account) -> None:
    """Giving it a lifetime must not quietly relax anything else about it."""
    response = client.post(
        "/auth/sign-in", json={"username": "operator", "password": _PASSWORD}
    )

    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert SESSION_COOKIE.lower() in cookie


def _digest(token: str) -> str:
    import hashlib

    return hashlib.sha256(token.encode("utf-8")).hexdigest()
