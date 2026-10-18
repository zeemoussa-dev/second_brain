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

`REQ-SB-95-US-04-T04` extended this file with the other half of being an
artifact kind: appearing in the cross-kind inventory, and actually
travelling in an `.sbf` bundle -- the dependency closure, the secret
scan, the export payload folder and the import dispatch. Those tests
live below the `-- The seventh kind across the artifact machinery --`
banner and pin, above all, two things: that a Workflow carries the
Actions its steps name (or it arrives in exactly the state T02's save
gate refuses), and that adding the seventh kind changed nothing about
the six that were already there.
"""
import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.business.core.workflows import workflow_manager as workflow_manager_module
from app.business.core.workflows.workflow_manager import (
    WorkflowManager,
    WorkflowStepActionNotFoundError,
)
from app.business.logic import (
    artifact_dependency_resolver,
    artifact_export,
    artifact_import,
    artifact_secret_scan,
    artifacts_inventory,
    sbf_archive,
)
from app.config import settings
from app.data_access import pipelines as pipelines_data
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


# The three ids every step fixture in this file names. They are invented
# for these tests and exist in no install's catalogue.
THE_ACTION_IDS_THESE_FIXTURES_NAME = ("list-team-actions", "send-mail", "append-capture")


@pytest.fixture(autouse=True)
def the_fixtures_action_ids_are_catalogued(monkeypatch) -> None:
    """These tests are about step order, step identity and cost -- never
    about what this install has catalogued (ESC-075, authorised
    2026-10-18; ESC-064 is the same case one kind earlier).

    `T02` added `ADR-034`'s save-time referential check, which refuses a
    step naming an action id the catalogue does not have. That is the
    locked `AC-02` behaviour working, so the fixtures are what move:
    the three invented ids above are catalogued here, for this file
    only, and not one assertion below changes.

    **The real store is put out of reach, not merely satisfied.** The
    whole `ActionManager` the Manager reaches for is replaced, so no
    code path from these tests can read the operator's own
    `<DATA_PATH>/data/Actions/` -- returning the right ids from the real
    Manager would still leave a test about step order passing or failing
    by accident of what this machine happens to have catalogued, which
    is the instance-state dependency `ESC-064`'s resolution called out.
    """
    class TheCatalogueTheseTestsAssume:
        def get_all(self) -> list:
            return [SimpleNamespace(id=action_id)
                    for action_id in THE_ACTION_IDS_THESE_FIXTURES_NAME]

    monkeypatch.setattr(
        "app.business.core.workflows.workflow_manager.ActionManager",
        TheCatalogueTheseTestsAssume,
    )


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


# -- The seventh kind across the artifact machinery (REQ-SB-95-US-04-T04) --
#
# A Workflow that cannot travel in a bundle is a local note, not an
# artifact. These tests cover the measured touch points the Action
# precedent (REQ-SB-95-US-02-T04, itself the Index precedent, ADR-019)
# already went through: the inventory, the dependency closure, the
# export payload folder, the secret scan and the import dispatch.
#
# The genuinely new edge is Workflow -> Action -> Skill. It is not a
# nicety: ADR-032 makes a step naming an uncatalogued Action invalid by
# construction, and T02's save gate refuses exactly that -- so a bundle
# that carried a Workflow without its Actions would land on the
# receiving install in the one state this install refuses to create.

# The two Actions the closure tests use, as they are really STORED.
# Written straight into the in-memory store rather than through
# `ActionManager.create()` on purpose: create() resolves a `skill`
# implementation against this machine's really-deployed Skills and a
# `ui` one against the registered feature keys, so going through it
# would make these tests pass or fail by accident of what the machine
# running them happens to have installed.
A_SKILL_IMPLEMENTED_ACTION = {
    "id": "list-team-actions",
    "description": "List the Actions assigned to my team",
    "inputs": [{"name": "team", "type": "string", "required": True}],
    "allowed_callers": ["cbo-agent"],
    "needs_confirmation": False,
    "implementation": {"skill": {"skill_id": "vault-search"}},
}
A_UI_IMPLEMENTED_ACTION = {
    "id": "send-mail",
    "description": "Send the operator an email",
    "inputs": [{"name": "to", "type": "string", "required": True}],
    "allowed_callers": ["cbo-agent"],
    "needs_confirmation": True,
    "implementation": {"ui": {"feature_key": "/settings/actions"}},
}


def _two_steps_naming_two_actions() -> list[dict]:
    """The PRD's motivating intent, trimmed to the two Actions the
    closure assertions name: one `skill`-implemented, one `ui`."""
    return [
        {"id": "collect", "action_id": "list-team-actions", "inputs": {"team": "CBO"},
         "description": "Collect the team's open Actions"},
        {"id": "send", "action_id": "send-mail", "inputs": {"to": "{{operator.self_email}}"},
         "needs_confirmation": True, "description": "Mail the list to me"},
    ]


class _FixedManager:
    """Stands in for one real Manager, answering from a fixed list.

    The live inventory reads this install's real Registry and its real
    Hermes cron jobs, so asserting against it would be asserting about
    the machine running the test rather than about the code."""

    def __init__(self, entities=()) -> None:
        self._entities = list(entities)

    def get_all(self) -> list:
        return list(self._entities)

    def get_by_id(self, entity_id: str):
        return next((entity for entity in self._entities if entity.id == entity_id), None)


@pytest.fixture
def stored_actions(monkeypatch) -> dict:
    """The whole Action store, in memory, keyed by action id -- faithful
    about a MISSING id, the same way `stored_workflows` above is.

    Patching the attribute on the shared `app.data_access.actions` module
    object is what puts the real `<DATA_PATH>/data/Actions/` out of reach
    for EVERY reader of it at once: the Manager, the dependency
    resolver, the export's content reader and the secret scan all hold a
    reference to that one module."""
    written: dict = {}

    def read(action_id: str) -> dict:
        if action_id not in written:
            raise FileNotFoundError(f"No Action.json for {action_id!r}")
        return written[action_id]

    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.read_action_json", read,
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.write_action_json",
        lambda action_id, data: written.update({action_id: data}),
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.list_action_ids",
        lambda: sorted(written),
    )
    return written


@pytest.fixture
def the_two_actions_the_steps_name(stored_actions) -> dict:
    stored_actions.update({
        "list-team-actions": dict(A_SKILL_IMPLEMENTED_ACTION),
        "send-mail": dict(A_UI_IMPLEMENTED_ACTION),
    })
    return stored_actions


@pytest.fixture
def the_six_pre_existing_kinds(monkeypatch) -> list[dict]:
    """The six Managers the inventory composed before Workflow, pinned
    to one fixed entry each. Returns the exact entries they must always
    produce, so "no pre-existing kind changed" is a real equality
    assertion and not a count."""
    monkeypatch.setattr(artifacts_inventory, "_skill_manager", _FixedManager([
        SimpleNamespace(id="vault-search", name="Vault Search", description="Search the vault"),
    ]))
    monkeypatch.setattr(artifacts_inventory, "_template_manager", _FixedManager([
        SimpleNamespace(id="Meeting", note_name="Meeting", error=None),
    ]))
    monkeypatch.setattr(artifacts_inventory, "_agent_manager", _FixedManager([
        SimpleNamespace(id="cbo-agent", name="CBO Agent", description="Chief of staff"),
    ]))
    monkeypatch.setattr(artifacts_inventory, "_pipeline_manager", _FixedManager([
        SimpleNamespace(id="morning-sweep", name="Morning Sweep", description="Sweeps the inbox"),
    ]))
    monkeypatch.setattr(artifacts_inventory, "_index_manager", _FixedManager([
        SimpleNamespace(id="adnoc", name="ADNOC"),
    ]))
    monkeypatch.setattr(artifacts_inventory, "_action_manager", _FixedManager([
        SimpleNamespace(id="send-mail", description="Send the operator an email"),
    ]))
    return [
        {"kind": "skill", "id": "vault-search", "name": "Vault Search", "description": "Search the vault"},
        {"kind": "template", "id": "Meeting", "name": "Meeting", "description": "Meeting"},
        {"kind": "agent", "id": "cbo-agent", "name": "CBO Agent", "description": "Chief of staff"},
        {"kind": "pipeline", "id": "morning-sweep", "name": "Morning Sweep", "description": "Sweeps the inbox"},
        {"kind": "index", "id": "adnoc", "name": "ADNOC", "description": ""},
        {"kind": "action", "id": "send-mail", "name": "send-mail",
         "description": "Send the operator an email"},
    ]


@pytest.fixture
def closure_sources(monkeypatch) -> None:
    """The resolver's and the export's non-Workflow, non-Action inputs,
    pinned. The Workflow branch is what is under test; the Actions it
    pulls in and the Skill one of those runs have to be real, resolvable
    entries for the closure to contain them at all, and
    `_skill_own_template_matches` statically scans the Skill's own text,
    which would otherwise be a live disk read."""
    monkeypatch.setattr(artifact_dependency_resolver, "_skill_manager", _FixedManager([
        SimpleNamespace(id="vault-search", name="Vault Search", description="Search the vault"),
    ]))
    monkeypatch.setattr(artifact_dependency_resolver, "_template_manager", _FixedManager([]))
    monkeypatch.setattr(
        "app.data_access.skills.read_skill_md",
        lambda skill_id: "---\nname: Vault Search\n---\nSearches the vault.\n",
    )
    monkeypatch.setattr("app.data_access.skills.list_scripts", lambda skill_id: {})
    monkeypatch.setattr("app.data_access.skills.category_of", lambda skill_id: "vault")


def test_the_inventory_lists_workflows_as_a_seventh_kind(
    the_six_pre_existing_kinds, stored_workflows,
) -> None:
    """[REQ-SB-95-US-04-AC-04] A Workflow appears under its own
    "workflow" kind beside the six that were already there, carrying the
    id, name and description every inventory entry carries. A Workflow
    has no `name` field of its own, so its id is its name -- the same
    fallback Template and Action already use."""
    WorkflowManager().create(
        "mail-me-the-team-list",
        request_kind="list the Actions assigned to my team and mail them to me",
        description="The operator's standing handling for this ask",
        steps=_two_steps_naming_two_actions(),
    )

    entries = artifacts_inventory.list_all_artifacts()

    assert [entry for entry in entries if entry["kind"] == "workflow"] == [{
        "kind": "workflow",
        "id": "mail-me-the-team-list",
        "name": "mail-me-the-team-list",
        "description": "The operator's standing handling for this ask",
    }]
    assert {entry["kind"] for entry in entries} == {
        "skill", "template", "agent", "pipeline", "index", "action", "workflow",
    }


def test_the_seventh_kind_changes_nothing_about_the_other_six(
    the_six_pre_existing_kinds, stored_workflows,
) -> None:
    """[REQ-SB-95-US-04-AC-04] The same six entries, byte for byte, with
    zero Workflows present and with Workflows present. This is the
    Constraint the whole task hangs on: adding a kind must be an
    addition, never a re-shaping of what was already listed."""
    before = [entry for entry in artifacts_inventory.list_all_artifacts() if entry["kind"] != "workflow"]
    assert before == the_six_pre_existing_kinds

    manager = WorkflowManager()
    manager.create("mail-me-the-team-list", description="Mail me the list",
                   steps=_two_steps_naming_two_actions())
    manager.create("sweep-the-inbox", description="Sweep it",
                   steps=[{"action_id": "append-capture"}])

    entries = artifacts_inventory.list_all_artifacts()

    assert [entry for entry in entries if entry["kind"] != "workflow"] == before
    assert [entry["id"] for entry in entries if entry["kind"] == "workflow"] == [
        "mail-me-the-team-list", "sweep-the-inbox",
    ]


def test_a_kind_with_no_workflows_is_an_absence_not_an_omission_or_an_error(
    the_six_pre_existing_kinds, stored_workflows,
) -> None:
    """[REQ-SB-95-US-04-AC-04] An install with no Workflows yet reads the
    inventory successfully and simply has no `workflow` rows -- the
    seventh kind never raises and never drops the other six on the way."""
    assert stored_workflows == {}

    entries = artifacts_inventory.list_all_artifacts()

    assert [entry for entry in entries if entry["kind"] == "workflow"] == []
    assert entries == the_six_pre_existing_kinds


def test_the_payload_folder_is_stated_not_naively_pluralised() -> None:
    """[REQ-SB-95-US-04-AC-05] The Index precedent's own test,
    Workflow-flavoured: the import side looks for a literal folder name,
    so the export side must state it rather than derive it."""
    assert artifact_export._PAYLOAD_FOLDER["workflow"] == "workflows"


def test_a_workflow_pulls_every_action_its_steps_name_and_their_skills(
    closure_sources, the_two_actions_the_steps_name, stored_workflows,
) -> None:
    """[REQ-SB-95-US-04-AC-05] The new edge, and the recursion through
    it. Exporting a Workflow has to carry both Actions its steps name --
    or the bundle lands on the other install as a Workflow whose every
    step points at nothing, which is precisely what T02's save gate
    refuses to create here. The `skill`-implemented Action then pulls
    its own Skill in through the branch that already existed."""
    WorkflowManager().create(
        "mail-me-the-team-list",
        request_kind="list the Actions assigned to my team and mail them to me",
        steps=_two_steps_naming_two_actions(),
    )

    closure = artifact_dependency_resolver.resolve_closure(
        [{"kind": "workflow", "id": "mail-me-the-team-list"}],
    )
    by_key = {(entry["kind"], entry["id"]): entry for entry in closure}

    assert set(by_key) == {
        ("workflow", "mail-me-the-team-list"),
        ("action", "list-team-actions"),
        ("action", "send-mail"),
        ("skill", "vault-search"),
    }
    assert by_key[("workflow", "mail-me-the-team-list")]["included_reason"] == "selected"

    # Every dependency names what pulled it in, one hop at a time, so the
    # operator reading the preview can see WHY a Skill they never
    # selected is in their bundle.
    assert by_key[("action", "list-team-actions")]["depends_via"] == (
        "workflow:mail-me-the-team-list (step collect)"
    )
    assert by_key[("action", "send-mail")]["depends_via"] == (
        "workflow:mail-me-the-team-list (step send)"
    )
    assert by_key[("skill", "vault-search")]["depends_via"] == (
        "action:list-team-actions (skill implementation)"
    )
    assert [by_key[key]["included_reason"] for key in (
        ("action", "list-team-actions"), ("action", "send-mail"), ("skill", "vault-search"),
    )] == ["dependency", "dependency", "dependency"]


def test_an_exported_workflow_travels_with_its_actions_and_arrives_runnable(
    closure_sources, the_two_actions_the_steps_name, stored_workflows,
) -> None:
    """[REQ-SB-95-US-04-AC-05] The whole point of the kind: a real `.sbf`
    carries `workflows/<id>/Workflow.json` beside both Actions and the
    Skill one of them runs, and importing it on an install that has
    neither produces a Workflow whose every step resolves there."""
    WorkflowManager().create(
        "mail-me-the-team-list",
        request_kind="list the Actions assigned to my team and mail them to me",
        description="The operator's standing handling for this ask",
        steps=_two_steps_naming_two_actions(),
        report={"description": "the list that was sent, and to whom",
                "include_step_ids": ["collect", "send"]},
    )

    sbf_path = artifact_export.commit_export(
        [{"kind": "workflow", "id": "mail-me-the-team-list"}], {},
    )
    try:
        manifest, payload = sbf_archive.read_archive(sbf_path)
    finally:
        Path(sbf_path).unlink(missing_ok=True)

    assert "workflows/mail-me-the-team-list/Workflow.json" in payload
    assert "actions/list-team-actions/Action.json" in payload
    assert "actions/send-mail/Action.json" in payload
    assert "skills/vault-search/SKILL.md" in payload
    assert {(a["kind"], a["id"]) for a in manifest["artifacts"]} == {
        ("workflow", "mail-me-the-team-list"),
        ("action", "list-team-actions"),
        ("action", "send-mail"),
        ("skill", "vault-search"),
    }

    # A clean install: neither the Workflow nor its Actions are there
    # before the import.
    stored_workflows.clear()
    the_two_actions_the_steps_name.clear()
    for entry in ("action/list-team-actions", "action/send-mail", "workflow/mail-me-the-team-list"):
        kind, artifact_id = entry.split("/")
        outcome = artifact_import._deploy_one(
            {"kind": kind, "id": artifact_id, "conflicts": False}, None, payload, {}, None,
        )
        assert outcome["status"] == "deployed", outcome

    imported = WorkflowManager().get_by_id("mail-me-the-team-list")
    assert imported.request_kind == "list the Actions assigned to my team and mail them to me"
    assert [(s.id, s.action_id, s.needs_confirmation) for s in imported.steps] == [
        ("collect", "list-team-actions", False),
        ("send", "send-mail", True),
    ]
    assert [s.inputs for s in imported.steps] == [
        {"team": "CBO"}, {"to": "{{operator.self_email}}"},
    ]
    assert imported.report.include_step_ids == ["collect", "send"]

    # "Arrives runnable" is the real claim, so it is asserted as the
    # thing that makes a Workflow runnable rather than as the presence of
    # some files: every step resolves against the receiving install's own
    # catalogue. Asked of the catalogue, not of the bundle.
    from app.business.core.actions.action_manager import ActionManager

    catalogued = {action.id for action in ActionManager().get_all()}
    assert [step.action_id for step in imported.steps if step.action_id not in catalogued] == []


def test_the_secret_scan_covers_a_workflow_steps_inputs(
    the_two_actions_the_steps_name, stored_workflows,
) -> None:
    """[REQ-SB-95-US-04-AC-05] A step's `inputs` holds the literal values
    an Action is called with (`workflow.py`), so it is where a pasted
    token really lands. `Workflow.json` is written by this app into the
    App Database Folder, so those bytes are inside the scanned surface.
    Also pins that the scanner and the export produce the SAME
    `file_path`, since the redaction is applied by `file_path:line`."""
    secret_shaped = "sk-" + "B" * 24
    WorkflowManager().create(
        "call-the-provider",
        request_kind="ask the provider",
        steps=[{"id": "call", "action_id": "send-mail",
                "inputs": {"api_key": secret_shaped, "to": "someone@example.com"}}],
    )
    closure = [{"kind": "workflow", "id": "call-the-provider"}]

    findings = artifact_secret_scan.scan_closure(closure)

    assert [(f["artifact_kind"], f["artifact_id"], f["file_path"]) for f in findings] == [
        ("workflow", "call-the-provider", "workflows/call-the-provider/Workflow.json"),
    ]

    content = artifact_export._text_content_for_scan(closure)
    redacted = artifact_secret_scan.apply_decisions(
        content, findings, {f"{f['file_path']}:{f['line']}": "redact" for f in findings},
    )

    scanned_file = "workflows/call-the-provider/Workflow.json"
    assert secret_shaped not in redacted[scanned_file]
    assert "[REDACTED-BY-SECOND-BRAIN-EXPORT]" in redacted[scanned_file]
    # The step's other input is untouched -- a redaction is one line, not
    # the whole step.
    assert "someone@example.com" in redacted[scanned_file]


def test_importing_a_workflow_whose_id_exists_never_silently_overwrites(stored_workflows) -> None:
    """[REQ-SB-95-US-04-AC-05] All four branches of the existing conflict
    machinery, on the Workflow kind. The undecided case is the important
    one: it fails honestly naming the missing decision rather than
    picking a winner -- and the operator's own documented handling is
    exactly the thing that must never be replaced behind their back."""
    WorkflowManager().create("mail-me-the-team-list", description="the original",
                             steps=_two_steps_naming_two_actions())
    payload = {
        "workflows/mail-me-the-team-list/Workflow.json": json.dumps({
            "id": "mail-me-the-team-list",
            "description": "the incoming one",
            "steps": [{"id": "collect", "action_id": "list-team-actions"}],
        }).encode("utf-8"),
    }
    conflicting = {"kind": "workflow", "id": "mail-me-the-team-list", "conflicts": True}

    undecided = artifact_import._deploy_one(conflicting, None, payload, {}, None)
    assert undecided["status"] == "failed"
    assert "no explicit decision supplied" in undecided["detail"]
    assert stored_workflows["mail-me-the-team-list"]["description"] == "the original"

    skipped = artifact_import._deploy_one(conflicting, "skip", payload, {}, None)
    assert skipped["status"] == "skipped"
    assert stored_workflows["mail-me-the-team-list"]["description"] == "the original"

    kept_both = artifact_import._deploy_one(conflicting, "keep_both", payload, {}, None)
    assert kept_both["status"] == "deployed"
    assert kept_both["deployed_as"] == "mail-me-the-team-list-imported"
    assert stored_workflows["mail-me-the-team-list"]["description"] == "the original"
    assert stored_workflows["mail-me-the-team-list-imported"]["description"] == "the incoming one"
    assert stored_workflows["mail-me-the-team-list-imported"]["id"] == "mail-me-the-team-list-imported"

    overwritten = artifact_import._deploy_one(conflicting, "overwrite", payload, {}, None)
    assert overwritten["status"] == "deployed"
    assert overwritten["deployed_as"] is None
    assert stored_workflows["mail-me-the-team-list"]["description"] == "the incoming one"


def test_an_imported_workflow_naming_an_unknown_action_is_refused_at_the_first_save(
    stored_workflows,
) -> None:
    """[REQ-SB-95-US-04-AC-05] Import does not re-run T02's save-time
    catalogue check, and this is why that is a deferral rather than a
    hole.

    A bundle legitimately carries a Workflow and its Actions together
    and nothing fixes which deploys first, so refusing at import would
    reject complete bundles. The gate still fires -- at the door it
    belongs to, with T02's own sentence, naming the step position and
    the unknown id. Written against the Manager's own path rather than a
    second check in `artifact_import`, so there is one refusal for one
    rule."""
    payload = {
        "workflows/imported-elsewhere/Workflow.json": json.dumps({
            "id": "imported-elsewhere",
            "steps": [{"id": "collect", "action_id": "list-team-actions"},
                      {"id": "exotic", "action_id": "an-action-this-install-never-had"}],
        }).encode("utf-8"),
    }

    outcome = artifact_import._deploy_one(
        {"kind": "workflow", "id": "imported-elsewhere", "conflicts": False}, None, payload, {}, None,
    )

    # It lands, definition intact -- losing the operator's documented
    # handling would be worse than holding one unresolvable step.
    assert outcome["status"] == "deployed"
    landed = WorkflowManager().get_by_id("imported-elsewhere")
    assert [s.action_id for s in landed.steps] == [
        "list-team-actions", "an-action-this-install-never-had",
    ]

    # And the first save of it meets T02's refusal, unchanged.
    with pytest.raises(WorkflowStepActionNotFoundError) as refusal:
        WorkflowManager().update("imported-elsewhere", steps=[
            {"id": s.id, "action_id": s.action_id, "inputs": s.inputs,
             "needs_confirmation": s.needs_confirmation, "description": s.description}
            for s in landed.steps
        ])

    assert "step 2" in str(refusal.value)
    assert "'an-action-this-install-never-had'" in str(refusal.value)
    assert "nothing was saved" in str(refusal.value)


# -- Pipelines are provably untouched (US-04 Scenario 7) ----------------

def _a_real_pipeline_definition() -> dict:
    return {
        "id": "morning-sweep",
        "name": "Morning Sweep",
        "description": "Sweeps the inbox",
        "section": "Data Gatherer",
        "cron_job_id": "job-7f3a",
        "cron_profile_id": "meeting-prep-agent",
        "schedule": "0 6 * * *",
        "steps": [{"id": "fetch-meetings", "name": "Fetch meetings"}],
    }


def test_a_pipeline_is_byte_identical_before_and_after_workflows_exist(
    monkeypatch, tmp_path,
) -> None:
    """[REQ-SB-95-US-04-AC-07] ADR-032 leaves Pipeline exactly as it is.
    Asserted on the real stored bytes and the real schedule fields, not
    on a Manager call that could be answering from somewhere else -- the
    Pipeline store is a flat `<DATA_PATH>/pipelines/<id>.json`, and
    adding a kind whose store is `<DATA_PATH>/data/Workflows/` must not
    reach it, list it, rewrite it or reformat it."""
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path)
    pipelines_data.write_pipeline_json("morning-sweep", _a_real_pipeline_definition())

    pipeline_file = tmp_path / "pipelines" / "morning-sweep.json"
    bytes_before = pipeline_file.read_bytes()
    ids_before = pipelines_data.list_pipeline_ids()

    manager = WorkflowManager()
    manager.create("mail-me-the-team-list", request_kind="mail me the team list",
                   steps=_two_steps_naming_two_actions())
    manager.create("morning-sweep", request_kind="sweep the inbox",
                   steps=[{"action_id": "append-capture"}])
    manager.delete("morning-sweep")

    assert pipeline_file.read_bytes() == bytes_before
    assert pipelines_data.list_pipeline_ids() == ids_before == ["morning-sweep"]
    # Its schedule fields specifically -- what a cron job actually runs on.
    reread = pipelines_data.read_pipeline_json("morning-sweep")
    assert (reread["cron_job_id"], reread["cron_profile_id"], reread["schedule"]) == (
        "job-7f3a", "meeting-prep-agent", "0 6 * * *",
    )
    assert reread == _a_real_pipeline_definition()

    # A Workflow sharing a Pipeline's id is still a different artifact in
    # a different store: creating and then deleting `morning-sweep` as a
    # Workflow neither converted the Pipeline nor removed it.
    assert sorted(p.name for p in (tmp_path / "pipelines").iterdir()) == ["morning-sweep.json"]
    assert [w.id for w in manager.get_all()] == ["mail-me-the-team-list"]


def test_no_pipeline_is_relabelled_as_a_workflow(
    the_six_pre_existing_kinds, stored_workflows,
) -> None:
    """[REQ-SB-95-US-04-AC-07] The inventory half: the install's Pipeline
    keeps its own `pipeline` row, and no `workflow` row is produced for
    it. Nothing converts, replaces or re-labels one as the other."""
    WorkflowManager().create("mail-me-the-team-list", steps=_two_steps_naming_two_actions())

    entries = artifacts_inventory.list_all_artifacts()
    pipeline_ids = {entry["id"] for entry in entries if entry["kind"] == "pipeline"}
    workflow_ids = {entry["id"] for entry in entries if entry["kind"] == "workflow"}

    assert pipeline_ids == {"morning-sweep"}
    assert workflow_ids == {"mail-me-the-team-list"}
    assert not pipeline_ids & workflow_ids
    assert [entry for entry in entries if entry["kind"] == "pipeline"] == [
        {"kind": "pipeline", "id": "morning-sweep", "name": "Morning Sweep",
         "description": "Sweeps the inbox"},
    ]


def test_no_action_call_or_workflow_run_can_travel_in_a_bundle(
    monkeypatch, tmp_path, closure_sources, the_two_actions_the_steps_name, stored_workflows,
) -> None:
    """[REQ-SB-95-US-04-AC-07] `ActionCalls/` and `WorkflowRuns/` are
    instance data (ADR-033/ADR-034): what happened once on THIS install,
    never a capability another install can be given. Real records are
    put on disk first, so this asserts their absence from a bundle
    rather than the absence of a folder nobody created."""
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path)
    for instance_folder, filename in (("ActionCalls", "call-001.json"), ("WorkflowRuns", "run-001.json")):
        folder = tmp_path / "data" / instance_folder
        folder.mkdir(parents=True, exist_ok=True)
        (folder / filename).write_text('{"outcome": "done"}', encoding="utf-8")

    # Nothing else on this install, so "everything" really is everything.
    for manager_name in ("_agent_manager", "_template_manager", "_index_manager", "_pipeline_manager"):
        monkeypatch.setattr(artifacts_inventory, manager_name, _FixedManager([]))
    monkeypatch.setattr(artifacts_inventory, "_skill_manager", _FixedManager([
        SimpleNamespace(id="vault-search", name="Vault Search", description="Search the vault"),
    ]))
    WorkflowManager().create("mail-me-the-team-list", steps=_two_steps_naming_two_actions())

    everything = [
        {"kind": entry["kind"], "id": entry["id"]}
        for entry in artifacts_inventory.list_all_artifacts()
    ]
    sbf_path = artifact_export.commit_export(everything, {})
    try:
        manifest, payload = sbf_archive.read_archive(sbf_path)
    finally:
        Path(sbf_path).unlink(missing_ok=True)

    # Positive control: the export really did run and really did carry
    # the Workflow, so the absences below mean something.
    assert "workflows/mail-me-the-team-list/Workflow.json" in payload

    assert [path for path in payload if "ActionCalls" in path or "WorkflowRuns" in path] == []
    assert [a for a in manifest["artifacts"] if a["kind"] in ("action_call", "workflow_run")] == []
    assert "call-001" not in str(payload) and "run-001" not in str(payload)
    # Structural, not filtered: no kind maps to either store, so no
    # selection can name them and no closure can reach them.
    assert not {"action_call", "workflow_run", "actioncall", "workflowrun"} & set(
        artifact_export._PAYLOAD_FOLDER
    )
