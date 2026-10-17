"""The Action catalogue's HTTP surface (REQ-SB-95-US-02-T03).

Driven through the real `app.main.app` object with `TestClient`, which
is what every other API test here does (test_blueprints_api.py,
test_plugin_host.py, test_setup_wizard.py and nine more) -- so these
tests also prove the router is actually REGISTERED, not merely
importable.

Two things are monkeypatched and nothing else:

- the Action store, so no test writes into this install's real
  <DATA_PATH>/data/Actions/;
- the three resolution sources, because what is deployed, routed and
  registered on the machine running the suite is instance state -- a
  test asserting against it would pass or fail by accident.

The Manager's own rules are NOT re-tested here (tests/
test_action_resolution.py owns those). What is tested is that this
router surfaces them honestly: the refusal keeps the Manager's words,
and the list keeps the broken entry.
"""
import pytest
from fastapi.testclient import TestClient

import app.main as main_app

client = TestClient(main_app.app)

A_DEPLOYED_SKILL = "email-thread-capture"
A_REAL_ROUTE = ("POST", "/vault-index/refresh")
A_REAL_FEATURE_KEY = "/settings/artifacts"


@pytest.fixture
def resolvable(monkeypatch):
    """The live sources, replaced by ones this test controls. Returns
    the mutable deployed-skill set so a test can undeploy something
    after a save -- the AC-07 event."""
    deployed = {A_DEPLOYED_SKILL}
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.deployed_skill_ids",
        lambda: set(deployed),
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.app_route_table",
        lambda: {A_REAL_ROUTE},
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.UI_FEATURE_KEYS",
        (A_REAL_FEATURE_KEY,),
    )
    return deployed


@pytest.fixture
def stored_actions(monkeypatch) -> dict:
    """The whole store, in memory, keyed by action id -- so "nothing was
    written" is an assertion rather than an absence of evidence."""
    written: dict = {}

    def read(action_id: str) -> dict:
        if action_id not in written:
            raise FileNotFoundError(action_id)
        return written[action_id]

    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.write_action_json",
        lambda action_id, data: written.update({action_id: data}),
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.read_action_json",
        read,
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.list_action_ids",
        lambda: sorted(written),
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.delete_action_definition",
        lambda action_id: written.pop(action_id, None),
    )
    return written


A_COMPLETE_ACTION = {
    "id": "capture-the-thread",
    "description": "Capture an email thread into the vault",
    "inputs": [
        {"name": "thread_id", "type": "string", "required": True, "description": "The thread to capture"},
        {"name": "dry_run", "type": "boolean", "required": False, "description": ""},
    ],
    "allowed_callers": ["cbo-agent", "pss-agent"],
    "needs_confirmation": True,
    "implementation": {"skill": {"skill_id": A_DEPLOYED_SKILL}},
}


def test_a_complete_action_is_saved_listed_and_reopens_as_saved(resolvable, stored_actions) -> None:
    """[REQ-SB-95-US-02-AC-01] The whole round trip over HTTP: saved,
    then listed with id/description/implementation kind, then reopened
    carrying EXACTLY the inputs, required flags, allowed_callers and
    confirmation flag that were posted -- a catalogue that quietly drops
    a required flag or a caller is worse than one that refuses."""
    created = client.post("/actions", json=A_COMPLETE_ACTION)

    assert created.status_code == 200, created.text
    assert created.json()["id"] == "capture-the-thread"

    listed = client.get("/actions")
    assert listed.status_code == 200
    assert listed.json() == [{
        "id": "capture-the-thread",
        "description": "Capture an email thread into the vault",
        "implementation_kind": "skill",
        "status": "resolves",
        "reason": None,
    }]

    reopened = client.get("/actions/capture-the-thread")
    assert reopened.status_code == 200
    body = reopened.json()
    assert body["inputs"] == A_COMPLETE_ACTION["inputs"]
    assert [entry["required"] for entry in body["inputs"]] == [True, False]
    assert body["allowed_callers"] == ["cbo-agent", "pss-agent"]
    assert body["needs_confirmation"] is True
    assert body["implementation"] == {
        "kind": "skill", "skill_id": A_DEPLOYED_SKILL, "method": "", "path": "", "feature_key": "",
    }


def test_an_edit_round_trips_and_an_unknown_id_is_404(resolvable, stored_actions) -> None:
    """[REQ-SB-95-US-02-AC-01] The other half of CRUD. An omitted field
    is left alone, a supplied one replaces -- and editing an id that
    does not exist is a 404, never a silently-created Action."""
    client.post("/actions", json=A_COMPLETE_ACTION)

    edited = client.put(
        "/actions/capture-the-thread",
        json={"description": "Capture a thread", "allowed_callers": ["*"]},
    )

    assert edited.status_code == 200
    assert edited.json()["description"] == "Capture a thread"
    assert edited.json()["allowed_callers"] == ["*"]
    # Untouched by an edit that did not mention them.
    assert edited.json()["needs_confirmation"] is True
    assert len(edited.json()["inputs"]) == 2

    assert client.put("/actions/no-such-action", json={"description": "x"}).status_code == 404
    assert client.get("/actions/no-such-action").status_code == 404


def test_deleting_removes_it_from_the_catalogue(resolvable, stored_actions) -> None:
    """[REQ-SB-95-US-02-AC-01] Unguarded delete is correct today -- the
    Workflow reverse-lookup guard arrives with the Workflow kind
    (REQ-SB-95-US-04-T02)."""
    client.post("/actions", json=A_COMPLETE_ACTION)

    assert client.delete("/actions/capture-the-thread").json() == {"deleted": True}
    assert client.get("/actions").json() == []
    assert client.delete("/actions/capture-the-thread").json() == {"deleted": False}


def test_an_implementation_that_does_not_resolve_is_refused_and_not_listed(
    resolvable, stored_actions,
) -> None:
    """[REQ-SB-95-US-02-AC-02] The refusal reaches the client naming
    what did not resolve -- the Manager's own sentence, not a flattened
    "Bad Request" -- and the Action is in neither the store nor the
    catalogue afterwards."""
    refused = client.post("/actions", json={
        "id": "search-the-vault",
        "description": "Search the vault",
        "implementation": {"skill": {"skill_id": "vault-search"}},
    })

    assert 400 <= refused.status_code < 500
    detail = refused.json()["detail"]
    assert "vault-search" in detail
    assert "not deployed" in detail

    assert client.get("/actions").json() == []
    assert stored_actions == {}


def test_each_implementation_kind_is_refused_on_its_own_terms(resolvable, stored_actions) -> None:
    """[REQ-SB-95-US-02-AC-02] An http route this app does not expose
    and an unregistered ui feature key are refused the same way, each
    naming the thing the operator actually typed."""
    bad_route = client.post("/actions", json={
        "id": "refresh-the-index",
        "implementation": {"http": {"method": "POST", "path": "/vault-index/refersh"}},
    })
    assert 400 <= bad_route.status_code < 500
    assert "/vault-index/refersh" in bad_route.json()["detail"]

    bad_feature = client.post("/actions", json={
        "id": "open-the-artifacts-page",
        "implementation": {"ui": {"feature_key": "/settings/artefacts"}},
    })
    assert 400 <= bad_feature.status_code < 500
    assert "/settings/artefacts" in bad_feature.json()["detail"]

    assert stored_actions == {}


def test_an_edit_onto_an_unresolvable_implementation_is_refused(resolvable, stored_actions) -> None:
    """[REQ-SB-95-US-02-AC-02] "creating or editing" -- a saved,
    resolving Action cannot be downgraded into a broken one over HTTP,
    and the stored definition is untouched after the refusal."""
    client.post("/actions", json=A_COMPLETE_ACTION)
    before = dict(stored_actions["capture-the-thread"])

    refused = client.put("/actions/capture-the-thread", json={
        "description": "edited",
        "implementation": {"ui": {"feature_key": "/nowhere"}},
    })

    assert 400 <= refused.status_code < 500
    assert "/nowhere" in refused.json()["detail"]
    assert stored_actions["capture-the-thread"] == before


def test_putting_a_get_body_straight_back_is_refused_loudly(resolvable, stored_actions) -> None:
    """[REQ-SB-95-US-02-AC-03] The read shape and the write shape of
    `implementation` differ (flat `kind` vs the kind as a key), so a
    client that echoes a GET body back must find out immediately. It is
    refused by the exactly-one rule -- never accepted as "no change",
    which would be a saved Action silently keeping an implementation
    the operator believed they had replaced."""
    client.post("/actions", json=A_COMPLETE_ACTION)
    fetched = client.get("/actions/capture-the-thread").json()

    echoed = client.put("/actions/capture-the-thread", json=fetched)

    assert 400 <= echoed.status_code < 500
    assert "exactly one implementation" in echoed.json()["detail"]


def test_zero_and_two_implementations_are_refused_and_exactly_one_saves(
    resolvable, stored_actions,
) -> None:
    """[REQ-SB-95-US-02-AC-03] Never zero and never two. Both refusals
    carry the exactly-one rule in words, and the third post -- naming
    exactly one -- saves normally, so the rule is about the payload and
    not about the id."""
    no_implementation = client.post("/actions", json={
        "id": "capture-the-thread", "description": "Capture an email thread",
    })
    assert 400 <= no_implementation.status_code < 500
    assert "exactly one implementation" in no_implementation.json()["detail"]

    two_implementations = client.post("/actions", json={
        "id": "capture-the-thread",
        "implementation": {
            "skill": {"skill_id": A_DEPLOYED_SKILL},
            "ui": {"feature_key": A_REAL_FEATURE_KEY},
        },
    })
    assert 400 <= two_implementations.status_code < 500
    assert "exactly one implementation" in two_implementations.json()["detail"]
    assert "skill, ui" in two_implementations.json()["detail"]

    assert stored_actions == {}

    exactly_one = client.post("/actions", json={
        "id": "capture-the-thread",
        "implementation": {"skill": {"skill_id": A_DEPLOYED_SKILL}},
    })
    assert exactly_one.status_code == 200
    assert [entry["id"] for entry in client.get("/actions").json()] == ["capture-the-thread"]
    # Only the kind it named is stored -- the two it did not name are
    # absent from the definition, not present-and-null.
    assert stored_actions["capture-the-thread"]["implementation"] == {
        "skill": {"skill_id": A_DEPLOYED_SKILL}
    }


def test_an_action_that_stopped_resolving_is_listed_as_broken(resolvable, stored_actions) -> None:
    """[REQ-SB-95-US-02-AC-07] The Skill resolved at save and was
    undeployed afterwards. The catalogue must still list that Action,
    carrying `broken` and the named cause -- omitting it, or failing the
    whole list because of it, is the silent failure ADR-032 exists to
    prevent. The healthy Action beside it is unaffected."""
    client.post("/actions", json=A_COMPLETE_ACTION)
    client.post("/actions", json={
        "id": "refresh-the-index",
        "description": "Rebuild the vault index now",
        "implementation": {"http": {"method": "POST", "path": "/vault-index/refresh"}},
    })

    assert [entry["status"] for entry in client.get("/actions").json()] == ["resolves", "resolves"]

    resolvable.remove(A_DEPLOYED_SKILL)

    catalogue = {entry["id"]: entry for entry in client.get("/actions").json()}
    assert catalogue["capture-the-thread"]["status"] == "broken"
    assert catalogue["capture-the-thread"]["implementation_kind"] == "skill"
    assert A_DEPLOYED_SKILL in catalogue["capture-the-thread"]["reason"]
    assert "not deployed" in catalogue["capture-the-thread"]["reason"]
    assert catalogue["capture-the-thread"]["description"] == A_COMPLETE_ACTION["description"]

    assert catalogue["refresh-the-index"]["status"] == "resolves"
    assert catalogue["refresh-the-index"]["reason"] is None

    # Reading the broken entry still works -- a broken implementation is
    # a status, not a corrupt Action.
    assert client.get("/actions/capture-the-thread").status_code == 200
