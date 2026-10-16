"""Save-time implementation resolution, and the read-side broken-entry
status (REQ-SB-95-US-02-T02, ADR-032).

ADR-032's whole reason for resolving at SAVE is that "a broken action
cannot sit in the catalogue waiting to fail in front of the operator".
Two halves follow from that and are pinned here:

- A save whose one implementation does not resolve is REFUSED, naming
  what did not resolve, with nothing written. Catalogued-but-undeployed
  is the interesting skill case -- the Skill exists in this repo and in
  no Hermes profile, so a check that only asked "is it catalogued?"
  would pass and the runner would still find nothing.
- An Action that resolved when saved can break afterwards, because the
  thing it points at is owned by something else. That is discovered by
  READING the catalogue, never by calling the Action.

The three resolution sources are monkeypatched -- the install's real
deployed Skills, its real route table and its real front-end keys are
instance state, and a test that asserted against them would pass or
fail by what happens to be deployed on the machine running it. One test
deliberately does the opposite and reads the LIVE route table, because
"reads the live app's routes, not a hand-maintained list" is itself the
thing under test.

Writes are monkeypatched exactly as tests/test_action_artifact_kind.py
does, so "nothing was written" is an assertion and not an absence of
evidence.
"""
import pytest

from app.business.core.actions.action_manager import (
    ActionImplementationUnresolvedError,
    ActionManager,
    app_route_table,
)

A_DEPLOYED_SKILL = "email-thread-capture"
A_REAL_ROUTE = ("POST", "/vault-index/refresh")
A_REAL_FEATURE_KEY = "/settings/artifacts"


@pytest.fixture
def resolvable(monkeypatch):
    """The three live sources, replaced by ones this test controls.
    Returns the mutable deployed-skill set so a test can undeploy
    something mid-test, which is exactly the AC-07 event."""
    deployed = {A_DEPLOYED_SKILL}
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.deployed_skill_ids",
        lambda: set(deployed),
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.app_route_table",
        lambda: {A_REAL_ROUTE},
    )
    monkeypatch.setattr(
        "app.business.core.actions.action_manager.UI_FEATURE_KEYS",
        (A_REAL_FEATURE_KEY,),
    )
    return deployed


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


def test_a_skill_that_is_catalogued_but_not_deployed_is_refused(resolvable, stored_actions) -> None:
    """[REQ-SB-95-US-02-AC-02] Deployed, not merely catalogued. A Skill
    sitting in this repo and in no Hermes profile is precisely the
    action that would fail in front of the operator."""
    with pytest.raises(ActionImplementationUnresolvedError) as refusal:
        ActionManager().create(
            "search-the-vault",
            description="Search the vault",
            implementation={"skill": {"skill_id": "vault-search"}},
        )

    assert "vault-search" in str(refusal.value)
    assert "not deployed" in str(refusal.value)
    assert stored_actions == {}


def test_an_http_route_the_app_does_not_expose_is_refused(resolvable, stored_actions) -> None:
    """[REQ-SB-95-US-02-AC-02] The refusal names the path, so the
    operator can see it is a typo (or a route that was removed) without
    opening the route table."""
    with pytest.raises(ActionImplementationUnresolvedError) as refusal:
        ActionManager().create(
            "refresh-the-index",
            implementation={"http": {"method": "POST", "path": "/vault-index/refersh"}},
        )

    assert "/vault-index/refersh" in str(refusal.value)
    assert stored_actions == {}


def test_the_same_path_under_the_wrong_method_is_refused(resolvable, stored_actions) -> None:
    """[REQ-SB-95-US-02-AC-02] A route is a method AND a path. Matching
    on the path alone would resolve a GET onto a POST-only endpoint --
    an action that 405s the first time anything runs it."""
    with pytest.raises(ActionImplementationUnresolvedError) as refusal:
        ActionManager().create(
            "refresh-the-index",
            implementation={"http": {"method": "GET", "path": "/vault-index/refresh"}},
        )

    assert "GET" in str(refusal.value)
    assert stored_actions == {}


def test_a_ui_feature_key_that_is_not_registered_is_refused(resolvable, stored_actions) -> None:
    """[REQ-SB-95-US-02-AC-02] `ui` is the kind the app points at and
    never performs, so an unregistered key means pointing the operator
    at a screen that does not exist."""
    with pytest.raises(ActionImplementationUnresolvedError) as refusal:
        ActionManager().create(
            "open-the-artifacts-page",
            implementation={"ui": {"feature_key": "/settings/artefacts"}},
        )

    assert "/settings/artefacts" in str(refusal.value)
    assert "not registered" in str(refusal.value)
    assert stored_actions == {}


def test_resaving_the_refused_action_with_a_resolvable_implementation_succeeds(
    resolvable, stored_actions,
) -> None:
    """[REQ-SB-95-US-02-AC-02] The refusal is about the implementation,
    not about the Action: the same id saves normally once it names
    something that resolves, and reopens as what was saved."""
    manager = ActionManager()
    with pytest.raises(ActionImplementationUnresolvedError):
        manager.create(
            "refresh-the-index",
            implementation={"http": {"method": "POST", "path": "/vault-index/refersh"}},
        )

    created = manager.create(
        "refresh-the-index",
        description="Rebuild the vault index now",
        implementation={"http": {"method": "POST", "path": "/vault-index/refresh"}},
    )

    assert created.implementation.kind == "http"
    reopened = ActionManager().get_by_id("refresh-the-index")
    assert reopened.description == "Rebuild the vault index now"
    assert (reopened.implementation.method, reopened.implementation.path) == A_REAL_ROUTE
    assert list(stored_actions) == ["refresh-the-index"]


def test_an_update_onto_an_unresolvable_implementation_changes_nothing(
    resolvable, stored_actions,
) -> None:
    """[REQ-SB-95-US-02-AC-02] Editing is the other half of "creating or
    editing": a saved, resolving Action must not be downgraded into a
    broken one, and the stored definition must be untouched after the
    refusal."""
    manager = ActionManager()
    manager.create(
        "capture-the-thread",
        description="Capture an email thread",
        implementation={"skill": {"skill_id": A_DEPLOYED_SKILL}},
    )
    before = dict(stored_actions["capture-the-thread"])

    with pytest.raises(ActionImplementationUnresolvedError):
        manager.update(
            "capture-the-thread",
            description="edited",
            implementation={"ui": {"feature_key": "/nowhere"}},
        )

    assert stored_actions["capture-the-thread"] == before


def test_the_http_route_table_is_read_off_the_live_app(stored_actions) -> None:
    """[REQ-SB-95-US-02-AC-02] Deliberately NOT monkeypatched. The
    constraint is that resolution reads the running app's own routes;
    the installed FastAPI keeps included routers lazily, so a flat read
    of `app.routes` sees only the four /docs paths and would refuse
    every real route there is."""
    table = app_route_table()

    assert A_REAL_ROUTE in table
    assert ("POST", "/vault-index/refersh") not in table

    action = ActionManager().create(
        "refresh-the-index",
        implementation={"http": {"method": "POST", "path": "/vault-index/refresh"}},
    )
    assert action.implementation.path == "/vault-index/refresh"


def test_an_action_that_breaks_after_it_was_saved_is_reported_on_read(
    resolvable, stored_actions,
) -> None:
    """[REQ-SB-95-US-02-AC-07] The Skill resolved at save and is
    undeployed afterwards. Reading the catalogue has to surface that,
    naming the skill, while every other Action still reports `resolves`
    -- and nothing calls anything to find out."""
    manager = ActionManager()
    manager.create(
        "capture-the-thread",
        description="Capture an email thread",
        implementation={"skill": {"skill_id": A_DEPLOYED_SKILL}},
    )
    manager.create(
        "refresh-the-index",
        implementation={"http": {"method": "POST", "path": "/vault-index/refresh"}},
    )
    manager.create(
        "open-the-artifacts-page",
        implementation={"ui": {"feature_key": A_REAL_FEATURE_KEY}},
    )

    assert {entry["action_id"]: entry["status"] for entry in manager.resolution_report()} == {
        "capture-the-thread": "resolves",
        "refresh-the-index": "resolves",
        "open-the-artifacts-page": "resolves",
    }

    resolvable.remove(A_DEPLOYED_SKILL)

    report = {entry["action_id"]: entry for entry in ActionManager().resolution_report()}
    assert report["capture-the-thread"]["status"] == "broken"
    assert report["capture-the-thread"]["implementation_kind"] == "skill"
    assert A_DEPLOYED_SKILL in report["capture-the-thread"]["reason"]
    assert "not deployed" in report["capture-the-thread"]["reason"]

    assert report["refresh-the-index"]["status"] == "resolves"
    assert report["refresh-the-index"]["reason"] is None
    assert report["open-the-artifacts-page"]["status"] == "resolves"

    # Nothing had to call the Action to discover it: this story ships no
    # call surface at all (that is US-03), so the status can only have
    # come from re-reading the sources.
    assert not hasattr(ActionManager, "call")

    # And the stored definition is untouched -- the status is computed,
    # never written into Action.json.
    assert "status" not in stored_actions["capture-the-thread"]
    assert "resolution" not in stored_actions["capture-the-thread"]


def test_the_read_side_status_is_recomputed_every_time(resolvable, stored_actions) -> None:
    """[REQ-SB-95-US-02-AC-07] Computed on read, never cached. The same
    manager instance that just reported `broken` must report `resolves`
    the moment the Skill is deployed again -- a cached answer is the
    silent staleness ADR-032 exists to stop."""
    manager = ActionManager()
    manager.create(
        "capture-the-thread",
        implementation={"skill": {"skill_id": A_DEPLOYED_SKILL}},
    )

    resolvable.remove(A_DEPLOYED_SKILL)
    assert manager.resolution_report()[0]["status"] == "broken"

    resolvable.add(A_DEPLOYED_SKILL)
    assert manager.resolution_report()[0]["status"] == "resolves"
    assert manager.resolution_report()[0]["reason"] is None
