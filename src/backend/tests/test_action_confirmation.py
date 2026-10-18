"""Confirmation-required Actions (REQ-SB-95-US-03-T04, `ADR-033`):
`awaiting_confirmation`, the operator's confirm/decline surface, and the
single-use grant a re-call spends exactly once.

Driven through the real `app.main.app` with `TestClient` -- which is
`httpx.ASGITransport(app=app)` behind a sync wrapper -- the same shape
`test_action_invocation_gate.py` and `test_action_dispatch.py` use, so
what is proved here is the shipped route, the shipped gate and the
shipped dispatch rather than a reconstruction of them.

**"Nothing is performed" is measured three ways, not asserted once.**
A first call must perform no part of the operation, and a test that
only checked the response would pass while the operation happened:

- the dispatch seam is spied AROUND, not replaced, and counted;
- the `http` Action points at `test_action_dispatch`'s test-only target
  route, which records every entry into the real operation behind it,
  so "it did not run" is a measured empty list;
- `subprocess` and `os.system` raise, so a `skill` Action cannot have
  been quietly performed by this process either.

The target route is imported from `test_action_dispatch` for the side
effect of registering it, the way `test_action_invocation_gate.py`
already does. It is never a real route: an Action pointed at a real one
really runs it now, and the last file to forget that re-read the
operator's whole vault on every run of the suite (`ESC-073`).

**Nothing here may reach a real write.** Three things are isolated and
nothing else: the Action store (in memory), the Action-call ledger's own
root and its `_claims/` subdirectory (onto `tmp_path`, so the REAL
writer and the REAL exclusive-create primitive run against real files in
a directory pytest throws away), and the three resolution sources, which
are instance state. Hermes is sandboxed suite-wide by `conftest.py`.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main_app
from app.business.logic import action_invocation
from tests import test_action_dispatch

client = TestClient(main_app.app)

A_DEPLOYED_SKILL = "email-thread-capture"
A_REAL_FEATURE_KEY = "/settings/artifacts"
THE_CALLER = "cbo-agent"
ANOTHER_CALLER = "research-hub"

THE_TARGET_ROUTE = test_action_dispatch.THE_TARGET_ROUTE


@pytest.fixture(autouse=True)
def nothing_is_remembered_between_tests():
    """`test_action_dispatch`'s record of what its target route really
    performed, cleared around each test here too -- its own autouse
    fixture does not reach this module."""
    test_action_dispatch._entered_with.clear()
    yield
    test_action_dispatch._entered_with.clear()


def really_performed() -> list[dict]:
    """Every entry into the real operation behind the target route. The
    one measurement that distinguishes "nothing was performed" from
    "nothing was reported"."""
    return test_action_dispatch._entered_with


@pytest.fixture
def resolvable(monkeypatch):
    """The live sources, replaced by ones this test controls -- the same
    three the sibling Action test files replace, for the same reason."""
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.deployed_skill_ids",
        lambda: {A_DEPLOYED_SKILL},
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.app_route_table",
        lambda: {THE_TARGET_ROUTE},
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.UI_FEATURE_KEYS",
        (A_REAL_FEATURE_KEY,),
    )


@pytest.fixture
def stored_actions(monkeypatch) -> dict:
    """The whole Action store, in memory, keyed by action id."""
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
        "app.business.core.actions.action_manager.actions_data.read_action_json", read,
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
def ledger(tmp_path, monkeypatch) -> Path:
    """The ledger's root, moved onto tmp_path. Patched at the root so
    the real writer, the real file naming and the real `_claims/`
    exclusivity are exercised -- a grant that was only single-use
    because a fake store said so would prove nothing."""
    root = tmp_path / "ActionCalls"
    monkeypatch.setattr("app.data_access.action_calls._action_calls_root", lambda: root)
    return root


@pytest.fixture
def dispatched(monkeypatch) -> list[dict]:
    """A spy AROUND the real dispatch seam, not instead of it: what
    these tests count is how many times dispatch was entered -- zero
    before a confirmation, exactly once after -- while the real seam
    still decides what happens."""
    entries: list[dict] = []
    real_seam = action_invocation.dispatch_validated_action_call

    def spy(action, caller_agent_id, validated_inputs):
        entries.append({"action_id": action.id, "inputs": dict(validated_inputs)})
        return real_seam(action, caller_agent_id, validated_inputs)

    monkeypatch.setattr(
        "app.business.logic.action_invocation.dispatch_validated_action_call", spy,
    )
    return entries


@pytest.fixture
def no_subprocess_may_run(monkeypatch):
    """A `skill` Action must not be performed by this process at all,
    and least of all before it has been confirmed. Asserting that is
    weak unless running one is made impossible."""
    def refuse(*args, **kwargs):
        raise AssertionError(f"a subprocess was started: {args!r}")

    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, refuse)
    monkeypatch.setattr(os, "system", refuse)


A_CONFIRMATION_REQUIRED_HTTP_ACTION = {
    "id": "file-the-note-carefully",
    "description": "File a note into a folder, once the operator says so",
    "inputs": [
        {"name": "folder", "type": "string", "required": True, "description": "which folder"},
        {"name": "note", "type": "string", "required": True, "description": "the note"},
    ],
    "allowed_callers": [THE_CALLER],
    "needs_confirmation": True,
    "implementation": {"http": {"method": THE_TARGET_ROUTE[0], "path": THE_TARGET_ROUTE[1]}},
}

A_CONFIRMATION_REQUIRED_SKILL_ACTION = {
    "id": "capture-the-thread-carefully",
    "description": "Capture an email thread, once the operator says so",
    "inputs": [
        {"name": "thread_id", "type": "string", "required": True, "description": "which thread"},
    ],
    "allowed_callers": [THE_CALLER],
    "needs_confirmation": True,
    "implementation": {"skill": {"skill_id": A_DEPLOYED_SKILL}},
}

A_CONFIRMATION_REQUIRED_UI_ACTION = {
    "id": "export-the-artifacts-carefully",
    "description": "Export this install's artifacts, once the operator says so",
    "inputs": [],
    "allowed_callers": [THE_CALLER],
    "needs_confirmation": True,
    "implementation": {"ui": {"feature_key": A_REAL_FEATURE_KEY}},
}

THE_CONFIRMED_INPUTS = {"folder": "Projects", "note": "kickoff"}


def ledger_records(root: Path) -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(root.glob("*.json"))]


def record_for(root: Path, call_id: str) -> dict:
    return json.loads((root / f"{call_id}.json").read_text(encoding="utf-8"))


def call(action_id: str, confirmed_call_id: str | None = None,
         caller_agent_id: str = THE_CALLER, **inputs):
    return client.post(
        f"/actions/{action_id}/call",
        json={
            "caller_agent_id": caller_agent_id,
            "inputs": inputs,
            "confirmed_call_id": confirmed_call_id,
        },
    )


def refused_verdict(response) -> dict:
    """A gate refusal is one 409 carrying the whole verdict as its
    detail -- `awaiting_confirmation` included, so no caller can read
    "it has not run yet" as a success."""
    assert response.status_code == 409, response.text
    verdict = response.json()["detail"]
    assert verdict["accepted"] is False, verdict
    return verdict


def accepted_verdict(response) -> dict:
    assert response.status_code == 200, response.text
    verdict = response.json()
    assert verdict["accepted"] is True, verdict
    return verdict


def confirm(call_id: str):
    return client.post(f"/actions/calls/{call_id}/confirm")


def decline(call_id: str):
    return client.post(f"/actions/calls/{call_id}/decline")


def pending() -> list[dict]:
    response = client.get("/actions/calls/pending")
    assert response.status_code == 200, response.text
    return response.json()


def test_the_first_call_performs_nothing_and_opens_an_awaiting_confirmation_record(
    resolvable, stored_actions, ledger, dispatched,
) -> None:
    """[REQ-SB-95-US-03-AC-06] Nothing is half-performed. A
    confirmation-required Action is validated in full and then stops:
    the dispatch seam is never entered, the real operation behind its
    route is never run, and what comes back is a refusal carrying the
    `call_id` the operator will decide on -- recorded in the ledger at
    `awaiting_confirmation`, which is neither a refusal nor a success.
    """
    client.post("/actions", json=A_CONFIRMATION_REQUIRED_HTTP_ACTION)

    verdict = refused_verdict(call("file-the-note-carefully", **THE_CONFIRMED_INPUTS))

    assert dispatched == []
    assert really_performed() == []
    assert verdict["outcome"] == "awaiting_confirmation"
    assert verdict["call_id"]
    assert verdict["call_id"] in verdict["refusal"]
    assert "confirmation" in verdict["refusal"]

    records = ledger_records(ledger)
    assert len(records) == 1, records
    assert records[0]["call_id"] == verdict["call_id"]
    assert records[0]["outcome"] == "awaiting_confirmation"
    assert records[0]["inputs"] == THE_CONFIRMED_INPUTS
    assert records[0]["grant"] is None

    # The operator's surface shows it, which is the only way the call
    # can ever be decided on.
    assert [entry["call_id"] for entry in pending()] == [verdict["call_id"]]


def test_confirming_grants_once_and_the_re_call_really_performs_the_operation(
    resolvable, stored_actions, ledger, dispatched,
) -> None:
    """[REQ-SB-95-US-03-AC-06] Confirming performs nothing: it turns the
    record into a single-use grant, and the record stays on the pending
    list so a confirmation nobody acted on cannot read as done. The
    re-call naming that id spends the grant exactly once, enters
    dispatch exactly once, and the real operation behind the route
    really happens with the inputs the operator confirmed.
    """
    client.post("/actions", json=A_CONFIRMATION_REQUIRED_HTTP_ACTION)
    awaiting = refused_verdict(call("file-the-note-carefully", **THE_CONFIRMED_INPUTS))
    call_id = awaiting["call_id"]

    confirmed = confirm(call_id)
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["outcome"] == "confirmed"
    assert confirmed.json()["grant"]["single_use"] is True
    assert confirmed.json()["grant"]["inputs"] == THE_CONFIRMED_INPUTS
    assert dispatched == []
    assert really_performed() == []
    assert [entry["outcome"] for entry in pending()] == ["confirmed"]

    verdict = accepted_verdict(
        call("file-the-note-carefully", confirmed_call_id=call_id, **THE_CONFIRMED_INPUTS),
    )

    assert len(dispatched) == 1, dispatched
    assert really_performed() == [{"folder": "Projects", "note": "kickoff", "urgent": False}]
    assert verdict["outcome"] == "performed"
    assert verdict["granted_by_call_id"] == call_id
    assert verdict["result"] == {"filed": "Projects/kickoff", "urgent": False}

    # Two rows, joined: the operator's decision, and the call that acted
    # on it. The confirmation's grant is marked spent.
    spent = record_for(ledger, call_id)
    assert spent["outcome"] == "confirmed"
    assert spent["grant"]["consumed_at"]
    assert verdict["call_id"] in spent["detail"]

    performed = record_for(ledger, verdict["call_id"])
    assert performed["outcome"] == "performed"
    assert performed["granted_by_call_id"] == call_id

    # Nothing is outstanding any more: the confirmation was spent.
    assert pending() == []


def test_a_consumed_confirmation_cannot_be_consumed_a_second_time(
    resolvable, stored_actions, ledger, dispatched,
) -> None:
    """[REQ-SB-95-US-03-AC-06] Single-use means single-use. The second
    re-call naming the same confirmed id is refused in words that say
    so, the dispatch seam is not entered again, and the operation does
    not happen twice -- which, for an Action the operator was asked
    about precisely because it matters, is the whole point.
    """
    client.post("/actions", json=A_CONFIRMATION_REQUIRED_HTTP_ACTION)
    call_id = refused_verdict(call("file-the-note-carefully", **THE_CONFIRMED_INPUTS))["call_id"]
    confirm(call_id)
    accepted_verdict(
        call("file-the-note-carefully", confirmed_call_id=call_id, **THE_CONFIRMED_INPUTS),
    )

    replayed = refused_verdict(
        call("file-the-note-carefully", confirmed_call_id=call_id, **THE_CONFIRMED_INPUTS),
    )

    assert replayed["outcome"] == "refused:confirmation_not_granted"
    assert "already been consumed" in replayed["refusal"]
    assert len(dispatched) == 1, dispatched
    assert len(really_performed()) == 1, really_performed()


def test_declining_performs_nothing_and_every_later_re_call_is_told_it_was_declined(
    resolvable, stored_actions, ledger, dispatched,
) -> None:
    """[REQ-SB-95-US-03-AC-06] The operator's no is terminal and
    honest. The record says `declined`, nothing is performed, and a
    re-call naming that id is refused with a sentence saying it was
    declined -- so the agent tells the operator the truth instead of
    retrying or describing an outcome that never happened.
    """
    client.post("/actions", json=A_CONFIRMATION_REQUIRED_HTTP_ACTION)
    call_id = refused_verdict(call("file-the-note-carefully", **THE_CONFIRMED_INPUTS))["call_id"]

    declined = decline(call_id)
    assert declined.status_code == 200, declined.text
    assert declined.json()["outcome"] == "declined"
    assert declined.json()["grant"] is None

    assert record_for(ledger, call_id)["outcome"] == "declined"
    assert dispatched == []
    assert really_performed() == []
    assert pending() == []

    refused = refused_verdict(
        call("file-the-note-carefully", confirmed_call_id=call_id, **THE_CONFIRMED_INPUTS),
    )

    assert refused["outcome"] == "refused:confirmation_not_granted"
    assert "declined" in refused["refusal"]
    assert dispatched == []
    assert really_performed() == []
    # Declining is not re-decidable: the record keeps saying no.
    assert confirm(call_id).status_code == 409
    assert record_for(ledger, call_id)["outcome"] == "declined"


@pytest.mark.parametrize(
    "action_definition,action_id",
    [
        (A_CONFIRMATION_REQUIRED_HTTP_ACTION, "file-the-note-carefully"),
        (A_CONFIRMATION_REQUIRED_UI_ACTION, "export-the-artifacts-carefully"),
        (A_CONFIRMATION_REQUIRED_SKILL_ACTION, "capture-the-thread-carefully"),
    ],
)
def test_no_implementation_kind_dispatches_on_the_first_call(
    resolvable, stored_actions, ledger, dispatched, no_subprocess_may_run,
    action_definition, action_id,
) -> None:
    """[REQ-SB-95-US-03-AC-06] Confirmation sits before the dispatch
    seam, not inside one branch of it, so WHICH kind the Action is
    cannot change whether it is honoured. All three stop in the same
    place: nothing performed, nothing pointed at, nothing authorised,
    one `awaiting_confirmation` record and no grant.
    """
    client.post("/actions", json=action_definition)

    inputs = {"folder": "Projects", "note": "kickoff"} if action_id.startswith("file") else (
        {"thread_id": "AAMk-0042"} if action_id.startswith("capture") else {}
    )
    verdict = refused_verdict(call(action_id, **inputs))

    assert verdict["outcome"] == "awaiting_confirmation"
    assert verdict["grant"] is None
    assert verdict["where_the_operator_does_it"] is None
    assert verdict["result"] is None
    assert dispatched == []
    assert really_performed() == []

    records = ledger_records(ledger)
    assert len(records) == 1, records
    assert records[0]["outcome"] == "awaiting_confirmation"
    assert records[0]["grant"] is None


def test_a_confirmation_is_not_transferable_to_a_different_operation(
    resolvable, stored_actions, ledger, dispatched,
) -> None:
    """[REQ-SB-95-US-03-AC-06] The operator confirms one operation, not
    a licence. A re-call that spends a confirmation for different
    inputs, a different Action or a different caller is refused and the
    confirmation is left UNSPENT -- so the thing that was actually
    approved can still be done.
    """
    client.post("/actions", json=A_CONFIRMATION_REQUIRED_HTTP_ACTION)
    client.post("/actions", json=A_CONFIRMATION_REQUIRED_SKILL_ACTION)
    call_id = refused_verdict(call("file-the-note-carefully", **THE_CONFIRMED_INPUTS))["call_id"]
    confirm(call_id)

    swapped_inputs = refused_verdict(
        call("file-the-note-carefully", confirmed_call_id=call_id,
             folder="Everything", note="kickoff"),
    )
    assert "the operator confirmed one operation and this is a different one" in (
        swapped_inputs["refusal"]
    )

    swapped_action = refused_verdict(
        call("capture-the-thread-carefully", confirmed_call_id=call_id, thread_id="AAMk-0042"),
    )
    assert "not transferable" in swapped_action["refusal"]

    assert dispatched == []
    assert really_performed() == []
    # Still spendable by the call it was actually confirmed for.
    assert record_for(ledger, call_id)["grant"].get("consumed_at") is None
    performed = accepted_verdict(
        call("file-the-note-carefully", confirmed_call_id=call_id, **THE_CONFIRMED_INPUTS),
    )
    assert performed["outcome"] == "performed"


def test_an_unminted_or_unconfirmed_id_grants_nothing(
    resolvable, stored_actions, ledger, dispatched,
) -> None:
    """[REQ-SB-95-US-03-AC-06] An id the operator never decided on
    authorises nothing -- neither one that was never minted, nor one
    still awaiting an answer. Nothing is invented in either case, and
    confirming something that does not exist is refused rather than
    created.
    """
    client.post("/actions", json=A_CONFIRMATION_REQUIRED_HTTP_ACTION)

    never_minted = refused_verdict(
        call("file-the-note-carefully", confirmed_call_id="never-minted",
             **THE_CONFIRMED_INPUTS),
    )
    assert never_minted["outcome"] == "refused:confirmation_not_granted"
    assert "never-minted" in never_minted["refusal"]

    awaiting_id = refused_verdict(call("file-the-note-carefully", **THE_CONFIRMED_INPUTS))["call_id"]
    not_yet = refused_verdict(
        call("file-the-note-carefully", confirmed_call_id=awaiting_id, **THE_CONFIRMED_INPUTS),
    )
    assert "still awaiting" in not_yet["refusal"]

    assert dispatched == []
    assert really_performed() == []
    assert confirm("never-minted").status_code == 409
