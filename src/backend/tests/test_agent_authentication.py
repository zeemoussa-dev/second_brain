"""How a Hermes worker proves which agent it is, and what that does and
does not let it do (`REQ-SB-103`, `ADR-062`).

**This file undoes `conftest.py`'s sign-in fixture, and it has to.**
That fixture patches `_AuthenticationReader.identity_for` to return a
synthetic Admin for every request in the suite, which is the right
default for 800 tests that are not about authentication -- and it means
a guard could be completely broken and every one of them would still
pass. `ESC-081` was exactly that shape: 14 green tests covering
behaviour impossible on a real install. So the real reader is restored
here, captured at import time before any fixture has touched the class.

The user store is moved onto `tmp_path` per test, so the accounts and
credentials below are this test's own and nothing reads or writes the
operator's.
"""
import pytest
from fastapi.testclient import TestClient

import app.api.auth_guard as auth_guard
import app.main as main_app
from app.business.core.users.agent_token import TOKEN_PREFIX
from app.business.core.users.agent_token_manager import AgentTokenManager
from app.business.core.users.user import Role
from app.business.core.users.user_manager import UserManager
from app.config import settings

# Captured at import, which happens at collection -- before conftest's
# autouse fixture replaces it. Taking it later would capture the stub.
THE_REAL_READER = auth_guard._AuthenticationReader.identity_for

client = TestClient(main_app.app)

THE_AGENT = "the-primary"
ANOTHER_AGENT = "send-email-agent"
A_PASSPHRASE = "a-disposable-passphrase-8842"


@pytest.fixture(autouse=True)
def authentication_is_real(tmp_path, monkeypatch):
    """The shipped guard, against this test's own store."""
    monkeypatch.setattr(auth_guard._AuthenticationReader, "identity_for", THE_REAL_READER)
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path)
    UserManager().initialise()


@pytest.fixture
def an_admin() -> dict:
    users = UserManager()
    user = users.create_user("the-operator", A_PASSPHRASE, Role.ADMIN, "The Operator")
    return {"user": user}


@pytest.fixture
def a_token(an_admin) -> str:
    _, token_text = AgentTokenManager().mint(THE_AGENT, "the WhatsApp worker", "the-operator")
    return token_text


def as_agent(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_a_worker_with_no_credential_is_refused_everywhere(an_admin) -> None:
    """[REQ-SB-103] The state this requirement found: `call_action.py`
    sent no credential at all, so every Hermes worker call to an install
    with an account answered 401 -- the Action gate and the Workflow
    runner included."""
    for method, path in (
        ("GET", "/workflows"),
        ("POST", "/actions/anything/call"),
        ("POST", "/workflows/anything/run"),
    ):
        answered = client.request(method, path, json={"caller_agent_id": THE_AGENT, "inputs": {}})
        assert answered.status_code == 401, f"{method} {path} -> {answered.status_code}"
        assert answered.json()["reason"] == "not_authenticated"


def test_a_credential_gets_a_worker_in_and_never_makes_it_a_person(a_token) -> None:
    """[REQ-SB-103] The whole design in one test. The token authenticates
    the agent, and `request.state.identity` stays None -- so a worker
    reads what this install knows and is refused by every route that
    needs a capability, because a capability is about a person."""
    reading = client.get("/workflows", headers=as_agent(a_token))
    assert reading.status_code == 200, reading.text

    # A route behind `requires()`. An agent has no role to check, so it
    # is refused as "not signed in" rather than mapped onto some default.
    for path in ("/admin/users", "/admin/agent-tokens"):
        refused = client.get(path, headers=as_agent(a_token))
        assert refused.status_code == 401, f"{path} -> {refused.status_code}"


def test_an_agent_may_not_write_outside_the_routes_it_is_for(a_token) -> None:
    """[REQ-SB-103] Reads are open to a worker; writes are an explicit
    list. These are the ones that would hurt most, and each is refused
    for its own reason rather than by accident of path shape."""
    authoring = client.post(
        "/actions", json={"id": "invented-by-a-worker", "description": "x",
                          "implementation": {"ui": {"feature_key": "/settings/actions"}}},
        headers=as_agent(a_token),
    )
    assert authoring.status_code == 403, authoring.text
    assert authoring.json()["reason"] == "not_for_agents"

    # Confirming its own pending Action call would be the gate undone.
    confirming = client.post("/actions/calls/anything/confirm", headers=as_agent(a_token))
    assert confirming.status_code == 403, confirming.text
    assert confirming.json()["reason"] == "not_for_agents"

    authoring_a_workflow = client.put(
        "/workflows/anything", json={"description": "x"}, headers=as_agent(a_token),
    )
    assert authoring_a_workflow.status_code == 403, authoring_a_workflow.text


def test_the_authoring_routes_are_refused_by_the_agent_rule_not_by_a_capability(
    a_token,
) -> None:
    """[REQ-SB-103] Why the agent write list names routes and not
    prefixes. `POST /actions` and `PUT /actions/{id}` carry NO
    `requires()` today, so nothing below the middleware would have
    stopped a worker from authoring the very catalogue that bounds it --
    a `/actions/` prefix would have handed it exactly that. This pins
    the reason, so the day someone widens the list the cost is visible.
    """
    from app.api import actions_router

    unguarded = [
        route for route in actions_router.router.routes
        if getattr(route, "path", "") in ("/actions", "/actions/{action_id}")
        and {"POST", "PUT", "DELETE"} & set(getattr(route, "methods", ()))
        and not route.dependencies
    ]
    assert unguarded, (
        "if these routes have since been given a capability guard, this test's premise is gone "
        "and the agent write list can be re-read in that light -- but do not widen it silently"
    )
    assert not auth_guard._an_agent_may_write_here("/actions")
    assert not auth_guard._an_agent_may_write_here("/actions/some-action")
    assert auth_guard._an_agent_may_write_here("/actions/some-action/call")


def test_a_worker_cannot_act_as_a_different_agent(a_token) -> None:
    """[REQ-SB-103] `ADR-033` authorises against `caller_agent_id`, and
    until now the app believed whatever id it was given. A token bound
    to one agent closes that: a body naming another is refused, not
    silently corrected -- a caller that asked to be somebody else has
    either a bug or an intention, and quietly doing something else
    hides both."""
    refused = client.post(
        "/workflows/anything/run",
        json={"caller_agent_id": ANOTHER_AGENT},
        headers=as_agent(a_token),
    )
    assert refused.status_code == 403, refused.text
    assert ANOTHER_AGENT in refused.json()["detail"]
    assert THE_AGENT in refused.json()["detail"]


def test_a_revoked_credential_stops_working_and_stays_on_the_record(a_token, an_admin) -> None:
    """[REQ-SB-103] Revocation is dated, not deleted: after a key has
    leaked, "was it revoked, and when" is the question that matters."""
    assert client.get("/workflows", headers=as_agent(a_token)).status_code == 200

    tokens = AgentTokenManager()
    [issued] = tokens.get_all()
    tokens.revoke(issued.token_sha256)

    assert client.get("/workflows", headers=as_agent(a_token)).status_code == 401
    [still_listed] = tokens.get_all()
    assert still_listed.is_revoked
    assert still_listed.revoked_at


def test_the_token_text_is_stored_nowhere(a_token) -> None:
    """[REQ-SB-103] Only the digest is kept, so the store cannot leak a
    working credential even to someone who can read it."""
    assert a_token.startswith(TOKEN_PREFIX)
    [issued] = AgentTokenManager().get_all()
    assert issued.token_sha256 != a_token
    assert a_token not in str(issued)

    raw = (settings.second_brain_data_path / "auth" / "users.db").read_bytes()
    assert a_token.encode() not in raw, "the plaintext reached the database file"


def test_an_unused_credential_says_so_and_a_used_one_says_when(a_token) -> None:
    """[REQ-SB-103] A key issued and never used usually means it never
    reached the worker, which looks identical to "the agent is quiet"
    unless the app says which."""
    [before] = AgentTokenManager().get_all()
    assert before.has_ever_been_used is False

    client.get("/workflows", headers=as_agent(a_token))

    [after] = AgentTokenManager().get_all()
    assert after.has_ever_been_used is True
    assert after.last_seen_at


def test_a_token_that_was_never_issued_is_refused_like_any_other(an_admin) -> None:
    """[REQ-SB-103] An unknown token, a revoked one and a value that is
    not an agent token are one answer on purpose: telling a caller which
    it was is telling an attacker whether a guessed key exists."""
    for pretend in (f"{TOKEN_PREFIX}not-a-real-one", "bearer-shaped-nonsense", ""):
        refused = client.get("/workflows", headers={"Authorization": f"Bearer {pretend}"})
        assert refused.status_code == 401
        assert refused.json()["reason"] == "not_authenticated"


# ---------------------------------------------------------------------
# What a relayed answer is attributed to (`REQ-SB-103`). The point of
# the whole credential: an agent reaches the answer route and still
# cannot approve anything of its own.


A_CHAT = "a-chat-this-test-invented@lid"
A_GROUP = "a-group-this-test-invented@g.us"


@pytest.fixture
def a_waiting_question(a_token, an_admin, tmp_path, monkeypatch) -> dict:
    """One run, held at a question, through a door this test declares."""
    monkeypatch.setattr(
        "app.data_access.workflow_runs._workflow_runs_root", lambda: tmp_path / "WorkflowRuns",
    )
    stored: dict = {}
    monkeypatch.setattr(
        "app.business.core.workflows.workflow_manager.workflows_data.write_workflow_json",
        lambda workflow_id, data: stored.update({workflow_id: data}),
    )

    def read(workflow_id: str) -> dict:
        if workflow_id not in stored:
            raise FileNotFoundError(workflow_id)
        return stored[workflow_id]

    monkeypatch.setattr(
        "app.business.core.workflows.workflow_manager.workflows_data.read_workflow_json", read,
    )
    monkeypatch.setattr(
        "app.business.core.workflows.workflow_manager.workflows_data.list_workflow_ids",
        lambda: sorted(stored),
    )

    from app.business.core.workflows.workflow_manager import WorkflowManager

    WorkflowManager().create(
        "ask-me-first",
        request_kind="ask me before you send",
        steps=[{"id": "ok", "kind": "human", "ask": "Shall I send it?", "allows_edit": False}],
    )
    started = client.post(
        "/workflows/ask-me-first/run",
        json={"caller_agent_id": THE_AGENT,
              "entry_point": {"source": "whatsapp", "chat_id": A_CHAT}},
        headers=as_agent(a_token),
    )
    assert started.status_code == 200, started.text
    run_id = started.json()["run_id"]
    assert client.post(
        f"/workflows/runs/{run_id}/next-step", headers=as_agent(a_token),
    ).status_code == 200
    return {"run_id": run_id, "owner_id": an_admin["user"].id}


def declare_the_door(monkeypatch, owner_user_id: str, chat_id: str = A_CHAT) -> None:
    monkeypatch.setattr(
        "app.data_access.entry_points.read_entry_points",
        lambda: [{"label": "a door", "source": "whatsapp", "chat_id": chat_id,
                  "agent_id": THE_AGENT, "owner_user_id": owner_user_id}],
    )


def test_a_relayed_answer_is_attributed_to_the_owner_of_the_door(
    a_token, a_waiting_question, monkeypatch,
) -> None:
    """[REQ-SB-103] The agent names the DOOR; the app resolves the
    person. And the record says `relayed`, not `in_person`: "an agent
    says the owner of this number approved it" is weaker evidence than
    "they clicked it here", and a record that read the same for both
    would be the fabricated certainty this requirement exists against.
    """
    declare_the_door(monkeypatch, a_waiting_question["owner_id"])

    answered = client.post(
        f"/workflows/runs/{a_waiting_question['run_id']}/steps/ok/answer",
        json={"decision": "approved", "said": "yes go ahead",
              "entry_point": {"source": "whatsapp", "chat_id": A_CHAT}},
        headers=as_agent(a_token),
    )

    assert answered.status_code == 200, answered.text
    decided_by = answered.json()["steps"][0]["decided_by"]
    assert decided_by["user_id"] == a_waiting_question["owner_id"]
    assert decided_by["how"] == "relayed"
    assert decided_by["relayed_by_agent"] == THE_AGENT
    assert answered.json()["steps"][0]["human_said"] == "yes go ahead"


def test_an_agent_cannot_name_the_person_itself(
    a_token, a_waiting_question, monkeypatch,
) -> None:
    """[REQ-SB-103] The asymmetry that makes the whole thing worth
    anything: a worker that could put a name in the field could put ANY
    name in the field. `decided_by` is not a field a caller can send --
    a body carrying one changes nothing, and the app still resolves the
    person from its own declarations."""
    declare_the_door(monkeypatch, a_waiting_question["owner_id"])

    answered = client.post(
        f"/workflows/runs/{a_waiting_question['run_id']}/steps/ok/answer",
        json={"decision": "approved", "said": "yes",
              "decided_by": {"user_id": "somebody-else", "display_name": "The Chairman"},
              "entry_point": {"source": "whatsapp", "chat_id": A_CHAT}},
        headers=as_agent(a_token),
    )

    assert answered.status_code == 200, answered.text
    decided_by = answered.json()["steps"][0]["decided_by"]
    assert decided_by["user_id"] == a_waiting_question["owner_id"]
    assert decided_by["display_name"] != "The Chairman"


def test_an_answer_through_a_door_nobody_owns_is_refused(
    a_token, a_waiting_question, monkeypatch,
) -> None:
    """[REQ-SB-103] An unattributable approval reads as authority it
    never had, which is worse than no approval at all. The run stays
    holding, and the question is still answerable in the app by a
    person -- which is why it is on everybody's "Waiting on You"."""
    monkeypatch.setattr("app.data_access.entry_points.read_entry_points", lambda: [])

    refused = client.post(
        f"/workflows/runs/{a_waiting_question['run_id']}/steps/ok/answer",
        json={"decision": "approved", "said": "yes",
              "entry_point": {"source": "whatsapp", "chat_id": A_CHAT}},
        headers=as_agent(a_token),
    )

    assert refused.status_code == 409, refused.text
    assert "nobody declared as the owner" in refused.json()["detail"]

    standing = client.post(
        f"/workflows/runs/{a_waiting_question['run_id']}/next-step", headers=as_agent(a_token),
    ).json()
    assert standing["status"] == "awaiting_person", "the question is still waiting"


def test_an_agent_that_names_no_door_is_refused(a_token, a_waiting_question) -> None:
    """[REQ-SB-103] Without a door there is no person, and defaulting to
    anybody is the thing this route exists not to do."""
    refused = client.post(
        f"/workflows/runs/{a_waiting_question['run_id']}/steps/ok/answer",
        json={"decision": "approved", "said": "yes"},
        headers=as_agent(a_token),
    )

    assert refused.status_code == 400, refused.text
    assert "which door it came through" in refused.json()["detail"]


def test_in_a_group_the_sender_is_who_answered_not_the_group(
    a_token, a_waiting_question, monkeypatch,
) -> None:
    """[REQ-SB-103] The operator's own framing -- the link is per
    SENDER. A group chat belongs to whoever was declared for the group,
    and attributing a group member's answer to that person would put
    one person's name on another's decision."""
    someone_else = UserManager().create_user(
        "the-colleague", A_PASSPHRASE, Role.POWER_USER, "The Colleague",
    )
    monkeypatch.setattr(
        "app.data_access.entry_points.read_entry_points",
        lambda: [
            {"source": "whatsapp", "chat_id": A_GROUP, "agent_id": THE_AGENT,
             "owner_user_id": a_waiting_question["owner_id"]},
            {"source": "whatsapp", "chat_id": "the-colleagues-number",
             "agent_id": THE_AGENT, "owner_user_id": someone_else.id},
        ],
    )

    answered = client.post(
        f"/workflows/runs/{a_waiting_question['run_id']}/steps/ok/answer",
        json={"decision": "approved", "said": "yes from me",
              "entry_point": {"source": "whatsapp", "chat_id": A_GROUP,
                              "sender_id": "the-colleagues-number"}},
        headers=as_agent(a_token),
    )

    assert answered.status_code == 200, answered.text
    decided_by = answered.json()["steps"][0]["decided_by"]
    assert decided_by["user_id"] == someone_else.id, (
        "the group's owner answered for somebody who did not speak"
    )
    assert decided_by["sender_id"] == "the-colleagues-number"


def test_a_person_answering_here_is_recorded_as_having_done_it_here(
    a_waiting_question,
) -> None:
    """[REQ-SB-103] The other half of the distinction. A signed-in
    person is `in_person`, from their session, and a door they typed
    into the body is ignored -- being signed in IS the evidence of who
    they are, and honouring a body field would be a way to answer as
    somebody else."""
    signed_in = client.post(
        "/auth/sign-in", json={"username": "the-operator", "password": A_PASSPHRASE},
    )
    assert signed_in.status_code == 200, signed_in.text

    answered = client.post(
        f"/workflows/runs/{a_waiting_question['run_id']}/steps/ok/answer",
        json={"decision": "declined", "said": "not today",
              "entry_point": {"source": "whatsapp", "chat_id": "a-door-i-do-not-own"}},
    )

    assert answered.status_code == 200, answered.text
    decided_by = answered.json()["steps"][0]["decided_by"]
    assert decided_by["how"] == "in_person"
    assert decided_by["username"] == "the-operator"
    assert "relayed_by_agent" not in decided_by
    client.cookies.clear()
