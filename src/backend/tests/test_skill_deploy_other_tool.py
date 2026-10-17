"""BUG-091 -- deploying one Tool's Skill deleted another Tool's Skill of the same name.

A deployed Skill is found by its bare slug. When the copy in Hermes sat under a
different category than the catalog's, the deploy treated it as a stale grouping:
it created the new one and deleted the old. On 2026-10-09 that removed an
install's Outlook `email-thread-capture` to put the Graph one in its place, and
email capture stopped on that machine for eight days.
"""
from types import SimpleNamespace

import pytest

from app.business.core.skills import skill_manager as module
from app.business.core.skills.skill_manager import SkillManager, SkillPreconditionError


class _FakeSkills:
    def __init__(self, deployed_category):
        self.deployed = [SimpleNamespace(
            slug="email-thread-capture", category=deployed_category,
            id=f"{deployed_category}/email-thread-capture",
        )]
        self.created, self.deleted, self.updated = [], [], []

    def get_all(self, profile_id):
        return list(self.deployed)

    def create(self, profile_id, category, slug, skill_md, scripts):
        self.created.append(f"{category}/{slug}")

    def delete(self, profile_id, skill_dir_id):
        self.deleted.append(skill_dir_id)

    def update(self, profile_id, skill_dir_id, **changes):
        self.updated.append(skill_dir_id)


def _push(monkeypatch, deployed_category, catalog_categories):
    fake = _FakeSkills(deployed_category)
    monkeypatch.setattr(module, "get_client", lambda: SimpleNamespace(skills=fake))
    monkeypatch.setattr(module.skills_data, "list_categories", lambda: list(catalog_categories))
    graph_skill = SimpleNamespace(id="email-thread-capture", category="graph")
    return fake, lambda: SkillManager()._push_to_profile(graph_skill, "default", "---\n---\n", {})


def test_another_live_tools_skill_of_the_same_name_is_never_deleted(monkeypatch):
    fake, push = _push(monkeypatch, deployed_category="outlook", catalog_categories=["graph", "outlook", "vault"])

    with pytest.raises(SkillPreconditionError, match="outlook"):
        push()

    assert fake.deleted == [] and fake.created == []


def test_a_copy_under_a_retired_grouping_is_still_moved(monkeypatch):
    # The 2026-09-06 regroup by Tool: `vault-rebuild` is no Tool any more, so its
    # copy is stale and moving it is right.
    fake, push = _push(monkeypatch, deployed_category="vault-rebuild", catalog_categories=["graph", "vault"])

    assert push() == "moved"
    assert fake.created == ["graph/email-thread-capture"]
    assert fake.deleted == ["vault-rebuild/email-thread-capture"]


def test_the_same_tools_copy_is_updated_in_place(monkeypatch):
    fake, push = _push(monkeypatch, deployed_category="graph", catalog_categories=["graph"])

    assert push() == "updated"
    assert fake.deleted == []
