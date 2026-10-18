"""Dispatch by implementation kind (REQ-SB-95-US-03-T03, `ADR-033`):
`http` performed, `ui` pointed at, `skill` authorised by a single-use
grant.

Driven through the real `app.main.app` with `TestClient` -- which is
`httpx.ASGITransport(app=app)` behind a sync wrapper -- the same shape
`test_action_invocation_gate.py` uses, so these tests exercise the real
route, the real gate and the real dispatch rather than a reconstruction
of them.

**The `http` path really performs a route, so what it performs matters.**
It is pointed at a test-only route registered on the app by this file
(the technique `test_error_surfacing.py` already uses), never at a real
one: dispatching at, say, `POST /vault-index/refresh` would re-read the
whole of the operator's vault every time this file ran. The target
records what it was entered with and returns a real result, so "the app
really performed it" is checkable rather than inferred from a status
code.

**All three kinds are exercised end to end through
`POST /actions/{id}/call`**, so what is proved is the shipped path an
agent really takes. The two cases that must not reach a route at all --
an Action naming the call gate's own route, and an operation that fails
behind one -- drive `_perform_http_implementation()` directly, because
what they assert is what the performer decides before and after the
request, not what the gate does with it.

**Nothing here may reach a real write, a real subprocess or a real
outbound call.** Four things are isolated and nothing else:

- the Action store, in memory;
- the Action-call ledger's own root and its `_claims/` subdirectory,
  onto `tmp_path`, so the REAL writer runs against real files in a
  directory pytest throws away;
- the three resolution sources, because what is deployed, routed and
  registered on the machine running the suite is instance state;
- `subprocess`, in the `skill` tests, which must prove the app
  AUTHORISES rather than performs -- an assertion that nothing ran is
  worth little if a subprocess could have run unnoticed.

The `http` dispatch opens no socket at all: `ASGITransport` hands the
request to the application object in process, so no test here can reach
the operator's backend on :8001 even if one is running.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel

import app.main as main_app
from app.business.core.actions.action import Action, ActionImplementation, ActionInput
from app.business.logic import action_invocation

THIS_MODULE = sys.modules[__name__]

A_DEPLOYED_SKILL = "email-thread-capture"
A_REAL_FEATURE_KEY = "/settings/artifacts"
THE_CALLER = "cbo-agent"

THE_TARGET_ROUTE = ("POST", "/__test_action_target/{folder}")

_entered_with: list[dict] = []


class _TargetBody(BaseModel):
    note: str
    urgent: bool = False


def _the_real_operation(folder: str, note: str, urgent: bool) -> dict:
    """The thing an `http` Action actually causes to happen. Reached
    only through the real route, so recording an entry here means the
    app went all the way through its own stack -- and a scoped
    monkeypatch over this one name is what the failure test uses to
    break the operation without breaking the route."""
    _entered_with.append({"folder": folder, "note": note, "urgent": urgent})
    return {"filed": f"{folder}/{note}", "urgent": urgent}


_router = APIRouter()


@_router.post("/__test_action_target/{folder}")
def _perform_the_target(folder: str, body: _TargetBody) -> dict:
    return _the_real_operation(folder, body.note, body.urgent)


# A second target, shared with `tests/test_action_invocation_gate.py`,
# which imports this module for the side effect of registering it
# (`ESC-073`). That file's Action pointed at the REAL
# `POST /vault-index/refresh` while dispatch performed nothing; the
# moment it did, every run of the suite re-read the operator's whole
# vault -- 1.09s to 8.60s for that one file. It declares inputs of its
# own and only needs somewhere harmless to land, so this target accepts
# any of them and echoes them back as a real result.
THE_ANY_INPUTS_TARGET_ROUTE = ("POST", "/__test_action_target_any_inputs")


@_router.post("/__test_action_target_any_inputs")
def _accept_any_inputs(body: dict) -> dict:
    return {"accepted_inputs": body}


main_app.app.include_router(_router)
client = TestClient(main_app.app)


@pytest.fixture(autouse=True)
def nothing_is_remembered_between_tests():
    _entered_with.clear()
    yield
    _entered_with.clear()


@pytest.fixture
def resolvable(monkeypatch):
    """The live sources, replaced by ones this test controls -- the same
    three `test_action_invocation_gate.py` replaces, for the same
    reason."""
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
    the real writer, the real file naming, the real mkdir AND the real
    `_claims/` exclusivity are exercised -- a single-use grant that was
    only single-use because a fake store said so would prove nothing."""
    root = tmp_path / "ActionCalls"
    monkeypatch.setattr("app.data_access.action_calls._action_calls_root", lambda: root)
    return root


@pytest.fixture
def no_subprocess_may_run(monkeypatch):
    """`skill` is AUTHORISED, never performed (`ADR-019`, `ADR-033`).
    Asserting that no Skill ran is weak unless running one is made
    impossible, so every way this process could start one raises."""
    def refuse(*args, **kwargs):
        raise AssertionError(f"a subprocess was started during dispatch: {args!r}")

    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, refuse)
    monkeypatch.setattr(os, "system", refuse)


def skill_catalog_modules_loaded() -> set[str]:
    """Which `skills/catalog/` payload modules are in `sys.modules`.
    `ADR-019` says the app never imports any; this is how that is
    checked rather than asserted."""
    marker = os.path.join("skills", "catalog")
    return {
        name for name, module in list(sys.modules.items())
        if marker in (getattr(module, "__file__", "") or "")
    }


def ledger_records(root: Path) -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(root.glob("*.json"))]


def the_one_record(root: Path) -> dict:
    records = ledger_records(root)
    assert len(records) == 1, records
    return records[0]


def call(action_id: str, caller_agent_id: str = THE_CALLER, **inputs):
    return client.post(
        f"/actions/{action_id}/call",
        json={"caller_agent_id": caller_agent_id, "inputs": inputs},
    )


def accepted_verdict(response) -> dict:
    """2xx means the gate was passed; the verdict is the whole body."""
    assert response.status_code == 200, response.text
    verdict = response.json()
    assert verdict["accepted"] is True, verdict
    return verdict


AN_HTTP_ACTION = {
    "id": "file-the-note",
    "description": "File a note into a folder",
    "inputs": [
        {"name": "folder", "type": "string", "required": True, "description": "which folder"},
        {"name": "note", "type": "string", "required": True, "description": "the note"},
        {"name": "urgent", "type": "boolean", "required": False, "description": ""},
    ],
    "allowed_callers": [THE_CALLER],
    "needs_confirmation": False,
    "implementation": {"http": {"method": "POST", "path": "/__test_action_target/{folder}"}},
}

A_SKILL_ACTION = {
    "id": "capture-the-thread",
    "description": "Capture an email thread into the vault",
    "inputs": [
        {"name": "thread_id", "type": "string", "required": True, "description": "which thread"},
    ],
    "allowed_callers": [THE_CALLER],
    "needs_confirmation": False,
    "implementation": {"skill": {"skill_id": A_DEPLOYED_SKILL}},
}

A_UI_ACTION = {
    "id": "export-the-artifacts",
    "description": "Export this install's artifacts",
    "inputs": [
        {"name": "kind", "type": "string", "required": False, "description": "which kind"},
    ],
    "allowed_callers": [THE_CALLER],
    "needs_confirmation": False,
    "implementation": {"ui": {"feature_key": A_REAL_FEATURE_KEY}},
}


def the_http_action() -> Action:
    return Action(
        id="file-the-note",
        inputs=[ActionInput(name=entry["name"], required=entry["required"])
                for entry in AN_HTTP_ACTION["inputs"]],
        allowed_callers=[THE_CALLER],
        implementation=ActionImplementation(
            kind="http", method="POST", path="/__test_action_target/{folder}",
        ),
    )


def test_an_http_implementation_is_really_performed_by_the_app_and_reported_performed(
    resolvable, stored_actions, ledger,
) -> None:
    """[REQ-SB-95-US-03-AC-02] The app performs what it owns, through
    the one door an agent really calls. The target function is entered
    with the VALIDATED inputs -- the input the route declares as a path
    parameter bound into the path, the rest in the body -- and what the
    caller gets back, and what the ledger keeps, is the route's real
    result rather than a description of it.
    """
    client.post("/actions", json=AN_HTTP_ACTION)

    verdict = accepted_verdict(
        call("file-the-note", folder="Projects", note="kickoff", urgent=True),
    )

    assert _entered_with == [{"folder": "Projects", "note": "kickoff", "urgent": True}]
    assert verdict["outcome"] == "performed"
    assert verdict["result"] == {"filed": "Projects/kickoff", "urgent": True}
    assert "POST /__test_action_target/{folder}" in verdict["detail"]
    assert verdict["grant"] is None
    assert verdict["where_the_operator_does_it"] is None

    record = the_one_record(ledger)
    assert record["call_id"] == verdict["call_id"]
    assert record["outcome"] == "performed"
    assert record["inputs"] == {"folder": "Projects", "note": "kickoff", "urgent": True}
    assert record["result"] == {"filed": "Projects/kickoff", "urgent": True}


def test_an_http_implementation_naming_the_call_gate_itself_is_refused_not_recursed() -> None:
    """[REQ-SB-95-US-03-AC-02] The gate's own route is on the live route
    table, so an `http` Action may legally be saved pointing at it.
    Dispatching that would re-enter the gate without end -- a fresh
    event loop and worker thread each time -- so it is reported as a
    failure instead, and nothing is performed."""
    refused = action_invocation._perform_http_implementation(
        the_http_action(), "POST", "/actions/{action_id}/call", {"action_id": "file-the-note"},
    )

    assert refused["outcome"] == "failed"
    assert refused["outcome"] != "performed"
    assert "inside the gate" in refused["detail"]
    assert _entered_with == []


def test_a_skill_implementation_is_authorised_by_a_grant_and_never_performed_here(
    resolvable, stored_actions, ledger, no_subprocess_may_run,
) -> None:
    """[REQ-SB-95-US-03-AC-02] The app does not perform what it does not
    own. The answer is a single-use grant naming the deployed Skill and
    the validated inputs; nothing under `skills/catalog/` is imported,
    no subprocess runs, and the ledger records an authorisation -- a
    word that cannot be read as `performed`."""
    catalog_modules_before = skill_catalog_modules_loaded()
    client.post("/actions", json=A_SKILL_ACTION)

    verdict = accepted_verdict(call("capture-the-thread", thread_id="AAMk-0042"))

    assert verdict["outcome"] == "authorised"
    assert verdict["outcome"] != "performed"
    assert verdict["result"] is None
    assert verdict["grant"] == {
        "skill_id": A_DEPLOYED_SKILL,
        "caller_agent_id": THE_CALLER,
        "inputs": {"thread_id": "AAMk-0042"},
        "granted_at": verdict["grant"]["granted_at"],
        "call_id": verdict["call_id"],
        "single_use": True,
    }

    # Newly imported DURING the dispatch is the checkable claim, not
    # "none are loaded at all": another test file legitimately imports a
    # payload script by path to test it, and `sys.modules` is shared
    # across the whole run. What `ADR-019` forbids is the APP importing
    # one, which is what this difference measures.
    assert skill_catalog_modules_loaded() == catalog_modules_before

    record = the_one_record(ledger)
    assert record["outcome"] == "authorised"
    assert record["grant"]["skill_id"] == A_DEPLOYED_SKILL
    assert record["grant"]["inputs"] == {"thread_id": "AAMk-0042"}
    assert record["grant"]["single_use"] is True
    assert record["result"] is None


def test_a_grant_is_consumed_exactly_once_and_the_second_attempt_is_refused(
    resolvable, stored_actions, ledger, no_subprocess_may_run,
) -> None:
    """[REQ-SB-95-US-03-AC-02] Single-use means single-use. The first
    consumption hands back what was granted; the second is refused in
    words that say so, and cannot be mistaken for a success."""
    client.post("/actions", json=A_SKILL_ACTION)
    verdict = accepted_verdict(call("capture-the-thread", thread_id="AAMk-0042"))
    call_id = verdict["call_id"]

    first = action_invocation.consume_single_use_grant(
        call_id, reported_outcome="performed", reported_detail="the runner ran the skill",
    )

    assert first.consumed is True
    assert first.refusal is None
    assert first.grant["skill_id"] == A_DEPLOYED_SKILL
    assert first.grant["inputs"] == {"thread_id": "AAMk-0042"}

    second = action_invocation.consume_single_use_grant(call_id)

    assert second.consumed is False
    assert "already been consumed" in second.refusal
    assert second.grant is None

    record = the_one_record(ledger)
    assert record["outcome"] == "performed"
    assert record["detail"] == "the runner ran the skill"
    assert record["grant"]["consumed_at"]


def test_a_grant_that_was_never_minted_cannot_be_consumed(
    resolvable, stored_actions, ledger,
) -> None:
    """[REQ-SB-95-US-03-AC-02] The same mechanism refuses an id it never
    granted anything to, rather than inventing an authorisation -- the
    silent fallback `ADR-032` forbids, one layer down."""
    refused = action_invocation.consume_single_use_grant("never-minted")

    assert refused.consumed is False
    assert "never-minted" in refused.refusal


def test_a_ui_implementation_is_pointed_at_and_never_performed(
    resolvable, stored_actions, ledger,
) -> None:
    """[REQ-SB-95-US-03-AC-02] `ADR-032`'s "point to but not perform".
    Nothing ran, the answer names the screen the operator does it on,
    and the ledger says it was pointed at rather than done."""
    client.post("/actions", json=A_UI_ACTION)

    verdict = accepted_verdict(call("export-the-artifacts", kind="Skill"))

    assert _entered_with == []
    assert verdict["outcome"] == "pointed_at"
    assert verdict["outcome"] != "performed"
    assert verdict["where_the_operator_does_it"] == A_REAL_FEATURE_KEY
    assert A_REAL_FEATURE_KEY in verdict["detail"]
    assert verdict["result"] is None
    assert verdict["grant"] is None

    record = the_one_record(ledger)
    assert record["outcome"] == "pointed_at"
    assert record["result"] is None
    assert record["grant"] is None


def test_a_failure_inside_an_http_dispatch_is_reported_honestly_and_never_performed(
    monkeypatch,
) -> None:
    """[REQ-SB-95-US-03-AC-02] Nothing half-performed. The route is
    reached for real and the operation behind it fails; what comes back
    is a failure naming the status and saying the operation did not
    happen, never `performed`, and the error body is not passed off as
    a result."""
    def the_operation_fails(folder: str, note: str, urgent: bool) -> dict:
        raise RuntimeError("the disk is full")

    monkeypatch.setattr(THIS_MODULE, "_the_real_operation", the_operation_fails)

    failed = action_invocation._perform_http_implementation(
        the_http_action(), "POST", "/__test_action_target/{folder}",
        {"folder": "Projects", "note": "kickoff"},
    )

    assert _entered_with == []
    assert failed["outcome"] == "failed"
    assert failed["outcome"] != "performed"
    assert "did NOT happen" in failed["detail"]
    assert "500" in failed["detail"]
