"""The Workflow catalogue's HTTP surface (REQ-SB-95-US-04-T03).

Driven through the real `app.main.app` object with `TestClient` -- the
same thing `httpx.ASGITransport(app=app)` does underneath, and what
every other API test here already uses (tests/test_actions_api.py,
test_blueprints_api.py and eleven more) -- so these tests also prove the
router is really REGISTERED in app/main.py, not merely importable.

**Both stores are brought by the tests, and the Action catalogue is
built, not faked.** Two things are monkeypatched and nothing else: the
Workflow store and the Action store, each an in-memory dict, plus the
three resolution sources an Action's implementation is checked against
(what is deployed, routed and registered on the machine running the
suite is instance state -- a test asserting against it passes or fails
by accident). The three Actions these Workflows name are then created
through the real `POST /actions`, so they are catalogued exactly as the
operator's own catalogue screen would show them.

That is deliberately NOT a stubbed `ActionManager`: `AC-02` is the
save-time referential check against the LIVE catalogue (`ADR-034`), and
a fake catalogue would leave this file asserting that the router
surfaces a refusal the real catalogue might never produce.
`test_these_tests_bring_their_own_action_catalogue` below pins that the
catalogue under test is the one these tests created and nothing this
install happens to have (`ESC-064`/`ESC-075` are both this failure).

What is NOT re-tested here: the Manager's own rules
(tests/test_workflow_artifact_kind.py and
tests/test_workflow_action_integrity.py own those). What is tested is
that this router surfaces them honestly -- the refusal keeps the
Manager's words, and the order survives the round trip.

The run routes (`ADR-034`) are `T05`'s and are deliberately absent.
"""
import pytest
from fastapi.testclient import TestClient

import app.main as main_app

client = TestClient(main_app.app)

A_DEPLOYED_SKILL = "email-thread-capture"
A_REAL_ROUTE = ("POST", "/vault-index/refresh")
A_REAL_FEATURE_KEY = "/settings/artifacts"

# The PRD's own motivating intent -- "list the Actions assigned to my
# team and send it to me by Mail" -- needs three real Actions to point
# at. Each one resolves against the sources the `resolvable` fixture
# controls, never against anything this machine has.
THE_ACTIONS_THESE_WORKFLOWS_NAME = {
    "list-team-actions": {"ui": {"feature_key": A_REAL_FEATURE_KEY}},
    "send-mail": {"skill": {"skill_id": A_DEPLOYED_SKILL}},
    "append-capture": {"http": {"method": "POST", "path": "/vault-index/refresh"}},
}

AN_ACTION_NO_INSTALL_HAS = "mail-the-whole-company"


@pytest.fixture
def resolvable(monkeypatch) -> None:
    """The live resolution sources, replaced by ones these tests
    control, so creating the three Actions below cannot depend on what
    is deployed here today."""
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.deployed_skill_ids",
        lambda: {A_DEPLOYED_SKILL},
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.app_route_table",
        lambda: {A_REAL_ROUTE},
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.UI_FEATURE_KEYS",
        (A_REAL_FEATURE_KEY,),
    )


@pytest.fixture
def stored_actions(monkeypatch) -> dict:
    """The Action store, in memory -- so nothing here reads or writes
    the operator's real <DATA_PATH>/data/Actions/, and the catalogue
    these Workflows are held to is exactly what this file put in it."""
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


@pytest.fixture
def stored_workflows(monkeypatch) -> dict:
    """The Workflow store, in memory, keyed by workflow id -- so
    "nothing was written" is an assertion rather than an absence of
    evidence.

    An unknown id raises `FileNotFoundError`, exactly as the real
    `read_workflow_json` does: a fake raising `KeyError` would sail past
    the Manager's own `(OSError, ValueError)` handling and turn "an
    unknown id is a 404" into an unhandled 500.
    """
    written: dict = {}

    def read(workflow_id: str) -> dict:
        if workflow_id not in written:
            raise FileNotFoundError(f"No Workflow.json for {workflow_id!r}")
        return written[workflow_id]

    monkeypatch.setattr(
        "app.business.core.workflows.workflow_manager.workflows_data.write_workflow_json",
        lambda workflow_id, data: written.update({workflow_id: data}),
    )
    monkeypatch.setattr(
        "app.business.core.workflows.workflow_manager.workflows_data.read_workflow_json",
        read,
    )
    monkeypatch.setattr(
        "app.business.core.workflows.workflow_manager.workflows_data.list_workflow_ids",
        lambda: sorted(written),
    )
    monkeypatch.setattr(
        "app.business.core.workflows.workflow_manager.workflows_data.delete_workflow_definition",
        lambda workflow_id: written.pop(workflow_id, None),
    )
    return written


@pytest.fixture
def a_real_action_catalogue(resolvable, stored_actions) -> dict:
    """The three Actions, really created over the real Actions API."""
    for action_id, implementation in THE_ACTIONS_THESE_WORKFLOWS_NAME.items():
        created = client.post("/actions", json={
            "id": action_id,
            "description": f"{action_id} (created by tests/test_workflows_api.py)",
            "implementation": implementation,
        })
        assert created.status_code == 200, created.text
    return stored_actions


def _three_ordered_steps() -> list[dict]:
    """Collect, then send -- with the sending step the one the operator
    wants to confirm -- then leave a trace. Order and flags are what the
    round trip is about, so both are asymmetric on purpose: a bug that
    reversed the list or spread the flag would be invisible against
    three identical steps."""
    return [
        {"id": "collect", "action_id": "list-team-actions",
         "inputs": {"team": "CBO"}, "description": "Collect the team's open Actions"},
        {"id": "send", "action_id": "send-mail", "inputs": {"to": "{{operator.self_email}}"},
         "needs_confirmation": True, "description": "Mail the list to me"},
        {"id": "log", "action_id": "append-capture", "inputs": {"note": "sent"},
         "description": "Leave a trace in the vault"},
    ]


A_DOCUMENTED_WORKFLOW = {
    "id": "mail-me-the-team-list",
    "request_kind": "list the Actions assigned to my team and mail them to me",
    "description": "The operator's standing handling for this ask",
    "steps": _three_ordered_steps(),
    "report": {"description": "the list that was sent, and to whom",
               "include_step_ids": ["collect", "send"]},
}


def test_these_tests_bring_their_own_action_catalogue(a_real_action_catalogue) -> None:
    """[REQ-SB-95-US-04-AC-02] The premise every assertion below rests
    on, asserted rather than assumed: the catalogue these Workflows are
    validated against holds exactly the three Actions this file created,
    and `mail-the-whole-company` is genuinely absent from it.

    Pinned because the alternative failure is silent -- a file that read
    the operator's real <DATA_PATH>/data/Actions/ would pass or fail by
    accident of what this machine happens to have catalogued today, and
    could not pass on an empty install at all (`ESC-064`, `ESC-075`).
    """
    catalogued = sorted(entry["id"] for entry in client.get("/actions").json())

    assert catalogued == ["append-capture", "list-team-actions", "send-mail"]
    assert AN_ACTION_NO_INSTALL_HAS not in catalogued
    assert client.get(f"/actions/{AN_ACTION_NO_INSTALL_HAS}").status_code == 404


def test_a_workflow_round_trips_its_ordered_steps_over_http(
    a_real_action_catalogue, stored_workflows,
) -> None:
    """[REQ-SB-95-US-04-AC-01] The whole round trip over HTTP: a request
    kind and three ordered steps against real catalogued Actions are
    saved, then reopened carrying the SAME steps in the SAME order with
    the same per-step confirmation flags, the same per-step inputs and
    the same report definition -- and the catalogue lists it.

    A surface that quietly reordered the steps, or spread one step's
    confirmation flag across the others, would be worse than one that
    refused the save: the operator's documented handling would run in an
    order they never wrote down."""
    created = client.post("/workflows", json=A_DOCUMENTED_WORKFLOW)

    assert created.status_code == 200, created.text
    assert created.json()["id"] == "mail-me-the-team-list"

    reopened = client.get("/workflows/mail-me-the-team-list")
    assert reopened.status_code == 200
    body = reopened.json()
    assert body["request_kind"] == A_DOCUMENTED_WORKFLOW["request_kind"]
    assert body["description"] == A_DOCUMENTED_WORKFLOW["description"]
    assert [(step["id"], step["action_id"], step["needs_confirmation"])
            for step in body["steps"]] == [
        ("collect", "list-team-actions", False),
        ("send", "send-mail", True),
        ("log", "append-capture", False),
    ]
    assert [step["inputs"] for step in body["steps"]] == [
        {"team": "CBO"}, {"to": "{{operator.self_email}}"}, {"note": "sent"},
    ]
    assert [step["description"] for step in body["steps"]] == [
        "Collect the team's open Actions", "Mail the list to me", "Leave a trace in the vault",
    ]
    assert body["report"] == {
        "description": "the list that was sent, and to whom",
        "include_step_ids": ["collect", "send"],
    }

    listed = client.get("/workflows")
    assert listed.status_code == 200
    assert [(entry["id"], entry["request_kind"], [step["id"] for step in entry["steps"]])
            for entry in listed.json()] == [
        ("mail-me-the-team-list", A_DOCUMENTED_WORKFLOW["request_kind"],
         ["collect", "send", "log"]),
    ]


def test_an_edit_reorders_leaves_omitted_fields_alone_and_a_delete_unlists_it(
    a_real_action_catalogue, stored_workflows,
) -> None:
    """[REQ-SB-95-US-04-AC-01] The rest of CRUD over the same surface. A
    supplied step list REPLACES the stored one in the order given (that
    is what a reorder is), a field the edit did not mention is left
    alone, an unknown id is a 404 on both read and edit, and a delete
    answers `ADR-014`'s result dict rather than a 404."""
    client.post("/workflows", json=A_DOCUMENTED_WORKFLOW)
    original = client.get("/workflows/mail-me-the-team-list").json()["steps"]

    edited = client.put("/workflows/mail-me-the-team-list", json={
        "description": "Reordered: leave the trace first",
        "steps": [original[2], original[0], original[1]],
    })

    assert edited.status_code == 200
    assert [step["id"] for step in edited.json()["steps"]] == ["log", "collect", "send"]
    # Each step kept its own confirmation flag rather than the flag of
    # the position it moved into.
    assert [step["needs_confirmation"] for step in edited.json()["steps"]] == [False, False, True]
    assert edited.json()["description"] == "Reordered: leave the trace first"
    # Untouched by an edit that did not mention them.
    assert edited.json()["request_kind"] == A_DOCUMENTED_WORKFLOW["request_kind"]
    assert edited.json()["report"]["include_step_ids"] == ["collect", "send"]

    assert client.get("/workflows/no-such-workflow").status_code == 404
    assert client.put("/workflows/no-such-workflow", json={"description": "x"}).status_code == 404

    assert client.delete("/workflows/mail-me-the-team-list").json() == {"deleted": True}
    assert client.get("/workflows").json() == []
    assert client.delete("/workflows/mail-me-the-team-list").json() == {"deleted": False}


def test_a_step_naming_an_unknown_action_is_refused_and_nothing_is_stored(
    a_real_action_catalogue, stored_workflows,
) -> None:
    """[REQ-SB-95-US-04-AC-02] The refusal reaches the client naming
    WHICH step and WHICH unknown action id -- the Manager's own
    sentence, not a flattened "Bad Request" -- and the Workflow is in
    neither the store nor the catalogue afterwards.

    The step is named by POSITION because that is what the operator is
    looking at in an ordered editor, and a step that was never saved has
    no id they have ever seen."""
    refused = client.post("/workflows", json={
        **A_DOCUMENTED_WORKFLOW,
        "steps": [
            _three_ordered_steps()[0],
            {"id": "send", "action_id": AN_ACTION_NO_INSTALL_HAS, "needs_confirmation": True},
            _three_ordered_steps()[2],
        ],
    })

    assert 400 <= refused.status_code < 500
    detail = refused.json()["detail"]
    # A plain-string detail, not FastAPI's own list-of-errors shape --
    # one body shape for every refusal this router returns.
    assert isinstance(detail, str)
    assert "step 2" in detail
    assert AN_ACTION_NO_INSTALL_HAS in detail
    assert "nothing was saved" in detail

    assert client.get("/workflows").json() == []
    assert client.get("/workflows/mail-me-the-team-list").status_code == 404
    assert stored_workflows == {}


def test_a_step_naming_no_action_at_all_is_refused_the_same_way(
    a_real_action_catalogue, stored_workflows,
) -> None:
    """[REQ-SB-95-US-04-AC-02] An empty action id leaves a step pointing
    at nothing exactly as an unknown one does, so it is one refusal with
    one status and one body shape -- never FastAPI's own 422, whose
    `detail` is a list of error objects the screen would have to tell
    apart from this one before it could show the operator anything."""
    refused = client.post("/workflows", json={
        "id": "half-written", "steps": [{"description": "I have not picked an Action yet"}],
    })

    assert 400 <= refused.status_code < 500
    assert isinstance(refused.json()["detail"], str)
    assert "step 1" in refused.json()["detail"]
    assert stored_workflows == {}


def test_an_edit_pointing_a_step_at_an_unknown_action_leaves_the_workflow_unchanged(
    a_real_action_catalogue, stored_workflows,
) -> None:
    """[REQ-SB-95-US-04-AC-02] "an existing Workflow updated the same way
    is left unchanged on disk" -- over HTTP. The refusal names the step
    and the unknown id, and the stored definition is byte-for-byte what
    it was before the refused edit, not a partially-applied one that
    kept the new description."""
    client.post("/workflows", json=A_DOCUMENTED_WORKFLOW)
    before_on_disk = dict(stored_workflows["mail-me-the-team-list"])
    before_over_http = client.get("/workflows/mail-me-the-team-list").json()

    refused = client.put("/workflows/mail-me-the-team-list", json={
        "description": "an edit that must not land",
        "steps": [
            _three_ordered_steps()[0],
            {"id": "send", "action_id": AN_ACTION_NO_INSTALL_HAS},
            _three_ordered_steps()[2],
        ],
    })

    assert 400 <= refused.status_code < 500
    detail = refused.json()["detail"]
    assert "step 2" in detail
    assert AN_ACTION_NO_INSTALL_HAS in detail

    assert stored_workflows["mail-me-the-team-list"] == before_on_disk
    assert client.get("/workflows/mail-me-the-team-list").json() == before_over_http
