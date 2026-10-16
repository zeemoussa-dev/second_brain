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

`REQ-SB-95-US-02-T04` extended this file with the other half of being an
artifact kind: appearing in the cross-kind inventory, and actually
travelling in an `.sbf` bundle -- the dependency closure, the secret
scan, the export payload folder and the import dispatch. Those tests
live below the `-- The sixth kind across the artifact machinery --`
banner and pin, above all, that adding the sixth kind changed nothing
about the five that were already there.
"""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.business.core.actions.action_manager import (
    ActionImplementationCardinalityError,
    ActionManager,
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


# -- The sixth kind across the artifact machinery (REQ-SB-95-US-02-T04) ----
#
# An Action that cannot travel in a bundle is a catalogue row, not an
# artifact. These tests cover the five measured touch points the Index
# precedent (ADR-019) already went through: the inventory, the dependency
# closure, the export payload folder, the secret scan and the import
# dispatch.

A_SKILL_IMPLEMENTATION = {"skill": {"skill_id": "vault-search"}}
A_UI_IMPLEMENTATION = {"ui": {"feature_key": "/settings/artifacts"}}


class _FixedManager:
    """Stands in for one real Manager, answering from a fixed list.

    The live inventory reads this install's real Registry (41 Agents on
    the reporting machine), so asserting against it would be asserting
    about the machine running the test rather than about the code. Only
    `get_all`/`get_by_id` are used by the two modules under test here."""

    def __init__(self, entities=()) -> None:
        self._entities = list(entities)

    def get_all(self) -> list:
        return list(self._entities)

    def get_by_id(self, entity_id: str):
        return next((entity for entity in self._entities if entity.id == entity_id), None)


@pytest.fixture
def action_store(monkeypatch) -> dict:
    """The whole store, in memory -- same idea as `stored_actions` above,
    but faithful about a MISSING id.

    The real `read_action_json` raises `FileNotFoundError` for an id that
    does not exist, and `ActionManager.get_by_id` catches exactly that to
    answer `None`. A bare `written[action_id]` raises `KeyError`, which
    escapes instead -- and `_next_alternate_id`'s keep-both probe for an
    id that does not exist yet is precisely the call that makes the
    difference visible. Kept separate rather than changing the fixture
    `T01`'s own verified tests run on."""
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
def pre_existing_kinds(monkeypatch) -> list[dict]:
    """The five Managers the inventory composed before Action, pinned to
    one fixed entry each. Returns the exact entries they must always
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
    return [
        {"kind": "skill", "id": "vault-search", "name": "Vault Search", "description": "Search the vault"},
        {"kind": "template", "id": "Meeting", "name": "Meeting", "description": "Meeting"},
        {"kind": "agent", "id": "cbo-agent", "name": "CBO Agent", "description": "Chief of staff"},
        {"kind": "pipeline", "id": "morning-sweep", "name": "Morning Sweep", "description": "Sweeps the inbox"},
        {"kind": "index", "id": "adnoc", "name": "ADNOC", "description": ""},
    ]


@pytest.fixture
def closure_sources(monkeypatch) -> None:
    """The resolver's and the export's non-Action inputs, pinned. The
    Action branch is what is under test; the Skill it pulls in has to be
    a real, resolvable entry for the closure to contain it at all, and
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


def test_the_inventory_lists_actions_as_a_sixth_kind(pre_existing_kinds, action_store) -> None:
    """[REQ-SB-95-US-02-AC-04] An Action appears under its own "action"
    kind beside the five that were already there, carrying the id, name
    and description every inventory entry carries. An Action has no
    `name` field of its own, so its id is its name -- the same fallback
    Template already uses."""
    ActionManager().create(
        "make-strategic-entity",
        description="Promote a customer to a Strategic Entity",
        implementation=A_SKILL_IMPLEMENTATION,
    )

    entries = artifacts_inventory.list_all_artifacts()

    assert [entry for entry in entries if entry["kind"] == "action"] == [{
        "kind": "action",
        "id": "make-strategic-entity",
        "name": "make-strategic-entity",
        "description": "Promote a customer to a Strategic Entity",
    }]
    assert {entry["kind"] for entry in entries} == {
        "skill", "template", "agent", "pipeline", "index", "action",
    }


def test_the_sixth_kind_changes_nothing_about_the_other_five(pre_existing_kinds, action_store) -> None:
    """[REQ-SB-95-US-02-AC-04] The same five entries, byte for byte, with
    zero Actions present and with Actions present. This is the Constraint
    the whole task hangs on: adding a kind must be an addition, never a
    re-shaping of what was already listed."""
    before = [entry for entry in artifacts_inventory.list_all_artifacts() if entry["kind"] != "action"]
    assert before == pre_existing_kinds

    manager = ActionManager()
    manager.create("make-strategic-entity", description="Promote", implementation=A_SKILL_IMPLEMENTATION)
    manager.create("open-the-artifacts-page", description="Open it", implementation=A_UI_IMPLEMENTATION)

    entries = artifacts_inventory.list_all_artifacts()

    assert [entry for entry in entries if entry["kind"] != "action"] == before
    assert [entry["id"] for entry in entries if entry["kind"] == "action"] == [
        "make-strategic-entity", "open-the-artifacts-page",
    ]


def test_a_kind_with_no_artifacts_is_an_absence_not_an_omission_or_an_error(
    pre_existing_kinds, action_store,
) -> None:
    """[REQ-SB-95-US-02-AC-04] An install with no Actions yet reads the
    inventory successfully and simply has no `action` rows -- the sixth
    kind never raises and never drops the other five on the way."""
    assert action_store == {}

    entries = artifacts_inventory.list_all_artifacts()

    assert [entry for entry in entries if entry["kind"] == "action"] == []
    assert entries == pre_existing_kinds


def test_the_payload_folder_is_not_naively_pluralised() -> None:
    """[REQ-SB-95-US-02-AC-05] The Index precedent's own test, Action-
    flavoured: the import side looks for a literal folder name, so the
    export side must state it rather than derive it."""
    assert artifact_export._PAYLOAD_FOLDER["action"] == "actions"


def test_an_action_pulls_the_skill_it_runs_into_the_closure(closure_sources, action_store) -> None:
    """[REQ-SB-95-US-02-AC-05] Exporting an Action that runs a Skill has
    to carry that Skill, or the bundle lands on the other install as an
    Action pointing at nothing. An `http` or `ui` Action names something
    that ships with the app, so it pulls in nothing extra."""
    manager = ActionManager()
    manager.create("make-strategic-entity", implementation=A_SKILL_IMPLEMENTATION)
    manager.create("open-the-artifacts-page", implementation=A_UI_IMPLEMENTATION)

    closure = artifact_dependency_resolver.resolve_closure(
        [{"kind": "action", "id": "make-strategic-entity"}],
    )
    by_key = {(entry["kind"], entry["id"]): entry for entry in closure}

    assert set(by_key) == {("action", "make-strategic-entity"), ("skill", "vault-search")}
    assert by_key[("action", "make-strategic-entity")]["included_reason"] == "selected"
    assert by_key[("skill", "vault-search")]["included_reason"] == "dependency"
    assert by_key[("skill", "vault-search")]["depends_via"] == (
        "action:make-strategic-entity (skill implementation)"
    )

    ui_closure = artifact_dependency_resolver.resolve_closure(
        [{"kind": "action", "id": "open-the-artifacts-page"}],
    )
    assert [(entry["kind"], entry["id"]) for entry in ui_closure] == [
        ("action", "open-the-artifacts-page"),
    ]


def test_an_exported_action_travels_and_imports_onto_a_clean_store(closure_sources, action_store) -> None:
    """[REQ-SB-95-US-02-AC-05] The whole point of the kind: a real `.sbf`
    carries `actions/<id>/Action.json` beside the Skill it runs, and
    importing it on an install that has no such Action produces one whose
    implementation resolves there."""
    ActionManager().create(
        "make-strategic-entity",
        description="Promote a customer to a Strategic Entity",
        inputs=[{"name": "entity_name", "type": "string", "required": True}],
        allowed_callers=["cbo-agent"],
        needs_confirmation=True,
        implementation=A_SKILL_IMPLEMENTATION,
    )

    sbf_path = artifact_export.commit_export(
        [{"kind": "action", "id": "make-strategic-entity"}], {},
    )
    try:
        manifest, payload = sbf_archive.read_archive(sbf_path)
    finally:
        Path(sbf_path).unlink(missing_ok=True)

    assert "actions/make-strategic-entity/Action.json" in payload
    assert "skills/vault-search/SKILL.md" in payload
    assert {(a["kind"], a["id"]) for a in manifest["artifacts"]} == {
        ("action", "make-strategic-entity"), ("skill", "vault-search"),
    }

    # A clean install: the id is genuinely absent before the import.
    action_store.clear()
    outcome = artifact_import._deploy_one(
        {"kind": "action", "id": "make-strategic-entity", "conflicts": False},
        None, payload, {}, None,
    )

    assert outcome["status"] == "deployed"
    imported = ActionManager().get_by_id("make-strategic-entity")
    assert imported.description == "Promote a customer to a Strategic Entity"
    assert [(i.name, i.required) for i in imported.inputs] == [("entity_name", True)]
    assert imported.allowed_callers == ["cbo-agent"]
    assert imported.needs_confirmation is True
    assert imported.implementation.kind == "skill"
    assert imported.implementation.skill_id == "vault-search"
    assert [entry["status"] for entry in ActionManager().resolution_report()] == ["resolves"]


def test_the_secret_scan_covers_an_actions_own_bytes(closure_sources, action_store) -> None:
    """[REQ-SB-95-US-02-AC-05] `Action.json` is written by this app into
    the App Database Folder, so it is inside the scanned surface -- an
    Action carrying a pasted key must not ride out of the install
    unnoticed. Also pins that the scanner and the export produce the SAME
    `file_path`, since the redaction is applied by `file_path:line`."""
    secret_shaped = "sk-" + "A" * 24
    ActionManager().create(
        "call-the-provider",
        description=f"Uses {secret_shaped} to authenticate",
        implementation=A_UI_IMPLEMENTATION,
    )
    closure = [{"kind": "action", "id": "call-the-provider"}]

    findings = artifact_secret_scan.scan_closure(closure)

    assert [(f["artifact_kind"], f["artifact_id"], f["file_path"]) for f in findings] == [
        ("action", "call-the-provider", "actions/call-the-provider/Action.json"),
    ]

    content = artifact_export._text_content_for_scan(closure)
    redacted = artifact_secret_scan.apply_decisions(
        content, findings, {f"{f['file_path']}:{f['line']}": "redact" for f in findings},
    )

    assert secret_shaped not in redacted["actions/call-the-provider/Action.json"]
    assert "[REDACTED-BY-SECOND-BRAIN-EXPORT]" in redacted["actions/call-the-provider/Action.json"]


def test_importing_an_action_whose_id_exists_never_silently_overwrites(action_store) -> None:
    """[REQ-SB-95-US-02-AC-05] All four branches of the existing conflict
    machinery, on the Action kind. The undecided case is the important
    one: it fails honestly naming the missing decision rather than
    picking a winner."""
    ActionManager().create(
        "make-strategic-entity", description="the original", implementation=A_SKILL_IMPLEMENTATION,
    )
    payload = {
        "actions/make-strategic-entity/Action.json": json.dumps({
            "id": "make-strategic-entity",
            "description": "the incoming one",
            "implementation": {"skill": {"skill_id": "vault-search"}},
        }).encode("utf-8"),
    }
    conflicting = {"kind": "action", "id": "make-strategic-entity", "conflicts": True}

    undecided = artifact_import._deploy_one(conflicting, None, payload, {}, None)
    assert undecided["status"] == "failed"
    assert "no explicit decision supplied" in undecided["detail"]
    assert action_store["make-strategic-entity"]["description"] == "the original"

    skipped = artifact_import._deploy_one(conflicting, "skip", payload, {}, None)
    assert skipped["status"] == "skipped"
    assert action_store["make-strategic-entity"]["description"] == "the original"

    kept_both = artifact_import._deploy_one(conflicting, "keep_both", payload, {}, None)
    assert kept_both["status"] == "deployed"
    assert kept_both["deployed_as"] == "make-strategic-entity-imported"
    assert action_store["make-strategic-entity"]["description"] == "the original"
    assert action_store["make-strategic-entity-imported"]["description"] == "the incoming one"
    assert action_store["make-strategic-entity-imported"]["id"] == "make-strategic-entity-imported"

    overwritten = artifact_import._deploy_one(conflicting, "overwrite", payload, {}, None)
    assert overwritten["status"] == "deployed"
    assert overwritten["deployed_as"] is None
    assert action_store["make-strategic-entity"]["description"] == "the incoming one"
