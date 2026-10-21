"""A Workflow that is not a fixed script (`REQ-SB-103`): a step may be
an Action, another agent, or a person -- and what a step is called with
may come from the ask or from what an earlier step came back with.

Driven through the real `app.main.app` with `TestClient`, like
`test_workflow_runs.py`, so what is proved is the shipped routes, the
shipped run engine and the shipped Action gate. The Workflow store and
the Action store are in memory; the WorkflowRuns root and the
Action-call ledger are moved onto `tmp_path`, so the real writers run
against real files in a directory pytest throws away.

**The one Action these Workflows name is a `ui` Action**, deliberately.
Everything this file is about -- references resolving, an agent being
handed a step, a person being asked -- happens before and around
dispatch, and pointing a step at anything that really performs would
add a side effect none of these assertions are about.

**What is asserted is the record on disk**, not the response body
composed in the same call: the point of `performed_by`, `human_said`
and `decided_by` is that they survive into a file somebody reads later.
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main_app

client = TestClient(main_app.app)

THE_CALLER = "cbo-agent"
A_REAL_FEATURE_KEY = "/settings/artifacts"
THE_UI_ACTION = "review-the-open-actions"

# The suite signs every request in as this Admin (`conftest.py`). Named
# here because attribution is the point of several assertions below,
# and a test that asserted "somebody" would pass against a bug that
# recorded the wrong person.
THE_SIGNED_IN_PERSON = "The Test Suite"

# The operator's own motivating ask, in its three-kind shape: find the
# Actions (an Action), have an agent draft the mail (an agent), show it
# to the person before it goes (a human), then send (an Action).
THE_MIXED_WORKFLOW = {
    "id": "mail-me-the-team-list-my-way",
    "request_kind": "list the Actions assigned to my team and mail them to me",
    "description": "Three kinds of step, one handling",
    "steps": [
        {"id": "find", "kind": "action", "action_id": THE_UI_ACTION, "inputs": {},
         "description": "Find the Actions assigned to the team"},
        {"id": "draft", "kind": "agent", "agent_id": "send-email-agent",
         "ask": "{{steps.find.result}}",
         "description": "Have the mail agent format this"},
        {"id": "approve", "kind": "human", "ask": "{{steps.draft.result}}",
         "allows_edit": True,
         "description": "Show it to me before it goes"},
        {"id": "send", "kind": "action", "action_id": THE_UI_ACTION,
         "inputs": {"body": "{{steps.approve.result}}"},
         "description": "Send what was approved"},
    ],
    "report": {"description": "what was found, drafted, approved and sent",
               "include_step_ids": []},
}

# A human step the Workflow says may NOT be changed -- approve it or
# decline it. The run must refuse an edit here rather than send
# something the handling never said could be edited.
THE_UNEDITABLE_WORKFLOW = {
    "id": "ask-me-but-do-not-let-me-rewrite-it",
    "request_kind": "ask me first",
    "description": "A question that takes yes or no",
    "steps": [
        {"id": "approve", "kind": "human", "ask": "Shall I send the team list?",
         "allows_edit": False, "description": "Yes or no"},
    ],
    "report": {"description": "what I answered", "include_step_ids": []},
}

# A human step whose question references a step that is still waiting.
# Asking it would spend a person's attention on a bug, so the step is
# refused instead (`step_references`' own rule, through the engine).
THE_UNASKABLE_WORKFLOW = {
    "id": "ask-me-something-nobody-can-answer",
    "request_kind": "ask me first",
    "description": "A question built from a value that does not exist",
    "steps": [
        {"id": "approve", "kind": "human", "ask": "{{request.nothing_was_supplied}}",
         "description": "A question with a hole in it"},
    ],
    "report": {"description": "what I answered", "include_step_ids": []},
}


@pytest.fixture
def resolvable(monkeypatch) -> None:
    """The feature key the `ui` Action points at, resolvable without the
    operator's real install behind it -- what is registered on the
    machine running the suite is instance state, and an Action that
    resolved by accident of this install would make every run below
    accidental too."""
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.UI_FEATURE_KEYS",
        (A_REAL_FEATURE_KEY,),
    )


@pytest.fixture
def stored_actions(monkeypatch) -> dict:
    written: dict = {}

    def read(action_id: str) -> dict:
        if action_id not in written:
            raise FileNotFoundError(f"No Action.json for {action_id!r}")
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
    return written


@pytest.fixture
def stored_workflows(monkeypatch) -> dict:
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
    root = tmp_path / "ActionCalls"
    monkeypatch.setattr("app.data_access.action_calls._action_calls_root", lambda: root)
    return root


@pytest.fixture
def runs(tmp_path, monkeypatch) -> Path:
    root = tmp_path / "WorkflowRuns"
    monkeypatch.setattr("app.data_access.workflow_runs._workflow_runs_root", lambda: root)
    return root


@pytest.fixture
def a_catalogued_action(resolvable, stored_actions) -> dict:
    created = client.post("/actions", json={
        "id": THE_UI_ACTION,
        "description": "Look over the team's open Actions on the artifacts screen",
        # `body` is declared because the last step of the mixed Workflow
        # is called with what the person approved. An input the Action
        # does not declare is refused by the gate, which is its job --
        # but it would refuse this test's point before reaching it.
        "inputs": [
            {"name": "body", "type": "string", "required": False,
             "description": "what was approved"},
        ],
        "allowed_callers": [THE_CALLER],
        "implementation": {"ui": {"feature_key": A_REAL_FEATURE_KEY}},
    })
    assert created.status_code == 200, created.text
    return stored_actions


@pytest.fixture
def workflows(a_catalogued_action, stored_workflows, runs, ledger) -> None:
    for definition in (THE_MIXED_WORKFLOW, THE_UNEDITABLE_WORKFLOW, THE_UNASKABLE_WORKFLOW):
        created = client.post("/workflows", json=definition)
        assert created.status_code == 200, created.text


def start_a_run(workflow_id: str, request: dict | None = None) -> dict:
    started = client.post(
        f"/workflows/{workflow_id}/run",
        json={"caller_agent_id": THE_CALLER, "request": request or {}},
    )
    assert started.status_code == 200, started.text
    return started.json()


def take_the_next_step(run_id: str) -> dict:
    answered = client.post(f"/workflows/runs/{run_id}/next-step")
    assert answered.status_code == 200, answered.text
    return answered.json()


def report(run_id: str, step_id: str, outcome: str, result=None):
    return client.post(
        f"/workflows/runs/{run_id}/steps/{step_id}/outcome",
        json={"outcome": outcome, "detail": "", "result": result},
    )


def answer(run_id: str, step_id: str, decision: str, said: str = "", result=None):
    return client.post(
        f"/workflows/runs/{run_id}/steps/{step_id}/answer",
        json={"decision": decision, "said": said, "result": result},
    )


def stored_run(runs_root: Path, run_id: str) -> dict:
    return json.loads((runs_root / f"{run_id}.json").read_text(encoding="utf-8"))


def step_of(run: dict, step_id: str) -> dict:
    return next(step for step in run["steps"] if step["step_id"] == step_id)


def test_an_agent_step_is_handed_back_and_never_claimed_as_performed(workflows, runs) -> None:
    """[REQ-SB-103] The app does not call the agent -- Hermes owns that
    conversation. So an agent step is handed BACK carrying who to ask
    and what to ask them, and the record says `performed_by: agent`
    rather than letting a reader infer from a `done` status that the
    app did it."""
    run_id = start_a_run(THE_MIXED_WORKFLOW["id"])["run_id"]

    take_the_next_step(run_id)
    assert report(run_id, "find", "done", result={"tasks": ["review the MSA", "call Ana"]}).status_code == 200

    handed = take_the_next_step(run_id)

    assert handed["step"]["step_id"] == "draft"
    assert handed["step"]["kind"] == "agent"
    assert handed["step"]["agent_id"] == "send-email-agent"
    assert handed["step"]["performed_by"] == "agent"
    assert handed["step"]["dispatch_outcome"] == "handed_to_agent"
    # The question the agent is handed is the RESOLVED one -- the result
    # of the step before it, not the reference that named it.
    assert handed["step"]["resolved_ask"] == {"tasks": ["review the MSA", "call Ana"]}
    assert "send-email-agent" in handed["detail"]

    on_disk = step_of(stored_run(runs, run_id), "draft")
    assert on_disk["performed_by"] == "agent"
    assert on_disk["call_ids"] == [], "an agent step opens no Action call"


def test_a_human_step_holds_the_run_until_somebody_answers(workflows, runs) -> None:
    """[REQ-SB-103] A run waiting on a person is neither `running` nor
    `blocked`: nothing is happening and nothing went wrong. It is
    `awaiting_person`, which is what "what is waiting on me" is built
    from, and it stays there however many times the next step is asked
    for."""
    run_id = start_a_run(THE_MIXED_WORKFLOW["id"])["run_id"]
    take_the_next_step(run_id)
    report(run_id, "find", "done", result=["review the MSA"])
    take_the_next_step(run_id)
    report(run_id, "draft", "done", result="Here is the team list. -- the mail agent")

    waiting = take_the_next_step(run_id)

    assert waiting["status"] == "awaiting_person"
    assert waiting["step"]["step_id"] == "approve"
    assert waiting["step"]["status"] == "awaiting_person"
    assert waiting["step"]["performed_by"] == "human"
    assert waiting["step"]["resolved_ask"] == "Here is the team list. -- the mail agent"
    assert waiting["step"]["asked_at"]

    asked_again = take_the_next_step(run_id)
    assert asked_again["step"]["asked_at"] == waiting["step"]["asked_at"], (
        "asking for the next step again must not re-ask the person"
    )
    assert stored_run(runs, run_id)["status"] == "awaiting_person"


def test_a_person_may_change_what_goes_out_and_the_change_is_what_flows(
    workflows, runs,
) -> None:
    """[REQ-SB-103] The operator's own framing: "edit, so the human can
    change it before it goes". The edited value -- not what was
    proposed -- is what the next step is called with, and the record
    keeps what they said apart from what now flows."""
    run_id = start_a_run(THE_MIXED_WORKFLOW["id"])["run_id"]
    take_the_next_step(run_id)
    report(run_id, "find", "done", result=["review the MSA"])
    take_the_next_step(run_id)
    report(run_id, "draft", "done", result="Here is the team list.")
    take_the_next_step(run_id)

    edited = answer(
        run_id, "approve", "edited",
        said="add that the MSA is urgent",
        result="Here is the team list. The MSA review is urgent.",
    )
    assert edited.status_code == 200, edited.text

    approved = step_of(stored_run(runs, run_id), "approve")
    assert approved["status"] == "done"
    assert approved["human_decision"] == "edited"
    assert approved["human_said"] == "add that the MSA is urgent"
    assert approved["result"] == "Here is the team list. The MSA review is urgent."
    assert approved["decided_by"]["display_name"] == THE_SIGNED_IN_PERSON

    sent = take_the_next_step(run_id)
    assert sent["step"]["resolved_inputs"] == {
        "body": "Here is the team list. The MSA review is urgent.",
    }, "the step after a human edit is called with the edit, not with what was proposed"


def test_an_approval_with_no_edit_carries_what_the_person_said(workflows, runs) -> None:
    """[REQ-SB-103] At a human step the person's words ARE the value --
    "yes, and copy finance" is the answer, not a comment on it -- so an
    approval that supplies no replacement flows what they said."""
    run_id = start_a_run(THE_UNEDITABLE_WORKFLOW["id"])["run_id"]
    take_the_next_step(run_id)

    assert answer(run_id, "approve", "approved", said="yes, go ahead").status_code == 200

    approved = step_of(stored_run(runs, run_id), "approve")
    assert approved["human_decision"] == "approved"
    assert approved["result"] == "yes, go ahead"
    assert THE_SIGNED_IN_PERSON in approved["detail"]


def test_an_edit_to_a_step_that_does_not_allow_one_is_refused_and_nothing_is_recorded(
    workflows, runs,
) -> None:
    """[REQ-SB-103] `allows_edit: false` means "what goes out is what
    was proposed". Honouring an edit anyway would send something the
    handling never authorised, so it is refused -- and the step is left
    waiting rather than settled on a decision nobody may make."""
    run_id = start_a_run(THE_UNEDITABLE_WORKFLOW["id"])["run_id"]
    take_the_next_step(run_id)

    refused = answer(run_id, "approve", "edited", said="let me rewrite that",
                     result="something else entirely")

    assert refused.status_code == 409
    assert "does not allow editing" in refused.json()["detail"]
    still_waiting = step_of(stored_run(runs, run_id), "approve")
    assert still_waiting["status"] == "awaiting_person"
    assert still_waiting["human_decision"] is None
    assert still_waiting["result"] is None


def test_an_edit_that_names_no_replacement_is_refused(workflows, runs) -> None:
    """[REQ-SB-103] An edit replaces what was proposed. One that names
    nothing to replace it with is not an approval of the old value, and
    treating it as one is how the unedited draft goes out under the
    word "edited"."""
    run_id = start_a_run(THE_MIXED_WORKFLOW["id"])["run_id"]
    take_the_next_step(run_id)
    report(run_id, "find", "done", result=["review the MSA"])
    take_the_next_step(run_id)
    report(run_id, "draft", "done", result="Here is the team list.")
    take_the_next_step(run_id)

    refused = answer(run_id, "approve", "edited", said="change it")

    assert refused.status_code == 409
    assert "named nothing to replace it with" in refused.json()["detail"]
    assert step_of(stored_run(runs, run_id), "approve")["status"] == "awaiting_person"


def test_a_decline_blocks_the_run_at_that_step_and_nothing_after_it_runs(
    workflows, runs,
) -> None:
    """[REQ-SB-103] A decline is a real answer, not an error: 200, the
    record says who declined and what they said, and the steps after it
    were not run."""
    run_id = start_a_run(THE_UNEDITABLE_WORKFLOW["id"])["run_id"]
    take_the_next_step(run_id)

    declined = answer(run_id, "approve", "declined", said="not this week")
    assert declined.status_code == 200, declined.text
    assert declined.json()["status"] == "blocked"

    approved = step_of(stored_run(runs, run_id), "approve")
    assert approved["status"] == "refused"
    assert approved["human_decision"] == "declined"
    assert THE_SIGNED_IN_PERSON in approved["refusal"]
    assert "not this week" in approved["refusal"]

    nothing_further = take_the_next_step(run_id)
    assert nothing_further["step"] is None
    assert nothing_further["report"]["every_documented_step_done"] is False


def test_a_persons_answer_is_not_recordable_as_an_ordinary_step_outcome(
    workflows, runs,
) -> None:
    """[REQ-SB-103] The separation the whole requirement rests on: an
    agent running a Workflow cannot report "the person approved it" by
    reporting the step `done`. The outcome route refuses a step waiting
    on a person, by name."""
    run_id = start_a_run(THE_UNEDITABLE_WORKFLOW["id"])["run_id"]
    take_the_next_step(run_id)

    refused = report(run_id, "approve", "done")

    assert refused.status_code == 409
    assert "waiting for their answer" in refused.json()["detail"]
    assert step_of(stored_run(runs, run_id), "approve")["status"] == "awaiting_person"


def test_an_answer_to_a_step_that_is_not_waiting_on_a_person_is_refused(
    workflows, runs,
) -> None:
    """[REQ-SB-103] The mirror of the rule above: an Action step takes
    its outcome reported, never an answer recorded, so a caller cannot
    dress a dispatch up as somebody's approval."""
    run_id = start_a_run(THE_MIXED_WORKFLOW["id"])["run_id"]
    take_the_next_step(run_id)

    refused = answer(run_id, "find", "approved", said="looks right to me")

    assert refused.status_code == 409
    assert "not a step waiting on a person's answer" in refused.json()["detail"]


def test_a_question_with_an_unresolvable_reference_is_refused_not_asked(
    workflows, runs,
) -> None:
    """[REQ-SB-103] An unresolved reference in a QUESTION is as bad as
    one in an email body: "shall I send {{request.x}}?" is a question
    nobody can answer, and asking it spends a person's attention on a
    bug. The step is refused and names the reference."""
    run_id = start_a_run(THE_UNASKABLE_WORKFLOW["id"])["run_id"]

    nothing_asked = take_the_next_step(run_id)

    assert nothing_asked["status"] == "blocked"
    refused = step_of(stored_run(runs, run_id), "approve")
    assert refused["status"] == "refused"
    assert refused["asked_at"] is None, "nobody was asked"
    assert "nothing_was_supplied" in refused["refusal"]


def test_a_step_is_called_with_what_the_ask_was_about(workflows, runs) -> None:
    """[REQ-SB-103] "Tell me what is happening for a certain customer"
    -- the customer comes from the request the run was started with, and
    the Workflow names it rather than holding it."""
    run_id = start_a_run(THE_MIXED_WORKFLOW["id"], request={"customer": "a-named-customer"})["run_id"]

    assert stored_run(runs, run_id)["request"] == {"customer": "a-named-customer"}


def test_the_report_says_who_did_each_step(workflows, runs) -> None:
    """[REQ-SB-103] A report that read the same whether the app
    performed a step, an agent claimed it or a person approved it is
    the fabricated certainty this requirement exists against."""
    run_id = start_a_run(THE_UNEDITABLE_WORKFLOW["id"])["run_id"]
    take_the_next_step(run_id)
    answer(run_id, "approve", "approved", said="yes")

    finished = take_the_next_step(run_id)

    described = finished["report"]["steps"][0]
    assert described["kind"] == "human"
    assert described["performed_by"] == "human"
    assert described["human_decision"] == "approved"
    assert described["decided_by"]["display_name"] == THE_SIGNED_IN_PERSON
    assert finished["report"]["every_documented_step_done"] is True
