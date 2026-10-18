"""The Operator Profile does not travel in a bundle -- `REQ-SB-95-US-01-T04`
(`ADR-032`).

An `.sbf` is the one artefact an operator hands to somebody else, and the
Profile holds a real person's name, their mail addresses and their
colleagues' addresses and roles. "It is not an artifact kind yet" is true
today and is not a guarantee; this file is the guarantee.

**Written to fail on the EIGHTH artifact kind, not only on today's seven.**
A test asserting `Operator/` is absent passes forever and proves nothing
the day someone adds a `Contacts/` folder, and a negative test naming one
example dates itself the moment that example ships (`ESC-077`). So
everything below is derived rather than written down:

- **Where the Profile lives** is read off `data_access/operator_profile.py`
  at test time, never spelled as `"Operator"`/`"Profile.json"` here -- move
  the store and this guard moves with it.
- **What may be exported** is the live `artifacts_inventory` output, so a
  future kind joins the exported selection automatically and has to pass
  these assertions without anyone remembering to add it.
- **What counts as personal data** is every leaf value of the Profile
  record as really stored, so a field added to the Profile tomorrow is
  guarded tonight.

The one place a Profile value is allowed to appear is an exported Agent's
own `soul.md`, which carries the published `## Who you work for` block --
`AC-08`, the privacy question the operator settled on 2026-10-17 by
accepting it. That allowance is asserted as an exact equality, not a
skipped check: any OTHER payload entry carrying a Profile value fails.

Nothing here can reach the operator's own install. `tests/conftest.py`
sandboxes Hermes suite-wide; this file additionally points
`hermes_home_path`, `second_brain_data_path` and `vault_path` at
`tmp_path` before anything runs, and restores the Registry's module-level
globals. Every value below is fictitious. No bundle is ever built from a
real store.
"""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

import pytest

import app.business.hermes.client as hermes_client_module
from app.business.core.operator import operator_profile_manager as operator_manager_module
from app.business.core.operator.operator_profile_manager import OperatorProfileManager
from app.business.core.plugins import plugin_manager as plugin_manager_module
from app.business.logic import (
    artifact_dependency_resolver,
    artifact_export,
    artifact_seed_data,
    artifacts_inventory,
    sbf_archive,
)
from app.config import settings
from app.data_access import actions as actions_data
from app.data_access import indexes as indexes_data
from app.data_access import operator_profile as operator_profile_data
from app.data_access import pipelines as pipelines_data
from app.data_access import skills as skills_data
from app.data_access import templates as templates_data
from app.data_access import workflows as workflows_data
from app.data_access.registry import loader as registry_loader
from app.hermes.cli import HermesCLI

OWN_ADDRESS = "operator@example.test"

A_PROFILE = {
    "name": "Robin Fictional",
    "other_email_addresses": ["robin.alt@example.test", "robin@example.invalid"],
    "timezone": "Etc/UTC",
    "team": [
        {"email": "blue@example.test", "role": "Fictional Engineer"},
        {"email": "green@example.test", "role": "Fictional Designer"},
        {"email": "amber@example.test", "role": "Fictional Analyst"},
    ],
}

THE_EXPORTED_AGENT = "blue-agent"
THE_AGENTS_HAND_AUTHORED_SOUL = "You are the Customer Expert.\n\n## Guardrails\n\nAsk first.\n"
A_SKILL = "vault-search"
A_TEMPLATE = "Meeting"
A_PIPELINE = "morning-sweep"
AN_INDEX = "adnoc"
AN_ACTION = "list-team-actions"
A_WORKFLOW = "mail-me-the-team-list"

# `ADR-014` fixes a Hermes profile tarball as opaque bytes this guard must
# not reach into, and the suite-wide sandbox means no real
# `hermes export-profile` can run anyway. A fixed, inert blob stands in --
# what the real one contains is recorded as a disclosure in the task's
# Implementation Log, not asserted here.
THE_OPAQUE_PROFILE_TARBALL = b"<an opaque Hermes profile tarball>"


class _FixedManager:
    """One real Manager, answering from a fixed list.

    The live Skill/Template/Agent/Pipeline/Index Managers read this
    machine's own repository catalogue, Registry and Hermes cron jobs, so
    composing them here would make the bundle under test depend on the
    machine running it. Action and Workflow are deliberately NOT pinned:
    their real Managers read the (scratch) data path, so two of the seven
    kinds reach the bundle through genuinely live code.
    """

    def __init__(self, entities=()) -> None:
        self._entities = list(entities)

    def get_all(self) -> list:
        return list(self._entities)

    def get_by_id(self, entity_id: str):
        return next((entity for entity in self._entities if entity.id == entity_id), None)

    def get_implementing_skill_id(self, entity_id: str) -> None:
        return None


def the_profile_store() -> tuple[str, str]:
    """(the folder the Profile's store lives in, the file it is stored as),
    read off the data-access module rather than written down here."""
    relative = operator_profile_data.profile_path().relative_to(settings.second_brain_data_path)
    return relative.parent.name, relative.name


def the_personal_values_really_stored() -> list[str]:
    """Every leaf string of the Profile record as it is really on disk.

    Derived, so a field added to the Profile in a later task is covered by
    this guard without anyone extending a list here.
    """
    values: list[str] = []

    def collect(value) -> None:
        if isinstance(value, str):
            if value.strip():
                values.append(value)
        elif isinstance(value, dict):
            for nested in value.values():
                collect(nested)
        elif isinstance(value, list):
            for nested in value:
                collect(nested)

    collect(json.loads(operator_profile_data.profile_path().read_text(encoding="utf-8")))
    return values


def everything_this_install_offers() -> list[dict]:
    """The export selection, taken from the live inventory -- so an eighth
    artifact kind is exported by these tests the day it exists."""
    return [
        {"kind": entry["kind"], "id": entry["id"]}
        for entry in artifacts_inventory.list_all_artifacts()
    ]


def export(selection: list[dict]) -> tuple[dict, dict[str, bytes]]:
    """A real `.sbf` written to disk, read back as bytes, then removed --
    the archive's own members, never the in-memory payload dict, because a
    file can be absent from the manifest and present in the archive."""
    sbf_path = artifact_export.commit_export(selection, {})
    try:
        return sbf_archive.read_archive(sbf_path)
    finally:
        Path(sbf_path).unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def scratch_install(tmp_path, monkeypatch) -> Path:
    """A real Hermes home with two real profiles, and a data path that does
    not exist yet. Returns the exported agent's real SOUL.md path."""
    home = tmp_path / "hermes-home"
    (home / "profiles" / THE_EXPORTED_AGENT).mkdir(parents=True)
    # The `default` profile IS the home directory itself and is always in
    # the roster, so it needs a soul of its own.
    (home / "SOUL.md").write_text("You are the Primary.\n", encoding="utf-8", newline="\n")
    soul_path = home / "profiles" / THE_EXPORTED_AGENT / "SOUL.md"
    soul_path.write_text(THE_AGENTS_HAND_AUTHORED_SOUL, encoding="utf-8", newline="\n")

    monkeypatch.setattr(settings, "hermes_home_path", home)
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path / "second-brain-data")
    monkeypatch.setattr(settings, "vault_path", tmp_path / "vault")
    monkeypatch.setattr(settings, "self_email", OWN_ADDRESS)
    monkeypatch.setattr(HermesCLI, "_hermes_exe", lambda self: None)
    monkeypatch.setattr(hermes_client_module, "_client", None)

    # The Registry's module-level cache, saved and put back -- otherwise a
    # test pointing the data path at `tmp_path` leaves the whole session's
    # Registry holding a scratch directory.
    monkeypatch.setattr(registry_loader, "_registry", None)
    monkeypatch.setattr(registry_loader, "_hermes_reachable", lambda: False)
    return soul_path


@pytest.fixture
def one_of_every_kind(tmp_path, monkeypatch) -> dict[str, Path]:
    """One artifact of each of the seven kinds, reachable by a real export.

    Returns the agent's Registry-side mirror directory -- the `Agent.json`/
    `soul.md` pair `artifact_export` really reads for an `agent` entry
    (`registry_loader.agent_data_dir`), which is NOT the Hermes-side
    SOUL.md the publication pass writes.
    """
    templates_data.write_template_json(A_TEMPLATE, {"id": A_TEMPLATE, "note_name": A_TEMPLATE})
    indexes_data.write_index_json(AN_INDEX, {"id": AN_INDEX, "name": "ADNOC"})
    pipelines_data.write_pipeline_json(A_PIPELINE, {
        "id": A_PIPELINE, "name": "Morning Sweep", "description": "Sweeps the inbox",
        "schedule": "0 6 * * *", "steps": [],
    })
    actions_data.write_action_json(AN_ACTION, {
        "id": AN_ACTION,
        "description": "List the open Actions assigned to the operator's own organisation",
        "inputs": [{"name": "team", "type": "string", "required": True}],
        "allowed_callers": [THE_EXPORTED_AGENT],
        "needs_confirmation": False,
        "implementation": {"skill": {"skill_id": A_SKILL}},
    })
    workflows_data.write_workflow_json(A_WORKFLOW, {
        "id": A_WORKFLOW,
        "request_kind": "list the open Actions and mail them to me",
        "description": "The operator's standing handling for this ask",
        "steps": [{"id": "collect", "action_id": AN_ACTION, "inputs": {"team": "CBO"}}],
    })

    mirror = tmp_path / "registry-mirror" / THE_EXPORTED_AGENT
    mirror.mkdir(parents=True)
    (mirror / "Agent.json").write_text(
        json.dumps({"id": THE_EXPORTED_AGENT, "name": "Blue Agent", "type": "expert"}, indent=2),
        encoding="utf-8",
    )
    (mirror / "soul.md").write_text(THE_AGENTS_HAND_AUTHORED_SOUL, encoding="utf-8")
    monkeypatch.setattr(
        registry_loader, "agent_data_dir",
        lambda agent_id: mirror if agent_id == THE_EXPORTED_AGENT else None,
    )

    a_skill = SimpleNamespace(id=A_SKILL, name="Vault Search", description="Search the vault")
    an_agent = SimpleNamespace(
        id=THE_EXPORTED_AGENT, name="Blue Agent", description="A fictional expert",
        depends_on=[], skill_ids=[],
    )
    for module in (artifacts_inventory, artifact_dependency_resolver):
        monkeypatch.setattr(module, "_skill_manager", _FixedManager([a_skill]))
        monkeypatch.setattr(module, "_template_manager", _FixedManager([
            SimpleNamespace(id=A_TEMPLATE, note_name=A_TEMPLATE, error=None),
        ]))
        monkeypatch.setattr(module, "_agent_manager", _FixedManager([an_agent]))
        monkeypatch.setattr(module, "_pipeline_manager", _FixedManager([
            SimpleNamespace(id=A_PIPELINE, name="Morning Sweep", description="Sweeps the inbox"),
        ]))
        monkeypatch.setattr(module, "_index_manager", _FixedManager([
            SimpleNamespace(id=AN_INDEX, name="ADNOC"),
        ]))
    monkeypatch.setattr(skills_data, "read_skill_md", lambda skill_id: "---\nname: Vault Search\n---\nSearches the vault.\n")
    monkeypatch.setattr(skills_data, "list_scripts", lambda skill_id: {})
    monkeypatch.setattr(skills_data, "category_of", lambda skill_id: "vault")
    monkeypatch.setattr(artifact_export, "_export_agent_profile_tarball", lambda agent_id: THE_OPAQUE_PROFILE_TARBALL)
    return {"mirror": mirror}


@pytest.fixture
def a_saved_profile(scratch_install) -> dict:
    """A real Profile on disk, really published into the agent's own
    SOUL.md -- waited for, so the pass has finished before anything is
    exported."""
    OperatorProfileManager().save(A_PROFILE)
    assert operator_manager_module.join_background_publications(timeout=30.0)
    published_soul = scratch_install.read_text(encoding="utf-8")
    assert "## Who you work for" in published_soul, "the publication pass did not run"
    return {"published_soul": published_soul}


def test_the_profile_is_not_an_artifact_kind_and_no_selection_can_name_it(
    a_saved_profile, one_of_every_kind,
) -> None:
    """[REQ-SB-95-US-01-AC-06] It cannot be selected, and it cannot be
    resolved into a closure as anything's dependency.

    The names tried are derived from the store's own folder and file, so
    this does not depend on guessing what a future kind would be called --
    and the first assertion is what fails loudly if one of them ever
    becomes a real kind, which is the direction a guard should date in.
    """
    store_folder, store_file = the_profile_store()
    names_it_could_be_offered_under = {
        store_folder.lower(),
        PurePosixPath(store_file).stem.lower(),
        f"{store_folder.lower()}_{PurePosixPath(store_file).stem.lower()}",
    }

    live_kinds = {entry["kind"].lower() for entry in artifacts_inventory.list_all_artifacts()}
    assert not live_kinds & names_it_could_be_offered_under, (
        "the Operator Profile is offered as an exportable artifact kind (ADR-032 forbids it)"
    )
    assert not {folder.lower() for folder in artifact_export._PAYLOAD_FOLDER.values()} & {
        store_folder.lower(),
    }

    for kind in sorted(names_it_could_be_offered_under):
        assert artifact_dependency_resolver.resolve_closure(
            [{"kind": kind, "id": PurePosixPath(store_file).stem}],
        ) == []

    # Not vacuous: there really is a record that an export could have
    # reached, and the install really has artifacts to export.
    assert operator_profile_data.profile_exists()
    assert {entry["kind"] for entry in everything_this_install_offers()} >= {
        "skill", "template", "agent", "pipeline", "index", "action", "workflow",
    }, "the fixture's own artifacts are not offered -- the assertions above are vacuous"


def test_a_bundle_of_every_live_kind_carries_nothing_of_the_profile(
    a_saved_profile, one_of_every_kind,
) -> None:
    """[REQ-SB-95-US-01-AC-06] The real archive's own members, over a
    selection taken from the live inventory.

    The containment rule is the part that survives a future kind: the ONLY
    bundle member allowed to carry a Profile value is the exported agent's
    own `soul.md` (`AC-08`, accepted by the operator 2026-10-17). Any other
    member carrying one -- an eighth kind that swept `data/Operator/` in
    beside `data/Actions/`, a seed file, a new mirror -- fails here.
    """
    mirror = one_of_every_kind["mirror"]
    # The Registry-side mirror as it really is after any agent edit that
    # follows a publication (`AgentManager.update()` rewrites it from the
    # Hermes-side soul) -- the genuine worst case, not a kinder one.
    (mirror / "soul.md").write_text(a_saved_profile["published_soul"], encoding="utf-8")

    selection = everything_this_install_offers()
    manifest, payload = export(selection)

    # Positive control, derived per kind: every selected kind really did
    # contribute payload, so the absences below mean something.
    for entry in selection:
        folder = artifact_export._PAYLOAD_FOLDER.get(entry["kind"], entry["kind"] + "s")
        assert any(member.startswith(f"{folder}/") for member in payload), entry
    assert payload[f"agents/{THE_EXPORTED_AGENT}/profile.tar.gz"] == THE_OPAQUE_PROFILE_TARBALL

    store_folder, store_file = the_profile_store()
    assert [member for member in payload if store_folder.lower() in member.lower().split("/")] == []
    assert [member for member in payload if PurePosixPath(member).name == store_file] == []
    assert [
        artifact for artifact in manifest["artifacts"]
        if store_folder.lower() in f"{artifact['kind']}{artifact['id']}".lower()
    ] == []

    # The record's own bytes, verbatim, are in no member of the archive.
    stored_record = operator_profile_data.profile_path().read_bytes()
    assert [member for member, content in payload.items() if stored_record in content] == []

    the_agents_own_soul = f"agents/{THE_EXPORTED_AGENT}/soul.md"
    carried_by = {
        value: sorted(member for member, content in payload.items() if value.encode("utf-8") in content)
        for value in the_personal_values_really_stored()
    }
    leaks = {value: members for value, members in carried_by.items() if set(members) - {the_agents_own_soul}}
    assert leaks == {}, f"a Profile value travels outside the exported agent's own soul.md: {leaks}"

    # And the allowance is real rather than a hole nothing uses: the
    # published block genuinely is in that one file (the AC-08 disclosure).
    assert carried_by[A_PROFILE["team"][0]["email"]] == [the_agents_own_soul]
    assert carried_by[A_PROFILE["name"]] == [the_agents_own_soul]


def test_no_seed_data_entry_names_the_profile(a_saved_profile) -> None:
    """[REQ-SB-95-US-01-AC-06] The other door into a bundle: a plugin's
    allowlisted seed-data paths, which are written as archive members
    without any kind being selected at all."""
    store_folder, store_file = the_profile_store()

    for target_path, needle in artifact_seed_data.seed_data_files().items():
        parts = PurePosixPath(target_path).parts
        assert PurePosixPath(target_path).name != store_file, target_path
        assert store_folder not in parts, target_path
        assert needle != store_file, target_path


def test_even_a_seed_entry_naming_the_store_carries_no_byte_of_the_record(
    a_saved_profile, one_of_every_kind, monkeypatch,
) -> None:
    """[REQ-SB-95-US-01-AC-06] Defence in depth, and the reason the live
    check above is not the whole guard: seed-data content is forced to
    empty regardless of what the real file holds, so even a future plugin
    registering the Profile's own store as seed data cannot ship the
    operator's team."""
    relative_store_path = operator_profile_data.profile_path().relative_to(
        settings.second_brain_data_path,
    ).as_posix()
    monkeypatch.setattr(plugin_manager_module, "_plugin_seed_data_files", [relative_store_path])
    monkeypatch.setattr(
        skills_data, "read_skill_md",
        lambda skill_id: f"---\nname: Vault Search\n---\nIt reads {the_profile_store()[1]}.\n",
    )

    _, payload = export([{"kind": "skill", "id": A_SKILL}])

    hostile_member = f"seed_data/{relative_store_path}"
    assert payload[hostile_member] == b""
    for value in the_personal_values_really_stored():
        assert [member for member, content in payload.items() if value.encode("utf-8") in content] == []


def test_what_travels_is_byte_identical_with_and_without_a_saved_profile(
    one_of_every_kind,
) -> None:
    """[REQ-SB-95-US-01-AC-06] The Profile's existence changes nothing that
    travels -- same members, same bytes, same manifest artifacts.

    Asserted with the Registry-side mirror left exactly as it was across
    both exports, because that is what the export really reads and what a
    publication pass really does: `publish_operator_profile` writes the
    Hermes-side SOUL.md and deliberately not the mirror (`AC-07`). So the
    bundle is unchanged by a Profile save, which is the claim.
    """
    selection = everything_this_install_offers()
    assert not operator_profile_data.profile_exists()
    manifest_before, payload_before = export(selection)

    OperatorProfileManager().save(A_PROFILE)
    assert operator_manager_module.join_background_publications(timeout=30.0)
    assert operator_profile_data.profile_exists()

    manifest_after, payload_after = export(selection)

    assert payload_after == payload_before
    assert manifest_after["artifacts"] == manifest_before["artifacts"]
    assert manifest_after["secret_scan"] == manifest_before["secret_scan"]
