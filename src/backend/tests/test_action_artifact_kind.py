"""Action becomes the sixth artifact kind (REQ-SB-95-US-02, ADR-032).

The Index precedent (ADR-019) is the shape this follows, so these tests
pin the two things that make an Action a real stored artifact rather
than a dict passing through: that everything the operator authored
survives the round-trip byte for byte -- an optional input must not read
back as required -- and that the exactly-one-implementation rule is a
refusal at save time, not a coercion. An Action silently saved with no
implementation, or with two, is exactly the "broken action sitting in
the catalogue waiting to fail in front of the operator" ADR-032 exists
to prevent.

No real data path is touched: write/read/list are monkeypatched the way
tests/test_index_artifact_kind.py already does, except in the one test
that is specifically ABOUT the path, which points settings at a tmp dir.
"""
import pytest

from app.business.core.actions.action_manager import (
    ActionImplementationCardinalityError,
    ActionManager,
)
from app.config import settings
from app.data_access import actions as actions_data


@pytest.fixture(autouse=True)
def _implementations_resolve(monkeypatch) -> None:
    """These tests are about round-tripping and the exactly-one rule, not about
    what happens to be deployed on the machine running them.

    `T02` added a save-time resolution gate (`AC-02`), which correctly refuses an
    implementation naming a Skill that is catalogued but not deployed -- and
    `vault-search`, the one these fixtures name, is exactly that on the reporting
    install. Without this the assertions below would silently become a test of
    the local deployment, and would fail on any machine where that Skill is
    absent. The same three sources `tests/test_action_resolution.py` controls."""
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.deployed_skill_ids",
        lambda: {"vault-search"},
    )


@pytest.fixture
def stored_actions(monkeypatch) -> dict:
    """The whole store, in memory, keyed by action id."""
    written: dict = {}
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.write_action_json",
        lambda action_id, data: written.update({action_id: data}),
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.read_action_json",
        lambda action_id: written[action_id],
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.list_action_ids",
        lambda: sorted(written),
    )
    return written


@pytest.fixture
def refusing_store(monkeypatch) -> list:
    """Records every write attempt, so "nothing was written" is an
    assertion rather than an absence of evidence."""
    attempts: list = []
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.write_action_json",
        lambda action_id, data: attempts.append(action_id),
    )
    return attempts


def test_a_saved_action_round_trips_everything_the_operator_authored(stored_actions) -> None:
    """[REQ-SB-95-US-02-AC-01] Inputs with their required flags,
    allowed_callers and the confirmation flag all survive reopening, and
    the catalogue lists the Action with its id, description and
    implementation kind."""
    manager = ActionManager()

    created = manager.create(
        "make-strategic-entity",
        description="Promote a customer to a Strategic Entity",
        inputs=[
            {"name": "entity_name", "type": "string", "required": True},
            {"name": "note", "type": "string", "required": False},
        ],
        allowed_callers=["cbo-agent"],
        needs_confirmation=True,
        implementation={"skill": {"skill_id": "vault-search"}},
    )

    # Written under its OWN id, at that id's own definition.
    assert list(stored_actions) == ["make-strategic-entity"]
    assert stored_actions["make-strategic-entity"]["id"] == "make-strategic-entity"
    assert created.id == "make-strategic-entity"

    reopened = ActionManager().get_by_id("make-strategic-entity")
    assert [(i.name, i.type, i.required) for i in reopened.inputs] == [
        ("entity_name", "string", True),
        ("note", "string", False),
    ]
    assert reopened.allowed_callers == ["cbo-agent"]
    assert reopened.needs_confirmation is True
    assert reopened.implementation.kind == "skill"
    assert reopened.implementation.skill_id == "vault-search"

    catalogue = ActionManager().get_all()
    assert [(a.id, a.description, a.implementation.kind) for a in catalogue] == [
        ("make-strategic-entity", "Promote a customer to a Strategic Entity", "skill"),
    ]


def test_the_store_is_the_data_paths_own_actions_folder(monkeypatch, tmp_path) -> None:
    """[REQ-SB-95-US-02-AC-01] ADR-032 fixes the store at
    <DATA_PATH>/data/Actions/<id>/Action.json -- instance data in the
    App Database Folder, never the repository."""
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path)

    assert actions_data.action_file("make-strategic-entity") == (
        tmp_path / "data" / "Actions" / "make-strategic-entity" / "Action.json"
    )

    actions_data.write_action_json("make-strategic-entity", {"id": "make-strategic-entity"})
    assert (tmp_path / "data" / "Actions" / "make-strategic-entity" / "Action.json").is_file()
    assert actions_data.list_action_ids() == ["make-strategic-entity"]
    assert actions_data.read_action_json("make-strategic-entity")["id"] == "make-strategic-entity"


def test_an_action_naming_no_implementation_is_refused(refusing_store) -> None:
    """[REQ-SB-95-US-02-AC-03] Zero implementations is a refusal naming
    the rule, never a save of something nothing can run."""
    with pytest.raises(ActionImplementationCardinalityError) as refusal:
        ActionManager().create("orphan", description="runs nothing", implementation={})

    assert "exactly one implementation" in str(refusal.value)
    assert "skill, http or ui" in str(refusal.value)
    assert refusing_store == []


def test_an_action_naming_two_implementations_is_refused(refusing_store) -> None:
    """[REQ-SB-95-US-02-AC-03] Two is the same refusal as none -- the
    rule is exactly one, so the save must not quietly pick a winner."""
    with pytest.raises(ActionImplementationCardinalityError) as refusal:
        ActionManager().create(
            "two-headed",
            implementation={
                "skill": {"skill_id": "vault-search"},
                "http": {"method": "POST", "path": "/vault-index/refresh"},
            },
        )

    assert "exactly one implementation" in str(refusal.value)
    assert refusing_store == []


def test_an_action_naming_exactly_one_implementation_is_saved(stored_actions) -> None:
    """[REQ-SB-95-US-02-AC-03] The third branch of the same rule: one of
    the three is saved normally."""
    action = ActionManager().create(
        "refresh-vault-index",
        description="Rebuild the vault index now",
        implementation={"http": {"method": "POST", "path": "/vault-index/refresh"}},
    )

    assert stored_actions["refresh-vault-index"]["implementation"] == {
        "http": {"method": "POST", "path": "/vault-index/refresh"},
    }
    assert action.implementation.kind == "http"
    assert action.implementation.path == "/vault-index/refresh"
