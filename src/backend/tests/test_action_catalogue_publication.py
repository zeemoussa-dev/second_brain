"""The Action catalogue published into agent context
(REQ-SB-95-US-03-T01, ADR-033).

The block is the third auto-generated, marker-delimited section of an
agent's own SOUL.md, beside the specialists and index-guidance ones
AgentManager already owns, and it is regenerated FROM the catalogue --
per agent, filtered by `allowed_callers`, idempotently, and removed
entirely for an agent that may call nothing.

Each test drives `AgentManager.publish_action_catalogue()` explicitly.
The automatic trigger on `ActionManager.create()`/`update()`/`delete()`
is the open half of this task and is deliberately not wired yet
(ESCALATIONS.md, 2026-10-18: publication rewrites every affected
agent's REAL SOUL.md, and this suite has no Hermes sandbox), so there
is no test here pretending otherwise.

Hermes is stood in for by an in-memory SOUL.md store rather than
mocked method-by-method: publication is a round trip (read the real
SOUL text, split it, rewrite it, read it back), and the one property
that matters most -- that the hand-authored text around the block is
byte-identical afterwards -- is only testable if the test exercises
that whole round trip the way `AgentManager.update()` really does.

The Action store and the three resolution sources are monkeypatched
exactly as tests/test_action_resolution.py does them, so the catalogue
under test is this test's, never whatever the machine has saved.
"""
import pytest

from app.business.core.actions.action_manager import ActionManager
from app.business.core.agents.agent import Agent
from app.business.core.agents.agent_manager import (
    _ACTION_CATALOGUE_BEGIN,
    _ACTION_CATALOGUE_END,
    AgentManager,
    _split_soul_sections,
)

A_REAL_ROUTE = ("POST", "/vault-index/refresh")
HAND_AUTHORED_SOUL = (
    "You are the Customer Expert.\n\n"
    "## Scope boundary\n\n"
    "Only ADNOC.\n\n"
    "## Guardrails\n\n"
    "Never invent a number.\n\n"
    "## Scope\n\n"
    "Folders: Customers\n"
    "Tags: adnoc"
)


@pytest.fixture
def resolvable(monkeypatch):
    """The three live resolution sources, replaced by ones this test
    controls -- every Action below is an `http` one pointing at a
    single route, because what it points AT is not what is under test
    here."""
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.app_route_table",
        lambda: {A_REAL_ROUTE},
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.deployed_skill_ids", set,
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.UI_FEATURE_KEYS", (),
    )


def _raise_missing(action_id: str):
    raise FileNotFoundError(action_id)


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
        # FileNotFoundError, not a KeyError: an absent definition is an
        # OSError to every caller here, which is the one shape the read
        # paths are written to tolerate.
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
def souls(monkeypatch) -> dict:
    """Two agents whose real SOUL.md text lives in this dict.

    Stands in for Hermes at the three seams publication actually uses
    -- read one agent, read the roster, write one agent's SOUL -- and
    composes/splits through AgentManager's own real `_soul_text` and
    `_split_soul_sections`, so what a test reads back is what a real
    profile would hold.
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
        agent = read_one(self, agent_id)
        if agent is None:
            return None
        store[agent_id] = AgentManager._soul_text(
            self, agent.name,
            fields.get("prompt", agent.prompt),
            fields.get("guardrails", agent.guardrails),
            fields.get("scope", agent.scope),
        )
        return read_one(self, agent_id)

    monkeypatch.setattr(AgentManager, "get_by_id", read_one)
    monkeypatch.setattr(AgentManager, "get_all", read_all)
    monkeypatch.setattr(AgentManager, "update", write_one)
    return store


def _block_of(soul_text: str) -> str:
    """The published block, markers included -- and proof there is
    exactly one of each marker while we are here."""
    assert soul_text.count(_ACTION_CATALOGUE_BEGIN) == 1
    assert soul_text.count(_ACTION_CATALOGUE_END) == 1
    start = soul_text.index(_ACTION_CATALOGUE_BEGIN)
    end = soul_text.index(_ACTION_CATALOGUE_END) + len(_ACTION_CATALOGUE_END)
    return soul_text[start:end]


def _outside_the_block(soul_text: str) -> str:
    start = soul_text.index(_ACTION_CATALOGUE_BEGIN)
    end = soul_text.index(_ACTION_CATALOGUE_END) + len(_ACTION_CATALOGUE_END)
    return soul_text[:start] + soul_text[end:]


def _three_actions(manager: ActionManager) -> None:
    """Two of them callable by `customer-expert` -- one by explicit id,
    one by the `["*"]` wildcard -- and one callable only by somebody
    else."""
    manager.create(
        "refresh-the-index",
        description="Rebuild the vault index now",
        inputs=[
            {"name": "scope", "type": "string", "required": True, "description": "which folder"},
            {"name": "force", "type": "boolean", "required": False},
        ],
        allowed_callers=["customer-expert"],
        implementation={"http": {"method": "POST", "path": "/vault-index/refresh"}},
    )
    manager.create(
        "report-unmet-request",
        description="Record a request no action covers",
        allowed_callers=["*"],
        implementation={"http": {"method": "POST", "path": "/vault-index/refresh"}},
    )
    manager.create(
        "archive-the-mailbox",
        description="Archive everything",
        allowed_callers=["note-taker"],
        implementation={"http": {"method": "POST", "path": "/vault-index/refresh"}},
    )


def _publish() -> list[str]:
    return AgentManager().publish_action_catalogue()


def test_an_agents_block_lists_exactly_what_that_agent_may_call(stored_actions, souls) -> None:
    """[REQ-SB-95-US-03-AC-01] Three Actions, two of which permit
    `customer-expert` -- one by explicit id, one by `["*"]`. Its block
    names those two with their descriptions, inputs and required flags
    and the one way to call them, and names nothing else."""
    _three_actions(ActionManager())
    _publish()

    block = _block_of(souls["customer-expert"])

    assert "`refresh-the-index`" in block
    assert "Rebuild the vault index now" in block
    assert "`report-unmet-request`" in block
    assert "Record a request no action covers" in block
    assert "archive-the-mailbox" not in block, "an Action this agent may not call is not published to it"
    assert "Archive everything" not in block

    assert "`scope` (string, required) -- which folder" in block
    assert "`force` (boolean, optional)" in block

    assert "POST /actions/<action_id>/call" in block, "the one way to call them"
    assert "caller_agent_id" in block

    assert "do not hand-edit" in block


def test_an_agent_permitted_to_call_nothing_carries_no_block_at_all(stored_actions, souls) -> None:
    """[REQ-SB-95-US-03-AC-01] No empty shell: neither marker appears.
    A heading announcing a catalogue with nothing under it would read
    to an agent as "this app can do nothing", which is a different
    claim from "you may call none of it"."""
    ActionManager().create(
        "archive-the-mailbox",
        description="Archive everything",
        allowed_callers=["note-taker"],
        implementation={"http": {"method": "POST", "path": "/vault-index/refresh"}},
    )
    _publish()

    assert _ACTION_CATALOGUE_BEGIN not in souls["customer-expert"]
    assert _ACTION_CATALOGUE_END not in souls["customer-expert"]
    assert souls["customer-expert"] == HAND_AUTHORED_SOUL
    assert _ACTION_CATALOGUE_BEGIN in souls["note-taker"], "the agent that may call it still gets one"


def test_republishing_replaces_its_own_block_and_leaves_everything_else_untouched(
    stored_actions, souls,
) -> None:
    """[REQ-SB-95-US-03-AC-08] Add, edit and delete an Action, each
    followed by a republication. Exactly one marker pair survives, the
    block tracks every change, and the hand-authored prompt, guardrails
    and scope text around it is byte-identical throughout."""
    manager = ActionManager()
    _three_actions(manager)
    _publish()
    outside_before = _outside_the_block(souls["customer-expert"])

    manager.create(
        "open-the-thread",
        description="Open an email thread",
        allowed_callers=["*"],
        implementation={"http": {"method": "POST", "path": "/vault-index/refresh"}},
    )
    _publish()
    block = _block_of(souls["customer-expert"])
    assert "`open-the-thread`" in block

    manager.update("open-the-thread", description="Open the email thread in Outlook")
    _publish()
    block = _block_of(souls["customer-expert"])
    assert "Open the email thread in Outlook" in block
    assert "Open an email thread\n" not in block

    # A pass with nothing to change writes nothing at all, which is what
    # makes republication safe to run on every catalogue edit.
    assert _publish() == []

    manager.delete("open-the-thread")
    _publish()
    block = _block_of(souls["customer-expert"])
    assert "open-the-thread" not in block

    assert _outside_the_block(souls["customer-expert"]) == outside_before
    assert "## Scope boundary\n\nOnly ADNOC." in souls["customer-expert"]
    assert "Never invent a number." in souls["customer-expert"]
    assert "Folders: Customers" in souls["customer-expert"]


def test_a_deleted_action_disappears_from_every_agent_that_listed_it(stored_actions, souls) -> None:
    """[REQ-SB-95-US-03-AC-08] A wildcard Action is in both agents'
    blocks; deleting it has to leave neither of them still offering
    it."""
    manager = ActionManager()
    _three_actions(manager)
    _publish()
    assert "`report-unmet-request`" in souls["customer-expert"]
    assert "`report-unmet-request`" in souls["note-taker"]

    manager.delete("report-unmet-request")
    _publish()

    assert "report-unmet-request" not in souls["customer-expert"]
    assert "report-unmet-request" not in souls["note-taker"]
    # `note-taker` is left with its own one Action, not an empty shell
    # and not a removed block.
    assert "`archive-the-mailbox`" in _block_of(souls["note-taker"])


def test_one_agent_failing_to_publish_does_not_stop_the_rest(
    stored_actions, souls, monkeypatch,
) -> None:
    """[REQ-SB-95-US-03-AC-08] A profile Hermes refuses to write leaves
    that one agent's block stale -- which ADR-033 accepts, since the
    gate reads the live catalogue and never this text -- but the other
    agents still have to be told what the app can do."""
    _three_actions(ActionManager())
    write_one = AgentManager.update

    def refuse_customer_expert(self: AgentManager, agent_id: str, **fields: object):
        if agent_id == "customer-expert":
            raise RuntimeError("hermes refused this profile")
        return write_one(self, agent_id, **fields)

    monkeypatch.setattr(AgentManager, "update", refuse_customer_expert)

    assert _publish() == ["note-taker"]
    assert souls["customer-expert"] == HAND_AUTHORED_SOUL
    assert "`archive-the-mailbox`" in _block_of(souls["note-taker"])
