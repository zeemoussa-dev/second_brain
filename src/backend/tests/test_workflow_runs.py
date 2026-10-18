"""Workflow runs (REQ-SB-95-US-04-T05, `ADR-034`): the run record, one
step at a time, per-step confirmation, and the report composed from
recorded outcomes.

Driven through the real `app.main.app` with `TestClient` -- which is
`httpx.ASGITransport(app=app)` behind a sync wrapper -- so what is
proved here is the shipped routes, the shipped run engine and the
shipped Action gate rather than a reconstruction of any of them.

**Nothing here may reach a real store.** Four things are isolated and
nothing else: the Workflow store and the Action store (in memory), and
the Action-call ledger's root and the WorkflowRuns root (onto
`tmp_path`, so the REAL writers run against real files in a directory
pytest throws away). Hermes is sandboxed suite-wide by `conftest.py`.
The three Actions these Workflows name are then created through the
real `POST /actions`, so the catalogue the steps are held to and
dispatched against is the one these tests built --
`test_these_tests_bring_their_own_action_catalogue` pins that, because
a file that read the operator's real catalogue would pass or fail by
accident of what this machine has today and could not pass on an empty
install at all (`ESC-064`, `ESC-075`).

**The `http` step points at a test-only route** imported from
`tests/test_action_dispatch.py` for the side effect of registering it.
Dispatch is live: an Action pointing at a real route really runs it,
and the last file to forget that re-read the operator's whole vault on
every run of the suite (`ESC-073`).

**"The run did not advance" is measured, not asserted.** The dispatch
seam is spied AROUND rather than replaced, so a second hand-out of the
same step would show up as a second entry even if every status in the
record still looked right.
"""
import json
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
THE_TARGET_ROUTE = test_action_dispatch.THE_TARGET_ROUTE

# The PRD's own motivating intent -- "list the Actions assigned to my
# team and send it to me by Mail" -- needs real Actions to point at,
# one of each implementation kind, because the three things the app
# does with a step (point at it, perform it, authorise it) are exactly
# what a run must keep apart.
THE_UI_ACTION = "review-the-open-actions"
THE_HTTP_ACTION = "file-the-summary"
THE_SKILL_ACTION = "mail-the-team-list"
THE_CONFIRMING_SKILL_ACTION = "mail-the-team-list-with-my-ok"

# Deliberately something nobody is building: a step id no Workflow in
# this repository documents, used only to prove an invented step is
# refused. Naming a near-future feature here is what blocked `T04`.
A_STEP_NO_WORKFLOW_DOCUMENTS = "post-it-to-the-noticeboard"
A_RUN_NO_INSTALL_HAS = "0000000000000000000000000000beef"

THE_ACTIONS_THESE_RUNS_DISPATCH = {
    THE_UI_ACTION: {
        "description": "Look over the team's open Actions on the artifacts screen",
        "inputs": [],
        "allowed_callers": [THE_CALLER],
        "implementation": {"ui": {"feature_key": A_REAL_FEATURE_KEY}},
    },
    THE_HTTP_ACTION: {
        "description": "File the summary into a folder",
        "inputs": [
            {"name": "folder", "type": "string", "required": True, "description": "which folder"},
            {"name": "note", "type": "string", "required": True, "description": "the note"},
        ],
        "allowed_callers": [THE_CALLER],
        "implementation": {"http": {"method": THE_TARGET_ROUTE[0], "path": THE_TARGET_ROUTE[1]}},
    },
    THE_SKILL_ACTION: {
        "description": "Mail the list, performed by the runner in its own profile",
        "inputs": [
            {"name": "to", "type": "string", "required": True, "description": "the recipient"},
        ],
        "allowed_callers": [THE_CALLER],
        "implementation": {"skill": {"skill_id": A_DEPLOYED_SKILL}},
    },
    THE_CONFIRMING_SKILL_ACTION: {
        "description": "Mail the list, once the operator says so",
        "inputs": [
            {"name": "to", "type": "string", "required": True, "description": "the recipient"},
        ],
        "allowed_callers": [THE_CALLER],
        "needs_confirmation": True,
        "implementation": {"skill": {"skill_id": A_DEPLOYED_SKILL}},
    },
}

# Three steps, one of each kind, asymmetric on purpose: a bug that
# reversed the list, spread one step's flag over the others or lost a
# step's inputs would be invisible against three identical steps.
THE_THREE_STEP_WORKFLOW = {
    "id": "mail-me-the-team-list",
    "request_kind": "list the Actions assigned to my team and mail them to me",
    "description": "The operator's standing handling for this ask",
    "steps": [
        {"id": "collect", "action_id": THE_UI_ACTION, "inputs": {},
         "description": "Look the list over myself"},
        {"id": "file", "action_id": THE_HTTP_ACTION,
         "inputs": {"folder": "Projects", "note": "the team list"},
         "description": "File the summary"},
        {"id": "mail", "action_id": THE_SKILL_ACTION, "inputs": {"to": "the-operator"},
         "description": "Mail it to me"},
    ],
    "report": {"description": "what was collected, filed and mailed", "include_step_ids": []},
}

THE_CONFIRMATION_WORKFLOW = {
    "id": "mail-me-the-team-list-with-my-ok",
    "request_kind": "mail me the team list, but ask me first",
    "description": "Same handling, with the operator in the loop before the mail goes",
    "steps": [
        {"id": "collect", "action_id": THE_UI_ACTION, "inputs": {},
         "description": "Look the list over myself"},
        {"id": "mail", "action_id": THE_CONFIRMING_SKILL_ACTION,
         "inputs": {"to": "the-operator"}, "needs_confirmation": True,
         "description": "Mail it to me, once I say so"},
    ],
    "report": {"description": "what was mailed, and that I approved it",
               "include_step_ids": []},
}

# A step the operator marked for confirmation over an Action that is not
# confirmation-required. The gate takes confirmation from the Action's
# own flag and from nothing else, so there is no confirmation for the
# run to pause at -- and performing it anyway is the one thing that must
# not happen.
THE_UNCONFIRMABLE_WORKFLOW = {
    "id": "mail-me-the-team-list-unconfirmable",
    "request_kind": "mail me the team list, but ask me first",
    "description": "A step flag with no confirmation behind it",
    "steps": [
        {"id": "mail", "action_id": THE_SKILL_ACTION, "inputs": {"to": "the-operator"},
         "needs_confirmation": True, "description": "Mail it to me, once I say so"},
    ],
    "report": {"description": "what was mailed", "include_step_ids": []},
}


@pytest.fixture(autouse=True)
def nothing_is_remembered_between_tests():
    """`test_action_dispatch`'s record of what its target route really
    performed, cleared around each test here too -- its own autouse
    fixture does not reach this module."""
    test_action_dispatch._entered_with.clear()
    yield
    test_action_dispatch._entered_with.clear()


def dispatches_of(dispatched: list[dict], action_id: str) -> list[dict]:
    """Only the entries for one Action. The confirmation tests run an
    earlier, unconfirmed step first, so "the paused step was never
    dispatched" has to be asked about that step rather than about the
    whole run."""
    return [entry for entry in dispatched if entry["action_id"] == action_id]


def ledger_records(root: Path) -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(root.glob("*.json"))]


def really_performed() -> list[dict]:
    """Every entry into the real operation behind the `http` step's
    target route -- the measurement that tells "nothing was performed"
    from "nothing was reported"."""
    return test_action_dispatch._entered_with


@pytest.fixture
def resolvable(monkeypatch) -> None:
    """The live resolution sources, replaced by ones these tests
    control: what is deployed, routed and registered on the machine
    running the suite is instance state, and an Action that resolved by
    accident of this install would make every run below accidental
    too."""
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
    """The Action store, in memory, so nothing here reads or writes the
    operator's real <DATA_PATH>/data/Actions/."""
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
def stored_workflows(monkeypatch) -> dict:
    """The Workflow store, in memory. An unknown id raises
    `FileNotFoundError`, exactly as the real `read_workflow_json` does:
    a fake raising `KeyError` would sail past the Manager's own
    `(OSError, ValueError)` handling."""
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
        "app.business.core.workflows.workflow_manager.workflows_data.read_workflow_json", read,
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
def ledger(tmp_path, monkeypatch) -> Path:
    """The Action-call ledger's root, moved onto tmp_path -- patched at
    the root so the real writer and the real `_claims/` exclusive-create
    primitive run, and a single-use grant is single-use because the
    filesystem says so rather than because a fake store does."""
    root = tmp_path / "ActionCalls"
    monkeypatch.setattr("app.data_access.action_calls._action_calls_root", lambda: root)
    return root


@pytest.fixture
def runs(tmp_path, monkeypatch) -> Path:
    """The WorkflowRuns root, moved onto tmp_path, for the same reason:
    what these tests assert about the stored record is asserted against
    real JSON written by the real writer."""
    root = tmp_path / "WorkflowRuns"
    monkeypatch.setattr("app.data_access.workflow_runs._workflow_runs_root", lambda: root)
    return root


@pytest.fixture
def dispatched(monkeypatch) -> list[dict]:
    """A spy AROUND the real dispatch seam, not instead of it: what
    these tests count is how many times a step was really dispatched,
    while the real seam still decides what happens to it."""
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
def a_real_action_catalogue(resolvable, stored_actions) -> dict:
    """The four Actions, really created over the real Actions API, so
    they are catalogued exactly as the operator's own screen shows
    them."""
    for action_id, definition in THE_ACTIONS_THESE_RUNS_DISPATCH.items():
        created = client.post("/actions", json={"id": action_id, **definition})
        assert created.status_code == 200, created.text
    return stored_actions


@pytest.fixture
def the_three_step_workflow(a_real_action_catalogue, stored_workflows, runs, ledger) -> dict:
    created = client.post("/workflows", json=THE_THREE_STEP_WORKFLOW)
    assert created.status_code == 200, created.text
    return created.json()


@pytest.fixture
def the_confirmation_workflow(a_real_action_catalogue, stored_workflows, runs, ledger) -> dict:
    created = client.post("/workflows", json=THE_CONFIRMATION_WORKFLOW)
    assert created.status_code == 200, created.text
    return created.json()


def start_a_run(workflow_id: str) -> dict:
    started = client.post(f"/workflows/{workflow_id}/run",
                          json={"caller_agent_id": THE_CALLER})
    assert started.status_code == 200, started.text
    return started.json()


def take_the_next_step(run_id: str) -> dict:
    answered = client.post(f"/workflows/runs/{run_id}/next-step")
    assert answered.status_code == 200, answered.text
    return answered.json()


def report(run_id: str, step_id: str, outcome: str, detail: str = "") -> dict:
    return client.post(
        f"/workflows/runs/{run_id}/steps/{step_id}/outcome",
        json={"outcome": outcome, "detail": detail},
    )


def stored_run(runs_root: Path, run_id: str) -> dict:
    """The run as it really is ON DISK -- every assertion about what the
    record distinguishes is made against the written bytes, not against
    the response body that happened to be composed in the same call."""
    return json.loads((runs_root / f"{run_id}.json").read_text(encoding="utf-8"))


def statuses(run: dict) -> list[tuple]:
    return [(step["step_id"], step["status"]) for step in run["steps"]]


def test_these_tests_bring_their_own_action_catalogue(a_real_action_catalogue) -> None:
    """[REQ-SB-95-US-04-AC-03] The premise every run below rests on,
    asserted rather than assumed: the catalogue these runs dispatch
    against holds exactly the four Actions this file created.

    Pinned because the alternative failure is silent -- a file reading
    the operator's real <DATA_PATH>/data/Actions/ would pass or fail by
    accident of what this machine happens to have today, and could not
    pass on an empty install at all (`ESC-064`, `ESC-075`)."""
    catalogued = sorted(entry["id"] for entry in client.get("/actions").json())

    assert catalogued == sorted(THE_ACTIONS_THESE_RUNS_DISPATCH)


def test_a_started_run_hands_back_exactly_one_step_and_it_is_the_first(
    the_three_step_workflow, runs, dispatched,
) -> None:
    """[REQ-SB-95-US-04-AC-03] Start a run of a three-step Workflow and
    exactly ONE next step comes back -- a single step object, not a
    list -- and it is step 1 in the documented order.

    Starting performs nothing: the record is written with every step at
    `not_reached`, and only taking the step dispatches it. That is also
    what makes the four step states tellable apart in the stored bytes:
    `not_reached` is written for every step from the first byte, so
    "nobody got here" is a recorded fact rather than the absence of
    one."""
    started = start_a_run("mail-me-the-team-list")

    assert started["workflow_id"] == "mail-me-the-team-list"
    assert started["status"] == "running"
    assert statuses(stored_run(runs, started["run_id"])) == [
        ("collect", "not_reached"), ("file", "not_reached"), ("mail", "not_reached"),
    ]
    assert dispatched == []

    answered = take_the_next_step(started["run_id"])

    assert isinstance(answered["step"], dict)
    assert (answered["step"]["step_id"], answered["step"]["position"]) == ("collect", 1)
    assert answered["step"]["action_id"] == THE_UI_ACTION
    assert answered["status"] == "running"
    assert answered["report"] is None
    assert statuses(stored_run(runs, started["run_id"])) == [
        ("collect", "running"), ("file", "not_reached"), ("mail", "not_reached"),
    ]
    # A `ui` step is pointed at, never performed -- the run records the
    # gate's own word for it rather than inventing one of its own.
    assert answered["step"]["dispatch_outcome"] == action_invocation.OUTCOME_POINTED_AT
    assert really_performed() == []


def test_asking_again_without_recording_an_outcome_returns_the_same_step(
    the_three_step_workflow, runs, dispatched,
) -> None:
    """[REQ-SB-95-US-04-AC-03] Ask for the next step again without
    recording step 1's outcome and the SAME step 1 comes back; the run
    does not advance and nothing is dispatched a second time.

    The second half is the one that matters and is measured, not
    asserted: a re-dispatch would perform an `http` step twice and open
    a second pending decision for a confirmation-marked one, and every
    status in the record would still look right afterwards."""
    started = start_a_run("mail-me-the-team-list")
    first = take_the_next_step(started["run_id"])
    again = take_the_next_step(started["run_id"])

    assert again["step"]["step_id"] == first["step"]["step_id"] == "collect"
    assert again["step"]["call_ids"] == first["step"]["call_ids"]
    assert again["status"] == "running"
    assert statuses(stored_run(runs, started["run_id"])) == [
        ("collect", "running"), ("file", "not_reached"), ("mail", "not_reached"),
    ]
    assert [entry["action_id"] for entry in dispatched] == [THE_UI_ACTION]


def test_recording_the_current_steps_outcome_is_what_advances_the_run(
    the_three_step_workflow, runs, dispatched,
) -> None:
    """[REQ-SB-95-US-04-AC-03] Record step 1's outcome, then fetch:
    step 2 comes back, and the run record holds step 1's recorded
    outcome -- its reported status, its reported words, and the gate's
    own `pointed_at` left exactly as the gate said it.

    The two are kept apart on purpose: what the app did and what the
    caller reports are different facts about one step, and overwriting
    the first with the second is how a step the operator did themselves
    comes to read as though the app performed it."""
    started = start_a_run("mail-me-the-team-list")
    take_the_next_step(started["run_id"])

    recorded = report(started["run_id"], "collect", "done", "I looked the list over")
    assert recorded.status_code == 200, recorded.text

    on_disk = stored_run(runs, started["run_id"])
    collected = on_disk["steps"][0]
    assert collected["status"] == "done"
    assert collected["detail"] == "I looked the list over"
    assert collected["dispatch_outcome"] == action_invocation.OUTCOME_POINTED_AT
    assert collected["recorded_at"]

    advanced = take_the_next_step(started["run_id"])

    assert (advanced["step"]["step_id"], advanced["step"]["position"]) == ("file", 2)
    assert advanced["step"]["dispatch_outcome"] == action_invocation.OUTCOME_PERFORMED
    assert statuses(stored_run(runs, started["run_id"])) == [
        ("collect", "done"), ("file", "running"), ("mail", "not_reached"),
    ]
    # The `http` step really ran, in process, against the test-only
    # target route -- and only that step did.
    assert really_performed() == [
        {"folder": "Projects", "note": "the team list", "urgent": False},
    ]
    assert [entry["action_id"] for entry in dispatched] == [THE_UI_ACTION, THE_HTTP_ACTION]


def test_a_confirmation_marked_step_pauses_at_an_awaiting_call_record_until_the_operator_says_yes(
    the_confirmation_workflow, runs, ledger, dispatched,
) -> None:
    """[REQ-SB-95-US-04-AC-03] A step marked as needing confirmation
    opens an `awaiting_confirmation` Action-call record, the run pauses
    there visibly, and it advances only once the operator confirms.

    Every part of that is `ADR-033`'s existing mechanism, unchanged: the
    record is an ordinary ledger row, it appears on the operator's
    existing pending list, they answer on the existing
    `/actions/calls/{id}/confirm` route, and the re-call spends the
    single-use grant. The run contributes the pause and nothing else.

    "Nothing was performed while paused" is measured twice -- the
    dispatch seam was never entered, and the skill grant is still
    unspent -- because a response that merely said so would read
    identically either way."""
    started = start_a_run("mail-me-the-team-list-with-my-ok")
    take_the_next_step(started["run_id"])
    assert report(started["run_id"], "collect", "done").status_code == 200

    paused = take_the_next_step(started["run_id"])

    assert paused["status"] == "awaiting_confirmation"
    assert paused["step"]["step_id"] == "mail"
    assert paused["step"]["status"] == "awaiting_confirmation"
    awaiting_call_id = paused["step"]["awaiting_call_id"]
    assert awaiting_call_id
    assert paused["step"]["call_ids"] == [awaiting_call_id]
    assert dispatches_of(dispatched, THE_CONFIRMING_SKILL_ACTION) == []

    opened = json.loads((ledger / f"{awaiting_call_id}.json").read_text(encoding="utf-8"))
    assert opened["outcome"] == action_invocation.OUTCOME_AWAITING_CONFIRMATION
    assert opened["action_id"] == THE_CONFIRMING_SKILL_ACTION
    assert opened["inputs"] == {"to": "the-operator"}

    pending = client.get("/actions/calls/pending")
    assert [entry["call_id"] for entry in pending.json()] == [awaiting_call_id]

    # Asked again while the operator has not answered: the same step,
    # the same one call record, no second decision to make.
    still_paused = take_the_next_step(started["run_id"])
    assert still_paused["step"]["call_ids"] == [awaiting_call_id]
    assert [record["call_id"] for record in ledger_records(ledger)
            if record["action_id"] == THE_CONFIRMING_SKILL_ACTION] == [awaiting_call_id]
    assert statuses(stored_run(runs, started["run_id"])) == [
        ("collect", "done"), ("mail", "awaiting_confirmation"),
    ]

    confirmed = client.post(f"/actions/calls/{awaiting_call_id}/confirm")
    assert confirmed.status_code == 200, confirmed.text

    advanced = take_the_next_step(started["run_id"])

    assert advanced["status"] == "running"
    assert advanced["step"]["step_id"] == "mail"
    assert advanced["step"]["status"] == "running"
    # Two ledger rows, joined by `granted_by_call_id`: the operator's
    # decision, and the re-call that spent it (`ADR-033`'s own shape --
    # one call id can carry only one grant, ever).
    assert len(advanced["step"]["call_ids"]) == 2
    assert advanced["step"]["call_ids"][0] == awaiting_call_id
    spending_call = json.loads(
        (ledger / f"{advanced['step']['call_ids'][1]}.json").read_text(encoding="utf-8")
    )
    assert spending_call["granted_by_call_id"] == awaiting_call_id
    assert spending_call["outcome"] == action_invocation.OUTCOME_AUTHORISED
    assert len(dispatches_of(dispatched, THE_CONFIRMING_SKILL_ACTION)) == 1

    assert report(started["run_id"], "mail", "done", "the runner sent it").status_code == 200
    finished = take_the_next_step(started["run_id"])
    assert finished["step"] is None
    assert finished["status"] == "complete"
    assert finished["report"]["every_documented_step_done"] is True


def test_a_declined_confirmation_leaves_the_run_blocked_at_that_step(
    the_confirmation_workflow, runs, ledger, dispatched,
) -> None:
    """[REQ-SB-95-US-04-AC-03] The other answer. Declined is terminal:
    the step records `refused` with the operator's own refusal sentence,
    the run does NOT advance, and it is `blocked` rather than anything
    that could read as finished."""
    started = start_a_run("mail-me-the-team-list-with-my-ok")
    take_the_next_step(started["run_id"])
    report(started["run_id"], "collect", "done")
    paused = take_the_next_step(started["run_id"])
    awaiting_call_id = paused["step"]["awaiting_call_id"]

    declined = client.post(f"/actions/calls/{awaiting_call_id}/decline")
    assert declined.status_code == 200, declined.text

    after = take_the_next_step(started["run_id"])

    assert after["step"] is None
    assert after["status"] == "blocked"
    assert "declined" in after["detail"]
    assert statuses(stored_run(runs, started["run_id"])) == [
        ("collect", "done"), ("mail", "refused"),
    ]
    refused_step = stored_run(runs, started["run_id"])["steps"][1]
    assert "declined" in refused_step["refusal"]
    assert after["report"]["every_documented_step_done"] is False
    assert dispatches_of(dispatched, THE_CONFIRMING_SKILL_ACTION) == []

    # And it stays blocked: asking again neither retries the step nor
    # moves past it, which is what "no skipped step" means at the end of
    # a run as much as in the middle of one.
    assert take_the_next_step(started["run_id"])["status"] == "blocked"
    assert dispatches_of(dispatched, THE_CONFIRMING_SKILL_ACTION) == []


def test_a_step_marked_for_confirmation_whose_action_needs_none_is_refused_not_performed(
    a_real_action_catalogue, stored_workflows, runs, ledger, dispatched,
) -> None:
    """[REQ-SB-95-US-04-AC-03] A step the operator marked as needing
    their confirmation must not advance without one. The Action gate
    takes confirmation from the Action's own flag and from nothing else
    (`REQ-SB-95-US-03-T04`), so a step flag with no confirmation-required
    Action behind it has nothing to pause at -- and the run refuses it,
    naming which step and why, rather than performing something the
    operator asked to be asked about.

    This is the one scope-internal judgement call in `T05` and is logged
    as such: the alternative within this task's scope was to perform the
    step, which is the exact failure `REQ-SB-95` exists to close."""
    created = client.post("/workflows", json=THE_UNCONFIRMABLE_WORKFLOW)
    assert created.status_code == 200, created.text

    started = start_a_run("mail-me-the-team-list-unconfirmable")
    answered = take_the_next_step(started["run_id"])

    assert answered["step"] is None
    assert answered["status"] == "blocked"
    refused_step = stored_run(runs, started["run_id"])["steps"][0]
    assert refused_step["status"] == "refused"
    assert "'mail'" in refused_step["refusal"]
    assert THE_SKILL_ACTION in refused_step["refusal"]
    assert "nothing was performed" in refused_step["refusal"].lower()
    assert dispatched == []
    assert list(ledger.glob("*.json")) == []


def test_an_outcome_for_a_step_that_is_not_the_current_one_or_not_in_the_workflow_is_refused(
    the_three_step_workflow, runs,
) -> None:
    """[REQ-SB-95-US-04-AC-03] No skipping, and no invented step.

    Four refusals, each a 409 carrying the engine's own sentence rather
    than a flattened "Conflict": a later step while the run is on an
    earlier one, a step id this run does not hold, a step nothing has
    handed out yet, and an outcome word that is neither `done` nor
    `failed`. After all four the record is byte-for-byte what it was --
    a refusal that still wrote something would be worse than one that
    performed the step, because nothing would say so."""
    started = start_a_run("mail-me-the-team-list")
    run_id = started["run_id"]

    not_handed_out_yet = report(run_id, "collect", "done")
    assert not_handed_out_yet.status_code == 409
    assert "has not been handed out yet" in not_handed_out_yet.json()["detail"]

    take_the_next_step(run_id)
    before = stored_run(runs, run_id)

    skipped = report(run_id, "mail", "done")
    assert skipped.status_code == 409
    assert "'collect'" in skipped.json()["detail"]
    assert "none is skipped" in skipped.json()["detail"]

    invented = report(run_id, A_STEP_NO_WORKFLOW_DOCUMENTS, "done")
    assert invented.status_code == 409
    assert A_STEP_NO_WORKFLOW_DOCUMENTS in invented.json()["detail"]
    assert "no step was added" in invented.json()["detail"]

    not_a_word = report(run_id, "collect", "mostly_done")
    assert not_a_word.status_code == 409
    assert "'mostly_done'" in not_a_word.json()["detail"]

    assert stored_run(runs, run_id) == before

    unknown_run = client.post(f"/workflows/runs/{A_RUN_NO_INSTALL_HAS}/next-step")
    assert unknown_run.status_code == 404
    assert A_RUN_NO_INSTALL_HAS in unknown_run.json()["detail"]


def test_a_failed_step_is_reported_as_failed_and_never_as_done(
    the_three_step_workflow, runs, monkeypatch,
) -> None:
    """[REQ-SB-95-US-04-AC-03] Break the real operation behind step 2's
    `http` Action -- a scoped monkeypatch of the one function the
    target route calls, so the route, the gate and the dispatch path are
    all still the real ones -- and the composed report names that step
    as failed, never as done.

    The app observed this failure itself, so the step is settled by the
    framework and is NOT left for the caller to report over: a step the
    gate says did not run must not be reportable as done. The report
    still carries every documented step, including the one the run never
    reached, each under its own distinct status."""
    def it_breaks(folder: str, note: str, urgent: bool) -> dict:
        raise RuntimeError("the summary could not be filed")

    monkeypatch.setattr(test_action_dispatch, "_the_real_operation", it_breaks)

    started = start_a_run("mail-me-the-team-list")
    run_id = started["run_id"]
    take_the_next_step(run_id)
    report(run_id, "collect", "done")

    failed = take_the_next_step(run_id)

    assert failed["step"] is None
    assert failed["status"] == "blocked"
    assert statuses(stored_run(runs, run_id)) == [
        ("collect", "done"), ("file", "failed"), ("mail", "not_reached"),
    ]

    composed = failed["report"]
    assert composed["every_documented_step_done"] is False
    assert [(step["step_id"], step["status"]) for step in composed["steps"]] == [
        ("collect", "done"), ("file", "failed"), ("mail", "not_reached"),
    ]
    assert composed["description"] == "what was collected, filed and mailed"
    filed = next(step for step in composed["steps"] if step["step_id"] == "file")
    assert filed["dispatch_outcome"] == action_invocation.OUTCOME_FAILED
    assert "did not" in filed["detail"].lower() or "failed with" in filed["detail"].lower()

    # The step after the failure was never reached, and says so in the
    # record rather than being absent from it.
    mailed = next(step for step in composed["steps"] if step["step_id"] == "mail")
    assert mailed["status"] == "not_reached"
    assert mailed["call_ids"] == []

    # And it cannot be talked out of it: the failed step's outcome is
    # recorded and is not retaken.
    assert report(run_id, "file", "done").status_code == 409


def test_the_run_record_holds_every_documented_step_in_order_and_nothing_else(
    the_three_step_workflow, runs,
) -> None:
    """[REQ-SB-95-US-04-AC-03] The run record's step list equals the
    Workflow's documented steps, in the documented order, with nothing
    added and nothing dropped -- including each step's own inputs and
    confirmation flag.

    Asserted against the Workflow as the catalogue really serves it
    rather than against the literal this file posted, so a Manager that
    re-keyed or re-ordered a step on the way in would be caught here
    too. The snapshot is also what makes a run reproducible: editing the
    Workflow afterwards must not change a run already in flight."""
    documented = client.get("/workflows/mail-me-the-team-list").json()["steps"]
    started = start_a_run("mail-me-the-team-list")
    on_disk = stored_run(runs, started["run_id"])

    assert [step["step_id"] for step in on_disk["steps"]] == [
        step["id"] for step in documented
    ]
    assert [step["action_id"] for step in on_disk["steps"]] == [
        step["action_id"] for step in documented
    ]
    assert [step["inputs"] for step in on_disk["steps"]] == [
        step["inputs"] for step in documented
    ]
    assert [step["needs_confirmation"] for step in on_disk["steps"]] == [
        step["needs_confirmation"] for step in documented
    ]
    assert [step["position"] for step in on_disk["steps"]] == [1, 2, 3]
    assert on_disk["workflow_id"] == "mail-me-the-team-list"
    assert on_disk["request_kind"] == THE_THREE_STEP_WORKFLOW["request_kind"]
    assert on_disk["caller_agent_id"] == THE_CALLER

    # Editing the Workflow does not reach a run already in flight.
    shortened = client.put("/workflows/mail-me-the-team-list", json={
        "steps": [{"id": "collect", "action_id": THE_UI_ACTION, "inputs": {}}],
    })
    assert shortened.status_code == 200, shortened.text
    assert [step["step_id"] for step in stored_run(runs, started["run_id"])["steps"]] == [
        "collect", "file", "mail",
    ]


def test_a_run_that_cannot_be_started_is_refused_and_nothing_is_written(
    a_real_action_catalogue, stored_workflows, runs,
) -> None:
    """[REQ-SB-95-US-04-AC-03] An unknown Workflow is a 404, a Workflow
    with no documented steps and a start naming no caller are 409s
    carrying the engine's sentence, and none of the three leaves a run
    record behind -- an empty run that existed would be an open run
    nobody could ever finish."""
    unknown = client.post("/workflows/a-workflow-nobody-wrote/run",
                          json={"caller_agent_id": THE_CALLER})
    assert unknown.status_code == 404
    assert "a-workflow-nobody-wrote" in unknown.json()["detail"]

    assert client.post("/workflows", json={
        "id": "an-intent-with-no-handling-yet", "request_kind": "nothing yet", "steps": [],
    }).status_code == 200
    stepless = client.post("/workflows/an-intent-with-no-handling-yet/run",
                           json={"caller_agent_id": THE_CALLER})
    assert stepless.status_code == 409
    assert "documents no steps" in stepless.json()["detail"]

    client.post("/workflows", json=THE_THREE_STEP_WORKFLOW)
    nameless = client.post("/workflows/mail-me-the-team-list/run",
                           json={"caller_agent_id": "  "})
    assert nameless.status_code == 409
    assert "named none" in nameless.json()["detail"]

    assert not runs.exists() or list(runs.glob("*.json")) == []
