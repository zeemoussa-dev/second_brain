"""An Agent declares which Skills it should have, and deployment acts on it.

Before 2026-09-06 `skill_ids` was doubly write-only: `AgentManager.create()`
wrote `[]` into Agent.json regardless of what was asked for, and `_to_agent`
then OVERWROTE the field on every read with a live mirror of whatever Hermes
happened to have. So the declaration could neither be expressed nor compared
against reality -- which is exactly what a Blueprint needs to do.
"""
import pytest

from app.business.core.agents.agent_manager import AgentManager
from app.business.core.skills.skill_manager import SkillManager, SkillPreconditionError


class _Skill:
    def __init__(self, skill_id, deployed_to):
        self.id = skill_id
        self.deployed_to = list(deployed_to)


def _profile_holding(*slugs):
    """Stub of what a profile ACTUALLY has -- ensure_skills reads reality,
    not the deployed_to record (BUG-056)."""
    skills = [type("K", (), {"slug": s})() for s in slugs]
    return lambda: type("C", (), {"skills": type("S", (), {
        "get_all": staticmethod(lambda pid: skills)
    })()})()


def test_declared_skills_are_deployed_to_the_agents_profile(monkeypatch) -> None:
    deployed: list[tuple[str, str]] = []
    monkeypatch.setattr(SkillManager, "get_by_id", lambda self, sid: _Skill(sid, []))
    monkeypatch.setattr(SkillManager, "deploy", lambda self, sid, pid: deployed.append((sid, pid)))
    monkeypatch.setattr("app.business.core.agents.agent_manager.get_client", _profile_holding())

    result = AgentManager().ensure_skills("files-manager", ["capture-files", "summarize-and-tag-files"])

    assert deployed == [("capture-files", "files-manager"), ("summarize-and-tag-files", "files-manager")]
    assert set(result.values()) == {"deployed"}


def test_a_skill_already_on_the_profile_is_not_redeployed(monkeypatch) -> None:
    monkeypatch.setattr(SkillManager, "get_by_id", lambda self, sid: _Skill(sid, ["files-manager"]))
    monkeypatch.setattr(
        SkillManager, "deploy",
        lambda self, sid, pid: pytest.fail("should not redeploy an already-deployed Skill"),
    )
    monkeypatch.setattr(
        "app.business.core.agents.agent_manager.get_client", _profile_holding("capture-files"))

    assert AgentManager().ensure_skills("files-manager", ["capture-files"]) == {"capture-files": "already"}


def test_one_refusal_does_not_abandon_the_rest(monkeypatch) -> None:
    """Refusals are returned, not raised. A Skill failing its Template
    precondition must not leave the Agent half-provisioned."""
    done: list[str] = []

    def deploy(self, sid, pid):
        if sid == "bad":
            raise SkillPreconditionError("'bad' cannot be deployed -- template 'thread' has no section 'Nope'")
        done.append(sid)

    monkeypatch.setattr(SkillManager, "get_by_id", lambda self, sid: _Skill(sid, []))
    monkeypatch.setattr(SkillManager, "deploy", deploy)
    monkeypatch.setattr("app.business.core.agents.agent_manager.get_client", _profile_holding())

    result = AgentManager().ensure_skills("a", ["bad", "capture-notes"])

    assert done == ["capture-notes"]
    assert result["capture-notes"] == "deployed"
    assert "no section" in result["bad"]


def test_an_unknown_skill_is_reported_not_silently_skipped(monkeypatch) -> None:
    monkeypatch.setattr(SkillManager, "get_by_id", lambda self, sid: None)

    assert AgentManager().ensure_skills("a", ["ghost"]) == {"ghost": "no such Skill in the catalog"}


def test_a_skill_missing_from_the_profile_is_deployed_even_if_the_record_says_otherwise(monkeypatch) -> None:
    """BUG-056: `deployed_to` is persisted metadata that deleting an Agent
    never cleared. After delete-and-reinstall it still named the Agent, so
    ensure_skills said "already", skipped the deploy, and the install
    reported success while the profile had NO skills on disk. Silent and
    total -- the worst shape a failure can take."""
    deployed: list[tuple[str, str]] = []
    monkeypatch.setattr(
        SkillManager, "get_by_id",
        lambda self, sid: _Skill(sid, ["notes-manager"]),   # the stale record
    )
    monkeypatch.setattr(SkillManager, "deploy", lambda self, sid, pid: deployed.append((sid, pid)))
    # Reality: the profile has nothing.
    monkeypatch.setattr(
        "app.business.core.agents.agent_manager.get_client",
        lambda: type("C", (), {"skills": type("S", (), {"get_all": staticmethod(lambda pid: [])})()})(),
    )

    result = AgentManager().ensure_skills("notes-manager", ["capture-notes"])

    assert deployed == [("capture-notes", "notes-manager")]
    assert result == {"capture-notes": "deployed"}


def test_a_skill_actually_on_the_profile_is_not_redeployed(monkeypatch) -> None:
    """The other direction: reality says present, so leave it alone."""
    monkeypatch.setattr(SkillManager, "get_by_id", lambda self, sid: _Skill(sid, []))
    monkeypatch.setattr(
        SkillManager, "deploy",
        lambda self, sid, pid: pytest.fail("must not redeploy a Skill already on the profile"),
    )
    monkeypatch.setattr(
        "app.business.core.agents.agent_manager.get_client",
        lambda: type("C", (), {"skills": type("S", (), {
            "get_all": staticmethod(lambda pid: [type("K", (), {"slug": "capture-notes"})()])
        })()})(),
    )

    assert AgentManager().ensure_skills("notes-manager", ["capture-notes"]) == {"capture-notes": "already"}
