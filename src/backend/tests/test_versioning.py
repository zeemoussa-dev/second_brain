"""Three versions, deliberately distinct.

  Template.schema_version  how to PARSE the file (v1 flat vs v2 two-layer)
  Template.version         what the CONTENT promises (which sections exist)
  Skill version            what is shipped, so a deployment can be told stale

A Skill depends on the second, never the first. Conflating them is what the
v1/v2 defect cost a debugging session over -- a file that cannot say what it
is gets read by the wrong parser, silently.
"""
import pytest

from app.business.core.skills.skill_manager import SkillManager
from app.business.core.templates.template_manager import TemplateManager


def test_schema_version_and_content_version_are_separate() -> None:
    for template in TemplateManager().get_all():
        assert template.schema_version == 2, f"{template.id} parses as v2"
        assert template.version >= 1, f"{template.id} declares a content version"


def test_every_declaration_names_the_template_version_it_was_written_against() -> None:
    manager = SkillManager()
    declaring = [s for s in manager.get_all() if manager._declared_writes(s.id)]
    assert declaring, "no Skill declares writes -- the fixture is wrong, not the code"
    for skill in declaring:
        for entry in manager._declared_writes(skill.id):
            assert isinstance(entry["requires"], int), f"{skill.id}/{entry['action']}"


def test_a_version_mismatch_is_refused_at_deploy(monkeypatch) -> None:
    """Exact match, not >=. A bump means a section was removed or renamed,
    so an older Skill is wrong rather than merely behind."""
    manager = SkillManager()
    monkeypatch.setattr(
        SkillManager, "_declared_writes",
        lambda self, skill_id: [
            {"action": "a", "template": "thread", "requires": 99, "sections": ["Summary"]}
        ],
    )

    [problem] = manager.validate_declared_writes("anything")

    assert "needs 'thread' v99" in problem and "install has v1" in problem


def test_a_declaration_without_requires_is_still_allowed(monkeypatch) -> None:
    """`requires` is optional -- a Skill that does not pin a version is
    checked structurally only, which is the pre-existing behaviour."""
    manager = SkillManager()
    monkeypatch.setattr(
        SkillManager, "_declared_writes",
        lambda self, skill_id: [
            {"action": "a", "template": "thread", "requires": None, "sections": ["Summary"]}
        ],
    )

    assert manager.validate_declared_writes("anything") == []


def test_drift_report_uses_the_documented_statuses() -> None:
    """The report is only useful if the statuses mean what they say.
    `modified` is the sharp one: same version, different content -- the
    version CLAIMS current and is not."""
    report = SkillManager().check_deployment_drift()
    assert report, "no deployments to check -- the fixture is wrong, not the code"
    assert all(
        set(entry) == {"skill_id", "profile_id", "status", "catalog_version", "deployed_version"}
        for entry in report
    )
    assert all(
        entry["status"] in {"current", "stale", "modified", "missing"} for entry in report
    )
