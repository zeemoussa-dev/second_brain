"""Workflows published into agent context, and a matching request handled
end to end (REQ-SB-95-US-04-T06, `ADR-034`).

The block is the fourth auto-generated, marker-delimited section of an
agent's own SOUL.md, beside the specialists, index-guidance and Action
ones `AgentManager` already owns. It is regenerated FROM the Workflow
catalogue -- per agent, filtered down to the Workflows that agent could
really run, idempotently, and removed entirely for an agent that can run
none.

**What it deliberately does NOT carry is the steps.** `ADR-034` puts the
order, the confirmation points and the report in the run record, so the
published text is "these kinds of request have documented handling, and
the way to act on one is to start a run". The last test in this file is
what makes that real: the runner script never learns the steps, and the
run still happens in the documented order with the report composed by
the app.

The file is in four parts:

1. **The block itself** -- driven by calling `publish_workflow_catalogue()`
   explicitly, with the automatic triggers silenced so a test asserting
   "this is what MY publication did" is not racing one it did not start.
2. **The trigger** -- that `WorkflowManager.create()`, `update()` and
   `delete()` each fire publication, that it really reaches the agents,
   and that the save does not wait for the writes.
3. **A real profile, byte for byte** -- a scratch Hermes home holding a
   real SOUL.md on disk, published into through the real
   `AgentManager.update()`, with the bytes before and after compared.
   Reasoning about `_rewrite_soul()` is not proof; `BUG-093`/`BUG-092`
   are what happens when it is treated as one.
4. **A matching request, end to end** -- the shipped runner script,
   loaded from a throwaway deployed profile and pointed at the real app
   through a loopback-shaped transport, running a real two-step Workflow.

Nothing here can reach the operator's own install. `tests/conftest.py`
sandboxes Hermes for every test; the tests that want one build it under
`tmp_path`, and every store these tests touch -- Actions, Workflows,
WorkflowRuns, the Action-call ledger, the Registry data path -- is
redirected onto `tmp_path` or into memory first.
"""
import copy
import importlib.util
import io
import json
import shutil
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.business.hermes.client as hermes_client_module
import app.main as main_app
from app.business.core.actions import action_manager as action_manager_module
from app.business.core.actions.action_manager import ActionManager
from app.business.core.agents.agent import Agent
from app.business.core.agents.agent_manager import (
    _WORKFLOW_CATALOGUE_BEGIN,
    _WORKFLOW_CATALOGUE_END,
    AgentManager,
    _rewrite_soul,
    _split_soul_sections,
)
from app.business.core.workflows import workflow_manager as workflow_manager_module
from app.business.core.workflows.workflow_manager import WorkflowManager
from app.config import settings
from app.data_access.registry import loader as registry_loader
from app.data_access.registry import writer as registry_writer
from app.hermes.cli import HermesCLI

client = TestClient(main_app.app)

A_REAL_ROUTE = ("POST", "/vault-index/refresh")
A_REAL_FEATURE_KEY = "/settings/actions"
A_DEPLOYED_SKILL = "capture-the-thread"
THE_CALLER = "cbo-agent"
THE_BASE_URL = "http://127.0.0.1:8001"

RUNNER_DIR = (
    Path(main_app.__file__).resolve().parent
    / "business" / "core" / "skills" / "catalog" / "actions" / "call-action" / "scripts"
)

# Prose this app cannot read, inside and outside the two sections it can,
# plus a final newline -- so "every other byte identical" has something to
# be wrong about.
HAND_AUTHORED_SOUL = (
    "You are the Customer Expert.\n\n"
    "## Scope boundary\n\n"
    "Only ADNOC.\n\n"
    "## Guardrails\n\n"
    "Never invent a number.\n\n"
    "## Scope\n\n"
    "Everything ADNOC, and ask before you widen it.\n\n"
    "Folders: Customers\n"
    "Tags: adnoc\n"
)


@pytest.fixture
def resolvable(monkeypatch):
    """The three live resolution sources, replaced by ones these tests
    control -- what is deployed, routed and registered on this machine is
    instance state."""
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.app_route_table", lambda: {A_REAL_ROUTE},
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.deployed_skill_ids",
        lambda: {A_DEPLOYED_SKILL},
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.UI_FEATURE_KEYS", (A_REAL_FEATURE_KEY,),
    )


def _raise_missing(entity_id: str):
    raise FileNotFoundError(entity_id)


@pytest.fixture
def stored_actions(monkeypatch, resolvable) -> dict:
    """The whole Action store, in memory, keyed by action id."""
    written: dict = {}
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.write_action_json",
        lambda action_id, data: written.update({action_id: data}),
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.read_action_json",
        lambda action_id: written[action_id] if action_id in written else _raise_missing(action_id),
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.list_action_ids",
        lambda: sorted(written),
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.delete_action_definition",
        lambda action_id: written.pop(action_id, None),
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.ActionManager._plugin_contributed",
        lambda self: [],
    )
    return written


@pytest.fixture
def stored_workflows(monkeypatch) -> dict:
    """The whole Workflow store, in memory, keyed by workflow id -- so no
    test here can read or write `<DATA_PATH>/data/Workflows/`."""
    written: dict = {}
    monkeypatch.setattr(
        "app.business.core.workflows.workflow_manager.workflows_data.write_workflow_json",
        lambda workflow_id, data: written.update({workflow_id: data}),
    )
    monkeypatch.setattr(
        "app.business.core.workflows.workflow_manager.workflows_data.read_workflow_json",
        lambda workflow_id: (
            written[workflow_id] if workflow_id in written else _raise_missing(workflow_id)
        ),
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
def publication_is_explicit_only(monkeypatch):
    """Both automatic triggers, off -- for the tests that drive
    publication themselves.

    The Action one too, not only the Workflow one: these tests save
    Actions to build a catalogue their Workflows can reference, and an
    Action-catalogue block arriving in the background would land in the
    very souls whose "nothing outside the markers changed" is the thing
    under test.
    """
    monkeypatch.setattr(
        workflow_manager_module, "publish_workflow_catalogue_in_background", lambda: None,
    )
    monkeypatch.setattr(
        action_manager_module, "publish_action_catalogue_in_background", lambda: None,
    )


@pytest.fixture
def souls(monkeypatch) -> dict:
    """Two agents whose real SOUL.md text lives in this dict.

    Stands in for Hermes at the three seams publication uses -- read one
    agent, read the roster, write one agent's SOUL -- and goes through
    `AgentManager`'s own real `_split_soul_sections` and `_rewrite_soul`,
    so what a test reads back is what a real profile would hold. Part 3
    below then does the same thing against a real file on disk.
    """
    store = {"customer-expert": HAND_AUTHORED_SOUL, "note-taker": "You are the Note Taker."}

    def read_one(self: AgentManager, agent_id: str) -> Agent | None:
        if agent_id not in store:
            return None
        core_prompt, guardrails, scope = _split_soul_sections(store[agent_id])
        return Agent(
            id=agent_id, name=agent_id, description=None, type="worker", section_id=None,
            is_background_agent=False, icon=None, color=None, working_mode="autonomous",
            managed_by="hermes", model=None, reasoning_effort=None,
            prompt=core_prompt, guardrails=guardrails, scope=scope,
        )

    def read_all(self: AgentManager, **_: object) -> list[Agent]:
        return [read_one(self, agent_id) for agent_id in sorted(store)]

    def write_one(self: AgentManager, agent_id: str, **fields: object) -> Agent | None:
        if read_one(self, agent_id) is None:
            return None
        store[agent_id] = _rewrite_soul(
            store[agent_id],
            prompt=fields.get("prompt"),
            guardrails=fields.get("guardrails"),
            scope=fields.get("scope"),
        )
        return read_one(self, agent_id)

    monkeypatch.setattr(AgentManager, "get_by_id", read_one)
    monkeypatch.setattr(AgentManager, "get_all", read_all)
    monkeypatch.setattr(AgentManager, "update", write_one)
    return store


def _block_of(soul_text: str) -> str:
    """The published block, markers included -- and proof there is exactly
    one of each marker while we are here."""
    assert soul_text.count(_WORKFLOW_CATALOGUE_BEGIN) == 1
    assert soul_text.count(_WORKFLOW_CATALOGUE_END) == 1
    start = soul_text.index(_WORKFLOW_CATALOGUE_BEGIN)
    end = soul_text.index(_WORKFLOW_CATALOGUE_END) + len(_WORKFLOW_CATALOGUE_END)
    return soul_text[start:end]


def _outside_the_block(soul_text: str) -> str:
    start = soul_text.index(_WORKFLOW_CATALOGUE_BEGIN)
    end = soul_text.index(_WORKFLOW_CATALOGUE_END) + len(_WORKFLOW_CATALOGUE_END)
    return soul_text[:start] + soul_text[end:]


def _publish() -> list[str]:
    return AgentManager().publish_workflow_catalogue()


def _two_actions(allowed_callers: list[str] | None = None) -> None:
    manager = ActionManager()
    manager.create(
        "list-the-teams-actions",
        description="List the actions assigned to my team",
        allowed_callers=list(allowed_callers or ["customer-expert"]),
        implementation={"ui": {"feature_key": A_REAL_FEATURE_KEY}},
    )
    manager.create(
        "mail-it-to-me",
        description="Send it to the operator by mail",
        allowed_callers=list(allowed_callers or ["customer-expert"]),
        implementation={"skill": {"skill_id": A_DEPLOYED_SKILL}},
    )


def _two_workflows() -> None:
    manager = WorkflowManager()
    manager.create(
        "team-actions-by-mail",
        request_kind="give me the list of actions assigned to my team and send it to me by mail",
        description="The operator's own standing request, handled the same way every time.",
        steps=[
            {"id": "gather", "action_id": "list-the-teams-actions"},
            {"id": "send", "action_id": "mail-it-to-me"},
        ],
        report={"description": "which actions were listed and whether the mail really went"},
    )
    manager.create(
        "weekly-account-digest",
        request_kind="send me this week's account digest",
        steps=[{"id": "collect", "action_id": "list-the-teams-actions"}],
        report={"description": "the digest that was sent"},
    )


# ---------------------------------------------------------------- part 1
# The published block itself.


def test_both_workflows_are_published_with_their_request_kind_and_how_to_start_one(
    stored_actions, stored_workflows, souls, publication_is_explicit_only,
) -> None:
    """[REQ-SB-95-US-04-AC-03] Two Workflows, published into one agent's
    SOUL.md: each named with the kind of request it handles and what it
    reports, inside one marker pair, with the start-a-run instruction and
    nothing of the hand-authored file disturbed.

    The steps are asserted ABSENT. Reciting them here is `ADR-034`'s
    rejected alternative -- the run engine owns the order, and a second,
    unenforced copy of it in the prompt is exactly the prompt-only
    grounding this requirement replaces."""
    _two_actions()
    _two_workflows()

    assert sorted(_publish()) == ["customer-expert"]
    block = _block_of(souls["customer-expert"])

    assert "`team-actions-by-mail`" in block
    assert "give me the list of actions assigned to my team and send it to me by mail" in block
    assert "The operator's own standing request, handled the same way every time." in block
    assert "which actions were listed and whether the mail really went" in block

    assert "`weekly-account-digest`" in block
    assert "send me this week's account digest" in block

    assert "POST /workflows/<workflow_id>/run" in block, "the start-a-run instruction"
    assert "POST /workflows/runs/<run_id>/next-step" in block
    assert "POST /workflows/runs/<run_id>/steps/<step_id>/outcome" in block
    assert "caller_agent_id" in block
    assert "do not hand-edit" in block

    for an_action_a_step_names in ("list-the-teams-actions", "mail-it-to-me"):
        assert an_action_a_step_names not in block, (
            "the published text must not recite the steps -- the run engine owns the order, and "
            "a second, unenforced copy of it in the prompt is what ADR-034 rejected"
        )

    # Every character that is not the block and the blank line
    # introducing it is the hand-authored file, unchanged.
    assert souls["customer-expert"].replace("\n\n" + block, "") == HAND_AUTHORED_SOUL
    assert _WORKFLOW_CATALOGUE_BEGIN not in souls["note-taker"], (
        "an agent that may call neither step's Action is told about neither Workflow"
    )


def test_a_workflow_an_agent_could_not_finish_is_never_published_to_it(
    stored_actions, stored_workflows, souls, publication_is_explicit_only,
) -> None:
    """[REQ-SB-95-US-04-AC-03] A Workflow is published to an agent only
    when every step names an Action that agent may call. Telling an agent
    about handling that would be refused at a step it cannot reach is the
    fabricated capability this requirement exists to close -- and the run
    would be refused anyway, because the published text decides
    nothing."""
    ActionManager().create(
        "list-the-teams-actions",
        description="List the actions assigned to my team",
        allowed_callers=["*"],
        implementation={"ui": {"feature_key": A_REAL_FEATURE_KEY}},
    )
    ActionManager().create(
        "mail-it-to-me",
        description="Send it to the operator by mail",
        allowed_callers=["customer-expert"],
        implementation={"skill": {"skill_id": A_DEPLOYED_SKILL}},
    )
    _two_workflows()

    _publish()

    assert "`team-actions-by-mail`" in _block_of(souls["customer-expert"])
    assert "`weekly-account-digest`" in _block_of(souls["customer-expert"])
    # `note-taker` may call the first Action and not the second, so it is
    # told about the one-step Workflow and not the two-step one.
    assert "`weekly-account-digest`" in _block_of(souls["note-taker"])
    assert "team-actions-by-mail" not in souls["note-taker"]


def test_an_agent_with_no_runnable_workflow_carries_no_block_at_all(
    stored_actions, stored_workflows, souls, publication_is_explicit_only,
) -> None:
    """[REQ-SB-95-US-04-AC-03] No empty shell. A heading over nothing
    reads to an agent as "this app documents no handling", which is a
    different claim from "none of it is yours to run"."""
    _two_actions(allowed_callers=["note-taker"])
    _two_workflows()

    _publish()

    assert _WORKFLOW_CATALOGUE_BEGIN not in souls["customer-expert"]
    assert _WORKFLOW_CATALOGUE_END not in souls["customer-expert"]
    assert souls["customer-expert"] == HAND_AUTHORED_SOUL
    assert _WORKFLOW_CATALOGUE_BEGIN in souls["note-taker"]


def test_republishing_replaces_its_own_block_and_leaves_everything_else_untouched(
    stored_actions, stored_workflows, souls, publication_is_explicit_only,
) -> None:
    """[REQ-SB-95-US-04-AC-03] Add, edit and delete a Workflow, each
    followed by a republication. Exactly one marker pair survives
    throughout, the block tracks every change, a pass with nothing to
    change writes nothing at all, and the hand-authored text around the
    block is byte-identical from first publication to last."""
    _two_actions()
    _two_workflows()
    _publish()
    outside_before = _outside_the_block(souls["customer-expert"])

    manager = WorkflowManager()
    manager.create(
        "file-the-thread",
        request_kind="file this mail thread",
        steps=[{"id": "file", "action_id": "mail-it-to-me"}],
    )
    _publish()
    assert "`file-the-thread`" in _block_of(souls["customer-expert"])

    manager.update("file-the-thread", request_kind="file this mail thread into the vault")
    _publish()
    block = _block_of(souls["customer-expert"])
    assert "file this mail thread into the vault" in block
    assert "file this mail thread\n" not in block

    assert _publish() == [], "a pass with nothing to change rewrites nothing"

    assert manager.delete("file-the-thread") == {"deleted": True}
    _publish()
    assert "file-the-thread" not in souls["customer-expert"]

    assert _outside_the_block(souls["customer-expert"]) == outside_before
    assert "## Scope boundary\n\nOnly ADNOC." in souls["customer-expert"]
    assert "Never invent a number." in souls["customer-expert"]
    assert "Folders: Customers" in souls["customer-expert"]
    assert souls["customer-expert"].endswith("\n"), "the file's own final newline (`BUG-092`)"


def test_one_agent_failing_to_publish_does_not_stop_the_rest(
    stored_actions, stored_workflows, souls, monkeypatch, publication_is_explicit_only,
) -> None:
    """[REQ-SB-95-US-04-AC-03] A profile Hermes refuses to write leaves
    that one agent's block stale -- which `ADR-034` accepts, since the run
    engine reads the stored Workflow and never this text -- but the other
    agents still have to be told."""
    _two_actions(allowed_callers=["*"])
    _two_workflows()
    write_one = AgentManager.update

    def refuse_customer_expert(self: AgentManager, agent_id: str, **fields: object):
        if agent_id == "customer-expert":
            raise RuntimeError("hermes refused this profile")
        return write_one(self, agent_id, **fields)

    monkeypatch.setattr(AgentManager, "update", refuse_customer_expert)

    assert _publish() == ["note-taker"]
    assert souls["customer-expert"] == HAND_AUTHORED_SOUL
    assert "`team-actions-by-mail`" in _block_of(souls["note-taker"])


def test_an_action_pass_and_a_workflow_pass_never_drop_each_others_block(
    stored_actions, stored_workflows, souls, publication_is_explicit_only, monkeypatch,
) -> None:
    """[REQ-SB-95-US-04-AC-03] Two catalogues, two background passes, one
    SOUL.md. Each pass composes its new text from the agent it read when
    it started, so two in flight together is a plain lost update.

    Found live on 2026-10-18, not reasoned about: on a disposable install,
    an Action save and a Workflow save seconds apart left the profile
    carrying the Action block and no Workflow block at all. Here the
    Workflow pass is held open inside its first write and an Action pass
    is started on top of it; both blocks have to survive."""
    _two_actions(allowed_callers=["*"])
    _two_workflows()

    write_one = AgentManager.update
    first_write_began = threading.Event()
    let_the_first_write_finish = threading.Event()
    already_slowed: list[str] = []

    def slow_the_first_write(self: AgentManager, agent_id: str, **fields: object):
        if not already_slowed:
            already_slowed.append(agent_id)
            first_write_began.set()
            let_the_first_write_finish.wait(timeout=10.0)
        return write_one(self, agent_id, **fields)

    monkeypatch.setattr(AgentManager, "update", slow_the_first_write)

    workflow_pass = threading.Thread(target=AgentManager().publish_workflow_catalogue)
    workflow_pass.start()
    assert first_write_began.wait(timeout=10.0), "the Workflow pass reached its first write"

    action_pass = threading.Thread(target=AgentManager().publish_action_catalogue)
    action_pass.start()
    let_the_first_write_finish.set()
    workflow_pass.join(timeout=10.0)
    action_pass.join(timeout=10.0)
    assert not workflow_pass.is_alive() and not action_pass.is_alive()

    for agent_id in ("customer-expert", "note-taker"):
        assert _WORKFLOW_CATALOGUE_BEGIN in souls[agent_id], agent_id
        assert "BEGIN ACTION CATALOGUE" in souls[agent_id], agent_id


# ---------------------------------------------------------------- part 2
# The trigger: no caller has to remember a second step.


def test_create_update_and_delete_each_fire_publication(
    stored_actions, stored_workflows, monkeypatch,
) -> None:
    """[REQ-SB-95-US-04-AC-03] Every Workflow write triggers a
    republication, so editing the catalogue IS the whole operation.

    A refused save and a delete of an id this install never had fire
    nothing: neither changed the catalogue, so republishing on them would
    rewrite every agent's SOUL.md to say exactly what it already said."""
    monkeypatch.setattr(
        action_manager_module, "publish_action_catalogue_in_background", lambda: None,
    )
    fired: list[str] = []
    monkeypatch.setattr(
        workflow_manager_module, "publish_workflow_catalogue_in_background",
        lambda: fired.append("published"),
    )
    _two_actions()
    manager = WorkflowManager()

    manager.create("team-actions-by-mail", request_kind="the standing one",
                   steps=[{"id": "gather", "action_id": "list-the-teams-actions"}])
    assert fired == ["published"], "create() publishes"

    manager.update("team-actions-by-mail", request_kind="the standing request")
    assert fired == ["published"] * 2, "update() publishes"

    manager.delete("team-actions-by-mail")
    assert fired == ["published"] * 3, "delete() publishes"

    assert manager.delete("never-existed") == {"deleted": False}
    assert manager.update("never-existed", request_kind="nothing") is None
    with pytest.raises(workflow_manager_module.WorkflowStepActionNotFoundError):
        manager.create("broken", steps=[{"action_id": "no-such-action"}])
    assert fired == ["published"] * 3, "nothing that changed no catalogue republishes"


def test_saving_a_workflow_really_reaches_the_agents_with_no_explicit_publish(
    stored_actions, stored_workflows, souls, monkeypatch,
) -> None:
    """[REQ-SB-95-US-04-AC-03] End to end through the real background
    pass: the only calls this test makes are the save and the delete, and
    the agents' own SOUL text carries each change afterwards."""
    monkeypatch.setattr(
        action_manager_module, "publish_action_catalogue_in_background", lambda: None,
    )
    _two_actions()

    WorkflowManager().create(
        "team-actions-by-mail",
        request_kind="give me my team's actions and mail them to me",
        steps=[{"id": "gather", "action_id": "list-the-teams-actions"}],
    )
    assert workflow_manager_module.join_background_publications(timeout=30.0)

    assert "`team-actions-by-mail`" in _block_of(souls["customer-expert"])
    assert "give me my team's actions and mail them to me" in souls["customer-expert"]
    assert "## Scope boundary\n\nOnly ADNOC." in souls["customer-expert"], (
        "the hand-authored text is still there afterwards"
    )

    WorkflowManager().delete("team-actions-by-mail")
    assert workflow_manager_module.join_background_publications(timeout=30.0)

    assert _WORKFLOW_CATALOGUE_BEGIN not in souls["customer-expert"]
    assert souls["customer-expert"] == HAND_AUTHORED_SOUL


def test_saving_a_workflow_returns_without_waiting_for_the_republication(
    stored_actions, stored_workflows, monkeypatch,
) -> None:
    """[REQ-SB-95-US-04-AC-03] The same measurement that produced the
    operator's 2026-10-18 decision for Actions: publication costs ~2.7s
    per agent, so one save would hold the screen for ~110s across a
    41-profile install. `create()` has to come back while the pass is
    still running, not after it."""
    publication_started = threading.Event()
    let_publication_finish = threading.Event()
    publication_finished = threading.Event()

    def slow_publication() -> list[str]:
        publication_started.set()
        let_publication_finish.wait(timeout=30.0)
        publication_finished.set()
        return []

    monkeypatch.setattr(
        action_manager_module, "publish_action_catalogue_in_background", lambda: None,
    )
    monkeypatch.setattr(workflow_manager_module, "publish_workflow_catalogue", slow_publication)
    _two_actions()

    WorkflowManager().create(
        "team-actions-by-mail", request_kind="the standing request",
        steps=[{"id": "gather", "action_id": "list-the-teams-actions"}],
    )

    assert publication_started.wait(timeout=10.0), "the pass really ran"
    assert not publication_finished.is_set(), "create() returned before it finished"

    let_publication_finish.set()
    assert workflow_manager_module.join_background_publications(timeout=30.0)
    assert publication_finished.is_set()


def test_a_pass_that_outlives_its_install_publishes_into_nothing(
    stored_actions, stored_workflows, souls, monkeypatch, tmp_path,
) -> None:
    """[REQ-SB-95-US-04-AC-03] `hermes_home_path` is reconfigurable while
    the app is running (`REQ-SB-89`'s setup wizard), and nothing waits for
    a publication pass. A pass that is still in flight when the install
    changes underneath it must abandon itself rather than write one
    install's catalogue into another install's profiles."""
    published: list[str] = []
    monkeypatch.setattr(
        workflow_manager_module, "publish_workflow_catalogue",
        lambda: published.append("published") or [],
    )

    assert workflow_manager_module._publish_into(tmp_path / "an-install-this-is-not") == []
    assert published == [], "it refused to publish into an install it was not started for"

    assert workflow_manager_module._publish_into(settings.hermes_home_path) == []
    assert published == ["published"], "and still publishes into the one it was"


# ---------------------------------------------------------------- part 3
# A real SOUL.md on disk, compared byte for byte.


@pytest.fixture
def registry_globals_are_restored(monkeypatch):
    """The Registry's module-level cache, saved and put back.

    A real `AgentManager.update()` reloads it from whatever data path is
    configured, so a test that points that path at `tmp_path` would
    otherwise leave the whole session's Registry holding a scratch
    directory's contents -- an order-dependent failure for whatever runs
    next, and one that would look like a defect in that test.
    """
    monkeypatch.setattr(registry_loader, "_registry", registry_loader._registry)
    monkeypatch.setattr(
        registry_loader, "_last_seen_fingerprint", registry_loader._last_seen_fingerprint,
    )
    monkeypatch.setattr(registry_loader, "_status", copy.deepcopy(registry_loader._status))


def test_publishing_into_a_real_profile_changes_only_the_block(
    stored_actions, stored_workflows, publication_is_explicit_only,
    registry_globals_are_restored, tmp_path, monkeypatch,
) -> None:
    """[REQ-SB-95-US-04-AC-03] The invariant, proved against real bytes
    rather than argued from the code: a write that adds this block leaves
    every other byte of a real SOUL.md identical -- the other sections,
    their prose, their order and the final newline.

    A real scratch Hermes home with a real profile, the real
    `AgentManager.update()` (real `HermesProfiles.read_soul`/`write_soul`,
    real Registry mirror), and the Registry data path redirected onto
    `tmp_path` so nothing is written outside it."""
    home = tmp_path / "hermes-home"
    (home / "profiles" / "customer-expert").mkdir(parents=True)
    soul_path = home / "profiles" / "customer-expert" / "SOUL.md"
    soul_path.write_text(HAND_AUTHORED_SOUL, encoding="utf-8", newline="\n")
    # The `default` profile IS the home directory itself, and the roster
    # always includes it -- so it needs a soul too, or the pass is
    # publishing into one profile and skipping an unreadable one.
    (home / "SOUL.md").write_text("You are the Primary.\n", encoding="utf-8", newline="\n")

    monkeypatch.setattr(settings, "hermes_home_path", home)
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path / "data-path")
    monkeypatch.setattr(HermesCLI, "_hermes_exe", lambda self: None)
    monkeypatch.setattr(hermes_client_module, "_client", None)

    # A real Registry for these two profiles, written by the real writer:
    # `update()` relocates an agent's Registry folder from its Section, and
    # an agent no Section has placed cannot be written at all.
    registry_writer.write_section_json("customers", {"id": "customers", "name": "Customers"})
    for agent_id in ("default", "customer-expert"):
        registry_writer.write_agent_files(
            registry_writer.agent_dir(agent_id, section_id="customers", is_background_agent=False),
            config={"id": agent_id, "name": agent_id, "type": "worker"},
            soul_text="placeholder, overwritten by the publication below",
        )

    _two_actions(allowed_callers=["*"])
    _two_workflows()
    before = soul_path.read_bytes()

    republished = AgentManager().publish_workflow_catalogue()

    assert "customer-expert" in republished
    after = soul_path.read_bytes()
    assert after != before

    block = _block_of(after.decode("utf-8"))
    assert "`team-actions-by-mail`" in block
    # Every byte that is not the block and the blank line introducing it.
    assert after.replace(("\n\n" + block).encode("utf-8"), b"") == before

    # And again: a second pass with nothing to change must not touch the
    # file at all -- `BUG-092`'s "a no-op republication must look like
    # one", which an mtime-watching vault sync reacts to.
    unchanged_at = soul_path.stat().st_mtime_ns
    assert AgentManager().publish_workflow_catalogue() == []
    assert soul_path.read_bytes() == after
    assert soul_path.stat().st_mtime_ns == unchanged_at


# ---------------------------------------------------------------- part 4
# A matching request, handled end to end by the runner script.


@pytest.fixture
def run_store(tmp_path, monkeypatch) -> Path:
    """`WorkflowRuns/` and the Action-call ledger, both onto `tmp_path` --
    the real writers, the real JSON, a throwaway directory."""
    runs = tmp_path / "WorkflowRuns"
    monkeypatch.setattr("app.data_access.workflow_runs._workflow_runs_root", lambda: runs)
    monkeypatch.setattr(
        "app.data_access.action_calls._action_calls_root", lambda: tmp_path / "ActionCalls",
    )
    return runs


@pytest.fixture
def loopback(monkeypatch) -> list[dict]:
    """`urllib.request.urlopen`, replaced by the app itself through
    `TestClient` (`httpx.ASGITransport`, in process). The routes, the run
    engine, the Action gate and the ledger are the real ones, no socket is
    opened, and nothing here can reach a backend on :8001 even if one is
    running. A refusal arrives as a real `HTTPError`, body and all."""
    made: list[dict] = []

    class _Response:
        def __init__(self, status: int, content: bytes):
            self.status = status
            self._content = content

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self) -> bytes:
            return self._content

    def fake_urlopen(request, timeout=None):
        body = json.loads(request.data.decode("utf-8"))
        assert request.get_method() == "POST"
        assert request.full_url.startswith(THE_BASE_URL + "/workflows/")
        path = request.full_url[len(THE_BASE_URL):]
        made.append({"path": path, "body": body})
        response = client.post(path, json=body)
        if response.status_code >= 400:
            raise urllib.error.HTTPError(
                request.full_url, response.status_code, "", {}, io.BytesIO(response.content),
            )
        return _Response(response.status_code, response.content)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return made


@pytest.fixture
def deployed_runner(tmp_path, monkeypatch):
    """The shipped runner Skill, copied into a throwaway Hermes profile in
    the flat shape a real deploy writes (scripts beside SKILL.md), with a
    one-line granted Skill beside it. Nothing it runs is the operator's.

    `run_workflow.py` is loaded from THERE rather than from the repo: it
    works out which agent it is from its own deployed path, and `import
    call_action` has to resolve to the copy deployed next to it.
    """
    monkeypatch.delenv("HERMES_PROFILE_ID", raising=False)
    skill_dir = tmp_path / "hermes" / "profiles" / THE_CALLER / "skills" / "actions" / "call-action"
    skill_dir.mkdir(parents=True)
    for script in ("call_action.py", "run_workflow.py"):
        shutil.copy(RUNNER_DIR / script, skill_dir / script)

    granted = tmp_path / "hermes" / "profiles" / THE_CALLER / "skills" / "vault" / A_DEPLOYED_SKILL
    granted.mkdir(parents=True)
    (granted / "SKILL.md").write_text("---\nname: capture-the-thread\n---\n", encoding="utf-8")
    (granted / "mail_it.py").write_text(
        "import json, sys\n"
        "handed_over = json.loads(sys.stdin.read() or '{}')\n"
        "print('mailed the list to ' + handed_over.get('to', 'nobody'))\n",
        encoding="utf-8",
    )

    monkeypatch.syspath_prepend(str(skill_dir))
    monkeypatch.delitem(sys.modules, "call_action", raising=False)
    spec = importlib.util.spec_from_file_location(
        "run_workflow_under_test", skill_dir / "run_workflow.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    yield module
    sys.modules.pop("call_action", None)


def drive(runner, capsys, *arguments) -> tuple[int, str]:
    """Run the script exactly as an agent's `terminal` call would -- its
    real `main()`, over a real command line."""
    original_argv = list(sys.argv)
    sys.argv = ["run_workflow.py", *arguments]
    try:
        code = runner.main()
    finally:
        sys.argv = original_argv
    captured = capsys.readouterr()
    return code, (captured.out + captured.err)


def test_a_matching_request_runs_the_documented_workflow_end_to_end(
    stored_actions, stored_workflows, run_store, loopback, deployed_runner, capsys,
) -> None:
    """[REQ-SB-95-US-04-AC-03] The whole point, in one test. The runner
    knows only a workflow id -- the published block never told it the
    steps -- and a real two-step Workflow runs anyway:

    - it starts a run and is handed step 1 and only step 1;
    - it reports that step's outcome and is then handed step 2;
    - step 2's Action is a Skill, so the app AUTHORISES it and the runner
      really performs it in its own profile (`ADR-019`);
    - what it finally relays is the run engine's own composed report, read
      back out of its own stdout and compared with the record on disk --
      not a summary the script assembled;
    - the run record holds both documented steps, in the documented order,
      both `done`, and no step that is not in the Workflow.
    """
    ActionManager().create(
        "list-the-teams-actions",
        description="List the actions assigned to my team",
        allowed_callers=["*"],
        implementation={"ui": {"feature_key": A_REAL_FEATURE_KEY}},
    )
    ActionManager().create(
        "mail-it-to-me",
        description="Send it to the operator by mail",
        inputs=[{"name": "to", "type": "string", "required": True, "description": "who"}],
        allowed_callers=["*"],
        implementation={"skill": {"skill_id": A_DEPLOYED_SKILL}},
    )
    WorkflowManager().create(
        "team-actions-by-mail",
        request_kind="give me the list of actions assigned to my team and send it to me by mail",
        steps=[
            {"id": "gather", "action_id": "list-the-teams-actions"},
            {"id": "send", "action_id": "mail-it-to-me", "inputs": {"to": "the operator"}},
        ],
        report={"description": "which actions were listed and whether the mail really went"},
    )

    code, said = drive(deployed_runner, capsys, "team-actions-by-mail")

    assert code == 0, said
    # One start, then for each step a next-step and an outcome, then the
    # final next-step that answers "there is no next step".
    assert [entry["path"].split("/")[-1] for entry in loopback] == [
        "run", "next-step", "outcome", "next-step", "outcome", "next-step",
    ], loopback
    assert loopback[0]["body"] == {"caller_agent_id": THE_CALLER}, (
        "it named itself from its own deployed path"
    )

    assert "RECORDED, NOT PERFORMED" in said, "step 1 is a `ui` Action -- the operator does it"
    assert A_REAL_FEATURE_KEY in said
    assert "mailed the list to the operator" in said, (
        "step 2's granted Skill really ran, in this profile, and said so itself"
    )

    run_files = sorted(run_store.glob("*.json"))
    assert len(run_files) == 1, run_files
    record = json.loads(run_files[0].read_text(encoding="utf-8"))
    assert [step["step_id"] for step in record["steps"]] == ["gather", "send"], (
        "every documented step, in the documented order, and no invented one"
    )
    assert [step["status"] for step in record["steps"]] == ["done", "done"]
    assert [step["dispatch_outcome"] for step in record["steps"]] == ["pointed_at", "authorised"]
    assert record["status"] == "complete"

    relayed = json.loads(said[said.index("THE APP'S OWN REPORT"):].split("\n", 1)[1])
    composed_now = client.post(f"/workflows/runs/{record['run_id']}/next-step").json()["report"]
    assert relayed == composed_now, (
        "what the agent relays is the app's composed report, not text the script wrote"
    )
    assert relayed["description"] == "which actions were listed and whether the mail really went"
    assert relayed["every_documented_step_done"] is True


def test_the_runner_stops_at_a_step_the_operator_must_confirm(
    stored_actions, stored_workflows, run_store, loopback, deployed_runner, capsys,
) -> None:
    """[REQ-SB-95-US-04-AC-03] A step marked for confirmation pauses the
    run at an `awaiting_confirmation` Action-call record. The runner
    reports what is waiting, performs nothing beyond it and makes no
    second attempt of its own -- the operator answers in the app."""
    ActionManager().create(
        "mail-it-to-me",
        description="Send it to the operator by mail",
        allowed_callers=["*"],
        needs_confirmation=True,
        implementation={"ui": {"feature_key": A_REAL_FEATURE_KEY}},
    )
    WorkflowManager().create(
        "mail-the-digest",
        request_kind="mail me the digest",
        steps=[{"id": "send", "action_id": "mail-it-to-me", "needs_confirmation": True}],
    )

    code, said = drive(deployed_runner, capsys, "mail-the-digest")

    assert code == 2, said
    assert "WAITING FOR THE OPERATOR" in said
    assert "NOTHING beyond it has run" in said
    assert "do not retry" in said.lower()
    assert [entry["path"].split("/")[-1] for entry in loopback] == ["run", "next-step"], (
        "it stopped rather than reporting an outcome nobody observed"
    )

    record = json.loads(sorted(run_store.glob("*.json"))[0].read_text(encoding="utf-8"))
    assert record["status"] == "awaiting_confirmation"
    assert record["steps"][0]["status"] == "awaiting_confirmation"
    waiting_on = record["steps"][0]["awaiting_call_id"]
    assert waiting_on
    assert f"--resume {record['run_id']}" in said, (
        "it names the run to come back to -- a second plain run would redo the earlier steps"
    )

    # The operator answers in the app, and the SAME run carries on.
    assert client.post(f"/actions/calls/{waiting_on}/confirm").status_code == 200
    code, said = drive(deployed_runner, capsys, "--resume", record["run_id"])

    assert code == 0, said
    assert "Continuing run" in said
    assert len(list(run_store.glob("*.json"))) == 1, "resuming opened no second run"
    resumed = json.loads(sorted(run_store.glob("*.json"))[0].read_text(encoding="utf-8"))
    assert resumed["status"] == "complete"
    assert resumed["steps"][0]["status"] == "done"
    assert len(resumed["steps"][0]["call_ids"]) == 2, (
        "ADR-033's own two rows: the operator's decision and the re-call that spends it"
    )


def test_an_unknown_workflow_is_the_apps_own_refusal_relayed(
    stored_actions, stored_workflows, run_store, loopback, deployed_runner, capsys,
) -> None:
    """[REQ-SB-95-US-04-AC-03] No run, no invented handling: the app's own
    sentence reaches the operator intact and the script does not fall back
    to working the request out itself."""
    code, said = drive(deployed_runner, capsys, "no-such-workflow")

    assert code == 2, said
    assert "NO RUN WAS STARTED" in said
    assert "there is no workflow 'no-such-workflow' in this install's catalogue" in said
    assert "Do not handle the request step by step yourself" in said
    assert list(run_store.glob("*.json")) == []
