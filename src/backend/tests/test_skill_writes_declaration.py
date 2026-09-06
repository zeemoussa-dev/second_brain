"""A Skill declares which Template sections its Actions write.

This replaces `allowed_callers` inside Template.json, which was a reverse
edge: it made a vault STRUCTURE definition depend on the capability layer,
contradicting the dependency resolver's own "a Template has no further
real dependencies of its own". An Entity Template is a vault structure and
does not know which Skills exist.

The map that replaces it is DERIVED from what deployed Skills declare, so
it cannot name an Action that is not deployed, and cannot rot against a
renamed script the way the hand-maintained list silently did.
"""
import pytest

from app.business.core.skills.skill_manager import SkillManager
from app.business.core.templates.template_manager import TemplateManager


def test_the_derived_map_matches_what_the_templates_used_to_declare() -> None:
    """The migration must be lossless: exactly the control that existed
    before, expressed on the side that owns the Actions."""
    assert SkillManager().build_section_access_map() == {
        "thread": {
            "Summary": ["apply_thread_review"],
            "Actions": ["apply_thread_review"],
            "Related": ["link_opportunity", "link_person_to_thread"],
            "Files": ["apply_file_review", "capture_attachments", "capture_file_link"],
        }
    }


def test_the_templates_no_longer_name_any_skill() -> None:
    """The point of the whole change -- structure must not reference
    capability, or a Master Template cannot be shipped or versioned
    independently of the Skills."""
    for template in TemplateManager().get_all():
        for section in template.sections:
            assert section.allowed_callers == [], (
                f"{template.id}.{section.name} still names Skill Actions"
            )


def test_every_shipped_skill_declaration_resolves_against_a_real_template() -> None:
    """The precondition that makes deployment refusable: a declared section
    must exist and be machine_write."""
    manager = SkillManager()
    for skill in manager.get_all():
        assert manager.validate_declared_writes(skill.id) == [], skill.id


def test_an_undeployed_skill_grants_nothing(monkeypatch) -> None:
    """The map is a projection of what is DEPLOYED. A Skill sitting in the
    catalog must not hand its Actions write access it never received."""
    manager = SkillManager()
    real = manager.get_all()
    monkeypatch.setattr(
        SkillManager, "get_all",
        lambda self: [type(s)(**{**s.__dict__, "deployed_to": []}) for s in real],
    )

    assert manager.build_section_access_map() == {}


def test_a_declaration_naming_a_missing_template_is_refused(monkeypatch) -> None:
    manager = SkillManager()
    monkeypatch.setattr(
        SkillManager, "_declared_writes",
        lambda self, skill_id: [{"action": "a", "template": "no-such", "sections": ["X"]}],
    )

    [problem] = manager.validate_declared_writes("anything")

    assert "no Master Template" in problem


def test_a_declaration_naming_a_human_only_section_is_refused(monkeypatch) -> None:
    """The check that stops a Skill claiming write access to the operator's
    own writing."""
    manager = SkillManager()
    monkeypatch.setattr(
        SkillManager, "_declared_writes",
        lambda self, skill_id: [
            {"action": "a", "template": "thread", "sections": ["Personal Notes"]}
        ],
    )

    [problem] = manager.validate_declared_writes("anything")

    assert "human_only" in problem and "not machine_write" in problem
