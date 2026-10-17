"""The validating call gate and the Action-call ledger
(REQ-SB-95-US-03-T02, `ADR-033`).

Driven through the real `app.main.app` with `TestClient` -- which is
`httpx.ASGITransport(app=app)` behind a sync wrapper, and the shape
every other API test here already uses -- so these tests also prove
`POST /actions/{action_id}/call` is really REGISTERED, not merely
importable.

**Nothing here may reach a real write.** Three things are patched and
nothing else:

- the Action store, in memory, so no test touches this install's real
  <DATA_PATH>/data/Actions/;
- the Action-call ledger's own root, onto `tmp_path`, so the REAL
  `data_access/action_calls.py` writer runs and is asserted against real
  files -- in a directory pytest throws away;
- the three resolution sources, because what is deployed, routed and
  registered on the machine running the suite is instance state a test
  must not assert against.

Deliberately NOT patched, and deliberately not reached: anything of
Hermes'. The gate reads the live catalogue (`ADR-033`) and never an
agent's published SOUL text, so no code path here opens a profile --
which is also why this file is safe to run on a real install while
REQ-SB-95-US-03-T01's publication trigger stays unwired (`ESC-072`).
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main_app
from app.business.logic import action_invocation

client = TestClient(main_app.app)

A_DEPLOYED_SKILL = "email-thread-capture"
A_REAL_ROUTE = ("POST", "/vault-index/refresh")
A_REAL_FEATURE_KEY = "/settings/artifacts"

THE_CALLER = "cbo-agent"


@pytest.fixture
def resolvable(monkeypatch):
    """The live sources, replaced by ones this test controls. Returns
    the mutable deployed-skill set so a test can undeploy something
    after a save -- the "implementation stopped resolving" event."""
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
def ledger(tmp_path, monkeypatch) -> Path:
    """The ledger's root, moved onto tmp_path -- the real writer, the
    real JSON, a throwaway directory. Patched at the root rather than at
    `write_call_json` so the file naming and the mkdir are exercised too:
    "a ledger record was written" has to mean a file, not a recorded
    intention."""
    root = tmp_path / "ActionCalls"
    monkeypatch.setattr("app.data_access.action_calls._action_calls_root", lambda: root)
    return root


@pytest.fixture
def dispatched(monkeypatch) -> list[dict]:
    """A spy AROUND the real dispatch seam, not instead of it: a refusal
    test needs to count entries (zero), and the accepted test needs the
    seam's own honest "nothing was performed" outcome to be what the
    ledger records. Replacing the seam outright would let this file pass
    while the shipped gate claimed a performed operation."""
    entries: list[dict] = []
    real_seam = action_invocation.dispatch_validated_action_call

    def spy(action, caller_agent_id, validated_inputs):
        entries.append({
            "action_id": action.id,
            "caller_agent_id": caller_agent_id,
            "inputs": dict(validated_inputs),
        })
        return real_seam(action, caller_agent_id, validated_inputs)

    monkeypatch.setattr(
        "app.business.logic.action_invocation.dispatch_validated_action_call", spy,
    )
    return entries


A_CATALOGUED_ACTION = {
    "id": "refresh-the-index",
    "description": "Rebuild the vault index now",
    "inputs": [
        {"name": "scope", "type": "string", "required": True, "description": "which folder"},
        {"name": "force", "type": "boolean", "required": False, "description": ""},
    ],
    "allowed_callers": [THE_CALLER],
    "needs_confirmation": False,
    "implementation": {"http": {"method": "POST", "path": "/vault-index/refresh"}},
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


def refusal_of(response) -> dict:
    """Every gate refusal is a 409 whose `detail` IS the verdict."""
    assert response.status_code == 409, response.text
    return response.json()["detail"]


def test_an_unknown_action_id_is_refused_naming_it_and_nothing_is_dispatched(
    resolvable, stored_actions, ledger, dispatched,
) -> None:
    """[REQ-SB-95-US-03-AC-03] The refusal comes from the framework
    before any dispatch, names the id the caller invented, and leaves a
    ledger record naming it too -- which is how a missing capability
    gets discovered instead of fabricated."""
    refused = refusal_of(call("does-not-exist"))

    assert refused["accepted"] is False
    assert refused["outcome"] == "refused:unknown_action"
    assert "does-not-exist" in refused["refusal"]
    assert dispatched == []

    record = the_one_record(ledger)
    assert record["call_id"] == refused["call_id"]
    assert record["action_id"] == "does-not-exist"
    assert record["caller_agent_id"] == THE_CALLER
    assert record["outcome"] == "refused:unknown_action"
    assert "does-not-exist" in record["refusal"]


def test_a_missing_required_input_is_refused_by_name_with_nothing_substituted(
    resolvable, stored_actions, ledger, dispatched,
) -> None:
    """[REQ-SB-95-US-03-AC-04] Ask rather than guess. The refusal names
    the input, and the recorded inputs hold exactly what the caller sent
    -- a defaulted, inferred or empty `scope` appearing anywhere here
    would be the silent fallback ADR-032 exists to prevent."""
    assert client.post("/actions", json=A_CATALOGUED_ACTION).status_code == 200

    refused = refusal_of(call("refresh-the-index", force=True))

    assert refused["outcome"] == "refused:missing_required_input"
    assert "'scope'" in refused["refusal"]
    assert dispatched == []

    record = the_one_record(ledger)
    assert record["outcome"] == "refused:missing_required_input"
    assert "'scope'" in record["refusal"]
    assert record["inputs"] == {"force": True}
    assert "scope" not in record["inputs"]
    assert "scope" not in json.dumps(record["inputs"])


def test_an_input_the_action_does_not_declare_is_refused_rather_than_dropped(
    resolvable, stored_actions, ledger, dispatched,
) -> None:
    """[REQ-SB-95-US-03-AC-04] An undeclared input is refused BY NAME.
    Silently dropping it would run the operation the caller asked for
    with meaningfully different arguments and report success."""
    client.post("/actions", json=A_CATALOGUED_ACTION)

    refused = refusal_of(call("refresh-the-index", scope="Projects", recurse=True))

    assert refused["outcome"] == "refused:unknown_input"
    assert "'recurse'" in refused["refusal"]
    assert dispatched == []
    assert the_one_record(ledger)["inputs"] == {"scope": "Projects", "recurse": True}


def test_a_caller_outside_allowed_callers_is_refused_and_the_wildcard_admits_it(
    resolvable, stored_actions, ledger, dispatched,
) -> None:
    """[REQ-SB-95-US-03-AC-07] The same caller, the same Action, the
    same inputs -- refused under `["other-agent"]` and accepted under
    `["*"]`, so what changed the answer is the catalogue and nothing
    else."""
    client.post("/actions", json={**A_CATALOGUED_ACTION, "allowed_callers": ["other-agent"]})

    refused = refusal_of(call("refresh-the-index", caller_agent_id="this-agent", scope="Projects"))

    assert refused["outcome"] == "refused:caller_not_permitted"
    assert "this-agent" in refused["refusal"]
    assert "refresh-the-index" in refused["refusal"]
    assert dispatched == []
    assert the_one_record(ledger)["outcome"] == "refused:caller_not_permitted"

    client.put("/actions/refresh-the-index", json={"allowed_callers": ["*"]})

    accepted = call("refresh-the-index", caller_agent_id="this-agent", scope="Projects")

    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["accepted"] is True
    assert [entry["caller_agent_id"] for entry in dispatched] == ["this-agent"]


def test_a_valid_call_passes_the_gate_records_it_and_enters_dispatch_exactly_once(
    resolvable, stored_actions, ledger, dispatched,
) -> None:
    """[REQ-SB-95-US-03-AC-02] Validation completes, the ledger carries
    the caller, the Action and the validated inputs, and the dispatch
    seam is entered once with those same inputs.

    And the accepted verdict does NOT claim an operation was performed:
    dispatch by implementation kind is REQ-SB-95-US-03-T03's, so the
    seam reports that nothing ran and the ledger records that word. A
    gate that reported `performed` here would be the fabricated outcome
    this whole story exists to make impossible."""
    client.post("/actions", json=A_CATALOGUED_ACTION)

    accepted = call("refresh-the-index", scope="Projects", force=True)

    assert accepted.status_code == 200, accepted.text
    verdict = accepted.json()
    assert verdict["accepted"] is True
    assert verdict["refusal"] is None
    assert verdict["outcome"] == "not_dispatched"
    assert "not implemented yet" in verdict["detail"]

    assert dispatched == [{
        "action_id": "refresh-the-index",
        "caller_agent_id": THE_CALLER,
        "inputs": {"scope": "Projects", "force": True},
    }]

    record = the_one_record(ledger)
    assert record["call_id"] == verdict["call_id"]
    assert record["caller_agent_id"] == THE_CALLER
    assert record["action_id"] == "refresh-the-index"
    assert record["inputs"] == {"scope": "Projects", "force": True}
    assert record["outcome"] == "not_dispatched"


def test_an_implementation_that_stopped_resolving_is_refused_naming_what_broke(
    resolvable, stored_actions, ledger, dispatched,
) -> None:
    """[REQ-SB-95-US-03-AC-02] The second line behind
    REQ-SB-95-US-02-T02's save-time check: the Skill was deployed when
    the Action was saved and was undeployed afterwards. The gate refuses
    naming what no longer resolves, rather than dispatching at something
    that is not there."""
    saved = client.post("/actions", json={
        **A_CATALOGUED_ACTION,
        "id": "capture-the-thread",
        "implementation": {"skill": {"skill_id": A_DEPLOYED_SKILL}},
    })
    assert saved.status_code == 200, saved.text

    resolvable.remove(A_DEPLOYED_SKILL)

    refused = refusal_of(call("capture-the-thread", scope="Projects"))

    assert refused["outcome"] == "refused:implementation_does_not_resolve"
    assert A_DEPLOYED_SKILL in refused["refusal"]
    assert "not deployed" in refused["refusal"]
    assert dispatched == []
    assert the_one_record(ledger)["outcome"] == "refused:implementation_does_not_resolve"
