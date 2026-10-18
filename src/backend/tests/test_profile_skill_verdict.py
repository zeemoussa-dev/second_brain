"""One verdict rule, two enumeration directions (`REQ-SB-99-US-01`, `ADR-043`).

`check_deployment_drift()` has always asked "is the deployed copy still what
we ship?" from the catalog's side, walking `deployed_to` -- the Registry's
claim, which is the exact list `REQ-SB-96` exists because it is wrong. The
profile debug view asks the same question from the install's own tree.

What is pinned here: the four-status rule exists once and both directions
agree on it; the install-first direction sees a skill the catalog has never
heard of and says so rather than omitting it; nothing on that path reads
`deployed_to` or writes anything; and the whole comparison costs exactly one
directory listing for the one profile asked about (`BUG-086` is the measured
precedent for what the per-profile storm costs).

No test here touches a real install: the Hermes client is a fake object and
the catalog reader is monkeypatched, on top of conftest's suite-wide sandbox.
"""
from __future__ import annotations

import pytest

from app.business.core.skills.skill import Skill
from app.business.core.skills.skill_manager import SkillManager
from app.business.hermes import client as client_module
from app.config import settings
from app.data_access import skills as skills_data
from app.hermes import HermesSkill

PROFILE = "adnoc-expert"


def skill_md(version: str, body: str) -> str:
    return f"---\nname: a-skill\nversion: {version}\n---\n{body}\n"


# The profile's own tree: "<category>/<slug>" -> (version, SKILL.md bytes).
# The categories deliberately differ from the catalog's Tool grouping -- a
# deployed copy still sits under the category it landed in (2026-09-06).
DEPLOYED_TREE = {
    "vault/vault-index": ("1.0.0", skill_md("1.0.0", "index the vault")),
    "vault/thread-capture": ("0.9.0", skill_md("0.9.0", "an older body")),
    "outlook/email-capture": ("2.0.0", skill_md("2.0.0", "edited in place")),
    "jarvis/hand-rolled-thing": ("0.1.0", skill_md("0.1.0", "written on the box")),
}

# The framework catalog, keyed by slug. `hand-rolled-thing` is absent on purpose.
CATALOG = {
    "vault-index": skill_md("1.0.0", "index the vault"),
    "thread-capture": skill_md("1.2.0", "the current body"),
    "email-capture": skill_md("2.0.0", "what we actually ship"),
}


class RefusesToBeIterated:
    """`deployed_to` as a tripwire: the install-first path must never read it."""

    def __iter__(self):
        raise AssertionError("compare_profile_skills read deployed_to")

    def __contains__(self, item):
        raise AssertionError("compare_profile_skills read deployed_to")


class FakeHermesSkills:
    """One profile's real tree, counting every listing and every byte read.

    Every write-shaped call raises: this path is read-only by construction
    (`REQ-SB-99-US-01-AC-05`), so a write here should fail loudly rather
    than be caught by a later assertion.
    """

    def __init__(self, tree: dict[str, tuple[str, str]]):
        self._tree = dict(tree)
        self.get_all_calls: list[str] = []
        self.read_calls: list[tuple[str, str]] = []

    def get_all(self, profile_id: str) -> list[HermesSkill]:
        self.get_all_calls.append(profile_id)
        if profile_id != PROFILE:
            return []
        return [
            HermesSkill(
                id=skill_id, name=skill_id.split("/")[1], description="",
                version=version, category=skill_id.split("/")[0],
                slug=skill_id.split("/")[1],
            )
            for skill_id, (version, _md) in sorted(self._tree.items())
        ]

    def read(self, profile_id: str, skill_id: str) -> str | None:
        self.read_calls.append((profile_id, skill_id))
        if profile_id != PROFILE:
            return None
        entry = self._tree.get(skill_id)
        return entry[1] if entry else None

    def _refuse(self, *args, **kwargs):
        raise AssertionError("a read-only comparison attempted a write into Hermes")

    write = deploy = undeploy = save = create = update = delete = _refuse


@pytest.fixture()
def profile_tree(monkeypatch):
    """The fake install plus a catalog that can only be read, never written."""
    hermes_skills = FakeHermesSkills(DEPLOYED_TREE)
    fake_client = type("FakeClient", (), {"skills": hermes_skills})()
    monkeypatch.setattr(client_module, "_client", fake_client)

    catalog_reads: list[str] = []

    def read_skill_md(slug: str) -> str | None:
        catalog_reads.append(slug)
        return CATALOG.get(slug)

    def refuse_to_write(*args, **kwargs):
        raise AssertionError("a read-only comparison attempted a catalog write")

    monkeypatch.setattr(skills_data, "read_skill_md", read_skill_md)
    monkeypatch.setattr(skills_data, "write_skill_md", refuse_to_write)
    monkeypatch.setattr(skills_data, "write_section_access_map", refuse_to_write)
    monkeypatch.setattr(skills_data, "delete_skill_dir", refuse_to_write)
    monkeypatch.setattr(skills_data, "write_script", refuse_to_write)

    hermes_skills.catalog_reads = catalog_reads
    return hermes_skills


def rows_by_slug(rows: list[dict]) -> dict[str, dict]:
    return {row["slug"]: row for row in rows}


# [REQ-SB-99-US-01-AC-02]
def test_every_skill_on_disk_gets_its_verdict_and_its_real_deployed_version(profile_tree):
    rows = rows_by_slug(SkillManager().compare_profile_skills(PROFILE))

    assert set(rows) == {"vault-index", "thread-capture", "email-capture", "hand-rolled-thing"}
    assert rows["vault-index"]["status"] == "current"
    assert rows["thread-capture"]["status"] == "stale"
    assert rows["email-capture"]["status"] == "modified"
    assert rows["hand-rolled-thing"]["status"] == "unknown_to_framework"

    # The version read off the profile's OWN tree, not the catalog's.
    assert rows["vault-index"]["deployed_version"] == "1.0.0"
    assert rows["thread-capture"]["deployed_version"] == "0.9.0"
    assert rows["email-capture"]["deployed_version"] == "2.0.0"
    assert rows["hand-rolled-thing"]["deployed_version"] == "0.1.0"
    assert rows["thread-capture"]["catalog_version"] == "1.2.0"

    # The id is the path it really sits at, which is not the catalog's grouping.
    assert rows["email-capture"]["skill_id"] == "outlook/email-capture"


# [REQ-SB-99-US-01-AC-02]
def test_a_skill_the_catalog_never_heard_of_is_listed_because_it_is_on_disk(
    profile_tree, monkeypatch
):
    [unknown] = [
        row for row in SkillManager().compare_profile_skills(PROFILE)
        if row["status"] == "unknown_to_framework"
    ]
    assert unknown["slug"] == "hand-rolled-thing"
    assert unknown["catalog_version"] is None

    without_it = {k: v for k, v in DEPLOYED_TREE.items() if k != "jarvis/hand-rolled-thing"}
    monkeypatch.setattr(profile_tree, "_tree", without_it)

    rows = SkillManager().compare_profile_skills(PROFILE)

    assert "hand-rolled-thing" not in rows_by_slug(rows), (
        "the row survived the skill leaving the disk -- enumeration is coming "
        "from the catalog or from deployed_to, not from the install's own tree"
    )
    assert len(rows) == 3


# [REQ-SB-99-US-01-AC-02]
def test_both_directions_return_the_same_status_for_the_same_skill(profile_tree, monkeypatch):
    """The regression this exists to stop: two implementations of "does the
    deployed copy match" drifting apart (228 stale copies of vault_manager.py).
    `tests/test_versioning.py` guards the catalog-first contract itself."""
    monkeypatch.setattr(
        SkillManager, "get_all",
        lambda self: [Skill(
            id="thread-capture", name="thread-capture", description="",
            category="vault", deployed_to=[PROFILE],
        )],
    )

    catalog_first = SkillManager().check_deployment_drift()
    install_first = rows_by_slug(SkillManager().compare_profile_skills(PROFILE))

    [claimed] = [row for row in catalog_first if row["skill_id"] == "thread-capture"]
    assert claimed["status"] == "stale"
    assert claimed["status"] == install_first["thread-capture"]["status"]
    assert claimed["catalog_version"] == install_first["thread-capture"]["catalog_version"]
    assert claimed["deployed_version"] == install_first["thread-capture"]["deployed_version"]


# [REQ-SB-99-US-01-AC-05]
def test_nothing_on_this_path_writes_or_consults_deployed_to(profile_tree, monkeypatch):
    """Looking at a profile changes nothing in it, and does not inherit
    `deployed_to`'s untrustworthiness by reading it."""
    monkeypatch.setattr(
        SkillManager, "get_all",
        lambda self: [Skill(
            id="thread-capture", name="thread-capture", description="",
            category="vault", deployed_to=RefusesToBeIterated(),
        )],
    )

    rows = SkillManager().compare_profile_skills(PROFILE)

    assert len(rows) == 4
    # The sandbox this ran inside, stated rather than assumed: the configured
    # install root does not exist, so no real profile could have been touched.
    assert not settings.hermes_home_path.exists()


# [constraint: cost]
def test_one_profile_costs_one_listing_and_one_read_per_skill(profile_tree):
    """`BUG-086`: the Agents Map took six seconds because a listing re-read
    every skill of every profile. The per-profile comparison pays for the one
    profile it was asked about, once."""
    SkillManager().compare_profile_skills(PROFILE)

    assert profile_tree.get_all_calls == [PROFILE], (
        "listed the tree " + str(len(profile_tree.get_all_calls)) + " times "
        f"({profile_tree.get_all_calls}) -- one listing per profile, never per skill"
    )
    assert profile_tree.catalog_reads == [
        "hand-rolled-thing", "email-capture", "thread-capture", "vault-index"
    ], "one catalog read per distinct slug, not one per lookup"
    # No deployed bytes are read for a slug the catalog does not have: there
    # is nothing to compare it against.
    assert profile_tree.read_calls == [
        (PROFILE, "outlook/email-capture"),
        (PROFILE, "vault/thread-capture"),
        (PROFILE, "vault/vault-index"),
    ]
