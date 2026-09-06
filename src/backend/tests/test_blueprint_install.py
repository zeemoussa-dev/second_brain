"""Installing a Blueprint: preconditions first, then create.

A Blueprint is a recipe, not a snapshot -- so its install path has to check
that what it references actually exists on THIS install before it creates
anything. Refusing up front is the point: the alternative is an Agent that
installs cleanly and then fails inside a cron worker at 03:00.
"""
import pytest

from app.business.core.agents.agent_manager import AgentManager
from app.business.core.blueprints.blueprint_manager import BlueprintManager
from app.business.core.sections.section_manager import SectionManager
from app.business.core.skills.skill_manager import SkillManager


def test_the_shipped_librarian_blueprint_parses() -> None:
    blueprint = BlueprintManager().get_by_id("librarian")

    assert blueprint is not None and blueprint.error is None
    assert [a.id for a in blueprint.agents] == ["files-manager", "notes-manager", "research-agent"]
    assert blueprint.skill_ids == [
        "capture-files", "capture-notes", "research-kb-writer", "summarize-and-tag-files",
    ]


def test_required_templates_are_derived_from_the_skills_not_authored() -> None:
    """The Blueprint names no Templates at all -- they follow from what its
    Skills declare. A second authored list would be a fact that can drift."""
    import json
    from app.data_access import blueprints as bd

    raw = json.dumps(bd.read_blueprint_json("librarian"))
    assert "template" not in raw.lower(), "a Blueprint must not author its Template list"
    assert "thread" in BlueprintManager().preflight("librarian")["templates"]


def test_preflight_reports_which_skills_it_could_not_check() -> None:
    """The Template closure is only as complete as the Skills' declarations,
    so preflight names the ones it could not check. Every librarian Skill now
    declares `writes:`, so that list is empty and the check is total -- the
    point is that the field EXISTS, because a partial check reading as a
    clean one is worse than no check."""
    result = BlueprintManager().preflight("librarian")

    assert result["unchecked_skills"] == []
    assert result["templates"] == ["file", "note", "research-kb-doc", "thread"]


def test_an_undeclared_skill_is_reported_as_unchecked(monkeypatch) -> None:
    monkeypatch.setattr(SkillManager, "_declared_writes", lambda self, sid: [])

    result = BlueprintManager().preflight("librarian")

    assert set(result["unchecked_skills"]) == set(result["skills"])
    assert result["ok"] is True, "unchecked is not the same as failing"


def test_a_missing_skill_blocks_the_install(monkeypatch) -> None:
    monkeypatch.setattr(SkillManager, "get_by_id", lambda self, sid: None)
    manager = BlueprintManager()

    result = manager.preflight("librarian")

    assert result["ok"] is False
    assert any("not in the catalog" in p for p in result["problems"])


def test_an_unsatisfied_template_precondition_blocks_the_install(monkeypatch) -> None:
    monkeypatch.setattr(
        SkillManager, "validate_declared_writes",
        lambda self, sid: ["template 'thread' has no section 'Ghost'"],
    )

    result = BlueprintManager().preflight("librarian")

    assert result["ok"] is False
    assert any("no section 'Ghost'" in p for p in result["problems"])


def test_install_creates_nothing_when_preflight_fails(monkeypatch) -> None:
    """The guarantee that matters: a refusal must not leave a half-built
    Section behind."""
    monkeypatch.setattr(SkillManager, "get_by_id", lambda self, sid: None)
    monkeypatch.setattr(
        SectionManager, "create", lambda self, name: pytest.fail("must not create a Section"),
    )
    monkeypatch.setattr(
        AgentManager, "create", lambda self, *a, **k: pytest.fail("must not create an Agent"),
    )

    result = BlueprintManager().install("librarian")

    assert result["installed"] is False
    assert result["problems"]


def test_an_unknown_blueprint_is_refused_not_guessed() -> None:
    result = BlueprintManager().preflight("no-such-blueprint")

    assert result["ok"] is False
    assert "no Blueprint" in result["problems"][0]


def test_a_malformed_blueprint_stays_visible_in_the_library(monkeypatch) -> None:
    """Listed carrying `error`, never silently dropped -- a broken Blueprint
    the operator cannot see is worse than one that fails loudly."""
    from app.data_access import blueprints as bd

    monkeypatch.setattr(bd, "list_blueprint_ids", lambda: ["broken"])
    monkeypatch.setattr(bd, "read_blueprint_json", lambda bid: {"agents": [{"no_id": True}]})

    [blueprint] = BlueprintManager().get_all()

    assert blueprint.id == "broken" and blueprint.error is not None
