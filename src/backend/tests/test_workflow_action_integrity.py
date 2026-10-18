"""Referential integrity between a Workflow's steps and the Action
catalogue (REQ-SB-95-US-04-T02, ADR-032 "invalid by construction rather
than by review", ADR-034 "one direction only").

Two halves of one edge, and the tests below pin both plus the shape of
the edge itself:

- **Save time.** A step naming an action id the catalogue does not have
  is refused before anything is written, naming WHICH step and WHICH id
  -- an operator cannot act on "invalid workflow". A refused update
  leaves the stored definition exactly as it was.
- **Delete time.** Deleting an Action a Workflow step names is refused,
  naming the referencing Workflows, and removes nothing. The question
  is asked of the Workflow side on every delete; nothing about
  Workflows is ever stored on an Action, which is asserted literally by
  comparing the stored Action.json byte for byte before and after a
  Workflow starts referencing it.
- **One direction, no cycle.** `workflow_manager.py` imports
  `ActionManager` at module scope; `action_manager.py` imports nothing
  from the workflows package at module scope, which is what keeps that
  legal.

No real store is touched: both stores are in-memory fakes keyed by id,
the way tests/test_actions_api.py and tests/test_workflow_artifact_kind.py
already fake theirs, and the resolution sources are controlled because
what is deployed on the machine running the suite is instance state.

The catalogue-publication trigger is replaced by a counter here, which
TIGHTENS rather than bypasses the suite-wide Hermes sandbox in
tests/conftest.py: these tests then spawn no background thread at all,
and "a refused delete publishes nothing" becomes an assertion instead of
a silence.
"""
import ast
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.main as main_app
from app.business.core.actions.action_manager import (
    ActionManager,
    ActionReferencedByWorkflowError,
)
from app.business.core.workflows.workflow_manager import (
    WorkflowManager,
    WorkflowStepActionNotFoundError,
)

client = TestClient(main_app.app)

A_DEPLOYED_SKILL = "email-thread-capture"
LIST_THE_TEAMS_ACTIONS = "list-team-actions"
SEND_THE_MAIL = "send-mail"
# Catalogued and named by no step of any Workflow these tests build --
# the control case for "the guard refuses referenced Actions and only
# those".
AN_UNREFERENCED_ACTION = "append-capture"
AN_UNCATALOGUED_ACTION = "post-to-slack"


@pytest.fixture(autouse=True)
def resolvable_implementations(monkeypatch) -> None:
    """Every Action these tests catalogue names one deployed Skill, so
    the save-time RESOLUTION gate (REQ-SB-95-US-02-T02) never decides
    the outcome of a test about REFERENTIAL integrity."""
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.deployed_skill_ids",
        lambda: {A_DEPLOYED_SKILL},
    )


@pytest.fixture(autouse=True)
def publications(monkeypatch) -> list:
    """Every catalogue publication this file triggers, counted and not
    performed."""
    fired: list = []
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.publish_action_catalogue_in_background",
        lambda: fired.append(True),
    )
    return fired


@pytest.fixture
def stored_actions(monkeypatch) -> dict:
    """The Action store, in memory, keyed by action id."""
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
    return written


@pytest.fixture
def action_deletions(monkeypatch, stored_actions) -> list:
    """Records every real deletion, so "delete_action_definition was
    never called" is an assertion rather than an absence of
    evidence."""
    deleted: list = []

    def delete(action_id: str) -> None:
        deleted.append(action_id)
        stored_actions.pop(action_id, None)

    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.delete_action_definition", delete,
    )
    return deleted


@pytest.fixture
def stored_workflows(monkeypatch) -> dict:
    """The Workflow store, in memory, keyed by workflow id. Raises
    FileNotFoundError for an unknown id exactly as the real
    read_workflow_json does."""
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
def workflow_writes(monkeypatch, stored_workflows) -> list:
    """Every write attempt against the Workflow store, so "nothing was
    written" is measured rather than inferred from an empty store."""
    attempts: list = []

    def write(workflow_id: str, data: dict) -> None:
        attempts.append(workflow_id)
        stored_workflows[workflow_id] = data

    monkeypatch.setattr(
        "app.business.core.workflows.workflow_manager.workflows_data.write_workflow_json", write,
    )
    return attempts


@pytest.fixture
def the_catalogue(stored_actions) -> ActionManager:
    """Three real catalogued Actions -- the PRD's own motivating intent
    (list the Actions assigned to my team, then mail them to me), plus
    one no Workflow here ever references."""
    manager = ActionManager()
    for action_id in (LIST_THE_TEAMS_ACTIONS, SEND_THE_MAIL, AN_UNREFERENCED_ACTION):
        manager.create(
            action_id,
            description=f"The {action_id} operation",
            implementation={"skill": {"skill_id": A_DEPLOYED_SKILL}},
        )
    return manager


def _three_steps(second_step_action_id: str) -> list[dict]:
    return [
        {"id": "collect", "action_id": LIST_THE_TEAMS_ACTIONS, "inputs": {"team": "CBO"}},
        {"id": "send", "action_id": second_step_action_id, "needs_confirmation": True},
        {"id": "log", "action_id": LIST_THE_TEAMS_ACTIONS, "description": "Leave a trace"},
    ]


# -- Save time: a step cannot name an Action that does not exist --


def test_a_step_naming_an_unknown_action_is_refused_naming_the_step_and_the_id(
    the_catalogue, workflow_writes,
) -> None:
    """[REQ-SB-95-US-04-AC-02] The refusal names step 2 and the unknown
    id, because the operator is looking at an ordered editor and has to
    know which row to fix -- and NOTHING reaches the store."""
    with pytest.raises(WorkflowStepActionNotFoundError) as refusal:
        WorkflowManager().create(
            "mail-me-the-team-list",
            request_kind="Give me my team's actions by mail",
            steps=_three_steps(AN_UNCATALOGUED_ACTION),
        )

    message = str(refusal.value)
    assert "step 2" in message, message
    assert repr(AN_UNCATALOGUED_ACTION) in message, message
    assert workflow_writes == [], "a refused save must not write a half-valid Workflow"


def test_a_workflow_whose_every_step_is_catalogued_is_written(
    the_catalogue, workflow_writes, stored_workflows,
) -> None:
    """[REQ-SB-95-US-04-AC-02] The same Workflow, with every step naming
    a real catalogued Action, saves -- validation refuses the unknown
    id and nothing else."""
    created = WorkflowManager().create(
        "mail-me-the-team-list",
        request_kind="Give me my team's actions by mail",
        steps=_three_steps(SEND_THE_MAIL),
    )

    assert workflow_writes == ["mail-me-the-team-list"]
    assert list(stored_workflows) == ["mail-me-the-team-list"]
    assert [step.action_id for step in created.steps] == [
        LIST_THE_TEAMS_ACTIONS, SEND_THE_MAIL, LIST_THE_TEAMS_ACTIONS,
    ]
    assert [step.needs_confirmation for step in created.steps] == [False, True, False]


def test_pointing_a_stored_workflow_at_an_unknown_action_leaves_it_unchanged(
    the_catalogue, workflow_writes, stored_workflows,
) -> None:
    """[REQ-SB-95-US-04-AC-02] An edit is held to the catalogue afresh,
    and a refused edit leaves the stored definition byte for byte as it
    was -- not merely "mostly unchanged"."""
    manager = WorkflowManager()
    manager.create("mail-me-the-team-list", steps=_three_steps(SEND_THE_MAIL))
    before = json.dumps(stored_workflows["mail-me-the-team-list"], sort_keys=True)

    with pytest.raises(WorkflowStepActionNotFoundError) as refusal:
        manager.update("mail-me-the-team-list", steps=_three_steps(AN_UNCATALOGUED_ACTION))

    assert "step 2" in str(refusal.value)
    assert json.dumps(stored_workflows["mail-me-the-team-list"], sort_keys=True) == before
    assert workflow_writes == ["mail-me-the-team-list"], "only the first, valid save wrote"
    assert [step.action_id for step in manager.get_by_id("mail-me-the-team-list").steps] == [
        LIST_THE_TEAMS_ACTIONS, SEND_THE_MAIL, LIST_THE_TEAMS_ACTIONS,
    ]


def test_a_step_naming_no_action_at_all_is_refused_by_the_same_rule(
    the_catalogue, workflow_writes,
) -> None:
    """[REQ-SB-95-US-04-AC-02] "No Workflow may ever be left holding a
    step that points at nothing" covers the empty id too, which would
    otherwise pass straight through as a step naming ''."""
    with pytest.raises(WorkflowStepActionNotFoundError) as refusal:
        WorkflowManager().create("half-written", steps=[
            {"id": "collect", "action_id": LIST_THE_TEAMS_ACTIONS},
            {"id": "send", "action_id": ""},
        ])

    assert "step 2" in str(refusal.value)
    assert workflow_writes == []


# -- Delete time: the reverse lookup, computed and never stored --


def _a_workflow_referencing(action_id: str) -> None:
    WorkflowManager().create("mail-me-the-team-list", request_kind="The team list by mail", steps=[
        {"id": "collect", "action_id": LIST_THE_TEAMS_ACTIONS},
        {"id": "send", "action_id": action_id},
    ])


def test_deleting_an_action_a_workflow_step_names_is_refused_naming_the_workflows(
    the_catalogue, stored_workflows, action_deletions, stored_actions, publications,
) -> None:
    """[REQ-SB-95-US-04-AC-06] Over the real HTTP surface, because the
    operator meets this refusal at a screen: one 409 carrying the
    Manager's own sentence, which names the referencing Workflow. The
    Action is still catalogued afterwards and the Workflow still holds
    its step."""
    _a_workflow_referencing(SEND_THE_MAIL)
    publications.clear()

    refused = client.delete(f"/actions/{SEND_THE_MAIL}")

    assert refused.status_code == 409, refused.text
    assert "mail-me-the-team-list" in refused.json()["detail"]
    assert SEND_THE_MAIL in refused.json()["detail"]
    assert action_deletions == [], "nothing may be removed before the operator has cleared the step"
    assert SEND_THE_MAIL in stored_actions
    assert publications == [], "a refused delete changed no catalogue, so it publishes nothing"
    still_there = WorkflowManager().get_by_id("mail-me-the-team-list")
    assert [step.action_id for step in still_there.steps] == [
        LIST_THE_TEAMS_ACTIONS, SEND_THE_MAIL,
    ]


def test_the_manager_refuses_the_same_deletion_whatever_door_it_came_through(
    the_catalogue, stored_workflows, action_deletions,
) -> None:
    """[REQ-SB-95-US-04-AC-06] The guard is the Manager's, not the
    router's: a caller holding ActionManager directly is refused by the
    same rule with the same sentence, which is what makes "invalid by
    construction" true of the backend rather than of one route."""
    _a_workflow_referencing(SEND_THE_MAIL)

    with pytest.raises(ActionReferencedByWorkflowError) as refusal:
        ActionManager().delete(SEND_THE_MAIL)

    assert "mail-me-the-team-list" in str(refusal.value)
    assert action_deletions == []


def test_an_action_no_workflow_references_deletes_normally(
    the_catalogue, stored_workflows, action_deletions, stored_actions,
) -> None:
    """[REQ-SB-95-US-04-AC-06] The guard refuses referenced Actions and
    only those: an unreferenced one deletes exactly as it did before the
    Workflow kind existed, including the {"deleted": False} an unknown
    id has always returned."""
    _a_workflow_referencing(SEND_THE_MAIL)

    deleted = client.delete(f"/actions/{AN_UNREFERENCED_ACTION}")

    assert deleted.status_code == 200, deleted.text
    assert deleted.json() == {"deleted": True}
    assert action_deletions == [AN_UNREFERENCED_ACTION]
    assert AN_UNREFERENCED_ACTION not in stored_actions
    assert client.delete("/actions/never-existed").json() == {"deleted": False}


def test_an_action_record_gains_no_workflow_reference_field(
    the_catalogue, stored_workflows, stored_actions, action_deletions,
) -> None:
    """[REQ-SB-95-US-04-AC-06] The edge runs one direction only: the
    stored Action.json is byte-identical before a Workflow references
    it, after it does, and after a delete that referencing refused."""
    before = json.dumps(stored_actions[SEND_THE_MAIL], sort_keys=True)

    _a_workflow_referencing(SEND_THE_MAIL)
    assert json.dumps(stored_actions[SEND_THE_MAIL], sort_keys=True) == before

    with pytest.raises(ActionReferencedByWorkflowError):
        ActionManager().delete(SEND_THE_MAIL)

    assert json.dumps(stored_actions[SEND_THE_MAIL], sort_keys=True) == before
    assert "workflow" not in before.lower(), "no back-reference field, not even an empty one"


# -- The shape of the edge: one direction, no cycle, pinned cost --


def test_the_action_side_imports_nothing_from_the_workflows_package_at_module_scope() -> None:
    """[REQ-SB-95-US-04-AC-06] What keeps the save-time half legal.
    `workflow_manager.py` imports `ActionManager` at module scope, so a
    module-scope import back would be a cycle -- the reverse lookup
    defers its import inside the function instead, the same shape
    `AgentManager._action_catalogue()` already uses against this module.
    """
    from app.business.core.actions import action_manager as action_manager_module
    from app.business.core.workflows import workflow_manager as workflow_manager_module

    tree = ast.parse(Path(action_manager_module.__file__).read_text(encoding="utf-8"))
    module_scope_imports = [
        node.module or ""
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
    ]

    assert not [name for name in module_scope_imports if "workflow" in name], (
        "a module-scope import of the workflows package would close an import cycle"
    )
    assert any("workflow" in (node.module or "") for node in ast.walk(tree)
               if isinstance(node, ast.ImportFrom)), "the deferred import is still there"

    workflow_manager_source = Path(workflow_manager_module.__file__).read_text(encoding="utf-8")
    assert any(
        "actions.action_manager" in (node.module or "")
        for node in ast.parse(workflow_manager_source).body
        if isinstance(node, ast.ImportFrom)
    ), "the Workflow side is the one that imports at module scope"


def test_validating_a_save_reads_the_catalogue_once_and_a_delete_scans_workflows_once(
    monkeypatch, the_catalogue, stored_workflows, action_deletions,
) -> None:
    """[REQ-SB-95-US-04-AC-02][REQ-SB-95-US-04-AC-06] Cost pinned by
    equality, not by a bound (BUG-086 was a slowness bug of exactly that
    shape).

    A three-step save must cost the SAME catalogue read as a one-step
    save -- reading it per step is the O(steps x catalogue) shape the
    Action side's own `_ResolutionSources` exists to avoid. A delete
    must scan the Workflow store once, and an unknown id must not scan
    it at all.
    """
    counts = {"list_actions": 0, "read_action": 0, "list_workflows": 0, "read_workflow": 0}
    from app.business.core.actions import action_manager as action_manager_module
    from app.business.core.workflows import workflow_manager as workflow_manager_module

    def counted(counter: str, real):
        def wrapper(*args, **kwargs):
            counts[counter] += 1
            return real(*args, **kwargs)
        return wrapper

    monkeypatch.setattr(action_manager_module.actions_data, "list_action_ids",
                        counted("list_actions", action_manager_module.actions_data.list_action_ids))
    monkeypatch.setattr(action_manager_module.actions_data, "read_action_json",
                        counted("read_action", action_manager_module.actions_data.read_action_json))
    monkeypatch.setattr(workflow_manager_module.workflows_data, "list_workflow_ids",
                        counted("list_workflows",
                                workflow_manager_module.workflows_data.list_workflow_ids))
    monkeypatch.setattr(workflow_manager_module.workflows_data, "read_workflow_json",
                        counted("read_workflow",
                                workflow_manager_module.workflows_data.read_workflow_json))

    WorkflowManager().create("mail-me-the-team-list", steps=_three_steps(SEND_THE_MAIL))

    # get_all() lists the store twice -- once for the stored Actions and
    # once inside the plugin-contributed composition -- and reads each of
    # the three catalogued Actions once. THREE steps, ONE catalogue read:
    # the numbers below are a property of the catalogue, not of the
    # Workflow's length.
    assert counts["list_actions"] == 2
    assert counts["read_action"] == 3

    counts.update(list_actions=0, read_action=0)
    WorkflowManager().create("just-mail-it", steps=[
        {"id": "send", "action_id": SEND_THE_MAIL},
    ])

    assert counts["list_actions"] == 2, "a one-step save costs the same catalogue read as a three"
    assert counts["read_action"] == 3

    counts.update(list_workflows=0, read_workflow=0)
    with pytest.raises(ActionReferencedByWorkflowError):
        ActionManager().delete(SEND_THE_MAIL)

    assert counts["list_workflows"] == 1, "the Workflow store is scanned once per delete"
    assert counts["read_workflow"] == 2, "one read per stored Workflow (there are two), none per step"

    counts.update(list_workflows=0, read_workflow=0)
    assert ActionManager().delete("never-existed") == {"deleted": False}
    assert counts["list_workflows"] == 0, "an id that deletes nothing scans nothing"
    assert counts["read_workflow"] == 0
