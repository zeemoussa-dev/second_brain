"""The delegated token path, tested where it can actually go wrong.

These are contract tests like the rest of this Skill's suite, not unit trivia.
The failures worth pinning are the ones that would be SILENT or that would
break exactly once:

  * a rotated refresh token that is not persisted -- Entra invalidates the one
    just used, so dropping the replacement gives a pipeline that runs
    successfully once and then fails forever with invalid_grant;
  * a missing token store that raises something vague instead of naming the
    one-time sign-in the operator has to run;
  * a sign-in that returns no refresh token at all, which means `offline_access`
    was not granted and unattended running is impossible -- it must fail loudly
    at authorize time, not quietly at 3am;
  * the store leaking a token into a place it should not be.

No network: every test drives the token endpoint through a stub.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import graph_lib  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    """Every test gets its own store, and never the real one."""
    monkeypatch.setenv("GRAPH_TOKEN_STORE", str(tmp_path / "token.json"))
    monkeypatch.setenv("GRAPH_TENANT_ID", "tenant-guid")
    monkeypatch.setenv("GRAPH_CLIENT_ID", "client-guid")
    monkeypatch.setattr(graph_lib, "_cached_access_token", None)
    return tmp_path / "token.json"


def _stub_token_endpoint(monkeypatch, responses):
    """Feeds `responses` to successive _redeem calls, recording each form."""
    sent = []

    def fake_redeem(form):
        sent.append(dict(form))
        result = responses[min(len(sent) - 1, len(responses) - 1)]
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(graph_lib, "_redeem", fake_redeem)
    return sent


def test_a_rotated_refresh_token_is_persisted(isolated_store, monkeypatch):
    """The one that would work exactly once if we got it wrong."""
    graph_lib._write_refresh_token("original-refresh")
    _stub_token_endpoint(monkeypatch, [
        {"access_token": "access-1", "refresh_token": "rotated-refresh"},
    ])

    assert graph_lib._access_token() == "access-1"

    stored = json.loads(isolated_store.read_text(encoding="utf-8"))
    assert stored["refresh_token"] == "rotated-refresh", (
        "Entra invalidates the refresh token it just redeemed; not saving the "
        "replacement makes the NEXT run fail with invalid_grant"
    )


def test_an_unrotated_refresh_token_leaves_the_store_alone(isolated_store, monkeypatch):
    graph_lib._write_refresh_token("original-refresh")
    before = isolated_store.read_text(encoding="utf-8")
    _stub_token_endpoint(monkeypatch, [{"access_token": "access-1"}])

    graph_lib._access_token()

    assert isolated_store.read_text(encoding="utf-8") == before


def test_a_missing_store_names_the_command_that_fixes_it(isolated_store):
    with pytest.raises(graph_lib.GraphUnavailable) as raised:
        graph_lib._access_token()
    message = str(raised.value)
    assert "authorize_graph.py" in message, (
        "an operator hitting this at 3am needs the fix in the error, not a "
        "generic 'no token' that sends them reading source"
    )
    assert str(isolated_store) in message


def test_a_store_with_no_refresh_token_is_rejected(isolated_store):
    isolated_store.write_text(json.dumps({"signed_in_as": "someone"}), encoding="utf-8")
    with pytest.raises(graph_lib.GraphUnavailable, match="no refresh_token"):
        graph_lib._access_token()


def test_a_signin_without_offline_access_fails_loudly(monkeypatch):
    """No refresh token means unattended running is impossible. Failing here,
    at sign-in, is the whole point -- the alternative is discovering it on the
    first cron run after everyone has gone home."""
    _stub_token_endpoint(monkeypatch, [{"access_token": "access-only"}])
    with pytest.raises(graph_lib.GraphUnavailable, match="offline_access"):
        graph_lib.complete_device_code("device-code", interval=5, expires_in=60)


def test_device_code_signin_stores_the_refresh_token(isolated_store, monkeypatch):
    _stub_token_endpoint(monkeypatch, [
        {"access_token": "access-1", "refresh_token": "fresh-refresh"},
    ])
    graph_lib.complete_device_code("device-code", interval=5, expires_in=60)

    stored = json.loads(isolated_store.read_text(encoding="utf-8"))
    assert stored["refresh_token"] == "fresh-refresh"
    assert stored["updated_at"]


def test_authorization_pending_is_waited_out_not_treated_as_failure(isolated_store, monkeypatch):
    """Entra answers `authorization_pending` until the human finishes; treating
    that as an error would make sign-in impossible."""
    monkeypatch.setattr(graph_lib.time, "sleep", lambda _seconds: None)
    _stub_token_endpoint(monkeypatch, [
        graph_lib.GraphUnavailable("Graph token request refused (authorization_pending: ...)"),
        {"access_token": "access-1", "refresh_token": "fresh-refresh"},
    ])

    graph_lib.complete_device_code("device-code", interval=5, expires_in=60)
    assert json.loads(isolated_store.read_text(encoding="utf-8"))["refresh_token"] == "fresh-refresh"


def test_a_real_refusal_is_not_waited_out(monkeypatch):
    monkeypatch.setattr(graph_lib.time, "sleep", lambda _seconds: None)
    _stub_token_endpoint(monkeypatch, [
        graph_lib.GraphUnavailable("Graph token request refused (expired_token: ...)"),
    ])
    with pytest.raises(graph_lib.GraphUnavailable, match="expired_token"):
        graph_lib.complete_device_code("device-code", interval=5, expires_in=60)


def test_the_refresh_token_is_sent_not_a_client_secret(isolated_store, monkeypatch):
    """A device-code public client has no secret; sending one would be both
    wrong and a credential in a place it does not belong."""
    graph_lib._write_refresh_token("original-refresh")
    monkeypatch.setenv("GRAPH_CLIENT_SECRET", "should-never-be-used")
    sent = _stub_token_endpoint(monkeypatch, [{"access_token": "access-1"}])

    graph_lib._access_token()

    assert sent[0]["grant_type"] == "refresh_token"
    assert sent[0]["refresh_token"] == "original-refresh"
    assert "client_secret" not in sent[0]


def test_the_token_store_is_not_inside_the_repo(monkeypatch, tmp_path):
    """The refresh token is a credential; it belongs in instance data."""
    monkeypatch.delenv("GRAPH_TOKEN_STORE", raising=False)
    monkeypatch.setenv("SECOND_BRAIN_DATA_PATH", str(tmp_path / "config"))
    path = graph_lib._token_store_path()
    assert path.parent == tmp_path / "config"
    assert "second brain" not in str(path).lower().replace("\\", " ").replace("/", " ")
