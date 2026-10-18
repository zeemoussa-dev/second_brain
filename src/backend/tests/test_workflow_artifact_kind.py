"""Workflow becomes the seventh artifact kind (REQ-SB-95-US-04, ADR-032,
ADR-034).

The Action precedent (REQ-SB-95-US-02-T01, itself the Index precedent)
is the shape this follows, so these tests pin what makes a Workflow a
real stored artifact rather than a dict passing through:

- **Order is data.** The steps come back in the order they were saved,
  with the same per-step confirmation flags and the same report
  definition -- and a reorder really reorders, dropping and duplicating
  nothing. ADR-034 makes "in order" and "no skipped step" properties of
  a run record, which is only worth anything if the stored order is
  exactly what the operator documented.
- **Its own store**, at the data path's own data/Workflows/<id>/
  Workflow.json.
- **Nothing shared with Pipeline** (ADR-032; US-04 Scenario 7): neither
  the Manager nor its data access imports anything from
  business/core/pipelines/, and a real save puts nothing anywhere near
  the Pipeline store.

No real data path is touched: write/read/list/delete are monkeypatched
the way tests/test_action_artifact_kind.py already does, except in the
two tests that are specifically ABOUT where bytes land, which point
settings at a tmp dir.

Referential integrity with the Action catalogue is deliberately absent
here -- T02 owns it. T01 stores what it is given, in order.
"""
import ast
from pathlib import Path

import pytest

from app.business.core.workflows import workflow_manager as workflow_manager_module
from app.business.core.workflows.workflow_manager import WorkflowManager
from app.config import settings
from app.data_access import workflows as workflows_data


def _three_ordered_steps() -> list[dict]:
    """The PRD's own motivating intent: list the Actions assigned to my
    team, then mail them to me -- with the sending step the one the
    operator wants to confirm."""
    return [
        {"id": "collect", "action_id": "list-team-actions",
         "inputs": {"team": "CBO"}, "description": "Collect the team's open Actions"},
        {"id": "send", "action_id": "send-mail", "inputs": {"to": "{{operator.self_email}}"},
         "needs_confirmation": True, "description": "Mail the list to me"},
        {"id": "log", "action_id": "append-capture", "inputs": {"note": "sent"},
         "description": "Leave a trace in the vault"},
    ]


@pytest.fixture
def stored_workflows(monkeypatch) -> dict:
    """The whole store, in memory, keyed by workflow id.

    An unknown id raises `FileNotFoundError`, exactly as the real
    `read_workflow_json` does -- a fake that raised `KeyError` instead
    would sail past the Manager's own `(OSError, ValueError)` handling
    and make "an unknown id is answered, not raised" untestable.
    """
    written: dict = {}

    def read(workflow_id):
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
def store_call_counts(monkeypatch, stored_workflows) -> dict:
    """How many raw reads/lists/writes each Manager call really costs.
    Counted so the assertions below can pin cost by EQUALITY -- a bound
    like "fewer than ten reads" is what let BUG-086's measured slowness
    sit unnoticed."""
    counts = {"read": 0, "list": 0, "write": 0}
    data_access = workflow_manager_module.workflows_data
    read, list_ids, write = (
        data_access.read_workflow_json,
        data_access.list_workflow_ids,
        data_access.write_workflow_json,
    )

    def counted_read(workflow_id):
        counts["read"] += 1
        return read(workflow_id)

    def counted_list():
        counts["list"] += 1
        return list_ids()

    def counted_write(workflow_id, data):
        counts["write"] += 1
        return write(workflow_id, data)

    monkeypatch.setattr(data_access, "read_workflow_json", counted_read)
    monkeypatch.setattr(data_access, "list_workflow_ids", counted_list)
    monkeypatch.setattr(data_access, "write_workflow_json", counted_write)
    return counts


def test_a_saved_workflow_round_trips_its_ordered_steps_and_report(stored_workflows) -> None:
    """[REQ-SB-95-US-04-AC-01] An id, the kind of request it handles,
    three ordered steps with the second marked for confirmation, and a
    report definition -- all of it written under its own id and read
    back identically."""
    created = WorkflowManager().create(
        "mail-me-the-team-list",
        request_kind="list the Actions assigned to my team and mail them to me",
        description="The operator's standing handling for this ask",
        steps=_three_ordered_steps(),
        report={"description": "the list that was sent, and to whom",
                "include_step_ids": ["collect", "send"]},
    )

    # Written under its OWN id, at that id's own definition.
    assert list(stored_workflows) == ["mail-me-the-team-list"]
    assert stored_workflows["mail-me-the-team-list"]["id"] == "mail-me-the-team-list"
    assert created.id == "mail-me-the-team-list"

    reopened = WorkflowManager().get_by_id("mail-me-the-team-list")
    assert reopened.request_kind == "list the Actions assigned to my team and mail them to me"
    assert [(s.id, s.action_id, s.needs_confirmation) for s in reopened.steps] == [
        ("collect", "list-team-actions", False),
        ("send", "send-mail", True),
        ("log", "append-capture", False),
    ]
    # Each step's own inputs survive with it -- the step, not the
    # Workflow, is what carries them.
    assert [s.inputs for s in reopened.steps] == [
        {"team": "CBO"}, {"to": "{{operator.self_email}}"}, {"note": "sent"},
    ]
    assert reopened.report.description == "the list that was sent, and to whom"
    assert reopened.report.include_step_ids == ["collect", "send"]

    catalogue = WorkflowManager().get_all()
    assert [(w.id, w.request_kind, len(w.steps)) for w in catalogue] == [
        ("mail-me-the-team-list", "list the Actions assigned to my team and mail them to me", 3),
    ]


def test_the_store_is_the_data_paths_own_workflows_folder(monkeypatch, tmp_path) -> None:
    """[REQ-SB-95-US-04-AC-01] ADR-032 fixes the store at
    <DATA_PATH>/data/Workflows/<id>/Workflow.json -- instance data in
    the App Database Folder, never the repository."""
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path)

    assert workflows_data.workflow_file("mail-me-the-team-list") == (
        tmp_path / "data" / "Workflows" / "mail-me-the-team-list" / "Workflow.json"
    )

    workflows_data.write_workflow_json("mail-me-the-team-list", {"id": "mail-me-the-team-list"})
    assert (tmp_path / "data" / "Workflows" / "mail-me-the-team-list" / "Workflow.json").is_file()
    assert workflows_data.list_workflow_ids() == ["mail-me-the-team-list"]
    assert workflows_data.read_workflow_json("mail-me-the-team-list")["id"] == "mail-me-the-team-list"


def test_reordering_the_steps_saves_and_returns_the_new_order(stored_workflows) -> None:
    """[REQ-SB-95-US-04-AC-01] The operator's documented order is the
    whole point: a reorder must really move the steps, and must not
    drop or duplicate one on the way."""
    manager = WorkflowManager()
    manager.create("mail-me-the-team-list", request_kind="mail me the team list",
                   steps=_three_ordered_steps(), report={"description": "what was sent"})

    original = manager.get_by_id("mail-me-the-team-list").steps
    reordered = [original[2], original[0], original[1]]
    manager.update("mail-me-the-team-list", steps=[
        {"id": s.id, "action_id": s.action_id, "inputs": s.inputs,
         "needs_confirmation": s.needs_confirmation, "description": s.description}
        for s in reordered
    ])

    reopened = WorkflowManager().get_by_id("mail-me-the-team-list")
    assert [s.id for s in reopened.steps] == ["log", "collect", "send"]
    # Nothing dropped, nothing duplicated, and each step kept its own
    # confirmation flag rather than the flag of the position it moved to.
    assert len(reopened.steps) == 3
    assert len({s.id for s in reopened.steps}) == 3
    assert [s.needs_confirmation for s in reopened.steps] == [False, False, True]
    assert [s.action_id for s in reopened.steps] == ["append-capture", "list-team-actions", "send-mail"]
    # The order on disk is the order read back -- nothing re-sorts it.
    assert [s["id"] for s in stored_workflows["mail-me-the-team-list"]["steps"]] == [
        "log", "collect", "send",
    ]
    assert reopened.report.description == "what was sent"


def test_an_imported_workflow_keeps_its_documented_step_order(stored_workflows) -> None:
    """[REQ-SB-95-US-04-AC-01] The import provisioning path (ADR-015) is
    a write path like any other: a bundle that re-ordered an operator's
    documented handling on the way in would be the same silent
    corruption as re-ordering it on save."""
    imported = WorkflowManager().import_workflow("mail-me-the-team-list", {
        "request_kind": "mail me the team list",
        "steps": _three_ordered_steps(),
        "report": {"description": "what was sent"},
    })

    assert [s.id for s in imported.steps] == ["collect", "send", "log"]
    assert [s.needs_confirmation for s in imported.steps] == [False, True, False]


def test_a_step_without_an_id_is_given_one_that_survives_a_reorder(stored_workflows) -> None:
    """[REQ-SB-95-US-04-AC-01] A run addresses one step at a time by id
    (ADR-034), so every stored step needs one -- and it must not be its
    position, or moving a step would silently re-point its id at a
    different step."""
    manager = WorkflowManager()
    manager.create("two-steps", steps=[
        {"action_id": "list-team-actions"},
        {"action_id": "send-mail", "needs_confirmation": True},
    ])

    minted = [s.id for s in manager.get_by_id("two-steps").steps]
    assert all(minted) and len(set(minted)) == 2

    manager.update("two-steps", steps=[
        {"id": minted[1], "action_id": "send-mail", "needs_confirmation": True},
        {"id": minted[0], "action_id": "list-team-actions"},
    ])

    swapped = manager.get_by_id("two-steps").steps
    assert [s.id for s in swapped] == [minted[1], minted[0]]
    assert [s.action_id for s in swapped] == ["send-mail", "list-team-actions"]


def test_reading_a_workflow_costs_exactly_one_read(store_call_counts) -> None:
    """[REQ-SB-95-US-04-AC-01] Pinned by equality, not by a bound: six
    tasks build on this Manager, and a get_by_id that quietly grew a
    second read would multiply across every one of them (BUG-086 was a
    measured slowness of exactly this shape)."""
    manager = WorkflowManager()
    for workflow_id in ("one", "two", "three"):
        manager.create(workflow_id, steps=_three_ordered_steps())

    # Each create(): one write, then one read to return what was saved.
    assert store_call_counts == {"write": 3, "read": 3, "list": 0}

    store_call_counts.update({"read": 0, "list": 0, "write": 0})
    manager.get_by_id("one")
    assert store_call_counts == {"read": 1, "list": 0, "write": 0}

    store_call_counts.update({"read": 0, "list": 0, "write": 0})
    assert len(manager.get_all()) == 3
    # One listing, then one read per Workflow -- no per-step read, and
    # no second pass over the store.
    assert store_call_counts == {"list": 1, "read": 3, "write": 0}


def test_deleting_a_workflow_removes_only_its_own_definition(stored_workflows) -> None:
    """[REQ-SB-95-US-04-AC-01] An unknown id is {"deleted": False}, never
    an exception (ADR-014's result-dict convention), and deleting one
    Workflow leaves the others alone."""
    manager = WorkflowManager()
    manager.create("keep-me", steps=_three_ordered_steps())
    manager.create("delete-me", steps=_three_ordered_steps())

    assert manager.delete("delete-me") == {"deleted": True}
    assert manager.delete("delete-me") == {"deleted": False}
    assert manager.delete("never-existed") == {"deleted": False}
    assert list(stored_workflows) == ["keep-me"]
    # The same "answered, never raised" contract on the read and update
    # sides, so a caller never has to guess which one throws.
    assert manager.get_by_id("never-existed") is None
    assert manager.update("never-existed", description="nothing to update") is None


# -- Nothing shared with Pipeline (US-04 Scenario 7) --------------------

def _imported_module_names(module_path: Path) -> set[str]:
    """Every module name this file imports, read off its syntax tree --
    so the assertion is about the source itself and cannot be satisfied
    by an import that merely happens not to run."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(module_path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
    return names


def test_the_workflow_kind_imports_nothing_from_pipelines() -> None:
    """[REQ-SB-95-US-04-AC-07] ADR-032 leaves Pipeline exactly as it is.
    PipelineManager was read as shape reference and nothing more -- no
    shared Manager, no shared entity, no migration helper."""
    for module in (workflow_manager_module, workflows_data):
        imported = _imported_module_names(Path(module.__file__))
        assert not [name for name in imported if "pipeline" in name.lower()], (
            f"{Path(module.__file__).name} imports something from Pipeline"
        )


def test_saving_a_workflow_writes_nothing_outside_its_own_store(monkeypatch, tmp_path) -> None:
    """[REQ-SB-95-US-04-AC-07] The other half of "nothing shared": a real
    save against a real (temporary) data path puts bytes in exactly one
    place, and the Pipeline store -- <DATA_PATH>/pipelines/ -- is not
    created, read or touched."""
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path)

    WorkflowManager().create(
        "mail-me-the-team-list",
        request_kind="mail me the team list",
        steps=_three_ordered_steps(),
        report={"description": "what was sent"},
    )

    written = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    assert written == [
        "data",
        "data/Workflows",
        "data/Workflows/mail-me-the-team-list",
        "data/Workflows/mail-me-the-team-list/Workflow.json",
    ]
    assert not (tmp_path / "pipelines").exists()
