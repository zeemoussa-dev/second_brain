"""BUG-086 -- the Agents Map took six seconds because listing agents read every
skill of every profile.

A listed agent is a summary: id, name, type, section, icon. It has never carried
skills. Loading them anyway meant parsing every SKILL.md of every profile -- 2,788
files on the reporting install -- and throwing all of it away, on every call, for
`/agents`, `/sections` and anything else that lists.

What is pinned: listing does not touch skills, and asking for one agent still
does.
"""
import pytest

from app.business.core.agents.agent_manager import AgentManager
from app.business.hermes import client as client_module
from app.hermes import HermesAgent, HermesSkill


class FakeSkills:
    """Counts what a listing asks for, and refuses to be free about it."""

    def __init__(self):
        self.calls = []

    def get_all(self, profile_id):
        self.calls.append(profile_id)
        return [HermesSkill(
            id="vault/vault-index", name="vault-index", description="", version="1.0.0",
            category="vault", slug="vault-index",
        )]


class FakeProfiles:
    def __init__(self, skills):
        self._skills = skills
        self.souls_read = []
        self.ids = ["default", "adnoc-expert", "masdar-expert"]

    def _agent(self, profile_id, include_skills):
        return HermesAgent(
            id=profile_id, name=profile_id, description="", short_description="",
            model="gpt-5", provider="custom", reasoning_effort="medium",
            is_primary=profile_id == "default",
            skills=self._skills.get_all(profile_id) if include_skills else [],
            icon="smart_toy",
        )

    def get_all(self, *, include_skills: bool = True):
        return [self._agent(profile_id, include_skills) for profile_id in self.ids]

    def find_by_id(self, agent_id):
        return self._agent(agent_id, True) if agent_id in self.ids else None

    def read_soul(self, agent_id):
        self.souls_read.append(agent_id)
        return ""



@pytest.fixture()
def hermes(monkeypatch):
    skills = FakeSkills()
    profiles = FakeProfiles(skills)
    # `get_by_id` asks for tools as well; the listing path does not (`include_tools`).
    cli = type("Cli", (), {"list_tools": staticmethod(lambda _agent_id: {})})()
    fake_client = type("C", (), {"profiles": profiles, "skills": skills, "cli": cli})()
    monkeypatch.setattr(client_module, "_client", fake_client)
    return skills


def test_listing_agents_does_not_read_a_single_skill(hermes):
    AgentManager().get_all()

    assert hermes.calls == [], (
        "listing read skills for " + ", ".join(hermes.calls) + " -- on a real install that is every "
        "SKILL.md of every profile, discarded immediately"
    )


def test_a_listed_agent_still_carries_what_the_map_renders(hermes):
    agents = {agent.id: agent for agent in AgentManager().get_all()}

    assert "adnoc-expert" in agents
    assert agents["adnoc-expert"].name == "adnoc-expert"
    assert agents["adnoc-expert"].model == "gpt-5"


def test_asking_for_one_agent_still_reads_its_skills(hermes):
    agent = AgentManager().get_by_id("adnoc-expert")

    assert agent is not None
    assert agent.skill_ids == ["vault/vault-index"]
    assert hermes.calls == ["adnoc-expert"]
