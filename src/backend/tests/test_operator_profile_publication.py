"""The operator's facts published into every agent's context --
`REQ-SB-95-US-01-T02` (`ADR-036`, `ADR-038`).

The block is the fourth auto-generated, marker-delimited section of an
agent's own SOUL.md, beside the specialists, index-guidance, Action and
Workflow ones `AgentManager` already owns. Three things make it
different from all of them, and every one of those differences is a
locked AC here:

- **It fans out.** The Profile is a singleton, so one save publishes the
  SAME characters into every agent rather than a per-agent selection.
- **It is never removed when empty.** An install with no Profile gets a
  block saying exactly that and naming where to configure it -- which is
  what makes `AC-05` answerable at all.
- **One pass, one Registry reload, zero `update()` calls** (`AC-07`).
  `update()` begins and ends with a full `asyncio.run(registry_loader.
  boot())`; 41 agents is 41 boots for one Profile save.

Everything here runs against a **real scratch Hermes home** with real
profiles on disk, through the real `HermesProfiles.read_soul`/
`write_soul`, rather than a dict standing in for Hermes: `BUG-092` and
`BUG-093` were both in this write path -- a dropped final newline and a
re-emitted `## Scope` that destroyed a human's prose -- and reasoning
about `_rewrite_soul()` is not proof that they stay closed.

Nothing here can reach the operator's own install or their own data.
`tests/conftest.py` sandboxes Hermes for every test in the suite; this
file then points `hermes_home_path` AND `second_brain_data_path` at
`tmp_path` before anything runs, and restores the Registry's module-level
globals. Every value below is fictitious.
"""
from __future__ import annotations

import copy
import threading
from pathlib import Path

import pytest

import app.business.hermes.client as hermes_client_module
from app.business import setup_wizard
from app.business.core.actions import action_manager as action_manager_module
from app.business.core.actions.action_manager import ActionManager
from app.business.core.agents import agent_manager as agent_manager_module
from app.business.core.agents.agent_manager import (
    _ACTION_CATALOGUE_BEGIN,
    _OPERATOR_PROFILE_BEGIN,
    _OPERATOR_PROFILE_END,
    AgentManager,
    _split_soul_sections,
)
from app.business.core.operator import operator_profile_manager as operator_manager_module
from app.business.core.operator.operator_profile_manager import OperatorProfileManager
from app.config import settings
from app.data_access import operator_profile as operator_profile_data
from app.data_access.registry import loader as registry_loader
from app.data_access.registry import writer as registry_writer
from app.hermes.cli import HermesCLI
from app.hermes.profiles import HermesProfiles

OWN_ADDRESS = "operator@example.test"
A_MOVED_OWN_ADDRESS = "robin.moved@example.test"

A_PROFILE = {
    "name": "Robin Fictional",
    "other_email_addresses": ["robin.alt@example.test", "robin@example.invalid"],
    "timezone": "Etc/UTC",
    "team": [
        {"email": "blue@example.test", "role": "Engineer"},
        {"email": "green@example.test", "role": "Designer"},
        {"email": "amber@example.test", "role": "Analyst"},
    ],
}

# Prose this app cannot read, inside and outside the two sections it can,
# plus a final newline -- so "every other byte identical" has something
# to be wrong about (`BUG-092`/`BUG-093`).
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
THE_HAND_AUTHORED_AGENT = "blue-agent"
# The `default` profile IS the home directory itself and is always in the
# roster, so it needs a soul of its own or the pass is publishing into
# three profiles and skipping an unreadable fourth.
OTHER_SOULS = {
    "default": "You are the Primary.\n",
    "green-agent": "You are the Note Taker.",
    "amber-agent": "You are the Mail Reader.\n\n## Guardrails\n\nAsk first.\n",
}

A_REAL_ROUTE = ("POST", "/vault-index/refresh")
A_REAL_FEATURE_KEY = "/settings/actions"


@pytest.fixture(autouse=True)
def scratch_install(tmp_path, monkeypatch) -> dict[str, Path]:
    """A real Hermes home with four real profiles, and a data path that
    does not exist yet -- the fresh-install state.

    Returns each agent's real SOUL.md path, so a test asserts against
    bytes on disk rather than against something this file remembered.
    """
    home = tmp_path / "hermes-home"
    home.mkdir(parents=True)
    soul_paths: dict[str, Path] = {}

    def write_a_profile(agent_id: str, text: str) -> None:
        if agent_id == "default":
            soul_path = home / "SOUL.md"
        else:
            (home / "profiles" / agent_id).mkdir(parents=True)
            soul_path = home / "profiles" / agent_id / "SOUL.md"
        soul_path.write_text(text, encoding="utf-8", newline="\n")
        soul_paths[agent_id] = soul_path

    write_a_profile(THE_HAND_AUTHORED_AGENT, HAND_AUTHORED_SOUL)
    for agent_id, text in OTHER_SOULS.items():
        write_a_profile(agent_id, text)

    monkeypatch.setattr(settings, "hermes_home_path", home)
    monkeypatch.setattr(settings, "second_brain_data_path", tmp_path / "second-brain-data")
    monkeypatch.setattr(settings, "self_email", OWN_ADDRESS)
    monkeypatch.setattr(HermesCLI, "_hermes_exe", lambda self: None)
    monkeypatch.setattr(hermes_client_module, "_client", None)

    # The Registry's module-level cache, saved and put back: a pass
    # reloads it from whatever data path is configured, so without this a
    # test pointing that path at `tmp_path` would leave the whole
    # session's Registry holding a scratch directory -- an order-dependent
    # failure for whatever runs next, looking like a defect in that test.
    monkeypatch.setattr(registry_loader, "_registry", None)
    monkeypatch.setattr(
        registry_loader, "_last_seen_fingerprint", registry_loader._last_seen_fingerprint,
    )
    monkeypatch.setattr(registry_loader, "_status", copy.deepcopy(registry_loader._status))
    # No HTTP from a Registry boot: it probes Hermes' base URL, which is
    # a real request to whatever is listening on this machine.
    monkeypatch.setattr(registry_loader, "_hermes_reachable", lambda: False)
    return soul_paths


@pytest.fixture
def publication_is_explicit_only(monkeypatch) -> None:
    """The automatic trigger, off -- for the tests that drive the pass
    themselves and must not race one they did not start."""
    monkeypatch.setattr(
        operator_manager_module, "publish_operator_profile_in_background", lambda: None,
    )


@pytest.fixture
def registry_boots(monkeypatch) -> list[str]:
    """Every `registry_loader.boot()` awaited during a test, counted --
    and not actually performed, so no test here pays for a Registry boot
    it is only counting."""
    boots: list[str] = []

    async def counted(mode: str = "cold_boot") -> None:
        boots.append(mode)

    monkeypatch.setattr(registry_loader, "boot", counted)
    return boots


@pytest.fixture
def soul_writes(monkeypatch) -> list[str]:
    """Every real SOUL.md write, in order, by agent id -- the real write
    still happens."""
    written: list[str] = []
    really_write = HermesProfiles.write_soul

    def record(self: HermesProfiles, agent_id: str, content: str) -> None:
        written.append(agent_id)
        really_write(self, agent_id, content)

    monkeypatch.setattr(HermesProfiles, "write_soul", record)
    return written


def publish() -> list[str]:
    return AgentManager().publish_operator_profile()


def soul_of(soul_paths: dict[str, Path], agent_id: str) -> str:
    return soul_paths[agent_id].read_text(encoding="utf-8")


def block_of(soul_text: str) -> str:
    """The published block, markers included -- and proof there is
    exactly one of each marker while we are here."""
    assert soul_text.count(_OPERATOR_PROFILE_BEGIN) == 1
    assert soul_text.count(_OPERATOR_PROFILE_END) == 1
    start = soul_text.index(_OPERATOR_PROFILE_BEGIN)
    end = soul_text.index(_OPERATOR_PROFILE_END) + len(_OPERATOR_PROFILE_END)
    return soul_text[start:end]


def outside_the_block(soul_text: str) -> str:
    start = soul_text.index(_OPERATOR_PROFILE_BEGIN)
    end = soul_text.index(_OPERATOR_PROFILE_END) + len(_OPERATOR_PROFILE_END)
    return soul_text[:start] + soul_text[end:]


# ---------------------------------------------------------------- part 1
# The block itself: what it says, and that every agent gets the same.


def test_the_operator_and_the_whole_team_reach_every_agent_identically(
    scratch_install, publication_is_explicit_only,
) -> None:
    """[REQ-SB-95-US-01-AC-02] A Profile with a name and three colleagues
    with roles, published across four agents: one block each, naming the
    operator and all three colleagues with their roles, and the four
    block texts byte-identical to one another.

    Byte-identical is the assertion that matters: a singleton FANS OUT.
    The Action and Workflow blocks are filtered per agent by what that
    agent may call; an operator is not, and recomputing per agent would
    be the first step towards two agents disagreeing about who they work
    for."""
    OperatorProfileManager().save(A_PROFILE)

    assert sorted(publish()) == sorted(scratch_install)

    blocks = {agent_id: block_of(soul_of(scratch_install, agent_id)) for agent_id in scratch_install}
    assert len(set(blocks.values())) == 1, "identical text in every agent, not a per-agent render"

    block = blocks[THE_HAND_AUTHORED_AGENT]
    assert "Robin Fictional" in block
    for member in A_PROFILE["team"]:
        assert f"`{member['email']}` -- {member['role']}" in block
    for address in A_PROFILE["other_email_addresses"]:
        assert address in block
    assert A_PROFILE["timezone"] in block
    assert "do not hand-edit" in block


def test_the_heading_is_who_you_work_for_and_the_soul_still_splits_the_same(
    scratch_install, publication_is_explicit_only,
) -> None:
    """[REQ-SB-95-US-01-AC-02] The heading is `## Who you work for`, and
    the block's presence changes nothing about how the file reads back.

    `_split_soul_sections()` matches the exact headings `## Guardrails`
    and `## Scope` ANYWHERE in the text, so either of those inside this
    block would cut its body out into the agent's guardrails or scope
    field -- a real 2026-08-28 defect, recorded in that function's own
    docstring."""
    before = soul_of(scratch_install, THE_HAND_AUTHORED_AGENT)
    guardrails_before, scope_before = _split_soul_sections(before)[1:]

    OperatorProfileManager().save(A_PROFILE)
    publish()

    after = soul_of(scratch_install, THE_HAND_AUTHORED_AGENT)
    block = block_of(after)
    assert "\n## Who you work for\n" in block
    assert "## Guardrails" not in block
    assert "## Scope" not in block

    core_after, guardrails_after, scope_after = _split_soul_sections(after)
    assert guardrails_after == guardrails_before == "Never invent a number."
    assert scope_after == scope_before == {"folders": ["Customers"], "tags": ["adnoc"]}
    assert "Robin Fictional" in core_after, (
        "the block round-trips as part of the prompt, which is where a marker block belongs -- "
        "it is not absorbed into guardrails or scope"
    )


def test_republishing_a_changed_profile_replaces_its_own_block_and_nothing_else(
    scratch_install, publication_is_explicit_only,
) -> None:
    """[REQ-SB-95-US-01-AC-02] Publish, change the Profile, publish
    again: exactly one marker pair survives, the block tracks the change,
    and every character outside the markers is byte-identical to
    before."""
    manager = OperatorProfileManager()
    manager.save(A_PROFILE)
    publish()
    first = soul_of(scratch_install, THE_HAND_AUTHORED_AGENT)
    outside_before = outside_the_block(first)

    manager.save({
        **A_PROFILE,
        "name": "Robin Renamed",
        "team": [{"email": "violet@example.test", "role": "Chief of Staff"}],
    })
    assert sorted(publish()) == sorted(scratch_install)

    second = soul_of(scratch_install, THE_HAND_AUTHORED_AGENT)
    block = block_of(second)
    assert "Robin Renamed" in block
    assert "`violet@example.test` -- Chief of Staff" in block
    assert "Robin Fictional" not in second, "the prior block is replaced, not left beside the new one"
    assert "blue@example.test" not in second, "a colleague the operator removed is gone everywhere"
    assert outside_the_block(second) == outside_before
    assert second.replace(block, "") == first.replace(block_of(first), "")


def test_the_block_says_where_the_own_address_came_from_and_tracks_the_setting(
    scratch_install, publication_is_explicit_only, monkeypatch,
) -> None:
    """[REQ-SB-95-US-01-AC-04] The own address is published, it is
    labelled with the setting it was read from, and changing that setting
    changes the next publication -- with nothing written back to the
    setting, to a `.env` or to `Profile.json`.

    The label is the deliberate part. The address is not in the record
    the block otherwise describes (`ADR-038`: `SELF_EMAIL` owns it), so
    publishing it unattributed would be true about the operator and false
    about where it is edited."""
    OperatorProfileManager().save(A_PROFILE)
    publish()

    block = block_of(soul_of(scratch_install, THE_HAND_AUTHORED_AGENT))
    assert OWN_ADDRESS in block
    assert "`SELF_EMAIL`" in block and "Settings > System" in block
    assert "not from the Operator Profile" in block

    monkeypatch.setattr(settings, "self_email", A_MOVED_OWN_ADDRESS)
    assert sorted(publish()) == sorted(scratch_install)

    moved = block_of(soul_of(scratch_install, THE_HAND_AUTHORED_AGENT))
    assert A_MOVED_OWN_ADDRESS in moved
    assert OWN_ADDRESS not in soul_of(scratch_install, THE_HAND_AUTHORED_AGENT)

    stored = operator_profile_data.profile_path().read_bytes()
    for address in (OWN_ADDRESS, A_MOVED_OWN_ADDRESS):
        assert address.encode("utf-8") not in stored, "the Profile stores no copy of the address"
    assert b"self_email" not in stored and b"own_address" not in stored
    assert settings.self_email == A_MOVED_OWN_ADDRESS, "publication reads the setting, never writes it"
    assert not list(Path(settings.second_brain_data_path).rglob(".env"))
    assert not list(Path(settings.hermes_home_path).rglob(".env"))


def test_an_unconfigured_profile_is_published_as_unconfigured(
    scratch_install, publication_is_explicit_only,
) -> None:
    """[REQ-SB-95-US-01-AC-05] No Profile has ever been saved. The block
    is still there in every agent -- it is not removed when there is
    nothing to say -- it states that no Operator Profile is configured
    and where to configure it, and it invents no team.

    The alternative, publishing nothing, is what leaves an agent to
    answer "who is my team?" from mail traffic and vault notes. The
    honest sentence has to be in the context, or there is nothing for the
    agent to say it from."""
    assert not operator_profile_data.profile_exists()

    assert sorted(publish()) == sorted(scratch_install)

    for agent_id in scratch_install:
        block = block_of(soul_of(scratch_install, agent_id))
        assert "No Operator Profile is configured on this install." in block
        assert "Settings > Operator Profile" in block, "it names where to configure it"
        assert "team" in block and "do not assemble one" in block
        # It invents nobody: no colleague, no name, no role, no "team of".
        for invented in ("Robin", "blue@example.test", "Engineer", "@example.invalid"):
            assert invented not in block
        # The own address comes from a different surface and IS
        # configured, so it is still published -- and still labelled.
        assert OWN_ADDRESS in block and "`SELF_EMAIL`" in block


def test_an_unconfigured_install_with_no_self_email_says_that_too(
    scratch_install, publication_is_explicit_only, monkeypatch,
) -> None:
    """[REQ-SB-95-US-01-AC-05] The emptiest install there is: no Profile
    and no `SELF_EMAIL`. Nothing is printed as a blank value -- the block
    says the address is not configured and where it would be set."""
    monkeypatch.setattr(settings, "self_email", "")

    publish()

    block = block_of(soul_of(scratch_install, "green-agent"))
    assert "Their own mail address: not configured" in block
    assert "`SELF_EMAIL`" in block and "Settings > System" in block


# ---------------------------------------------------------------- part 2
# One pass, one reload, no `update()` -- and no byte out of place.


def test_one_pass_reloads_the_registry_once_and_never_calls_update(
    scratch_install, publication_is_explicit_only, registry_boots, soul_writes, monkeypatch,
) -> None:
    """[REQ-SB-95-US-01-AC-07] Four agents, one pass: `registry_loader.
    boot()` is awaited exactly ONCE for the whole pass, `AgentManager.
    update()` is called ZERO times, and each agent's soul is written
    exactly once.

    This is the locked difference from the Action and Workflow passes
    beside it. `update()` begins and ends with `_reload_registry()`,
    which is `asyncio.run(registry_loader.boot())` -- a full Registry
    boot per agent, 41 of them on the reporting install, for one Profile
    save."""
    updates: list[str] = []
    monkeypatch.setattr(
        AgentManager, "update", lambda self, agent_id, **fields: updates.append(agent_id),
    )
    OperatorProfileManager().save(A_PROFILE)

    republished = publish()

    assert len(scratch_install) >= 3
    assert sorted(republished) == sorted(scratch_install)
    assert updates == [], "the pass must not go through update(), whose reload is per agent"
    assert len(registry_boots) == 1, registry_boots
    assert sorted(soul_writes) == sorted(scratch_install), "each agent's soul written exactly once"


def test_a_pass_with_nothing_to_change_writes_nothing_and_reloads_nothing(
    scratch_install, publication_is_explicit_only, registry_boots, soul_writes,
) -> None:
    """[REQ-SB-95-US-01-AC-07] Re-running the same publication is not a
    cheap no-op, it is NO op: no SOUL.md write and no Registry boot. A
    file's mtime is what a vault sync and a `git diff` react to, so a
    no-op republication has to look like one (`BUG-092`)."""
    OperatorProfileManager().save(A_PROFILE)
    publish()
    soul_writes.clear()
    registry_boots.clear()

    assert publish() == []

    assert soul_writes == []
    assert registry_boots == []


def test_publishing_into_a_real_profile_changes_only_the_block(
    scratch_install, publication_is_explicit_only, registry_boots,
) -> None:
    """[REQ-SB-95-US-01-AC-02] The invariant, proved against real bytes
    rather than argued from the code: adding this block to a real
    SOUL.md leaves every other byte identical -- the other sections,
    their prose, their order, the line endings and the final newline --
    and a second pass does not touch the file at all.

    `BUG-092` (a dropped final newline) and `BUG-093` (a re-emitted
    `## Scope` that destroyed a human's prose) were both in this exact
    write path."""
    soul_path = scratch_install[THE_HAND_AUTHORED_AGENT]
    before = soul_path.read_bytes()
    OperatorProfileManager().save(A_PROFILE)

    assert THE_HAND_AUTHORED_AGENT in publish()

    after = soul_path.read_bytes()
    assert after != before
    block = block_of(after.decode("utf-8")).encode("utf-8")
    assert after.replace(b"\n\n" + block, b"") == before
    assert b"\r\n" not in after, "a file that was LF stays LF"
    assert after.endswith(b"\n"), "the final newline survives"

    # And again: a pass with nothing to change must not touch the file.
    unchanged_at = soul_path.stat().st_mtime_ns
    assert publish() == []
    assert soul_path.read_bytes() == after
    assert soul_path.stat().st_mtime_ns == unchanged_at


# ---------------------------------------------------------------- part 3
# The trigger, and living beside the other two passes.


def test_saving_the_profile_is_the_only_action_anyone_takes(
    scratch_install, registry_boots,
) -> None:
    """[REQ-SB-95-US-01-AC-02] `OperatorProfileManager.save()` publishes:
    no route, script or future caller has a second step to remember, and
    no prompt is hand-edited to carry the same facts.

    Asserted through the real background thread, not a spy on the
    trigger: what matters is that the facts really arrive in the real
    files after a plain save."""
    OperatorProfileManager().save(A_PROFILE)

    assert operator_manager_module.join_background_publications(timeout=30.0)

    for agent_id in scratch_install:
        soul = soul_of(scratch_install, agent_id)
        block = block_of(soul)
        assert "Robin Fictional" in block
        assert soul.count("Robin Fictional") == 1, (
            "the operator's name appears only inside the derived block -- nothing hand-copied "
            "it into an agent's own prompt text"
        )
    hand_authored = soul_of(scratch_install, THE_HAND_AUTHORED_AGENT)
    assert hand_authored.replace("\n\n" + block_of(hand_authored), "") == HAND_AUTHORED_SOUL


def test_the_save_returns_before_the_publication_finishes(
    scratch_install, monkeypatch,
) -> None:
    """[REQ-SB-95-US-01-AC-02] The trigger does not make the operator
    wait: a roster-wide pass rewrites every agent's SOUL.md, and one
    `PUT /operator/profile` must not hold a screen open for it."""
    let_the_pass_finish = threading.Event()
    pass_started = threading.Event()

    def slow_pass(self: AgentManager) -> list[str]:
        pass_started.set()
        let_the_pass_finish.wait(timeout=10.0)
        return []

    monkeypatch.setattr(AgentManager, "publish_operator_profile", slow_pass)

    saved = OperatorProfileManager().save(A_PROFILE)
    assert pass_started.wait(timeout=10.0), "the save really started a pass"
    # `save()` has already returned, with the record it wrote, while the
    # pass it started is still blocked inside its own run.
    assert saved.name == A_PROFILE["name"]
    assert not let_the_pass_finish.is_set()

    let_the_pass_finish.set()
    assert operator_manager_module.join_background_publications(timeout=30.0)


def test_a_pass_that_outlives_its_install_publishes_into_nothing(
    scratch_install, monkeypatch, tmp_path,
) -> None:
    """[REQ-SB-95-US-01-AC-02] Both halves of "the install" are
    reconfigurable while the app runs (`REQ-SB-89`'s setup wizard) and
    nothing waits for a publication pass. A pass still in flight when
    either one changes must abandon itself rather than write one
    operator's name and team into another install's agents."""
    published: list[str] = []
    monkeypatch.setattr(
        operator_manager_module, "publish_operator_profile",
        lambda: published.append("published") or [],
    )
    here = (settings.hermes_home_path, settings.second_brain_data_path)

    assert operator_manager_module._publish_into((tmp_path / "elsewhere", here[1])) == []
    assert operator_manager_module._publish_into((here[0], tmp_path / "elsewhere")) == []
    assert published == [], "it refused both installs it was not started for"

    assert operator_manager_module._publish_into(here) == []
    assert published == ["published"], "and still publishes into the one it was"


def test_saving_the_profile_never_touches_the_self_email_setting(
    scratch_install, publication_is_explicit_only, monkeypatch,
) -> None:
    """[REQ-SB-95-US-01-AC-04] The regression clause, re-pinned on the
    publication path: a save, and the publication it triggers, still
    never call `setup_wizard.sync_settings_to_hermes(...)`."""
    synced: list[tuple] = []
    monkeypatch.setattr(
        setup_wizard, "sync_settings_to_hermes", lambda *args, **kwargs: synced.append(args),
    )

    OperatorProfileManager().save(A_PROFILE)
    publish()

    assert synced == []
    for module in (operator_manager_module, agent_manager_module):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "import setup_wizard" not in source and "setup_wizard import" not in source, (
            "a module-attribute spy cannot see a `from ... import` binding, so the absence of "
            "the import is pinned too"
        )


@pytest.fixture
def resolvable(monkeypatch) -> None:
    """The three live resolution sources an Action is validated against,
    replaced by ones this test controls."""
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.app_route_table", lambda: {A_REAL_ROUTE},
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.deployed_skill_ids", lambda: set(),
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.UI_FEATURE_KEYS", (A_REAL_FEATURE_KEY,),
    )


@pytest.fixture
def stored_actions(monkeypatch, resolvable) -> dict:
    """The whole Action store, in memory -- no test here reads or writes
    `<DATA_PATH>/data/Actions/`."""
    written: dict = {}

    def read_one(action_id: str):
        if action_id not in written:
            raise FileNotFoundError(action_id)
        return written[action_id]

    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.write_action_json",
        lambda action_id, data: written.update({action_id: data}),
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.read_action_json", read_one,
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.actions_data.list_action_ids",
        lambda: sorted(written),
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.ActionManager._plugin_contributed",
        lambda self: [],
    )
    monkeypatch.setattr(
        action_manager_module, "publish_action_catalogue_in_background", lambda: None,
    )
    return written


def test_an_action_pass_and_an_operator_pass_never_drop_each_others_block(
    scratch_install, publication_is_explicit_only, stored_actions, monkeypatch,
) -> None:
    """[REQ-SB-95-US-01-AC-02] Two passes, one SOUL.md. Each composes its
    new text from the agent it read when it started, so two in flight
    together is a plain lost update -- measured live on 2026-10-18
    between the Action and Workflow passes, which left a real profile
    carrying the Action block and no Workflow block at all
    (`REQ-SB-95-US-04-T06`).

    This pass is the third writer of the same file and takes the same
    `_publication_lock`. Here the Operator pass is held open inside its
    first write and an Action pass is started on top of it; both blocks
    have to survive. Confirmed to FAIL with the lock replaced by a
    `nullcontext`."""
    # A real Registry for these four profiles, written by the real
    # writer: the Action pass goes through `AgentManager.update()`, which
    # relocates an agent's Registry folder, and an agent no Section has
    # placed cannot be written at all.
    registry_writer.write_section_json("customers", {"id": "customers", "name": "Customers"})
    for agent_id in scratch_install:
        registry_writer.write_agent_files(
            registry_writer.agent_dir(agent_id, section_id="customers", is_background_agent=False),
            config={"id": agent_id, "name": agent_id, "type": "worker"},
            soul_text="placeholder, overwritten by the publication below",
        )

    ActionManager().create(
        "list-the-teams-actions",
        description="List the actions assigned to my team",
        allowed_callers=["*"],
        implementation={"ui": {"feature_key": A_REAL_FEATURE_KEY}},
    )
    OperatorProfileManager().save(A_PROFILE)

    really_write = AgentManager._write_published_soul
    first_write_began = threading.Event()
    let_the_first_write_finish = threading.Event()
    already_slowed: list[str] = []

    def slow_the_first_write(self: AgentManager, agent, new_prompt: str) -> bool:
        if not already_slowed:
            already_slowed.append(agent.id)
            first_write_began.set()
            let_the_first_write_finish.wait(timeout=10.0)
        return really_write(self, agent, new_prompt)

    monkeypatch.setattr(AgentManager, "_write_published_soul", slow_the_first_write)

    operator_pass = threading.Thread(target=AgentManager().publish_operator_profile)
    operator_pass.start()
    assert first_write_began.wait(timeout=10.0), "the Operator pass reached its first write"

    action_pass = threading.Thread(target=AgentManager().publish_action_catalogue)
    action_pass.start()
    let_the_first_write_finish.set()
    operator_pass.join(timeout=30.0)
    action_pass.join(timeout=30.0)
    assert not operator_pass.is_alive() and not action_pass.is_alive()

    for agent_id in scratch_install:
        soul = soul_of(scratch_install, agent_id)
        assert _OPERATOR_PROFILE_BEGIN in soul, agent_id
        assert _ACTION_CATALOGUE_BEGIN in soul, agent_id
